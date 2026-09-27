# M07 Analog model specification

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


* Decision points: RTH bars closing on the quarter hour 10:00-16:00 (25/session). ~35.8k DEV points per instrument.
* Representations: SHAPE_ATR (close path at 6 evenly spaced points, (P_t - P_start)/ATR20_daily) and SHAPE_RANGE
  ((P_t - low_W)/(high_W - low_W)); windows 15/30/60/120m only.
* STATE families (standardised with warm-up-only constants; each family total weight 1): RANGE (60m qualified-range
  position or trailing position, RTH position, prior-RTH position), REGIME (tier, trend20/100), VOL (ATR20 pct, width,
  efficiency), NESTED (low/high alignment counts, 5D position), VWAP (z), CLOCK (time of day).
* Context hierarchy: same regime tier and same volatility tercile enforced by a large distance penalty, then Euclidean
  distance. Modes compared: SHAPE_ONLY (no context), SHAPE_PLUS_STATE (hierarchy + shape + all state), STATE_ONLY
  (hierarchy + state), RANDOM_IN_CONTEXT control (random neighbours inside the same context cell).
* k = 25/50/100/200 (all reported), at most 2 neighbours per library session; independent campaigns = distinct sessions.
* Library for a query in block starting at session s: points from sessions <= s-2 (1-session embargo), frozen per
  20-session block; warm-up 250 sessions (predictions start ~2020-05); library < 500 points -> NO_MATCH.
* Confidence HIGH/MED/LOW/NO_MATCH from median neighbour distance vs causal quantiles of previous blocks, neighbour
  agreement |mean|/(sd/sqrt(indep)), independent-campaign count. Targets: 30/60/120m return, 60m MFE/MAE, first passage.
* No DTW, no deep learning, no one-neighbour forecast.

