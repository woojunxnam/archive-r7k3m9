## A survivors: all fresh starts (S2), 2/3-tick stress (S5), local robustness range (S3)
| family | note | cap | mtm | dd | fr20 | fr22 | fr25 | ne | rtpd | qm | pcd | mtm_2t | fr22_2t | fr22_3t | rob_n | rob_fr22_min | rob_fr22_max | rob_ne_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-HARV | free3 prof_be +1 (wave1c structure sweep) | 12 | 104.0k | -44.1k | 128.0k | 99.6k | 110.5k | 7.8 | 2.88 | 5.0 | 8.07 | 101.8k | 99.1k | 98.5k | 6 | 95.3k | 105.5k | 45.8 |
| A-HARV | dead50 prof_be +1 (wave1c structure sweep) | 12 | 106.2k | -44.0k | 128.0k | 99.7k | 110.6k | 7.8 | 2.85 | 5.1 | 8.11 | 104.2k | 99.1k | 98.6k | 6 | 88.2k | 100.0k | 446.1 |
| A-SALV | dead5d atr0.5 closest_be trig={'trig': 'always'} | 16 | 143.9k | -52.5k | 113.4k | 98.3k | 96.7k | 5.1 | 2.79 | 6.3 | 8.89 | 133.6k | 87.2k | 87.1k | 7 | 76.2k | 98.6k | 446.1 |
| A-SALV | dead5d pts10 closest_be trig={'trig': 'always'} | 16 | 141.4k | -52.6k | 112.9k | 98.2k | 96.8k | 5.1 | 2.79 | 6.3 | 8.74 |  |  |  | 3 | 76.2k | 98.4k | 446.1 |

## A+B portfolios at G=16 (sorted by mean weekly P&L)
| mech | G | capA | sizeB | book | inter | total_pnl | max_mtm_dd_bar | min_equity_bar | fresh2022_min_equity | wk_mean | wk_median | wk_worst | wk_worst_4w | wk_ge1k | wk_ge4k | corr_weekly | peak_contracts | pnl_per_contract_day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 16 | 0 | 16 | B7F+B4F |  | 49.1k | -13.4k | 145.3k | 140.7k | 133.1 | 380.4 | -11.2k | -8.9k | 25% | 0% |  | 16 | 36.91 |
| none | 16 | 0 | 16 | B7F+B4F |  | 49.1k | -13.4k | 145.3k | 140.7k | 133.1 | 380.4 | -11.2k | -8.9k | 25% | 0% |  | 16 | 36.91 |
| none | 16 | 0 | 16 | B7F |  | 48.4k | -14.8k | 146.3k | 150.6k | 131.1 | 120.3 | -6.6k | -7.7k | 18% | 0% |  | 16 | 83.71 |
| none | 16 | 0 | 16 | B7F |  | 48.4k | -14.8k | 146.3k | 150.6k | 131.1 | 120.3 | -6.6k | -7.7k | 18% | 0% |  | 16 | 83.71 |

## A+B portfolios at G=10 (top 8 by mean weekly P&L)
| mech | G | capA | sizeB | book | inter | total_pnl | max_mtm_dd_bar | min_equity_bar | fresh2022_min_equity | wk_mean | wk_median | wk_worst | wk_worst_4w | wk_ge1k | wk_ge4k | corr_weekly | peak_contracts | pnl_per_contract_day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 10 | 0 | 10 | B7F+B4F |  | 30.7k | -8.4k | 147.1k | 144.2k | 83.2 | 237.8 | -7.0k | -5.6k | 9% | 0% |  | 10 | 36.91 |
| none | 10 | 0 | 10 | B7F+B4F |  | 30.7k | -8.4k | 147.1k | 144.2k | 83.2 | 237.8 | -7.0k | -5.6k | 9% | 0% |  | 10 | 36.91 |
| none | 10 | 0 | 10 | B7F+B4F |  | 30.7k | -8.4k | 147.1k | 144.2k | 83.2 | 237.8 | -7.0k | -5.6k | 9% | 0% |  | 10 | 36.91 |
| none | 10 | 0 | 10 | B7F+B4F |  | 30.7k | -8.4k | 147.1k | 144.2k | 83.2 | 237.8 | -7.0k | -5.6k | 9% | 0% |  | 10 | 36.91 |
| none | 10 | 0 | 10 | B7F |  | 30.2k | -9.3k | 147.7k | 150.4k | 81.9 | 75.2 | -4.1k | -4.8k | 4% | 0% |  | 10 | 83.71 |
| none | 10 | 0 | 10 | B7F |  | 30.2k | -9.3k | 147.7k | 150.4k | 81.9 | 75.2 | -4.1k | -4.8k | 4% | 0% |  | 10 | 83.71 |
| none | 10 | 0 | 10 | B7F |  | 30.2k | -9.3k | 147.7k | 150.4k | 81.9 | 75.2 | -4.1k | -4.8k | 4% | 0% |  | 10 | 83.71 |
| none | 10 | 0 | 10 | B7F |  | 30.2k | -9.3k | 147.7k | 150.4k | 81.9 | 75.2 | -4.1k | -4.8k | 4% | 0% |  | 10 | 83.71 |

## A+B portfolios at G=12 (top 8 by mean weekly P&L)
| mech | G | capA | sizeB | book | inter | total_pnl | max_mtm_dd_bar | min_equity_bar | fresh2022_min_equity | wk_mean | wk_median | wk_worst | wk_worst_4w | wk_ge1k | wk_ge4k | corr_weekly | peak_contracts | pnl_per_contract_day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 12 | 0 | 12 | B7F+B4F |  | 36.8k | -10.0k | 146.5k | 143.1k | 99.8 | 285.3 | -8.4k | -6.7k | 17% | 0% |  | 12 | 36.91 |
| none | 12 | 0 | 12 | B7F+B4F |  | 36.8k | -10.0k | 146.5k | 143.1k | 99.8 | 285.3 | -8.4k | -6.7k | 17% | 0% |  | 12 | 36.91 |
| none | 12 | 0 | 12 | B7F+B4F |  | 36.8k | -10.0k | 146.5k | 143.1k | 99.8 | 285.3 | -8.4k | -6.7k | 17% | 0% |  | 12 | 36.91 |
| none | 12 | 0 | 12 | B7F |  | 36.3k | -11.1k | 147.2k | 150.4k | 98.3 | 90.2 | -5.0k | -5.7k | 15% | 0% |  | 12 | 83.71 |
| none | 12 | 0 | 12 | B7F |  | 36.3k | -11.1k | 147.2k | 150.4k | 98.3 | 90.2 | -5.0k | -5.7k | 15% | 0% |  | 12 | 83.71 |
| none | 12 | 0 | 12 | B7F |  | 36.3k | -11.1k | 147.2k | 150.4k | 98.3 | 90.2 | -5.0k | -5.7k | 15% | 0% |  | 12 | 83.71 |

## A+B portfolios at G=14 (top 8 by mean weekly P&L)
| mech | G | capA | sizeB | book | inter | total_pnl | max_mtm_dd_bar | min_equity_bar | fresh2022_min_equity | wk_mean | wk_median | wk_worst | wk_worst_4w | wk_ge1k | wk_ge4k | corr_weekly | peak_contracts | pnl_per_contract_day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 14 | 0 | 14 | B7F+B4F |  | 43.0k | -11.7k | 145.9k | 141.9k | 116.5 | 332.8 | -9.8k | -7.8k | 21% | 0% |  | 14 | 36.91 |
| none | 14 | 0 | 14 | B7F+B4F |  | 43.0k | -11.7k | 145.9k | 141.9k | 116.5 | 332.8 | -9.8k | -7.8k | 21% | 0% |  | 14 | 36.91 |
| none | 14 | 0 | 14 | B7F+B4F |  | 43.0k | -11.7k | 145.9k | 141.9k | 116.5 | 332.8 | -9.8k | -7.8k | 21% | 0% |  | 14 | 36.91 |
| none | 14 | 0 | 14 | B7F |  | 42.3k | -13.0k | 146.8k | 150.5k | 114.7 | 105.3 | -5.8k | -6.7k | 16% | 0% |  | 14 | 83.71 |
| none | 14 | 0 | 14 | B7F |  | 42.3k | -13.0k | 146.8k | 150.5k | 114.7 | 105.3 | -5.8k | -6.7k | 16% | 0% |  | 14 | 83.71 |
| none | 14 | 0 | 14 | B7F |  | 42.3k | -13.0k | 146.8k | 150.5k | 114.7 | 105.3 | -5.8k | -6.7k | 16% | 0% |  | 14 | 83.71 |

## A+B portfolios at G=20 (top 8 by mean weekly P&L)
| mech | G | capA | sizeB | book | inter | total_pnl | max_mtm_dd_bar | min_equity_bar | fresh2022_min_equity | wk_mean | wk_median | wk_worst | wk_worst_4w | wk_ge1k | wk_ge4k | corr_weekly | peak_contracts | pnl_per_contract_day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 20 | 0 | 20 | B7F+B4F |  | 61.4k | -16.7k | 144.1k | 138.4k | 166.4 | 475.5 | -14.0k | -11.2k | 31% | 0% |  | 20 | 36.91 |
| none | 20 | 0 | 20 | B7F+B4F |  | 61.4k | -16.7k | 144.1k | 138.4k | 166.4 | 475.5 | -14.0k | -11.2k | 31% | 0% |  | 20 | 36.91 |
| none | 20 | 0 | 20 | B7F |  | 60.5k | -18.6k | 145.4k | 150.7k | 163.8 | 150.4 | -8.3k | -9.6k | 20% | 0% |  | 20 | 83.71 |
| none | 20 | 0 | 20 | B7F |  | 60.5k | -18.6k | 145.4k | 150.7k | 163.8 | 150.4 | -8.3k | -9.6k | 20% | 0% |  | 20 | 83.71 |

## A+B portfolios at G=24 (top 8 by mean weekly P&L)
| mech | G | capA | sizeB | book | inter | total_pnl | max_mtm_dd_bar | min_equity_bar | fresh2022_min_equity | wk_mean | wk_median | wk_worst | wk_worst_4w | wk_ge1k | wk_ge4k | corr_weekly | peak_contracts | pnl_per_contract_day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 24 | 0 | 24 | B7F+B4F |  | 73.7k | -20.1k | 143.0k | 136.1k | 199.7 | 570.6 | -16.9k | -13.4k | 36% | 0% |  | 24 | 36.91 |
| none | 24 | 0 | 24 | B7F |  | 72.6k | -22.3k | 144.5k | 150.8k | 196.6 | 180.5 | -9.9k | -11.5k | 36% | 1% |  | 24 | 83.71 |
