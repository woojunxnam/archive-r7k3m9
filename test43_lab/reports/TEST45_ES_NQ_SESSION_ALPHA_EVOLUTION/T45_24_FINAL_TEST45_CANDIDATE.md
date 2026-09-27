# T45_24 Final TEST45 candidate

Predeclared rule (written in `src/t45_07_eval.py` before GA/GP results were inspected):

1. OOS evidence: outer-block median > 0 and >= 4/5 blocks > 0.

2. Champion+overlay return/DD >= Champion.

3. Incremental >= $5/day and |corr| <= 0.5.

4. Combined MaxDD <= $10k and worst day >= -$2.5k.

5. Beats the simplest same-family control on outer median AND combined return/DD.

6. GA/GP: plateau + recurrence.

Candidates audited: 154; eligible: 0.

|     | candidate                                | rung                                    |   outer_median |   outer_pos |   comb_ret_dd |   champ_ret_dd |   incr_avg |   corr |   comb_mdd |   comb_worst |   ctrl_outer_median | rules_failed   |
|----:|:-----------------------------------------|:----------------------------------------|---------------:|------------:|--------------:|---------------:|-----------:|-------:|-----------:|-------------:|--------------------:|:---------------|
|  93 | DET|S2|ES                                | DET                                     |         -0.376 |           2 |         0.010 |          0.009 |      1.977 |  0.096 |   5373.990 |    -1722.990 |               0.809 | R1,R3,R5       |
| 101 | DET|S4|BOTH                              | DET                                     |          1.525 |           3 |         0.010 |          0.009 |      0.799 |  0.046 |   5349.500 |    -2184.980 |              -3.489 | R1,R3          |
|  71 | V6_STATE_CARRY_BOOST2|BOTH|15:30|champ>0 | DET (GA-recurrence-derived simple rule) |         27.899 |           4 |         0.010 |          0.009 |     41.504 |  0.549 |   9742.100 |    -3468.580 |               7.075 | R3,R4          |
|  99 | DET|S4|ES                                | DET                                     |         -0.044 |           2 |         0.010 |          0.009 |      1.144 |  0.037 |   5619.650 |    -1722.990 |               0.809 | R1,R3,R5       |
|  90 | DET|CONTROL_B|ES                         | DET                                     |          0.809 |           3 |         0.010 |          0.009 |      1.276 |  0.114 |   5647.730 |    -2235.480 |               0.809 | R1,R3,R5       |
|  75 | V6_STATE_CARRY_BOOST2|BOTH|15:45|champ>0 | DET (GA-recurrence-derived simple rule) |         27.017 |           4 |         0.010 |          0.009 |     43.000 |  0.562 |   9947.000 |    -3469.580 |               9.023 | R3,R4          |
|  59 | V6_STATE_CARRY_BOOST2|BOTH|14:30|champ>0 | DET (GA-recurrence-derived simple rule) |         41.712 |           4 |         0.010 |          0.009 |     47.594 |  0.611 |  10437.620 |    -5646.690 |              14.201 | R3,R4          |
|  43 | V6_STATE_CARRY_BOOST2|MNQ|15:30|champ>0  | DET (GA-recurrence-derived simple rule) |         31.678 |           4 |         0.010 |          0.009 |     38.884 |  0.539 |   9591.950 |    -2941.730 |               6.388 | R3,R4          |
|  77 | V6_STATE_CARRY|BOTH|16:00|champ>1        | DET (GA-recurrence-derived simple rule) |          1.987 |           5 |         0.010 |          0.009 |      5.941 |  0.360 |   6189.640 |    -2046.610 |              16.922 | R5             |
|  47 | V6_STATE_CARRY_BOOST2|MNQ|15:45|champ>0  | DET (GA-recurrence-derived simple rule) |         28.787 |           4 |         0.010 |          0.009 |     39.990 |  0.555 |   9739.990 |    -2941.730 |               7.474 | R3,R4          |
|  40 | V6_STATE_CARRY|MNQ|15:30|champ>0         | DET (GA-recurrence-derived simple rule) |         16.633 |           4 |         0.010 |          0.009 |     20.688 |  0.543 |   7764.510 |    -2581.100 |               6.388 | R3,R4          |
|  44 | V6_STATE_CARRY|MNQ|15:45|champ>0         | DET (GA-recurrence-derived simple rule) |         15.025 |           4 |         0.009 |          0.009 |     20.977 |  0.560 |   7856.030 |    -2592.100 |               7.474 | R3,R4          |
|  49 | V6_STATE_CARRY|MNQ|16:00|champ>1         | DET (GA-recurrence-derived simple rule) |          1.551 |           5 |         0.009 |          0.009 |      5.027 |  0.307 |   6193.430 |    -2046.610 |              12.246 | R5             |
|  81 | V6_STATE_CARRY|BOTH|16:14|champ>1        | DET (GA-recurrence-derived simple rule) |          1.603 |           5 |         0.009 |          0.009 |      5.147 |  0.345 |   6227.140 |    -2046.610 |              13.605 | R5             |
|  53 | V6_STATE_CARRY|MNQ|16:14|champ>1         | DET (GA-recurrence-derived simple rule) |          1.251 |           5 |         0.009 |          0.009 |      4.490 |  0.293 |   6193.430 |    -2046.610 |              10.217 | R3,R5          |
|  68 | V6_STATE_CARRY|BOTH|15:30|champ>0        | DET (GA-recurrence-derived simple rule) |         18.051 |           4 |         0.009 |          0.009 |     24.638 |  0.567 |   8352.520 |    -3024.840 |               7.075 | R3,R4          |
|  72 | V6_STATE_CARRY|BOTH|15:45|champ>0        | DET (GA-recurrence-derived simple rule) |         17.782 |           4 |         0.009 |          0.009 |     25.273 |  0.581 |   8501.530 |    -3030.840 |               9.023 | R3,R4          |
|  31 | V6_STATE_CARRY_BOOST2|MNQ|14:30|champ>0  | DET (GA-recurrence-derived simple rule) |         43.297 |           4 |         0.009 |          0.009 |     44.666 |  0.599 |  10592.270 |    -4216.710 |              11.973 | R3,R4          |
|  28 | V6_STATE_CARRY|MNQ|14:30|champ>0         | DET (GA-recurrence-derived simple rule) |         22.492 |           5 |         0.009 |          0.009 |     23.648 |  0.601 |   8382.750 |    -2935.970 |              11.973 | R3,R4          |
| 153 | GP_CLOSE_NESTED_STITCHED                 | GP                                      |          3.744 |           4 |         0.009 |          0.009 |      9.389 |  0.376 |   6817.400 |      nan     |               9.023 | R5,R6          |
|  36 | V6_STATE_CARRY|MNQ|15:15|champ>0         | DET (GA-recurrence-derived simple rule) |         15.145 |           4 |         0.009 |          0.009 |     20.345 |  0.559 |   8204.510 |    -2643.600 |               4.470 | R3,R4          |
|  39 | V6_STATE_CARRY_BOOST2|MNQ|15:15|champ>0  | DET (GA-recurrence-derived simple rule) |         28.728 |           4 |         0.009 |          0.009 |     38.691 |  0.562 |  10282.450 |    -3251.710 |               4.470 | R3,R4          |
|  20 | V6_STATE_CARRY|ES|16:00|champ>0          | DET (GA-recurrence-derived simple rule) |          3.622 |           3 |         0.009 |          0.009 |      4.030 |  0.466 |   6431.120 |    -2086.110 |               2.765 | R1,R3          |
| 100 | DET|S4|MNQ                               | DET                                     |          1.938 |           3 |         0.009 |          0.009 |     -0.346 |  0.047 |   5956.370 |    -1878.980 |              -2.421 | R1,R3          |
|  32 | V6_STATE_CARRY|MNQ|15:00|champ>0         | DET (GA-recurrence-derived simple rule) |         14.225 |           4 |         0.009 |          0.009 |     21.089 |  0.576 |   8347.010 |    -2781.100 |               2.497 | R3,R4          |
|  48 | V6_STATE_CARRY|MNQ|16:00|champ>0         | DET (GA-recurrence-derived simple rule) |         13.832 |           4 |         0.009 |          0.009 |     16.299 |  0.535 |   7838.810 |    -2463.100 |              12.246 | R3             |
|  12 | V6_STATE_CARRY|ES|15:30|champ>0          | DET (GA-recurrence-derived simple rule) |          1.417 |           3 |         0.009 |          0.009 |      4.334 |  0.490 |   6508.620 |    -2086.110 |               0.687 | R1,R3          |
|  96 | DET|S3|ES                                | DET                                     |          1.711 |           5 |         0.009 |          0.009 |      1.397 |  0.165 |   6204.450 |    -1722.990 |               0.809 | R3,R5          |
|  56 | V6_STATE_CARRY|BOTH|14:30|champ>0        | DET (GA-recurrence-derived simple rule) |         26.286 |           4 |         0.009 |          0.009 |     28.269 |  0.630 |   9225.510 |    -3650.960 |              14.201 | R3,R4          |
|  79 | V6_STATE_CARRY_BOOST2|BOTH|16:00|champ>0 | DET (GA-recurrence-derived simple rule) |         28.841 |           4 |         0.009 |          0.009 |     34.827 |  0.538 |   9979.040 |    -3290.080 |              16.922 | R3,R4          |
|  76 | V6_STATE_CARRY|BOTH|16:00|champ>0        | DET (GA-recurrence-derived simple rule) |         19.267 |           4 |         0.009 |          0.009 |     20.032 |  0.555 |   8330.060 |    -2856.840 |              16.922 | R3,R4          |
|   0 | V6_STATE_CARRY|ES|14:30|champ>0          | DET (GA-recurrence-derived simple rule) |          3.794 |           4 |         0.009 |          0.009 |      5.006 |  0.561 |   6652.370 |    -2370.220 |               2.228 | R3             |
|  21 | V6_STATE_CARRY|ES|16:00|champ>1          | DET (GA-recurrence-derived simple rule) |          0.436 |           4 |         0.009 |          0.009 |      0.865 |  0.219 |   6189.640 |    -1722.990 |               2.765 | R3,R5          |
|  51 | V6_STATE_CARRY_BOOST2|MNQ|16:00|champ>0  | DET (GA-recurrence-derived simple rule) |         26.859 |           4 |         0.009 |          0.009 |     31.871 |  0.530 |   9706.550 |    -2941.730 |              12.246 | R3,R4          |
|  35 | V6_STATE_CARRY_BOOST2|MNQ|15:00|champ>0  | DET (GA-recurrence-derived simple rule) |         27.046 |           4 |         0.009 |          0.009 |     39.611 |  0.581 |  10598.030 |    -3573.710 |               2.497 | R3,R4          |
|  67 | V6_STATE_CARRY_BOOST2|BOTH|15:15|champ>0 | DET (GA-recurrence-derived simple rule) |         23.891 |           4 |         0.009 |          0.009 |     41.138 |  0.574 |  10803.240 |    -4181.690 |               1.500 | R3,R4          |
|  25 | V6_STATE_CARRY|ES|16:14|champ>1          | DET (GA-recurrence-derived simple rule) |          0.287 |           4 |         0.009 |          0.009 |      0.600 |  0.212 |   6227.140 |    -1722.990 |               0.959 | R3,R5          |
|  16 | V6_STATE_CARRY|ES|15:45|champ>0          | DET (GA-recurrence-derived simple rule) |          2.756 |           3 |         0.009 |          0.009 |      4.690 |  0.496 |   6709.870 |    -2086.110 |               2.283 | R1,R3          |
|   1 | V6_STATE_CARRY|ES|14:30|champ>1          | DET (GA-recurrence-derived simple rule) |          1.111 |           5 |         0.009 |          0.009 |      1.285 |  0.251 |   6330.890 |    -1722.990 |               2.228 | R3,R5          |
|   5 | V6_STATE_CARRY|ES|15:00|champ>1          | DET (GA-recurrence-derived simple rule) |          1.132 |           4 |         0.009 |          0.009 |      1.143 |  0.241 |   6315.890 |    -1722.990 |              -0.553 | R3             |
|  17 | V6_STATE_CARRY|ES|15:45|champ>1          | DET (GA-recurrence-derived simple rule) |          0.524 |           4 |         0.009 |          0.009 |      0.781 |  0.222 |   6320.890 |    -1722.990 |               2.283 | R2,R3,R5       |
|  13 | V6_STATE_CARRY|ES|15:30|champ>1          | DET (GA-recurrence-derived simple rule) |          0.337 |           4 |         0.009 |          0.009 |      0.751 |  0.211 |   6345.890 |    -1722.990 |               0.687 | R2,R3,R5       |
|  52 | V6_STATE_CARRY|MNQ|16:14|champ>0         | DET (GA-recurrence-derived simple rule) |         12.303 |           4 |         0.009 |          0.009 |     15.580 |  0.531 |   8098.810 |    -2303.100 |              10.217 | R2,R3          |
|  15 | V6_STATE_CARRY_BOOST2|ES|15:30|champ>0   | DET (GA-recurrence-derived simple rule) |          2.835 |           3 |         0.009 |          0.009 |      8.668 |  0.490 |   7301.210 |    -2449.230 |               0.687 | R1,R2          |
|  63 | V6_STATE_CARRY_BOOST2|BOTH|15:00|champ>0 | DET (GA-recurrence-derived simple rule) |         21.345 |           4 |         0.009 |          0.009 |     39.781 |  0.595 |  10962.240 |    -4636.190 |               1.944 | R2,R3,R4       |
|  23 | V6_STATE_CARRY_BOOST2|ES|16:00|champ>0   | DET (GA-recurrence-derived simple rule) |          7.244 |           3 |         0.009 |          0.009 |      8.060 |  0.466 |   7273.640 |    -2449.230 |               2.765 | R1,R2          |
|   9 | V6_STATE_CARRY|ES|15:15|champ>1          | DET (GA-recurrence-derived simple rule) |          0.485 |           5 |         0.009 |          0.009 |      0.900 |  0.219 |   6440.890 |    -1722.990 |              -1.042 | R2,R3          |
|  64 | V6_STATE_CARRY|BOTH|15:15|champ>0        | DET (GA-recurrence-derived simple rule) |         15.920 |           4 |         0.008 |          0.009 |     24.064 |  0.589 |   9250.520 |    -3108.590 |               1.500 | R2,R3,R4       |
|   3 | V6_STATE_CARRY_BOOST2|ES|14:30|champ>0   | DET (GA-recurrence-derived simple rule) |          7.588 |           4 |         0.008 |          0.009 |     10.011 |  0.561 |   7588.710 |    -3085.210 |               2.228 | R2,R3,R4       |
|   8 | V6_STATE_CARRY|ES|15:15|champ>0          | DET (GA-recurrence-derived simple rule) |          0.775 |           3 |         0.008 |          0.009 |      4.121 |  0.515 |   6921.120 |    -2120.220 |              -1.042 | R1,R2,R3       |
|   4 | V6_STATE_CARRY|ES|15:00|champ>0          | DET (GA-recurrence-derived simple rule) |          0.711 |           3 |         0.008 |          0.009 |      3.216 |  0.543 |   6851.120 |    -2186.470 |              -0.553 | R1,R2,R3       |
|  91 | DET|CONTROL_B|MNQ                        | DET                                     |         -2.421 |           2 |         0.008 |          0.009 |     -0.202 |  0.125 |   6442.020 |    -2374.230 |              -2.421 | R1,R2,R3,R5    |
|  24 | V6_STATE_CARRY|ES|16:14|champ>0          | DET (GA-recurrence-derived simple rule) |          4.209 |           3 |         0.008 |          0.009 |      3.435 |  0.461 |   6881.120 |    -2086.110 |               0.959 | R1,R2,R3       |
|  55 | V6_STATE_CARRY_BOOST2|MNQ|16:14|champ>0  | DET (GA-recurrence-derived simple rule) |         23.829 |           4 |         0.008 |          0.009 |     29.770 |  0.525 |  10055.550 |    -2941.730 |              10.217 | R2,R3,R4       |
|  60 | V6_STATE_CARRY|BOTH|15:00|champ>0        | DET (GA-recurrence-derived simple rule) |         14.936 |           4 |         0.008 |          0.009 |     23.970 |  0.609 |   9388.020 |    -3297.340 |               1.944 | R2,R3,R4       |
|  94 | DET|S2|MNQ                               | DET                                     |         -2.421 |           2 |         0.008 |          0.009 |     -0.559 |  0.128 |   6442.020 |    -2374.230 |              -2.421 | R1,R2,R3,R5    |
|  19 | V6_STATE_CARRY_BOOST2|ES|15:45|champ>0   | DET (GA-recurrence-derived simple rule) |          5.513 |           3 |         0.008 |          0.009 |      9.381 |  0.496 |   7714.070 |    -2449.230 |               2.283 | R1,R2          |
| 105 | DET|S6b|ES                               | DET                                     |          3.340 |           3 |         0.008 |          0.009 |      5.751 |  0.341 |   7347.300 |    -2320.480 |               2.283 | R1,R2          |
| 106 | DET|S6b|MNQ                              | DET                                     |         12.554 |           4 |         0.008 |          0.009 |     16.397 |  0.392 |   8756.300 |    -2614.100 |               7.474 | R2,R4          |
|  80 | V6_STATE_CARRY|BOTH|16:14|champ>0        | DET (GA-recurrence-derived simple rule) |         16.512 |           4 |         0.008 |          0.009 |     18.794 |  0.551 |   9062.560 |    -2622.470 |              13.605 | R2,R3,R4       |

**FINAL_TEST45_CHALLENGER = NONE**

Near misses (one rule failed): V6_STATE_CARRY|BOTH|16:00|champ>1 (R5); V6_STATE_CARRY|MNQ|16:00|champ>1 (R5); V6_STATE_CARRY|BOTH|16:14|champ>1 (R5); V6_STATE_CARRY|MNQ|16:00|champ>0 (R3); V6_STATE_CARRY|ES|14:30|champ>0 (R3); V6_STATE_CARRY|ES|15:00|champ>1 (R3)

Interpretation: MNQ's overnight premium is concentrated on nights when the frozen Champion is long MNQ. Carry on Champion-flat nights loses about $9/day. This is real historical structure, independently rediscovered by GA and GP in every outer fold. It is, however, an intensification of the Champion's own overnight leg (corr 0.54-0.64 for champ>0). Its low-correlation variant (champ>1) adds only ~$5-6/day and fails R5 against unconditional carry. It is frozen as SHADOW for forward monitoring and cannot be promoted by the coming OOS.

**Causality fix recorded:** the first pass used the Champion position of the 16:12 bar as a feature at decision times 14:30-16:00. That is look-ahead. It was found before selection. Every stage (T45_03, 08-26) was re-run with the Champion position in effect at the decision minute. All numbers here are post-fix.

