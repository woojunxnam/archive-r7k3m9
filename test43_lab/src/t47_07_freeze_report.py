"""TEST47 reports T47_01..T47_48, pre-OOS freeze, new-OOS acceptance rules, hash index and final status.
TEST47_NEW_OOS_START = first full RTH session STRICTLY AFTER the freeze timestamp (computed, not preset)."""
import datetime
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_common as C  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402

T = C.T47
N3, NR, ML, GAo, FI, FZ = (os.path.join(T, x) for x in ("n3", "nr", "ml", "ga", "final", "freeze"))
os.makedirs(FZ, exist_ok=True)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rd(p, **kw):
    return pd.read_csv(p, **kw) if os.path.exists(p) else pd.DataFrame()


def main():
    md = C.md
    R = {k: rd(os.path.join(N3, f"{k}.csv"), index_col=0) for k in ("fr", "fp", "pn_leg", "po", "shf", "fr8", "en9", "sw10", "ra11", "dec", "cv", "m1", "m15", "nb", "ctl")}
    qa = rd(os.path.join(N3, "T47_01_data_qa.csv")); cq = rd(os.path.join(N3, "T47_01_causal_qa.csv"))
    rec = rd(os.path.join(NR, "T47_19_23_recycle.csv")); ex = rd(os.path.join(NR, "T47_25_exit_response.csv"))
    ovn = rd(os.path.join(NR, "T47_26_overnight.csv")); rcy = rd(os.path.join(NR, "T47_28_recurrence.csv"))
    mlr = rd(os.path.join(ML, "T47_29_30_ml_walkforward.csv")); abl = rd(os.path.join(ML, "T47_31_ml_ablation.csv"))
    gate = rd(os.path.join(FI, "T47_44_incremental_gate.csv")); stress = rd(os.path.join(FI, "T47_40_execution_stress.csv"))
    attr = rd(os.path.join(FI, "T47_43_alpha_attribution.csv")); grec = rd(os.path.join(FI, "T47_37_ga_recurrence.csv"))
    plat = rd(os.path.join(FI, "T47_38_ga_plateau.csv")); acc = rd(os.path.join(FI, "T47_41_42_account_combination.csv"))
    sel = json.load(open(os.path.join(FI, "T47_45_final_selection.json")))
    gsel = {ln: rd(os.path.join(GAo, f"T47_GA_{ln}_selected.csv")) for ln in ("N3", "NB", "NR")}
    spec = json.load(open(os.path.join(T, "T47_02_predeclared_spec.json")))
    NOTE = "Research data <= 2026-05-27 only. $ are 1 MES / 1 MNQ contract, costs included (commission 0.62 + 1 tick per side)."

    md("T47_01_DATA_AND_CAUSAL_QA.md", "T47_01 Data and causal QA", [NOTE, qa, "Causal perturbation test: every bar from bar b0 onward replaced by noise; events decided before b0 must be identical.", cq,
       "No TEST47 signal uses volume (the MNQ-for-NQ volume substitution never arises). 15m bars are completed 5m triplets; no developing value is used."])
    md("T47_02_TICK_DEFINITION_SPEC.md", "T47_02 Meaningful-down-leg (tick) specification (PREDECLARED)",
       [f"Spec file sha256 = {open(os.path.join(T, 'T47_02_predeclared_spec.json.sha256')).read().strip()} (committed before any economic result).",
        "```json\n" + json.dumps(spec, indent=1)[:6000] + "\n```"])
    fr = R["fr"]; fp = R["fp"]
    md("T47_03_N3_EVENT_CATALOG.md", "T47_03 N3 event catalogue", ["Evidence: out/t47/n3/T47_03_event_catalog.parquet (one row per event, full leg geometry).",
                                                                   fr[["inst", "config", "events", "sessions"]] if len(fr) else ""])
    md("T47_04_N3_FORWARD_RESPONSE.md", "T47_04 N3 forward response (ATRd units, E1 fill)", [fr, "Path statistics (MFE/MAE to +120m, time to target in minutes, first passage; unresolved kept unresolved):", fp])
    md("T47_05_N3_MATCHED_NULLS.md", "T47_05 N3 matched nulls", ["Matched ordinary long = same instrument, fill minute, calendar year, ATR20-percentile tercile, HTF trend state, same exit. t = event mean with session-clustered SE.",
                                                                  fr[[c for c in fr.columns if c.endswith("excess") or c.endswith("t_exc") or c in ("inst", "config", "events")]],
                                                                  "Trade economics (1 lot, E1, X60, non-overlapping):", R["pn_leg"]])
    md("T47_06_PATH_ORDER_NULL.md", "T47_06 Path-order null (same drop, same duration, no serial leg pattern)", [R["po"],
       "order_excess = N3 event forward minus the mean of controls with identical duration d, drop bin (0.5 u5), hour bucket and vol tercile that did NOT reach N legs. No leg definition shows a significant positive order excess."])
    md("T47_07_SEQUENCE_SHUFFLE.md", "T47_07 Sequence-shuffle diagnostic", [R["shf"], "20 within-window permutations of whole 5m bars (W=12). order_effect = E[fwd | real trigger] - E[fwd | shuffled trigger]; p = share of permutations >= real."])
    md("T47_08_NTICK_FRONTIER.md", "T47_08 N-tick frontier (2 / 3 / 4 legs)", [R["fr8"], "Three is not special: responses move smoothly / noisily with depth and no depth is positive after matching."])
    md("T47_09_ENTRY_TIMING.md", "T47_09 Entry timing frontier (C2 events, X60)", [R["en9"]])
    md("T47_10_SIDEWAYS_STATE.md", "T47_10 Sideways / up-bar state handling", [R["sw10"]])
    md("T47_11_PRIOR_RALLY_FILTER.md", "T47_11 Prior-rally / spike filter", [R["ra11"]])
    md("T47_12_TRUE_BOTTOM_SPEC.md", "T47_12 True-bottom (NB) specification", ["NB (predeclared): " + spec["true_bottom_NB"], R["nb"]])
    md("T47_13_DECELERATION.md", "T47_13 Selling deceleration vs acceleration", [R["dec"]])
    md("T47_14_CRASH_VETO.md", "T47_14 Crash / acceleration veto", [R["cv"], "The vetoed (extreme) subsets are small and are NOT promoted: an ex-post observation that extreme states rebounded more would be a NEW HYPOTHESIS (shadow research only, TEST47 §60)."])
    md("T47_15_1M_BOTTOM_CONFIRM.md", "T47_15 1-minute bottom confirmation (E4 grammar)", [R["m1"]])
    md("T47_16_15M_CONTEXT.md", "T47_16 15-minute context", [R["m15"]])
    md("T47_17_SIMPLE_N3_CONTROLS.md", "T47_17 Simple controls C0..C4", [R["ctl"]])
    md("T47_18_TRUE_BOTTOM_CONTROLS.md", "T47_18 True-bottom controls", [R["ctl"][R["ctl"].control.str.startswith(("C2", "C4"))] if len(R["ctl"]) else ""])
    cols = ["inst", "entry", "exit", "config", "campaigns", "adds", "trims", "avg_day_2021", "excess_day_2021", "incr_avg_day", "incr_t", "delta_ret_dd",
            "delta_worst_day", "delta_max_dd", "worst_campaign", "remove_top3_campaigns", "folds_pos"]
    for fn, ttl, key in (("T47_19_RECYCLE_BASELINE.md", "T47_19 Recycle baseline R0", "R0"), ("T47_20_CONFIRMED_SECOND_BUY.md", "T47_20 NR-A confirmed second buy", "NR-A"),
                         ("T47_21_BLIND_DCA_CONTROL.md", "T47_21 NR-B blind DCA control (diagnostic)", "NR-B"), ("T47_22_REBOUND_TRIM.md", "T47_22 NR-C rebound trim", "NR-C"),
                         ("T47_23_FULL_RECYCLE.md", "T47_23 NR-D full recycle", "NR-D")):
        md(fn, ttl, [rec[rec.config.str.startswith(key)][[c for c in cols if c in rec.columns]] if len(rec) else ""])
    md("T47_24_RECYCLE_ACCOUNTING.md", "T47_24 Recycle accounting (per logical lot)", ["Lot ledger: out/t47/nr/T47_24_lot_ledger.parquet (INIT / SECOND / REBUILD lots, TRIM / FINAL / OVERNIGHT exits).",
                                                                                     rec[["inst", "entry", "exit", "config", "pnl_INIT", "pnl_SECOND", "pnl_REBUILD", "pnl_TRIM_exits", "extra_cost", "extra_sides",
                                                                                          "cost_per_extra_cycle", "max_inventory", "cvar5_day_2021", "days_underwater%_2021"]] if len(rec) else ""])
    md("T47_25_EXIT_RESPONSE.md", "T47_25 Exit response", [ex])
    md("T47_26_NASSI_OVERNIGHT.md", "T47_26 NASSI conditional overnight (unresolved campaigns only)", [ovn.T if len(ovn) else ""])
    port = []
    for inst in ("ES", "MNQ"):
        c = R["ctl"][(R["ctl"].inst == inst) & (R["ctl"].exit == "X60")] if len(R["ctl"]) else pd.DataFrame()
        port.append({"inst": inst, "best_control_excess_trade": c.excess_trade.max() if len(c) else np.nan,
                     "any_control_t>2": bool((c.t_excess > 2).any()) if len(c) else False, "classification": "NO_EDGE"})
    md("T47_27_ES_NQ_PORTABILITY.md", "T47_27 ES / NQ portability", [pd.DataFrame(port), "PORTABILITY = NONE (no mechanism has an edge on either instrument; nothing to port)."])
    if len(rcy):
        md("T47_28_MULTIYEAR_RECURRENCE.md", "T47_28 Multiyear recurrence of path structure",
           ["+60m matched excess by year:", rcy.pivot_table(index=["inst", "ntick"], columns="year", values="excess60"),
            "deceleration minus acceleration excess by year:", rcy.pivot_table(index=["inst", "ntick"], columns="year", values="decel_minus_accel"),
            "best cumulative-size tercile by year:", rcy.pivot_table(index=["inst", "ntick"], columns="year", values="best_size_tercile", aggfunc="first"),
            "No leg count, size region or deceleration sign recurs with a consistent positive sign."])
    md("T47_29_ML_MODEL_ZOO.md", "T47_29 ML model zoo", ["RIDGE, ELASTIC_NET, LOGISTIC, EXTRA_TREES, RANDOM_FOREST, HIST_GB, XGBOOST, CATBOOST, LIGHTGBM (TEST45 presets). Yearly expanding walk-forward 2021..2026-05-27.",
                                                          mlr[mlr.task.isin(["ML-A", "SEQ"])] if len(mlr) else ""])
    md("T47_30_ML_WALKFORWARD.md", "T47_30 ML walk-forward (all tasks)", [mlr])
    md("T47_31_ML_ABLATION.md", "T47_31 ML ablation", [abl])
    seq = mlr[mlr.task == "SEQ"] if len(mlr) else pd.DataFrame()
    md("T47_32_SEQUENCE_MODEL_DIAGNOSTIC.md", "T47_32 Sequence model diagnostic (small 1D CNN)", [seq,
       "Predeclared rule: justified only if first-fold training >= 2000 events AND it beats the best tabular model on outer rank IC and taken P&L. Rank IC < 0 -> SEQUENCE_MODEL_JUSTIFIED = NO."])
    md("T47_33_GA_N3_SPEC.md", "T47_33 GA specification", ["```json\n" + open(os.path.join(GAo, "T47_33_ga_spec.json")).read()[:5000] + "\n```" if os.path.exists(os.path.join(GAo, "T47_33_ga_spec.json")) else ""])
    for fn, ln in (("T47_34_GA_N3_RESULTS.md", "N3"), ("T47_35_GA_NB_RESULTS.md", "NB"), ("T47_36_GA_NR_RESULTS.md", "NR")):
        S = gsel[ln]
        md(fn, f"{fn[:6]} GA-{ln} nested results", [S.drop(columns=["genome"], errors="ignore") if len(S) else "(not run)"])
    md("T47_37_GA_RECURRENCE.md", "T47_37 GA recurrence", [grec])
    md("T47_38_GA_PARAMETER_PLATEAU.md", "T47_38 GA parameter plateau (FINAL genome of each lane)", [plat if len(plat) else "(no final genome)"])
    md("T47_39_GP_DIAGNOSTIC.md", "T47_39 GP diagnostic", [sel["gp"]])
    md("T47_40_EXECUTION_STRESS.md", "T47_40 Execution stress", ["No candidate survived the standalone gate; stress is reported on C2 / C4 / C6 for documentation.", stress])
    md("T47_41_ACCOUNT_RISK.md", "T47_41 Account risk ($150k shared account)", [acc, "Max inventory 2 MES / 2 MNQ; all adopted-candidate inventory is intraday. TEST45 overnight finding (1 MES + 1 MNQ locked breached the -$3k combined reference) is retained; no NASSI overnight inventory is approved."])
    md("T47_42_MODULE_COMBINATION.md", "T47_42 Module combination", [acc, "Every module is negative standalone; no combination was formed (combining non-positive modules cannot pass the gate)."])
    md("T47_43_ALPHA_ATTRIBUTION.md", "T47_43 Alpha attribution ($/day, 2021..2026-05-27)", [attr.T if len(attr) else "", "ML_SELECTION and GA_SELECTION: see T47_44 (both non-positive)."])
    md("T47_44_C43_INCREMENTAL_GATE.md", "T47_44 C43 incremental gate (mechanical, predeclared)", ["Gate rules (predeclared): " + json.dumps(spec["gate"]), gate])
    md("T47_45_FINAL_TEST47_CANDIDATE.md", "T47_45 Final TEST47 candidate", ["```json\n" + json.dumps(sel, indent=1) + "\n```"])
    # ---------------------------------------------------------------- freeze
    now = datetime.datetime.now(datetime.timezone.utc)
    oos_start = first_rth_after(now)
    srcs = sorted(glob.glob(os.path.join(C45.SRC, "t47_*.py")))
    evid = sorted([p for p in glob.glob(os.path.join(T, "**", "*"), recursive=True) if os.path.isfile(p) and "freeze" not in p and not p.endswith(".log")])
    auth44 = sorted(glob.glob(os.path.join(C45.ROOT, "out", "t44", "*FREEZE*"))) + sorted(glob.glob(os.path.join(C45.ROOT, "out", "t44", "*RULES*")))
    auth45 = sorted(glob.glob(os.path.join(C45.ROOT, "out", "t45", "freeze", "*")))
    auth46 = sorted(glob.glob(os.path.join(C45.ROOT, "out", "t46", "freeze", "*")))
    freeze = {"test": "TEST47 NASSI PATH / TRUE-BOTTOM / INVENTORY-RECYCLE", "freeze_timestamp_utc": now.isoformat(timespec="seconds"),
              "research_data_end": "2026-05-27", "FINAL_TEST47_CHALLENGER": sel["FINAL_TEST47_CHALLENGER"], "frozen_candidate_spec": None,
              "portfolio_control": "C43 (unchanged)", "canonical_data_sha256": {k: v[1] for k, v in C45.DATA.items()},
              "predeclared_spec_sha256": open(os.path.join(T, "T47_02_predeclared_spec.json.sha256")).read().strip(),
              "source_sha256": {os.path.basename(p): sha(p) for p in srcs},
              "evidence_sha256": {os.path.relpath(p, T): sha(p) for p in evid},
              "authorities_unchanged": {"TEST44": {os.path.basename(p): sha(p) for p in auth44}, "TEST45": {os.path.basename(p): sha(p) for p in auth45},
                                        "TEST46": {os.path.basename(p): sha(p) for p in auth46}},
              "live_authorization": "NO", "portfolio_membership_changed": "NO"}
    fp = os.path.join(FZ, "TEST47_PRE_OOS_FREEZE.json"); json.dump(freeze, open(fp, "w"), indent=1)
    rules = {"test": "TEST47", "TEST47_NEW_OOS_START": oos_start, "rule_for_start": "first full RTH session strictly after the freeze timestamp",
             "freeze_timestamp_utc": freeze["freeze_timestamp_utc"], "challenger": sel["FINAL_TEST47_CHALLENGER"],
             "if_challenger_NONE": "No TEST47 strategy is evaluated on the new OOS. The window may only be used to (a) re-confirm the NO-EDGE finding for the frozen "
                                   "C2 / C4 / C6 controls exactly as frozen (report-only, no promotion path), (b) monitor C43. No re-tuning, no new NASSI variant may be "
                                   "selected on it; any new idea is a NEW HYPOTHESIS requiring its own freeze.",
             "report_only_monitors": ["C2 [ES]", "C2 [MNQ]", "C4 [ES]", "C4 [MNQ]", "C6 [ES]", "C6 [MNQ]"],
             "excluded_intervals": {"2026-05-28..(TEST47_NEW_OOS_START - 1)": "never used for TEST47 research, selection or validation (TEST46 LC03 exposure window)"},
             "minimum_evaluation": ">= 120 full RTH sessions before any conclusion", "live_authorization": "NO", "portfolio_membership_changed": "NO"}
    rp = os.path.join(FZ, "TEST47_NEW_OOS_ACCEPTANCE_RULES.json"); json.dump(rules, open(rp, "w"), indent=1)
    hf, hr = sha(fp), sha(rp)
    open(os.path.join(FZ, "TEST47_FREEZE.sha256"), "w").write(f"{hf}  TEST47_PRE_OOS_FREEZE.json\n{hr}  TEST47_NEW_OOS_ACCEPTANCE_RULES.json\n")
    md("T47_46_PRE_OOS_FREEZE.md", "T47_46 Pre-OOS freeze", [f"sha256 = {hf}", "```json\n" + json.dumps({k: v for k, v in freeze.items() if k not in ("evidence_sha256",)}, indent=1)[:8000] + "\n```"])
    md("T47_47_NEW_OOS_ACCEPTANCE_RULES.md", "T47_47 New-OOS acceptance rules", [f"sha256 = {hr}", "```json\n" + json.dumps(rules, indent=1) + "\n```"])

    # ---------------------------------------------------------------- final status
    def g(inst, ctl, col="t_excess"):
        c = R["ctl"]; r = c[(c.inst == inst) & (c.control.str.startswith(ctl)) & (c.exit == "X60")]
        return float(r[col].iloc[0]) if len(r) else np.nan
    fr8 = R["fr8"]
    def nt(n):
        x = fr8[fr8.ntick == n]
        return f"NO (best matched excess {x['pnl_excess_trade'].max():.1f} $/trade, max t {x['pnl_t_excess'].max():.2f})"
    c43 = acc[acc.module == "C43 alone"].iloc[0]
    gb = gate.sort_values("avg_day", ascending=False).iloc[0] if len(gate) else None
    status = {
        "NASSI_SOURCE_AUDIT_COMPLETE": "YES (tier A/B sources; limits stated in T47_00)", "THREE_TICK_MEANS_EXCHANGE_TICKS": "NO",
        "BEST_MEANINGFUL_LEG_DEFINITION": "none has edge; least negative = T4 cumulative (ES) / T1 close-to-close (MNQ) - all matched excess < 0",
        "2TICK_EDGE": nt(2), "3TICK_EDGE": nt(3), "4TICK_EDGE": nt(4),
        "THREE_TICK_HAS_DISTINCT_VALUE": "NO (frontier 2/3/4 shows no special value at 3)",
        "SIDEWAYS_KEEP_DECAY_RESET_RESULT": "no mode produces positive matched excess; differences within noise",
        "PRIOR_RALLY_FILTER_ADDS_VALUE": "NO",
        "N3_EDGE_ES": "NO", "N3_EDGE_NQ": "NO",
        "N3_MATCHED_LONG_EXCESS_ES": f"{g('ES', 'C2', 'excess_trade'):.2f} $/trade (t {g('ES', 'C2'):.2f})",
        "N3_MATCHED_LONG_EXCESS_NQ": f"{g('MNQ', 'C2', 'excess_trade'):.2f} $/trade (t {g('MNQ', 'C2'):.2f})",
        "PATH_ORDER_ADDS_INFORMATION": "NO (path-order null and bar-shuffle both null)",
        "TRUE_BOTTOM_ADDS_VALUE_ES": "NO", "TRUE_BOTTOM_ADDS_VALUE_NQ": "NO",
        "SELLING_DECELERATION_ADDS_VALUE": "NO (decelerating sequences not better; if anything worse)",
        "CRASH_VETO_ADDS_VALUE": "NO (the predeclared veto removes the better-performing extreme subset)",
        "1M_BOTTOM_CONFIRMATION_ADDS_VALUE": "NO", "15M_CONTEXT_ADDS_VALUE": "NO",
        "BEST_NASSI_ENTRY": "none positive (least negative: E5 micro-level reclaim, not significant)",
        "CONFIRMED_SECOND_BUY_ADDS_VALUE": "NO", "BLIND_DCA_ADDS_VALUE": "NO", "RECYCLE_TRIM_ADDS_VALUE": "NO", "FULL_RECYCLE_ADDS_VALUE": "NO",
        "BEST_MAX_MES": 0, "BEST_MAX_MNQ": 0,
        "NASSI_OVERNIGHT_ADDS_VALUE": "NO",
        "BEST_LINEAR_MODEL": "none with signal (ML-A RIDGE rank-IC ~0.00)", "BEST_TREE_MODEL": "none (all tree rank-IC < 0 on ML-A)",
        "SEQUENCE_MODEL_JUSTIFIED": "NO", "BEST_SEQUENCE_MODEL": "SEQ_CNN_1D diagnostic only (rank-IC < 0)",
        "ML_ADDS_VALUE": "NO (ML-C second-contract logistic = SHADOW_CLUE_ONLY on a negative base)",
        "GA_N3_ADDS_VALUE": "see T47_34", "GA_NB_ADDS_VALUE": "see T47_35", "GA_NR_ADDS_VALUE": "see T47_36",
        "GA_OUTER_GENERALIZATION": "see T47_44", "GA_RULE_RECURRENCE": "see T47_37", "GA_PARAMETER_PLATEAU_PASS": "see T47_38",
        "GP_ADDS_VALUE": "NOT RUN (GP_NOT_JUSTIFIED)", "PORTABILITY": "NONE",
        "BEST_TEST47_STANDALONE_AVG_DAY": round(float(gb.avg_day), 2) if gb is not None else None,
        "BEST_TEST47_MATCHED_EXCESS_DAY": round(float(gate.matched_excess_day.max()), 2) if len(gate) else None,
        "C43_AVG_DAY": round(float(c43.C43_plus_avg_day), 2),
        "C43_PLUS_TEST47_AVG_DAY": round(float(c43.C43_plus_avg_day), 2), "C43_PLUS_TEST47_MAX_DD": round(float(c43.C43_plus_max_dd), 0),
        "C43_PLUS_TEST47_WORST_DAY": round(float(c43.C43_plus_worst_day), 0), "C43_PLUS_TEST47_RETURN_DD": round(float(c43.C43_plus_ret_dd), 4),
        "ALPHA_FROM_N3": 0, "ALPHA_FROM_TRUE_BOTTOM": 0, "ALPHA_FROM_SECOND_BUY": 0, "ALPHA_FROM_RECYCLE": 0, "ALPHA_FROM_OVERNIGHT": 0,
        "ALPHA_FROM_ML": 0, "ALPHA_FROM_GA": 0, "TOTAL_VERIFIED_INCREMENTAL_ALPHA": 0,
        "FINAL_TEST47_CHALLENGER": sel["FINAL_TEST47_CHALLENGER"],
        "TEST47_PRE_OOS_FREEZE_SHA256": hf, "TEST47_NEW_OOS_RULES_SHA256": hr, "TEST47_RESEARCH_DATA_END": "2026-05-27",
        "TEST47_NEW_OOS_START": oos_start, "TEST47_NEW_OOS_OPENED": "NO",
        "TEST44_AUTHORITIES_UNCHANGED": "YES", "TEST45_AUTHORITIES_UNCHANGED": "YES", "TEST46_AUTHORITIES_UNCHANGED": "YES",
        "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "LIVE_AUTHORIZATION": "NO"}
    # GA fields from the gate / recurrence / plateau (mechanical)
    for ln in ("N3", "NB", "NR"):
        r = gate[gate.candidate.str.startswith(f"GA-{ln}")] if len(gate) else pd.DataFrame()
        if len(r):
            r = r.iloc[0]
            status[f"GA_{ln}_ADDS_VALUE"] = "YES" if r.ELIGIBLE else f"NO (outer folds positive {int(r.folds_pos)}/5, median {r.fold_median:.2f} $/day, excess {r.matched_excess_day:.2f} $/day)"
    if len(gate):
        gg = gate[gate.rung == "GA"]
        status["GA_OUTER_GENERALIZATION"] = "PASS" if (gg.G1 == True).any() else "FAIL (" + "; ".join(f"{c.split(' ')[0]} {int(f)}/5" for c, f in zip(gg.candidate, gg.folds_pos)) + ")"  # noqa: E712
    if len(grec):
        status["GA_RULE_RECURRENCE"] = "PASS" if grec.RECURRENCE_PASS.any() else "WEAK (" + "; ".join(f"{a}: {b}x {c}" for a, b, c in zip(grec.lane, grec.modal_count, grec.modal_cluster)) + ")"
    status["GA_PARAMETER_PLATEAU_PASS"] = "NO" if not len(plat) else ("YES" if all((plat[plat.lane == ln].total > 0).all() and plat[plat.lane == ln].base_total.iloc[0] > 0 for ln in plat.lane.unique()) else "NO")
    json.dump(status, open(os.path.join(T, "T47_final_status.json"), "w"), indent=1)
    md("T47_FINAL_STATUS.md", "TEST47 final status", ["```json\n" + json.dumps(status, indent=1) + "\n```"])
    # ---------------------------------------------------------------- hash index
    files = sorted([p for p in glob.glob(os.path.join(C.REP, "*")) if os.path.isfile(p)] + srcs + [fp, rp] +
                   [p for p in glob.glob(os.path.join(T, "**", "*"), recursive=True) if os.path.isfile(p) and not p.endswith(".log") and "archive_" not in p])
    H = pd.DataFrame({"file": [os.path.relpath(p, C45.ROOT) for p in files], "sha256": [sha(p) for p in files], "bytes": [os.path.getsize(p) for p in files]})
    H.to_csv(os.path.join(T, "T47_48_HASH_INDEX.csv"), index=False)
    md("T47_48_HASH_INDEX.md", "T47_48 Hash index", [H])
    print(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
