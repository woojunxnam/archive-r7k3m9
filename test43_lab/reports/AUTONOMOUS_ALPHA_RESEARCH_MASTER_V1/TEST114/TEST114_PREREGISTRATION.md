# TEST114 ACADEMIC INTRADAY (CLOSE) MOMENTUM — preregistration

Committed ALONE before any TEST114 economics.  Master prereg 319a7f6.  Attribution: SOURCE_SUPPORTED_PRINCIPLE, Tier 1 (Gao, Han, Li & Zhou,
"Market intraday momentum", JFE 2018: the first half-hour return measured from the prior close predicts the last half-hour return; the
second-to-last half-hour return adds information).
Comparison with TEST49 (closed): TEST49 T3 late strength used return since the OPEN >= 0.5 ATR_d plus range position at 14:30/15:00 held to
16:15.  GHLZ uses the return from the PRIOR CLOSE (includes the overnight gap) to 10:00, sign only, and the last half hour only.  If the GHLZ
predictor carries no information beyond the same-window "return since open > 0" predictor -> RESEARCH_DUPLICATE.

Clock (1m END-stamped grid, j = 0 is 09:31): P(10:00) = close of j = 29; prior close = prior session close of j = 389 (16:00); decision at 15:30 =
close of j = 359; entry = FP[j = 360] (next legal open); exit = FP[J16 = 390] (16:00).  One event per instrument-session.
Definitions (long only; short signals are not traded):
- G1_R1: r1 = (P(10:00) - prior close) / ATR_d > 0 -> long 15:30 -> 16:00.
- G2_R1_R12: r1 > 0 AND r12 = (P(15:30) - P(10:00)) / ATR_d > 0 -> long 15:30 -> 16:00.
- G1_R1_X1615 (the single allowed adjacent timing sensitivity): G1 condition, exit FP[J15] (16:15).
- TB_OPEN_CONTROL (duplication control, same window): return since the 09:30 open at 15:30 > 0 -> long 15:30 -> 16:00.
4 definitions.  Outcome = return / ATR_d net of micro round-trip cost.
Null: unconditional 15:30 -> exit long, cell mean over all valid sessions of the same instrument in year x vt (all sessions, leave-own-out
immaterial).  Date-clustered 95% CI (2,000 reps, seed 7); positive years; instrument signs; 2021+; 2022.
EVENT_CLUE / STRONG as ESP-1 with the single primary horizon (the exit named in each definition); STRONG adjacency: G1 <-> G2 same sign
>= 50% magnitude.  Duplication test: among sessions with TB_OPEN_CONTROL = TRUE, the mean difference (r1 > 0) minus (r1 <= 0) of the last
half-hour return with date-clustered CI; if the CI includes 0 AND the G1 excess is not larger than the TB excess -> RESEARCH_DUPLICATE.
A strategy phase (separate prereg) only for a non-duplicate STRONG_CLUE.
