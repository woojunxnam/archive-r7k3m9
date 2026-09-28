"""Forward promotion status (REPORT ONLY - never promotes, never authorises live trading).
Reads the latest forward daily_report.csv (sessions >= 2026-09-29) and evaluates the frozen T61-R1C forward gates."""
import json
import sys

import numpy as np
import pandas as pd


def status(path):
    R = pd.read_csv(path, parse_dates=["date"]); R = R[R.date >= "2026-09-29"]
    t61 = R[R.portfolio == "T61-R1C"].set_index("date"); c43 = R[R.portfolio == "C43-CORE"].set_index("date")
    d = t61.daily_pnl.values; eq = np.cumsum(d); dd = float((np.maximum.accumulate(np.r_[0, eq])[1:] - eq).max()) if len(d) else 0.0
    n = len(t61)
    g = {"oos_sessions": n, "common_250_sessions": n >= 250,
         "T61_incremental_vs_C43_avg_day": float((t61.daily_pnl - c43.daily_pnl.reindex(t61.index)).mean()) if n else np.nan,
         "TEST53_matched_excess_avg_day": float(t61.TEST53_matched_excess.mean()) if n else np.nan,
         "max_intraday_margin_pct": float(t61.peak_intraday_margin_pct.max()) if n else np.nan,
         "peak_MNQ": float(t61.peak_MNQ.max()) if n else np.nan, "implementation_violations": int(t61.implementation_violations.sum()),
         "forward_maxdd": dd, "forward_worst_day": float(d.min()) if n else np.nan}
    g["COMMON_GATE"] = bool(g["common_250_sessions"] and g["T61_incremental_vs_C43_avg_day"] > 0 and g["TEST53_matched_excess_avg_day"] > 0
                            and g["max_intraday_margin_pct"] < 100 and g["peak_MNQ"] <= 6 and g["implementation_violations"] == 0)
    g["LIVE_REFERENCE_RISK"] = bool(dd <= 20000 and (g["forward_worst_day"] >= -5000 if n else False))
    g["USER_APPROVAL_OF_DOUBLED_GOVERNOR"] = "REQUIRED (not recorded here)"
    g["AUTO_PROMOTION"] = "NO"; g["LIVE_AUTHORIZATION"] = "NO"
    return g


if __name__ == "__main__":
    print(json.dumps(status(sys.argv[1]), indent=1))
