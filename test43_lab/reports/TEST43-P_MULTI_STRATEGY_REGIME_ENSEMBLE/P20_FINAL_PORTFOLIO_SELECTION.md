# P20 Final portfolio selection

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


Pre-registered rule (frozen before VAL): {
 "PRIMARY": "among MODERATE variants passing VAL: highest DEV ret/DD; ties -> fewer sleeves",
 "SECONDARY_1": "simplest static diversified: P2_STATIC_DIVERSIFIED|MODERATE if it passes VAL, else P2B",
 "SECONDARY_2": "defensive: CONSERVATIVE variant passing VAL with the lowest DEV MaxDD",
 "note": "P3 is eligible for PRIMARY only if it also beats P2 on VAL after cost (avg/day and ret/DD); no rescue"
}

Result: PRIMARY = P2B_STATIC_4SLEEVE|MODERATE; SECONDARY_1 = P2_STATIC_DIVERSIFIED|MODERATE; SECONDARY_2 = P1_CLUSTER_EQUAL_RISK|CONSERVATIVE.

| portfolio | risk_env | members | DEV_avg | DEV_max_dd | DEV_worst | DEV_ret_dd | Y2020_avg | Y2022_avg | VAL_avg | VAL_max_dd | VAL_worst | VAL_excess_vs_mb |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1_CLUSTER_EQUAL_RISK | CONSERVATIVE | MNQ_robust_A_MOD_2+MNQ_arch_A_AGG_0+MNQ_robust_C_CON_0+MNQ_r2_C_MOD_1+ES_robust_A_MOD_1+ES_r2_F_MOD_2+ES_r2_A_CON_1+ES_robust_C_CON_4 | 49.19 | 4800.12 | -1722.99 | 0.01 | 74.83 | 3.23 | 72.98 | 2540.85 | -1654.59 | 43.93 |
| P2_STATIC_DIVERSIFIED | MODERATE | MNQ_robust_A_MOD_2+MNQ_robust_C_CON_0+ES_robust_A_MOD_1 | 70.08 | 8795.88 | -2655.11 | 0.01 | 113.78 | 11.85 | 118.09 | 4358.42 | -2269.85 | 77.26 |
| P2B_STATIC_4SLEEVE | MODERATE | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0 | 84.49 | 8021.98 | -2499.96 | 0.01 | 151.3 | 1.33 | 112.03 | 3663.38 | -1926.23 | 69.3 |

Contract weights (desired contracts per sleeve contract) are in `TEST43P_FINAL_PORTFOLIOS.json`.

