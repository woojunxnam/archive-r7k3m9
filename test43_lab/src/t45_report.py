"""TEST45 deliverables T45_00..T45_27 (markdown + machine-readable status) generated from the frozen outputs."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402

T = C.T45
R = C.REP
pd.set_option("display.float_format", lambda v: f"{v:.3f}")


def rd(p, **k):
    return pd.read_csv(os.path.join(T, p), **k)


def tbl(df, cols=None, n=None, r=3):
    d = df if cols is None else df[[c for c in cols if c in df.columns]]
    if n:
        d = d.head(n)
    return d.round(r)


def main():
    os.makedirs(R, exist_ok=True)
    fz = json.load(open(f"{T}/freeze/TEST45_PRE_OOS_FREEZE.json"))
    hf = open(f"{T}/freeze/TEST45_PRE_OOS_FREEZE.sha256").read().split()[0]
    hr = open(f"{T}/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.sha256").read().split()[0]
    base = rd("baseline/T45_00_baseline_reproduction.csv")
    qa = json.load(open(f"{T}/baseline/T45_00_baseline_qa.json"))
    tsq = rd("session/T45_timestamp_qa.csv")
    seg = rd("session/T45_01_segments.csv"); segy = rd("session/T45_01_segments_by_year.csv")
    carry = rd("session/T45_02_carry_controls.csv"); carryp = rd("session/T45_02_carry_by_period.csv")
    lock = rd("session/T45_17_lock_risk.csv"); lockw = rd("session/T45_17_worst_locks.csv")
    late = rd("morning/T45_03_late_features.csv"); gap = rd("morning/T45_04_gap_buckets.csv"); fl = rd("morning/T45_05_flush.csv")
    mx = rd("morning/T45_06_matrix.csv"); inv = rd("morning/T45_07_inventory.csv"); cx = rd("morning/T45_16_cross_index.csv")
    det = rd("det/T45_08_overlays.csv"); detp = rd("det/T45_08_overlays_by_period.csv")
    ml = rd("ml/T45_10_model_walkforward.csv"); mla = rd("ml/T45_11_model_ablation.csv"); mlr = rd("ml/T45_10_regime_states.csv")
    mls = json.load(open(f"{T}/ml/T45_09_model_zoo_spec.json"))
    gas = json.load(open(f"{T}/ga/T45_12_ga_spec.json")); gsel = rd("ga/T45_13_ga_selected.csv")
    gps = json.load(open(f"{T}/gp/T45_15_gp_spec.json")); gpsel = rd("gp/T45_15_gp_selected.csv")
    nof = rd("final/T45_13_nested_outer_folds.csv"); obc = rd("final/T45_outer_block_comparison.csv")
    rec = rd("final/T45_13_ga_recurrence.csv"); scon = rd("final/T45_13_ga_selected_concepts.csv")
    bcor = pd.read_csv(f"{T}/final/T45_13_ga_selected_behaviour_corr.csv", index_col=0)
    gpl = rd("final/T45_14_ga_fold_plateau.csv"); gfp = rd("final/T45_14_ga_final_plateau.csv")
    gfin = json.load(open(f"{T}/final/T45_ga_gp_final.json"))
    comb = rd("final/T45_19_module_combination.csv"); scal = rd("final/T45_19_20_combination_scaling.csv"); per = rd("final/T45_21_22_periods.csv")
    v6 = rd("final/T45_v6_state_carry_family.csv"); aud = rd("final/T45_24_candidate_rule_audit.csv")
    sel = json.load(open(f"{T}/final/T45_24_final_selection.json"))
    ch = base[base.candidate == "CHAMPION_CONTROL_V1"].iloc[0]
    ga_st = obc[obc.candidate == "GA_NESTED_STITCHED"].iloc[0]; gpc_st = obc[obc.candidate == "GP_CLOSE_NESTED_STITCHED"].iloc[0]
    gpm_st = obc[obc.candidate == "GP_MORNING_NESTED_STITCHED"].iloc[0]
    trees = ["RANDOM_FOREST", "EXTRA_TREES", "HIST_GB", "XGBOOST", "LIGHTGBM", "CATBOOST"]
    mA = ml[(ml.task == "A_CARRY") & (ml.features == "ALL_NO_REGIME")]
    best_lin = mA[mA.model.isin(["RIDGE", "ELASTIC_NET", "LOGISTIC"])].sort_values("rankIC").iloc[-1]
    best_tree = mA[mA.model.isin(trees)].sort_values("rankIC").iloc[-1]
    ga_folds_pos = int((nof[nof.method == "GA"].outer_avg > 0).sum())
    NOTE_IS = ("**Warning:** rows labelled `GA|FINAL` / `GP|*|FINAL` / `best GA/GP overlay` were evolved on ALL data <= 2026-05-27, so their "
               "block numbers are IN-SAMPLE and are not evidence. The out-of-sample evidence for GA/GP is the NESTED STITCHED series "
               "(each outer block traded by the genome evolved without that block).")
    CAUSAL = ("**Causality fix recorded:** the first pass used the Champion position of the 16:12 bar as a feature at decision times "
              "14:30-16:00. That is look-ahead. It was found before selection. Every stage (T45_03, 08-26) was re-run with the Champion "
              "position in effect at the decision minute. All numbers here are post-fix.")
    # --------------------------------------------------------------------------------------------- reports
    C.md("T45_00_AUTHORITY_AND_BASELINE_QA.md", "T45_00 Authority and baseline QA", [
        "Research data: canonical 1m ES/MNQ (hash-verified), session_date <= 2026-05-27 only. Nothing after 2026-05-27 was acquired or opened.",
        "Authorities (sha256 verified, unchanged):", pd.DataFrame(qa["authority_hashes"]).T,
        "Frozen controls re-run through 2026-05-27 with the frozen TEST44 code. Daily P&L and positions reproduce the frozen outputs **exactly** (max abs diff 0.0):",
        tbl(base, ["candidate", "daily_pnl_max_abs_diff", "ALL_total", "ALL_avg", "ALL_max_dd", "ALL_worst", "FH_total", "FH_avg", "FH_max_dd", "FH_worst", "peak_margin_util"]),
        f"CHAMPION_CONTROL_V1: full history ${ch.ALL_total:,.0f} ({ch.ALL_avg:.2f}/day, MaxDD ${ch.ALL_max_dd:,.0f}); former TEST43 holdout "
        f"(USED data) ${ch.FH_total:,.2f} ({ch.FH_avg:.2f}/day, MaxDD ${ch.FH_max_dd:,.0f}, worst ${ch.FH_worst:,.0f}).", CAUSAL])
    C.md("T45_01_SESSION_RETURN_DECOMPOSITION.md", "T45_01 Session return decomposition (descriptive)", [
        "Timestamp QA (addendum 9). Canonical bars are END-stamped. The bar stamped HH:MM covers [HH:MM-1, HH:MM).", tbl(tsq),
        "Segments: points per contract, $ per 1 MES / 1 MNQ, and prior-session RTH-ATR units. `C LOCKED 16:15 -> next 09:30` is the actual return of locked inventory. `16:00 -> next 09:30` is for comparison only.",
        tbl(seg, ["inst", "segment", "n", "mean_pts", "median_pts", "pos_share", "std_pts", "t_stat", "mean_atr", "mean_$1c", "p1_$1c", "worst_$1c", "MFE_mean_atr", "MAE_mean_atr"]),
        "By year (mean ATR units / $ per contract):", tbl(segy.pivot_table(index=["inst", "segment"], columns="period", values="mean_$1c").reset_index(), r=2)])
    C.md("T45_02_CLOSE_TO_OPEN_PREMIUM.md", "T45_02 Close-to-open premium (simple controls)", [
        "+1 contract decided at T (fill at the open of bar T+1), locked, exited by a pre-planned order at the next RTH open print. Costs: commission + 1 tick per side plus roll.",
        tbl(carry, ["control", "avg", "total", "max_dd", "worst", "matched_beta_excess", "session_matched_beta_excess", "cost", "incr_avg", "incr_max_dd", "corr_champion"]),
        "By period (+1/+1; decision at 15:45 and 16:14):", tbl(carryp, ["control", "period", "avg", "total", "max_dd", "worst", "session_matched_beta_excess"]),
        "Reading: the locked premium is positive gross (ES ~$5.8, MNQ ~$11.7 per contract per night) but not significant (t 1.5-1.8). "
        "Costs remove most of the ES premium. Matched-beta excess is negative (it is beta, not alpha). 2022 is strongly negative."])
    C.md("T45_03_LATE_RTH_FEATURES.md", "T45_03 Late-RTH features vs locked overnight target", [
        "Features are known at the decision minute. The target is (next RTH open - fill at T+1)/ATR. Stability = sign of rank-IC over the pre-2021 block and the 5 outer blocks.",
        tbl(late.reindex(late.rankIC.abs().sort_values(ascending=False).index), ["inst", "decision", "feature", "n", "IC", "rankIC", "q5_minus_q1_atr",
                                                                                   "block_rankIC_same_sign_share", "block_rankIC_min", "block_rankIC_max"], n=40),
        "The strongest and most stable information is the frozen Champion's own state (champ_pos_at_t) for MNQ. Late momentum reverses weakly (mom15/mom60 < 0 -> better night)."])
    C.md("T45_04_GAP_DOWN_REBOUND.md", "T45_04 Gap-down rebound (H1/H2/H5)", [
        "Decision at 09:31 (open known), fill 09:32. Buckets were predeclared and not searched. Columns: forward return in ATR units, t, net $ per contract, recovery probabilities, MAE.",
        tbl(gap, ["inst", "gap", "norm", "bucket", "n", "+15m_atr", "+60m_atr", "to 12:00_atr", "to 16:00 close_atr", "to 16:00 close_t", "to 16:00 close_net$",
                  "p_touch_prior_ref", "p_recover_50%_gap", "p_recover_100%_gap", "median_min_to_50%", "MAE_atr"]),
        "Answer: no monotonic rebound. Moderate down-gaps give small positive, insignificant drift. ES gaps below -1.5 ATR continue down "
        "(-0.20 ATR to the close; recovery probability falls). That is a crash/trend regime (H5). MNQ extreme buckets are too small (n<=11)."])
    C.md("T45_05_OPENING_FLUSH_REBOUND.md", "T45_05 Opening flush -> rebound (H3/H4)", [
        "The decision is taken only after the observation window completes; fill at the next bar.",
        tbl(fl, ["inst", "window", "state", "n", "+30m_atr", "+60m_atr", "to 12:00_atr", "to 16:00 close_atr", "to 16:00 close_t", "to 16:00 close_net$",
                 "p_close_above_open", "p_recover_50%_gap"]),
        "Answer: larger post-open selloffs do not show reliable rebound expectancy. Extreme gap + extreme flush is negative (crash regime). "
        "Isolated positive cells (e.g. ES 15m selloff -0.5..-0.8 ATR, n=19) are small-sample."])
    C.md("T45_06_GAP_FLUSH_MATRIX.md", "T45_06 Gap x flush matrix", [
        "Target: fill 10:01 -> 16:00 (ATR). Cells with n < 20 are flagged. ETA2 rows give between-cell variance explained; the 't' column there is df-adjusted ETA2.",
        tbl(mx), "Answer: the combined state explains no more than either alone once cell counts are adjusted (adjusted ETA2 ~0). The large-gap/large-flush corner is negative."])
    C.md("T45_07_OPEN_INVENTORY_MANAGEMENT.md", "T45_07 Open inventory management", [
        "An existing overnight long (1 contract). Value of each action relative to EXIT at the open print ($ per contract, net of incremental cost).",
        tbl(inv, ["inst", "state", "action_vs_EXIT_AT_OPEN", "n", "mean$", "median$", "t", "p5$", "worst$"]),
        "Answer: after a favourable gap, exit at the open. After an extreme adverse gap, keeping into late morning was positive for MNQ (t~2 at "
        "30m-12:00; n~84). This is a single-cell observation. As overlay S6b it did not pass the account-level tests (T45_08/24)."])
    C.md("T45_08_DETERMINISTIC_OVERLAYS.md", "T45_08 Deterministic overlays S0-S6 and CONTROL_A-E", [
        "Thresholds were predeclared (gap <= -0.5 ATR, 30m selloff <= -0.3 ATR, crash guard -1.5 ATR). S5b and S5c were informed by T45_03 and are marked. "
        "Every overlay trades in the same account as the unchanged Champion.",
        tbl(det, ["name", "avg", "total", "max_dd", "worst", "matched_beta_excess", "session_matched_beta_excess", "incr_avg", "incr_max_dd", "corr_champion",
                  "loss_day_overlap", "SLIP4_total", "blk_PRE_2021", "blk_O1_2021", "blk_O2_2022", "blk_O3_2023", "blk_O4_2024", "blk_O5_2025_26"]),
        "Answer: gap/flush controls earn about $0-2/day and are not additive. Unconditional carry adds $/day but raises the combined MaxDD sharply and loses in 2022."])
    C.md("T45_09_MODEL_ZOO_SPEC.md", "T45_09 Model zoo specification", [
        f"Walk-forward: FIRST_TRAIN {mls['FIRST_TRAIN']} sessions, blocks {mls['BLOCK']}, purge {mls['PURGE']}. Session-level pooled ES+MNQ rows. Targets clipped at +/-3 ATR.",
        f"Models (one broad regularised preset each, no search): {', '.join(mls['models'])}; HMM (3-state Gaussian, causal filtered posteriors, refit per block).",
        "Tasks: A overnight carry (15:45 -> next open), B gap rebound (09:31 -> 16:00), C opening flush (10:00 -> 16:00), D open inventory "
        "(09:31 -> 12:00), E regime (HMM posterior feature + state table). Deep NNs were not used.",
        "Features per task:", pd.DataFrame([{"task": k, "features": ", ".join(v)} for k, v in mls["features"].items()]),
        "Mapping to trades: POS1 = +1 if prediction > 0; POS2 = +2 above the expanding 80th percentile of past predictions. Every mapping runs through the same integer overlay engine."])
    C.md("T45_10_MODEL_WALKFORWARD.md", "T45_10 Model walk-forward", [
        tbl(ml, ["task", "model", "features", "n_oof", "IC", "rankIC", "top_minus_bottom_tercile_atr", "calibration_slope", "block_rankIC_pos_share",
                 "POS1_avg", "POS1_max_dd", "POS1_session_matched_beta_excess", "POS1_incr_max_dd", "POS1_outer_blocks_min", "POS2_avg", "POS2_max_dd"]),
        "HMM regime states (calm -> volatile): mean target by causal most-likely state.", tbl(mlr),
        f"Answer: morning tasks B/C/D have rank-IC <= ~0 for every family. Carry task A: best linear {best_lin.model} rank-IC {best_lin.rankIC:.3f}; "
        f"best tree {best_tree.model} rank-IC {best_tree.rankIC:.3f}. Neither beats the unconditional carry on combined return/DD. "
        "The HMM separates regimes: carry works in the calm state and the morning rebound in the volatile state. The effect is too weak to trade after costs."])
    C.md("T45_11_MODEL_ABLATION.md", "T45_11 Model ablation (drop one feature family)", [
        "Families: G gap, L late-RTH, F opening flush, X ES/NQ relative, S V6/Champion state, V volatility, T trend.", tbl(mla),
        "Answer: for carry, dropping S (Champion state) or G/V removes most of the value. Other families are noise."])
    C.md("T45_12_GA_SPEC.md", "T45_12 Genetic algorithm specification", [
        f"Island-model NSGA-II (own implementation: constrained non-dominated sort + crowding): {len(gas['SEEDS'])} seeds x {gas['ISLANDS']} islands x "
        f"pop {gas['POP']} x {gas['GENS']} generations. Ring migration of {gas['N_MIG']} after generation {gas['MIG_EVERY']}.",
        f"Unique genomes evaluated: **{gas['unique_genomes_total']:,}** (per fold: {gas['unique_per_fold']}), within the 250k limit.",
        "Nested chronological validation: for outer blocks 2021, 2022, 2023, 2024 and 2025-01..2026-05-27, evolution sees ONLY sessions before the block. "
        "A final run on all data uses the identical procedure.",
        "Objectives (minimised): -median inner-fold $/day, -worst inner-fold $/day, training MaxDD, -session-matched-beta excess, complexity. "
        "Constraints: >=30 active sessions, sides/day <= 4, |corr Champion| <= 0.6. Whole-history P&L is NOT an objective.",
        "Predeclared selection per outer fold: feasible rank-0 members with worst inner fold > 0; maximise median_inner / max(MaxDD, 1000); tie-break lower complexity.",
        "Genome space (overlay only, V6 never evolved):", pd.DataFrame(gas["space"], columns=["gene", "type", "domain"]),
        f"Frozen lock governor: {gas['lock_governor']}. QMAX {gas['QMAX']} per symbol."])
    C.md("T45_13_GA_PARETO_FRONTIER.md", "T45_13 GA Pareto frontier, nested outer folds, recurrence", [
        "Selected genome per fold (ranks 0-4) with inner and OUTER performance:",
        tbl(gsel, ["fold", "sel_rank", "inner_median", "inner_worst", "train_mdd", "complexity", "outer_avg", "outer_max_dd", "outer_session_matched_beta_excess",
                   "outer_corr_champion", "degradation_outer_minus_inner_median"]),
        "Nested outer folds (rank 0):", tbl(nof.drop(columns=["genome_or_rule"])),
        f"Stitched nested GA: outer median ${ga_st.outer_median:.2f}/day, {int(ga_st.outer_pos)}/5 blocks > 0. Champion+GA return/DD "
        f"{ga_st.comb_ret_dd:.4f} vs Champion {ga_st.champ_ret_dd:.4f} (2021-2026 span).",
        "Concept recurrence over 36 independent runs (6 folds x 2 seeds x 3 islands); a concept is present in a run if >= 25% of that run's final front uses it:",
        tbl(rec.sort_values("runs_with>=25%_of_front", ascending=False), n=40), "Concepts of the selected genomes:", tbl(scon),
        "Behavioural correlation of the selected genomes (full-history daily P&L):", bcor.round(2),
        "Answer: the only concept that recurs across folds, seeds and islands is a CLOSE module: flat base, +1 locked when the "
        "Champion is long in that instrument (champ_pos>). Morning genes do not recur consistently."])
    C.md("T45_14_GA_NEIGHBORHOOD_ROBUSTNESS.md", "T45_14 GA neighbourhood robustness", [
        "Perturbations: each active continuous gene at -20/-10/+10/+20% (+/-0.05 near 0), plus adjacent discrete times. "
        "PASS requires every perturbation to keep avg > 0 and >= 50% of base, and MaxDD <= 1.5 x base.",
        "Outer-fold selections (on their own training window):", tbl(gpl), f"Final GA genome plateau pass: {gfin['GA_FINAL']['plateau_pass']}",
        tbl(gfp), "Answer: GENETIC_PARAMETER_PLATEAU_PASS = NO. Only 1 of 5 fold selections is a plateau; the final genome has cliff-like genes."])
    C.md("T45_15_GENETIC_PROGRAMMING.md", "T45_15 Genetic programming (restricted rule structure)", [
        f"Primitives: {gps['primitives']}. Max depth {gps['MAX_DEPTH']}, <= {gps['MAX_NODES']} nodes. Parsimony = node count as an objective. "
        f"Morning inputs {gps['morning_inputs']}. Close inputs {gps['close_inputs']}. No date/weekday/month/year/contract/raw-price inputs.",
        f"Unique programs: {gps['unique_programs_total']:,}. Nested outer folds are identical to GA.",
        tbl(gpsel[gpsel.sel_rank == 0], ["fold", "kind", "rule", "inner_median", "inner_worst", "train_mdd", "outer_avg", "outer_max_dd",
                                           "outer_session_matched_beta_excess", "outer_corr_champion"]),
        f"Stitched nested GP_CLOSE: outer median ${gpc_st.outer_median:.2f}/day, {int(gpc_st.outer_pos)}/5 > 0, combined ret/DD {gpc_st.comb_ret_dd:.4f}. "
        f"GP_MORNING: median ${gpm_st.outer_median:.2f}, {int(gpm_st.outer_pos)}/5.",
        "Answer: GP_CLOSE rediscovers `current_V6_intensity > 0/1` in every fold (the same concept as GA). GP_MORNING evolves momentum "
        "filters (no selloff), not rebounds, and does not generalise. GP adds no value over GA."])
    C.md("T45_16_ES_NQ_CROSS_INDEX.md", "T45_16 ES/NQ cross-index information", [
        "OLS (HC1) of each target on own-instrument state, with and without ES/NQ relative terms. Chronological yearly out-of-sample R2:", tbl(cx, r=4),
        "ES-NQ differential segment returns are in T45_01. Relative (X) features in ML ablation: T45_11.",
        "Answer: ES_NQ_RELATIVE_STATE_ADDS_VALUE = NO. Out-of-sample R2 is not improved (one marginal exception: MNQ flush; both OOS R2 < 0)."])
    C.md("T45_17_OVERNIGHT_LOCK_RISK.md", "T45_17 Overnight lock risk (16:15 -> next 09:30)", [
        "No overnight stop exists. Distribution of the locked return ($) by position, plus the report-only mark-to-market excursion during the lock "
        "(the path is NEVER a feature) and IBKR-scaled overnight margin.", tbl(lock, r=1), "Worst locked nights:", tbl(lockw, r=2),
        "Answer: 1 contract per symbol is inside the account envelope (1 MES worst -$1,170, 1 MNQ -$2,006, 1+1 -$3,176). 2 MNQ or 2+2 "
        "(-$4,011 / -$6,351 worst, p0.5 -$3.1k for 2+2) breaks the -$3,000 worst-day gate on its own, before the Champion's own P&L."])
    C.md("T45_18_INTEGER_EXECUTION.md", "T45_18 Integer execution", [
        "All modules -> one desired MES and one desired MNQ state -> frozen lock governor -> one integer target per symbol (0/1/2; 3 only as a scaling diagnostic). "
        "No module sends its own order. The overlay is a separate virtual sleeve. Broker net target = Champion target + overlay target.",
        "Execution clock (frozen):", pd.DataFrame([fz["execution_clock"]]).T,
        "Fill fallbacks: entries use forward fills <= 3 min and are otherwise skipped. Reductions may use <= 15 min, or the last bar on an early close. "
        "A position carried into a contract-switch session pays a 2-side roll during RTH before the lock."])
    C.md("T45_19_MODULE_COMBINATION.md", "T45_19 Module combination with the Champion", [NOTE_IS, tbl(comb, r=4),
         "Answer: combinations of the predeclared modules do not improve the Champion's return/DD. Only in-sample evolved overlays look better, and nested evidence does not confirm them."])
    C.md("T45_20_SCALING_FRONTIER.md", "T45_20 Scaling frontier (cap 1 / 2 / 3; 3 is diagnostic only)", [NOTE_IS,
         tbl(scal, ["candidate", "cap", "avg", "max_dd", "worst", "comb_avg", "comb_mdd", "comb_ret_dd", "incr_avg", "corr", "worst_locked_night_$", "max_contracts",
                    "avg_locked_contracts", "SLIP4_total", "outer_median", "outer_pos"]),
         "HOW MUCH VALIDATED HISTORICAL ALPHA DID TEST45 ADD? None that passes the predeclared bar. The best nested out-of-sample evidence (GA stitched) "
         f"adds ${ga_st.incr_avg:.1f}/day on 2021-2026 at a WORSE combined return/DD ({ga_st.comb_ret_dd:.4f} vs {ga_st.champ_ret_dd:.4f}).",
         "WHAT IS MISSING FOR ~$600/DAY: the Champion earns ~$53-59/day. $600/day at the same return/DD needs ~11x the risk, which is not acceptable. "
         "Several independent sources, each ~$50+/day with correlation < 0.3, would be needed. TEST45 found the session effects (gap, flush, open "
         "inventory, cross-index) to be ~0 after cost. Overnight carry is beta, and its only robust conditional form is an intensification of the "
         "Champion's own overnight leg (correlation 0.5-0.6), not a new source."])
    C.md("T45_21_2020_2022_STRESS.md", "T45_21 2020 / 2022 stress", [
        tbl(per[per.period.isin(["Y2020", "Y2022"])], ["candidate", "period", "overlay_avg", "champ_avg", "comb_avg", "champ_mdd", "comb_mdd", "comb_worst", "corr"]),
        "V6-state carry family (2022 block):", tbl(v6, ["rule", "outer_O2_2022", "Y2022_overlay_avg"], n=120)])
    C.md("T45_22_FORMER_HOLDOUT_DIAGNOSTIC.md", "T45_22 Former TEST43 holdout diagnostic (USED historical data)", [
        "2025-10-01..2026-05-27 is permanently USED data. It is not an untouched test, and no rule was tuned to it.",
        tbl(per[per.period == "FORMER_HOLDOUT_USED"], ["candidate", "overlay_avg", "champ_avg", "comb_avg", "champ_mdd", "comb_mdd", "comb_worst", "corr"]),
        tbl(v6, ["rule", "FH_overlay_avg"], n=120)])
    ladder = pd.DataFrame([
        {"rung": 1, "method": "Champion", "evidence": "TEST43 one-shot holdout PASS", "comb_ret_dd": ch.ALL_ret_dd, "verdict": "benchmark"},
        {"rung": 2, "method": "simple deterministic (CONTROL_A-D, S1-S6)", "evidence": "fixed rules", "comb_ret_dd": aud[aud.rung == "DET"].comb_ret_dd.max(),
         "verdict": "no eligible rule"},
        {"rung": 2, "method": "V6_STATE_CARRY (GA-recurrence-derived simple rule)", "evidence": "concept in 5/5 nested folds",
         "comb_ret_dd": aud[aud.rung.str.startswith("DET (GA")].comb_ret_dd.max(), "verdict": "best near-misses (R3/R4 or R5); shadow"},
        {"rung": 3, "method": "regularised linear ML", "evidence": "walk-forward", "comb_ret_dd": aud[aud.candidate.str.contains("RIDGE|ELASTIC|LOGISTIC") & (aud.rung == "ML")].comb_ret_dd.max(), "verdict": "fails R2/R4"},
        {"rung": 4, "method": "tree ensembles", "evidence": "walk-forward", "comb_ret_dd": aud[aud.candidate.str.contains("|".join(trees)) & (aud.rung == "ML")].comb_ret_dd.max(), "verdict": "fails R2/R4"},
        {"rung": 5, "method": "regime model (HMM)", "evidence": "walk-forward feature", "comb_ret_dd": aud[aud.candidate.str.contains("HMM")].comb_ret_dd.max(), "verdict": "no added value"},
        {"rung": 6, "method": "numeric GA (nested)", "evidence": "stitched outer folds", "comb_ret_dd": ga_st.comb_ret_dd, "verdict": "fails R2/R4/R5/R6"},
        {"rung": 7, "method": "genetic programming (nested)", "evidence": "stitched outer folds", "comb_ret_dd": gpc_st.comb_ret_dd, "verdict": "fails R5/R6"},
        {"rung": 8, "method": "combined ML + evolved overlay", "evidence": "only in-sample evolutions available", "comb_ret_dd": np.nan, "verdict": "not credible (in-sample)"}])
    C.md("T45_23_COMPLEXITY_LADDER.md", "T45_23 Complexity ladder", [ladder, "Complexity did not earn its place. No rung passes the predeclared rule."])
    C.md("T45_24_FINAL_TEST45_CANDIDATE.md", "T45_24 Final TEST45 candidate", [
        "Predeclared rule (written in `src/t45_07_eval.py` before GA/GP results were inspected):",
        "1. OOS evidence: outer-block median > 0 and >= 4/5 blocks > 0.",
        "2. Champion+overlay return/DD >= Champion.",
        "3. Incremental >= $5/day and |corr| <= 0.5.",
        "4. Combined MaxDD <= $10k and worst day >= -$2.5k.",
        "5. Beats the simplest same-family control on outer median AND combined return/DD.",
        "6. GA/GP: plateau + recurrence.",
        f"Candidates audited: {sel['n_candidates']}; eligible: {sel['n_eligible']}.",
        tbl(aud.sort_values("comb_ret_dd", ascending=False), ["candidate", "rung", "outer_median", "outer_pos", "comb_ret_dd", "champ_ret_dd", "incr_avg", "corr", "comb_mdd",
                                                                "comb_worst", "ctrl_outer_median", "rules_failed"], n=60, r=4),
        f"**FINAL_TEST45_CHALLENGER = {sel['FINAL_TEST45_CHALLENGER']}**",
        "Near misses (one rule failed): " + "; ".join(f"{x['candidate']} ({x['rules_failed']})" for x in sel["near_misses_one_rule"][:6]),
        "Interpretation: MNQ's overnight premium is concentrated on nights when the frozen Champion is long MNQ. Carry on Champion-flat nights "
        "loses about $9/day. This is real historical structure, independently rediscovered by GA and GP in every outer fold. It is, however, an "
        "intensification of the Champion's own overnight leg (corr 0.54-0.64 for champ>0). Its low-correlation variant (champ>1) adds only "
        "~$5-6/day and fails R5 against unconditional carry. It is frozen as SHADOW for forward monitoring and cannot be promoted by the coming OOS.", CAUSAL])
    C.md("T45_25_PRE_OOS_FREEZE.md", "T45_25 Pre-OOS freeze", [f"`out/t45/freeze/TEST45_PRE_OOS_FREEZE.json` sha256 **{hf}**",
                                                               "```json\n" + json.dumps(fz, indent=1, default=str)[:12000] + "\n```"])
    rules = json.load(open(f"{T}/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json"))
    C.md("T45_26_NEW_OOS_ACCEPTANCE_RULES.md", "T45_26 New-OOS acceptance rules", [f"`out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json` sha256 **{hr}**",
                                                                                  "```json\n" + json.dumps(rules, indent=1) + "\n```"])
    status = {
        "CASH_REFERENCE_CLOSE": "16:00:00 ET (close of the 1m bar end-stamped 16:00)",
        "LAST_ALLOWED_EXECUTION": "16:15:00 ET",
        "LAST_CAUSAL_EXECUTION_BAR": "decision on bars end-stamped <= 16:14; fill at the OPEN of the bar end-stamped 16:15",
        "LOCKED_OVERNIGHT_INTERVAL": "16:15-bar-open fill -> next RTH open print (open of bar end-stamped 09:31)",
        "RTH_EXECUTION_WINDOW_CONFIRMED": "YES (09:30-16:15 custom window; fills 09:31..16:15 bar opens; 16:15 bar exists on 98.6% of sessions; pre-2021-06 CME 16:15-16:30 halt makes 16:16 absent)",
        "REFERENCE_RTH_CLOSE": "16:00 cash reference (not 16:15)",
        "OVERNIGHT_PATH_FEATURES_USED": "NO", "OVERNIGHT_HOLDING_ALLOWED": "YES", "OVERNIGHT_TRADING_ALLOWED": "NO",
        "GAP_LOCK_REBOUND_EDGE": "NO", "GAP_CASH_REBOUND_EDGE": "NO", "GAP_DOWN_REBOUND_EDGE": "NO",
        "OPENING_FLUSH_REBOUND_EDGE": "NO", "GAP_PLUS_FLUSH_EDGE": "NO", "GAP_PLUS_FLUSH_ADDS_VALUE": "NO",
        "EXTREME_GAP_CRASH_REGIME_DETECTED": "YES (ES gaps < -1.5 ATR and extreme gap + extreme flush continue lower; MNQ extreme buckets too small)",
        "LATE_RTH_BUILD_ADDS_VALUE": "NO (unconditional); conditional on the Champion's own state: historically yes, but not promotable (T45_24)",
        "16_00_TO_16_15_ADDS_VALUE": "NO (segment mean ES +$1.07 / MNQ +$2.07 per contract, t~1.6, below round-trip cost)",
        "16_15_TO_09_30_PREMIUM_CONFIRMED": "NO as alpha (gross +$5.8 ES / +$11.7 MNQ per contract-night, t 1.5-1.8; negative matched-beta excess; 2022 strongly negative)",
        "CLOSE_TO_OPEN_PREMIUM_CONFIRMED": "NO as alpha (beta premium, not significant)",
        "CONDITIONAL_CLOSE_BOOST_ADDS_VALUE": "NO (R3/R4/R5 failures; best is the Champion-state conditional carry -> shadow)",
        "OPEN_INVENTORY_MANAGER_ADDS_VALUE": "NO",
        "ES_NQ_RELATIVE_STATE_ADDS_VALUE": "NO",
        "OVERNIGHT_LOCK_1_CONTRACT_SAFE_ENOUGH": "YES (1 MES worst -$1,170; 1 MNQ -$2,006; 1+1 -$3,176)",
        "OVERNIGHT_LOCK_2_CONTRACT_SAFE_ENOUGH": "NO (2 MNQ worst -$4,011; 2+2 -$6,351 exceeds the -$3k worst-day gate alone)",
        "BEST_SIMPLE_MODEL": f"{best_lin.model} (task A carry, rank-IC {best_lin.rankIC:.3f})",
        "BEST_TREE_MODEL": f"{best_tree.model} (task A carry, rank-IC {best_tree.rankIC:.3f})",
        "BEST_REGIME_MODEL": "3-state Gaussian HMM (causal): carry positive only in the calm state; no tradeable gain",
        "GENETIC_OUTER_FOLD_GENERALIZATION": f"PARTIAL ({ga_folds_pos}/5 outer folds > 0, median ${ga_st.outer_median:.1f}/day, large inner->outer degradation; combined ret/DD below Champion)",
        "GENETIC_RULE_RECURRENCE": "YES (Champion-state conditional carry: every outer fold, GA and GP)",
        "GENETIC_PARAMETER_PLATEAU_PASS": "NO",
        "GA_ADDS_VALUE_OVER_SIMPLE_RULES": "NO", "GA_ADDS_VALUE_OVER_ML": "NO", "GP_ADDS_VALUE_OVER_GA": "NO", "GENETIC_PROGRAMMING_ADDS_VALUE": "NO",
        "GENETIC_COMPLEXITY_JUSTIFIED": "NO", "ML_ADDS_VALUE_OVER_SIMPLE_RULES": "NO",
        "BEST_PRACTICAL_MAX_MES": "1 (research); 0 adopted - no TEST45 overlay", "BEST_PRACTICAL_MAX_MNQ": "1 (research); 0 adopted - no TEST45 overlay",
        "CHAMPION_HISTORICAL_AVG_DAY": f"{ch.ALL_avg:.2f} (2019-05..2026-05-27; former holdout {ch.FH_avg:.2f})",
        "BEST_TEST45_HISTORICAL_AVG_DAY": f"no adopted overlay; best nested-OOS evidence Champion+GA stitched {ga_st.comb_avg:.2f} vs Champion {ga_st.champ_avg:.2f} on 2021-2026",
        "INCREMENTAL_ALPHA_VS_CHAMPION": "0 adopted (best nested-OOS +%.1f/day at worse return/DD)" % ga_st.incr_avg,
        "BEST_TEST45_MAX_DD": f"n/a (NONE); Champion {ch.ALL_max_dd:,.0f}",
        "FINAL_TEST45_CHALLENGER": sel["FINAL_TEST45_CHALLENGER"],
        "TEST45_PRE_OOS_FREEZE_SHA256": hf, "TEST45_NEW_OOS_RULES_SHA256": hr,
        "TEST44_AUTHORITIES_UNCHANGED": "YES",
        "NEW_OOS_DATA_ACQUIRED": "NO", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    C.jdump(status, f"{T}/T45_final_status.json")
    # hash index (everything TEST45 except the local panel cache)
    files = sorted(set(glob.glob(f"{T}/**/*", recursive=True)) | set(glob.glob(f"{C.SRC}/t45_*.py")) | set(glob.glob(f"{R}/*.md")))
    files = [f for f in files if os.path.isfile(f) and not f.endswith("panel.npz") and not f.endswith(".log") and "T45_27_HASH_INDEX" not in f]
    H = pd.DataFrame([{"file": os.path.relpath(f, C.ROOT), "sha256": C.sha(f), "bytes": os.path.getsize(f)} for f in files])
    H.to_csv(f"{T}/T45_27_HASH_INDEX.csv", index=False)
    C.md("T45_27_HASH_INDEX.md", "T45_27 Hash index", ["Final status:", pd.DataFrame([status]).T, f"{len(H)} files:", H])
    print(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
