# AUTONOMOUS_ALPHA_RESEARCH_MASTER_PROGRAM_V1 (INDEX ONLY) — preregistration

Committed ALONE before any program economics.  Base: 0143116 (TEST98 closed) + bookkeeping a90ada1 (TEST98 ledger schema repair).
Research data <= 2026-05-27 only.  T61 forward OOS (begins 2026-09-29) is NOT opened, inspected or used.  NEW_OOS_OPENED = NO.
LIVE_AUTHORIZATION = NO.  CURRENT MAIN = MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 — never modified by this program.
Also filed as AUTONOMOUS_ALPHA_RESEARCH_MASTER_PROGRAM_V1_PREREGISTRATION.md (identical content).

## 1. Scope
- Markets: ES, NQ, YM, RTY signals; micro economics MES / MNQ / MYM / M2K.  Cross-asset (GC/CL/FX/rates/crypto) NOT used, also not as features.
- Long only.  Legal execution window 09:30-16:15 ET; decisions on completed information; fills at next legal open (no buy-stops, no intrabar
  breakout fills); 1m paths for barrier / MFE / MAE ordering.  Overnight holding allowed only as a frozen position after the final legal execution.
- Main benchmark (reproduced at program start, 2019-07-01..2026-05-27, 1741 sessions): avg/day 143.207, 2021+ 151.78, MaxDD 13,936,
  worst day -4,666, ret/DD 0.010276.  Capacity: T61 priority; T61 + basket MNQ <= 6, MES <= 8.  No double counting; NQ and MNQ not independent.

## 2. Frontier and target
- INDEX_RESEARCH_FRONTIER_V1 (report only) starts as CURRENT_LOCKED_MAIN; only PORTFOLIO_ADDITIVE_HISTORICAL_SURVIVORs may be added (report-only,
  SELECTION_EXPOSED = YES).  Every candidate is reported against Main and against the frontier.
- $600/day is NOT an optimisation target.  Tracked: CURRENT_FRONTIER_AVG_DAY, GAP_TO_600 = 600 - frontier avg (start 456.79).

## 3. Common event-study protocol (ESP-1, applies to every test unless its own prereg states otherwise)
- Engine: TEST97 5m event engine (chained RTH 5m bars, b = 0..80, completed at 09:34 + 5b; entry = open of bar b+1), extended by the program
  engine with horizon h24 (120 min) and HTF aggregation (TEST99 Phase 0).  Common population: signal bar b <= 67 (h24 reported where complete).
- Outcomes: mean / median / P(>0) of forward return in ATR_d units at 5-120 min, 16:00, 16:15; net of micro round-trip cost (cost_atr);
  MFE/MAE 60m, time-to-MFE, new-high, underwater at 16:15, time-to-recover, barrier races +-0.25/0.5/1.0 ATR_d (engine path statistics).
- Nulls: A = time/year/causal-vol/bull-day matched generic long; B = family-specific magnitude/state matched (defined per test; tercile/decile
  edges CAUSAL: per instrument, recomputed monthly from sessions strictly before the month, 120-session warm-up excluded; fallback shares reported);
  C = simple momentum (close > prior 4-bar high); D = same-exposure beta (strategy phase).
- Inference: date-clustered bootstrap (instruments on the same date form one cluster), 2,000 reps, seed 7.  Positive years counted over 2019..2026.
- Classification of an event variant (pooled, family null B, at a primary horizon):
  * EVENT_CLUE: mean excess > 0 with CI lower > 0, >= 5/8 positive years, same sign in >= 3/4 instruments, gross mean > cost_atr.
  * STRONG_CLUE: EVENT_CLUE AND NULL C excess > 0 AND 2021+ excess > 0 AND adjacent consistency (adjacent TF / adjacent preregistered parameter
    has the same sign and >= 50% of the magnitude).  Isolated cells are rejected (never STRONG).
  * WEAK_RESEARCH_CLUE_ONLY: mean excess > 0, >= 5/8 years, CI includes 0.   REJECT otherwise.
  * The expected number of chance CI passes (0.025 x tests) is reported with every test.
- Response curves before thresholds: continuous state features are reported by causal quintile bins; no threshold search.
- 2022 (adverse regime) fields: absolute, matched-long excess, matched-beta excess, loss capture, MaxDD, worst day, exposure, peak, recovery.

## 4. Strategy phase (requires its own later prereg commit; only for a STRONG_CLUE)
- Entry open of b+1 (1 micro per signal instrument), exit at the clue's primary horizon, optional preregistered stop; Main occupancy / capacity.
- Mandatory stresses: SLIP4, +1 bar delay, 20% deterministic missed entries (every 5th signal skipped), chronological folds (>= 4/5 positive),
  remove-top-3, plateau (preregistered neighbours >= 60% of base), sample (>= 200 trades, >= 25 per fold), 2022 fields.
- STANDARD route: standalone pass AND >= +$10/day (and >= +$10 in 2021+) AND Main+module ret/DD >= Main AND MaxDD <= 1.10 x Main AND worst >= -5000.
- DIVERSIFIER route: standalone pass AND >= +$3/day AND |corr to Main| <= 0.30 AND ret/DD >= 1.05 x Main AND MaxDD <= 1.05 x Main AND worst >= -5000.
- ML only if >= 600 events, >= 150 pre-first-fold, coherent heterogeneity, family null survives, economic reason; Ridge / logistic TRADE-SKIP /
  optional HistGB; <= 12 configs per family; OOS net $ objective; chronological expanding folds; own prereg.
- GA last resort: >= 3 independent coherent dimensions and real OOS economics; <= 600 genomes/family, <= 2,400 global; nested chronology.

## 5. Sequence (each test: PREREG commit alone -> implement -> run -> audit -> RESULT commit -> classify -> freeze -> MASTER_STATE update)
TEST99 HTF momentum scaling (Phase 0 5m-aggregation parity with frozen TEST97 arrays; HTF1 strong bull bar, HTF2 2h rolling-high breakout,
HTF3 two consecutive bullish upper-half bars; 15/30/60m; null = same cumulative displacement / range / TOD) ->
TEST100 VWAP trend-side state (V1 acceptance, V2 walk, V3 first hold) -> TEST101 event-anchored VWAP -> TEST102 Saty ATR phase / EMA ribbon ->
TEST103 complex pullback / second entry -> TEST104 level interaction factory (PDH/PDL, PWH/PWL, ORH/ORL, causal 60m swings, 2h extremes; L1-L5) ->
TEST105 level-failure deep branch (only if TEST104 finds a coherent failure; else NOT_RUN_BY_RULE) -> TEST106 Fisher ACD (vs ORB) ->
TEST107 response speed / time-to-MFE (survivors or strong clues only) -> TEST108 range budget veto -> TEST109 ICT mini-lane (<= 12 defs) ->
TEST110 bounded recovery inventory (positive validated base only) -> TEST111 survivor-only overnight -> TEST112 portfolio risk overlay
(reduce-only) -> TEST113 mechanism-specific cross-index synchrony (conditional) -> TEST114 academic close momentum -> TEST115 HTF trend-strength /
stage factory -> TEST116 DeMark-style temporal exhaustion (low priority; NOVELTY_DELTA_VS_TEST46_47 or NOT RUN) -> TEST117 final synthesis
(deterministic sequential capacity allocator, Main priority, frontier, GAP_TO_600, MAIN_DD_NORMALIZED_AVG_DAY, scaling frontier report-only).
Optional reserve: <= 3 families with a NOVELTY_MEMO, <= 20 definitions each.  Budget pressure order: TEST114 > TEST115 > TEST116.
Conditional tests (TEST105, 107, 110, 111, 113) are NOT_RUN_BY_RULE when their precondition fails.

## 6. Budget
<= 400 new deterministic definitions (~<= 40 per family phase), <= 60 ML configs, <= 2,400 GA genomes.  Distinct hypotheses, ledger rows,
ML configs and GA genomes are counted separately (instruments / pooled rows / horizons are not hypotheses).

## 7. Stop conditions
A core complete; B saturated; C $600 reached with a production-valid frontier and all core families first-passed; D data / causality / integrity
blocker; E budget exhausted.  If the index universe saturates first -> INDEX_TARGET_600_NOT_REACHED.

## 8. Labels
SURVIVOR, PORTFOLIO_ADDITIVE_SURVIVOR, MARKET_SPECIFIC_SURVIVOR, HISTORICAL_SURVIVOR_SELECTION_EXPOSED, STRONG_CLUE, WEAK_RESEARCH_CLUE_ONLY,
FORWARD_CLUE_ONLY, RESEARCH_ONLY_APPROX, SELECTION_BIASED, PARITY_BLOCKED, DATA_BLOCKED, IMPLEMENTATION_BLOCKED, REJECT, SATURATED_FAMILY,
NOT_RUN_BY_RULE (+ EVENT_CLUE, RESEARCH_DUPLICATE, NOT_RUN_BY_DUPLICATION).  Every new historical survivor: HISTORICAL_SELECTION_EXPOSED = YES.

## 9. Forbidden
Changing gates; neighbour search; unlogged trials; deleting losers; treating correlated indices as independent; post-cutoff data; opening OOS;
next-bar features; daily H/L before completion; eventual swings; buy-stop fills; coarse-bar stop ordering; adding because price is cheaper
(except the DCA control); unlimited DCA; unbounded no-stop; overnight rescue; silently changing Main; double counting; cross-asset.

## 10. Source attribution
Each family is tagged SOURCE_SUPPORTED_PRINCIPLE / SYSTEMATIC_FORMALIZATION / OUR_NEW_HYPOTHESIS with Tier 1 (peer-reviewed / primary author
book) to Tier 3 (practitioner media) sources: Brooks, Hougaard, Crabel, Dennis/Turtle, Raschke, Grimes, PATs/Mack, Trader Dante, Nick Shawn
(no DCA attribution), Saty Mahajan, Shannon AVWAP, Fisher ACD, Wyckoff, Sperandeo 2B, ICT (low priority), Gao-Han-Li-Zhou, Moskowitz-Ooi-Pedersen,
Weinstein, Wilder, DeMark.

## 11. Final report fields (§38)
CURRENT_OFFICIAL_MAIN, MAIN metrics, INDEX_RESEARCH_FRONTIER members / metrics, GAP_TO_600, TARGET_600_REACHED, INDEX_RESEARCH_SATURATED,
per-test classification, survivors, clues, saturated families, cumulative hypotheses / ledger rows / ML configs / GA genomes,
CROSS_ASSET_RESEARCH_OPENED = NO, PORTFOLIO_MEMBERSHIP_CHANGED = NO, NEW_OOS_OPENED = NO, LIVE_AUTHORIZATION = NO.
