# T45_16 ES/NQ cross-index information

OLS (HC1) of each target on own-instrument state, with and without ES/NQ relative terms. Chronological yearly out-of-sample R2:

|    | inst   | task                           |    n |   R2_own |   R2_own+rel | rel_coef_t                           |   OOS_R2_own |   OOS_R2_own+rel | rel_adds_OOS   |
|---:|:-------|:-------------------------------|-----:|---------:|-------------:|:-------------------------------------|-------------:|-----------------:|:---------------|
|  0 | ES     | gap rebound (09:32 -> 16:00)   | 1733 |    0.000 |        0.001 | rel_gap:0.49                         |       -0.001 |           -0.006 | False          |
|  1 | ES     | flush rebound (10:01 -> 16:00) | 1728 |    0.000 |        0.003 | rel_selloff30:-1.00, rel_ret30:-0.25 |       -0.006 |           -0.007 | False          |
|  2 | ES     | carry (15:46 -> next open)     | 1728 |    0.005 |        0.005 | rel_rth_ret:-0.41, rel_mom60:0.41    |       -0.019 |           -0.025 | False          |
|  3 | MNQ    | gap rebound (09:32 -> 16:00)   | 1733 |    0.001 |        0.001 | rel_gap:0.08                         |       -0.002 |           -0.005 | False          |
|  4 | MNQ    | flush rebound (10:01 -> 16:00) | 1729 |    0.002 |        0.005 | rel_selloff30:0.59, rel_ret30:0.78   |       -0.006 |           -0.004 | True           |
|  5 | MNQ    | carry (15:46 -> next open)     | 1728 |    0.005 |        0.005 | rel_rth_ret:0.60, rel_mom60:0.00     |       -0.025 |           -0.031 | False          |

ES-NQ differential segment returns are in T45_01. Relative (X) features in ML ablation: T45_11.

Answer: ES_NQ_RELATIVE_STATE_ADDS_VALUE = NO. Out-of-sample R2 is not improved (one marginal exception: MNQ flush; both OOS R2 < 0).

