# TEST96 D4 - C43 mechanism portability (Stage A normalised)

Structural audit: C43 sleeves are regime-tiered long-exposure allocators on 3m bars (daily trend tier -> target fraction of a contract cap, buy window, overnight carry, VWAP-z trims, DD / day-stop governors).  Mechanism logic is portable; ES/NQ-specific constants = dollar governor levels and contract caps (normalised by $ATR ratio).  PASS rule for C43_PORTABLE: sum-of-sleeves net > 0, excess vs exposure-matched long > 0, >= 4/5 folds, remove-top3 > 0.

|    | sleeve                          |   k_$ATR |   avg_day |   avg_day_2021 |   excess_vs_exposure_matched_long_day |     max_dd |      worst |   folds_pos |   avg_pos |   corr_to_main |   remove_top3 |   main_plus_ret_dd |   main_ret_dd |   main_plus_maxdd |   main_maxdd |
|---:|:--------------------------------|---------:|----------:|---------------:|--------------------------------------:|-----------:|-----------:|------------:|----------:|---------------:|--------------:|-------------------:|--------------:|------------------:|-------------:|
|  0 | C43_MECH_YM:MNQ_arch_A_AGG_0    |    0.527 |     2.322 |          4.791 |                               -13.771 |  17433.440 |  -1826.900 |           3 |     2.370 |          0.396 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  1 | C43_MECH_YM:MNQ_robust_A_MOD_2  |    0.527 |    -1.592 |         -0.614 |                               -41.441 |  35904.880 |  -1805.860 |           3 |     3.029 |          0.403 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  2 | C43_MECH_YM:MNQ_r2_C_MOD_1      |    0.527 |    -1.303 |         -4.821 |                                -0.853 |  23062.680 |  -2264.480 |           3 |     2.734 |          0.497 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  3 | C43_MECH_YM:MNQ_robust_C_CON_0  |    0.527 |     4.306 |          4.858 |                                -1.469 |   7989.400 |  -2240.720 |           3 |     0.441 |          0.276 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  4 | C43_MECH_YM:ES_robust_A_MOD_1   |    0.882 |    10.231 |          5.541 |                               -20.374 |  26378.620 |  -4050.540 |           2 |     3.670 |          0.422 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  5 | C43_MECH_YM:ES_r2_F_MOD_2       |    0.882 |    -0.293 |          1.750 |                                -6.225 |  19604.880 |  -2890.960 |           3 |     3.002 |          0.513 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  6 | C43_MECH_YM:ES_r2_A_CON_1       |    0.882 |    15.238 |         16.948 |                                 3.799 |   6625.320 |  -2096.500 |           4 |     2.020 |          0.555 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  7 | C43_MECH_YM:ES_robust_C_CON_4   |    0.882 |    10.965 |         12.685 |                                -0.325 |   9809.420 |  -1848.980 |           4 |     2.306 |          0.542 |       nan     |            nan     |       nan     |           nan     |      nan     |
|  8 | C43_MECH_YM (sum of 8)          |  nan     |    39.874 |         41.137 |                               -80.658 |  99877.860 | -13484.160 |           3 |   nan     |          0.584 |     19111.320 |              0.003 |         0.010 |         65017.420 |    13936.302 |
|  9 | C43_MECH_RTY:MNQ_arch_A_AGG_0   |    0.435 |   -18.273 |        -16.529 |                               -18.565 |  37391.000 |  -1260.880 |           1 |     1.754 |          0.333 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 10 | C43_MECH_RTY:MNQ_robust_A_MOD_2 |    0.435 |   -24.583 |        -23.061 |                               -39.509 |  52454.600 |  -3494.320 |           0 |     2.276 |          0.285 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 11 | C43_MECH_RTY:MNQ_r2_C_MOD_1     |    0.435 |   -10.827 |        -15.499 |                                -6.191 |  30054.180 |  -2057.100 |           1 |     2.314 |          0.349 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 12 | C43_MECH_RTY:MNQ_robust_C_CON_0 |    0.435 |     2.404 |          1.848 |                                -1.469 |  15197.940 |  -3927.220 |           3 |     1.873 |          0.412 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 13 | C43_MECH_RTY:ES_robust_A_MOD_1  |    0.728 |    12.267 |         13.600 |                               -23.845 |  27949.400 |  -2453.520 |           3 |     3.726 |          0.393 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 14 | C43_MECH_RTY:ES_r2_F_MOD_2      |    0.728 |     4.476 |          0.567 |                                -1.442 |  18218.620 |  -2891.320 |           3 |     3.396 |          0.478 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 15 | C43_MECH_RTY:ES_r2_A_CON_1      |    0.728 |     5.502 |          4.226 |                                -3.091 |  15135.260 |  -3519.000 |           4 |     2.660 |          0.463 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 16 | C43_MECH_RTY:ES_robust_C_CON_4  |    0.728 |     2.787 |          0.881 |                                -3.678 |  19417.500 |  -1995.360 |           3 |     2.588 |          0.452 |       nan     |            nan     |       nan     |           nan     |      nan     |
| 17 | C43_MECH_RTY (sum of 8)         |  nan     |   -26.246 |        -33.966 |                               -97.790 | 148038.120 | -15684.300 |           3 |   nan     |          0.498 |    -92342.800 |              0.001 |         0.010 |        100518.826 |    13936.302 |


## Reference on source instruments

Reference (same excess measure on the ORIGINAL ES / MNQ sleeves, data <= 2026-05-27): excess vs exposure-matched long per sleeve
MNQ_arch_A_AGG_0 -36.0, MNQ_robust_A_MOD_2 -3.8, MNQ_r2_C_MOD_1 +1.6, MNQ_robust_C_CON_0 +4.5, ES_robust_A_MOD_1 +0.3, ES_r2_F_MOD_2 +1.7,
ES_r2_A_CON_1 +4.0, ES_robust_C_CON_4 -2.2 $/day -> C43's value at source is predominantly managed long exposure (beta + governors), not a
timing edge; its portable 'mechanism' is therefore mostly beta, which on YM / RTY adds correlated drawdown.

C43_PORTABLE_TO_YM = NO (sum excess vs exposure-matched long < 0; 4/8 sleeves negative net)
C43_PORTABLE_TO_RTY = NO (sum net negative)
