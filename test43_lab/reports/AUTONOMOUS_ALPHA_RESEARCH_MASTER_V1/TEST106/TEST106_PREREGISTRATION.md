# TEST106 FISHER ACD OPENING-AUCTION STATE — preregistration

Committed ALONE before any TEST106 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SOURCE_SUPPORTED_PRINCIPLE (Mark Fisher,
"The Logical Trader", ACD), Tier 1/2.  NOVELTY_DELTA vs TEST49 ORB retention / TEST97 ORB15: the A-level is offset from the opening range by a
fraction of recent daily range and must be HELD for a time (time acceptance), and failed-A-down / C-up reversal states are included.  Each ACD
event is compared with the plain ORB break on the same sessions; equivalent -> RESEARCH_DUPLICATE.

Opening range OR = 09:30-09:45 (5m bars 0-2), ORH / ORL.  A-value = 0.10 x mean RTH range of the prior 10 sessions (causal).
- A1_A_UP: first close >= ORH + A-value (b >= 3), THEN held: the next 2 bars (10 min, 1/2 of the OR length rule scaled to 5m bars) all close
  >= ORH + A-value.  Event at the second holding bar.
- A2_A_UP_IMMEDIATE: first close >= ORH + A-value (no hold) — the ACD trigger without time acceptance.
- A3_FAILED_A_DOWN: first close <= ORL - A-value, then within 6 bars a close back above ORL (the A-down failed); event at that close
  (Fisher "failed A" long).
- A4_C_UP: after an A-down trigger (close <= ORL - A-value), the first close >= ORH + A-value (C-up reversal).
- ORB comparator (control): first close > ORH (b >= 3) — plain ORB on the same OR.
All events b <= 60.  4 ACD definitions + 1 comparator = 5 definitions.
Null F106 (primary): pool = all valid NON-event bars with close > ORH (for A1 / A2 / A4 / ORB) or close > ORL (for A3); cell = year x vt x tod3 x
quintile of (close - ORH) / ATR_d (resp. close - ORL) x tercile of OR width / ATR_d (causal edges); min 10; fallbacks.
Also: paired raw comparison ACD vs ORB (same sessions where both fire).  Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 / 120 min, 16:15.
Adjacency for STRONG: A1 <-> A2 (same trigger family); A3 <-> A4 (reversal family).
