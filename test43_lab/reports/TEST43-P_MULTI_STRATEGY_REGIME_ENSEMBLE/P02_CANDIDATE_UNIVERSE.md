# P02 Candidate universe

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


Eligible (8): MNQ_arch_A_AGG_0, MNQ_robust_A_MOD_2, MNQ_r2_C_MOD_1, MNQ_robust_C_CON_0, ES_robust_A_MOD_1, ES_r2_F_MOD_2, ES_r2_A_CON_1, ES_robust_C_CON_4.
Shadow controls (3): ES_robust_F_AGG_0 (cost + neighbourhood DD), MNQ_arch_E_AGG_0 (neighbourhood DD), ES_r2_G_AGG_0 (P01).
Candidate hashes / parameters: `freeze/TEST43P_PRE_VAL_FREEZE.json` -> candidates.

## 2022 verification (canonical frozen replay; all user-quoted figures reproduced)
| id | role | Y2022_avg | Y2022_max_dd | Y2022_worst | Y2022_mb_avg | Y2022_excess | Y2020_avg | Y2020_max_dd |
|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | ELIGIBLE | -28.0 | 12161.1 | -2404.9 | -8.3 | -19.7 | 148.1 | 12082.2 |
| MNQ_robust_A_MOD_2 | ELIGIBLE | -17.4 | 11732.0 | -2528.4 | -18.5 | 1.1 | 196.3 | 12511.4 |
| MNQ_r2_C_MOD_1 | ELIGIBLE | -6.9 | 4704.4 | -2536.9 | -7.0 | 0.1 | 77.0 | 3461.6 |
| MNQ_robust_C_CON_0 | ELIGIBLE | 13.1 | 3352.7 | -1457.0 | -6.6 | 19.7 | 54.9 | 3151.7 |
| ES_robust_A_MOD_1 | ELIGIBLE | 6.2 | 11601.4 | -2430.6 | -54.6 | 60.8 | 97.8 | 9490.2 |
| ES_r2_F_MOD_2 | ELIGIBLE | -10.6 | 9108.0 | -2553.8 | -31.8 | 21.2 | 58.5 | 7989.3 |
| ES_r2_A_CON_1 | ELIGIBLE | -15.1 | 7158.1 | -1745.0 | -25.9 | 10.8 | 26.9 | 6573.1 |
| ES_robust_C_CON_4 | ELIGIBLE | -25.1 | 7915.5 | -1716.9 | -24.7 | -0.4 | 21.4 | 7449.4 |
| ES_robust_F_AGG_0 | SHADOW | 59.5 | 16985.1 | -3732.9 | -48.7 | 108.2 | 131.1 | 18905.3 |
| MNQ_arch_E_AGG_0 | SHADOW | -47.3 | 13214.3 | -1741.0 | -46.4 | -0.8 | 94.1 | 17547.0 |
| ES_r2_G_AGG_0 | SHADOW | 3.2 | 14099.5 | -3356.2 | -52.8 | 56.0 | 116.1 | 11484.2 |

