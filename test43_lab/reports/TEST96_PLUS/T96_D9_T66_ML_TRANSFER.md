# TEST96 D9 - T66 opening-state ML mechanism transfer

|    | module                 |   trades |   avg_day |   avg_day_2021 |   matched_A_day |   momentum_B_day |   folds_pos |   min_fold_n |   remove_top3 |   slip4_day |   delay1_day |   corr_to_main | STANDALONE_PASS   | PORTFOLIO_PASS   | DIVERSIFIER_PASS   |   label_base_rate |
|---:|:-----------------------|---------:|----------:|---------------:|----------------:|-----------------:|------------:|-------------:|--------------:|------------:|-------------:|---------------:|:------------------|:-----------------|:-------------------|------------------:|
|  0 | T66_ML_YM              |      238 |    -1.153 |         -1.475 |          -0.596 |            0.113 |           1 |           23 |     -2522.400 |      -1.563 |       -1.024 |          0.110 | False             | False            | False              |             0.247 |
|  1 | T66_ML_RTY             |      166 |    -0.422 |         -0.540 |          -0.211 |           -0.230 |           1 |           13 |     -1276.620 |      -0.708 |       -0.353 |          0.108 | False             | False            | False              |             0.271 |
|  2 | T66_ML_MNQ [REFERENCE] |      202 |     1.961 |          2.510 |           1.856 |            0.686 |           4 |           28 |      2245.240 |       1.613 |        1.819 |          0.201 | True              | False            | False              |             0.266 |

FRAGILITY FINDING (MNQ reference): adding the 8 sessions that the frozen TEST65 eligibility rule excludes (1729 vs 1721 training rows) changes 81 of 231 signals and turns the MNQ reference from +1.96 to -0.37 $/day.  The frozen T66 member of FIXED_CLUE_BASKET_V1 is therefore threshold-fragile; it is NOT modified (frozen), but this is recorded as a forward-shadow caveat.

