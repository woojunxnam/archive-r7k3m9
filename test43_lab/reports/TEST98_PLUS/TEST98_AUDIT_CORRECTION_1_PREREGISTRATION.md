# TEST98_AUDIT_CORRECTION_1 — preregistration (committed alone before execution)

Base: TEST98 Phase-1 result commit 91dbf4a (prereg 12d9765).  Not a new research phase; no new parameters or hypotheses.  CURRENT MAIN unchanged;
research data <= 2026-05-27; NEW_OOS_OPENED = NO; LIVE_AUTHORIZATION = NO.

1. Feature correction (only PQ2_bullrun12 and PQ2_hlrun12).  The Phase-1 runmax() took a rolling max of an UNBOUNDED run counter, so a run that
   began before the 12-bar window could exceed 12.  Corrected definition (= the preregistered wording): for breakout bar b, the longest run of
   consecutive qualifying bars lying entirely inside bars b-11..b of the chained 5m series (qualifying: close > open for bullrun; low > previous
   low for hlrun, the previous low may be bar b-12 as in Phase 1).  No information after b.  Everything else is re-used exactly: event population
   (fresh N=12 breakout, bars 1..67, 120-session warm-up), causal monthly quintile bins, null F (cells, causal terciles, fallback), horizons,
   coherence gate (|rho| >= 0.9, top-minus-bottom date-clustered 95% CI excluding 0 with 2,000 reps seed 7, >= 5 of 8 years, >= 3 of 4 indices),
   follow-through diagnostic.  Old vs corrected results are reported for these two features only; no neighbour features.
2. Wording corrections: PHASE1_CROSS_VALIDATION = NOT RUN (Phase 1 used prior-session monthly expanding quantile boundaries, a date-clustered
   bootstrap and calendar-year consistency, not chronological CV folds; ML not opened).  The 22 / 37 follow-through result is relabelled
   RAW_NEXT_BAR_STRONG_ASSOCIATION (not residualised against null F, not evaluated as chronological OOS prediction); PRECONFIRM_FEATURES_PREDICT_
   FOLLOWTHROUGH stays NO under the preregistered economic definition.
3. Multiple-testing note: 74 primary coherence tests; a naive 5% CI-only reference gives ~3.7 nominal CI hits under independence; the full gate is
   much stricter and the tests are correlated, so 3.7 is not the expected number of full passes; actual full passes = 0.  No threshold changed.
4. Decision rule: if neither corrected run feature is COHERENT under the original gate -> TEST98_STATUS = CLOSED, TEST98_SIMPLE_PRECONFIRM_PATH_
   FAMILY = SATURATED, TEST98_PORTFOLIO_SURVIVOR = NO, ML_OPENED = NO, GA_OPENED = NO, PORTFOLIO_MEMBERSHIP_CHANGED = NO, NEW_OOS_OPENED = NO,
   LIVE_AUTHORIZATION = NO, OPEN_ACCEPTANCE = WEAK_RESEARCH_CLUE_ONLY.  If one becomes COHERENT it is reported as a corrected clue only (no
   strategy / ML phase opened in this correction).
