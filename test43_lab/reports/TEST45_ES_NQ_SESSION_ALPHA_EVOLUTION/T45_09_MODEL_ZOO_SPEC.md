# T45_09 Model zoo specification

Walk-forward: FIRST_TRAIN 500 sessions, blocks 63, purge 1. Session-level pooled ES+MNQ rows. Targets clipped at +/-3 ATR.

Models (one broad regularised preset each, no search): RIDGE, ELASTIC_NET, LOGISTIC, RANDOM_FOREST, EXTRA_TREES, HIST_GB, XGBOOST, LIGHTGBM, CATBOOST; HMM (3-state Gaussian, causal filtered posteriors, refit per block).

Tasks: A overnight carry (15:45 -> next open), B gap rebound (09:31 -> 16:00), C opening flush (10:00 -> 16:00), D open inventory (09:31 -> 12:00), E regime (HMM posterior feature + state table). Deep NNs were not used.

Features per task:

|    | task        | features                                                                                                                                                                                                                                                                                                                                                                                |
|---:|:------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|  0 | A_CARRY     | inst, L_rth_ret, L_day_ret, L_dist_vwap, L_range_pos, L_mom15, L_mom30, L_mom60, L_dd_from_high, L_rec_from_low, L_accel, L_rth_range, L_rvol, G_gap_lock, T_prior_ret, T_trend20, V_prior_range, V_vol_pct, X_rel_rth_ret, X_rel_day_ret, X_rel_mom60, S_champ_pos, S_champ_dd, hmm_p0, hmm_p1, hmm_p2                                                                                 |
|  1 | B_GAP       | inst, G_gap_lock_atr, G_gap_cash_atr, G_gap_lock_range, G_gap_lock_sigma, G_gap_lock_pct, G_gap_cash_range, G_gap_cash_sigma, G_gap_cash_pct, T_prior_ret, T_trend20, V_prior_range, V_vol_pct, X_rel_gap, S_champ_open, S_champ_dd, hmm_p0, hmm_p1, hmm_p2                                                                                                                             |
|  2 | C_FLUSH     | inst, G_gap_lock_atr, G_gap_cash_atr, G_gap_lock_range, G_gap_lock_sigma, G_gap_lock_pct, G_gap_cash_range, G_gap_cash_sigma, G_gap_cash_pct, T_prior_ret, T_trend20, V_prior_range, V_vol_pct, X_rel_gap, S_champ_open, S_champ_dd, hmm_p0, hmm_p1, hmm_p2, F_ret_w, F_selloff_w, F_recovery_w, F_reclaim_frac, F_range_pos_w, F_disp_total, F_dist_vwap_w, X_rel_selloff, X_rel_ret30 |
|  3 | D_INVENTORY | inst, G_gap_lock_atr, G_gap_cash_atr, G_gap_lock_range, G_gap_lock_sigma, G_gap_lock_pct, G_gap_cash_range, G_gap_cash_sigma, G_gap_cash_pct, T_prior_ret, T_trend20, V_prior_range, V_vol_pct, X_rel_gap, S_champ_open, S_champ_dd, hmm_p0, hmm_p1, hmm_p2                                                                                                                             |

Mapping to trades: POS1 = +1 if prediction > 0; POS2 = +2 above the expanding 80th percentile of past predictions. Every mapping runs through the same integer overlay engine.

