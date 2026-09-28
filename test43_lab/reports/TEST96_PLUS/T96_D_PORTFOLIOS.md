# TEST96 Track D fixed synthesis P0-P3

|    | portfolio       |   avg_day |   incr_avg_day |   incr_avg_day_2021 |    max_dd |   worst_day |   ret_dd |   ret_dd_2021 |   corr_add_to_main |
|---:|:----------------|----------:|---------------:|--------------------:|----------:|------------:|---------:|--------------:|-------------------:|
|  0 | P0_CURRENT_MAIN |   143.207 |          0.000 |               0.000 | 13936.302 |   -4666.440 |    0.010 |         0.011 |            nan     |
|  1 | P1_MAIN+YM      |   146.222 |          3.015 |               3.279 | 15345.982 |   -4666.440 |    0.010 |         0.010 |              0.298 |
|  2 | P2_MAIN+RTY     |   143.207 |          0.000 |               0.000 | 13936.302 |   -4666.440 |    0.010 |         0.011 |            nan     |
|  3 | P3_MAIN+YM+RTY  |   146.222 |          3.015 |               3.279 | 15345.982 |   -4666.440 |    0.010 |         0.010 |              0.298 |

```json
{
 "bundle_rule": "Stage-A STANDALONE_PASS or DIVERSIFIER_PASS; lots by $ATR ratio pre-2021",
 "FIXED_YM_TRANSFER_BUNDLE": {
  "members": [
   "T68_YM",
   "T67_YM"
  ],
  "lots_each": 1,
  "median_$ATR_MES_pre2021": 208.39285714285717,
  "median_$ATR_YM_micro_pre2021": 183.89285714285714
 },
 "FIXED_RTY_TRANSFER_BUNDLE": {
  "members": [],
  "lots_each": 1,
  "median_$ATR_MES_pre2021": 208.39285714285717,
  "median_$ATR_RTY_micro_pre2021": 151.6071428571431
 },
 "P1_MAIN+YM_PASS_PORTFOLIO": false,
 "P1_MAIN+YM_PASS_DIVERSIFIER": false,
 "P2_MAIN+RTY_PASS_PORTFOLIO": false,
 "P2_MAIN+RTY_PASS_DIVERSIFIER": false,
 "P3_MAIN+YM+RTY_PASS_PORTFOLIO": false,
 "P3_MAIN+YM+RTY_PASS_DIVERSIFIER": false
}
```

