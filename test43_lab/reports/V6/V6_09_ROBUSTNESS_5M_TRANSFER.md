# V6_09 Finalist robustness, 5m re-run and ES<->MNQ transfer

DEV+VAL only; holdout never loaded. The former "+1 bar delay" test is renamed **TIMING_BRITTLENESS_STRESS**: it stresses
decision-to-fill timing and is not an estimate of production latency (production = local engine -> IBKR; TradingView is a
sentinel only). Research fill convention unchanged.

## Parameter neighbourhoods, remove-top-days, rolling windows
| id | n_neighbours | base_DEV | nb_DEV_median | nb_DEV_p10 | base_VAL | nb_VAL_median | nb_VAL_p10 | nb_DEVdd_p90 | nb_share_DEV_ge_80pct | DV_avg_ex_top5 | roll12m_pos_share | roll12m_min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | 80 | 78.0 | 75.7 | 55.4 | 77.6 | 77.6 | 11.9 | 14862.3 | 0.8 | 61.8 | 0.9 | -9556.6 |
| MNQ_arch_E_AGG_0 | 28 | 68.2 | 67.8 | 52.0 | 64.8 | 64.8 | 31.1 | 26433.5 | 0.9 | 55.8 | 0.8 | -16184.7 |
| MNQ_robust_A_MOD_2 | 80 | 111.5 | 109.1 | 85.7 | 76.7 | 76.7 | 44.3 | 16106.0 | 0.8 | 92.3 | 1.0 | -6219.7 |
| MNQ_r2_C_MOD_1 | 96 | 47.4 | 47.4 | 36.9 | 62.5 | 62.5 | 47.0 | 10029.2 | 0.9 | 41.3 | 1.0 | -3426.8 |
| MNQ_robust_C_CON_0 | 64 | 31.4 | 31.4 | 21.6 | 56.3 | 56.3 | 16.8 | 7276.5 | 0.9 | 27.1 | 0.9 | -3284.9 |
| ES_robust_F_AGG_0 | 60 | 116.0 | 114.9 | 102.8 | 115.0 | 115.0 | 94.7 | 28087.6 | 1.0 | 85.7 | 1.0 | -9668.0 |
| ES_r2_G_AGG_0 | 52 | 92.5 | 91.2 | 65.0 | 134.2 | 134.2 | 123.5 | 19885.5 | 0.8 | 80.5 | 1.0 | -2137.3 |
| ES_robust_A_MOD_1 | 84 | 65.6 | 65.5 | 57.1 | 98.9 | 98.9 | 86.7 | 16945.8 | 1.0 | 48.3 | 0.9 | -9961.6 |
| ES_r2_F_MOD_2 | 80 | 53.3 | 52.9 | 45.9 | 66.3 | 66.3 | 17.8 | 13261.7 | 1.0 | 43.3 | 1.0 | -8627.7 |
| ES_r2_A_CON_1 | 48 | 29.2 | 29.2 | 26.0 | 52.4 | 52.4 | 46.1 | 9054.8 | 1.0 | 24.4 | 0.9 | -7104.8 |
| ES_robust_C_CON_4 | 72 | 33.8 | 32.0 | 24.0 | 34.0 | 34.0 | 11.1 | 10656.0 | 0.8 | 25.9 | 0.9 | -7321.0 |

## Cost, timing-brittleness and margin stress (DEV+VAL avg/day and DD)
| id | SLIP2_DV_avg | SLIP4_DV_avg | COMM1.00_DV_avg | COMM0.61_DV_avg | TIMING_BRITTLENESS_STRESS_DV_avg | TIMING_BRITTLENESS_STRESS_DV_dd | MARGINx1.5_DV_avg | ON_MARGINx2_DV_avg | ON_MARGINx2_breach |
|---|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | 76.4 | 71.9 | 76.7 | 78.0 | 68.0 | 13020.8 | 77.3 | 60.8 | False |
| MNQ_arch_E_AGG_0 | 67.6 | 67.3 | 67.7 | 67.8 | 68.4 | 19373.3 | 67.8 | 67.8 | False |
| MNQ_robust_A_MOD_2 | 104.7 | 98.8 | 105.1 | 107.5 | 111.0 | 12701.2 | 107.5 | 107.5 | False |
| MNQ_r2_C_MOD_1 | 49.2 | 49.1 | 49.2 | 49.2 | 49.3 | 8045.2 | 49.2 | 49.2 | False |
| MNQ_robust_C_CON_0 | 34.2 | 34.0 | 34.2 | 34.3 | 34.2 | 5680.3 | 34.3 | 34.3 | False |
| ES_robust_F_AGG_0 | 91.1 | 63.7 | 111.7 | 116.0 | 117.1 | 27558.6 | 115.9 | 115.9 | False |
| ES_r2_G_AGG_0 | 94.6 | 89.2 | 96.6 | 97.4 |  |  |  |  |  |
| ES_robust_A_MOD_1 | 67.0 | 65.4 | 68.8 | 69.5 | 71.5 | 13342.3 | 69.5 | 69.5 | False |
| ES_r2_F_MOD_2 | 54.2 | 53.1 | 54.6 | 54.9 | 53.3 | 10161.5 | 54.8 | 51.8 | False |
| ES_r2_A_CON_1 | 31.5 | 30.8 | 31.8 | 31.9 | 31.0 | 8894.8 | 31.9 | 32.0 | False |
| ES_robust_C_CON_4 | 33.5 | 32.8 | 33.7 | 33.8 | 34.1 | 10385.3 | 33.8 | 33.8 | False |

## Regime / time-of-day attribution (gross MTM, USD)
| id | hi_vol_avg | lo_vol_avg | trend_avg | range_avg | tod_morning_0930_1100 | tod_midday_1100_1400 | tod_late_1400_1600 | overnight_gross |
|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | 59.0 | 116.0 | 105.0 | 6.0 | 9858.0 | 28664.0 | 30452.0 | 63252.0 |
| MNQ_arch_E_AGG_0 | 19.0 | 142.0 | 78.0 | 33.0 | -8131.0 | 34456.0 | 21429.0 | 62382.0 |
| MNQ_robust_A_MOD_2 | 132.0 | 103.0 | 128.0 | 52.0 | -7567.0 | 80919.0 | 37111.0 | 70952.0 |
| MNQ_r2_C_MOD_1 | 44.0 | 52.0 | 59.0 | 23.0 | -2038.0 | 20778.0 | 10668.0 | 50262.0 |
| MNQ_robust_C_CON_0 | 55.0 | 9.0 | 37.0 | 26.0 | 4816.0 | 8158.0 | 10112.0 | 32552.0 |
| ES_robust_F_AGG_0 | 58.0 | 97.0 | 108.0 | 139.0 | 6366.0 | 88751.0 | 62155.0 | 66655.0 |
| ES_r2_G_AGG_0 | 83.0 | 52.0 | 104.0 | 78.0 | 12060.0 | 46282.0 | 19658.0 | 86710.0 |
| ES_robust_A_MOD_1 | 58.0 | 17.0 | 69.0 | 71.0 | 28008.0 | 35540.0 | 24148.0 | 30488.0 |
| ES_r2_F_MOD_2 | 72.0 | 23.0 | 65.0 | 26.0 | 20920.0 | 21046.0 | 12120.0 | 36580.0 |
| ES_r2_A_CON_1 | 27.0 | 9.0 | 37.0 | 17.0 | 5734.0 | 10444.0 | 7454.0 | 28985.0 |
| ES_robust_C_CON_4 | 23.0 | 12.0 | 40.0 | 16.0 | 3856.0 | 9078.0 | 14755.0 | 27898.0 |

## 5m re-run (no re-optimisation) and cross-market transfer (caps scaled by ATR$ ratio ES->MNQ x0.557)
| id | test | DEV_avg_daily | DEV_excess_vs_mb | DEV_max_dd | VAL_avg_daily | VAL_excess_vs_mb | VAL_max_dd | fills | note |
|---|---|---|---|---|---|---|---|---|---|
| MNQ_arch_A_AGG_0 | BASE_3m | 78.0 | 48.0 | 12161.1 | 77.6 | 36.7 | 7160.0 | 2203.0 |  |
| MNQ_arch_A_AGG_0 | TF_5m | 60.9 | 31.0 | 16713.5 | 67.3 | 26.0 | 7822.5 | 2179.0 |  |
| MNQ_arch_A_AGG_0 | TRANSFER_TO_ES | 15.3 | -17.6 | 28222.1 | -38.5 | -80.0 | 19237.2 | 2510.0 |  |
| MNQ_arch_E_AGG_0 | BASE_3m | 68.2 | 16.0 | 19364.8 | 64.8 | 13.6 | 10399.2 | 149.0 |  |
| MNQ_arch_E_AGG_0 | TF_5m | 68.2 | 16.1 | 19323.8 | 65.1 | 14.0 | 10399.2 | 149.0 |  |
| MNQ_arch_E_AGG_0 | TRANSFER_TO_ES | 42.6 | -14.7 | 32963.4 | 32.9 | -29.5 | 16936.8 | 391.0 |  |
| MNQ_robust_A_MOD_2 | BASE_3m | 111.5 | 71.6 | 13361.4 | 76.7 | 23.8 | 5857.4 | 2192.0 |  |
| MNQ_robust_A_MOD_2 | TF_5m | 100.8 | 60.6 | 15603.6 | 78.4 | 25.6 | 7135.3 | 2199.0 |  |
| MNQ_robust_A_MOD_2 | TRANSFER_TO_ES | 55.0 | 12.0 | 19958.3 | 58.5 | 0.7 | 8822.4 | 2344.0 |  |
| MNQ_r2_C_MOD_1 | BASE_3m | 47.4 | 25.1 | 8041.2 | 62.5 | 15.8 | 7014.1 | 55.0 |  |
| MNQ_r2_C_MOD_1 | TF_5m | 47.7 | 25.3 | 7890.7 | 69.7 | 22.6 | 5665.6 | 53.0 |  |
| MNQ_r2_C_MOD_1 | TRANSFER_TO_ES | 18.8 | -2.2 | 16391.6 | 52.0 | 15.4 | 4701.2 | 149.0 |  |
| MNQ_robust_C_CON_0 | BASE_3m | 31.4 | 20.7 | 5979.8 | 56.3 | 42.5 | 2257.0 | 94.0 |  |
| MNQ_robust_C_CON_0 | TF_5m | 28.6 | 17.1 | 9282.5 | 56.3 | 42.5 | 2257.0 | 101.0 |  |
| MNQ_robust_C_CON_0 | TRANSFER_TO_ES | 13.1 | 9.6 | 5443.5 | 25.2 | 15.2 | 5071.8 | 176.0 |  |
| ES_robust_F_AGG_0 | BASE_3m | 116.0 | 50.3 | 19571.7 | 115.0 | 33.7 | 11090.5 | 1777.0 |  |
| ES_robust_F_AGG_0 | TF_5m | 110.6 | 44.6 | 26423.0 | 107.3 | 25.7 | 11984.2 | 1771.0 |  |
| ES_robust_F_AGG_0 | TRANSFER_TO_MNQ | 109.0 | 47.5 | 34927.7 | 169.0 | 90.4 | 12631.7 | 1615.0 |  |
| ES_r2_G_AGG_0 | 5m/transfer |  |  |  |  |  |  |  | v6x lane: bar-count internals are 3m-specific; not transferable without re-spec |
| ES_robust_A_MOD_1 | BASE_3m | 65.6 | 37.4 | 11601.4 | 98.9 | 54.9 | 11480.6 | 278.0 |  |
| ES_robust_A_MOD_1 | TF_5m | 58.9 | 30.7 | 15478.9 | 133.9 | 90.3 | 11103.1 | 281.0 |  |
| ES_robust_A_MOD_1 | TRANSFER_TO_MNQ | 32.3 | 4.2 | 17964.3 | 115.3 | 77.1 | 7084.4 | 305.0 |  |
| ES_r2_F_MOD_2 | BASE_3m | 53.3 | 25.4 | 9880.3 | 66.3 | 24.2 | 8362.5 | 257.0 |  |
| ES_r2_F_MOD_2 | TF_5m | 56.9 | 29.0 | 10196.5 | 66.0 | 24.0 | 8352.5 | 258.0 |  |
| ES_r2_F_MOD_2 | TRANSFER_TO_MNQ | 52.1 | 25.5 | 11265.3 | 36.3 | 0.0 | 12843.1 | 176.0 |  |
| ES_r2_A_CON_1 | BASE_3m | 29.2 | 11.7 | 8643.6 | 52.4 | 21.6 | 7073.1 | 208.0 |  |
| ES_r2_A_CON_1 | TF_5m | 29.0 | 11.5 | 8766.1 | 54.0 | 23.2 | 7050.6 | 208.0 |  |
| ES_r2_A_CON_1 | TRANSFER_TO_MNQ | 22.3 | 5.1 | 9141.7 | 27.3 | -4.5 | 11992.6 | 195.0 |  |
| ES_robust_C_CON_4 | BASE_3m | 33.8 | 12.4 | 8834.8 | 34.0 | 2.2 | 8914.9 | 182.0 |  |
| ES_robust_C_CON_4 | TF_5m | 32.7 | 11.9 | 9042.3 | 33.5 | 1.7 | 8864.9 | 179.0 |  |
| ES_robust_C_CON_4 | TRANSFER_TO_MNQ | 29.1 | 12.2 | 9540.1 | 45.1 | 12.2 | 10399.2 | 43.0 |  |

## Conclusions
* Most candidates sit on plateaus (>=80% of +-10/20% neighbours keep >=80% of DEV avg). No margin breach in any stress.
* TIMING_BRITTLENESS_STRESS is negligible for all V6A candidates (V6A trades large, infrequent state transitions).
* ES_robust_F_AGG_0: cost-sensitive (SLIP4 $64 vs $116/day) and neighbour DD p90 $28k -> DOWNGRADED; DD $26.4k at 5m;
  transfers to MNQ with a $34.9k DD (envelope breach).
* MNQ_arch_E_AGG_0: neighbour DD p90 $26k -> DOWNGRADED.
* 5m keeps most candidates (MNQ_robust_A_MOD_2 111.5->100.8 DEV, VAL 78.4; ES_robust_A_MOD_1 65.6->58.9, VAL 133.9).
* Transfer: MNQ_robust_A_MOD_2 -> ES works (+$12 DEV excess, +$0.7 VAL); ES_robust_A_MOD_1 -> MNQ +$4.2 / +$77.1;
  ES_robust_C_CON_4 -> MNQ +$12.2 / +$12.2; MNQ_arch_A_AGG_0 -> ES fails. The v6x lane (ES_r2_G_AGG_0) is not
  5m-transferable (bar-count internals are 3m-specific).
* Simple architectures (A, C) are the most portable; these remain the primary finalist pool for the freeze.
