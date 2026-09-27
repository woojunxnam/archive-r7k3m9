# C_SOXL — Legacy SOXL inventory strategy: exact mechanism record and transfer map to MES 3m

Status: legacy-authority extraction. Nothing here is new research. Every formula, threshold and transition is quoted from one of the three sources below. Where the sources disagree, or where a detail is left unspecified, this document says so rather than filling the gap.

## 0. Sources and precedence

| Tag | Source | Local raw copy (`/home/user/lab/authorities/legacy/`) | SHA256 |
|---|---|---|---|
| [PINE] | `SOXL 5m V18 2X FRICTION FINAL BACKUP 20260918.pine` (Drive 1FDw2cEiWVPMFi6rmze5BDwHXsxWLherZ), 2355 lines, Pine v6 | `SOXL_5m_V18_2X_FRICTION_FINAL_BACKUP_20260918.pine.txt` | 2b1a3b595ec6053cb918446b6c34e1f0b477adbb5992c05a68c55fa6ee681db1 |
| [HANDOFF] | `SOXL_V1_STRATEGY_MECHANISM_AND_PINESCRIPT_PORTABILITY_HANDOFF_20260916` (Doc 1ktH6q1j…) | `SOXL_V1_STRATEGY_MECHANISM_AND_PINESCRIPT_PORTABILITY_HANDOFF_20260916.txt` | 54ef552f4b30b9ec44de6debf714cd000eb1f3109b74e0262afbe228932c5980 |
| [ROADMAP] | `SOXL_TQQQ_RESEARCH_AND_AUTOTRADER_ROADMAP_20260913` (Doc 11ls9uXx…) | `SOXL_TQQQ_RESEARCH_AND_AUTOTRADER_ROADMAP_20260913.txt` | 6fd9e71a69ca0488fbce8de5733660d32ae75c4f37e65829c05df5b470971268 |

Hashes are also listed in `SOXL_SOURCES.sha256` in that directory. The two Docs were exported as text/plain, so the Doc hashes cover that export and are not a hash of a Drive binary.

How the sources relate:
- [HANDOFF] describes the **Python production champion, SOXL V1 = C0 CORE + G0/E1 MINI**, on a 1m base clock. MATH-A is excluded (KEEP_SUPPORTED_NOT_PROMOTED).
- [PINE] is a **later, native-5m research strategy (V18)**. It contains C0 and G0/E1, but adds several things: a VWAP layer, progressive C0 admission, a trend sleeve, a "smart core" long-horizon sleeve, and defense governors. **In the frozen V18 configuration the MINI is disabled**: `V17_ABLATION_MODE = "NO_MINI"`, so `allowMini = false`. The file describes itself as "Production candidate under stress: SMA_STACK Smart Core + C0 + Trend. MINI is disabled after V17 ablation." The MINI code is still present and fully specified, so it is documented below.
- Where [PINE] and [HANDOFF] differ, this document takes the numbers from [PINE] (the task asks for the Pine) and marks the difference.

---

## 1. Architecture: sticky CORE plus tactical sleeves

[PINE] runs four sleeves inside one virtual cash ledger. The ledger starts at `ACCOUNT_START = 140000`.

| Sleeve | Role | Capital authority | Lots / slots | Tracked arrays |
|---|---|---|---|---|
| **Smart Core** ("bull core", V12 to V17) | Sticky long-horizon exposure (the "CORE") | `BULL_CORE_MAX_BUDGET = 60000`, as 3 tranches of $20,000 (BASE, MID, TOP) | 3 | `bullCoreQtyA/EntryA/CostA/TvIdA` |
| **C0** | Mean-reversion inventory grid (tactical) | `SHARED_BUDGET = 80000`, unit = 80000/6 | 6 | `coreQtyA/EntryA/CostA/DayA/TvIdA/PendingIdA` |
| **Trend** (V5 "TREND_CLUSTER") | Winner-pyramiding offense (tactical) | `TREND_BUDGET = 30000`, 3 slots (10,000 each), inside the $80k shared cap | 3 | `trendQtyA/EntryA/CostA/TvIdA` |
| **MINI** (G0/E1) | Short-horizon bottom/rebound campaign (tactical) | `MINI_BUDGET = 10000`, N3 → 10000/3 per entry, inside the $80k shared cap; `MINI_RISK = 250` | 3 | `miniQtyA/EntryA/CostA/TvIdA` |

The Pine comment explains the separation: "This capital is separate from the $80k tactical shared authority but still shares the same account cash. BULL60 can therefore use the otherwise idle ~$60k and bring maximum planned gross capital toward $140k."

The separation shows up in two places in the code:
- **Shared-cap checks** (C0 buy admission, C0 cap reduction, trend admission, mini admission and mini CAP exit) sum only `core + mini + trend` quantity times `close` against `SHARED_BUDGET`. **Smart-core quantity is excluded.**
- **Cash checks** include smart core. Every sleeve's admission test contains `+ bullCoreReservedNext <= cash`, so smart-core entries planned for the next open reserve cash ahead of the tactical sleeves.

Pyramiding is set to `15` ("6 C0 + 3 MINI + 3 TREND + 3 SMART CORE"). Each logical lot gets a unique TradingView entry ID: `C0_<seq>_S<slot>`, `M<armId>_<slot>`, `TR_<seq>_S<slot>`, or `BULL_BASE/MID/TOP`. Exits target a specific ID through `strategy.close(id)` or `strategy.exit(from_entry=id)`.

### 1.1 How the core is protected

The **Smart Core** is the sticky exposure. It is evaluated only once per session, on the first RTH bar (`isRth and newSession`), and fills at the next bar's open. Its protections are:
1. **Secular-bear zero.** In the frozen mode, `SOXX_TIERED_RS_ZERO_BEAR_SMA_STACK`, all three tranches go to zero when `soxxSecularBearSmaStack` is true (see §8).
2. **Drawdown protection.** When the V8/V9 epoch-drawdown protection is active (`v8RiskLevel >= 3`, i.e. 15% epoch DD), the MID and TOP overlays are disallowed (`riskOverlayAllowed` becomes false). BASE is **not** removed by drawdown protection. It depends only on `not zeroBearActive`.
3. The smart core is **not** subject to the shared $80k cap reductions, the C0 timeout, or the mini/trend exits.

The **C0 tactical core** in [HANDOFF] terms is protected by the 10-session timeout, the shared-cap reduction (highest-cost lot first), progressive admission, the 65m decline-acceleration veto, the timeout-cluster governor, and the DD15 start-only block.

---

## 2. Clocks, sessions and causality ([PINE])

- The chart must be **5m RTH standard candles** (`is5m`, `RTH = "0930-1600:23456"`, `TZ = "America/New_York"`). `sessMin = minuteOfDay - 570`, so it is 0 at 09:30.
- "Alpha clock = native completed 5m bars. Market entries fill next 5m Open. C0 limits rest for the next 5m bar." Settings: `process_orders_on_close=false`, `calc_on_every_tick=false`, `use_bar_magnifier=true`.
- **Daily authority** is built causally from the 5m bars. When the session changes, the previous session is finalized. It counts as complete only if `dayCount == 78` (a full day) or `dayCount == 42 and dayLastSessMin == 205` (a 13:00 early close). An incomplete session pushes `na`, which breaks the rolling-five readiness on purpose.
  - `TR_d = max(H-L, |H-prevC|, |L-prevC|)`, where `prevC = priorDailyClose`.
  - `atr5Daily = mean(last 5 dailyTR)`. It is `na` if any of the five is `na`.
  - **`g = atr5Daily / 5`**. This is the C0 grid step.
  - `structuralDiscount = (H+L+C)/3 - 0.25*(H-L)` of the prior complete session.
  - Daily EMA20 and EMA50 of the prior complete session's close use a Python-style EMA: recursive, seeded from the first finite value, with output only after n observations.
- **65m context** is built from 13 native 5m bars aligned to 09:30. Buckets are `floor(sessMin/65)`. The bucket closes on the bar with `sessMin % 65 == 60` and counts as complete only if `n65 == 13`.
- **HTF external data**: SOXX and QQQ daily values come from `request.security(..., "1D", expr[1], lookahead_on)`, which is the prior completed day and non-repainting.
- **Helpers**: `f_rma_step` gives an SMA seed after n contiguous finite values, and a gap resets it. Prices are rounded to cents: `f_round_down = floor(x*100)/100` and `f_round_up = ceil(x*100)/100`.

[HANDOFF] notes the same logic on a 1m base clock, with 5m features from completed 5m aggregates and "65m context available only after that 65m bar completes". It also warns that "If TradingView's exact RTH 65m segmentation differs from the Python scheduler, parity will fail."

---

## 3. Logical lot / slot accounting

**C0 (6 slots, k = 0..5)**, tracked per lot:
- `coreQtyA[k]`: shares. `> 0` means occupied.
- `coreEntryA[k]`: fill price. This drives **highest-cost** selection.
- `coreCostA[k]`: entry fee. It is reduced pro-rata on partial sells: `ec = oldCost*qk/oldQ`.
- `coreDayA[k]`: `sessionId` at fill. This drives the **10-session timeout**.
- `coreTvIdA[k]`: the owning TradingView entry ID. `corePendingIdA[k]` is the working-order ID.
- Working-order state for the next bar: `workCoreBuyActive/Px/Q[k]`, `workCoreSellSlot/Target/Q`, `workCoreMktExit[k]` plus a reason.
- Helper functions: `f_core_count` (occupied slots), `f_core_qty`, `f_core_highest_cost_slot` (argmax entry among occupied slots), `f_core_lowest_entry`, `f_core_free_slot`, `f_core_avg`.
- Campaign-level C0 state: `anchor`, `sellRef`, `c0CampaignArmed`, `c0UnlockedSlots`.

**MINI (3 slots)**, tracked per lot: qty, entry, cost and TV ID. Campaign-level state: `miniActive`, `miniState` (NONE / ARMED / BUILDING / DERISK), `miniArmId`, `miniEntryCount`, `miniDipCount`, `miniRecoveryCount`, `miniOriginalATR`, `miniFirstPrice`, `miniLastPrice`, `miniLastEntryTime`, `miniDeadline`, `miniTrough`, `miniRearmLevel`, `miniVWAPExitStage`, `miniRealized`, `miniSoftDone`, `miniRiskFlag`, and `miniReductionStarted`.

**Trend (3 slots)**, tracked per lot: qty, entry, cost and ID. Sleeve-level state: `trendLastPrice`, `trendLastEntryBar`, `trendLastExitBar`, `trendHighWater`, `trendStop`, `trendTrailArmed`.

**Smart core (3 tranches)**: qty, entry, cost and ID (`BULL_BASE/MID/TOP`).

**Emulator reconciliation.** The virtual ledger "mirrors the frozen Python OHLC economics and drives logical lot selection". Stale C0 order IDs are cancelled after one bar. An **orphan cleanup** calls `strategy.close(oid)` on any TradingView open trade whose ID is not owned by a tracked lot and has survived more than `ORPHAN_GRACE_BARS = 2` bars. `tvMismatch = |strategy.position_size - virtualQty| > 0.5` is raised as a dashboard flag and an alert.

[HANDOFF] invariants for MINI: the first entry counts as one lifetime economic entry, and partial-fill fragments do not create new economic entry IDs.

---

## 4. Per-bar processing order (state machine skeleton, [PINE])

For each RTH 5m bar with `g` valid:

**A. Settle orders planned on the previous bar**, using market fills `mktBuyFill = open + 2 ticks` and `mktSellFill = max(tick, open - 2 ticks)`:
1. C0 market exits (TIMEOUT / CAP_REDUCTION / STALE_DECAY). Then `sellRef := lowest remaining entry`. A TIMEOUT records `sessionId` in `timeoutSessionA`, at most once per session.
2. MINI market exit (partial or full, FIFO by slot). `miniRealized` is updated. When the mini is flat, `miniActive=false` and `state=NONE`.
   - 2b. Smart-core exits, then smart-core entries.
   - 2c. Trend exit (all slots), then trend entry.
3. **C0 SELL-FIRST.** The rebound target is checked before any buy touch. See §5.4.
4. MINI entry fill.
5. C0 buy-limit fills, **only if no C0 sell happened this bar** (`not coreSoldThisBar`).
6. End-of-bar state:
   - If C0 is flat, `not armActive` and `not armEventNow`, then `c0CampaignArmed=false` and `c0UnlockedSlots=0`.
   - `anchor := count==0 ? close : max(anchor, high)`.
   - Update `miniTrough = min(trough, low)`. If marked mini PnL (including the exit fee) `<= -MINI_RISK`, set `miniRiskFlag`.
   - Update `trendHighWater`.

**B. Cancel stale TV orders and run orphan cleanup.**

**C. Plan next-bar actions**, in this order:
1. Governors (§9).
2. Smart core (first bar only).
3. MINI exit decision.
4. Trend exit.
5. C0 timeout, then stale decay (switched off), then shared-cap reduction.
6. Trend entry, which "reserves a next-open trend entry before new mean-reversion inventory".
7. C0 rebound target and buy grid, only if no C0 market reduction is planned.
8. MINI STARTER / DIP / RECOVERY, only if no mini exit was planned and no C0 market exit was planned.

---

## 5. C0 core grid: exact mechanics

### 5.1 Anchor
- At a new session: `anchor := open` of the first RTH bar.
- After each bar's fills: `anchor := (no active core lots) ? close : max(anchor, high)`.

[HANDOFF] describes the same rule on 1m bars ("flat core follows the last completed Close; once core inventory exists, the anchor ratchets upward with observed Highs").

### 5.2 Buy levels and progressive deeper admission (spacing)
- `level_rank = f_round_down(anchor - rank * g)`, for `rank = activeCount+1 .. c0AllowedSlots`. **The next lot is always admitted one grid step (g) deeper per occupied rank.** The ranks already filled are skipped ([HANDOFF]: `levels = [anchor-g … anchor-6g][number_of_active_core_lots:]`). Because the anchor ratchets up to the high while inventory is held, the rank-k level is measured from the post-entry high, not from the last fill.
- Duplicate prices are removed, and only `px > 0` is kept. Each admitted level is assigned to the next free slot index.
- Size per lot: `q = f_floor_qty(SHARED_BUDGET/6 * entryRiskScale, px)`. `entryRiskScale = min(volScale, hwmScale)`, which is 1.0 in V18 because both shields are off. `f_floor_qty` is `floor(alloc/px)`, reduced until `q*px + fee <= alloc`.
- Admission requires `amount + reserved + bullCoreReservedNext <= cash` **and** `currentExposure + reserved + amount <= SHARED_BUDGET`, where `currentExposure = (core + mini + trend qty) * close` and `reserved` accumulates the trend reservation plus earlier admitted levels on this bar.
- Order: `strategy.entry(C0_<seq>_S<slot>, long, qty=q, limit=px)`. It lives for one bar and is re-planned every bar.
- **Window.** `nextMinute = minuteOfDay + 5` must fall in `[571, 945]` and `sessMin < 385`. So no buy rests into the 15:50/15:55 bars or overnight.

**Progressive admission** (`c0ProgressiveAdmission = true`) caps the number of slots that can be occupied:
- `c0StartEvidence = armActive and (fastVWAPExtreme or fastVWAPReclaim2 or fastVWAPDecel)`. `armActive` is the live G0 grouped-depression arm, defined in §6.1.
- **Stage 1 (max 2 slots):** if `activeCount == 0 and c0StartEvidence and not c0AccelVeto and not v7BlockStart`, then `c0CampaignArmed = true` and `unlocked = max(unlocked, 2)`. If `activeCount > 0`, the campaign stays armed with at least 2 slots.
- **Stage 2 (max 4), `c0Unlock4`:** `slowKnown and slowDeclineDecel and (fastVWAPDecel or fastVWAPReclaim2) and kcRecovery and bbRecoverySelected and rvolRecoveryOK and not adxBearHard`. In V18, `kcRecovery`, `rvolRecoveryOK` and `not adxBearHard` are all true because Keltner, RelVol and ADX are off. `BB_REQUIRE_U4 = true`, and `bbRecoverySelected = fastBBReclaim or fastBBExhaustion` (mode `RECLAIM_OR_EXHAUST`).
- **Stage 3 (6), `c0Unlock6`:** `slowKnown and slowDeclineDecel and (fastVWAPReclaim1 or fastVWAPAcceptance) and kcRecovery and bbRecoverySelected and rvolRecoveryOK and not adxBearRising`.
- Unlocks are **monotone within a campaign**. `c0UnlockedSlots` only resets to 0 when C0 is flat and no arm is live.
- `c0AllowedSlots = min(c0UnlockedSlots, regimeCap)`, where `regimeCap = min(adxCap=6, rvolCap=6, clusterSlotCap, v7BearCap=6[, hwm cap off])`.
- `c0AddPermission = c0CampaignArmed and not c0AccelVeto and not defenseHard and not (v7BlockStart and activeCount == 0)`. **`c0AccelVeto = slowKnown and slowDeclineAccel` blocks all new C0 buys, including deeper adds, while the completed 65m decline is accelerating.**

BB state used by the unlocks is computed on 5m closes with `BB_STATE_LEN = 23` and `MULT = 2.0` (population sd):
- `bbPctB = (c - lower)/(upper - lower)`
- `bbWidth = span/|basis|`
- `bbReclaim`: previous %B < 0 and current %B ≥ 0
- `bbExhaustion`: `%B < 0 and %B > prev %B and widthDelta < prevWidthDelta`

### 5.3 Fill convention (virtual ledger, mirroring `backtest_fill_limits_assumption=2`)
- A buy fills if `open <= px` (fill at the open) or `low <= px - 2*mintick` (fill at px).
- A sell target fills if `open >= target` (fill at the open) or `high >= target + 2*mintick` (fill at target).
- [HANDOFF] Python convention: fill at the open if the open is at or through the limit, otherwise fill at the limit if the low/high touches it, with no penetration requirement. The Pine requires 2 ticks of penetration, which is the "2t limit" of the V18 friction setting.

### 5.4 Highest-cost-first rebound reduction
- `sellRef`:
  - After buys in a bar: `sellRef := deepest (minimum) fill price of that bar`.
  - After a C0 target sell: `sellRef := (lots remain) ? that target : na`.
  - After market exits: `sellRef := lowest remaining entry`.
- Target: `target = f_round_up(sellRef + 2 * gPlan)`. It applies to **the single highest-cost occupied slot** (`f_core_highest_cost_slot`), with `qty = that slot's full qty`, via `strategy.exit("TP_"+id, from_entry=id, limit=target, comment="C0_REBOUND")`.
- `gPlan = g`, with one exception. On the last bar (`sessMin == 385`) of a complete 78-bar day, with at least 4 prior TRs valid, `gPlan = (sum of last 4 dailyTR + todayTR)/5/5`, i.e. tomorrow's g, so that the overnight target is right for a next-session gap.
- [HANDOFF] adds: "a reduction may realize a loss relative to that selected lot or to account average cost. Do not impose an 'only sell above average entry' rule."
- **Same-bar priority is SELL-FIRST.** If any C0 sell happened this bar (target or market), C0 buy touches in that bar are ignored.

### 5.5 Lot expiry (TIMEOUT)
- At `sessMin == 380` (the 15:50 bar close), every lot with `sessionId - coreDayA[k] >= 10` is planned as a market exit at the 15:55 open, reason `TIMEOUT`.
- [HANDOFF]: "ten-trading-session lot-age rule … Do not convert this to ten calendar days."

### 5.6 Shared-cap reduction
- Every bar, excluding lots already scheduled for exit: `while (coreQ + miniQ + trendQ) * close > SHARED_BUDGET`, schedule the **highest-cost remaining core lot** for a full-tranche market exit (`CAP_REDUCTION`), for at most 6 iterations.
- [HANDOFF]: "for C0 this is a full-tranche cap reduction, rather than silently resizing every lot pro-rata … a risk/capital action, not an alpha exit."
- When any C0 market exit is planned (`coreMarketPlanned`), no new C0 target or buys are planned that bar, and no MINI entry either.

### 5.7 Stale decay (present but OFF)
`useDecayShield = false`. If it were on, at 15:50 the highest-cost lot with age `>= DECAY_START_DAYS = 5` would be removed when `close < core avg` and not (`slowTrendBull` or `slowDeclineDecel` or `fastBBReclaim`).

---

## 6. G0 grouped-depression arm and 5m features ([PINE] = [HANDOFF] §4.1–4.3)

On each completed 5m bar:
- **A**: `RSI2 < 21`. RSI uses RMA(2) of gain/loss. If both are 0, RSI = 50.
- **B**: `close < SMA23 - 2*popStd23`. The Pine notes this is frozen.
- **C**: `z55(ROC27) < -1.6`. `ROC27 = 100*(typical/typical[27] - 1)`, `typical = (H+L+C)/3`, and z is taken over 55 bars using the mean and population std of ROC.
- **D**: `close < structuralDiscount`.
- `known` requires RSI, sd23, z55, structuralDiscount, `ATR14 > 0` (RMA of TR), EMA20 and CLV all valid.
- `score = A + B + C + D`, and `qualifying = known and score >= 2`.
- Supporting features:
  - `turn = c > prevC`
  - `COMPOSITE = c > o and turn and RSI2 > prevRSI2 and CLV >= 0.65`, with the fresh version firing on a false→true transition
  - `softDown = c < prevC < prevC2`

### 6.1 Arm creation (cohort de-duplication)
Starting state: `falseRun = 2` and `lastArmFastIndex = -10000`.

An arm fires when `qualifying and falseRun >= 2 and fastIndex - lastArmFastIndex >= 3 and not armActive`. Then:
- `armActive = true`
- `armExpiry = time_close + 30 min`
- `armSessionKey = today`
- `armEventNow = true`

`falseRun` resets to 0 on any qualifying or unknown bar, and otherwise increments. `armActive` clears after expiry, on a session change, or at `sessMin == 0`.

In words: a new arm needs at least 2 non-qualifying known bars since the last qualifying bar, at least 3 bars since the last arm, and no live arm.

---

## 7. VWAP layer ([PINE])

**Session VWAP** resets each RTH session:
- `p = (H+L+C)/3`
- `VWAP = Σpv/Σv`
- `SD = sqrt(max(Σp²v/Σv - VWAP², 0))`
- `z = (c - VWAP)/SD`
- `L1 = VWAP - SD` and `L2 = VWAP - 2SD`

Derived states:
- `vExtreme`: `z <= VWAP_START_Z = -1.50`.
- `vReclaim1`: `prevC < prevL1 and c >= L1`. `vReclaim2` is the same test at L2.
- `vDecel`: `low <= previous bar's low and z > prev z`, i.e. a new low with an improving z.
- Acceptance: `vReclaim1` arms acceptance with `run = 1`. Each following bar with `c >= L1` does `run += 1`, and any bar below L1 disarms it. `vAccept = armed and run >= VWAP_ACCEPT_BARS = 2`. The previous-bar VWAP states reset at `sessMin == 0`.

VWAP roles:

| Role | Condition |
|---|---|
| **C0 stage-1 start evidence** | `vExtreme or vReclaim2 or vDecel` (with armActive) |
| **C0 unlock 4** | `vDecel or vReclaim2` |
| **C0 unlock 6** | `vReclaim1 or vAccept` |
| **MINI STARTER** | `vExtreme or vReclaim2` (`vwapStarterAllowReclaim2 = true`) |
| **MINI DIP** | `z <= VWAP_DIP_Z = -1.75` |
| **MINI RECOVERY** | `vReclaim1 or vAccept` (`vwapRecoveryRequireAcceptance = false`) |
| **Trend start** | `fastClose > fastVWAP` (and > EMA20) |

**VWAP reduction ladder (MINI)**, with `enableVWAPExitLadder = true` and `miniVWAPExitStage` 0→1→2→3:
1. Stage 0, `vReclaim1` → `VWAP_L1_RECLAIM`: sell 1/3 and set stage = 1.
2. Stage 1, `close >= VWAP - 0.5*SD` → `VWAP_M05`: sell 1/3 and set stage = 2.
3. Stage ≥ 2, `close >= VWAP` → `VWAP_MEAN`: sell 100% and set stage = 3.

These sit below RISK, TIME, CATASTROPHIC and SOFT in priority, and above REBOUND (`legacyReboundAfterVWAP = true`).

---

## 8. Smart core / long-exposure retention ([PINE] V12–V17)

`bullCoreEnabled = ticker == "SOXL" and V12_CORE_MODE != "CONTROL" and g ready`. The frozen mode is `SOXX_TIERED_RS_ZERO_BEAR_SMA_STACK` (`CONTROL` is used only when `V17_ABLATION_MODE == "TACTICAL_ONLY"`). "SOXX and SOXL reference the same NYSE Semiconductor Index while SOXX is not daily 3x leveraged", so the SOXX daily state is used as a 1x proxy.

The SOXX daily states are all prior-day values: D1 = yesterday, D2 = the day before.
- `soxxMedium = C_D1 > EMA50_D1 and EMA50_D1 >= EMA50_D2`
- `soxxStrong = soxxMedium and EMA20_D1 > EMA50_D1 and EMA20_D1 > EMA20_D2`
- `soxxLeadership = ROC20(SOXX)_D1 > ROC20(QQQ)_D1`
- `soxxSecularBearSmaStack = C_D1 < SMA200_D1 and SMA50_D1 < SMA200_D1 and SMA200_D1 < SMA200_D2`

This is the **selected** bear definition. The EMA version, a no-slope version and a price-slope version exist as ablations. A hysteresis lock exists but is not used by SMA_STACK.

Desired tranches, recomputed on the first bar of each session:
- `zeroBearActive = soxxSecularBearSmaStack`
- `wantBase = not zeroBearActive`
- `riskOverlayAllowed = not (v8RiskLevel >= 3) and not zeroBearActive`
- `wantMid = riskOverlayAllowed and soxxMedium`
- `wantTop = riskOverlayAllowed and soxxStrong and soxxLeadership`

Transitions, applied per tranche on the first RTH bar:
- **Held and not desired:** market exit at the next open. The reason is the first that applies, in this order: `BULL_PROTECT`, `BULL_TOTAL_BEAR`, `BULL_BEAR_LOCK`, `BULL_FAST_BRAKE`, `BULL_RISK_OFF`.
- **Not held and desired:** market entry of `f_floor_qty(20000, close)` if `amount + already reserved <= cash`.

Otherwise the tranche is held. It has no stop, no target and no timeout. This is the **long-exposure retention** mechanism: in non-bear regimes at least the $20k BASE tranche stays on permanently.

---

## 9. Campaign-state control, REDUCTION lock and deterministic REARM

The sources do not use one global ACCUMULATION/HOLD/REDUCTION/REARM enum. The equivalent state machines are listed below.

### 9.1 MINI campaign (the explicit "no adds after reduction" rule)
States in [PINE] are `NONE → ARMED → BUILDING → DERISK → NONE`. [HANDOFF] names them `ARMED → BUILDING / ADD_BLOCKED → DERISK → CLOSED`.
- **ARMED** is set when a STARTER is planned. It resets all campaign fields and locks `miniOriginalATR = fastATR14`. If the STARTER fails capital admission, the state goes back to NONE.
- **BUILDING** starts at the first mini fill. At that point `miniFirstPrice` is set and `miniDeadline = min(fill time + 360 min, 16:00 - 1 min)`.
- **DERISK**: any planned mini exit sets `miniReductionStarted = true` and `miniState = "DERISK"`. In the entry block, `if miniActive and miniReductionStarted → role := ""`. **So once any reduction (SOFT, VWAP ladder, REBOUND, partial CAP or anything else) begins, no DIP or RECOVERY add can be planned for that campaign.** [HANDOFF] §4.5/§5.8: "once any reduction begins, reduction_started becomes true, state becomes DERISK, pending entry is cancelled, and NO NEW ADD is allowed for that campaign."
- **Deterministic REARM**: the only way back to accumulation is (a) the campaign goes completely flat (`miniActive = false`, state NONE) **and** (b) a **new** G0 arm event (`armEventNow`, subject to the §6.1 cohort spacing) with STARTER VWAP evidence and 65m DECLINE_DECELERATION permission. That creates a new campaign with a new arm ID. Nothing re-enables adds inside a campaign that has started reducing.
- A partial fill is not modelled in the virtual ledger. [HANDOFF] says partial fragments are not new economic entries.

### 9.2 C0 campaign
- **ACCUMULATION** is the C0 campaign being armed with an unlocked-slot budget of 2, then 4, then 6 (§5.2).
- **HOLD/REDUCE**: while lots are held the campaign stays armed. Rebound sells remove the highest-cost lot one at a time. They do **not** block further deeper buys, because C0 is a grid. The only same-bar interaction is SELL-FIRST.
- **Hard blocks on adds**:
  - `c0AccelVeto` (65m decline accelerating)
  - `defenseHard` (cluster hard stop)
  - `coreMarketPlanned` (any timeout or cap exit this bar)
  - `v7BlockStart` (DD15), which blocks only new campaigns
- **Reset**: flat, with no live arm, sets `c0CampaignArmed = false` and `unlocked = 0`. A new campaign then needs fresh stage-1 evidence.

### 9.3 Account-level DD15 protection with deterministic market REARM (V8/V9/V10 "CURRENT")
- `v8EpochHWM = max(epochHWM, strategy.equity)` and `epochDD% = 100*(HWM - eq)/HWM`.
- If `epochDD% >= 15.0`, then `v8RiskLevel = 3` and `v8DefenseStartSession = sessionId`, set on the first trigger.
- Effects: `v8BlockStart` means **no new C0 campaign when C0 is flat** ("only NEW C0 campaign starts are blocked. Existing C0 and the trend sleeve are untouched"), and smart-core MID/TOP overlays are removed.
- **REARM** (deterministic): `v8RiskLevel > 0 and sessionId > v8DefenseStartSession and (v8DailyBull and slowTrendBull)`.
  - `v8DailyBull = priorDailyClose > dailyEMA20 and dailyEMA20 > prevDailyEMA20`, computed on the SOXL daily state built from 5m.
  - `slowTrendBull` is the 65m bull state in §10.
  - On REARM: level = 0, `v8EpochHWM = current equity`, and `v8RearmCount += 1`.

### 9.4 Timeout-cluster governor (`useClusterShield = true`)
- `timeoutSessionA` keeps the sessions that saw a C0 TIMEOUT within the last `CLUSTER_WINDOW = 20` sessions.
- `clusterHard = count >= 3 and sessionId - lastTimeoutSession <= 5`.
- `clusterSlotCap`: 0 if hard, 2 if count ≥ 2, otherwise 6.
- `clusterTrendCap`: 0 if hard, 1 if count ≥ 2, otherwise 3.
- `defenseHard = clusterHard` (HWM shield off). It blocks new C0 adds, trend entries and mini entries.
- The governor re-arms by the passage of time. The hard state drops once more than 5 sessions pass after the last timeout, or once old timeouts roll out of the 20-session window.

### 9.5 Other governors present but OFF in V18
`useVolShield`, `useDecayShield`, `useHWMShield`, `useADXGovernor`, `useKeltner` and `useRelVol` are false. The V7 "hard bear" (daily bear stack plus 65m bear) is telemetry and alert only.

---

## 10. Trend sleeve vs mean-reversion sleeves

The mean-reversion side is C0 plus MINI: it buys depression and sells rebound. The trend side is the offense and pyramids winners only. It is enabled on SOXL (`useTrendSleeve`, not on TQQQ unless `allowTrendOnTQQQ`).

**65m bull state**, evaluated on complete 65m buckets:
- `known65` requires EMA20, ATR14 > 0, High20/Low20, slope, d3 and dprev all valid.
- `slope65 = EMA20 - EMA20[3]`, `d3 = C - C[3]`, `dprev = C[3] - C[6]`.
- `bull65 = known65 and C > EMA20 and slope65 > 0 and d3 > 0 and dprev >= 0 and (not dmiKnown or +DI > -DI)`. DMI and ADX use RMA14.
- `slowTrendBullFresh = bull65 and not prior bull65`.
- `slowTrendFailCount` is reset on bull and otherwise incremented.
- DECLINE: `known65 and C < EMA20 and d3 < 0 and dprev < 0`. `slowDeclineDecel = decline and d3 > dprev`, and `slowDeclineAccel = decline and d3 <= dprev`.

**Entry**, planned on a completed 5m bar with `slowTrendBull and not defenseHard and not workTrendExit`:
- START: `count == 0`, cooldown `bar_index - trendLastExitBar >= 13`, `fastClose > fastEMA20 and fastClose > sessionVWAP`, and one of:
  - `slowTrendBullFresh`
  - `fastTrendBreakout` (close > max high of the prior 20 5m bars)
  - `fastTrendReclaim` (close > EMA20 and > VWAP, with prevClose ≤ prior EMA20 or ≤ prior VWAP)
- ADD: `0 < count < min(3, clusterTrendCap)`, spacing `>= 13 bars` since the last entry, `fastTrendBreakout`, and `fastClose >= trendLastPrice + TREND_ADD_ATR(0.50) * slowATR14`.
- Size: `f_floor_qty(30000/3 * entryRiskScale, close)`. It must pass the shared $80k exposure cap and cash. The entry is a market order at the next open.

**Exit (frozen `TREND_EXIT_MODE = "CURRENT"`)**, always a full sleeve exit:
- The trail is armed immediately.
- `stop = max(highWater - 3.0*ATR65, EMA65 - 1.0*ATR65)`, and it only ratchets up.
- Exit if any of the following holds:
  - `close <= stop` → `TREND_TRAIL`
  - `slowTrendFailCount >= 2` → `TREND_65M_FAIL`
  - `close < EMA65 and -DI > +DI and ADX rising` → `TREND_BEAR_BREAK`

The trend sleeve has no fixed take-profit. Its planned entry is reserved before C0 buy admission on the same bar.

---

## 11. MINI (G0/E1) roles and exits: exact conditions ([PINE], disabled in V18)

Common gates:
- `fastEventNow`, no planned mini exit, no C0 market exit this bar.
- Entry window: `nextMinute ∈ [571, 945] and sessMin < 385`.
- **Permission** for every role: `slowKnown and slowDeclineDecel` (completed 65m DECLINE_DECELERATION).

| Role | Exact condition |
|---|---|
| **STARTER** | `armEventNow and not miniActive` and (`vExtreme or vReclaim2`). This creates the campaign. |
| **DIP** | `miniActive`, qty > 0, `miniEntryCount < 3`, not reduction-started, spacing `time_close - miniLastEntryTime >= 15 min`, `armEventNow` (a fresh arm), `miniDipCount < 1`, `fastClose <= miniLastPrice - 0.5*miniOriginalATR`, `fastVWAPZ <= -1.75` |
| **RECOVERY** | same campaign and spacing gates, `fastCompositeFresh`, `miniRecoveryCount < 1`, `fastClose >= miniLastPrice + 0.25*ATR0`, `fastEMA20 - fastClose >= 0.5*ATR0`, `vReclaim1 or vAccept` |

If both DIP and RECOVERY qualify, DIP wins.

Size and caps:
- Size is `q = f_floor_qty(10000/3, fastClose)` into the first free slot.
- Admission: cash, `(core + mini + trend + q)*close + coreReservedNext <= 80000`, `(mini + q)*close <= 10000`, and `not defenseHard`.
- Fill at the next open (plus 2 ticks). N3/BOTH means at most 3 lifetime entries: 1 STARTER, ≤1 DIP, ≤1 RECOVERY.

**Exit priority** (planned at the bar close, filled at the next open). The first match wins:
1. `CAP`: `mq*close > 10000` or `(core+mini+trend)*close > 80000`. Full exit.
2. `RISK`: `miniRiskFlag` set, i.e. marked campaign PnL including costs was `<= -250`.
3. `TIME`: `time + 5 min >= miniDeadline`.
4. On a known fast bar:
   - `CATASTROPHIC`: `close <= firstPrice - 3*ATR0`. Full exit.
   - `SOFT` (once only): `close < firstPrice - 1*ATR0` or (`mq*close/10000 >= 0.5 and softDown`). Sell 1/3.
   - VWAP ladder L1 / M05 / MEAN (§7).
   - `REBOUND`: `close >= required`, where `required = max(trough + 0.75*ATR0, rearmLevel)`. Sell 1/3, then `rearmLevel = close + 0.75*ATR0`.
5. `SLOW_MEAN`: `slowKnown and close >= slowEMA20` (65m). Full exit.

The partial size is `qSell = min(total, max(1, ceil(total * fraction)))`, taken FIFO across slots. The Pine's CAP and RISK/TIME are full exits with fraction 1. [HANDOFF] also lists RISK/TIME ahead of the fast exits, and notes that the $250 is "not a guaranteed maximum realized loss".

---

## 12. Friction, sizing and fills ([PINE] V18 "2X FRICTION")

- Strategy properties:
  - `commission_type = percent`, `commission_value = 0.04` (4 bps per fill)
  - `slippage = 2` (ticks)
  - `backtest_fill_limits_assumption = 2`
  - `margin_long = 100` (no leverage beyond cash)
  - `initial_capital = 140000`
- Virtual-ledger fee: `f_fee(q, px) = q*px*COST_BPS/10000 + min(max(0.0035*q, 0.35), 0.01*q*px)`, with `COST_BPS = 4.0`. That is 4 bps plus an IBKR-style per-share commission with a $0.35 minimum and a 1% cap. The per-share component "remains in the virtual ledger only".
- Market fills in the ledger are at open ± 2 ticks. Limit fills need 2 ticks of penetration unless the bar gaps through the limit.
- Dashboard label: "4bp fee / 2t slip / 2t limit".
- **Internal inconsistency.** The header comments still say "Strategy Tester charges 2 bps per fill" and "1 tick slippage". The constants that are actually used are 4 bps and 2 ticks. This matches the "V18 2X FRICTION" name: double the V12-era friction.
- Diagnostics: a same-capital SOXL buy-and-hold benchmark (one buy at the first RTH open, same slippage and fee) with mark-to-market max drawdown, "upside capture" and "DD reduction vs B&H". **The Pine file contains no recorded result values.**
- [ROADMAP] canary and production policy for comparison: the canary is 1 SOXL share, 20 bps spread limit, max $250.

### 12.1 Results cited in the documents (verbatim numbers only)
These results belong to the **Python C0 + G0/E1 (V1)** research lane, not to the V18 Pine:
- Evidence period: "2022-01-03 through 2026-09-10 SOXL lane is exposed research history, not untouched OOS". "V1 retains a known severe-bear weakness."
- MATH-A overlay (not promoted). Account increments at 2/5/10 bps: +$5,288.85 / +$5,230.44 / +$5,159.29. MaxDD at 2 bps was -$40,739.84 on both paths. The 95% block CI of the increment was [-$2,898.04, +$17,432.52]. Excluding the most favourable inventory-difference interval gives -$57.06, and excluding two intervals gives -$1,916.49. "2022 손실 개선은 없고" (no improvement on the 2022 loss).
- Cross-asset portability at a common 2 bps/side. C0 / Combined net:
  - SOXL: 126,640.85 / 144,866.17
  - TQQQ: 37,105.57 / 38,647.50
  - NQ normalized: 15,597.13 / 15,299.45
  - Combined MaxDD: -40,739.84 / -39,952.73 / -14,147.45
  - Over the full ETF period, SOXL Combined net was 141,037.12. The TQQQ 10 bps G0 increment was -458.32. G0 increment CIs included 0 for all three assets.
  - Verdicts: `TQQQ_NO_RETUNE_PORTABILITY=PARTIALLY_PORTABLE`, `NQ_RTH_NO_RETUNE_PORTABILITY=INCONCLUSIVE`, `OVERALL_V1_MECHANISM=INCONCLUSIVE`.
  - "NQ는 실제 MNQ 계약 PnL이 아니다" (NQ is not actual MNQ contract PnL). "실제 MNQ 최소 계약 notional 20,969 > core unit 13,333.33이므로 기존 단위별 정상 정수 수량 0" (the real minimum MNQ contract notional, 20,969, exceeds the core unit of 13,333.33, so the normal integer quantity per existing unit is 0).
- Surgical TRANSITION_DEEP_HALF (ranks 5–6 at 50% unless the daily bear is confirmed). TQQQ went from $40,543 / −$39,953 to $45,677 / −$36,932. NQ normalized went from $15,299 / −$14,147 to $17,281 / −$13,108. Excluding 2022 the increments were −$3,234 / −$666. Verdict: NO_IMPROVEMENT_FOUND for both.
- Final calibration: "NO_ROBUST_EDGE; CROSS_ASSET_PARAMETER_STRUCTURE = NO_STABLE_BASIN". TQQQ C0 went from Net 39,011.93 / DD -39,941.05 to a diagnostic center of 50,531.49 / -24,368.37, but the result was NARROW_PEAK, WF delta -38,650.72, and G0_HARMFUL at that center. NQ C0 went from 15,597.13 / -14,139.99 to 14,418.88 / -9,867.40, also NARROW_PEAK.
- Conditional long-history HF/BATS source paths for fixed C0+G0/E1: net 122,791.90 / 164,880.57, MaxDD -51,289.94 / -42,240.89. This is "not verified dollar expectancy; source-path identity FAIL".
- Portfolio context (research only): P0 = SOXL_CORE_MINI_V1.0 at $144,866.17 / -$40,739.84, median week $0.00. P1 = P0 + MNQ sleeves at $286,998.08 / -$44,757.12, median week $866.24. Positive weeks went from 42.2% to 66.5%, and zero weeks from 43.0% to 1.7%.

---

## 13. TRANSFER MAP TO MES 3m

Target: a long-only MES strategy on 3-minute bars, Pine v6, with **one net position**, **1-MES steps**, and **max 24–40 MES**, built as sticky core plus tactical overlay. The **Translation** column is a proposal that follows from the mechanisms. The **Risk** column lists hazards that follow from the documents and from the structural differences between the instruments. No MES performance is claimed.

### 13.1 Structural differences that condition every item
1. **Instrument.** SOXL is a 3x daily-reset leveraged ETF on a semiconductor index. MES is an unlevered-per-contract future on the S&P 500. The SOXL grid steps, ATR multiples and the smart-core SOXX proxy all encode 3x semiconductor volatility. The documents already record that V1 did **not** port cleanly to TQQQ or to NQ (PARTIALLY_PORTABLE / INCONCLUSIVE / NO_STABLE_BASIN). An S&P micro is a further step away.
2. **Granularity.** SOXL sizes in shares (fine-grained dollars per lot). MES sizes in whole contracts. The roadmap already found that "MNQ minimum contract notional 20,969 > core unit 13,333.33", which gives an integer quantity of 0. The MES design must **define lots in contracts, not dollars**. For example, a C0 lot = k MES with k ≥ 1, and all partial reductions (1/3 fractions) round through `max(1, ceil(q*f))` to whole contracts.
3. **Bar clock.** 5m becomes 3m. A full RTH day is 78 × 5m bars and 130 × 3m bars. The 13:00 early close is 42 × 5m bars and 70 × 3m bars. **65m is not a multiple of 3m** (65/3 is not an integer), so the 13×5m aggregation cannot be copied. It must be redefined: for example 60m = 20×3m (six buckets plus a 30m tail) or 78m = 26×3m (five buckets). Parity with the SOXL semantics is then impossible by construction, and the change has to be recorded as a new definition. Bar-count lengths (RSI2, SMA23, ROC27/z55, EMA20, ATR14, 20-bar breakout, 13-bar cooldown, 3-bar arm spacing, 30-min arm expiry, 15-min add spacing) need an explicit choice: keep the bar counts (shorter wall time) or keep the wall time (rescale the counts). Either choice is a retune the documents warn about.
4. **Session.** MES trades nearly 24 hours. The SOXL engine is RTH-only with session-built daily TR, a 10-RTH-session timeout, and a session VWAP reset at 09:30 ET. The MES design must decide whether bars outside RTH are ignored (the SOXL-equivalent choice) and how overnight gaps enter TR. [ROADMAP] records that NQ ETH use was "SEMANTICALLY_BLOCKED" because of calendar issues.
5. **Friction.** A percent commission is the wrong model for futures. Use a fixed per-contract commission plus a tick-based slippage. The MES tick is 0.25 index points. The SOXL "2t slip / 2t limit penetration" convention should be translated in ticks and then stress-tested.
6. **Rolls.** MES rolls quarterly. [ROADMAP] requires "old-contract exit → confirmation → successor entry, no double exposure" and a frozen roll calendar before live use. Lot ages (the 10-session timeout) and anchors must survive a roll without being reset by the continuous-contract back-adjustment.
7. **Drift and volatility.** SOXL's large intraday ranges and deep mean-reverting dips feed the 1–6g ladder. S&P intraday excursions are relatively smaller and drift is steadier. That favours the sticky core and trend sleeve over deep-grid fills, and increases the time C0 inventory spends parked.

### 13.2 Mechanism-by-mechanism map

| # | SOXL mechanism (source) | MES 3m translation (1-MES steps, net position) | Expected risks |
|---|---|---|---|
| 1 | **Sleeve separation**: Smart core ($60k, outside shared cap) plus shared tactical cap ($80k: C0 + Trend + Mini). §1 | Keep **virtual sleeves** with separate contract budgets that sum to the cap, e.g. CORE_MAX + TACTICAL_MAX ≤ 24–40. The net order equals the Σ sleeve targets minus the position ([ROADMAP] "GLOBAL_BROKER_TARGET = Σ sleeves; ORDER_DELTA = target − observed"). Pine only has one net position, so keep per-lot virtual arrays as the Pine does, with `strategy.entry/close` by ID or a single `strategy.order` delta. | Emulator/virtual mismatch (the Pine already needs `tvMismatch` and orphan cleanup). With netting, a sleeve that sells while another buys on the same bar should net to zero orders, and the SOXL ID-per-lot design does not do that. |
| 2 | **Smart core tranches** BASE/MID/TOP, first-bar daily decision, SOXX 1x proxy, SMA-stack secular-bear zero, RS vs QQQ for TOP. §8 | Tranches of N_core/3 MES each. The daily state can come from MES/ES itself (already 1x) or SPX. Keep prior-day-only `[1]`/lookahead-on semantics. The RS leg (SOXX vs QQQ) has no direct S&P analogue. Either drop it or define a new one (a new hypothesis, not a transfer). | The permanent BASE tranche carries full index drawdown in non-"secular bear" declines. SMA200-stack bear detection lags, so a 2022-type decline is partly held before the zero triggers. Daily-only decisions leave intraday gap and tail risk on the largest sleeve. |
| 3 | **C0 grid**: `g = ATR5_daily/5`, anchor (open → close if flat / ratchet high if held), `level_k = anchor − k·g`, 6 lots, next lot one g deeper. §5.1–5.2 | Keep the formula in index points, tick-rounded (0.25). Lot = k MES. With 6 lots and k = 1–3, C0 alone is 6–18 MES, which fits under 24–40 with core plus trend. The daily TR must be built from the chosen session (RTH-only for parity with the SOXL logic). | On a lower-volatility index, g in points is small relative to the tick and to friction. The 2g rebound target may be only a few ticks net of costs, so check it against the MES fee and slippage before use. Deeper ranks (5–6) held for 10 sessions are the documented weak spot ("deep-inventory 체류가 길고 worst campaign의 반등이 약했다", i.e. deep-inventory holding was long and the worst campaign's rebound was weak, found on TQQQ/NQ). |
| 4 | **Progressive admission** 2 → 4 → 6 via arm+VWAP evidence, 65m decel+VWAP/BB, 65m decel + L1 reclaim/acceptance. `c0AccelVeto` blocks all adds. §5.2 | Transfer as-is conceptually, with the slow context redefined (60m or 78m). Unlocks stay monotone per campaign and reset only when flat with no live arm. | Redefining the slow bucket changes the decel/accel classification, so the unlock frequency is unknown. BB/VWAP thresholds tuned on 3x-ETF dispersion may unlock too rarely (C0 idle) or too often on S&P. |
| 5 | **Highest-cost-first rebound**: target `sellRef + 2g` on the single highest-entry lot. sellRef = deepest fill / last target / lowest entry after market exits. SELL-FIRST same bar. §5.4 | Direct translation: reduce the highest-cost virtual lot by its k MES at a limit target. Keep SELL-FIRST. Keep the overnight gPlan refresh, which on MES must be computed at the chosen session end. | Needs a 3m-bar same-bar ambiguity rule (buy and sell touched in one bar). Bar magnifier or intrabar ordering differs from the Python/SOXL conventions. Realized losses against average cost are allowed by design, so do not "fix" that. |
| 6 | **10-session timeout** at 15:50 → 15:55 open, highest-cost cap reduction, timeout-cluster governor (20-session window; ≥2 → cap 2; ≥3 and ≤5 sessions → hard 0). §5.5–5.6, §9.4 | Keep the session count (not calendar days) on the MES session definition. On 3m bars the planning bar becomes the last-but-one RTH bar (15:54 → fill at 15:57). The cap reduction translates to "total tactical contracts > TACTICAL_MAX" and removes the highest-cost lot. | Timeouts crystallize losses at a fixed clock. On a steadily drifting index, a failed campaign may time out right before recovery. Roll dates can collide with the timeout. |
| 7 | **G0 grouped arm** (A RSI2<21, B SMA23−2σ, C z55(ROC27)<−1.6, D < prior pivot − 0.25·range; score ≥2; falseRun ≥2; spacing ≥3 bars; 30-min expiry). §6 | Port the formulas unchanged, but choose explicitly between bar-count and wall-time scaling. D uses the prior RTH session HLC. | The thresholds come from exposed SOXL history. On S&P, `score>=2` frequency and the forward returns after it are unknown. The feature correlation noted in [HANDOFF] may reduce the evidence to one factor. |
| 8 | **VWAP roles**: z ≤ −1.5 extreme; −2SD/−1SD reclaims; decel; 2-bar acceptance; DIP z ≤ −1.75; ladder L1 → −0.5SD → VWAP. §7 | Session VWAP from the RTH open (or define a futures session anchor; ETH volume changes the VWAP). The ladder maps to 1/3, 1/3 and remainder of the tactical lot in whole MES via `max(1, ceil(q/3))`. | With 1–3 MES per campaign the 1/3 steps collapse. For example, 2 contracts sell 1, then 1, then 0, which changes the ladder economics. Volume-weighted SD on ES is dominated by open and close volume, so band widths differ intraday from SOXL. |
| 9 | **MINI STARTER/DIP/RECOVERY** (N3/BOTH, 15-min spacing, 0.5·ATR0 dip, +0.25·ATR0 recovery with ≥0.5·ATR0 room to EMA20; all need 65m DECLINE_DECELERATION). §11 | Tactical overlay lots of 1 MES each (N3 → 3 MES max). Next-open market entries. Frozen V18 disabled the mini ("NO_MINI"), and [ROADMAP] reports G0 increments whose CI includes 0, "TQQQ cost-sensitive, NQ 기여 미약" (weak NQ contribution), and G0_HARMFUL at the TQQQ calibration center. Treat it as optional and last to port. | Evidence against its value on other assets. Per-contract friction on 1-lot entries is proportionally heavier. |
| 10 | **REDUCTION blocks re-adds until a deterministic REARM.** Mini: `miniReductionStarted` blocks DIP/RECOVERY until the campaign is flat and a new arm arrives. Account: DD15 blocks new C0 campaigns and MID/TOP until `dailyBull and 65m bull` on a later session, then the HWM resets. §9 | Implement one explicit enum per tactical campaign: ACCUMULATION → HOLD → REDUCTION → (flat) → REARM_WAIT → ACCUMULATION. Legal transitions: the first reduction moves to REDUCTION (adds forbidden). Flat plus a new fresh arm moves to ACCUMULATION with a new campaign ID. DD15-style epoch protection with market re-arm at account level. | With a net-position futures book, a "reduction" in one sleeve must not be undone by another sleeve's add in the same net order, or the lock is bypassed in effect. The rearm conditions are regime detectors tuned on SOXL daily and 65m data. |
| 11 | **Trend sleeve**: 65m bull (C>EMA20, slope>0, d3>0, dprev≥0, +DI>−DI). Start on fresh bull, 20-bar breakout or EMA/VWAP reclaim, above EMA20 and VWAP. Add on breakout with +0.5·ATR65 over the last entry. 13-bar spacing/cooldown. Stop = max(HW − 3·ATR65, EMA65 − 1·ATR65), plus 2-bucket fail and bear-break exits. §10 | Well suited to S&P drift. Slots of k MES (3 slots). The 13-bar cooldown equals 65 minutes on 5m and needs rescaling on 3m (65 is not divisible by 3, so use 21 or 22 bars ≈ 63 or 66 minutes). | Trend and core are both long-beta, so a combined drawdown can reach the full 24–40 MES in a sharp reversal. The ATR65-based stop on a redefined slow bucket changes the stop distances. Whipsaw frequency on 3m is unknown. |
| 12 | **Capital/exposure gates**: every admission checks cash and `(core+mini+trend)*close ≤ 80k`. The trend reservation comes before C0, and C0 before mini. §5.2, §10, §11 | Replace dollar exposure with contract counts (and optionally margin). Hard total ≤ 24–40 MES. Tactical ≤ TACTICAL_MAX. Keep the reservation order: exits first, then trend, then C0, then mini. | Margin stress (the MNQ research found 2.0x-margin stress breaches). A fixed cap in contracts means exposure in dollars scales with the index level. |
| 13 | **Friction** 4 bps + per-share commission, open ± 2 ticks, 2-tick limit penetration. §12 | Per-contract commission plus exchange fees (fixed $), 1–2 tick slippage on market orders, and a tick-penetration rule for limits. Stress with at least 2x friction, following V18 "2X FRICTION". | Small g relative to the MES tick makes the C0 edge highly sensitive to the fill convention. The limit-fill assumption is the largest source of Pine vs live divergence. |
| 14 | **Causality**: prior-day `[1]`/lookahead-on, completed-bucket HTF, session-complete checks (78 or 42 bars), `na`-on-incomplete. §2 | Keep all of it. Recompute the completeness counts for 3m (130 or 70 bars). Handle holiday and early-close sessions explicitly. Do not forward-fill. | Continuous-contract back-adjustment changes historical levels, and so the daily TR, the pivots and D. Decide between the raw front month and back-adjusted data before building the daily authority. |
| 15 | **Parity-first discipline** ([HANDOFF] §9, §11): state and event parity before PnL. Do not retune thresholds to match. | Build the MES version as an observational indicator first (levels, arms, unlocks, states), then the strategy. Treat every threshold change forced by 3m/65m incompatibility as a pre-registered new variant. | The documents' own verdicts for index-futures transfer (NQ INCONCLUSIVE, NO_STABLE_BASIN, NARROW_PEAK) mean any MES edge has to be established fresh. It is not inherited. |

### 13.3 Illustrative contract budget (a design choice, not from the sources)
A partition consistent with "1-MES steps, max 24–40" that mirrors the SOXL proportions (smart core $60k : tactical $80k ≈ 3 : 4, with the trend at $30k of the $80k):
- Smart core 3 tranches × 3–5 MES = 9–15
- C0 6 lots × 1–2 MES = 6–12
- Trend 3 slots × 2–3 MES = 6–9
- Mini 3 × 1 MES = 0–3 (optional)

The total is ≤ 24–39. Every per-lot count here is an assumption to be pre-registered. None of it comes from the legacy documents.

### 13.4 Items that must not be carried over silently
- MATH-A: excluded in every source.
- The EMA/hysteresis bear variants and the switched-off shields: they are ablations, not the frozen V18 authority.
- The "2 bps / 1 tick" wording in the Pine header comments: the executed constants are 4 bps and 2 ticks.
- SOXL buy-and-hold framing: the MES benchmark should be MES buy-and-hold at the same contract cap.
