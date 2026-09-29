# TEST117 FINAL INDEX PORTFOLIO SYNTHESIS — preregistration

Committed ALONE before the synthesis run.  Master prereg 319a7f6.  Report-only; Main is never modified.
- Candidate set = every PORTFOLIO_ADDITIVE_HISTORICAL_SURVIVOR from TEST99-TEST116 and RESERVE_R1 (MASTER_SURVIVOR_LIBRARY.csv).
  Clues (STRONG / EVENT / WEAK / RESEARCH_DUPLICATE) are NOT candidates.
- Deterministic sequential capacity allocator: Main first (T61 priority, basket), then candidates in the order they were classified, each
  admitted only if it passes the STANDARD or DIVERSIFIER route against the CURRENT frontier and fits the residual capacity (T61 + basket +
  candidates MNQ <= 6, MES <= 8); no re-optimisation of any candidate.
- Outputs: frontier members and metrics (avg/day, 2021+ avg/day, MaxDD, worst day, ret/DD), CURRENT_FRONTIER_AVG_DAY, GAP_TO_600 = 600 - avg,
  MAIN_DD_NORMALIZED_AVG_DAY = avg/day per $10,000 of MaxDD, and a report-only linear scaling frontier k x frontier for k in {1, 1.5, 2, 3, 4,
  k_600} with MaxDD / worst scaled by k (labelled SCALING_REPORT_ONLY: exceeds the preregistered capacity caps for k > 1; not a recommendation).
- If the frontier is unchanged and the core sequence is complete -> INDEX_TARGET_600_NOT_REACHED; stop condition A/B.
