"""TEST70+ ADAPTIVE BOX LAB - registries and final status (stopping criterion B / C)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402

R = lambda t, f: pd.read_csv(os.path.join(B.BOX, t, f))


def main():
    A = R("TEST70", "BOX_GEOMETRY_ATLAS.csv"); T71 = R("TEST71", "TEST71_RESULTS.csv"); T72 = R("TEST72", "TEST72_RESULTS.csv")
    P72 = pd.concat([R("TEST72", f"TEST72_POLICY_TABLE_{i}.csv") for i in ("MNQ", "ES")]); T73 = R("TEST73", "TEST73_RESULTS.csv")
    DR = R("TEST73", "TEST73_BOX_DIRECTION_EDGE.csv"); T74 = R("TEST74", "TEST74_RESULTS.csv"); T76 = R("TEST76", "TEST76_ML_A_RESULTS.csv")
    C76 = R("TEST76", "TEST76_ML_C_TOP_HOLD.csv"); TOP = R("TEST70", "ATLAS_TOP_HOLD_STUDY.csv")
    for t, why in (("TEST75", "NOT RUN: no standalone box configuration passed (program rule: overlay only if standalone economics positive)"),
                   ("TEST77", "NOT RUN: GA not justified (no deterministic net-positive family; ML adds no value)")):
        json.dump({"status": why}, open(os.path.join(B.BOX, t, f"{t}_STATUS.json"), "w"), indent=1)
    best = T71.sort_values("avg_day", ascending=False).iloc[0]
    th = TOP[TOP.hold == "h1615"].groupby("instrument")[["hold_incr_raw", "hold_incr_excess"]].median()
    g = lambda df, inst, col, **kw: float(df[(df.instrument == inst) & np.all([df[k] == v for k, v in kw.items()], axis=0)][col].iloc[0])
    t73 = lambda inst, lab: float(T73[(T73.instrument == inst) & (T73.config == f"T73_TREND_{lab}")].avg_day.iloc[0])
    st = {"T61_R1C_FROZEN": "YES", "T61_FORWARD_OOS_START": "2026-09-29", "T61_OOS_USED_IN_BOX_RESEARCH": "NO",
          "TEST70_RESULT": f"ATLAS: 0/88 geometry x instrument cells eligible (>= 4/5 folds matched excess AND SLIP4 excess > 0); {int((A.net_day > 0).sum())}/88 net-positive "
                           f"(max {A.net_day.max():.2f} $/day); lower-zone touches break the floor before the top ~80% of the time",
          "TEST71_RESULT": f"FAIL: 18 configs, 0 pass; best {best.config} {best.instrument} {best.avg_day:.2f} $/day; recycling cycles 2-3 lose "
                           f"{T71.cycle2plus_net_per_trade.max():.1f}..{T71.cycle2plus_net_per_trade.min():.1f} $/trade",
          "TEST72_RESULT": f"FAIL: all 18 migration policies net negative (MNQ {P72[P72.instrument == 'MNQ'].avg_day.max():.2f}..{P72[P72.instrument == 'MNQ'].avg_day.min():.2f}, "
                           f"ES {P72[P72.instrument == 'ES'].avg_day.max():.2f}..{P72[P72.instrument == 'ES'].avg_day.min():.2f} $/day)",
          "TEST73_RESULT": f"FAIL: trend ladder gross ~0 before costs; D trailing MNQ {t73('MNQ', 'D_TRAILING'):.2f}, ES {t73('ES', 'D_TRAILING'):.2f} $/day",
          "TEST74_RESULT": "FAIL: alignment raises matched excess per event slightly (small+medium) but net stays negative; maximal confluence worst",
          "TEST75_RESULT": "NOT RUN (no standalone survivor)",
          "TEST76_RESULT": "FAIL: first run VOID (look-ahead feature 'life', documented); corrected primary HGB MNQ "
                           f"{g(T76, 'MNQ', 'avg_day', model='HGB (PRIMARY)'):.2f}, ES {g(T76, 'ES', 'avg_day', model='HGB (PRIMARY)'):.2f} $/day; 0/16 models pass",
          "TEST77_RESULT": "NOT RUN (GA not justified)",
          "BEST_BOX_GEOMETRY": f"{best.geometry} ({best.instrument}) - best traded config, NOT a survivor", "BEST_BOX_OBSERVATION_WINDOW": "none (anchor = prior RTH close)",
          "BEST_BOX_LIFETIME": "full RTH session (static)", "BEST_BOX_WIDTH_ATR": 0.375, "BEST_LOWER_ZONE": "0.00-0.15", "BEST_UPPER_ZONE": "0.85-1.00",
          "BOTTOM_TOUCH_MATCHED_EXCESS": f"median over 88 cells {A.excess_per_event.median():.2f} $/event ({A.excess_day.median():.2f} $/day); best cells +1..+4 $/event, always below round-trip friction (MNQ 2.24 / ES 3.74 $)",
          "TOP_EXIT_INCREMENTAL_VALUE": f"NEGATIVE: holding from TOP to 16:15 adds (median, $/event) MNQ raw {th.loc['MNQ', 'hold_incr_raw']:.2f} / matched {th.loc['MNQ', 'hold_incr_excess']:.2f}, "
                                        f"ES raw {th.loc['ES', 'hold_incr_raw']:.2f} / matched {th.loc['ES', 'hold_incr_excess']:.2f}",
          "TOP_FULL_EXIT_VALUE": f"MNQ {t73('MNQ', 'A_TOP_EXIT'):.2f}, ES {t73('ES', 'A_TOP_EXIT'):.2f} $/day (TEST73 A)",
          "TOP_HOLD_VALUE": f"MNQ {t73('MNQ', 'C_HOLD'):.2f}, ES {t73('ES', 'C_HOLD'):.2f} $/day (TEST73 C)",
          "TRAILING_BOX_VALUE": f"MNQ {t73('MNQ', 'D_TRAILING'):.2f}, ES {t73('ES', 'D_TRAILING'):.2f} $/day (TEST73 D)",
          "BEST_UPPER_BREAK_POLICY": "UP2 REBUILD (least negative in both instruments)", "BEST_LOWER_BREAK_POLICY": "MNQ DOWN3 (stable fresh box), ES DOWN1 (all negative)",
          "BEST_MIGRATION_POLICY": f"MNQ UP2+DOWN3 {T72[T72.instrument == 'MNQ'].avg_day.iloc[0]:.2f} $/day, ES UP2+DOWN1 {T72[T72.instrument == 'ES'].avg_day.iloc[0]:.2f} $/day (no survivor)",
          **{f"{d}_BOX_EDGE": "; ".join(f"{i} {g(DR, i, 'avg_day', dir=d):.2f} $/day (excess {g(DR, i, 'excess_day', dir=d):.2f})" for i in ("MNQ", "ES")) for d in ("RISING", "FLAT", "FALLING")},
          "RANGE_RECYCLE_AVG_DAY": f"MNQ {T72[T72.instrument == 'MNQ'].avg_day.iloc[0]:.2f}, ES {T72[T72.instrument == 'ES'].avg_day.iloc[0]:.2f}",
          "TREND_LADDER_AVG_DAY": f"MNQ {t73('MNQ', 'D_TRAILING'):.2f}, ES {t73('ES', 'D_TRAILING'):.2f}",
          "MULTI_BOX_ALIGNMENT_VALUE": "; ".join(f"{r.instrument} {r.variant} {r.net_day:.2f} $/day (x/event {r.excess_per_event:.2f})" for r in T74.itertuples()),
          "ES_BOX_RESULT": "NONE", "MNQ_BOX_RESULT": "NONE", "BOX_CLASSIFICATION": "NONE",
          "BOX_TRADES_PER_DAY": round(best.trades_per_day, 3), "BOX_CONTRACT_SIDES_PER_DAY": round(best.contract_sides_per_day, 3),
          "BOX_FRICTION_PER_DAY": round(best.commission_day + best.slippage_day, 3),
          "BEST_BOX_STANDALONE_AVG_DAY": round(best.avg_day, 3), "BEST_BOX_MATCHED_EXCESS_DAY": round(best.excess_day, 3), "BEST_BOX_MAXDD": round(best.max_dd, 1),
          "BEST_BOX_WORST_DAY": round(best.worst_day, 1), "BEST_BOX_SLIP4_AVG_DAY": round(best.slip4_day, 3),
          "ML_ADDS_ECONOMIC_VALUE": "NO", "GA_RUN": "NO", "GA_ADDS_ECONOMIC_VALUE": "n/a", "NEW_BOX_SURVIVOR": "NONE",
          "T61_PLUS_BOX_AVG_DAY": "n/a (no survivor; T61 alone 125.08)", "T61_PLUS_BOX_INCREMENTAL_DAY": 0.0, "T61_PLUS_BOX_MAXDD": "n/a (T61 12,607)",
          "T61_PLUS_BOX_WORST_DAY": "n/a (T61 -4,347)", "T61_PLUS_BOX_RET_DD": "n/a (T61 0.00992)", "CORR_BOX_TO_T61": "n/a",
          "PEAK_MARGIN_T61_PLUS_BOX": "n/a (T61 30.6%)", "PEAK_MES_T61_PLUS_BOX": "n/a (T61 6)", "PEAK_MNQ_T61_PLUS_BOX": "n/a (T61 6)",
          "BOX_MODULE_OOS_START": "n/a",
          "STOPPING_CRITERION": "B + C: >= 4 distinct geometry / migration families (fixed-window, ATR, swing, balance, quantile, packing, VWAP, session; range recycle, "
                                "migration, trend ladder, nested) show no robust net value; the only positive quantity (matched excess ~ +1-3 $/event) is smaller "
                                "than round-trip friction; ML adds nothing once look-ahead is removed; GA not justified",
          "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"}
    Bd = pd.read_csv(os.path.join(B.BOX, "BOX_RESEARCH_BUDGET.csv"))
    st["BOX_BUDGET"] = {"hypotheses": int(Bd.hypotheses.sum()) + (0 if "TEST70" in set(Bd.test) else 88), "ml_configs": int(Bd.ml_configs.sum()), "genomes": 0}
    st["CUMULATIVE_PROGRAM_BUDGET"] = {"hypotheses": 1394 + st["BOX_BUDGET"]["hypotheses"], "ml_configs": 189 + st["BOX_BUDGET"]["ml_configs"], "genomes": 777629}
    if "TEST70" not in set(pd.read_csv(os.path.join(B.BOX, "BOX_RESEARCH_BUDGET.csv")).test):
        B.budget("TEST70", hypotheses=88, note="atlas 44 geometries x 2 instruments")
    json.dump(st, open(os.path.join(B.BOX, "BOX_FINAL_STATUS.json"), "w"), indent=1, default=str)
    # registries
    rs = [("TEST70", "box geometry atlas (10 families, 44 geometries x 2)", "455ffc57", st["TEST70_RESULT"]), ("TEST71", "simple box B0 + recycling", "see TEST71", st["TEST71_RESULT"]),
          ("TEST72", "box migration UP1-3 x DOWN1-3", "5e5339f6", st["TEST72_RESULT"]), ("TEST73", "trend box ladder A/C/D", "a1775b27", st["TEST73_RESULT"]),
          ("TEST74", "nested box alignment", "459e0e8e", st["TEST74_RESULT"]), ("TEST75", "T61 overlay", "-", st["TEST75_RESULT"]),
          ("TEST76", "box ML (economic targets)", "db69545e", st["TEST76_RESULT"]), ("TEST77", "box GA", "-", st["TEST77_RESULT"])]
    B.reg_append("BOX_RESEARCH_REGISTRY", [{"test": t, "family": f, "prereg": h, "result": r} for t, f, h, r in rs], key="test")
    B.reg_append("BOX_REJECT_REGISTRY", [
        {"family": "static / tiled box bottom-buy (A,C,E,F,G,I)", "tests": "TEST70/71", "reason": "net < 0 in 82/88 cells; excess < friction", "retest_forbidden": "YES"},
        {"family": "rolling / swing / balance box bottom-buy (B,D,H)", "tests": "TEST70/71", "reason": "net < 0; H_BAL6 excess 5/5 folds but -4.9 $/day net", "retest_forbidden": "YES"},
        {"family": "range recycling (cycles 2-3)", "tests": "TEST71", "reason": "cycles >= 2 lose 2-15 $/trade", "retest_forbidden": "YES"},
        {"family": "stateful box migration (UP1-3 x DOWN1-3)", "tests": "TEST72", "reason": "all policies net negative", "retest_forbidden": "YES"},
        {"family": "trend box ladder (rising-box pullback, hold / trailing)", "tests": "TEST73", "reason": "gross ~0 before costs", "retest_forbidden": "YES"},
        {"family": "nested box confluence", "tests": "TEST74", "reason": "net negative; confluence reduces sample without edge", "retest_forbidden": "YES"},
        {"family": "box ML meta-selection", "tests": "TEST76", "reason": "0/16 pass after look-ahead removal", "retest_forbidden": "YES"}], key="family")
    B.reg_append("BOX_CLUE_REGISTRY", [
        {"clue_id": "BOX_TOP_NOT_EXIT", "source": "TEST70 top-hold study", "clue": st["TOP_EXIT_INCREMENTAL_VALUE"] + " -> upper box is NOT an exit edge (drift)"},
        {"clue_id": "BOX_ZONE_MOMENTUM", "source": "TEST70 zone study", "clue": "MNQ forward net to 16:15 rises monotonically with box position (upper zones best): location = momentum, not mean reversion"},
        {"clue_id": "BOX_EXCESS_LT_FRICTION", "source": "TEST70/71", "clue": "bottom touches beat time-matched longs by ~+1-3 $/event but a round trip costs 2.24 (MNQ) / 3.74 (ES) $"},
        {"clue_id": "BOX_FALLING_TO_RISING", "source": "BOX_TRANSITION_MATRIX", "clue": "MNQ FALLING->RISING transition bottom buys +1.5 $/event excess (median over geometries); too small"},
        {"clue_id": "BOX_LEAKAGE_LESSON", "source": "TEST76", "clue": "box lifetime / death is look-ahead for break-terminated boxes; any future box feature must be birth-time only"}], key="clue_id")
    if not os.path.exists(os.path.join(B.BOX, "BOX_SURVIVOR_LIBRARY.csv")):
        pd.DataFrame(columns=["module", "status"]).to_csv(os.path.join(B.BOX, "BOX_SURVIVOR_LIBRARY.csv"), index=False)
    if not os.path.exists(os.path.join(B.BOX, "BOX_T61_INCREMENTAL_FRONTIER.csv")):
        pd.DataFrame([{"module": "none", "note": "TEST75 not run - no standalone survivor"}]).to_csv(os.path.join(B.BOX, "BOX_T61_INCREMENTAL_FRONTIER.csv"), index=False)
    cols = ["instrument", "geometry", "events", "net_day", "excess_day", "excess4_day", "top_before_break", "folds_excess_pos", "score_fold_median_excess_day"]
    B.md("TEST70_BOX_GEOMETRY_ATLAS.md", "TEST70 - box geometry atlas", ["Preregistered 455ffc57. Ranking = matched economic excess; hit rates are diagnostics.",
                                                                      A[cols].sort_values("score_fold_median_excess_day", ascending=False).round(3)])
    B.md("TEST75_T61_OVERLAY.md", "TEST75 - T61 overlay", [st["TEST75_RESULT"]]); B.md("TEST77_BOX_GA.md", "TEST77 - box GA", [st["TEST77_RESULT"]])
    B.md("BOX_00_FINAL_REPORT.md", "TEST70+ ADAPTIVE BOX / RANGE-LADDER ALPHA LAB - final report", ["```json\n" + json.dumps(st, indent=1, default=str) + "\n```"])
    print(json.dumps(st, indent=1, default=str))


if __name__ == "__main__":
    main()
