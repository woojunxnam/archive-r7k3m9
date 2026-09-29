# P4 event-conditioned HTF regime — results (prereg ebfe9b0)

**EVENT_CONDITIONED_HTF = SATURATED**: 0/12 curves coherent (max |Spearman| 0.9 only for C2 stage_slope with CI including 0 and 0/8 years). HTF strength/stage adds nothing beyond simple direction inside the trapped-seller, P2 or HTF1 populations. HTF strength features are NOT added to later ML (P3 already contained them as generic features; no change).

| population          | feature     |    n |   spearman |   top_minus_bottom |   ci_lo |   ci_hi |   years_same_sign |   inst_same_sign | COHERENT   | VALUE   | bins                                         |
|:--------------------|:------------|-----:|-----------:|-------------------:|--------:|--------:|------------------:|-----------------:|:-----------|:--------|:---------------------------------------------|
| C1_R1_TRAPPED_UNION | adx14       | 4219 |       -0.3 |            -0.0108 | -0.0675 |  0.05   |                 4 |                3 | False      | False   | [0.0217, 0.0055, -0.0283, -0.023, 0.0109]    |
| C1_R1_TRAPPED_UNION | stage_slope | 2485 |       -0.3 |            -0.0064 | -0.0958 |  0.0866 |                 0 |                3 | False      | False   | [-0.0128, 0.0286, 0.0034, 0.0174, -0.0193]   |
| C1_R1_TRAPPED_UNION | tsmom1      | 3552 |        0.3 |             0.0048 | -0.0666 |  0.0742 |                 4 |                2 | False      | False   | [-0.0035, -0.009, 0.0, -0.0384, 0.0013]      |
| C1_R1_TRAPPED_UNION | tsmom12     | 1570 |       -0.5 |            -0.0209 | -0.1178 |  0.0819 |                 0 |                3 | False      | False   | [0.0179, -0.0175, 0.012, -0.0177, -0.003]    |
| C2_P2_FAILED_FIRST  | adx14       |  664 |        0.4 |             0.0988 | -0.0036 |  0.2096 |                 6 |                3 | False      | False   | [-0.0446, -0.024, 0.0309, -0.0653, 0.0542]   |
| C2_P2_FAILED_FIRST  | stage_slope |  333 |       -0.9 |            -0.0581 | -0.2299 |  0.1183 |                 0 |                3 | False      | False   | [-0.0073, 0.0967, -0.0237, -0.0504, -0.0654] |
| C2_P2_FAILED_FIRST  | tsmom1      |  555 |       -0.1 |             0.0207 | -0.0951 |  0.1494 |                 4 |                3 | False      | False   | [-0.0431, 0.0079, 0.012, -0.0446, -0.0224]   |
| C2_P2_FAILED_FIRST  | tsmom12     |  206 |        0   |             0.0494 | -0.1245 |  0.2169 |                 0 |                1 | False      | False   | [0.0163, -0.013, -0.0566, -0.0814, 0.0657]   |
| C5_HTF1_30m         | adx14       | 3092 |       -0.3 |            -0.0002 | -0.0702 |  0.0696 |                 3 |                2 | False      | False   | [0.0186, -0.0044, -0.0354, -0.0302, 0.0183]  |
| C5_HTF1_30m         | stage_slope | 1854 |        0.7 |             0.0135 | -0.0987 |  0.1151 |                 2 |                3 | False      | False   | [-0.0058, -0.0475, -0.0106, 0.0068, 0.0077]  |
| C5_HTF1_30m         | tsmom1      | 2644 |        0.2 |             0.0347 | -0.0559 |  0.1299 |                 4 |                3 | False      | False   | [-0.0236, 0.001, 0.0209, -0.0618, 0.0111]    |
| C5_HTF1_30m         | tsmom12     | 1191 |       -0.1 |             0.0169 | -0.0981 |  0.1363 |                 1 |                2 | False      | False   | [-0.0204, 0.014, 0.0208, -0.0501, -0.0035]   |
