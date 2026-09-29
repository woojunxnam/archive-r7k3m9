# INDEX_ML_GA_RECLAMATION_PROGRAM_V1 — program preregistration

Committed ALONE before any program economics.  Base head be5e15f (MASTER program complete).  Branch claude/test43-mes-optimization-lab-olvn9b.
Data: canonical 1m ES/NQ/YM/RTY (SHA256 2b4f41b1 / e6298965 / edde4419 / 7539af44 verified at program start), research cutoff 2026-05-27.
T61 forward OOS (2026-09-29+) not opened / inspected / used.  NEW_OOS_OPENED = NO.  LIVE_AUTHORIZATION = NO.  INDEX ONLY; cross-asset CLOSED.
Official Main = MAIN_GROWTH_V1 (T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1), never modified.  $600/day is reported (GAP_TO_600), never optimised.
Every accepted item carries HISTORICAL_SELECTION_EXPOSED = YES and RELAXED_GATE_SELECTION_EXPOSED = YES; nothing joins Main.

## Phases (each: PREREG commit alone -> push -> execute -> RESULT commit -> push)
P0A TEST114_AUDIT_CORRECTION_1 (exact-clock GHLZ target).  P0B common-engine audit.  P1 CANDIDATE_BANK_V1 + frozen feature dictionary.
P3 nested walk-forward ML.  P4 event-conditioned HTF regime.  P5 structural GA / exhaustive search.  P6 ML+GA consensus.  P7 strategy stress.
P8 bounded recovery / winner pyramid.  P9 relaxed portfolio frontier (exhaustive enumeration first).  Final index saturation decision.
Phase-specific details (feature list, horizons, configs, genome spaces) are frozen in each phase prereg; the rules below bind all phases.

## Evidence tiers (prospective; never applied retroactively to call old candidates survivors)
- TIER A (ML/GA exploration entry): preregistered event definition; no known defect; >= 500 usable events (or a coherent grouped family >= 500);
  plausible causal features; point-estimate family-null excess > 0; >= 5/8 positive years OR repeated same-direction evidence across related
  preregistered mechanisms; >= 3/4 indices same direction OR documented market-specific structure; gross mean at the frozen horizon >= ~cost
  (>= 0.9 x round-trip cost).  CI lower > 0 NOT required.
- TIER B (ML_ECONOMIC_CANDIDATE / GA pass), on STITCHED_HISTORICAL_OUTER_OOS (2021-01-01..2026-05-27): net avg/day > 0, SLIP4 avg/day > 0,
  >= 3/5 outer folds positive, remove-top3 total > 0, no catastrophic fold (worst fold avg/day >= -2 x |stitched avg/day|), >= 150 selected
  trades, selection coverage >= 10% of the population, causal features only.  Config choice for the pass test is NESTED (chosen inside each
  outer training window by inner validation); the best-of-configs stitched result is reported but marked SELECTION_EXPOSED_BEST_OF_N.
- TIER C routes (Main+candidate on the stitched window 2021-01-01..2026-05-27, Main measured on the same window):
  C1/ROUTE A CORE ALPHA: incremental >= +$5/day (>= +$10 = stronger status), standalone and SLIP4 > 0, ret/DD >= Main, MaxDD <= 1.10 x Main, worst >= -$5k.
  C2/ROUTE B SMALL DIVERSIFIER: incremental >= +$1.5/day, standalone and SLIP4 > 0, |corr Main| <= 0.35, ret/DD >= 1.02 x Main,
  MaxDD <= 1.03 x Main (or improves), worst day not worse by > $250, capacity valid.
  C3/ROUTE C RISK REDUCER: incremental >= -$0.5/day, MaxDD or bottom-5% loss improves >= 5%, ret/DD improves, worst day not worse by > $250,
  no short exposure (program is long-only).

## Outer folds (expanding): O1 train <= 2020 / test 2021; O2 <= 2021 / 2022; O3 <= 2022 / 2023; O4 <= 2023 / 2024; O5 <= 2024 / 2025-01-01..2026-05-27.
Inner validation: the last calendar year of each training window (train-inner = earlier years).  All scaling / imputation / hyperparameters /
thresholds / selection fractions / genomes chosen inside training only.  Stitched outer = concatenation of outer-test results only.

## Budgets (caps, not targets): <= 12 ML configs per family, <= 80 global; <= 1,250 genomes per family, <= 8,000 global (exhaustive
enumeration whenever the structural space fits the cap).  Portfolio: exhaustive enumeration when tractable.

## Integrity (never relaxed)
Data cutoff; causal features at decision time; next-legal-open entries; realistic micro costs (MES 1.87, MNQ/MYM/M2K 1.12 $/side) and SLIP4
(0.62 + 4 ticks); no double counting; every config / genome logged; 1m ordering for barriers; no eventual highs/lows or future swings; no
uncontrolled DCA (max 2 units, ADD1 only, ADD1 marginal EV <= 0 -> stop); capacity MNQ <= 6 and MES <= 8 including Main occupancy (MYM <= 4,
M2K <= 4 program caps); remove-top-winners; no OOS opening.  Recovery logic is OUR_NEW_HYPOTHESIS (not attributed to any author).

## Overfit diagnostics: Deflated Sharpe Ratio (Bailey & Lopez de Prado, using the number and variance of trials), PBO via CSCV (16 blocks),
White Reality Check (stationary bootstrap of the max mean over the trial set); any not reliably computable -> OVERFIT_DIAGNOSTIC_NOT_COMPUTED.

## Final decision: INDEX_FULLY_SATURATED = YES only under all conditions of program section 42; cross-asset is never opened here.
