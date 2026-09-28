"""TEST98 Phase-1 report + status (reads Phase-1 outputs; no new economics)."""
import ast, json, os
import pandas as pd
D = "/home/user/lab/out/t98"; R = "/home/user/lab/reports/TEST98_PLUS"
V = pd.read_csv(f"{D}/P1_FEATURE_VERDICTS.csv"); B = pd.read_csv(f"{D}/P1_BASE_EVENT.csv"); C = pd.read_csv(f"{D}/P1_RESPONSE_CURVES.csv"); L = pd.read_csv(f"{D}/TEST98_RESEARCH_LEDGER.csv")
meta = json.load(open(f"{D}/P1_META.json"))
fam = lambda p: bool(V[V.family == p][["h6_COHERENT", "h12_COHERENT"]].any().any())
label_pred = [r.feature for r in V.itertuples() if (lambda lh: lh[0] > 0 or lh[1] < 0)(ast.literal_eval(r.h12_pstrong_ci))]
S = {"TEST": "TEST98_PRECONFIRM_PATH_QUALITY Phase 1", "PREREG_COMMIT": "12d9765",
     "PATH_QUALITY_ADDS_ALPHA": "NO", "EFFICIENCY_ADDS_VALUE": "NO" if not fam("PQ1") else "YES", "PERSISTENT_PRESSURE_ADDS_VALUE": "NO" if not fam("PQ2") else "YES",
     "LOW_DAMAGE_PATH_ADDS_VALUE": "NO" if not fam("PQ3") else "YES",
     "BREAKOUT_OVERSHOOT_STRUCTURE": "NONE (overshoot curve flat vs null F; rho 0.3 / 0.4, CI includes 0)",
     "VWAP_ACCEPTANCE_ADDS_VALUE": "NO (vwap_share12: +0.008 / +0.010 top-bottom, CI includes 0)",
     "OPEN_ACCEPTANCE_ADDS_VALUE": "NO (open_share_session rho 0.9 at 60 min, +0.011 top-bottom, CI -0.0036..+0.0245 -> not coherent; open_share12 degenerate bins)",
     "PRECONFIRM_FEATURES_PREDICT_FOLLOWTHROUGH": "NO under the preregistered definition (label prediction must coincide with economic coherence); "
                                                   f"label-only: {len(label_pred)} of {len(V)} features shift P(next bar STRONG) with CI excluding 0 "
                                                   "(largest: breakout-bar range/ATR5 +0.041, ER12 +0.018, failed probes -0.020) but none converts into "
                                                   "forward-return excess over the magnitude-matched null",
     "MAGNITUDE_NULL_SURVIVAL": "NO (no feature coherent vs null F; base fresh-breakout excess vs F ~ 0 by construction; gross 60-min 0.0038 ATR vs cost 0.0105)",
     "BEST_MARKET": "NONE (NO_EDGE in all four; RTY negative gross)", "BEST_PATH_FAMILY": "NONE (closest: PQ5 open acceptance / PQ4 open distance, CIs include 0)",
     "ML_ELIGIBLE": "NO (event count 23,560 >= 600 but no coherent path family survives null F)", "GA_ELIGIBLE": "NO",
     "DISTINCT_VARIANTS_TESTED": int(len(V)), "LEDGER_ROWS": int(len(L)), "FEATURE_BIN_DEFINITIONS": int(L.variant.nunique()), "ML_CONFIGS": 0, "GA_GENOMES": 0,
     "multiple_testing": f"{len(V)} features x 2 primary horizons = {2 * len(V)} coherence tests; 0 passed",
     "null_F_fallback_share": meta["levels_share"], "NEW_STRATEGY_PHASE_OPENED": "NO", "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1",
     "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO",
     "interpretation": "The information TEST97 saw in follow-through is not identifiable before the confirmation bar: pre-confirmation path features "
                       "predict WHICH breakouts get a strong next bar, but after holding move magnitude constant they do not predict forward returns "
                       "from the pre-confirmation entry; the follow-through information appears to be realised by the confirmation bar itself."}
json.dump(S, open(f"{D}/TEST98_PHASE1_STATUS.json", "w"), indent=1, default=str)
vc = ["feature", "family", "h6_rho", "h6_top_minus_bottom", "h6_ci_lo", "h6_ci_hi", "h12_rho", "h12_top_minus_bottom", "h12_ci_lo", "h12_ci_hi", "h12_years_same", "h12_inst_same",
      "h12_COHERENT", "h12_best_bin", "h12_best_xF", "h12_best_gross", "h12_pstrong_diff", "h12_pstrong_ci"]
bc = ["instrument", "n_events", "h2_mean", "h3_mean", "h4_mean", "h6_mean", "h9_mean", "h12_mean", "h1615_mean", "h6_xA", "h12_xA", "h12_xC", "h6_xF", "h12_xF", "cost_atr",
      "mfe60", "mae60", "mae60_p95", "t_mfe", "t_first_pos", "bar025", "bar050", "bar100", "newhigh60", "underwater_1615"]
lines = ["# TEST98_PRECONFIRM_PATH_QUALITY - Phase 1 results (prereg commit 12d9765)", "", "```json", json.dumps(S, indent=1, default=str), "```", "",
         "## Base event: fresh N=12 close-confirmed breakout (ATR_d units)", B[[c for c in bc if c in B]].to_markdown(floatfmt=".4f"), "",
         "## Feature verdicts (response vs magnitude-matched family null F; causal quintiles)", V[vc].to_markdown(floatfmt=".4f"), "",
         "## Response curves (pooled, 30 / 60 min)", C[C.horizon.isin(["h6", "h12"])][["feature", "horizon", "bin", "n", "xF", "gross", "p_next_strong", "p_next_bear"]].to_markdown(floatfmt=".4f")]
open(f"{R}/TEST98_PHASE1_REPORT.md", "w").write("\n".join(lines) + "\n"); print(json.dumps(S, indent=1, default=str))
