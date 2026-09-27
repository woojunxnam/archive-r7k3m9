# P10 P3 regime adaptive (limited tilt on P2)

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


Tilt: 0% (= P2), 25%, 50%. Cells = trend tier (BEAR/NEUTRAL/BULL, lagged) x HIVOL; expanding strictly-prior estimates,
t-statistic shrinkage, no tilt before 250 sessions or with < 20 cell sessions; total risk renormalised. No TEST43-M signal.

| risk_env | L | DEV_avg | DEV_total | DEV_max_dd | DEV_worst | DEV_ret_dd | DEV_excess_vs_mb | DEV_mu_avg | DEV_mu_peak | DEV_mu_on_avg | DEV_mu_on_peak | DEV_atr_avg | DEV_atr_peak | fills_per_day | env |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONSERVATIVE | 549.6 | 39.486 | 56346.81 | 5734.72 | -1654.74 | 0.007 | 21.989 | 0.017 | 0.104 | 0.018 | 0.104 | 540.609 | 5576.712 | 0.655 | CONSERVATIVE |
| MODERATE | 894.3 | 70.98 | 101289.08 | 7699.6 | -2655.11 | 0.009 | 42.702 | 0.024 | 0.125 | 0.025 | 0.125 | 879.629 | 9616.638 | 1.296 | MODERATE |
| AGGRESSIVE | 1711.6 | 99.716 | 142294.2 | 14053.81 | -4433.35 | 0.007 | 52.698 | 0.038 | 0.223 | 0.039 | 0.223 | 1403.604 | 15336.75 | 1.413 | AGGRESSIVE |

| risk_env | L | DEV_avg | DEV_total | DEV_max_dd | DEV_worst | DEV_ret_dd | DEV_excess_vs_mb | DEV_mu_avg | DEV_mu_peak | DEV_mu_on_avg | DEV_mu_on_peak | DEV_atr_avg | DEV_atr_peak | fills_per_day | env |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONSERVATIVE | 701.1 | 48.172 | 68741.09 | 6591.19 | -1766.23 | 0.007 | 29.947 | 0.017 | 0.132 | 0.018 | 0.132 | 551.978 | 8079.85 | 1.002 | CONSERVATIVE |
| MODERATE | 894.3 | 71.793 | 102449.28 | 8150.47 | -2655.11 | 0.009 | 43.852 | 0.024 | 0.143 | 0.025 | 0.143 | 865.996 | 9616.638 | 1.304 | MODERATE |
| AGGRESSIVE | 1711.6 | 88.719 | 126602.42 | 14560.9 | -4325.85 | 0.006 | 41.682 | 0.037 | 0.207 | 0.039 | 0.207 | 1391.684 | 13914.312 | 1.413 | AGGRESSIVE |

## Regime performance matrix (DEV, shrunk toward unconditional, k = 60 sessions)
| id | regime | n_sessions | avg | median | shrunk_avg | max_dd_within_cell | worst | t_vs_uncond |
|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | BEAR_HIVOL | 58 | -17.52 | 0.0 | 31.07 | 1015.96 | -956.34 | -5.79 |
| MNQ_arch_A_AGG_0 | BEAR_NOT_HIVOL | 157 | 15.59 | 0.0 | 32.85 | 368.36 | -206.62 | -4.46 |
| MNQ_arch_A_AGG_0 | BULL_HIVOL | 328 | 97.36 | 0.0 | 94.37 | 10877.48 | -2107.68 | 0.35 |
| MNQ_arch_A_AGG_0 | BULL_NOT_HIVOL | 610 | 98.15 | 7.76 | 96.35 | 8317.6 | -2057.34 | 0.54 |
| MNQ_arch_A_AGG_0 | NEUTRAL_HIVOL | 176 | 54.77 | -43.24 | 60.69 | 12161.1 | -2455.78 | -0.24 |
| MNQ_arch_A_AGG_0 | NEUTRAL_NOT_HIVOL | 98 | 86.46 | 0.0 | 83.26 | 6162.02 | -1707.44 | 0.09 |
| MNQ_robust_A_MOD_2 | BEAR_HIVOL | 58 | -13.49 | 0.0 | 50.06 | 1657.74 | -709.0 | -3.56 |
| MNQ_robust_A_MOD_2 | BEAR_NOT_HIVOL | 157 | 13.22 | 0.0 | 40.4 | 128.74 | -128.74 | -10.13 |
| MNQ_robust_A_MOD_2 | BULL_HIVOL | 328 | 212.12 | 0.0 | 196.56 | 11240.38 | -2612.2 | 1.29 |
| MNQ_robust_A_MOD_2 | BULL_NOT_HIVOL | 610 | 119.92 | 0.0 | 119.16 | 13022.44 | -2577.1 | 0.18 |
| MNQ_robust_A_MOD_2 | NEUTRAL_HIVOL | 176 | 51.38 | 0.0 | 66.66 | 12096.94 | -2663.44 | -0.7 |
| MNQ_robust_A_MOD_2 | NEUTRAL_NOT_HIVOL | 98 | 61.77 | 0.0 | 80.66 | 2870.66 | -1317.48 | -0.78 |
| MNQ_r2_C_MOD_1 | BEAR_HIVOL | 58 | 0.0 | 0.0 | 24.13 | 0.0 | 0.0 | -inf |
| MNQ_r2_C_MOD_1 | BEAR_NOT_HIVOL | 157 | 18.6 | 0.0 | 26.58 | 0.0 | 0.0 | -2.58 |
| MNQ_r2_C_MOD_1 | BULL_HIVOL | 328 | 67.83 | 56.5 | 64.68 | 5032.66 | -2826.36 | 0.51 |
| MNQ_r2_C_MOD_1 | BULL_NOT_HIVOL | 610 | 53.25 | 57.5 | 52.73 | 7353.04 | -2776.5 | 0.26 |
| MNQ_r2_C_MOD_1 | NEUTRAL_HIVOL | 176 | 43.65 | 0.0 | 44.62 | 1655.86 | -893.0 | -0.18 |
| MNQ_r2_C_MOD_1 | NEUTRAL_NOT_HIVOL | 98 | 24.19 | 0.0 | 33.02 | 1938.0 | -752.5 | -0.93 |
| MNQ_robust_C_CON_0 | BEAR_HIVOL | 58 | 1.17 | 0.0 | 16.52 | 0.0 | 0.0 | -25.79 |
| MNQ_robust_C_CON_0 | BEAR_NOT_HIVOL | 157 | 0.0 | 0.0 | 8.67 | 0.0 | 0.0 | -inf |
| MNQ_robust_C_CON_0 | BULL_HIVOL | 328 | 71.81 | 0.0 | 65.56 | 3718.24 | -1877.0 | 1.3 |
| MNQ_robust_C_CON_0 | BULL_NOT_HIVOL | 610 | 20.52 | 0.0 | 21.49 | 2827.62 | -1691.24 | -0.91 |
| MNQ_robust_C_CON_0 | NEUTRAL_HIVOL | 176 | 43.03 | 0.0 | 40.06 | 1486.0 | -1092.5 | 0.62 |
| MNQ_robust_C_CON_0 | NEUTRAL_NOT_HIVOL | 98 | 10.57 | 0.0 | 18.46 | 1938.0 | -752.5 | -0.93 |
| ES_robust_A_MOD_1 | BEAR_HIVOL | 103 | 31.6 | 7.5 | 44.11 | 7622.45 | -2221.24 | -0.35 |
| ES_robust_A_MOD_1 | BEAR_NOT_HIVOL | 117 | 29.12 | -22.5 | 41.49 | 9537.43 | -2128.74 | -0.47 |
| ES_robust_A_MOD_1 | BULL_HIVOL | 223 | 148.44 | 41.25 | 130.87 | 9241.18 | -2903.6 | 0.82 |
| ES_robust_A_MOD_1 | BULL_NOT_HIVOL | 722 | 70.89 | 46.88 | 70.48 | 15813.77 | -2722.36 | 0.15 |
| ES_robust_A_MOD_1 | NEUTRAL_HIVOL | 136 | -8.09 | -2.5 | 14.47 | 4997.49 | -1456.25 | -2.18 |
| ES_robust_A_MOD_1 | NEUTRAL_NOT_HIVOL | 126 | 29.75 | 1.88 | 41.31 | 1830.0 | -548.75 | -2.04 |
| ES_r2_F_MOD_2 | BEAR_HIVOL | 103 | 8.34 | 10.0 | 24.91 | 2507.49 | -882.5 | -1.36 |
| ES_r2_F_MOD_2 | BEAR_NOT_HIVOL | 117 | -2.25 | -15.0 | 16.59 | 4964.93 | -1548.71 | -1.58 |
| ES_r2_F_MOD_2 | BULL_HIVOL | 223 | 148.83 | 35.0 | 128.59 | 4633.03 | -2630.61 | 1.62 |
| ES_r2_F_MOD_2 | BULL_NOT_HIVOL | 722 | 46.78 | 50.0 | 47.28 | 10784.43 | -2606.78 | -0.26 |
| ES_r2_F_MOD_2 | NEUTRAL_HIVOL | 136 | 40.07 | -3.12 | 44.13 | 4997.49 | -1456.25 | -0.24 |
| ES_r2_F_MOD_2 | NEUTRAL_NOT_HIVOL | 126 | 24.75 | 65.0 | 33.98 | 4619.35 | -1353.11 | -0.73 |
| ES_r2_A_CON_1 | BEAR_HIVOL | 103 | 8.34 | 10.0 | 16.02 | 2507.49 | -882.5 | -0.63 |
| ES_r2_A_CON_1 | BEAR_NOT_HIVOL | 117 | 5.69 | -10.0 | 13.66 | 3627.49 | -912.49 | -0.87 |
| ES_r2_A_CON_1 | BULL_HIVOL | 223 | 56.0 | 40.0 | 50.32 | 5017.91 | -1745.0 | 0.66 |
| ES_r2_A_CON_1 | BULL_NOT_HIVOL | 722 | 28.77 | 35.0 | 28.81 | 9624.24 | -1875.0 | -0.03 |
| ES_r2_A_CON_1 | NEUTRAL_HIVOL | 136 | -1.07 | 22.19 | 8.2 | 4960.61 | -1648.1 | -0.74 |
| ES_r2_A_CON_1 | NEUTRAL_NOT_HIVOL | 126 | 55.95 | 66.26 | 47.33 | 2020.6 | -548.75 | 1.12 |
| ES_robust_C_CON_4 | BEAR_HIVOL | 103 | 3.93 | 2.5 | 14.91 | 2998.11 | -1452.48 | -0.68 |
| ES_robust_C_CON_4 | BEAR_NOT_HIVOL | 117 | -1.86 | -10.0 | 10.21 | 3784.95 | -912.49 | -1.27 |
| ES_robust_C_CON_4 | BULL_HIVOL | 223 | 46.92 | 55.0 | 44.13 | 6091.75 | -1716.87 | 0.3 |
| ES_robust_C_CON_4 | BULL_NOT_HIVOL | 722 | 41.27 | 43.75 | 40.7 | 6410.5 | -1679.36 | 0.44 |
| ES_robust_C_CON_4 | NEUTRAL_HIVOL | 136 | 19.39 | -3.12 | 23.79 | 5614.34 | -1503.74 | -0.32 |
| ES_robust_C_CON_4 | NEUTRAL_NOT_HIVOL | 126 | 40.34 | 38.75 | 38.22 | 3369.34 | -1211.24 | 0.2 |
| ES_robust_F_AGG_0 | BEAR_HIVOL | 103 | 40.65 | 0.12 | 68.39 | 16885.37 | -2291.12 | -0.4 |
| ES_robust_F_AGG_0 | BEAR_NOT_HIVOL | 117 | 345.19 | -214.22 | 267.51 | 16897.92 | -3732.92 | 0.99 |
| ES_robust_F_AGG_0 | BULL_HIVOL | 223 | 150.03 | 187.5 | 142.82 | 10827.52 | -2769.93 | 0.28 |
| ES_robust_F_AGG_0 | BULL_NOT_HIVOL | 722 | 121.09 | 90.02 | 120.7 | 23515.99 | -4048.68 | 0.07 |
| ES_robust_F_AGG_0 | NEUTRAL_HIVOL | 136 | -27.4 | 0.0 | 16.51 | 7433.69 | -1782.49 | -3.5 |
| ES_robust_F_AGG_0 | NEUTRAL_NOT_HIVOL | 126 | 30.41 | 76.25 | 58.02 | 4333.12 | -1824.97 | -1.85 |
| MNQ_arch_E_AGG_0 | BEAR_HIVOL | 58 | -62.0 | -62.0 | 4.18 | 6308.24 | -1429.5 | -1.56 |
| MNQ_arch_E_AGG_0 | BEAR_NOT_HIVOL | 157 | 35.78 | -28.0 | 44.73 | 7526.82 | -1741.0 | -0.76 |
| MNQ_arch_E_AGG_0 | BULL_HIVOL | 328 | 43.39 | 78.0 | 47.22 | 10216.86 | -4314.0 | -0.47 |
| MNQ_arch_E_AGG_0 | BULL_NOT_HIVOL | 610 | 111.48 | 116.0 | 107.6 | 12167.48 | -3917.62 | 0.91 |
| MNQ_arch_E_AGG_0 | NEUTRAL_HIVOL | 176 | 17.9 | 80.75 | 30.68 | 10062.96 | -3374.0 | -0.79 |
| MNQ_arch_E_AGG_0 | NEUTRAL_NOT_HIVOL | 98 | 100.49 | 255.5 | 88.21 | 9335.6 | -4430.94 | 0.28 |
| ES_r2_G_AGG_0 | BEAR_HIVOL | 103 | 106.89 | 0.0 | 101.6 | 6410.84 | -2606.16 | 0.12 |
| ES_r2_G_AGG_0 | BEAR_NOT_HIVOL | 117 | 144.37 | 0.0 | 126.8 | 10807.8 | -3356.16 | 0.43 |
| ES_r2_G_AGG_0 | BULL_HIVOL | 223 | 141.93 | 0.0 | 131.46 | 11052.01 | -3913.61 | 0.51 |
| ES_r2_G_AGG_0 | BULL_NOT_HIVOL | 722 | 105.69 | 37.55 | 104.68 | 18114.3 | -4922.36 | 0.28 |
| ES_r2_G_AGG_0 | NEUTRAL_HIVOL | 136 | -63.38 | 0.0 | -15.65 | 9139.02 | -2914.96 | -2.84 |
| ES_r2_G_AGG_0 | NEUTRAL_NOT_HIVOL | 126 | 38.11 | 0.0 | 55.66 | 3022.46 | -2401.84 | -1.06 |

## Complementarity (rank within regime, 1 = best)
| id | rank_BEAR_HIVOL | rank_BEAR_NOT_HIVOL | rank_BULL_HIVOL | rank_BULL_NOT_HIVOL | rank_NEUTRAL_HIVOL | rank_NEUTRAL_NOT_HIVOL | shrunk_avg_BEAR_HIVOL | shrunk_avg_BEAR_NOT_HIVOL | shrunk_avg_BULL_HIVOL | shrunk_avg_BULL_NOT_HIVOL | shrunk_avg_NEUTRAL_HIVOL | shrunk_avg_NEUTRAL_NOT_HIVOL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES_r2_A_CON_1 | 7.0 | 6.0 | 7.0 | 7.0 | 8.0 | 3.0 | 16.0 | 13.7 | 50.3 | 28.8 | 8.2 | 47.3 |
| ES_r2_F_MOD_2 | 4.0 | 5.0 | 3.0 | 5.0 | 4.0 | 6.0 | 24.9 | 16.6 | 128.6 | 47.3 | 44.1 | 34.0 |
| ES_robust_A_MOD_1 | 2.0 | 1.0 | 2.0 | 3.0 | 7.0 | 4.0 | 44.1 | 41.5 | 130.9 | 70.5 | 14.5 | 41.3 |
| ES_robust_C_CON_4 | 8.0 | 7.0 | 8.0 | 6.0 | 6.0 | 5.0 | 14.9 | 10.2 | 44.1 | 40.7 | 23.8 | 38.2 |
| MNQ_arch_A_AGG_0 | 3.0 | 3.0 | 4.0 | 2.0 | 2.0 | 1.0 | 31.1 | 32.9 | 94.4 | 96.3 | 60.7 | 83.3 |
| MNQ_r2_C_MOD_1 | 5.0 | 4.0 | 6.0 | 4.0 | 3.0 | 7.0 | 24.1 | 26.6 | 64.7 | 52.7 | 44.6 | 33.0 |
| MNQ_robust_A_MOD_2 | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 2.0 | 50.1 | 40.4 | 196.6 | 119.2 | 66.7 | 80.7 |
| MNQ_robust_C_CON_0 | 6.0 | 8.0 | 5.0 | 8.0 | 5.0 | 8.0 | 16.5 | 8.7 | 65.6 | 21.5 | 40.1 | 18.5 |

Tilt multiplier range realised (alpha 0.5): min 0.48, max 1.76.
All sleeves earn most in BULL cells; defensive roles are relative (MNQ C-CON has the smallest BEAR losses in 2022) rather
than regime-specific positive alpha. P3 improves DEV MODERATE MaxDD slightly but does not beat P2 on VAL after cost.
REGIME_ADAPTIVE_BEATS_STATIC_AFTER_COST = NO at MODERATE (VAL SLIP4: P3_25 104.8 / P3_50 102.4 vs P2 114.4 $/day); AGGRESSIVE P3 higher on VAL but not a selected envelope.

