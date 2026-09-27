# P06 Common risk unit

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


Primary risk unit = sleeve standalone DEV daily P&L standard deviation. Sleeve contract weight w = budget x L / sigma;
instrument target = sum of weighted desired contracts; integer rounding only at the net execution layer.

| id | inst | sigma_daily_pnl_dev | avg_atr_dollar_exposure | avg_notional | avg_intraday_margin | avg_overnight_margin | contracts_per_risk_unit_$1000_daily_vol |
|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | MNQ | 925.75 | 820.51 | 49491.63 | 4683.93 | 5024.68 | 1.08 |
| MNQ_robust_A_MOD_2 | MNQ | 1112.32 | 1143.65 | 66698.0 | 6925.39 | 6429.3 | 0.9 |
| MNQ_r2_C_MOD_1 | MNQ | 519.57 | 643.03 | 37676.6 | 2919.09 | 4186.18 | 1.92 |
| MNQ_robust_C_CON_0 | MNQ | 349.89 | 334.42 | 17345.76 | 1419.76 | 1884.9 | 2.86 |
| ES_robust_A_MOD_1 | ES | 968.59 | 959.74 | 64401.53 | 4654.57 | 5612.79 | 1.03 |
| ES_r2_F_MOD_2 | ES | 649.15 | 864.51 | 64140.36 | 4185.18 | 5841.14 | 1.54 |
| ES_r2_A_CON_1 | ES | 434.07 | 576.26 | 40450.76 | 2592.07 | 3710.16 | 2.3 |
| ES_robust_C_CON_4 | ES | 484.73 | 668.25 | 48668.32 | 3170.94 | 4434.74 | 2.06 |
| ES_robust_F_AGG_0 | ES | 1743.0 | 1873.09 | 150531.36 | 12645.24 | 12135.14 | 0.57 |
| MNQ_arch_E_AGG_0 | MNQ | 1011.92 | 1326.76 | 80568.41 | 6399.38 | 8864.08 | 0.99 |
| ES_r2_G_AGG_0 | ES | 1207.18 | 1632.83 | 124743.57 | 8445.48 | 11189.64 | 0.83 |

## Sleeve stability (P2 representative rule) and cost robustness
| id | cluster | F1_excess | F2_excess | F3_excess | min_fold_excess | slip4_retention | ret_dd | sigma_daily_dev | avg_contracts | p2_score |
|---|---|---|---|---|---|---|---|---|---|---|
| MNQ_robust_A_MOD_2 | 1 | 46.93 | 81.61 | 59.15 | 46.93 | 0.92 | 0.01 | 1112.32 | 2.5 | 46.93 |
| MNQ_arch_A_AGG_0 | 1 | 33.93 | 56.19 | 33.26 | 33.26 | 0.92 | 0.01 | 925.75 | 1.89 | 33.26 |
| MNQ_robust_C_CON_0 | 2 | 10.71 | 24.96 | 16.32 | 10.71 | 0.99 | 0.01 | 349.89 | 0.66 | 10.71 |
| MNQ_r2_C_MOD_1 | 2 | 14.61 | 28.32 | 9.16 | 9.16 | 1.0 | 0.01 | 519.57 | 1.39 | 9.16 |
| ES_robust_A_MOD_1 | 3 | 41.52 | 56.87 | 14.0 | 14.0 | 0.9 | 0.01 | 968.59 | 3.13 | 14.0 |
| ES_r2_F_MOD_2 | 3 | 10.7 | 48.14 | 10.15 | 10.15 | 0.97 | 0.01 | 649.15 | 3.1 | 10.15 |
| ES_r2_A_CON_1 | 3 | 5.95 | 17.69 | 8.36 | 5.95 | 0.96 | 0.0 | 434.07 | 1.94 | 5.95 |
| ES_robust_C_CON_4 | 3 | -3.4 | 22.23 | 11.92 | -3.4 | 0.97 | 0.0 | 484.73 | 2.37 | -3.4 |

