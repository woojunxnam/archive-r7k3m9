"""TEST45 Phase 23-26: apply the PREDECLARED final-candidate rule (t45_07_eval docstring) mechanically to every candidate."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402

F = os.path.join(C.T45, "final")
LADDER = {"DET": 2, "V6": 2, "ML": 3, "GA": 6, "GP": 7}


def main():
    L = pd.read_csv(f"{F}/T45_19_20_combination_scaling.csv"); L = L[L.cap == 2]
    V = pd.read_csv(f"{F}/T45_v6_state_carry_family.csv")
    CR = pd.read_csv(f"{F}/T45_outer_block_comparison.csv")
    ga_plateau = pd.read_csv(f"{F}/T45_14_ga_fold_plateau.csv")
    rec = pd.read_csv(f"{F}/T45_13_ga_recurrence.csv")
    # comparators (simplest control of the same family)
    unc = V[V.rule.str.startswith("UNCOND_CARRY")].set_index("rule")
    ctlB = CR[CR.candidate.str.startswith("DET|CONTROL_B GAP_LOCK")].set_index("candidate")

    def carry_ctrl(inst, t="15:45"):
        r = unc.loc[f"UNCOND_CARRY|{inst}|{t}"]; return r.outer_median, r.comb_ret_dd

    def morn_ctrl(inst):
        r = ctlB.loc[f"DET|CONTROL_B GAP_LOCK<=-0.5ATR +1 09:32->16:00 [{inst}]"]; return r.outer_median, r.comb_ret_dd
    rows = []
    for _, r in V[~V.rule.str.contains("anti")].iterrows():
        fam, inst, t = r.rule.split("|")[:3]
        cm, cr = carry_ctrl(inst, t)
        rows.append({"candidate": r.rule, "rung": "DET (GA-recurrence-derived simple rule)", "oos_evidence": "fixed rule, full-history blocks (concept found independently in 5/5 nested GA/GP folds)",
                     "outer_median": r.outer_median, "outer_pos": r.outer_pos, "comb_ret_dd": r.comb_ret_dd, "champ_ret_dd": r.champ_ret_dd,
                     "incr_avg": r.incr_avg, "corr": r["corr"], "comb_mdd": r.comb_mdd, "comb_worst": r.comb_worst, "ctrl_outer_median": cm, "ctrl_comb_ret_dd": cr,
                     "plateau_ok": True, "recurrence_ok": True})
    for _, r in L.iterrows():
        nm = r.candidate
        if nm.startswith("GA|") or nm.startswith("GP|"):
            continue                                   # in-sample final evolutions: judged via their nested stitched procedure below
        fam = nm.split("|")[1]; inst = nm.split("|")[2]
        morning = fam in ("CONTROL_B", "S2", "S3", "S4")
        cm, cr = morn_ctrl(inst) if morning else carry_ctrl(inst, "16:14" if fam == "CONTROL_A" else "15:45")
        rows.append({"candidate": nm, "rung": "DET", "oos_evidence": "fixed predeclared rule, full-history blocks", "outer_median": r.outer_median,
                     "outer_pos": r.outer_pos, "comb_ret_dd": r.comb_ret_dd, "champ_ret_dd": r.champ_ret_dd, "incr_avg": r.incr_avg, "corr": r["corr"],
                     "comb_mdd": r.comb_mdd, "comb_worst": r.comb_worst, "ctrl_outer_median": cm, "ctrl_comb_ret_dd": cr, "plateau_ok": True, "recurrence_ok": True})
    ga_rec = rec[(rec.concept == "c_boost_feature") & (rec.value == "champ_pos>")]
    for _, r in CR.iterrows():
        nm = r.candidate
        if "NESTED" in nm or nm.startswith("ML|"):
            if nm.startswith("ML|"):
                task = nm.split("|")[1]
                cm, cr = carry_ctrl("BOTH") if task == "A_CARRY" else morn_ctrl("BOTH")
                rung, pl, rc = "ML", True, True
            else:
                cm, cr = (carry_ctrl("BOTH") if "CLOSE" in nm else morn_ctrl("BOTH")) if "GP" in nm else \
                    (max(carry_ctrl("BOTH")[0], morn_ctrl("BOTH")[0]), max(carry_ctrl("BOTH")[1], morn_ctrl("BOTH")[1]))
                rung = "GA" if nm.startswith("GA") else "GP"
                pl = bool(ga_plateau.plateau_pass.sum() >= 3) if rung == "GA" else False   # GP plateau not established -> fails closed
                rc = bool(len(ga_rec) and ga_rec.outer_folds_present.max() >= 3)
            rows.append({"candidate": nm, "rung": rung, "oos_evidence": "nested outer folds (stitched)" if "NESTED" in nm else "expanding walk-forward from 2021-05",
                         "outer_median": r.outer_median, "outer_pos": r.outer_pos, "comb_ret_dd": r.comb_ret_dd, "champ_ret_dd": r.champ_ret_dd,
                         "incr_avg": r.incr_avg, "corr": r["corr"], "comb_mdd": r.comb_mdd, "comb_worst": np.nan, "ctrl_outer_median": cm, "ctrl_comb_ret_dd": cr,
                         "plateau_ok": pl, "recurrence_ok": rc})
    R = pd.DataFrame(rows)
    R["R1_oos_positive"] = (R.outer_median > 0) & (R.outer_pos >= 4)
    R["R2_ret_dd_ge_champion"] = R.comb_ret_dd >= R.champ_ret_dd
    R["R3_incr_ge5_corr_le0.5"] = (R.incr_avg >= 5) & (R["corr"].abs() <= 0.5)
    R["R4_envelope"] = (R.comb_mdd <= 10000) & ((R.comb_worst >= -2500) | R.comb_worst.isna())
    R["R5_beats_simplest_control"] = (R.outer_median > R.ctrl_outer_median) & (R.comb_ret_dd > R.ctrl_comb_ret_dd)
    R["R6_plateau_recurrence"] = R.plateau_ok & R.recurrence_ok
    rc = [c for c in R.columns if c.startswith("R") and c[1].isdigit()]
    R["ELIGIBLE"] = R[rc].all(1)
    R["rules_failed"] = R[rc].apply(lambda x: ",".join(c.split("_")[0] for c in rc if not x[c]), axis=1)
    R.to_csv(f"{F}/T45_24_candidate_rule_audit.csv", index=False)
    el = R[R.ELIGIBLE]
    if len(el):
        best = el.comb_ret_dd.max()
        el = el[el.comb_ret_dd >= 0.9 * best].copy(); el["ladder"] = el.rung.str.split(" ").str[0].map(LADDER)
        final = el.sort_values(["ladder", "comb_ret_dd"], ascending=[True, False]).iloc[0].candidate
    else:
        final = "NONE"
    near = R[R.rules_failed.str.count(",") == 0].sort_values("comb_ret_dd", ascending=False)
    json.dump({"FINAL_TEST45_CHALLENGER": final, "n_candidates": len(R), "n_eligible": int(R.ELIGIBLE.sum()),
               "near_misses_one_rule": near[["candidate", "rules_failed", "comb_ret_dd", "incr_avg", "corr", "outer_median", "outer_pos"]].head(15).to_dict("records")},
              open(f"{F}/T45_24_final_selection.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 80)
    print(R[["candidate", "outer_median", "outer_pos", "comb_ret_dd", "incr_avg", "corr", "comb_mdd", "comb_worst", "ctrl_outer_median", "rules_failed", "ELIGIBLE"]].round(4).to_string())
    print("FINAL", final)


if __name__ == "__main__":
    main()
