# M06 Destination analysis

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


Invalidation: sweep extreme (sweep/reclaim) or range midpoint (breakouts). Window 4H bars (20..80). Descriptive only; no TP ladder.

## Sweep / reclaim: midpoint and opposite boundary before invalidation
| inst | hz | ev | n | P_mid_before_inval | P_opp_before_inval | med_bars_to_mid | med_bars_to_opp | mean_MAE_before_mid_atr | mean_MFE_after_mid_atr |
|---|---|---|---|---|---|---|---|---|---|
| ES | 120m | L_RECLAIM | 7152 | 0.438 | 0.266 | 5.0 | 13.0 | -0.028 | 0.224 |
| ES | 120m | L_RETEST_HOLD | 2071 | 0.535 | 0.32 | 4.0 | 14.0 | -0.031 | 0.209 |
| ES | 120m | U_RECLAIM | 7663 | 0.392 | 0.236 | 5.0 | 13.0 | -0.026 | 0.232 |
| ES | 120m | U_RETEST_HOLD | 2132 | 0.49 | 0.281 | 4.0 | 11.0 | -0.03 | 0.208 |
| ES | 15m | L_RECLAIM | 18439 | 0.614 | 0.435 | 1.0 | 2.0 | -0.012 | 0.086 |
| ES | 15m | L_RETEST_HOLD | 2676 | 0.705 | 0.51 | 1.0 | 2.0 | -0.013 | 0.08 |
| ES | 15m | U_RECLAIM | 18937 | 0.589 | 0.405 | 1.0 | 2.0 | -0.012 | 0.088 |
| ES | 15m | U_RETEST_HOLD | 2347 | 0.668 | 0.467 | 1.0 | 2.0 | -0.013 | 0.088 |
| ES | 30m | L_RECLAIM | 14129 | 0.551 | 0.362 | 2.0 | 5.0 | -0.016 | 0.123 |
| ES | 30m | L_RETEST_HOLD | 2842 | 0.635 | 0.409 | 1.0 | 5.0 | -0.017 | 0.113 |
| ES | 30m | U_RECLAIM | 14246 | 0.522 | 0.335 | 2.0 | 4.0 | -0.015 | 0.127 |
| ES | 30m | U_RETEST_HOLD | 2743 | 0.581 | 0.374 | 1.0 | 4.0 | -0.017 | 0.123 |
| ES | 60m | L_RECLAIM | 10149 | 0.494 | 0.309 | 3.0 | 9.0 | -0.022 | 0.18 |
| ES | 60m | L_RETEST_HOLD | 2635 | 0.561 | 0.354 | 2.0 | 9.0 | -0.024 | 0.176 |
| ES | 60m | U_RECLAIM | 10756 | 0.445 | 0.275 | 3.0 | 8.0 | -0.02 | 0.193 |
| ES | 60m | U_RETEST_HOLD | 2603 | 0.536 | 0.317 | 3.0 | 9.0 | -0.023 | 0.173 |
| ES | OR30 | L_RECLAIM | 931 | 0.405 | 0.193 | 4.0 | 12.0 | -0.037 | 0.246 |
| ES | OR30 | L_RETEST_HOLD | 205 | 0.473 | 0.195 | 3.0 | 12.0 | -0.047 | 0.214 |
| ES | OR30 | U_RECLAIM | 1066 | 0.357 | 0.175 | 4.0 | 9.0 | -0.032 | 0.273 |
| ES | OR30 | U_RETEST_HOLD | 208 | 0.476 | 0.197 | 3.0 | 10.0 | -0.043 | 0.255 |
| ES | PRTH | L_RECLAIM | 1161 | 0.115 | 0.022 | 28.0 | 44.5 | -0.051 | 0.455 |
| ES | PRTH | L_RETEST_HOLD | 251 | 0.207 | 0.032 | 27.5 | 37.5 | -0.091 | 0.407 |
| ES | PRTH | U_RECLAIM | 1526 | 0.1 | 0.023 | 25.5 | 29.0 | -0.035 | 0.497 |
| ES | PRTH | U_RETEST_HOLD | 252 | 0.258 | 0.063 | 26.0 | 54.0 | -0.075 | 0.499 |
| MNQ | 120m | L_RECLAIM | 6958 | 0.431 | 0.247 | 5.0 | 14.0 | -0.028 | 0.215 |
| MNQ | 120m | L_RETEST_HOLD | 2086 | 0.502 | 0.279 | 4.0 | 12.5 | -0.031 | 0.203 |
| MNQ | 120m | U_RECLAIM | 7551 | 0.38 | 0.221 | 4.0 | 13.0 | -0.025 | 0.231 |
| MNQ | 120m | U_RETEST_HOLD | 2132 | 0.458 | 0.261 | 5.0 | 14.0 | -0.031 | 0.229 |
| MNQ | 15m | L_RECLAIM | 18713 | 0.597 | 0.409 | 1.0 | 2.0 | -0.011 | 0.084 |
| MNQ | 15m | L_RETEST_HOLD | 2742 | 0.655 | 0.446 | 1.0 | 2.0 | -0.012 | 0.082 |
| MNQ | 15m | U_RECLAIM | 19306 | 0.567 | 0.382 | 1.0 | 2.0 | -0.011 | 0.087 |
| MNQ | 15m | U_RETEST_HOLD | 2511 | 0.632 | 0.426 | 1.0 | 3.0 | -0.011 | 0.082 |
| MNQ | 30m | L_RECLAIM | 14186 | 0.539 | 0.343 | 1.0 | 5.0 | -0.015 | 0.124 |
| MNQ | 30m | L_RETEST_HOLD | 2973 | 0.58 | 0.364 | 1.0 | 5.0 | -0.016 | 0.116 |
| MNQ | 30m | U_RECLAIM | 14379 | 0.498 | 0.311 | 2.0 | 4.0 | -0.014 | 0.124 |
| MNQ | 30m | U_RETEST_HOLD | 2912 | 0.567 | 0.335 | 2.0 | 5.0 | -0.016 | 0.121 |
| MNQ | 60m | L_RECLAIM | 10367 | 0.478 | 0.296 | 3.0 | 10.0 | -0.02 | 0.186 |
| MNQ | 60m | L_RETEST_HOLD | 2771 | 0.551 | 0.34 | 3.0 | 10.0 | -0.021 | 0.176 |
| MNQ | 60m | U_RECLAIM | 10678 | 0.431 | 0.263 | 3.0 | 8.0 | -0.019 | 0.19 |
| MNQ | 60m | U_RETEST_HOLD | 2708 | 0.513 | 0.3 | 3.0 | 9.0 | -0.021 | 0.18 |
| MNQ | OR30 | L_RECLAIM | 912 | 0.384 | 0.157 | 4.0 | 14.0 | -0.043 | 0.279 |
| MNQ | OR30 | L_RETEST_HOLD | 217 | 0.429 | 0.157 | 4.0 | 12.0 | -0.052 | 0.27 |
| MNQ | OR30 | U_RECLAIM | 1035 | 0.326 | 0.151 | 4.0 | 11.0 | -0.036 | 0.307 |
| MNQ | OR30 | U_RETEST_HOLD | 202 | 0.441 | 0.188 | 3.0 | 12.0 | -0.043 | 0.3 |
| MNQ | PRTH | L_RECLAIM | 1047 | 0.12 | 0.022 | 30.0 | 40.0 | -0.051 | 0.475 |
| MNQ | PRTH | L_RETEST_HOLD | 246 | 0.289 | 0.049 | 28.0 | 44.0 | -0.078 | 0.458 |
| MNQ | PRTH | U_RECLAIM | 1433 | 0.1 | 0.029 | 18.0 | 27.0 | -0.034 | 0.52 |
| MNQ | PRTH | U_RETEST_HOLD | 223 | 0.22 | 0.081 | 22.0 | 28.0 | -0.071 | 0.51 |

## Break / acceptance: range-width units vs ATR units; does width carry destination information beyond ATR?
`excess_vs_ATRonly_1.0R` = P(hit +1.0 range width) minus the probability predicted by an ATR-only excursion curve at the
same distance; `partial_spearman` = rank correlation of excursion with width after removing local (bar-ATR) volatility.
| inst | hz | ev | n | P_hit_0.5R | P_hit_1.0R | P_hit_2.0R | P_hit_0.5ATR | P_hit_1.0ATR | w_atr_median | excess_vs_ATRonly_1.0R | t_excess_1.0R | spearman_mfe_width | partial_spearman_mfe_width_given_localvol |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | 120m | DB_ACCEPT | 2331 | 0.605 | 0.406 | 0.197 | 0.098 | 0.021 | 0.149 | -0.005 | -0.471 | 0.266 | 0.081 |
| ES | 120m | UB_ACCEPT | 2833 | 0.586 | 0.373 | 0.157 | 0.053 | 0.003 | 0.151 | -0.004 | -0.445 | 0.265 | 0.074 |
| ES | 120m | UB_RETEST_HOLD | 1422 | 0.525 | 0.322 | 0.132 | 0.051 | 0.006 | 0.154 | -0.015 | -1.247 | 0.293 | 0.053 |
| ES | 15m | DB_ACCEPT | 13297 | 0.657 | 0.475 | 0.261 | 0.014 | 0.001 | 0.049 | 0.024 | 4.772 | 0.349 | 0.261 |
| ES | 15m | UB_ACCEPT | 14695 | 0.653 | 0.462 | 0.223 | 0.006 | 0.001 | 0.049 | 0.023 | 4.976 | 0.349 | 0.251 |
| ES | 15m | UB_RETEST_HOLD | 3418 | 0.614 | 0.423 | 0.193 | 0.005 | 0.001 | 0.053 | 0.017 | 1.896 | 0.353 | 0.197 |
| ES | 30m | DB_ACCEPT | 9018 | 0.612 | 0.433 | 0.237 | 0.033 | 0.004 | 0.07 | 0.011 | 1.825 | 0.331 | 0.23 |
| ES | 30m | UB_ACCEPT | 9811 | 0.626 | 0.43 | 0.208 | 0.02 | 0.001 | 0.072 | 0.008 | 1.465 | 0.335 | 0.209 |
| ES | 30m | UB_RETEST_HOLD | 3067 | 0.593 | 0.394 | 0.179 | 0.018 | 0.001 | 0.076 | 0.001 | 0.078 | 0.338 | 0.146 |
| ES | 60m | DB_ACCEPT | 4678 | 0.629 | 0.447 | 0.24 | 0.077 | 0.014 | 0.103 | 0.006 | 0.684 | 0.324 | 0.196 |
| ES | 60m | UB_ACCEPT | 5432 | 0.624 | 0.436 | 0.217 | 0.046 | 0.004 | 0.106 | 0.007 | 0.952 | 0.295 | 0.174 |
| ES | 60m | UB_RETEST_HOLD | 2316 | 0.56 | 0.373 | 0.189 | 0.044 | 0.001 | 0.11 | -0.012 | -1.224 | 0.287 | 0.094 |
| ES | OR30 | DB_ACCEPT | 659 | 0.522 | 0.275 | 0.1 | 0.106 | 0.011 | 0.273 | -0.026 | -1.516 | 0.202 |  |
| ES | OR30 | UB_ACCEPT | 770 | 0.452 | 0.179 | 0.043 | 0.039 | 0.004 | 0.263 | -0.037 | -2.712 | 0.265 |  |
| ES | OR30 | UB_RETEST_HOLD | 267 | 0.431 | 0.165 | 0.026 | 0.034 | 0.007 | 0.262 | -0.053 | -2.297 | 0.325 |  |
| ES | PRTH | DB_ACCEPT | 467 | 0.182 | 0.047 | 0.002 | 0.111 | 0.026 | 0.732 | -0.023 | -2.286 | 0.247 |  |
| ES | PRTH | UB_ACCEPT | 681 | 0.123 | 0.018 | 0.001 | 0.044 | 0.004 | 0.655 | -0.016 | -3.12 | 0.193 |  |
| ES | PRTH | UB_RETEST_HOLD | 293 | 0.15 | 0.034 | 0.0 | 0.051 | 0.003 | 0.627 | -0.005 | -0.507 | 0.194 |  |
| MNQ | 120m | DB_ACCEPT | 2452 | 0.588 | 0.392 | 0.193 | 0.087 | 0.012 | 0.142 | -0.006 | -0.605 | 0.25 | 0.112 |
| MNQ | 120m | UB_ACCEPT | 2880 | 0.584 | 0.361 | 0.152 | 0.055 | 0.003 | 0.153 | -0.018 | -2.013 | 0.245 | 0.069 |
| MNQ | 120m | UB_RETEST_HOLD | 1481 | 0.533 | 0.322 | 0.134 | 0.045 | 0.002 | 0.149 | -0.025 | -2.024 | 0.29 | 0.073 |
| MNQ | 15m | DB_ACCEPT | 13697 | 0.637 | 0.452 | 0.245 | 0.013 | 0.001 | 0.047 | 0.011 | 2.206 | 0.359 | 0.284 |
| MNQ | 15m | UB_ACCEPT | 15052 | 0.639 | 0.443 | 0.215 | 0.006 | 0.0 | 0.048 | 0.008 | 1.74 | 0.348 | 0.253 |
| MNQ | 15m | UB_RETEST_HOLD | 3851 | 0.586 | 0.4 | 0.191 | 0.005 | 0.0 | 0.049 | -0.001 | -0.097 | 0.362 | 0.179 |
| MNQ | 30m | DB_ACCEPT | 9221 | 0.598 | 0.412 | 0.223 | 0.032 | 0.003 | 0.069 | -0.007 | -1.189 | 0.359 | 0.253 |
| MNQ | 30m | UB_ACCEPT | 9950 | 0.621 | 0.425 | 0.207 | 0.018 | 0.002 | 0.071 | -0.002 | -0.297 | 0.334 | 0.217 |
| MNQ | 30m | UB_RETEST_HOLD | 3386 | 0.561 | 0.358 | 0.17 | 0.017 | 0.001 | 0.071 | -0.024 | -2.782 | 0.379 | 0.137 |
| MNQ | 60m | DB_ACCEPT | 4793 | 0.614 | 0.428 | 0.233 | 0.074 | 0.013 | 0.1 | -0.007 | -0.962 | 0.322 | 0.2 |
| MNQ | 60m | UB_ACCEPT | 5448 | 0.622 | 0.425 | 0.209 | 0.046 | 0.005 | 0.103 | -0.007 | -1.028 | 0.289 | 0.162 |
| MNQ | 60m | UB_RETEST_HOLD | 2432 | 0.558 | 0.375 | 0.176 | 0.044 | 0.005 | 0.103 | -0.016 | -1.532 | 0.326 | 0.067 |
| MNQ | OR30 | DB_ACCEPT | 651 | 0.479 | 0.253 | 0.057 | 0.115 | 0.014 | 0.323 | -0.009 | -0.533 | 0.151 |  |
| MNQ | OR30 | UB_ACCEPT | 769 | 0.427 | 0.153 | 0.025 | 0.046 | 0.003 | 0.321 | -0.021 | -1.644 | 0.177 |  |
| MNQ | OR30 | UB_RETEST_HOLD | 271 | 0.38 | 0.118 | 0.03 | 0.041 | 0.004 | 0.328 | -0.037 | -1.875 | 0.165 |  |
| MNQ | PRTH | DB_ACCEPT | 463 | 0.205 | 0.048 | 0.004 | 0.119 | 0.015 | 0.751 | -0.01 | -0.988 | 0.118 |  |
| MNQ | PRTH | UB_ACCEPT | 679 | 0.121 | 0.021 | 0.003 | 0.035 | 0.003 | 0.702 | -0.005 | -0.934 | 0.083 |  |
| MNQ | PRTH | UB_RETEST_HOLD | 277 | 0.13 | 0.022 | 0.0 | 0.054 | 0.0 | 0.701 | -0.008 | -0.906 | 0.148 |  |

**Reading.** Excursions scale with width (Spearman 0.2-0.35) but mostly because width proxies local volatility; measured
moves in range units are not hit more often than an ATR-only model predicts (excess ~0 or negative at 30m+; positive
only for ES 15m). Midpoint is reached ~40-70% before invalidation at intraday scales, the opposite boundary ~25-50%.
RANGE_WIDTH_PREDICTS_DESTINATION_ES = NO (only 15m, not across scales), _MNQ = NO.

