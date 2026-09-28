# T46_06 Strategy-specific overnight

**Lane A is RESEARCH-ONLY: every INDEX6 seed is PARITY_BLOCKED (T46_01); nothing in Lane A can be promoted.**

|    | seed                                           |   n |   raw_carry_avg_$ |   matched_control_carry_$ |   strategy_conditioned_excess_$ |   excess_t |   pre2023_excess |   2023+_excess |
|---:|:-----------------------------------------------|----:|------------------:|--------------------------:|--------------------------------:|-----------:|-----------------:|---------------:|
|  0 | LC02 ES-VOR                                    | 183 |            13.559 |                     3.885 |                           9.613 |      0.993 |            9.982 |          9.332 |
|  1 | LC03 NQ-NOON                                   | 205 |            16.319 |                    15.398 |                           0.893 |      0.050 |           45.050 |        -43.698 |
|  2 | LC05 NQ-PDH                                    | 623 |            17.118 |                    11.430 |                           5.757 |      0.612 |            3.546 |          7.837 |
|  3 | T30-L1 NQ-COMP(base, W01 filter unrecoverable) | 478 |            19.647 |                    10.808 |                           8.730 |      0.787 |           18.492 |         -3.941 |

Answer: carry conditioned on an active seed does not beat matched unconditional carry significantly (all |t| <= 1).

