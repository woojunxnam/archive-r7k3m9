# P8 POSITION MANAGEMENT (bounded recovery / winner pyramid) — preregistration (alone)

OUR_NEW_HYPOTHESIS (not attributed to Nick Shawn / ICT / Dante / PATs).  Bases = P7 STRESS_PASS candidates with positive stitched economics:
C1_R1_TRAPPED_UNION (take-all), C2_P2_FAILED_FIRST (take-all), C7_L1_SWH60 (ML nested).  Identical initial populations (stitched outer trades,
before capacity; capacity / peak units of the add units reported).  Max 2 units, ADD1 only, no ADD2, no overnight stacking, frozen exit =
the base exit (16:15 coordinate); no optimised price stop (NO_HARD_STOP discovery with actual MAE tails and margin reported).
Arms:
A SINGLE.
B BLIND_DCA_CONTROL: ADD1 at the next open after the first completed 5m bar of the holding window whose close <= UNIT1 entry - 0.5 x ATR_d.
C FRESH_SIGNAL_RECOVERY: ADD1 at the entry (next legal open) of the first NEW independent bank event in the same instrument-session occurring
  after UNIT1 entry and before its exit, provided the basket is underwater at that event's decision close (close < UNIT1 entry).
  Independent = events of OTHER bank candidates not sharing the base mechanism: base C1 or C2 -> {C3, C5, C6, C7, C8}; base C7 -> {C1, C3, C5, C6, C8}.
D WINNER_PYRAMID: same independent-event rule, provided UNIT1 is in profit at the event decision close (close > UNIT1 entry).
Accounting: UNIT1 EV ($/base trade), ADD1 marginal EV ($ per add, base cost; also SLIP4) with date-clustered 95% CI (2,000 reps), basket EV,
number of adds, worst basket P&L, basket MAE p95 / p99 (1m lows), 2022.  RULE: ADD1 marginal EV <= 0 -> STOP (no deeper stack, no exception).
Exit architectures (only for an arm with ADD1 marginal EV > 0 and >= 100 adds): R1 basket break-even + costs (exit both units at the first 1m
close >= basket BE + round-trip costs after the add, else base exit); R2 peel ADD1 when price recovers to UNIT1 entry (ADD1 exits, UNIT1 keeps
base exit).  R3 VWAP / R4 AVWAP recovery NOT RUN (VWAP / AVWAP information was not validated in TEST100 / TEST101).  R5 structural level
recovery NOT RUN (no frozen level carried in the base trade records of these families).
A management arm is MANAGEMENT_IMPROVEMENT only if ADD1 marginal EV > 0 with CI lower > 0 is NOT required, but ADD1 EV > 0, SLIP4 ADD1 EV > 0,
>= 3/5 folds positive for the add P&L, and worst basket loss not worse than 2 x the worst single-unit loss.
