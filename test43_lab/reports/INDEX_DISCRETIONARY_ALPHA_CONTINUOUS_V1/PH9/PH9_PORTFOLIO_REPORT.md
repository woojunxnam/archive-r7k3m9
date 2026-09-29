# PH8 / PH9 — results (prereg 6d83b2c)

PH8 cross-index confirmation: NOT_RUN_BY_RULE (no new positive mechanism).

PH9: 7 portfolios (exhaustive).  Best ret/DD frontier = **MAIN + C2 + ADD1 first-winner press (1 lot)**: 160.65 $/day on the stitched window (+8.88 = +4.96 C2 ALPHA-candidate + 3.91 GENERIC WINNER PRESS), ret/DD 0.01139 (1.046 x Main), MaxDD 14,105, routes A and B.  C2 + ADD1 + ADD2: +12.10 $/day but ret/DD 0.01089 (= Main) -> no route (leverage-like).  Lots 2: worse risk-normalised.

**FULL-SELECTION OVERFIT DIAGNOSTIC** (3,816 stored series + counted trials, N = 6441): selected increment DSR **0.025**, PBO **0.35**, White RC p **0.36** -> after the whole research chain, the frontier increment is statistically indistinguishable from the best of many tries.

```json
{
 "frontiers": {
  "FRONTIER_A": "C2+W1+W2x1",
  "FRONTIER_B": "C2+W1x1",
  "FRONTIER_C": "C2x1",
  "FRONTIER_D": "C2+W1+W2x1"
 },
 "diag": {
  "selected": "C2+W1x1",
  "series_in_matrix": 3816,
  "N_trials": 6441,
  "daily_sharpe": 0.03969719335923486,
  "sr0": 0.08982257833326251,
  "DSR": 0.02474796021481582,
  "PBO": 0.3536907536907537,
  "reality_check_p": 0.362,
  "status": "COMPUTED_WITH_LIMITATION (nested per-fold choices and 33 PH5 ML policies and 2,592 reclamation genomes counted in N only)"
 }
}
```

|                           |      MAIN_ONLY |           C2x1 |           C2x2 |        C2+W1x1 |         C2+W1x2 |      C2+W1+W2x1 |      C2+W1+W2x2 |
|:--------------------------|---------------:|---------------:|---------------:|---------------:|----------------:|----------------:|----------------:|
| avg_day                   |    151.78      |    156.742     |    159.375     |    160.655     |    161.641      |    163.884      |    163.334      |
| incr                      |      0         |      4.96265   |      7.59562   |      8.87539   |      9.86106    |     12.1046     |     11.5548     |
| slip4_avg_day             |    151.78      |    155.018     |    156.007     |    157.364     |    155.4        |    159.199      |    155.786      |
| max_dd                    |  13936.3       |  13979.6       |  14463.8       |  14105.3       |  16946.9        |  15048.4        |  16769.4        |
| worst_day                 |  -4666.44      |  -4727.68      |  -4788.92      |  -4791.92      |  -4917.4        |  -4857.16       |  -5143.62       |
| ret_dd                    |      0.0108909 |      0.0112122 |      0.0110189 |      0.0113897 |      0.00953805 |      0.0108904  |      0.00974002 |
| sharpe_daily              |      0.123551  |      0.12377   |      0.121432  |      0.122879  |      0.115228   |      0.121552   |      0.114248   |
| corr_main_cand            |      0         |      0.257314  |      0.25062   |      0.273465  |      0.272678   |      0.274942   |      0.261804   |
| loss_jaccard              |      0         |      0.210843  |      0.206015  |      0.216216  |      0.211394   |      0.222057   |      0.210762   |
| y2022                     |   3112.7       |   8229.27      |  13741.8       |  13003.5       |  19095          |  17172.1        |  22844.1        |
| y2022_mb_excess           |      0         |   5408.18      |  11148.5       |  10182.4       |  16501.7        |  14351          |  20250.8        |
| remove_top3               | 185663         | 190858         | 192884         | 194649         | 190862          | 197000          | 190965          |
| add_units_avg_day         |      0         |      0         |      0         |      3.91274   |      2.26544    |      7.14194    |      3.95918    |
| peak_MNQ                  |      6         |      6         |      6         |      6         |      6          |      6          |      6          |
| peak_MES                  |      8         |      8         |      8         |      8         |      8          |      8          |      8          |
| peak_MYM                  |      0         |      1         |      2         |      2         |      4          |      3          |      4          |
| peak_M2K                  |      0         |      1         |      2         |      2         |      4          |      3          |      4          |
| cand_margin_peak_approx   |      0         |   5400         |  10800         |  10800         |  18400          |  16200          |  25600          |
| per10k_dd                 |    108.909     |    112.122     |    110.189     |    113.897     |     95.3805     |    108.904      |     97.4002     |
| risk_normalized_increment |      0         |      3.21291   |      1.27982   |      4.98762   |    -13.529      |     -0.00515109 |    -11.5092     |
| route_A                   |      0         |      0         |      1         |      1         |      0          |      0          |      0          |
| route_B                   |      0         |      1         |      0         |      1         |      0          |      0          |      0          |
| route_C                   |      0         |      0         |      0         |      0         |      0          |      0          |      0          |
