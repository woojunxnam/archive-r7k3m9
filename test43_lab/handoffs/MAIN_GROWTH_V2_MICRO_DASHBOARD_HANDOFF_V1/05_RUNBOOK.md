# Dashboard Integration Runbook

## Phase A — integrity
From repository root:

```bash
python test43_lab/handoffs/MAIN_GROWTH_V2_MICRO_DASHBOARD_HANDOFF_V1/verify_handoff.py
```

Any mismatch is fail-closed.

Also verify frozen T61 package with its existing verifier before using T61 state.

## Phase B — reproduce T61 first
Existing forward-shadow command:

```bash
cd test43_lab
python shadow/forward_shadow.py forward \
  --es <path-to-current-ES-1m-parquet> \
  --mnq <path-to-current-MNQ-1m-parquet> \
  --through YYYY-MM-DD
```

This produces T61/C43/T55 shadow outputs only. It does NOT yet produce the complete V2.

The dashboard should consume the T61 session log fields rather than rewrite T61 logic.

## Phase C — integrate frozen clue basket
Do not recreate rules from memory.
Read:
- `frozen/fixed_clue_basket_v1/MANIFEST.json`
- `frozen/fixed_clue_basket_v1/src/t94b_basket.py`
- frozen model files in `frozen/fixed_clue_basket_v1/models/`

Build a forward-only adapter and historical parity test it against the frozen basket ledger before displaying it as VALID.

## Phase D — integrate C2
Required live signal inputs:
- ES 1m
- NQ 1m
- YM 1m
- RTY 1m
with the exact session/timestamp semantics expected by t96/t97/mp_engine.

Generate P2_FAILED_FIRST from canonical source logic, not from historical event parquet.

Then maintain per-open-trade state for first-winner ADD1.

## Phase E — causal capacity allocator
Historical research allocator is NOT the live allocator. See `09_LIVE_IMPLEMENTATION_GAPS.md`.

Required dashboard behavior until causal replay is completed:
- calculate RAW desired V2 targets;
- calculate CURRENT capacity availability;
- show whether an order would currently be allowed;
- keep broker execution disabled.

## Phase F — dashboard mode
Initial mode:
`READ_ONLY_SHADOW`

Display:
- component desired targets
- final capacity-adjusted shadow targets
- reason codes
- current position if broker connection exists
- daily P&L
- overnight inventory
- data freshness
- source integrity
- causal allocator validation flag

Only after parity + causal-capacity replay passes should a separate user-approved step enable broker actions.

## Historical parity targets
Main V1, 2021+:
- avg/day 151.7795
- MaxDD 13936.30
- worst -4666.44

V2 research frontier, 2021+:
- avg/day 160.6549
- SLIP4 157.3637
- MaxDD 14105.27
- worst -4791.92
- ret/DD 0.0113897

C2 counts in winner audit:
- base opportunities 590
- first eligible winner opportunities 545

Do not demand exact V2 metric parity from a corrected causal live allocator; report the difference explicitly.
