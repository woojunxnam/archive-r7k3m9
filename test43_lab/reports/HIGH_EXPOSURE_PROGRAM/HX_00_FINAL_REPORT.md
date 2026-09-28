# TEST55+ high-exposure program - final report

```json
{
 "C43_CORE_AVG_DAY": 53.36,
 "C43_CORE_MAXDD": 6193,
 "C43_CORE_WORST_DAY": -1723,
 "C43_GROWTH_AVG_DAY": 70.13,
 "C43_GROWTH_AVG_DAY_2021": 73.98,
 "C43_GROWTH_MAXDD": 9520,
 "C43_GROWTH_WORST_DAY": -2692,
 "C43_GROWTH_FORWARD_STATUS": "FORWARD_SHADOW (TEST55 GROWTH-lane PASS; unopened OOS); superseded as FINAL_GROWTH by TEST61 per predeclared rule",
 "C43_CURRENT_PEAK_MES": 3,
 "C43_CURRENT_PEAK_MNQ": 3,
 "C43_PEAK_MARGIN_USAGE": 0.123,
 "C43_AVG_MARGIN_USAGE": 0.026,
 "ACCOUNT_IS_MARGIN_CONSTRAINED": "NO",
 "ACCOUNT_IS_RISK_CONSTRAINED": "YES",
 "TEST55_RESULT": "GROWTH-QUALITY PASS (incr +21.5 $/day, MaxDD 9.5k, worst -2.7k, ret/DD 0.0074, plateau+stress PASS); CORE fail (ret/DD < C43)",
 "TEST56_RESULT": "NO GROWTH/CORE PASS; timing value NEGATIVE for every state map (-4.7..-27.7 $/day); DD governor worsens (whipsaw)",
 "TEST61_RESULT": "GROWTH-QUALITY PASS (125.5 $/day full, 129 $/day 2021+, MaxDD 12.6k, worst -4.3k, ret/DD 0.0100 > C43, plateau+stress PASS, margin 31%); CORE fail (worst day)",
 "TEST57_RESULT": "FAIL (outer folds 3/5, timing value -9.0 $/day; 2022 -59 $/day; selections = MNQ beta 5 units)",
 "TEST58_RESULT": "k=2 FAIL GROWTH on the preregistered k-neighbour plateau (linear scaling makes k=1 < 60% of k=2 by construction); ret/DD 0.0074->0.0053->0.0041->0.0030",
 "TEST59_RESULT": "M2 overnight hold > 16:15 exit (TEST55 kept); beta carrier: overnight >> intraday-only in return, worst day barely improves",
 "TEST60_RESULT": "NO (rank-IC <= 0.025; best Ridge add +7.5 $/day timing carried by 2 years; offline bandit reduces to the same sign policy)",
 "BEST_ADAPTIVE_EXPOSURE_POLICY": "NONE (every state/ML/GA exposure policy had timing value <= 0 or failed nested folds)",
 "BEST_AVG_MES": 1.5,
 "BEST_MAX_MES": 6,
 "BEST_AVG_MNQ": 2.2,
 "BEST_MAX_MNQ": 8,
 "BEST_MARGIN_UTILIZATION": 0.306,
 "BEST_BETA_CARRIER_AVG_DAY": 44.17,
 "BEST_BETA_CARRIER_MAXDD": 23877,
 "BEST_BETA_CARRIER_TIMING_VALUE": "<= 0 (constant carriers ~0 by construction; every adaptive carrier negative)",
 "BEST_BETA_CARRIER_MATCHED_BETA_EXCESS": 0,
 "BEST_GROWTH_PORTFOLIO_COMPONENTS": "C43-GROWTH-T61 (C43x2 + TEST53 residual, total MNQ<=6)",
 "BEST_GROWTH_PORTFOLIO_AVG_DAY": 125.5,
 "BEST_GROWTH_PORTFOLIO_MAXDD": 12607,
 "BEST_GROWTH_PORTFOLIO_WORST_DAY": -4347,
 "BEST_GROWTH_PORTFOLIO_RET_DD": 0.01,
 "INCREMENT_VS_C43": 76.55,
 "MAX_$150K_AVG_DAY_CORE_ENVELOPE": {
  "label": "C43x1 + T53x1 + BETA0",
  "avg_day_full": 70.13,
  "avg_day_2021": 73.98,
  "max_dd": 9520,
  "worst_day": -2692
 },
 "MAX_$150K_AVG_DAY_GROWTH_ENVELOPE": {
  "label": "C43x2 + T53x1 + BETA2",
  "avg_day_full": 156.58,
  "avg_day_2021": 158.61,
  "max_dd": 24051,
  "worst_day": -5279
 },
 "MAX_$150K_AVG_DAY_AGGRESSIVE_ENVELOPE": {
  "label": "C43x2 + T53x3 + BETA5",
  "avg_day_full": 209.65,
  "avg_day_2021": 218.41,
  "max_dd": 44880,
  "worst_day": -9973
 },
 "MAX_$150K_AVG_DAY_MARGIN_ONLY": {
  "ES": {
   "contracts": 24,
   "avg_day_full": 269.41,
   "max_dd": 145110,
   "worst_day": -38910
  },
  "MNQ": {
   "contracts": 15,
   "avg_day_full": 332.3,
   "max_dd": 181065,
   "worst_day": -34860
  }
 },
 "24_MES_CAP_EVER_SELECTED": "NO",
 "24_MNQ_CAP_EVER_SELECTED": "NO",
 "WHY_HIGH_EXPOSURE_IS_OR_IS_NOT_USEFUL": "Margin is not binding (C43 <=12% NLV). The binding constraint is the locked-overnight / crash-day tail (~-2k worst day per MES-eq unit of beta). Extra exposure only adds beta; no state, ML or GA policy produced positive timing value, because the best up-days cluster inside high-vol drawdowns. High exposure raises return linearly and tail/DD linearly: useful only as a capital/risk-tolerance choice, not as alpha.",
 "V533_AVG_DAY": 75.98,
 "V533_MAXDD": 135092,
 "V533_TIMING_VALUE": "NEGATIVE",
 "BEST_POLICY_VS_V533": "C43-GROWTH 125.5 $/day at MaxDD 12607 vs V5.3.3 75.98 $/day at MaxDD 135092",
 "$600_DAY_POSSIBLE_WITH_$150K_CORE": "NO",
 "$600_DAY_POSSIBLE_WITH_$150K_GROWTH": "NO",
 "$600_DAY_POSSIBLE_WITH_$150K_AGGRESSIVE": "NO",
 "ESTIMATED_CAPITAL_FOR_$600_AT_BEST_NEW_POLICY": 717000.0,
 "BUDGET": {
  "TOTAL_HYPOTHESES": 1354,
  "TOTAL_ML_CONFIGS": 175,
  "TOTAL_GA_GENOMES": 777629,
  "HX_PROGRAM_HYPOTHESES": 25,
  "HX_PROGRAM_GENOMES": 90453,
  "HX_PROGRAM_ML_CONFIGS": 5
 },
 "OFFLINE_BANDIT": {
  "condition_met": true,
  "note": "reward is linear in exposure, so the contextual bandit's greedy action is always the max or min tier by the sign of the predicted return: it reduces to ML-B/ML-C sign policies already evaluated (best RIDGE ML-B timing +7.5 $/day, rank-IC 0.025, 2/6 years carry it)",
  "result": "NO robust state-dependent marginal exposure value"
 },
 "FINAL_CORE_PORTFOLIO": "C43-CORE",
 "FINAL_GROWTH_PORTFOLIO": "C43-GROWTH-T61 (C43x2 + TEST53 residual, total MNQ<=6)",
 "FINAL_AGGRESSIVE_RESEARCH_PORTFOLIO": "C43 + TEST53 x3 residual (report-only)",
 "FINAL_GROWTH_PROGRAM_PRE_OOS_FREEZE_SHA256": "cb90e447548cfd34f0fd6ae4fcf8b73b5769527dd1c64312cf5d7f1a3cc578e5",
 "FINAL_GROWTH_PROGRAM_OOS_RULES_SHA256": "b8ed111952a8e16bb27851a3d516c2a43206648c2329faed5bd9c72d62d830eb",
 "FINAL_GROWTH_PROGRAM_OOS_START": "2026-09-28",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO"
}
```

Pareto frontier (report-only composition of frozen components):

|    |   C43_scale |   TEST53_lots |   beta_units |   avg_day_full |   avg_day_2021 |     max_dd |   worst_day |   ret_dd |   peak_on_margin_frac |   avg_on_margin_frac |   peak_MES |   peak_MNQ_lock |   beta_timing_day | CORE_env   | GROWTH_env   | AGGR_env   | margin_ok_70   | label                  | pareto   |
|---:|------------:|--------------:|-------------:|---------------:|---------------:|-----------:|------------:|---------:|----------------------:|---------------------:|-----------:|----------------:|------------------:|:-----------|:-------------|:-----------|:---------------|:-----------------------|:---------|
|  0 |           1 |             0 |            0 |         53.358 |         52.506 |   6193.430 |   -1722.990 |    0.009 |                 0.123 |                0.026 |          3 |               2 |             0.000 | True       | True         | True       | True           | C43x1 + T53x0 + BETA0  | True     |
|  6 |           1 |             1 |            0 |         70.131 |         73.977 |   9519.960 |   -2692.137 |    0.007 |                 0.163 |                0.039 |          3 |               4 |             0.000 | True       | True         | True       | True           | C43x1 + T53x1 + BETA0  | True     |
| 30 |           2 |             0 |            0 |        106.716 |        105.011 |  12386.860 |   -3445.980 |    0.009 |                 0.246 |                0.052 |          6 |               4 |             0.000 | False      | True         | True       | True           | C43x2 + T53x0 + BETA0  | True     |
| 36 |           2 |             1 |            0 |        123.489 |        126.483 |  12606.700 |   -4347.367 |    0.010 |                 0.286 |                0.065 |          6 |               6 |             0.000 | False      | True         | True       | True           | C43x2 + T53x1 + BETA0  | True     |
| 31 |           2 |             0 |            2 |        139.806 |        137.138 |  20656.750 |   -5235.730 |    0.007 |                 0.308 |                0.082 |          7 |               5 |             5.997 | False      | True         | True       | True           | C43x2 + T53x0 + BETA2  | True     |
| 42 |           2 |             2 |            0 |        140.007 |        147.629 |  19039.920 |   -5384.274 |    0.007 |                 0.326 |                0.078 |          6 |               8 |             0.000 | False      | True         | True       | True           | C43x2 + T53x2 + BETA0  | True     |
| 37 |           2 |             1 |            2 |        156.579 |        158.610 |  24050.750 |   -5278.617 |    0.007 |                 0.348 |                0.094 |          7 |               7 |             5.997 | False      | True         | True       | True           | C43x2 + T53x1 + BETA2  | True     |
| 48 |           2 |             3 |            0 |        156.653 |        168.938 |  25642.760 |   -6421.181 |    0.006 |                 0.366 |                0.091 |          6 |              10 |             0.000 | False      | False        | True       | True           | C43x2 + T53x3 + BETA0  | True     |
| 33 |           2 |             0 |            5 |        159.712 |        154.482 |  28486.360 |   -7025.480 |    0.006 |                 0.330 |                0.108 |          8 |               6 |             1.873 | False      | False        | True       | True           | C43x2 + T53x0 + BETA5  | True     |
| 43 |           2 |             2 |            2 |        173.098 |        179.756 |  29466.190 |   -6315.524 |    0.006 |                 0.388 |                0.108 |          7 |               9 |             5.997 | False      | False        | True       | True           | C43x2 + T53x2 + BETA2  | True     |
| 39 |           2 |             1 |            5 |        176.485 |        175.954 |  31291.700 |   -7898.867 |    0.006 |                 0.370 |                0.121 |          8 |               8 |             1.873 | False      | False        | True       | True           | C43x2 + T53x1 + BETA5  | True     |
| 49 |           2 |             3 |            2 |        189.743 |        201.065 |  34881.630 |   -7352.431 |    0.005 |                 0.427 |                0.121 |          7 |              11 |             5.997 | False      | False        | True       | True           | C43x2 + T53x3 + BETA2  | True     |
| 54 |           2 |             5 |            0 |        189.944 |        211.556 |  41046.660 |   -8494.994 |    0.005 |                 0.502 |                0.117 |          6 |              14 |             0.000 | False      | False        | True       | True           | C43x2 + T53x5 + BETA0  | True     |
| 45 |           2 |             2 |            5 |        193.004 |        197.100 |  36492.440 |   -8935.774 |    0.005 |                 0.409 |                0.134 |          8 |              10 |             1.873 | False      | False        | True       | True           | C43x2 + T53x2 + BETA5  | True     |
| 50 |           2 |             3 |            3 |        200.826 |        212.221 |  44374.920 |   -9972.681 |    0.005 |                 0.449 |                0.142 |          8 |              11 |            -0.278 | False      | False        | True       | True           | C43x2 + T53x3 + BETA3  | True     |
| 51 |           2 |             3 |            5 |        209.649 |        218.409 |  44879.780 |   -9972.681 |    0.005 |                 0.449 |                0.147 |          8 |              12 |             1.873 | False      | False        | True       | True           | C43x2 + T53x3 + BETA5  | True     |
| 55 |           2 |             5 |            2 |        223.035 |        243.682 |  51799.470 |  -10184.950 |    0.004 |                 0.549 |                0.146 |          7 |              15 |             5.997 | False      | False        | False      | True           | C43x2 + T53x5 + BETA2  | True     |
| 46 |           2 |             2 |            8 |        235.562 |        238.353 |  59126.340 |  -11368.460 |    0.004 |                 0.493 |                0.184 |         10 |              10 |             1.314 | False      | False        | False      | True           | C43x2 + T53x2 + BETA8  | True     |
| 57 |           2 |             5 |            5 |        242.941 |        261.026 |  62148.460 |  -12046.494 |    0.004 |                 0.583 |                0.173 |          8 |              16 |             1.873 | False      | False        | False      | True           | C43x2 + T53x5 + BETA5  | True     |
| 52 |           2 |             3 |            8 |        252.208 |        259.662 |  66221.080 |  -11835.181 |    0.004 |                 0.533 |                0.197 |         10 |              12 |             1.314 | False      | False        | False      | True           | C43x2 + T53x3 + BETA8  | True     |
| 35 |           2 |             0 |           12 |        254.326 |        244.611 |  74372.500 |  -17172.500 |    0.003 |                 0.497 |                0.212 |         12 |               9 |             5.867 | False      | False        | False      | True           | C43x2 + T53x0 + BETA12 | True     |
| 41 |           2 |             1 |           12 |        271.099 |        266.083 |  79008.660 |  -17172.500 |    0.003 |                 0.537 |                0.225 |         12 |              10 |             5.867 | False      | False        | False      | True           | C43x2 + T53x1 + BETA12 | True     |
| 58 |           2 |             5 |            8 |        285.499 |        302.280 |  82317.140 |  -13908.994 |    0.003 |                 0.664 |                0.223 |         10 |              16 |             1.314 | False      | False        | False      | True           | C43x2 + T53x5 + BETA8  | True     |
| 47 |           2 |             2 |           12 |        287.617 |        287.229 |  85192.960 |  -17172.500 |    0.003 |                 0.576 |                0.238 |         12 |              12 |             5.867 | False      | False        | False      | True           | C43x2 + T53x2 + BETA12 | True     |
| 53 |           2 |             3 |           12 |        304.263 |        308.538 |  92234.980 |  -17172.500 |    0.003 |                 0.616 |                0.251 |         12 |              14 |             5.867 | False      | False        | False      | True           | C43x2 + T53x3 + BETA12 | True     |
| 59 |           2 |             5 |           12 |        337.554 |        351.155 | 108411.080 |  -17460.494 |    0.003 |                 0.745 |                0.277 |         12 |              18 |             5.867 | False      | False        | False      | False          | C43x2 + T53x5 + BETA12 | True     |

V5.3.3 comparison:

|    | portfolio                                              |   avg_day |     max_dd |   worst_day |   peak_on_margin | timing_value_day      |
|---:|:-------------------------------------------------------|----------:|-----------:|------------:|-----------------:|:----------------------|
|  0 | C43-CORE                                               |    53.358 |   6193.430 |   -1722.990 |            0.123 | C43 alpha (validated) |
|  1 | C43-GROWTH-T55 (C43 + TEST53 residual total MNQ<=3)    |    70.131 |   9519.960 |   -2692.137 |            0.163 | 9.850115080989724     |
|  2 | C43-GROWTH-T61 (C43x2 + TEST53 residual, total MNQ<=6) |   125.496 |  12606.700 |   -4347.367 |            0.306 | 11.132837537860672    |
|  3 | V5.3.3 (MES full history, reference)                   |    75.980 | 135092.000 |  -24992.000 |          nan     | negative              |
|  4 | constant matched long 3 units (beta)                   |    44.174 |  23877.160 |   -5566.500 |            0.091 | 0.0                   |

Beta/alpha decomposition:

|    | portfolio                         |   net_day |   PASSIVE_BETA_day |   ALPHA_TIMING_day |
|---:|:----------------------------------|----------:|-------------------:|-------------------:|
|  0 | C43-CORE                          |    53.358 |             23.640 |             29.718 |
|  1 | TEST53 residual increment (2021+) |    21.472 |             14.944 |              6.527 |
|  2 | BETA carrier CONST 3              |    44.174 |             44.605 |             -0.278 |

$600 frontier (growth portfolio scaling):

|    |   target_day |   growth_scale |   est_max_dd |   capital_same_pct_dd |
|---:|-------------:|---------------:|-------------:|----------------------:|
|  0 |      100.000 |          0.797 |    10045.471 |            119525.379 |
|  1 |      150.000 |          1.195 |    15068.206 |            179288.069 |
|  2 |      200.000 |          1.594 |    20090.941 |            239050.759 |
|  3 |      300.000 |          2.391 |    30136.412 |            358576.138 |
|  4 |      400.000 |          3.187 |    40181.883 |            478101.517 |
|  5 |      600.000 |          4.781 |    60272.824 |            717152.276 |

TEST57 stitched:

|                     | 0                                                                                                    |
|:--------------------|:-----------------------------------------------------------------------------------------------------|
| candidate           | C43 + GA-EXPOSURE stitched                                                                           |
| avg_day_full        | 73.6921941412985                                                                                     |
| avg_day_2021        | 78.53648529411818                                                                                    |
| max_dd              | 18051.309999999634                                                                                   |
| worst_day           | -6722.229999999981                                                                                   |
| ret_dd              | 0.004082373752447883                                                                                 |
| base_avg_day_2021   | 52.5056617647064                                                                                     |
| base_ret_dd         | 0.008615250265901252                                                                                 |
| incr_avg_day_2021   | 26.03082352941177                                                                                    |
| fold_O1_2021        | 72.05533596837947                                                                                    |
| fold_O2_2022        | -59.04278884462151                                                                                   |
| fold_O3_2023        | 0.0                                                                                                  |
| fold_O4_2024        | 13.777301587301588                                                                                   |
| fold_O5_2025_26     | 80.79257790368271                                                                                    |
| folds_pos           | 3                                                                                                    |
| fold_median         | 13.777301587301588                                                                                   |
| remove_top3_incr    | 24289.920000000013                                                                                   |
| remove_top5_incr    | 18431.420000000013                                                                                   |
| max_year_share      | 0.36299078923317146                                                                                  |
| y2019               | 19.962812499999927                                                                                   |
| y2020               | 74.83498023715404                                                                                    |
| y2021               | 132.269881422925                                                                                     |
| y2022               | -55.816095617530486                                                                                  |
| y2023               | 51.96569721115311                                                                                    |
| y2024               | 88.81666666666707                                                                                    |
| y2025               | 112.90031746032108                                                                                   |
| y2026               | 232.46643564356825                                                                                   |
| pre2023_avg         | 46.26319774011281                                                                                    |
| from2023_avg        | 102.05044392523462                                                                                   |
| peak_on_margin_frac | 0.4                                                                                                  |
| peak_in_margin_frac | 0.4                                                                                                  |
| timing_value_day    | -8.973735507787357                                                                                   |
| c1                  | False                                                                                                |
| c2                  | True                                                                                                 |
| c3                  | True                                                                                                 |
| c4                  | False                                                                                                |
| c5                  | False                                                                                                |
| c6                  | True                                                                                                 |
| c7                  | True                                                                                                 |
| CORE                | False                                                                                                |
| GROWTH              | False                                                                                                |
| AGGRESSIVE_REPORT   | False                                                                                                |
| margin_band         | 0.4                                                                                                  |
| fold_clusters       | ON|max5|min0|vt0|gov0 ; ON|max5|min2|vt0|gov1 ; NONE ; ON|max8|min0|vt0|gov0 ; ON|max5|min1|vt0|gov1 |

