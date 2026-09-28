"""TEST52 shadow-module combination, exactly as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import prog_ga as PG  # noqa: E402
import t47_engine as E  # noqa: E402
import t49_engine as T49  # noqa: E402
from t49_run import matched  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test52"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    mods = {}
    for nm, lane, path in (("M1_GA-AC", "lane_ac", "out/test48/ga/GA-AC_selected.csv"), ("M2_GA-CT", "lane_ct", "out/test49/ga/GA-CT_selected.csv"),
                           ("M3_GA-VX", "lane_vx", "out/test50/ga/GA-VX_selected.csv")):
        st, ex, cl = PG.stitched(lane, pd.read_csv(os.path.join(C45.ROOT, path)))
        mods[nm] = (st, ex)
    sess = PG._ctx["sess"]; champ = PG._ctx["champ"]
    es, nq = E.setup()
    st4 = T49.State(nq)
    b = T49.family_entries(st4, "T1_OPENING_DRIVE", t="10:00", k=0.25)
    ej = np.where(b >= 0, 5 * (b + 1), -1)
    d, s, j, pnl, so = T49.trades(nq, ej, "X1615")
    key = nq.year * 100 + nq.vt * 10 + nq.bull.astype(int)
    exc = matched(nq, s, j, pnl, "X1615", key); xd = np.zeros(nq.n); np.add.at(xd, so, exc)
    mods["M4_MNQ_OPEN_DRIVE"] = (d, xd)
    m = sess >= P.SPAN21
    D = pd.DataFrame({k: v[0][m] for k, v in mods.items()})
    corr = D.corr(); act = (D != 0).astype(int)
    jac = pd.DataFrame({a: {b_: float(((D[a] < 0) & (D[b_] < 0)).sum() / max(((D[a] < 0) | (D[b_] < 0)).sum(), 1)) for b_ in D} for a in D})
    tot = sum(v[0] for v in mods.values()); totx = sum(v[1] for v in mods.values())
    row = P.evaluate_module("TEST52 equal-weight shadow combination", tot, totx, sess, champ, {"plateau_pass": True, "recurrence_pass": True})
    row["peak_simultaneous_modules_active_days"] = int((act.sum(1) >= 3).sum()); row["max_modules_same_day"] = int(act.sum(1).max())
    indiv = pd.DataFrame([P.evaluate_module(k, v[0], v[1], sess, champ) for k, v in mods.items()])
    pd.DataFrame([row]).to_csv(f"{OUT}/T52_combination_gate.csv", index=False); corr.to_csv(f"{OUT}/T52_corr.csv"); jac.to_csv(f"{OUT}/T52_loss_jaccard.csv")
    indiv.to_csv(f"{OUT}/T52_modules.csv", index=False)
    pd.set_option("display.width", 250)
    print(corr.round(2)); print(jac.round(2))
    print(indiv[["module", "folds_pos", "standalone_avg_day", "matched_excess_day", "corr_C43", "comb_ret_dd", "PASS"]].round(3))
    for k in ["folds_pos", "fold_median", "standalone_avg_day", "standalone_max_dd", "standalone_worst_day", "matched_excess_day", "corr_C43", "comb_avg_day", "comb_max_dd",
              "comb_worst_day", "comb_ret_dd", "C43_ret_dd", "max_year_share", "remove_top3", "remove_top5", "max_modules_same_day"] + [f"G{i}" for i in range(1, 10)] + ["PASS"]:
        print(k, round(row[k], 4) if isinstance(row[k], float) else row[k])
