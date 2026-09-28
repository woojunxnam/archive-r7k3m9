"""Generic test finalisation for a nested GA lane: stitched outer result, recurrence, plateau, 4-tick stress, program gate."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import prog_ga as PG  # noqa: E402


def lane_gate(lane, S, num_params, disc_params=None):
    st, ex, clusters = PG.stitched(lane, S)
    sess = PG._ctx["sess"]; champ = PG._ctx["champ"]
    vc = pd.Series(clusters).value_counts()
    rec_pass = bool(vc.index[0] != "NONE" and vc.iloc[0] >= 3)
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    fin = S[(S.fold == "FINAL_ALL_TO_2026-05-27") & (S.sel_rank == 0)]
    ppass, pbase, PR, gfin = False, np.nan, pd.DataFrame(), None
    if len(fin) and isinstance(fin.iloc[0].get("genome"), str):
        gfin = json.loads(fin.iloc[0].genome)
        ppass, pbase, PR = PG.plateau(lane, gfin, s21, [p for p in num_params if gfin.get(p, 0) not in (0, 0.0)], disc_params)
    st4 = np.zeros(len(sess))
    for name, a, b in C45.OUTER:
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        if not len(r) or not isinstance(r.iloc[0].get("genome"), str):
            continue
        g = json.loads(r.iloc[0].genome)
        s0 = int(np.searchsorted(sess.values, np.datetime64(a))); s1 = int(np.searchsorted(sess.values, np.datetime64(b), side="right"))
        st4[s0:s1] = PG._ctx["L"].run(g, PG._ctx, slip=4.0)[0][s0:s1]
    row = P.evaluate_module(f"{PG._ctx['L'].NAME} nested stitched", st, ex, sess, champ,
                            {"plateau_pass": ppass, "recurrence_pass": rec_pass, "stress4_pos": bool(st4[s21:].sum() > 0)})
    row["fold_clusters"] = " ; ".join(clusters); row["final_genome"] = json.dumps(gfin) if gfin else None; row["plateau_base"] = pbase
    return row, st, ex, PR
