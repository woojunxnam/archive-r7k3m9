# TEST101 EVENT-ANCHORED VWAP — preregistration

Committed ALONE before any TEST101 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SOURCE_SUPPORTED_PRINCIPLE (Brian Shannon,
anchored VWAP), Tier 2.  NOVELTY_DELTA vs TEST100: the reference line is anchored at a causal upside event, and the test is AVWAP vs session VWAP
on the identical anchor / hold rule.

Anchors (first occurrence per session, 5m completed bar a, a <= 60):
- ANC_BRK12: first fresh N = 12 upside breakout of the session (close > max high of the prior 12 chained 5m bars; previous bar not a breakout).
- ANC_PDH: first close above the prior RTH session high.
- ANC_OR30: first close above the 09:30-10:00 opening-range high (bars 0-5), a >= 6.
- TEST99 anchor: NOT used (TEST99 produced no EVENT_CLUE).
AVWAP(b) = sum over 1m grid minutes 5a .. 5b+4 of typical price x volume / sum of volume (1m grid volume, same as the engine session VWAP;
equal-weight typical price if the volume sum is 0).  Causal: uses only completed minutes.

Events (first occurrence after the anchor, b > a, b <= 67):
- AV_<anchor>: first bar whose low <= AVWAP + 0.25 x ATR5 and close > AVWAP (hold of the anchored VWAP from above).
- SV_<anchor>: same rule with session VWAP (comparator on the same anchor).
6 definitions (3 AVWAP + 3 session-VWAP comparators).
Null F101 (primary): pool = all valid NON-event bars after the same session's anchor with close > the tested line (AVWAP for AV_, session VWAP for
SV_); cell = year x vt x tod3 x quintile of (close - line) / ATR_d x tercile of (close - anchor-bar close) / ATR_d; causal edges; min 10; fallbacks.
Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 min, 120 min, 16:15.  AVWAP-vs-SVWAP: difference of pooled raw means and of F101 excess reported.
Adjacency for STRONG: AV_<anchor> requires the same-sign AV result on >= 1 other anchor (>= 50% magnitude).  Strategy phase only for STRONG_CLUE.
