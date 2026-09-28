# T47_40 Execution stress

No candidate survived the standalone gate; stress is reported on C2 / C4 / C6 for documentation.

|    | inst   | candidate   | stress                      |   avg_day |   delta_vs_base |      total |
|---:|:-------|:------------|:----------------------------|----------:|----------------:|-----------:|
|  0 | ES     | C2          | base                        |    -3.989 |           0.000 |  -5425.370 |
|  1 | ES     | C2          | +1 bar entry delay          |    -3.603 |           0.386 |  -4900.370 |
|  2 | ES     | C2          | 4-tick slippage             |    -7.921 |          -3.932 | -10772.870 |
|  3 | ES     | C2          | missed initial entry 20%    |    -3.448 |           0.541 |  -4688.940 |
|  4 | ES     | C2          | missed second add 50%       |    -3.989 |           0.000 |  -5425.370 |
|  5 | ES     | C2          | missed trim 50%             |    -3.989 |           0.000 |  -5425.370 |
|  6 | ES     | C2          | next-bar confirmation delay |    -4.914 |          -0.925 |  -6682.870 |
|  7 | ES     | C4          | base                        |    -3.033 |           0.000 |  -4125.500 |
|  8 | ES     | C4          | +1 bar entry delay          |    -2.349 |           0.685 |  -3194.340 |
|  9 | ES     | C4          | 4-tick slippage             |    -6.894 |          -3.860 |  -9375.500 |
| 10 | ES     | C4          | missed initial entry 20%    |    -2.218 |           0.815 |  -3016.640 |
| 11 | ES     | C4          | missed second add 50%       |    -3.033 |           0.000 |  -4125.500 |
| 12 | ES     | C4          | missed trim 50%             |    -3.033 |           0.000 |  -4125.500 |
| 13 | ES     | C4          | next-bar confirmation delay |    -3.619 |          -0.586 |  -4921.840 |
| 14 | ES     | C6          | base                        |    -3.849 |           0.000 |  -5235.180 |
| 15 | ES     | C6          | +1 bar entry delay          |    -1.629 |           2.221 |  -2215.250 |
| 16 | ES     | C6          | 4-tick slippage             |    -9.265 |          -5.415 | -12600.180 |
| 17 | ES     | C6          | missed initial entry 20%    |    -4.782 |          -0.932 |  -6503.170 |
| 18 | ES     | C6          | missed second add 50%       |    -3.684 |           0.165 |  -5010.240 |
| 19 | ES     | C6          | missed trim 50%             |    -3.641 |           0.209 |  -4951.430 |
| 20 | ES     | C6          | next-bar confirmation delay |    -3.421 |           0.428 |  -4652.750 |
| 21 | MNQ    | C2          | base                        |    -3.794 |           0.000 |  -5159.280 |
| 22 | MNQ    | C2          | +1 bar entry delay          |    -3.219 |           0.575 |  -4377.280 |
| 23 | MNQ    | C2          | 4-tick slippage             |    -5.386 |          -1.593 |  -7325.280 |
| 24 | MNQ    | C2          | missed initial entry 20%    |    -0.923 |           2.870 |  -1255.640 |
| 25 | MNQ    | C2          | missed second add 50%       |    -3.794 |           0.000 |  -5159.280 |
| 26 | MNQ    | C2          | missed trim 50%             |    -3.794 |           0.000 |  -5159.280 |
| 27 | MNQ    | C2          | next-bar confirmation delay |    -3.749 |           0.044 |  -5099.280 |
| 28 | MNQ    | C4          | base                        |    -6.198 |           0.000 |  -8429.320 |
| 29 | MNQ    | C4          | +1 bar entry delay          |    -2.569 |           3.629 |  -3494.100 |
| 30 | MNQ    | C4          | 4-tick slippage             |    -7.782 |          -1.584 | -10583.320 |
| 31 | MNQ    | C4          | missed initial entry 20%    |    -3.845 |           2.353 |  -5229.240 |
| 32 | MNQ    | C4          | missed second add 50%       |    -6.198 |           0.000 |  -8429.320 |
| 33 | MNQ    | C4          | missed trim 50%             |    -6.198 |           0.000 |  -8429.320 |
| 34 | MNQ    | C4          | next-bar confirmation delay |    -3.095 |           3.103 |  -4209.100 |
| 35 | MNQ    | C6          | base                        |    -6.039 |           0.000 |  -8212.820 |
| 36 | MNQ    | C6          | +1 bar entry delay          |     0.527 |           6.566 |    717.320 |
| 37 | MNQ    | C6          | 4-tick slippage             |    -8.284 |          -2.246 | -11266.820 |
| 38 | MNQ    | C6          | missed initial entry 20%    |    -3.057 |           2.982 |  -4157.680 |
| 39 | MNQ    | C6          | missed second add 50%       |    -6.330 |          -0.292 |  -8609.340 |
| 40 | MNQ    | C6          | missed trim 50%             |    -5.303 |           0.736 |  -7212.320 |
| 41 | MNQ    | C6          | next-bar confirmation delay |    -0.213 |           5.826 |   -289.680 |

