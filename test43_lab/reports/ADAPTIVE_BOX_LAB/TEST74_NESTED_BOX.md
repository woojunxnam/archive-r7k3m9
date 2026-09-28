# TEST74 - nested box alignment

{'small': 'A_OBS15_LIFE30', 'medium': 'A_OBS60_LIFE120', 'large': 'E_PREV_HL', 'aligned': 'touch close in the lower half [0, 0.5) of the box in force', 'variants': ['SMALL_ONLY', 'SMALL+MEDIUM', 'SMALL+LARGE', 'SMALL+MEDIUM+LARGE'], 'metric': 'bottom-trade net $/day, matched excess $/day, folds', 'note': 'hierarchy fixed by the program preregistration; no other hierarchy is searched', 'budget': {'hypotheses': 8}}

|    | instrument   | variant            |   events |   net_per_event |   excess_per_event |   net_day |   excess_day |   net4_day |   top_before_break |   folds_net_pos |   folds_x_pos |
|---:|:-------------|:-------------------|---------:|----------------:|-------------------:|----------:|-------------:|-----------:|-------------------:|----------------:|--------------:|
|  0 | MNQ          | SMALL_ONLY         |    11840 |          -2.210 |             -0.184 |   -15.031 |       -1.253 |    -35.433 |              0.193 |               0 |             2 |
|  1 | MNQ          | SMALL+MEDIUM       |     3468 |          -1.917 |              0.261 |    -3.818 |        0.520 |     -9.794 |              0.196 |               0 |             4 |
|  2 | MNQ          | SMALL+LARGE        |     2690 |          -3.249 |             -1.198 |    -5.019 |       -1.851 |     -9.655 |              0.183 |               0 |             2 |
|  3 | MNQ          | SMALL+MEDIUM+LARGE |      827 |          -4.115 |             -1.773 |    -1.955 |       -0.842 |     -3.380 |              0.173 |               1 |             1 |
|  4 | ES           | SMALL_ONLY         |    12176 |          -3.710 |             -0.101 |   -25.946 |       -0.704 |    -78.399 |              0.197 |               0 |             2 |
|  5 | ES           | SMALL+MEDIUM       |     3495 |          -3.582 |              0.165 |    -7.191 |        0.331 |    -22.247 |              0.198 |               0 |             2 |
|  6 | ES           | SMALL+LARGE        |     2830 |          -4.207 |             -0.578 |    -6.839 |       -0.939 |    -19.030 |              0.186 |               0 |             2 |
|  7 | ES           | SMALL+MEDIUM+LARGE |      902 |          -4.292 |             -0.340 |    -2.223 |       -0.176 |     -6.109 |              0.181 |               0 |             2 |

