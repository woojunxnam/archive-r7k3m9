# AUDIT 5 — D7 frozen practical carrier — results (prereg bcee7ee)

D7 (2,393 signals, 2272 filled after Main-priority capacity): **+5.04 $/day, SLIP4 -1.92**, delay +4.41, missed-20% +3.72,
remove-top3 +1321, folds 3/5 (O1 -4.5, O2 +16.5, O3 +0.9, O4 -4.7, O5 +13.7), 2022 +4140, MaxDD 5910, worst day -2304,
corr Main 0.36, loss-day Jaccard 0.39, **mean on Main's bottom-5% days -133 $** (adds to Main's worst days), turnover 1.67 trades/day.
MAIN + D7: 156.82 $/day, MaxDD 16743 (vs 13936), worst -6060 (vs -4666), ret/DD 0.00937 (vs 0.01089).
The earlier PH5 +9.20 $/day was pre-capacity; with Main priority and SLIP4 the carrier is negative and worsens Main's tail.

**D7_PRACTICAL_CARRIER_STATUS = D7_PRACTICAL_CARRIER_FAIL** (stress fail: SLIP4 < 0; no route A / B / C).

## Affected portfolio comparisons (report only, integrated allocator)
| portfolio | avg/day | incr | SLIP4 | MaxDD | worst | ret/DD | risk-norm incr | routes A/B/C |
|---|---|---|---|---|---|---|---|---|
| MAIN + D7 | 156.82 | +5.04 | 149.86 | 16743 | -6060 | 0.00937 | -15.24 | False/False/False |
| MAIN + C2 | 156.74 | +4.96 | 155.02 | 13980 | -4728 | 0.01121 | +3.21 | False/True/False |
| MAIN + C2+D7 | 161.44 | +9.66 | 152.77 | 16786 | -6060 | 0.00962 | -12.73 | False/False/False |
| MAIN + C2+W1 | 160.65 | +8.88 | 157.36 | 14105 | -4792 | 0.01139 | +4.99 | True/True/False |
| MAIN + C2+W1+D7 | 165.28 | +13.50 | 155.07 | 16569 | -6060 | 0.00998 | -9.16 | False/False/False |

```json
{
 "D7": {
  "signals": 2393,
  "trades_after_capacity": 2272,
  "avg_day": 5.044463235294127,
  "slip4": -1.9161985294117547,
  "delay1": 4.411382352941182,
  "missed20": 3.7172941176470604,
  "remove_top3": 1320.890000000013,
  "folds": {
   "O1": -4.540474308300352,
   "O2": 16.495219123505983,
   "O3": 0.8865737051793072,
   "O4": -4.664444444444458,
   "O5": 13.659546742209628
  },
  "folds_pos": 3,
  "y2022": 4140.300000000002,
  "max_dd": 5909.759999999999,
  "worst_day": -2303.710000000001,
  "corr_main": 0.3615307177132417,
  "turnover_trades_per_day": 1.6705882352941177,
  "loss_jaccard": 0.38609112709832133,
  "d7_mean_on_main_bottom5": -132.5095588235294,
  "comb_avg_day": 156.82397956287514,
  "comb_max_dd": 16743.062365193015,
  "comb_worst": -6059.596893120728,
  "comb_ret_dd": 0.009366505131635594,
  "main_ret_dd": 0.01089094598770062,
  "main_max_dd": 13936.302365192969,
  "main_worst": -4666.439999999971,
  "peaks": {
   "MES": 4,
   "MNQ": 3,
   "MYM": 4,
   "M2K": 4
  },
  "incr": 5.044463235294103,
  "STRESS_PASS": false,
  "ROUTE_B": false,
  "ROUTE_C": false,
  "D7_PRACTICAL_CARRIER_STATUS": "D7_PRACTICAL_CARRIER_FAIL"
 },
 "portfolios": {
  "D7": {
   "avg_day": 156.82397956287514,
   "incr": 5.044463235294103,
   "slip4_avg_day": 149.86331779816928,
   "max_dd": 16743.062365193015,
   "worst_day": -6059.596893120728,
   "ret_dd": 0.009366505131635594,
   "corr_main_cand": 0.3615307177132417,
   "route_A": false,
   "route_B": false,
   "route_C": false,
   "per10k_dd": 93.66505131635594,
   "risk_normalized_increment": -15.244408560650257,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 4,
   "peak_M2K": 4,
   "cand_margin_peak_approx": 12700
  },
  "C2": {
   "avg_day": 156.74216338640454,
   "incr": 4.9626470588235065,
   "slip4_avg_day": 155.01826632758102,
   "max_dd": 13979.562365192993,
   "worst_day": -4727.67999999997,
   "ret_dd": 0.01121223678479871,
   "corr_main_cand": 0.25731399678829553,
   "route_A": false,
   "route_B": true,
   "route_C": false,
   "per10k_dd": 112.1223678479871,
   "risk_normalized_increment": 3.2129079709809076,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 1,
   "peak_M2K": 1,
   "cand_margin_peak_approx": 5400
  },
  "C2+D7": {
   "avg_day": 161.44300897463987,
   "incr": 9.663492647058831,
   "slip4_avg_day": 152.77389132758103,
   "max_dd": 16786.32236519301,
   "worst_day": -6059.596893120728,
   "ret_dd": 0.009617532980862875,
   "corr_main_cand": 0.3988936241637639,
   "route_A": false,
   "route_B": false,
   "route_C": false,
   "per10k_dd": 96.17532980862875,
   "risk_normalized_increment": -12.734130068377453,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 4,
   "peak_M2K": 4,
   "cand_margin_peak_approx": 12700
  },
  "C2+W1": {
   "avg_day": 160.6549060334634,
   "incr": 8.875389705882355,
   "slip4_avg_day": 157.36372956287514,
   "max_dd": 14105.269999999935,
   "worst_day": -4791.919999999968,
   "ret_dd": 0.011389707962588744,
   "corr_main_cand": 0.27346480557244396,
   "route_A": true,
   "route_B": true,
   "route_C": false,
   "per10k_dd": 113.89707962588744,
   "risk_normalized_increment": 4.987619748881244,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 2,
   "peak_M2K": 2,
   "cand_margin_peak_approx": 10800
  },
  "C2+W1+D7": {
   "avg_day": 165.28361191581632,
   "incr": 13.504095588235288,
   "slip4_avg_day": 155.07478838640458,
   "max_dd": 16569.11236519296,
   "worst_day": -6059.596893120728,
   "ret_dd": 0.009975405336922614,
   "corr_main_cand": 0.40066355018597477,
   "route_A": false,
   "route_B": false,
   "route_C": false,
   "per10k_dd": 99.75405336922614,
   "risk_normalized_increment": -9.155406507780057,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 4,
   "peak_M2K": 4,
   "cand_margin_peak_approx": 15400
  }
 }
}
```
