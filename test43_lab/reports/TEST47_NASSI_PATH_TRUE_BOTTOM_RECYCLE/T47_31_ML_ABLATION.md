# T47_31 ML ablation

|    | model   | dropped                                                     |   rankIC |   taken_pnl |
|---:|:--------|:------------------------------------------------------------|---------:|------------:|
|  0 | RIDGE   | path shape (legs, ratios, cum, dur, vel, neutral, rec, nup) |   -0.003 |  -17030.030 |
|  1 | RIDGE   | bar structure (wick, body, cloc)                            |    0.003 |  -11413.750 |
|  2 | RIDGE   | 15m context                                                 |   -0.007 |  -14790.760 |
|  3 | RIDGE   | regime (gap, ret5, volt, bull, rv5, u5atr)                  |   -0.024 |  -22597.810 |
|  4 | RIDGE   | location (tod, dopen, dtwap, rally)                         |    0.020 |  -12263.700 |
|  5 | RIDGE   | ONLY path shape kept                                        |   -0.022 |  -26437.470 |
|  6 | HIST_GB | path shape (legs, ratios, cum, dur, vel, neutral, rec, nup) |   -0.025 |  -26795.080 |
|  7 | HIST_GB | bar structure (wick, body, cloc)                            |   -0.016 |  -18162.830 |
|  8 | HIST_GB | 15m context                                                 |   -0.038 |  -27227.990 |
|  9 | HIST_GB | regime (gap, ret5, volt, bull, rv5, u5atr)                  |   -0.017 |  -23191.780 |
| 10 | HIST_GB | location (tod, dopen, dtwap, rally)                         |   -0.035 |  -26065.900 |
| 11 | HIST_GB | ONLY path shape kept                                        |   -0.018 |  -19525.880 |

