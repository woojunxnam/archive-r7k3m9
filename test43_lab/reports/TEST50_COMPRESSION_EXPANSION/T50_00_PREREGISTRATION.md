# TEST50 preregistration

```json
{
 "test": "TEST50",
 "written_utc": "2026-09-28T03:36:58Z",
 "research_data_end": "2026-05-27",
 "question": "After an intraday volatility compression, does an UPSIDE expansion predict continuation to the close beyond matched long beta, and does the prior compression carry information beyond the expansion bar itself?",
 "why_mechanism_could_exist": "Compression = balance / absorbed inventory with resting liquidity on both sides; the first directional expansion out of balance reflects new information or a forced imbalance (stops above the range, systematic breakout flow) that tends to persist for hours (volatility clustering + order-flow persistence).",
 "prior_result_motivating_it": "TEST48 GA-AC: the same semantic cluster (MNQ compression -> expansion / higher-low breakout, hold to 16:00) was selected in 5/5 nested outer folds (stitched +4.5 $/day, matched excess +4.1, 4/5 folds) but failed the combined worst day (-3203) and year concentration.",
 "difference_from_failed_families": "Not a rebound (no displacement/selloff requirement); not an unconditional ORB (requires a prior measured compression and an expansion OUT of the compression box); includes a predeclared protective stop to address the worst-day failure mode.",
 "reused_evidence_penalty": "The compression->expansion structure was selected by TEST48 GA on the same 2021+ folds; therefore TEST50 finalists need t >= 3.5 (MNQ) / t >= 3.0 (ES, not previously selected) in addition to the program gate.",
 "falsification": "No compression x expansion combo passes the program gate at the penalised threshold, the 'no-compression expansion' null is as good as the compression version, or GA-VX fails nested outer generalisation / recurrence / plateau.",
 "compression": {
  "K1_RANGE": "12-bar high-low range <= c x u5, c in {3, 4, 5}",
  "K2_RVOL": "std of the last 12 5m close changes <= q x u5, q in {0.5, 0.7}",
  "K3_CONTRACTION": "last 12-bar range <= 0.35 x session range so far (after 10:30)"
 },
 "expansion": {
  "X1_BOX_BREAK": "5m close above the compression-box high",
  "X2_EXP_BAR": "bullish bar body >= 1.0 u5, close location >= 0.7",
  "X3_HL_BREAK": "higher-low (low since arm >= box low) and close above the high made since the arm",
  "X4_BREAK_RETEST": "X1, then 2 bars whose lows stay above the box midpoint, then a close above the post-break high (prove-first)"
 },
 "window": "compression checked 10:30..14:30; expansion within 12 bars after the arm; if none, re-arm on the next compression; one entry per session; last fill 15:00",
 "exits": [
  "X120",
  "X1600 (primary)",
  "X1615",
  "NEXTOPEN"
 ],
 "stop": {
  "variants": [
   "NONE",
   "BOX (box low - 0.5 u5, checked on 1m lows)"
  ],
  "primary": "BOX"
 },
 "nulls": {
  "N_EXP_ONLY": "same expansion bar definition without a prior compression requirement",
  "N_COMP_ONLY": "enter at the end of the compression window without expansion"
 },
 "matched_null": "same instrument, fill minute, year, vol tercile, HTF trend, same exit",
 "program_gate": "prog_common.evaluate_module G1..G9",
 "ga_lane": {
  "name": "GA-VX",
  "genes": "inst, compression type & threshold & length (6/12/24), expansion type & size, window, stop on/off & buffer, exit, start time, HTF/vol permission",
  "budget": "POP 64, GENS 40, 2 seeds x 3 islands, 6 folds",
  "novelty": "|corr C43| <= 0.5"
 }
}
```

