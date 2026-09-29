# Live Implementation Gaps / Mandatory Blockers

This file is mandatory reading.

## 1. There is no single canonical V2 forward runner yet

Existing:
- T61 forward-shadow runner: YES.
- Fixed clue basket frozen package: YES.
- Fixed clue basket integrated forward runner: NO.
- C2 + winner integrated forward runner: NO.

Therefore do not claim that the current repo can already emit a fully live MAIN_GROWTH_V2 broker target.

## 2. Historical C2 capacity allocator is not live-causal

`rp_p9.allocate()` and related historical code evaluate capacity with logic equivalent to:

```python
base = main_occ[session, entry:exit+1]
if max(base + candidate_occ[entry:exit+1]) + lots > cap:
    skip_trade
```

At the entry time this inspects Main occupancy later in the same holding interval.
That future occupancy is unavailable live.

This does NOT prove the C2 signal itself has lookahead; it is an execution/allocation issue.
It was often conservative because it skipped trades that might later conflict, but it can still change historical selection and P&L.

## 3. Required live-causal replacement

Do not silently replace the allocator and call it equivalent.

Create and preregister a small implementation audit:

`C2_LIVE_CAUSAL_ALLOCATOR_V1`

Proposed mechanics:
- at C2 entry/add fill, check capacity using current known Main target + already-open overlay positions only;
- if allowed, fill the overlay;
- later, if MAIN_GROWTH_V1 raises its target and a cap would be exceeded, Main has priority;
- reduce/cut overlay at that legal fill time;
- candidate reductions should use a deterministic frozen rule, preferably latest overlay unit first (winner ADD1 before parent base where possible);
- never anticipate future Main targets.

Replay 2021-01-01..2026-05-27 and compare against the research allocator.

Required report:
- trade/base/add fills changed
- forced cuts
- avg/day
- SLIP4
- MaxDD
- worst day
- ret/DD
- per-instrument changes
- capacity conflicts
- difference vs $160.65/day research frontier

Until this audit passes:
- dashboard display = allowed
- forward shadow = allowed
- automatic broker execution of the C2 sleeve = BLOCKED

## 4. User promotion status

The user has promoted MAIN_GROWTH_V2 to **LIVE CANDIDATE** for dashboard use.

That promotion does not erase:
- historical selection exposure,
- final-selection DSR ~0.023,
- PBO ~0.36,
- RC p ~0.36,
- or the capacity implementation issue above.

Show those facts in the strategy details panel rather than hiding them.
