# M11 Timeframe / fractal transfer

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


## Transition ordering across scales (Spearman of transition probabilities vs 3m/60m)
| inst | res | hz | spearman_vs_3m_60m |
|---|---|---|---|
| ES | 3m | 120m | 0.942 |
| ES | 3m | 15m | 0.693 |
| ES | 3m | 30m | 0.893 |
| ES | 3m | 60m | 1.0 |
| ES | 5m | 120m | 0.996 |
| ES | 5m | 15m | 0.691 |
| ES | 5m | 30m | 0.749 |
| ES | 5m | 60m | 0.895 |
| MNQ | 3m | 120m | 0.946 |
| MNQ | 3m | 15m | 0.688 |
| MNQ | 3m | 30m | 0.849 |
| MNQ | 3m | 60m | 1.0 |
| MNQ | 5m | 120m | 0.998 |
| MNQ | 5m | 15m | 0.705 |
| MNQ | 5m | 30m | 0.746 |
| MNQ | 5m | 60m | 0.83 |

## Outcome effects across 15/30/60/120m and 3m vs 5m bars
| inst | ev | 3m_sign_agree_of_4 | 5m_sign_agree_of_4 | 3m_n_sig_tcrit | 5m_n_sig_tcrit | t_corr_3m_vs_5m | same_sign_3m_5m_of_4 | FRACTAL_TRANSFER |
|---|---|---|---|---|---|---|---|---|
| ES | DB_ACCEPT | 3 | 3 | 0 | 0 | 0.778 | 4 | NO |
| ES | DB_BREAK | 3 | 4 | 0 | 0 | 0.92 | 3 | NO |
| ES | DB_FAILED_ACCEPT | 3 | 3 | 0 | 0 | -0.056 | 2 | NO |
| ES | DB_REENTRY | 3 | 3 | 0 | 0 | 0.448 | 4 | NO |
| ES | DB_RESUMED | 3 | 2 | 0 | 0 | -0.087 | 3 | NO |
| ES | DB_RETEST_HOLD | 3 | 3 | 0 | 0 | 0.15 | 2 | NO |
| ES | L_FAILED_RECLAIM | 2 | 2 | 0 | 0 | 0.948 | 4 | NO |
| ES | L_FAILED_RETEST | 4 | 4 | 0 | 0 | 0.138 | 4 | NO |
| ES | L_RANGE_REENTRY | 4 | 4 | 0 | 0 | -0.004 | 4 | NO |
| ES | L_RECLAIM | 4 | 4 | 0 | 0 | -0.353 | 4 | NO |
| ES | L_RESUMPTION | 3 | 2 | 0 | 0 | 0.249 | 3 | NO |
| ES | L_RETEST | 3 | 4 | 0 | 0 | -0.181 | 3 | NO |
| ES | L_RETEST_HOLD | 2 | 3 | 0 | 0 | -0.804 | 1 | NO |
| ES | L_SWEEP | 4 | 4 | 0 | 0 | 0.469 | 4 | NO |
| ES | UB_ACCEPT | 3 | 2 | 0 | 0 | 0.766 | 3 | NO |
| ES | UB_BREAK | 3 | 2 | 0 | 0 | 0.968 | 3 | NO |
| ES | UB_FAILED_ACCEPT | 2 | 2 | 0 | 0 | 0.973 | 4 | NO |
| ES | UB_REENTRY | 2 | 3 | 0 | 0 | -0.19 | 3 | NO |
| ES | UB_RESUMED | 3 | 4 | 0 | 0 | -0.688 | 3 | NO |
| ES | UB_RETEST_HOLD | 4 | 4 | 0 | 0 | -0.615 | 4 | NO |
| ES | U_FAILED_RECLAIM | 3 | 3 | 0 | 0 | -0.24 | 2 | NO |
| ES | U_FAILED_RETEST | 2 | 3 | 0 | 0 | 0.627 | 3 | NO |
| ES | U_RECLAIM | 3 | 2 | 0 | 0 | 0.582 | 3 | NO |
| ES | U_RESUMPTION | 3 | 2 | 0 | 0 | -0.722 | 1 | NO |
| ES | U_RETEST | 3 | 2 | 0 | 0 | -0.816 | 1 | NO |
| ES | U_RETEST_HOLD | 3 | 3 | 0 | 0 | 0.003 | 2 | NO |
| ES | U_SWEEP | 2 | 2 | 0 | 0 | 0.78 | 2 | NO |
| MNQ | DB_ACCEPT | 4 | 4 | 0 | 2 | -0.372 | 4 | NO |
| MNQ | DB_BREAK | 4 | 4 | 0 | 1 | 0.906 | 4 | NO |
| MNQ | DB_FAILED_ACCEPT | 3 | 4 | 1 | 0 | 0.992 | 3 | NO |
| MNQ | DB_REENTRY | 2 | 3 | 0 | 0 | -0.362 | 1 | NO |
| MNQ | DB_RESUMED | 3 | 4 | 0 | 0 | -0.001 | 3 | NO |
| MNQ | DB_RETEST_HOLD | 2 | 3 | 0 | 0 | -0.221 | 1 | NO |
| MNQ | L_FAILED_RECLAIM | 4 | 3 | 0 | 0 | 0.48 | 3 | NO |
| MNQ | L_FAILED_RETEST | 4 | 4 | 0 | 0 | 0.654 | 4 | NO |
| MNQ | L_RANGE_REENTRY | 3 | 4 | 0 | 0 | 0.911 | 3 | NO |
| MNQ | L_RECLAIM | 3 | 4 | 0 | 0 | 0.913 | 3 | NO |
| MNQ | L_RESUMPTION | 2 | 2 | 0 | 0 | 0.075 | 2 | NO |
| MNQ | L_RETEST | 4 | 4 | 0 | 1 | 0.347 | 4 | NO |
| MNQ | L_RETEST_HOLD | 3 | 3 | 0 | 0 | -0.092 | 2 | NO |
| MNQ | L_SWEEP | 3 | 3 | 0 | 3 | 0.922 | 4 | NO |
| MNQ | UB_ACCEPT | 3 | 3 | 0 | 0 | 0.783 | 2 | NO |
| MNQ | UB_BREAK | 3 | 2 | 0 | 0 | 0.07 | 3 | NO |
| MNQ | UB_FAILED_ACCEPT | 2 | 3 | 0 | 0 | 0.76 | 3 | NO |
| MNQ | UB_REENTRY | 4 | 3 | 0 | 1 | -0.02 | 3 | NO |
| MNQ | UB_RESUMED | 2 | 3 | 0 | 1 | 0.386 | 1 | NO |
| MNQ | UB_RETEST_HOLD | 3 | 4 | 0 | 0 | -0.808 | 3 | NO |
| MNQ | U_FAILED_RECLAIM | 3 | 2 | 0 | 0 | 0.784 | 3 | NO |
| MNQ | U_FAILED_RETEST | 4 | 3 | 0 | 1 | 0.373 | 3 | NO |
| MNQ | U_RECLAIM | 2 | 3 | 0 | 0 | 0.811 | 3 | NO |
| MNQ | U_RESUMPTION | 3 | 2 | 0 | 0 | 0.667 | 3 | NO |
| MNQ | U_RETEST | 2 | 3 | 0 | 0 | 0.939 | 3 | NO |
| MNQ | U_RETEST_HOLD | 2 | 4 | 0 | 0 | 0.994 | 2 | NO |
| MNQ | U_SWEEP | 3 | 3 | 0 | 0 | 0.723 | 4 | NO |

**Reading.** The *structure* is scale-invariant (transition ordering rank-correlation 0.69-1.0; ES and MNQ nearly
identical) — consistent with recurrent scale-normalised state mechanics. The *outcome information* is absent at every
scale, so there is nothing to transfer. MNQ L_SWEEP is the only mechanism with same-sign effects on both bar resolutions
(5m: 3 horizons above the 5m critical value; 3m: none) and it failed VAL.
FRACTAL_EFFECT_TRANSFERS_ACROSS_TIMEFRAMES_ES = NO, _MNQ = NO.

