# T47_07 Sequence-shuffle diagnostic

|    | inst   | leg   |   windows |   real_triggers |   real_fwd_excess_atr |   shuffled_mean |   shuffled_sd |   order_effect |   perm_p_one_sided |
|---:|:-------|:------|----------:|----------------:|----------------------:|----------------:|--------------:|---------------:|-------------------:|
|  0 | ES     | T1    |    105864 |             876 |                -0.023 |          -0.011 |         0.008 |         -0.012 |              0.900 |
|  1 | ES     | T4    |    105864 |             542 |                -0.012 |          -0.015 |         0.010 |          0.003 |              0.400 |
|  2 | MNQ    | T1    |    105872 |             872 |                -0.010 |          -0.006 |         0.007 |         -0.004 |              0.750 |
|  3 | MNQ    | T4    |    105872 |             542 |                -0.006 |          -0.008 |         0.010 |          0.002 |              0.500 |

20 within-window permutations of whole 5m bars (W=12). order_effect = E[fwd | real trigger] - E[fwd | shuffled trigger]; p = share of permutations >= real.

