# TEST103 COMPLEX PULLBACK / SECOND ENTRY — preregistration

Committed ALONE before any TEST103 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SOURCE_SUPPORTED_PRINCIPLE (Brooks
"high 2" / two-legged pullback; PATs / Mack second entry), Tier 2.  NOVELTY_DELTA vs TEST48 ARM->CONFIRM (generic delay) and TEST97 W3_V3
(first pullback): the event requires a FAILED first resumption attempt (a structural failure state) or a two-leg correction, i.e. the "second"
entry is conditioned on the first one having been trapped.

Context (all definitions): a session thrust = first bar b0 <= 55 with close > max high of the prior 12 chained 5m bars (fresh N=12 breakout,
TEST98 base event).  Swing high SH = the running max high from b0 until the pullback starts.  Pullback start = first bar after b0 with a lower high
than the prior bar.  Pullback depth is limited to <= 1.0 ATR_d below SH (else the context is cancelled); context expires at b0 + 24.
- P1_H2 (two-leg pullback, Brooks high-2): during the pullback, leg 1 = a bar whose high exceeds the prior bar's high (first "high-1" attempt)
  that does NOT make a new high above SH, followed by a lower low than the pullback low before that attempt (leg 2); event = the next bar whose
  high exceeds the prior bar's high AND closes above the prior bar's high (second attempt, close-confirmed), still <= 1.0 ATR_d below SH.
- P2_FAILED_FIRST: the first close above the prior bar high after the pullback start is the FIRST resumption; it FAILS if within the next 3 bars
  a bar closes below the first-resumption bar's low.  Event = the next close above the prior bar high after that failure (second resumption).
- P3_EMA21_SECOND: the second (not first) touch of EMA21 (low <= EMA21, close > EMA21) within the context window.
- P1_H1_COMPARATOR (control, same contexts): the first "high-1" close above the prior bar high after the pullback start (TEST97-like first entry).
- P4 (HTF/LTF): NOT_RUN_BY_RULE (TEST99 produced no EVENT_CLUE).  P5 (nested conditional): only if >= 1 of P1-P3 is an EVENT_CLUE; else NOT_RUN_BY_RULE.
4 definitions (P1_H2, P2_FAILED_FIRST, P3_EMA21_SECOND, P1_H1_COMPARATOR).
Null F103 (primary): pool = all valid NON-event bars inside ANY active thrust context of the same session (b0 < b <= b0 + 24); cell = year x vt x tod3
x tercile of (close - SH) / ATR_d x tercile of (close - close[b0]) / ATR_d (causal edges); min 10; fallbacks.  Also reported: second-minus-first
paired comparison (P1_H2 / P2 vs P1_H1 raw means).  Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 / 120 min, 16:15.
Adjacency for STRONG: P1_H2 <-> P2_FAILED_FIRST (both are second-entry forms).  Strategy phase only for STRONG_CLUE.
