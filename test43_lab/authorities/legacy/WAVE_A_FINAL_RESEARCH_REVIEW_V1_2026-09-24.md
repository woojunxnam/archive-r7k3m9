# Wave A Final Research Review V1 — TEST34 + TEST35 + TEST37

Date: 2026-09-24 (ET) · Claude Code (execution engineer / independent auditor). Claude does not classify for promotion;
the ChatGPT second pass owns classification.

## 1. Pipeline status

- **Pipeline order.** canonical 1m → deterministic 3m/5m/15m → Pine/Python MTF parity → execution probe → source freeze
  → 8 predeclared Deep sentinels → canonical/Python bulk → Stage-1/stress → C0 attribution → TF3/TF5 attribution →
  Prop Path → exact portfolio gates. All steps are complete.
- **Pre-PnL gates.** Every gate passed before PnL was opened. The source/PnL authority freeze was written at 12:06 ET,
  before any economic number was computed.
- **Scope.** Exactly the 16 frozen IDs × ES/NQ/RTY/YM = 64 lanes. T34-M4 was not implemented. No cross-candidate
  suppression was applied. Deep ran only for the 8 sentinels, 8 same-data twins and 1 post-selection finalist.
- **Data.** DATA_END = 2026-09-23. POST_FREEZE_RECENT_EXTENSION = 2026-05-28..2026-09-23 (82 sessions).
- **Bulk replay.** 72,345 trades across 128 lanes (64 A1 + 64 C0). 12 signals were void (missing or partial next native
  bar). Exit mix: TIME_120 65,549 · SESSION_FLAT 6,358 · HALFDAY_FLAT 391 · STOP 21 · SESSION_END_NO_TERMINAL_BAR 26
  (canonical sessions with a missing terminal bar).

## 2. Result

64 primary lanes → Stage-1: **8 SURVIVOR · 8 BORDERLINE (5 A, 3 B) · 48 REJECT → 1 strict standalone survivor.**

| mechanism (8 lanes each) | Stage-1 SURV / BORDER | strict | Σ LATEST_1Y 4t | Σ MODERN 4t | Σ PRE_2023 4t | Σ POST_FREEZE 4t |
|---|---|---:|---:|---:|---:|---:|
| T34-M1-L failed value edge | 0 / 1 | 0 | −6,362 | −10,564 | −4,766 | −1,116 |
| T34-M1-S failed value edge | 1 / 2 | 0 | +368 | −15,528 | −9,926 | +772 |
| T34-M2-L value migration | 0 / 1 | 0 | −93 | +4,618 | −11,695 | +156 |
| T34-M2-S value migration | 0 / 0 | 0 | −2,853 | −7,648 | −5,085 | −18 |
| T35-E1-L high-energy pullback | 2 / 0 | 0 | +1,677 | −3,753 | −16,972 | −1,976 |
| **T35-E1-S high-energy pullback** | **5 / 2** | **1** | +11,412 | +2,129 | −7,397 | +5,242 |
| T37-S2-L outer-band failure | 0 / 0 | 0 | −4,109 | −2,793 | +1,091 | +227 |
| T37-S2-S outer-band failure | 0 / 2 | 0 | +3,702 | +273 | +808 | +1,159 |

- Only 19 of 64 lanes are positive in MODERN after micro 4t. Only 4 of 64 stay positive after also removing the top 3
  winners.
- The Stage-1 survivors are spread across markets (2 per market). Lane split: TF5 6, TF3 2.
- Every Stage-1 survivor except one fails the strict gate. Their MODERN micro-4t remove-top3 ranges from −3,202 to −434.
  The 2025–26 latest year carries them; 2023–24 does not.

**The only strict survivor: `T35-E1-S-A1-TF5 / NQ`.**

| item | value |
|---|---|
| LATEST_1Y | 54 trades, PF 2.48, both halves positive |
| MODERN micro 4t | 235 trades, +4,855, PF 1.28 |
| strict rt3 | **+604** (TradingView finalist Deep: +232) |
| PRE_2023 | −1,889 |
| annual | 2021 −2,248 · 2023 −442 · 2024 −443 · 2025 +2,086 · 2026 +3,654 |
| rolling 12m positive | 45.9% of windows |
| post-freeze extension | +2,671, but rt3 −459 |

- It is the best of 64 lanes on the strict metric, so multiple-comparison risk is material.
- Its TF3 twin (same onsets, entry 2 minutes earlier) fails the strict gate at rt3 −3,202.

Labels:
- PORTABILITY = MARKET_SPECIFIC (NQ only). On ES/RTY the same ID is a Stage-1 SURVIVOR but its strict value is negative.
- EDGE_STRENGTH = THIN / RECENT-BIASED / EXECUTION-CLOCK-SENSITIVE.

## 3. Attribution

- **A1 vs static control** (`WAVE_A_CONTROL_ATTRIBUTION_V1.md`):
  - M1, M2-S and E1-S: the 15m states work as **loss filters**. The controls lose heavily, and A1 keeps 13–63% of
    their trades. Apart from NQ E1-S TF5, the filtered result is still not a positive standalone edge.
  - E1-L and S2-L: the static controls beat the treatments.
  - Most A1 trades are shifted entries (the control's first signal of the session comes earlier), so these are not
    pure same-bar filters. For S2, A1 and C0 windows are disjoint by construction.
- **CONTROL_SURVIVOR_RESEARCH_FLAGS = 3.** These are flagged, not promoted:
  - `T34-M2-L-C0-TF3/NQ`: strict rt3 +6,608. PRE_2023 −3,135.
  - `T34-M2-L-C0-TF5/NQ`: strict rt3 +5,903. PRE_2023 −2,711.
  - `T35-E1-L-C0-TF3/RTY`: strict rt3 +37, so marginal.

  The two NQ controls (buy a retest of the latest confirmed 15m VAH from above) are the strongest economics in Wave A,
  consistent with the 2023+ NQ long regime.
- **TF5 vs TF3** (`WAVE_A_TF3_TF5_ATTRIBUTION_V1.md`):
  - TF3 adds 5–19% more trades.
  - It enters 2 minutes earlier on shared windows.
  - It shows no consistent MAE, underwater or expectancy benefit.
  - Labels: TF5_BASELINE_PREFERRED 1 (NQ E1-S), BOTH_UNSUPPORTED 31. TF3 precision preferred 0; execution-resolution
    sensitive 0.

## 4. Survivor path and portfolio

- **Prop path** (`WAVE_A_PROP_PATH_DIAGNOSTIC_V1.md`, 1 MNQ):
  - p95 MAE $367 (18% of the $2,000 MLL); worst open DD 39%; worst day 35%.
  - MODERN MaxDD −2,060, so 7 of 235 rolling starts breach a static −$2,000.
  - Result: **PROP_PATH_WEAK**. Firm simulations were not run.
  - The preregistered structural exit raised net and rt3 and cut MAE and the worst day, but deepened MaxDD and breaches
    (7 → 39). It stays attribution only.
- **Exact portfolio gate** (`WAVE_A_PORTFOLIO_GATE_V1.md`). Bases reproduced exactly.
  - Primary: net +4,903, but Sharpe-like −0.119, PF −0.023 and MaxDD −584. Daily correlation 0.30. The candidate loses on
    base loss days (−1,063) and in the base MaxDD episode (−584).
  - Secondary: Sharpe-like −0.121, MaxDD −1,581.
  - **DO_NOT_ADD on both.** The reason is the risk-adjusted deterioration and the same-regime loss overlap, not NQ
    concentration.

## 5. Mechanism statement (for ChatGPT)

```
WAVE_A_PORTABLE_ALPHA = NO
WAVE_A_MARKET_SPECIFIC_ALPHA = T35-E1-S-A1-TF5 / NQ only (thin, recent-biased, clock-sensitive)
15M_STATE_AS_LOSS_FILTER = YES for M1 / M2-S / E1-S; NOT an edge by itself
TF3_PRECISION_VALUE = NO
CONTROL_SURVIVOR_RESEARCH_FLAGS = 3 (NQ M2-L C0 both lanes strong but pre-2023 negative; RTY E1-L C0 TF3 marginal)
FAMILY_LEVEL_PROMOTION = NO
```

## 6. Implementation readings the second pass may want to review

These are documented in the freeze (§2):

- POC is retained when the existing POC ties the maximum.
- The onset window is the next 15m bucket only.
- A void next-bar entry still consumes the session latch.
- E1/S2/M1/M2 controls use the latest confirmed state on every publication. The S2 control's windows are disjoint from
  A1's.
- Roll-excluded sessions do not feed ATR.
- No extra 60-session warm-up is applied; every analysis window starts at least 60 sessions after the data start.

END
