# T46_10 Blind DCA control

**Lane A is RESEARCH-ONLY: every INDEX6 seed is PARITY_BLOCKED (T46_01); nothing in Lane A can be promoted.**

Incremental P&L of the SECOND contract only (add fill -> original exit):

|    | seed                                           | rule                   |   adds |   add_avg_$ |   add_total_$ |   add_win% |       t |
|---:|:-----------------------------------------------|:-----------------------|-------:|------------:|--------------:|-----------:|--------:|
|  2 | LC02 ES-VOR                                    | DCA blind (-0.25 ATRd) |     27 |      -5.175 |      -139.730 |      0.074 |  -0.577 |
|  5 | LC03 NQ-NOON                                   | DCA blind (-0.25 ATRd) |      1 |      -2.240 |        -2.240 |      0.000 | nan     |
|  8 | LC05 NQ-PDH                                    | DCA blind (-0.25 ATRd) |     81 |       4.945 |       400.560 |      0.099 |   0.660 |
| 11 | T30-L1 NQ-COMP(base, W01 filter unrecoverable) | DCA blind (-0.25 ATRd) |     84 |     -10.984 |      -922.660 |      0.452 |  -0.830 |

No rule is significant (|t| < 1.5). Add counts for P2/P3 are small; blind DCA is not better than the structural adds.

