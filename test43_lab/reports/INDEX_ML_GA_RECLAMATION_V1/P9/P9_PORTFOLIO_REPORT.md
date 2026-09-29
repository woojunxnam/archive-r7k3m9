# P9 RELAXED_RESEARCH_FRONTIER_V1 — results (prereg 215d01f)

45 portfolios enumerated exhaustively (integrated capacity allocator, Main priority).

```json
{
 "FRONTIER_A": "C2+MGMTx2",
 "FRONTIER_B": "C2+MGMTx1",
 "FRONTIER_C": "C2x1",
 "FRONTIER_D": "C1+MGMTx1",
 "PARETO": [
  "MAIN_ONLY",
  "C7x1",
  "C1x1",
  "C1x1 + C7x1",
  "C1+MGMTx1",
  "C1+MGMTx1 + C7x1",
  "C2x1",
  "C2x1 + C7x1",
  "C2x2",
  "C2x2 + C7x1",
  "C2+MGMTx1",
  "C2+MGMTx2",
  "C2+MGMTx2 + C7x1"
 ],
 "N_PORTFOLIOS": 45
}
```

## Frontier validation
|                           |      MAIN_ONLY |      C2+MGMTx2 |      C2+MGMTx1 |           C2x1 |       C1+MGMTx1 |
|:--------------------------|---------------:|---------------:|---------------:|---------------:|----------------:|
| avg_day                   |    151.78      |    161.548     |    158.287     |    156.742     |    170.203      |
| incr                      |      0         |      9.76816   |      6.50717   |      4.96265   |     18.4233     |
| slip4_avg_day             |    151.78      |    157.151     |    156         |    155.018     |    155.004      |
| max_dd                    |  13936.3       |  15187.1       |  14036         |  13979.6       |  20913.7        |
| worst_day                 |  -4666.44      |  -4954.4       |  -4810.42      |  -4727.68      |  -4948.61       |
| ret_dd                    |      0.0108909 |      0.0106372 |      0.0112772 |      0.0112122 |      0.00813836 |
| sharpe_daily              |      0.123551  |      0.120341  |      0.1237    |      0.12377   |      0.103684   |
| corr_main_cand            |      0         |      0.25872   |      0.261862  |      0.257314  |      0.462794   |
| loss_jaccard              |      0         |      0.212575  |      0.218891  |      0.210843  |      0.557814   |
| bottom5_cand_mean         |      0         |   -119.467     |    -59.7334    |    -44.6351    |   -537.294      |
| active_overlap            |      0         |      0.305882  |      0.315441  |      0.315441  |      0.895588   |
| y2022                     |   3112.7       |  15266         |   9228.41      |   8229.27      |   -452.36       |
| y2022_mb_excess           |      0         |  12672.7       |   6407.32      |   5408.18      |    279.009      |
| remove_top3               | 185663         | 194170         | 192430         | 190858         | 196161          |
| add_units_avg_day         |      0         |      2.17254   |      1.54452   |      0         |      4.76192    |
| peak_MNQ                  |      6         |      6         |      6         |      6         |      6          |
| peak_MES                  |      8         |      8         |      8         |      8         |      8          |
| peak_MYM                  |      0         |      4         |      2         |      1         |      2          |
| peak_M2K                  |      0         |      4         |      2         |      1         |      2          |
| cand_margin_peak_approx   |      0         |  18400         |   9200         |   5400         |  10800          |
| per10k_dd                 |    108.909     |    106.372     |    112.772     |    112.122     |     81.3836     |
| risk_normalized_increment |      0         |     -2.53768   |      3.86253   |      3.21291   |    -27.5258     |
| route_A                   |      0         |      0         |      1         |      0         |      0          |
| route_B                   |      0         |      0         |      1         |      1         |      0          |
| route_C                   |      0         |      0         |      0         |      0         |      0          |

## All portfolios
| portfolio             |   avg_day |    incr |   max_dd |   worst_day |   ret_dd | route_A   | route_B   | route_C   |
|:----------------------|----------:|--------:|---------:|------------:|---------:|:----------|:----------|:----------|
| MAIN_ONLY             |   151.78  |  0      |  13936.3 |    -4666.44 |   0.0109 | False     | False     | False     |
| C7x1                  |   156.448 |  4.6681 |  15299.8 |    -4666.44 |   0.0102 | False     | False     | False     |
| C7x2                  |   156.851 |  5.0717 |  16663.4 |    -5447.92 |   0.0094 | False     | False     | False     |
| C7+MGMTx1             |   156.188 |  4.4081 |  15459.5 |    -4666.44 |   0.0101 | False     | False     | False     |
| C7+MGMTx2             |   155.895 |  4.1157 |  17015.8 |    -5512.42 |   0.0092 | False     | False     | False     |
| C1x1                  |   165.441 | 13.6614 |  18137.2 |    -4948.61 |   0.0091 | False     | False     | False     |
| C1x1 + C7x1           |   169.351 | 17.5714 |  19500.7 |    -4948.61 |   0.0087 | False     | False     | False     |
| C1x1 + C7x2           |   168.121 | 16.3414 |  20887   |    -6068.15 |   0.008  | False     | False     | False     |
| C1x1 + C7+MGMTx1      |   169.238 | 17.4589 |  19683.2 |    -4948.61 |   0.0086 | False     | False     | False     |
| C1x1 + C7+MGMTx2      |   165.796 | 14.0169 |  20887   |    -7761.89 |   0.0079 | False     | False     | False     |
| C1x2                  |   164.865 | 13.086  |  22155.4 |    -5549.85 |   0.0074 | False     | False     | False     |
| C1x2 + C7x1           |   168.232 | 16.453  |  23429.2 |    -5582.65 |   0.0072 | False     | False     | False     |
| C1x2 + C7x2           |   164.238 | 12.4589 |  24527.2 |    -7851.38 |   0.0067 | False     | False     | False     |
| C1x2 + C7+MGMTx1      |   167.089 | 15.31   |  23768   |    -6662.64 |   0.007  | False     | False     | False     |
| C1x2 + C7+MGMTx2      |   161.562 |  9.7824 |  25612.2 |   -10011.4  |   0.0063 | False     | False     | False     |
| C1+MGMTx1             |   170.203 | 18.4233 |  20913.7 |    -4948.61 |   0.0081 | False     | False     | False     |
| C1+MGMTx1 + C7x1      |   173.046 | 21.2661 |  22277.2 |    -5157.9  |   0.0078 | False     | False     | False     |
| C1+MGMTx1 + C7x2      |   170.979 | 19.1991 |  23509.3 |    -6709.38 |   0.0073 | False     | False     | False     |
| C1+MGMTx1 + C7+MGMTx1 |   172.742 | 20.9628 |  22459.7 |    -5157.9  |   0.0077 | False     | False     | False     |
| C1+MGMTx1 + C7+MGMTx2 |   168.653 | 16.8731 |  23509.3 |    -7761.89 |   0.0072 | False     | False     | False     |
| C1+MGMTx2             |   158.661 |  6.8817 |  26808.8 |    -7903.56 |   0.0059 | False     | False     | False     |
| C1+MGMTx2 + C7x1      |   162.347 | 10.5677 |  27898.4 |    -7903.56 |   0.0058 | False     | False     | False     |
| C1+MGMTx2 + C7x2      |   157.446 |  5.6665 |  29019.6 |    -7970.84 |   0.0054 | False     | False     | False     |
| C1+MGMTx2 + C7+MGMTx1 |   161.202 |  9.4229 |  28058.1 |    -7903.56 |   0.0057 | False     | False     | False     |
| C1+MGMTx2 + C7+MGMTx2 |   154.738 |  2.9586 |  29131.2 |   -10011.4  |   0.0053 | False     | False     | False     |
| C2x1                  |   156.742 |  4.9626 |  13979.6 |    -4727.68 |   0.0112 | False     | True      | False     |
| C2x1 + C7x1           |   161.389 |  9.6093 |  15343.1 |    -4727.68 |   0.0105 | False     | False     | False     |
| C2x1 + C7x2           |   161.74  |  9.9604 |  16706.6 |    -5447.92 |   0.0097 | False     | False     | False     |
| C2x1 + C7+MGMTx1      |   161.094 |  9.314  |  15502.8 |    -4727.68 |   0.0104 | False     | False     | False     |
| C2x1 + C7+MGMTx2      |   160.408 |  8.6281 |  17059.1 |    -7145.16 |   0.0094 | False     | False     | False     |
| C2x2                  |   159.375 |  7.5956 |  14463.8 |    -4788.92 |   0.011  | True      | False     | False     |
| C2x2 + C7x1           |   163.953 | 12.1738 |  15386.4 |    -4788.92 |   0.0107 | False     | False     | False     |
| C2x2 + C7x2           |   163.588 | 11.8088 |  16749.9 |    -6617.92 |   0.0098 | False     | False     | False     |
| C2x2 + C7+MGMTx1      |   163.472 | 11.6923 |  15546.1 |    -5429.18 |   0.0105 | False     | False     | False     |
| C2x2 + C7+MGMTx2      |   161.978 | 10.1986 |  17102.3 |    -8777.9  |   0.0095 | False     | False     | False     |
| C2+MGMTx1             |   158.287 |  6.5072 |  14036   |    -4810.42 |   0.0113 | True      | True      | False     |
| C2+MGMTx1 + C7x1      |   162.914 | 11.1345 |  15399.5 |    -4810.42 |   0.0106 | False     | False     | False     |
| C2+MGMTx1 + C7x2      |   163.093 | 11.3138 |  16763.1 |    -5447.92 |   0.0097 | False     | False     | False     |
| C2+MGMTx1 + C7+MGMTx1 |   162.513 | 10.7331 |  15559.2 |    -4810.42 |   0.0104 | False     | False     | False     |
| C2+MGMTx1 + C7+MGMTx2 |   161.74  |  9.9604 |  17115.5 |    -7145.16 |   0.0094 | False     | False     | False     |
| C2+MGMTx2             |   161.548 |  9.7682 |  15187.1 |    -4954.4  |   0.0106 | False     | False     | False     |
| C2+MGMTx2 + C7x1      |   165.395 | 13.6158 |  15499.2 |    -4954.4  |   0.0107 | False     | False     | False     |
| C2+MGMTx2 + C7x2      |   164.88  | 13.1002 |  16862.8 |    -6617.92 |   0.0098 | False     | False     | False     |
| C2+MGMTx2 + C7+MGMTx1 |   164.914 | 13.1343 |  15658.9 |    -5429.18 |   0.0105 | False     | False     | False     |
| C2+MGMTx2 + C7+MGMTx2 |   162.463 | 10.683  |  17215.2 |    -8777.9  |   0.0094 | False     | False     | False     |
