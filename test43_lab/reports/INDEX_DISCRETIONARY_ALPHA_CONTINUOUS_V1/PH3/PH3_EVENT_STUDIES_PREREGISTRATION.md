# PH3 D1-D8 LOCATION x CONTEXT x TRIGGER EVENT STUDIES — preregistration (alone)

Atlas: PH2 (5685297).  Band = 0.25 x ATR5; cluster radius 0.15 x ATR_d (sensitivities 0.10 / 0.20 only in D4).  Decision bar b <= 67, entry FP[5b+5].
"Nearest support at b-1" = PH2 S* at bar b-1 (the support the market is standing on); resistance analogously.  Deadlines in 5m bars.
Support-failure machine (per session, one active sequence at a time, restarts after completion / cancel):
- FAILURE at b: close[b] < L = S*[b-1] (level frozen, type recorded).  RECLAIM r: first later close > L within 12 bars (else cancel).
- D1 SUPPORT FAILURE -> RECLAIM -> SECOND ATTEMPT: after r, FIRST RESUMPTION q (close > prior high); FAILS if within 3 bars a close < low[q];
  then SECOND RESUMPTION = next close > prior high with close > L -> event.  Cancel on any close < L after r, or at failure + 24.
- D2 SWEEP / RECLAIM -> RETEST -> HIGHER LOW: SWEEP = (low[b] < L and close[b] > L, previous close > L) OR a D1-type failure reclaimed within
  3 bars; sweep low = min low since the breach.  RETEST: later bar (<= 12 bars) with low <= L + band, close > L and low > sweep low.
  CONFIRMATION: first bar within 6 bars after the retest with close > high of the retest bar -> event.
- LN1 (location null for D1) = the RECLAIM bar r; LN2 (location null for D2) = the SWEEP reclaim bar.
- PATTERN nulls D1P / D2P: identical machines with the generic level G = min low of the prior 6 bars, used only when no known support is within
  0.15 x ATR_d of G (away from location).
- D1B C2 AT LOCATION: frozen C2_P2_FAILED_FIRST events whose 12-bar low before the event is within 0.15 x ATR_d of any known support (PH2 levels at
  b); pattern null D1B_P = C2 events not at location; location null TOUCH = bars with low <= S* + band and close > S* (first per session).
- D3 BREAKOUT -> RETEST -> HOLD -> SECOND PUSH (resistance types PDH, PWH, SW30H, SW60H, R2HH, R4HH, BSR; ORH excluded = no ORB): BREAK at b:
  close > L = R*[b-1] and close[b-1] <= L; RETEST within 12 bars (low <= L + band, close > L; cancel on close < L); FIRST PUSH close > prior high;
  then >= 1 bar with a lower close; SECOND PUSH = close > max high since the break -> event; deadline break + 24.  LN3 = the BREAK bar.
  Pattern null D3P: generic level = max high of the prior 6 bars with no known resistance within 0.15 x ATR_d.
- D7 BREAKOUT FAILURE -> SUPPORT CONVERSION: BREAK as D3; FAILURE within 6 bars (close < L); RECLAIM within 6 bars (close > L); SECOND
  RESOLUTION = close > max high since the break -> event.  Location null = LN3; pattern null D7P (generic 6-bar high).
- D8 TWO-LEG AT LOCATION: frozen P1_H2 events whose 12-bar low is within 0.15 x ATR_d of a known support; pattern null D8P = P1_H2 not at location;
  location null = TOUCH.
Response curves (causal quintiles on the event population; PH2 features at the event bar unless stated):
- D4 CONFLUENCE on D1 u D2 u D1B: number of known supports within r x ATR_d of the event level (L, or the 12-bar low for D1B); r = 0.15 primary,
  0.10 / 0.20 sensitivities.  D5 ROOM: UPSIDE_ROOM (no known resistance -> top bin) on (a) support events D1 u D2 u D1B u D8, (b) breakout events
  D3 u D7, (c) all C2 events.  D6 APPROACH at the FAILURE / SWEEP bar of D1 u D2: disp6, bars_since_high, bear_frac6, consec_bear,
  range_contract, lower_wick, cpos_chg3, sup_touch.
Definitions: 16 event definitions + 14 curves = 30 (<= 80).
Outcomes: horizons 30 / 60 / 120 min, 16:15 (engine R, ATR_d units); gross $ and base / SLIP4 net; MFE / MAE 60m, time-to-MFE, P(>0).
MAGNITUDE NULL (all definitions): cell mean over ALL valid bars of the instrument in year x vt x tod3 x causal tercile(disp6) x causal
tercile(rng12); x = R - null.  LOCATION / PATTERN comparisons: difference of mean x (event minus null population) with date-clustered CI.
Curves: coherence rule of the master programs (|Spearman| >= 0.9, top-bottom CI excludes 0, >= 5/8 years, >= 3/4 instruments) on x.
Gate: ECONOMIC_RESEARCH_CANDIDATE per the program prereg; value type LOCATION_VALUE / PATTERN_VALUE by the point comparisons.
