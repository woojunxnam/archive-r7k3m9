# T44_00 Status

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

Research complete; pre-OOS freeze and new-OOS rules written and hashed. No data after 2026-05-27 was acquired or inspected.

```
FRACTIONAL_ROUNDING_WAS_MATERIAL_FAILURE_SOURCE = YES for the former holdout (integer gross -$22.4k vs virtual fractional; PRIMARY -$6.7k realised vs +$15.7k desired), but NOT a persistent historical bias (gap 2019-2024 within +-$1.8k)
ONE_CONTRACT_BEATS_TEST43_ALLOCATOR = NO on full-history return/DD (best D1 0.0032 vs D0 0.0059); YES only inside the former-holdout window
ONE_TWO_CONTRACT_BEATS_TEST43_ALLOCATOR = NO on full-history return/DD (best D2 0.0041); YES only inside the former-holdout window
CLUSTER_SLOT_ADDS_VALUE = MARGINAL (best feasible D3 0.0035 vs D1 0.0029 at max 1; lower DD, not better at max 2+)
INTEGER_TRACKING_ADDS_VALUE = YES among integer allocators (D4 best at every contract cap; best feasible 0.0045)
RESIDUAL_ALLOCATOR_ADDS_VALUE = NO (best feasible 0.0031 with 2-5x turnover; error diffusion re-creates the chop it was meant to avoid)
BEST_PRACTICAL_MAX_CONTRACTS = 2 (highest return inside the MODERATE envelope with every fold positive; 1 has similar return/DD; 3-4 breach the envelope)
RIDGE_ADDS_VALUE_OVER_SIMPLE_INTEGER = YES on risk efficiency (ML span ret/DD 0.0126 vs 0.0042, MaxDD $1618 vs $8819, excess 18.2 vs 15.6/day) but LOWER absolute P&L (20.5 vs 37.5/day)
XGBOOST_ADDS_VALUE_OVER_SIMPLE_INTEGER = WEAK YES on ret/DD (0.0083 vs 0.0042) with much lower P&L (16.2 vs 37.5/day) and lower matched-beta excess
XGBOOST_ADDS_VALUE_OVER_RIDGE = NO (ret/DD 0.0083 vs 0.0126; excess 14.4 vs 18.2)
XGBOOST_COMPLEXITY_JUSTIFIED = NO
CHAMPION_CONTROL_V1 = P1_CLUSTER_EQUAL_RISK|CONSERVATIVE
SIMPLE_INTEGER_CHALLENGER = D4|off0.1|lam0.0|mu0.0|max1
RIDGE_CHALLENGER = RIDGE|A_ONLY|TOP_HALF|D4|off0.2|lam0.0|mu0.0|max2
XGBOOST_CHALLENGER = XGB_REGULARIZED|E_ALL|GATE_POS|D4|off0.1|lam0.0|mu0.0|max1
PRE_OOS_FREEZE_SHA256 = 3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4
NEW_OOS_RULES_SHA256 = 2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236
NEW_OOS_DATA_ACQUIRED = NO
NEW_OOS_OPENED = NO
PORTFOLIO_MEMBERSHIP_CHANGED = NO
LIVE_AUTHORIZATION = NO
```

## Final comparison (all candidates on identical costs, margin, $150k account, MODERATE governor; CHAMPION frozen as TEST43)
| candidate | ALL_avg | ALL_max_dd | ALL_worst | ALL_ret_dd | ALL_excess_vs_mb | ML_OOS_SPAN_avg | ML_OOS_SPAN_max_dd | ML_OOS_SPAN_ret_dd | ML_OOS_SPAN_excess_vs_mb | F4_2025_2026_avg | F4_2025_2026_max_dd | Y2020_avg | Y2022_avg | FORMER_HOLDOUT_avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SIMPLE_INTEGER_CHALLENGER | 39.521 | 8819.4 | -2482.49 | 0.004 | 13.955 | 37.457 | 8819.4 | 0.004 | 15.632 | 69.829 | 8819.4 | 56.708 | -21.672 | 67.989 |
| RIDGE_CHALLENGER | 31.565 | 5465.0 | -1785.25 | 0.006 | 18.625 | 20.454 | 1618.36 | 0.013 | 18.196 | 32.856 | 1618.36 | 83.048 | 4.788 | 44.836 |
| XGBOOST_CHALLENGER | 23.823 | 5169.71 | -1785.25 | 0.005 | 13.877 | 16.188 | 1956.18 | 0.008 | 14.367 | 30.807 | 1956.18 | 56.708 | 1.946 | 44.494 |
| CHAMPION_CONTROL_V1 | 52.59 | 6193.43 | -1722.99 | 0.008 | 29.428 | 53.659 | 6193.43 | 0.009 | 36.168 | 66.318 | 6193.43 | 74.835 | 3.227 | 58.732 |
| D0_CURRENT_TEST43 | 75.54 | 12788.17 | -2499.96 | 0.006 | 38.072 | 64.134 | 12788.17 | 0.005 | 37.117 | 39.367 | 12788.17 | 151.295 | 1.326 | -43.42 |

Reading: no TEST44 allocator beats CHAMPION_CONTROL_V1 on absolute P&L or matched-beta excess. The Ridge challenger has the best risk
efficiency on the ML walk-forward span (ret/DD 0.013 vs champion 0.009) at far lower exposure. The walk-forward span is NOT fully clean:
the frozen sleeves were optimised on 2019-2024, and ~100 meta variants were compared on the same span (selection optimism). F4
(2025-01..2026-05, sleeves out of sample) is the cleanest block. The new OOS (from 2026-05-28) decides; promotion requires the frozen
thresholds in T44_22.
