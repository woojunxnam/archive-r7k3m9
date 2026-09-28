"""TEST49 finalisation."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import prog_final as PF  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test49")
REP = os.path.join(C45.ROOT, "reports", "TEST49_CONTINUATION")

if __name__ == "__main__":
    G = pd.read_csv(f"{OUT}/T49_grid.csv")
    S = pd.read_csv(f"{OUT}/ga/GA-CT_selected.csv")
    row, st, ex, PR = PF.lane_gate("lane_ct", S, ["k_ret", "eff_min", "above_min", "pos_min"], {"t0": ["10:00", "10:15", "10:30", "11:00", "11:30"], "span": [0, 3, 6, 12, 24]})
    np.save(f"{OUT}/GA-CT_stitched_daily.npy", np.stack([st, ex]))
    gate = pd.concat([pd.DataFrame([row]), G.sort_values("t_excess", ascending=False).head(10)], ignore_index=True)
    gate.to_csv(f"{OUT}/T49_gate.csv", index=False)
    PR.to_csv(f"{OUT}/T49_plateau.csv", index=False)
    keys = ["folds_pos", "fold_median", "fold_worst", "standalone_avg_day", "standalone_max_dd", "standalone_worst_day", "matched_excess_day", "corr_C43",
            "comb_avg_day", "comb_max_dd", "comb_worst_day", "comb_ret_dd", "C43_ret_dd", "active_days", "max_year_share", "remove_top3", "remove_top5",
            "roll12m_pos_share"] + [f"G{i}" for i in range(1, 10)] + ["PASS", "fold_clusters", "final_genome", "plateau_base"]
    for k in keys:
        print(k, row[k] if not isinstance(row[k], float) else round(row[k], 4))
    print(PR.round(1).to_string())
