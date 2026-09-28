# TEST96 Track B - B0-B5 (RESEARCH_ONLY_APPROX, prereg ad9240b7)

All members are RESEARCH_ONLY_APPROX (none passes the frozen parity rule) -> results cannot authorize; SELECTION-BIASED.

|      | inst   |   trades_kept |   trades_in |   avg_day |   avg_day_2021 |   slip4_day |   corr_to_main |   max_dd |
|:-----|:-------|--------------:|------------:|----------:|---------------:|------------:|---------------:|---------:|
| LC02 | MES    |           189 |         192 |     0.429 |          1.028 |      -0.385 |          0.110 |  864.430 |
| LC03 | MNQ    |           167 |         210 |     1.640 |          2.036 |       1.352 |          0.091 |  451.280 |
| LC05 | MNQ    |           552 |         646 |     0.575 |          1.097 |      -0.376 |          0.271 | 2595.400 |

|    | candidate            |   avg_day |   incr_avg_day |   incr_avg_day_2021 |    max_dd |   worst_day |   ret_dd |   ret_dd_2021 |   corr_add_to_main |   loss_jaccard | PORTFOLIO_PASS_IF_EXACT   |
|---:|:---------------------|----------:|---------------:|--------------------:|----------:|------------:|---------:|--------------:|-------------------:|---------------:|:--------------------------|
|  0 | B0_MAIN              |   143.207 |          0.000 |               0.000 | 13936.302 |   -4666.440 |    0.010 |         0.011 |            nan     |        nan     |                           |
|  1 | B1_MAIN+INDEX_APPROX |   145.851 |          2.644 |               4.161 | 13229.192 |   -4666.440 |    0.011 |         0.012 |              0.287 |          0.324 | False                     |

