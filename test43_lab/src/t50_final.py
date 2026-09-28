"""TEST50 finalisation."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_final as PF  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test50")
if __name__ == "__main__":
    G = pd.read_csv(f"{OUT}/T50_grid.csv")
    S = pd.read_csv(f"{OUT}/ga/GA-VX_selected.csv")
    row, st, ex, PR = PF.lane_gate("lane_vx", S, ["kthr", "xsize", "buf"], {"L": [6, 12, 24], "W": [6, 12, 24]})
    np.save(f"{OUT}/GA-VX_stitched_daily.npy", np.stack([st, ex]))
    gate = pd.concat([pd.DataFrame([row]), G.sort_values("t_excess", ascending=False).head(10)], ignore_index=True)
    gate.to_csv(f"{OUT}/T50_gate.csv", index=False); PR.to_csv(f"{OUT}/T50_plateau.csv", index=False)
    for k in ["folds_pos", "fold_median", "fold_worst", "standalone_avg_day", "standalone_max_dd", "matched_excess_day", "corr_C43", "comb_max_dd",
              "comb_worst_day", "comb_ret_dd", "C43_ret_dd", "active_days", "max_year_share", "remove_top3"] + [f"G{i}" for i in range(1, 10)] + ["PASS", "fold_clusters", "final_genome"]:
        print(k, row[k] if not isinstance(row[k], float) else round(row[k], 4))
    print(PR.round(1).to_string())
