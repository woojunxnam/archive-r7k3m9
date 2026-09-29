# AUTONOMOUS_ALPHA_RESEARCH_MASTER_PROGRAM_V1 — final report

```json
{
 "CURRENT_OFFICIAL_MAIN": "MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged)",
 "MAIN_AVG_DAY": 143.21,
 "MAIN_AVG_DAY_2021": 151.78,
 "MAIN_MAXDD": 13936.0,
 "MAIN_WORST_DAY": -4666.0,
 "MAIN_RET_DD": 0.01028,
 "INDEX_RESEARCH_FRONTIER_MEMBERS": "CURRENT_LOCKED_MAIN only",
 "CURRENT_FRONTIER_AVG_DAY": 143.21,
 "GAP_TO_600": 456.79,
 "MAIN_DD_NORMALIZED_AVG_DAY": 102.76,
 "LINEAR_SCALE_FOR_600": 4.19,
 "SCALING_NOTE": "report-only; k>1 exceeds MNQ<=6 / MES<=8 caps; MaxDD scales to ~58.4k at k=4.19",
 "TARGET_600_REACHED": "NO",
 "INDEX_TARGET_600_NOT_REACHED": "YES",
 "INDEX_RESEARCH_SATURATED": "YES (all core families first-passed; 0 EVENT_CLUE survived as non-duplicate; reserve R1 pooled clue unresolved)",
 "STOP_CONDITION": "A (core complete) + B (saturated)",
 "NEW_SURVIVORS": 0,
 "PORTFOLIO_ADDITIVE_SURVIVORS": 0,
 "STRONG_CLUES": "TEST106 A2 ACD A-up 60m (RESEARCH_DUPLICATE of ORB, ~$1/day economics)",
 "BEST_WEAK_CLUES": "trapped-seller failure structures: TEST103 P2 (second resumption after failed first), TEST104 L2 (failed breakdown reclaim-retest, 15/15 cells positive), RESERVE_R1 union (120m xF +0.0119, CI lo -0.0006; gross < cost)",
 "TESTS": {
  "TEST99": "REJECT (HTF1 WEAK_RESEARCH_CLUE_ONLY)",
  "TEST100": "REJECT (0/18 EVENT_CLUE; V1_K3 / V2_K6 60m WEAK_RESEARCH_CLUE_ONLY)",
  "TEST101": "REJECT (0/18 EVENT_CLUE; AV_OR30 WEAK_RESEARCH_CLUE_ONLY at all 3 primary horizons)",
  "TEST102": "REJECT (S1 not COHERENT; S2/S3 0/9 EVENT_CLUE; S4 NOT_RUN_BY_RULE)",
  "TEST103": "REJECT by ESP-1 (0/12 EVENT_CLUE); second-entry forms = WEAK_RESEARCH_CLUE_ONLY (best of program so far)",
  "TEST104": "REJECT by ESP-1 (0/39 EVENT_CLUE); L2 failed-breakdown-reclaim-retest = WEAK_RESEARCH_CLUE_ONLY, family-consistent",
  "TEST105": "NOT_RUN_BY_RULE",
  "TEST106": "A2 = STRONG_CLUE at 60m (event level) BUT RESEARCH_DUPLICATE of plain ORB; no strategy phase",
  "TEST107": "NOT_RUN_BY_RULE",
  "TEST108": "REJECT (0/12 curves COHERENT; VETO_HAS_VALUE = NO everywhere)",
  "TEST109": "REJECT (0/18 EVENT_CLUE): FVG adds nothing beyond matched displacement",
  "TEST110": "NOT_RUN_BY_RULE",
  "TEST111": "NOT_RUN_BY_RULE",
  "TEST113": "NOT_RUN_BY_RULE",
  "TEST112": "REJECT (0/3 states COHERENT; no overlay applied)",
  "TEST114": "REJECT (sign-reversed in 2019-2026 index futures; not a duplicate - worse than the TEST49-style control)",
  "TEST115": "REJECT (0/8 curves COHERENT; STRENGTH_ADDS_VALUE = NO)",
  "TEST116": "NOT_RUN_BY_DUPLICATION",
  "RESERVE_R1": "REJECT by ESP-1 (WEAK_RESEARCH_CLUE_ONLY at all 3 primary horizons; SELECTION_EXPOSED)",
  "TEST117": "FRONTIER UNCHANGED = CURRENT_LOCKED_MAIN; INDEX_TARGET_600_NOT_REACHED"
 },
 "CUM_DISTINCT_HYPOTHESES": 71,
 "CUM_LEDGER_ROWS_REGISTRY": 1879,
 "MASTER_RESEARCH_LEDGER_ROWS": 1120,
 "CUM_ML_CONFIGS": 0,
 "CUM_GA_GENOMES": 0,
 "BUDGET_USED": "71/400 definitions, 0/60 ML configs, 0/2400 GA genomes (ML/GA gates never met: no family null survived)",
 "SATURATED_FAMILIES": [
  "HTF momentum scaling",
  "VWAP trend-side state",
  "event-anchored VWAP",
  "ATR phase / EMA ribbon",
  "complex pullback / second entry",
  "level interaction factory",
  "Fisher ACD opening auction",
  "range budget veto",
  "ICT falsification mini-lane",
  "reduce-only portfolio risk overlay",
  "academic intraday close momentum (GHLZ)",
  "HTF trend-strength / stage factory",
  "trapped-seller failure union (reserve)"
 ],
 "CROSS_ASSET_RESEARCH_OPENED": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "RESEARCH_DATA_END": "2026-05-27",
 "T61_FORWARD_OOS_USED": "NO"
}
```

## Test registry

|    | test       | family                                  | status   | classification                                                                                                                                                                                                                                                                                                      | prereg_sha      | result_sha               |   distinct_definitions |   ledger_rows |   ml_configs |   ga_genomes | best_clue           |   note |
|---:|:-----------|:----------------------------------------|:---------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------|:-------------------------|-----------------------:|--------------:|-------------:|-------------:|:--------------------|-------:|
|  0 | TEST99     | HTF momentum scaling                    | DONE     | REJECT (HTF1 WEAK_RESEARCH_CLUE_ONLY)                                                                                                                                                                                                                                                                               | b8da734         | see MASTER_COMMIT_LEDGER |                      9 |           240 |            0 |            0 | HTF1 30m 16:15 weak |    nan |
|  1 | TEST100    | VWAP trend-side state                   | DONE     | REJECT (0/18 EVENT_CLUE; V1_K3 / V2_K6 60m WEAK_RESEARCH_CLUE_ONLY)                                                                                                                                                                                                                                                 | b69e62e         | see MASTER_COMMIT_LEDGER |                      6 |           120 |            0 |            0 | V2_K6               |    nan |
|  2 | TEST101    | event-anchored VWAP                     | DONE     | REJECT (0/18 EVENT_CLUE; AV_OR30 WEAK_RESEARCH_CLUE_ONLY at all 3 primary horizons)                                                                                                                                                                                                                                 | 53bc874         | see MASTER_COMMIT_LEDGER |                      6 |           120 |            0 |            0 | AV_OR30             |    nan |
|  3 | TEST102    | ATR phase / EMA ribbon                  | DONE     | REJECT (S1 not COHERENT; S2/S3 0/9 EVENT_CLUE; S4 NOT_RUN_BY_RULE)                                                                                                                                                                                                                                                  | 3a389ea         | see MASTER_COMMIT_LEDGER |                      4 |           160 |            0 |            0 | S3_E21              |    nan |
|  4 | TEST103    | complex pullback / second entry         | DONE     | REJECT by ESP-1 (0/12 EVENT_CLUE); second-entry forms = WEAK_RESEARCH_CLUE_ONLY (best of program so far)                                                                                                                                                                                                            | b9d9db6         | see MASTER_COMMIT_LEDGER |                      4 |            80 |            0 |            0 | P2_FAILED_FIRST     |    nan |
|  5 | TEST104    | level interaction factory               | DONE     | REJECT by ESP-1 (0/39 EVENT_CLUE); L2 failed-breakdown-reclaim-retest = WEAK_RESEARCH_CLUE_ONLY, family-consistent                                                                                                                                                                                                  | 3ead923         | see MASTER_COMMIT_LEDGER |                     15 |           460 |            0 |            0 | L2_SWL60            |    nan |
|  6 | TEST105    | level failure deep branch               | NOT_RUN  | NOT_RUN_BY_RULE (no coherent L2/L3 EVENT_CLUE in TEST104)                                                                                                                                                                                                                                                           | rule in 3ead923 | nan                      |                      0 |             0 |            0 |            0 | nan                 |    nan |
|  7 | TEST106    | Fisher ACD opening auction              | DONE     | A2 = STRONG_CLUE at 60m (event level) BUT RESEARCH_DUPLICATE of plain ORB; no strategy phase                                                                                                                                                                                                                        | 7363e7c         | see MASTER_COMMIT_LEDGER |                      5 |           100 |            0 |            0 | A2_A_UP_IMMEDIATE   |    nan |
|  8 | TEST107    | response speed / time-to-MFE            | NOT_RUN  | NOT_RUN_BY_RULE (no survivor; only STRONG_CLUE is a RESEARCH_DUPLICATE)                                                                                                                                                                                                                                             | rule in 319a7f6 | nan                      |                      0 |             0 |            0 |            0 | nan                 |    nan |
|  9 | TEST108    | range budget veto                       | DONE     | REJECT (0/12 curves COHERENT; VETO_HAS_VALUE = NO everywhere)                                                                                                                                                                                                                                                       | 4951038         | see MASTER_COMMIT_LEDGER |                      4 |           400 |            0 |            0 | none                |    nan |
| 10 | TEST109    | ICT falsification mini-lane             | DONE     | REJECT (0/18 EVENT_CLUE): FVG adds nothing beyond matched displacement                                                                                                                                                                                                                                              | a05fae4         | see MASTER_COMMIT_LEDGER |                      6 |           120 |            0 |            0 | CHOCH_15m           |    nan |
| 11 | TEST110    | bounded recovery inventory              | NOT_RUN  | NOT_RUN_BY_RULE (no positive validated base)                                                                                                                                                                                                                                                                        | rule in 319a7f6 | nan                      |                      0 |             0 |            0 |            0 | nan                 |    nan |
| 12 | TEST111    | survivor-only overnight extension       | NOT_RUN  | NOT_RUN_BY_RULE (no survivor)                                                                                                                                                                                                                                                                                       | rule in 319a7f6 | nan                      |                      0 |             0 |            0 |            0 | nan                 |    nan |
| 13 | TEST113    | cross-index synchrony                   | NOT_RUN  | NOT_RUN_BY_RULE (no non-duplicate EVENT_CLUE mechanism)                                                                                                                                                                                                                                                             | rule in 319a7f6 | nan                      |                      0 |             0 |            0 |            0 | nan                 |    nan |
| 14 | TEST112    | reduce-only portfolio risk overlay      | DONE     | REJECT (0/3 states COHERENT; no overlay applied)                                                                                                                                                                                                                                                                    | 91532f1         | see MASTER_COMMIT_LEDGER |                      3 |            15 |            0 |            0 | none                |    nan |
| 15 | TEST114    | academic intraday close momentum (GHLZ) | DONE     | REJECT (sign-reversed in 2019-2026 index futures; not a duplicate - worse than the TEST49-style control)                                                                                                                                                                                                            | ac38e48         | see MASTER_COMMIT_LEDGER |                      4 |             4 |            0 |            0 | none                |    nan |
| 16 | TEST115    | HTF trend-strength / stage factory      | DONE     | REJECT (0/8 curves COHERENT; STRENGTH_ADDS_VALUE = NO)                                                                                                                                                                                                                                                              | 28b77c2         | see MASTER_COMMIT_LEDGER |                      4 |            40 |            0 |            0 | none                |    nan |
| 17 | TEST116    | temporal exhaustion (DeMark-inspired)   | NOT_RUN  | NOT_RUN_BY_DUPLICATION (no NOVELTY_DELTA_VS_TEST46_47: a TD buy-setup count of consecutive closes below close[t-4] is a serial-weakness exhaustion count, the same mechanism as TEST47 NASSI N3 serial-leg selling exhaustion and TEST46 range-exhaustion reversal; budget-pressure order also skips TEST116 first) | rule in 319a7f6 | nan                      |                      0 |             0 |            0 |            0 | nan                 |    nan |
| 18 | RESERVE_R1 | trapped-seller failure union (reserve)  | DONE     | REJECT by ESP-1 (WEAK_RESEARCH_CLUE_ONLY at all 3 primary horizons; SELECTION_EXPOSED)                                                                                                                                                                                                                              | 1ce475c         | see MASTER_COMMIT_LEDGER |                      1 |            20 |            0 |            0 | R1_TRAPPED_UNION    |    nan |
| 19 | TEST117    | final synthesis                         | DONE     | FRONTIER UNCHANGED = CURRENT_LOCKED_MAIN; INDEX_TARGET_600_NOT_REACHED                                                                                                                                                                                                                                              | 87bc894         | see MASTER_COMMIT_LEDGER |                      0 |             0 |            0 |            0 | none                |    nan |

## Clue library

|    | test       | variant           | label                                       | horizon   |   excess |   ci_lo |   years_pos | note                                                                         |
|---:|:-----------|:------------------|:--------------------------------------------|:----------|---------:|--------:|------------:|:-----------------------------------------------------------------------------|
|  0 | TEST99     | T99_HTF1_30m      | WEAK_RESEARCH_CLUE_ONLY                     | h1615     |   0.0205 | -0.0060 |           6 | HTF1 family weak, adjacent 15m h24 consistent                                |
|  1 | TEST100    | V2_K6             | WEAK_RESEARCH_CLUE_ONLY                     | h12       |   0.0027 | -0.0058 |           6 | K12 negative; incoherent                                                     |
|  2 | TEST101    | AV_OR30           | WEAK_RESEARCH_CLUE_ONLY                     | h12       |   0.0089 | -0.0010 |           6 | all 3 horizons positive, 4/4 inst; not adjacent-consistent across anchors    |
|  3 | TEST102    | S3_E21            | WEAK_RESEARCH_CLUE_ONLY                     | h12       |   0.0047 | -0.0045 |           6 | 60m only, decays by 120m                                                     |
|  4 | TEST103    | P2_FAILED_FIRST   | WEAK_RESEARCH_CLUE_ONLY                     | h24       |   0.0226 | -0.0009 |           6 | trapped-first-attempt second resumption; P1_H2 same sign all horizons; n=713 |
|  5 | TEST103    | P1_H2             | WEAK_RESEARCH_CLUE_ONLY                     | h1615     |   0.0127 | -0.0106 |           6 | two-leg high-2                                                               |
|  6 | TEST104    | L2_SWL60          | WEAK_RESEARCH_CLUE_ONLY                     | h1615     |   0.0282 | -0.0070 |           6 | L2 family positive on 15/15 cells                                            |
|  7 | TEST104    | L2_PDL            | WEAK_RESEARCH_CLUE_ONLY                     | h12       |   0.0171 |  0.0010 |           5 | CI>0 but gross < cost                                                        |
|  8 | TEST104    | L1_SWH60          | WEAK_RESEARCH_CLUE_ONLY                     | h24       |   0.0143 | -0.0050 |           6 | break-retest-hold of 60m swing                                               |
|  9 | TEST106    | A2_A_UP_IMMEDIATE | STRONG_CLUE / RESEARCH_DUPLICATE_OF_ORB     | h12       |   0.0137 |  0.0010 |           6 | not distinguishable from plain ORB; economically ~$1/day                     |
| 10 | TEST106    | A3_FAILED_A_DOWN  | WEAK_RESEARCH_CLUE_ONLY                     | h1615     |   0.0187 | -0.0256 |           5 | failed A-down, consistent with TEST104 L2 failed-breakdown structure         |
| 11 | TEST109    | CHOCH_15m         | WEAK_RESEARCH_CLUE_ONLY                     | h1615     |   0.0132 | -0.0118 |           7 | 5m not consistent                                                            |
| 12 | RESERVE_R1 | R1_TRAPPED_UNION  | WEAK_RESEARCH_CLUE_ONLY (SELECTION_EXPOSED) | h24       |   0.0119 | -0.0006 |           6 | pooling P2+L2+A3 does not clear the CI; gross < cost at 120m                 |

## Summary
Every core family (TEST99-TEST104, TEST106, TEST108, TEST109, TEST112, TEST114, TEST115) was first-passed under the common ESP-1 protocol with causal, family-specific magnitude/state nulls.  Only one ESP-1 STRONG_CLUE appeared (ACD A-up, 60 min) and it is statistically indistinguishable from a plain opening-range break (a closed family) with ~$1/day economics.  The only recurring positive structure is the 'trapped seller' failure (failed breakdown / failed first attempt, then reclaim), positive across three independent tests and pooled in RESERVE_R1, but its point estimates (~0.01-0.03 ATR_d) do not clear the date-clustered CI and sit at or below micro round-trip cost.  Conditional tests (TEST105, 107, 110, 111, 113) were not run by rule; TEST116 not run by duplication.  ML/GA gates were never met.  The frontier stays at the locked Main (143.21 $/day); GAP_TO_600 = 456.79; the index universe is saturated at the event-alpha level for this data and cost structure: INDEX_TARGET_600_NOT_REACHED.

