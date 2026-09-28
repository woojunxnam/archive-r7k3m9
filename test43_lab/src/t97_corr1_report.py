"""TEST97_AUDIT_CORRECTION_1 report + corrected final status (reads corr1 outputs; no economics)."""
import json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E
D = os.path.join(E.OUT, "corr1"); R = json.load(open(os.path.join(D, "CORR1_RESULTS.json")))
C = pd.read_csv(os.path.join(D, "C_W3_V1_FAMILY_NULL.csv")); DP = pd.read_csv(os.path.join(D, "D_W3_V3_PAIRED.csv")); DM = pd.read_csv(os.path.join(D, "D_W3_V3_PATH.csv"))
EI = pd.read_csv(os.path.join(D, "E_M04_INFO_TIMING.csv")); F = pd.read_csv(os.path.join(D, "F_FT2_POPULATION_AUDIT.csv")); FP = pd.read_csv(os.path.join(D, "F_FT2_VIRTUAL_PORTFOLIO.csv"))
G = pd.read_csv(os.path.join(D, "G_FT2_NULL_ROBUSTNESS.csv"))
S = {"CORRECTION": "TEST97_AUDIT_CORRECTION_1", "PREREG_COMMIT": "85f5bdc", **R["B"],
     "TEST97_PORTFOLIO_SURVIVOR": "NO",
     "FT2_STATUS": "DOWNGRADED - EVENT CLUE NOT ROBUST: 5,000-rep precision audit puts the h12 CI lower bound below 0 even with the original null "
                   "(-0.0009) and with causal monthly-expanding edges (-0.0033); strategy remains rejected; selection-exposed",
     "W3_V1_STATUS": "CORRECTED_HISTORICAL_CLUE (not promoted): with the preregistered k=0 family null, k=0.2 and k=0.3 at 16:15 show +0.029 ATR over "
                     "the close-above-open population (CI lower bound +0.0016, 8/8 and 7/8 years, gross > cost); 30 / 60-min horizons and k=0.1/0.5/0.75 "
                     "do not; vs null A the same events are only +0.007 ATR; 15 (k x horizon) cells tested",
     "W3_V3_FIRST_PULLBACK_STATUS": "NO SIGNIFICANT DIFFERENCE (previous 'worse than chase' RETRACTED - it compared different populations): on 3,763 "
                                    "matched sessions pullback-minus-chase at the same exit = +0.0058 ATR (CI -0.0045..+0.0161, 6/8 years); own 60-min "
                                    "horizons -0.003; ES / NQ negative, YM / RTY positive; pullback entry has lower 60-min MAE (0.18 vs 0.21 ATR)",
     "FOLLOW_THROUGH_INFORMATION_STATUS": "VALID CLUE (weak): confirmed minus unconfirmed at the same minute B +0.012 (h6, CI>0) / +0.014 (h12, CI>0); "
                                          "F +0.034 (h12, CI lower +0.0007); E and D CIs include 0",
     "FOLLOW_THROUGH_TIMING_STATUS": "NEGATIVE: on identical confirmed events and identical exit minutes the confirmation entry is worse than the original "
                                     "entry by 0.05 (B/C) to 0.13 (F) ATR (CIs exclude 0) - waiting pays up the confirmation bar; note the original-entry "
                                     "arm is conditioned on a later confirmation (hindsight population), so this measures the cost of waiting, not a "
                                     "tradeable original-entry edge",
     "RECOVERY_STACK_STATUS": "REJECT on the FT2 initial population (ADD1 < 0 in all four indices); standing rule: ADD1 <= 0 -> stop deeper stacking; "
                              "deeper blind-DCA outputs NOT USABLE (threshold scaled by units, deviates from prereg)",
     "FT2_POPULATION_AUDIT": R["F"], "PORTFOLIO_REPORTING": "VIRTUAL_ADDITIVE_DIAGNOSTIC only (no CAPACITY_VALID_PORTFOLIO)",
     "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
json.dump(S, open(os.path.join(E.OUT, "TEST97_PLUS_FINAL_STATUS_CORRECTED.json"), "w"), indent=1, default=str)
cp = C[C.instrument == "POOLED"][["k", "horizon", "n", "gross_mean", "xA", "xB1", "mean", "ci_lo", "ci_hi", "years_pos", "cost_atr", "CLUE"]].rename(columns={"mean": "x_family_k0"})
ci = C[C.instrument != "POOLED"].pivot_table(index=["k", "horizon"], columns="instrument", values="mean")
E.md("TEST97_AUDIT_CORRECTION_1_REPORT.md", "TEST97_AUDIT_CORRECTION_1 - corrected results (prereg commit 85f5bdc)", [
    "```json\n" + json.dumps(S, indent=1, default=str) + "\n```",
    "## C. W3_V1 volatility breakout vs preregistered k=0 family null (pooled; ATR_d)", cp, "per instrument (family-null excess)", ci,
    "## D. W3_V3 first pullback vs chase on identical sessions (paired B - A)", DP, "Note: at a common exit minute the paired difference equals the entry-price "
    "difference, so the h12-same-exit and 16:15 rows coincide by construction.", DM,
    "## E. M04 information vs timing (pooled)", EI[EI.instrument == "POOLED"],
    "## F. FT2 population / strict X60 audit", F, "### VIRTUAL_ADDITIVE_DIAGNOSTIC (not capacity valid)", FP,
    "## G. FT2 null robustness (5,000-rep date-clustered bootstrap)", G[G.instrument == "POOLED"],
    "## H. Position management governance", "```json\n" + json.dumps(R["H"], indent=1) + "\n```"])
# supersede the old count terminology in the TEST97 final status (keep the original file, add corrected fields)
p = os.path.join(E.OUT, "TEST97_PLUS_FINAL_STATUS.json"); old = json.load(open(p))
old.pop("TOTAL_TEST97_VARIANTS", None); old.update({k: R["B"][k] for k in ("TOTAL_TEST97_LEDGER_ROWS", "TOTAL_TEST97_DISTINCT_VARIANTS", "TOTAL_TEST97_ML_CONFIGS", "TOTAL_TEST97_GA_GENOMES")})
old["SUPERSEDED_BY"] = "TEST97_PLUS_FINAL_STATUS_CORRECTED.json (TEST97_AUDIT_CORRECTION_1)"; json.dump(old, open(p, "w"), indent=1, default=str)
print(json.dumps(S, indent=1, default=str))
