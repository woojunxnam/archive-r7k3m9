"""TEST78+ BOX-MOMENTUM INVERSION LAB - final status (no mechanism qualified at TEST78; TEST79-83 not run by preregistration)."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402

O = os.path.join(B.BOX, "TEST78")


def main():
    P = pd.read_csv(os.path.join(O, "T78_POOLED.csv")); C = pd.read_csv(os.path.join(O, "T78_CONDITIONING.csv"))
    q = lambda i, e, h="h1600": P[(P.instrument == i) & (P.event == e) & (P.horizon == h)].iloc[0]
    f = lambda e, h="h1600": "; ".join(f"{i} matched {q(i, e, h).matched_x_per_event:+.2f} / momentum-null {q(i, e, h).momentum_x_per_event:+.2f} $/event "
                                       f"({int(q(i, e, h).folds_mom_pos)}/5 folds, net {q(i, e, h).net_per_event:+.2f}, SLIP4 {q(i, e, h).net4_per_event:+.2f}, n {int(q(i, e, h).n)})"
                                       for i in ("MNQ", "ES")) + f" [{h}]"
    s2 = q("MNQ", "SEQ2")
    nr = "NOT RUN: no upper-state mechanism qualified in TEST78 (preregistered rule 1dda59d7)"
    st = {"TEST78_RESULT": "ATLAS: 0 qualifying (event x instrument x horizon) cells of 160; upper-zone touch / acceptance / break / retest are POSITIVE vs "
                           "matched-long but NEGATIVE vs the generic-momentum null in MNQ -> value = ordinary momentum; only the rising sequence (SEQ2) is "
                           "box-positive vs momentum but fails fold recurrence (MNQ 3/5) or SLIP4 (ES)",
          "TEST79_RESULT": nr, "TEST80_RESULT": nr, "TEST81_RESULT": nr, "TEST82_RESULT": nr, "TEST83_RESULT": "NOT RUN: no standalone survivor",
          "UPPER_TOUCH_MATCHED_EXCESS": f("A1_TOUCH"), "UPPER_ACCEPTANCE_MATCHED_EXCESS": f("A2_CLOSE") + " | two closes: " + f("A3_TWO_CLOSES"),
          "UPPER_BREAK_MATCHED_EXCESS": f("BRK10") + " | BRK20: " + f("BRK20"), "OLD_TOP_RETEST_MATCHED_EXCESS": f("U4_RETEST"),
          "RISING_BOX_SEQUENCE_EXCESS": f("SEQ2") + " | A4 rising: " + f("A4_RISING"),
          "BOX_VS_GENERIC_MOMENTUM_EXCESS": "NEGATIVE or ~0 for touch / acceptance / break / retest (MNQ -0.7..-4.2 $/event at 16:00); positive only for SEQ2 "
                                            "(MNQ +3.37, ES +1.76) without fold / cost robustness -> the box adds no robust information beyond generic momentum",
          "BEST_ENTRY_MECHANISM": "SEQ2 (two consecutive rising box midpoints + upper-zone close), MNQ - NOT qualifying",
          "BEST_HOLD_HORIZON": "16:00 (16:15 and next-open weaker vs the momentum null)", "BEST_INSTRUMENT": "MNQ",
          "TRADES_PER_DAY": f"strategy not run; SEQ2 MNQ event rate {s2.per_day:.2f}/day pooled over 3 geometries",
          "SIDES_PER_DAY": f"strategy not run; ~{2 * s2.per_day:.2f}/day at event rate", "SLIP4_AVG_DAY": f"strategy not run; SEQ2 MNQ SLIP4 {s2.net4_per_event:+.2f} $/event",
          "NEW_UPPER_BOX_SURVIVOR": "NONE", "T61_PLUS_MODULE_AVG_DAY": "n/a (T61 alone 125.08)", "T61_PLUS_MODULE_INCREMENTAL_DAY": 0.0,
          "T61_PLUS_MODULE_MAXDD": "n/a (T61 12,607)", "T61_PLUS_MODULE_WORST_DAY": "n/a (T61 -4,347)", "T61_PLUS_MODULE_RET_DD": "n/a (T61 0.00992)",
          "CORR_MODULE_TO_T61": "n/a", "MODULE_OOS_START": "n/a",
          "KEY_ANSWERS": {"upper box location a real long signal?": "only as generic momentum (positive raw / matched-long, not beyond the momentum null)",
                          "better than generic momentum?": "NO (except the non-robust SEQ2 subset)",
                          "touch vs acceptance?": "no difference of economic consequence (A1 ~ A2 ~ A3)",
                          "breakout better than upper-zone entry?": "NO - breaks are worse vs momentum (MNQ BRK10 -3.71 $/event at 16:00)",
                          "old-top support retest?": "NO - worst mechanism (MNQ -4.22, ES -1.34 vs momentum)",
                          "rising box sequences?": "directionally YES (SEQ2 best everywhere) but not robust (3/5 folds MNQ; ES fails costs)",
                          "width contraction / expansion?": "contraction does NOT help (MNQ A2 contracting -2.36 vs momentum); expanding +1.65 (3/5)",
                          "hold horizon?": "16:00; 5-60 min horizons are negative after costs", "adds to T61?": "not evaluated - no standalone survivor"},
          "STOPPING_CRITERION": "B + C: touch, acceptance, breakout, retest and rising-sequence mechanisms all failed the preregistered qualification; "
                                "upper-state value is explained by generic momentum", "ML_RUN": "NO (not justified)", "GA_RUN": "NO (not justified)",
          "T61_OOS_USED_FOR_RESEARCH": "NO", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    vz = C[(C.instrument == "MNQ") & (C.event == "A2_CLOSE") & (C.horizon == "h1600") & (C.vel_class == "NEAR_ZERO")].iloc[0]
    B.reg_append("BOX_RESEARCH_REGISTRY", [{"test": "TEST78", "family": "upper-state event atlas (box momentum inversion)", "prereg": "1dda59d7", "result": st["TEST78_RESULT"]}] +
                 [{"test": t, "family": fam, "prereg": "1dda59d7", "result": nr} for t, fam in (("TEST79", "upper-state long"), ("TEST80", "upper-break hold policy"),
                                                                                                  ("TEST81", "old-top support retest"), ("TEST82", "rising box sequence"))] +
                 [{"test": "TEST83", "family": "box momentum overlay on T61", "prereg": "1dda59d7", "result": st["TEST83_RESULT"]}], key="test")
    B.reg_append("BOX_REJECT_REGISTRY", [
        {"family": "upper-zone touch / acceptance long", "tests": "TEST78", "reason": "momentum-null excess < 0 (MNQ); = generic momentum", "retest_forbidden": "YES"},
        {"family": "upper-box breakout long", "tests": "TEST78", "reason": "momentum-null excess < 0 in both instruments at every horizon", "retest_forbidden": "YES"},
        {"family": "old-top support-flip retest", "tests": "TEST78", "reason": "worst mechanism vs momentum null", "retest_forbidden": "YES"}], key="family")
    B.reg_append("BOX_CLUE_REGISTRY", [
        {"clue_id": "BOX_UPPER_IS_MOMENTUM", "source": "TEST78", "clue": "the TEST70 top-hold clue is reproduced vs matched-long but disappears vs a session-return-matched momentum null"},
        {"clue_id": "BOX_SEQ2_RISING_SEQUENCE", "source": "TEST78", "clue": f"two consecutive rising box midpoints + upper-zone close: MNQ 16:00 momentum excess {s2.momentum_x_per_event:+.2f} $/event, "
                                                                           f"net {s2.net_per_event:+.2f}, 3/5 folds, n {int(s2.n)}; directionally consistent, not robust - forward monitor only"},
        {"clue_id": "BOX_VEL_NEAR_ZERO_A2", "source": "TEST78 conditioning (NOT preregistered as a mechanism)", "clue": f"MNQ A2 in NEAR_ZERO velocity boxes 16:00: momentum excess "
                                                                                                                      f"{vz.momentum_x_per_event:+.2f}, {int(vz.folds_mom_pos)}/5 folds, n {int(vz.n)} - subgroup discovery, "
                                                                                                                      "multiple-comparison exposed, no rescue"}], key="clue_id")
    B.budget("TEST78", hypotheses=160, note="10 event types x 8 horizons x 2 instruments (pooled over 4 geometries) + conditioning diagnostics")
    Bd = pd.read_csv(os.path.join(B.BOX, "BOX_RESEARCH_BUDGET.csv"))
    st["CUMULATIVE_PROGRAM_BUDGET"] = {"hypotheses": 1394 + int(Bd.hypotheses.sum()), "ml_configs": 189 + int(Bd.ml_configs.sum()), "genomes": 777629}
    json.dump(st, open(os.path.join(B.BOX, "TEST78_PLUS_FINAL_STATUS.json"), "w"), indent=1, default=str)
    cols = ["instrument", "event", "horizon", "n", "net_per_event", "net4_per_event", "matched_x_per_event", "momentum_x_per_event", "folds_mom_pos", "qualifies"]
    B.md("TEST78_UPPER_STATE_ATLAS.md", "TEST78 - upper-state event atlas (box momentum inversion)", ["Preregistered 1dda59d7.", P[cols].round(2)])
    B.md("TEST78_PLUS_00_FINAL_REPORT.md", "TEST78+ BOX-MOMENTUM INVERSION LAB - final report", ["```json\n" + json.dumps(st, indent=1, default=str) + "\n```"])
    print(json.dumps(st, indent=1, default=str))


if __name__ == "__main__":
    main()
