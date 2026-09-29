# P9 RELAXED_RESEARCH_FRONTIER_V1 — portfolio enumeration — preregistration (alone)

Inputs: frozen Main daily series + STITCHED outer trade lists (2021-01-01..2026-05-27) of P7 STRESS_PASS modules and their P8
MANAGEMENT_IMPROVEMENT variants (no full-sample backtests):
- TRAPPED mechanism slot (C1 / C2 / C4 share one mechanism -> at most ONE option): {none, C1, C1+WINNER_PYRAMID, C2, C2+WINNER_PYRAMID}.
- C7 slot: {none, C7, C7+FRESH_RECOVERY}.   (C4, C5, C6 failed P7 stress; C3, C8 had no Tier-B arm -> excluded.)
- Integer lots per selected option: {1, 2} (conservative bound).  -> 1 + 4x2 = 9 trapped options x 1 + 2x2 = 5 C7 options = 45 portfolios (EXHAUSTIVE).
Integrated deterministic allocator: all module trades (and add units, which exist only if their base unit filled) are processed chronologically
with shared capacity: Main occupancy has absolute priority; a candidate order of `lots` micros is skipped if at any minute of its holding interval
Main + open candidate micros + lots would exceed MNQ 6 / MES 8 / MYM 4 / M2K 4.  Base cost; SLIP4 recomputed identically.
Metrics per portfolio: avg/day, 2021+ (= whole window), SLIP4 avg/day, MaxDD, worst day, ret/DD, daily Sharpe, corr Main, pairwise module corr,
loss-day Jaccard vs Main, bottom-5% overlap, active overlap, peak MES / MNQ / MYM / M2K (Main + candidates), approximate margin (P7 APPROX
per-micro margins + Main at its peak), turnover, 2022 P&L, 2022 matched-beta excess (P6 control), year contributions, top-3 day removal,
AVG_DAY_PER_$10K_MAXDD and RISK_NORMALIZED_INCREMENT (= its value minus Main's).
Frontiers (report only): FRONTIER_A highest avg/day with MaxDD <= 1.10 x Main and worst >= -$5,000; FRONTIER_B best ret/DD; FRONTIER_C lowest
MaxDD among portfolios with positive increment; FRONTIER_D highest avg/day under the frozen production capacity (all 45 are capacity-valid by
construction; D additionally requires worst >= -$5,000).  Each frontier is also labelled with the ROUTE (A / B / C, P7 definitions) it satisfies
vs Main; a frontier satisfying no route is REPORT_ONLY_NOT_IMPROVED.  Pareto set over (avg/day max, ret/DD max, MaxDD min, worst max) reported.
Increments are decomposed as ALPHA (base units, lots 1), POSITION MANAGEMENT (add units), and LEVERAGE (lots 2 - lots 1); none is called alpha
if it comes only from lots.  GAP_TO_600 = 600 - best relaxed frontier avg/day (whole-sample Main avg 143.21 + frontier increment on the stitched
window is also shown).  Main is never modified; PORTFOLIO_MEMBERSHIP_CHANGED = NO.
