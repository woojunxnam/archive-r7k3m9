# TEST100 VWAP TREND-SIDE STATE / ACCEPTANCE — preregistration

Committed ALONE before any TEST100 economics.  Master prereg 319a7f6, ESP-1 applies (engine mp_engine, common population b <= 67, entry open b+1).
Attribution: SYSTEMATIC_FORMALIZATION (Shannon VWAP trend side; Brooks "price stays above the moving average" trend state), Tier 2.
NOVELTY_DELTA vs closed families: not a reclaim from below (TEST46/48), not a lower-band touch, not HTF-bull + VWAP pullback (TEST97 W3_V3 uses
EMA20/VWAP touch after a 60-bar thrust), not a pre-breakout path feature (TEST98 PQ5).  Here the event is the ONSET of a trend-side VWAP state and
the null holds price on the same side of VWAP at the same distance and session move.

Definitions (5m completed bars; VWAP = session VWAP at the bar's completion; ATR5 = engine atr5; all first-occurrence-in-session):
- V1_K3 / V1_K6 acceptance: first bar b in the session at which the last K closes (bars b-K+1..b, same session) are all > VWAP.
- V2_K6 / V2_K12 walk: first bar b at which, over the last K same-session bars, every close > VWAP, every low >= VWAP - 0.25 x ATR5[b], and
  close[b] > close[b-K+1]  (price travelling along / above VWAP without penetrating it).
- V3_K3 / V3_K6 first trend-side hold: after the V1_K acceptance bar, the first later bar whose low <= VWAP + 0.25 x ATR5 and whose close > VWAP
  (a test of VWAP from above that holds).
6 definitions.  The 0.25 x ATR5 band is fixed here (not tuned).

Null F100 (primary): pool = all valid NON-event bars with close > VWAP; cell = year x vt x tod3 x quintile of (close - VWAP) / ATR_d x tercile
of (close - session open) / ATR_d; causal monthly-expanding edges from the pool (120-session warm-up); min 10; fallback drop year, then vt.
NULL A / NULL C reported.  Horizons 30 / 60 / 120 min, 16:15; PRIMARY 60 min, 120 min, 16:15 (18 primary tests, ~0.45 chance passes).
Adjacency for STRONG: V1 K3<->K6, V2 K6<->K12, V3 K3<->K6 (same sign, >= 50% magnitude).  Strategy phase only for STRONG_CLUE (separate prereg).
