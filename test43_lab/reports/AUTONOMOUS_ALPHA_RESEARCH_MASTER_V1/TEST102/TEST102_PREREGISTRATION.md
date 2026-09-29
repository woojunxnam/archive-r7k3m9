# TEST102 SATY ATR PHASE / EMA RIBBON — preregistration

Committed ALONE before any TEST102 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SYSTEMATIC_FORMALIZATION (Saty Mahajan ATR
levels / pivot ribbon), Tier 3.  NOVELTY_DELTA vs TEST49 trend-day and TEST97 W3_V3 (EMA20 touch after a 60-bar thrust): an ATR-normalised
continuous phase state and an EMA-stack state, each tested against a null holding the session move fixed.

EMAs on chained 5m closes (span 8 / 21 / 34, adjust = False).  ATR_d = engine daily ATR.
- S1 phase (continuous state): phase = (close - EMA21) / ATR_d at every valid bar (b <= 67).  Response curve over causal quintiles (edges from all
  valid bars in sessions strictly before the month; 120-session warm-up).  Null S1N: cell mean over all valid bars in year x vt x tod3 x tercile of
  (close - session open) / ATR_d (causal edges).  COHERENT iff at a primary horizon: |Spearman(bin, bin excess)| >= 0.9, top-minus-bottom
  date-clustered 95% CI (2,000 reps) excludes 0, same sign in >= 5/8 years and >= 3/4 instruments.  "S1 has value" iff COHERENT and the best
  bin's excess > 0 and its gross mean > cost_atr.
- S2 ribbon onset: first bar of a session at which EMA8 > EMA21 > EMA34 and the previous chained bar was not stacked.
- S3 ribbon pullback: while stacked (EMA8 > EMA21 > EMA34 at b), first bar of the session whose low <= EMA21 and close > EMA21 (S3_E21), and
  separately low <= EMA8 and close > EMA8 (S3_E8).
- S4 (phase-conditioned ribbon) runs ONLY if S1 has value; otherwise NOT_RUN_BY_RULE.
Null F102 for S2 / S3: pool = all valid NON-event bars; cell = year x vt x tod3 x phase quintile x session-move tercile (causal edges); min 10;
fallbacks.  Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 / 120 min, 16:15.  Adjacency for STRONG: S3_E8 <-> S3_E21; S2 needs S3 same sign.
4 definitions (S1, S2, S3_E21, S3_E8).  Strategy phase only for STRONG_CLUE (separate prereg).
