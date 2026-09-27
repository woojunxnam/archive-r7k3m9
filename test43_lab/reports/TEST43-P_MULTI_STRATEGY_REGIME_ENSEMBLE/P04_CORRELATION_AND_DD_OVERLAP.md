# P04 Correlation and drawdown overlap (DEV)

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


| A | B | daily_corr | weekly_corr | position_corr | overnight_exposure_corr | dd_overlap | worst20_overlap | loss2020_overlap | loss2022_overlap | hivol_loss_overlap | margin_corr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | MNQ_robust_A_MOD_2 | 0.6 | 0.6 | 0.47 | 0.5 | 0.6 | 0.18 | 0.54 | 0.47 | 0.51 | 0.51 |
| MNQ_arch_A_AGG_0 | MNQ_r2_C_MOD_1 | 0.45 | 0.5 | 0.26 | 0.28 | 0.56 | 0.08 | 0.49 | 0.16 | 0.44 | 0.27 |
| MNQ_arch_A_AGG_0 | MNQ_robust_C_CON_0 | 0.31 | 0.3 | 0.1 | 0.12 | 0.49 | 0.03 | 0.41 | 0.17 | 0.31 | 0.1 |
| MNQ_arch_A_AGG_0 | ES_robust_A_MOD_1 | 0.34 | 0.41 | 0.04 | 0.05 | 0.5 | 0.03 | 0.56 | 0.2 | 0.54 | 0.06 |
| MNQ_arch_A_AGG_0 | ES_r2_F_MOD_2 | 0.43 | 0.52 | 0.19 | 0.2 | 0.64 | 0.03 | 0.58 | 0.2 | 0.55 | 0.23 |
| MNQ_arch_A_AGG_0 | ES_r2_A_CON_1 | 0.41 | 0.51 | 0.11 | 0.11 | 0.57 | 0.05 | 0.57 | 0.2 | 0.54 | 0.16 |
| MNQ_arch_A_AGG_0 | ES_robust_C_CON_4 | 0.43 | 0.49 | 0.24 | 0.26 | 0.57 | 0.08 | 0.57 | 0.2 | 0.55 | 0.23 |
| MNQ_arch_A_AGG_0 | ES_robust_F_AGG_0 | 0.39 | 0.45 | 0.38 | 0.44 | 0.49 | 0.05 | 0.52 | 0.12 | 0.44 | 0.27 |
| MNQ_arch_A_AGG_0 | MNQ_arch_E_AGG_0 | 0.5 | 0.61 | 0.36 | 0.39 | 0.67 | 0.03 | 0.59 | 0.2 | 0.54 | 0.31 |
| MNQ_arch_A_AGG_0 | ES_r2_G_AGG_0 | 0.41 | 0.44 | 0.32 | 0.35 | 0.49 | 0.03 | 0.41 | 0.13 | 0.38 | 0.32 |
| MNQ_robust_A_MOD_2 | MNQ_r2_C_MOD_1 | 0.63 | 0.63 | 0.39 | 0.41 | 0.64 | 0.11 | 0.53 | 0.19 | 0.42 | 0.46 |
| MNQ_robust_A_MOD_2 | MNQ_robust_C_CON_0 | 0.49 | 0.48 | 0.27 | 0.27 | 0.52 | 0.11 | 0.43 | 0.21 | 0.34 | 0.3 |
| MNQ_robust_A_MOD_2 | ES_robust_A_MOD_1 | 0.45 | 0.51 | 0.15 | 0.18 | 0.61 | 0.03 | 0.51 | 0.2 | 0.46 | 0.12 |
| MNQ_robust_A_MOD_2 | ES_r2_F_MOD_2 | 0.54 | 0.6 | 0.29 | 0.32 | 0.62 | 0.08 | 0.52 | 0.2 | 0.46 | 0.29 |
| MNQ_robust_A_MOD_2 | ES_r2_A_CON_1 | 0.53 | 0.63 | 0.25 | 0.27 | 0.56 | 0.05 | 0.52 | 0.2 | 0.46 | 0.27 |
| MNQ_robust_A_MOD_2 | ES_robust_C_CON_4 | 0.57 | 0.63 | 0.38 | 0.42 | 0.54 | 0.05 | 0.51 | 0.2 | 0.47 | 0.37 |
| MNQ_robust_A_MOD_2 | ES_robust_F_AGG_0 | 0.49 | 0.56 | 0.47 | 0.54 | 0.57 | 0.03 | 0.5 | 0.16 | 0.43 | 0.4 |
| MNQ_robust_A_MOD_2 | MNQ_arch_E_AGG_0 | 0.61 | 0.68 | 0.39 | 0.43 | 0.64 | 0.08 | 0.61 | 0.22 | 0.51 | 0.37 |
| MNQ_robust_A_MOD_2 | ES_r2_G_AGG_0 | 0.55 | 0.59 | 0.46 | 0.5 | 0.66 | 0.11 | 0.39 | 0.16 | 0.36 | 0.48 |
| MNQ_r2_C_MOD_1 | MNQ_robust_C_CON_0 | 0.75 | 0.68 | 0.63 | 0.64 | 0.56 | 0.43 | 0.83 | 0.58 | 0.58 | 0.63 |
| MNQ_r2_C_MOD_1 | ES_robust_A_MOD_1 | 0.48 | 0.48 | 0.15 | 0.18 | 0.55 | 0.03 | 0.51 | 0.07 | 0.43 | 0.14 |
| MNQ_r2_C_MOD_1 | ES_r2_F_MOD_2 | 0.6 | 0.54 | 0.32 | 0.33 | 0.61 | 0.08 | 0.52 | 0.07 | 0.43 | 0.32 |
| MNQ_r2_C_MOD_1 | ES_r2_A_CON_1 | 0.61 | 0.57 | 0.31 | 0.32 | 0.57 | 0.08 | 0.52 | 0.07 | 0.44 | 0.33 |
| MNQ_r2_C_MOD_1 | ES_robust_C_CON_4 | 0.63 | 0.57 | 0.5 | 0.51 | 0.6 | 0.08 | 0.52 | 0.07 | 0.44 | 0.47 |
| MNQ_r2_C_MOD_1 | ES_robust_F_AGG_0 | 0.53 | 0.5 | 0.4 | 0.45 | 0.49 | 0.08 | 0.52 | 0.07 | 0.45 | 0.39 |
| MNQ_r2_C_MOD_1 | MNQ_arch_E_AGG_0 | 0.73 | 0.77 | 0.47 | 0.5 | 0.64 | 0.11 | 0.81 | 0.07 | 0.53 | 0.36 |
| MNQ_r2_C_MOD_1 | ES_r2_G_AGG_0 | 0.64 | 0.57 | 0.48 | 0.49 | 0.63 | 0.11 | 0.5 | 0.11 | 0.48 | 0.53 |
| MNQ_robust_C_CON_0 | ES_robust_A_MOD_1 | 0.41 | 0.42 | 0.19 | 0.22 | 0.55 | 0.05 | 0.41 | 0.05 | 0.27 | 0.16 |
| MNQ_robust_C_CON_0 | ES_r2_F_MOD_2 | 0.48 | 0.43 | 0.22 | 0.21 | 0.57 | 0.18 | 0.42 | 0.05 | 0.27 | 0.2 |
| MNQ_robust_C_CON_0 | ES_r2_A_CON_1 | 0.5 | 0.48 | 0.3 | 0.29 | 0.56 | 0.08 | 0.42 | 0.05 | 0.27 | 0.29 |
| MNQ_robust_C_CON_0 | ES_robust_C_CON_4 | 0.5 | 0.48 | 0.4 | 0.4 | 0.62 | 0.08 | 0.42 | 0.05 | 0.28 | 0.38 |
| MNQ_robust_C_CON_0 | ES_robust_F_AGG_0 | 0.38 | 0.37 | 0.21 | 0.24 | 0.38 | 0.05 | 0.42 | 0.04 | 0.29 | 0.15 |
| MNQ_robust_C_CON_0 | MNQ_arch_E_AGG_0 | 0.43 | 0.44 | 0.12 | 0.13 | 0.52 | 0.08 | 0.67 | 0.06 | 0.35 | -0.04 |
| MNQ_robust_C_CON_0 | ES_r2_G_AGG_0 | 0.48 | 0.43 | 0.31 | 0.32 | 0.46 | 0.14 | 0.39 | 0.1 | 0.36 | 0.31 |
| ES_robust_A_MOD_1 | ES_r2_F_MOD_2 | 0.72 | 0.74 | 0.45 | 0.45 | 0.7 | 0.18 | 0.96 | 0.98 | 0.96 | 0.6 |
| ES_robust_A_MOD_1 | ES_r2_A_CON_1 | 0.85 | 0.88 | 0.64 | 0.62 | 0.67 | 0.54 | 0.97 | 0.97 | 0.95 | 0.81 |
| ES_robust_A_MOD_1 | ES_robust_C_CON_4 | 0.73 | 0.7 | 0.34 | 0.36 | 0.63 | 0.21 | 0.98 | 0.98 | 0.96 | 0.4 |
| ES_robust_A_MOD_1 | ES_robust_F_AGG_0 | 0.69 | 0.69 | 0.36 | 0.35 | 0.6 | 0.05 | 0.76 | 0.59 | 0.67 | 0.53 |
| ES_robust_A_MOD_1 | MNQ_arch_E_AGG_0 | 0.55 | 0.61 | 0.06 | 0.07 | 0.62 | 0.08 | 0.64 | 0.85 | 0.8 | 0.04 |
| ES_robust_A_MOD_1 | ES_r2_G_AGG_0 | 0.54 | 0.54 | 0.19 | 0.25 | 0.54 | 0.03 | 0.64 | 0.45 | 0.47 | 0.08 |
| ES_r2_F_MOD_2 | ES_r2_A_CON_1 | 0.88 | 0.88 | 0.65 | 0.64 | 0.78 | 0.25 | 0.97 | 0.98 | 0.96 | 0.68 |
| ES_r2_F_MOD_2 | ES_robust_C_CON_4 | 0.81 | 0.81 | 0.42 | 0.43 | 0.74 | 0.25 | 0.96 | 0.99 | 0.97 | 0.42 |
| ES_r2_F_MOD_2 | ES_robust_F_AGG_0 | 0.65 | 0.65 | 0.39 | 0.45 | 0.55 | 0.14 | 0.77 | 0.59 | 0.66 | 0.53 |
| ES_r2_F_MOD_2 | MNQ_arch_E_AGG_0 | 0.7 | 0.7 | 0.33 | 0.35 | 0.69 | 0.18 | 0.64 | 0.85 | 0.8 | 0.29 |
| ES_r2_F_MOD_2 | ES_r2_G_AGG_0 | 0.66 | 0.66 | 0.36 | 0.38 | 0.58 | 0.21 | 0.63 | 0.44 | 0.48 | 0.35 |
| ES_r2_A_CON_1 | ES_robust_C_CON_4 | 0.88 | 0.87 | 0.53 | 0.52 | 0.73 | 0.25 | 0.97 | 0.99 | 0.95 | 0.58 |
| ES_r2_A_CON_1 | ES_robust_F_AGG_0 | 0.68 | 0.71 | 0.34 | 0.39 | 0.47 | 0.11 | 0.76 | 0.58 | 0.66 | 0.47 |
| ES_r2_A_CON_1 | MNQ_arch_E_AGG_0 | 0.7 | 0.71 | 0.16 | 0.17 | 0.58 | 0.18 | 0.65 | 0.86 | 0.81 | 0.1 |
| ES_r2_A_CON_1 | ES_r2_G_AGG_0 | 0.65 | 0.65 | 0.27 | 0.27 | 0.48 | 0.11 | 0.64 | 0.44 | 0.49 | 0.26 |
| ES_robust_C_CON_4 | ES_robust_F_AGG_0 | 0.66 | 0.65 | 0.41 | 0.46 | 0.46 | 0.08 | 0.76 | 0.59 | 0.66 | 0.47 |
| ES_robust_C_CON_4 | MNQ_arch_E_AGG_0 | 0.7 | 0.68 | 0.4 | 0.42 | 0.61 | 0.14 | 0.65 | 0.86 | 0.82 | 0.29 |
| ES_robust_C_CON_4 | ES_r2_G_AGG_0 | 0.68 | 0.69 | 0.42 | 0.44 | 0.56 | 0.05 | 0.63 | 0.45 | 0.48 | 0.43 |
| ES_robust_F_AGG_0 | MNQ_arch_E_AGG_0 | 0.61 | 0.64 | 0.43 | 0.46 | 0.62 | 0.08 | 0.56 | 0.62 | 0.62 | 0.61 |
| ES_robust_F_AGG_0 | ES_r2_G_AGG_0 | 0.66 | 0.66 | 0.55 | 0.61 | 0.58 | 0.11 | 0.61 | 0.36 | 0.47 | 0.59 |
| MNQ_arch_E_AGG_0 | ES_r2_G_AGG_0 | 0.61 | 0.61 | 0.33 | 0.36 | 0.61 | 0.21 | 0.45 | 0.43 | 0.43 | 0.38 |

## Incremental effect of adding B to A (equal daily-vol risk)
| A | B | incr_B_to_A_d_avg | incr_B_to_A_d_maxdd | incr_B_to_A_d_worst | incr_B_to_A_retdd_ratio |
|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | MNQ_robust_A_MOD_2 | 0.008 | -1.407 | 0.129 | 1.226 |
| MNQ_arch_A_AGG_0 | MNQ_r2_C_MOD_1 | 0.004 | -4.009 | -0.799 | 1.499 |
| MNQ_arch_A_AGG_0 | MNQ_robust_C_CON_0 | 0.003 | -4.767 | -0.664 | 1.619 |
| MNQ_arch_A_AGG_0 | ES_robust_A_MOD_1 | -0.008 | -2.351 | 0.391 | 1.098 |
| MNQ_arch_A_AGG_0 | ES_r2_F_MOD_2 | -0.001 | -1.31 | -0.193 | 1.097 |
| MNQ_arch_A_AGG_0 | ES_r2_A_CON_1 | -0.008 | 0.221 | -0.393 | 0.884 |
| MNQ_arch_A_AGG_0 | ES_robust_C_CON_4 | -0.007 | 0.929 | -0.191 | 0.853 |
| MNQ_arch_A_AGG_0 | ES_robust_F_AGG_0 | -0.009 | -2.185 | 0.805 | 1.073 |
| MNQ_arch_A_AGG_0 | MNQ_arch_E_AGG_0 | -0.008 | 0.851 | -0.234 | 0.845 |
| MNQ_arch_A_AGG_0 | ES_r2_G_AGG_0 | -0.004 | -1.396 | -0.178 | 1.068 |
| MNQ_robust_A_MOD_2 | MNQ_r2_C_MOD_1 | -0.004 | 0.648 | -1.412 | 0.907 |
| MNQ_robust_A_MOD_2 | MNQ_robust_C_CON_0 | -0.005 | -2.463 | -1.023 | 1.191 |
| MNQ_robust_A_MOD_2 | ES_robust_A_MOD_1 | -0.016 | -1.613 | 0.018 | 0.968 |
| MNQ_robust_A_MOD_2 | ES_r2_F_MOD_2 | -0.009 | -0.407 | -0.615 | 0.942 |
| MNQ_robust_A_MOD_2 | ES_r2_A_CON_1 | -0.016 | 1.01 | -0.486 | 0.771 |
| MNQ_robust_A_MOD_2 | ES_robust_C_CON_4 | -0.015 | 1.666 | -0.339 | 0.744 |
| MNQ_robust_A_MOD_2 | ES_robust_F_AGG_0 | -0.017 | -1.137 | 0.594 | 0.919 |
| MNQ_robust_A_MOD_2 | MNQ_arch_E_AGG_0 | -0.016 | 2.282 | -0.384 | 0.702 |
| MNQ_robust_A_MOD_2 | ES_r2_G_AGG_0 | -0.012 | -0.62 | -0.603 | 0.93 |
| MNQ_r2_C_MOD_1 | MNQ_robust_C_CON_0 | -0.001 | -3.887 | 0.048 | 1.323 |
| MNQ_r2_C_MOD_1 | ES_robust_A_MOD_1 | -0.012 | -4.782 | 1.6 | 1.26 |
| MNQ_r2_C_MOD_1 | ES_r2_F_MOD_2 | -0.005 | -3.219 | 0.704 | 1.199 |
| MNQ_r2_C_MOD_1 | ES_r2_A_CON_1 | -0.012 | -1.835 | 0.769 | 0.985 |
| MNQ_r2_C_MOD_1 | ES_robust_C_CON_4 | -0.011 | -2.101 | 1.224 | 1.02 |
| MNQ_r2_C_MOD_1 | ES_robust_F_AGG_0 | -0.012 | -2.506 | 2.0 | 1.032 |
| MNQ_r2_C_MOD_1 | MNQ_arch_E_AGG_0 | -0.012 | -2.567 | 0.875 | 1.042 |
| MNQ_r2_C_MOD_1 | ES_r2_G_AGG_0 | -0.007 | -3.414 | 1.109 | 1.18 |
| MNQ_robust_C_CON_0 | ES_robust_A_MOD_1 | -0.011 | -5.176 | 1.552 | 1.259 |
| MNQ_robust_C_CON_0 | ES_r2_F_MOD_2 | -0.004 | -4.786 | 0.656 | 1.331 |
| MNQ_robust_C_CON_0 | ES_r2_A_CON_1 | -0.011 | -2.44 | 0.721 | 1.021 |
| MNQ_robust_C_CON_0 | ES_robust_C_CON_4 | -0.01 | -0.283 | 1.355 | 0.903 |
| MNQ_robust_C_CON_0 | ES_robust_F_AGG_0 | -0.012 | -7.836 | 1.952 | 1.609 |
| MNQ_robust_C_CON_0 | MNQ_arch_E_AGG_0 | -0.011 | -7.122 | 0.827 | 1.501 |
| MNQ_robust_C_CON_0 | ES_r2_G_AGG_0 | -0.006 | -8.007 | 1.061 | 1.745 |
| ES_robust_A_MOD_1 | ES_r2_F_MOD_2 | 0.007 | 1.018 | -0.277 | 1.02 |
| ES_robust_A_MOD_1 | ES_r2_A_CON_1 | -0.0 | 3.365 | -0.435 | 0.778 |
| ES_robust_A_MOD_1 | ES_robust_C_CON_4 | 0.001 | 2.483 | -0.028 | 0.84 |
| ES_robust_A_MOD_1 | ES_robust_F_AGG_0 | -0.001 | -2.097 | 0.828 | 1.202 |
| ES_robust_A_MOD_1 | MNQ_arch_E_AGG_0 | -0.0 | 0.381 | 0.012 | 0.967 |
| ES_robust_A_MOD_1 | ES_r2_G_AGG_0 | 0.004 | -1.281 | -0.042 | 1.194 |
| ES_r2_F_MOD_2 | ES_r2_A_CON_1 | -0.007 | 2.346 | -0.089 | 0.788 |
| ES_r2_F_MOD_2 | ES_robust_C_CON_4 | -0.006 | 1.465 | 0.314 | 0.843 |
| ES_r2_F_MOD_2 | ES_robust_F_AGG_0 | -0.008 | -5.009 | 1.282 | 1.349 |
| ES_r2_F_MOD_2 | MNQ_arch_E_AGG_0 | -0.007 | -0.439 | 0.171 | 0.937 |
| ES_r2_F_MOD_2 | ES_r2_G_AGG_0 | -0.003 | -3.466 | 0.277 | 1.251 |
| ES_r2_A_CON_1 | ES_robust_C_CON_4 | 0.001 | -0.881 | 0.581 | 1.064 |
| ES_r2_A_CON_1 | ES_robust_F_AGG_0 | -0.0 | -8.3 | 1.35 | 1.705 |
| ES_r2_A_CON_1 | MNQ_arch_E_AGG_0 | 0.0 | -3.713 | 0.504 | 1.23 |
| ES_r2_A_CON_1 | ES_r2_G_AGG_0 | 0.005 | -7.024 | 0.738 | 1.652 |
| ES_robust_C_CON_4 | ES_robust_F_AGG_0 | -0.002 | -6.572 | 1.045 | 1.529 |
| ES_robust_C_CON_4 | MNQ_arch_E_AGG_0 | -0.001 | -1.914 | -0.18 | 1.099 |
| ES_robust_C_CON_4 | ES_r2_G_AGG_0 | 0.004 | -4.222 | 0.34 | 1.367 |
| ES_robust_F_AGG_0 | MNQ_arch_E_AGG_0 | 0.0 | 0.807 | -0.603 | 0.938 |
| ES_robust_F_AGG_0 | ES_r2_G_AGG_0 | 0.005 | -1.014 | -0.332 | 1.183 |
| MNQ_arch_E_AGG_0 | ES_r2_G_AGG_0 | 0.005 | -6.601 | 0.404 | 1.632 |
(units: standardised daily P&L; retdd_ratio > 1 = the pair has better return/DD than A alone)

