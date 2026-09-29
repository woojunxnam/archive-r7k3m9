# TEST104 LEVEL INTERACTION FACTORY — preregistration

Committed ALONE before any TEST104 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SYSTEMATIC_FORMALIZATION (Trader Dante
break-retest; Sperandeo 2B; Wyckoff spring; Brooks breakout pullback), Tier 2.  No volume-profile levels.
NOVELTY_DELTA: boxes / Darvas (TEST70-78) used the price's own range; PDL / 5-day-low / OR-low rebounds (TEST46/47) used touches of support.
Here: external reference levels, frozen at the break, with a break -> retest -> hold STATE (L1/L2), sweeps only on level types never tested
(L3), and response curves of approach speed / touch count on level breaks (L4/L5).

Levels (causal; value known at the completion of 5m bar b):
- PDH / PDL: prior RTH session high / low.  PWH / PWL: max high / min low of the RTH sessions of the previous calendar (ISO) week.
- ORH / ORL: 09:30-10:00 high / low (bars 0-5), usable from bar 6.
- SWH60 / SWL60: most recent causally CONFIRMED 60m swing high / low on the chained complete 60m bars (pivot at k-2 with high > the two bars on each
  side; known from the completion of bar k), usable from the next 5m bar.
- H2H / L2H: prior 2-hour extreme = max high / min low of the prior 24 chained 5m bars.
Resistance set R = {PDH, PWH, ORH, SWH60, H2H}; support set U = {PDL, PWL, ORL, SWL60, L2H}.

Events (first occurrence per session and level; b <= 67; break search b <= 60):
- L1_<R> break-retest-hold: break = first close above the level after a close at/below it (level FROZEN at the break bar); then the first later
  bar with low <= level + 0.25 x ATR5 and close > level (hold).  Cancelled if a close < level occurs before the hold.  (5 definitions)
- L2_<U> failed breakdown -> reclaim -> retest-hold: breakdown = first close below the level after a close at/above it (level frozen); reclaim = first
  later close > level; hold = first bar after the reclaim with low <= level + 0.25 x ATR5 and close > level; cancelled by a close < level between
  reclaim and hold.  (5 definitions)
- L3_<PWL, SWL60, L2H> sweep / spring / 2B: bar with low < level, close > level, previous close > level.  PDL / ORL excluded (closed family).  (3)
- L4 approach speed (response curve): over all L1 BREAK bars (union of R levels), feature = (close[b] - close[b-6]) / ATR_d.  (1)
- L5 touch count (response curve): over the same break bars, feature = number of earlier same-session bars with high >= level - 0.25 x ATR5 and
  close <= level.  (1)
15 definitions.  L4 / L5 curves use causal quintiles and the TEST98 / TEST102 coherence rule.
Null F104 (primary, per level type): pool = all valid NON-event bars of the session with close > the (current, unfrozen) level; cell = year x vt x
tod3 x quintile of (close - level) / ATR_d x tercile of (close - session open) / ATR_d (causal edges); min 10; fallbacks.  L4 / L5: break bars vs the
same F104 null.  Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 / 120 min, 16:15.
Adjacency for STRONG: >= 1 other level type of the same L-family with the same sign and >= 50% magnitude.
TEST105 (level failure deep branch) runs only if TEST104 yields a COHERENT level-failure result (an L2 or L3 EVENT_CLUE); else NOT_RUN_BY_RULE.
