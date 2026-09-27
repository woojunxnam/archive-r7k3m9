# P05 Behavioural clusters

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


Similarity = 0.5 x daily P&L corr + 0.25 x 30-min actual-position corr + 0.25 x drawdown-overlap (Jaccard); average
linkage on 1 - similarity. Cut 0.5 used (cuts 0.4 / 0.6 shown for sensitivity).

| id | MNQ_arch_A_AGG_0 | MNQ_robust_A_MOD_2 | MNQ_r2_C_MOD_1 | MNQ_robust_C_CON_0 | ES_robust_A_MOD_1 | ES_r2_F_MOD_2 | ES_r2_A_CON_1 | ES_robust_C_CON_4 |
|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | 1.0 | 0.57 | 0.43 | 0.3 | 0.3 | 0.42 | 0.38 | 0.42 |
| MNQ_robust_A_MOD_2 | 0.57 | 1.0 | 0.57 | 0.44 | 0.41 | 0.5 | 0.47 | 0.52 |
| MNQ_r2_C_MOD_1 | 0.43 | 0.57 | 1.0 | 0.67 | 0.41 | 0.53 | 0.52 | 0.59 |
| MNQ_robust_C_CON_0 | 0.3 | 0.44 | 0.67 | 1.0 | 0.39 | 0.44 | 0.47 | 0.51 |
| ES_robust_A_MOD_1 | 0.3 | 0.41 | 0.41 | 0.39 | 1.0 | 0.65 | 0.75 | 0.61 |
| ES_r2_F_MOD_2 | 0.42 | 0.5 | 0.53 | 0.44 | 0.65 | 1.0 | 0.8 | 0.69 |
| ES_r2_A_CON_1 | 0.38 | 0.47 | 0.52 | 0.47 | 0.75 | 0.8 | 1.0 | 0.76 |
| ES_robust_C_CON_4 | 0.42 | 0.52 | 0.59 | 0.51 | 0.61 | 0.69 | 0.76 | 1.0 |

| id | 0.4 | 0.5 | 0.6 |
|---|---|---|---|
| ES_r2_A_CON_1 | 4 | 3 | 1 |
| ES_r2_F_MOD_2 | 4 | 3 | 1 |
| ES_robust_A_MOD_1 | 4 | 3 | 1 |
| ES_robust_C_CON_4 | 4 | 3 | 1 |
| MNQ_arch_A_AGG_0 | 1 | 1 | 1 |
| MNQ_r2_C_MOD_1 | 3 | 2 | 1 |
| MNQ_robust_A_MOD_2 | 2 | 1 | 1 |
| MNQ_robust_C_CON_0 | 3 | 2 | 1 |

Clusters (cut 0.5): 1 = MNQ_arch_A_AGG_0 + MNQ_robust_A_MOD_2 (MNQ growth), 2 = MNQ_r2_C_MOD_1 + MNQ_robust_C_CON_0
(MNQ defensive), 3 = all four ES candidates (A/F/A/C behave as one ES long-exposure cluster).
Mean within-cluster daily corr 0.78; mean between-cluster daily corr 0.49.
Names do not define clusters: ES A, F and C are one behavioural cluster.

