# P09 P2 static diversified (and P2B)

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.

| risk_env | L | DEV_avg | DEV_total | DEV_max_dd | DEV_worst | DEV_ret_dd | DEV_excess_vs_mb | DEV_mu_avg | DEV_mu_peak | DEV_mu_on_avg | DEV_mu_on_peak | DEV_atr_avg | DEV_atr_peak | fills_per_day | env |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONSERVATIVE | 549.6 | 39.633 | 56556.47 | 5828.36 | -1701.97 | 0.007 | 24.146 | 0.015 | 0.103 | 0.016 | 0.103 | 458.44 | 5576.712 | 0.647 | CONSERVATIVE |
| MODERATE | 969.9 | 70.076 | 99998.72 | 8795.88 | -2655.11 | 0.008 | 41.993 | 0.024 | 0.145 | 0.025 | 0.145 | 879.958 | 10582.988 | 1.228 | MODERATE |
| AGGRESSIVE | 1455.2 | 94.966 | 135516.16 | 12574.86 | -4123.1 | 0.008 | 52.898 | 0.034 | 0.189 | 0.036 | 0.189 | 1272.841 | 15193.35 | 1.274 | AGGRESSIVE |

## P2B (4 sleeves: count-frontier saturation point)
| risk_env | members | L | DEV_avg | DEV_max_dd | DEV_worst | DEV_ret_dd | DEV_excess_vs_mb |
|---|---|---|---|---|---|---|---|
| CONSERVATIVE | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0 | 760.3 | 58.074 | 6004.36 | -1701.97 | 0.01 | 36.004 |
| MODERATE | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0 | 969.9 | 84.488 | 8021.98 | -2499.96 | 0.011 | 53.086 |
| AGGRESSIVE | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0 | 2013.2 | 117.376 | 15027.97 | -4416.8 | 0.008 | 63.422 |

P2 = one representative per cluster (max min-fold matched-beta excess): MNQ_robust_A_MOD_2, MNQ_robust_C_CON_0, ES_robust_A_MOD_1. P2B adds MNQ_arch_A_AGG_0 (second member of the MNQ growth cluster) and has the best DEV return/DD.
