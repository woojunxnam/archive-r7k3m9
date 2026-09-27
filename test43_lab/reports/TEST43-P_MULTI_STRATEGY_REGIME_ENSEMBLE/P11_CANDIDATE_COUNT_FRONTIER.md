# P11 How many strategies is enough?

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.

| n_candidates | members | effective_clusters | L | DEV_avg | DEV_max_dd | DEV_worst | DEV_ret_dd | DEV_excess_vs_mb | Y2020_avg | Y2022_avg | DEV_mu_peak |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MNQ_robust_A_MOD_2 | 1 | 1140.8 | 73.171 | 10824.92 | -2612.2 | 0.007 | 38.069 | 160.069 | -32.657 | 0.153 |
| 2 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1 | 2 | 1237.2 | 64.414 | 11457.9 | -2667.0 | 0.006 | 31.874 | 138.19 | -30.99 | 0.194 |
| 3 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0 | 3 | 969.9 | 70.076 | 8795.88 | -2655.11 | 0.008 | 41.993 | 113.782 | 11.85 | 0.145 |
| 4 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0 | 3 | 969.9 | 84.488 | 8021.98 | -2499.96 | 0.011 | 53.086 | 151.295 | 1.326 | 0.112 |
| 5 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0+ES_r2_F_MOD_2 | 3 | 969.9 | 86.308 | 8412.74 | -2649.23 | 0.01 | 52.6 | 144.295 | 2.653 | 0.116 |
| 6 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0+ES_r2_F_MOD_2+MNQ_r2_C_MOD_1 | 3 | 894.3 | 80.157 | 7837.62 | -2592.73 | 0.01 | 48.713 | 135.361 | -2.288 | 0.101 |
| 7 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0+ES_r2_F_MOD_2+MNQ_r2_C_MOD_1+ES_r2_A_CON_1 | 3 | 894.3 | 60.875 | 10256.13 | -2697.98 | 0.006 | 31.824 | 77.05 | -10.283 | 0.124 |
| 8 | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0+ES_r2_F_MOD_2+MNQ_r2_C_MOD_1+ES_r2_A_CON_1+ES_robust_C_CON_4 | 3 | 824.6 | 66.39 | 9968.5 | -2610.35 | 0.007 | 39.039 | 102.702 | -14.333 | 0.103 |

Deterministic round-robin across clusters (best-first). Diversification saturates at 4 sleeves (3 clusters): 5-6 give similar ret/DD, 7-8 (adding more ES cluster members) degrade it. DIVERSIFICATION_SATURATION_COUNT = 4.
