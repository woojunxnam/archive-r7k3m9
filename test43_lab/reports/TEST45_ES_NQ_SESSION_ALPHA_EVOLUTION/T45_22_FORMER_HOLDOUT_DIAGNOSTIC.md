# T45_22 Former TEST43 holdout diagnostic (USED historical data)

2025-10-01..2026-05-27 is permanently USED data. It is not an untouched test, and no rule was tuned to it.

|     | candidate           |   overlay_avg |   champ_avg |   comb_avg |   champ_mdd |   comb_mdd |   comb_worst |   corr |
|----:|:--------------------|--------------:|------------:|-----------:|------------:|-----------:|-------------:|-------:|
|   9 | DET|CONTROL_A|ES    |         8.737 |      58.732 |     67.469 |    6193.430 |   7853.220 |    -1847.100 |  0.328 |
|  19 | DET|CONTROL_A|MNQ   |        33.892 |      58.732 |     92.623 |    6193.430 |   8878.290 |    -2303.100 |  0.392 |
|  29 | DET|CONTROL_A|BOTH  |        40.474 |      58.732 |     99.206 |    6193.430 |  11696.590 |    -2626.840 |  0.373 |
|  39 | DET|S1|ES           |         9.018 |      58.732 |     67.749 |    6193.430 |   8009.590 |    -1962.100 |  0.322 |
|  49 | DET|S1|MNQ          |        38.431 |      58.732 |     97.163 |    6193.430 |   8946.910 |    -2592.100 |  0.406 |
|  59 | DET|S1|BOTH         |        45.818 |      58.732 |    104.550 |    6193.430 |  11835.080 |    -3030.840 |  0.380 |
|  69 | DET|CONTROL_B|ES    |        10.448 |      58.732 |     69.180 |    6193.430 |   5647.730 |    -1625.850 |  0.084 |
|  79 | DET|CONTROL_B|MNQ   |        11.233 |      58.732 |     69.965 |    6193.430 |   6310.470 |    -1745.860 |  0.104 |
|  89 | DET|CONTROL_B|BOTH  |        21.681 |      58.732 |     80.412 |    6193.430 |   6160.730 |    -1787.970 |  0.101 |
|  99 | DET|S2|ES           |        12.107 |      58.732 |     70.839 |    6193.430 |   5373.990 |    -1625.850 |  0.042 |
| 109 | DET|S2|MNQ          |        11.233 |      58.732 |     69.965 |    6193.430 |   6310.470 |    -1745.860 |  0.104 |
| 119 | DET|S2|BOTH         |        23.340 |      58.732 |     82.072 |    6193.430 |   5886.990 |    -1745.860 |  0.087 |
| 129 | DET|S3|ES           |         7.252 |      58.732 |     65.984 |    6193.430 |   6204.450 |    -1532.100 |  0.236 |
| 139 | DET|S3|MNQ          |       -10.635 |      58.732 |     48.096 |    6193.430 |   9506.530 |    -1358.100 |  0.257 |
| 149 | DET|S3|BOTH         |        -3.383 |      58.732 |     55.349 |    6193.430 |   8921.240 |    -1746.970 |  0.270 |
| 159 | DET|S4|ES           |         9.440 |      58.732 |     68.171 |    6193.430 |   5619.650 |    -1532.100 |  0.023 |
| 169 | DET|S4|MNQ          |         1.973 |      58.732 |     60.705 |    6193.430 |   5956.370 |    -1358.100 | -0.032 |
| 179 | DET|S4|BOTH         |        11.413 |      58.732 |     70.144 |    6193.430 |   5349.500 |    -1366.840 |  0.003 |
| 189 | DET|S5b|ES          |        16.956 |      58.732 |     75.687 |    6193.430 |   9013.790 |    -2400.840 |  0.436 |
| 199 | DET|S5b|MNQ         |        46.695 |      58.732 |    105.427 |    6193.430 |  10740.910 |    -2897.350 |  0.499 |
| 209 | DET|S5b|BOTH        |        46.588 |      58.732 |    105.320 |    6193.430 |  12193.060 |    -3469.580 |  0.411 |
| 219 | DET|S6b|ES          |        20.919 |      58.732 |     79.651 |    6193.430 |   6218.340 |    -2048.350 |  0.341 |
| 229 | DET|S6b|MNQ         |        59.613 |      58.732 |    118.345 |    6193.430 |   5591.790 |    -2614.100 |  0.425 |
| 239 | DET|S6b|BOTH        |        79.077 |      58.732 |    137.809 |    6193.430 |   6542.090 |    -3139.090 |  0.401 |
| 249 | DET|S6c|ES          |        19.911 |      58.732 |     78.643 |    6193.430 |   6634.470 |    -2010.850 |  0.340 |
| 259 | DET|S6c|MNQ         |        47.758 |      58.732 |    106.490 |    6193.430 |   8517.290 |    -2516.600 |  0.429 |
| 269 | DET|S6c|BOTH        |        66.039 |      58.732 |    124.771 |    6193.430 |  10030.340 |    -3004.090 |  0.405 |
| 279 | GA|FINAL            |        41.960 |      58.732 |    100.691 |    6193.430 |   8594.470 |    -2862.600 |  0.582 |
| 289 | GP|GP_MORNING|FINAL |        33.644 |      58.732 |     92.375 |    6193.430 |   4183.840 |    -1523.360 |  0.048 |
| 299 | GP|GP_CLOSE|FINAL   |        20.428 |      58.732 |     79.160 |    6193.430 |   5690.870 |    -2581.100 |  0.545 |

|     | rule                                                           |   FH_overlay_avg |
|----:|:---------------------------------------------------------------|-----------------:|
|   0 | V6_STATE_CARRY|ES|14:30|champ>0                                |           10.127 |
|   1 | V6_STATE_CARRY|ES|14:30|champ>1                                |            0.644 |
|   2 | UNCOND_CARRY|ES|14:30                                          |            6.093 |
|   3 | V6_STATE_CARRY_BOOST2|ES|14:30|champ>0                         |           20.255 |
|   4 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|14:30   |           -4.034 |
|   5 | V6_STATE_CARRY|ES|15:00|champ>0                                |            9.491 |
|   6 | V6_STATE_CARRY|ES|15:00|champ>1                                |            0.516 |
|   7 | UNCOND_CARRY|ES|15:00                                          |            8.699 |
|   8 | V6_STATE_CARRY_BOOST2|ES|15:00|champ>0                         |           18.982 |
|   9 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|15:00   |           -0.792 |
|  10 | V6_STATE_CARRY|ES|15:15|champ>0                                |            4.446 |
|  11 | V6_STATE_CARRY|ES|15:15|champ>1                                |           -0.113 |
|  12 | UNCOND_CARRY|ES|15:15                                          |            3.533 |
|  13 | V6_STATE_CARRY_BOOST2|ES|15:15|champ>0                         |            8.891 |
|  14 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|15:15   |           -0.913 |
|  15 | V6_STATE_CARRY|ES|15:30|champ>0                                |            7.408 |
|  16 | V6_STATE_CARRY|ES|15:30|champ>1                                |            0.387 |
|  17 | UNCOND_CARRY|ES|15:30                                          |            9.775 |
|  18 | V6_STATE_CARRY_BOOST2|ES|15:30|champ>0                         |           14.816 |
|  19 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|15:30   |            2.367 |
|  20 | V6_STATE_CARRY|ES|15:45|champ>0                                |            7.938 |
|  21 | V6_STATE_CARRY|ES|15:45|champ>1                                |            0.114 |
|  22 | UNCOND_CARRY|ES|15:45                                          |            9.018 |
|  23 | V6_STATE_CARRY_BOOST2|ES|15:45|champ>0                         |           15.876 |
|  24 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|15:45   |            1.079 |
|  25 | V6_STATE_CARRY|ES|16:00|champ>0                                |            8.537 |
|  26 | V6_STATE_CARRY|ES|16:00|champ>1                                |            0.940 |
|  27 | UNCOND_CARRY|ES|16:00                                          |           10.419 |
|  28 | V6_STATE_CARRY_BOOST2|ES|16:00|champ>0                         |           17.073 |
|  29 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|16:00   |            1.882 |
|  30 | V6_STATE_CARRY|ES|16:14|champ>0                                |            6.817 |
|  31 | V6_STATE_CARRY|ES|16:14|champ>1                                |            0.591 |
|  32 | UNCOND_CARRY|ES|16:14                                          |            8.737 |
|  33 | V6_STATE_CARRY_BOOST2|ES|16:14|champ>0                         |           13.634 |
|  34 | V6_FLAT_CARRY (anti: carry only when Champion flat)|ES|16:14   |            1.920 |
|  35 | V6_STATE_CARRY|MNQ|14:30|champ>0                               |           18.658 |
|  36 | V6_STATE_CARRY|MNQ|14:30|champ>1                               |           -8.333 |
|  37 | UNCOND_CARRY|MNQ|14:30                                         |           36.534 |
|  38 | V6_STATE_CARRY_BOOST2|MNQ|14:30|champ>0                        |           26.558 |
|  39 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|14:30  |           17.876 |
|  40 | V6_STATE_CARRY|MNQ|15:00|champ>0                               |           22.456 |
|  41 | V6_STATE_CARRY|MNQ|15:00|champ>1                               |           -5.853 |
|  42 | UNCOND_CARRY|MNQ|15:00                                         |           42.486 |
|  43 | V6_STATE_CARRY_BOOST2|MNQ|15:00|champ>0                        |           30.408 |
|  44 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|15:00  |           20.029 |
|  45 | V6_STATE_CARRY|MNQ|15:15|champ>0                               |           12.568 |
|  46 | V6_STATE_CARRY|MNQ|15:15|champ>1                               |           -9.111 |
|  47 | UNCOND_CARRY|MNQ|15:15                                         |           32.204 |
|  48 | V6_STATE_CARRY_BOOST2|MNQ|15:15|champ>0                        |           16.875 |
|  49 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|15:15  |           19.636 |
|  50 | V6_STATE_CARRY|MNQ|15:30|champ>0                               |           16.565 |
|  51 | V6_STATE_CARRY|MNQ|15:30|champ>1                               |           -9.888 |
|  52 | UNCOND_CARRY|MNQ|15:30                                         |           42.980 |
|  53 | V6_STATE_CARRY_BOOST2|MNQ|15:30|champ>0                        |           22.320 |
|  54 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|15:30  |           26.414 |
|  55 | V6_STATE_CARRY|MNQ|15:45|champ>0                               |           14.668 |
|  56 | V6_STATE_CARRY|MNQ|15:45|champ>1                               |          -11.784 |
|  57 | UNCOND_CARRY|MNQ|15:45                                         |           38.431 |
|  58 | V6_STATE_CARRY_BOOST2|MNQ|15:45|champ>0                        |           22.932 |
|  59 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|15:45  |           23.763 |
|  60 | V6_STATE_CARRY|MNQ|16:00|champ>0                               |            9.645 |
|  61 | V6_STATE_CARRY|MNQ|16:00|champ>1                               |           -1.371 |
|  62 | UNCOND_CARRY|MNQ|16:00                                         |           36.001 |
|  63 | V6_STATE_CARRY_BOOST2|MNQ|16:00|champ>0                        |           15.162 |
|  64 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|16:00  |           26.356 |
|  65 | V6_STATE_CARRY|MNQ|16:14|champ>0                               |            9.815 |
|  66 | V6_STATE_CARRY|MNQ|16:14|champ>1                               |           -2.637 |
|  67 | UNCOND_CARRY|MNQ|16:14                                         |           33.892 |
|  68 | V6_STATE_CARRY_BOOST2|MNQ|16:14|champ>0                        |           13.717 |
|  69 | V6_FLAT_CARRY (anti: carry only when Champion flat)|MNQ|16:14  |           24.077 |
|  70 | V6_STATE_CARRY|BOTH|14:30|champ>0                              |           28.629 |
|  71 | V6_STATE_CARRY|BOTH|14:30|champ>1                              |           -7.689 |
|  72 | UNCOND_CARRY|BOTH|14:30                                        |           39.364 |
|  73 | V6_STATE_CARRY_BOOST2|BOTH|14:30|champ>0                       |           33.662 |
|  74 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|14:30 |           14.780 |
|  75 | V6_STATE_CARRY|BOTH|15:00|champ>0                              |           31.631 |
|  76 | V6_STATE_CARRY|BOTH|15:00|champ>1                              |           -5.338 |
|  77 | UNCOND_CARRY|BOTH|15:00                                        |           47.645 |
|  78 | V6_STATE_CARRY_BOOST2|BOTH|15:00|champ>0                       |           34.438 |
|  79 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|15:00 |           19.948 |
|  80 | V6_STATE_CARRY|BOTH|15:15|champ>0                              |           16.976 |
|  81 | V6_STATE_CARRY|BOTH|15:15|champ>1                              |           -9.224 |
|  82 | UNCOND_CARRY|BOTH|15:15                                        |           33.424 |
|  83 | V6_STATE_CARRY_BOOST2|BOTH|15:15|champ>0                       |           17.621 |
|  84 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|15:15 |           19.739 |
|  85 | V6_STATE_CARRY|BOTH|15:30|champ>0                              |           23.823 |
|  86 | V6_STATE_CARRY|BOTH|15:30|champ>1                              |           -9.501 |
|  87 | UNCOND_CARRY|BOTH|15:30                                        |           50.397 |
|  88 | V6_STATE_CARRY_BOOST2|BOTH|15:30|champ>0                       |           26.547 |
|  89 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|15:30 |           29.759 |
|  90 | V6_STATE_CARRY|BOTH|15:45|champ>0                              |           22.344 |
|  91 | V6_STATE_CARRY|BOTH|15:45|champ>1                              |          -11.670 |
|  92 | UNCOND_CARRY|BOTH|15:45                                        |           45.818 |
|  93 | V6_STATE_CARRY_BOOST2|BOTH|15:45|champ>0                       |           26.400 |
|  94 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|15:45 |           26.077 |
|  95 | V6_STATE_CARRY|BOTH|16:00|champ>0                              |           17.432 |
|  96 | V6_STATE_CARRY|BOTH|16:00|champ>1                              |           -0.431 |
|  97 | UNCOND_CARRY|BOTH|16:00                                        |           43.856 |
|  98 | V6_STATE_CARRY_BOOST2|BOTH|16:00|champ>0                       |           19.915 |
|  99 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|16:00 |           29.212 |
| 100 | V6_STATE_CARRY|BOTH|16:14|champ>0                              |           16.097 |
| 101 | V6_STATE_CARRY|BOTH|16:14|champ>1                              |           -2.046 |
| 102 | UNCOND_CARRY|BOTH|16:14                                        |           40.474 |
| 103 | V6_STATE_CARRY_BOOST2|BOTH|16:14|champ>0                       |           16.115 |
| 104 | V6_FLAT_CARRY (anti: carry only when Champion flat)|BOTH|16:14 |           27.362 |

