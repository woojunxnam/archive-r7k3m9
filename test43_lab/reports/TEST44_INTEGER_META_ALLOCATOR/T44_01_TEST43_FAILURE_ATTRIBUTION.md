# T44_01 TEST43 failure attribution

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.


## D0 (TEST43 PRIMARY): fractional virtual desire vs realised integer position, gross $
| period | ES_virtual_fractional_gross | ES_realised_integer_gross | ES_avg_desired | ES_avg_held | ES_share_bars_desired_lt_0.5_held_0 | MNQ_virtual_fractional_gross | MNQ_realised_integer_gross | MNQ_avg_desired | MNQ_avg_held | MNQ_share_bars_desired_lt_0.5_held_0 | gap_total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 31290.0 | 28982.0 | 1.0 | 1.0 | 0.0 | 126904.0 | 111358.0 | 1.0 | 1.0 | 0.0 | -17853.0 |
| F1_2019_2020 | 8127.0 | 9870.0 | 1.0 | 1.0 | 0.0 | 34972.0 | 34979.0 | 2.0 | 2.0 | 0.0 | 1750.0 |
| F2_2021_2022 | 8085.0 | 7389.0 | 1.0 | 1.0 | 0.0 | 21900.0 | 22954.0 | 1.0 | 1.0 | 0.0 | 357.0 |
| F3_2023_2024 | 8599.0 | 7588.0 | 1.0 | 1.0 | 0.0 | 41177.0 | 42502.0 | 1.0 | 1.0 | 0.0 | 313.0 |
| F4_2025_2026 | 6479.0 | 4136.0 | 1.0 | 1.0 | 0.0 | 28854.0 | 10924.0 | 1.0 | 1.0 | 0.0 | -20272.0 |
| FORMER_HOLDOUT | 1645.0 | -2666.0 | 1.0 | 0.0 | 0.0 | 14099.0 | -4002.0 | 1.0 | 0.0 | 0.0 | -22412.0 |

## TEST43 holdout sleeve attribution (from the one-shot holdout)
| sleeve | contract_weight | avg_weighted_desired_contracts | avg_realised_contracts_allocated | gross_contribution_virtual | gross_contribution_realised | standalone_virtual_ledger_holdout_pnl |
|---|---|---|---|---|---|---|
| MNQ_robust_A_MOD_2 | 0.22 | 0.32 | 0.2 | -584.0 | -4286.19 | -3488.46 |
| ES_robust_A_MOD_1 | 0.25 | 0.7 | 0.44 | 1645.04 | -2666.25 | 5649.96 |
| MNQ_robust_C_CON_0 | 0.69 | 0.41 | 0.07 | 14099.91 | 483.64 | 20343.1 |
| MNQ_arch_A_AGG_0 | 0.26 | 0.27 | 0.18 | 582.91 | -198.95 | 1362.14 |

The quantisation gap was small and two-sided in 2019-2024 (+$1.8k, +$0.4k, +$0.3k) and -$22.4k in the former holdout: rounding at
fractional desires (~0.2-0.9 contracts per instrument) turned a +$15.7k desired P&L into -$6.7k. It is an episodic, path-dependent
distortion rather than a persistent bias, which is why DEV/VAL could not reveal it.
