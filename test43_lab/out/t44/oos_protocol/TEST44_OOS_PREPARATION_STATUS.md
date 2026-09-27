# TEST44 NEW-OOS PREPARATION STATUS

No market data after 2026-05-27 was acquired, downloaded, parsed or inspected. Nothing about strategies, models, allocation or acceptance rules changed.

```
PRE_OOS_FREEZE_UNCHANGED = YES
OOS_RULES_UNCHANGED = YES
OOS_DATA_PROTOCOL_FROZEN = YES
OOS_DATA_PROTOCOL_JSON_SHA256 = f50902babcbc848574984abb59c4e9cd435e2a3d20878a66955686b6429d7cc3
OOS_DATA_PROTOCOL_MD_SHA256 = a7e846c4fdfbef214cbd46cb4dc08a661d3344b3b48328ea212f121628decdc3
OOS_EVALUATOR_READY = YES
OOS_EVALUATOR_SHA256 = dde908ea03ae93d31f827c21366f7a2088c8027ab711f86d64dbce37fafa3b29
OUTPUT_SCHEMA_SHA256 = 33ea7e876a1b7144bb58078236b3b7bd7a1ff7cf4ed351287294da05b516093d
EVALUATOR_DRY_RUN = historical mechanics check only (2025-10-01..2026-05-27, already USED data): all integrity checks passed, historical daily P&L reproduced (max diff 4.5e-13), refusal without flags verified
MIN_COMPLETED_RTH_SESSIONS_BEFORE_EVALUATION = 120
OOS_RTH_SESSIONS_EVALUATED = 0
NEW_OOS_DATA_ACQUIRED = NO
NEW_OOS_OPENED = NO
LIVE_AUTHORIZATION = NO
```

## Evaluator (`src/t44_oos_evaluator.py`, prepared, not run on OOS)
* Candidates: CHAMPION_CONTROL_V1, SIMPLE_INTEGER_CHALLENGER, RIDGE_CHALLENGER, XGBOOST_CHALLENGER only.
* Refuses to run without `--oos-es`, `--oos-mnq` and `--confirm-open-new-oos`.
* Fail-closed checks BEFORE any economics: pre-OOS freeze and rules SHA256; all frozen code hashes; Ridge and XGB model hashes; champion manifest hash; OOS data protocol hash; sleeve parameter hashes; frozen canonical hashes; delivered OOS files hashed before parsing; protocol validators (schema, byte/value-identical prefix through 2026-05-27, append-only ordering, no maintenance-hour bars, roll/adjustment invariants, OHLC); 3m bars rebuilt from the delivery equal the frozen rebuild through 2026-05-27; historical daily P&L of all four candidates through 2026-05-27 reproduces the frozen values; no pre-2026-05-28 date inside the OOS window; >= 120 completed RTH sessions (session with the 16:00 RTH closing bar for BOTH ES and MNQ; early-close days do not count, which makes the gate stricter).
* Meta procedure exactly as frozen: OOS block 1 (sessions 1-63) uses the hash-verified final fits; then expanding refit every 63 sessions with a 1-session purge.
* Report-only additions: FROZEN_MODEL_PREFIX (OOS sessions 1-63) and ONLINE_REFIT_CONTINUATION (64+) metrics; ORIGINAL_CHAMPION_CONSERVATIVE diagnostic (MaxDD <= $10k, worst >= -$2k) for the champion; session-matched beta; integer sleeve attribution. The frozen MODERATE rules remain authoritative.
* Output schema: `out/t44/oos_protocol/TEST44_OOS_OUTPUT_SCHEMA.json`.

Data protocol: `out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.md` / `.json` (hashes above).
