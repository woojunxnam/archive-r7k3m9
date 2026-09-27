"""TEST43-P Phase 0: ES_r2_G_AGG_0 wall-clock portability gate (frozen parameters, no re-optimisation).
DEV+VAL only (holdout excluded by truncation).  Writes out/p/p01_*.csv"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, instruments, lab, v6lab, v6x  # noqa: E402
from t43 import v6x_frozen_pre_wallclock as v6x_old  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "p")
PATHS = {"ES": "../out/p123/ES_3m_bars.parquet", "MNQ": "../out/mnq/MNQ_3m_bars.parquet",
         "ES5": "../out/v6/ES_5m_bars.parquet", "MNQ5": "../out/v6/MNQ_5m_bars.parquet"}
PROF = {"ES": "MES", "MNQ": "MNQ", "ES5": "MES", "MNQ5": "MNQ"}
PER = ("DEV", "VAL", "DV", "F1", "F2", "F3", "Y2020", "Y2022", "PRE23", "P23")
SL = {c["id"]: c for c in json.load(open("../out/v6/shortlist.json"))}
G = SL["ES_r2_G_AGG_0"]["params"]
ATR_RATIO = 289.69 / 519.78   # ES->MNQ median daily ATR$ ratio (V6_09)
_S = {}


def setup(inst):
    if inst not in _S:
        b = pd.read_parquet(PATHS[inst]); b = b[b.session_date <= lab.VAL_END].reset_index(drop=True)
        a = B.to_arrays(b)
        a["roll_day"] = b.roll_adjacent.fillna(False).astype(bool).values
        a["mref"] = (b.o - b.cum_adjustment.astype(float)).values
        _S[inst] = (b, a)
    return _S[inst]


def transfer_params(p):
    q = dict(p)
    prof = instruments.PROFILES["MNQ"]
    q["pointValue"] = prof["point_value"]; q["rollCostPerContract"] = 2 * (prof["commission_side"] + prof["tick_value"])
    q["commission"] = prof["commission_side"]
    sc = lambda x: int(round(x * ATR_RATIO))  # noqa: E731
    q["intradayMaxQty"] = max(1, sc(p["intradayMaxQty"])); q["coreQty"] = min(q["intradayMaxQty"], sc(p["coreQty"]))
    q["kBase"] = sc(p["kBase"]); q["kMid"] = q["coreQty"] - q["kBase"] - sc(p["kTop"]); q["kTop"] = sc(p["kTop"])
    q["lotQty"] = max(1, sc(p["lotQty"]))
    return q


def evaluate(inst, p, kernel=v6x, m_intra=1.0, m_on=1.0):
    b, a = setup(inst)
    prof = instruments.PROFILES[PROF[inst]]; pv = prof["point_value"]
    res = kernel.run(a, kernel.make_params(**p))
    d = lab.daily(b, res)
    o = {"inst": inst}
    o.update(v6lab.period_block(inst, d, PER, lab.VAL_END, mb=True))
    rawpx = (b.c - b.cum_adjustment.astype(float)).values
    frac = np.where(b.in_rth.values, instruments.margin_frac(prof, "intraday") * m_intra,
                    instruments.margin_frac(prof, "overnight") * m_on)
    util = res["pos"] * rawpx * pv * frac / np.maximum(res["equity"], 1.0)
    o["peak_margin_util"] = float(util.max()); o["margin_breach"] = bool(util.max() > 1 or res["equity"].min() <= 0)
    days = o["DV_days"]
    o["fills"] = int(len(res["f_qty"])); o["fills_per_day"] = o["fills"] / days
    o["friction"] = float(res["f_qty"].sum()) * (p.get("commission", 0.62) + p.get("slippageTicks", 1) * 0.25 * pv)
    o["friction_per_day"] = o["friction"] / days
    rth = b.in_rth.values; dv = (b.session_date <= lab.VAL_END).values
    o["avg_pos"] = float(res["pos"][dv].mean()); o["avg_on_pos"] = float(res["pos"][dv & ~rth].mean())
    o["max_pos"] = int(res["pos"].max())
    return o, res, d


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    # 1) regression: frozen kernel vs wall-clock kernel on native 3m
    o0, r0, _ = evaluate("ES", G, kernel=v6x_old); o1, r1, _ = evaluate("ES", G)
    same = (len(r0["f_qty"]) == len(r1["f_qty"]) and np.array_equal(r0["f_bar"], r1["f_bar"]) and
            np.array_equal(r0["f_qty"], r1["f_qty"]) and np.array_equal(r0["f_px"], r1["f_px"]) and
            np.array_equal(r0["pos"], r1["pos"]))
    rows.append({"test": "OLD_3M_FROZEN_KERNEL", **o0}); rows.append({"test": "WALLCLOCK_3M", **o1, "fill_for_fill_identical": same})
    # 2) portability: 5m and MNQ transfer
    p5 = dict(G, barMinutes=5)
    rows.append({"test": "WALLCLOCK_ES_5M", **evaluate("ES5", p5)[0]})
    rows.append({"test": "NAIVE_ES_5M_NO_CONVERSION(ref)", **evaluate("ES5", G, kernel=v6x_old)[0]})
    pm = transfer_params(G)
    rows.append({"test": "TRANSFER_MNQ_3M", **evaluate("MNQ", pm)[0], "transfer_params": json.dumps(pm)})
    rows.append({"test": "TRANSFER_MNQ_5M", **evaluate("MNQ5", dict(pm, barMinutes=5))[0]})
    # 3) stress on ES 3m (frozen parameters)
    for lab_, q, mi, mo in (("SLIP2", dict(G, slippageTicks=2), 1, 1), ("SLIP4", dict(G, slippageTicks=4), 1, 1),
                            ("COMM1.00", dict(G, commission=1.00), 1, 1),
                            ("TIMING_BRITTLENESS_STRESS", dict(G, fillDelayBars=1), 1, 1),
                            ("MARGINx1.5_INTRADAY", G, 1.5, 1), ("ON_MARGINx2", G, 1, 2),
                            ("ES_5M_SLIP4", dict(p5, slippageTicks=4), 1, 1),
                            ("ES_5M_TIMING_BRITTLENESS_STRESS", dict(p5, fillDelayBars=1), 1, 1)):
        inst = "ES5" if lab_.startswith("ES_5M") else "ES"
        rows.append({"test": lab_, **evaluate(inst, q, m_intra=mi, m_on=mo)[0]})
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/p01_g_portability.csv", index=False)
    cols = ["test", "DV_total", "DEV_avg_daily", "DEV_max_dd", "DEV_worst_day", "DEV_excess_vs_mb", "VAL_avg_daily",
            "VAL_max_dd", "VAL_excess_vs_mb", "Y2022_avg_daily", "Y2022_max_dd", "fills", "friction", "avg_pos",
            "avg_on_pos", "peak_margin_util", "margin_breach", "DEV_env", "VAL_env"]
    pd.set_option("display.width", 260)
    print(df[cols].round(1).to_string(index=False))
    print("fill-for-fill identical on 3m:", same)


if __name__ == "__main__":
    main()
