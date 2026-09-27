"""V6 research harness (DEV+VAL only; holdout is excluded by truncation)."""
from __future__ import annotations
import os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from . import features, instruments, lab, v6a

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "out")
BARS = {"ES": os.path.join(ROOT, "p123", "ES_3m_bars.parquet"), "MNQ": os.path.join(ROOT, "mnq", "MNQ_3m_bars.parquet"),
        "ES5": os.path.join(ROOT, "v6", "ES_5m_bars.parquet"), "MNQ5": os.path.join(ROOT, "v6", "MNQ_5m_bars.parquet")}
PROF = {"ES": "MES", "MNQ": "MNQ", "ES5": "MES", "MNQ5": "MNQ"}
PERIODS = {
    "DEV": lab.SPLITS["DEV"], "VAL": lab.SPLITS["VAL"], "DV": (None, lab.VAL_END),
    "PRE23": (None, pd.Timestamp("2022-12-31")), "P23": (pd.Timestamp("2023-01-01"), lab.VAL_END),
    "Y2020": (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31")),
    "Y2022": (pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31")),
    "F1": (None, pd.Timestamp("2020-12-31")),
    "F2": (pd.Timestamp("2021-01-01"), pd.Timestamp("2022-12-31")),
    "F3": (pd.Timestamp("2023-01-01"), pd.Timestamp("2024-12-31")),
}
_S = {}


def inst_params(inst):
    p = instruments.PROFILES[PROF[inst]]
    return dict(pointValue=p["point_value"], mIntraFrac=instruments.margin_frac(p, "intraday"),
                mOnFrac=instruments.margin_frac(p, "overnight"),
                rollCost=2 * (p["commission_side"] + p["tick_value"]), commission=p["commission_side"])


def load(inst, end=lab.VAL_END):
    key = (inst, str(end))
    if key not in _S:
        b = pd.read_parquet(BARS[inst])
        if end is not None:
            b = b[b.session_date <= end].reset_index(drop=True)
        f = features.build(b, instruments.PROFILES[PROF[inst]]["point_value"])
        _S[key] = (b, f)
    return _S[key]


def daily(b, r):
    return lab.daily(b, {"equity": r["equity"], "pos": r["pos"]})


_C1 = {}


def const1_daily(inst, end=lab.VAL_END):
    """Constant 1-contract long (entry at first bar, roll cost, commission+1 tick) daily table."""
    key = (inst, str(end))
    if key not in _C1:
        from . import bench
        b, _ = load(inst, end)
        p = instruments.PROFILES[PROF[inst]]
        rd = b.roll_adjacent.fillna(False).astype(bool).values
        eq, pos, _ = bench.constant_long(b, 1, roll_day=rd, pv=p["point_value"], comm=p["commission_side"])
        _C1[key] = lab.daily(b, {"equity": eq, "pos": pos})
    return _C1[key]


def matched_beta(inst, d, per, end=lab.VAL_END):
    """Constant long with the SAME average exposure over the SAME period."""
    s, e = PERIODS[per]
    c1 = const1_daily(inst, end)
    x = d if s is None else d[d.index >= s]
    x = x if e is None else x[x.index <= e]
    y = c1.loc[x.index]
    n = float(x["avg_pos"].mean())
    y = y.copy(); y["pnl"] = y["pnl"] * n; y["avg_pos"] = n; y["max_pos"] = n; y["end_pos"] = n
    st = lab.period_stats(y)
    return {"mb_avg": st["avg_daily"], "mb_dd": st["max_dd"], "mb_worst": st["worst_day"], "mb_n": n,
            "mb_ret_dd": st["avg_daily"] / st["max_dd"] if st["max_dd"] > 0 else np.nan}


def period_block(inst, d, periods, end=lab.VAL_END, mb=True):
    out = {}
    for per in periods:
        s, e = PERIODS[per]
        st = lab.period_stats(d, s, e)
        for k in ("days", "total", "avg_daily", "median", "pos_pct", "worst_day", "max_dd", "avg_mes", "avg_on_mes",
                  "max_mes", "avg_ex_top5", "ret_dd"):
            out[f"{per}_{k}"] = st.get(k)
        out[f"{per}_env"] = lab.envelope(st) if st else None
        if mb and st:
            m = matched_beta(inst, d, per, end)
            for k, v in m.items():
                out[f"{per}_{k}"] = v
            out[f"{per}_excess_vs_mb"] = st["avg_daily"] - m["mb_avg"]
            out[f"{per}_dd_ratio_vs_mb"] = st["max_dd"] / m["mb_dd"] if m["mb_dd"] > 0 else np.nan
            cr = st["avg_daily"] / st["max_dd"] if st["max_dd"] > 0 else np.nan
            out[f"{per}_retdd_gain_vs_mb"] = cr / m["mb_ret_dd"] if m["mb_ret_dd"] and m["mb_ret_dd"] > 0 else np.nan
    return out


def evaluate(inst, cfg, end=lab.VAL_END, periods=("DEV", "VAL", "DV", "PRE23", "P23", "Y2020", "Y2022"), keep=False, mb=False):
    b, f = load(inst, end)
    p = inst_params(inst); p.update({k: v for k, v in cfg.items() if not k.startswith("_")})
    r = v6a.run(b, f, v6a.make_params(**p))
    d = daily(b, r)
    out = {"inst": inst, "label": cfg.get("_label", "")}
    out.update(period_block(inst, d, periods, end, mb=mb))
    # IBKR-style margin check: intraday frac in RTH, overnight frac outside
    rawpx = (b.c - b.cum_adjustment.astype(float)).values
    frac = np.where(b.in_rth.values, p["mIntraFrac"], p["mOnFrac"])
    req = r["pos"] * rawpx * p["pointValue"] * frac
    eq = r["equity"]
    util = np.where(eq > 0, req / np.maximum(eq, 1.0), np.where(req > 0, np.inf, 0))
    out["peak_margin_util"] = float(util.max()); out["peak_margin_req"] = float(req.max())
    out["margin_breach"] = bool(util.max() > 1.0); out["min_equity"] = float(eq.min())
    sides = float(np.abs(r["f_qty"]).sum())
    out["contract_sides"] = sides; out["fills"] = int(len(r["f_qty"]))
    out["friction"] = sides * (p["commission"] + 0.25 * p["pointValue"])
    for k, v in cfg.items():
        if not k.startswith("_"):
            out["p_" + k] = v
    if keep:
        return out, r, d
    return out


def _init(inst, end):
    load(inst, end)


def _one(args):
    inst, cfg, end = args
    try:
        return evaluate(inst, cfg, end)
    except Exception as e:  # noqa: BLE001
        return {"inst": inst, "label": cfg.get("_label", ""), "error": repr(e)}


def run_many(inst, cfgs, end=lab.VAL_END, workers=4):
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(inst, end)) as ex:
        rows = list(ex.map(_one, [(inst, c, end) for c in cfgs], chunksize=max(1, len(cfgs) // (workers * 6))))
    return pd.DataFrame(rows)
