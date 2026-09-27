# M15 DEV internal robustness

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


Chronological folds F1 (<=2020), F2 (2021-22), F3 (2023-24), PRE23 vs 2023+ for every row (M04/M05/M01/M03 tables).
Horizon stability (15/30/60/120m), k stability (25/50/100/200), bar-resolution stability (3m vs 5m), timing placebo.

* Mechanism rows: ES 268, MNQ 267, 5m 529. PASS after placebo calibration: ES
  2, MNQ 1 (return); all isolated to one horizon -> UNSTABLE.
* Analog: no configuration positive at >=2 of 4 k with t >= 2; fold signs flip.
* Balance -> lower future range: stable in all folds (volatility information only).

