"""Autonomous program close-out: registries (TEST54, survivor library, budget), $600/day scaling + capital frontier, program freeze,
future-OOS acceptance rules, final program report.  FINAL_PROGRAM_OOS_START = first full RTH session strictly after the freeze."""
import datetime
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
from t43 import instruments  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402

FZ = os.path.join(P.PROG, "freeze"); os.makedirs(FZ, exist_ok=True)


def main():
    # ---------------------------------------------------------------- TEST54 + libraries
    g54 = pd.read_csv(os.path.join(C45.ROOT, "out/test54/T54_gate.csv")).iloc[0]
    P.reg_append("AUTONOMOUS_TEST_REGISTRY", [{"test": "TEST54", "hypothesis": "TEST53 ensemble inside ONE total MNQ target (C43 + ensemble <= 2)",
                                               "prereg_hash": open(os.path.join(C45.ROOT, "out/test54/TEST54_PREREGISTRATION.json.sha256")).read()[:16],
                                               "result": f"FAIL G4 (ret/DD {g54.comb_ret_dd:.4f} < {g54.C43_ret_dd:.4f}) and G8 (year share {g54.max_year_share:.2f})",
                                               "survivor_count": 0, "best_clue": "under the practical integer frontier the ensemble adds +13 $/day but lowers C43 ret/DD",
                                               "next_test_reason": "STOP: saturation criteria B and C met (see program report)"}], key="test")
    P.reg_append("REJECTED_FAMILY_REGISTRY", [{"family": "mnq_long_shadow_ensemble", "mechanism": "M1-M4 combined (TEST52-54)", "test": "TEST52/53/54",
                                               "reason_rejected": "fails G4 in every construction (uncapped worst day; capped ret/DD 0.0080; total-cap ret/DD 0.0067)",
                                               "sample_size": "1300-2100 signals (2021+)", "outer_fold_result": "4-5/5 folds positive", "retest_forbidden": "YES on 2019-2026-05 data",
                                               "reopen_requires": "independent confirmation on the program OOS (report-only monitor)"}], key="family")
    surv = pd.DataFrame([{"ID": k, "instrument": "MNQ", "mechanism": v, "direction": "LONG", "status": "SHADOW (not a survivor)"} for k, v in {
        "M1_GA-AC": "compression arm -> expansion / higher-low breakout, hold to 16:00 (TEST48)",
        "M2_GA-CT": "HTF-bull day, not near session low, late morning -> next 09:31 open (TEST49)",
        "M3_GA-VX": "compression -> upside expansion with box stop (TEST50)",
        "M4_MNQ_OPEN_DRIVE": "MNQ up >= 0.25 ATRd with efficiency >= 0.5 at 10:00 -> 16:15 (TEST49)",
        "ENSEMBLE_TEST53": "M1-M4 as one capped MNQ target + day governor"}.items()])
    surv.to_csv(P.REG["SURVIVOR_LIBRARY"], index=False)
    # ---------------------------------------------------------------- scaling + capital frontier (final portfolio = C43 alone)
    sess = pd.DatetimeIndex(C45.build_panel()["sessions"])
    ch = C45.champion_daily()
    x = ch.pnl.reindex(sess).fillna(0.0).values
    st = pd.read_csv(os.path.join(C45.ROOT, "out/t45/baseline/champion_session_state.csv"), index_col=0, parse_dates=True).reindex(sess).fillna(0)
    mes, mnq = instruments.PROFILES["MES"], instruments.PROFILES["MNQ"]
    on_margin = (st.pES_end * mes["ibkr_overnight"] + st.pMNQ_end * mnq["ibkr_overnight"]).values
    peak_es = int(st[[c for c in st.columns if c.startswith("pES")]].values.max()); peak_nq = int(st[[c for c in st.columns if c.startswith("pMNQ")]].values.max())
    rows = []
    for k in (1, 1.25, 1.5, 2, 3, 4, 6, 8, 11.43):
        r = P.risk(k * x)
        rows.append({"scale": k, "integer_executable": float(k).is_integer(), "avg_day": r["avg_day"], "max_dd": r["max_dd"], "worst_day": r["worst_day"],
                     "ret_dd": r["ret_dd"], "peak_MES": peak_es * k, "peak_MNQ": peak_nq * k, "peak_overnight_margin": float(on_margin.max() * k),
                     "peak_margin_share_150k": float(on_margin.max() * k / 150000),
                     "primary_env_ok (DD<=15k, worst>=-3k)": bool(r["max_dd"] <= 15000 and r["worst_day"] >= -3000),
                     "tight_env_ok (10k/-2k)": bool(r["max_dd"] <= 10000 and r["worst_day"] >= -2000),
                     "aggressive_env_ok (20k/-5k)": bool(r["max_dd"] <= 20000 and r["worst_day"] >= -5000)})
    SC = pd.DataFrame(rows); SC.to_csv(os.path.join(P.PROG, "SCALING_FRONTIER.csv"), index=False)
    base = P.risk(x); dd_pct = base["max_dd"] / 150000
    scale600 = 600 / base["avg_day"]
    cap = pd.DataFrame([{"capital": c, "scale_at_same_pct_DD": c / 150000, "expected_avg_day": base["avg_day"] * c / 150000,
                         "max_dd": base["max_dd"] * c / 150000} for c in (150000, 200000, 250000, 300000, 500000, 1000000, round(150000 * scale600, -3))])
    cap.to_csv(os.path.join(P.PROG, "CAPITAL_FRONTIER.csv"), index=False)
    P.reg_append("PORTFOLIO_CANDIDATE_FRONTIER", [{"candidate": "C43 + TEST54 ensemble (total MNQ<=2)", "avg_day": round(g54.comb_avg_day, 2), "max_dd": round(g54.comb_max_dd),
                                                   "worst_day": round(g54.comb_worst_day), "ret_dd": round(g54.comb_ret_dd, 4), "status": "SHADOW (fails G4/G8)"}], key="candidate")
    B = P.reg_load("RESEARCH_BUDGET_LOG")
    prog = B[B.test.isin(["TEST48", "TEST49", "TEST50", "TEST51", "TEST52", "TEST53", "TEST54"])]
    tot = {"TOTAL_HYPOTHESES_TESTED": int(prog.hypotheses.sum()), "TOTAL_ML_CONFIGS": int(prog.ml_configs.sum()), "TOTAL_VALID_GENOMES": int(prog.valid_genomes.sum()),
           "TOTAL_FINALISTS": int(prog.finalists.sum()), "INCL_TEST45_47_GENOMES": int(B.valid_genomes.sum())}
    # ---------------------------------------------------------------- freeze
    now = datetime.datetime.now(datetime.timezone.utc)
    oos = first_rth_after(now)
    files = sorted(glob.glob(os.path.join(C45.SRC, "prog_*.py")) + glob.glob(os.path.join(C45.SRC, "t4[89]_*.py")) + glob.glob(os.path.join(C45.SRC, "t5[0-4]_*.py"))
                   + glob.glob(os.path.join(C45.SRC, "lane_*.py")) + glob.glob(os.path.join(C45.ROOT, "out", "test5*", "*PREREGISTRATION.json*"))
                   + glob.glob(os.path.join(C45.ROOT, "out", "test4[89]", "*PREREGISTRATION.json*")) + list(P.REG.values())
                   + [os.path.join(P.PROG, "SCALING_FRONTIER.csv"), os.path.join(P.PROG, "CAPITAL_FRONTIER.csv")])
    evid = sorted(p for d in ("test48", "test49", "test50", "test51", "test52", "test53", "test54") for p in glob.glob(os.path.join(C45.ROOT, "out", d, "**", "*"), recursive=True)
                  if os.path.isfile(p) and not p.endswith(".log") and "archive_" not in p)
    auth = {t: {os.path.basename(p): P.sha(p) for p in sorted(glob.glob(os.path.join(C45.ROOT, "out", t, "freeze", "*")))} for t in ("t45", "t46", "t47")}
    auth["t44"] = {os.path.basename(p): P.sha(p) for p in sorted(glob.glob(os.path.join(C45.ROOT, "out", "t44", "*FREEZE*")) + glob.glob(os.path.join(C45.ROOT, "out", "t44", "*RULES*")))}
    freeze = {"program": "AUTONOMOUS ES/NQ LONG-ALPHA PROGRAM (TEST48..TEST54)", "freeze_timestamp_utc": now.isoformat(timespec="seconds"),
              "research_data_end": "2026-05-27", "FINAL_PROGRAM_CHALLENGER": "NONE", "portfolio": "C43 control unchanged (no module added)",
              "shadow_monitors": surv.ID.tolist(), "budget": tot, "canonical_data_sha256": {k: v[1] for k, v in C45.DATA.items()},
              "source_and_registry_sha256": {os.path.relpath(p, C45.ROOT): P.sha(p) for p in files if os.path.isfile(p)},
              "evidence_sha256": {os.path.relpath(p, C45.ROOT): P.sha(p) for p in evid}, "authorities_unchanged_sha256": auth,
              "live_authorization": "NO", "portfolio_membership_changed": "NO"}
    fp = os.path.join(FZ, "FINAL_PROGRAM_PRE_OOS_FREEZE.json"); json.dump(freeze, open(fp, "w"), indent=1)
    rules = {"FINAL_PROGRAM_OOS_START": oos, "rule_for_start": "first full RTH session strictly after the program freeze timestamp",
             "freeze_timestamp_utc": freeze["freeze_timestamp_utc"], "challenger": "NONE",
             "policy": "No module is promoted. The OOS may be used only to (a) monitor C43 unchanged, (b) evaluate the frozen SHADOW monitors M1-M4 and the TEST53 "
                       "ensemble exactly as frozen (report-only). A shadow may be proposed for promotion only by a NEW numbered program after >= 250 full RTH "
                       "OOS sessions with: positive matched-long excess, C43+shadow ret/DD >= C43 ret/DD, combined worst day >= -3000, MaxDD <= 15000, total "
                       "MNQ <= 2 respected.  No re-tuning on OOS data.",
             "excluded_intervals": {"2026-05-28..(FINAL_PROGRAM_OOS_START-1)": "never used for research, selection or validation"},
             "live_authorization": "NO", "portfolio_membership_changed": "NO"}
    rp = os.path.join(FZ, "FINAL_PROGRAM_OOS_ACCEPTANCE_RULES.json"); json.dump(rules, open(rp, "w"), indent=1)
    hf, hr = P.sha(fp), P.sha(rp)
    open(os.path.join(FZ, "FINAL_PROGRAM_FREEZE.sha256"), "w").write(f"{hf}  FINAL_PROGRAM_PRE_OOS_FREEZE.json\n{hr}  FINAL_PROGRAM_OOS_ACCEPTANCE_RULES.json\n")
    # ---------------------------------------------------------------- report
    T = P.reg_load("AUTONOMOUS_TEST_REGISTRY")
    status = {"TEST47_RESULT": "NONE (gate 0/17; frozen, sha ecec4587...)", **{f"{t}_RESULT": r for t, r in zip(T.test, T.result) if t >= "TEST48"},
              "TOTAL_MAJOR_TESTS": 7, **{k.replace("INCL_", ""): v for k, v in tot.items()},
              "NEW_SURVIVOR_COUNT": 0, "NEW_ALPHA_MODULES": 0, "BEST_NEW_MODULE": "NONE (best shadow: M2 GA-CT MNQ bull-day hold to next open)",
              "BEST_NEW_MODULE_AVG_DAY": "n/a (shadow M2: +11.5 $/day stitched outer, not promotable)", "BEST_NEW_MODULE_MATCHED_EXCESS": "n/a (shadow M2: +5.4 $/day)",
              "BEST_NEW_MODULE_MAXDD": "n/a (shadow M2: 3,970)", "C43_AVG_DAY": round(base["avg_day"], 2), "BEST_FINAL_PORTFOLIO_COMPONENTS": "C43 only",
              "BEST_FINAL_PORTFOLIO_AVG_DAY": round(base["avg_day"], 2), "BEST_FINAL_PORTFOLIO_MAXDD": round(base["max_dd"]),
              "BEST_FINAL_PORTFOLIO_WORST_DAY": round(base["worst_day"]), "BEST_FINAL_PORTFOLIO_RETURN_DD": round(base["ret_dd"], 4),
              "BEST_FINAL_PORTFOLIO_MATCHED_BETA_EXCESS": "unchanged (C43 only)", "INCREMENTAL_AVG_DAY_VS_C43": 0,
              "PORTFOLIO_DAILY_CORRELATION_STRUCTURE": "C43 only; shadow modules M1-M4 pairwise corr -0.01..0.20, corr to C43 0.14-0.35",
              "BEST_PRACTICAL_MAX_MES": peak_es, "BEST_PRACTICAL_MAX_MNQ": peak_nq, "$150K_EXPECTED_AVG_DAY": round(base["avg_day"], 2),
              "SCALE_REQUIRED_FOR_$600_DAY": round(scale600, 2), "$600_DAY_WITHIN_PRIMARY_RISK_ENVELOPE": "NO",
              "ESTIMATED_CAPITAL_FOR_$600_AT_SIMILAR_RISK": round(150000 * scale600, -3),
              "FINAL_PROGRAM_CHALLENGER": "NONE", "FINAL_PROGRAM_PRE_OOS_FREEZE_SHA256": hf, "FINAL_PROGRAM_OOS_RULES_SHA256": hr,
              "FINAL_PROGRAM_OOS_START": oos, "NEW_OOS_OPENED": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(status, open(os.path.join(P.PROG, "FINAL_PROGRAM_STATUS.json"), "w"), indent=1)
    P.md("PROGRAM_00_FINAL_REPORT.md", "Autonomous ES/NQ long-alpha program - final report",
         ["```json\n" + json.dumps(status, indent=1) + "\n```", "Test registry:", T, "Rejected families:", P.reg_load("REJECTED_FAMILY_REGISTRY"),
          "Shadow clues:", P.reg_load("SHADOW_CLUE_REGISTRY"), "Shadow library:", surv, "Portfolio frontier:", P.reg_load("PORTFOLIO_CANDIDATE_FRONTIER"),
          "Scaling frontier (C43):", SC, "Capital frontier (same % DD):", cap, "Budget:", P.reg_load("RESEARCH_BUDGET_LOG"),
          "Stop reason: criteria B (no new promotable clue in TEST51-54; the ensemble clue was exhausted under the practical integer frontier) and C (remaining "
          "families are near-neighbours of rejected ones or need unavailable data: YM/RTY context, parity-blocked INDEX6 hold extension)."])
    print(json.dumps(status, indent=1)); print(SC.round(3).to_string()); print(cap.round(0).to_string())


if __name__ == "__main__":
    main()
