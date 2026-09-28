"""TEST65+ program final status (stopping criterion: >= 4 distinct families after TEST65 failed)."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import prog_common as P  # noqa: E402

if __name__ == "__main__":
    K.reg_append("TEST65_PLUS_RESEARCH_REGISTRY", [{"test": "TEST69", "family": "ES pre-FOMC drift (2 MES, 09:31 -> 13:55)", "prereg_sha": "76e8b531",
                                                   "result": "FAIL: -0.15 $/day, 2/5 folds, excess < 0, plateau fails (54 events)", "status": "REJECT", "utc": K.now()}], key="test")
    K.reg_append("TEST65_PLUS_REJECT_REGISTRY", [{"family": "es_pre_fomc_drift", "test": "TEST69", "reason": "no drift 2019-2026 (win 41%), excess < 0",
                                                 "retest_forbidden": "YES", "reopen_requires": "-"}], key="family")
    for t, h, m, note in (("TEST65", 11, 9, "gap map categories + walk-forward detectability logits"), ("TEST66", 10, 1, "early opening trend + ML meta-label"),
                          ("TEST67", 5, 0, "ES turn-of-month"), ("TEST68", 6, 4, "secondary breakout ML"), ("TEST69", 5, 0, "pre-FOMC")):
        P.budget(t, hypotheses=h, ml_configs=m, genomes=0, finalists=0, note=note)
    B = pd.read_csv(P.REG["RESEARCH_BUDGET_LOG"])
    F = pd.read_csv(K.REG["T61_INCREMENTAL_PORTFOLIO_FRONTIER"])
    qa = json.load(open(os.path.join(K.LAB, "out", "forward_shadow_qa", "FORWARD_SHADOW_QA.json")))
    man = json.load(open(os.path.join(K.LAB, "frozen", "t61_r1c", "T61_R1C_MANIFEST.json")))
    best = F.sort_values("incr_avg_day", ascending=False).iloc[0]
    st = {"T61_R1C_FROZEN": "YES", "T61_R1C_MANIFEST_SHA256": open(os.path.join(K.LAB, "frozen", "t61_r1c", "T61_R1C_MANIFEST.sha256")).read().split()[0],
          "T61_R1C_HISTORICAL_AVG_DAY": 125.08, "T61_R1C_MAXDD": 12607, "T61_R1C_WORST_DAY": -4347, "T61_R1C_PEAK_MNQ": 6, "T61_R1C_PEAK_MES": 6,
          "T61_FORWARD_OOS_START": "2026-09-29",
          "FORWARD_SHADOW_HARNESS_READY": bool(qa["PREFIX_INVARIANT"] and qa["REPRODUCES_FROZEN_HISTORY"] and qa["FAIL_CLOSED_ON_TAMPER"]),
          "FORWARD_SHADOW_QA": qa,
          "TEST65": "MAP: T61 flat states have negative forward drift (exposure timing already efficient); largest residual = opening trend (AUC 0.58)",
          "TEST66": "FAIL early opening-trend (rule -0.41 $/day; ML +1.96 $/day, no plateau)",
          "TEST67": "FAIL ES turn-of-month (+3.77 $/day; plateau / ret-DD fail)",
          "TEST68": "FAIL MNQ secondary breakout ML (-0.65 $/day)",
          "TEST69": "FAIL ES pre-FOMC drift (-0.15 $/day)",
          "STOPPING_CRITERION": "B: >= 4 distinct families after TEST65 failed (early opening trend, ES calendar flow, secondary breakout, ES event drift)",
          "NEW_ADDITIVE_SURVIVOR": "NONE", "BEST_NEW_MODULE (non-passing, by incremental $/day)": best.module,
          "BEST_NEW_MODULE_INCR_AVG_DAY": round(float(best.incr_avg_day), 2), "CORR_NEW_MODULE_TO_T61": round(float(best.corr_to_t61), 3),
          "T61_PLUS_NEW_MODULE": "n/a (no survivor)", "INCREMENTAL_AVG_DAY_OVER_T61": 0.0, "PEAK_MARGIN": "T61-R1C 30.6% NLV (unchanged)",
          "PEAK_MES": 6, "PEAK_MNQ": 6, "NEW_MODULE_OOS_START": "n/a",
          "GA_RUN": "NO (method order: GA only with signal; none found)",
          "BUDGET_TOTALS": {"hypotheses": int(B.hypotheses.sum()), "ml_configs": int(B.ml_configs.sum()), "valid_genomes": int(B.valid_genomes.sum())},
          "T61_OOS_DATA_USED_FOR_RESEARCH": "NO", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"}
    K.jdump(st, os.path.join(K.OUT, "TEST65_PLUS_FINAL_STATUS.json"))
    reg = lambda n: pd.read_csv(K.REG[n])
    K.md("TEST65_PLUS_00_FINAL_REPORT.md", "TEST65+ additive-alpha program - final report",
         ["```json\n" + json.dumps(st, indent=1, default=str) + "\n```", "## Incremental frontier (T61-R1C + module)", F.round(3),
          "## Research registry", reg("TEST65_PLUS_RESEARCH_REGISTRY"), "## Rejects", reg("TEST65_PLUS_REJECT_REGISTRY"), "## Clues", reg("TEST65_PLUS_CLUE_REGISTRY")])
    pd.DataFrame(columns=["module", "status"]).to_csv(K.REG["TEST65_PLUS_SURVIVOR_LIBRARY"], index=False) if not os.path.exists(K.REG["TEST65_PLUS_SURVIVOR_LIBRARY"]) else None
    print(json.dumps(st, indent=1, default=str))
