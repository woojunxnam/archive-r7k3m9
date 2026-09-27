# P07 P0 full universe, equal risk

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.

| risk_env | L | DEV_avg | DEV_total | DEV_max_dd | DEV_worst | DEV_ret_dd | DEV_excess_vs_mb | DEV_mu_avg | DEV_mu_peak | DEV_mu_on_avg | DEV_mu_on_peak | DEV_atr_avg | DEV_atr_peak | fills_per_day | env |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONSERVATIVE | 701.1 | 49.752 | 70996.52 | 7247.14 | -1781.74 | 0.007 | 28.273 | 0.021 | 0.101 | 0.023 | 0.101 | 621.553 | 5180.8 | 0.821 | CONSERVATIVE |
| MODERATE | 824.6 | 66.39 | 94738.35 | 9968.5 | -2610.35 | 0.007 | 39.039 | 0.025 | 0.103 | 0.027 | 0.103 | 837.255 | 6663.075 | 1.008 | MODERATE |
| AGGRESSIVE | 1578.2 | 114.449 | 163318.5 | 14173.73 | -4381.2 | 0.008 | 60.792 | 0.043 | 0.166 | 0.046 | 0.166 | 1583.513 | 11111.75 | 1.5 | AGGRESSIVE |

At MODERATE P0 does not beat the best single sleeve on DEV return/DD (P0 0.0067 vs 0.0068): half the universe is one ES cluster, so equal weight across names overweights ES. FULL_UNIVERSE_ADDS_VALUE = NO.
