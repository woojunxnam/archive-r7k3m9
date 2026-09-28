# TEST98_AUDIT_CORRECTION_1 - results (prereg b1ac158)

```json
{
 "CORRECTION": "TEST98_AUDIT_CORRECTION_1",
 "PREREG_COMMIT": "b1ac158",
 "PHASE1_RESULT_COMMIT": "91dbf4a",
 "CORRECTED_RUN_FEATURES_COHERENT": false,
 "PHASE1_CROSS_VALIDATION": "NOT RUN (Phase 1 used prior-session monthly expanding quantile boundaries, date-clustered bootstrap and calendar-year consistency; no chronological CV folds; ML not opened)",
 "FOLLOW_THROUGH_22_OF_37": "RAW_NEXT_BAR_STRONG_ASSOCIATION - not residualised against null F, not evaluated as chronological OOS prediction, not a deployable model",
 "PRECONFIRM_FEATURES_PREDICT_FOLLOWTHROUGH": "NO (preregistered economic definition)",
 "MULTIPLE_TESTING_NOTE": "74 primary coherence tests inspected; a naive 5% CI-only reference implies ~3.7 nominal CI hits under independence; the full coherence gate is much stricter and the tests are correlated, so 3.7 is NOT the expected number of full passes; actual full coherence passes = 0 (unchanged after this correction); no multiplicity threshold changed",
 "TEST98_STATUS": "CLOSED",
 "TEST98_SIMPLE_PRECONFIRM_PATH_FAMILY": "SATURATED",
 "TEST98_PORTFOLIO_SURVIVOR": "NO",
 "OPEN_ACCEPTANCE": "WEAK_RESEARCH_CLUE_ONLY",
 "ML_OPENED": "NO",
 "GA_OPENED": "NO",
 "DISTINCT_VARIANTS_TESTED": 37,
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1"
}
```

## Old (defective runmax) vs corrected within-window runs (pooled; excess vs null F)
|    | feature            |   max_value_at_events |   h6_rho |   h6_top_minus_bottom |   h6_ci_lo |   h6_ci_hi | h6_COHERENT   |   h12_rho |   h12_top_minus_bottom |   h12_ci_lo |   h12_ci_hi |   h12_years_same |   h12_inst_same | h12_COHERENT   |   h12_pstrong_diff |
|---:|:-------------------|----------------------:|---------:|----------------------:|-----------:|-----------:|:--------------|----------:|-----------------------:|------------:|------------:|-----------------:|----------------:|:---------------|-------------------:|
|  0 | PQ2_bullrun12      |               16.0000 |  -0.2000 |                0.0005 |    -0.0070 |     0.0081 | False         |    0.3000 |                 0.0011 |     -0.0107 |      0.0120 |                3 |               2 | False          |            -0.0123 |
|  1 | PQ2_hlrun12        |               20.0000 |   0.1000 |                0.0015 |    -0.0086 |     0.0118 | False         |    0.0000 |                 0.0057 |     -0.0095 |      0.0206 |                4 |               2 | False          |            -0.0022 |
|  2 | PQ2_bullrun12_CORR |               12.0000 |  -0.8000 |               -0.0018 |    -0.0115 |     0.0084 | False         |   -0.1000 |                -0.0012 |     -0.0158 |      0.0137 |                5 |               3 | False          |            -0.0024 |
|  3 | PQ2_hlrun12_CORR   |               12.0000 |   0.4000 |                0.0025 |    -0.0061 |     0.0108 | False         |    0.0000 |                 0.0057 |     -0.0074 |      0.0187 |                4 |               3 | False          |            -0.0007 |

## Corrected response curves
|    | feature            | horizon   |   bin |    n |      xF |   xF_ES |   xF_NQ |   xF_YM |   xF_RTY |
|---:|:-------------------|:----------|------:|-----:|--------:|--------:|--------:|--------:|---------:|
| 20 | PQ2_bullrun12_CORR | h6        |     0 | 1237 |  0.0010 | -0.0134 |  0.0012 |  0.0036 |   0.0053 |
| 21 | PQ2_bullrun12_CORR | h6        |     1 | 3360 |  0.0019 |  0.0031 | -0.0071 |  0.0059 |  -0.0021 |
| 22 | PQ2_bullrun12_CORR | h6        |     2 | 7503 |  0.0003 |  0.0005 | -0.0004 |  0.0015 |  -0.0002 |
| 23 | PQ2_bullrun12_CORR | h6        |     3 | 4152 | -0.0021 | -0.0020 | -0.0008 | -0.0089 |   0.0029 |
| 24 | PQ2_bullrun12_CORR | h6        |     4 | 6673 | -0.0008 | -0.0015 |  0.0020 | -0.0019 |  -0.0017 |
| 25 | PQ2_bullrun12_CORR | h12       |     0 | 1237 | -0.0035 | -0.0051 | -0.0045 |  0.0086 |  -0.0036 |
| 26 | PQ2_bullrun12_CORR | h12       |     1 | 3360 |  0.0002 |  0.0058 | -0.0243 |  0.0041 |  -0.0067 |
| 27 | PQ2_bullrun12_CORR | h12       |     2 | 7503 | -0.0009 |  0.0006 | -0.0030 | -0.0024 |   0.0012 |
| 28 | PQ2_bullrun12_CORR | h12       |     3 | 4152 |  0.0036 | -0.0104 |  0.0089 | -0.0029 |   0.0093 |
| 29 | PQ2_bullrun12_CORR | h12       |     4 | 6673 | -0.0047 | -0.0059 | -0.0041 | -0.0043 |  -0.0036 |
| 30 | PQ2_hlrun12_CORR   | h6        |     0 | 3022 | -0.0050 | -0.0033 | -0.0048 | -0.0144 |   0.0019 |
| 31 | PQ2_hlrun12_CORR   | h6        |     1 | 1413 |  0.0012 |  0.0286 |  0.0029 | -0.0073 | nan      |
| 32 | PQ2_hlrun12_CORR   | h6        |     2 | 4842 |  0.0022 | -0.0013 |  0.0033 |  0.0050 |   0.0034 |
| 33 | PQ2_hlrun12_CORR   | h6        |     3 | 5872 |  0.0031 |  0.0034 |  0.0002 |  0.0040 |   0.0055 |
| 34 | PQ2_hlrun12_CORR   | h6        |     4 | 7776 | -0.0025 | -0.0009 | -0.0001 | -0.0015 |  -0.0078 |
| 35 | PQ2_hlrun12_CORR   | h12       |     0 | 3022 | -0.0099 | -0.0067 | -0.0164 | -0.0213 |   0.0036 |
| 36 | PQ2_hlrun12_CORR   | h12       |     1 | 1413 |  0.0080 |  0.0391 |  0.0070 |  0.0117 | nan      |
| 37 | PQ2_hlrun12_CORR   | h12       |     2 | 4842 |  0.0035 | -0.0029 |  0.0128 |  0.0059 |   0.0055 |
| 38 | PQ2_hlrun12_CORR   | h12       |     3 | 5872 |  0.0012 |  0.0040 | -0.0030 |  0.0006 |   0.0038 |
| 39 | PQ2_hlrun12_CORR   | h12       |     4 | 7776 | -0.0042 | -0.0037 | -0.0025 | -0.0024 |  -0.0082 |
