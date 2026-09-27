# Legacy Synthesis B — TEST33 through TEST42

Scope: index-futures intraday research (ES/NQ/RTY/YM, intended micro execution MES/MNQ/M2K/MYM) from TEST33, Wave A (TEST34/35/37), TEST39 (via Roadmap V26), EXT-ADX-01 (via Roadmap V26), TEST41 (spec lock) and TEST42 (program).
Written 2026-09-27 for the MES/ES long-only 3m-bar inventory strategy program (Pine v6).

Evidence convention in this file:
- **[SRC]** means the statement or number is taken verbatim or near-verbatim from one of the six source files listed in section 0.
- **[PROPOSED]** means the formula is a causal reconstruction written for reuse here. The sources name the feature but do not give its numeric freeze, so it is not a legacy authority. Where a parameter appears as a symbol (for example `k`, `N`), no value was frozen in the sources, and any value must be pre-registered before PnL.
- **[NOT IN SOURCES]** means the caller's brief refers to a result that these six files do not contain.

---

## 0. Source authorities

Raw text was saved to `/home/user/lab/authorities/legacy/`. The checksums below were also appended to `SHA256SUMS.txt` in that directory. The Google Docs were saved as the natural-language text returned by `read_file_content`, with Drive's markdown escapes (`\#`, `\-`, `\>`) kept. The `.md` file holds the exact decoded bytes from `download_file_content`.

| File (saved as) | Drive ID | sha256 |
|---|---|---|
| TEST33_FINAL_STATUS_AFTER_CHATGPT_V2_2026-09-24.txt | 1Tk325tZfoxe6sxIv-i5eEayp_23PdZ8e7Jt4ty7QEz4 | 01eee871149a4f9433fc87b96a1b60d9426a32d06f9a7f9e3d3dd4edac7828f4 |
| WAVE_A_FINAL_RESEARCH_REVIEW_V1_2026-09-24.md | 1q2M56aubj9ZaTt5cxc2Bpv2tsWrqNA8b | 6da3d714fe4ebaf7f04f40a62e426615cab9faa17cad6e2d4c2929547f01fd8a |
| WAVE_A_TEST34_35_37_PREREGISTRATION_V0_2026-09-24.txt | 1r9ruX9i5q-t3NWe-Z1n0EmT-F5PD6rLTB_t-vr0V3sw | 45971f3736db0e19123d18f0b4018825a18ed60cc30b7645713785b15d8e43b4 |
| RESEARCH_ROADMAP_V26_TEST39_COMPLETE_NEXT_ENTRY_DISCOVERY_2026-09-24.txt | 13pcaUpFyvfOTwQA7cKRosza3ZfLwl0ypss61KumZn_k | b54389b3e3ac33101a7a961b41e13b7b57e00f7076b92d375e64583fc16025be |
| TEST41_RTH_SMALL_BURST_FIRST_PASSAGE_SPEC_LOCK_V1_2026-09-24.txt | 1UpEvt_zMgLmbtO33AdkPlMbge42vN_xCC8CoLa3JIyY | d072b32ff64284796c76d5cc24b86e60907149b932de638e7df0c0ab4e78d5a4 |
| TEST42_MASTER_PROGRAM_FAST_PATH_V1_2026-09-25.txt | 1HvSVmV3WEiFoMChzTUID0HYaT-mNMWFqc8DSqg8Ap7I | 50a3fd0c0a6ada7cc71e64370f32cad8c94754264c276d810a707c04ecd3db75 |

Referenced authorities that were **not** read, because they were outside the brief: SURVIVOR_EXIT_RESPONSE_CURVE_STANDARD_V1 (1ySvN1uUsUyafiA0sPqOdUhZJ8SC9Obqjv44necwWbH4), MTF_EXECUTION_LANES_STANDARD_V1 (1Xu-fzGJ2v7mKXruy4A7U1FQDdTyBX4HNxWYUhSs4voU), TEST39_FINAL_STATUS_AFTER_CHATGPT_V1 (1QdycixLjyw62Zt60uST_ZXK89ObPXmoUdkeYE0FWVFY), SINGLE_NATIVE_TIMEFRAME_RESEARCH_STANDARD_V1 (1l6z8Z9VAheHh-MpMObAQ-d6QnH161M63wThr_fDm_4Y), EXT_ADX_01_CHATGPT_SECOND_PASS_V1 (1sR_Qpa8nEp5Sw6SXM3HX_EqBngA0yIacfHQG9_kI8as), and the Wave A numeric freeze and attribution files (WAVE_A_CONTROL_ATTRIBUTION_V1.md, WAVE_A_TF3_TF5_ATTRIBUTION_V1.md, WAVE_A_PROP_PATH_DIAGNOSTIC_V1.md, WAVE_A_PORTFOLIO_GATE_V1.md).

### Coverage gaps the reader must know
1. **TEST42-A "48/48 reject"** [NOT IN SOURCES]. The TEST42 master program (dated 2026-09-25) shows `TEST42_A = NEXT / EXECUTION_READY`, with no results. The arithmetic is consistent with the claim: 6 TR families × 4 markets × 2 directions = 48 lanes. The verdict itself has to come from a later TEST42-A result document.
2. **TEST41 results** [NOT IN SOURCES]. Only the pre-PnL spec lock was read. There is also a scope discrepancy. The TEST41 V1 lock defines M1 ADX/DI, M2 micro retest→resume, M3 pivot structure break and M4 directional expansion, each × R0/R1. TEST42 (one day later) says TEST41 tested "structural range acceptance/rejection; prior-day / overnight / OR15 / IB60; rolling 3-bar local range (TEST41-B); ADX/DI prove-first (TEST41-A); market-state / second-entry H1/H2-L1/L2". So TEST41 was apparently re-scoped or extended into sub-programs A/B/... after the V1 lock. The authoritative TEST41 result file must be located.
3. **TEST39** is known only through the Roadmap V26 summary.
4. **Wave A exact numeric thresholds** (value-area bin size, energy thresholds, sigma multipliers) are in the Wave A freeze file, which was not read. Section 4 formulas are therefore [PROPOSED] unless marked [SRC].

---

## 1. TEST33 — Event-anchored AVWAP (M1/M3/M6/M7, A1 treatment vs C0 control)

### 1.1 What was tested
- 64 market/candidate lanes on ES/NQ/RTY/YM. Each mechanism has an AVWAP-treatment arm (A1) and a simpler control (C0). The structure is event → anchored VWAP from the event bar → separation from AVWAP → first qualified retest of AVWAP → HOLD confirmation → entry. [SRC]
- Pre-PnL gates all passed [SRC]:
  - canonical data extended append-only through 2026-09-23 with 100% overlap identity;
  - static audit;
  - TradingView compile with 0 errors and 0 warnings;
  - Pine/Python bar/state/signal parity with 0 mismatches;
  - execution probe on all 64 lanes;
  - 8/8 Deep sentinels on identical TV bars;
  - source/PnL authority frozen before PnL.

### 1.2 Verdict [SRC]
- Stage-1: 11 SURVIVOR, 11 BORDERLINE, 42 REJECT. **Strict standalone survivors: 1.**
- The only survivor is **T33-M6-S-A1 / NQ SHORT** (compression release → event AVWAP separation → first qualified retest → HOLD; primary shell; intended execution MNQ). Its evidence:
  - LATEST_1Y: 45 trades, PF 1.96 native, both halves positive.
  - MODERN 2023+: 191 trades; micro 4t net +$3,888.48; PF 1.404; remove-top3 +$1,648.14 (about +$8.8/trade stressed).
  - TV finalist Deep strict gate: +$1,324.92.
  - Weaknesses: PRE_2023 micro 4t −$506.78; 2021 and 2022 negative; 2023 flat to slightly negative; rolling-12m positive only 59.5%. It was the best of 64 lanes on the strict metric, so false-discovery risk is material. The post-freeze extension was +$688 over 16 trades.
- Labels: `EDGE_STRENGTH = THIN / RECENT-BIASED`, `PORTABILITY = MARKET_SPECIFIC_NQ`, `RESEARCH_WATCH / PERSONAL_CANDIDATE`, `LIVE = NO`.
- Mechanism statement: `EVENT_AVWAP_PORTABLE_ALPHA = NO`; `EVENT_AVWAP_MARKET_SPECIFIC_ALPHA = YES` (only NQ M6 SHORT); `FAMILY_LEVEL_PROMOTION = NO`. By mechanism:
  - M1: A1 generally worsened the control.
  - M3: mixed.
  - M6: mixed apart from NQ-S.
  - M7: A1 loses less than C0, but both arms lose on every market.
- Structural exit: reduced MAE, worst day and underwater time, but cut micro 4t net by about $1,469. Only +$179 remained after 4t plus remove-top3. Result: `ATTRIBUTION_ONLY / NOT PREFERRED`.
- Portfolio, Primary (base 3,007 trades / $58,008.61 / PF 1.4663 / MaxDD −$4,739.63), with the candidate added at 1 MNQ:
  - net +$3,492.42 and Sharpe-like +0.0882;
  - PF 1.4663 → 1.4594 and event MaxDD worse by about $139;
  - daily correlation 0.0131 and bottom-5% tail-day overlap 0;
  - bootstrap 95% CI for marginal net about −$848 to +$8,536, which includes zero;
  - classification `MARGINAL_MIXED / DO_NOT_ADD`.
- Portfolio, Secondary (base 3,433 / $191,543.38 / PF 1.4317 / MaxDD −$19,376.60), with the candidate at 2 MNQ: net +$6,984.84, MaxDD better by about $456, PF lower (1.4317 → 1.4291), and candidate PnL negative on base loss days. Classification `DO_NOT_ADD`.
- Prop:
  - The path at 1 MNQ is not weak: p95 MAE about $233 (11.7% of $2,000); worst open DD about $677 (33.8%); 0 rolling starts breached static −$2,000.
  - Cadence is sparse: median gap 5 days, p90 15 days, max 50 days, 70 gaps of 7+ days.
  - Labels: `STANDALONE_PROP_STRATEGY = NOT_SUPPORTED`, `PROP_PORTFOLIO_COMPATIBILITY = WATCH`.

### 1.3 Survived
- Only T33-M6-S-A1 on NQ SHORT, as a watch item. It is irrelevant to a **long-only MES** program: wrong side and wrong market. No LONG and no ES lane survived strict.
- Implementation conventions accepted by the second pass [SRC]. These are reusable (see section 4.1):
  - SAME_BAR_REJECT only;
  - separation may occur on the anchor bar but cannot be the later retest;
  - first qualified retest only;
  - a failed HOLD ends the pending sequence;
  - retest cap at anchor+12 bars, with HOLD allowed on the adjacent following bar;
  - M3 stabilization at anchor+1;
  - the latest same-family/side event replaces the pending anchor;
  - E6 contiguous-session prefix;
  - E3 baseline = previous 20 contiguous completed 5m bars, **same session only**.

### 1.4 Failed — do not reopen as standalone alpha
- Event-AVWAP as a portable family (M1, M3, M7; M6 outside NQ-S).
- AVWAP as an "improvement" layer on M1. It worsened the control.
- M7 in either arm (it loses on all markets).
- Structural exit as a replacement for the primary shell.

---

## 2. Wave A — TEST34 (Dynamic Value Area) + TEST35 (VWAP Excursion Energy) + TEST37 (VWAP Sigma State)

### 2.1 What was tested [SRC]
- Architecture:
  - canonical 1m, deterministically aggregated to 3m/5m/15m;
  - **15m = confirmed state clock only**, with no developing 15m state;
  - execution lanes TF5 (15m state + native 5m setup/entry/exit) and TF3 (15m state + native 3m), with no 3m↔5m dependency;
  - RTH DAY only.
- Frozen scope was 16 IDs × 4 markets = 64 lanes, each with an A1 treatment and a C0 static control, for 128 replayed lanes. The 8 mechanisms were T34-M1 L/S (failed value edge), T34-M2 L/S (value migration), T35-E1 L/S (high-energy pullback) and T37-S2 L/S (outer-band failure), each in TF3 and TF5. T34-M4 was not implemented.
- Bulk replay: 72,345 trades; 12 void signals.
- Exit mix: TIME_120 65,549; SESSION_FLAT 6,358; HALFDAY_FLAT 391; STOP 21; SESSION_END_NO_TERMINAL_BAR 26. The primary shell was therefore effectively a **120-minute time exit** with a rarely hit (catastrophic) stop.
- DATA_END 2026-09-23; post-freeze extension 2026-05-28..2026-09-23 (82 sessions).

### 2.2 Verdict [SRC]
- Stage-1: 8 SURVIVOR, 8 BORDERLINE (5 A, 3 B), 48 REJECT. **1 strict standalone survivor.**
- Only 19/64 lanes were positive in MODERN after micro 4t, and only 4/64 after also removing the top 3 winners. For the other Stage-1 survivors, MODERN 4t remove-top3 ranged from −$3,202 to −$434. Their positive results came from 2025–26; 2023–24 did not carry them.
- Mechanism table (Σ over 8 lanes, micro 4t):

| mechanism | S1 SURV/BORDER | strict | LATEST_1Y | MODERN | PRE_2023 | POST_FREEZE |
|---|---|---|---|---|---|---|
| T34-M1-L failed value edge | 0/1 | 0 | −6,362 | −10,564 | −4,766 | −1,116 |
| T34-M1-S failed value edge | 1/2 | 0 | +368 | −15,528 | −9,926 | +772 |
| T34-M2-L value migration | 0/1 | 0 | −93 | +4,618 | −11,695 | +156 |
| T34-M2-S value migration | 0/0 | 0 | −2,853 | −7,648 | −5,085 | −18 |
| T35-E1-L high-energy pullback | 2/0 | 0 | +1,677 | −3,753 | −16,972 | −1,976 |
| T35-E1-S high-energy pullback | 5/2 | 1 | +11,412 | +2,129 | −7,397 | +5,242 |
| T37-S2-L outer-band failure | 0/0 | 0 | −4,109 | −2,793 | +1,091 | +227 |
| T37-S2-S outer-band failure | 0/2 | 0 | +3,702 | +273 | +808 | +1,159 |

- The strict survivor is **T35-E1-S-A1-TF5 / NQ**:
  - LATEST_1Y: 54 trades, PF 2.48, both halves positive.
  - MODERN 4t: 235 trades, +4,855, PF 1.28; strict rt3 +604 (TV Deep +232).
  - PRE_2023: −1,889.
  - Annual: 2021 −2,248, 2023 −442, 2024 −443, 2025 +2,086, 2026 +3,654.
  - Rolling-12m positive 45.9%; post-freeze +2,671 but rt3 −459.
  - Its TF3 twin (same onsets, entry 2 minutes earlier) **fails** strict at rt3 −3,202.
  - Labels: `MARKET_SPECIFIC (NQ only)`, `THIN / RECENT-BIASED / EXECUTION-CLOCK-SENSITIVE`. On ES and RTY the same ID is Stage-1 but negative on the strict gate.
- Prop path at 1 MNQ: p95 MAE $367 (18% of $2,000 MLL); worst open DD 39%; MODERN MaxDD −2,060; 7/235 rolling starts breached. Result `PROP_PATH_WEAK`.
- Portfolio at Primary: net +4,903 but Sharpe-like −0.119, PF −0.023, MaxDD −584, daily corr 0.30. The candidate loses on base loss days (−1,063). Secondary: Sharpe-like −0.121, MaxDD −1,581. **DO_NOT_ADD on both**, because of risk-adjusted deterioration and same-regime loss overlap.

### 2.3 Survived / flagged [SRC]
- Survivor: T35-E1-S-A1-TF5/NQ, SHORT (again not usable long-only on MES).
- `CONTROL_SURVIVOR_RESEARCH_FLAGS = 3`. These are **controls**, not treatments:
  - `T34-M2-L-C0-TF3/NQ`: strict rt3 +6,608, PRE_2023 −3,135.
  - `T34-M2-L-C0-TF5/NQ`: strict rt3 +5,903, PRE_2023 −2,711.
  - `T35-E1-L-C0-TF3/RTY`: rt3 +37 (marginal).
  - The two NQ controls are "**buy a retest of the latest confirmed 15m VAH from above**". They are the strongest economics in Wave A but are consistent with the 2023+ NQ long regime (pre-2023 negative). **This is the one long-side value-area idea worth re-examining for ES/MES, as a regime-dependent control, not as proven alpha.**
- `15M_STATE_AS_LOSS_FILTER = YES` for M1, M2-S and E1-S. The confirmed 15m states cut losses heavily: A1 keeps 13–63% of control trades. But the filtered result is still not a positive standalone edge, except NQ E1-S TF5. Use the states as **loss filters**, not as alpha sources.

### 2.4 Failed — do not reopen as standalone alpha [SRC]
- `WAVE_A_PORTABLE_ALPHA = NO`; `FAMILY_LEVEL_PROMOTION = NO`.
- T34-M1 failed value edge, L and S (MODERN −10,564 / −15,528).
- T34-M2-S value migration short.
- T35-E1-L high-energy pullback long (PRE_2023 −16,972). This matters for a long-only program: the long high-energy shallow-pullback continuation failed.
- T37-S2 outer-band failure → inner re-entry, L and S (no strict survivor; long MODERN −2,793).
- E1-L and S2-L: the **static controls beat the complex treatments**.
- `TF3_PRECISION_VALUE = NO`. TF3 adds 5–19% more trades and enters 2 minutes earlier, with no consistent MAE, underwater or expectancy benefit. Labels: TF5_BASELINE_PREFERRED 1, BOTH_UNSUPPORTED 31, TF3 preferred 0. **For a 3m program this is a caution: a 3m clock is not an edge by itself.**
- Structural exit: raised net and rt3, but deepened MaxDD and increased breaches 7 → 39. Attribution only.
- Never tested (concept only): TEST35 energy-divergence exhaustion, deep-excursion + elasticity MR/continuation; TEST37 sigma-band walk, sigma expansion → first pullback, deep standardized excursion → reclaim; TEST34 compression release → first edge retest (T34-M4 not implemented), prior-value reclaim. These are **untested**, not failed. They were pruned before PnL.

---

## 3. TEST39, EXT-ADX-01, TEST41, TEST42

### 3.1 TEST39 — RTH_FAST_CAPTURE_EXIT_RESPONSE [SRC via Roadmap V26]
- Tested whether fast-capture or structural hard-TP exits (FAST50/FAST100/STRUCT50/STRUCT75/STRUCT100) rescue native-5m RTH/US-window reversion lanes (48 lanes; TEST32 cohort).
- Verdict:
  - FAST_MFE_HIGH_GIVEBACK is descriptively present in 46/48 lanes, but **early favorable excursion ≠ robust entry edge**.
  - All five exit treatments are `EXIT_TREATMENT_FRAGILE`; `EXIT_TREATMENT_GENERALIZABLE = NONE`.
  - Generic hard-TP optimization is **CLOSED** for the cohort. No portfolio replay.
  - One narrow signal: T32-M3-L-C0/YM/STRUCT50 `NEW_EXIT_VARIANT_RESEARCH_SIGNAL / NARROW_OPTIMUM_RISK / NOT_PROMOTED`. Do not grid around it.
- Failed: rescuing weak entries with exit engineering (TP ladders, fast-capture, structural TPs).

### 3.2 EXT-ADX-01 [SRC via Roadmap V26 and TEST41 §2, §18]
- Source-constrained ADX/DI LONG, wide structural stop, 0.30R TP.
- Status: NQ control and NQ RTH-bull proxy `PROVISIONAL_SURVIVOR_PENDING_NULL`; YM control/proxy `REJECT`.
- TEST41 summary: "ADX/DI event/day selection can contain information, but … wide structural stop … produced only thin modern portfolio value."
- Required next step: one bounded NQ signal-free null to separate ADX event value from generic long exposure plus wide-stop 0.30R mechanics. **Lesson: a long strategy with a wide stop and small R-multiple TP can look positive from long beta alone. Always benchmark it against a signal-free long null.**
- TEST42 lists ADX as "DEFERRED / saturated by EXT-ADX and TEST41-A".

### 3.3 TEST41 — RTH small-burst first-passage [SRC, spec only; results NOT IN SOURCES]
- Question: do causal entries reach a small fixed target before an equal fixed stop more often than a signal-free causal null, after micro friction?
- Design:
  - native 5m only; 4 mechanisms × L/S × R0/R1 × 4 markets = 64 lanes;
  - TP = SL: ES 10 pts, NQ 25, RTY 10, YM 100 (about $50 per micro);
  - 15-minute timeout;
  - signal bars 09:30–14:20, entries 09:35–14:25, none at or after 14:30;
  - one entry per lane per session.
- Reusable mechanism definitions are in section 4.5. The methodology (nulls, gates) is in section 5.
- TEST42 implies TEST41-A (ADX/DI prove-first) and TEST41-B (rolling 3-bar local range acceptance/rejection) were completed. Their verdicts are not in these sources.

### 3.4 TEST42 — Index range auction fast path [SRC, program only]
- TEST42-A clocked trailing range memory: TR(10,30), TR(20,30), TR(30,30), TR(15,60), TR(30,60), TR(60,60). Read as TR(lookback minutes, block minutes): the trailing range of the prior N minutes, frozen at the start of a new 30m or 60m block. This reading is inferred from "how much recent market memory … immediately before a new 30m or 60m auction block". The caller reports **48/48 REJECT** [NOT IN SOURCES]. If confirmed, clocked trailing-range acceptance/rejection is closed as standalone alpha on all index markets and both sides.
- TEST42-B ATR auction ladder: V = mean True Range of the immediately preceding block; levels ±0.50V and ±1.00V from the block open (0.382V/0.618V only as neighbor controls). Status CONCEPT_READY.
- TEST42-C developing RTH range quartiles: `L_q = RTH_Low_prev + q·(RTH_High_prev − RTH_Low_prev)`, q ∈ {0.25, 0.50, 0.75}, using the high/low of **completed prior bars** of today's RTH. Status CONCEPT_READY.
- Deferred: BR2/4/8 micro ranges (a near-neighbor of TEST41-B), Bollinger, Triple Stochastic, multi-range confluence, and TEST42-D auction-regime transition.
- Common taxonomy and bracket: see section 4.6.

---

## 4. Reusable feature definitions (causal formulas)

General causality rules [SRC-derived]:
- Signals use completed bars only.
- Entry is at the next bar open.
- Higher-timeframe state is used only after that bar is confirmed.
- No `request.security` and no `request.security_lower_tf` in the Pine strategy (TEST41/TEST42/Roadmap V26 single-native-TF standard).
- Rolling baselines must declare `SAME_SESSION` or `CROSS_SESSION` [SRC, TEST33 lesson].

Notation: bar index `t` on the native execution clock (3m for the target program). `tp_t = (H_t+L_t+C_t)/3` is typical price. `V_t` is volume. `s0` is the first bar of the RTH session. All sums run over completed bars `s0..t`.

### 4.1 Session VWAP, event-anchored VWAP, separation, first qualified retest
- Session VWAP [PROPOSED standard]: `VWAP_t = Σ_{i=s0..t} tp_i·V_i / Σ V_i`. In Pine v6 use `ta.vwap(hlc3, timeframe.change("D"))` or a manual RTH-anchored accumulator. For a 09:30 RTH anchor on ETH-inclusive data, reset on the first bar with `time >= 09:30 ET`. `ta.vwap` with the default session reset anchors at the ETH start (18:00 ET), which **differs from RTH VWAP**.
- Event-anchored VWAP (AVWAP) [PROPOSED; structure SRC]: at event bar `a` (for example a compression-release bar), `AVWAP_t = Σ_{i=a..t} tp_i·V_i / Σ_{i=a..t} V_i`. Anchoring on the event bar itself is causal only if the event is known at the close of `a`. The AVWAP value at `a` includes bar `a`.
- Separation [PROPOSED]: `sep_t = (C_t − AVWAP_t)/D_t`, where `D_t` is a causal scale (for example ATR on completed bars, or the section 4.3 sigma). Qualify when `sep_t ≥ k_sep` for a LONG anchor (short mirror). The separation threshold was not in the sources.
- First qualified retest [SRC rules]:
  - After separation, the first bar `r > a` whose range touches AVWAP (long: `L_r ≤ AVWAP_r`, or within a tolerance band) and which is not the separation bar.
  - Cap: `r ≤ a+12` bars.
  - HOLD: the retest bar closes on the trend side (long: `C_r > AVWAP_r`), or the HOLD occurs on the **adjacent following bar** `r+1`.
  - A failed HOLD ends the sequence (no second retest).
  - SAME_BAR_REJECT: a bar that both separates and retests is rejected.
  - A newer same-family/side event replaces the pending anchor.
- Repaint and lookahead: none if computed on the close with next-open entry. Risk: using `high/low` of the current bar to "touch" and then entering on the same bar's close is allowed only if the signal is evaluated at bar close (Pine default `calc_on_every_tick=false`; do not use `process_orders_on_close` unless the backtest intends a close fill).

### 4.2 Dynamic value area and value migration (TEST34)
- Developing volume profile [PROPOSED]:
  - Bin completed-bar volume by price with tick-multiple bin width `b`.
  - For a bar without intrabar data, distribute `V_i` uniformly across bins spanned by `[L_i, H_i]`, or assign it to the `tp_i` bin (declare which).
  - POC = the bin with maximum volume. **Tie rule [SRC]: keep the existing POC when it ties the maximum.**
  - Value area = expand from the POC, adding the larger adjacent bin (by volume) until cumulative volume ≥ 70% of total (70% is the conventional value, not a source number). VAH and VAL are the outer bin edges.
- Confirmed 15m publication [SRC architecture]: VAH/VAL/POC are evaluated on completed 15m bucket closes and held constant until the next 15m close. On a 3m chart, compute on 3m bars and **publish only when `(minute_of_session+3) % 15 == 0` after bar close**, using the value at that instant. Doing this natively avoids `request.security` and its repaint risk.
- Onset window [SRC]: an event is eligible only in the next 15m bucket after its state publication.
- Value width: `W_t = (VAH − VAL)/ATR_ref`. Compression is `W_t` below a trailing same-session reference; expansion is the opposite.
- Value migration [PROPOSED]: `mig_t = POC_pub(k) − POC_pub(k−1)` (or the VA midpoint) between consecutive confirmed publications. Upward migration = `VAL_k > VAL_{k−1}` and `VAH_k > VAH_{k−1}` (non-overlap or majority shift).
- Prior-value re-entry / acceptance: price closes back inside the prior published `[VAL, VAH]` after being outside (re-entry). Acceptance is N consecutive closes outside.
- Legacy surviving control shape [SRC]: **buy a retest of the latest confirmed 15m VAH from above** (T34-M2-L-C0, NQ only, pre-2023 negative).
- Pine-safety: profile arrays grow over the session. Cap the bin count and use `array` or `map`, reset at s0. Bin assignment must use only completed bars.

### 4.3 VWAP sigma state (TEST37)
- Causal volume-weighted dispersion [PROPOSED standard]: `σ_t = sqrt( Σ V_i·tp_i² / Σ V_i − VWAP_t² )` over `s0..t`. Guard `max(·,0)` for numerical noise. Pine v6 `ta.vwap(src, anchor, stdev_mult)` returns `[vwap, upper, lower]` using this definition.
- Standardized location: `z_t = (C_t − VWAP_t)/σ_t`. Undefined while `σ_t = 0` (first bar). Require a minimum bar count after s0.
- Bands: `VWAP ± m·σ` with multipliers `m` to be pre-registered (sources give none).
- Sigma-band dwell: `dwell_m,t` = consecutive completed bars with `z ≥ m` (or `z ≤ −m`), or the fraction of the last N bars in that zone.
- Sigma-width compression/expansion: `σ_t/σ_{t−N}` or `σ_t/ATR_ref`. Note that session σ is cumulative and dominated by early-session volume, so it moves slowly late in the day; declare this.
- VWAP slope: `slope_t = (VWAP_t − VWAP_{t−N})/(N·ATR_ref)`.
- Standardized-distance divergence [PROPOSED]: price makes a new session high (`H_t > max H_{s0..t−1}`) while `z_t < z` at the prior session-high bar. That is bearish divergence; mirror for bullish.
- Band walk: `≥ n` consecutive closes with `z ≥ m_outer`, or with each low above `VWAP + m_inner·σ`.
- Outer-band failure → inner re-entry (T37-S2) [PROPOSED]: bar `f` with `H_f ≥ VWAP+m_out·σ` and `C_f < VWAP+m_out·σ`, then a close back inside `VWAP+m_in·σ` within N bars → fade (short). The mirror gives a long. **Tested in Wave A and failed as standalone (section 2.4).**
- Deep standardized excursion → reclaim: `min z over the last N ≤ −m_deep`, then a close back above `VWAP − m_in·σ`. Untested.

### 4.4 VWAP excursion energy, memory and elasticity (TEST35) [all PROPOSED; family names SRC]
Define the excursion start `e` as the most recent bar where `sign(C−VWAP)` changed. `d_i = (C_i − VWAP_i)/σ_i` or `/ATR_ref` (declare which).
- Excursion duration: `Dur_t = t − e + 1`, in bars on the same side.
- Integrated normalized distance: `IND_t = Σ_{i=e..t} |d_i|`.
- Signed energy: `E_t = Σ_{i=e..t} d_i`, which equals `sign·IND` within one excursion. Over a trailing window N crossing sides, it is `Σ d_i`.
- Volume-weighted energy: `EV_t = Σ d_i·V_i / mean(V over same-session reference)`.
- Max displacement: `MD_t = max_{i∈[e,t]} |d_i|`.
- Extension efficiency: `EE_t = |C_t − C_{e−1}| / Σ_{i=e..t} |C_i − C_{i−1}|` (Kaufman ER restricted to the excursion).
- Recovery elasticity: after `MD` is reached at bar `m`, `Elast_t = (MD − |d_t|)/(t − m)`, the speed of return toward VWAP. The fraction retraced is `(MD − |d_t|)/MD`.
- Adverse velocity: `AV_t = (|d_{t−k}| − |d_t|)/k`, the speed of the move back against the excursion over the last k bars.
- Path smoothness: `1 − (Σ|ΔC| − |ΣΔC|)/Σ|ΔC|` over the excursion, or `std(ΔC)/|mean ΔC|` (lower = smoother).
- High-energy shallow pullback (T35-E1) setup concept: high `IND` or `E`, then a pullback that retraces a small fraction of `MD` without crossing VWAP, then resume. **E1-L failed. E1-S survived only on NQ TF5, thin.**
- Pine-safety: all quantities are running accumulators reset at the side-change bar and at s0. There is no lookahead if `e` is detected on a closed bar. Normalizing by the session σ has the early-session instability noted in section 4.3.

### 4.5 Price-action entry primitives (TEST41) [SRC exact]
- **Custom ADX/DI** (EXT-ADX source math, length 14, threshold 25, **no `ta.dmi` substitution**). The exact custom smoothing is in the EXT-ADX source, which was not read here. The standard Wilder form for reference [PROPOSED]:
  - `+DM = up>down and up>0 ? up : 0`, where `up = H−H[1]` and `down = L[1]−L`; `−DM` mirrors it.
  - `TR = max(H−L, |H−C[1]|, |L−C[1]|)`.
  - Smooth each with RMA(14): `DI± = 100·RMA(±DM)/RMA(TR)`.
  - `DX = 100·|DI+−DI−|/(DI+ + DI−)`; `ADX = RMA(DX,14)`.
  - LONG confirm: `crossover(DI+, DI−) and ADX>25`. Or pending on the cross while `ADX≤25`, cancelled if `DI+≤DI−`, confirmed when ADX crosses from ≤25 to >25 while `DI+>DI−`. The signal is the confirmation bar close. SHORT is the exact inverse.
- **Micro impulse → shallow retest → prove-first resume** (signal bar t), LONG:
  - `C[t−2]>O[t−2] and C[t−2]>max(H[t−5],H[t−4],H[t−3])`
  - `C[t−1]<O[t−1] and L[t−1] >= (H[t−2]+L[t−2])/2`
  - `C[t]>O[t] and C[t]>H[t−1]`
  - SHORT is the exact inverse. No ER/VWAP/ATR/MA/RVOL.
- **Confirmed 3-bar pivot structure transition**:
  - Pivot high at j is confirmed after j+1 closes: `H[j]>H[j−1] and H[j]>=H[j+1]`. Pivot low: `L[j]<L[j−1] and L[j]<=L[j+1]`.
  - Keep the last two confirmed pivot highs and lows.
  - LONG: `PH1<PH2 and PL1<PL2` (bearish structure), with the current bar bullish and `C ≥ PH1 + 1 tick`. SHORT is the inverse.
  - Pivots are never relabeled. In Pine, `ta.pivothigh(1,1)` returns the value on bar j+1 for pivot j. Note that `ta.pivothigh` uses strict `>` on both sides, which differs from this `>=` on the right. **Implement manually.**
- **Directional expansion bar**:
  - `range=H−L>0`, `body=|C−O|`.
  - LONG: `C>O`, `range > max(range[1..3])`, `body/range ≥ 2/3`, `(C−L)/range ≥ 0.75`, `C > max(H[1..3])`.
  - SHORT: inverse, with `(C−L)/range ≤ 0.25` and `C < min(L[1..3])`.
- **R1 prior-session momentum**: C1 and C2 are the terminal closes of the last two valid completed RTH sessions (not calendar days). LONG requires `C1>C2`; equality or a missing value means no trade. Build it natively from the same stream, not from a daily request.

### 4.6 Range-auction primitives (TEST42) [SRC exact]
- Accepted High: `C > RangeHigh` → LONG. Accepted Low: `C < RangeLow` → SHORT.
- Failed High: `H > RangeHigh and C < RangeHigh` → SHORT. Failed Low: `L < RangeLow and C > RangeLow` → LONG.
- A bar touching both edges is MIX: no trade, range retired. A touch alone is descriptive.
- First classified event only per range instance.
- Bracket:
  - failed-high short SL = sweep high + 1 tick; failed-low long SL = sweep low − 1 tick;
  - accepted-high long SL = RangeHigh − 1 tick; accepted-low short SL = RangeLow + 1 tick;
  - the stop must be adverse to the next-open entry, otherwise no trade;
  - TP = 0.67R quantized away from entry; no trail, BE, partials or scale-in.
- Session: hard-flat at 15:45 ET; last normal entry 15:40.

---

## 5. Methodology lessons to reuse

### 5.1 Pipeline and governance [SRC]
1. Freeze the spec, then compute non-PnL density/overlap/collision, prune, freeze numerics, and hash, **before** any PnL. The TEST33 and Wave A authority freezes were time-stamped before the first economic number.
2. Pre-PnL QA gates:
   - canonical 1m append-only with overlap identity;
   - deterministic aggregation;
   - Pine compile with 0 errors and 0 warnings;
   - Pine vs Python signal parity with **0 mismatches** on identical bars;
   - next-open entry clock parity;
   - pivot no-lookahead tests;
   - synthetic same-minute TP+SL = adverse-first test;
   - half-day, missing-bar and roll fail-closed tests;
   - first-signal-per-day campaign parity;
   - predeclared TV Deep sentinels.
3. Python/canonical replay is the economic authority. TradingView Deep is for sentinels and finalists only, not bulk. TEST42 relaxes this for first-pass screening ("fast path": Pine → TV execution on 4 markets → review). Only promising families then get Python parity, nulls, remove-top, PRE/2023+, neighbor, OOS/WF and the portfolio gate.
4. Implementation readings documented before PnL are kept even if ambiguous. Never change them post hoc (TEST33 E3 same-session case).
5. Parallel isolation: a wave must not inspect another running test's PnL when selecting candidates.
6. No portfolio membership or live change without user approval. Each test ends with explicit `PORTFOLIO_MEMBERSHIP_CHANGED` and `LIVE_AUTHORIZATION` flags.

### 5.2 Cost and friction conventions [SRC]
- Micro RT fee $1.22 (TEST21 authority) for MES, MNQ, M2K and MYM. Tick values: MES $1.25 (0.25 pt, $5/pt); MNQ $0.50 ($2/pt); M2K $0.50 (0.10 pt, $5/pt); MYM $0.50 (1 pt, $0.50/pt).
- BASE = 1 tick adverse per fill + fee. **4T stress = 4 ticks adverse per fill + fee.** No positive slippage. Target gaps get no improvement; stop gaps fill at the worse 1m open.
- Barriers are defined from the frictionless `entry_ref`. Costs do not move the barriers.
- Report gross and net; never judge on gross.

### 5.3 Stress and rejection criteria [SRC]
- Strict gate as used in TEST33/Wave A: micro 4t with **remove-top3 winners** (rt3) positive in MODERN (2023+), plus a positive LATEST_1Y with both halves positive. Also report PRE_2023, annual results, rolling-12m positive share and the post-freeze extension.
- TEST41 strict survivor gate:
  - ≥100 full-history trades and ≥50 trades in 2023+;
  - 4T net > 0 in full history, PRE_2023 and 2023+;
  - 2023+ 4T remove-top3 > 0;
  - both nulls separate.
  - Positive economics with too few trades is labelled `SPARSE_RESEARCH_SIGNAL`. An R1-only survivor is labelled `REGIME_CONDITIONAL`.
- Signal-free causal nulls: 500 seeded permutations per family (seed 410924), with plans hashed before null economics. Fail closed, no redraw.
  - DATE_SHUFFLE keeps market, direction, regime and year and moves the event to other eligible same-year dates at the same clock.
  - CLOCK_SHUFFLE keeps the date and moves the event among the lane's same-year clocks.
  - SEPARATES = full-history 4T percentile ≥95, 2023+ 4T percentile ≥90, and 2023+ TP-first rate percentile ≥90.
  - DATE pass with CLOCK fail = `DAY_OR_REGIME_SELECTION_ONLY`, which is not promotable.
- A long strategy must beat a signal-free long-exposure null (EXT-ADX lesson). Long beta in 2023+ index futures inflates long results. The strongest Wave A economics (NQ VAH-retest long controls) coincide with the 2023+ NQ long regime and are negative pre-2023.
- Multiple comparisons: a best-of-64 survivor is flagged for false-discovery risk. Both TEST33 and Wave A produced exactly one thin, recent-biased, single-market survivor out of 64. This is roughly what chance plus regime drift would produce.
- Controls: every complex treatment carries a simpler control (raw event, raw touch, raw state). A treatment is not "distinct" merely because it trades less. In Wave A the controls often beat the treatments.
- Execution-clock sensitivity: check the TF3 vs TF5 twin, same onsets with a different clock. If the survivor dies on the neighboring clock, label it `EXECUTION-CLOCK-SENSITIVE`.
- Exit governance:
  - Exits cannot rescue weak entries (TEST39).
  - Structural exits stay attribution-only unless they beat the primary shell after 4t+rt3.
  - Post-survivor TP response curve only: BASE / +0.50…+2.00 ATR_PREV in 0.25 steps, computed in Python, never used to reopen discovery or rescue promotion.
  - TEST42 q = 0.50/0.75/1.00 replay is allowed only after entry evidence exists.
- Portfolio gate (incremental, exact base reproduction first): judge Sharpe-like, PF, MaxDD delta, loss-day behavior, tail-day overlap, daily correlation, bootstrap CI of marginal net, and root concentration. A positive marginal net with a CI that includes zero, or a candidate that loses on base loss days, means DO_NOT_ADD.
- Prop: separate path quality (p95 MAE, worst open DD versus a $2,000 MLL, rolling-start breaches) from cadence (gap distribution). Sparse cadence rejects **standalone** prop use only, not use as a sleeve.

### 5.4 Session and window conventions [SRC]
- RTH research session 09:30–15:45 ET with the published half-day calendar. TEST41 entries run 09:35–14:25. TEST42 last entry is 15:40, with hard-flat at 15:45.
- Roll-excluded sessions do not feed ATR. Analysis windows start ≥60 sessions after the data start.
- **Portfolio gap:** Main entries strictly after 14:30 ET = 0. Late-RTH or closing-auction behavior is a confirmed structural gap (not alpha). Future late-RTH work must use genuinely late mechanisms (failed late continuation, closing acceleration, late inventory unwind, session-extreme rejection/acceptance, close-location), **not re-timed morning VWAP/OR setups**.

---

## 6. Implications for the MES/ES long-only 3m inventory strategy
1. None of the strict survivors from TEST33 or Wave A is an ES long: both are NQ SHORT. There is no legacy ES-long VWAP/AVWAP/value/sigma/energy edge to inherit.
2. Do not reopen as standalone long alpha:
   - event-AVWAP retest families;
   - failed-value-edge;
   - high-energy shallow-pullback long (T35-E1-L);
   - outer-band-failure long (T37-S2-L);
   - exit/TP rescue of weak entries;
   - clocked trailing-range memory (TEST42-A, if the 48/48 reject is confirmed);
   - ADX/DI as an edge by itself (saturated).
3. Reuse as **loss filters or state features**, not as signals: the confirmed 15m value/energy/sigma states, which cut control losses heavily. A 3m program must publish 15m state only at confirmed bucket closes.
4. Candidate long idea to re-test honestly: the retest of the latest confirmed VAH from above (a control shape). It needs a signal-free long null, the PRE_2023 check and the 4t+rt3 gate.
5. A 3m clock has no demonstrated precision value over 5m (Wave A). Any 3m design must show it survives on the neighboring clock.
