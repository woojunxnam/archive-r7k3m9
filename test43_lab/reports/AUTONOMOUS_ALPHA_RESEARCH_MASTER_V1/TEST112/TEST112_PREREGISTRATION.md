# TEST112 PORTFOLIO RISK OVERLAY (REDUCE-ONLY) — preregistration

Committed ALONE before any TEST112 economics.  Master prereg 319a7f6.  Attribution: OUR_NEW_HYPOTHESIS.
Rule records in this commit (no economics): TEST110 bounded recovery inventory = NOT_RUN_BY_RULE (no positive validated base);
TEST111 survivor-only overnight extension = NOT_RUN_BY_RULE (no survivor); TEST113 mechanism-specific cross-index synchrony = NOT_RUN_BY_RULE
(no non-duplicate EVENT_CLUE mechanism).
NOVELTY_DELTA vs TEST56 (C43 state maps, DD governor): target is the CURRENT Main (T61-R1C + basket); REDUCE-ONLY; response curves first;
Main's own P&L / drawdown is NOT a state (DD-governor family closed).

States for session d, all computed from ES RTH sessions strictly before d (no intraday information, no cross-asset):
- R1 vol regime = ATR5 / ATR60 of prior daily ranges.
- R2 trend = prior close / SMA50(prior closes) - 1.
- R3 recent drawdown = prior close / max(prior 20 closes) - 1.
3 definitions.  Causal quintiles (edges from sessions strictly before the month, monthly expanding, 120-session warm-up).
Response curve: Main daily P&L (MAIN_GROWTH_V1 daily series, 2019-07-01..2026-05-27) by quintile.  COHERENT iff |Spearman| >= 0.9, the
best-minus-worst quintile day-bootstrap 95% CI (2,000 reps, seed 7) excludes 0, same sign in >= 5/8 years.
Frozen reduce-only rule (one per state, no tuning): if COHERENT and the worst quintile's mean Main P&L < 0, Main is HALVED on days in that
quintile (approximation: daily P&L x 0.5 -> RESEARCH_ONLY_APPROX because T61 carries positions across sessions).
OVERLAY_VALUE iff: ret/DD >= 1.05 x Main AND MaxDD <= Main AND worst day >= Main worst AND the halved days' Main mean < 0 in >= 4 of 5
chronological folds (2019-20, 2021, 2022, 2023-24, 2025-26).  Report-only: Main is never modified.
