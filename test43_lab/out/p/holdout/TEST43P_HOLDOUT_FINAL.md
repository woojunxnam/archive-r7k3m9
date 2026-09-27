# TEST43-P FINAL HOLDOUT (ONE SHOT)

Window 2025-10-01 .. 2026-05-27 (165 sessions). Frozen objects only; nothing changed before or after evaluation.
Integrity re-verified BEFORE any holdout economics: 37 checks (3 freeze files byte-equal to 33359fd with expected SHA256,
selection/window, 9 manifest code files + 10 supporting/audit files, 11 candidate hashes, canonical ES/MNQ SHA256). 3m bars rebuilt from the
hash-verified canonical files; the full-period run reproduced the frozen DEV+VAL daily P&L (max |diff| 4.5e-13); data last session 2026-05-27.

```
PRIMARY_HOLDOUT_PASS = NO
SECONDARY_1_HOLDOUT_PASS = NO
SECONDARY_2_HOLDOUT_PASS = YES
HOLDOUT_OPENED = YES
HOLDOUT_WINDOW = 2025-10-01 through 2026-05-27
PRIMARY_NET_PNL = -7164.289999999106
PRIMARY_AVG_DAY = -43.41993939393397
PRIMARY_MAX_DD = 12788.169999999227
PRIMARY_WORST_DAY = -2212.7299999999814
PRIMARY_REMOVE_TOP3_AVG = -68.79533333332793
PRIMARY_BEST_DAY_CONCENTRATION = -0.19962201418425882
PRIMARY_MATCHED_BETA_EXCESS = -79.47892562912324
PRIMARY_SESSION_MATCHED_BETA_EXCESS = -80.99153041472904
FINAL_TEST43P_STATUS = PRIMARY = HOLDOUT_FAIL; SECONDARY PASS REPORTED ONLY (no automatic promotion)
LIVE_AUTHORIZATION = NO
```

## Frozen acceptance (evaluator src/p07_acceptance.py, unchanged)
| frozen condition | PRIMARY | SECONDARY_1 | SECONDARY_2 |
|---|---|---|---|
| net_pnl_positive | False | False | True |
| no_margin_breach | True | True | True |
| peak_margin_util_le_0.5 | True | True | True |
| max_dd_within_envelope | True | True | True |
| worst_day_within_envelope | True | True | True |
| remove_top3_avg_positive | False | False | True |
| best_day_le_35pct_of_total | False | False | True |
| ALL (PASS) | False | False | True |

## Holdout economics (report-only items included)
| metric | PRIMARY | SECONDARY_1 | SECONDARY_2 |
|---|---|---|---|
| net_pnl | -7164.29 | -8064.47 | 9690.71 |
| gross_pnl | -6670.0 | -7647.0 | 9909.25 |
| friction_commission_slippage | 488.31 | 409.25 | 214.8 |
| roll_cost | 5.98 | 8.22 | 3.74 |
| contract_sides_MES | 109.0 | 135.0 | 40.0 |
| contract_sides_MNQ | 254.0 | 140.0 | 125.0 |
| avg_day | -43.42 | -48.876 | 58.732 |
| median_day | 0.0 | 0.0 | 0.0 |
| max_dd | 12788.17 | 12555.75 | 6193.43 |
| worst_day | -2212.73 | -1503.31 | -1523.36 |
| best_day | 1430.15 | 1836.27 | 2055.13 |
| best_day_share | -0.2 | -0.228 | 0.212 |
| return_dd | -0.003 | -0.004 | 0.009 |
| avg_ex_top1 | -52.088 | -60.004 | 46.276 |
| avg_ex_top3 | -68.795 | -75.06 | 23.352 |
| avg_ex_top5 | -82.669 | -87.94 | 4.016 |
| positive_day_share | 0.352 | 0.321 | 0.376 |
| matched_beta_avg_day | 36.059 | 29.559 | 38.369 |
| matched_beta_excess_per_day | -79.479 | -78.435 | 20.363 |
| session_matched_beta_excess_per_day | -80.992 | -79.291 | 19.456 |
| avg_contracts_MES | 0.436 | 0.497 | 0.655 |
| avg_contracts_MNQ | 0.453 | 0.318 | 0.412 |
| avg_rth_MES | 0.517 | 0.597 | 0.682 |
| avg_on_MES | 0.404 | 0.458 | 0.645 |
| avg_rth_MNQ | 0.67 | 0.455 | 0.531 |
| avg_on_MNQ | 0.369 | 0.265 | 0.366 |
| max_contracts_MES | 4.0 | 5.0 | 2.0 |
| max_contracts_MNQ | 4.0 | 3.0 | 2.0 |
| peak_margin_util | 0.071 | 0.059 | 0.079 |
| peak_overnight_margin_util | 0.071 | 0.059 | 0.079 |

## Stress (report only)
| role | portfolio | test | net_pnl | avg_day | max_dd | worst_day |
|---|---|---|---|---|---|---|
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | SLIP4 | -7363.0 | -44.6 | 12901.4 | -2221.0 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | TIMING_BRITTLENESS_STRESS | -7235.4 | -43.9 | 12763.5 | -2065.2 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | SLIP4 | -8204.0 | -49.7 | 12639.8 | -1542.3 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | TIMING_BRITTLENESS_STRESS | -8197.7 | -49.7 | 12593.0 | -1581.6 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | SLIP4 | 9584.2 | 58.1 | 6200.2 | -1530.1 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | TIMING_BRITTLENESS_STRESS | 9238.2 | 56.0 | 6515.9 | -1502.9 |

## Monthly (descriptive)
| role | portfolio | month | sessions | net_pnl | avg_day | intra_month_max_dd | window_dd_at_month_end | positive_day_share |
|---|---|---|---|---|---|---|---|---|
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2025-10 | 23 | 146.9 | 6.4 | 3448.2 | 1623.6 | 0.4 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2025-11 | 19 | 906.8 | 47.7 | 2672.6 | 716.8 | 0.4 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2025-12 | 22 | -3456.0 | -157.1 | 3456.0 | 4172.8 | 0.4 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2026-01 | 20 | -4475.5 | -223.8 | 4917.6 | 8648.4 | 0.4 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2026-02 | 19 | -2198.4 | -115.7 | 2198.4 | 10846.8 | 0.1 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2026-03 | 22 | -1867.2 | -84.9 | 3249.5 | 12713.9 | 0.1 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2026-04 | 22 | 3070.2 | 139.6 | 1144.5 | 9643.7 | 0.5 |
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 2026-05 | 18 | 709.0 | 39.4 | 616.4 | 8934.7 | 0.6 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2025-10 | 23 | -604.7 | -26.3 | 3746.8 | 1528.9 | 0.4 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2025-11 | 19 | -68.7 | -3.6 | 2215.9 | 1597.5 | 0.4 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2025-12 | 22 | -3008.0 | -136.7 | 3686.9 | 4605.5 | 0.4 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2026-01 | 20 | -3167.0 | -158.3 | 3167.0 | 7772.5 | 0.5 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2026-02 | 19 | -2319.8 | -122.1 | 2529.8 | 10092.3 | 0.1 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2026-03 | 22 | -2463.4 | -112.0 | 3845.8 | 12555.7 | 0.1 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2026-04 | 22 | 3620.9 | 164.6 | 674.1 | 8934.8 | 0.4 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 2026-05 | 18 | -53.8 | -3.0 | 639.5 | 8988.6 | 0.3 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2025-10 | 23 | -85.6 | -3.7 | 2186.5 | 1205.0 | 0.5 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2025-11 | 19 | -251.4 | -13.2 | 1805.4 | 1456.4 | 0.4 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2025-12 | 22 | -2133.0 | -97.0 | 2411.6 | 3589.4 | 0.4 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2026-01 | 20 | -829.0 | -41.4 | 2128.6 | 4418.4 | 0.5 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2026-02 | 19 | -1775.1 | -93.4 | 1985.1 | 6193.4 | 0.1 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2026-03 | 22 | 76.8 | 3.5 | 453.1 | 6116.6 | 0.0 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2026-04 | 22 | 7664.5 | 348.4 | 1475.0 | 0.0 | 0.5 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 2026-05 | 18 | 7023.5 | 390.2 | 2336.5 | 0.0 | 0.6 |

## Rolling 3-month (63 sessions) windows
| rolling 63-session window | PRIMARY | SECONDARY_1 | SECONDARY_2 |
|---|---|---|---|
| n_windows | 103.0 | 103.0 | 103.0 |
| min | -10460.8 | -9319.7 | -4938.9 |
| max | 1499.9 | 643.4 | 14716.6 |
| positive_share | 0.2 | 0.2 | 0.3 |

## Sleeve attribution
`gross_contribution_virtual` = weighted sleeve desire held (fractional, before integer rounding / governor);
`gross_contribution_realised` = actual integer portfolio position allocated pro rata to each sleeve's share of the instrument desire;
`standalone_virtual_ledger_holdout_pnl` = the sleeve's own frozen standalone run.
| role | sleeve | inst | contract_weight | risk_budget | avg_weighted_desired_contracts | avg_realised_contracts_allocated | gross_contribution_virtual | gross_contribution_realised | friction_allocated | net_contribution_realised_approx | standalone_virtual_ledger_holdout_pnl | standalone_virtual_ledger_holdout_pnl_x_weight |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PRIMARY | MNQ_robust_A_MOD_2 | MNQ | 0.22 | 0.25 | 0.32 | 0.2 | -584.0 | -4286.19 | 117.69 | -4404.81 | -3488.46 | -760.45 |
| PRIMARY | ES_robust_A_MOD_1 | ES | 0.25 | 0.25 | 0.7 | 0.44 | 1645.04 | -2666.25 | 203.83 | -2873.82 | 5649.96 | 1414.4 |
| PRIMARY | MNQ_robust_C_CON_0 | MNQ | 0.69 | 0.25 | 0.41 | 0.07 | 14099.91 | 483.64 | 9.62 | 473.95 | 20343.1 | 14097.9 |
| PRIMARY | MNQ_arch_A_AGG_0 | MNQ | 0.26 | 0.25 | 0.27 | 0.18 | 582.91 | -198.95 | 157.17 | -357.36 | 1362.14 | 356.77 |
| SECONDARY_1 | MNQ_robust_A_MOD_2 | MNQ | 0.29 | 0.33 | 0.43 | 0.24 | -778.66 | -4570.41 | 144.95 | -4719.5 | -3488.46 | -1013.94 |
| SECONDARY_1 | MNQ_robust_C_CON_0 | MNQ | 0.92 | 0.33 | 0.54 | 0.08 | 18799.88 | -406.09 | 11.85 | -418.28 | 20343.1 | 18797.2 |
| SECONDARY_1 | ES_robust_A_MOD_1 | ES | 0.33 | 0.33 | 0.94 | 0.5 | 2193.38 | -2680.0 | 252.45 | -2936.19 | 5649.96 | 1885.87 |
| SECONDARY_2 | MNQ_robust_A_MOD_2 | MNQ | 0.08 | 0.17 | 0.12 | 0.09 | -220.62 | -701.04 | 55.67 | -756.7 | -3488.46 | -287.28 |
| SECONDARY_2 | MNQ_arch_A_AGG_0 | MNQ | 0.1 | 0.17 | 0.1 | 0.08 | 220.21 | 734.35 | 74.34 | 660.01 | 1362.14 | 134.78 |
| SECONDARY_2 | MNQ_robust_C_CON_0 | MNQ | 0.26 | 0.17 | 0.15 | 0.12 | 5326.54 | 5726.44 | 4.55 | 5721.89 | 20343.1 | 5325.78 |
| SECONDARY_2 | MNQ_r2_C_MOD_1 | MNQ | 0.18 | 0.17 | 0.24 | 0.13 | 2554.48 | 1839.25 | 5.45 | 1833.8 | 14455.42 | 2548.47 |
| SECONDARY_2 | ES_robust_A_MOD_1 | ES | 0.05 | 0.08 | 0.13 | 0.13 | 310.72 | 37.32 | 39.37 | -4.02 | 5649.96 | 267.16 |
| SECONDARY_2 | ES_r2_F_MOD_2 | ES | 0.07 | 0.08 | 0.15 | 0.15 | 314.67 | 164.4 | 10.8 | 153.06 | 4279.86 | 301.96 |
| SECONDARY_2 | ES_r2_A_CON_1 | ES | 0.11 | 0.08 | 0.22 | 0.21 | 1703.64 | 1347.44 | 11.62 | 1335.24 | 16010.35 | 1689.3 |
| SECONDARY_2 | ES_robust_C_CON_4 | ES | 0.09 | 0.08 | 0.19 | 0.17 | 1323.28 | 753.34 | 13.0 | 739.68 | 13850.42 | 1308.67 |

## Reading (descriptive; no rescue, no change)
* PRIMARY failed on net P&L (-$7,164), remove-top-3 and concentration (total negative). Drawdown ($12.8k < $15k), worst day
  (-$2,213 > -$3k) and margin (peak 7%) stayed inside the frozen envelope. SECONDARY_1 failed the same way (-$8,064).
  SECONDARY_2 (P1 cluster equal risk, CONSERVATIVE) passed every frozen condition (+$9,691, MaxDD $6.2k, worst -$1,523, ex-top3 +$23/day,
  best day 21% of total); it is reported only and NOT promoted automatically.
* Losses concentrated in 2025-12 .. 2026-03 (PRIMARY -$12.0k over four months, window DD $12.7k at end of March); April-May recovered partly.
* Both matched-beta measures are strongly negative for PRIMARY/SECONDARY_1 (about -$80/day): passive exposure of the same size
  earned money while the portfolios lost.
* Attribution shows a large gap between what the sleeves wanted and what the portfolio held. For PRIMARY the weighted virtual desires
  earned +$15.7k gross (MNQ_robust_C_CON_0 alone +$14.1k), but the integer net position earned -$6.7k gross. With calibrated risk scales the
  weighted desires are fractions of a contract (PRIMARY average about 0.4 MES + 0.5 MNQ held), so integer rounding with the 0.6 deadband
  often held a different exposure than intended. MNQ_robust_C_CON_0's desire was mostly rounded away, while the losing MNQ_robust_A_MOD_2 and
  ES_robust_A_MOD_1 exposure was held. This implementation effect was present but not visible on DEV/VAL; it is recorded here as a finding
  for future work, NOT used to modify or re-run this holdout.
* Standalone sleeves over the holdout: 7 of 8 eligible sleeves were positive on their own ledgers (MNQ_robust_A_MOD_2 -$3.5k the exception).

## Post-holdout governance
The 2025-10-01 .. 2026-05-27 window is now permanently OPENED / USED and may never again be called untouched. Any future work (including
ML / XGBoost / meta-allocation or integer-sizing fixes) must treat it as historical research data and requires a NEW forward / out-of-sample
period. No retune, reweight, member change, threshold change or rerun under the holdout label. LIVE_AUTHORIZATION = NO.
