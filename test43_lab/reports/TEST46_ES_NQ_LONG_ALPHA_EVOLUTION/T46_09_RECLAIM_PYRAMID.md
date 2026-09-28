# T46_09 Reclaim pyramid (P3)

**Lane A is RESEARCH-ONLY: every INDEX6 seed is PARITY_BLOCKED (T46_01); nothing in Lane A can be promoted.**

Incremental P&L of the SECOND contract only (add fill -> original exit):

|    | seed                                           | rule                                           |   adds |   add_avg_$ |   add_total_$ |   add_win% |       t |
|---:|:-----------------------------------------------|:-----------------------------------------------|-------:|------------:|--------------:|-----------:|--------:|
|  1 | LC02 ES-VOR                                    | P3 reclaim (dip >=0.25 ATRd then close>=entry) |      4 |       9.072 |        36.290 |      0.750 |   0.664 |
|  4 | LC03 NQ-NOON                                   | P3 reclaim (dip >=0.25 ATRd then close>=entry) |      1 |     -67.240 |       -67.240 |      0.000 | nan     |
|  7 | LC05 NQ-PDH                                    | P3 reclaim (dip >=0.25 ATRd then close>=entry) |     10 |      71.760 |       717.600 |      0.700 |   1.346 |
| 10 | T30-L1 NQ-COMP(base, W01 filter unrecoverable) | P3 reclaim (dip >=0.25 ATRd then close>=entry) |     11 |      49.215 |       541.360 |      0.545 |   1.008 |

No rule is significant (|t| < 1.5). Add counts for P2/P3 are small; blind DCA is not better than the structural adds.

