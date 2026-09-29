# TEST115 HTF trend-strength / stage factory — results (prereg 28b77c2)

```json
{
 "TEST115_CLASSIFICATION": "REJECT (0/8 curves COHERENT; STRENGTH_ADDS_VALUE = NO)",
 "T1_ADX_IN_UPTREND": "not coherent (Spearman -0.3); weakest trend quintile best",
 "T2_STAGE2_SLOPE": "not coherent (-0.6); steepest stage-2 slopes worst",
 "T3_TSMOM_12M": "not coherent (-0.8/-0.6); top TSMOM quintiles negative vs direction null",
 "T4_TSMOM_1M": "flat",
 "STRENGTH_BEYOND_DIRECTION": "NO (if anything stronger trends have lower intraday long excess; never significant)",
 "DISTINCT_NEW_DEFINITIONS": 4,
 "LEDGER_ROWS": 40,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Coherence (null: year x vt x close>SMA50)

|    | feature        | horizon   |   spearman |   top_minus_bottom |   ci_lo |   ci_hi |   years_same_sign |   inst_same_sign | COHERENT   | STRENGTH_ADDS_VALUE   | bins                                        |
|---:|:---------------|:----------|-----------:|-------------------:|--------:|--------:|------------------:|-----------------:|:-----------|:----------------------|:--------------------------------------------|
|  0 | T1_ADX         | R1615     |    -0.3000 |            -0.0343 | -0.1129 |  0.0404 |                 6 |                3 | False      | False                 | [0.0231, -0.0337, -0.0025, -0.023, -0.0112] |
|  1 | T1_ADX         | R1600     |    -0.3000 |            -0.0397 | -0.1194 |  0.0355 |                 6 |                3 | False      | False                 | [0.0246, -0.0308, 0.0019, -0.0173, -0.0151] |
|  2 | T2_STAGE_SLOPE | R1615     |    -0.6000 |            -0.0442 | -0.1783 |  0.0883 |                 3 |                3 | False      | False                 | [-0.0087, 0.0071, 0.0357, -0.0523, -0.0529] |
|  3 | T2_STAGE_SLOPE | R1600     |    -0.6000 |            -0.0452 | -0.1768 |  0.0860 |                 3 |                3 | False      | False                 | [-0.0096, 0.0057, 0.0367, -0.0447, -0.0548] |
|  4 | T3_TSMOM_12M   | R1615     |    -0.8000 |            -0.0446 | -0.1430 |  0.0518 |                 1 |                4 | False      | False                 | [0.0192, 0.0214, 0.0189, -0.078, -0.0254]   |
|  5 | T3_TSMOM_12M   | R1600     |    -0.6000 |            -0.0419 | -0.1405 |  0.0572 |                 1 |                4 | False      | False                 | [0.0184, 0.0313, 0.0208, -0.0814, -0.0236]  |
|  6 | T4_TSMOM_1M    | R1615     |    -0.1000 |             0.0090 | -0.0694 |  0.0926 |                 3 |                3 | False      | False                 | [-0.0095, 0.0051, 0.0073, -0.0435, -0.0006] |
|  7 | T4_TSMOM_1M    | R1600     |     0.2000 |             0.0128 | -0.0664 |  0.0969 |                 3 |                3 | False      | False                 | [-0.0095, 0.0001, 0.0079, -0.0406, 0.0033]  |

Per-instrument rows: out/index_alpha_master_v1/t115/.

Interpretation: once the simple HTF direction is known, trend STRENGTH (ADX, stage-2 slope, time-series momentum) carries no additional information for intraday long returns; the non-significant tilt is toward mean reversion at extremes. Family closed.

