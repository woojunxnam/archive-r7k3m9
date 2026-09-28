# Track A — forward shadow harness (C43-CORE / T55 / T61-R1C_ATOMIC_CAP6)

* `frozen/t61_r1c/` — immutable package (source import closure, artifacts, freeze v3, `T61_R1C_MANIFEST.json`, `T61_R1C_HASH_INDEX.csv`,
  `verify_frozen.py`).  Every run verifies all hashes (frozen copies **and** the live `src/` / `out/` originals) and fails closed.
* `forward_shadow.py forward --es <1m ES parquet> --mnq <1m MNQ parquet> --through YYYY-MM-DD` — after each session close.  Canonical format:
  END-stamped, America/New_York, 1-minute bars (same schema as `data/canonical_1m_*.parquet`).  Writes only sessions >= **2026-09-29**
  to `out/forward_shadow/through_<date>/`: `daily_report.csv`, `session_log_<PORTFOLIO>.csv.gz`, `run_summary.json`, `RUN_MANIFEST.json`.
* Engine = byte-identical frozen code run in a throw-away workspace; state is continuous (2026-05-28 .. 2026-09-28 is engine warm-up only,
  never written or looked at); TEST53 genomes after 2026-05-27 = `FINAL_ALL_TO_2026-05-27` rank 0.
* `qa_shadow.py` — research-data-only QA: exact reproduction of the frozen history, prefix (causality) invariance, forward-fold code path,
  tamper → fail closed.  Result: `out/forward_shadow_qa/FORWARD_SHADOW_QA.json`.
* `promotion_check.py <daily_report.csv>` — report-only forward gate status.  No auto-promotion; LIVE_AUTHORIZATION = NO; no order code.
