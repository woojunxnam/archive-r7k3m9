# M17 Final mechanism review

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


## Answers
```
RANGE_BALANCE_STATE_HAS_INFORMATION = YES (volatility/range only; NO directional information)
SWEEP_RECLAIM_RETEST_HAS_INFORMATION_ES = NO
SWEEP_RECLAIM_RETEST_HAS_INFORMATION_MNQ = NO
BREAK_RETEST_HAS_INFORMATION_ES = NO
BREAK_RETEST_HAS_INFORMATION_MNQ = NO
NESTED_RANGE_ALIGNMENT_ADDS_VALUE_ES = NO
NESTED_RANGE_ALIGNMENT_ADDS_VALUE_MNQ = NO
RANGE_MID_IS_LOW_INFORMATION_ZONE_ES = NO (no zone is informative; boundaries are not more informative)
RANGE_MID_IS_LOW_INFORMATION_ZONE_MNQ = NO (no zone is informative; boundaries are not more informative)
RANGE_WIDTH_PREDICTS_DESTINATION_ES = NO
RANGE_WIDTH_PREDICTS_DESTINATION_MNQ = NO
SHAPE_ONLY_ANALOG_ADDS_VALUE_ES = NO
SHAPE_ONLY_ANALOG_ADDS_VALUE_MNQ = NO
STATE_ONLY_ANALOG_ADDS_VALUE_ES = NO
STATE_ONLY_ANALOG_ADDS_VALUE_MNQ = NO
SHAPE_PLUS_STATE_ADDS_VALUE_ES = NO
SHAPE_PLUS_STATE_ADDS_VALUE_MNQ = NO
FRACTAL_EFFECT_TRANSFERS_ACROSS_TIMEFRAMES_ES = NO (structure is scale-invariant; outcome information absent)
FRACTAL_EFFECT_TRANSFERS_ACROSS_TIMEFRAMES_MNQ = NO (structure is scale-invariant; outcome information absent)
TEST43M_IMPROVES_V6_ES = NO
TEST43M_REDUCES_DD_ES = NO
TEST43M_INCREASES_MATCHED_BETA_EXCESS_ES = NO
TEST43M_IMPROVES_V6_MNQ = NO
TEST43M_REDUCES_DD_MNQ = NO
TEST43M_INCREASES_MATCHED_BETA_EXCESS_MNQ = NO
TEST43M_SURVIVES_VAL_ES = PARTIAL (1/7 frozen candidates; gate failed on DEV)
TEST43M_SURVIVES_VAL_MNQ = PARTIAL (1/7 frozen candidates; gate failed on DEV)
TEST43M_PROMOTE_TO_FINALIST = NO
HOLDOUT_OPENED = NO
PORTFOLIO_MEMBERSHIP_CHANGED = NO
LIVE_AUTHORIZATION = NO
```
## Summary
1. Balance vs expansion can be identified mechanically and causally; balance predicts continued low range, not direction.
2. Sweep/reclaim/retest and break/acceptance/retest are well-defined, scale-invariant state machines whose transition
   probabilities are almost identical for ES and MNQ and across 15m-120m and 3m/5m bars — but after matched controls and a
   placebo-calibrated threshold they carry no forward-return, MFE/MAE or first-passage information.
3. Nested alignment, range location zones (including the MID hypothesis) and range-width destinations add nothing beyond
   regime + vol + clock + location controls (width only proxies local volatility).
4. Historical analogs (kNN, strictly walk-forward, deduplicated) have no positive residual information in any mode;
   shape analogs predict risk (MAE) only as well as a local volatility ratio.
5. As exposure modifiers on untouched V6 candidates they mostly lower P&L and raise turnover; reductions avoid as much
   adverse as they forgo favourable movement and lose the friction.
6. Three methodological traps were found and corrected (session-equal weighting look-ahead, within-session demeaning
   look-ahead, unresolved first-passage volatility artefact) — each alone would have produced a false "edge".
7. Keep V6 finalists unchanged. The TEST43-M modules stay in the repo as diagnostics (and as a volatility-state input
   candidate for a future risk-governor study, not a trading signal).

