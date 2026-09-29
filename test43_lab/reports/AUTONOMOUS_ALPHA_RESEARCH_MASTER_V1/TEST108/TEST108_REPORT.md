# TEST108 range budget veto — results (prereg 4951038)

```json
{
 "TEST108_CLASSIFICATION": "REJECT (0/12 curves COHERENT; VETO_HAS_VALUE = NO everywhere)",
 "RB1_CONSUMED_RANGE_ON_BRK12": "weak negative slope (Spearman -0.5..-0.7), CI includes 0; veto of the top quintile improves the base by only +0.0006..+0.0015 ATR",
 "RB_ON_ORB15": "no negative slope; the most-consumed quintile is among the best (vetoing it HURTS by -0.0004..-0.0029 ATR)",
 "RANGE_BUDGET_VETO_ADDS_VALUE": "NO",
 "DISTINCT_NEW_DEFINITIONS": 4,
 "LEDGER_ROWS": 400,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Coherence (state null year x vt x tod3)

|    | feature   | horizon   |   spearman |   top_minus_bottom |   ci_lo |   ci_hi |   years_same_sign |   inst_same_sign | COHERENT   |   best_bin |   best_bin_xN | bins                                        | VETO_HAS_VALUE   |
|---:|:----------|:----------|-----------:|-------------------:|--------:|--------:|------------------:|-----------------:|:-----------|-----------:|--------------:|:--------------------------------------------|:-----------------|
|  0 | RB1_BRK12 | h12       |    -0.7000 |            -0.0119 | -0.0301 |  0.0056 |                 5 |                4 | False      |          0 |        0.0090 | [0.009, -0.0022, 0.0041, 0.0007, -0.0029]   | False            |
|  1 | RB1_BRK12 | h24       |    -0.5000 |            -0.0099 | -0.0414 |  0.0209 |                 5 |                3 | False      |          0 |        0.0089 | [0.0089, -0.0013, 0.0057, -0.0046, -0.001]  | False            |
|  2 | RB1_BRK12 | h1615     |    -0.7000 |            -0.0165 | -0.0548 |  0.0204 |                 5 |                4 | False      |          0 |        0.0090 | [0.009, -0.0074, 0.0071, -0.0041, -0.0075]  | False            |
|  3 | RB2_BRK12 | h12       |     0.1000 |             0.0022 | -0.0151 |  0.0186 |                 4 |                3 | False      |          1 |        0.0084 | [-0.0017, 0.0084, 0.0035, -0.0015, 0.0005]  | False            |
|  4 | RB2_BRK12 | h24       |     0.3000 |             0.0117 | -0.0191 |  0.0397 |                 6 |                4 | False      |          4 |        0.0089 | [-0.0028, 0.0074, 0.0042, -0.0064, 0.0089]  | False            |
|  5 | RB2_BRK12 | h1615     |    -0.2000 |             0.0014 | -0.0342 |  0.0369 |                 4 |                2 | False      |          1 |        0.0039 | [-0.0007, 0.0039, -0.0023, -0.0032, 0.0006] | False            |
|  6 | RB1_ORB15 | h12       |     0.3000 |             0.0117 | -0.0232 |  0.0485 |                 4 |                3 | False      |          1 |        0.0195 | [0.0052, 0.0195, 0.0137, 0.0073, 0.0169]    | False            |
|  7 | RB1_ORB15 | h24       |     0.6000 |             0.0095 | -0.0397 |  0.0572 |                 5 |                2 | False      |          4 |        0.0174 | [0.0079, 0.0138, 0.0106, 0.0105, 0.0174]    | False            |
|  8 | RB1_ORB15 | h1615     |     0.2000 |             0.0071 | -0.0594 |  0.0751 |                 4 |                2 | False      |          4 |        0.0266 | [0.0195, 0.0201, -0.0034, 0.0154, 0.0266]   | False            |
|  9 | RB2_ORB15 | h12       |     0.2000 |             0.0076 | -0.0283 |  0.0437 |                 4 |                3 | False      |          1 |        0.0211 | [0.0076, 0.0211, 0.0061, 0.0121, 0.0152]    | False            |
| 10 | RB2_ORB15 | h24       |     0.1000 |             0.0062 | -0.0399 |  0.0532 |                 4 |                2 | False      |          1 |        0.0234 | [0.0073, 0.0234, -0.0035, 0.0191, 0.0135]   | False            |
| 11 | RB2_ORB15 | h1615     |     0.2000 |             0.0075 | -0.0596 |  0.0761 |                 4 |                2 | False      |          1 |        0.0299 | [0.0169, 0.0299, -0.01, 0.0173, 0.0244]     | False            |

## Veto arithmetic (pooled)

|    | curve     | horizon   |   base_xN |   vetoed_xN |   improvement |   frac_removed |   top_bin_xN |
|---:|:----------|:----------|----------:|------------:|--------------:|---------------:|-------------:|
|  0 | RB1_BRK12 | h12       |    0.0019 |      0.0029 |        0.0010 |         0.1770 |      -0.0029 |
|  1 | RB1_BRK12 | h24       |    0.0016 |      0.0022 |        0.0006 |         0.1770 |      -0.0010 |
|  2 | RB1_BRK12 | h1615     |   -0.0004 |      0.0011 |        0.0015 |         0.1770 |      -0.0075 |
|  3 | RB2_BRK12 | h12       |    0.0019 |      0.0022 |        0.0003 |         0.1839 |       0.0005 |
|  4 | RB2_BRK12 | h24       |    0.0021 |      0.0006 |       -0.0015 |         0.1839 |       0.0089 |
|  5 | RB2_BRK12 | h1615     |   -0.0004 |     -0.0006 |       -0.0002 |         0.1839 |       0.0006 |
|  6 | RB1_ORB15 | h12       |    0.0123 |      0.0111 |       -0.0012 |         0.2044 |       0.0169 |
|  7 | RB1_ORB15 | h24       |    0.0120 |      0.0106 |       -0.0014 |         0.2044 |       0.0174 |
|  8 | RB1_ORB15 | h1615     |    0.0155 |      0.0126 |       -0.0029 |         0.2044 |       0.0266 |
|  9 | RB2_ORB15 | h12       |    0.0123 |      0.0115 |       -0.0007 |         0.2044 |       0.0152 |
| 10 | RB2_ORB15 | h24       |    0.0120 |      0.0116 |       -0.0004 |         0.2044 |       0.0135 |
| 11 | RB2_ORB15 | h1615     |    0.0155 |      0.0132 |       -0.0023 |         0.2044 |       0.0244 |

Per-instrument rows: out/index_alpha_master_v1/t108/.

Interpretation: consumption of the daily range budget does not predict failure of intraday continuation entries; for opening-range breaks larger consumption is, if anything, better. Family SATURATED.

