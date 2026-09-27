# P14 Shared account, margin and risk

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


One $150,000 account; shared equity, drawdown, margin (raw price x IBKR fraction), governor (portfolio DD tiers, day loss
cut, gross $ATR and instrument-share caps available), net integer target per instrument, next-bar-open fills.
Validation: single-sleeve portfolios reproduce the standalone sleeve P&L exactly (ES_robust_A_MOD_1 $93,596; MNQ_robust_A_MOD_2 $159,115 on DEV).

## Selected portfolios (DEV+VAL)
| role | portfolio | avg_margin_util | peak_margin_util | avg_on_margin_util | peak_on_margin_util | avg_atr_$ | peak_atr_$ | avg_MES | avg_MNQ | max_total_contracts |
|---|---|---|---|---|---|---|---|---|---|---|
| PRIMARY | P2B_STATIC_4SLEEVE|MODERATE | 0.02546344360821379 | 0.1129899735285168 | 0.026083360898736255 | 0.1129899735285168 | 958.389933437943 | 8538.7 | 0.8908103668104376 | 1.3905164976145774 | 10 |
| SECONDARY_1 | P2_STATIC_DIVERSIFIED|MODERATE | 0.024240376083328026 | 0.1450557831565569 | 0.024919665481399882 | 0.1450557831565569 | 899.7986983354365 | 11186.2875 | 0.9001739843283096 | 1.1954900351279152 | 13 |
| SECONDARY_2 | P1_CLUSTER_EQUAL_RISK|CONSERVATIVE | 0.018171521372241893 | 0.0778603782478826 | 0.01922949974578671 | 0.0778603782478826 | 561.5547442731887 | 4865.2875 | 0.7385804305678632 | 0.7302478200589122 | 6 |

Margin is never binding (peak utilisation well below the 0.5 cap), so the 1.5x intraday / 2x overnight margin stresses
leave P&L unchanged; the binding constraint in calibration is the worst-day floor.

