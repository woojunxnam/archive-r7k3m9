# T46_08 Winner pyramid (P2)

**Lane A is RESEARCH-ONLY: every INDEX6 seed is PARITY_BLOCKED (T46_01); nothing in Lane A can be promoted.**

Incremental P&L of the SECOND contract only (add fill -> original exit):

|    | seed                                           | rule                                            |   adds |   add_avg_$ |   add_total_$ |   add_win% |      t |
|---:|:-----------------------------------------------|:------------------------------------------------|-------:|------------:|--------------:|-----------:|-------:|
|  0 | LC02 ES-VOR                                    | P2 winner (+0.25 ATRd & close>VWAP, within 60m) |     25 |      -5.440 |      -136.000 |      0.560 | -0.252 |
|  3 | LC03 NQ-NOON                                   | P2 winner (+0.25 ATRd & close>VWAP, within 60m) |     12 |       3.343 |        40.120 |      0.583 |  0.157 |
|  6 | LC05 NQ-PDH                                    | P2 winner (+0.25 ATRd & close>VWAP, within 60m) |     79 |      12.342 |       975.040 |      0.557 |  0.659 |
|  9 | T30-L1 NQ-COMP(base, W01 filter unrecoverable) | P2 winner (+0.25 ATRd & close>VWAP, within 60m) |     35 |      57.631 |      2017.100 |      0.514 |  1.077 |

No rule is significant (|t| < 1.5). Add counts for P2/P3 are small; blind DCA is not better than the structural adds.

