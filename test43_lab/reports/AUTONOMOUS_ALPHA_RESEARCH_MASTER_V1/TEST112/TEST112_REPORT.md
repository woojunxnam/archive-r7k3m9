# TEST112 reduce-only portfolio risk overlay — results (prereg 91532f1)

```json
{
 "TEST112_CLASSIFICATION": "REJECT (0/3 states COHERENT; no overlay applied)",
 "R1_VOL_REGIME": "not coherent (Spearman -0.2)",
 "R2_TREND_EXTENSION": "not coherent (Spearman -0.4): the most-extended quintile has Main mean -7.6 $/day (best-minus-worst CI excludes 0) but the adjacent quintile is the BEST (261.8 $/day) -> isolated cell, rejected by the response-curve rule",
 "R3_RECENT_DRAWDOWN": "not coherent (Spearman -0.6)",
 "OVERLAY_VALUE": "NO",
 "MAIN_MODIFIED": "NO",
 "DISTINCT_NEW_DEFINITIONS": 3,
 "LEDGER_ROWS": 15,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Main daily P&L by causal state quintile

|    | state   |   bin |   n |   main_mean |
|---:|:--------|------:|----:|------------:|
|  0 | R1      |     0 | 249 |     84.6153 |
|  1 | R1      |     1 | 271 |    202.9975 |
|  2 | R1      |     2 | 350 |    166.2760 |
|  3 | R1      |     3 | 316 |     56.3031 |
|  4 | R1      |     4 | 251 |    137.9364 |
|  5 | R2      |     0 | 309 |    163.7847 |
|  6 | R2      |     1 | 323 |    145.3844 |
|  7 | R2      |     2 | 284 |    124.5262 |
|  8 | R2      |     3 | 231 |    261.8148 |
|  9 | R2      |     4 | 320 |     -7.6430 |
| 10 | R3      |     0 | 313 |    140.9582 |
| 11 | R3      |     1 | 330 |    162.6831 |
| 12 | R3      |     2 | 338 |    191.5835 |
| 13 | R3      |     3 | 228 |     94.3684 |
| 14 | R3      |     4 | 365 |     92.6674 |

## Coherence / overlay

|    | state   |   spearman |   worst_bin |   worst_mean |   best_minus_worst |    ci_lo |    ci_hi |   years_same_sign | COHERENT   | OVERLAY_VALUE   | rule                                         |
|---:|:--------|-----------:|------------:|-------------:|-------------------:|---------:|---------:|------------------:|:-----------|:----------------|:---------------------------------------------|
|  0 | R1      |    -0.2000 |           3 |      56.3031 |           146.6944 | -24.5940 | 322.9397 |                 6 | False      | False           | NOT APPLIED (not coherent or worst bin >= 0) |
|  1 | R2      |    -0.4000 |           4 |      -7.6430 |           269.4578 |  81.8339 | 464.2151 |                 6 | False      | False           | NOT APPLIED (not coherent or worst bin >= 0) |
|  2 | R3      |    -0.6000 |           4 |      92.6674 |            98.9161 | -64.4256 | 266.9070 |                 5 | False      | False           | NOT APPLIED (not coherent or worst bin >= 0) |

Per-instrument rows: out/index_alpha_master_v1/t112/.

Interpretation: pre-session index states do not map monotonically onto Main's daily P&L; the only bad cell (very extended trend) sits next to the best cell, so a reduce-only overlay would be a fitted isolated cell. Consistent with TEST56. No overlay.

