# AUDIT 5 — D7 frozen practical portfolio-carrier check (preregistration, alone)

D7 = exact PH3 definition (breakout of the nearest known non-ORH resistance -> failure back below within 6 bars -> reclaim within 6 bars ->
close above the max high since the break), take-all, entry FP[5b+5], exit engine 16:15 (PH4 exit dataset X1615 prices), 1 micro, no filter.
Stitched window 2021-01-01..2026-05-27.  Stresses: base, SLIP4, +1 bar delay, missed 20%, remove-top3, folds O1-O5, 2022, capacity (Main priority,
integrated allocator), turnover, MaxDD, worst day.  MAIN + D7: standalone and combined metrics, corr Main, loss-day Jaccard, D7 mean on Main's
bottom-5% days, peaks / approximate margin.  D7_PRACTICAL_CARRIER_PASS only if ROUTE B (small diversifier; label BETA / STRUCTURE CARRIER) or
ROUTE C passes; ROUTE A may not label it alpha (magnitude-null evidence absent).  Otherwise D7_PRACTICAL_CARRIER_FAIL.  No optimisation.
Affected portfolio comparisons (report only, integrated allocator): MAIN + {C2x1, C2 + WINNER_ADD1} x {without, with D7}, MAIN + D7.
