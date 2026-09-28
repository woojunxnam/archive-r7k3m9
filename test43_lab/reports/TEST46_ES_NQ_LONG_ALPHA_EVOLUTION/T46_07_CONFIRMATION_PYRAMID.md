# T46_07 Confirmation pyramid (P1)

**Lane A is RESEARCH-ONLY: every INDEX6 seed is PARITY_BLOCKED (T46_01); nothing in Lane A can be promoted.**

Incremental P&L of the SECOND contract only (add fill -> original exit):

|    | seed                        | rule                                                           |   adds |   add_avg_$ |   add_total_$ |   add_win% |     t |
|---:|:----------------------------|:---------------------------------------------------------------|-------:|------------:|--------------:|-----------:|------:|
| 12 | NQ seeds (LC03/LC05/T30-L1) | P1 independent confirmation (2nd distinct seed while 1st open) |    246 |      13.130 |      3229.960 |      0.516 | 1.444 |

No rule is significant (|t| < 1.5). Add counts for P2/P3 are small; blind DCA is not better than the structural adds.

