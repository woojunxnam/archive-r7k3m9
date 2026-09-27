# M16 VAL confirmation (one time, frozen, no retune)

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


Frozen file `out/m/frozen/TEST43M_FROZEN_MECHANISMS.json` (sha256 9322a80c013d88ed60d798309887f8aca1f605141832d5a573651a395dd1083d),
hash-checked before evaluation. VAL features built causally on data to 2025-09-30; DEV prefix reproduced exactly.
Pass rule (pre-registered): same sign as DEV and |t| >= 1.65.

## Information level
| id | inst | hz | what | metric | expected_sign | VAL_n | VAL_mean | VAL_t | DEV_mean | DEV_t | VAL_same_sign | VAL_PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | ES | 30m | L_SWEEP | d_ret60 | 1 | 2671 | -0.0001 | -0.0394 | 0.0026 | 1.9661 | False | False |
| C2 | ES | 15m | L_SWEEP | d_ret60 | 1 | 3950 | -0.0042 | -1.172 | 0.0016 | 1.3797 | False | False |
| C3 | ES | 120m | UB_ACCEPT | diff_vs_other_align | 1 | 214 | -0.0114 | -0.895 | 0.0117 | 2.3911 | False | False |
| C4a | ES | 5D | UB_FAILED_ACCEPT | d_ret60 | -1 | 86 | -0.0085 | -0.9473 | -0.0196 | -2.769 | True | False |
| C4b | ES | OR15 | U_RETEST_HOLD | d_ret60 | -1 | 12 | 0.0263 | 0.5189 | -0.0573 | -3.0818 | False | False |
| C6 | ES | 60m | COMPRESSION | d_frange60 | -1 | 1913 | -0.0303 | -2.9085 | -0.0271 | -8.2289 | True | True |
| A1 | ES | - | ABL_SHAPE_ATR_60m+RANGE|k50 | IC_pooled (resid) | 1 | 4711 | 0.0105 | 0.6172 | 0.0125 | 1.5699 | True | False |
| C1 | MNQ | 30m | L_SWEEP | d_ret60 | 1 | 2736 | 0.0004 | 0.0991 | 0.0033 | 2.458 | True | False |
| C2 | MNQ | 15m | L_SWEEP | d_ret60 | 1 | 4150 | -0.0016 | -0.5366 | 0.002 | 1.7522 | False | False |
| C3 | MNQ | 120m | UB_ACCEPT | diff_vs_other_align | 1 | 198 | -0.013 | -0.8915 | 0.0147 | 2.6756 | False | False |
| C5 | MNQ | 30m | DB_FAILED_ACCEPT | d_ret60 | 1 | 580 | 0.0009 | 0.1195 | 0.008 | 3.193 | True | False |
| C6 | MNQ | 60m | COMPRESSION | d_frange60 | -1 | 1954 | -0.0288 | -2.913 | -0.0202 | -6.6101 | True | True |
| A1 | MNQ | - | ABL_SHAPE_ATR_60m+RANGE|k50 | IC_pooled (resid) | 1 | 4711 | 0.0104 | 0.5772 | 0.0099 | 1.1172 | True | False |
| A2 | MNQ | - | SHAPE_ONLY_RANGE_120m|k100 | IC_pooled (resid) | 1 | 4711 | 0.0121 | 0.9136 | 0.0114 | 1.6922 | True | False |

## Overlay level (pre-registered size up 1.25 / down 0.75, hold 20 bars, no headroom) — V6 baseline vs V6 + TEST43-M
| id | spec | VAL_avg_daily | d_VAL_avg_daily | d_VAL_max_dd | d_VAL_excess_vs_mb | d_DEV_avg_daily | fills |
|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | BASE | 77.61 | 0.0 | 0.0 | 0.0 | 0.0 | 2203 |
| MNQ_arch_A_AGG_0 | O1_MNQ_LSWEEP30_UP|VAL | 90.56 | 12.95 | 0.84 | 13.23 | -11.58 | 2624 |
| MNQ_arch_A_AGG_0 | O3_MNQ_DOWNFAIL_LSWEEP_UP|VAL | 90.56 | 12.95 | 0.84 | 13.23 | -11.58 | 2624 |
| MNQ_arch_A_AGG_0 | O4_MNQ_ANALOG_A1|VAL | 87.29 | 9.68 | -39.0 | 9.81 | -7.28 | 2329 |
| MNQ_arch_E_AGG_0 | BASE | 64.78 | 0.0 | 0.0 | 0.0 | 0.0 | 149 |
| MNQ_arch_E_AGG_0 | O1_MNQ_LSWEEP30_UP|VAL | 64.78 | 0.0 | 0.0 | 0.0 | 0.0 | 149 |
| MNQ_arch_E_AGG_0 | O3_MNQ_DOWNFAIL_LSWEEP_UP|VAL | 64.78 | 0.0 | 0.0 | 0.0 | 0.0 | 149 |
| MNQ_arch_E_AGG_0 | O4_MNQ_ANALOG_A1|VAL | 64.78 | 0.0 | 0.0 | 0.0 | 0.0 | 149 |
| MNQ_robust_A_MOD_2 | BASE | 76.69 | 0.0 | 0.0 | 0.0 | 0.0 | 2192 |
| MNQ_robust_A_MOD_2 | O1_MNQ_LSWEEP30_UP|VAL | 99.12 | 22.43 | 732.68 | 21.35 | -4.04 | 3306 |
| MNQ_robust_A_MOD_2 | O3_MNQ_DOWNFAIL_LSWEEP_UP|VAL | 99.12 | 22.43 | 732.68 | 21.35 | -4.0 | 3307 |
| MNQ_robust_A_MOD_2 | O4_MNQ_ANALOG_A1|VAL | 85.05 | 8.36 | -294.84 | 7.81 | 2.89 | 2735 |
| MNQ_r2_C_MOD_1 | BASE | 62.53 | 0.0 | 0.0 | 0.0 | 0.0 | 55 |
| MNQ_r2_C_MOD_1 | O1_MNQ_LSWEEP30_UP|VAL | 45.86 | -16.67 | 0.0 | -16.0 | -11.42 | 167 |
| MNQ_r2_C_MOD_1 | O3_MNQ_DOWNFAIL_LSWEEP_UP|VAL | 45.86 | -16.67 | 0.0 | -16.0 | -11.42 | 167 |
| MNQ_r2_C_MOD_1 | O4_MNQ_ANALOG_A1|VAL | 45.86 | -16.67 | 0.0 | -16.0 | -7.82 | 133 |
| MNQ_robust_C_CON_0 | BASE | 56.26 | 0.0 | 0.0 | 0.0 | 0.0 | 94 |
| MNQ_robust_C_CON_0 | O1_MNQ_LSWEEP30_UP|VAL | 15.18 | -41.08 | 6285.58 | -42.85 | 4.44 | 112 |
| MNQ_robust_C_CON_0 | O3_MNQ_DOWNFAIL_LSWEEP_UP|VAL | 15.18 | -41.08 | 6285.58 | -42.85 | 4.44 | 112 |
| MNQ_robust_C_CON_0 | O4_MNQ_ANALOG_A1|VAL | 56.26 | 0.0 | 0.0 | 0.0 | 3.21 | 99 |
| ES_robust_F_AGG_0 | BASE | 114.97 | 0.0 | 0.0 | 0.0 | 0.0 | 1777 |
| ES_robust_F_AGG_0 | O1_ES_LSWEEP30_UP|VAL | 156.27 | 41.3 | 3492.67 | 40.95 | -22.46 | 5187 |
| ES_robust_F_AGG_0 | O2_ES_UPPERFAIL_DOWN|VAL | 111.73 | -3.24 | 214.83 | -2.67 | 1.25 | 2187 |
| ES_robust_F_AGG_0 | O4_ES_ANALOG_A1|VAL | 145.3 | 30.33 | -1931.06 | 29.37 | -6.07 | 3439 |
| ES_robust_A_MOD_1 | BASE | 98.86 | 0.0 | 0.0 | 0.0 | 0.0 | 278 |
| ES_robust_A_MOD_1 | O1_ES_LSWEEP30_UP|VAL | 128.64 | 29.78 | 389.84 | 29.73 | -9.8 | 555 |
| ES_robust_A_MOD_1 | O2_ES_UPPERFAIL_DOWN|VAL | 90.34 | -8.52 | -180.0 | -7.36 | -2.4 | 311 |
| ES_robust_A_MOD_1 | O4_ES_ANALOG_A1|VAL | 122.22 | 23.36 | 33.72 | 22.97 | -8.38 | 402 |
| ES_r2_F_MOD_2 | BASE | 66.29 | 0.0 | 0.0 | 0.0 | 0.0 | 257 |
| ES_r2_F_MOD_2 | O1_ES_LSWEEP30_UP|VAL | 71.57 | 5.28 | 0.0 | 5.11 | -1.67 | 355 |
| ES_r2_F_MOD_2 | O2_ES_UPPERFAIL_DOWN|VAL | 29.76 | -36.53 | 5708.71 | -38.13 | -2.38 | 295 |
| ES_r2_F_MOD_2 | O4_ES_ANALOG_A1|VAL | 26.43 | -39.87 | 6206.23 | -42.01 | -1.66 | 325 |
| ES_r2_A_CON_1 | BASE | 52.37 | 0.0 | 0.0 | 0.0 | 0.0 | 208 |
| ES_r2_A_CON_1 | O1_ES_LSWEEP30_UP|VAL | 58.67 | 6.3 | 118.74 | 5.58 | -1.84 | 1932 |
| ES_r2_A_CON_1 | O2_ES_UPPERFAIL_DOWN|VAL | 50.38 | -1.98 | 0.0 | -1.89 | -0.19 | 246 |
| ES_r2_A_CON_1 | O4_ES_ANALOG_A1|VAL | 49.19 | -3.18 | 437.42 | -3.17 | -0.74 | 737 |
| ES_robust_C_CON_4 | BASE | 34.01 | 0.0 | 0.0 | 0.0 | 0.0 | 182 |
| ES_robust_C_CON_4 | O1_ES_LSWEEP30_UP|VAL | 48.49 | 14.48 | 2613.68 | 1.1 | -8.72 | 300 |
| ES_robust_C_CON_4 | O2_ES_UPPERFAIL_DOWN|VAL | 40.05 | 6.04 | 0.0 | 5.81 | -3.49 | 159 |
| ES_robust_C_CON_4 | O4_ES_ANALOG_A1|VAL | 26.63 | -7.38 | 3909.94 | -16.12 | -7.55 | 245 |

**Overlay reading.** O1 (up x1.25 for 60m after a 30m lower-range sweep) raised VAL P&L for most candidates
(ES +$5..41/day, MNQ -41..+22/day) while the *same frozen spec lost money on DEV* for the same candidates (d_DEV_avg_daily
column) and usually raised VAL drawdown and turnover. The information-level test of the same event failed VAL (C1/C2).
VAL (2025-01..09, sharp April sell-off and V-rebound) rewards any add-on-weakness exposure; this is regime/beta
exposure, not a validated mechanism. Under the governance (DEV gate failed; no rescue) it is not promoted.

Result: 2 of 14 frozen candidates pass VAL at the information level (only C6, the
volatility-state effect of compression, for both instruments; every directional candidate fails). Per governance
nothing is rescued or retuned; TEST43-M is discarded and the V6 candidates remain intact.

