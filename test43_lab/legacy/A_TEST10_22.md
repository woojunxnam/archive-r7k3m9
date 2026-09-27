# A_TEST10_22 — Legacy lessons from TEST10, TEST11, TEST15-18 roadmap, TEST18, TEST22

Scope: we are building an MES/ES intraday long-only inventory strategy on 3-minute bars in Pine v6. This note pulls together what the legacy program (5-minute, multi-market, long and short) actually tested, what survived, what failed, and which feature definitions and Pine patterns can be reused.
Rule for this note: every number below is quoted from the source documents. Where the sources are silent, the note says **NOT IN SOURCES**. Pine formulas are copied from the saved files.

Where the evidence comes from:
- TEST10 and TEST11: Pine source only. No review document for either was provided, so verdicts are partly **inferred** and marked as such.
- TEST18: Pine source and the final review.
- TEST22: the final review only. The TEST22 Pine was not provided, so its exact indicator formulas are unknown.
- Roadmap LOCK V2: plan and governance only, no results.

---

## 0. Source files (saved raw under `/home/user/lab/authorities/legacy/`)

| Saved file | Drive name | Drive ID | Bytes | sha256 |
|---|---|---|---|---|
| TEST10_SURVIVOR_DERIVED_FACTORY_FULL_HISTORY_V1.pine | TEST10_SURVIVOR_DERIVED_FACTORY_FULL_HISTORY_V1.pine | 1TuMh0sJco1bIfcNFhZtvCk_9frshIvpE | 23982 | df22d2a11ab58fc04be2bca0c3370c49ea190d9e21e5102352b2ae6f89188f62 |
| TEST11_FAILED_RECOVERY_FACTORY_V1.pine | TEST11_FAILED_RECOVERY_FACTORY_V1.pine | 1uqaWAhsIi5hZKDyIjFFcxhWonrGQg6ey | 33964 | fcac294beae81fe89c8e0fc61f1473ac2a1379754091aece6c4046c7f773b873 |
| TEST18_NATIVE_FACTORY_V1.pine | TEST18_NATIVE_FACTORY_V1.pine | 1wqabZmWKNoPkk2nt0aNqZGo-Y7j5bvHX | 10771 | 8f9611e974a6bb998a7ccb8e4297e1571f54f4133296400ace26a7af9fc06e93 |
| RESEARCH_ROADMAP_TEST15-18_LOCK_V2_2026-09-17.gdoc.txt | RESEARCH_ROADMAP_TEST15-18_LOCK_V2_2026-09-17 (Google Doc) | 1lcZTaDsBK6lwAlo5AZr_5NUwhFj6C62_VrEfZLFD4EA | 6480 | 762f2ddc21fc0f3ab936bfee79843fe0f6e9455f4d11c75bb08cf7d4f61ce0b3 |
| TEST18_FINAL_REVIEW_2026-09-17.gdoc.txt | TEST18_FINAL_REVIEW_2026-09-17 (Google Doc) | 1-pgKhZjYRde8OjW3mCG1seQnUCBKrqNC2VbLHYpuviY | 3125 | 413538b7391a78b6d896bc5c478763c9fdedaade2c8830fd60957d760daf627d |
| TEST22_FINAL_REVIEW_2026-09-18.gdoc.txt | TEST22_FINAL_REVIEW_2026-09-18 (Google Doc) | 1eTr1PCTvJMYQaVYI1rDD0PnGc2N4-OnepGU3jIucysA | 4697 | 541bd58a5e94aabe092e47db90febbc3abed6998b58fa5e1ba7e9cb97960df16 |

How the files were saved:
- **Pine files** are byte-exact decodes of the Drive `download_file_content` base64. Each byte size matches the Drive metadata `fileSize` (23982, 33964, 10771).
- **Google Docs** are the text rendering returned by Drive `read_file_content`, not an official Drive export. That rendering keeps markdown escapes such as `\-` and `\#`. The hashes cover that rendering.
- The TEST10 header cites its parent file hash: `9dbdf0eaaa7eb17193f149bb46f09ccdc62324986a436b2b2fd24fefd641acc3`, for `TEST10_SURVIVOR_DERIVED_FACTORY_V1_1.pine`. That parent file was not provided.

---

## 1. Common execution shell (TEST10, TEST11, TEST18)

All three factories run the same frozen shell. Reuse it as the baseline for comparable results.

- Strategy settings:
  - `process_orders_on_close=false`: the signal is computed on a completed bar and the order fills at the next bar's open.
  - `slippage=1` tick.
  - `commission_type=cash_per_contract` and `commission_value=2.24` per side. TEST11's virtual engine uses `ROUND_TRIP_COMMISSION = 4.48`.
  - `pyramiding=0`. `calc_on_every_tick=false` and `use_bar_magnifier=false` are set explicitly in TEST10 and TEST11.
- Chart: exactly 5-minute, enforced with `runtime.error` if `timeframe.in_seconds() != 300`.
- Session: `RTH = "0930-1545:23456"` in `America/New_York`. All state updates only from bars inside this session.
- Entries: at most 1 per day (TEST11: 1 per day per candidate).
- Stop: a catastrophe stop at 2 × ATR, with no take-profit.
  - TEST10/11: 2 × the RTH-bar ATR(14) of 5m bars, converted to ticks: `stopTicks = max(1, int(round(2.0*rthAtr/syminfo.mintick)))`, then `strategy.exit(..., loss=stopTicks)`.
  - TEST18: 2 × the prior-completed-session daily ATR14: `pendingStopDist = max(mintick, ceil(2.0*atrPrev/mintick)*mintick)`.
- Time exit: maximum hold of 120 minutes.
  - TEST10/11: `time_close >= strategy.opentrades.entry_time(0) + 120*60*1000`, then `close_all(immediately=true)`.
  - TEST18: tracks `entryTime := time` on the fill bar instead.
- Hard flat at 15:45 ET:
  - TEST10/11: the bar in `"1540-1545:23456"` triggers `close_all(immediately=true)`, which fills at that bar's close (15:45).
  - TEST18: `hour(time_close)==15 and minute(time_close)==45`, plus a `session.islastbar` safety close.
- Governance path, from the Roadmap LOCK V2:
  1. recent discovery
  2. frozen classification
  3. native confirmation
  4. full history
  5. 4-tick stress
  6. winner concentration (remove top 3 winners)
  7. actual micro economics
  8. portfolio gate

  Further rules: no post-result rescue tuning, and no full-history batch pre-screen. The native TradingView Strategy Tester is the execution and PnL authority. Any change made after seeing results requires a new version.

---

## 2. TEST10 — Survivor-derived factory, full-history V1 (8 markets, 5m)

### 2.1 What was tested and verdict
- There are 20 frozen candidates (T10-01…T10-20), in mirrored LONG/SHORT pairs, across ES/NQ/RTY/YM/BTC/CL/GC/SI.
- This file is a mechanical derivative of V1.1. The file says the "ONLY economic change from native-confirmed V1.1" is that the Stage-1 date gate was removed. Every threshold, trigger, stop, hold rule and the flat rule is unchanged.
- Candidate families:
  - A: PDH/PDL breakout → retest → acceptance
  - B: 30-minute opening range (OR) breakout → retest
  - C: failed acceptance after a prior-day breakout
  - D: gap partial fill fails → continuation
  - E: confirmed 60m trend → 5m pullback recovery
  - F: confirmed 60m trend → failed continuation
  - G: confirmed 30m compression → expansion
  - H: 60m state + prior-day sweep/reclaim
  - I: three-push exhaustion
  - J: previous-week H/L breakout → retest
- **Verdict:** there is no TEST10 review document in the sources, so per-candidate PF and trade counts are **NOT IN SOURCES**. Indirect evidence:
  - The TEST11 Pine names "T11-19 CONTROL T10-04 OR breakdown -> retest reject SHORT" and "T11-20 CONTROL T10-10 60m bear -> 5m bounce rejection SHORT". It calls them "known-positive TEST10 controls".
  - The TEST18 review lists **TS10-S01 and TS10-S02** as active shadows.
  - Which candidates or markets TS10-S01/S02 map to is **NOT IN SOURCES**. TEST22 notes that TS22-S01 (NQ long) overlaps TS10-S02 by about 28.7%, "mostly opposite-direction interaction". That hints TS10-S02 trades NQ, but the sources do not state it.

### 2.2 Mechanisms that survived (inferred)
**T10-04 (OR breakdown → retest reject SHORT)** and **T10-10 (confirmed 60m bear → 5m bounce rejection SHORT)** are called known-positive controls. Exact Pine:

```pine
// T10-04  (window 10:00-13:30)
t04 = w1000_1330 and orDnArmed6 and not na(frozenOrLow) and
      high >= frozenOrLow and close < frozenOrLow and close < open and closeLocation <= 0.40 and
      not na(todRvol) and todRvol >= 0.80
// T10-10  (window 10:30-14:30)
t10 = w1030_1430 and valid60State and last60Bear and
      close[1] > open[1] and close < low[1] and close < open and close < rthVwap and closeLocation <= 0.40 and
      not na(todRvol) and todRvol >= 0.80
```

Both are **short-side** mechanisms. For a long-only MES book, their direct mirrors are T10-03 (OR breakout → retest hold LONG) and T10-09 (60m bull → 5m pullback recovery LONG). The sources do **not** say the mirrors survived.

### 2.3 Mechanisms that failed
No TEST10 results beyond the two controls are in the sources, so no TEST10 candidate can be declared failed from these documents. **NOT IN SOURCES.** Do not treat the absence of evidence as a failure, and do not reopen TEST10 candidates on the assumption that they passed.

### 2.4 Long-side TEST10 definitions (exact, for reference)
```pine
t01 = w1000_1430 and pdhArmed6 and low <= prevRthHigh and close > prevRthHigh and close > open and closeLocation >= 0.60 and todRvol >= 0.80   // PDH breakout->retest hold
t03 = w1000_1330 and orUpArmed6 and low <= frozenOrHigh and close > frozenOrHigh and close > open and closeLocation >= 0.60 and todRvol >= 0.80 // OR breakout->retest hold
t06 = w1000_1330 and pdlArmed6 and close > prevRthLow and close > open and closeLocation >= 0.65                                             // PDL breakdown failed acceptance
t07 = w1000_1130 and gapUpPartialFail and close > todayOpen and close > high[1] and close > open and closeLocation >= 0.65 and todRvol >= 0.80
t09 = w1030_1430 and valid60State and last60Bull and close[1] < open[1] and close > high[1] and close > open and close > rthVwap and closeLocation >= 0.60 and todRvol >= 0.80
t12 = w1030_1430 and valid60State and last60Bear and low < last60Low and close > last60Low and close > open and closeLocation >= 0.65
t13 = w1000_1430 and valid30State and last30Compressed and close > last30High + 0.10*rthAtr and close > open and closeLocation >= 0.70 and todRvol >= 1.00
t15 = w1030_1430 and valid60State and last60Bull and low < prevRthLow and close > prevRthLow and close > open and closeLocation >= 0.60
t18 = w1000_1430 and low[2] > low[1] and low[1] > low and (low[2]-low[1]) > 0 and (low[1]-low) > 0 and (low[1]-low) <= 0.75*(low[2]-low[1]) and close > high[1] and close > open and closeLocation >= 0.65
t19 = w1000_1430 and pwHighArmed12 and low <= prevWeekHigh and close > prevWeekHigh and close > open and closeLocation >= 0.60 and todRvol >= 0.80
```
(Every `todRvol` term above is guarded by `not na(todRvol)` in the source.)

---

## 3. TEST11 — Failed-recovery factory V1 (8 markets, 5m, native + 20 virtual)

### 3.1 What was tested and verdict
- The theme, verbatim: "downside context/event -> attempted recovery -> recovery failure -> continuation".
- There are 20 candidates:
  - T11-01…15: SHORT
  - T11-16/17/18: LONG "falsification / symmetry controls"
  - T11-19/20: the TEST10 known-positive controls, "not new-promotion candidates"
- No hard-coded date gate. Stage 1 uses TradingView's default recent loaded period (about 1Y), and full history uses the same Pine and hash.
- **Verdict: NOT IN SOURCES.** No TEST11 review was provided. Inference: the TEST18 review's active-shadow list (TS10-S01, TS10-S02, TS13-S01, TS16-S01, TS17-S01, TS18-S01, TS18-S02) contains **no TS11 entry**. So as of 2026-09-17, TEST11 produced no active shadow.

### 3.2 Survived
None evidenced. The only "positive" references are the TEST10 controls (§2.2).

### 3.3 Failed or unpromoted (do not reopen as standalone alpha without new evidence)
Inferred from the lack of any promotion. PF numbers are **NOT IN SOURCES**.
- 60m bear followed by failed recovery to VWAP (T11-01), EMA20 (T11-02) or the prior 60m midpoint (T11-03).
- Bearish first-30 impulse followed by failure at the OR midpoint (T11-04).
- Breakdown → reclaim → second rejection, at the OR low (T11-05), PDL (T11-07) or previous-week low (T11-08).
- OR-low breakdown followed by VWAP recovery failure (T11-06).
- Session-low extension followed by a bounce that is rejected (T11-09 at ≥0.75 ATR; T11-10 at ≥1.00 ATR with a diminishing bounce).
- 60m bear followed by three-push recovery exhaustion (T11-11).
- Gap-down partial fill followed by failure at the session open (T11-12).
- 60m bear plus 30m compression below VWAP → expansion (T11-13).
- A ≥1 ATR selloff, then 3-bar compression, then a break (T11-14).
- Down session with a failed VWAP reclaim at high RVOL (T11-15).
- **Long controls with no promotion recorded:** T11-16 (60m bull → VWAP pullback recovery LONG), T11-17 (60m bull → EMA20 pullback recovery LONG), T11-18 (OR-high breakout → inside failure → second acceptance LONG).

T11-16 as defined (for reference only; not validated):
```pine
t16 = w1030_1430 and valid60State and last60Bull and low <= rthVwap and close > rthVwap and close > open and closeLocation >= 0.65 and todRvol >= 0.80
```

### 3.4 New reusable features introduced in TEST11 (exact)
```pine
// frozen at 09:55 bar (first30EndBar = inRth and hh == 9 and mm == 55)
first30BearImpulse := not na(rthAtr) and rthAtr > 0 and close < todayOpen and todayOpen - close >= 0.75 * rthAtr
frozenOrMid = (frozenOrHigh + frozenOrLow) / 2.0
last60Mid   = (last60High + last60Low) / 2.0
// session-low age & extension
dayLowest/dayLowestBar updated when low < dayLowest (reset on first RTH bar)
lowAge2to6  = bar_index - dayLowestBar in [2,6];  lowAge3to7 = [3,7]
downExt075  = todayOpen - dayLowest >= 0.75 * rthAtr;  downExt100 = ... >= 1.00 * rthAtr
// reclaim/failure transition stamps (first occurrence per day, within armed window)
orDnReclaimBar: first bar within 6 bars after orDnBreakBar with close > frozenOrLow
pdlReclaimBar:  first bar within 6 bars after pdlBreakBar with close > prevRthLow
pwLowReclaimBar: within 12 bars after pwLowBreakBar with close > prevWeekLow
orUpFailBar:    first bar within 6 bars after orUpBreakBar with close < frozenOrHigh
// 3-bar compression
comp3 = (max(high[1],high[2],high[3]) - min(low[1],low[2],low[3])) <= 0.75 * rthAtr
```
The mirrored "extension → recovery quality" feature for longs is the sign flip: `high - todayOpen` extension, then the age of the pullback. TEST11 only implements the downside version.

---

## 4. Roadmap LOCK V2 (TEST15-18), dated 2026-09-17

- This is plan and governance only, with no results. The order is TEST15 cross-index (ES/NQ/RTY/YM) → TEST16 open interest regime → TEST17 footprint/delta → TEST18 VWAP acceptance/reclaim/cross-state → stop and discuss. TEST19 and TEST20 are left intentionally unassigned. The earlier COT and overnight-inventory assignments are **dropped** as active items.
- Global rules:
  - 5m for discovery; 15m validation is mandatory for native-confirmed Survivor/Borderline candidates "when meaningful".
  - Hard flat at 15:45 ET. No DCA. One micro per virtual sleeve.
  - Core6 stays frozen.
- TEST15 implementation rules, reusable for any cross-asset feature (for example an NQ/RTY/YM breadth filter on MES):
  - "Time-align ES/NQ/RTY/YM values at the decision timestamp."
  - "Use completed peer bars only."
  - "No future/unconfirmed request.security values."
- TEST15 feature list, all normalized by RTH ATR:
  - 30m and 60m return divided by RTH ATR
  - above/below RTH VWAP
  - VWAP slope over a frozen wall-clock window
  - RTH CLV
  - session H/L break state
  - opening gap divided by prior RTH ATR
  - peer breadth count
  - cross-sectional dispersion
  - relative strength against the peer average
- TEST16 lookahead rule: use prior **confirmed** daily OI only. No intraday OI for CME futures.
- TEST17 prerequisite: `request.footprint()` must be available and have stable history. TradingView's footprint classification is the authority; do not assume exchange-native aggressor truth.
- TEST15, TEST16 and TEST17 results are **NOT IN SOURCES**. The only trace is that shadows TS16-S01 and TS17-S01 exist, and TS16 belongs to an "NQ-long cluster" together with LC05 (TEST18 review).

---

## 5. TEST18 — VWAP state machine (7 markets, 5m, 28 candidates)

### 5.1 What was tested and verdict
- 196 implementations (28 candidates × ES/NQ/RTY/YM/GC/SI/CL). Stage 1: **24 Survivor / 10 Borderline A / 2 Borderline B / 160 Reject**. All 36 required native Strategy Tester files were reviewed.
- "Actual-micro 4t+top3 survivors among all 36", with PF after 4-tick stress and the top 3 winners removed:
  - NQ T18-03 LONG: about 1.060
  - NQ T18-09 LONG: about 1.191
  - NQ T18-23 LONG: about 1.043
  - RTY T18-10 SHORT: about 1.009
  - RTY T18-14 SHORT: about 1.055
  - RTY T18-16 SHORT: about 1.142
  - YM T18-16 SHORT: about 1.025
- YM rejects:
  - T18-14 SHORT: 39 recent trades, PF about 1.534, but 2023+ MYM 4t+top3 PF about 0.869 and net about −$729.94.
  - T18-22 SHORT: 30 trades, PF about 1.454, but remove-best is negative. 2023+ 4t+top3 PF about 0.558.
- **Promoted shadows:**
  - **TS18-S01 = RTY T18-14 SHORT → M2K** ("2σ lower-side VWAP expansion continuation").
    - 2023+ M2K 4t+top3 PF about 1.055.
    - Every year from 2023 to 2026 YTD is positive under 4-tick stress, and the latest 3m, 6m and 12m are positive.
    - Core6 Sharpe-like and MaxDD improve; the worst day is unchanged.
  - **TS18-S02 = RTY T18-16 SHORT → M2K** ("strongly falling RTH VWAP + price still close to VWAP + bearish bar").
    - PF about 1.142.
    - 2024 is slightly negative and the latest 3m is negative.
  - The two are not duplicates:
    - signal-day Jaccard about 13.5%
    - 0 identical entry timestamps
    - daily PnL correlation about 0.13 (common-day correlation about 0.36)
    - position overlap about 20–25%
- **Watches:**
  - T18-W01 NQ T18-09 LONG: robust standalone, but overlaps the LC05/TS16 NQ-long cluster.
  - T18-W02 YM T18-16 SHORT: thin; 2023 and 2024 weak.
  - T18-W03 RTY T18-10 SHORT: thin.
- Stated conclusion: "rejects the simplistic idea that far from VWAP automatically implies mean reversion." The value lies in "VWAP state and transition: slope, one-sided acceptance, distance expansion, band-walk continuation, first-touch rejection, prior-session VWAP transitions, and selected high-cross/chop reversal states."

### 5.2 Survived mechanisms (exact Pine; all gated by `ready`, 10:00 ≤ bar-open time < 14:30)
```pine
ready = signalWindow and not na(atrPrev) and atrPrev > 0 and not na(vwap) and not na(vwapSd) and vwapSd > 0
// LONG (NQ survivors after 4t+top3)
s03 = ready and signedStreak == 8 and slope6Atr >= 0.04                                              // 8th consecutive bar above VWAP + rising VWAP
s09 = ready and cross12 <= 1 and aboveFrac12 >= 10.0/12.0 and z >= 1.0 and z <= 2.0 and slope6Atr >= 0.04 and close > open   // one-sided band-walk (+1..+2σ) continuation
s23 = ready and rthBarCount > 1 and z[1] <= -1.5 and z > -1.0 and close > open                      // snapback from <= -1.5σ back inside -1σ
// SHORT (RTY/YM survivors) — mirrors
s10 = ready and cross12 <= 1 and belowFrac12 >= 10.0/12.0 and z <= -1.0 and z >= -2.0 and slope6Atr <= -0.04 and close < open
s14 = ready and z <= -2.0 and slope6Atr <= -0.07 and close < open and close < low[1]                 // TS18-S01
s16 = ready and distAtr <= 0 and distAtr >= -0.10 and slope6Atr <= -0.04 and close < open            // TS18-S02
```
Long mirrors of the RTY shorts, for MES reference:
- `s13` (z ≥ 2, slope ≥ 0.07, bullish, close > high[1]) mirrors s14.
- `s15` (0 ≤ distAtr ≤ 0.10, slope ≥ 0.04, bullish) mirrors s16.

Neither long mirror appears in the surviving list.

### 5.3 Failed or not promoted (from TEST18)
- Every other candidate/market combination (160 Stage-1 rejects), plus the 36 native files that did not reach the 4t+top3 survivor list.
- The review does not give per-candidate reasons. It does reject, generically, the idea that "far from VWAP ⇒ mean reversion". Candidates s07/s08 (chop fade at ±1σ), s11/s12, s17/s18 (excursion → snapback), and s21/s22 are not in the survivor list for any market.
- Per the roadmap, "simple VWAP stretch/reclaim or overextension/rejection" is already an excluded, previously tested idea. **Do not reopen static VWAP-distance mean reversion as standalone alpha.**
- **ES:** no ES implementation appears among the 7 actual-micro survivors, the shadows or the watches. ES-specific numbers are **NOT IN SOURCES**.

### 5.4 TEST18 feature definitions (exact)
```pine
// Session VWAP & volume-weighted sigma (hlc3), reset at first RTH bar (09:30)
cumV += nz(volume); cumPV += hlc3*nz(volume); cumPV2 += hlc3*hlc3*nz(volume)
vwap     = cumPV / cumV
vwapSd   = sqrt(max(cumPV2/cumV - vwap*vwap, 0))
z        = (close - vwap) / vwapSd
// Week-to-date VWAP: accumulators reset on Monday first RTH bar
wvwap    = weekCumPV / weekCumV
prevDayVwap = last RTH VWAP of prior session (captured at next firstRth)
// ATR: Wilder daily ATR14 over completed RTH sessions (session H/L/C), usable only after 14 sessions
trPrev = max(H-L, |H-prevSessClose|, |L-prevSessClose|);  atr14 = (atr14*13 + trPrev)/14;  atrPrev = atrCount>=14 ? atr14 : na
distAtr          = (close - vwap) / atrPrev
slope6Atr        = (vwap - vwap[6]) / atrPrev                       // 6 bars = 30 min on 5m
spreadChange3Atr = ((close - vwap) - (close[3] - vwap[3])) / atrPrev // 3 bars = 15 min on 5m
side      = close > vwap ? 1 : close < vwap ? -1 : 0
crossUp   = not firstRth and side == 1 and side[1] <= 0
crossDown = not firstRth and side == -1 and side[1] >= 0
cross12   = math.sum(crossEvent ? 1 : 0, 12)     // guarded rthBarCount >= 12
aboveFrac12 = math.sum(side > 0 ? 1 : 0, 12)/12 ; belowFrac12 mirror
signedStreak: +n consecutive bars above, -n below, reset to 0 on side==0, initialised to side at 09:30
failedBearBreak   = crossUp and ((side[1]==-1 and side[2]==1) or (side[1]==-1 and side[2]==-1 and side[3]==1))
failedBullReclaim = crossDown and mirror
```

---

## 6. TEST22 — VWAP-conditioned classic indicators and channel regimes (6 markets, 5m)

### 6.1 What was tested and verdict
- 168 frozen implementations: 6 markets (ES/NQ/RTY/YM/GC/CL) × 14 families × LONG/SHORT. BTC and SI were excluded by policy. The architecture is "parity-certified batched native", with 12 Deep Backtest files. The partial session of 2026-09-18 was excluded.
- Stage 1 (completed 1Y): **13 Survivor / 13 Borderline A / 2 Borderline B / 1 Borderline C / 139 Reject**, so 29 of 168 advanced.
- Stage-1 passes by family:

  | Family | Stage-1 passes |
  |---|---|
  | F10 CCI zero-line continuation | 5 |
  | F11 Keltner breakout continuation | 4 |
  | F1 RSI midline reset | 3 |
  | F3 MACD histogram acceleration | 3 |
  | F4 MACD signal-cross snapback | 3 |
  | F5 ADX/DI continuation | 3 |
  | F8 Bollinger re-entry | 2 |
  | F13 Choppiness release breakout | 2 |
  | F2 RSI extreme VWAP reversion | 1 |
  | F9 Stochastic pullback reset | 1 |
  | F12 Keltner re-entry | 1 |
  | F14 ROC reset | 1 |

- After the 2023+ intended-micro 4-tick + remove-top3 check, **only 3 remain above PF 1**:
  - **TS22-S01 = NQ T22-07 LONG → MNQ** ("MACD signal-cross snapback LONG with VWAP baseline/context"):
    - **Recent Stage 1:** 102 trades, PF about 1.627, both halves positive, still strongly positive with the top 3 removed.
    - **2023+ MNQ 4t:** 369 trades, net +$8,121.32, PF about 1.375. With the top 3 removed: PF about 1.160, net +$3,468.48.
    - **Annual 4t:**

      | Year | Net | PF |
      |---|---|---|
      | 2023 | +$1,083 | about 1.27 |
      | 2024 | +$340 | about 1.07 |
      | 2025 | +$3,411 | about 1.39 |
      | 2026 YTD | +$3,288 | about 1.92 |

    - **Recent windows (4t):**

      | Window | Trades | Net | PF |
      |---|---|---|---|
      | about 3m | 25 | +$1,786 | about 2.87 |
      | about 6m | 50 | +$2,027 | about 1.83 |
      | about 12m | 102 | +$3,305 | about 1.54 |

    - **Rolling:** 6m windows positive about 79% of the time; 12m about 94%.
    - **Full available history:** 1,460 trades. Full 4t PF about 1.075; with the top 3 removed, about 0.985. **Pre-2023 4t PF about 0.858.**
    - Labelled "MODERN-MARKET CONDITIONAL / ALL-ERA THIN".
  - **T22-W01 = NQ T22-05 LONG** (watch):
    - 2023+: 793 trades, 4t net +$3,890, PF about 1.076, 4t+top3 PF about 1.033.
    - Weaknesses: 2025 negative; recent about 3m slightly negative; full 4t+top3 PF about 0.864; adding it lowers portfolio PF and Sharpe and worsens the tail.
  - **T22-W02 = YM T22-19 LONG** (watch):
    - 2023+: 603 trades, 4t net +$1,040, PF about 1.076, 4t+top3 PF about 1.015.
    - Weaknesses: 2026 YTD negative; recent about 3m negative; full 4t+top3 PF about 0.782.
- Portfolio gate. Benchmark: Core6 + Shadow7, 2023-01-01 to 2026-09-15, intended micros, 4t.

  | Metric | Before | After adding TS22-S01 |
  |---|---|---|
  | Net | $28,264.79 | $36,386.11 |
  | PF | 1.3549 | 1.3591 |
  | Sharpe-like | 1.7682 | 1.9672 |
  | MaxDD | −$3,702.25 | −$3,870.24 |
  | Worst day | −$644.94 | −$931.18 |
  | Positive months | 73.3% | 73.3% |
  | Peak gross exposure | 6 | 6 (unchanged) |
  | Peak MNQ gross / absolute net | 3 (absolute net) | 3 / 3 (unchanged) |

  Correlations and overlaps:
  - Correlation with aggregate Main about 0.003; with the MNQ bucket about 0.013.
  - Position overlap: LC03 0.5%, LC04 13.0%, LC05 3.8%, TS10-S02 28.7%, TS16-S01 1.1%.
- Status: "MAIN SHADOW ID + DIRECT-LIVE-ELIGIBLE AT 1 MNQ AFTER EXECUTION MAPPING / ARM AUTHORIZATION. No size >1."

### 6.2 Survived
MACD signal-cross snapback LONG with VWAP context, on **NQ only**. Exact MACD parameters, the VWAP condition, the window and the trigger are **NOT IN SOURCES**, because the TEST22 Pine was not provided. T22-05 and T22-19 family names are also not given in the review.
**Action item:** obtain the TEST22 Pine (Drive) before reusing "MACD signal-cross snapback toward VWAP". Do not reconstruct it from memory.

### 6.3 Failed
- 165 of the 168 implementations are rejected from Main promotion "under V1".
- Several families passed Stage 1 but died under broad-history, 4-tick and top-3 stress: CCI zero-line (5 passes), Keltner breakout (4), RSI midline (3), MACD histogram (3), ADX/DI (3), and others. Do not reopen them as standalone alpha on 5m.
- **ES:** no ES candidate is among the three that stayed above PF 1.

---

## 7. Reusable feature definitions: causal formulas, risks, Pine-safety

`rthAtr` = SMA of the last 14 RTH 5m true ranges (TEST10/11). `atrPrev` = daily Wilder ATR14 from completed sessions (TEST18). Neither uses `request.security`.

| Feature | Exact causal definition (source) | Lookahead / repaint notes | Pine-safe? |
|---|---|---|---|
| RTH VWAP | `hlc3`-weighted, cumulative since the first RTH bar, `nz(volume)` (T10/T11/T18) | Bar-close value; the current bar is included, which is fine at close. It differs from TradingView's built-in `ta.vwap` anchor if the chart includes ETH. | Yes |
| VWAP sigma / z | `sqrt(max(ΣhlcA²·v/Σv − vwap², 0))`; `z=(close−vwap)/sd` (T18) | Early-session sd is tiny, so z explodes at 09:30–10:00. TEST18 only trades from 10:00, which mitigates it. | Yes |
| VWAP slope | `(vwap − vwap[6]) / atrPrev` (T18) | A **bar-count** lag: 6 bars = 30 min on 5m but only 18 min on 3m. The roadmap asks for **fixed wall-clock windows**, so use 10 bars on 3m for 30 min. It needs `rthBarCount > 6` (RTH chart) so it does not reach into the prior session. | Yes |
| Spread change | `((close−vwap) − (close[3]−vwap[3]))/atrPrev` (T18) | Same bar-count caveat. | Yes |
| Cross count / dwell / streak | `cross12`, `aboveFrac12`, `belowFrac12`, `signedStreak` (T18) | **Risk:** `math.sum` sits inside a conditional ternary (`rthBarCount >= 12 ? math.sum(...) : na`). Pine warns that built-ins should be called on every bar; the window may then include prior-session bars early in the day. Safer: compute `math.sum` unconditionally and then gate it. | Yes, with that fix |
| VWAP reclaim / failed reclaim | `crossUp` = side goes from ≤0 to 1 (not on the first bar); `failedBearBreak`/`failedBullReclaim` patterns over side[1..3] (T18) | Causal; uses completed bars only. | Yes |
| Prior-day VWAP transition | `prevDayVwap` = last RTH VWAP of the previous session; s27: `close[1] ≤ prevDayVwap and close > prevDayVwap and close > vwap and slope6Atr ≥ 0` | Causal. | Yes |
| Week-to-date VWAP | Resets on the **Monday** first RTH bar (T18) | **Bug:** on a Monday holiday the week never resets, so two weeks accumulate. Key the reset on a week change instead. | Fix needed |
| PDH/PDL/PDC | Session H/L/C of the prior 09:30–**15:45** RTH window, frozen at the next 09:30 bar (T10/T11) | Not the standard 16:00 close or high/low for index futures; 15:45–16:00 is excluded. It is causal. Be explicit about which definition you use. | Yes |
| Prior-day range close location | `prevRthCloseLoc = (C−L)/(H−L)` (T10/T11, computed but unused) | Causal. | Yes |
| Opening range (30m) | H/L of bars 09:30–10:00; `frozenOrHigh/Low` set on the 09:55 bar (`hh==9 and mm==55`), usable from the 10:00 bar (T10/T11) | Causal. On 3m the last OR bar is 09:57, so change the freeze condition. | Yes |
| Fresh breakout arming | e.g. `close > level + 0.10*rthAtr and close[1] <= level`, first time per day, inside the window; armed for 6 bars (12 for the prev-week level) | Uses a close-confirmed break. `close[1]` on the first bar references the prior session; that is harmless because windows start at 10:00. | Yes |
| Breakout → retest hold | Armed and `low <= level and close > level and close > open and CL >= 0.60 and todRvol >= 0.80` (T10-01/03/19) | Causal. | Yes |
| Failed acceptance | Armed PDH break, then `close < PDH and close < open and CL <= 0.35` (T10-05; T10-06 is the long mirror at `CL >= 0.65`) | Causal. | Yes |
| Previous-week H/L | Week key `year(time,TZ)*100 + weekofyear(time)`; on a key change, the prior RTH-week H/L/C is frozen (T10/T11) | **Risk:** `weekofyear(time)` has no TZ argument while `year()` has one. At a year boundary the key can shift oddly and trigger a spurious rollover. Use a consistent TZ, or detect the week change with `dayofweek`. | Mostly |
| Gap partial-fill failure | `gapUp = todayOpen − prevRthClose ≥ 0.25*prevRthRange`; `fillFrac = (todayOpen − orLow)/gapUp ∈ [0.25, 0.75]` and `orLow > prevRthClose`, evaluated at 09:55 (T10) | The gap is measured against the 15:45 "close", not the settlement. | Yes |
| Three-push exhaustion | Downside: `low[2]>low[1]>low`, push2 ≤ 0.75·push1, `close>high[1]`, bullish, `CL≥0.65` (T10-18); upside mirror T10-17; recovery version T11-10/11 on highs[1..3] | These are 3 consecutive 5m bars, not swing pivots, so no pivot repaint. | Yes |
| Extension → recovery quality | `todayOpen − dayLowest ≥ k·rthAtr` (k = 0.75/1.00), low age within 2–6 or 3–7 bars, bounce structure (T11-09/10) | Causal. | Yes |
| First-30 impulse | `todayOpen − close(09:55) ≥ 0.75·rthAtr` (T11) | Causal after 10:00. | Yes |
| Confirmed 30m/60m bars | Built from 5m bars at minutesFromOpen%30 (or %60) == 0; complete only if count == 6 (or 12); 60m bull = `C>O, |C−O|/range ≥ 0.50, CL ≥ 0.70` (bear: CL ≤ 0.30); valid for ≤ 12 bars (30m: ≤ 6) (T10/T11) | No `request.security` lookahead. The session ends 15:45, so the last 60m block (15:30–15:45) never completes. | Yes |
| 30m compression | `range30 ≤ 0.75 × mean(prior 4 completed 30m ranges)`, rolling across days (T10) | Causal. | Yes |
| Time-of-day RVOL | 75 five-minute slots × 20-day ring; `todRvol = volume / mean(prior ≥10 same-slot volumes)`, **computed before** the current value is inserted (T10/T11) | Causal. On 3m use 125 slots for 09:30–15:45. | Yes |
| Bar close location | `(close − low)/max(high − low, mintick)` | Causal. | Yes |
| RTH-only EMA20/50 | Recursive over RTH bars only, seeded with close, continues across sessions (T10/T11) | Causal. | Yes |
| MACD signal-cross snapback toward VWAP | **NOT IN SOURCES** (TEST22 Pine missing) | — | — |

ATR caveats:
- `rthAtr` (T10/T11) is a 14-bar **5m** ATR that carries across sessions. The first bar's TR includes the overnight gap relative to the previous 15:45 close, so ATR is inflated after gaps.
- The TEST18 daily ATR needs 14 completed sessions of warm-up.
- The two definitions differ by a large factor. A 2× daily-ATR stop is far wider than a 2× 5m-ATR stop, so results are not interchangeable.

---

## 8. Pine-safe implementation patterns worth reusing

1. **Guard rails at `barstate.isfirst`.** Call `runtime.error` for the wrong timeframe, the wrong session (`syminfo.session != "us_regular"`) or an unsupported `syminfo.root` (T18).
2. **Session-scoped state machine.** Use `var` state and reset everything on the first RTH bar: entries, break stamps, OR, VWAP accumulators, day-low tracking. Update only when `inRth`.
3. **Manual higher-timeframe bars from completed lower-timeframe bars.** Add a completeness check (`count == N`) and a freshness window (`bar_index − lastHTFBar ≤ N`). This avoids `request.security` repaint entirely.
4. **Frozen levels at fixed wall-clock bars** (OR at 09:55; prior-day values at 09:30). Downstream logic reads only frozen values.
5. **Event stamps with `bar_index`.** For break, reclaim and fail events: record the first occurrence per day, then use `armedN = bar_index > stamp and bar_index − stamp ≤ N` as the lookback. Expiry is bar-based; convert N for 3m.
6. **Time-of-day RVOL ring buffer.** Keep rolling sums and counts per slot, read the average before inserting today's value, and require a minimum sample count.
7. **Self-identifying order IDs.** `"TEST18|" + syminfo.root + "|" + candidate + "|LONG"` makes exported trade lists joinable across files.
8. **Stops.**
   - TEST10/11 style: `strategy.exit(loss=ticks)` issued in the same call as the entry. It is active from the fill bar.
   - TEST18 style: the stop is armed only after `position_size` becomes nonzero, which leaves the **fill bar unprotected** for one bar.
   - Prefer the TEST10 pattern.
9. **Time exit** via `strategy.opentrades.entry_time(0)` + 120 min, then `close_all(immediately=true)`. **Hard flat** via a session-window bar (`"1540-1545"`) or a `time_close` check, plus a `session.islastbar` backstop.
10. **Embedded multi-candidate virtual simulator** (TEST11). Array state per candidate:
    - Entry: pending → fill at next RTH open ± 1 tick adverse.
    - Stop check first (`low <= stop` for longs), then time/flat exits.
    - Exit prices: stop − 1 tick, or close − 1 tick.
    - `net = (exit − entry)·dir·pointvalue − 4.48`.
    - Exports `SIG_x`/`PNL_x` via `plot(display=display.data_window)` for triage.

    Caveats:
    - It fills gap-through stops at the stop price, which is optimistic.
    - The program treats the native Strategy Tester as the only confirmation authority. This is the "parity-certified batched native" idea that TEST22 scaled up.
11. **Frozen stop distance** is taken from the signal bar's ATR (T11 `frozenStopTicks`; T18 `pendingStopDist`), so the stop does not drift after entry.
12. **No date gate in the Pine.** Stage 1 uses TradingView's default loaded period and full history uses the same file and hash (T11). The earlier date gate (T10 V1.1) was removed to keep a single frozen artifact.

---

## 9. Evidence of market-specific and time-of-day behavior

- **NQ long bias in surviving edges.** Every surviving *long* mechanism in these documents is on NQ:
  - TEST18: T18-03, T18-09, T18-23.
  - TEST22: TS22-S01 (T22-07) and watch T22-05.

  YM long (T22-19) is a thin watch.
- **RTY short bias.** Both TEST18 shadows (TS18-S01, TS18-S02) and watch T18-W03 are RTY shorts. The review calls "RTY short continuation around a falling VWAP state" the most portfolio-useful TEST18 result.
- **YM:** T18-16 SHORT survives thinly. T18-14 and T18-22 SHORT fail on actual micros despite recent PF about 1.53 and 1.45, which shows recent PF does not carry over to the 2023+ micro test.
- **ES:** no ES candidate appears in any survivor, shadow or watch list in TEST18 or TEST22, and no ES numbers are given. For an MES long-only program, **none of the legacy mechanisms here has documented ES evidence.** Treat NQ results as hypotheses to test on ES, not as transferable edges.
- **Era dependence.** TS22-S01 has a pre-2023 4t PF of about 0.858, against about 1.375 for 2023+. Both TS18 shadows are labelled "MODERN-MARKET". Expect regime conditionality and test 2023+ separately from full history.
- **Time of day.** The sources contain design windows only, not measured time-of-day results:
  - TEST10/11 windows: 10:00–14:30, 10:00–13:30 (OR-based), 10:00–11:30 (gap), 10:30–14:30 (60m-state).
  - TEST18 window: 10:00–14:30.
  - Everything is flat by 15:45 ET, with a 120-minute maximum hold.
  - Measured time-of-day effects are **NOT IN SOURCES**.
- **Stress sensitivity.** In TEST22, 29 of 168 passed Stage 1, but only 3 stayed above PF 1 after 4-tick stress plus top-3 removal. In TEST18, only 7 of the 36 natively reviewed files survived the actual-micro 4t+top3 test. Budget for roughly a 5–10× attrition from Stage 1 to a robust result.

---

## 10. Implications for the MES 3m long-only inventory program

1. Reuse the TEST18 VWAP state features (z, slope, dwell, streak, cross count, reclaim/failed reclaim). Convert every bar-count window to wall-clock on 3m: 6 bars at 5m becomes 10 bars at 3m, 12 becomes 20, and 3 becomes 5. Fix the `math.sum`-in-ternary and Monday-reset issues first.
2. The best-evidenced long-side VWAP structures are:
   - one-sided above-VWAP band-walk (+1 to +2σ, rising slope, few crosses): s09
   - sustained above-VWAP streak with rising slope: s03
   - snapback from ≤ −1.5σ back inside −1σ: s23

   All three are **NQ-only** evidence, so they must be revalidated on ES/MES.
3. Do **not** reopen static distance-from-VWAP mean reversion, the TEST11 failed-recovery short family, or generic classic-indicator continuation (CCI, Keltner, RSI midline, ADX) as standalone alpha.
4. Retrieve the TEST22 Pine before using the MACD signal-cross snapback. Its parameters are unknown here.
5. Keep the governance chain: frozen definitions, native Strategy Tester authority, 4-tick stress, top-3 removal, actual-micro economics, a 2023+ vs pre-2023 split, and a portfolio gate reporting Sharpe-like, MaxDD, worst day, overlap and correlation.
