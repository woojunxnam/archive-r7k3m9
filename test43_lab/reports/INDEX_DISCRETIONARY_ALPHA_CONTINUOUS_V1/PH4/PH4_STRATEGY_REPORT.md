# PH4 strategy economics + frozen exit set — results (prereg 415e00b)

Exit dataset built for all 16 PH3 trigger definitions (5 frozen exits, base / SLIP4 $).  Only C2 (= D1B u D1B_P) is an eligible strategy population.

**C2 frozen exits (stitched window, per trade, pre-capacity): X60 -0.10, X120 +2.60, X1615 +15.65, XRES +3.16, XSTRUCT +10.86 $/trade.**  The C2 edge accrues late in the session: cutting at the nearest known resistance (-12.5 $/trade vs 16:15) or on structural failure (paired XSTRUCT - X1615 = -4.79 $/trade [-13.5, +4.2]) destroys value.

C2 with NESTED exit choice (training-window best; picks {'O1': 'X120', 'O2': 'X120', 'O3': 'X1615', 'O4': 'X1615', 'O5': 'X1615'}): 2.90 $/day after capacity, SLIP4 1.22, delay 3.14, missed-20% 1.69, 5/5 folds -> STRESS PASS; increment vs Main +2.90, ret/DD 0.01106 vs 0.01089 (1.016 x) -> ROUTE B FAILS (needs 1.02 x); the frozen X1615 C2 of the reclamation program remains the C2 reference.

No other trigger has a positive SLIP4 economic exit except the pattern nulls D2P / D8_P (small samples) — none of the location mechanisms is economic under any frozen exit.

```json
{
 "exit_picks": {
  "O1": "X120",
  "O2": "X120",
  "O3": "X1615",
  "O4": "X1615",
  "O5": "X1615"
 },
 "trades": 553,
 "avg_day": 2.904249999999997,
 "slip4_avg_day": 1.2244705882352915,
 "delay1_avg_day": 3.1364191176470406,
 "missed20_avg_day": 1.6927720588235264,
 "remove_top3": 721.709999999996,
 "folds": {
  "O1": 0.521304347826122,
  "O2": 3.9850996015936153,
  "O3": 2.54685258964142,
  "O4": 3.434920634920608,
  "O5": 3.7188951841359765
 },
 "folds_pos": 5,
 "y2022": 1000.2599999999975,
 "max_dd": 1885.489999999997,
 "worst_day": -1632.74,
 "corr_main": 0.2337955719511335,
 "incr": 2.904249999999962,
 "comb_ret_dd": 0.01106499347309471,
 "main_ret_dd": 0.01089094598770062,
 "comb_max_dd": 13979.562365193,
 "comb_worst": -4727.67999999997,
 "STRESS_PASS": true,
 "ROUTE_B": false,
 "ROUTE_A": false,
 "XSTRUCT_minus_X1615_per_trade": {
  "mean": -4.790677966101698,
  "ci_lo": -13.536497870721906,
  "ci_hi": 4.175841299879963,
  "n": 590
 },
 "fixed_exit_table": [
  {
   "exit": "X60",
   "n": 590,
   "usd": -0.10101694915253336,
   "usd4": -4.176440677966093
  },
  {
   "exit": "X120",
   "n": 590,
   "usd": 2.6016666666666644,
   "usd4": -1.4816666666666698
  },
  {
   "exit": "X1615",
   "n": 590,
   "usd": 15.654067796610175,
   "usd4": 11.578644067796615
  },
  {
   "exit": "XRES",
   "n": 590,
   "usd": 3.1604237288135573,
   "usd4": -0.9150000000000016
  },
  {
   "exit": "XSTRUCT",
   "n": 590,
   "usd": 10.86338983050848,
   "usd4": 6.787966101694921
  }
 ],
 "composition": {
  "D1B": 666,
  "D1B_P": 97
 }
}
```

## Exit table (stitched window, $/trade)
| def   |   usd_X60 |   usd_X120 |   usd_X1615 |   usd_XRES |   usd_XSTRUCT |   usd4_X60 |   usd4_X120 |   usd4_X1615 |   usd4_XRES |   usd4_XSTRUCT |     n |
|:------|----------:|-----------:|------------:|-----------:|--------------:|-----------:|------------:|-------------:|------------:|---------------:|------:|
| D1    |     -6.73 |     -10.3  |       -6.57 |      -3.37 |         -8.03 |     -10.9  |      -14.53 |       -10.74 |       -7.54 |         -12.2  |   308 |
| D1B   |     -2.16 |       1.45 |       14.28 |       3.7  |          8.65 |      -6.24 |       -2.63 |        10.2  |       -0.37 |           4.57 |   514 |
| D1B_P |     13.85 |       9.99 |       24.96 |      -0.51 |         25.83 |       9.78 |        5.88 |        20.89 |       -4.57 |          21.76 |    76 |
| D1P   |     -2.63 |     -10.07 |       -9.02 |      -8.13 |         -9.02 |      -6.85 |      -14.26 |       -13.24 |      -12.35 |         -13.24 |    70 |
| D2    |     -2.36 |       0.73 |        0.86 |      -0.45 |         -2.17 |      -6.47 |       -3.38 |        -3.24 |       -4.55 |          -6.27 |  5943 |
| D2P   |      1.66 |       3.93 |        7.44 |      -0.74 |          7.44 |      -2.32 |       -0.05 |         3.46 |       -4.72 |           3.46 |  1099 |
| D3    |      1.44 |       2.22 |        2.71 |       0.27 |          2.36 |      -2.77 |       -1.98 |        -1.51 |       -3.95 |          -1.85 |  2558 |
| D3P   |      0.46 |      -0.99 |       -5.4  |      -2.67 |         -5.4  |      -3.49 |       -4.93 |        -9.35 |       -6.61 |          -9.35 |   493 |
| D7    |      0.33 |       3.06 |        5.23 |       3.36 |          1.43 |      -3.78 |       -1.04 |         1.12 |       -0.75 |          -2.68 |  2393 |
| D7P   |     -8.62 |     -14.23 |      -12.2  |      -4.06 |        -12.2  |     -12.72 |      -18.33 |       -16.3  |       -8.16 |         -16.3  |   474 |
| D8    |     -1.65 |      -2.07 |        2.31 |      -0.23 |          0.09 |      -5.76 |       -6.19 |        -1.8  |       -4.34 |          -4.02 |  1388 |
| D8_P  |      2.9  |       1.19 |        4.83 |      -6.5  |          6.79 |      -1.13 |       -2.79 |         0.8  |      -10.53 |           2.76 |   188 |
| LN1   |     -1.23 |       1.48 |        3.55 |      -0.53 |          0.57 |      -5.32 |       -2.62 |        -0.54 |       -4.63 |          -3.52 | 10204 |
| LN2   |     -1.4  |       0.16 |        2.09 |       0.07 |         -0.93 |      -5.5  |       -3.94 |        -2    |       -4.03 |          -5.02 | 21073 |
| LN3   |     -2    |      -1.14 |        1.1  |      -1.82 |         -0.66 |      -6.11 |       -5.25 |        -3.01 |       -5.93 |          -4.77 | 18038 |
| TOUCH |     -5.3  |      -3.04 |        1.34 |      -1.32 |          0.09 |      -9.42 |       -7.17 |        -2.78 |       -5.44 |          -4.04 |  5341 |
