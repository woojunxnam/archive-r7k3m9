"""TEST117 final synthesis (prereg 87bc894)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t96_common as C  # noqa: E402
import box_common as B  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t117"); os.makedirs(OUT, exist_ok=True)


def main():
    surv = pd.read_csv(os.path.join(S.REP, "MASTER_SURVIVOR_LIBRARY.csv"))
    mc = C.main_ctx(); I = mc["Is"]["MNQ"]; main = mc["main"]; full = I.full; s21 = np.asarray(I.sess >= pd.Timestamp("2021-01-01")) & full
    r = B.risk(main[full]); fr = {"members": "CURRENT_LOCKED_MAIN", "avg_day": r["avg_day"], "avg_day_2021": float(main[s21].mean()), "max_dd": r["max_dd"],
                                  "worst_day": r["worst_day"], "ret_dd": r["ret_dd"]}
    admitted = []                                   # sequential allocator: no PORTFOLIO_ADDITIVE survivors exist -> nothing to admit
    assert len(surv) == 0, "survivor library not empty: allocator path must be implemented"
    fr["GAP_TO_600"] = 600 - fr["avg_day"]; fr["MAIN_DD_NORMALIZED_AVG_DAY"] = fr["avg_day"] / fr["max_dd"] * 10000
    k600 = 600 / fr["avg_day"]
    scal = [{"k": k, "avg_day": k * fr["avg_day"], "max_dd": k * fr["max_dd"], "worst_day": k * fr["worst_day"], "ret_dd": fr["ret_dd"],
             "label": "SCALING_REPORT_ONLY" + (" (exceeds capacity caps)" if k > 1 else "")} for k in (1, 1.5, 2, 3, 4, round(k600, 3))]
    json.dump({"frontier": fr, "admitted": admitted, "k_600": k600}, open(os.path.join(OUT, "TEST117_FRONTIER.json"), "w"), indent=1, default=float)
    pd.DataFrame(scal).to_csv(os.path.join(OUT, "TEST117_SCALING_FRONTIER.csv"), index=False)
    print(fr, k600); print(pd.DataFrame(scal).round(1))
    json.dump({"ledger_rows": 0, "definitions_new": 0}, open(os.path.join(OUT, "T117_META.json"), "w"))


if __name__ == "__main__":
    main()
