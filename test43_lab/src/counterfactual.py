"""V5.3.3 tactical counterfactual ablation (order-family suppression), DEV+VAL only.

Usage: python counterfactual.py MNQ|ES
Families are suppressed at order submission (the bar's action is cancelled, nothing substituted).
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, decomp, instruments, lab, v533, v6x  # noqa: E402

BARS = {"ES": "../out/p123/ES_3m_bars.parquet", "MNQ": "../out/mnq/MNQ_3m_bars.parquet"}
PROF = {"ES": "MES", "MNQ": "MNQ"}
R = v6x.R
FAM = {
    "BASE_BUILD": ["BASE_ANTISTALL", "BASE_STRENGTH", "DRIFT_BASE", "BASE_PULLBACK"],
    "OVERLAY_BUYS": ["OVERLAY_STRENGTH", "DRIFT_OVERLAY", "OVERLAY_PULLBACK"],
    "REPAIR_SELLS": ["REPAIR_SELL"],
    "REPAIR_REBUYS": ["LOWER_REBUY", "FAILED_RESTORE"],
    "LOWER_REBUY_ONLY": ["LOWER_REBUY"],
    "FAILED_RESTORE_ONLY": ["FAILED_RESTORE"],
    "PROFIT_SELLS(fast recycle)": ["PROFIT_SELL"],
    "RISK_SELLS(target trim)": ["TARGET_TRIM"],
    "BASE_RECYCLE(rotate/core exit)": ["BASE_ROTATE", "CORE_EXIT"],
    "DRIFT_BUYS": ["DRIFT_BASE", "DRIFT_OVERLAY"],
    "REVERSAL_ENTRIES": ["REVERSAL_INITIAL", "MIXED_INITIAL"],
    "TREND_CONT_ADDS": ["TREND_INITIAL", "BASE_STRENGTH", "OVERLAY_STRENGTH"],
    "PULLBACK_ADDS": ["BASE_PULLBACK", "OVERLAY_PULLBACK"],
}


def mask(names):
    m = 0
    for n in names:
        m |= 1 << R[n]
    return m


def main(inst):
    prof = instruments.PROFILES[PROF[inst]]; pv = prof["point_value"]
    b = pd.read_parquet(BARS[inst]); b = b[b.session_date <= lab.VAL_END].reset_index(drop=True)
    a = B.to_arrays(b)
    r0 = v533.run(a, v533.make_params(pointValue=pv))

    def run(m, label):
        r = v6x.run(a, v6x.make_params(pointValue=pv, disableMask=m))
        d = lab.daily(b, r)
        st = lab.period_stats(d)
        dc = decomp.decompose(b, r, pv=pv)
        sides = float(r["f_qty"].sum())
        c = b.c.values; o = b.o.values; pos = r["pos"].astype(float)
        prev_c = np.concatenate([[o[0]], c[:-1]]); pp = np.concatenate([[0.0], pos[:-1]])
        mtm = (pp * (o - prev_c) + pos * (c - o)) * pv
        return {"variant": label, "net": float(r["equity"][-1] - lab.INIT), "gross": dc["gross_mtm"],
                "beta": dc["beta_at_avg_pos"], "timing": dc["timing"], "friction": sides * (0.62 + 0.25 * pv),
                "fills": int(len(r["f_qty"])), "max_dd": st["max_dd"], "worst_day": st["worst_day"],
                "avg_pos": dc["avg_pos"], "avg_on_pos": st["avg_on_mes"], "avg_daily": st["avg_daily"],
                "gross_rth": float(mtm[b.in_rth.values].sum()), "gross_eth": float(mtm[~b.in_rth.values].sum()),
                "Y2022": float(d.loc["2022"].pnl.sum()) if "2022" in d.index.year.astype(str) else np.nan}

    base = run(0, "BASELINE")
    assert abs(base["net"] - (r0["equity"][-1] - lab.INIT)) < 1e-6, "v6x must reproduce v533"
    rows = [base]
    for k, v in FAM.items():
        rows.append(run(mask(v), "-" + k))
    pairs = ["REPAIR_SELLS", "REPAIR_REBUYS", "PROFIT_SELLS(fast recycle)", "RISK_SELLS(target trim)", "OVERLAY_BUYS",
             "PULLBACK_ADDS", "TREND_CONT_ADDS"]
    for x, y in itertools.combinations(pairs, 2):
        rows.append(run(mask(FAM[x] + FAM[y]), f"-{x} -{y}"))
    rows.append(run(mask(FAM["REPAIR_SELLS"] + FAM["REPAIR_REBUYS"] + FAM["PROFIT_SELLS(fast recycle)"] + FAM["RISK_SELLS(target trim)"]),
                    "-ALL_SELLS_EXCEPT_NONE(buy&hold-like)"))
    df = pd.DataFrame(rows)
    for k in ("net", "gross", "timing", "friction", "fills", "max_dd", "worst_day", "avg_pos", "avg_on_pos"):
        df["d_" + k] = df[k] - base[k]
    os.makedirs("../out/v6/cf", exist_ok=True)
    df.to_csv(f"../out/v6/cf/counterfactual_{inst}.csv", index=False)
    pd.set_option("display.width", 250)
    print(df[["variant", "net", "gross", "timing", "friction", "fills", "max_dd", "worst_day", "avg_pos", "avg_on_pos",
              "d_net", "d_timing", "d_friction", "d_fills"]].round(0).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
