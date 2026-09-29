# P4 EVENT-CONDITIONED HTF REGIME — preregistration (alone)

Question: inside the SAME frozen event population, does HTF trend STRENGTH / STAGE add information beyond simple HTF direction?
Populations: A = C1_R1_TRAPPED_UNION, B = C2_P2_FAILED_FIRST, C = C5_HTF1_30m (a strong 30m bar is a momentum event, so HTF strength is a
meaningful conditioner).  Outcome: net ATR return at the frozen 16:15 horizon (CANDIDATE_EVENTS.parquet).
Null (within population): leave-one-out cell mean over events of the same population in year x vt x tod3 x disp6 tercile (event magnitude)
x up50 (simple HTF direction); >= 10 other events per cell; fallback (1) drop year, (2) drop year and vt.  disp6 tercile edges and the feature
quintile edges are CAUSAL (per population, from events in sessions strictly before the month; 120-session warm-up; >= 50 prior events).
Features (frozen, P1 dictionary): adx14, stage_slope, tsmom1, tsmom12.  4 features x 3 populations = 12 response curves; no thresholds.
Coherence (per curve, 16:15): |Spearman| >= 0.9, top-minus-bottom date-clustered CI (2,000 reps, seed 7) excludes 0, same sign in >= 5/8 years
and >= 3/4 instruments.  EVENT_CONDITIONED_HTF = VALUE if >= 1 COHERENT curve whose best bin has positive excess; the coherent features are then
allowed into later ML only for that population.  Otherwise EVENT_CONDITIONED_HTF = SATURATED.
