# T46_00 Authority index

Verified unchanged:

|    | file                                                | sha256                                                           |
|---:|:----------------------------------------------------|:-----------------------------------------------------------------|
|  0 | out/t44/freeze/TEST44_PRE_OOS_FREEZE.json           | 3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4 |
|  1 | out/t44/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json | 2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236 |
|  2 | out/t45/freeze/TEST45_PRE_OOS_FREEZE.json           | 185d1ef91ddffe494ce5826a5142af31644a4816bb2a4db72d110909ed1c2987 |
|  3 | out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json | 76941f63465306928e535df74641a29b172c9420c9e0a69852a4f1b0ed5356da |

Incident record (sealed-window exposure):

# TEST46 incident: exposure to sealed new-OOS window (2026-05-28+) via a legacy ledger

- When: TEST46 Phase 0 (authority recovery), before any TEST46 model, rule, feature or selection existed.
- What: Google Drive file `SCREEN_1Y_LC03_NQ_T07-11_2025-2026.csv` (id 1SlgqGnNTHiX0uKnwWjJfNGijPprLqyCK) was read in full
  to test whether CSV ledgers can be read as text. The file is a TradingView export of the frozen LC03 (NQ-NOON) strategy
  and contains 26 trades, 8 of which fall on 2026-05-28 .. 2026-08-27 (inside the sealed window). Their dates, entry/exit
  prices and P&L were displayed to the research agent.
- Not done: the content was NOT saved, parsed, summarised further, or used in any computation. No market data after
  2026-05-27 was loaded into the lab. Nothing in this repository contains those rows.
- Frozen authorities are unaffected: TEST44 (3401331f.../2f74e2ca...) and TEST45 (185d1ef9.../76941f63...) were frozen and
  pushed BEFORE this exposure.
- Consequence for TEST46: every legacy FULL_HISTORY / SCREEN ledger on Drive was exported ~2026-09-15 and very likely
  contains post-2026-05-27 trades. Reading any of them whole (the Drive connector returns full files) re-exposes the sealed
  window. TEST46 Phase 0 ledger parity therefore cannot proceed without a user decision.
- Status: TEST46 paused at Phase 0. NEW_OOS_DATA_ACQUIRED (lab data) = NO; sealed-window legacy-ledger rows VIEWED = YES (8 LC03 trades).


Legacy ledger recovery. The raw files were downloaded without display into an out-of-repo quarantine, then passed through the mechanical sanitizer (src/t46_sanitize_ledgers.py). The sanitizer outputs only the fields listed:

|    | SOURCE      | SOURCE_HASH_MATCH   | SANITIZED_FILE          | SANITIZED_SHA256                                                 |   HISTORICAL_ROW_COUNT | MAX_RETAINED_ENTRY_DATE   | MAX_RETAINED_EXIT_DATE   | CUTOFF_COMPLIANCE   |
|---:|:------------|:--------------------|:------------------------|:-----------------------------------------------------------------|-----------------------:|:--------------------------|:-------------------------|:--------------------|
|  0 | LC02.csv    | NO                  | LC02_TO_20260527.csv    | 218f898c7e6e77e5c20d0ab71d3a1711ffd03f6dfefd356682ab087874f28dda |                    363 | 2026-05-14                | 2026-05-14               | PASS                |
|  1 | LC03.csv    | NO                  | LC03_TO_20260527.csv    | b4cbb6339bcaf2c9fa4b48867c12341d197d7707d7511cd1c74cc47eeafa97bf |                    430 | 2026-05-20                | 2026-05-20               | PASS                |
|  2 | LC05.csv    | NO                  | LC05_TO_20260527.csv    | 24243f1481a72c1b059cfcad9691b51c0304f43c8ae0cfddbbe437eed81f09bc |                   1322 | 2026-05-26                | 2026-05-26               | PASS                |
|  3 | T30_W01.csv | NO                  | T30_W01_TO_20260527.csv | 048e1e4a86b5dcd18538f93a512c0f6f9fdac1bdc908cbc789dd6ad2703bb2ab |                   1069 | 2026-05-21                | 2026-05-21               | PASS                |

The PROPFIRM_PORTFOLIO_V1 authority-hash evidence files are workstation-only and not reachable from this cloud environment. SOURCE_HASH_MATCH=NO means a different export (Drive FULL_HISTORY or batched export) of the same frozen strategy was used.

Frozen Pine sources recovered (no market data): authorities/index6/*.pine.

Code hashes:

|    | file                         | sha256                                                           |
|---:|:-----------------------------|:-----------------------------------------------------------------|
|  0 | src/t46_01_parity.py         | 3ff5438f29fe7b042967320ab119abf43554f9396e01600cf019087e839dc828 |
|  1 | src/t46_02_laneA.py          | 9c37962b5e581e040852c5785b8be95b09ac7d8f1de396588377832169603bd9 |
|  2 | src/t46_03_laneB.py          | 0d9865aa4371a50624104dc343c05fbd3cf53c82319166ea81efab9c48908614 |
|  3 | src/t46_05_gaA.py            | 25f2a61ca2be98a794928f9defb00079d9c5fcf0adae1445d2dade9c78d516ea |
|  4 | src/t46_06_ml.py             | f3a2e5a77c50601acd2d143d6ea4d2a3af6ba514bb39611dad78dbb2c866d947 |
|  5 | src/t46_07_select.py         | ddcb06b1c22f9989ad6622a4293ca633810822e1804bf2371f744236a7f848ed |
|  6 | src/t46_08_freeze_report.py  | c251a56defce599f92f2a29de5d561d1d77159de906a449781cf47bbf8db5fed |
|  7 | src/t46_common.py            | 9e4477ff4c09d3817f8f08896fd00d77c02292e755e2dcd60c21704aa5187a9d |
|  8 | src/t46_quarantine_ingest.py | 002a5c06156826a70ff3359dd4443665687dd6e028d10bf6a476e1a535a2ef8f |
|  9 | src/t46_rebound.py           | e1b55662ea040a4d3609f1eccad340cf7688aeb6cad1f24a90910b97e1b1e342 |
| 10 | src/t46_sanitize_ledgers.py  | 3f773023a4336250c1cfd601735215a3539b765b9acef826a866c59c864a007e |
| 11 | src/t46_seeds.py             | aa56246a7a303e8b10fed7a94fe8c5d1aed3e56a609cfcec6def1bb855294d0f |
| 12 | src/t46_zip_scan.py          | 53ff2c8e4f8ee7060d1dfc7a45d067d6ef18bdd07338f74e6b81558a0f2ab66a |

