# TEST43-P FINAL PRE-HOLDOUT PREFLIGHT

Audit only. No strategy, candidate, weight, selection or threshold was changed. HOLDOUT NOT OPENED.

```
FREEZE_HASHES_PASS = YES
CODE_HASHES_PASS = YES
DATA_HASHES_PASS = YES
DEV_REPRODUCTION_PASS = YES
VAL_REPRODUCTION_PASS = YES
HOLDOUT_UNTOUCHED_CONFIRMED = YES
ACCEPTANCE_EVALUATOR_PASS = YES
SESSION_MATCHED_BETA_READY = YES
READY_TO_OPEN_HOLDOUT = YES
HOLDOUT_OPENED = NO
```

Frozen: PRIMARY = P2B_STATIC_4SLEEVE|MODERATE; SECONDARY_1 = P2_STATIC_DIVERSIFIED|MODERATE; SECONDARY_2 = P1_CLUSTER_EQUAL_RISK|CONSERVATIVE.

## 1. Frozen files (SHA256 = expected = sidecar; byte-identical to HEAD and to their creation commits 21f0b33 / 1b54501)
| file | sha256 | bytes | pass |
|---|---|---|---|
| TEST43P_PRE_VAL_FREEZE.json | `18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817` | 14990 | True |
| TEST43P_FINAL_PORTFOLIOS.json | `3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7` | 22576 | True |
| TEST43P_HOLDOUT_ACCEPTANCE_RULES.json | `62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0` | 2287 | True |

The final manifest references the pre-VAL freeze and rules hashes, and its selection equals the rules' evaluated portfolios.

## 2. Candidate parameter hashes (recomputed from out/v6/shortlist.json; equal in the pre-VAL freeze and final manifest)
| candidate | frozen sha256 | pass |
|---|---|---|
| MNQ_arch_A_AGG_0 | `0fac501664da5045…` | True |
| MNQ_robust_A_MOD_2 | `94d6e15e51286926…` | True |
| MNQ_r2_C_MOD_1 | `8835af3fb6d8ea75…` | True |
| MNQ_robust_C_CON_0 | `6b60e4d482c8a97c…` | True |
| ES_robust_A_MOD_1 | `e472a139f17eb52b…` | True |
| ES_r2_F_MOD_2 | `19c1623b2afe5add…` | True |
| ES_r2_A_CON_1 | `295b8f3e22bd1a56…` | True |
| ES_robust_C_CON_4 | `f55f831f394d4cdf…` | True |
| ES_robust_F_AGG_0 | `da9903537d981ec9…` | True |
| MNQ_arch_E_AGG_0 | `51abc03cb431d0da…` | True |
| ES_r2_G_AGG_0 | `f72aa914f5be5299…` | True |

## 3. Code hashes (manifest files equal; supporting modules byte-identical to the pre-VAL freeze commit)
| file | sha256 now | pass |
|---|---|---|
| t43/portfolio.py | `e2da1d5d1d1ac3d6…` | True |
| t43/sleeves.py | `6a8e60b6017fd0c5…` | True |
| t43/v6a.py | `cc1bd489915c0278…` | True |
| t43/v6x.py | `6ae46e8aa439644a…` | True |
| p02_fingerprint.py | `fe5ab5dc010c61c1…` | True |
| p03_portfolio_dev.py | `663c926ae84e6209…` | True |
| p04_pre_val_freeze.py | `e95d7f6f65146292…` | True |
| p05_val_confirm.py | `89fc7795b3ed17a8…` | True |
| p06_final_freeze.py | `bcebb61bc8a6089a…` | True |
| t43/v6lab.py | `b3451ead1d2bb1e7…` | True |
| t43/features.py | `5470e3db652c6585…` | True |
| t43/lab.py | `9d7852dcb876457f…` | True |
| t43/instruments.py | `f2131b35da0bdbc4…` | True |
| t43/bars.py | `400d5f6be3639ee7…` | True |
| t43/v533.py | `0292d52b125f9b98…` | True |
| t43/metrics.py | `99ed0c68d89c9384…` | True |
| t43/bench.py | `67ca436e7832000d…` | True |

New audit-only files (not part of any strategy path): `src/p07_acceptance.py` `36dd2755bd32d5bdf64a2f8025dda6bbe5b15aa466bce82171f31c3d86271e1f`, `src/p08_preflight.py` `90413343ae75f8e5bb6f335c3d522d6434e4c4b1d2e0fbd6c96498cf5eeba0fd`.

## 4. Canonical data (hashed BEFORE parsing)
ES `2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116` pass=True; MNQ `66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2` pass=True.

## 5-6. Holdout untouched; window
* Every TEST43-P path loads bars through `v6lab.load(inst, end=VAL_END)` / `sleeves.run_sleeve(end=VAL_END)`, which drop all
  session_date > 2025-09-30 rows immediately after reading the bar file, before features, sleeves or portfolio; no TEST43-P call
  uses `end=None`. The 3m bar files on disk contain holdout rows (built from the full canonical files in V1); those rows are read
  and discarded, never evaluated.
* All 37 dated TEST43-P output tables and all sleeve files end on or before 2025-09-30.
* Window: lab HOLDOUT split starts 2025-10-01; rules window ['2025-10-01', '2026-05-27']; pre-VAL freeze marks HOLDOUT "closed".
* This preflight reproduced DEV/VAL only; no holdout P&L was computed or reported.

## 7. Reproduction from the full canonical files
3m bars rebuilt from canonical 1m (normalise -> aggregate_3m -> clock), truncated at 2025-09-30, compared to the stored bars:
ES 752,381 rows identical=True; MNQ 751,048 rows identical=True.
All 11 sleeves rerun from the rebuilt bars: max |daily P&L diff| = 1.8e-12.
All 18 frozen portfolio variants (incl. the 3 selected): max |daily P&L diff| DEV 9.1e-13, VAL 9.1e-13 (floating-point rounding only); identical session index.

## 8-9. Simulator structure
virtual sleeves (standalone ledgers, output = desired exposure only) -> risk normalisation (w = budget x L / sigma_DEV; weights equal the
final manifest) -> ONE float target per instrument (verified = sum of weighted sleeve desires) -> shared-account governor (one equity,
HWM, DD tier, day cut, margin) -> integer net target -> one order stream per instrument (fills ES [281, 2288] for PRIMARY, [ES, MNQ]).
No sleeve creates fills; only the net target is executed. A single-sleeve portfolio reproduces the standalone sleeve exactly.

## 10. Costs, margin, account
commission $0.62/side, 1 tick slippage, roll MES $3.74 / MNQ $2.24, margin fractions MES [0.06416935897435898, 0.09167051282051282], MNQ [0.07769201093071854, 0.11098842629802283],
marginU 0.5, one $150,000 account — all equal to the final freeze: True.

## 11. Acceptance evaluator (`src/p07_acceptance.py`)
Implements exactly: total net P&L > 0; no margin breach; peak margin utilisation <= 0.5 of equity; MaxDD <= envelope DD (window
drawdown measured from the entry account level); worst day >= envelope floor; remove-top-3 average/day > 0; best day <= 35% of
total net P&L. Reported only: matched beta, SLIP4, TIMING_BRITTLENESS_STRESS, SESSION_MATCHED_BETA.

Self-tests (synthetic):
| case | expected pass | got | targeted condition | ok |
|---|---|---|---|---|
| baseline_pass | True | True | None | True |
| negative_total | False | False | net_pnl_positive | True |
| margin_breach | False | False | no_margin_breach | True |
| margin_util_above_0.5 | False | False | peak_margin_util_le_0.5 | True |
| maxdd_breach_MOD | False | False | max_dd_within_envelope | True |
| worst_day_CONS | False | False | worst_day_within_envelope | True |
| worst_day_same_ok_MOD | True | True | None | True |
| top3_dependence | False | False | remove_top3_avg_positive | True |
| single_day_concentration | False | False | best_day_le_35pct_of_total | True |

Dry run on VAL (evaluator mechanics only; not a decision, not a holdout result):
| role | PASS | total | MaxDD | worst | ex-top3 avg | best-day share | peak margin |
|---|---|---|---|---|---|---|---|
| PRIMARY | True | 21,061 | 3,663 | -1,926 | 66.6 | 0.161 | 0.113 |
| SECONDARY_1 | True | 22,201 | 4,358 | -2,270 | 63.5 | 0.189 | 0.142 |
| SECONDARY_2 | True | 13,720 | 2,541 | -1,655 | 46.3 | 0.142 | 0.078 |

## 12. SESSION_MATCHED_BETA (REPORT ONLY; not a pass condition; not used for any selection)
Passive long per instrument sized to the portfolio's average RTH contracts during RTH bars and average overnight contracts
during non-RTH bars, adjusted prices, net of size-change commission + 1 tick and roll cost.
| portfolio|period | portfolio net | session-matched net | excess $/day | ES RTH/ON | MNQ RTH/ON |
|---|---|---|---|---|---|---|
| PRIMARY|DEV | 120,564 | 43,467 | 54.0 | 1.01/0.87 | 1.77/1.33 |
| PRIMARY|VAL | 21,061 | 9,273 | 62.7 | 0.88/0.73 | 1.31/0.85 |
| SECONDARY_1|DEV | 99,999 | 38,524 | 43.1 | 1.04/0.87 | 1.50/1.13 |
| SECONDARY_1|VAL | 22,201 | 8,578 | 72.5 | 0.93/0.74 | 1.10/0.83 |
| SECONDARY_2|DEV | 70,200 | 26,510 | 30.6 | 0.78/0.74 | 0.85/0.71 |
| SECONDARY_2|VAL | 13,720 | 5,877 | 41.7 | 0.69/0.64 | 0.70/0.55 |

## Conclusion
Every required integrity item passes. The system is READY for the separate one-shot holdout command. HOLDOUT_OPENED = NO.
Machine-readable: `out/p/freeze/TEST43P_FINAL_PREFLIGHT.json`.
