# T44_20 Final challengers

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

Selection rules (applied mechanically): simple = max full-history ret/DD among envelope-feasible deterministic allocators (ties -> fewer contracts); Ridge / XGB = max ML-span ret/DD with F2, F3, F4 > 0, positive matched-beta excess and ML-span MaxDD <= $15k (ties -> fewer features).

```json
{
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
}
```

## Integer attribution (requested vs received, denial reasons)
| candidate | sleeve | inst | cluster | avg_requested | avg_received | denied_share_of_requests | denied_symbol_or_cluster_or_track | denied_governor_cut | gross_contribution | instrument_requested_total_avg | instrument_executed_avg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SIMPLE_INTEGER_CHALLENGER | ES_r2_A_CON_1 | ES | 3 | 1.099 | 0.915 | 0.168 | 0.185 | 0.0 | 27366.25 | 3.935 | 0.915 |
| SIMPLE_INTEGER_CHALLENGER | ES_robust_C_CON_4 | ES | 3 | 1.32 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | 3.935 | 0.915 |
| SIMPLE_INTEGER_CHALLENGER | ES_r2_F_MOD_2 | ES | 3 | 0.721 | 0.0 | 1.0 | 0.679 | 0.0 | 0.0 | 3.935 | 0.915 |
| SIMPLE_INTEGER_CHALLENGER | ES_robust_A_MOD_1 | ES | 3 | 0.796 | 0.0 | 1.0 | 0.753 | 0.0 | 0.0 | 3.935 | 0.915 |
| SIMPLE_INTEGER_CHALLENGER | MNQ_robust_C_CON_0 | MNQ | 2 | 0.42 | 0.365 | 0.13 | 0.055 | 0.0 | 39082.5 | 3.061 | 0.72 |
| SIMPLE_INTEGER_CHALLENGER | MNQ_r2_C_MOD_1 | MNQ | 2 | 1.134 | 0.313 | 0.724 | 0.613 | 0.0 | 5007.5 | 3.061 | 0.72 |
| SIMPLE_INTEGER_CHALLENGER | MNQ_arch_A_AGG_0 | MNQ | 1 | 0.676 | 0.039 | 0.943 | 0.415 | 0.0 | 1690.5 | 3.061 | 0.72 |
| SIMPLE_INTEGER_CHALLENGER | MNQ_robust_A_MOD_2 | MNQ | 1 | 0.831 | 0.003 | 0.997 | 0.514 | 0.0 | -1084.0 | 3.061 | 0.72 |
| RIDGE_CHALLENGER | ES_r2_A_CON_1 | ES | 3 | 0.526 | 0.258 | 0.51 | 0.264 | 0.0 | 11656.25 | 1.483 | 0.27 |
| RIDGE_CHALLENGER | ES_robust_C_CON_4 | ES | 3 | 0.478 | 0.011 | 0.977 | 0.302 | 0.0 | 1645.0 | 1.483 | 0.27 |
| RIDGE_CHALLENGER | ES_r2_F_MOD_2 | ES | 3 | 0.418 | 0.001 | 0.997 | 0.385 | 0.0 | 906.25 | 1.483 | 0.27 |
| RIDGE_CHALLENGER | ES_robust_A_MOD_1 | ES | 3 | 0.061 | 0.0 | 1.0 | 0.03 | 0.0 | 0.0 | 1.483 | 0.27 |
| RIDGE_CHALLENGER | MNQ_robust_C_CON_0 | MNQ | 2 | 0.237 | 0.228 | 0.038 | 0.009 | 0.0 | 17120.0 | 1.277 | 0.46 |
| RIDGE_CHALLENGER | MNQ_r2_C_MOD_1 | MNQ | 2 | 0.44 | 0.187 | 0.574 | 0.219 | 0.0 | 15071.0 | 1.277 | 0.46 |
| RIDGE_CHALLENGER | MNQ_arch_A_AGG_0 | MNQ | 1 | 0.256 | 0.038 | 0.851 | 0.125 | 0.0 | 9940.0 | 1.277 | 0.46 |
| RIDGE_CHALLENGER | MNQ_robust_A_MOD_2 | MNQ | 1 | 0.344 | 0.006 | 0.981 | 0.204 | 0.0 | 1320.5 | 1.277 | 0.46 |
| XGBOOST_CHALLENGER | ES_r2_A_CON_1 | ES | 3 | 0.378 | 0.303 | 0.2 | 0.075 | 0.0 | 14357.5 | 1.514 | 0.304 |
| XGBOOST_CHALLENGER | ES_robust_C_CON_4 | ES | 3 | 0.475 | 0.001 | 0.998 | 0.36 | 0.0 | 142.5 | 1.514 | 0.304 |
| XGBOOST_CHALLENGER | ES_r2_F_MOD_2 | ES | 3 | 0.293 | 0.0 | 0.999 | 0.275 | 0.0 | 281.25 | 1.514 | 0.304 |
| XGBOOST_CHALLENGER | ES_robust_A_MOD_1 | ES | 3 | 0.367 | 0.0 | 1.0 | 0.347 | 0.0 | -22.5 | 1.514 | 0.304 |
| XGBOOST_CHALLENGER | MNQ_robust_C_CON_0 | MNQ | 2 | 0.235 | 0.207 | 0.117 | 0.028 | 0.0 | 19063.5 | 1.368 | 0.304 |
| XGBOOST_CHALLENGER | MNQ_r2_C_MOD_1 | MNQ | 2 | 0.411 | 0.047 | 0.886 | 0.255 | 0.0 | 2532.5 | 1.368 | 0.304 |
| XGBOOST_CHALLENGER | MNQ_arch_A_AGG_0 | MNQ | 1 | 0.347 | 0.037 | 0.892 | 0.209 | 0.0 | 6440.5 | 1.368 | 0.304 |
| XGBOOST_CHALLENGER | MNQ_robust_A_MOD_2 | MNQ | 1 | 0.376 | 0.012 | 0.968 | 0.225 | 0.0 | 157.0 | 1.368 | 0.304 |

## Deterministic attribution
| config | sleeve | inst | cluster | avg_requested | avg_received | denied_share_of_requests | denied_symbol_or_cluster_or_track | denied_governor_cut | gross_contribution | instrument_requested_total_avg | instrument_executed_avg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D4|off0.2|lam0.0|mu0.0|max2 | ES_r2_A_CON_1 | ES | 3 | 0.78 | 0.477 | 0.389 | 0.303 | 0.0 | 19356.25 | 2.257 | 0.48 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_robust_C_CON_4 | ES | 3 | 0.822 | 0.003 | 0.996 | 0.501 | 0.0 | -278.75 | 2.257 | 0.48 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_r2_F_MOD_2 | ES | 3 | 0.57 | 0.0 | 1.0 | 0.528 | 0.0 | 0.0 | 2.257 | 0.48 |
| D4|off0.2|lam0.0|mu0.0|max2 | ES_robust_A_MOD_1 | ES | 3 | 0.086 | 0.0 | 1.0 | 0.043 | 0.0 | 0.0 | 2.257 | 0.48 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_robust_C_CON_0 | MNQ | 2 | 0.42 | 0.413 | 0.016 | 0.007 | 0.0 | 43116.0 | 2.862 | 1.07 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_r2_C_MOD_1 | MNQ | 2 | 1.134 | 0.583 | 0.486 | 0.461 | 0.0 | 26601.5 | 2.862 | 1.07 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_arch_A_AGG_0 | MNQ | 1 | 0.492 | 0.066 | 0.865 | 0.242 | 0.0 | 10316.5 | 2.862 | 1.07 |
| D4|off0.2|lam0.0|mu0.0|max2 | MNQ_robust_A_MOD_2 | MNQ | 1 | 0.816 | 0.007 | 0.991 | 0.499 | 0.0 | -411.5 | 2.862 | 1.07 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_r2_A_CON_1 | ES | 3 | 1.099 | 0.915 | 0.168 | 0.185 | 0.0 | 27366.25 | 3.935 | 0.915 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_robust_C_CON_4 | ES | 3 | 1.32 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | 3.935 | 0.915 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_r2_F_MOD_2 | ES | 3 | 0.721 | 0.0 | 1.0 | 0.679 | 0.0 | 0.0 | 3.935 | 0.915 |
| D4|off0.1|lam0.0|mu0.0|max1 | ES_robust_A_MOD_1 | ES | 3 | 0.796 | 0.0 | 1.0 | 0.753 | 0.0 | 0.0 | 3.935 | 0.915 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_robust_C_CON_0 | MNQ | 2 | 0.42 | 0.365 | 0.13 | 0.055 | 0.0 | 39082.5 | 3.061 | 0.72 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_r2_C_MOD_1 | MNQ | 2 | 1.134 | 0.313 | 0.724 | 0.613 | 0.0 | 5007.5 | 3.061 | 0.72 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_arch_A_AGG_0 | MNQ | 1 | 0.676 | 0.039 | 0.943 | 0.415 | 0.0 | 1690.5 | 3.061 | 0.72 |
| D4|off0.1|lam0.0|mu0.0|max1 | MNQ_robust_A_MOD_2 | MNQ | 1 | 0.831 | 0.003 | 0.997 | 0.514 | 0.0 | -1084.0 | 3.061 | 0.72 |
