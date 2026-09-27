# M03 Nested range alignment

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


Positions recorded simultaneously: trailing 15/30/60/120m, RTH-so-far, prior RTH, 5D. Classes (descriptive, not tuned):
MULTI_LOW (>=4 of 7 positions <= 0.25, none >= 0.75), MULTI_HIGH (mirror), MID_CLUSTER (>=4 in 0.35-0.65), MIXED.

## Descriptive map (all RTH bars)
| inst | align | n | mean_d_ret60 | t_d_ret60 | pos60ctl_mean_d_ret60 | pos60ctl_t_d_ret60 | F1_t_d_ret60 | F2_t_d_ret60 | F3_t_d_ret60 |
|---|---|---|---|---|---|---|---|---|---|
| ES | MULTI_LOW | 27085 | -0.005 | -1.029 | 0.001 | 0.196 | -0.358 | 0.069 | 0.465 |
| ES | MULTI_HIGH | 50246 | 0.005 | 1.972 | 0.002 | 0.744 | 0.155 | 1.077 | 0.087 |
| ES | MID_CLUSTER | 21544 | 0.004 | 1.247 | 0.003 | 1.106 | 1.144 | 0.283 | 0.544 |
| ES | MIXED | 87595 | -0.002 | -0.893 | -0.002 | -0.944 | -0.277 | -0.741 | -0.595 |
| MNQ | MULTI_LOW | 27829 | -0.006 | -1.366 | -0.001 | -0.215 | -0.296 | -0.184 | 0.04 |
| MNQ | MULTI_HIGH | 49841 | 0.005 | 2.18 | 0.002 | 1.039 | 0.306 | 1.042 | 0.469 |
| MNQ | MID_CLUSTER | 21063 | -0.0 | -0.115 | -0.001 | -0.33 | -0.443 | -0.054 | -0.103 |
| MNQ | MIXED | 87589 | -0.001 | -0.445 | -0.001 | -0.375 | 0.125 | -0.419 | -0.326 |

## Events whose effect differs by alignment (|t_diff| >= 2 of 453 event x alignment rows)
| inst | hz | ev | align | n | mean_d_ret60 | diff_vs_other_align | t_diff |
|---|---|---|---|---|---|---|---|
| ES | 120m | UB_ACCEPT | MIXED | 1123 | -0.009 | -0.017 | -3.523 |
| ES | 120m | UB_ACCEPT | MULTI_HIGH | 1458 | 0.007 | 0.012 | 2.391 |
| ES | 15m | L_RECLAIM | MIXED | 9998 | 0.001 | -0.005 | -2.017 |
| ES | 15m | L_RECLAIM | MULTI_LOW | 1704 | 0.014 | 0.012 | 2.469 |
| ES | 15m | UB_RETEST_HOLD | MID_CLUSTER | 1070 | 0.007 | 0.011 | 2.128 |
| ES | 5D | U_RETEST_HOLD | MIXED | 45 | 0.005 | 0.121 | 2.077 |
| ES | 60m | U_RETEST_HOLD | MID_CLUSTER | 810 | -0.008 | -0.012 | -2.07 |
| ES | OR15 | U_RECLAIM | MIXED | 371 | -0.032 | -0.037 | -2.287 |
| ES | OR30 | L_RECLAIM | MID_CLUSTER | 163 | 0.031 | 0.036 | 2.073 |
| ES | OR60 | UB_ACCEPT | MIXED | 129 | -0.04 | -0.052 | -2.63 |
| ES | OR60 | UB_ACCEPT | MULTI_HIGH | 617 | 0.011 | 0.043 | 2.225 |
| ES | PRTH | UB_ACCEPT | MIXED | 210 | -0.018 | -0.023 | -2.096 |
| ES | PRTH | UB_ACCEPT | MULTI_HIGH | 439 | 0.006 | 0.025 | 2.216 |
| MNQ | 120m | UB_ACCEPT | MIXED | 1203 | -0.009 | -0.018 | -3.265 |
| MNQ | 120m | UB_ACCEPT | MULTI_HIGH | 1432 | 0.009 | 0.015 | 2.676 |
| MNQ | 30m | UB_RETEST_HOLD | MIXED | 1913 | 0.003 | 0.013 | 2.572 |
| MNQ | 30m | U_RETEST_HOLD | MIXED | 1309 | -0.005 | -0.014 | -2.812 |
| MNQ | 30m | U_RETEST_HOLD | MULTI_HIGH | 601 | 0.014 | 0.014 | 2.425 |
| MNQ | 60m | U_RETEST_HOLD | MULTI_LOW | 36 | -0.067 | -0.066 | -2.06 |
| MNQ | OR30 | U_RECLAIM | MID_CLUSTER | 88 | 0.051 | 0.057 | 2.297 |
| MNQ | OR60 | UB_ACCEPT | MIXED | 108 | -0.054 | -0.066 | -3.137 |
| MNQ | OR60 | UB_ACCEPT | MULTI_HIGH | 634 | 0.011 | 0.058 | 2.798 |

Only 8 of ~450 event x alignment cells reach |t| >= 2 (chance ~ 5%). The one recurring pattern (UB_ACCEPT with
MULTI_HIGH at 120m / OR60, both instruments) was frozen as candidate C3 and **failed VAL** (M16).
NESTED_RANGE_ALIGNMENT_ADDS_VALUE_ES = NO, _MNQ = NO.

