# T44_16 Feature-family ablation

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

| model | features | n | IC_pooled | IC_monthly_mean | IC_monthly_t | share_positive_scores | top3_minus_bottom3_y_atr | gated_mean_y | kept_mean_y |
|---|---|---|---|---|---|---|---|---|---|
| RIDGE | E_ALL | 10240 | 0.0383 | 0.0471 | 3.9119 | 0.4444 | 0.0113 | -0.0042 | 0.0046 |
| RIDGE | E_minus_A | 10240 | -0.0126 | -0.0086 | -0.6751 | 0.4081 | -0.001 | -0.0004 | -0.0001 |
| RIDGE | E_minus_B | 10240 | 0.0329 | 0.0373 | 2.998 | 0.4395 | 0.0094 | -0.0037 | 0.0042 |
| RIDGE | E_minus_C | 10240 | 0.0572 | 0.0607 | 4.7162 | 0.49 | 0.0128 | -0.0059 | 0.0056 |
| RIDGE | E_minus_D | 10240 | 0.0406 | 0.0467 | 4.011 | 0.4312 | 0.0107 | -0.0051 | 0.0061 |
| RIDGE | A_ONLY | 10240 | 0.051 | 0.0547 | 4.4031 | 0.3072 | 0.0099 | -0.003 | 0.0059 |
| XGB_REGULARIZED | E_ALL | 10240 | 0.0386 | 0.0448 | 3.6863 | 0.2107 | 0.0088 | -0.0017 | 0.0052 |
| XGB_REGULARIZED | E_minus_A | 10240 | -0.009 | -0.0054 | -0.3842 | 0.113 | -0.0001 | 0.0004 | -0.0052 |
| XGB_REGULARIZED | E_minus_B | 10240 | 0.0495 | 0.0564 | 3.9776 | 0.2361 | 0.0115 | -0.003 | 0.0085 |
| XGB_REGULARIZED | E_minus_C | 10240 | 0.0474 | 0.0481 | 3.1255 | 0.2904 | 0.0088 | -0.0026 | 0.0054 |
| XGB_REGULARIZED | E_minus_D | 10240 | 0.0545 | 0.0562 | 4.1215 | 0.2404 | 0.0112 | -0.0036 | 0.0103 |
| XGB_REGULARIZED | A_ONLY | 10240 | 0.064 | 0.0628 | 4.7543 | 0.255 | 0.0138 | -0.0033 | 0.0087 |

Family A (frozen sleeve state) carries the information: removing A kills IC for both models. For XGB removing B, C or D each raises IC; for Ridge removing C or D raises IC and removing B lowers it slightly (0.038 -> 0.033). The A-only models match or beat the full models. Complexity did not earn its place.
