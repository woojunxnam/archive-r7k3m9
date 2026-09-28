# TEST84 - volume data / profile approximation QA

1m OHLCV only: every profile is an APPROXIMATION (VP-A single price, VP-B uniform range, VP-C centre-weighted). NQ signal = MNQ volume proxy.

|                                  | 0                                                                                                                  | 1                                                                                                                       |
|:---------------------------------|:-------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------|
| instrument                       | MNQ                                                                                                                | ES                                                                                                                      |
| sessions                         | 1741                                                                                                               | 1741                                                                                                                    |
| rth_minutes                      | 705105                                                                                                             | 705105                                                                                                                  |
| zero_volume_share                | 0.009852433325533077                                                                                               | 0.009414200721878301                                                                                                    |
| missing_price_share              | 0.0022975301550832716                                                                                              | 0.0022975301550832716                                                                                                   |
| sessions_with_any_zero_bar_share | 0.03331418724870764                                                                                                | 0.032739804709936815                                                                                                    |
| abnormal_volume_days             | 9                                                                                                                  | 7                                                                                                                       |
| roll_sessions                    | 27                                                                                                                 | 27                                                                                                                      |
| roll_vs_nonroll_volume_ratio     | 0.8625156929662824                                                                                                 | 0.8471416602761384                                                                                                      |
| median_daily_rth_volume_by_year  | {2019: 135789, 2020: 439942, 2021: 643847, 2022: 992661, 2023: 804481, 2024: 977663, 2025: 1113169, 2026: 1390144} | {2019: 926131, 2020: 1214606, 2021: 1039994, 2022: 1423276, 2023: 1316241, 2024: 1109638, 2025: 1091745, 2026: 1231029} |
| open_5m_share                    | 0.038952261492937706                                                                                               | 0.03439175865596527                                                                                                     |
| close_5m_share                   | 0.00311318644923013                                                                                                | 0.006730842509035229                                                                                                    |
| midday_min_5m_share              | 0.00311318644923013                                                                                                | 0.006730842509035229                                                                                                    |
| signal_volume_source             | MNQ micro (PROXY for NQ; full NQ not in data set)                                                                  | ES full contract                                                                                                        |

|    | instrument   | proxy   |   checked |   mismatches |
|---:|:-------------|:--------|----------:|-------------:|
|  0 | MNQ          | VP-A    |       300 |            0 |
|  1 | MNQ          | VP-B    |       300 |            0 |
|  2 | MNQ          | VP-C    |       300 |            0 |
|  3 | ES           | VP-A    |       300 |            0 |
|  4 | ES           | VP-B    |       300 |            0 |
|  5 | ES           | VP-C    |       300 |            0 |

|    | instrument   | feature   | pair      |   corr_of_30m_change |   median_abs_diff_ATR |   same_bin_share |
|---:|:-------------|:----------|:----------|---------------------:|----------------------:|-----------------:|
|  0 | MNQ          | P2_POC    | VP-A/VP-B |                0.453 |                 0.020 |            0.320 |
|  1 | MNQ          | P2_POC    | VP-A/VP-C |                0.498 |                 0.000 |            0.509 |
|  2 | MNQ          | P2_POC    | VP-B/VP-C |                0.785 |                 0.000 |            0.645 |
|  3 | MNQ          | P4_POC    | VP-A/VP-B |                0.763 |                 0.020 |            0.401 |
|  4 | MNQ          | P4_POC    | VP-A/VP-C |                0.791 |                 0.000 |            0.600 |
|  5 | MNQ          | P4_POC    | VP-B/VP-C |                0.929 |                 0.000 |            0.684 |
|  6 | MNQ          | P2_VAH    | VP-A/VP-B |                0.635 |                 0.020 |            0.356 |
|  7 | MNQ          | P2_VAH    | VP-A/VP-C |                0.644 |                 0.020 |            0.397 |
|  8 | MNQ          | P2_VAH    | VP-B/VP-C |                0.887 |                 0.000 |            0.746 |
|  9 | MNQ          | P2_VAL    | VP-A/VP-B |                0.718 |                 0.020 |            0.358 |
| 10 | MNQ          | P2_VAL    | VP-A/VP-C |                0.734 |                 0.020 |            0.421 |
| 11 | MNQ          | P2_VAL    | VP-B/VP-C |                0.896 |                 0.000 |            0.740 |
| 12 | ES           | P2_POC    | VP-A/VP-B |                0.395 |                 0.020 |            0.320 |
| 13 | ES           | P2_POC    | VP-A/VP-C |                0.455 |                 0.000 |            0.512 |
| 14 | ES           | P2_POC    | VP-B/VP-C |                0.742 |                 0.000 |            0.652 |
| 15 | ES           | P4_POC    | VP-A/VP-B |                0.752 |                 0.020 |            0.390 |
| 16 | ES           | P4_POC    | VP-A/VP-C |                0.778 |                 0.000 |            0.591 |
| 17 | ES           | P4_POC    | VP-B/VP-C |                0.933 |                 0.000 |            0.679 |
| 18 | ES           | P2_VAH    | VP-A/VP-B |                0.624 |                 0.020 |            0.385 |
| 19 | ES           | P2_VAH    | VP-A/VP-C |                0.645 |                 0.020 |            0.432 |
| 20 | ES           | P2_VAH    | VP-B/VP-C |                0.889 |                 0.000 |            0.756 |
| 21 | ES           | P2_VAL    | VP-A/VP-B |                0.687 |                 0.020 |            0.386 |
| 22 | ES           | P2_VAL    | VP-A/VP-C |                0.712 |                 0.020 |            0.456 |
| 23 | ES           | P2_VAL    | VP-B/VP-C |                0.888 |                 0.000 |            0.747 |

PREFIX_INVARIANT = True

