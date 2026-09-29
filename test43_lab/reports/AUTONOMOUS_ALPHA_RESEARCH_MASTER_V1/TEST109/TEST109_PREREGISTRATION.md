# TEST109 ICT FALSIFICATION MINI-LANE — preregistration

Committed ALONE before any TEST109 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SYSTEMATIC_FORMALIZATION of ICT concepts
(Tier 3, low priority).  Budget <= 12 definitions; used 6.  Purpose: falsification — does a fair value gap or a change of character carry
information beyond a matched displacement of the same size?

Bars: 5m engine bars and complete 15m bars (TEST99 aggregation, parity-proven).  All three bars of a pattern must be in the same session.
- FVG_DISP_<5m|15m>: bullish fair value gap completes at bar k: high[k-2] < low[k] and bar k-1 bullish.  Event at bar k.
  Null F109A: pool = non-event same-session triplets with a bullish middle bar; cell = year x vt x tod3 x quintile of 3-bar displacement
  (close[k] - close[k-3]) / ATR_d x tercile of the middle-bar range / ATR_d (causal edges).  = "FVG vs matched no-FVG displacement".
- FVG_RETRACE_<5m|15m>: after the most recent same-session FVG (gap = high[k-2] .. low[k]), the first later bar j <= k + 12 (5m) / k + 4 (15m)
  with low[j] <= low[k] and close[j] > high[k-2] (price trades into the gap and holds above its bottom).
- CHOCH_<5m|15m>: bullish change of character: causal pivot highs (pivot at t-2 with a high above the two bars on each side, confirmed at t,
  chained); when the last two confirmed pivot highs are descending, the first close above the last pivot high.  First per session.
  Null F109B (retrace and CHoCH): pool = all non-event bars of the TF; cell = year x vt x tod3 x quintile of (close[k] - close[k-3]) / ATR_d x
  tercile of (close - session open) / ATR_d (causal edges).
- FVG after level failure: NOT_RUN_BY_RULE (TEST104 produced no level-failure EVENT_CLUE).
Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 / 120 min, 16:15.  Adjacency for STRONG: 5m <-> 15m of the same definition.
