# INDEX_ML_GA_RECLAMATION_V1 — FINAL REPORT

```json
{
 "CURRENT_OFFICIAL_MAIN": "MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged)",
 "MAIN_AVG_DAY": "143.21 full sample (151.78 on the stitched window 2021-01-01..2026-05-27)",
 "MAIN_MAXDD": 13936,
 "MAIN_WORST_DAY": -4666,
 "MAIN_RET_DD": "0.01028 full / 0.01089 window",
 "TEST114_CLOCK_CORRECTION_STATUS": "CORRECTED (target FP[389] 15:59 -> C[389] 16:00 close); G1 xN -0.0074 ATR, still negative -> GHLZ CLOSED",
 "ENGINE_AUDIT": "PASS (no shared bug; no TEST99-115 result invalidated)",
 "CANDIDATE_BANK_MEMBERS": "C1_R1_TRAPPED_UNION, C2_P2_FAILED_FIRST, C3_P1_H2, C4_L2_FAMILY, C5_HTF1_30m, C6_AV_OR30, C7_L1_SWH60, C8_CHOCH_15m (+ REF_A2_ACD, REF_ORB15 reference only); event parity vs MASTER = PASS; frozen horizon 16:15 for all",
 "ML_ELIGIBLE_CANDIDATES": "all 8 (Tier A YES)",
 "ML_CONFIGS_RUN": 64,
 "GA_ELIGIBLE_CANDIDATES": "C1, C7 (nested ML Tier B), C4 (repeated deterministic clue)",
 "GA_GENOMES_RUN": 2592,
 "BEST_ML_CANDIDATE": "C1_R1_TRAPPED_UNION NESTED_SELECTED (C7 nested also Tier B)",
 "BEST_ML_STITCHED_AVG_DAY": 16.8,
 "BEST_ML_SLIP4": 7.92,
 "BEST_ML_MAXDD": 6895,
 "ML_VALUE_NOTE": "ML beat the deterministic take-all only for C7; for C1 the nested ML (16.80) is below take-all (20.44)",
 "BEST_GA_CANDIDATE": "C4_L2_FAMILY (GA_OVERFIT_CLUE_ONLY, stability 0.24)",
 "BEST_GA_STITCHED_AVG_DAY": 14.54,
 "GA_PASS": "NONE",
 "BEST_TRAPPED_SELLER_RESULT": "C2_P2_FAILED_FIRST take-all: 4.96 $/day after capacity, SLIP4 3.24, corr 0.26, 2022 +5,117 -> ROUTE B SMALL DIVERSIFIER; with winner pyramid 6.51 $/day -> ROUTES A and B",
 "BEST_LEVEL_FAILURE_RESULT": "C4_L2_FAMILY GA arm 12.21 $/day but only 2/5 folds -> STRESS FAIL",
 "BEST_HTF_RESULT": "C5_HTF1_30m take-all 6.54 $/day after capacity, SLIP4 -1.02 -> STRESS FAIL",
 "BEST_PULLBACK_RESULT": "C3_P1_H2: no Tier-B arm (take-all 3.03, SLIP4 -1.73)",
 "EVENT_CONDITIONED_HTF_VALUE": "SATURATED (0/12 coherent curves)",
 "BEST_RECOVERY_RESULT": "fresh-signal recovery: C1 ADD1 -11.14 $ -> STOP; C2 +20.38 (n 31, too small for exit tests); C7 +4.59 (exit architectures R1/R2 worse)",
 "BEST_WINNER_ADD_RESULT": "C2 winner pyramid ADD1 +14.59 $/add (n 197, SLIP4 +10.45, 4/5 folds, CI [-5.7,+34.1]); C1 +8.01 (n 1,615)",
 "ADD1_MARGINAL_EV_BY_CANDIDATE": {
  "C1_R1_TRAPPED_UNION|B_BLIND_DCA": 3.18,
  "C1_R1_TRAPPED_UNION|C_FRESH_RECOVERY": -11.14,
  "C1_R1_TRAPPED_UNION|D_WINNER_PYRAMID": 8.01,
  "C2_P2_FAILED_FIRST|B_BLIND_DCA": 23.29,
  "C2_P2_FAILED_FIRST|C_FRESH_RECOVERY": 20.38,
  "C2_P2_FAILED_FIRST|D_WINNER_PYRAMID": 14.59,
  "C7_L1_SWH60|B_BLIND_DCA": -12.83,
  "C7_L1_SWH60|C_FRESH_RECOVERY": 4.59,
  "C7_L1_SWH60|D_WINNER_PYRAMID": 3.15
 },
 "BEST_RELAXED_FRONTIER_MEMBERS": "MAIN + C2_P2_FAILED_FIRST (1 micro) + WINNER_PYRAMID ADD1  [FRONTIER_B; routes A and B]",
 "BEST_RELAXED_FRONTIER_AVG_DAY": 158.29,
 "BEST_RELAXED_FRONTIER_MAXDD": 14036,
 "BEST_RELAXED_FRONTIER_WORST_DAY": -4810,
 "BEST_RELAXED_FRONTIER_RET_DD": 0.01128,
 "BEST_RELAXED_FRONTIER_SLIP4": 156.0,
 "ALPHA_INCREMENT_VS_MAIN": "+6.51 $/day on the window = +4.96 ALPHA (C2 base) + 1.55 POSITION MANAGEMENT (add units); LEVERAGE 0; AVG_DAY_PER_$10K_MAXDD 112.77 vs Main 108.91 (RISK_NORMALIZED_INCREMENT +3.86)",
 "OTHER_FRONTIERS": {
  "FRONTIER_A": "C2+MGMTx2",
  "FRONTIER_C": "C2x1",
  "FRONTIER_D": "C1+MGMTx1"
 },
 "FRONTIER_D_NOTE": "C1+WINNER_PYRAMID gives the highest dollars under capacity (170.20 $/day, +18.42) but MaxDD 20,914 (1.50 x Main), ret/DD 0.00814 -> no route; not an improvement",
 "GAP_TO_600": 441.71,
 "GAP_TO_600_FULL_SAMPLE_EQUIV": 450.28,
 "TARGET_600_REACHED": "NO",
 "TOTAL_NEW_ML_CONFIGS": 64,
 "TOTAL_NEW_GA_GENOMES": 2592,
 "TOTAL_PORTFOLIO_COMBINATIONS": 45,
 "DEFLATED_SHARPE_STATUS": "COMPUTED: C2 DSR 0.85 (best), C1 0.49, C4 0.40, C7 0.51 - none >= 0.95",
 "PBO_STATUS": "COMPUTED (CSCV 16 blocks): C2 0.57, C1 0.78, C4 0.13, C7 0.67",
 "REALITY_CHECK_STATUS": "COMPUTED (White RC, stationary bootstrap): C2 p 0.028, C1 p 0.035, others >= 0.10",
 "INDEX_FULLY_SATURATED": "NO",
 "UNRESOLVED_LANE": "trapped-seller second resumption (C2_P2_FAILED_FIRST) + winner-pyramid ADD1 as a small diversifier: passes relaxed routes A/B on the stitched historical window (HISTORICAL + RELAXED_GATE SELECTION_EXPOSED; DSR 0.85, PBO 0.57) -> candidate for FORWARD SHADOW monitoring only; everything else saturated (deterministic, HTF, GHLZ, GA, recovery)",
 "CROSS_ASSET_RESEARCH_OPENED": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO"
}
```

## Phase summary
- P0A TEST114 exact-clock correction: still negative -> GHLZ closed.  P0B engine audit PASS.
- P1 bank frozen with exact MASTER event parity.
- P3 nested ML (64 configs): nested Tier B only C1 and C7; ML rarely beats the take-all population.
- P4 event-conditioned HTF: saturated.
- P5 exhaustive structural GA (2,592 genomes): no stable genome (C1/C4 GA_OVERFIT_CLUE_ONLY).
- P6 consensus: 6 candidates, matched-beta excess ~ raw dollars, but the plain ORB reference earns more than any candidate; DSR < 0.95 everywhere.
- P7 stress: C1, C2, C7 pass; only C2 passes a portfolio route (B).
- P8 management: fresh recovery stops for C1; winner pyramid positive for C1/C2 (CIs include 0).
- P9: best relaxed frontier = Main + C2 + winner pyramid: +6.51 $/day, ret/DD 0.01128 vs 0.01089, MaxDD 14,036 vs 13,936.

Every accepted item: HISTORICAL_SELECTION_EXPOSED = YES, RELAXED_GATE_SELECTION_EXPOSED = YES.  Official Main unchanged.  Cross-asset not opened (INDEX not fully saturated; cross-asset would in any case need user authorization).
