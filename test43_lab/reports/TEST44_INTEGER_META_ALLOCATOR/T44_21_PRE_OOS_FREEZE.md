# T44_21 Pre-OOS freeze

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

`out/t44/freeze/TEST44_PRE_OOS_FREEZE.json` SHA256 `3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4`

```json
{
 "program": "TEST44 discrete contract + meta allocator lab",
 "frozen_before_any_data_after": "2026-05-27",
 "research_data": [
  "2019-05-06",
  "2026-05-27"
 ],
 "former_TEST43_holdout": "2025-10-01..2026-05-27 = USED historical data",
 "new_oos_start": "2026-05-28",
 "new_oos_data_acquired": false,
 "new_oos_opened": false,
 "canonical_data_sha256": {
  "ES": "2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116",
  "MNQ": "66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2"
 },
 "shadow_controls": [
  "ES_robust_F_AGG_0",
  "MNQ_arch_E_AGG_0",
  "ES_r2_G_AGG_0"
 ],
 "CHAMPION_CONTROL_V1": {
  "definition": "TEST43-P SECONDARY_2 P1_CLUSTER_EQUAL_RISK|CONSERVATIVE, byte-identical frozen implementation",
  "final_portfolios_sha256": "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7"
 },
 "integer_mapping": {
  "intensity": "desired_target / sleeve max desired target on DEV (<=2024-12-31)",
  "OFF": "desired <= 0 or intensity < off-band",
  "NORMAL": "1 contract",
  "STRONG": "2 contracts when intensity >= theta"
 },
 "challengers": {
  "SIMPLE_INTEGER_CHALLENGER": {
   "alloc_cfg": "D4|off0.1|lam0.0|mu0.0|max1",
   "model": null,
   "caps_per_symbol": 1,
   "engine_mode": "TRACK",
   "request_kwargs": {
    "kind": "D2",
    "theta": 0.5,
    "theta0": 0.1
   },
   "engine_kwargs": {
    "lam": 0.0,
    "mu": 0.0
   }
  },
  "RIDGE_CHALLENGER": {
   "alloc_cfg": "D4|off0.2|lam0.0|mu0.0|max2",
   "model": "RIDGE",
   "features": "A_ONLY",
   "usage": "TOP_HALF",
   "caps_per_symbol": 2,
   "engine_mode": "TRACK",
   "request_kwargs": {
    "kind": "D2",
    "theta": 0.5,
    "theta0": 0.2
   },
   "engine_kwargs": {
    "lam": 0.0,
    "mu": 0.0
   }
  },
  "XGBOOST_CHALLENGER": {
   "alloc_cfg": "D4|off0.1|lam0.0|mu0.0|max1",
   "model": "XGB_REGULARIZED",
   "features": "E_ALL",
   "usage": "GATE_POS",
   "caps_per_symbol": 1,
   "engine_mode": "TRACK",
   "request_kwargs": {
    "kind": "D2",
    "theta": 0.5,
    "theta0": 0.1
   },
   "engine_kwargs": {
    "lam": 0.0,
    "mu": 0.0
   }
  }
 },
 "cluster_rules": {
  "clusters": {
   "1": "MNQ A family",
   "2": "MNQ C family",
   "3": "ES family"
  },
  "desired_state": "sum over clusters of mean member demand (cluster-equal)"
 },
 "governor": {
  "account": 150000.0,
  "envelope": "MODERATE",
  "dd_tiers": "0.6*15000 -> $ATR budget x0.5; 0.85*15000 -> x0.25",
  "rearm": "after 20 sessions at a reduced tier (HWM reset) or DD < 0.3*15000",
  "day_stop": "0.8*3000 -> x0.5 rest of session",
  "atr_budget": "budget_frac 1.0 x $ATR of the per-symbol caps",
  "margin": "<= 0.5 equity; overnight fraction when next bar not RTH",
  "cut_order": "lowest-priority instrument first (LOW_DD static priority)"
 },
 "meta_models": {
  "sample": "(sleeve, session)",
  "target": "1-contract ON P&L minus ON-share x passive 1-contract P&L, in daily-ATR units, clipped +-3",
  "features": {
   "A": [
    "inten_last",
    "inten_mean",
    "on_share_prev",
    "on_last",
    "is_MNQ",
    "cl1",
    "cl2",
    "cl3"
   ],
   "B": [
    "tier",
    "atr_pct",
    "trend20",
    "trend100"
   ],
   "C": [
    "y_roll20",
    "y_roll60",
    "y_sd60",
    "y_dd120"
   ],
   "D": [
    "acct_dd",
    "acct_mu",
    "acct_ret20"
   ]
  },
  "calendar_features": "none",
  "walk_forward": {
   "first_train_sessions": 500,
   "refit_every_sessions": 63,
   "purge_sessions": 1,
   "expanding": true
  },
  "ridge_alpha": 10.0,
  "xgb_presets": {
   "XGB_SHALLOW": {
    "max_depth": 2,
    "learning_rate": 0.03,
    "n_estimators": 400,
    "min_child_weight": 50,
    "reg_lambda": 10.0,
    "subsample": 1.0,
    "colsample_bytree": 1.0
   },
   "XGB_REGULARIZED": {
    "max_depth": 3,
    "learning_rate": 0.03,
    "n_estimators": 400,
    "min_child_weight": 100,
    "reg_lambda": 30.0,
    "subsample": 0.7,
    "colsample_bytree": 0.7
   },
   "XGB_VERY_REGULARIZED": {
    "max_depth": 1,
    "learning_rate": 0.02,
    "n_estimators": 200,
    "min_child_weight": 200,
    "reg_lambda": 50.0,
    "subsample": 0.7,
    "colsample_bytree": 0.7
   }
  },
  "score_usages": [
   "GATE_POS",
   "TOP_HALF",
   "DROP_BOTTOM_Q"
  ],
  "oos_procedure": "start from the final fits below; refit every 63 OOS sessions on all labelled sessions (expanding, 1-session purge), identical hyper-parameters",
  "final_fits": {
   "RIDGE_CHALLENGER": {
    "file": "out/t44/freeze/ridge_final.json",
    "sha256": "a8c3a62ea9b15233c858aa4f57161cc73dc51b47953aeafcc6ea52985a8a8415",
    "train_last_session": "2026-05-26",
    "train_rows": 14192,
    "intercept": -0.0013894233326028945
   },
   "XGBOOST_CHALLENGER": {
    "file": "out/t44/freeze/xgb_final.json",
    "sha256": "bfb02c2928d0252941988bb43eb3c87f9ccc2c0b8c65d699056a215f58302b2b",
    "train_last_session": "2026-05-26",
    "train_rows": 13712,
    "best_iteration": 78
   }
  }
 },
 "costs": {
  "commission_side": 0.62,
  "slippage_ticks": 1,
  "roll_cost": {
   "MES": 3.74,
   "MNQ": 2.24
  }
 },
 "margin_fracs": {
  "MES": [
   0.06416935897435898,
   0.09167051282051282
  ],
  "MNQ": [
   0.07769201093071854,
   0.11098842629802283
  ]
 }
}
```
