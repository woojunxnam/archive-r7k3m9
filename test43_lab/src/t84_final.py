"""TEST84+ final status: auction-profile / momentum-follow / press-winner lanes."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402

R = lambda t, f: pd.read_csv(os.path.join(A.AP, t, f))


def main():
    Q = json.load(open(os.path.join(A.AP, "TEST84", "TEST84_VOLUME_QA.json"))); PF = R("TEST84", "TEST84_PREFIX_INVARIANCE.csv")
    P = R("TEST85", "T85_PROFILE_ATLAS.csv"); M = R("TEST85", "T85_MOMENTUM_ATLAS.csv"); TR = R("TEST85", "T85_HVN_TRAVEL.csv"); DC = R("TEST85", "T85_DECAY_EXIT.csv")
    T86 = R("TEST86", "TEST86_RESULTS.csv"); T91 = R("TEST91", "TEST91_RESULTS.csv"); PW = R("TEST94_PRESS_WINNER", "T94_PRESS_GRID.csv")
    RTH = ["h30", "h60", "h1100", "h1300", "h1600", "h1615"]

    def best(df, inst, ev, proxy=None):
        x = df[(df.instrument == inst) & (df.event == ev) & df.horizon.isin(RTH)]
        if proxy:
            x = x[x.proxy == proxy]
        if not len(x):
            return "n/a"
        r = x.loc[x.B.idxmax()]
        return f"{inst} {ev} [{r.proxy} {r.horizon}] net {r.net:+.2f}, SLIP4 {r.net4:+.2f}, B(momentum) {r.B:+.2f}, C(volume) {getattr(r, 'C', float('nan')):+.2f}, {int(r.folds_B_pos)}/5, n {int(r.n)}"
    both = lambda df, ev: " | ".join(best(df, i, ev) for i in ("MNQ", "ES"))
    pg = T86[(T86.mechanism == "PG12_DOWN_STACK") & (T86.entry == "IMMEDIATE")].iloc[0]; pi = T86[(T86.mechanism == "PI_DIVERGE") & (T86.entry == "IMMEDIATE")].iloc[0]
    ml = T91[(T91.mechanism == "PG12_DOWN_STACK") & (T91.model == "HGB (PRIMARY)")].iloc[0]
    pwa = PW.groupby("instrument")[["ADD1_MARGINAL_EV", "ADD2_MARGINAL_EV", "ADD3_MARGINAL_EV", "loser_avg_max_units", "winner_avg_max_units", "big_winner_avg_max_units",
                                    "giveback_fraction", "win_rate", "payoff", "expectancy", "avg_day", "pyramid_vs_frontload_day", "pyramid_vs_constant1_day"]].median()
    bp = PW.sort_values("avg_day", ascending=False).iloc[0]
    s = {"T61_R1C_FROZEN": "YES", "T61_OOS_USED_IN_RESEARCH": "NO",
         "TEST84_RESULT": f"QA PASS: prefix invariance {int(PF.checked.sum())} samples / {int(PF.mismatches.sum())} mismatches; ES full-contract volume clean; NQ signal = MNQ volume PROXY",
         "TEST85_RESULT": "ATLAS: 2 profile mechanisms qualify (MNQ PG12_DOWN_STACK 16:00 / 30m, MNQ PI_DIVERGE 60m; >= 2/3 proxies); 0 momentum mechanisms qualify; "
                          "ES PH_PRICE_NULL (next open) excluded as a null of a rejected family",
         "TEST86_RESULT": f"FAIL: PG12 {pg.avg_day:+.2f} $/day (5/5 folds, SLIP4 {pg.slip4_day:+.2f}) plateau fails at 60m hold + year share {pg.max_year_share:.2f}; "
                          f"PI_DIVERGE {pi.avg_day:+.2f} $/day plateau fails; T61 increments {pg.t61_incr_day:+.2f} / {pi.t61_incr_day:+.2f} < +10",
         "TEST87_RESULT": "NOT RUN: POC migration (PA1 / PA2 / PC1 / PC2) did not qualify at TEST85",
         "TEST88_RESULT": "NOT RUN: HVN / LVN travel (PD / PE) did not qualify (profile target exits negative)", "TEST89_RESULT": "NOT RUN: prior-VAH acceptance (PB1-PB4) did not qualify",
         "TEST90_RESULT": "NOT RUN: rising-POC pullback (PF) did not qualify",
         "TEST91_RESULT": f"ML-B (economic target) on the 2 qualifying events: PG12 HGB {ml.avg_day:+.2f} $/day ({ml.avg_day_2021:+.2f} 2021+), 5/5 folds, 8/9 models standalone-pass, "
                          f"T61 increment {ml.t61_incr_day:+.2f} < +10 -> not a survivor; PI_DIVERGE <= +2.3 $/day",
         "TEST92_RESULT": "NOT RUN: GA not justified (no deterministic survivor)", "TEST93_RESULT": "no survivor to add; T61 incremental gates computed inside TEST86 / TEST91",
         "PROFILE_DATA_QUALITY": f"ES zero-volume {Q[1]['zero_volume_share']:.3%}, missing {Q[1]['missing_price_share']:.3%}, {Q[1]['abnormal_volume_days']} abnormal days, "
                                 f"{Q[1]['roll_sessions']} roll sessions (roll/non-roll volume {Q[1]['roll_vs_nonroll_volume_ratio']:.2f}); MNQ volume grows ~10x 2019->2026 (proxy only)",
         "BEST_VOLUME_ALLOCATION_PROXY": "VP-B uniform-range (PG12); VP-B / VP-C agree closely, VP-A (single price) differs",
         "PROXY_ROBUSTNESS": "PG12 qualifies under VP-A and VP-B (VP-C misses only the 40-per-fold sample by 1); PI_DIVERGE under VP-A and VP-C at 60m; all other mechanisms fail in every proxy",
         "BEST_PROFILE_TYPE": "P2 developing vs P1 prior RTH (value stacking)", "BEST_VALUE_AREA": "70% (65 / 75 neighbours positive and >= 60% of base for PG12)",
         "POC_MIGRATION_EXCESS": both(P, "PA1_POC_UP") + " || developing: " + both(P, "PC1_DPOC_UP"),
         "VALUE_ACCEPTANCE_EXCESS": both(P, "PB3_VAH_TWO") + " || accept: " + both(P, "PB4_VAH_ACCEPT"),
         "LVN_TRAVEL_EXCESS": both(P, "PD_HVN_LVN_TRAVEL") + " || LVN break: " + both(P, "PE_LVN_BREAK"),
         "HVN_TARGET_VALUE": "NEGATIVE: exit at next HVN " + ", ".join(f"{r.instrument}/{r.proxy} {r.target_exit:+.1f}" for r in TR.itertuples()) + " vs hold 16:15 "
                             + ", ".join(f"{r.instrument}/{r.proxy} {r.hold1615:+.1f}" for r in TR.itertuples()) + " $/trade",
         "VALUE_STACKING_EXCESS": both(P, "PG12_DOWN_STACK") + " || up-stack: " + both(P, "PG_UP_STACK"),
         "PROFILE_COMPRESSION_EXCESS": both(P, "PH_VALUE_COMPRESS_EXPAND") + " || PRICE-RANGE NULL: " + both(P, "PH_PRICE_NULL") + " -> value compression adds nothing over price range",
         "PRICE_POC_CONFIRMATION_EXCESS": both(P, "PI_PRICE_POC_CONFIRM") + " || divergence: " + both(P, "PI_DIVERGE") + " -> opposite of the hypothesis",
         "PROFILE_VS_GENERIC_MOMENTUM": "B excess mostly small positive but fails costs / folds; only PG12 and PI_DIVERGE beat momentum robustly at event level",
         "PROFILE_VS_GENERIC_VOLUME": "C (relative-volume matched) excess tracks B -> raw volume level does not explain the profile events",
         "BEST_ENTRY": "IMMEDIATE (one-bar acceptance similar; no plateau for it)", "BEST_HOLD": "16:00 (PG12) / 60m (PI_DIVERGE)",
         "ES_PROFILE_RESULT": "NONE", "NQ_PROFILE_RESULT": "NONE (MNQ-volume proxy; PG12 clue)",
         "TRADES_PER_DAY": round(pg.trades_per_day, 3), "SIDES_PER_DAY": round(pg.sides_per_day, 3), "SLIP4_AVG_DAY": round(pg.slip4_day, 2),
         "ML_RUN": "YES (TEST91, 18 configs)", "GA_RUN": "NO", "NEW_PROFILE_SURVIVOR": "NONE",
         "T61_PLUS_PROFILE_AVG_DAY": round(pg.t61_comb_avg_day, 2), "T61_PLUS_PROFILE_INCREMENTAL_DAY": round(pg.t61_incr_day, 2), "T61_PLUS_PROFILE_MAXDD": round(pg.t61_comb_maxdd),
         "T61_PLUS_PROFILE_WORST_DAY": round(pg.t61_comb_worst), "T61_PLUS_PROFILE_RET_DD": round(pg.t61_comb_ret_dd, 5), "CORR_PROFILE_TO_T61": round(pg.corr_to_t61, 3),
         "PROFILE_MODULE_OOS_START": "n/a (no survivor)",
         # momentum lane
         "MOMENTUM_FAMILY_RESULT": "NO QUALIFYING MECHANISM (0 of 23 event types x 2 instruments pass net + SLIP4 + momentum-null + folds + n>=300)",
         "BEST_MOMENTUM_MECHANISM": best(M, "MNQ", "M68_DECEL", "PRICE") + " (n < 300 -> not qualifying)",
         "OPENING_IMPULSE_VALUE": both(M, "M1_OPEN_IMPULSE") + " -> MNQ value = generic momentum (B < 0)",
         "PERSISTENCE_VALUE": both(M, "M3_PERSIST") + " || one-time: " + both(M, "M3_ONE_TIME"),
         "SECOND_IMPULSE_VALUE": both(M, "M5_SECOND_IMPULSE"), "FAILED_PULLBACK_RESUMPTION_VALUE": both(M, "M6_FAILED_PULLBACK"),
         "MULTITIMEFRAME_ALIGNMENT_VALUE": both(M, "M7_MTF_5_15_60") + " (alignment adds ~0)", "ES_NQ_CONFIRMATION_VALUE": both(M, "M8_AGREE") + " || diverge: " + both(M, "M8_DIVERGE"),
         "MOMENTUM_DECAY_EXIT_VALUE": "; ".join(f"{r.instrument}: VWAP-loss exit {r.decay_exit_net:+.2f} vs hold {r.hold_net:+.2f} $/trade" for r in DC.itertuples()),
         "PRICE_PLUS_VOLUME_VALUE": " | ".join(best(M, "MNQ", "M9_PRICE_VALUE", px) for px in ("VP-A", "VP-B", "VP-C")),
         "PRICE_ONLY_MOMENTUM_VALUE": best(M, "MNQ", "M9_PRICE_ONLY", "VP-B"),
         "INCREMENTAL_VALUE_OF_VOLUME_CONFIRMATION": "NOT ROBUST (sign flips across proxies: VP-A positive, VP-B / VP-C negative)",
         "BEST_MOMENTUM_HOLD": "16:00 / 16:15", "BEST_MOMENTUM_ENTRY_SPEED": "immediate (no delayed-confirmation variant beat it)",
         "MOMENTUM_TRADES_PER_DAY": "n/a (no strategy)", "MOMENTUM_SLIP4_AVG_DAY": "n/a", "NEW_MOMENTUM_SURVIVOR": "NONE",
         **{k: "n/a (no momentum survivor)" for k in ("T61_PLUS_MOMENTUM_AVG_DAY", "T61_PLUS_MOMENTUM_INCREMENTAL_DAY", "T61_PLUS_MOMENTUM_MAXDD", "T61_PLUS_MOMENTUM_WORST_DAY",
                                                       "T61_PLUS_MOMENTUM_RET_DD", "CORR_MOMENTUM_TO_T61")},
         # press-winner lane
         "PRESS_WINNER_BASE_SIGNAL": "M1_OPEN_IMPULSE (NON-PROMOTABLE DIAGNOSTIC: no qualifying momentum base)",
         "BEST_PRESS_LADDER": f"{bp.ladder} ({bp.instrument} {bp.trigger} {bp.speed} spacing {bp.spacing} {bp.exit}: {bp.avg_day:+.2f} $/day, remove-top3 {bp.remove_top3_day:+.0f})",
         "BEST_ADD_TRIGGER": "D_VALUE_ACCEPT (least negative marginal adds; ES ADD1 +0.2, MNQ ADD1 -7.3 median)", "BEST_ADD_SPEED": "SLOW (least negative)", "BEST_ADD_SPACING": "0.25 ATR (least negative)",
         **{f"ADD{k}_MARGINAL_EV": {i: round(pwa.loc[i, f"ADD{k}_MARGINAL_EV"], 2) for i in pwa.index} for k in (1, 2, 3)},
         "LOSER_AVG_MAX_UNITS": pwa.loser_avg_max_units.round(2).to_dict(), "WINNER_AVG_MAX_UNITS": pwa.winner_avg_max_units.round(2).to_dict(),
         "BIG_WINNER_AVG_MAX_UNITS": pwa.big_winner_avg_max_units.round(2).to_dict(), "NO_ADD_TO_LOSER_VIOLATIONS": int(PW.violations.sum()),
         "CUT_LOSER_VALUE": "R1 (reduce to probe on VWAP loss) vs R0 (full exit): median MNQ " + f"{PW[(PW.instrument == 'MNQ') & (PW.exit == 'R1')].avg_day.median():+.2f} vs "
                            f"{PW[(PW.instrument == 'MNQ') & (PW.exit == 'R0')].avg_day.median():+.2f} $/day", "BEST_REDUCTION_POLICY": "R1 (MNQ), no difference (ES)",
         "AVG_WINNER / AVG_LOSER": "see T94_PRESS_GRID.csv", "WIN_RATE": pwa.win_rate.round(3).to_dict(), "PAYOFF_RATIO": pwa.payoff.round(2).to_dict(),
         "CAMPAIGN_EXPECTANCY": pwa.expectancy.round(2).to_dict(), "GIVEBACK_FRACTION": pwa.giveback_fraction.round(2).to_dict(),
         "PRESS_WINNER_AVG_DAY": pwa.avg_day.round(2).to_dict(), "PRESS_WINNER_MAXDD / WORST / SLIP4": "see grid (best config fails remove-top3)",
         "PYRAMID_VS_FRONTLOAD_EXCESS": pwa.pyramid_vs_frontload_day.round(2).to_dict(), "PYRAMID_VS_CONSTANT_EXCESS": pwa.pyramid_vs_constant1_day.round(2).to_dict(),
         "RTH_PRESS_VALUE": "NEGATIVE / ~0", "OVERNIGHT_FULL_PRESS_VALUE": "NOT RUN (RTH press failed)", "OVERNIGHT_TRIM_VALUE": "NOT RUN",
         "PRICE_PLUS_VOLUME_ADD_VALUE": "D_VALUE_ACCEPT least negative but still <= 0 in MNQ", "ML_ADDS_VALUE (press)": "NOT RUN (no positive marginal add EV)", "GA_ADDS_VALUE (press)": "NOT RUN",
         **{k: "n/a" for k in ("T61_PLUS_PRESS_AVG_DAY", "T61_PLUS_PRESS_INCREMENTAL_DAY", "T61_PLUS_PRESS_MAXDD", "T61_PLUS_PRESS_WORST_DAY", "T61_PLUS_PRESS_RET_DD", "CORR_PRESS_TO_T61")},
         "NEW_PRESS_WINNER_SURVIVOR": "NONE",
         "STOPPING_CRITERION": "B + C: value migration, value acceptance, POC movement, HVN / LVN traversal, profile compression, price / POC confirmation and all momentum-follow "
                               "families fail matched-momentum economics or the +10 $/day increment; press-winner adds have negative marginal EV",
         "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    Bd = pd.read_csv(os.path.join(A.AP, "PROFILE_RESEARCH_BUDGET.csv"))
    A.budget("TEST85", hypotheses=int(P.groupby(["instrument", "event", "proxy", "horizon"]).ngroups + M.groupby(["instrument", "event", "proxy", "horizon"]).ngroups), note="atlas cells")
    Bd = pd.read_csv(os.path.join(A.AP, "PROFILE_RESEARCH_BUDGET.csv"))
    s["PROGRAM_BUDGET"] = {"hypotheses": int(Bd.hypotheses.sum()), "ml_configs": int(Bd.ml_configs.sum()), "genomes": 0}
    s["CUMULATIVE_BUDGET"] = {"hypotheses": 1702 + s["PROGRAM_BUDGET"]["hypotheses"], "ml_configs": 207 + s["PROGRAM_BUDGET"]["ml_configs"], "genomes": 777629}
    json.dump(s, open(os.path.join(A.AP, "TEST84_PLUS_FINAL_STATUS.json"), "w"), indent=1, default=str)
    # registries
    tests = {k: v for k, v in s.items() if k.startswith("TEST") and k.endswith("_RESULT")}
    A.reg_append("PROFILE_RESEARCH_REGISTRY", [{"test": k.replace("_RESULT", ""), "result": v} for k, v in tests.items()]
                 + [{"test": "TEST94_PRESS_WINNER", "result": "diagnostic: adds negative marginal EV; pyramid < frontload / constant"}], key="test")
    A.reg_append("PROFILE_REJECT_REGISTRY", [
        {"family": "POC / value migration long", "reason": "fails costs / folds vs momentum null"}, {"family": "prior-VAH acceptance long", "reason": "B small, SLIP4 < 0"},
        {"family": "HVN -> LVN travel with HVN target", "reason": "target exits negative; hold version 3/5 folds"},
        {"family": "LVN break", "reason": "n too small (MNQ 105) / ES < 300"}, {"family": "value compression -> expansion", "reason": "price-range null better"},
        {"family": "price / POC confirmation", "reason": "confirmation not qualifying; divergence qualifies but fails plateau"},
        {"family": "value stacking PG12_DOWN_STACK (deterministic + ML)", "reason": "plateau (60m hold) / year share; ML +6 $/day < +10 increment"},
        {"family": "momentum-follow M1-M10, M68", "reason": "no qualifying cell (momentum null / sample / costs)"},
        {"family": "press-winner pyramiding on M1", "reason": "negative marginal add EV; worse than frontload / constant"}], key="family")
    A.reg_append("PROFILE_CLUE_REGISTRY", [
        {"clue_id": "PG12_DOWN_STACK", "clue": f"MNQ, 12:00 developing value below prior value -> long to 16:00: +{pg.usd_per_trade:.1f} $/trade, 5/5 folds, SLIP4 positive, ML meta-selection "
                                             f"consistent (+{ml.avg_day_2021:.1f} $/day 2021+, 8/9 models); REBOUND-PROXIMATE; forward monitor only"},
        {"clue_id": "PI_DIVERGE", "clue": "new session high WITHOUT developing POC following -> 60m continuation (+4.4 $/trade, 5/5 folds) - opposite of the confirmation hypothesis"},
        {"clue_id": "HVN_TARGET_BAD_EXIT", "clue": "profile HVN targets are bad exits (same lesson as box tops)"},
        {"clue_id": "M68_DECEL", "clue": "MNQ second hour weaker than first (both up) -> 16:00 +36.6 $/event, B +21.5, 4/5, n 257 (sample < 300)"},
        {"clue_id": "PRESS_NO_CONVEX_EDGE", "clue": "adding after market proof on M1 has negative marginal EV; exposure convexity achieved (losers ~1.2-1.8 units) but adds lose"}], key="clue_id")
    PR = P.groupby(["instrument", "event", "horizon"]).agg(proxies_B_pos=("B", lambda v: int((v > 0).sum())), proxies_ok=("cell_ok", "sum")).reset_index()
    PR["MODEL_OF_VOLUME_DEPENDENT"] = (PR.proxies_B_pos > 0) & (PR.proxies_B_pos < 2)
    PR.to_csv(os.path.join(A.AP, "PROFILE_PROXY_ROBUSTNESS.csv"), index=False)
    if not os.path.exists(os.path.join(A.AP, "PROFILE_SURVIVOR_LIBRARY.csv")):
        pd.DataFrame(columns=["module", "status"]).to_csv(os.path.join(A.AP, "PROFILE_SURVIVOR_LIBRARY.csv"), index=False)
    A.md("TEST84_PLUS_00_FINAL_REPORT.md", "TEST84+ AUCTION-PROFILE / MOMENTUM-FOLLOW / PRESS-WINNER - final report", ["```json\n" + json.dumps(s, indent=1, default=str) + "\n```"])
    print(json.dumps(s, indent=1, default=str))


if __name__ == "__main__":
    main()
