# TEST99 HTF MOMENTUM SCALING — Phase 0 / Phase 1 preregistration

Committed ALONE before any TEST99 economics.  Master prereg 319a7f6 (ESP-1 applies).  Data <= 2026-05-27.  NEW_OOS_OPENED = NO.
Attribution: SYSTEMATIC_FORMALIZATION (Brooks strong trend bars on higher time frames; Raschke/Turtle short-horizon breakout), Tier 2.
NOVELTY_DELTA vs TEST97 (5m strong bar / N-bar breakout) and TEST74/95 (generic 5/15/60 alignment): bar STRUCTURE on 15/30/60m bars evaluated
against a null matched on the same HTF bar's displacement, range and time of day (not direction alignment, not 5m bars).

## Phase 0 — aggregation parity (fail closed)
- P0a: 5m OHLC recomputed independently from the 1m RTH grid (open = first 1m open, high = max, low = min, close = last close of grid [5b, 5b+5))
  must equal the frozen TEST97 engine arrays (o5/h5/l5/c5) exactly (max |diff| = 0) for ES / NQ / YM / RTY.
- P0b: HTF bars for TF m in {15, 30, 60} min (m5 = 3 / 6 / 12 five-minute bars) anchored at 09:30: HTF bar k covers 5m bars [k m5, (k+1) m5 - 1],
  completes at 5m bar b = (k+1) m5 - 1 (decision), entry = open of 5m bar b+1.  Only complete HTF bars (b <= 80) exist; the partial 16:00-16:15
  remainder is excluded from events and from rolling chains.  HTF OHLC from 5m must equal HTF OHLC aggregated directly from 1m (max |diff| = 0).
- Frozen boundaries: 15m completes at b = 2, 5, ..., 80 (27 bars); 30m at b = 5, 11, ..., 77 (13 bars); 60m at b = 11, 23, 35, 47, 59, 71 (6 bars).
- Any mismatch -> TEST99 = PARITY_BLOCKED, no Phase 1.

## Phase 1 — event study (9 new definitions + 3 5m reference rows)
HTF series are chained across sessions (complete bars only).  Range means use the prior 20 completed same-TF bars.
- HTF1 strong bull bar: body = close - open > 0, body / range >= 0.60, close position (close - low) / range >= 0.80,
  range >= 1.25 x mean range of the prior 20 same-TF bars.
- HTF2 2h rolling-high breakout (FRESH): close > max high of the prior n same-TF bars (15m n = 8, 30m n = 4, 60m n = 2 — i.e. prior 2 hours),
  and the previous same-TF bar was not such a breakout.
- HTF3 two consecutive bullish upper-half bars (FIRST): bars k-1 and k both bullish with close position >= 0.5, and bar k-2 was not
  (bullish and upper-half)  (first completion of a run).
- 5m reference rows (same code, m5 = 1; HTF1-5m = TEST97 strong bar; HTF2-5m n = 24; HTF3-5m) are REFERENCE only (not new hypotheses).
- Common population: decision bar b <= 67 (ESP-1).  60m TF therefore has decision bars 11..59 (5 per session).

### Nulls
- PRIMARY family null F99 (per instrument, per TF): pool = all NON-event complete same-TF bars; cell = year x vol tercile (engine vt) x time bucket
  (<10:30 / 10:30-14:00 / >14:00 by decision bar) x HTF-bar displacement quintile ((close_k - close_{k-1}) / ATR_d) x HTF-bar range tercile
  (range_k / ATR_d).  Quintile/tercile edges CAUSAL (per instrument and TF, from sessions strictly before the month, monthly expanding; first 120
  sessions warm-up excluded).  Minimum 10 pool bars per cell; fallback (1) drop year, (2) drop year and vt; shares reported.
- NULL A and NULL C (TEST97 engine) reported.
### Outputs
Horizons 30 / 60 / 120 min (5m bars 6 / 12 / 24 after entry) and 16:15; PRIMARY horizons 60 min, 120 min and 16:15.  Engine path statistics.
Per variant: n, mean, median, P>0, cost_atr, excess vs F99 with date-clustered 95% CI (2,000 reps, seed 7), positive years, instrument signs,
2021+ excess, NULL A / C excess, fallback shares, 2022 event excess.
### Classification (ESP-1)
EVENT_CLUE / STRONG_CLUE / WEAK_RESEARCH_CLUE_ONLY / REJECT per variant x primary horizon.  "Adjacent consistency" for STRONG = the adjacent
TF (15<->30, 30<->60; 5m reference counts as adjacent to 15m) of the same family has the same-sign F99 excess at that horizon with >= 50% of the
magnitude.  Chance passes: 9 x 3 = 27 tests -> ~0.7 expected.
A strategy phase (separate prereg) opens only for a STRONG_CLUE.  ML / GA are not run in TEST99 Phase 1.
