# Dashboard Claude Code Handoff Prompt

You are taking over integration of MAIN_GROWTH_V2 into the user's futures dashboard.

FIRST, read every file in:

`test43_lab/handoffs/MAIN_GROWTH_V2_MICRO_DASHBOARD_HANDOFF_V1/`

Do not start coding before reading:
- 00_START_HERE.md
- 01_PORTFOLIO_SPEC.json
- 02_EXECUTION_LOGIC.md
- 03_SOURCE_MANIFEST.json
- 04_DASHBOARD_DATA_CONTRACT.json
- 05_RUNBOOK.md
- 06_VALIDATION_CHECKLIST.md
- 08_METRICS_AND_STATUS.json
- 09_LIVE_IMPLEMENTATION_GAPS.md

Then run:

```bash
python test43_lab/handoffs/MAIN_GROWTH_V2_MICRO_DASHBOARD_HANDOFF_V1/verify_handoff.py
```

Treat the listed canonical source paths as authority. Do not re-derive the strategy from prose when code exists.

MAIN_GROWTH_V2 is MICRO ONLY:
- T61-R1C_ATOMIC_CAP6
- FIXED_CLUE_BASKET_V1
- C2_P2_FAILED_FIRST 1 micro
- FIRST_WINNER_ADD1 1 additional micro
- ES->MES, NQ->MNQ, YM->MYM, RTY->M2K
- no ADD2
- no recovery/DCA
- C2 exits 16:15
- T61 may hold overnight

Your first implementation target is READ_ONLY_SHADOW dashboard integration, not broker execution.

Critical blocker:
the historical C2 capacity allocator uses future interval occupancy and is not live-causal.
Do not port that behavior into live execution.
Implement/preregister C2_LIVE_CAUSAL_ALLOCATOR_V1, replay it historically, and report the metric delta before asking for broker authorization.

Also note:
the frozen clue basket currently has no complete forward integration runner.
Build it from the frozen package and prove historical parity before marking its dashboard card VALID.

Never use post-2026-05-27 data for research retuning.
Forward OOS starts 2026-09-29.

When finished, return:
1. files changed,
2. dashboard architecture,
3. parity results,
4. causal allocator replay results,
5. remaining blockers,
6. exact steps required before any live broker execution.
