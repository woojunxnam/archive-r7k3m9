# TEST65+ additive-alpha program - final report

```json
{
 "T61_R1C_FROZEN": "YES",
 "T61_R1C_MANIFEST_SHA256": "35456801e1f5624b91857a80f50c2a1c6b4c6fe6709f636f4ce69e61a7e8a9a8",
 "T61_R1C_HISTORICAL_AVG_DAY": 125.08,
 "T61_R1C_MAXDD": 12607,
 "T61_R1C_WORST_DAY": -4347,
 "T61_R1C_PEAK_MNQ": 6,
 "T61_R1C_PEAK_MES": 6,
 "T61_FORWARD_OOS_START": "2026-09-29",
 "FORWARD_SHADOW_HARNESS_READY": true,
 "FORWARD_SHADOW_QA": {
  "reproduction_maxabs_T61-R1C": 4.547473508864641e-13,
  "reproduction_maxabs_C43-CORE": 0.0,
  "prefix_rows_compared": 189,
  "prefix_max_abs_diff_by_col": {},
  "prefix_minute_mismatch_C43-CORE": 0,
  "prefix_minute_mismatch_T55": 0,
  "prefix_minute_mismatch_T61-R1C": 0,
  "PREFIX_INVARIANT": true,
  "REPRODUCES_FROZEN_HISTORY": true,
  "forward_fold_code_path_trades_by_module": "{'M1': 23, 'M2': 28, 'M3': 36, 'M4': 13}",
  "FAIL_CLOSED_ON_TAMPER": true
 },
 "TEST65": "MAP: T61 flat states have negative forward drift (exposure timing already efficient); largest residual = opening trend (AUC 0.58)",
 "TEST66": "FAIL early opening-trend (rule -0.41 $/day; ML +1.96 $/day, no plateau)",
 "TEST67": "FAIL ES turn-of-month (+3.77 $/day; plateau / ret-DD fail)",
 "TEST68": "FAIL MNQ secondary breakout ML (-0.65 $/day)",
 "TEST69": "FAIL ES pre-FOMC drift (-0.15 $/day)",
 "STOPPING_CRITERION": "B: >= 4 distinct families after TEST65 failed (early opening trend, ES calendar flow, secondary breakout, ES event drift)",
 "NEW_ADDITIVE_SURVIVOR": "NONE",
 "BEST_NEW_MODULE (non-passing, by incremental $/day)": "E67r_TOM_INTRADAY_ONLY_MES2",
 "BEST_NEW_MODULE_INCR_AVG_DAY": 6.31,
 "CORR_NEW_MODULE_TO_T61": 0.22,
 "T61_PLUS_NEW_MODULE": "n/a (no survivor)",
 "INCREMENTAL_AVG_DAY_OVER_T61": 0.0,
 "PEAK_MARGIN": "T61-R1C 30.6% NLV (unchanged)",
 "PEAK_MES": 6,
 "PEAK_MNQ": 6,
 "NEW_MODULE_OOS_START": "n/a",
 "GA_RUN": "NO (method order: GA only with signal; none found)",
 "BUDGET_TOTALS": {
  "hypotheses": 1394,
  "ml_configs": 189,
  "valid_genomes": 777629
 },
 "T61_OOS_DATA_USED_FOR_RESEARCH": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Incremental frontier (T61-R1C + module)

|    | test   | module                      |   incr_avg_day |   comb_avg_day |   comb_maxdd |   comb_worst |   comb_ret_dd |   corr_to_t61 | PASS   |
|---:|:-------|:----------------------------|---------------:|---------------:|-------------:|-------------:|--------------:|--------------:|:-------|
|  0 | TEST66 | E66_EARLY_OPENING_TREND     |         -0.410 |        124.673 |    12533.900 |    -4347.367 |         0.010 |         0.065 | False  |
|  1 | TEST66 | E66ML_META_LABELER          |          1.961 |        127.044 |    12750.680 |    -4347.367 |         0.010 |         0.111 | False  |
|  2 | TEST67 | E67_TOM_MES2                |          3.767 |        128.850 |    13018.282 |    -4890.220 |         0.010 |         0.262 | False  |
|  3 | TEST67 | E67r_TOM_INTRADAY_ONLY_MES2 |          6.306 |        131.389 |    12731.460 |    -4347.367 |         0.010 |         0.220 | False  |
|  4 | TEST67 | E67r_TOM_MNQ1               |          0.863 |        125.945 |    13434.420 |    -4347.367 |         0.009 |         0.245 | False  |
|  5 | TEST68 | E68ML_SECONDARY_BREAKOUT    |         -0.650 |        124.433 |    13208.960 |    -4347.367 |         0.009 |         0.125 | False  |
|  6 | TEST68 | E68r_ALL_BREAKS             |          4.602 |        129.685 |    12955.280 |    -4553.700 |         0.010 |         0.200 | False  |
|  7 | TEST69 | E69_PRE_FOMC_MES2           |         -0.152 |        124.931 |    12579.180 |    -4222.347 |         0.010 |         0.042 | False  |
|  8 | TEST69 | E69r_PRE_FOMC_MNQ1          |          0.145 |        125.228 |    12542.440 |    -4320.107 |         0.010 |         0.057 | False  |
|  9 | TEST69 | E69r_POST_STATEMENT_MES2    |         -1.325 |        123.758 |    13626.680 |    -6237.347 |         0.009 |         0.141 | False  |

## Research registry

|    | test   | family                                                          | prereg_sha                                                       | result                                                                                                                                                      | status   | utc                       |
|---:|:-------|:----------------------------------------------------------------|:-----------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|:--------------------------|
|  0 | TEST65 | T61 residual opportunity map (labels only)                      | c25145de97d25498c2af489c127002fa3213265fac41d961d186d4c9b5687338 | map built; TEST66 -> MISSED_OPENING_TREND (detectable & stable, max score)                                                                                  | MAP      | 2026-09-28T15:27:07+00:00 |
|  1 | TEST66 | early opening-trend participation (MNQ, 09:40, u<3)             | f2b483c1                                                         | FAIL: E66 rule -0.41 $/day, 2/5 folds, plateau fails; E66ML +1.96 $/day 4/5 folds, excess/SLIP4/delay pass but no preregistered plateau -> FAIL (no rescue) | REJECT   | 2026-09-28T15:29:37+00:00 |
|  2 | TEST67 | ES turn-of-month calendar flow (2 MES, td-1 open -> td+3 close) | 6f004e63                                                         | FAIL: +3.77 $/day, 4/5 folds, excess +2.1, SLIP4/delay ok, but plateau (td+4 = 57% of base) and comb ret/DD 0.00990 < 0.00992                               | REJECT   | 2026-09-28T15:31:13+00:00 |
|  3 | TEST68 | MNQ secondary session-high breakout, ML meta-label              | 75056bea                                                         | FAIL: ML -0.65 $/day 2/5 folds, all plateau neighbours negative; unfiltered breaks (report-only) +4.6 $/day but year share 0.62                             | REJECT   | 2026-09-28T15:31:50+00:00 |
|  4 | TEST69 | ES pre-FOMC drift (2 MES, 09:31 -> 13:55)                       | 76e8b531                                                         | FAIL: -0.15 $/day, 2/5 folds, excess < 0, plateau fails (54 events)                                                                                         | REJECT   | 2026-09-28T15:32:17+00:00 |

## Rejects

|    | family                             | test   | reason                                                                                                  | retest_forbidden                 | reopen_requires                                           |
|---:|:-----------------------------------|:-------|:--------------------------------------------------------------------------------------------------------|:---------------------------------|:----------------------------------------------------------|
|  0 | early_opening_trend_participation  | TEST66 | simple rule negative / plateau split; ML meta-label +2 $/day (1.6% of T61) without plateau              | YES (as MNQ opening-hour add-on) | new information source (order flow / breadth) not in OHLC |
|  1 | es_turn_of_month_flow              | TEST67 | small (+3.8 $/day), 2024 -3.3k, plateau fail, ret/DD not improved                                       | YES on 2019-2026-05 data         | forward evidence only                                     |
|  2 | nq_secondary_session_high_breakout | TEST68 | meta-label destroys value (detectability AUC did not convert to $); raw version concentrated in 2025-26 | YES                              | forward evidence of the raw trigger                       |
|  3 | es_pre_fomc_drift                  | TEST69 | no drift 2019-2026 (win 41%), excess < 0                                                                | YES                              | -                                                         |

## Clues

|    | clue_id                   | source_test          | clue                                                                                                                                                                                    | use                            |
|---:|:--------------------------|:---------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------|
|  0 | T65_FLAT_STATES_NEG_DRIFT | TEST65               | when T61 is flat (u=0) the forward excess drift to 16:15 / next open is NEGATIVE in every window; T61 exposure timing is already efficient -> no generic 'add when underexposed' module | reject generic exposure fill   |
|  1 | T65_OPENING_TREND_GAP     | TEST65               | MISSED_OPENING_TREND: 290 events (42/yr), hypothetical potential 195 $/day, clean-forward detectability median AUC 0.58 (5/5 folds >0.52), lift 1.16                                    | TEST66                         |
|  2 | T65_NQ_SECONDARY_BREAKOUT | TEST65               | post-10:30 secondary session-high break (>=60m after prior high): AUC 0.61 5/5 folds, trigger mean fwd +0.024 ATR, potential 56 $/day                                                   | TEST68 candidate               |
|  3 | T65_LATE_CONT             | TEST65               | late RTH continuation (session up, W4/W5): AUC 0.587 5/5, potential 56 $/day                                                                                                            | candidate                      |
|  4 | T65_ES_INDEP_SMALL        | TEST65               | ES-independent windows rare (10 events, 2 $/day potential) though detectable (AUC 0.59)                                                                                                 | TEST67 (ES-specific) low prior |
|  5 | T65_EARLY_EXIT_NO         | TEST65               | T61 reductions are not followed by continuation (trigger mean fwd -0.017 ATR, AUC 0.49)                                                                                                 | no hold-extension module       |
|  6 | T66_ML_OPENING_SMALL      | TEST66               | ML meta-label opening entry (09:35) +1.96 $/day, 4/5 folds, excess +1.9, corr 0.11: real but economically negligible vs T61 125 $/day                                                   | none (too small)               |
|  7 | T67_TOM_INTRADAY          | TEST67 (report-only) | TOM sessions intraday-only 2 MES: +6.3 $/day, ret/DD 0.0103 but 3/5 folds; overnight part adds tail (-3.2k) not return                                                                  | no rescue; record only         |
|  8 | T68_AUC_NOT_DOLLARS       | TEST68               | classification AUC 0.61 on a >=0.3 ATR label did not translate into $ (label = magnitude/vol, not direction); future detectability screens must use $-expectancy labels                 | method lesson                  |
|  9 | T68_RAW_BREAKS            | TEST68 (report-only) | all secondary breaks 2021+: +4.6 $/day, 4/5 folds, excess +3.4, corr 0.20, 2025-26 = 62%                                                                                                | forward monitor only           |

