# TEST95+ canonical momentum / trend / breakout + INDEX6 integration - final

Prereg sha256 `ba5521152b6494dfb0c89f957a2e23a0e748fedf8e2ccb6db8e354d7317ef041`.  Baseline MAIN_GROWTH_V1 (frozen, unmodified).  Research data <= 2026-05-27.  NEW_OOS_OPENED = NO, LIVE_AUTHORIZATION = NO.

## Track A - all preregistered cells

|    | module            |   trades |   avg_day |   avg_day_2021 |   matched_A_day |   momentum_B_day |   folds_pos |   slip4_day | plateau_pass   |   corr_to_main |   main_plus_ret_dd |   main_ret_dd | STANDALONE_PASS   | PORTFOLIO_PASS   |
|---:|:------------------|---------:|----------:|---------------:|----------------:|-----------------:|------------:|------------:|:---------------|---------------:|-------------------:|--------------:|:------------------|:-----------------|
|  0 | T1_P_ENGULF_ES    |     1501 |    -3.121 |         -3.264 |          -0.575 |           -1.545 |           0 |      -9.488 | False          |          0.105 |              0.010 |         0.010 | False             | False            |
|  1 | T1_P_RESUME_ES    |     1278 |    -2.155 |         -3.058 |          -0.225 |           -0.657 |           1 |      -7.579 | False          |          0.118 |              0.010 |         0.010 | False             | False            |
|  2 | T1_P_BREAK_ES     |      438 |    -1.052 |         -0.793 |          -0.462 |           -0.470 |           1 |      -2.900 | False          |          0.061 |              0.010 |         0.010 | False             | False            |
|  3 | T2A_PREMKT59_ES   |     1199 |    -3.340 |         -3.317 |          -1.054 |           -1.792 |           0 |      -8.505 | False          |         -0.005 |              0.010 |         0.010 | False             | False            |
|  4 | T2B_PREMKT59_ES   |     1199 |    -1.951 |         -1.747 |           0.026 |           -2.115 |           1 |      -7.116 | False          |          0.107 |              0.010 |         0.010 | False             | False            |
|  5 | T1_P_ENGULF_MNQ   |     1327 |    -2.433 |         -2.054 |          -1.353 |           -2.537 |           0 |      -4.674 | False          |          0.121 |              0.010 |         0.010 | False             | False            |
|  6 | T1_P_RESUME_MNQ   |     1283 |    -4.135 |         -3.799 |          -3.507 |           -4.880 |           2 |      -6.306 | False          |          0.159 |              0.010 |         0.010 | False             | False            |
|  7 | T1_P_BREAK_MNQ    |      437 |    -0.729 |         -0.281 |          -0.493 |           -0.834 |           3 |      -1.471 | False          |          0.088 |              0.010 |         0.010 | False             | False            |
|  8 | T2A_PREMKT59_MNQ  |     1243 |    -4.027 |         -4.691 |          -3.075 |           -4.825 |           0 |      -6.169 | False          |          0.022 |              0.010 |         0.010 | False             | False            |
|  9 | T2B_PREMKT59_MNQ  |     1243 |     0.527 |          0.013 |           1.092 |           -4.387 |           2 |      -1.615 | True           |          0.093 |              0.010 |         0.010 | False             | False            |
| 10 | L3_MKEY_ES        |       11 |     0.139 |          0.140 |          -2.142 |          nan     |           1 |       0.091 | True           |          0.387 |              0.010 |         0.010 | False             | False            |
| 11 | L2_MKEY_ES        |       20 |     0.431 |         -1.761 |          -6.911 |          nan     |           2 |       0.345 | True           |          0.537 |              0.009 |         0.010 | False             | False            |
| 12 | L2B_MKEY_ES       |       40 |     3.483 |          1.677 |          -7.027 |          nan     |           2 |       3.310 | True           |          0.565 |              0.009 |         0.010 | False             | False            |
| 13 | L3_INTRADAY5M_ES  |      193 |    -2.795 |         -2.544 |          -2.774 |           -1.939 |           0 |      -3.618 | False          |          0.180 |              0.010 |         0.010 | False             | False            |
| 14 | L3_MKEY_MNQ       |       20 |     2.104 |         -0.056 |          -0.876 |          nan     |           3 |       2.070 | False          |          0.242 |              0.010 |         0.010 | False             | False            |
| 15 | L2_MKEY_MNQ       |       15 |     7.062 |          5.044 |           5.684 |          nan     |           4 |       7.036 | False          |          0.279 |              0.010 |         0.010 | False             | False            |
| 16 | L2B_MKEY_MNQ      |       46 |     7.188 |          1.517 |          -1.942 |          nan     |           4 |       7.109 | True           |          0.379 |              0.008 |         0.010 | False             | False            |
| 17 | L3_INTRADAY5M_MNQ |      203 |    -3.406 |         -3.632 |          -4.368 |           -2.669 |           3 |      -3.754 | False          |          0.206 |              0.010 |         0.010 | False             | False            |

## L5 per-unit ledger

|    | module     |   unit |   n |   usd_per_trade |     total |   per_day |
|---:|:-----------|-------:|----:|----------------:|----------:|----------:|
|  0 | L5_L3_ES   |      1 |  11 |         165.965 |  1825.610 |     1.049 |
|  1 | L5_L3_ES   |      2 |   5 |         -38.315 |  -191.575 |    -0.110 |
|  2 | L5_L3_ES   |      3 |   4 |         -83.428 |  -333.710 |    -0.192 |
|  3 | L5_L3_ES   |      4 |   2 |        -193.115 |  -386.230 |    -0.222 |
|  4 | L5_L2_ES   |      1 |  20 |          50.132 |  1002.637 |     0.576 |
|  5 | L5_L2_ES   |      2 |   9 |         115.316 |  1037.840 |     0.596 |
|  6 | L5_L2_ES   |      3 |   5 |        -304.590 | -1522.950 |    -0.875 |
|  7 | L5_L2_ES   |      4 |   2 |        -192.490 |  -384.980 |    -0.221 |
|  8 | L5_L2B_ES  |      1 |  40 |         157.904 |  6316.143 |     3.628 |
|  9 | L5_L2B_ES  |      2 |   9 |         115.316 |  1037.840 |     0.596 |
| 10 | L5_L2B_ES  |      3 |   5 |        -304.590 | -1522.950 |    -0.875 |
| 11 | L5_L2B_ES  |      4 |   2 |        -192.490 |  -384.980 |    -0.221 |
| 12 | L5_L3_MNQ  |      1 |  21 |         173.644 |  3646.528 |     2.095 |
| 13 | L5_L3_MNQ  |      2 |   2 |        1406.510 |  2813.020 |     1.616 |
| 14 | L5_L3_MNQ  |      3 |   2 |         176.160 |   352.320 |     0.202 |
| 15 | L5_L2_MNQ  |      1 |  15 |         865.900 | 12988.500 |     7.460 |
| 16 | L5_L2_MNQ  |      2 |   4 |         922.460 |  3689.840 |     2.119 |
| 17 | L5_L2_MNQ  |      3 |   1 |         144.835 |   144.835 |     0.083 |
| 18 | L5_L2B_MNQ |      1 |  46 |         287.150 | 13208.885 |     7.587 |
| 19 | L5_L2B_MNQ |      2 |   4 |         922.460 |  3689.840 |     2.119 |
| 20 | L5_L2B_MNQ |      3 |   1 |         144.835 |   144.835 |     0.083 |

## Market Key state-transition diagnostic (daily, R = 2 ATR20; forward 16:15 -> 16:15 return in ATR; descriptive only)

|    | instrument   | state    |    n |   fwd1_atr |     t1 |   fwd5_atr |   up1_share |
|---:|:-------------|:---------|-----:|-----------:|-------:|-----------:|------------:|
|  0 | ES           | ALL      | 1732 |      0.034 |  1.772 |      0.156 |       0.544 |
|  1 | ES           | in_UT    |  470 |     -0.001 | -0.025 |      0.097 |       0.519 |
|  2 | ES           | in_NRE   |  410 |      0.073 |  1.585 |      0.044 |       0.571 |
|  3 | ES           | in_NRA   |  715 |      0.025 |  0.954 |      0.215 |       0.545 |
|  4 | ES           | in_DT    |  137 |      0.083 |  0.934 |      0.385 |       0.540 |
|  5 | ES           | UT->NRE  |   42 |      0.125 |  0.693 |      0.321 |       0.667 |
|  6 | ES           | NRE->NRA |   87 |     -0.055 | -0.602 |     -0.100 |       0.529 |
|  7 | ES           | NRE->DT  |   31 |      0.042 |  0.194 |      0.137 |       0.484 |
|  8 | ES           | NRA->UT  |   39 |     -0.116 | -0.921 |      0.425 |       0.436 |
|  9 | ES           | NRA->NRE |   80 |     -0.010 | -0.089 |      0.157 |       0.525 |
| 10 | ES           | NRA->DT  |    5 |     -0.266 | -0.310 |      0.840 |       0.600 |
| 11 | ES           | DT->NRA  |   37 |     -0.071 | -0.359 |     -0.130 |       0.432 |
|  0 | MNQ          | ALL      | 1732 |      0.045 |  2.412 |      0.212 |       0.554 |
|  1 | MNQ          | in_UT    |  386 |     -0.011 | -0.293 |     -0.060 |       0.513 |
|  2 | MNQ          | in_NRE   |  483 |      0.088 |  2.282 |      0.263 |       0.578 |
|  3 | MNQ          | in_NRA   |  751 |      0.033 |  1.276 |      0.302 |       0.554 |
|  4 | MNQ          | in_DT    |  112 |      0.126 |  1.433 |      0.333 |       0.598 |
|  5 | MNQ          | UT->NRE  |   44 |      0.136 |  0.904 |      0.368 |       0.659 |
|  6 | MNQ          | NRE->NRA |   91 |     -0.003 | -0.029 |      0.192 |       0.549 |
|  7 | MNQ          | NRE->DT  |   24 |     -0.074 | -0.404 |      0.121 |       0.583 |
|  8 | MNQ          | NRA->UT  |   41 |      0.093 |  1.403 |      0.165 |       0.537 |
|  9 | MNQ          | NRA->NRE |   74 |      0.087 |  0.819 |      0.324 |       0.608 |
| 10 | MNQ          | DT->NRA  |   28 |     -0.101 | -0.559 |     -0.461 |       0.536 |

## Status

```json
{
 "PREREGISTRATION_SHA256": "ba5521152b6494dfb0c89f957a2e23a0e748fedf8e2ccb6db8e354d7317ef041",
 "RESEARCH_DATA_END": "2026-05-27",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "CURRENT_MAIN": "MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged)",
 "TRACK_A": {
  "families_tested": [
   "T1_HTF_LTF (ENGULF / RESUME / BREAK)",
   "T2_PREMARKET59 (T2A / T2B) vs C_ORB",
   "L1-L4 daily Market Key (L2 / L2B / L3, state exit vs fixed holds)",
   "L3 intraday 5m Market Key [HYP]",
   "L5 staged accumulation"
  ],
  "cells": 18,
  "standalone_pass": 0,
  "portfolio_pass": 0,
  "best_net_cell": {
   "module": "L2B_MKEY_MNQ",
   "avg_day": 7.188489373923036,
   "trades": 46,
   "matched_A_day": -1.942085141587291
  },
  "T3_WINNER_PRESS": "NOT RUN - no T1 / T2 base passed (prereg condition)",
  "L5_ADD1": {
   "L5_L3_ES": -38.3,
   "L5_L2_ES": 115.3,
   "L5_L2B_ES": 115.3,
   "L5_L3_MNQ": 1406.5,
   "L5_L2_MNQ": 922.5,
   "L5_L2B_MNQ": 922.5
  },
  "L5_verdict": "ES ADD1 <= 0 on L3 -> ladder stops (prereg); MNQ / L2 ADD1 > 0 but n = 2-9 units -> not estimable",
  "ML_GA": "NOT RUN - no deterministic family with positive net AND positive matched excess AND the minimum sample (only L2_MKEY_MNQ: +7.1/day, matched +5.7/day but 15 trades vs >= 150 floor); ML on 15 events is not estimable",
  "STOP_REASON": ">= 4 distinct canonical families failed without a new clue (prereg stopping rule)",
  "CANONICAL_SURVIVOR": "NONE"
 },
 "TRACK_B": {
  "INDEX6_PARITY_STATUS": {
   "LC02": "BLOCKED (precision 0.978 < threshold)",
   "LC03": "BLOCKED (recall 0.970, price parity 0.771)",
   "LC05": "BLOCKED (needs canonical NQ volume; NQ transfer blocked)",
   "TS16-S01": "STRUCTURALLY EXCLUDED (OI unavailable; amendment)",
   "TS22-S01": "BLOCKED (ledger / TradingView parity export not recovered)",
   "T30-W01": "BLOCKED (needs YM / RTY + exact W01 selector)"
  },
  "RECOVERED_EXACT": [],
  "RESEARCH_ONLY_APPROX": [
   "LC02",
   "LC03 (TEST46 sanitized ledgers, not authorizing)"
  ],
  "BLOCKED": [
   "LC05",
   "TS22-S01",
   "T30-W01"
  ],
  "TEST20_L2_ONLY": "BLOCKED - semantics live in Google Docs dated after 2026-05-27 (sealed-window risk; not read)",
  "T20_V1_TS20_E01A": "BLOCKED - same reason; Pine source located (metadata only)",
  "INDEX5_NOOI_RECOVERED": "NO",
  "INDEX6_CURRENT_MAIN_COMBINATION_TESTED": "NO",
  "INDEX5_CURRENT_MAIN_COMBINATION_TESTED": "NO",
  "B0-B5_candidates": "only B0 (MAIN) evaluable; B1-B5 NOT TESTED (no exact member ledgers)",
  "INDEX_PORTFOLIO_PROMOTABLE": "NO"
 },
 "TRACK_C": {
  "C0_YM_DATA": "BLOCKED - canonical_1m_YM.parquet exists (manifest SHA edde4419...) as 6 x 7.5 MB Drive chunks; every chunk download fails ('MCP server Google_Drive session expired', retried after reconnect this session); RTY identical",
  "C0_REQUIRED_USER_ACTION": "re-split YM / RTY / NQ parquet into <= 1 MB chunks (exact bytes) with a SPLIT_MANIFEST (sha256 per chunk + whole file)",
  "C1_LEGACY_YM (TS13-S01 / TS21-S01)": "NOT RECOVERED - no YM data",
  "C2-C5": "NOT RUN",
  "YM_DIVERSIFIER_FOUND": "NO"
 }
}
```

