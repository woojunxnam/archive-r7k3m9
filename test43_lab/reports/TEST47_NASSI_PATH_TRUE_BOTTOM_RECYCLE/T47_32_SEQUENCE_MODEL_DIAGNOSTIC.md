# T47_32 Sequence model diagnostic (small 1D CNN)

|    | task   | model                  |    n |   taken |   taken_pnl |   years_pos |   rankIC |   calib_slope |   top_decile_y |   bottom_decile_y |    all_pnl |   incr_vs_take_all |   taken_maxdd |   years |   cost_taken |   first_fold_train_n |
|---:|:-------|:-----------------------|-----:|--------:|------------:|------------:|---------:|--------------:|---------------:|------------------:|-----------:|-------------------:|--------------:|--------:|-------------:|---------------------:|
| 33 | SEQ    | SEQ_CNN_1D (24x3 bars) | 4587 |    2043 |  -15735.570 |           1 |   -0.028 |         0.081 |         -0.008 |             0.003 | -38545.880 |          22810.310 |     16488.980 |   6.000 |     6079.320 |             1280.000 |

Predeclared rule: justified only if first-fold training >= 2000 events AND it beats the best tabular model on outer rank IC and taken P&L. Rank IC < 0 -> SEQUENCE_MODEL_JUSTIFIED = NO.

