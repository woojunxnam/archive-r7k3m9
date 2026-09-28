# TEST97_AUDIT_CORRECTION_1 — preregistration

Written and committed BEFORE any corrected code or economics are run.  Governance sequence: PREREG COMMIT -> EXECUTION -> RESULT COMMIT.
Base: commit 84a6dd7.  Research data end 2026-05-27.  CURRENT MAIN (T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1) unchanged.  NEW_OOS_OPENED = NO,
LIVE_AUTHORIZATION = NO.  No new parameter values: every threshold, window, k, horizon and definition below is the one already preregistered in
TEST97 Wave 1 (d6fb544b), Wave 2 (9136fe6c), Phase 3 (985955df) or Wave 3 (0e027b59).  Nothing here can promote FT2 or change MAIN.
Out of scope in this pass: overnight, next day, multi-day, ML, GA, new FT2 thresholds, NQ-only optimisation, cross-index FT2 synchrony, TEST98.

Common statistics used below: forward returns in ATR_d units from the TEST97 engine (entry = open of the bar after the completed signal bar);
date-clustered bootstrap (instruments on the same date form one cluster), seed 7; 2,000 replications unless stated; "positive years" = calendar
years 2019..2026 with a positive mean.

## B. Count terminology (no economics)
Report TOTAL_TEST97_LEDGER_ROWS (= rows of out/t97/TEST97_RESEARCH_LEDGER.csv), TOTAL_TEST97_DISTINCT_VARIANTS (= distinct variant definitions,
i.e. candidate_id before "|"), TOTAL_TEST97_ML_CONFIGS = 0, TOTAL_TEST97_GA_GENOMES = 0.  "570" must not be called distinct variants.

## C. W3_V1 Williams volatility breakout — implement the preregistered family null
- Events unchanged: first completed 5m close above session open + k x prior-day RTH range, bars 1..65, k in {0.1, 0.2, 0.3, 0.5, 0.75}
  (k = 0 is the family null population).  Common population (signal bar <= 67) as in the engine.
- Family null (exact bar-index matching): for a k > 0 event of instrument i at bar b in session s, null value = mean forward return of the k = 0
  events of the SAME instrument at the SAME bar index b in OTHER sessions.  Events with no such k = 0 event are dropped and counted.
- Report per k (ES / NQ / YM / RTY and pooled) at h6, h12, h16:15: n, gross mean, xA, xB1, family-null excess, date-clustered 95% CI of the
  family-null excess (pooled), positive years.
- Classification: if the pooled family-null excess has CI lower bound > 0 at a preregistered horizon AND >= 5 positive years AND gross > cost, the
  result is labelled CORRECTED_HISTORICAL_CLUE (not promoted, no strategy opened); otherwise W3_V1 stays NO_EDGE.

## D. W3_V3 first pullback — same-session paired comparison
- Qualifying population = sessions where the preregistered sequence completes: first bar < 60 with close > prior 60-bar high (thrust, bar b0);
  first later bar whose low touches EMA20 or VWAP; then the first bullish bar closing above the prior bar high (resumption, bar b1 <= 65).
  Definitions, windows and thresholds unchanged.
- On exactly these sessions: A_CHASE = entry open of bar b0+1; B_PULLBACK = entry open of bar b1+1.
- (1) Own-horizon comparison: h6 / h12 / h16:15 from each entry.  (2) Timing attribution at the SAME absolute exit minute: both entries exit at
  (a) the pullback entry's h12 exit minute and (b) 16:15.  Paired difference B - A per session with date-clustered 95% CI (2,000 reps),
  ES / NQ / YM / RTY and pooled; MFE / MAE (60-min path stats of each entry).  Strategy economics are NOT opened, so SLIP4 is not applicable.
- Until run: FIRST_PULLBACK_ADDS_VALUE = UNRESOLVED / IMPLEMENTATION_BLOCKED.

## E. M04 follow-through — timing attribution at the same exit minute
- Identical confirmed populations B_next_bull, C_next_close_gt, E_next_HH_HL, F_next_STRONG (confirmation at bar b+1 after the N = 12 STRONG
  breakout bar b) and D_two_bull (confirmation at b+2).
- INFORMATION value (unchanged definition): confirmed minus unconfirmed, both entered at the same decision minute, h6 / h12.
- TIMING value: on the confirmed events only, ORIGINAL entry (open of b+1) vs CONFIRMATION entry (open after the confirmation bar), both exiting at
  the SAME absolute minute: (a) the confirmation entry's h12 exit minute, (b) 16:15.  Paired difference with date-clustered 95% CI.
- The FT2 entry rule is not changed.  Until run: FOLLOW_THROUGH_INFORMATION = VALID CLUE, FOLLOW_THROUGH_TIMING_VALUE = UNRESOLVED.

## F. FT2 Phase-3 population / X60 audit (audit only; no rescue)
- Explain the difference between the Wave-2 FT2 EVENT_EDGE population (431 pooled, common population: confirmation bar <= 67) and the Phase-3
  trade count (~602: every RTH FT2 event with entry before 16:15, no bar cap).
- Strict X60: entry grid + 60 <= 16:15 grid (J1615).  Report the all-RTH population, the strict-X60 eligible population, the excluded late events,
  and the late-subset performance; the previous clipped X60 is relabelled X60_CLIPPED.  No new time window is created.
- Strategy-level fields for the strict X60 and X16:15 versions (per instrument and 4-index virtual sum): trades, $/day, $/trade, SLIP4, and the
  prospective long-only 2022 fields (absolute 2022 P&L, matched-long excess (A), loss-capture ratio = 2022 P&L / 2022 matched-long P&L,
  2022 MaxDD, 2022 worst day, average and peak exposure (contracts), recovery = first date after 2022 at which cumulative P&L regains its
  2021-12-31 level).
- Any portfolio numbers are labelled VIRTUAL_ADDITIVE_DIAGNOSTIC (no capacity), never CAPACITY_VALID_PORTFOLIO.

## G. FT2 null robustness — downgrade-only audit
- Recompute ONLY Wave-2 P2 "W2_P2_FT_STRONG" with ONE predeclared causal variant of null B2: the decile edges of 2-bar displacement and tercile
  edges of 2-bar range are computed per instrument from sessions strictly BEFORE the first session of the event's calendar month (monthly
  expanding recomputation); warm-up = the first 120 sessions of each instrument are excluded from the event population.  Cell membership and
  the cell mean pool are otherwise unchanged (contemporaneous matched control, as for null A).
- Report old (full-sample edges) and causal-edge results, each with a 5,000-replication date-clustered bootstrap, for h6 / h12 / h16:15.
- Rule: if the causal-edge pooled h12 CI lower bound <= 0 or < 5 positive years, FT2_STATUS is DOWNGRADED to "EVENT CLUE NOT ROBUST TO CAUSAL
  MATCHING"; a better result can NOT upgrade FT2 (it stays a rejected-strategy event clue, selection exposed).

## H. Position-management governance (documentation)
- RECOVERY_STACK = REJECT on the FT2 initial population (ADD1 < 0 in ES / NQ / YM / RTY); no ADD2 / ADD3 research.
- Standing rule for any future stack: if ADD1 <= 0 -> stop deeper stacking automatically.
- The existing blind-DCA code used "average - 0.5 ATR x units" for deeper adds while the prereg said "average - 0.5 ATR" per add; the deeper
  blind-DCA outputs are marked NOT USABLE for any positive conclusion (no rerun needed).

## Final classifications to report
TEST97_PORTFOLIO_SURVIVOR, FT2_STATUS, W3_V1_STATUS, W3_V3_FIRST_PULLBACK_STATUS, FOLLOW_THROUGH_INFORMATION_STATUS, FOLLOW_THROUGH_TIMING_STATUS,
RECOVERY_STACK_STATUS, PORTFOLIO_MEMBERSHIP_CHANGED = NO, NEW_OOS_OPENED = NO, LIVE_AUTHORIZATION = NO.
