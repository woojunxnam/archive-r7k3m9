# TEST117 final index portfolio synthesis — results (prereg 87bc894)

```json
{
 "frontier": {
  "members": "CURRENT_LOCKED_MAIN",
  "avg_day": 143.2070661720334,
  "avg_day_2021": 151.77951632758104,
  "max_dd": 13936.302365193056,
  "worst_day": -4666.439999999971,
  "ret_dd": 0.010275829443088406,
  "GAP_TO_600": 456.79293382796664,
  "MAIN_DD_NORMALIZED_AVG_DAY": 102.75829443088406
 },
 "admitted": [],
 "k_600": 4.18973739242186
}
```

## Linear scaling frontier (REPORT ONLY)

|    |      k |   avg_day |     max_dd |   worst_day |   ret_dd | label                                       |
|---:|-------:|----------:|-----------:|------------:|---------:|:--------------------------------------------|
|  0 | 1.0000 |  143.2071 | 13936.3024 |  -4666.4400 |   0.0103 | SCALING_REPORT_ONLY                         |
|  1 | 1.5000 |  214.8106 | 20904.4535 |  -6999.6600 |   0.0103 | SCALING_REPORT_ONLY (exceeds capacity caps) |
|  2 | 2.0000 |  286.4141 | 27872.6047 |  -9332.8800 |   0.0103 | SCALING_REPORT_ONLY (exceeds capacity caps) |
|  3 | 3.0000 |  429.6212 | 41808.9071 | -13999.3200 |   0.0103 | SCALING_REPORT_ONLY (exceeds capacity caps) |
|  4 | 4.0000 |  572.8283 | 55745.2095 | -18665.7600 |   0.0103 | SCALING_REPORT_ONLY (exceeds capacity caps) |
|  5 | 4.1900 |  600.0376 | 58393.1069 | -19552.3836 |   0.0103 | SCALING_REPORT_ONLY (exceeds capacity caps) |

No PORTFOLIO_ADDITIVE_HISTORICAL_SURVIVOR exists, so the sequential allocator admits nothing and the frontier equals the locked Main.

