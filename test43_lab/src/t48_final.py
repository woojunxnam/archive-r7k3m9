"""TEST48 finalisation: GA-AC stitched outer result, recurrence, plateau, program gate, registry updates, reports."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import prog_ga as PG  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test48")
REP = os.path.join(C45.ROOT, "reports", "TEST48_ARM_CONFIRM")


def main():
    G = pd.read_csv(f"{OUT}/T48_grid.csv")
    S = pd.read_csv(f"{OUT}/ga/GA-AC_selected.csv")
    st, ex, clusters = PG.stitched("lane_ac", S)
    sess = PG._ctx["sess"]; champ = PG._ctx["champ"]
    vc = pd.Series(clusters).value_counts()
    rec_pass = bool(vc.index[0] != "NONE" and vc.iloc[0] >= 3)
    fin = S[(S.fold == "FINAL_ALL_TO_2026-05-27") & (S.sel_rank == 0)]
    ppass, pbase, PR = False, np.nan, pd.DataFrame()
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    if len(fin) and isinstance(fin.iloc[0].get("genome"), str):
        g = json.loads(fin.iloc[0].genome)
        ppass, pbase, PR = PG.plateau("lane_ac", g, s21, ["xm", "expx"], {"W": [6, 12, 24]})
    # 4-tick stress on the stitched selection
    st4 = np.zeros(len(sess))
    for name, a, b in C45.OUTER:
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        if not len(r) or not isinstance(r.iloc[0].get("genome"), str):
            continue
        g = json.loads(r.iloc[0].genome)
        s0 = int(np.searchsorted(sess.values, np.datetime64(a))); s1 = int(np.searchsorted(sess.values, np.datetime64(b), side="right"))
        st4[s0:s1] = PG._ctx["L"].run(g, PG._ctx, slip=4.0)[0][s0:s1]
    ga_row = P.evaluate_module("GA-AC nested stitched", st, ex, sess, champ,
                               {"plateau_pass": ppass, "recurrence_pass": rec_pass, "stress4_pos": bool(st4[s21:].sum() > 0)})
    ga_row["fold_clusters"] = " ; ".join(clusters)
    gate = pd.concat([pd.DataFrame([ga_row]), G.sort_values("t_excess", ascending=False).head(10)], ignore_index=True)
    gate.to_csv(f"{OUT}/T48_gate.csv", index=False)
    if len(PR):
        PR.to_csv(f"{OUT}/T48_plateau.csv", index=False)
    survivors = int(ga_row["PASS"]) + int(G.finalist.sum())
    res = "SURVIVOR" if survivors else "NO SURVIVOR"
    # ------------------------------------------------ registries
    P.reg_append("AUTONOMOUS_TEST_REGISTRY", [{"test": "TEST48", "hypothesis": "ARM -> later independent confirmation entry (5 setups x 6 confirmations) + GA-AC",
                                               "prereg_hash": open(f"{OUT}/TEST48_PREREGISTRATION.json.sha256").read().strip()[:16],
                                               "result": res, "survivor_count": survivors,
                                               "best_clue": "delayed confirmation beats immediate on average (CF4 15m +1.2 $/day median, 73% of cells); MNQ ORB continuation 4-5/5 folds",
                                               "next_test_reason": "continuation (TEST49) - strength beats weakness in every TEST48 family"}], key="test")
    if not survivors:
        P.reg_append("REJECTED_FAMILY_REGISTRY", [{"family": "arm_confirm_simple_grid", "mechanism": "setup ARM then later independent confirmation (CF1-CF5)",
                                                   "test": "TEST48", "reason_rejected": f"0/180 simple combos pass (max t {G.t_excess.max():.2f}); GA-AC folds {ga_row['folds_pos']}/5",
                                                   "sample_size": "50-1300 trades/combo", "outer_fold_result": f"GA-AC median {ga_row['fold_median']:.2f} $/day",
                                                   "retest_forbidden": "YES (as entry family)", "reopen_requires": "as a sizing / second-contract decision on a validated base"}], key="family")
    P.reg_append("SHADOW_CLUE_REGISTRY", [{"clue_id": "C48_DELAY_BEATS_IMMEDIATE", "source_test": "TEST48",
                                           "mechanism": "waiting for a later independent confirmation improves matched excess vs immediate entry",
                                           "why_interesting": "positive in 53-73% of cells for each confirmation type; CF4 15m median +1.2 $/day",
                                           "why_not_promotable": "levels stay small / not significant; improvement of negative bases",
                                           "future_prereg_test": "second-contract timing (add only after confirmation) on a validated base"},
                                          {"clue_id": "C48_MNQ_ORB", "source_test": "TEST48", "mechanism": "MNQ opening-range breakout continuation",
                                           "why_interesting": "CF0/CF4 4-5/5 positive folds, t 1.2-1.9", "why_not_promotable": "t < 3 on a 180-cell grid",
                                           "future_prereg_test": "TEST49 T5 breakout retention with reused-evidence penalty (t >= 3.5)"}], key="clue_id")
    P.budget("TEST48", hypotheses=0, genomes=0, finalists=survivors, note="final gate")
    # ------------------------------------------------ reports
    os.makedirs(REP, exist_ok=True)
    P.md("T48_00_PREREGISTRATION.md", "TEST48 preregistration", ["```json\n" + open(f"{OUT}/TEST48_PREREGISTRATION.json").read() + "\n```"], REP)
    cols = ["inst", "setup", "conf", "exit", "trades_2021", "avg_trade", "excess_trade", "t_excess", "matched_excess_day", "folds_pos", "fold_median",
            "delta_excess_day_vs_immediate", "corr_C43", "PASS", "finalist"]
    P.md("T48_01_SIMPLE_GRID.md", "TEST48 simple ARM -> CONFIRM grid", [G[cols]], REP)
    dl = G.groupby(["conf"])["delta_excess_day_vs_immediate"].agg(["mean", "median", lambda x: (x > 0).mean()]).rename(columns={"<lambda_0>": "share_pos"})
    P.md("T48_02_DELAYED_VS_IMMEDIATE.md", "TEST48 delayed vs immediate (matched excess $/day)", [dl], REP)
    P.md("T48_03_GA_AC.md", "TEST48 GA-AC nested lane", [S.drop(columns=["genome"], errors="ignore"), f"Stitched outer: {json.dumps({k: ga_row[k] for k in ('folds_pos', 'fold_median', 'standalone_avg_day', 'matched_excess_day', 'corr_C43', 'PASS')})}",
                                                        f"Fold clusters: {ga_row['fold_clusters']}", f"Plateau pass: {ppass} (base {pbase})", PR], REP)
    P.md("T48_04_GATE.md", "TEST48 program gate", [gate[[c for c in gate.columns if not c.startswith("y20")]]], REP)
    P.md("T48_05_SUMMARY.md", "TEST48 summary", [f"RESULT = {res}", f"SURVIVOR_COUNT = {survivors}",
                                                 "LEARNED: the first event is at best an ARM; later confirmation improves matched excess on average but no ARM->CONFIRM "
                                                 "entry reaches significance. Every family that buys STRENGTH (ORB, compression higher-low breakout) scores above every "
                                                 "family that buys WEAKNESS (N3, pullback) -> TEST49 targets continuation.",
                                                 "NEXT_TEST_REASON = continuation / strength-to-close (clue G1, C48_MNQ_ORB)"], REP)
    print(pd.DataFrame([ga_row])[["module", "folds_pos", "fold_median", "standalone_avg_day", "matched_excess_day", "corr_C43", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "PASS"]].round(2).to_string())
    print("clusters", clusters, "plateau", ppass, pbase); print(PR.round(1).to_string() if len(PR) else "")
    print("RESULT", res)


if __name__ == "__main__":
    main()
