# TEST115 HTF TREND-REGIME / STAGE-STRENGTH FACTORY — preregistration

Committed ALONE before any TEST115 economics.  Master prereg 319a7f6.  Attribution: SOURCE_SUPPORTED_PRINCIPLE, Tier 1/2 (Moskowitz-Ooi-Pedersen
time-series momentum; Wilder ADX/DMI; Weinstein stage analysis).  NOVELTY_DELTA vs TEST95/96 literals and generic HTF-bull filters: STRENGTH of
the trend (continuous) evaluated INSIDE the up-direction state, against a null that already conditions on simple HTF direction.

All features per instrument from completed RTH daily bars strictly before session d (daily close = 16:15 price; ATR_d = engine ATR14).
- T1_ADX: Wilder ADX(14) on daily H/L/C, evaluated only on sessions with +DI(14) > -DI(14).
- T2_STAGE_SLOPE: Weinstein stage 2 proxy: close > SMA150 and SMA150 rising; feature = (SMA150_t - SMA150_{t-20}) / ATR_d, evaluated only on sessions
  with close > SMA150.
- T3_TSMOM_12M: (close_t / close_{t-252} - 1) / (stdev of daily returns over 252 days x sqrt(252)), all sessions.
- T4_TSMOM_1M: (close_t / close_{t-21} - 1) / (stdev of daily returns over 63 days x sqrt(21)), all sessions.
4 definitions (response curves).  Outcome per session: intraday long from the first legal open (FP at 09:31) to 16:15 (PRIMARY) and to 16:00,
in ATR_d units.  Null HDN (simple HTF direction): cell mean over all valid sessions of the same instrument in year x vt x (close > SMA50).
Causal quintiles (edges from sessions strictly before the month, monthly expanding; 120-session warm-up).  Coherence: |Spearman| >= 0.9,
top-minus-bottom date-clustered 95% CI (2,000 reps) excludes 0, same sign >= 5/8 years and >= 3/4 instruments.
STRENGTH_ADDS_VALUE iff COHERENT with the best bin's excess > 0 and its gross mean > cost.  A strategy phase needs a separate prereg.
