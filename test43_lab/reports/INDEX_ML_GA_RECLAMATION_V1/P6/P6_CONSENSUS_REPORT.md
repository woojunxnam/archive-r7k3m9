# P6 consensus + matched-beta + overfit diagnostics — results (prereg 2d5d88d)

CONSENSUS_CANDIDATES: C1 (A take-all), C2 (A), C4 (C GA), C5 (A), C6 (A), C7 (B ML nested).  NO_TIER_B_ARM: C3, C8.

Key facts: (1) ML beats take-all only for C7; for C1/C2/C5/C6 the deterministic take-all is best, so the consensus arm is the frozen population itself. (2) Matched-beta excess ~= raw dollars: a random intraday long entry at the same instrument / year / vol / time-of-day earns ~0 net of cost, so the raw dollars are not intraday beta drift; BUT the plain ORB reference earns MORE (26.74 $/day, excess 23.60) than any candidate -> the candidates largely share a generic 'bullish intraday trigger -> hold to 16:15' effect (ORB family closed in TEST49 / TEST106). (3) Overfit diagnostics are weak: DSR 0.40-0.85 (none >= 0.95), PBO 0.13-0.84, White Reality Check p 0.03 (C1), 0.03 (C2), >= 0.10 for others.

| family              | choice      | label               |
|:--------------------|:------------|:--------------------|
| C1_R1_TRAPPED_UNION | A_TAKE_ALL  | CONSENSUS_CANDIDATE |
| C2_P2_FAILED_FIRST  | A_TAKE_ALL  | CONSENSUS_CANDIDATE |
| C3_P1_H2            | nan         | NO_TIER_B_ARM       |
| C4_L2_FAMILY        | C_GA        | CONSENSUS_CANDIDATE |
| C5_HTF1_30m         | A_TAKE_ALL  | CONSENSUS_CANDIDATE |
| C6_AV_OR30          | A_TAKE_ALL  | CONSENSUS_CANDIDATE |
| C7_L1_SWH60         | B_ML_NESTED | CONSENSUS_CANDIDATE |
| C8_CHOCH_15m        | nan         | NO_TIER_B_ARM       |
| REF_A2_ACD          | A_TAKE_ALL  | CONSENSUS_CANDIDATE |
| REF_ORB15           | A_TAKE_ALL  | CONSENSUS_CANDIDATE |

| family              | arm         |   avg_day |   slip4_avg_day |   trades |   folds_pos |   worst_fold |   remove_top3 |    y2022 |   max_dd |   corr_main | tier_b   |   mb_excess_avg_day |   mb_excess_2022 |   mb_excess_folds_pos |
|:--------------------|:------------|----------:|----------------:|---------:|------------:|-------------:|--------------:|---------:|---------:|------------:|:---------|--------------------:|-----------------:|----------------------:|
| C1_R1_TRAPPED_UNION | A_TAKE_ALL  |     20.44 |            9.69 |     3527 |           4 |        -8.23 |      16962.7  | -2065.13 |  6895.47 |        0.48 | True     |               19.91 |          1859.27 |                     5 |
| C1_R1_TRAPPED_UNION | B_ML_NESTED |     16.8  |            7.92 |     2904 |           4 |        -8.23 |      12020.7  | -2065.13 |  6895.47 |        0.45 | True     |               17.32 |          1859.27 |                     4 |
| C1_R1_TRAPPED_UNION | C_GA        |      7.27 |            3.64 |     1200 |           5 |         2.08 |       5979.94 |  1272.19 |  4971.64 |        0.36 | True     |                9.47 |          2708.24 |                     4 |
| C1_R1_TRAPPED_UNION | D_ML_IN_GA  |      5.9  |            4    |      650 |           3 |        -7.06 |       4455.94 |  2834.18 |  5246.27 |        0.29 | True     |                7.1  |          4170.9  |                     3 |
| C2_P2_FAILED_FIRST  | A_TAKE_ALL  |      6.79 |            5.02 |      590 |           4 |        -3.27 |       5460.33 |  5116.57 |  3110.41 |        0.27 | True     |                7.1  |          5408.18 |                     4 |
| C2_P2_FAILED_FIRST  | B_ML_NESTED |      2.25 |            1.12 |      380 |           4 |        -8.51 |       -515.51 |  2288.26 |  3283.69 |        0.25 | False    |                2.08 |          2366.89 |                     4 |
| C3_P1_H2            | A_TAKE_ALL  |      3.03 |           -1.73 |     1576 |           4 |       -13.57 |      -1143.32 |  3517.12 |  7084.84 |        0.35 | False    |                3.23 |          4601.82 |                     3 |
| C3_P1_H2            | B_ML_NESTED |      1.83 |           -0.51 |      784 |           3 |       -16.28 |      -1735.75 |  3275.11 |  4704.74 |        0.25 | False    |                1.73 |          3860.37 |                     3 |
| C4_L2_FAMILY        | A_TAKE_ALL  |     12.45 |           -1.07 |     4446 |           4 |       -18.53 |       2037.75 | -4651.94 | 10762.7  |        0.41 | False    |               12.63 |          -340.87 |                     3 |
| C4_L2_FAMILY        | B_ML_NESTED |      7.36 |           -2.84 |     3357 |           4 |       -26.74 |      -4875.64 | -6711.7  | 13381.1  |        0.37 | False    |                7.3  |         -4357.79 |                     3 |
| C4_L2_FAMILY        | C_GA        |     14.54 |            9.04 |     1806 |           3 |        -7.03 |       5605.62 | -1765.52 | 10831.7  |        0.3  | True     |               14.18 |          2140.66 |                     4 |
| C4_L2_FAMILY        | D_ML_IN_GA  |      3.44 |            0.64 |      928 |           3 |        -8.57 |      -5435.42 | -2151.24 |  9375.24 |        0.16 | False    |                4.25 |          1048.2  |                     4 |
| C5_HTF1_30m         | A_TAKE_ALL  |     12.73 |            4.83 |     2625 |           3 |        -3.96 |       9802.86 |  -993.31 |  8668.93 |        0.47 | True     |               11.93 |          1460.76 |                     5 |
| C5_HTF1_30m         | B_ML_NESTED |      4.09 |           -1.29 |     1804 |           2 |        -5.6  |      -1352.13 |  -993.31 |  7550.25 |        0.41 | False    |                5.26 |          1460.76 |                     4 |
| C6_AV_OR30          | A_TAKE_ALL  |     14.75 |            4.59 |     3277 |           5 |         0.28 |       9956.9  |    69.96 |  7909.95 |        0.52 | True     |               12.12 |          3049.24 |                     5 |
| C6_AV_OR30          | B_ML_NESTED |      2.76 |           -3.61 |     2058 |           4 |        -9.29 |      -2065.29 |    69.96 | 11539.2  |        0.44 | False    |                2.02 |          3049.24 |                     4 |
| C7_L1_SWH60         | A_TAKE_ALL  |      4.31 |            1.14 |     1043 |           4 |       -15.99 |        645.33 | -4012.42 |  5855.03 |        0.43 | False    |                3.58 |         -3225.39 |                     3 |
| C7_L1_SWH60         | B_ML_NESTED |      6.36 |            4.31 |      678 |           3 |        -2.58 |       3455.42 |  -647.23 |  3630.25 |        0.38 | True     |                5.32 |          -478.5  |                     3 |
| C7_L1_SWH60         | C_GA        |     -1.77 |           -3.09 |      404 |           3 |       -17.87 |      -4249.54 | -4484.84 |  5636.19 |        0.18 | False    |               -1.24 |         -3907.33 |                     2 |
| C7_L1_SWH60         | D_ML_IN_GA  |      0.04 |           -0.47 |      161 |           3 |        -5.55 |      -1308.69 | -1393.3  |  2096.96 |        0.14 | False    |                0.26 |         -1197.13 |                     3 |
| C8_CHOCH_15m        | A_TAKE_ALL  |     12.94 |            4.99 |     2669 |           4 |       -27.13 |       8717.57 |  2666.16 |  8192.34 |        0.48 | False    |               12.07 |          4547.6  |                     4 |
| C8_CHOCH_15m        | B_ML_NESTED |      7.93 |            3.85 |     1393 |           4 |       -24.03 |       5669.57 |  3638.11 |  7445.05 |        0.39 | False    |                8.45 |          5108.27 |                     4 |
| REF_A2_ACD          | A_TAKE_ALL  |     16.73 |            7.8  |     2893 |           5 |         3.37 |      10866.1  |   846.4  |  8715.21 |        0.51 | True     |               14.42 |          3968.68 |                     5 |
| REF_ORB15           | A_TAKE_ALL  |     26.74 |           15.43 |     3667 |           4 |       -10.61 |      24023.8  | -2663.94 | 11374.3  |        0.57 | True     |               23.6  |          2291.08 |                     5 |

## Overfit diagnostics
| family              |   trials | chosen_arm   |   daily_sharpe |    sr0 |    dsr |    pbo |   reality_check_p | status   | label               |
|:--------------------|---------:|:-------------|---------------:|-------:|-------:|-------:|------------------:|:---------|:--------------------|
| C1_R1_TRAPPED_UNION |     1017 | A_TAKE_ALL   |         0.0442 | 0.045  | 0.4878 | 0.7839 |            0.035  | COMPUTED | CONSENSUS_CANDIDATE |
| C2_P2_FAILED_FIRST  |        9 | A_TAKE_ALL   |         0.0533 | 0.0252 | 0.8522 | 0.5709 |            0.028  | COMPUTED | CONSENSUS_CANDIDATE |
| C3_P1_H2            |        9 | nan          |         0.0129 | 0.0176 | 0.4313 | 0.8396 |            0.3595 | COMPUTED | NO_TIER_B_ARM       |
| C4_L2_FAMILY        |      873 | C_GA         |         0.0334 | 0.0402 | 0.3973 | 0.1277 |            0.26   | COMPUTED | CONSENSUS_CANDIDATE |
| C5_HTF1_30m         |        9 | A_TAKE_ALL   |         0.0326 | 0.0158 | 0.7317 | 0.7721 |            0.1325 | COMPUTED | CONSENSUS_CANDIDATE |
| C6_AV_OR30          |        9 | A_TAKE_ALL   |         0.0314 | 0.0206 | 0.6531 | 0.3838 |            0.101  | COMPUTED | CONSENSUS_CANDIDATE |
| C7_L1_SWH60         |      729 | B_ML_NESTED  |         0.0381 | 0.0374 | 0.5112 | 0.6672 |            0.1155 | COMPUTED | CONSENSUS_CANDIDATE |
| C8_CHOCH_15m        |        9 | nan          |         0.0348 | 0.0158 | 0.76   | 0.4538 |            0.1025 | COMPUTED | NO_TIER_B_ARM       |
