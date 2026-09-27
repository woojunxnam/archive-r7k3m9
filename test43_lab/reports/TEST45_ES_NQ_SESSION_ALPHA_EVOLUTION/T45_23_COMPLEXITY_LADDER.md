# T45_23 Complexity ladder

|    |   rung | method                                             | evidence                            |   comb_ret_dd | verdict                                |
|---:|-------:|:---------------------------------------------------|:------------------------------------|--------------:|:---------------------------------------|
|  0 |      1 | Champion                                           | TEST43 one-shot holdout PASS        |         0.008 | benchmark                              |
|  1 |      2 | simple deterministic (CONTROL_A-D, S1-S6)          | fixed rules                         |         0.010 | no eligible rule                       |
|  2 |      2 | V6_STATE_CARRY (GA-recurrence-derived simple rule) | concept in 5/5 nested folds         |         0.010 | best near-misses (R3/R4 or R5); shadow |
|  3 |      3 | regularised linear ML                              | walk-forward                        |         0.005 | fails R2/R4                            |
|  4 |      4 | tree ensembles                                     | walk-forward                        |         0.006 | fails R2/R4                            |
|  5 |      5 | regime model (HMM)                                 | walk-forward feature                |         0.005 | no added value                         |
|  6 |      6 | numeric GA (nested)                                | stitched outer folds                |         0.007 | fails R2/R4/R5/R6                      |
|  7 |      7 | genetic programming (nested)                       | stitched outer folds                |         0.009 | fails R5/R6                            |
|  8 |      8 | combined ML + evolved overlay                      | only in-sample evolutions available |       nan     | not credible (in-sample)               |

Complexity did not earn its place. No rung passes the predeclared rule.

