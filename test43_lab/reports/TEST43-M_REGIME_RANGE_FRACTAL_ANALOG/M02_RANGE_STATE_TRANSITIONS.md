# M02 Range state transitions and balance-state information

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


## Balance / compression vs matched control (60m forward return and forward 60m range, ATR units)
| inst | hz | state | n_bars | mean_d_ret60 | t_d_ret60 | mean_d_frange60 | t_d_frange60 | F1_t_d_frange60 | F2_t_d_frange60 | F3_t_d_frange60 |
|---|---|---|---|---|---|---|---|---|---|---|
| ES | 15m | QUALIFIED_BALANCE | 31092 | 0.001 | 0.639 | -0.006 | -2.102 | -1.272 | -0.821 | -1.589 |
| ES | 15m | COMPRESSION | 12340 | -0.0 | -0.106 | -0.006 | -1.926 | -1.106 | -0.985 | -1.267 |
| ES | 15m | SM_BREAKOUT_ATTEMPT | 11700 | 0.0 | 0.092 | -0.005 | -1.77 | -0.462 | -1.404 | -1.278 |
| ES | 15m | SM_ACCEPTED_EXPANSION | 55312 | 0.001 | 0.247 | 0.005 | 1.372 | 1.194 | -0.01 | 1.205 |
| ES | 30m | QUALIFIED_BALANCE | 32501 | 0.004 | 1.703 | -0.01 | -3.666 | -2.479 | -1.808 | -2.09 |
| ES | 30m | COMPRESSION | 14811 | 0.006 | 2.196 | -0.017 | -5.864 | -3.93 | -4.364 | -1.96 |
| ES | 30m | SM_BREAKOUT_ATTEMPT | 8097 | 0.003 | 1.043 | -0.011 | -3.929 | -2.484 | -1.335 | -3.225 |
| ES | 30m | SM_ACCEPTED_EXPANSION | 55663 | 0.002 | 0.586 | 0.002 | 0.629 | 1.233 | -0.85 | 0.695 |
| ES | 60m | QUALIFIED_BALANCE | 32688 | 0.003 | 1.037 | -0.014 | -5.028 | -3.619 | -1.877 | -3.501 |
| ES | 60m | COMPRESSION | 14842 | 0.002 | 0.673 | -0.027 | -8.229 | -5.658 | -4.129 | -4.578 |
| ES | 60m | SM_BREAKOUT_ATTEMPT | 13746 | 0.002 | 0.614 | -0.007 | -2.065 | -1.159 | -1.611 | -0.828 |
| ES | 60m | SM_ACCEPTED_EXPANSION | 55415 | -0.0 | -0.137 | 0.005 | 1.462 | 1.454 | -0.006 | 1.115 |
| ES | 120m | QUALIFIED_BALANCE | 32363 | 0.005 | 1.631 | -0.019 | -6.444 | -4.715 | -3.337 | -3.318 |
| ES | 120m | COMPRESSION | 13583 | 0.005 | 1.212 | -0.03 | -8.018 | -6.11 | -3.965 | -4.196 |
| ES | 120m | SM_BREAKOUT_ATTEMPT | 17149 | 0.007 | 1.6 | -0.002 | -0.411 | -0.972 | 0.115 | 0.132 |
| ES | 120m | SM_ACCEPTED_EXPANSION | 60175 | -0.002 | -0.58 | 0.003 | 0.755 | 0.981 | 0.4 | -0.173 |
| MNQ | 15m | QUALIFIED_BALANCE | 31193 | -0.0 | -0.05 | -0.001 | -0.54 | 0.033 | -0.47 | -0.566 |
| MNQ | 15m | COMPRESSION | 12702 | -0.001 | -0.495 | -0.003 | -0.889 | 0.192 | -1.192 | -0.652 |
| MNQ | 15m | SM_BREAKOUT_ATTEMPT | 11838 | 0.002 | 0.769 | -0.004 | -1.691 | -0.765 | -0.392 | -1.997 |
| MNQ | 15m | SM_ACCEPTED_EXPANSION | 55779 | -0.0 | -0.007 | 0.003 | 1.087 | 0.707 | -0.022 | 1.237 |
| MNQ | 30m | QUALIFIED_BALANCE | 32896 | 0.002 | 0.88 | -0.006 | -2.346 | -1.044 | -1.674 | -1.385 |
| MNQ | 30m | COMPRESSION | 15236 | 0.002 | 0.543 | -0.012 | -4.464 | -1.753 | -3.963 | -2.183 |
| MNQ | 30m | SM_BREAKOUT_ATTEMPT | 8081 | 0.005 | 2.05 | -0.007 | -2.645 | -1.224 | -0.923 | -2.703 |
| MNQ | 30m | SM_ACCEPTED_EXPANSION | 56419 | 0.003 | 1.012 | 0.002 | 0.593 | -0.067 | 0.674 | 0.41 |
| MNQ | 60m | QUALIFIED_BALANCE | 33287 | 0.002 | 0.962 | -0.007 | -2.671 | -1.121 | -1.613 | -2.003 |
| MNQ | 60m | COMPRESSION | 15148 | 0.004 | 1.343 | -0.02 | -6.61 | -3.6 | -3.996 | -3.912 |
| MNQ | 60m | SM_BREAKOUT_ATTEMPT | 13482 | -0.002 | -0.528 | -0.003 | -0.902 | 0.175 | -1.104 | -0.959 |
| MNQ | 60m | SM_ACCEPTED_EXPANSION | 54982 | -0.001 | -0.325 | 0.004 | 1.093 | 1.02 | 0.51 | 0.29 |
| MNQ | 120m | QUALIFIED_BALANCE | 32714 | 0.003 | 1.03 | -0.012 | -4.265 | -1.845 | -3.453 | -2.134 |
| MNQ | 120m | COMPRESSION | 13617 | 0.005 | 1.245 | -0.024 | -6.543 | -3.531 | -4.555 | -3.224 |
| MNQ | 120m | SM_BREAKOUT_ATTEMPT | 16744 | -0.002 | -0.502 | 0.001 | 0.316 | -0.165 | -0.04 | 0.895 |
| MNQ | 120m | SM_ACCEPTED_EXPANSION | 58697 | -0.004 | -1.164 | 0.001 | 0.341 | 1.035 | -0.384 | -0.018 |

**Reading.** Qualified balance / compression predicts a *smaller* next-60m range than the matched control (t -4 to -8
at 30-120m, all folds negative, both instruments): balance persists; it does not forecast expansion. It carries **no
directional** information (|t| < 2.2). RANGE_BALANCE_STATE_HAS_INFORMATION = YES (volatility / range only, not direction).
Controls match the daily vol regime, not intraday local volatility, so part of this is ordinary intraday vol clustering.

## Event transition probabilities (structural; nearly identical for ES and MNQ)
| inst | from | to | 120m | 15m | 30m | 60m | PRTH |
|---|---|---|---|---|---|---|---|
| ES | DB_ACCEPT | DB_REENTRY | 0.655 | 0.614 | 0.706 | 0.679 | 0.633 |
| ES | DB_ACCEPT | DB_RETEST_HOLD | 0.518 | 0.235 | 0.306 | 0.42 | 0.497 |
| ES | DB_BREAK | DB_ACCEPT | 0.345 | 0.693 | 0.69 | 0.491 | 0.389 |
| ES | DB_BREAK | DB_FAILED_ACCEPT | 0.655 | 0.307 | 0.31 | 0.509 | 0.611 |
| ES | DB_RETEST_HOLD | DB_RESUMED | 0.2 | 0.23 | 0.249 | 0.216 | 0.275 |
| ES | L_RECLAIM | L_RETEST | 0.362 | 0.244 | 0.302 | 0.347 | 0.22 |
| ES | L_RETEST | L_RETEST_HOLD | 0.8 | 0.596 | 0.665 | 0.75 | 0.984 |
| ES | L_RETEST_HOLD | L_RESUMPTION | 0.366 | 0.318 | 0.349 | 0.344 | 0.502 |
| ES | L_SWEEP | L_FAILED_RECLAIM | 0.167 | 0.354 | 0.259 | 0.212 | 0.211 |
| ES | L_SWEEP | L_RECLAIM | 0.833 | 0.646 | 0.741 | 0.788 | 0.789 |
| ES | UB_ACCEPT | UB_REENTRY | 0.625 | 0.588 | 0.668 | 0.657 | 0.565 |
| ES | UB_ACCEPT | UB_RETEST_HOLD | 0.502 | 0.233 | 0.313 | 0.426 | 0.43 |
| ES | UB_BREAK | UB_ACCEPT | 0.375 | 0.709 | 0.707 | 0.512 | 0.41 |
| ES | UB_BREAK | UB_FAILED_ACCEPT | 0.625 | 0.291 | 0.293 | 0.488 | 0.59 |
| ES | UB_RETEST_HOLD | UB_RESUMED | 0.25 | 0.258 | 0.271 | 0.259 | 0.471 |
| ES | U_RECLAIM | U_RETEST | 0.333 | 0.211 | 0.284 | 0.315 | 0.169 |
| ES | U_RETEST | U_RETEST_HOLD | 0.835 | 0.587 | 0.678 | 0.767 | 0.977 |
| ES | U_RETEST_HOLD | U_RESUMPTION | 0.319 | 0.271 | 0.289 | 0.305 | 0.421 |
| ES | U_SWEEP | U_RECLAIM | 0.811 | 0.626 | 0.716 | 0.763 | 0.763 |
| MNQ | DB_ACCEPT | DB_REENTRY | 0.666 | 0.609 | 0.705 | 0.676 | 0.613 |
| MNQ | DB_ACCEPT | DB_RETEST_HOLD | 0.497 | 0.258 | 0.333 | 0.443 | 0.471 |
| MNQ | DB_BREAK | DB_ACCEPT | 0.373 | 0.701 | 0.704 | 0.494 | 0.426 |
| MNQ | DB_BREAK | DB_FAILED_ACCEPT | 0.627 | 0.299 | 0.296 | 0.506 | 0.574 |
| MNQ | DB_RETEST_HOLD | DB_RESUMED | 0.204 | 0.256 | 0.248 | 0.229 | 0.329 |
| MNQ | L_RECLAIM | L_RETEST | 0.378 | 0.25 | 0.31 | 0.356 | 0.241 |
| MNQ | L_RETEST | L_RETEST_HOLD | 0.794 | 0.586 | 0.676 | 0.751 | 0.98 |
| MNQ | L_RETEST_HOLD | L_RESUMPTION | 0.362 | 0.316 | 0.344 | 0.36 | 0.548 |
| MNQ | L_SWEEP | L_FAILED_RECLAIM | 0.173 | 0.359 | 0.263 | 0.213 | 0.229 |
| MNQ | L_SWEEP | L_RECLAIM | 0.827 | 0.641 | 0.737 | 0.787 | 0.771 |
| MNQ | UB_ACCEPT | UB_REENTRY | 0.609 | 0.581 | 0.656 | 0.625 | 0.554 |
| MNQ | UB_ACCEPT | UB_RETEST_HOLD | 0.514 | 0.256 | 0.34 | 0.446 | 0.407 |
| MNQ | UB_BREAK | UB_ACCEPT | 0.388 | 0.72 | 0.711 | 0.52 | 0.43 |
| MNQ | UB_BREAK | UB_FAILED_ACCEPT | 0.612 | 0.28 | 0.289 | 0.48 | 0.57 |
| MNQ | UB_RETEST_HOLD | UB_RESUMED | 0.271 | 0.281 | 0.278 | 0.288 | 0.422 |
| MNQ | U_RECLAIM | U_RETEST | 0.345 | 0.223 | 0.3 | 0.332 | 0.158 |
| MNQ | U_RETEST | U_RETEST_HOLD | 0.818 | 0.584 | 0.676 | 0.763 | 0.982 |
| MNQ | U_RETEST_HOLD | U_RESUMPTION | 0.335 | 0.294 | 0.292 | 0.321 | 0.462 |
| MNQ | U_SWEEP | U_RECLAIM | 0.802 | 0.624 | 0.707 | 0.757 | 0.75 |
Full per-bar state transition matrix: `M02_state_transition_matrix__*.csv`.

