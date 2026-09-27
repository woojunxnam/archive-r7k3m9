# P00 Status

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.

Run complete up to the final freeze. Holdout NOT loaded.

```
G_WALLCLOCK_FIX_PASS = YES (exact fill-for-fill 3m reproduction; 3m-specific bar counts / clock anchors converted)
G_3M_REGRESSION_PASS = YES (1011 fills, identical positions/equity)
G_5M_PASS = NO (DEV MaxDD $20.5k > $20k AGGRESSIVE envelope; return 90% retained)
G_TRANSFER_PASS = NO (MNQ 3m: DEV MaxDD $23.4k envelope breach, VAL excess -$40.6/day)
CANDIDATES_ANALYZED = 11 (8 eligible + 3 shadow)
BEHAVIORAL_CLUSTERS = 3 (MNQ-A growth, MNQ-C defensive, ES all four)
FULL_UNIVERSE_ADDS_VALUE = NO
CLUSTER_EQUAL_RISK_ADDS_VALUE = NO
STATIC_DIVERSIFIED_ADDS_VALUE = YES (P2); P2B 4-sleeve: YES
REGIME_ADAPTIVE_ADDS_VALUE = NO (DEV mixed; VAL MODERATE below P2 static)
REGIME_ADAPTIVE_BEATS_STATIC_AFTER_COST = NO at MODERATE (VAL SLIP4: P3_25 104.8 / P3_50 102.4 vs P2 114.4 $/day); AGGRESSIVE P3 higher on VAL but not a selected envelope
DIVERSIFICATION_SATURATION_COUNT = 4 (3 clusters; 5+ adds no ret/DD)
BEST_2020_PORTFOLIO = P2B_STATIC_4SLEEVE (MODERATE, DEV-period 2020)
BEST_2022_PORTFOLIO = P3_REGIME_ADAPTIVE_25 (MODERATE, 2022)
PRIMARY_PORTFOLIO = P2B_STATIC_4SLEEVE|MODERATE
SECONDARY_PORTFOLIO_1 = P2_STATIC_DIVERSIFIED|MODERATE
SECONDARY_PORTFOLIO_2 = P1_CLUSTER_EQUAL_RISK|CONSERVATIVE
PRE_VAL_FREEZE_SHA256 = 18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817
FINAL_FREEZE_SHA256 = 3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7
HOLDOUT_RULES_SHA256 = 62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0
HOLDOUT_OPENED = NO
PORTFOLIO_MEMBERSHIP_CHANGED = NO
LIVE_AUTHORIZATION = NO
```

Authority: GitHub branch `claude/test43-mes-optimization-lab-olvn9b` (full tables in `test43_lab/out/p`, freeze files in
`test43_lab/out/p/freeze`). V6_09 authority is `test43_lab/reports/V6/V6_09_ROBUSTNESS_5M_TRANSFER.md` (Drive copy blocked by
connector write policy; not a research blocker). TEST43-M not rerun; no TEST43-M directional signal is used.

## Selected portfolios (DEV and VAL)
| portfolio | risk_env | members | DEV_avg | DEV_max_dd | DEV_worst | DEV_excess_vs_mb | VAL_avg | VAL_total | VAL_max_dd | VAL_worst | VAL_excess_vs_mb | SLIP4_VAL_avg | TIMING_BRITTLENESS_STRESS_VAL_avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1_CLUSTER_EQUAL_RISK | CONSERVATIVE | MNQ_robust_A_MOD_2+MNQ_arch_A_AGG_0+MNQ_robust_C_CON_0+MNQ_r2_C_MOD_1+ES_robust_A_MOD_1+ES_r2_F_MOD_2+ES_r2_A_CON_1+ES_robust_C_CON_4 | 49.2 | 4800.1 | -1723.0 | 30.4 | 73.0 | 13719.5 | 2540.8 | -1654.6 | 43.9 | 71.3 | 76.4 |
| P2_STATIC_DIVERSIFIED | MODERATE | MNQ_robust_A_MOD_2+MNQ_robust_C_CON_0+ES_robust_A_MOD_1 | 70.1 | 8795.9 | -2655.1 | 42.0 | 118.1 | 22200.9 | 4358.4 | -2269.8 | 77.3 | 114.4 | 122.0 |
| P2B_STATIC_4SLEEVE | MODERATE | MNQ_robust_A_MOD_2+ES_robust_A_MOD_1+MNQ_robust_C_CON_0+MNQ_arch_A_AGG_0 | 84.5 | 8022.0 | -2500.0 | 53.1 | 112.0 | 21060.7 | 3663.4 | -1926.2 | 69.3 | 107.2 | 116.9 |

Next step (not in this run): open the holdout once under `TEST43P_HOLDOUT_ACCEPTANCE_RULES.json`.
