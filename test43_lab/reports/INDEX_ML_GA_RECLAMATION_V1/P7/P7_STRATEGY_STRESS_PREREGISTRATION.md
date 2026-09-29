# P7 ECONOMIC STRATEGY SIMULATION / STRESS — preregistration (alone)

Candidates (P6 CONSENSUS_CANDIDATES, consensus arm, stitched outer trades): C1_R1_TRAPPED_UNION (A take-all), C2_P2_FAILED_FIRST (A),
C4_L2_FAMILY (C GA), C5_HTF1_30m (A), C6_AV_OR30 (A), C7_L1_SWH60 (B ML nested).  References (A2 / ORB) excluded.
Same-mechanism group {C1, C2, C4}: each is stressed; at most one may enter any frontier.
Execution: 1 micro per signal; entry = FP[5b+5] (next legal open), exit = FP at the arm's horizon (h12: 5(b+13), h24: 5(b+25), 16:15: grid 404).
Concurrency is NOT capped to one position: every signal trades if capacity allows.  Capacity (conservative): a trade is skipped if, at any minute
of its holding interval, Main occupancy + open candidate micros + 1 would exceed MNQ 6 / MES 8; MYM 4 and M2K 4 (candidate only).
Stresses: base cost; SLIP4; +1 signal-bar delay (entry FP[5b+10], same exit; skipped if entry >= exit); deterministic 20% missed entries (every
5th trade in chronological order removed); remove top-3 days; chronological folds O1-O5; 2022 P&L and 2022 matched-beta excess (P6 control);
peak concurrent MES / MNQ / MYM / M2K (candidate and Main+candidate); approximate margin (APPROX initial margin per micro: MES 1,500, MNQ 2,100,
MYM 1,000, M2K 800); turnover (trades / day).
STRATEGY_STRESS_PASS: base > 0, SLIP4 > 0, delay > 0, missed-20% > 0, remove-top3 > 0, >= 3/5 folds positive, after capacity.
Routes (Main measured on the same stitched window; Main + candidate daily sum):
ROUTE A CORE ALPHA: incremental >= +$5/day (>= +$10 stronger), standalone and SLIP4 > 0, ret/DD >= Main, MaxDD <= 1.10 x Main, worst >= -$5,000.
ROUTE B SMALL DIVERSIFIER: incremental >= +$1.5/day, standalone and SLIP4 > 0, |corr Main| <= 0.35, ret/DD >= 1.02 x Main, MaxDD <= 1.03 x Main
or improves, worst day not worse by > $250, capacity valid.
ROUTE C RISK REDUCER: incremental >= -$0.5/day, MaxDD or bottom-5% mean loss improves >= 5%, ret/DD improves, worst day not worse by > $250.
All accepted items: RELAXED_GATE_SELECTION_EXPOSED = YES, HISTORICAL_SELECTION_EXPOSED = YES; none joins official Main.
