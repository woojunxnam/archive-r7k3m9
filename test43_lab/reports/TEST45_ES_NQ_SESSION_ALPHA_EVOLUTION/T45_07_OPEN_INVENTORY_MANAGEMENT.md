# T45_07 Open inventory management

An existing overnight long (1 contract). Value of each action relative to EXIT at the open print ($ per contract, net of incremental cost).

|     | inst   | state                     | action_vs_EXIT_AT_OPEN                         |    n |   mean$ |   median$ |      t |       p5$ |    worst$ |
|----:|:-------|:--------------------------|:-----------------------------------------------|-----:|--------:|----------:|-------:|----------:|----------:|
|   0 | ES     | favorable gap (>+0.25)    | KEEP -> exit after 1m                          |  508 |  -1.137 |     0.000 | -1.580 |   -27.062 |   -63.750 |
|   1 | ES     | favorable gap (>+0.25)    | KEEP -> exit after 5m                          |  508 |  -1.334 |    -1.250 | -0.959 |   -53.312 |  -112.500 |
|   2 | ES     | favorable gap (>+0.25)    | KEEP -> exit after 15m                         |  508 |  -1.720 |    -2.500 | -0.779 |   -80.750 |  -211.250 |
|   3 | ES     | favorable gap (>+0.25)    | KEEP -> exit after 30m                         |  506 |   1.512 |     1.250 |  0.506 |  -103.438 |  -320.000 |
|   4 | ES     | favorable gap (>+0.25)    | KEEP -> exit after 60m                         |  506 |   4.331 |     7.500 |  1.060 |  -142.500 |  -336.250 |
|   5 | ES     | favorable gap (>+0.25)    | KEEP -> exit 12:00                             |  508 |  -0.376 |     9.375 | -0.066 |  -227.375 |  -615.000 |
|   6 | ES     | favorable gap (>+0.25)    | KEEP -> exit 15:00                             |  507 |   1.985 |    17.500 |  0.264 |  -305.875 |  -996.250 |
|   7 | ES     | favorable gap (>+0.25)    | KEEP -> exit 16:00                             |  507 |  -3.402 |    23.750 | -0.402 |  -338.000 | -1317.500 |
|   8 | ES     | favorable gap (>+0.25)    | ADD +1 after 1m -> exit both 16:00             |  507 |  -9.359 |    46.260 | -0.555 |  -693.740 | -2641.240 |
|   9 | ES     | favorable gap (>+0.25)    | (no overnight) ENTER 1 after 1m -> exit 16:00  |  507 |  -5.956 |    22.510 | -0.709 |  -347.615 | -1323.740 |
|  10 | ES     | favorable gap (>+0.25)    | ADD +1 after 15m -> exit both 16:00            |  507 |  -8.718 |    46.260 | -0.530 |  -668.865 | -2529.990 |
|  11 | ES     | favorable gap (>+0.25)    | (no overnight) ENTER 1 after 15m -> exit 16:00 |  507 |  -5.315 |    20.010 | -0.654 |  -326.740 | -1212.490 |
|  12 | ES     | favorable gap (>+0.25)    | ADD +1 after 30m -> exit both 16:00            |  505 | -12.141 |    40.010 | -0.744 |  -664.740 | -2679.990 |
|  13 | ES     | favorable gap (>+0.25)    | (no overnight) ENTER 1 after 30m -> exit 16:00 |  505 |  -8.614 |    13.760 | -1.064 |  -328.490 | -1362.490 |
|  14 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit after 1m                          |  847 |   1.014 |     1.250 |  1.707 |   -26.250 |  -106.250 |
|  15 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit after 5m                          |  847 |  -0.264 |     0.000 | -0.247 |   -49.625 |  -166.250 |
|  16 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit after 15m                         |  847 |  -0.301 |     1.250 | -0.179 |   -72.125 |  -288.750 |
|  17 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit after 30m                         |  842 |   2.013 |     5.000 |  0.915 |  -100.000 |  -336.250 |
|  18 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit after 60m                         |  841 |   1.746 |     3.750 |  0.592 |  -132.500 |  -385.000 |
|  19 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit 12:00                             |  847 |   3.589 |     8.750 |  0.885 |  -204.625 |  -516.250 |
|  20 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit 15:00                             |  834 |   7.654 |     5.000 |  1.307 |  -252.938 |  -762.500 |
|  21 | ES     | neutral (-0.25..+0.25]    | KEEP -> exit 16:00                             |  834 |   5.727 |     4.375 |  0.841 |  -289.188 |  -958.750 |
|  22 | ES     | neutral (-0.25..+0.25]    | ADD +1 after 1m -> exit both 16:00             |  834 |   6.668 |     2.510 |  0.492 |  -580.490 | -1913.740 |
|  23 | ES     | neutral (-0.25..+0.25]    | (no overnight) ENTER 1 after 1m -> exit 16:00  |  834 |   0.941 |     0.010 |  0.139 |  -290.865 |  -954.990 |
|  24 | ES     | neutral (-0.25..+0.25]    | ADD +1 after 15m -> exit both 16:00            |  834 |   8.213 |     8.760 |  0.618 |  -552.928 | -1993.740 |
|  25 | ES     | neutral (-0.25..+0.25]    | (no overnight) ENTER 1 after 15m -> exit 16:00 |  834 |   2.486 |     4.385 |  0.377 |  -285.490 | -1034.990 |
|  26 | ES     | neutral (-0.25..+0.25]    | ADD +1 after 30m -> exit both 16:00            |  829 |   6.179 |     8.760 |  0.474 |  -537.990 | -1964.990 |
|  27 | ES     | neutral (-0.25..+0.25]    | (no overnight) ENTER 1 after 30m -> exit 16:00 |  829 |   0.369 |     6.260 |  0.058 |  -258.240 | -1006.240 |
|  28 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit after 1m                          |  283 |   3.105 |     3.750 |  2.852 |   -26.125 |   -88.750 |
|  29 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit after 5m                          |  283 |   5.115 |     5.000 |  2.622 |   -47.375 |  -106.250 |
|  30 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit after 15m                         |  283 |  -0.393 |     3.750 | -0.119 |   -92.250 |  -200.000 |
|  31 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit after 30m                         |  283 |   0.733 |     6.250 |  0.163 |  -123.500 |  -283.750 |
|  32 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit after 60m                         |  283 |  -3.008 |     6.250 | -0.505 |  -162.375 |  -325.000 |
|  33 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit 12:00                             |  283 |  -5.477 |     2.500 | -0.610 |  -232.125 |  -676.250 |
|  34 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit 15:00                             |  282 |   3.595 |    20.000 |  0.337 |  -312.438 |  -627.500 |
|  35 | ES     | adverse (-0.75..-0.25]    | KEEP -> exit 16:00                             |  282 |  11.290 |    18.750 |  1.006 |  -329.750 |  -578.750 |
|  36 | ES     | adverse (-0.75..-0.25]    | ADD +1 after 1m -> exit both 16:00             |  282 |  15.715 |    33.135 |  0.703 |  -656.928 | -1152.490 |
|  37 | ES     | adverse (-0.75..-0.25]    | (no overnight) ENTER 1 after 1m -> exit 16:00  |  282 |   4.425 |     8.760 |  0.397 |  -324.802 |  -573.740 |
|  38 | ES     | adverse (-0.75..-0.25]    | ADD +1 after 15m -> exit both 16:00            |  282 |  19.225 |    38.135 |  0.893 |  -622.428 | -1083.740 |
|  39 | ES     | adverse (-0.75..-0.25]    | (no overnight) ENTER 1 after 15m -> exit 16:00 |  282 |   7.936 |    20.635 |  0.753 |  -316.115 |  -504.990 |
|  40 | ES     | adverse (-0.75..-0.25]    | ADD +1 after 30m -> exit both 16:00            |  282 |  18.126 |    34.385 |  0.858 |  -570.865 | -1043.740 |
|  41 | ES     | adverse (-0.75..-0.25]    | (no overnight) ENTER 1 after 30m -> exit 16:00 |  282 |   6.836 |    13.135 |  0.659 |  -284.490 |  -517.490 |
|  42 | ES     | extreme adverse (<=-0.75) | KEEP -> exit after 1m                          |   97 |   1.959 |     1.250 |  0.706 |   -45.500 |   -55.000 |
|  43 | ES     | extreme adverse (<=-0.75) | KEEP -> exit after 5m                          |   97 |   5.168 |     6.250 |  1.009 |   -74.750 |  -101.250 |
|  44 | ES     | extreme adverse (<=-0.75) | KEEP -> exit after 15m                         |   96 |  -4.648 |     6.875 | -0.528 |  -173.125 |  -358.750 |
|  45 | ES     | extreme adverse (<=-0.75) | KEEP -> exit after 30m                         |   98 |   5.816 |    -8.125 |  0.553 |  -140.938 |  -320.000 |
|  46 | ES     | extreme adverse (<=-0.75) | KEEP -> exit after 60m                         |   98 |   1.901 |    -6.250 |  0.140 |  -190.938 |  -376.250 |
|  47 | ES     | extreme adverse (<=-0.75) | KEEP -> exit 12:00                             |   98 |  25.765 |    21.250 |  1.402 |  -203.750 |  -433.750 |
|  48 | ES     | extreme adverse (<=-0.75) | KEEP -> exit 15:00                             |   96 |  10.234 |    -1.875 |  0.399 |  -307.812 |  -827.500 |
|  49 | ES     | extreme adverse (<=-0.75) | KEEP -> exit 16:00                             |   96 |   5.716 |    27.500 |  0.207 |  -402.812 |  -917.500 |
|  50 | ES     | extreme adverse (<=-0.75) | ADD +1 after 1m -> exit both 16:00             |   95 |  19.615 |    46.260 |  0.361 |  -811.865 | -1893.740 |
|  51 | ES     | extreme adverse (<=-0.75) | (no overnight) ENTER 1 after 1m -> exit 16:00  |   95 |   7.089 |    20.010 |  0.259 |  -406.990 |  -976.240 |
|  52 | ES     | extreme adverse (<=-0.75) | ADD +1 after 15m -> exit both 16:00            |   94 |  22.749 |    59.385 |  0.421 |  -810.052 | -1663.740 |
|  53 | ES     | extreme adverse (<=-0.75) | (no overnight) ENTER 1 after 15m -> exit 16:00 |   94 |  11.632 |     9.385 |  0.431 |  -375.990 |  -746.240 |
|  54 | ES     | extreme adverse (<=-0.75) | ADD +1 after 30m -> exit both 16:00            |   96 |   1.104 |    26.260 |  0.022 |  -751.865 | -1813.740 |
|  55 | ES     | extreme adverse (<=-0.75) | (no overnight) ENTER 1 after 30m -> exit 16:00 |   96 |  -4.612 |     7.510 | -0.193 |  -359.678 |  -896.240 |
|  56 | ES     | ALL                       | KEEP -> exit after 1m                          | 1735 |   0.778 |     1.250 |  1.808 |   -27.500 |  -106.250 |
|  57 | ES     | ALL                       | KEEP -> exit after 5m                          | 1735 |   0.604 |     0.000 |  0.763 |   -51.625 |  -166.250 |
|  58 | ES     | ALL                       | KEEP -> exit after 15m                         | 1734 |  -0.972 |     0.000 | -0.764 |   -85.438 |  -358.750 |
|  59 | ES     | ALL                       | KEEP -> exit after 30m                         | 1729 |   1.872 |     3.750 |  1.117 |  -113.750 |  -336.250 |
|  60 | ES     | ALL                       | KEEP -> exit after 60m                         | 1728 |   1.733 |     5.000 |  0.772 |  -152.062 |  -385.000 |
|  61 | ES     | ALL                       | KEEP -> exit 12:00                             | 1736 |   2.203 |     8.750 |  0.700 |  -219.062 |  -676.250 |
|  62 | ES     | ALL                       | KEEP -> exit 15:00                             | 1719 |   5.460 |    12.500 |  1.284 |  -287.750 |  -996.250 |
|  63 | ES     | ALL                       | KEEP -> exit 16:00                             | 1719 |   3.946 |    11.250 |  0.824 |  -312.000 | -1317.500 |
|  64 | ES     | ALL                       | ADD +1 after 1m -> exit both 16:00             | 1718 |   4.139 |    18.760 |  0.435 |  -631.990 | -2641.240 |
|  65 | ES     | ALL                       | (no overnight) ENTER 1 after 1m -> exit 16:00  | 1718 |  -0.183 |     7.510 | -0.038 |  -323.928 | -1323.740 |
|  66 | ES     | ALL                       | ADD +1 after 15m -> exit both 16:00            | 1717 |   5.818 |    23.760 |  0.625 |  -622.740 | -2529.990 |
|  67 | ES     | ALL                       | (no overnight) ENTER 1 after 15m -> exit 16:00 | 1717 |   1.578 |    11.260 |  0.343 |  -309.740 | -1212.490 |
|  68 | ES     | ALL                       | ADD +1 after 30m -> exit both 16:00            | 1712 |   2.458 |    23.135 |  0.269 |  -592.677 | -2679.990 |
|  69 | ES     | ALL                       | (no overnight) ENTER 1 after 30m -> exit 16:00 | 1712 |  -1.495 |    10.010 | -0.334 |  -299.177 | -1362.490 |
|  70 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit after 1m                          |  491 |  -1.930 |    -1.500 | -1.200 |   -60.500 |  -110.500 |
|  71 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit after 5m                          |  491 |  -3.468 |     0.000 | -1.092 |  -124.750 |  -287.000 |
|  72 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit after 15m                         |  491 |  -6.796 |     1.000 | -1.353 |  -212.000 |  -410.500 |
|  73 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit after 30m                         |  490 |  -1.851 |     2.750 | -0.289 |  -243.375 |  -664.500 |
|  74 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit after 60m                         |  490 |   0.505 |     5.750 |  0.061 |  -333.300 |  -693.000 |
|  75 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit 12:00                             |  491 |  -4.798 |     9.500 | -0.437 |  -451.000 | -1287.500 |
|  76 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit 15:00                             |  488 |  -7.122 |    13.750 | -0.494 |  -583.875 | -1652.500 |
|  77 | MNQ    | favorable gap (>+0.25)    | KEEP -> exit 16:00                             |  488 | -11.713 |    14.500 | -0.728 |  -639.275 | -2165.500 |
|  78 | MNQ    | favorable gap (>+0.25)    | ADD +1 after 1m -> exit both 16:00             |  488 | -23.680 |    40.010 | -0.744 | -1297.540 | -4270.240 |
|  79 | MNQ    | favorable gap (>+0.25)    | (no overnight) ENTER 1 after 1m -> exit 16:00  |  488 | -11.966 |    21.010 | -0.757 |  -643.340 | -2104.740 |
|  80 | MNQ    | favorable gap (>+0.25)    | ADD +1 after 15m -> exit both 16:00            |  488 | -18.506 |    44.260 | -0.606 | -1185.915 | -4333.740 |
|  81 | MNQ    | favorable gap (>+0.25)    | (no overnight) ENTER 1 after 15m -> exit 16:00 |  488 |  -6.793 |    23.510 | -0.458 |  -564.915 | -2168.240 |
|  82 | MNQ    | favorable gap (>+0.25)    | ADD +1 after 30m -> exit both 16:00            |  487 | -23.520 |    46.760 | -0.789 | -1161.140 | -4460.240 |
|  83 | MNQ    | favorable gap (>+0.25)    | (no overnight) ENTER 1 after 30m -> exit 16:00 |  487 | -11.615 |    17.260 | -0.811 |  -580.390 | -2294.740 |
|  84 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit after 1m                          |  863 |   1.412 |     1.500 |  1.163 |   -56.450 |  -150.500 |
|  85 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit after 5m                          |  863 |  -2.977 |    -2.500 | -1.315 |  -108.450 |  -288.500 |
|  86 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit after 15m                         |  863 |  -0.282 |     2.000 | -0.085 |  -163.350 |  -369.000 |
|  87 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit after 30m                         |  859 |   3.256 |    11.500 |  0.722 |  -218.300 |  -605.000 |
|  88 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit after 60m                         |  859 |   1.032 |     4.500 |  0.172 |  -277.650 |  -816.500 |
|  89 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit 12:00                             |  863 |   3.462 |    20.000 |  0.432 |  -413.850 |  -961.500 |
|  90 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit 15:00                             |  853 |  17.846 |    31.500 |  1.673 |  -486.600 | -1450.500 |
|  91 | MNQ    | neutral (-0.25..+0.25]    | KEEP -> exit 16:00                             |  853 |  14.503 |    31.500 |  1.199 |  -543.100 | -1817.000 |
|  92 | MNQ    | neutral (-0.25..+0.25]    | ADD +1 after 1m -> exit both 16:00             |  853 |  25.357 |    51.760 |  1.055 | -1089.140 | -3640.740 |
|  93 | MNQ    | neutral (-0.25..+0.25]    | (no overnight) ENTER 1 after 1m -> exit 16:00  |  853 |  10.854 |    19.760 |  0.906 |  -542.340 | -1823.740 |
|  94 | MNQ    | neutral (-0.25..+0.25]    | ADD +1 after 15m -> exit both 16:00            |  853 |  27.350 |    60.760 |  1.172 | -1092.540 | -3746.740 |
|  95 | MNQ    | neutral (-0.25..+0.25]    | (no overnight) ENTER 1 after 15m -> exit 16:00 |  853 |  12.847 |    26.260 |  1.121 |  -520.840 | -1929.740 |
|  96 | MNQ    | neutral (-0.25..+0.25]    | ADD +1 after 30m -> exit both 16:00            |  849 |  24.587 |    56.260 |  1.084 | -1066.640 | -3724.240 |
|  97 | MNQ    | neutral (-0.25..+0.25]    | (no overnight) ENTER 1 after 30m -> exit 16:00 |  849 |   9.799 |    22.260 |  0.894 |  -486.140 | -1907.240 |
|  98 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit after 1m                          |  298 |   3.606 |     2.750 |  1.508 |   -59.150 |  -140.500 |
|  99 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit after 5m                          |  298 |  10.091 |    15.500 |  2.248 |  -117.950 |  -268.000 |
| 100 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit after 15m                         |  298 |   2.797 |     9.500 |  0.404 |  -193.500 |  -369.500 |
| 101 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit after 30m                         |  298 |  -5.146 |     9.000 | -0.571 |  -280.650 |  -457.000 |
| 102 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit after 60m                         |  297 |  -7.924 |     6.000 | -0.670 |  -352.700 |  -709.500 |
| 103 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit 12:00                             |  298 |  -8.765 |    -2.500 | -0.542 |  -510.325 | -1006.500 |
| 104 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit 15:00                             |  295 |  -5.036 |    29.000 | -0.272 |  -544.350 | -1053.000 |
| 105 | MNQ    | adverse (-0.75..-0.25]    | KEEP -> exit 16:00                             |  295 |  12.337 |    28.500 |  0.642 |  -518.100 |  -999.500 |
| 106 | MNQ    | adverse (-0.75..-0.25]    | ADD +1 after 1m -> exit both 16:00             |  295 |  18.902 |    42.760 |  0.497 | -1046.740 | -1967.240 |
| 107 | MNQ    | adverse (-0.75..-0.25]    | (no overnight) ENTER 1 after 1m -> exit 16:00  |  295 |   6.565 |    20.260 |  0.348 |  -521.790 |  -967.740 |
| 108 | MNQ    | adverse (-0.75..-0.25]    | ADD +1 after 15m -> exit both 16:00            |  295 |  19.229 |    35.260 |  0.530 | -1031.190 | -1813.740 |
| 109 | MNQ    | adverse (-0.75..-0.25]    | (no overnight) ENTER 1 after 15m -> exit 16:00 |  295 |   6.892 |    23.260 |  0.389 |  -497.990 |  -863.240 |
| 110 | MNQ    | adverse (-0.75..-0.25]    | ADD +1 after 30m -> exit both 16:00            |  295 |  27.582 |    52.760 |  0.788 |  -940.290 | -1684.240 |
| 111 | MNQ    | adverse (-0.75..-0.25]    | (no overnight) ENTER 1 after 30m -> exit 16:00 |  295 |  15.245 |    24.760 |  0.903 |  -420.890 |  -860.240 |
| 112 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit after 1m                          |   83 |   8.934 |     6.000 |  1.416 |   -69.900 |  -198.000 |
| 113 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit after 5m                          |   83 |  13.578 |    19.500 |  1.055 |  -148.450 |  -349.500 |
| 114 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit after 15m                         |   82 |  10.579 |    27.000 |  0.574 |  -316.500 |  -371.500 |
| 115 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit after 30m                         |   84 |  49.411 |    47.500 |  2.134 |  -246.800 |  -417.000 |
| 116 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit after 60m                         |   83 |  51.416 |    28.000 |  1.819 |  -306.600 |  -474.000 |
| 117 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit 12:00                             |   84 |  82.232 |    29.250 |  2.151 |  -381.600 |  -730.000 |
| 118 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit 15:00                             |   83 |  56.873 |    31.000 |  1.196 |  -513.550 | -1077.500 |
| 119 | MNQ    | extreme adverse (<=-0.75) | KEEP -> exit 16:00                             |   83 |  28.404 |    19.500 |  0.540 |  -653.900 | -1203.000 |
| 120 | MNQ    | extreme adverse (<=-0.75) | ADD +1 after 1m -> exit both 16:00             |   82 |  66.888 |    34.760 |  0.644 | -1287.965 | -2484.240 |
| 121 | MNQ    | extreme adverse (<=-0.75) | (no overnight) ENTER 1 after 1m -> exit 16:00  |   82 |  28.126 |    19.760 |  0.543 |  -648.215 | -1281.240 |
| 122 | MNQ    | extreme adverse (<=-0.75) | ADD +1 after 15m -> exit both 16:00            |   81 |  60.204 |    39.760 |  0.596 | -1252.240 | -2157.740 |
| 123 | MNQ    | extreme adverse (<=-0.75) | (no overnight) ENTER 1 after 15m -> exit 16:00 |   81 |  23.735 |     6.760 |  0.483 |  -603.740 |  -954.740 |
| 124 | MNQ    | extreme adverse (<=-0.75) | ADD +1 after 30m -> exit both 16:00            |   83 |   4.856 |    10.260 |  0.052 | -1302.440 | -2491.740 |
| 125 | MNQ    | extreme adverse (<=-0.75) | (no overnight) ENTER 1 after 30m -> exit 16:00 |   83 | -23.547 |   -14.240 | -0.547 |  -605.240 | -1288.740 |
| 126 | MNQ    | ALL                       | KEEP -> exit after 1m                          | 1735 |   1.203 |     0.500 |  1.316 |   -59.500 |  -198.000 |
| 127 | MNQ    | ALL                       | KEEP -> exit after 5m                          | 1735 |  -0.080 |     2.000 | -0.046 |  -116.150 |  -349.500 |
| 128 | MNQ    | ALL                       | KEEP -> exit after 15m                         | 1734 |  -1.084 |     3.000 | -0.411 |  -190.875 |  -410.500 |
| 129 | MNQ    | ALL                       | KEEP -> exit after 30m                         | 1731 |   2.603 |     9.500 |  0.750 |  -244.750 |  -664.500 |
| 130 | MNQ    | ALL                       | KEEP -> exit after 60m                         | 1729 |   1.763 |     6.000 |  0.390 |  -314.800 |  -816.500 |
| 131 | MNQ    | ALL                       | KEEP -> exit 12:00                             | 1736 |   2.838 |    13.500 |  0.467 |  -445.625 | -1287.500 |
| 132 | MNQ    | ALL                       | KEEP -> exit 15:00                             | 1719 |   8.716 |    27.500 |  1.123 |  -534.950 | -1652.500 |
| 133 | MNQ    | ALL                       | KEEP -> exit 16:00                             | 1719 |   7.360 |    24.500 |  0.854 |  -588.600 | -2165.500 |
| 134 | MNQ    | ALL                       | ADD +1 after 1m -> exit both 16:00             | 1718 |  12.302 |    47.260 |  0.720 | -1155.915 | -4270.240 |
| 135 | MNQ    | ALL                       | (no overnight) ENTER 1 after 1m -> exit 16:00  | 1718 |   4.460 |    20.260 |  0.525 |  -568.665 | -2104.740 |
| 136 | MNQ    | ALL                       | ADD +1 after 15m -> exit both 16:00            | 1717 |  14.471 |    54.260 |  0.878 | -1130.640 | -4333.740 |
| 137 | MNQ    | ALL                       | (no overnight) ENTER 1 after 15m -> exit 16:00 | 1717 |   6.755 |    23.260 |  0.839 |  -536.040 | -2168.240 |
| 138 | MNQ    | ALL                       | ADD +1 after 30m -> exit both 16:00            | 1714 |  10.478 |    50.260 |  0.656 | -1080.840 | -4460.240 |
| 139 | MNQ    | ALL                       | (no overnight) ENTER 1 after 30m -> exit 16:00 | 1714 |   3.037 |    20.760 |  0.396 |  -514.915 | -2294.740 |

Answer: after a favourable gap, exit at the open. After an extreme adverse gap, keeping into late morning was positive for MNQ (t~2 at 30m-12:00; n~84). This is a single-cell observation. As overlay S6b it did not pass the account-level tests (T45_08/24).

