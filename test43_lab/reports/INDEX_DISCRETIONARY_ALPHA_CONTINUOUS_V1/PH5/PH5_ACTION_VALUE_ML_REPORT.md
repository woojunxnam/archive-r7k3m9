# PH5 action values + response speed + discretionary-emulator ML — results (prereg 89d85e2)

- ENTRY (Model E, 15 configs): ML never beats take-all in any population (increments -15.6 .. +2.0 $/day; only D8 Ridge +1.98 with 4/5 folds and a -10.6 worst fold). Take-all raw economics: D7 +9.20 $/day (SLIP4 +1.98, 4/5 folds) is the only positive-SLIP4 new trigger besides C2 (+6.79 / +5.02); it failed the PH3 magnitude-null gate, i.e. its dollars are mostly generic intraday drift after a bullish trigger (like ORB).
- HOLD vs EXIT (response speed): 'good trades work quickly' is FALSE for C2 as an exit rule — exiting non-working trades at 10 / 20 / 30 min costs -1.81 / -0.96 / -1.65 $/day; hold value rises with current return (winners keep going; Spearman 0.7-0.8, not coherent), but losers also recover on average; Model H (9 configs) all negative (-1.3 .. -5.4 $/day).
- ADD: generic first-winner ADD1 +6.30 $/day (SLIP4 +4.65, 4/5 folds) = GENERIC WINNER PRESS (confirms PH1); generic first-underwater ADD1 +3.18 $/day (SLIP4 +1.63) = blind averaging inside C2, control only; Model A (6 configs) does not beat the generic press (5.42-6.36).
- EXIT architecture: every alternative to 16:15 loses (X60 -6.40, X120 -5.98, XRES -5.23, XSTRUCT -2.28 $/day); Model X (3 configs) negative.

33 ML configs.  Hold-value curves by current-return quintile: [{'checkpoint_min': 10, 'hold_by_ret_quintile': [7.85, 9.45, -2.5, 31.24, 40.09], 'spearman': 0.7}, {'checkpoint_min': 20, 'hold_by_ret_quintile': [-0.05, 11.16, 10.58, 30.91, 30.57], 'spearman': 0.7999999999999999}, {'checkpoint_min': 30, 'hold_by_ret_quintile': [-3.57, 24.07, -5.21, 30.22, 39.45], 'spearman': 0.7}]

## ML
| task   | population    | config      |   value_day |   folds_pos |   worst_fold |    n |   slip4_value_day |   incr_vs_take_all |
|:-------|:--------------|:------------|------------:|------------:|-------------:|-----:|------------------:|-------------------:|
| E      | D2            | RIDGE_TOP50 |       -9.46 |           1 |       -36.57 | 3122 |            -18.36 |             -13.23 |
| E      | D2            | LOGIT_TOP50 |      -11.86 |           2 |       -46.16 | 2777 |            -20.32 |             -15.64 |
| E      | D2            | HGB_TOP50   |       -8.58 |           2 |       -50.09 | 3272 |            -18.32 |             -12.36 |
| E      | D3            | RIDGE_TOP50 |       -5.12 |           3 |       -17.37 | 1190 |             -8.58 |             -10.21 |
| E      | D3            | LOGIT_TOP50 |       -0.33 |           2 |        -5.84 | 1273 |             -4.07 |              -5.42 |
| E      | D3            | HGB_TOP50   |       -0.3  |           2 |        -6.35 | 1269 |             -4.24 |              -5.39 |
| E      | D7            | RIDGE_TOP50 |        7.91 |           5 |         2.23 | 1212 |              4.46 |              -1.3  |
| E      | D7            | LOGIT_TOP50 |        4.56 |           4 |        -2.73 | 1295 |              0.64 |              -4.65 |
| E      | D7            | HGB_TOP50   |        8.34 |           4 |        -4.13 | 1240 |              4.7  |              -0.86 |
| E      | D8            | RIDGE_TOP50 |        4.34 |           4 |       -10.63 |  601 |              2.59 |               1.98 |
| E      | D8            | LOGIT_TOP50 |        1.66 |           4 |       -11.47 |  703 |             -0.43 |              -0.7  |
| E      | D8            | HGB_TOP50   |        2.22 |           3 |       -11.13 |  587 |              0.41 |              -0.14 |
| E      | C2            | RIDGE_TOP50 |        4.39 |           4 |        -7.08 |  303 |              3.47 |              -2.4  |
| E      | C2            | LOGIT_TOP50 |        3.62 |           4 |        -5.74 |  319 |              2.64 |              -3.17 |
| E      | C2            | HGB_TOP50   |        5.43 |           4 |        -2.82 |  270 |              4.64 |              -1.36 |
| H      | C2_10m        | RIDGE       |       -2.63 |           1 |        -8.42 |  161 |            nan    |             nan    |
| H      | C2_10m        | LOGIT       |       -2.23 |           2 |        -7.17 |  106 |            nan    |             nan    |
| H      | C2_10m        | HGB         |       -3.14 |           1 |        -8.34 |  251 |            nan    |             nan    |
| H      | C2_20m        | RIDGE       |       -5.41 |           1 |       -11.08 |  181 |            nan    |             nan    |
| H      | C2_20m        | LOGIT       |       -3    |           1 |        -8.35 |  146 |            nan    |             nan    |
| H      | C2_20m        | HGB         |       -4.34 |           0 |        -7.83 |  245 |            nan    |             nan    |
| H      | C2_30m        | RIDGE       |       -5.44 |           1 |       -11.94 |  185 |            nan    |             nan    |
| H      | C2_30m        | LOGIT       |       -1.28 |           1 |        -3.07 |  107 |            nan    |             nan    |
| H      | C2_30m        | HGB         |       -5.19 |           1 |       -10.94 |  269 |            nan    |             nan    |
| A      | C2_WINNER     | RIDGE       |        5.96 |           4 |        -3.5  |  453 |              4.52 |             nan    |
| A      | C2_WINNER     | LOGIT       |        6.36 |           4 |        -3.86 |  468 |              4.88 |             nan    |
| A      | C2_WINNER     | HGB         |        5.42 |           4 |        -5.52 |  435 |              4.07 |             nan    |
| A      | C2_UNDERWATER | RIDGE       |        1.92 |           3 |        -5.01 |  335 |              1.03 |             nan    |
| A      | C2_UNDERWATER | LOGIT       |        1.99 |           4 |        -2.86 |  394 |              0.97 |             nan    |
| A      | C2_UNDERWATER | HGB         |        3.6  |           4 |        -4.55 |  398 |              2.44 |             nan    |
| X      | C2            | RIDGE       |       -5    |           1 |        -9.98 |  540 |            nan    |             nan    |
| X      | C2            | HGB         |       -4.2  |           1 |        -9.56 |  540 |            nan    |             nan    |
| X      | C2            | ENET        |       -3.11 |           1 |        -8.3  |  540 |            nan    |             nan    |

## Action values
| action                        | population   |   value_day |   folds_pos |   worst_fold |    n |   slip4_value_day |
|:------------------------------|:-------------|------------:|------------:|-------------:|-----:|------------------:|
| ENTRY_TAKE_ALL                | D2           |        3.77 |           3 |       -40.92 | 5943 |            -14.17 |
| ENTRY_TAKE_ALL                | D3           |        5.09 |           3 |        -2.95 | 2558 |             -2.84 |
| ENTRY_TAKE_ALL                | D7           |        9.2  |           4 |        -3.97 | 2393 |              1.98 |
| ENTRY_TAKE_ALL                | D8           |        2.36 |           4 |       -13.21 | 1388 |             -1.84 |
| ENTRY_TAKE_ALL                | C2           |        6.79 |           4 |        -3.27 |  590 |              5.02 |
| EXIT_IF_NOT_WORKING_10m       | C2           |       -1.81 |           1 |       -11.26 |  303 |            nan    |
| EXIT_IF_NOT_WORKING_20m       | C2           |       -0.96 |           2 |        -4.63 |  281 |            nan    |
| EXIT_IF_NOT_WORKING_30m       | C2           |       -1.65 |           1 |        -4.91 |  276 |            nan    |
| ADD1_FIRST_WINNER_GENERIC     | C2           |        6.3  |           4 |        -4.73 |  547 |              4.65 |
| ADD1_FIRST_UNDERWATER_GENERIC | C2           |        3.18 |           4 |        -5.2  |  519 |              1.63 |
| EXIT_X60_vs_X1615             | C2           |       -6.4  |           1 |       -14.06 |  540 |            nan    |
| EXIT_X120_vs_X1615            | C2           |       -5.98 |           2 |       -16.4  |  540 |            nan    |
| EXIT_X1615_vs_X1615           | C2           |        0    |           0 |         0    |  540 |            nan    |
| EXIT_XRES_vs_X1615            | C2           |       -5.23 |           1 |       -15.34 |  540 |            nan    |
| EXIT_XSTRUCT_vs_X1615         | C2           |       -2.28 |           2 |        -7.63 |  540 |            nan    |
