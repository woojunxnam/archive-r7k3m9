# TEST97_AUDIT_CORRECTION_1 - corrected results (prereg commit 85f5bdc)

```json
{
 "CORRECTION": "TEST97_AUDIT_CORRECTION_1",
 "PREREG_COMMIT": "85f5bdc",
 "TOTAL_TEST97_LEDGER_ROWS": 570,
 "TOTAL_TEST97_DISTINCT_VARIANTS": 114,
 "TOTAL_TEST97_ML_CONFIGS": 0,
 "TOTAL_TEST97_GA_GENOMES": 0,
 "note": "each distinct definition normally yields ES / NQ / YM / RTY / POOLED rows; 570 are ledger rows, not distinct variants",
 "TEST97_PORTFOLIO_SURVIVOR": "NO",
 "FT2_STATUS": "DOWNGRADED - EVENT CLUE NOT ROBUST: 5,000-rep precision audit puts the h12 CI lower bound below 0 even with the original null (-0.0009) and with causal monthly-expanding edges (-0.0033); strategy remains rejected; selection-exposed",
 "W3_V1_STATUS": "CORRECTED_HISTORICAL_CLUE (not promoted): with the preregistered k=0 family null, k=0.2 and k=0.3 at 16:15 show +0.029 ATR over the close-above-open population (CI lower bound +0.0016, 8/8 and 7/8 years, gross > cost); 30 / 60-min horizons and k=0.1/0.5/0.75 do not; vs null A the same events are only +0.007 ATR; 15 (k x horizon) cells tested",
 "W3_V3_FIRST_PULLBACK_STATUS": "NO SIGNIFICANT DIFFERENCE (previous 'worse than chase' RETRACTED - it compared different populations): on 3,763 matched sessions pullback-minus-chase at the same exit = +0.0058 ATR (CI -0.0045..+0.0161, 6/8 years); own 60-min horizons -0.003; ES / NQ negative, YM / RTY positive; pullback entry has lower 60-min MAE (0.18 vs 0.21 ATR)",
 "FOLLOW_THROUGH_INFORMATION_STATUS": "VALID CLUE (weak): confirmed minus unconfirmed at the same minute B +0.012 (h6, CI>0) / +0.014 (h12, CI>0); F +0.034 (h12, CI lower +0.0007); E and D CIs include 0",
 "FOLLOW_THROUGH_TIMING_STATUS": "NEGATIVE: on identical confirmed events and identical exit minutes the confirmation entry is worse than the original entry by 0.05 (B/C) to 0.13 (F) ATR (CIs exclude 0) - waiting pays up the confirmation bar; note the original-entry arm is conditioned on a later confirmation (hindsight population), so this measures the cost of waiting, not a tradeable original-entry edge",
 "RECOVERY_STACK_STATUS": "REJECT on the FT2 initial population (ADD1 < 0 in all four indices); standing rule: ADD1 <= 0 -> stop deeper stacking; deeper blind-DCA outputs NOT USABLE (threshold scaled by units, deviates from prereg)",
 "FT2_POPULATION_AUDIT": {
  "explanation": "Wave-2 EVENT_EDGE used the common population (confirmation bar <= 67, all bar horizons complete): 431 pooled; Phase 3 used every RTH FT2 event with entry before 16:15 (no bar cap): ~602; Phase-3 'X60' clipped late events at 16:15 -> relabelled X60_CLIPPED",
  "counts": [
   {
    "instrument": "ES",
    "common_pop_events_b<=67": 79,
    "all_rth_events": 135,
    "strict_x60_events": 79,
    "late_excluded": 56
   },
   {
    "instrument": "NQ",
    "common_pop_events_b<=67": 100,
    "all_rth_events": 147,
    "strict_x60_events": 100,
    "late_excluded": 47
   },
   {
    "instrument": "YM",
    "common_pop_events_b<=67": 102,
    "all_rth_events": 144,
    "strict_x60_events": 102,
    "late_excluded": 42
   },
   {
    "instrument": "RTY",
    "common_pop_events_b<=67": 150,
    "all_rth_events": 176,
    "strict_x60_events": 150,
    "late_excluded": 26
   }
  ]
 },
 "PORTFOLIO_REPORTING": "VIRTUAL_ADDITIVE_DIAGNOSTIC only (no CAPACITY_VALID_PORTFOLIO)",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO",
 "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO"
}
```

## C. W3_V1 volatility breakout vs preregistered k=0 family null (pooled; ATR_d)

|    |      k | horizon   |    n |   gross_mean |      xA |     xB1 |   x_family_k0 |   ci_lo |   ci_hi |   years_pos |   cost_atr | CLUE   |
|---:|-------:|:----------|-----:|-------------:|--------:|--------:|--------------:|--------:|--------:|------------:|-----------:|:-------|
|  4 | 0.1000 | h6        | 5232 |       0.0002 | -0.0009 | -0.0039 |        0.0006 | -0.0081 |  0.0089 |      4.0000 |     0.0107 | False  |
|  9 | 0.1000 | h12       | 5232 |       0.0044 |  0.0034 |  0.0034 |        0.0018 | -0.0096 |  0.0128 |      4.0000 |     0.0107 | False  |
| 14 | 0.1000 | h1615     | 5232 |       0.0107 | -0.0013 | -0.0037 |        0.0110 | -0.0151 |  0.0365 |      6.0000 |     0.0107 | False  |
| 19 | 0.2000 | h6        | 4410 |       0.0022 |  0.0008 |  0.0002 |        0.0022 | -0.0065 |  0.0113 |      5.0000 |     0.0107 | False  |
| 24 | 0.2000 | h12       | 4410 |       0.0089 |  0.0073 |  0.0076 |        0.0070 | -0.0047 |  0.0197 |      7.0000 |     0.0107 | False  |
| 29 | 0.2000 | h1615     | 4410 |       0.0208 |  0.0073 |  0.0069 |        0.0290 |  0.0016 |  0.0557 |      8.0000 |     0.0107 | True   |
| 34 | 0.3000 | h6        | 3605 |       0.0049 |  0.0039 |  0.0037 |        0.0033 | -0.0059 |  0.0128 |      5.0000 |     0.0108 | False  |
| 39 | 0.3000 | h12       | 3605 |       0.0123 |  0.0105 |  0.0111 |        0.0115 | -0.0015 |  0.0243 |      5.0000 |     0.0108 | False  |
| 44 | 0.3000 | h1615     | 3605 |       0.0214 |  0.0071 |  0.0083 |        0.0288 |  0.0016 |  0.0555 |      7.0000 |     0.0108 | True   |
| 49 | 0.5000 | h6        | 2287 |       0.0071 |  0.0043 |  0.0061 |        0.0032 | -0.0080 |  0.0147 |      5.0000 |     0.0108 | False  |
| 54 | 0.5000 | h12       | 2287 |       0.0086 |  0.0044 |  0.0063 |        0.0085 | -0.0080 |  0.0242 |      5.0000 |     0.0108 | False  |
| 59 | 0.5000 | h1615     | 2287 |       0.0096 | -0.0071 | -0.0011 |        0.0236 | -0.0097 |  0.0553 |      5.0000 |     0.0108 | False  |
| 64 | 0.7500 | h6        | 1156 |       0.0074 |  0.0053 |  0.0070 |       -0.0027 | -0.0195 |  0.0134 |      4.0000 |     0.0110 | False  |
| 69 | 0.7500 | h12       | 1156 |       0.0119 |  0.0080 |  0.0110 |        0.0034 | -0.0193 |  0.0263 |      5.0000 |     0.0110 | False  |
| 74 | 0.7500 | h1615     | 1156 |       0.0020 | -0.0152 | -0.0059 |       -0.0024 | -0.0462 |  0.0407 |      4.0000 |     0.0110 | False  |

per instrument (family-null excess)

|                 |      ES |      NQ |     RTY |      YM |
|:----------------|--------:|--------:|--------:|--------:|
| (0.1, 'h12')    |  0.0049 | -0.0010 | -0.0056 |  0.0086 |
| (0.1, 'h1615')  |  0.0236 |  0.0140 | -0.0019 |  0.0076 |
| (0.1, 'h6')     |  0.0035 | -0.0033 | -0.0028 |  0.0049 |
| (0.2, 'h12')    |  0.0163 |  0.0039 | -0.0060 |  0.0138 |
| (0.2, 'h1615')  |  0.0493 |  0.0397 |  0.0070 |  0.0193 |
| (0.2, 'h6')     |  0.0013 | -0.0017 |  0.0051 |  0.0042 |
| (0.3, 'h12')    |  0.0065 |  0.0085 |  0.0054 |  0.0257 |
| (0.3, 'h1615')  |  0.0457 |  0.0262 |  0.0121 |  0.0312 |
| (0.3, 'h6')     | -0.0037 | -0.0062 |  0.0096 |  0.0137 |
| (0.5, 'h12')    |  0.0166 |  0.0031 | -0.0067 |  0.0215 |
| (0.5, 'h1615')  |  0.0552 |  0.0368 |  0.0166 | -0.0129 |
| (0.5, 'h6')     |  0.0001 | -0.0013 |  0.0014 |  0.0123 |
| (0.75, 'h12')   |  0.0088 | -0.0227 |  0.0004 |  0.0260 |
| (0.75, 'h1615') |  0.0389 | -0.0260 |  0.0272 | -0.0435 |
| (0.75, 'h6')    | -0.0002 | -0.0161 |  0.0062 | -0.0007 |

## D. W3_V3 first pullback vs chase on identical sessions (paired B - A)

|    | label                                             | instrument   |    n |    mean |    ci_lo |    ci_hi |   years_pos |    years |
|---:|:--------------------------------------------------|:-------------|-----:|--------:|---------:|---------:|------------:|---------:|
|  0 | W3_V3_own_h6_pullback_minus_chase                 | ES           |  945 | -0.0115 | nan      | nan      |    nan      | nan      |
|  1 | W3_V3_own_h6_pullback_minus_chase                 | NQ           |  978 | -0.0032 | nan      | nan      |    nan      | nan      |
|  2 | W3_V3_own_h6_pullback_minus_chase                 | YM           |  901 |  0.0070 | nan      | nan      |    nan      | nan      |
|  3 | W3_V3_own_h6_pullback_minus_chase                 | RTY          |  939 |  0.0119 | nan      | nan      |    nan      | nan      |
|  4 | W3_V3_own_h6_pullback_minus_chase                 | POOLED       | 3763 |  0.0009 |  -0.0092 |   0.0110 |      4.0000 |   8.0000 |
|  5 | W3_V3_own_h12_pullback_minus_chase                | ES           |  945 | -0.0190 | nan      | nan      |    nan      | nan      |
|  6 | W3_V3_own_h12_pullback_minus_chase                | NQ           |  978 | -0.0091 | nan      | nan      |    nan      | nan      |
|  7 | W3_V3_own_h12_pullback_minus_chase                | YM           |  901 |  0.0064 | nan      | nan      |    nan      | nan      |
|  8 | W3_V3_own_h12_pullback_minus_chase                | RTY          |  939 |  0.0103 | nan      | nan      |    nan      | nan      |
|  9 | W3_V3_own_h12_pullback_minus_chase                | POOLED       | 3763 | -0.0030 |  -0.0150 |   0.0090 |      2.0000 |   8.0000 |
| 10 | W3_V3_own_h1615_pullback_minus_chase              | ES           |  945 | -0.0008 | nan      | nan      |    nan      | nan      |
| 11 | W3_V3_own_h1615_pullback_minus_chase              | NQ           |  978 |  0.0014 | nan      | nan      |    nan      | nan      |
| 12 | W3_V3_own_h1615_pullback_minus_chase              | YM           |  901 |  0.0126 | nan      | nan      |    nan      | nan      |
| 13 | W3_V3_own_h1615_pullback_minus_chase              | RTY          |  939 |  0.0107 | nan      | nan      |    nan      | nan      |
| 14 | W3_V3_own_h1615_pullback_minus_chase              | POOLED       | 3763 |  0.0058 |  -0.0045 |   0.0161 |      6.0000 |   8.0000 |
| 15 | W3_V3_same_exit_pullback_h12_pullback_minus_chase | ES           |  945 | -0.0008 | nan      | nan      |    nan      | nan      |
| 16 | W3_V3_same_exit_pullback_h12_pullback_minus_chase | NQ           |  978 |  0.0014 | nan      | nan      |    nan      | nan      |
| 17 | W3_V3_same_exit_pullback_h12_pullback_minus_chase | YM           |  901 |  0.0126 | nan      | nan      |    nan      | nan      |
| 18 | W3_V3_same_exit_pullback_h12_pullback_minus_chase | RTY          |  939 |  0.0107 | nan      | nan      |    nan      | nan      |
| 19 | W3_V3_same_exit_pullback_h12_pullback_minus_chase | POOLED       | 3763 |  0.0058 |  -0.0045 |   0.0161 |      6.0000 |   8.0000 |
| 20 | W3_V3_same_exit_1615_pullback_minus_chase         | ES           |  945 | -0.0008 | nan      | nan      |    nan      | nan      |
| 21 | W3_V3_same_exit_1615_pullback_minus_chase         | NQ           |  978 |  0.0014 | nan      | nan      |    nan      | nan      |
| 22 | W3_V3_same_exit_1615_pullback_minus_chase         | YM           |  901 |  0.0126 | nan      | nan      |    nan      | nan      |
| 23 | W3_V3_same_exit_1615_pullback_minus_chase         | RTY          |  939 |  0.0107 | nan      | nan      |    nan      | nan      |
| 24 | W3_V3_same_exit_1615_pullback_minus_chase         | POOLED       | 3763 |  0.0058 |  -0.0045 |   0.0161 |      6.0000 |   8.0000 |

Note: at a common exit minute the paired difference equals the entry-price difference, so the h12-same-exit and 16:15 rows coincide by construction.

|    | instrument   |   sessions |   chase_mfe60 |   chase_mae60 |   pullback_mfe60 |   pullback_mae60 |
|---:|:-------------|-----------:|--------------:|--------------:|-----------------:|-----------------:|
|  0 | ES           |        945 |        0.1810 |        0.1939 |           0.1516 |           0.1809 |
|  1 | NQ           |        978 |        0.1910 |        0.2054 |           0.1627 |           0.1802 |
|  2 | YM           |        901 |        0.1982 |        0.2063 |           0.1663 |           0.1697 |
|  3 | RTY          |        939 |        0.2115 |        0.2321 |           0.1771 |           0.1783 |

## E. M04 information vs timing (pooled)

|    | label                                                    | instrument   |    n |    mean | confirm         | exit               |   ci_lo |   ci_hi |   years_pos |    years |   n_unconf |
|---:|:---------------------------------------------------------|:-------------|-----:|--------:|:----------------|:-------------------|--------:|--------:|------------:|---------:|-----------:|
|  4 | M04_B_next_bull_same_exit_conf_h12_conf_minus_orig       | POOLED       | 3667 | -0.0525 | B_next_bull     | same_exit_conf_h12 | -0.0552 | -0.0501 |      0.0000 |   8.0000 |   nan      |
|  9 | M04_B_next_bull_same_exit_1615_conf_minus_orig           | POOLED       | 3667 | -0.0525 | B_next_bull     | same_exit_1615     | -0.0552 | -0.0501 |      0.0000 |   8.0000 |   nan      |
| 10 | M04_B_next_bull_INFO_h6_confirmed_minus_unconfirmed      | POOLED       | 3667 |  0.0117 | B_next_bull     | h6                 |  0.0017 |  0.0225 |    nan      | nan      |  3870.0000 |
| 11 | M04_B_next_bull_INFO_h12_confirmed_minus_unconfirmed     | POOLED       | 3667 |  0.0138 | B_next_bull     | h12                |  0.0004 |  0.0288 |    nan      | nan      |  3870.0000 |
| 16 | M04_C_next_close_gt_same_exit_conf_h12_conf_minus_orig   | POOLED       | 3665 | -0.0525 | C_next_close_gt | same_exit_conf_h12 | -0.0550 | -0.0499 |      0.0000 |   8.0000 |   nan      |
| 21 | M04_C_next_close_gt_same_exit_1615_conf_minus_orig       | POOLED       | 3665 | -0.0525 | C_next_close_gt | same_exit_1615     | -0.0550 | -0.0499 |      0.0000 |   8.0000 |   nan      |
| 22 | M04_C_next_close_gt_INFO_h6_confirmed_minus_unconfirmed  | POOLED       | 3665 |  0.0112 | C_next_close_gt | h6                 |  0.0013 |  0.0219 |    nan      | nan      |  3872.0000 |
| 23 | M04_C_next_close_gt_INFO_h12_confirmed_minus_unconfirmed | POOLED       | 3665 |  0.0134 | C_next_close_gt | h12                | -0.0000 |  0.0282 |    nan      | nan      |  3872.0000 |
| 28 | M04_E_next_HH_HL_same_exit_conf_h12_conf_minus_orig      | POOLED       | 5941 | -0.0169 | E_next_HH_HL    | same_exit_conf_h12 | -0.0192 | -0.0144 |      0.0000 |   8.0000 |   nan      |
| 33 | M04_E_next_HH_HL_same_exit_1615_conf_minus_orig          | POOLED       | 5941 | -0.0169 | E_next_HH_HL    | same_exit_1615     | -0.0192 | -0.0144 |      0.0000 |   8.0000 |   nan      |
| 34 | M04_E_next_HH_HL_INFO_h6_confirmed_minus_unconfirmed     | POOLED       | 5941 |  0.0079 | E_next_HH_HL    | h6                 | -0.0047 |  0.0206 |    nan      | nan      |  1596.0000 |
| 35 | M04_E_next_HH_HL_INFO_h12_confirmed_minus_unconfirmed    | POOLED       | 5941 |  0.0130 | E_next_HH_HL    | h12                | -0.0045 |  0.0298 |    nan      | nan      |  1596.0000 |
| 40 | M04_F_next_STRONG_same_exit_conf_h12_conf_minus_orig     | POOLED       |  431 | -0.1312 | F_next_STRONG   | same_exit_conf_h12 | -0.1416 | -0.1220 |      0.0000 |   8.0000 |   nan      |
| 45 | M04_F_next_STRONG_same_exit_1615_conf_minus_orig         | POOLED       |  431 | -0.1312 | F_next_STRONG   | same_exit_1615     | -0.1416 | -0.1220 |      0.0000 |   8.0000 |   nan      |
| 46 | M04_F_next_STRONG_INFO_h6_confirmed_minus_unconfirmed    | POOLED       |  431 |  0.0253 | F_next_STRONG   | h6                 | -0.0004 |  0.0509 |    nan      | nan      |  7106.0000 |
| 47 | M04_F_next_STRONG_INFO_h12_confirmed_minus_unconfirmed   | POOLED       |  431 |  0.0339 | F_next_STRONG   | h12                |  0.0007 |  0.0676 |    nan      | nan      |  7106.0000 |
| 52 | M04_D_two_bull_same_exit_conf_h12_conf_minus_orig        | POOLED       | 1739 | -0.1048 | D_two_bull      | same_exit_conf_h12 | -0.1111 | -0.0988 |      0.0000 |   8.0000 |   nan      |
| 57 | M04_D_two_bull_same_exit_1615_conf_minus_orig            | POOLED       | 1739 | -0.1048 | D_two_bull      | same_exit_1615     | -0.1111 | -0.0988 |      0.0000 |   8.0000 |   nan      |
| 58 | M04_D_two_bull_INFO_h6_confirmed_minus_unconfirmed       | POOLED       | 1739 |  0.0112 | D_two_bull      | h6                 | -0.0013 |  0.0229 |    nan      | nan      |  5554.0000 |
| 59 | M04_D_two_bull_INFO_h12_confirmed_minus_unconfirmed      | POOLED       | 1739 |  0.0084 | D_two_bull      | h12                | -0.0090 |  0.0256 |    nan      | nan      |  5554.0000 |

## F. FT2 population / strict X60 audit

|    | population       | instrument   |   trades |   avg_day |   usd_per_trade |   slip4_day |   common_pop_events_b<=67 |   all_rth_events |   strict_x60_events |   late_excluded |   y2022_pnl |   y2022_matched_long_pnl |   y2022_excess_A |   y2022_loss_capture |   y2022_maxdd |   y2022_worst_day |   y2022_avg_exposure_contracts |   peak_exposure_contracts | recovery_date   |
|---:|:-----------------|:-------------|---------:|----------:|----------------:|------------:|--------------------------:|-----------------:|--------------------:|----------------:|------------:|-------------------------:|-----------------:|---------------------:|--------------:|------------------:|-------------------------------:|--------------------------:|:----------------|
|  0 | STRICT_X60       | ES           |       79 |    0.6007 |         13.2378 |      0.2604 |                        79 |              135 |                  79 |              56 |     38.9200 |                 -20.3360 |          59.2560 |              -1.9138 |      378.7400 |         -378.7400 |                         0.0101 |                    1.0000 | 2023-01-03      |
|  1 | X60_CLIPPED_ALL  | ES           |      135 |    0.8193 |         10.5656 |      0.2377 |                        79 |              135 |                  79 |              56 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
|  2 | LATE_X60_CLIPPED | ES           |       56 |    0.2186 |          6.7957 |     -0.0227 |                        79 |              135 |                  79 |              56 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
|  3 | X1615_ALL        | ES           |      135 |    1.2170 |         15.6952 |      0.6355 |                        79 |              135 |                  79 |              56 |      9.0000 |                 -47.2169 |          56.2169 |              -0.1906 |      459.8900 |         -254.9900 |                         0.0377 |                    1.0000 | 2023-01-03      |
|  4 | LATE_X1615       | ES           |       56 |    0.2186 |          6.7957 |     -0.0227 |                        79 |              135 |                  79 |              56 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
|  5 | STRICT_X1615     | ES           |       79 |    0.9984 |         22.0037 |      0.6581 |                        79 |              135 |                  79 |              56 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
|  6 | STRICT_X60       | NQ           |      100 |    1.3116 |         22.8350 |      1.1393 |                       100 |              147 |                 100 |              47 |   -386.5600 |                  97.4069 |        -483.9669 |             nan      |      552.9800 |         -542.2400 |                         0.0112 |                    1.0000 | 2023-02-01      |
|  7 | X60_CLIPPED_ALL  | NQ           |      147 |    0.9108 |         10.7872 |      0.6575 |                       100 |              147 |                 100 |              47 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
|  8 | LATE_X60_CLIPPED | NQ           |       47 |   -0.4008 |        -14.8464 |     -0.4818 |                       100 |              147 |                 100 |              47 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
|  9 | X1615_ALL        | NQ           |      147 |    1.6543 |         19.5933 |      1.4010 |                       100 |              147 |                 100 |              47 |  -1025.0000 |                  40.6554 |       -1065.6554 |             nan      |     1605.9200 |         -626.7400 |                         0.0344 |                    1.0000 | 2023-08-29      |
| 10 | LATE_X1615       | NQ           |       47 |   -0.4008 |        -14.8464 |     -0.4818 |                       100 |              147 |                 100 |              47 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 11 | STRICT_X1615     | NQ           |      100 |    2.0551 |         35.7800 |      1.8828 |                       100 |              147 |                 100 |              47 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 12 | STRICT_X60       | YM           |      102 |   -0.2751 |         -4.6959 |     -0.4509 |                       102 |              144 |                 102 |              42 |    235.4000 |                 -52.5827 |         287.9827 |              -4.4768 |       79.2400 |          -79.2400 |                         0.0089 |                    1.0000 | 2023-01-03      |
| 13 | X60_CLIPPED_ALL  | YM           |      144 |   -0.2062 |         -2.4935 |     -0.4544 |                       102 |              144 |                 102 |              42 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 14 | LATE_X60_CLIPPED | YM           |       42 |    0.0689 |          2.8552 |     -0.0035 |                       102 |              144 |                 102 |              42 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 15 | X1615_ALL        | YM           |      144 |    0.3107 |          3.7565 |      0.0626 |                       102 |              144 |                 102 |              42 |    206.7200 |                  -4.4456 |         211.1656 |             -46.5001 |      243.2200 |         -179.7400 |                         0.0379 |                    1.0000 | 2023-01-03      |
| 16 | LATE_X1615       | YM           |       42 |    0.0689 |          2.8552 |     -0.0035 |                       102 |              144 |                 102 |              42 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 17 | STRICT_X1615     | YM           |      102 |    0.2418 |          4.1276 |      0.0661 |                       102 |              144 |                 102 |              42 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 18 | STRICT_X60       | RTY          |      150 |    0.7490 |          8.6933 |      0.4905 |                       150 |              176 |                 150 |              26 |     50.7000 |                 -28.4084 |          79.1084 |              -1.7847 |      143.7400 |         -143.7400 |                         0.0118 |                    1.0000 | 2023-01-03      |
| 19 | X60_CLIPPED_ALL  | RTY          |      176 |    0.8020 |          7.9333 |      0.4987 |                       150 |              176 |                 150 |              26 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 20 | LATE_X60_CLIPPED | RTY          |       26 |    0.0530 |          3.5485 |      0.0082 |                       150 |              176 |                 150 |              26 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 21 | X1615_ALL        | RTY          |      176 |    0.2649 |          2.6208 |     -0.0383 |                       150 |              176 |                 150 |              26 |      9.2600 |                  -8.1594 |          17.4194 |              -1.1349 |      450.7000 |         -346.7400 |                         0.0519 |                    1.0000 | 2023-01-03      |
| 22 | LATE_X1615       | RTY          |       26 |    0.0530 |          3.5485 |      0.0082 |                       150 |              176 |                 150 |              26 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |
| 23 | STRICT_X1615     | RTY          |      150 |    0.2119 |          2.4600 |     -0.0465 |                       150 |              176 |                 150 |              26 |    nan      |                 nan      |         nan      |             nan      |      nan      |          nan      |                       nan      |                  nan      | nan             |

### VIRTUAL_ADDITIVE_DIAGNOSTIC (not capacity valid)

|    | label                                                                    |   standalone_avg_day |   main_plus_avg_day |   main_plus_maxdd |   main_plus_worst |   main_plus_ret_dd |   main_ret_dd |   corr |   loss_jaccard |   bottom5_overlap |   active_days | peak_MES_MNQ_MYM_M2K    |
|---:|:-------------------------------------------------------------------------|---------------------:|--------------------:|------------------:|------------------:|-------------------:|--------------:|-------:|---------------:|------------------:|--------------:|:------------------------|
|  0 | FT2_STRICT_X60_4INDEX (VIRTUAL_ADDITIVE_DIAGNOSTIC - not capacity valid) |               2.3862 |            145.5932 |        13386.8424 |        -4666.4400 |             0.0109 |        0.0103 | 0.1665 |         0.2988 |            0.0682 |           276 | 1 / 1 / 1 / 1 (virtual) |
|  1 | FT2_X1615_ALL_4INDEX (VIRTUAL_ADDITIVE_DIAGNOSTIC - not capacity valid)  |               3.4470 |            146.6541 |        13136.0300 |        -4666.4400 |             0.0112 |        0.0103 | 0.2326 |         0.3627 |            0.0909 |           348 | 1 / 1 / 1 / 1 (virtual) |

## G. FT2 null robustness (5,000-rep date-clustered bootstrap)

|    | label                                    | instrument   |   n |   mean | method                         | horizon   |   ci_lo |   ci_hi |   years_pos |   years |
|---:|:-----------------------------------------|:-------------|----:|-------:|:-------------------------------|:----------|--------:|--------:|------------:|--------:|
|  4 | FT2_OLD_full_sample_edges_h6             | POOLED       | 429 | 0.0244 | OLD_full_sample_edges          | h6        | -0.0025 |  0.0519 |      5.0000 |  8.0000 |
|  9 | FT2_OLD_full_sample_edges_h12            | POOLED       | 423 | 0.0365 | OLD_full_sample_edges          | h12       | -0.0009 |  0.0746 |      6.0000 |  8.0000 |
| 14 | FT2_OLD_full_sample_edges_h1615          | POOLED       | 429 | 0.0526 | OLD_full_sample_edges          | h1615     | -0.0016 |  0.1047 |      4.0000 |  8.0000 |
| 19 | FT2_CAUSAL_monthly_expanding_edges_h6    | POOLED       | 420 | 0.0234 | CAUSAL_monthly_expanding_edges | h6        | -0.0045 |  0.0510 |      5.0000 |  8.0000 |
| 24 | FT2_CAUSAL_monthly_expanding_edges_h12   | POOLED       | 415 | 0.0370 | CAUSAL_monthly_expanding_edges | h12       | -0.0033 |  0.0765 |      6.0000 |  8.0000 |
| 29 | FT2_CAUSAL_monthly_expanding_edges_h1615 | POOLED       | 420 | 0.0573 | CAUSAL_monthly_expanding_edges | h1615     |  0.0034 |  0.1127 |      5.0000 |  8.0000 |

## H. Position management governance

```json
{
 "RECOVERY_STACK": "REJECT on the FT2 initial population (ADD1 < 0 in ES / NQ / YM / RTY); no ADD2 / ADD3 research",
 "standing_rule": "if ADD1 <= 0 -> stop deeper stacking automatically",
 "blind_DCA_note": "existing code used average - 0.5 ATR x units for deeper adds (prereg: average - 0.5 ATR per add) -> deeper blind-DCA outputs NOT USABLE"
}
```

