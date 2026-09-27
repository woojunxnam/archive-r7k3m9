"""V6 Phase 1: V5.3.3 baselines (ES->MES, MNQ) on DEV+VAL only, decomposition, controls.

Usage: python phase1.py ES|MNQ
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bench, decomp, instruments, lab, v533  # noqa: E402

BARS = {"ES": "../out/p123/ES_3m_bars.parquet", "MNQ": "../out/mnq/MNQ_3m_bars.parquet"}
PROF = {"ES": "MES", "MNQ": "MNQ"}
PERIODS = {
    "DEV+VAL": (None, lab.VAL_END), "DEV": lab.SPLITS["DEV"], "VAL": lab.SPLITS["VAL"],
    "PRE_2023": (None, pd.Timestamp("2022-12-31")), "2023+": (pd.Timestamp("2023-01-01"), lab.VAL_END),
    "2020": (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31")),
    "2022": (pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31")),
    "2025+": (pd.Timestamp("2025-01-01"), lab.VAL_END),
}


def stats_table(d, label):
    rows = []
    for p, (s, e) in PERIODS.items():
        st = lab.period_stats(d, s, e)
        st.update(label=label, period=p, env=lab.envelope(st))
        rows.append(st)
    return rows


def main(inst):
    prof = instruments.PROFILES[PROF[inst]]
    pv = prof["point_value"]
    b, a = lab.load(BARS[inst])
    b, a = lab.truncate(b, a, lab.VAL_END)
    out = f"../out/v6/p1_{inst}"
    os.makedirs(out, exist_ok=True)
    res = v533.run(a, v533.make_params(pointValue=pv))
    d = lab.daily(b, res)
    sides = float(res["f_qty"].sum())
    comm = sides * 0.62
    slip = sides * 0.25 * pv
    dc = decomp.decompose(b, res, pv=pv)
    cd = res["counter_dict"]
    summ = {
        "instrument": inst, "pv": pv, "days": len(d), "net": float(res["equity"][-1] - lab.INIT),
        "gross_mtm": dc["gross_mtm"], "beta_at_avg_pos": dc["beta_at_avg_pos"], "timing": dc["timing"],
        "commission": comm, "slippage": slip, "friction": comm + slip,
        "avg_pos": dc["avg_pos"], "max_pos": int(res["pos"].max()),
        "buy_fills": int((res["f_side"] == 1).sum()), "sell_fills": int((res["f_side"] == -1).sum()),
        "buy_orders": cd["buyOrderCount"], "sell_orders": cd["sellOrderCount"], "unfilled": cd["unfilledOrderCount"],
        "margin_util_tv10": lab.margin_util(b, a, res, pv=pv), "min_equity": float(res["equity"].min()),
    }
    # RTH vs overnight gross
    c = b.c.values; o = b.o.values; pos = res["pos"].astype(float)
    prev_c = np.concatenate([[o[0]], c[:-1]]); pp = np.concatenate([[0.0], pos[:-1]])
    mtm = (pp * (o - prev_c) + pos * (c - o)) * pv; rth = b.in_rth.values
    summ["gross_rth"] = float(mtm[rth].sum()); summ["gross_eth"] = float(mtm[~rth].sum())
    rows = stats_table(d, "V533")
    # annual
    ann = d.groupby(d.index.year).agg(days=("pnl", "size"), total=("pnl", "sum"), avg=("pnl", "mean"),
                                      worst=("pnl", "min"), avg_pos=("avg_pos", "mean"))
    ann.to_csv(f"{out}/annual.csv")
    # controls: const 1, matched
    eq1, pos1, rc = bench.constant_long(b, 1, roll_day=a["roll_day"], pv=pv)
    d1 = lab.daily(b, {"equity": eq1, "pos": pos1})
    rows += stats_table(d1, "CONST_1")
    ap = dc["avg_pos"]
    dm = d1.copy(); dm["pnl"] = dm["pnl"] * ap; dm["avg_pos"] = ap; dm["max_pos"] = ap; dm["end_pos"] = ap
    rows += stats_table(dm, f"CONST_MATCHED_{ap:.2f}")
    t = pd.DataFrame(rows)
    t.to_csv(f"{out}/periods.csv", index=False)
    d.to_csv(f"{out}/daily_v533.csv"); d1.to_csv(f"{out}/daily_const1.csv")
    json.dump(summ, open(f"{out}/summary.json", "w"), indent=1, default=float)
    print(json.dumps(summ, indent=1, default=float))
    cols = ["label", "period", "days", "avg_daily", "median", "pos_pct", "worst_day", "best_day", "max_dd", "avg_mes",
            "avg_ex_top1", "avg_ex_top3", "avg_ex_top5", "env"]
    print(t[cols].round(1).to_string())
    print(ann.round(0).to_string())
    # structural window counts (pre-holdout, last 149 sessions before VAL_END), counts only
    sd = b.session_date.drop_duplicates().sort_values()
    start = sd.iloc[-149]
    bb, aa = b[b.session_date >= start].reset_index(drop=True), None
    from t43 import bars as B
    aa = B.to_arrays(bb)
    r2 = v533.run(aa, v533.make_params(pointValue=pv))
    c2 = r2["counter_dict"]
    print("STRUCT149", {k: c2[k] for k in ("buyFillEvents", "sellFillEvents", "buyOrderCount", "sellOrderCount",
                                             "unfilledOrderCount", "baseBuildCount", "overlayBuyCount", "repairBuyCount",
                                             "repairSellCount", "profitSellCount", "riskSellCount")},
          "end_pos", int(r2["pos"][-1]), "max", int(r2["pos"].max()))


if __name__ == "__main__":
    main(sys.argv[1])
