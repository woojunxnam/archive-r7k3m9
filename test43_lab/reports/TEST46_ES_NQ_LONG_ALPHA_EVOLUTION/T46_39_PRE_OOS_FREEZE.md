# T46_39 Pre-OOS freeze

sha256 **e0724e207aea45c16416207379a540e4e44550434eeaefb4440911732dd334ce**

```json
{
 "program": "TEST46 ES/NQ long alpha evolution + structural rebound discovery",
 "research_data_end": "2026-05-27",
 "TEST44_45_OOS_START": "2026-05-28",
 "TEST46_ORIGINAL_OOS_PARTIALLY_EXPOSED": "YES (8 LC03 legacy-ledger trades 2026-05-28..2026-08-27 viewed)",
 "TEST46_QUARANTINED_INTERVAL": "2026-05-28 .. 2026-09-27 (never used for any TEST46 decision)",
 "TEST46_NEW_OOS_START": "2026-09-28",
 "new_oos_start_condition": "valid because no market data dated 2026-09-28 or later has been accessed by the lab before this freeze",
 "FINAL_TEST46_CHALLENGER": "NONE",
 "authorities_verified_unchanged": {
  "out/t44/freeze/TEST44_PRE_OOS_FREEZE.json": "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4",
  "out/t44/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json": "2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236",
  "out/t45/freeze/TEST45_PRE_OOS_FREEZE.json": "185d1ef91ddffe494ce5826a5142af31644a4816bb2a4db72d110909ed1c2987",
  "out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json": "76941f63465306928e535df74641a29b172c9420c9e0a69852a4f1b0ed5356da"
 },
 "legacy_ledger_recovery": {
  "source": "Google Drive FULL_HISTORY / batched TradingView exports ingested without display into an out-of-repo quarantine; authority-hash evidence files (PROPFIRM_PORTFOLIO_V1 evidence) not reachable from this environment",
  "sanitizer_report": [
   {
    "SOURCE": "LC02.csv",
    "SOURCE_HASH_MATCH": "NO",
    "SANITIZED_FILE": "LC02_TO_20260527.csv",
    "SANITIZED_SHA256": "218f898c7e6e77e5c20d0ab71d3a1711ffd03f6dfefd356682ab087874f28dda",
    "HISTORICAL_ROW_COUNT": 363,
    "MAX_RETAINED_ENTRY_DATE": "2026-05-14",
    "MAX_RETAINED_EXIT_DATE": "2026-05-14",
    "CUTOFF_COMPLIANCE": "PASS"
   },
   {
    "SOURCE": "LC03.csv",
    "SOURCE_HASH_MATCH": "NO",
    "SANITIZED_FILE": "LC03_TO_20260527.csv",
    "SANITIZED_SHA256": "b4cbb6339bcaf2c9fa4b48867c12341d197d7707d7511cd1c74cc47eeafa97bf",
    "HISTORICAL_ROW_COUNT": 430,
    "MAX_RETAINED_ENTRY_DATE": "2026-05-20",
    "MAX_RETAINED_EXIT_DATE": "2026-05-20",
    "CUTOFF_COMPLIANCE": "PASS"
   },
   {
    "SOURCE": "LC05.csv",
    "SOURCE_HASH_MATCH": "NO",
    "SANITIZED_FILE": "LC05_TO_20260527.csv",
    "SANITIZED_SHA256": "24243f1481a72c1b059cfcad9691b51c0304f43c8ae0cfddbbe437eed81f09bc",
    "HISTORICAL_ROW_COUNT": 1322,
    "MAX_RETAINED_ENTRY_DATE": "2026-05-26",
    "MAX_RETAINED_EXIT_DATE": "2026-05-26",
    "CUTOFF_COMPLIANCE": "PASS"
   },
   {
    "SOURCE": "T30_W01.csv",
    "SOURCE_HASH_MATCH": "NO",
    "SANITIZED_FILE": "T30_W01_TO_20260527.csv",
    "SANITIZED_SHA256": "048e1e4a86b5dcd18538f93a512c0f6f9fdac1bdc908cbc789dd6ad2703bb2ab",
    "HISTORICAL_ROW_COUNT": 1069,
    "MAX_RETAINED_ENTRY_DATE": "2026-05-21",
    "MAX_RETAINED_EXIT_DATE": "2026-05-21",
    "CUTOFF_COMPLIANCE": "PASS"
   }
  ],
  "sanitized_ledger_sha256": {
   "LC02_TO_20260527.csv": "218f898c7e6e77e5c20d0ab71d3a1711ffd03f6dfefd356682ab087874f28dda",
   "LC03_TO_20260527.csv": "b4cbb6339bcaf2c9fa4b48867c12341d197d7707d7511cd1c74cc47eeafa97bf",
   "LC05_TO_20260527.csv": "24243f1481a72c1b059cfcad9691b51c0304f43c8ae0cfddbbe437eed81f09bc",
   "T30_W01_TO_20260527.csv": "048e1e4a86b5dcd18538f93a512c0f6f9fdac1bdc908cbc789dd6ad2703bb2ab"
  }
 },
 "parity": [
  {
   "seed": "LC02",
   "ledger_entries_window": 176,
   "engine_entries_window": 180,
   "matched": 176,
   "ledger_recall": 1.0,
   "engine_precision": 0.9777777777777777,
   "price_within_1tick_share": 0.9772727272727273,
   "median_abs_price_diff": 0.0,
   "PARITY": "BLOCKED"
  },
  {
   "seed": "LC03",
   "ledger_entries_window": 198,
   "engine_entries_window": 195,
   "matched": 192,
   "ledger_recall": 0.9696969696969697,
   "engine_precision": 0.9846153846153847,
   "price_within_1tick_share": 0.7708333333333334,
   "median_abs_price_diff": 0.25,
   "PARITY": "BLOCKED"
  },
  {
   "seed": "LC05",
   "ledger_entries_window": 602,
   "engine_entries_window": 586,
   "matched": 405,
   "ledger_recall": 0.6727574750830565,
   "engine_precision": 0.6911262798634812,
   "price_within_1tick_share": 0.7308641975308642,
   "median_abs_price_diff": 0.25,
   "PARITY": "BLOCKED"
  }
 ],
 "parity_rule": "predeclared in src/t46_01_parity.py (v1.1 coverage/price-convention amendment before any Lane-A economics)",
 "seed_status": {
  "LC02 ES-VOR": "PARITY_BLOCKED (recall 1.00, precision 0.978 < 0.98)",
  "LC03 NQ-NOON": "PARITY_BLOCKED (recall 0.970)",
  "LC05 NQ-PDH": "PARITY_BLOCKED (0.67: RVOL/VWAP need NQ volume; canonical is MNQ)",
  "TS16-S01 NQ-OI": "PARITY_BLOCKED (no OI data) + LIVE-SAFETY HOLD",
  "TS22-S01 NQ-SNAP": "PARITY_BLOCKED (ledger not retrievable: Drive session failures)",
  "T30-W01 NQ-COMP": "PARITY_BLOCKED (requires YM1!/RTY1! cross-market context; W01 filter not recoverable)"
 },
 "shadow_clues_report_only": [
  "ML-A RIDGE bottom-quality filter over the broad structural-rebound pool (gate: G3,G5 failed)",
  "Lane-A hold extension of LC03 to 16:00 (research-only, seed PARITY_BLOCKED)"
 ],
 "code_sha256": {
  "src/t46_01_parity.py": "3ff5438f29fe7b042967320ab119abf43554f9396e01600cf019087e839dc828",
  "src/t46_02_laneA.py": "9c37962b5e581e040852c5785b8be95b09ac7d8f1de396588377832169603bd9",
  "src/t46_03_laneB.py": "0d9865aa4371a50624104dc343c05fbd3cf53c82319166ea81efab9c48908614",
  "src/t46_05_gaA.py": "25f2a61ca2be98a794928f9defb00079d9c5fcf0adae1445d2dade9c78d516ea",
  "src/t46_06_ml.py": "f3a2e5a77c50601acd2d143d6ea4d2a3af6ba514bb39611dad78dbb2c866d947",
  "src/t46_07_select.py": "ddcb06b1c22f9989ad6622a4293ca633810822e1804bf2371f744236a7f848ed",
  "src/t46_08_freeze_report.py": "c251a56defce599f92f2a29de5d561d1d77159de906a449781cf47bbf8db5fed",
  "src/t46_common.py": "9e4477ff4c09d3817f8f08896fd00d77c02292e755e2dcd60c21704aa5187a9d",
  "src/t46_quarantine_ingest.py": "002a5c06156826a70ff3359dd4443665687dd6e028d10bf6a476e1a535a2ef8f",
  "src/t46_rebound.py": "e1b55662ea040a4d3609f1eccad340cf7688aeb6cad1f24a90910b97e1b1e342",
  "src/t46_sanitize_ledgers.py": "3f773023a4336250c1cfd601735215a3539b765b9acef826a866c59c864a007e",
  "src/t46_seeds.py": "aa56246a7a303e8b10fed7a94fe8c5d1aed3e56a609cfcec6def1bb855294d0f",
  "src/t46_zip_scan.py": "53ff2c8e4f8ee7060d1dfc7a45d067d6ef18bdd07338f74e6b81558a0f2ab66a"
 },
 "new_oos_data_acquired": false,
 "test46_new_oos_opened": false,
 "live_authorization": "NO",
 "portfolio_membership_changed": "NO"
}
```

