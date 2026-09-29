# TEST102 ATR phase / EMA ribbon — results (prereg 3a389ea)

```json
{
 "TEST102_CLASSIFICATION": "REJECT (S1 not COHERENT; S2/S3 0/9 EVENT_CLUE; S4 NOT_RUN_BY_RULE)",
 "S1_PHASE": "NOT COHERENT (monotone DEcreasing at 120m/16:15: low phase better, Spearman -0.9/-1.0, but top-minus-bottom CI includes 0); no momentum value in ATR phase once session move is held fixed",
 "S2_RIBBON_ONSET": "WEAK_RESEARCH_CLUE_ONLY at 60m only",
 "S3_RIBBON_PULLBACK": "E21 / E8 WEAK at 60m only (xF +0.004..+0.005, CI includes 0); negative at 120m",
 "S4": "NOT_RUN_BY_RULE (S1 has no value)",
 "ATR_PHASE_RIBBON_ADDS_ALPHA": "NO",
 "DISTINCT_NEW_DEFINITIONS": 4,
 "LEDGER_ROWS": 160,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant         | horizon   |    n |    mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:----------------|:----------|-----:|--------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | S2_RIBBON_ONSET | h12       | 4657 |  0.0064 |     0.0109 |  0.0040 | -0.0048 |  0.0131 |           5 |          2 |    0.0065 |  0.0003 |  0.0067 |  0.0004 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  1 | S2_RIBBON_ONSET | h24       | 4061 |  0.0000 |     0.0109 | -0.0027 | -0.0182 |  0.0128 |           4 |          1 |   -0.0008 |  0.0009 | -0.0018 | -0.0117 | True          | 0.98/0.02/0.00 | REJECT                  |
|  2 | S2_RIBBON_ONSET | h1615     | 4657 |  0.0083 |     0.0109 |  0.0063 | -0.0152 |  0.0274 |           4 |          3 |    0.0076 |  0.0074 |  0.0012 | -0.0019 | False         | 0.99/0.01/0.00 | REJECT                  |
|  3 | S3_E21          | h12       | 4613 |  0.0048 |     0.0109 |  0.0047 | -0.0045 |  0.0134 |           6 |          3 |    0.0044 |  0.0096 |  0.0048 | -0.0006 | True          | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  4 | S3_E21          | h24       | 4164 | -0.0004 |     0.0109 |  0.0011 | -0.0131 |  0.0156 |           4 |          2 |    0.0002 | -0.0162 | -0.0026 | -0.0104 | False         | 0.96/0.04/0.00 | REJECT                  |
|  5 | S3_E21          | h1615     | 4613 | -0.0017 |     0.0109 | -0.0038 | -0.0265 |  0.0171 |           4 |          1 |   -0.0052 |  0.0016 | -0.0090 | -0.0113 | False         | 0.98/0.02/0.00 | REJECT                  |
|  6 | S3_E8           | h12       | 5009 |  0.0029 |     0.0109 |  0.0040 | -0.0061 |  0.0138 |           5 |          3 |    0.0047 |  0.0025 |  0.0024 | -0.0042 | True          | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  7 | S3_E8           | h24       | 4669 | -0.0037 |     0.0109 | -0.0014 | -0.0158 |  0.0121 |           4 |          1 |   -0.0020 | -0.0152 | -0.0060 | -0.0162 | False         | 0.98/0.02/0.00 | REJECT                  |
|  8 | S3_E8           | h1615     | 5009 |  0.0015 |     0.0109 |  0.0001 | -0.0232 |  0.0227 |           4 |          2 |    0.0016 | -0.0021 | -0.0088 | -0.0103 | False         | 0.98/0.02/0.00 | REJECT                  |

## S1 phase response-curve coherence (null: year x vt x tod3 x session-move tercile)

|    | feature   | horizon   |   spearman |   top_minus_bottom |   ci_lo |   ci_hi |   years_same_sign |   inst_same_sign | COHERENT   |   best_bin |   best_bin_xN | bins                                        |
|---:|:----------|:----------|-----------:|-------------------:|--------:|--------:|------------------:|-----------------:|:-----------|-----------:|--------------:|:--------------------------------------------|
|  0 | S1_PHASE  | h12       |    -0.5000 |            -0.0014 | -0.0112 |  0.0087 |                 4 |                3 | False      |          0 |        0.0010 | [0.001, -0.0004, 0.0003, -0.0005, -0.0004]  |
|  1 | S1_PHASE  | h24       |    -0.9000 |            -0.0072 | -0.0233 |  0.0092 |                 5 |                4 | False      |          0 |        0.0054 | [0.0054, 0.0021, -0.0016, -0.0048, -0.0018] |
|  2 | S1_PHASE  | h1615     |    -1.0000 |            -0.0186 | -0.0428 |  0.0053 |                 6 |                4 | False      |          0 |        0.0119 | [0.0119, -0.001, -0.0016, -0.0029, -0.0067] |

Per-instrument rows: out/index_alpha_master_v1/t102/.

Interpretation: the ATR-normalised distance from EMA21 carries a weak mean-reversion tilt (not momentum) once the session move is fixed; ribbon onset and ribbon pullbacks add a small, statistically unresolved 60-minute residual that disappears by 120 minutes. Family SATURATED.

