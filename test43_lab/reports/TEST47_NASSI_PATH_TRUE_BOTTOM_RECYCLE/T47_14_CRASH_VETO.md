# T47_14 Crash / acceleration veto

|    | inst   | veto                   | side   |   trades |   avg_trade |   excess_trade |   t_excess |   folds_pos |
|---:|:-------|:-----------------------|:-------|---------:|------------:|---------------:|-----------:|------------:|
|  0 | ES     | no veto                | kept   |      949 |      -8.170 |         -4.595 |     -1.426 |           0 |
|  1 | ES     | accel                  | kept   |      880 |      -8.457 |         -4.890 |     -1.503 |           0 |
|  2 | ES     | accel                  | vetoed |      102 |      11.186 |         14.614 |      1.429 |           2 |
|  3 | ES     | cum>=10                | kept   |      941 |      -7.846 |         -4.211 |     -1.327 |           0 |
|  4 | ES     | cum>=10                | vetoed |       13 |     -51.817 |        -50.385 |     -1.235 |           1 |
|  5 | ES     | gap<=-1.5              | kept   |      920 |      -7.345 |         -3.792 |     -1.149 |           0 |
|  6 | ES     | gap<=-1.5              | vetoed |       29 |     -34.343 |        -30.083 |     -2.511 |           1 |
|  7 | ES     | ret5<=-3               | kept   |      880 |     -10.263 |         -6.698 |     -2.241 |           0 |
|  8 | ES     | ret5<=-3               | vetoed |       69 |      18.524 |         22.216 |      0.990 |           5 |
|  9 | ES     | vol>=0.9               | kept   |      829 |     -12.878 |         -9.393 |     -3.262 |           0 |
| 10 | ES     | vol>=0.9               | vetoed |      120 |      24.354 |         28.550 |      1.857 |           2 |
| 11 | ES     | ANY (predeclared veto) | kept   |      702 |     -12.663 |         -9.180 |     -3.007 |           0 |
| 12 | ES     | ANY (predeclared veto) | vetoed |      277 |       5.434 |          9.222 |      1.199 |           4 |
| 13 | MNQ    | no veto                | kept   |      985 |      -4.909 |         -3.219 |     -0.644 |           1 |
| 14 | MNQ    | accel                  | kept   |      926 |      -4.714 |         -2.988 |     -0.582 |           1 |
| 15 | MNQ    | accel                  | vetoed |       86 |     -11.967 |         -8.740 |     -0.482 |           1 |
| 16 | MNQ    | cum>=10                | kept   |      980 |      -4.302 |         -2.594 |     -0.522 |           1 |
| 17 | MNQ    | cum>=10                | vetoed |        8 |     -74.303 |        -78.702 |     -0.954 |           0 |
| 18 | MNQ    | gap<=-1.5              | kept   |      974 |      -5.270 |         -3.591 |     -0.712 |           1 |
| 19 | MNQ    | gap<=-1.5              | vetoed |       11 |      27.078 |         29.710 |      1.022 |           2 |
| 20 | MNQ    | ret5<=-3               | kept   |      925 |      -7.989 |         -6.559 |     -1.325 |           1 |
| 21 | MNQ    | ret5<=-3               | vetoed |       60 |      42.577 |         48.282 |      1.647 |           5 |
| 22 | MNQ    | vol>=0.9               | kept   |      847 |      -8.147 |         -7.173 |     -1.378 |           1 |
| 23 | MNQ    | vol>=0.9               | vetoed |      138 |      14.967 |         21.053 |      1.347 |           2 |
| 24 | MNQ    | ANY (predeclared veto) | kept   |      756 |      -8.809 |         -7.892 |     -1.471 |           1 |
| 25 | MNQ    | ANY (predeclared veto) | vetoed |      254 |       3.205 |          7.730 |      0.690 |           3 |

The vetoed (extreme) subsets are small and are NOT promoted: an ex-post observation that extreme states rebounded more would be a NEW HYPOTHESIS (shadow research only, TEST47 §60).

