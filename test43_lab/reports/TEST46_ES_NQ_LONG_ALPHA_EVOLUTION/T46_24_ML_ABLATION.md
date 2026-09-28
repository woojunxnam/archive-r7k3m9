# T46_24 ML ablation

|    | model   | dropped                |   rankIC |   taken |   total_pnl_taken |
|---:|:--------|:-----------------------|---------:|--------:|------------------:|
|  0 | RIDGE   | displacement/structure |    0.050 |     879 |          6938.290 |
|  1 | RIDGE   | regime                 |    0.023 |     758 |          5924.080 |
|  2 | RIDGE   | relative ES/NQ         |    0.022 |     895 |          -918.050 |
|  3 | RIDGE   | family id              |    0.041 |     935 |          2185.850 |
|  4 | RIDGE   | VWAP/time              |    0.043 |     871 |          2972.460 |
|  5 | HIST_GB | displacement/structure |   -0.007 |    1039 |        -11563.110 |
|  6 | HIST_GB | regime                 |    0.007 |     987 |         -7265.380 |
|  7 | HIST_GB | relative ES/NQ         |   -0.021 |    1020 |        -14246.800 |
|  8 | HIST_GB | family id              |   -0.016 |    1034 |        -10736.160 |
|  9 | HIST_GB | VWAP/time              |   -0.021 |     968 |        -10035.070 |

The linear model's value depends on the ES/NQ relative feature; tree models are negative with or without it.

