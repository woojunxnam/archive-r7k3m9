# TEST104 level interaction factory — results (prereg 3ead923)

```json
{
 "TEST104_CLASSIFICATION": "REJECT by ESP-1 (0/39 EVENT_CLUE); L2 failed-breakdown-reclaim-retest = WEAK_RESEARCH_CLUE_ONLY, family-consistent",
 "L1_BREAK_RETEST_HOLD": "PDH / SWH60 WEAK (positive all horizons, CIs include 0); PWH mixed; ORH / H2H REJECT (negative)",
 "L2_FAILED_BREAKDOWN_RECLAIM_RETEST": "WEAK_RESEARCH_CLUE_ONLY on ALL 5 support types; 15/15 level x primary-horizon cells positive (xF +0.005..+0.028); L2_PDL 60m CI [+0.0010,+0.0336] excludes 0 but gross mean 0.0088 < cost 0.0109 -> fails the ESP-1 cost condition; L2_SWL60 16:15 xF +0.0282 [-0.0070,+0.0631]",
 "L2_FAMILY_CONSISTENCY_NOTE": "descriptive only (post hoc, not a preregistered classification criterion); the five L2 level types share sessions and are not independent",
 "L3_SWEEP_SPRING_2B_NEW_LEVELS": "PWL REJECT (negative); SWL60 WEAK; L2H WEAK at 60m only",
 "L4_APPROACH_SPEED": "NOT COHERENT",
 "L5_TOUCH_COUNT": "NOT COHERENT (first break with 0 prior touches best, top-minus-bottom CI includes 0)",
 "LEVEL_FAILURE_COHERENT_EVENT_CLUE": "NO -> TEST105 NOT_RUN_BY_RULE",
 "MULTIPLE_TESTING": "39 primary tests, ~1.0 chance CI pass expected; 1 CI pass observed (L2_PDL 60m, fails cost)",
 "DISTINCT_NEW_DEFINITIONS": 15,
 "LEDGER_ROWS": 460,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant   | horizon   |    n |    mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:----------|:----------|-----:|--------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | L1_PDH    | h12       | 1422 |  0.0047 |     0.0108 |  0.0064 | -0.0080 |  0.0202 |           5 |          3 |    0.0103 |  0.0202 |  0.0028 | -0.0035 | True          | 0.92/0.08/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  1 | L1_PDH    | h24       | 1353 |  0.0090 |     0.0108 |  0.0075 | -0.0115 |  0.0274 |           6 |          2 |    0.0091 |  0.0208 |  0.0032 | -0.0038 | True          | 0.91/0.09/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  2 | L1_PDH    | h1615     | 1422 |  0.0056 |     0.0108 |  0.0074 | -0.0252 |  0.0398 |           6 |          3 |    0.0098 |  0.0279 | -0.0099 | -0.0081 | True          | 0.92/0.08/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  3 | L1_PWH    | h12       |  662 |  0.0089 |     0.0115 |  0.0142 | -0.0026 |  0.0308 |           6 |          2 |    0.0101 | -0.0023 |  0.0100 |  0.0028 | False         | 0.89/0.11/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  4 | L1_PWH    | h24       |  621 | -0.0042 |     0.0115 | -0.0044 | -0.0290 |  0.0192 |           5 |          2 |   -0.0010 |  0.0025 | -0.0093 | -0.0158 | True          | 0.87/0.13/0.00 | REJECT                  |
|  5 | L1_PWH    | h1615     |  662 |  0.0068 |     0.0115 | -0.0144 | -0.0487 |  0.0190 |           2 |          1 |   -0.0178 | -0.0189 | -0.0062 | -0.0033 | True          | 0.90/0.10/0.00 | REJECT                  |
|  6 | L1_ORH    | h12       | 2605 | -0.0010 |     0.0108 | -0.0036 | -0.0148 |  0.0080 |           3 |          1 |    0.0007 | -0.0065 | -0.0005 | -0.0061 | True          | 0.84/0.16/0.00 | REJECT                  |
|  7 | L1_ORH    | h24       | 2526 |  0.0033 |     0.0108 | -0.0028 | -0.0208 |  0.0133 |           3 |          1 |    0.0008 | -0.0085 |  0.0009 | -0.0052 | True          | 0.83/0.16/0.00 | REJECT                  |
|  8 | L1_ORH    | h1615     | 2605 |  0.0070 |     0.0108 | -0.0055 | -0.0326 |  0.0195 |           5 |          0 |   -0.0015 | -0.0191 | -0.0007 | -0.0020 | True          | 0.84/0.16/0.00 | REJECT                  |
|  9 | L1_SWH60  | h12       | 1255 |  0.0030 |     0.0107 |  0.0068 | -0.0071 |  0.0213 |           5 |          3 |    0.0090 |  0.0020 |  0.0001 | -0.0036 | True          | 0.90/0.10/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 10 | L1_SWH60  | h24       | 1161 |  0.0154 |     0.0107 |  0.0143 | -0.0050 |  0.0343 |           6 |          3 |    0.0166 | -0.0029 |  0.0073 |  0.0049 | True          | 0.88/0.11/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 11 | L1_SWH60  | h1615     | 1255 |  0.0154 |     0.0107 |  0.0137 | -0.0147 |  0.0436 |           6 |          3 |    0.0165 | -0.0227 | -0.0008 |  0.0031 | True          | 0.90/0.10/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 12 | L1_H2H    | h12       | 3319 | -0.0022 |     0.0109 | -0.0038 | -0.0138 |  0.0067 |           4 |          1 |   -0.0049 | -0.0379 | -0.0023 | -0.0079 | True          | 0.51/0.48/0.02 | REJECT                  |
| 13 | L1_H2H    | h24       | 3102 | -0.0037 |     0.0109 | -0.0138 | -0.0299 |  0.0012 |           2 |          1 |   -0.0171 | -0.0565 | -0.0043 | -0.0127 | False         | 0.50/0.46/0.03 | REJECT                  |
| 14 | L1_H2H    | h1615     | 3319 |  0.0006 |     0.0109 | -0.0198 | -0.0455 |  0.0047 |           2 |          1 |   -0.0224 | -0.0387 | -0.0066 | -0.0080 | True          | 0.53/0.46/0.02 | REJECT                  |
| 15 | L2_PDL    | h12       | 1040 |  0.0088 |     0.0109 |  0.0171 |  0.0010 |  0.0336 |           5 |          4 |    0.0131 | -0.0107 |  0.0082 |  0.0037 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 16 | L2_PDL    | h24       |  941 |  0.0089 |     0.0109 |  0.0168 | -0.0054 |  0.0394 |           5 |          4 |    0.0125 | -0.0275 |  0.0083 |  0.0000 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 17 | L2_PDL    | h1615     | 1040 |  0.0226 |     0.0109 |  0.0159 | -0.0182 |  0.0496 |           5 |          3 |    0.0107 | -0.0156 |  0.0197 |  0.0138 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 18 | L2_PWL    | h12       |  409 |  0.0147 |     0.0106 |  0.0187 | -0.0089 |  0.0458 |           5 |          3 |    0.0093 |  0.0051 |  0.0105 |  0.0097 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 19 | L2_PWL    | h24       |  368 |  0.0176 |     0.0106 |  0.0163 | -0.0215 |  0.0533 |           5 |          2 |    0.0018 |  0.0230 |  0.0235 |  0.0085 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 20 | L2_PWL    | h1615     |  409 |  0.0307 |     0.0106 |  0.0207 | -0.0373 |  0.0737 |           5 |          3 |    0.0111 |  0.0087 |  0.0262 |  0.0220 | True          | 1.00/0.00/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 21 | L2_ORL    | h12       | 1975 |  0.0015 |     0.0109 |  0.0053 | -0.0079 |  0.0179 |           6 |          3 |    0.0047 | -0.0139 |  0.0009 | -0.0027 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 22 | L2_ORL    | h24       | 1835 |  0.0077 |     0.0109 |  0.0104 | -0.0084 |  0.0298 |           6 |          4 |    0.0100 | -0.0095 |  0.0062 |  0.0006 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 23 | L2_ORL    | h1615     | 1975 |  0.0048 |     0.0109 |  0.0102 | -0.0194 |  0.0401 |           7 |          3 |    0.0078 |  0.0018 |  0.0019 | -0.0021 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 24 | L2_SWL60  | h12       |  932 |  0.0081 |     0.0108 |  0.0161 | -0.0016 |  0.0330 |           6 |          4 |    0.0122 |  0.0128 |  0.0101 |  0.0020 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 25 | L2_SWL60  | h24       |  819 |  0.0103 |     0.0108 |  0.0159 | -0.0097 |  0.0411 |           5 |          4 |    0.0112 |  0.0273 |  0.0116 |  0.0001 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 26 | L2_SWL60  | h1615     |  932 |  0.0447 |     0.0108 |  0.0282 | -0.0070 |  0.0631 |           6 |          4 |    0.0155 |  0.0361 |  0.0443 |  0.0341 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 27 | L2_L2H    | h12       | 2252 |  0.0068 |     0.0109 |  0.0083 | -0.0033 |  0.0200 |           4 |          3 |    0.0074 | -0.0020 |  0.0063 |  0.0032 | True          | 0.99/0.01/0.00 | REJECT                  |
| 28 | L2_L2H    | h24       | 1977 |  0.0154 |     0.0109 |  0.0163 | -0.0013 |  0.0326 |           8 |          4 |    0.0183 |  0.0157 |  0.0142 |  0.0088 | True          | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 29 | L2_L2H    | h1615     | 2252 |  0.0155 |     0.0109 |  0.0169 | -0.0081 |  0.0419 |           6 |          4 |    0.0215 |  0.0178 |  0.0147 |  0.0097 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 30 | L3_PWL    | h12       |  722 | -0.0118 |     0.0106 | -0.0041 | -0.0296 |  0.0217 |           5 |          2 |   -0.0088 |  0.0150 | -0.0164 | -0.0182 | False         | 0.99/0.01/0.00 | REJECT                  |
| 31 | L3_PWL    | h24       |  648 | -0.0113 |     0.0106 | -0.0058 | -0.0414 |  0.0287 |           5 |          1 |   -0.0199 |  0.0208 | -0.0177 | -0.0226 | False         | 0.98/0.02/0.00 | REJECT                  |
| 32 | L3_PWL    | h1615     |  722 | -0.0127 |     0.0106 | -0.0177 | -0.0705 |  0.0339 |           4 |          1 |   -0.0330 | -0.0028 | -0.0212 | -0.0249 | False         | 0.99/0.01/0.00 | REJECT                  |
| 33 | L3_SWL60  | h12       | 1593 | -0.0037 |     0.0109 |  0.0059 | -0.0099 |  0.0216 |           6 |          3 |    0.0024 |  0.0110 | -0.0009 | -0.0106 | False         | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 34 | L3_SWL60  | h24       | 1413 |  0.0098 |     0.0109 |  0.0136 | -0.0091 |  0.0361 |           6 |          3 |    0.0090 |  0.0141 |  0.0113 | -0.0029 | False         | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 35 | L3_SWL60  | h1615     | 1593 |  0.0247 |     0.0109 |  0.0081 | -0.0238 |  0.0398 |           5 |          3 |   -0.0023 | -0.0214 |  0.0191 |  0.0108 | False         | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 36 | L3_L2H    | h12       | 4485 | -0.0008 |     0.0107 |  0.0027 | -0.0068 |  0.0121 |           5 |          4 |    0.0041 |  0.0111 |  0.0001 | -0.0067 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 37 | L3_L2H    | h24       | 3980 |  0.0071 |     0.0107 |  0.0066 | -0.0083 |  0.0214 |           4 |          4 |    0.0068 |  0.0281 |  0.0048 | -0.0034 | True          | 0.98/0.02/0.00 | REJECT                  |
| 38 | L3_L2H    | h1615     | 4485 |  0.0044 |     0.0107 |  0.0000 | -0.0216 |  0.0226 |           3 |          3 |    0.0035 |  0.0218 | -0.0000 | -0.0063 | True          | 0.99/0.01/0.00 | REJECT                  |

## L4 / L5 response-curve coherence

|    | feature           | horizon   |   spearman |   top_minus_bottom |   ci_lo |   ci_hi |   years_same_sign |   inst_same_sign | COHERENT   |   best_bin |   best_bin_xN | bins                                       |
|---:|:------------------|:----------|-----------:|-------------------:|--------:|--------:|------------------:|-----------------:|:-----------|-----------:|--------------:|:-------------------------------------------|
|  0 | L4_APPROACH_SPEED | h12       |     0.3000 |             0.0014 | -0.0219 |  0.0245 |                 4 |                2 | False      |          4 |        0.0099 | [0.0085, -0.0003, 0.0077, 0.004, 0.0099]   |
|  1 | L4_APPROACH_SPEED | h24       |    -0.4000 |            -0.0037 | -0.0372 |  0.0287 |                 4 |                3 | False      |          0 |        0.0084 | [0.0084, 0.0014, -0.0014, -0.0045, 0.0047] |
|  2 | L4_APPROACH_SPEED | h1615     |     0.3000 |             0.0090 | -0.0367 |  0.0573 |                 3 |                3 | False      |          4 |        0.0176 | [0.0086, 0.0029, -0.0098, 0.0042, 0.0176]  |
|  3 | L5_TOUCH_COUNT    | h12       |    -0.3000 |            -0.0232 | -0.0504 |  0.0039 |                 5 |                4 | False      |          0 |        0.0263 | [0.0263, -0.0004, 0.0063, 0.007, 0.0031]   |
|  4 | L5_TOUCH_COUNT    | h24       |    -0.6000 |            -0.0351 | -0.0714 |  0.0008 |                 4 |                4 | False      |          0 |        0.0254 | [0.0254, -0.0005, 0.003, 0.0045, -0.0097]  |
|  5 | L5_TOUCH_COUNT    | h1615     |     0.0000 |            -0.0296 | -0.0786 |  0.0210 |                 5 |                3 | False      |          0 |        0.0345 | [0.0345, -0.0109, -0.0008, 0.0041, 0.005]  |

Per-instrument rows: out/index_alpha_master_v1/t104/.

Interpretation: breaks of recent 2h highs and opening-range highs followed by a retest are worse than simply being above the level; the only consistently positive structure is the failed breakdown of a support level that is reclaimed and then retested from above (L2), positive for every support type and horizon but individually unresolved (n 400-2,300) and below cost at 60m. Under the preregistered rule TEST105 is NOT_RUN_BY_RULE; the L2 structure is recorded as a weak clue for the synthesis only.

