# PH2 CAUSAL LEVEL ATLAS + DISCRETIONARY STATE DICTIONARY — preregistration (alone; construction only, no economics)

All levels are values KNOWN at the completion of 5m bar b (chained RTH 5m bars, engine arrays).  No eventual highs / lows, no hindsight swings,
no hand-drawn levels.  ATR_d = engine daily ATR; ATR5 = engine 5m ATR.
SUPPORT set (8 types): PDL (prior RTH low), PWL (prior ISO-week RTH low), SW30L / SW60L (most recent CONFIRMED 30m / 60m swing low: pivot bar p
with low below the 2 complete bars on each side, known at completion of bar p+2, chained complete bars), R2HL / R4HL (min low of the prior
24 / 48 chained 5m bars), ORL (09:30-10:00 low, from bar 6), BRS (broken resistance as support: the most recent resistance level of types
PDH / PWH / SW30H / SW60H that price CLOSED above earlier in the same session; valid while not closed below by more than 0 after the break).
RESISTANCE set (8 types): PDH, PWH, SW30H, SW60H, R2HH, R4HH, ORH (from bar 6), BSR (broken support as resistance, symmetric).
Context lines (not counted in clusters): session VWAP.  Event AVWAP is used only inside an event whose frozen anchor exists (none in the atlas).
Per-bar state (ATR_d units unless stated):
- nearest support below the close S* and its type; DOWNSIDE_ROOM = (close - S*) / ATR_d; nearest resistance above R* and type;
  UPSIDE_ROOM = (R* - close) / ATR_d (no resistance known above -> NaN and flag no_res = 1); ROOM_ASYMMETRY = UP / (UP + DOWN).
- CONFLUENCE: number of support (resistance) levels within 0.15 x ATR_d of S* (R*) — PRIMARY radius 0.15; fixed sensitivities 0.10 and 0.20 only.
- nearest-level spacing (distance between S* and the next support below), level age (bars since the level value became known, capped at
  5 sessions), session touch count of S* (earlier session bars with low <= S* + 0.25 x ATR5 and close > S*).
- approach features at bar b (used later only at support interactions): disp6 into the level, bars since session high, bearish fraction of
  the last 6 bars, consecutive bearish closes, range contraction = mean range of last 3 bars / mean range of prior 6, lower-wick fraction of
  bar b, close-position change over the last 3 bars.
STATE_DICTIONARY: APPROACH, ATTEMPT (low within 0.25 x ATR5 of a support), FAILURE (close below support), RECLAIM (first close back above the
failed support), RETEST (later low within band, close above), FIRST RESUMPTION (close > prior bar high), FIRST RESUMPTION FAILURE (close below
the first-resumption bar's low within 3 bars), SECOND RESUMPTION, EXPANSION (close > max high since the failure), RESISTANCE / TREND LOSS
(close below the reclaimed level) — definitions frozen here, used by PH3.
Output: per-instrument atlas arrays (not committed; reproducible by code), descriptive summary (level availability, room / confluence
distributions), LEVEL_ATLAS.md, STATE_DICTIONARY.md, FEATURE_DICTIONARY.csv.  Audit: prefix invariance of the atlas (sessions <= 2024-12-31
recomputed with later data removed must be identical).
