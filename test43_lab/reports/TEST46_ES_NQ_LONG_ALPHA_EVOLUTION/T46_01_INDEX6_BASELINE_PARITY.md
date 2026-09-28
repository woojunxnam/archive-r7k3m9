# T46_01 INDEX6 baseline parity

Predeclared rule: over sessions 2019-09-03..2026-05-27 with full canonical coverage, PASS requires recall >= 98%, precision >= 98% and offset-consistent entry price within 1 tick for >= 95%.

|    | seed   |   ledger_entries_window |   engine_entries_window |   matched |   ledger_recall |   engine_precision |   price_within_1tick_share |   median_abs_price_diff | PARITY   |
|---:|:-------|------------------------:|------------------------:|----------:|----------------:|-------------------:|---------------------------:|------------------------:|:---------|
|  0 | LC02   |                     176 |                     180 |       176 |           1.000 |              0.978 |                      0.977 |                   0.000 | BLOCKED  |
|  1 | LC03   |                     198 |                     195 |       192 |           0.970 |              0.985 |                      0.771 |                   0.250 | BLOCKED  |
|  2 | LC05   |                     602 |                     586 |       405 |           0.673 |              0.691 |                      0.731 |                   0.250 | BLOCKED  |

|    | seed             | status                                                                                |
|---:|:-----------------|:--------------------------------------------------------------------------------------|
|  0 | LC02 ES-VOR      | PARITY_BLOCKED (recall 1.00, precision 0.978 < 0.98)                                  |
|  1 | LC03 NQ-NOON     | PARITY_BLOCKED (recall 0.970)                                                         |
|  2 | LC05 NQ-PDH      | PARITY_BLOCKED (0.67: RVOL/VWAP need NQ volume; canonical is MNQ)                     |
|  3 | TS16-S01 NQ-OI   | PARITY_BLOCKED (no OI data) + LIVE-SAFETY HOLD                                        |
|  4 | TS22-S01 NQ-SNAP | PARITY_BLOCKED (ledger not retrievable: Drive session failures)                       |
|  5 | T30-W01 NQ-COMP  | PARITY_BLOCKED (requires YM1!/RTY1! cross-market context; W01 filter not recoverable) |

INDEX6_PARITY_PASS = NO. LC02 misses by 0.2 pp of precision; the rule is not relaxed after the fact.

