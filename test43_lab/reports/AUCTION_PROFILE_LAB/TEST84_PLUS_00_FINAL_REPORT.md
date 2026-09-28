# TEST84+ AUCTION-PROFILE / MOMENTUM-FOLLOW / PRESS-WINNER - final report

```json
{
 "T61_R1C_FROZEN": "YES",
 "T61_OOS_USED_IN_RESEARCH": "NO",
 "TEST84_RESULT": "QA PASS: prefix invariance 1800 samples / 0 mismatches; ES full-contract volume clean; NQ signal = MNQ volume PROXY",
 "TEST85_RESULT": "ATLAS: 2 profile mechanisms qualify (MNQ PG12_DOWN_STACK 16:00 / 30m, MNQ PI_DIVERGE 60m; >= 2/3 proxies); 0 momentum mechanisms qualify; ES PH_PRICE_NULL (next open) excluded as a null of a rejected family",
 "TEST86_RESULT": "FAIL: PG12 +3.42 $/day (5/5 folds, SLIP4 +2.84) plateau fails at 60m hold + year share 0.55; PI_DIVERGE +2.45 $/day plateau fails; T61 increments +2.96 / +1.65 < +10",
 "TEST87_RESULT": "NOT RUN: POC migration (PA1 / PA2 / PC1 / PC2) did not qualify at TEST85",
 "TEST88_RESULT": "NOT RUN: HVN / LVN travel (PD / PE) did not qualify (profile target exits negative)",
 "TEST89_RESULT": "NOT RUN: prior-VAH acceptance (PB1-PB4) did not qualify",
 "TEST90_RESULT": "NOT RUN: rising-POC pullback (PF) did not qualify",
 "TEST91_RESULT": "ML-B (economic target) on the 2 qualifying events: PG12 HGB +6.01 $/day (+7.69 2021+), 5/5 folds, 8/9 models standalone-pass, T61 increment +6.01 < +10 -> not a survivor; PI_DIVERGE <= +2.3 $/day",
 "TEST92_RESULT": "NOT RUN: GA not justified (no deterministic survivor)",
 "TEST93_RESULT": "no survivor to add; T61 incremental gates computed inside TEST86 / TEST91",
 "PROFILE_DATA_QUALITY": "ES zero-volume 0.941%, missing 0.230%, 7 abnormal days, 27 roll sessions (roll/non-roll volume 0.85); MNQ volume grows ~10x 2019->2026 (proxy only)",
 "BEST_VOLUME_ALLOCATION_PROXY": "VP-B uniform-range (PG12); VP-B / VP-C agree closely, VP-A (single price) differs",
 "PROXY_ROBUSTNESS": "PG12 qualifies under VP-A and VP-B (VP-C misses only the 40-per-fold sample by 1); PI_DIVERGE under VP-A and VP-C at 60m; all other mechanisms fail in every proxy",
 "BEST_PROFILE_TYPE": "P2 developing vs P1 prior RTH (value stacking)",
 "BEST_VALUE_AREA": "70% (65 / 75 neighbours positive and >= 60% of base for PG12)",
 "POC_MIGRATION_EXCESS": "MNQ PA1_POC_UP [VP-B h60] net +0.55, SLIP4 -2.45, B(momentum) +2.53, C(volume) +2.05, 4/5, n 1714 | ES PA1_POC_UP [VP-B h1300] net -2.22, SLIP4 -9.72, B(momentum) +2.20, C(volume) +1.24, 5/5, n 1518 || developing: MNQ PC1_DPOC_UP [VP-C h1600] net +11.37, SLIP4 +8.37, B(momentum) +4.56, C(volume) +7.88, 3/5, n 1398 | ES PC1_DPOC_UP [VP-C h1100] net +0.13, SLIP4 -7.37, B(momentum) +2.38, C(volume) +2.76, 4/5, n 920",
 "VALUE_ACCEPTANCE_EXCESS": "MNQ PB3_VAH_TWO [VP-C h30] net +0.19, SLIP4 -2.81, B(momentum) +0.19, C(volume) +0.29, 3/5, n 1114 | ES PB3_VAH_TWO [VP-C h60] net +2.32, SLIP4 -5.18, B(momentum) +2.29, C(volume) +2.68, 5/5, n 1093 || accept: MNQ PB4_VAH_ACCEPT [VP-C h60] net +2.05, SLIP4 -0.95, B(momentum) +1.79, C(volume) +1.91, 2/5, n 999 | ES PB4_VAH_ACCEPT [VP-B h60] net -1.35, SLIP4 -8.85, B(momentum) +0.75, C(volume) +0.22, 3/5, n 979",
 "LVN_TRAVEL_EXCESS": "MNQ PD_HVN_LVN_TRAVEL [VP-B h1615] net +23.30, SLIP4 +20.30, B(momentum) +17.95, C(volume) +20.25, 3/5, n 310 | ES PD_HVN_LVN_TRAVEL [VP-A h60] net -2.26, SLIP4 -9.76, B(momentum) +1.62, C(volume) +0.88, 3/5, n 534 || LVN break: MNQ PE_LVN_BREAK [VP-B h60] net +8.57, SLIP4 +5.57, B(momentum) +14.75, C(volume) +16.57, 2/5, n 105 | ES PE_LVN_BREAK [VP-A h1615] net +5.12, SLIP4 -2.38, B(momentum) +9.57, C(volume) +7.94, 4/5, n 263",
 "HVN_TARGET_VALUE": "NEGATIVE: exit at next HVN ES/VP-A -5.1, ES/VP-B -9.2, ES/VP-C -6.1, MNQ/VP-A -7.2, MNQ/VP-B -5.2, MNQ/VP-C -6.3 vs hold 16:15 ES/VP-A -1.5, ES/VP-B -8.9, ES/VP-C -3.2, MNQ/VP-A +4.8, MNQ/VP-B +23.3, MNQ/VP-C +8.5 $/trade",
 "VALUE_STACKING_EXCESS": "MNQ PG12_DOWN_STACK [VP-C h1600] net +17.86, SLIP4 +14.86, B(momentum) +21.16, C(volume) +15.18, 5/5, n 336 | ES PG12_DOWN_STACK [VP-B h1600] net +1.74, SLIP4 -5.76, B(momentum) +4.15, C(volume) +4.91, 3/5, n 325 || up-stack: MNQ PG_UP_STACK [VP-A h1100] net -8.22, SLIP4 -11.22, B(momentum) -3.22, C(volume) -4.20, 1/5, n 542 | ES PG_UP_STACK [VP-A h30] net -6.63, SLIP4 -14.13, B(momentum) -2.45, C(volume) -1.74, 2/5, n 620",
 "PROFILE_COMPRESSION_EXCESS": "MNQ PH_VALUE_COMPRESS_EXPAND [VP-C h1300] net -0.27, SLIP4 -3.27, B(momentum) +0.78, C(volume) -1.00, 2/5, n 218 | ES PH_VALUE_COMPRESS_EXPAND [VP-B h1300] net -0.22, SLIP4 -7.72, B(momentum) +3.12, C(volume) +2.07, 4/5, n 255 || PRICE-RANGE NULL: MNQ PH_PRICE_NULL [VP-A h1600] net +5.68, SLIP4 +2.68, B(momentum) +3.47, C(volume) +2.42, 3/5, n 842 | ES PH_PRICE_NULL [VP-A h1300] net +0.16, SLIP4 -7.34, B(momentum) +2.92, C(volume) +2.82, 4/5, n 295 -> value compression adds nothing over price range",
 "PRICE_POC_CONFIRMATION_EXCESS": "MNQ PI_PRICE_POC_CONFIRM [VP-A h1600] net +32.40, SLIP4 +29.40, B(momentum) +13.51, C(volume) +23.12, 3/5, n 270 | ES PI_PRICE_POC_CONFIRM [VP-A h60] net +2.93, SLIP4 -4.57, B(momentum) +3.16, C(volume) +7.26, 2/5, n 317 || divergence: MNQ PI_DIVERGE [VP-A h60] net +4.01, SLIP4 +1.01, B(momentum) +2.44, C(volume) +5.37, 5/5, n 965 | ES PI_DIVERGE [VP-C h1300] net -0.66, SLIP4 -8.16, B(momentum) +3.55, C(volume) +3.34, 5/5, n 737 -> opposite of the hypothesis",
 "PROFILE_VS_GENERIC_MOMENTUM": "B excess mostly small positive but fails costs / folds; only PG12 and PI_DIVERGE beat momentum robustly at event level",
 "PROFILE_VS_GENERIC_VOLUME": "C (relative-volume matched) excess tracks B -> raw volume level does not explain the profile events",
 "BEST_ENTRY": "IMMEDIATE (one-bar acceptance similar; no plateau for it)",
 "BEST_HOLD": "16:00 (PG12) / 60m (PI_DIVERGE)",
 "ES_PROFILE_RESULT": "NONE",
 "NQ_PROFILE_RESULT": "NONE (MNQ-volume proxy; PG12 clue)",
 "TRADES_PER_DAY": 0.194,
 "SIDES_PER_DAY": 0.387,
 "SLIP4_AVG_DAY": 2.84,
 "ML_RUN": "YES (TEST91, 18 configs)",
 "GA_RUN": "NO",
 "NEW_PROFILE_SURVIVOR": "NONE",
 "T61_PLUS_PROFILE_AVG_DAY": 128.04,
 "T61_PLUS_PROFILE_INCREMENTAL_DAY": 2.96,
 "T61_PLUS_PROFILE_MAXDD": 14233,
 "T61_PLUS_PROFILE_WORST_DAY": -4347,
 "T61_PLUS_PROFILE_RET_DD": 0.009,
 "CORR_PROFILE_TO_T61": 0.105,
 "PROFILE_MODULE_OOS_START": "n/a (no survivor)",
 "MOMENTUM_FAMILY_RESULT": "NO QUALIFYING MECHANISM (0 of 23 event types x 2 instruments pass net + SLIP4 + momentum-null + folds + n>=300)",
 "BEST_MOMENTUM_MECHANISM": "MNQ M68_DECEL [PRICE h1600] net +36.61, SLIP4 +33.61, B(momentum) +21.49, C(volume) +18.26, 4/5, n 257 (n < 300 -> not qualifying)",
 "OPENING_IMPULSE_VALUE": "MNQ M1_OPEN_IMPULSE [PRICE h1615] net +39.77, SLIP4 +36.77, B(momentum) -2.41, C(volume) +31.61, 1/5, n 192 | ES M1_OPEN_IMPULSE [PRICE h1615] net +30.68, SLIP4 +23.18, B(momentum) +15.80, C(volume) +24.63, 3/5, n 143 -> MNQ value = generic momentum (B < 0)",
 "PERSISTENCE_VALUE": "MNQ M3_PERSIST [PRICE h30] net +4.56, SLIP4 +1.56, B(momentum) -0.53, C(volume) +2.36, 4/5, n 351 | ES M3_PERSIST [PRICE h30] net -2.87, SLIP4 -10.37, B(momentum) -1.10, C(volume) -1.12, 2/5, n 301 || one-time: n/a | n/a",
 "SECOND_IMPULSE_VALUE": "MNQ M5_SECOND_IMPULSE [PRICE h1100] net -2.99, SLIP4 -5.99, B(momentum) +4.47, C(volume) +3.04, 3/5, n 65 | ES M5_SECOND_IMPULSE [PRICE h30] net -4.24, SLIP4 -11.74, B(momentum) -1.98, C(volume) -0.81, 3/5, n 248",
 "FAILED_PULLBACK_RESUMPTION_VALUE": "MNQ M6_FAILED_PULLBACK [PRICE h1600] net +13.22, SLIP4 +10.22, B(momentum) +2.42, C(volume) +9.66, 3/5, n 502 | ES M6_FAILED_PULLBACK [PRICE h30] net -4.10, SLIP4 -11.60, B(momentum) -0.20, C(volume) -0.70, 3/5, n 516",
 "MULTITIMEFRAME_ALIGNMENT_VALUE": "MNQ M7_MTF_5_15_60 [PRICE h30] net -2.07, SLIP4 -5.07, B(momentum) +1.13, C(volume) +0.89, 2/5, n 1735 | ES M7_MTF_5_15_60 [PRICE h1100] net -4.87, SLIP4 -12.37, B(momentum) +0.07, C(volume) -0.11, 3/5, n 985 (alignment adds ~0)",
 "ES_NQ_CONFIRMATION_VALUE": "MNQ M8_AGREE [PRICE h1615] net +71.27, SLIP4 +68.27, B(momentum) +23.82, C(volume) +55.68, 2/5, n 99 | ES M8_AGREE [PRICE h1615] net +36.15, SLIP4 +28.65, B(momentum) +21.00, C(volume) +24.61, 3/5, n 99 || diverge: MNQ M8_DIVERGE [PRICE h30] net -1.18, SLIP4 -4.18, B(momentum) -6.07, C(volume) +2.95, 2/5, n 93 | ES M8_DIVERGE [PRICE h1300] net +31.17, SLIP4 +23.67, B(momentum) +17.33, C(volume) +35.89, 4/5, n 44",
 "MOMENTUM_DECAY_EXIT_VALUE": "ES: VWAP-loss exit -2.73 vs hold -12.76 $/trade; MNQ: VWAP-loss exit +4.17 vs hold +6.77 $/trade",
 "PRICE_PLUS_VOLUME_VALUE": "MNQ M9_PRICE_VALUE [VP-A h60] net +2.62, SLIP4 -0.38, B(momentum) +1.60, C(volume) +3.41, 4/5, n 146 | MNQ M9_PRICE_VALUE [VP-B h60] net -4.74, SLIP4 -7.74, B(momentum) -5.27, C(volume) -2.88, 3/5, n 160 | MNQ M9_PRICE_VALUE [VP-C h60] net -4.94, SLIP4 -7.94, B(momentum) -6.66, C(volume) -3.52, 3/5, n 164",
 "PRICE_ONLY_MOMENTUM_VALUE": "MNQ M9_PRICE_ONLY [VP-B h30] net +4.56, SLIP4 +1.56, B(momentum) -0.53, C(volume) +2.36, 4/5, n 351",
 "INCREMENTAL_VALUE_OF_VOLUME_CONFIRMATION": "NOT ROBUST (sign flips across proxies: VP-A positive, VP-B / VP-C negative)",
 "BEST_MOMENTUM_HOLD": "16:00 / 16:15",
 "BEST_MOMENTUM_ENTRY_SPEED": "immediate (no delayed-confirmation variant beat it)",
 "MOMENTUM_TRADES_PER_DAY": "n/a (no strategy)",
 "MOMENTUM_SLIP4_AVG_DAY": "n/a",
 "NEW_MOMENTUM_SURVIVOR": "NONE",
 "T61_PLUS_MOMENTUM_AVG_DAY": "n/a (no momentum survivor)",
 "T61_PLUS_MOMENTUM_INCREMENTAL_DAY": "n/a (no momentum survivor)",
 "T61_PLUS_MOMENTUM_MAXDD": "n/a (no momentum survivor)",
 "T61_PLUS_MOMENTUM_WORST_DAY": "n/a (no momentum survivor)",
 "T61_PLUS_MOMENTUM_RET_DD": "n/a (no momentum survivor)",
 "CORR_MOMENTUM_TO_T61": "n/a (no momentum survivor)",
 "PRESS_WINNER_BASE_SIGNAL": "M1_OPEN_IMPULSE (NON-PROMOTABLE DIAGNOSTIC: no qualifying momentum base)",
 "BEST_PRESS_LADDER": "L4 (MNQ D_VALUE_ACCEPT MEDIUM spacing 0.0 R1: +1.35 $/day, remove-top3 -7723)",
 "BEST_ADD_TRIGGER": "D_VALUE_ACCEPT (least negative marginal adds; ES ADD1 +0.2, MNQ ADD1 -7.3 median)",
 "BEST_ADD_SPEED": "SLOW (least negative)",
 "BEST_ADD_SPACING": "0.25 ATR (least negative)",
 "ADD1_MARGINAL_EV": {
  "ES": -6.58,
  "MNQ": -10.94
 },
 "ADD2_MARGINAL_EV": {
  "ES": -6.66,
  "MNQ": -10.53
 },
 "ADD3_MARGINAL_EV": {
  "ES": -8.21,
  "MNQ": -12.56
 },
 "LOSER_AVG_MAX_UNITS": {
  "ES": 1.21,
  "MNQ": 1.25
 },
 "WINNER_AVG_MAX_UNITS": {
  "ES": 2.31,
  "MNQ": 2.47
 },
 "BIG_WINNER_AVG_MAX_UNITS": {
  "ES": 2.67,
  "MNQ": 2.85
 },
 "NO_ADD_TO_LOSER_VIOLATIONS": 0,
 "CUT_LOSER_VALUE": "R1 (reduce to probe on VWAP loss) vs R0 (full exit): median MNQ -0.17 vs -0.45 $/day",
 "BEST_REDUCTION_POLICY": "R1 (MNQ), no difference (ES)",
 "AVG_WINNER / AVG_LOSER": "see T94_PRESS_GRID.csv",
 "WIN_RATE": {
  "ES": 0.196,
  "MNQ": 0.208
 },
 "PAYOFF_RATIO": {
  "ES": 3.69,
  "MNQ": 3.71
 },
 "CAMPAIGN_EXPECTANCY": {
  "ES": -4.19,
  "MNQ": -2.84
 },
 "GIVEBACK_FRACTION": {
  "ES": 1.04,
  "MNQ": 1.01
 },
 "PRESS_WINNER_AVG_DAY": {
  "ES": -0.34,
  "MNQ": -0.31
 },
 "PRESS_WINNER_MAXDD / WORST / SLIP4": "see grid (best config fails remove-top3)",
 "PYRAMID_VS_FRONTLOAD_EXCESS": {
  "ES": -0.29,
  "MNQ": -0.62
 },
 "PYRAMID_VS_CONSTANT_EXCESS": {
  "ES": -0.3,
  "MNQ": -0.55
 },
 "RTH_PRESS_VALUE": "NEGATIVE / ~0",
 "OVERNIGHT_FULL_PRESS_VALUE": "NOT RUN (RTH press failed)",
 "OVERNIGHT_TRIM_VALUE": "NOT RUN",
 "PRICE_PLUS_VOLUME_ADD_VALUE": "D_VALUE_ACCEPT least negative but still <= 0 in MNQ",
 "ML_ADDS_VALUE (press)": "NOT RUN (no positive marginal add EV)",
 "GA_ADDS_VALUE (press)": "NOT RUN",
 "T61_PLUS_PRESS_AVG_DAY": "n/a",
 "T61_PLUS_PRESS_INCREMENTAL_DAY": "n/a",
 "T61_PLUS_PRESS_MAXDD": "n/a",
 "T61_PLUS_PRESS_WORST_DAY": "n/a",
 "T61_PLUS_PRESS_RET_DD": "n/a",
 "CORR_PRESS_TO_T61": "n/a",
 "NEW_PRESS_WINNER_SURVIVOR": "NONE",
 "STOPPING_CRITERION": "B + C: value migration, value acceptance, POC movement, HVN / LVN traversal, profile compression, price / POC confirmation and all momentum-follow families fail matched-momentum economics or the +10 $/day increment; press-winner adds have negative marginal EV",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PROGRAM_BUDGET": {
  "hypotheses": 2204,
  "ml_configs": 18,
  "genomes": 0
 },
 "CUMULATIVE_BUDGET": {
  "hypotheses": 3906,
  "ml_configs": 225,
  "genomes": 777629
 }
}
```

