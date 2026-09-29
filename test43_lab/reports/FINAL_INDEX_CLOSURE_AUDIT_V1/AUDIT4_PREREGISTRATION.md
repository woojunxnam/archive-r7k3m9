# AUDIT 4 — C2 winner press vs same-base frontload (preregistration, alone)

Base: frozen C2 take-all trades (stitched window 2021-01-01..2026-05-27, 590 trades, entry FP[5b+5], exit engine 16:15).  Winner ADD1 = the frozen
PH7 / PH9 rule: first completed checkpoint with >= 30 min left, close > entry, not an independent-event bar, fill at next open, exit 16:15.
FRONTLOAD ADD1 = a second identical unit at the original entry.  No new signals, thresholds, ADD3 or tuning.
4A PURE TIMING (no capacity): per base opportunity, marginal = WINNER_ADD1 $ (0 if no winner checkpoint) - FRONTLOAD_ADD1 $; base and SLIP4;
date-clustered CI; $/day; folds O1-O5; years; instruments; C2-module (2-unit) MaxDD / worst day / worst trade / basket MAE for both variants.
4B CAPACITY (Main priority, MNQ 6 / MES 8 / MYM 4 / M2K 4, integrated allocator of the reclamation P9): A MAIN + C2x1; B1 MAIN + C2x2 FRONTLOAD as
two separate units (unit 2 fills only if unit 1 filled; partial fills allowed); B2 MAIN + C2x2 all-or-none (the earlier PH9 lots = 2 variant);
C MAIN + C2 + WINNER_ADD1.  Report base trades filled / skipped, second units filled / blocked, peaks, PnL lost to capacity (= uncapped - capped for
each variant), combined avg/day / MaxDD / worst / ret/DD.
Decomposition: TOTAL = (C - B1) capped; PURE_TIMING = (C - B1) uncapped (= 4A total); CAPACITY_EFFECT = TOTAL - PURE_TIMING (interaction included;
both counterfactuals reported).
4C classes (frozen): let T = 4A marginal $/day, K = CAPACITY_EFFECT $/day, TOT = T + K.
- NO_VALUE: C - A (winner press vs single) <= 0 in the capped portfolio.
- SIMPLE_EXPOSURE_SCALING: TOT <= 0 (winner press not better than frontloading) or combined ret/DD(C) <= ret/DD(B1).
- TRUE_MANAGEMENT_TIMING_VALUE: T > 0, T SLIP4 > 0, >= 3/5 folds of T positive, and T >= 75% of TOT.
- CAPACITY_TIMING_VALUE: TOT > 0 and T <= 25% of TOT (or T <= 0).
- MIXED_TIMING_AND_CAPACITY_VALUE: otherwise with TOT > 0.
Also compared on risk: combined ret/DD and MaxDD of A / B1 / B2 / C.  Any class is MANAGEMENT / EXPOSURE TIMING, never entry alpha.
