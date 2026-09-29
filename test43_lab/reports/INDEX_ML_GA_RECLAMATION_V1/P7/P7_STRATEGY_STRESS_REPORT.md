# P7 strategy stress + routes — results (prereg 4d653cc)

Main on the stitched window 2021-01-01..2026-05-27: 151.78 $/day, MaxDD 13,936, worst -4,666, ret/DD 0.01089.

STRESS_PASS: C1 (13.66 $/day after capacity; SLIP4 3.13), C2 (4.96; SLIP4 3.24), C7 (4.67; SLIP4 2.69).  FAIL: C4 (2/5 folds), C5 (SLIP4 < 0), C6 (SLIP4 < 0).

ROUTES: **C2_P2_FAILED_FIRST = ROUTE B SMALL DIVERSIFIER** (+4.96 $/day, corr 0.26, ret/DD 0.01122 = 1.03 x Main, MaxDD 13,980 = 1.003 x, worst -4,728). No ROUTE A (every higher-dollar candidate raises combined MaxDD 10-30%: C1 18,137; C4 17,801). No ROUTE C.

Capacity note: C1 loses ~6.8 $/day to the MNQ 6 cap (skipped NQ trades fall on days when Main is fully loaded, which are also strong days).

|                         | 0                   | 1                  | 2            | 3           | 4          | 5           |
|:------------------------|:--------------------|:-------------------|:-------------|:------------|:-----------|:------------|
| candidate               | C1_R1_TRAPPED_UNION | C2_P2_FAILED_FIRST | C4_L2_FAMILY | C5_HTF1_30m | C6_AV_OR30 | C7_L1_SWH60 |
| arm                     | A_TAKE_ALL          | A_TAKE_ALL         | C_GA         | A_TAKE_ALL  | A_TAKE_ALL | B_ML_NESTED |
| trades_after_capacity   | 3429                | 570                | 1770         | 2469        | 3112       | 641         |
| trades_signal           | 3527                | 590                | 1806         | 2625        | 3277       | 678         |
| avg_day                 | 13.661              | 4.963              | 12.214       | 6.537       | 8.659      | 4.668       |
| slip4_avg_day           | 3.126               | 3.239              | 6.794        | -1.021      | -1.134     | 2.695       |
| delay1_avg_day          | 12.274              | 5.178              | 10.851       | 4.521       | 10.936     | 4.274       |
| missed20_avg_day        | 15.266              | 4.581              | 8.799        | 3.554       | 3.565      | 7.33        |
| remove_top3             | 7747.18             | 2973.63            | 2448.76      | 1377.8      | 1674.5     | 1583.33     |
| fold_O1                 | 14.802              | -4.684             | 2.572        | -1.597      | 11.177     | 7.459       |
| fold_O2                 | -8.612              | 20.385             | -8.224       | -8.391      | -2.565     | -2.579      |
| fold_O3                 | 9.83                | 2.547              | -0.363       | 30.475      | 23.429     | -1.243      |
| fold_O4                 | 8.812               | 3.435              | -1.698       | -13.463     | -6.93      | 3.525       |
| fold_O5                 | 34.868              | 3.719              | 52.533       | 20.237      | 15.461     | 12.84       |
| folds_pos               | 4                   | 4                  | 2            | 2           | 3          | 3           |
| y2022                   | -2161.65            | 5116.57            | -2064.34     | -2106.15    | -643.84    | -647.23     |
| max_dd                  | 7053.86             | 3058.93            | 11604.57     | 7911.34     | 7876.33    | 4061.67     |
| worst_day               | -2693.71            | -1632.74           | -2371.45     | -2507.96    | -4532.96   | -2268.73    |
| corr_main               | 0.457               | 0.257              | 0.292        | 0.413       | 0.478      | 0.363       |
| turnover_trades_per_day | 2.521               | 0.419              | 1.301        | 1.815       | 2.288      | 0.471       |
| peak_MES                | 1                   | 1                  | 4            | 4           | 1          | 1           |
| peak_MNQ                | 1                   | 1                  | 3            | 3           | 1          | 1           |
| peak_MYM                | 1                   | 1                  | 4            | 3           | 1          | 1           |
| peak_M2K                | 1                   | 1                  | 3            | 4           | 1          | 1           |
| peak_MNQ_total          | 6                   | 6                  | 6            | 6           | 6          | 6           |
| peak_MES_total          | 8                   | 8                  | 8            | 8           | 8          | 8           |
| margin_peak_approx      | 5400                | 5400               | 13900        | 16900       | 5400       | 5400        |
| main_avg_day            | 151.78              | 151.78             | 151.78       | 151.78      | 151.78     | 151.78      |
| main_max_dd             | 13936.302           | 13936.302          | 13936.302    | 13936.302   | 13936.302  | 13936.302   |
| main_worst              | -4666.44            | -4666.44           | -4666.44     | -4666.44    | -4666.44   | -4666.44    |
| main_ret_dd             | 0.011               | 0.011              | 0.011        | 0.011       | 0.011      | 0.011       |
| comb_avg_day            | 165.441             | 156.742            | 163.994      | 158.316     | 160.438    | 156.448     |
| comb_max_dd             | 18137.202           | 13979.562          | 17800.77     | 17555.02    | 17473.47   | 15299.842   |
| comb_worst              | -4948.607           | -4727.68           | -4706.68     | -5010.607   | -7799.587  | -4666.44    |
| comb_ret_dd             | 0.009               | 0.011              | 0.009        | 0.009       | 0.009      | 0.01        |
| bottom5_main            | -2491.903           | -2491.903          | -2491.903    | -2491.903   | -2491.903  | -2491.903   |
| bottom5_comb            | -2878.497           | -2536.539          | -2774.01     | -2790.966   | -2848.845  | -2551.961   |
| incr                    | 13.661              | 4.963              | 12.214       | 6.537       | 8.659      | 4.668       |
| STRESS_PASS             | True                | True               | False        | False       | False      | True        |
| ROUTE_A                 | False               | False              | False        | False       | False      | False       |
| ROUTE_A_STRONG          | False               | False              | False        | False       | False      | False       |
| ROUTE_B                 | False               | True               | False        | False       | False      | False       |
| ROUTE_C                 | False               | False              | False        | False       | False      | False       |
