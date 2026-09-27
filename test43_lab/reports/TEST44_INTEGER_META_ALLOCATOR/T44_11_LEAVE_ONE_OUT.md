# T44_11 Integer leave-one-out

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

| config | removed | d_ALL_avg | d_ALL_max_dd | d_ALL_worst | d_ALL_ret_dd | d_ALL_excess_vs_mb | d_Y2020_avg | d_Y2022_avg | d_FORMER_HOLDOUT_avg |
|---|---|---|---|---|---|---|---|---|---|
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_arch_A_AGG_0 | -3.63 | 2454.1 | -533.12 | -0.0 | -5.11 | -5.94 | -0.79 | -19.19 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_robust_A_MOD_2 | -3.78 | -1653.92 | 0.0 | 0.0 | -0.57 | -12.7 | -2.41 | 27.75 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_r2_C_MOD_1 | -4.41 | -2316.23 | 167.15 | 0.0 | -0.05 | -1.0 | 4.16 | 10.93 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_robust_C_CON_0 | 0.13 | 2053.34 | -1221.12 | -0.0 | -4.76 | -3.49 | -9.28 | 26.05 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_robust_A_MOD_1 | 1.82 | 3147.25 | -666.87 | -0.0 | -0.56 | -0.89 | -5.47 | -9.39 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_r2_F_MOD_2 | 1.08 | 441.73 | 0.0 | -0.0 | 0.64 | 0.83 | -2.39 | -5.42 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_r2_A_CON_1 | -1.06 | 1568.26 | 0.0 | -0.0 | -1.07 | -2.28 | -1.37 | -13.6 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_robust_C_CON_4 | 2.33 | 1450.71 | -666.87 | -0.0 | 1.21 | 5.31 | 0.19 | -9.38 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_arch_A_AGG_0 | -2.38 | 4574.14 | 0.0 | -0.0 | -2.8 | -3.32 | -3.81 | -38.41 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_robust_A_MOD_2 | -0.7 | 2889.66 | -115.75 | -0.0 | -0.07 | 0.32 | 6.59 | -14.51 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_r2_C_MOD_1 | -2.22 | -221.84 | 41.01 | -0.0 | 0.22 | 0.88 | 4.18 | -49.44 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_robust_C_CON_0 | -2.56 | 491.74 | 0.0 | -0.0 | -3.37 | 0.0 | -3.69 | -14.01 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_robust_A_MOD_1 | -4.81 | 1653.68 | -251.88 | -0.0 | -5.69 | -17.6 | -7.82 | -2.36 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_r2_F_MOD_2 | -4.81 | 1653.68 | -251.88 | -0.0 | -5.69 | -17.6 | -7.82 | -2.36 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_r2_A_CON_1 | -0.14 | 52.49 | 0.0 | -0.0 | -0.14 | 0.0 | 0.0 | -2.55 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_robust_C_CON_4 | -0.35 | -0.0 | 0.0 | -0.0 | -0.33 | 0.0 | 0.0 | -6.17 |

Under integer execution several fractional-era diversifiers are redundant (removing ES_r2_A_CON_1 / ES_robust_C_CON_4 changes little); the MNQ A family and ES_robust_A_MOD_1 / ES_r2_F_MOD_2 carry the return; MNQ_robust_C_CON_0 lowers drawdown.
