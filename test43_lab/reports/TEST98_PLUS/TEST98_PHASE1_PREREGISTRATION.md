# TEST98_PRECONFIRM_PATH_QUALITY — Phase 1 (event study) preregistration

Committed ALONE before any TEST98 economics.  Base state: TEST97 closed (85f5bdc / 9cc4cf2, bookkeeping fd7c181).  CURRENT MAIN =
T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged).  Research data <= 2026-05-27.  NEW_OOS_OPENED = NO, LIVE_AUTHORIZATION = NO.
Phase 1 is an EVENT STUDY only.  Any ML phase or strategy phase requires its own later preregistration commit.

Root question: at the close of the bar where an upside breakout first becomes observable, does the PRE-CONFIRMATION path (bars <= b only)
separate continuation from failure once move magnitude is held approximately constant?  Not an FT2 rescue: no FT2 / W3-k thresholds, no
"next bar STRONG" condition, no future bar in any feature.

## 1. Base event (frozen)
- Instruments: ES, NQ, YM, RTY full contracts (signals); micro economics MES / MNQ / MYM / M2K (cost used only for the ATR cost hurdle).
- 5m RTH bars chained across sessions exactly as in the TEST97 engine (b = 0..80, completed at 09:34 + 5b).
- FRESH N=12 breakout at bar b: close[b] > max(high of the prior 12 completed chained 5m bars) AND close[b-1] <= that same statistic evaluated at
  b-1 (the first bar of a breakout run = the instant it first becomes observable).  No STRONG requirement.  N = 12 is the TEST97 canonical reference.
- Common population: signal bars 1..67 (all bar horizons complete), valid sessions (TEST97 engine `valid`).
- Entry coordinate for outcomes: open of bar b+1.  Overlapping events are allowed in the event study (date-clustered inference).
- Horizons: 10 / 15 / 20 / 30 / 45 / 60 min (bars 2 / 3 / 4 / 6 / 9 / 12) and 16:15.  Outcomes: mean, median, P(>0), ATR_d-normalised return,
  60-min MFE / MAE, new-high probability, time to MFE, time to first positive, underwater at 16:15, barrier races +-0.25 / 0.50 / 1.00 ATR_d
  (TEST97 engine path statistics).  PRIMARY horizons for tests: 30 min and 60 min.

## 2. Pre-confirmation features (all computed from bars <= b; trailing windows on the chained series)
- PQ1 efficiency: ER_k = |c[b]-c[b-k]| / sum_{t=b-k+1..b}|c[t]-c[t-1]|, k = 3 / 6 / 12; signed displacement disp_k = (c[b]-c[b-k]) / ATR_d (disp_12 is a control).
- PQ2 persistent pressure (k = 3 / 6 / 12): fraction bullish, fraction higher close, fraction higher low, fraction closing in the upper half;
  longest bullish run and longest higher-low run within the last 12 bars.
- PQ3 path damage (last 12 bars): max close drawdown from the running close high / ATR_d; max low drawdown from the running high / ATR_d;
  largest bearish body / ATR_d; path length / |net displacement|; count of closes below the prior bar midpoint.
- PQ4 breakout context (CONTROL curves only, no threshold search): overshoot = (c[b] - prior12 high) / ATR_d; range[b] / ATR5; body_pct[b];
  close_position[b]; (c[b] - session VWAP) / ATR_d; (c[b] - session open) / ATR_d; (c[b] - session open) / prior-day RTH range.
- PQ5 acceptance before the breakout: share of the session's last min(12, b+1) closes above VWAP; same above the session open; share of all session
  bars so far closing above the open; failed probes = bars in the prior 12 with high >= L - 0.25 x ATR5[b] and close <= L, where L = prior-12 high at
  b; near-high closes = bars in the prior 12 with close >= L - 0.25 x ATR5[b].  The 0.25 x ATR5 "near" band is fixed here (broad structural
  definition, not tuned).

## 3. Nulls
- PRIMARY FAMILY NULL F (within the fresh N=12 breakout population, per instrument, leave-own-event-out cell mean): cell = year x vol tercile
  (TEST97 vt) x time bucket (<10:30 / 10:30-14:00 / >14:00) x disp_12 tercile x 12-bar high-low range tercile x overshoot tercile.  Tercile edges
  are CAUSAL: per instrument, recomputed monthly from breakout events in sessions strictly before the month; the first 120 sessions of each
  instrument are warm-up (excluded).  Minimum 10 other events per cell; fallback hierarchy (1) drop year, (2) drop year and vol tercile; the share
  of events at each level is reported.
- NULL A (time / regime-matched generic long) and NULL C (basic momentum) from the TEST97 engine; NULL B = F (same breakout, magnitude matched).

## 4. Response curves and the coherence rule
- For every PQ1-PQ3 and PQ5 feature: causal quintile bins (edges from prior sessions, monthly, same warm-up); per bin pooled mean excess vs F at
  30 / 60 min (and all other horizons reported).  Discrete features with ties use the same causal quantile edges (bins may merge).
- A feature has a COHERENT_RESPONSE iff at a primary horizon: (a) |Spearman(bin index, bin mean)| >= 0.9 over the non-empty bins, (b) the
  top-minus-bottom bin difference has a date-clustered 95% CI (2,000 reps, seed 7) excluding 0, (c) the sign of (top - bottom) holds in >= 5 of 8
  calendar years, (d) the same sign in >= 3 of 4 instruments.
- A path FAMILY (PQ1 / PQ2 / PQ3 / PQ5) "adds value" iff >= 1 of its features is COHERENT at a primary horizon AND the best-bin mean excess vs F is
  positive.  PATH_QUALITY_ADDS_ALPHA additionally requires the best coherent bin's gross 60-min return to exceed the round-trip micro cost in ATR units.
- PQ4 context curves are reported with the same statistics but cannot by themselves open a strategy phase.
- Multiple testing: ~36 features x 2 primary horizons; the report lists the expected number of chance passes.

## 5. Follow-through diagnostic (TARGET ONLY - never a feature)
- Next-bar state label (bar b+1): bearish / weak bullish (body < 0.5) / bullish body >= 0.5 / STRONG (frozen TEST97 definition).  Per feature
  quintile report P(STRONG next) and P(bearish next); PRECONFIRM_FEATURES_PREDICT_FOLLOWTHROUGH = YES iff a feature's top-vs-bottom P(STRONG)
  difference has a date-clustered CI excluding 0 AND the same feature is economically COHERENT (economics remain the selection criterion).

## 6. Gates for later phases (not opened in Phase 1)
- ML_ELIGIBLE iff >= 600 events, >= 150 events before the first evaluated fold, >= 1 COHERENT path family, and the path effect survives F.  If
  eligible, Phase 1 STOPS; an ML-phase preregistration (Ridge net-$ ranking, Ridge/logistic TRADE/SKIP, optional barrier target; config cap
  fixed in that prereg) is committed separately before any ML run.
- GA_ELIGIBLE iff >= 3 independently COHERENT structural features AND a positive OOS deterministic or ML result (never in Phase 1).
- A strategy phase opens only after a mechanism survives; it needs its own preregistration (event, condition, entry, exit, costs, overlap and
  capacity rule, stresses, plateau, sample gate).
- Out of scope: overnight, next day, multi-day, recovery stacking, blind DCA, pyramiding, cross-index synchrony, FT2 / W3-k neighbours.

## 7. Bookkeeping
Every feature x bin x horizon row is written to out/t98/TEST98_RESEARCH_LEDGER.csv.  Reported counts: DISTINCT_VARIANTS_TESTED (feature
definitions), LEDGER_ROWS, ML configs, GA genomes.  Instruments / pooled rows are not distinct hypotheses.

## 8. Required Phase-1 fields
PATH_QUALITY_ADDS_ALPHA, EFFICIENCY_ADDS_VALUE, PERSISTENT_PRESSURE_ADDS_VALUE, LOW_DAMAGE_PATH_ADDS_VALUE, BREAKOUT_OVERSHOOT_STRUCTURE,
VWAP_ACCEPTANCE_ADDS_VALUE, OPEN_ACCEPTANCE_ADDS_VALUE, PRECONFIRM_FEATURES_PREDICT_FOLLOWTHROUGH, MAGNITUDE_NULL_SURVIVAL, BEST_MARKET,
BEST_PATH_FAMILY, ML_ELIGIBLE, GA_ELIGIBLE, DISTINCT_VARIANTS_TESTED, LEDGER_ROWS, NEW_STRATEGY_PHASE_OPENED, PORTFOLIO_MEMBERSHIP_CHANGED,
NEW_OOS_OPENED, LIVE_AUTHORIZATION.
