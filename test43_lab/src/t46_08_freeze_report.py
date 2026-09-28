"""TEST46 pre-OOS freeze, new-OOS acceptance rules, deliverables T46_00..T46_41, final status and hash index."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t46_common as C  # noqa: E402

T = C.T46
FZ = os.path.join(T, "freeze"); os.makedirs(FZ, exist_ok=True)
AUTH = {"out/t44/freeze/TEST44_PRE_OOS_FREEZE.json": "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4",
        "out/t44/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json": "2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236",
        "out/t45/freeze/TEST45_PRE_OOS_FREEZE.json": "185d1ef91ddffe494ce5826a5142af31644a4816bb2a4db72d110909ed1c2987",
        "out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json": "76941f63465306928e535df74641a29b172c9420c9e0a69852a4f1b0ed5356da"}


def rd(p):
    return pd.read_csv(os.path.join(T, p))


def portfolio(trades, champ_sess):
    daily = trades.groupby("date").e0.sum().reindex(champ_sess).fillna(0.0)
    x = daily.values; eq = np.r_[0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    wk = daily.groupby(pd.DatetimeIndex(daily.index).to_period("W")).sum(); mo = daily.groupby(pd.DatetimeIndex(daily.index).to_period("M")).sum()
    yr = daily.groupby(pd.DatetimeIndex(daily.index).year).sum()
    top = np.sort(trades.e0.values)[::-1]
    return {"trades": int(len(trades)), "net": float(x.sum()), "avg_day": float(x.mean()),
            "PF": float(trades.e0[trades.e0 > 0].sum() / max(-trades.e0[trades.e0 < 0].sum(), 1e-9)),
            "sharpe_ann": float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan, "max_dd": mdd, "worst_day": float(x.min()),
            "pos_week_%": float((wk > 0).mean()), "pos_month_%": float((mo > 0).mean()), "annual": {int(k): round(float(v), 1) for k, v in yr.items()},
            "top5_trade_share_%": float(top[:5].sum() / max(x.sum(), 1e-9) * 100)}, daily


def main():
    for p, h in AUTH.items():
        assert C45.sha(os.path.join(C.ROOT, p)) == h, p
    sess = C45.build_panel()["sessions"]
    sess = pd.DatetimeIndex(sess)
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0)
    parity = json.load(open(os.path.join(T, "T46_01_parity.json")))
    san = json.load(open(os.path.join(C.LEDGER_DIR, "SANITIZER_REPORT.json")))
    TR = pd.read_parquet(os.path.join(T, "laneA", "laneA_trades.parquet"))
    TR["date"] = pd.DatetimeIndex(TR.date)
    idx6, d6 = portfolio(TR, sess)
    idx5, d5 = portfolio(TR, sess)          # TS16 has no ledger/engine here, so INDEX5-NOOI == available INDEX set
    contrib = TR.groupby("inst").e0.sum().to_dict()
    sel = json.load(open(os.path.join(T, "final", "T46_38_final_selection.json")))
    gate = rd("final/T46_36_incremental_gate.csv")
    final = sel["FINAL_TEST46_CHALLENGER"]
    code = {os.path.relpath(f, C.ROOT): C45.sha(f) for f in sorted(glob.glob(os.path.join(C.SRC, "t46_*.py")))}
    ledg = {os.path.basename(f): C45.sha(f) for f in sorted(glob.glob(os.path.join(C.LEDGER_DIR, "*_TO_20260527.csv")))}
    fz = {"program": "TEST46 ES/NQ long alpha evolution + structural rebound discovery", "research_data_end": "2026-05-27",
          "TEST44_45_OOS_START": "2026-05-28", "TEST46_ORIGINAL_OOS_PARTIALLY_EXPOSED": "YES (8 LC03 legacy-ledger trades 2026-05-28..2026-08-27 viewed)",
          "TEST46_QUARANTINED_INTERVAL": "2026-05-28 .. 2026-09-27 (never used for any TEST46 decision)",
          "TEST46_NEW_OOS_START": C.TEST46_NEW_OOS_START,
          "new_oos_start_condition": "valid because no market data dated 2026-09-28 or later has been accessed by the lab before this freeze",
          "FINAL_TEST46_CHALLENGER": final,
          "authorities_verified_unchanged": AUTH,
          "legacy_ledger_recovery": {"source": "Google Drive FULL_HISTORY / batched TradingView exports ingested without display into an out-of-repo quarantine; "
                                     "authority-hash evidence files (PROPFIRM_PORTFOLIO_V1 evidence) not reachable from this environment",
                                     "sanitizer_report": san, "sanitized_ledger_sha256": ledg},
          "parity": parity, "parity_rule": "predeclared in src/t46_01_parity.py (v1.1 coverage/price-convention amendment before any Lane-A economics)",
          "seed_status": {"LC02 ES-VOR": "PARITY_BLOCKED (recall 1.00, precision 0.978 < 0.98)", "LC03 NQ-NOON": "PARITY_BLOCKED (recall 0.970)",
                          "LC05 NQ-PDH": "PARITY_BLOCKED (0.67: RVOL/VWAP need NQ volume; canonical is MNQ)",
                          "TS16-S01 NQ-OI": "PARITY_BLOCKED (no OI data) + LIVE-SAFETY HOLD", "TS22-S01 NQ-SNAP": "PARITY_BLOCKED (ledger not retrievable: Drive session failures)",
                          "T30-W01 NQ-COMP": "PARITY_BLOCKED (requires YM1!/RTY1! cross-market context; W01 filter not recoverable)"},
          "shadow_clues_report_only": ["ML-A RIDGE bottom-quality filter over the broad structural-rebound pool (gate: G3,G5 failed)",
                                       "Lane-A hold extension of LC03 to 16:00 (research-only, seed PARITY_BLOCKED)"],
          "code_sha256": code, "new_oos_data_acquired": False, "test46_new_oos_opened": False, "live_authorization": "NO",
          "portfolio_membership_changed": "NO"}
    fj = os.path.join(FZ, "TEST46_PRE_OOS_FREEZE.json"); json.dump(fz, open(fj, "w"), indent=1, default=str); hf = C45.sha(fj)
    rules = {"program": "TEST46", "pre_oos_freeze_sha256": hf, "written_before_TEST46_new_oos": True,
             "TEST46_NEW_OOS_START": C.TEST46_NEW_OOS_START, "challenger": final,
             "if_NONE": "no TEST46 promotion test is run; shadow clues may be monitored descriptively only",
             "evaluation_gate": {"min_sessions": ">= 120 completed RTH sessions on/after TEST46_NEW_OOS_START (TEST44 rule unchanged)",
                                 "data": "canonical ES/MNQ per TEST44_OOS_DATA_PROTOCOL; the 2026-05-28..2026-09-27 quarantine is never evaluated for TEST46"},
             "absolute_pass (C43 + candidate)": {"net_pnl": "> 0", "max_dd": "<= $15,000", "worst_day": ">= -$3,000", "remove_top3_avg": "> 0",
                                                 "best_day": "<= 35% of net", "SLIP4_net": "> 0", "margin": "no breach"},
             "promotion_over_C43": {"net": ">= 1.10 x C43", "ret_dd": ">= C43", "matched_beta_excess": ">= C43", "session_matched_excess": ">= C43",
                                    "overnight_lock": "no unacceptable locked exposure (TEST45 governor)"},
             "prohibited_after_opening": ["any parameter / feature / threshold / model change", "switching to a shadow clue"],
             "live_authorization": "NO"}
    fr = os.path.join(FZ, "TEST46_NEW_OOS_ACCEPTANCE_RULES.json"); json.dump(rules, open(fr, "w"), indent=1); hr = C45.sha(fr)
    open(os.path.join(FZ, "TEST46_FREEZE.sha256"), "w").write(f"{hf}  TEST46_PRE_OOS_FREEZE.json\n{hr}  TEST46_NEW_OOS_ACCEPTANCE_RULES.json\n")
    # ------------------------------------------------------------------------------------------------ reports
    hold = rd("laneA/T46_05_hold_extension.csv"); curve = rd("laneA/T46_04_exit_response.csv"); on = rd("laneA/T46_06_strategy_overnight.csv")
    pyr = rd("laneA/T46_07_10_pyramids.csv"); ev = rd("laneB/T46_18_event_forward_default.csv"); abl = rd("laneB/T46_11_grammar_ablation.csv")
    rec = rd("laneB/T46_20_multiyear_recurrence.csv"); ctl = rd("laneB/T46_21_simple_controls.csv"); ml = rd("ml/T46_23_ml_walkforward.csv")
    mla = rd("ml/T46_24_ml_ablation.csv"); gsel = rd("gaA/T46_26_gaA_selected.csv"); gspec = json.load(open(os.path.join(T, "gaA", "T46_25_gaA_spec.json")))
    PB = "**Lane A is RESEARCH-ONLY: every INDEX6 seed is PARITY_BLOCKED (T46_01); nothing in Lane A can be promoted.**"
    INC = open(os.path.join(T, "T46_INCIDENT_SEALED_WINDOW_EXPOSURE.md")).read()
    M = C.md
    M("T46_00_AUTHORITY_INDEX.md", "T46_00 Authority index", [
        "Verified unchanged:", pd.DataFrame([{"file": k, "sha256": v} for k, v in AUTH.items()]),
        "Incident record (sealed-window exposure):", INC,
        "Legacy ledger recovery. The raw files were downloaded without display into an out-of-repo quarantine, then passed through the mechanical sanitizer (src/t46_sanitize_ledgers.py). The sanitizer outputs only the fields listed:",
        pd.DataFrame(san),
        "The PROPFIRM_PORTFOLIO_V1 authority-hash evidence files are workstation-only and not reachable from this cloud environment. SOURCE_HASH_MATCH=NO means a different export (Drive FULL_HISTORY or batched export) of the same frozen strategy was used.",
        "Frozen Pine sources recovered (no market data): authorities/index6/*.pine.",
        "Code hashes:", pd.DataFrame([{"file": k, "sha256": v} for k, v in code.items()])])
    M("T46_01_INDEX6_BASELINE_PARITY.md", "T46_01 INDEX6 baseline parity", [
        "Predeclared rule: over sessions 2019-09-03..2026-05-27 with full canonical coverage, PASS requires recall >= 98%, precision >= 98% and offset-consistent entry price within 1 tick for >= 95%.",
        pd.DataFrame(parity), pd.DataFrame([{"seed": k, "status": v} for k, v in fz["seed_status"].items()]),
        "INDEX6_PARITY_PASS = NO. LC02 misses by 0.2 pp of precision; the rule is not relaxed after the fact."])
    M("T46_02_INDEX6_PORTFOLIO_BASELINE.md", "T46_02 INDEX6 legacy long baseline (available seeds, ledger entries, canonical micro economics)", [
        PB, "Replayed seeds: LC02, LC03, LC05 and T30-L1 (unfiltered). TS16 has no data; TS22 has no retrievable ledger.",
        pd.DataFrame([idx6]).T, f"Contribution by instrument ($): {json.dumps({k: round(v) for k, v in contrib.items()})}",
        f"Correlation with C43 (daily): {np.corrcoef(d6.values, champ.values)[0, 1]:.3f}"])
    M("T46_03_INDEX5_NOOI_BASELINE.md", "T46_03 INDEX5-NOOI baseline", [PB, "TS16 (the only OI seed) has no ledger or engine here, so INDEX5-NOOI equals the available set.", pd.DataFrame([idx5]).T])
    M("T46_04_EXIT_RESPONSE_CURVES.md", "T46_04 Exit response curves (same entries, standardized horizons, matched long baseline)", [PB, curve])
    M("T46_05_HOLD_EXTENSION.md", "T46_05 Hold extension E0..E6", [PB, hold,
      "Answer: the entry edge persists beyond the original 120-min shell for LC03 (to 16:00: matched excess t = 2.37) and weakly for LC02/T30-L1. The research-only EXIT_EXTENSION_ADDS_ALPHA is YES (not promotable)."])
    M("T46_06_STRATEGY_SPECIFIC_OVERNIGHT.md", "T46_06 Strategy-specific overnight", [PB, on,
      "Answer: carry conditioned on an active seed does not beat matched unconditional carry significantly (all |t| <= 1)."])
    for fn, title, rule in (("T46_07_CONFIRMATION_PYRAMID.md", "T46_07 Confirmation pyramid (P1)", "P1"), ("T46_08_WINNER_PYRAMID.md", "T46_08 Winner pyramid (P2)", "P2"),
                            ("T46_09_RECLAIM_PYRAMID.md", "T46_09 Reclaim pyramid (P3)", "P3"), ("T46_10_BLIND_DCA_CONTROL.md", "T46_10 Blind DCA control", "DCA")):
        M(fn, title, [PB, "Incremental P&L of the SECOND contract only (add fill -> original exit):", pyr[pyr.rule.str.startswith(rule)],
                      "No rule is significant (|t| < 1.5). Add counts for P2/P3 are small; blind DCA is not better than the structural adds."])
    M("T46_11_STRUCTURAL_REBOUND_GRAMMAR.md", "T46_11 Structural rebound grammar and ablations", [
        "Grammar: DISPLACEMENT + STRUCTURAL LEVEL + FAILURE (k bars without a new low) + RECLAIM + REGIME veto. Ablations remove one component each:", abl,
        "Answer: removing FAILURE or RECLAIM does not systematically worsen outcomes, so the structural confirmation adds no measurable information over displacement."])
    fams = {"T46_12_FAILED_BREAKDOWN.md": "B1", "T46_13_VWAP_BAND_RECLAIM.md": "B2", "T46_14_OR_FAILED_BREAKDOWN.md": "B3",
            "T46_15_RANGE_EXHAUSTION.md": "B4", "T46_16_HTF_BULL_PULLBACK.md": "B5", "T46_17_RELATIVE_EXHAUSTION.md": "B6"}
    for fn, fam in fams.items():
        M(fn, fn[:-3].replace("_", " "), [ev[ev.family.str.startswith(fam)], ctl[ctl.family.str.startswith(fam)],
                                        abl[abl.family.str.startswith(fam)] if fam == "B6" else ""])
    M("T46_18_EVENT_FORWARD_RETURNS.md", "T46_18 Event forward returns + first passage (unresolved kept unresolved)", [ev])
    M("T46_19_MATCHED_LONG_BASELINES.md", "T46_19 Matched long baselines", ["Baseline = unconditional long with the same fill minute, calendar year, volatility tercile and HTF state; excess = event - baseline (ATR units).",
                                                                        ev[["family", "inst", "events"] + [c for c in ev.columns if "excess" in c]]])
    M("T46_20_MULTIYEAR_RECURRENCE.md", "T46_20 Multi-window recurrence (2-year rolling windows)", [rec.pivot_table(index=["family", "inst"], columns="window", values="excess_to1600_atr")])
    M("T46_21_SIMPLE_CONTROLS.md", "T46_21 Simple deterministic controls (predeclared defaults)", [ctl, "The minimum-sample rule (predeclared in out/t46/laneB/T46_minimum_sample_rules.json) is passed by no control."])
    M("T46_22_ML_MODEL_ZOO.md", "T46_22 ML model zoo", ["Models (one regularized preset each): Ridge, ElasticNet, Logistic, RF, ExtraTrees, HistGB, XGBoost, LightGBM, CatBoost. The HMM regime model is not refit here because the TEST45 HMM added no value.",
                                                    "Tasks: ML-A bottom quality (production-compatible); ML-B hold extension and ML-D overnight (research-only). ML-C and ML-E are not fitted (reason in T46_23)."])
    M("T46_23_ML_WALKFORWARD.md", "T46_23 ML walk-forward (expanding yearly, first test year 2021)", [ml])
    M("T46_24_ML_ABLATION.md", "T46_24 ML ablation", [mla, "The linear model's value depends on the ES/NQ relative feature; tree models are negative with or without it."])
    M("T46_25_GA_SPEC.md", "T46_25 GA-A specification", [json.dumps({k: v for k, v in gspec.items() if k != "space"}, indent=1), pd.DataFrame(gspec["space"], columns=["gene", "type", "domain"]),
                                                         "GA-B/C/D (INDEX6 exit, pyramid, overnight evolution) were NOT run: seed parity failed and the TEST46 rule forbids evolving unverified seeds."])
    M("T46_26_GA_NESTED_RESULTS.md", "T46_26 GA-A nested outer folds", [gsel.drop(columns=["genome"])])
    M("T46_27_GA_PARETO.md", "T46_27 GA-A Pareto fronts", ["Fronts are stored per fold in out/t46/gaA/front_*.parquet. The selected genomes are in T46_26."])
    M("T46_28_GA_RECURRENCE.md", "T46_28 GA-A recurrence", ["Family recurrence in the final fronts: B5 HTF-bull/VWAP-reclaim on MNQ dominates the 2023/2024 folds, and B2 dominates 2021/2022. The selected genomes drift to D~0, i.e. no displacement, which means the grammar is abandoned. Outer results alternate sign. GA_RULE_RECURRENCE = WEAK."])
    M("T46_29_GA_PARAMETER_PLATEAU.md", "T46_29 GA-A parameter plateau", ["Not established: outer generalization failed first (median +$0.8/day, 3/5 blocks positive). GA_PARAMETER_PLATEAU_PASS = NO."])
    M("T46_30_GP_DIAGNOSTIC.md", "T46_30 GP diagnostic", ["GP not run. GA outer generalization failed and tree models did not beat the linear model, so there is no evidence of a useful nonlinear structure (prompt section 47)."])
    M("T46_31_INTEGER_ALLOCATOR.md", "T46_31 Integer allocator", ["No TEST46 module survived. The frozen integer target engine is unchanged: C43 alone, and any shadow module would be a 0/1 MES/MNQ virtual sleeve behind the shared governor."])
    M("T46_32_OVERNIGHT_RISK_GOVERNOR.md", "T46_32 Overnight inventory governor", ["Lane B modules are intraday (flat by 16:15), so they add no locked inventory. TEST45 lock stress holds: single-symbol 1-contract nights are inside the -$3k reference; 1 MES + 1 MNQ simultaneously reached -$3,175.50 historically and exceeds the combined -$3k gate."])
    M("T46_33_EXECUTION_STRESS.md", "T46_33 Execution stress", [ctl[["family", "inst", "exit", "total", "SLIP4_total"]], "No candidate reached the stress stage."])
    M("T46_34_MODULE_COMBINATION.md", "T46_34 Module combination", [gate[["candidate", "incr_avg", "comb_avg", "comb_mdd", "comb_worst", "comb_ret_dd", "C43_ret_dd", "corr"]]])
    M("T46_35_ALPHA_ATTRIBUTION.md", "T46_35 Alpha attribution", [pd.DataFrame([
        {"component": "ORIGINAL_SEED_ENTRY_ALPHA", "verified_$/day": 0.0, "note": "seeds PARITY_BLOCKED; ledger replay in T46_02"},
        {"component": "HOLD_EXTENSION_ALPHA", "verified_$/day": 0.0, "note": "research-only, positive for LC03 (T46_05)"},
        {"component": "PYRAMID_SECOND_CONTRACT_ALPHA", "verified_$/day": 0.0, "note": "not significant"},
        {"component": "OVERNIGHT_CARRY_ALPHA", "verified_$/day": 0.0, "note": "not significant vs matched carry"},
        {"component": "NEW_BOTTOM_REBOUND_ALPHA", "verified_$/day": 0.0, "note": "no mechanism passes; ML-A Ridge +$3.9/day fails the gate"},
        {"component": "ML_SELECTION_ALPHA", "verified_$/day": 0.0, "note": "see ML-A"}, {"component": "GA_SELECTION_ALPHA", "verified_$/day": 0.0, "note": "outer generalization failed"}])])
    M("T46_36_PORTFOLIO_INCREMENTAL_GATE.md", "T46_36 Portfolio incremental gate (mechanical)", [open(os.path.join(C.SRC, "t46_07_select.py")).read().split('"""')[1], gate])
    M("T46_37_SCALING_FRONTIER.md", "T46_37 Scaling frontier", ["No surviving module, so there is nothing to scale. $600/day at C43's return/DD would need about 11x the risk. Leverage is not an acceptable route. TEST46 added no verified alpha."])
    M("T46_38_FINAL_TEST46_CANDIDATE.md", "T46_38 Final TEST46 candidate", [json.dumps(sel, indent=1), f"**FINAL_TEST46_CHALLENGER = {final}**"])
    M("T46_39_PRE_OOS_FREEZE.md", "T46_39 Pre-OOS freeze", [f"sha256 **{hf}**", "```json\n" + json.dumps(fz, indent=1, default=str)[:15000] + "\n```"])
    M("T46_40_NEW_OOS_ACCEPTANCE_RULES.md", "T46_40 New-OOS acceptance rules", [f"sha256 **{hr}**", "```json\n" + json.dumps(rules, indent=1) + "\n```"])
    b = {r["candidate"]: r for _, r in gate.iterrows()}
    status = {"LEGACY_LEDGER_RECOVERY_SOURCE": "Google Drive FULL_HISTORY/batched exports -> undisplayed quarantine -> mechanical sanitizer (authority-hash evidence files unreachable)",
              "LC02_RAW_HASH_MATCH": "NO (different export)", "LC03_RAW_HASH_MATCH": "NO (different export)", "LC05_RAW_HASH_MATCH": "NO (different export)",
              "TS16_RAW_HASH_MATCH": "NOT RECOVERED", "TS22_RAW_HASH_MATCH": "NOT RECOVERED (Drive session failures)", "T30_RAW_HASH_MATCH": "NO (batched export, T30-L1 selector)",
              "SANITIZED_INDEX6_LEDGER_COUNT": len(ledg), "ALL_SANITIZED_MAX_DATE_LE_20260527": "YES",
              "TEST46_ORIGINAL_OOS_INTEGRITY": "PARTIALLY_COMPROMISED_LC03", "TEST46_RESEARCH_DATA_END": "2026-05-27",
              "TEST46_NEW_OOS_START": C.TEST46_NEW_OOS_START, "TEST46_NEW_OOS_OPENED": "NO",
              "INDEX6_PARITY_PASS": "NO (all seeds PARITY_BLOCKED; LC02 closest)", "INDEX6_AVG_DAY": round(idx6["avg_day"], 2),
              "INDEX6_MAX_DD": round(idx6["max_dd"], 0), "INDEX6_WORST_DAY": round(idx6["worst_day"], 0), "INDEX5_NOOI_AVG_DAY": round(idx5["avg_day"], 2),
              "INDEX5_NOOI_MAX_DD": round(idx5["max_dd"], 0), "BEST_EXISTING_SEED": "LC03 NQ-NOON (best PF/trade in canonical replay; research-only)",
              "BEST_SEED_EXIT_EXTENSION": "LC03 hold to 16:00 (matched excess t 2.37; research-only)", "EXIT_EXTENSION_ADDS_ALPHA": "YES research-only / NOT PROMOTABLE",
              "STRATEGY_SPECIFIC_OVERNIGHT_ADDS_ALPHA": "NO", "BEST_OVERNIGHT_SEED": "LC02 (excess +$9.6/trade, t 0.99, not significant)",
              "CONFIRMATION_PYRAMID_ADDS_VALUE": "NO (t 1.44)", "WINNER_PYRAMID_ADDS_VALUE": "NO", "RECLAIM_PYRAMID_ADDS_VALUE": "NO", "BLIND_DCA_ADDS_VALUE": "NO",
              "BEST_PYRAMID_ARCHITECTURE": "NONE", "FAILED_BREAKDOWN_EDGE_ES": "NO", "FAILED_BREAKDOWN_EDGE_NQ": "NO", "VWAP_BAND_RECLAIM_EDGE_ES": "NO",
              "VWAP_BAND_RECLAIM_EDGE_NQ": "NO (significantly negative)", "OR_FAILED_BREAK_EDGE_ES": "NO", "OR_FAILED_BREAK_EDGE_NQ": "NO",
              "RANGE_EXHAUSTION_EDGE_ES": "NO (n=40, t 1.27)", "RANGE_EXHAUSTION_EDGE_NQ": "NO", "HTF_BULL_PULLBACK_EDGE_ES": "NO", "HTF_BULL_PULLBACK_EDGE_NQ": "NO",
              "RELATIVE_EXHAUSTION_ADDS_VALUE": "NO (n=9)", "BEST_NEW_REBOUND_MECHANISM": "NONE", "MATCHED_LONG_EXCESS_POSITIVE": "NO",
              "BEST_LINEAR_MODEL": "RIDGE (ML-A rank-IC 0.038; +$5.3k 2021-26)", "BEST_TREE_MODEL": "EXTRA_TREES (ML-A rank-IC 0.034)", "BEST_REGIME_MODEL": "none (TEST45 HMM no value)",
              "ML_ADDS_VALUE": "NO (Ridge beats the simple control but fails the gate)", "GA_ADDS_VALUE": "NO", "GA_OUTER_GENERALIZATION": "FAIL (3/5 blocks, median +$0.8/day)",
              "GA_RULE_RECURRENCE": "WEAK", "GA_PARAMETER_PLATEAU_PASS": "NO", "GP_ADDS_VALUE": "NOT RUN (not justified)",
              "BEST_PRACTICAL_MAX_MES": "0 adopted", "BEST_PRACTICAL_MAX_MNQ": "0 adopted", "BEST_TEST46_INCREMENTAL_AVG_DAY": "0 verified (best unverified: ML-A Ridge +3.87)",
              "C43_PLUS_TEST46_AVG_DAY": round(float(champ.mean()), 2), "C43_PLUS_TEST46_MAX_DD": 6193, "C43_PLUS_TEST46_WORST_DAY": -1723,
              "C43_PLUS_TEST46_MATCHED_BETA_EXCESS": "unchanged (C43 only)", "ALPHA_FROM_HOLD_EXTENSION": 0, "ALPHA_FROM_PYRAMID": 0, "ALPHA_FROM_OVERNIGHT": 0,
              "ALPHA_FROM_NEW_REBOUND": 0, "ALPHA_FROM_ML_GA": 0, "TOTAL_VERIFIED_INCREMENTAL_HISTORICAL_ALPHA": 0, "FINAL_TEST46_CHALLENGER": final,
              "TEST46_PRE_OOS_FREEZE_SHA256": hf, "TEST46_NEW_OOS_RULES_SHA256": hr, "TEST44_AUTHORITIES_UNCHANGED": "YES", "TEST45_AUTHORITIES_UNCHANGED": "YES",
              "NEW_OOS_DATA_ACQUIRED": "NO", "NEW_OOS_OPENED (TEST44/45 evaluation)": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "LIVE_AUTHORIZATION": "NO"}
    C45.jdump(status, os.path.join(T, "T46_final_status.json"))
    files = sorted(set(glob.glob(f"{T}/**/*", recursive=True)) | set(glob.glob(f"{C.SRC}/t46_*.py")) | set(glob.glob(f"{C.REP}/*.md"))
                   | set(glob.glob(f"{C.LEDGER_DIR}/*")) | set(glob.glob(os.path.join(C.ROOT, "authorities", "index6", "*"))))
    files = [f for f in files if os.path.isfile(f) and not f.endswith(".log") and "bars5_" not in f and "T46_41_HASH_INDEX" not in f]
    H = pd.DataFrame([{"file": os.path.relpath(f, C.ROOT), "sha256": C45.sha(f), "bytes": os.path.getsize(f)} for f in files])
    H.to_csv(os.path.join(T, "T46_41_HASH_INDEX.csv"), index=False)
    M("T46_41_HASH_INDEX.md", "T46_41 Hash index", ["Final status:", pd.DataFrame([status]).T, H])
    print(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
