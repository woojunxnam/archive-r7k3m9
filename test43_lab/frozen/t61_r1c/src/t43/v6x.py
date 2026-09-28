"""TEST43 V6X research kernel = exact V5.3.3 kernel + research knobs.

With default knobs this reproduces v533.run_kernel fill-for-fill (enforced by tests).
Original V5.3.3 reference notes follow.


Authority: TEST43_V5_3_3_STEP1_FULL_OVERNIGHT_PARSER_SAFE_PINE
           Drive 1QSyl0DZs3sZnzTlzOQNJ-PDFZSl0fEHcVRvZ11zVWqE
           sha256(text export) 3fdfae6a230398a58819791de207dd90b2d344aea29bc700ba1c7c7ae438e6a8

This is a line-by-line port that preserves the Pine evaluation ORDER inside a
bar.  No logic is improved here.  Execution semantics reproduced:

  * script evaluates on completed 3m bar close (calc_on_every_tick=false)
  * strategy.order market orders fill at the NEXT bar open
    (process_orders_on_close=false), buy +1 tick / sell -1 tick slippage
  * commission $0.62 per contract per fill
  * net position via strategy.order (pyramiding irrelevant)
  * TradingView default FIFO trade matching -> position_avg_price and
    openprofit are computed from the remaining FIFO lots.

Pine ``na`` is represented by NaN (floats) or -1 (bar indices).  NaN
comparisons are False exactly as Pine ``na`` comparisons.
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

# ---------------------------------------------------------------- parameters
PARAM_NAMES = [
    "lotQty", "intradayMaxQty", "enableOvernightTrim", "overnightMaxQty",
    "rsiExtremeLevel", "easyAddRSI", "fastSellRSI", "baseSellRSI",
    "wrExtremeLevel", "easyAddWR",
    "pushesToExhaustion", "pushSpacingATR",
    "bottomRangePct", "microDBLookback", "microDBToleranceATR",
    "strongBullBodyPct", "strongBullClosePct", "strongBullRangeATR",
    "higherLowATR", "breakoutToleranceATR", "continuationATR", "breakoutClosePct",
    "strengthBuildBars", "maxCatchupExtensionATR", "addCooldownBars",
    "oppositeSideCooldownBars", "minimumOppositeMoveATR", "antiStallBars",
    "targetDecayBars",
    "recycleMinTicks", "recycleTPATR", "baseRotateMinTicks", "baseRotateATR", "coreTPATR",
    "repairLookback", "overlayRepairSellTicks", "overlayRepairSellATR",
    "baseRepairSellTicks", "baseRepairSellATR", "lowerRebuyTicks", "lowerRebuyATR",
    "repairLifeBars", "abandonRepairStrengthATR",
    "controlledUpsideBias", "useVWAPLocationBias", "useRangeLocationBias",
    "driftVWAPDeepSigma", "driftVWAPExtremeSigma", "driftRangeLowPct",
    "driftFiveDayLowPct", "driftMinLocationScore", "protectCoreBase",
    "useOneRepairSlot", "useRepairLocationGate", "repairMinVWAPZ",
    "repairMin60Pos", "repairMinSessionPos", "failedRepairRestoreTicks",
    "failedRepairRestoreATR",
    "allowCoreRotation", "coreRotationAgeBars", "coreRotationMinLoss",
    "commission", "slippageTicks", "openprofitIncludesEntryComm",
    "initialCapital", "marginPct", "enforceMargin",
    # ---- research knobs (defaults reproduce V5.3.3 exactly)
    "coreQty", "coreBuildMode", "coreStep", "overnightMode", "regimeLen",
    "rfThreshold", "rfLookback", "repairMin5DPos", "decayMode",
    "profitRefMode", "profitZ", "profitZMinTicks",
    "reductionLock", "rearmATR", "dayStop", "emergencyLoss", "emergencyToCore",
    "regimeMaxQty", "buyStartMod", "buyEndMod", "rollCostPerContract",
    "coreTierMode", "kBase", "kMid", "kTop", "tacticalMode",
    "ddLimit", "ddFloorQty", "ddRearmLen", "pointValue", "disableMask", "maxActionsPerSess",
    # ---- TEST43-P wall-clock time base (defaults = native 3m semantics)
    "barMinutes", "refMinutes", "fillDelayBars",
]
P = {n: i for i, n in enumerate(PARAM_NAMES)}

DEFAULTS = dict(
    lotQty=1, intradayMaxQty=24, enableOvernightTrim=0, overnightMaxQty=24,
    rsiExtremeLevel=15, easyAddRSI=40, fastSellRSI=65, baseSellRSI=78,
    wrExtremeLevel=-90, easyAddWR=-80,
    pushesToExhaustion=3, pushSpacingATR=0.05,
    bottomRangePct=0.35, microDBLookback=10, microDBToleranceATR=0.20,
    strongBullBodyPct=0.60, strongBullClosePct=0.75, strongBullRangeATR=0.80,
    higherLowATR=0.05, breakoutToleranceATR=0.20, continuationATR=0.20, breakoutClosePct=0.60,
    strengthBuildBars=6, maxCatchupExtensionATR=1.00, addCooldownBars=0,
    oppositeSideCooldownBars=2, minimumOppositeMoveATR=0.08, antiStallBars=15,
    targetDecayBars=20,
    recycleMinTicks=12, recycleTPATR=0.12, baseRotateMinTicks=10, baseRotateATR=0.15, coreTPATR=0.60,
    repairLookback=5, overlayRepairSellTicks=8, overlayRepairSellATR=0.08,
    baseRepairSellTicks=16, baseRepairSellATR=0.20, lowerRebuyTicks=10, lowerRebuyATR=0.10,
    repairLifeBars=20, abandonRepairStrengthATR=0.15,
    controlledUpsideBias=1, useVWAPLocationBias=1, useRangeLocationBias=1,
    driftVWAPDeepSigma=1.50, driftVWAPExtremeSigma=2.00, driftRangeLowPct=0.25,
    driftFiveDayLowPct=0.30, driftMinLocationScore=2, protectCoreBase=1,
    useOneRepairSlot=1, useRepairLocationGate=1, repairMinVWAPZ=-1.00,
    repairMin60Pos=0.35, repairMinSessionPos=0.30, failedRepairRestoreTicks=8,
    failedRepairRestoreATR=0.08,
    allowCoreRotation=1, coreRotationAgeBars=20, coreRotationMinLoss=250,
    commission=0.62, slippageTicks=1, openprofitIncludesEntryComm=1,
    initialCapital=150000.0, marginPct=0.10, enforceMargin=0,
    coreQty=0, coreBuildMode=0, coreStep=1, overnightMode=1, regimeLen=20,
    rfThreshold=0.0, rfLookback=20, repairMin5DPos=0.0, decayMode=0,
    profitRefMode=0, profitZ=0.0, profitZMinTicks=4,
    reductionLock=0, rearmATR=0.5, dayStop=0.0, emergencyLoss=0.0, emergencyToCore=1,
    regimeMaxQty=0, buyStartMod=570, buyEndMod=954, rollCostPerContract=0.0,
    coreTierMode=0, kBase=0, kMid=0, kTop=0, tacticalMode=1,
    ddLimit=0.0, ddFloorQty=0, ddRearmLen=20, pointValue=5.0, disableMask=0, maxActionsPerSess=0,
    barMinutes=3, refMinutes=3, fillDelayBars=0,
)

REASONS = [
    "NONE", "REVERSAL_INITIAL", "TREND_INITIAL", "MIXED_INITIAL", "TARGET_TRIM",
    "REPAIR_SELL", "LOWER_REBUY", "FAILED_RESTORE", "BASE_ANTISTALL", "BASE_STRENGTH",
    "DRIFT_BASE", "BASE_PULLBACK", "PROFIT_SELL", "BASE_ROTATE", "CORE_EXIT",
    "OVERLAY_STRENGTH", "DRIFT_OVERLAY", "OVERLAY_PULLBACK", "OVERNIGHT_TRIM",
    "CORE_BUILD", "PROFIT_Z", "DAY_STOP", "EMERGENCY", "REGIME_TRIM",
]
R = {n: i for i, n in enumerate(REASONS)}

COUNTER_NAMES = [
    "buyFillEvents", "sellFillEvents", "boughtContracts", "soldContracts", "maxMESSeen",
    "buyOrderCount", "sellOrderCount", "unfilledOrderCount", "reversalInitialCount",
    "continuationInitialCount", "baseBuildCount", "overlayBuyCount", "antiStallBuyCount",
    "strengthBuyCount", "pullbackBuyCount", "repairBuyCount", "repairSellCount",
    "repairSuccessFillCount", "repairFailedRestoreFillCount", "controlledDriftBuyCount",
    "profitSellCount", "riskSellCount", "overnightTrimCount", "marginRejects",
    "coreBuildOrders", "profitZOrders", "dayStopOrders", "emergencyOrders", "regimeTrimOrders", "rollCost",
    "ddTriggers", "spare31",
]
C = {n: i for i, n in enumerate(COUNTER_NAMES)}


def make_params(**over) -> np.ndarray:
    d = dict(DEFAULTS)
    for k, v in over.items():
        if k not in P:
            raise KeyError(k)
        d[k] = v
    return np.array([float(d[n]) for n in PARAM_NAMES], dtype=np.float64)


# ---------------------------------------------------------------- Pine ta.*
@njit(cache=True)
def pine_rma(x, n):
    out = np.full(x.shape[0], np.nan)
    alpha = 1.0 / n
    s = np.nan
    for i in range(x.shape[0]):
        if math.isnan(s):
            if i >= n - 1:
                ok = True
                acc = 0.0
                for j in range(i - n + 1, i + 1):
                    if math.isnan(x[j]):
                        ok = False
                        break
                    acc += x[j]
                if ok:
                    s = acc / n
        else:
            s = alpha * x[i] + (1 - alpha) * s
        out[i] = s
    return out


@njit(cache=True)
def pine_atr(h, l, c, n):
    tr = np.empty(h.shape[0])
    for i in range(h.shape[0]):
        if i == 0:
            tr[i] = h[i] - l[i]
        else:
            tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    return pine_rma(tr, n)


@njit(cache=True)
def pine_rsi(c, n):
    m = c.shape[0]
    u = np.full(m, np.nan)
    d = np.full(m, np.nan)
    for i in range(1, m):
        u[i] = max(c[i] - c[i - 1], 0.0)
        d[i] = max(c[i - 1] - c[i], 0.0)
    ru = pine_rma(u, n)
    rd = pine_rma(d, n)
    out = np.full(m, np.nan)
    for i in range(m):
        if math.isnan(ru[i]) or math.isnan(rd[i]):
            continue
        if rd[i] == 0.0:
            out[i] = 100.0
        elif ru[i] == 0.0:
            out[i] = 0.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + ru[i] / rd[i])
    return out


@njit(cache=True)
def pine_wpr(h, l, c, n):
    m = c.shape[0]
    out = np.full(m, np.nan)
    for i in range(n - 1, m):
        mx = h[i]
        mn = l[i]
        for j in range(i - n + 1, i + 1):
            mx = max(mx, h[j])
            mn = min(mn, l[j])
        if mx - mn != 0.0:
            out[i] = 100.0 * (c[i] - mx) / (mx - mn)
    return out


@njit(cache=True)
def _wc(x, rmin, bmin):
    """Convert a count of rmin-minute bars to the running bmin-minute bar size (wall-clock)."""
    if x <= 0 or rmin == bmin:
        return x
    return max(1, int(round(x * rmin / bmin)))


@njit(cache=True)
def _nanmax(a, b):
    if math.isnan(a):
        return b
    return max(a, b)


@njit(cache=True)
def _nanmin(a, b):
    if math.isnan(a):
        return b
    return min(a, b)


@njit(cache=True)
def _range_pos(px, lo, hi, mintick):
    w = hi - lo
    if w > mintick:
        return (px - lo) / w
    return 0.5


@njit(cache=True)
def _cmap(L, K, span):
    """Ladder units (V5.3.3 2..24) -> contracts.  Identity when K=0, max=24."""
    return K + int(math.floor(L * span / 24.0 + 0.5))


@njit(cache=True)
def _linv(p, K, span):
    """Contracts -> smallest ladder unit whose mapped size >= p.  Identity when K=0, max=24."""
    if span <= 0:
        return 24
    L = int(math.ceil((p - K) * 24.0 / span - 1e-9))
    if L < 0:
        L = 0
    return L


# ---------------------------------------------------------------- kernel
@njit(cache=True)
def run_kernel(o, h, l, c, v, hh, mm, in_rth, new_rth, prm, sess, mref, roll_day):
    n = o.shape[0]
    MT = 0.25
    PV = prm[97]
    disableMask = int(prm[98])
    maxActs = int(prm[99])
    actCount = 0
    lotQty = int(prm[0]); intradayMaxQty = int(prm[1]); enableOvernightTrim = prm[2] > 0.5
    overnightMaxQty = int(prm[3])
    rsiExtremeLevel = prm[4]; easyAddRSI = prm[5]; fastSellRSI = prm[6]; baseSellRSI = prm[7]
    wrExtremeLevel = prm[8]; easyAddWR = prm[9]
    pushesToExhaustion = int(prm[10]); pushSpacingATR = prm[11]
    bottomRangePct = prm[12]; microDBLookback = int(prm[13]); microDBToleranceATR = prm[14]
    strongBullBodyPct = prm[15]; strongBullClosePct = prm[16]; strongBullRangeATR = prm[17]
    higherLowATR = prm[18]; breakoutToleranceATR = prm[19]; continuationATR = prm[20]
    breakoutClosePct = prm[21]
    strengthBuildBars = int(prm[22]); maxCatchupExtensionATR = prm[23]; addCooldownBars = int(prm[24])
    oppositeSideCooldownBars = int(prm[25]); minimumOppositeMoveATR = prm[26]; antiStallBars = int(prm[27])
    targetDecayBars = int(prm[28])
    recycleMinTicks = prm[29]; recycleTPATR = prm[30]; baseRotateMinTicks = prm[31]
    baseRotateATR = prm[32]; coreTPATR = prm[33]
    repairLookback = int(prm[34]); overlayRepairSellTicks = prm[35]; overlayRepairSellATR = prm[36]
    baseRepairSellTicks = prm[37]; baseRepairSellATR = prm[38]; lowerRebuyTicks = prm[39]
    lowerRebuyATR = prm[40]; repairLifeBars = int(prm[41]); abandonRepairStrengthATR = prm[42]
    controlledUpsideBias = prm[43] > 0.5; useVWAPLocationBias = prm[44] > 0.5
    useRangeLocationBias = prm[45] > 0.5
    driftVWAPDeepSigma = prm[46]; driftVWAPExtremeSigma = prm[47]; driftRangeLowPct = prm[48]
    driftFiveDayLowPct = prm[49]; driftMinLocationScore = int(prm[50]); protectCoreBase = prm[51] > 0.5
    useOneRepairSlot = prm[52] > 0.5; useRepairLocationGate = prm[53] > 0.5; repairMinVWAPZ = prm[54]
    repairMin60Pos = prm[55]; repairMinSessionPos = prm[56]; failedRepairRestoreTicks = prm[57]
    failedRepairRestoreATR = prm[58]
    allowCoreRotation = prm[59] > 0.5; coreRotationAgeBars = int(prm[60]); coreRotationMinLoss = prm[61]
    COMM = prm[62]; SLIP = prm[63] * MT; opIncComm = prm[64] > 0.5
    initCap = prm[65]; marginPct = prm[66]; enforceMargin = prm[67] > 0.5
    K = int(prm[68]); coreBuildMode = int(prm[69]); coreStep = int(prm[70]); overnightMode = int(prm[71])
    regimeLen = int(prm[72]); rfThreshold = prm[73]; rfLookback = int(prm[74]); repairMin5DPos = prm[75]
    decayMode = int(prm[76]); profitRefMode = int(prm[77]); profitZ = prm[78]; profitZMinTicks = prm[79]
    reductionLockOn = prm[80] > 0.5; rearmATR = prm[81]; dayStop = prm[82]; emergencyLoss = prm[83]
    emergencyToCore = prm[84] > 0.5; regimeMaxQty = int(prm[85]); buyStartMod = int(prm[86])
    buyEndMod = int(prm[87]); rollCost = prm[88]
    coreTierMode = int(prm[89]); kBase = int(prm[90]); kMid = int(prm[91]); kTop = int(prm[92])
    tacticalOn = prm[93] > 0.5
    ddLimit = prm[94]; ddFloorQty = int(prm[95]); ddRearmLen = int(prm[96])
    # ---- wall-clock conversion: intraday bar counts are specified in refMinutes-bars (frozen research used 3m)
    # and converted to the running bar size.  Session-count quantities (regimeLen, ddRearmLen) are NOT converted.
    BMIN = int(prm[100]); RMIN = int(prm[101]); FD = int(prm[102])  # FD: TIMING_BRITTLENESS_STRESS only
    microDBLookback = _wc(microDBLookback, RMIN, BMIN); strengthBuildBars = _wc(strengthBuildBars, RMIN, BMIN)
    addCooldownBars = _wc(addCooldownBars, RMIN, BMIN); oppositeSideCooldownBars = _wc(oppositeSideCooldownBars, RMIN, BMIN)
    antiStallBars = _wc(antiStallBars, RMIN, BMIN); targetDecayBars = _wc(targetDecayBars, RMIN, BMIN)
    repairLookback = _wc(repairLookback, RMIN, BMIN); repairLifeBars = _wc(repairLifeBars, RMIN, BMIN)
    coreRotationAgeBars = _wc(coreRotationAgeBars, RMIN, BMIN); rfLookback = _wc(rfLookback, RMIN, BMIN)
    W15 = max(1, int(round(15.0 / BMIN))); W30 = max(1, int(round(30.0 / BMIN))); W60 = max(1, int(round(60.0 / BMIN)))
    RB = 64
    hwm = initCap; ddActive = False
    M = intradayMaxQty
    span = float(M - K)

    atr = pine_atr(h, l, c, 14)
    rsi2 = pine_rsi(c, 2)
    wr2 = pine_wpr(h, l, c, 2)

    # outputs
    pos_arr = np.zeros(n, dtype=np.int64)
    eq_arr = np.zeros(n)
    maxf = n // 2 + 16
    f_bar = np.zeros(maxf, dtype=np.int64)
    f_side = np.zeros(maxf, dtype=np.int64)
    f_qty = np.zeros(maxf, dtype=np.int64)
    f_px = np.zeros(maxf)
    f_reason = np.zeros(maxf, dtype=np.int64)
    f_real = np.zeros(maxf)
    nf = 0
    cnt = np.zeros(32)
    # per-bar diagnostics: target, base, repairPending
    tgt_arr = np.zeros(n, dtype=np.int64)
    base_arr = np.zeros(n, dtype=np.int64)
    # diag columns: 0 vwap,1 vwapStd,2 vwapZ,3 roll15H,4 roll15L,5 roll60H,6 roll60L,7 roll5DH,8 roll5DL,
    # 9 priorRTHHigh,10 priorRTHLow,11 ORH,12 ORL,13 atr,14 rsi2,15 wr2,16 repairPending,17 avgPrice,18 openprofit
    diag = np.full((n, 19), np.nan)

    # FIFO lots
    LMAX = 4096
    lot_px = np.zeros(LMAX)
    lot_q = np.zeros(LMAX, dtype=np.int64)
    lot_head = 0
    lot_tail = 0
    realized = 0.0      # net of all commissions paid on closed portions
    comm_paid = 0.0     # all commissions ever paid
    pos = 0

    # rolling RTH arrays (cap 20) and completed RTH sessions (cap 4)
    rthH = np.zeros(64); rthL = np.zeros(64); rthN = 0
    compH = np.zeros(4); compL = np.zeros(4); compN = 0

    priorRTHHigh = np.nan; priorRTHLow = np.nan
    currentRTHHigh = np.nan; currentRTHLow = np.nan
    openingRangeHigh = np.nan; openingRangeLow = np.nan
    rthCumVolume = 0.0; rthCumPV = 0.0; rthCumP2V = 0.0
    prev_vwapLowerDeep = np.nan; prev_vwapLowerExtreme = np.nan
    downPushes = 0; previousPushLow = np.nan
    prev_rsi = np.nan; prev_wr = np.nan
    prev_strongBull = False

    inventoryActive = False; inventoryStartBar = -1; inventoryLow = np.nan; coreATR = np.nan
    reversalMode = False; continuationMode = False
    activeTargetQty = 2; dayEngineStartBar = -1; lastDecayBar = -1
    buildWindowUntilBar = -1; buildAnchor = np.nan
    pendingInitialOrder = False; pendingInitialBar = -1; pendingInitialLane = 0  # 0 '',1 REV,2 CONT,3 MIXED
    pendingInitialTarget = 2; pendingInitialATR = np.nan
    repairPending = False; repairSellReference = np.nan; repairStartBar = -1; repairRestoreCap = 0
    h2Stage = 0; h2PullbackBar = -1
    sixtyBreakoutSeen = False; sixtyBreakoutLevel = np.nan; sixtyBreakoutBar = -1
    sixtyPullbackHeld = False; sixtyPullbackBar = -1
    continuation1Seen = False; continuation1High = np.nan; continuation1Bar = -1
    continuationPullbackSeen = False; continuationPullbackBar = -1
    lastFillBar = -1; lastBuyFillPrice = np.nan; lastSellFillPrice = np.nan
    lastInventoryActionBar = -1; lastFilledSide = 0  # 1 BUY, -1 SELL
    lastInventoryFillPrice = np.nan; lastBuyFillBar = -1; lastSellFillBar = -1
    pendingOrderSide = 0; pendingOrderReason = 0; pendingOrderQty = 0; pendingOrderBar = -1
    posPrevBar = 0
    # research state
    TMAX = 256
    tac_px = np.zeros(TMAX); tacN = 0          # logical tactical lot ledger (entry fill prices)
    reductionLocked = False; lastReductionPrice = np.nan
    dayStopped = False; emergencyActive = False
    sessStartEq = initCap
    regC = np.zeros(512); regN = 0; lastRTHClose = np.nan
    lastTrimSess = -1
    lastRollSess = -1
    prev_eq = initCap
    ema20 = np.nan; ema50 = np.nan; ema20p = np.nan; ema50p = np.nan; sma200p = np.nan
    tierState = 0

    for i in range(n):
        # ===================== FILL AT THIS BAR'S OPEN (order from bar i-1)
        if pendingOrderBar >= 0 and pendingOrderBar == i - 1 - FD and pendingOrderQty > 0:
            if pendingOrderSide == 1:
                px = o[i] + SLIP
                ok = True
                if enforceMargin:
                    eq_now = initCap + realized
                    for k in range(lot_head, lot_tail):
                        eq_now += (o[i] - lot_px[k]) * PV * lot_q[k]
                    if (pos + pendingOrderQty) * mref[i] * PV * marginPct > eq_now:
                        ok = False
                        cnt[23] += 1
                if ok:
                    q = pendingOrderQty
                    lot_px[lot_tail] = px
                    lot_q[lot_tail] = q
                    lot_tail += 1
                    if lot_tail >= LMAX:  # compact
                        m_ = lot_tail - lot_head
                        for k in range(m_):
                            lot_px[k] = lot_px[lot_head + k]
                            lot_q[k] = lot_q[lot_head + k]
                        lot_head = 0
                        lot_tail = m_
                    for jj in range(q):
                        if pos + jj >= K and tacN < TMAX:
                            tac_px[tacN] = px
                            tacN += 1
                    pos += q
                    comm_paid += q * COMM
                    realized -= q * COMM
                    f_bar[nf] = i; f_side[nf] = 1; f_qty[nf] = q; f_px[nf] = px
                    f_reason[nf] = pendingOrderReason; f_real[nf] = -q * COMM
                    nf += 1
            else:
                px = o[i] - SLIP
                q = min(pendingOrderQty, pos)
                if q > 0:
                    rem = q
                    rp = 0.0
                    while rem > 0:
                        take = min(rem, lot_q[lot_head])
                        rp += (px - lot_px[lot_head]) * PV * take
                        lot_q[lot_head] -= take
                        rem -= take
                        if lot_q[lot_head] == 0:
                            lot_head += 1
                    for jj in range(q):
                        if tacN > 0:
                            kbest = 0
                            for kk in range(1, tacN):
                                if tac_px[kk] > tac_px[kbest]:
                                    kbest = kk
                            tac_px[kbest] = tac_px[tacN - 1]
                            tacN -= 1
                    pos -= q
                    if pos < K:
                        tacN = 0
                    if pendingOrderReason == 4 or pendingOrderReason == 12 or pendingOrderReason == 20:
                        if reductionLockOn:
                            reductionLocked = True
                            lastReductionPrice = px
                    comm_paid += q * COMM
                    realized += rp - q * COMM
                    f_bar[nf] = i; f_side[nf] = -1; f_qty[nf] = q; f_px[nf] = px
                    f_reason[nf] = pendingOrderReason; f_real[nf] = rp - q * COMM
                    nf += 1

        if i == 0 or sess[i] != sess[i - 1]:
            actCount = 0
            sessStartEq = prev_eq
            dayStopped = False
            emergencyActive = False
        if roll_day[i] and sess[i] != lastRollSess:
            lastRollSess = sess[i]
            if pos > 0 and rollCost > 0:
                realized -= pos * rollCost
                cnt[29] += pos * rollCost
        inR = in_rth[i]
        nR = new_rth[i]
        atr_i = atr[i]
        rsi_i = rsi2[i]
        wr_i = wr2[i]

        mod_i = hh[i] * 60 + mm[i]
        # wall-clock: bar CLOSE time vs the frozen 3m-bar-close anchors (identical on 3m bars)
        buyWindow = inR and mod_i >= buyStartMod and mod_i + BMIN <= buyEndMod + RMIN
        trimDecisionBar = mod_i < 972 and mod_i + BMIN >= 972  # first bar closing at/after 16:12
        inOpeningRangeWindow = inR and hh[i] == 9 and mm[i] < 45
        openingRangeReady = inR and (hh[i] > 9 or (hh[i] == 9 and mm[i] >= 45))

        rsiExtreme = rsi_i <= rsiExtremeLevel
        wrExtreme = wr_i <= wrExtremeLevel
        rsiTurnUp = (rsi_i > prev_rsi) and (prev_rsi <= rsiExtremeLevel)
        wrTurnUp = (wr_i > prev_wr) and (prev_wr <= wrExtremeLevel)

        if nR and not math.isnan(lastRTHClose):
            if regN < 512:
                regC[regN] = lastRTHClose; regN += 1
            else:
                for k in range(511):
                    regC[k] = regC[k + 1]
                regC[511] = lastRTHClose
        if nR and not math.isnan(lastRTHClose):
            ema20p = ema20; ema50p = ema50
            ema20 = lastRTHClose if math.isnan(ema20) else (2.0 / 21.0) * lastRTHClose + (1 - 2.0 / 21.0) * ema20
            ema50 = lastRTHClose if math.isnan(ema50) else (2.0 / 51.0) * lastRTHClose + (1 - 2.0 / 51.0) * ema50
            if coreTierMode > 0:
                medium = (not math.isnan(ema50p)) and lastRTHClose > ema50 and ema50 >= ema50p
                strong = medium and ema20 > ema50 and (not math.isnan(ema20p)) and ema20 > ema20p
                bear = False
                if regN >= 201:
                    s200 = 0.0; s200p = 0.0; s50 = 0.0
                    for k in range(regN - 200, regN):
                        s200 += regC[k]
                    for k in range(regN - 201, regN - 1):
                        s200p += regC[k]
                    for k in range(regN - 50, regN):
                        s50 += regC[k]
                    s200 /= 200.0; s200p /= 200.0; s50 /= 50.0
                    bear = lastRTHClose < s200 and s50 < s200 and s200 < s200p
                if bear:
                    K = 0; tierState = 0
                else:
                    K = kBase + (kMid if medium else 0) + (kTop if strong else 0)
                    tierState = 1 + (1 if medium else 0) + (1 if strong else 0)
                K = min(K, M)
                span = float(M - K)
        if nR and ddActive and regN >= ddRearmLen and ddRearmLen > 0:
            smr = 0.0
            for k in range(regN - ddRearmLen, regN):
                smr += regC[k]
            if lastRTHClose > smr / ddRearmLen:
                ddActive = False
                hwm = prev_eq
        bullRegime = True
        if regN >= regimeLen and regimeLen > 0:
            sm = 0.0
            for k in range(regN - regimeLen, regN):
                sm += regC[k]
            bullRegime = c[i] > sm / regimeLen
        # ---------------- NEW RTH PREP
        if nR:
            if not math.isnan(currentRTHHigh):
                priorRTHHigh = currentRTHHigh
                priorRTHLow = currentRTHLow
                if compN < 4:
                    compH[compN] = currentRTHHigh; compL[compN] = currentRTHLow; compN += 1
                else:
                    for k in range(3):
                        compH[k] = compH[k + 1]; compL[k] = compL[k + 1]
                    compH[3] = currentRTHHigh; compL[3] = currentRTHLow
            currentRTHHigh = h[i]; currentRTHLow = l[i]
            openingRangeHigh = h[i]; openingRangeLow = l[i]
            rthN = 0
        elif inR:
            currentRTHHigh = h[i] if math.isnan(currentRTHHigh) else max(currentRTHHigh, h[i])
            currentRTHLow = l[i] if math.isnan(currentRTHLow) else min(currentRTHLow, l[i])
            if inOpeningRangeWindow:
                openingRangeHigh = h[i] if math.isnan(openingRangeHigh) else max(openingRangeHigh, h[i])
                openingRangeLow = l[i] if math.isnan(openingRangeLow) else min(openingRangeLow, l[i])

        # ---------------- VWAP
        src = (h[i] + l[i] + c[i]) / 3.0
        if nR:
            rthCumVolume = v[i]; rthCumPV = v[i] * src; rthCumP2V = v[i] * src * src
        elif inR:
            rthCumVolume += v[i]; rthCumPV += v[i] * src; rthCumP2V += v[i] * src * src
        rthVWAP = np.nan
        rthVWAPStd = np.nan
        if inR and rthCumVolume > 0:
            rthVWAP = rthCumPV / rthCumVolume
            var_ = max(rthCumP2V / rthCumVolume - rthVWAP * rthVWAP, 0.0)
            rthVWAPStd = math.sqrt(var_)
        vwapLowerDeep = rthVWAP - rthVWAPStd * driftVWAPDeepSigma
        vwapLowerExtreme = rthVWAP - rthVWAPStd * driftVWAPExtremeSigma
        vwapZ = 0.0
        if (not math.isnan(rthVWAP)) and (not math.isnan(rthVWAPStd)) and rthVWAPStd > MT:
            vwapZ = (c[i] - rthVWAP) / rthVWAPStd

        # ---------------- RTH rolling levels
        roll15High = np.nan; roll15Low = np.nan; roll30High = np.nan; roll30Low = np.nan
        roll60High = np.nan; roll60Low = np.nan
        if inR and rthN > 0:
            for k in range(max(0, rthN - W60), rthN):
                age = rthN - k  # 1 = most recent
                if age <= W15:
                    roll15High = _nanmax(roll15High, rthH[k]); roll15Low = _nanmin(roll15Low, rthL[k])
                if age <= W30:
                    roll30High = _nanmax(roll30High, rthH[k]); roll30Low = _nanmin(roll30Low, rthL[k])
                roll60High = _nanmax(roll60High, rthH[k]); roll60Low = _nanmin(roll60Low, rthL[k])
        prior4RTHHigh = np.nan; prior4RTHLow = np.nan
        for k in range(compN):
            prior4RTHHigh = _nanmax(prior4RTHHigh, compH[k]); prior4RTHLow = _nanmin(prior4RTHLow, compL[k])
        roll5DHigh = np.nan; roll5DLow = np.nan
        if inR:
            roll5DHigh = currentRTHHigh if math.isnan(prior4RTHHigh) else max(currentRTHHigh, prior4RTHHigh)
            roll5DLow = currentRTHLow if math.isnan(prior4RTHLow) else min(currentRTHLow, prior4RTHLow)

        posPriorRTH = 0.5
        if not math.isnan(priorRTHLow) and not math.isnan(priorRTHHigh):
            posPriorRTH = _range_pos(c[i], priorRTHLow, priorRTHHigh, MT)
        posOpening = 0.5
        if openingRangeReady and not math.isnan(openingRangeLow) and not math.isnan(openingRangeHigh):
            posOpening = _range_pos(c[i], openingRangeLow, openingRangeHigh, MT)
        pos15 = 0.5 if (math.isnan(roll15Low) or math.isnan(roll15High)) else _range_pos(c[i], roll15Low, roll15High, MT)
        pos30 = 0.5 if (math.isnan(roll30Low) or math.isnan(roll30High)) else _range_pos(c[i], roll30Low, roll30High, MT)
        pos60 = 0.5 if (math.isnan(roll60Low) or math.isnan(roll60High)) else _range_pos(c[i], roll60Low, roll60High, MT)
        posCurrentRTH = 0.5
        if inR and not math.isnan(currentRTHLow) and not math.isnan(currentRTHHigh):
            posCurrentRTH = _range_pos(c[i], currentRTHLow, currentRTHHigh, MT)
        pos5D = 0.5
        if inR and not math.isnan(roll5DLow) and not math.isnan(roll5DHigh):
            pos5D = _range_pos(c[i], roll5DLow, roll5DHigh, MT)

        nearPriorRTHLow = inR and (not math.isnan(priorRTHLow)) and posPriorRTH <= bottomRangePct
        nearOpeningLow = openingRangeReady and posOpening <= bottomRangePct
        near15Low = inR and (not math.isnan(roll15Low)) and pos15 <= bottomRangePct
        near30Low = inR and (not math.isnan(roll30Low)) and pos30 <= bottomRangePct
        near60Low = inR and (not math.isnan(roll60Low)) and pos60 <= bottomRangePct

        failedPriorRTHLow = inR and l[i] < priorRTHLow and c[i] > priorRTHLow
        failedOpeningLow = openingRangeReady and l[i] < openingRangeLow and c[i] > openingRangeLow
        failed15Low = inR and l[i] < roll15Low and c[i] > roll15Low
        failed30Low = inR and l[i] < roll30Low and c[i] > roll30Low
        failed60Low = inR and l[i] < roll60Low and c[i] > roll60Low
        anyFailedLowBreak = failedPriorRTHLow or failedOpeningLow or failed15Low or failed30Low or failed60Low

        failedPriorRTHHigh = inR and h[i] > priorRTHHigh and c[i] < priorRTHHigh
        failedOpeningHigh = openingRangeReady and h[i] > openingRangeHigh and c[i] < openingRangeHigh
        failed15High = inR and h[i] > roll15High and c[i] < roll15High
        failed30High = inR and h[i] > roll30High and c[i] < roll30High
        failed60High = inR and h[i] > roll60High and c[i] < roll60High
        anyFailedHighBreak = failedPriorRTHHigh or failedOpeningHigh or failed15High or failed30High or failed60High

        rangeScore = 0
        if nearPriorRTHLow or failedPriorRTHLow: rangeScore += 1
        if nearOpeningLow or failedOpeningLow: rangeScore += 1
        if near15Low or failed15Low: rangeScore += 1
        if near30Low or failed30Low: rangeScore += 1
        if near60Low or failed60Low: rangeScore += 1
        evidenceLocation = inR and rangeScore >= 1

        retestTolerance = atr_i * 0.10
        rangeRetest = inR and ((l[i] <= roll15Low + retestTolerance) or (l[i] <= roll30Low + retestTolerance)
                               or (openingRangeReady and l[i] <= openingRangeLow + retestTolerance))

        # ---------------- down pushes (first reset, then count)
        if nR:
            downPushes = 0
            previousPushLow = np.nan
        low1 = l[i - 1] if i > 0 else np.nan
        high1 = h[i - 1] if i > 0 else np.nan
        close1 = c[i - 1] if i > 0 else np.nan
        bearishPush = inR and c[i] < o[i] and l[i] < low1
        lowerEnough = math.isnan(previousPushLow) or l[i] <= previousPushLow - atr_i * pushSpacingATR
        validDownPush = inR and bearishPush and lowerEnough
        if validDownPush:
            downPushes += 1
            previousPushLow = l[i]

        candleRange = max(h[i] - l[i], MT)
        bodyPct = abs(c[i] - o[i]) / candleRange
        lowerWickPct = (min(o[i], c[i]) - l[i]) / candleRange
        closePct = (c[i] - l[i]) / candleRange

        bottomRejection = inR and lowerWickPct >= 0.25 and closePct >= 0.55
        sellClimax = inR and c[i] < o[i] and candleRange >= atr_i * 1.20 and closePct <= 0.35 and (
            rsiExtreme or wrExtreme or downPushes >= pushesToExhaustion)
        priorMicroLow = np.nan
        if i >= microDBLookback:
            priorMicroLow = l[i - 1]
            for k in range(i - microDBLookback, i):
                priorMicroLow = min(priorMicroLow, l[k])
        microDoubleBottom = inR and (not math.isnan(priorMicroLow)) and abs(l[i] - priorMicroLow) <= atr_i * microDBToleranceATR and c[i] > o[i]

        strongBullBar = inR and c[i] > o[i] and bodyPct >= strongBullBodyPct and closePct >= strongBullClosePct and candleRange >= atr_i * strongBullRangeATR
        bullFollowThrough = inR and prev_strongBull and c[i] > o[i] and c[i] > close1 and c[i] > (high1 + low1) / 2.0

        evidenceExhaustion = inR and (rsiExtreme or wrExtreme or downPushes >= pushesToExhaustion or sellClimax)
        evidenceReversal = inR and (rsiTurnUp or wrTurnUp or bottomRejection or anyFailedLowBreak or c[i] > high1)
        reversalEvidenceCount = (1 if evidenceLocation else 0) + (1 if evidenceExhaustion else 0) + (1 if evidenceReversal else 0)
        reversalProbe = buyWindow and reversalEvidenceCount >= 2
        strongReversalProbe = buyWindow and reversalEvidenceCount == 3

        vwapDeepReclaim = (useVWAPLocationBias and inR and not math.isnan(prev_vwapLowerDeep)) and (
            l[i] <= prev_vwapLowerDeep) and (c[i] > prev_vwapLowerDeep) and (c[i] > o[i] or c[i] > close1)
        vwapExtremeTouch = (useVWAPLocationBias and inR and not math.isnan(prev_vwapLowerExtreme)) and (
            l[i] <= prev_vwapLowerExtreme)
        driftLow60 = useRangeLocationBias and pos60 <= driftRangeLowPct
        driftLowSession = useRangeLocationBias and posCurrentRTH <= driftRangeLowPct
        driftLow5D = useRangeLocationBias and pos5D <= driftFiveDayLowPct
        driftLocationScore = (1 if (useVWAPLocationBias and (vwapZ <= -driftVWAPDeepSigma or vwapDeepReclaim or vwapExtremeTouch)) else 0) \
            + (1 if driftLow60 else 0) + (1 if driftLowSession else 0) + (1 if driftLow5D else 0)
        driftReclaimEvidence = (vwapDeepReclaim or failed60Low or failedPriorRTHLow or bottomRejection) and evidenceReversal
        controlledDriftDip = controlledUpsideBias and driftLocationScore >= driftMinLocationScore
        controlledDriftBuySignal = buyWindow and controlledDriftDip and driftReclaimEvidence
        controlledDriftExtreme = controlledDriftBuySignal and (vwapExtremeTouch or driftLocationScore >= 3)

        freshBreakPriorRTH = buyWindow and c[i] > priorRTHHigh and close1 <= priorRTHHigh
        freshBreakOpening = buyWindow and openingRangeReady and c[i] > openingRangeHigh and close1 <= openingRangeHigh
        freshBreak15 = buyWindow and c[i] > roll15High and close1 <= roll15High
        freshBreak30 = buyWindow and c[i] > roll30High and close1 <= roll30High
        freshBreak60 = buyWindow and c[i] > roll60High and close1 <= roll60High
        goodBreakoutClose = c[i] > o[i] and closePct >= breakoutClosePct
        continuationEntry = buyWindow and ((freshBreakOpening and goodBreakoutClose) or (freshBreak15 and goodBreakoutClose)
                                           or freshBreakPriorRTH or freshBreak30 or freshBreak60
                                           or (bullFollowThrough and c[i] > roll15High))
        strongContinuationEntry = freshBreak60 or freshBreak30 or freshBreakPriorRTH or (freshBreak15 and strongBullBar) or (freshBreakOpening and strongBullBar)

        # ===================== POSITION SNAPSHOT
        posNow = pos
        posPrev = posPrevBar
        actualBuy = posNow > posPrev
        actualSell = posNow < posPrev
        buyOrderSubmitted = False; sellOrderSubmitted = False
        buyOrderReason = 0; sellOrderReason = 0; buyOrderQty = 0; sellOrderQty = 0

        resolvingPendingOrder = pendingOrderBar >= 0 and i > pendingOrderBar + FD
        resolvedOrderSide = pendingOrderSide if resolvingPendingOrder else 0
        resolvedOrderReason = pendingOrderReason if resolvingPendingOrder else 0
        resolvedOrderFilled = resolvingPendingOrder and ((resolvedOrderSide == 1 and actualBuy) or (resolvedOrderSide == -1 and actualSell))
        if resolvingPendingOrder and not resolvedOrderFilled:
            cnt[7] += 1

        if actualBuy:
            cnt[0] += 1
            lastFilledSide = 1
            lastInventoryFillPrice = o[i] + MT
            lastBuyFillBar = i
            cnt[2] += posNow - posPrev
            lastFillBar = i
            lastBuyFillPrice = o[i] + MT
            if resolvedOrderReason == 6:
                cnt[17] += 1
            if resolvedOrderReason == 7:
                cnt[18] += 1
            if resolvedOrderReason == 10 or resolvedOrderReason == 16:
                cnt[19] += 1
            if posPrev == 0:
                inventoryActive = True
                inventoryStartBar = i
                inventoryLow = l[i]
                coreATR = atr_i if math.isnan(pendingInitialATR) else pendingInitialATR
                activeTargetQty = max(_linv(posNow, K, span), pendingInitialTarget)
                reversalMode = pendingInitialLane == 1 or pendingInitialLane == 3
                continuationMode = pendingInitialLane == 2 or pendingInitialLane == 3
                buildWindowUntilBar = i + strengthBuildBars
                buildAnchor = lastBuyFillPrice
                lastDecayBar = i
                pendingInitialOrder = False; pendingInitialBar = -1; pendingInitialLane = 0
                pendingInitialTarget = 2; pendingInitialATR = np.nan
            if repairPending and posNow >= repairRestoreCap:
                repairPending = False; repairSellReference = np.nan; repairStartBar = -1; repairRestoreCap = 0
        if actualSell:
            cnt[1] += 1
            lastFilledSide = -1
            lastInventoryFillPrice = o[i] - MT
            lastSellFillBar = i
            cnt[3] += posPrev - posNow
            lastFillBar = i
            lastSellFillPrice = o[i] - MT
            if resolvedOrderReason == 5:
                cnt[16] += 1
                repairPending = True
                repairSellReference = lastSellFillPrice
                repairStartBar = i
        if resolvingPendingOrder:
            pendingOrderSide = 0; pendingOrderReason = 0; pendingOrderQty = 0; pendingOrderBar = -1
        cnt[4] = max(cnt[4], abs(posNow))

        if pendingInitialOrder and pendingInitialBar >= 0 and i > pendingInitialBar and posNow == 0:
            pendingInitialOrder = False; pendingInitialBar = -1; pendingInitialLane = 0
            pendingInitialTarget = 2; pendingInitialATR = np.nan

        if posNow == 0 and posPrev > 0:
            inventoryActive = False; inventoryStartBar = -1; inventoryLow = np.nan; coreATR = np.nan
            activeTargetQty = 2; continuationMode = False; reversalMode = False
            h2Stage = 0; h2PullbackBar = -1
            sixtyBreakoutSeen = False; sixtyBreakoutLevel = np.nan; sixtyBreakoutBar = -1
            sixtyPullbackHeld = False; sixtyPullbackBar = -1
            continuation1Seen = False; continuation1High = np.nan; continuation1Bar = -1
            continuationPullbackSeen = False; continuationPullbackBar = -1
            buildWindowUntilBar = -1; buildAnchor = np.nan
            repairPending = False; repairSellReference = np.nan; repairStartBar = -1; repairRestoreCap = 0

        if posNow > 0 and not inventoryActive:
            inventoryActive = True
            inventoryStartBar = i
            inventoryLow = l[i]
            coreATR = atr_i
            activeTargetQty = max(2, _linv(posNow, K, span))
            lastDecayBar = i

        if nR:
            dayEngineStartBar = i
            downPushes = 0
            previousPushLow = np.nan
            h2Stage = 0; h2PullbackBar = -1
            sixtyBreakoutSeen = False; sixtyBreakoutLevel = np.nan; sixtyBreakoutBar = -1
            sixtyPullbackHeld = False; sixtyPullbackBar = -1
            continuation1Seen = False; continuation1High = np.nan; continuation1Bar = -1
            continuationPullbackSeen = False; continuationPullbackBar = -1
            continuationMode = False; reversalMode = False
            buildWindowUntilBar = -1; buildAnchor = np.nan
            if posNow > 0:
                activeTargetQty = max(2, _linv(posNow, K, span))
            else:
                activeTargetQty = 2
            lastDecayBar = i

        repairAge = (i - repairStartBar) if (repairPending and repairStartBar >= 0) else 0
        inventoryLive = inventoryActive and posNow > 0
        inventoryAge = (i - inventoryStartBar) if (inventoryLive and inventoryStartBar >= 0) else 0
        if inventoryLive:
            inventoryLow = l[i] if math.isnan(inventoryLow) else min(inventoryLow, l[i])

        # FIFO-derived position stats (TradingView semantics)
        avgPrice = np.nan
        openprofit = 0.0
        if posNow > 0:
            sq = 0.0
            spq = 0.0
            for k in range(lot_head, lot_tail):
                sq += lot_q[k]
                spq += lot_px[k] * lot_q[k]
                openprofit += (c[i] - lot_px[k]) * PV * lot_q[k]
            avgPrice = spq / sq
            if opIncComm:
                openprofit -= sq * COMM

        # ---------------- H2
        bullAttempt = inventoryLive and inR and c[i] > high1 and c[i] > o[i]
        h2Event = False
        if inventoryLive and inR:
            if h2Stage == 0 and bullAttempt:
                h2Stage = 1
            elif h2Stage == 1:
                h2PullbackEvent = l[i] < low1 or c[i] < close1
                if h2PullbackEvent and h2PullbackBar < 0:
                    h2PullbackBar = i
                if h2PullbackBar >= 0 and i > h2PullbackBar and bullAttempt:
                    h2Event = True
                    h2Stage = 2

        prior2High = np.nan
        if i >= 2:
            prior2High = max(h[i - 1], h[i - 2])
        higherLowBreak = inventoryLive and inR and (not math.isnan(inventoryLow)) and l[i] >= inventoryLow + atr_i * higherLowATR and c[i] > prior2High

        if inventoryLive and inR and (not sixtyBreakoutSeen) and (freshBreak60 or (c[i] > roll60High)):
            sixtyBreakoutSeen = True
            sixtyBreakoutLevel = roll60High
            sixtyBreakoutBar = i

        sixtyPullbackEvent = False
        if inventoryLive and inR and sixtyBreakoutSeen and (not sixtyPullbackHeld) and sixtyBreakoutBar >= 0 and i > sixtyBreakoutBar:
            sixtyTolerance = atr_i * breakoutToleranceATR
            sixtyTouched = l[i] <= sixtyBreakoutLevel + sixtyTolerance and l[i] >= sixtyBreakoutLevel - sixtyTolerance
            sixtyHeld = c[i] > sixtyBreakoutLevel
            if sixtyTouched and sixtyHeld and c[i] > o[i]:
                sixtyPullbackHeld = True
                sixtyPullbackBar = i
                sixtyPullbackEvent = True

        continuation1Event = inventoryLive and inR and sixtyPullbackHeld and (not continuation1Seen) and sixtyPullbackBar >= 0 \
            and i > sixtyPullbackBar and c[i] > o[i] and c[i] > high1 and c[i] >= sixtyBreakoutLevel + atr_i * continuationATR
        if continuation1Event:
            continuation1Seen = True
            continuation1High = h[i]
            continuation1Bar = i

        if inventoryLive and inR and continuation1Seen and (not continuationPullbackSeen) and i > continuation1Bar:
            if l[i] < low1 or c[i] < close1:
                continuationPullbackSeen = True
                continuationPullbackBar = i

        continuation2Event = inventoryLive and inR and continuationPullbackSeen and continuationPullbackBar >= 0 \
            and i > continuationPullbackBar and c[i] > o[i] and c[i] > high1 and (not math.isnan(continuation1High)) and c[i] > continuation1High

        # ---------------- TARGET ENGINE
        targetBefore = activeTargetQty
        freshStructuralEvidence = False
        if inventoryLive and inR:
            if reversalEvidenceCount == 3 and activeTargetQty < 4:
                activeTargetQty = 4; reversalMode = True; freshStructuralEvidence = True
            if (anyFailedLowBreak or bottomRejection) and activeTargetQty < 6:
                activeTargetQty = 6; reversalMode = True; freshStructuralEvidence = True
            if (microDoubleBottom or h2Event) and activeTargetQty < 8:
                activeTargetQty = 8; reversalMode = True; freshStructuralEvidence = True
            if bullFollowThrough and activeTargetQty < 10:
                activeTargetQty = 10; freshStructuralEvidence = True
            if higherLowBreak and activeTargetQty < 12:
                activeTargetQty = 12; freshStructuralEvidence = True
            if freshBreakOpening and activeTargetQty < 10:
                activeTargetQty = 10; continuationMode = True; freshStructuralEvidence = True
            if freshBreak15 and activeTargetQty < 12:
                activeTargetQty = 12; continuationMode = True; freshStructuralEvidence = True
            if freshBreakPriorRTH and activeTargetQty < 14:
                activeTargetQty = 14; continuationMode = True; freshStructuralEvidence = True
            if freshBreak30 and activeTargetQty < 16:
                activeTargetQty = 16; continuationMode = True; freshStructuralEvidence = True
            if freshBreak60 and activeTargetQty < 18:
                activeTargetQty = 18; continuationMode = True; freshStructuralEvidence = True
            if sixtyPullbackEvent and activeTargetQty < 20:
                activeTargetQty = 20; continuationMode = True; freshStructuralEvidence = True
            if continuation1Event and activeTargetQty < 22:
                activeTargetQty = 22; continuationMode = True; freshStructuralEvidence = True
            if continuation2Event and activeTargetQty < 24:
                activeTargetQty = 24; continuationMode = True; freshStructuralEvidence = True
        activeTargetQty = min(activeTargetQty, 24)
        targetRaisedThisBar = activeTargetQty > targetBefore
        if inventoryLive and inR and freshStructuralEvidence:
            lastDecayBar = i
            buildWindowUntilBar = i + strengthBuildBars
            buildAnchor = c[i]

        if decayMode != 2 and inventoryLive and inR and lastDecayBar >= 0 and i - lastDecayBar >= targetDecayBars and activeTargetQty > 2:
            activeTargetQty = max(2, activeTargetQty - 2)
            lastDecayBar = i

        baseGoal = min(int(math.ceil(activeTargetQty / 4.0)) * 2, activeTargetQty)
        tgtC = _cmap(activeTargetQty, K, span)
        baseC = _cmap(baseGoal, K, span)

        continuationInitialTarget = 18 if freshBreak60 else (16 if freshBreak30 else (14 if freshBreakPriorRTH else (
            12 if freshBreak15 else (10 if freshBreakOpening else 8))))

        # ---------------- INITIAL ORDER
        reversalInitialSignal = (posNow == 0 and not pendingInitialOrder) and (reversalProbe or controlledDriftBuySignal)
        continuationInitialSignal = posNow == 0 and (not pendingInitialOrder) and continuationEntry
        if reversalInitialSignal or continuationInitialSignal:
            mixedInitial = reversalInitialSignal and continuationInitialSignal
            strongInitial = strongReversalProbe or strongContinuationEntry or mixedInitial or controlledDriftExtreme
            buyOrderSubmitted = True
            buyOrderQty = min(4, intradayMaxQty) if strongInitial else lotQty
            buyOrderReason = 3 if mixedInitial else (2 if continuationInitialSignal else 1)
            pendingInitialOrder = True
            pendingInitialBar = i
            pendingInitialLane = 3 if mixedInitial else (2 if continuationInitialSignal else 1)
            if mixedInitial:
                pendingInitialTarget = max(4 if strongReversalProbe else 2, continuationInitialTarget)
            elif continuationInitialSignal:
                pendingInitialTarget = continuationInitialTarget
            else:
                pendingInitialTarget = 4 if strongReversalProbe else 2
            if controlledDriftExtreme:
                pendingInitialTarget = max(pendingInitialTarget, 8)
            pendingInitialTarget = min(pendingInitialTarget, 24)
            pendingInitialATR = atr_i
            if mixedInitial:
                cnt[8] += 1; cnt[9] += 1
            elif continuationInitialSignal:
                cnt[9] += 1
            else:
                cnt[8] += 1

        # ---------------- BUY TRIGGERS
        easyPullback = inR and (rsi_i <= easyAddRSI or wr_i <= easyAddWR or rangeRetest or l[i] < low1 or validDownPush or anyFailedLowBreak)
        strengthEvent = inR and (strongBullBar or bullFollowThrough or freshBreakOpening or freshBreak15 or freshBreakPriorRTH
                                 or freshBreak30 or freshBreak60 or h2Event or higherLowBreak or sixtyPullbackEvent
                                 or continuation1Event or continuation2Event)
        buildWindowActive = inventoryLive and inR and buildWindowUntilBar >= 0 and i <= buildWindowUntilBar
        continuationCatchupHold = continuationMode and buildWindowActive and (not anyFailedHighBreak) and (not math.isnan(buildAnchor)) \
            and c[i] >= buildAnchor - atr_i * 0.25 and c[i] <= buildAnchor + atr_i * maxCatchupExtensionATR and (c[i] > o[i] or c[i] >= close1)
        addCooldownOK = lastInventoryActionBar < 0 or i - lastInventoryActionBar > addCooldownBars

        repairLowerGap = max(atr_i * lowerRebuyATR, MT * lowerRebuyTicks)
        repairPriceLower = repairPending and (not math.isnan(repairSellReference)) and l[i] <= repairSellReference - repairLowerGap
        repairAddSignal = (inventoryLive and buyWindow and repairPending and repairPriceLower) and (
            posNow < repairRestoreCap and posNow + lotQty <= repairRestoreCap and posNow + lotQty <= intradayMaxQty) and (
            easyPullback or evidenceReversal or continuationEntry or controlledDriftBuySignal)

        barsWithoutFillForSignal = (i - lastFillBar) if lastFillBar >= 0 else 1000000
        antiStallContinuationOK = continuationMode and (not anyFailedHighBreak) and c[i] >= o[i]
        antiStallReversalOK = reversalMode and reversalEvidenceCount >= 2 and (bottomRejection or anyFailedLowBreak or c[i] > close1)
        antiStallBaseSignal = inventoryLive and buyWindow and posNow < baseC and posNow + lotQty <= baseC \
            and posNow + lotQty <= tgtC and barsWithoutFillForSignal >= antiStallBars and addCooldownOK \
            and (antiStallContinuationOK or antiStallReversalOK)

        driftPullbackPermission = (not controlledUpsideBias) or (controlledDriftDip or vwapZ <= -0.50 or pos60 <= bottomRangePct or posCurrentRTH <= bottomRangePct)
        baseBuildSignal = (inventoryLive and buyWindow and posNow < baseC and posNow + lotQty <= baseC
                           and posNow + lotQty <= tgtC and addCooldownOK) and (
            (easyPullback and driftPullbackPermission) or targetRaisedThisBar or strengthEvent or continuationCatchupHold
            or antiStallBaseSignal or controlledDriftBuySignal)
        if reductionLocked:
            if nR or posNow <= baseC or c[i] <= lastReductionPrice - rearmATR * atr_i:
                reductionLocked = False
        overlayBuySignal = (not reductionLocked) and (inventoryLive and buyWindow and posNow >= baseC and posNow < tgtC
                            and posNow + lotQty <= tgtC and addCooldownOK) and (
            (easyPullback and driftPullbackPermission) or strengthEvent or controlledDriftBuySignal)

        overlayProfitMove = max(atr_i * recycleTPATR, MT * recycleMinTicks)
        baseRotationMove = max(atr_i * baseRotateATR, MT * baseRotateMinTicks)
        profRef = lastBuyFillPrice
        if profitRefMode != 0 and tacN > 0:
            hi_ = tac_px[0]; lo_ = tac_px[0]; sm_ = 0.0
            for kk in range(tacN):
                hi_ = max(hi_, tac_px[kk]); lo_ = min(lo_, tac_px[kk]); sm_ += tac_px[kk]
            if profitRefMode == 1:
                profRef = hi_
            elif profitRefMode == 2:
                profRef = lo_
            else:
                profRef = sm_ / tacN
        overlayProfitSell = inventoryLive and inR and posNow > baseC and (not math.isnan(profRef)) and (
            c[i] >= profRef + overlayProfitMove or (rsi_i >= fastSellRSI and c[i] > profRef))
        profitZSell = profitZ > 0 and inventoryLive and inR and posNow > baseC and (not math.isnan(profRef)) and \
            vwapZ >= profitZ and c[i] >= profRef + profitZMinTicks * MT
        baseProfitRotationSell = (inventoryLive and inR and posNow >= 4 and posNow <= baseC) and (not protectCoreBase) and (
            c[i] >= avgPrice + baseRotationMove) and (rsi_i >= baseSellRSI or anyFailedHighBreak)
        recentLow = l[i]
        for k in range(max(0, i - repairLookback + 1), i + 1):
            recentLow = min(recentLow, l[k])
        if i < repairLookback - 1:
            recentLow = np.nan
        overlayRepairMove = max(atr_i * overlayRepairSellATR, MT * overlayRepairSellTicks)
        baseRepairMove = max(atr_i * baseRepairSellATR, MT * baseRepairSellTicks)
        requiredRepairMove = baseRepairMove if posNow <= baseC else overlayRepairMove
        meaningfulRepairRebound = inR and c[i] - recentLow >= requiredRepairMove
        reboundEvidence = inR and (rsi_i > prev_rsi or wr_i > prev_wr or c[i] > o[i] or c[i] > high1)
        underwater = inventoryLive and openprofit < 0
        coreRotationEligible = allowCoreRotation and (not protectCoreBase) and posNow == lotQty and inventoryAge >= coreRotationAgeBars \
            and openprofit <= -coreRotationMinLoss
        repairSlotAvailable = (not useOneRepairSlot) or (not repairPending)
        repairBaseFloorOK = (not protectCoreBase) or (posNow - lotQty >= baseC)
        repairLocationRecovered = (not useRepairLocationGate) or (vwapZ >= repairMinVWAPZ and pos60 >= repairMin60Pos and posCurrentRTH >= repairMinSessionPos)
        repairLocationRecovered = repairLocationRecovered and pos5D >= repairMin5DPos
        rfOK = True
        if rfThreshold > 0 and posNow > 0:
            rl_ = l[i]
            for kk in range(max(0, i - rfLookback + 1), i + 1):
                rl_ = min(rl_, l[kk])
            rf_ = (c[i] - rl_) / max(avgPrice - rl_, MT)
            rfOK = rf_ >= rfThreshold
        underwaterSellSignal = (inventoryLive and inR and underwater and meaningfulRepairRebound and reboundEvidence and rfOK) and (
            repairSlotAvailable and repairBaseFloorOK and repairLocationRecovered) and (posNow > lotQty or coreRotationEligible)
        failedHighSellSignal = (inventoryLive and inR and anyFailedHighBreak and posNow > lotQty) and (
            repairSlotAvailable and repairBaseFloorOK and repairLocationRecovered) and (
            c[i] < o[i] or rsi_i >= fastSellRSI or h[i] - c[i] >= candleRange * 0.35)
        excessTargetSellSignal = decayMode != 3 and inventoryLive and inR and posNow > tgtC and reboundEvidence
        coreProfitExit = (inventoryLive and inR and posNow == lotQty and activeTargetQty <= 2 and not protectCoreBase) and (
            (not math.isnan(coreATR)) and c[i] >= avgPrice + coreATR * coreTPATR)

        failedRepairRestoreMove = max(atr_i * failedRepairRestoreATR, MT * failedRepairRestoreTicks)
        strengthInvalidatesRepair = (repairPending and inR and (not math.isnan(repairSellReference)) and strengthEvent) and (
            c[i] >= repairSellReference + atr_i * abandonRepairStrengthATR)
        repairPriceFailedHigher = (repairPending and inR and not math.isnan(repairSellReference)) and (
            c[i] >= repairSellReference + failedRepairRestoreMove)
        repairTimedOut = repairPending and repairAge >= repairLifeBars
        repairLateSessionRestore = (repairPending and inR and hh[i] == 15) and (mod_i + BMIN >= 951)
        failedRepairRestoreSignal = (inventoryLive and inR and repairPending and posNow < repairRestoreCap
                                     and posNow + lotQty <= repairRestoreCap and posNow + lotQty <= intradayMaxQty) and (
            repairPriceFailedHigher or strengthInvalidatesRepair or repairTimedOut or repairLateSessionRestore)

        sellAfterBuyBarsOK = lastBuyFillBar < 0 or i - lastBuyFillBar >= oppositeSideCooldownBars
        buyAfterSellBarsOK = lastSellFillBar < 0 or i - lastSellFillBar >= oppositeSideCooldownBars
        oppositeMoveFloor = max(atr_i * minimumOppositeMoveATR, MT * 4)
        sellAfterBuyPriceOK = lastFilledSide != 1 or math.isnan(lastInventoryFillPrice) or c[i] >= lastInventoryFillPrice + oppositeMoveFloor
        buyAfterSellPriceOK = lastFilledSide != -1 or math.isnan(lastInventoryFillPrice) or c[i] <= lastInventoryFillPrice - oppositeMoveFloor or freshStructuralEvidence
        normalSellChurnOK = sellAfterBuyBarsOK and sellAfterBuyPriceOK
        normalBuyChurnOK = buyAfterSellBarsOK and buyAfterSellPriceOK

        # ---------------- ONE ACTION PER BAR
        if inventoryLive and inR and (not buyOrderSubmitted) and (not sellOrderSubmitted):
            if excessTargetSellSignal:
                sellOrderSubmitted = True; sellOrderQty = min(lotQty, posNow); sellOrderReason = 4; cnt[21] += 1
            elif failedHighSellSignal:
                sellOrderSubmitted = True; sellOrderQty = min(lotQty, posNow); sellOrderReason = 5
                repairRestoreCap = posNow; cnt[21] += 1
            elif underwaterSellSignal:
                sellOrderSubmitted = True; sellOrderQty = min(lotQty, posNow); sellOrderReason = 5
                repairRestoreCap = posNow; cnt[21] += 1
            elif repairAddSignal:
                buyOrderSubmitted = True; buyOrderQty = lotQty; buyOrderReason = 6; cnt[15] += 1
            elif failedRepairRestoreSignal:
                buyOrderSubmitted = True; buyOrderQty = lotQty; buyOrderReason = 7; cnt[15] += 1
            elif baseBuildSignal and normalBuyChurnOK:
                buyOrderSubmitted = True; buyOrderQty = lotQty
                if antiStallBaseSignal:
                    buyOrderReason = 8; cnt[12] += 1
                elif continuationCatchupHold or strengthEvent:
                    buyOrderReason = 9; cnt[13] += 1
                elif controlledDriftBuySignal:
                    buyOrderReason = 10; cnt[14] += 1
                else:
                    buyOrderReason = 11; cnt[14] += 1
                cnt[10] += 1
            elif overlayProfitSell and normalSellChurnOK:
                sellOrderSubmitted = True; sellOrderQty = lotQty; sellOrderReason = 12; cnt[20] += 1
            elif profitZSell and normalSellChurnOK:
                sellOrderSubmitted = True; sellOrderQty = lotQty; sellOrderReason = 20; cnt[20] += 1; cnt[25] += 1
            elif baseProfitRotationSell and normalSellChurnOK:
                sellOrderSubmitted = True; sellOrderQty = lotQty; sellOrderReason = 13; cnt[20] += 1
            elif coreProfitExit and normalSellChurnOK:
                sellOrderSubmitted = True; sellOrderQty = lotQty; sellOrderReason = 14; cnt[20] += 1
            elif overlayBuySignal and normalBuyChurnOK:
                buyOrderSubmitted = True; buyOrderQty = lotQty
                if strengthEvent:
                    buyOrderReason = 15; cnt[13] += 1
                elif controlledDriftBuySignal:
                    buyOrderReason = 16; cnt[14] += 1
                else:
                    buyOrderReason = 17; cnt[14] += 1
                cnt[11] += 1

        if not tacticalOn:
            buyOrderSubmitted = False
            sellOrderSubmitted = False
            if inR and posNow > K:
                sellOrderSubmitted = True; sellOrderQty = posNow - K; sellOrderReason = 23; cnt[28] += 1
        if dayStopped or emergencyActive:
            buyOrderSubmitted = False
        if coreBuildMode > 0 and posNow < K and inR and buyWindow and (not buyOrderSubmitted) and (not sellOrderSubmitted) \
                and (not dayStopped) and (not emergencyActive):
            okCore = True
            if coreBuildMode == 2:
                okCore = (easyPullback and driftPullbackPermission) or controlledDriftBuySignal
            if okCore:
                buyOrderSubmitted = True; buyOrderQty = min(coreStep, K - posNow); buyOrderReason = 19; cnt[24] += 1
        Meff = M
        if regimeMaxQty > 0 and not bullRegime:
            Meff = min(M, regimeMaxQty)
            if inR and posNow > max(Meff, K) and (not sellOrderSubmitted):
                buyOrderSubmitted = False
                sellOrderSubmitted = True; sellOrderQty = lotQty; sellOrderReason = 23; cnt[28] += 1
        if overnightMode == 2 or (overnightMode == 3 and not bullRegime):
            trimNow = (inR and mod_i + BMIN >= 960) or ((not inR) and i > 0 and in_rth[i - 1])
            if trimNow and posNow > K and lastTrimSess != sess[i]:
                lastTrimSess = sess[i]
                buyOrderSubmitted = False
                sellOrderSubmitted = True; sellOrderQty = posNow - K; sellOrderReason = 18; cnt[22] += 1
        if ddLimit > 0:
            eqg = initCap + realized
            for k in range(lot_head, lot_tail):
                eqg += (c[i] - lot_px[k]) * PV * lot_q[k]
            if not ddActive:
                hwm = max(hwm, eqg)
                if hwm - eqg >= ddLimit:
                    ddActive = True
                    cnt[30] += 1
            if ddActive:
                buyOrderSubmitted = False
                if posNow > ddFloorQty:
                    sellOrderSubmitted = True; sellOrderQty = posNow - ddFloorQty; sellOrderReason = 22
        if dayStop > 0 and (not dayStopped) and posNow > K:
            eqc = initCap + realized
            for k in range(lot_head, lot_tail):
                eqc += (c[i] - lot_px[k]) * PV * lot_q[k]
            if eqc - sessStartEq <= -dayStop:
                dayStopped = True
                buyOrderSubmitted = False
                sellOrderSubmitted = True; sellOrderQty = posNow - K; sellOrderReason = 21; cnt[26] += 1
        if emergencyLoss > 0 and (not emergencyActive) and posNow > 0 and openprofit <= -emergencyLoss:
            floorQ = K if emergencyToCore else 0
            if posNow > floorQ:
                emergencyActive = True
                buyOrderSubmitted = False
                sellOrderSubmitted = True; sellOrderQty = posNow - floorQ; sellOrderReason = 22; cnt[27] += 1
        if (overnightMode == 0 or enableOvernightTrim) and trimDecisionBar and posNow > overnightMaxQty and (not sellOrderSubmitted) and (not buyOrderSubmitted):
            sellOrderSubmitted = True; sellOrderQty = posNow - overnightMaxQty; sellOrderReason = 18; cnt[22] += 1

        if maxActs > 0 and actCount >= maxActs:
            if buyOrderSubmitted:
                buyOrderSubmitted = False
                if pendingInitialOrder and pendingInitialBar == i:
                    pendingInitialOrder = False; pendingInitialBar = -1
            if sellOrderSubmitted and not (sellOrderReason == 18 or sellOrderReason >= 21):
                sellOrderSubmitted = False
        if disableMask != 0:
            if buyOrderSubmitted and ((disableMask >> buyOrderReason) & 1) == 1:
                buyOrderSubmitted = False
                if pendingInitialOrder and pendingInitialBar == i:
                    pendingInitialOrder = False; pendingInitialBar = -1
            if sellOrderSubmitted and ((disableMask >> sellOrderReason) & 1) == 1:
                sellOrderSubmitted = False
        if FD > 0 and pendingOrderBar >= 0:   # stress mode: an in-flight delayed order blocks new submissions
            buyOrderSubmitted = False; sellOrderSubmitted = False
        if buyOrderSubmitted and buyOrderQty > 0:
            safe = min(buyOrderQty, max(Meff - posNow, 0))
            if safe > 0:
                cnt[5] += 1
                lastInventoryActionBar = i
                pendingOrderSide = 1; pendingOrderReason = buyOrderReason; pendingOrderQty = safe; pendingOrderBar = i
        if (buyOrderSubmitted and buyOrderQty > 0) or (sellOrderSubmitted and sellOrderQty > 0 and posNow > 0):
            actCount += 1
        if sellOrderSubmitted and sellOrderQty > 0 and posNow > 0:
            safe = min(sellOrderQty, posNow)
            cnt[6] += 1
            lastInventoryActionBar = i
            pendingOrderSide = -1; pendingOrderReason = sellOrderReason; pendingOrderQty = safe; pendingOrderBar = i

        # ---------------- push RTH arrays AFTER signals
        if inR:
            if rthN < RB:
                rthH[rthN] = h[i]; rthL[rthN] = l[i]; rthN += 1
            else:
                for k in range(RB - 1):
                    rthH[k] = rthH[k + 1]; rthL[k] = rthL[k + 1]
                rthH[RB - 1] = h[i]; rthL[RB - 1] = l[i]

        # ---------------- bookkeeping for next bar
        prev_vwapLowerDeep = vwapLowerDeep
        prev_vwapLowerExtreme = vwapLowerExtreme
        prev_rsi = rsi_i
        prev_wr = wr_i
        prev_strongBull = strongBullBar
        posPrevBar = posNow
        pos_arr[i] = posNow
        tgt_arr[i] = activeTargetQty
        base_arr[i] = baseGoal
        diag[i, 0] = rthVWAP; diag[i, 1] = rthVWAPStd; diag[i, 2] = vwapZ
        diag[i, 3] = roll15High; diag[i, 4] = roll15Low; diag[i, 5] = roll60High; diag[i, 6] = roll60Low
        diag[i, 7] = roll5DHigh; diag[i, 8] = roll5DLow; diag[i, 9] = priorRTHHigh; diag[i, 10] = priorRTHLow
        diag[i, 11] = openingRangeHigh; diag[i, 12] = openingRangeLow; diag[i, 13] = atr_i; diag[i, 14] = rsi_i
        diag[i, 15] = wr_i; diag[i, 16] = 1.0 if repairPending else 0.0; diag[i, 17] = avgPrice; diag[i, 18] = openprofit
        mtm = 0.0
        for k in range(lot_head, lot_tail):
            mtm += (c[i] - lot_px[k]) * PV * lot_q[k]
        eq_arr[i] = initCap + realized + mtm
        prev_eq = eq_arr[i]
        if inR:
            lastRTHClose = c[i]

    return (pos_arr, eq_arr, f_bar[:nf], f_side[:nf], f_qty[:nf], f_px[:nf], f_reason[:nf], f_real[:nf],
            cnt, tgt_arr, base_arr, diag)


def run(arr: dict, params: np.ndarray):
    n = len(arr["o"])
    mref = arr.get("mref", arr["o"])
    roll = arr.get("roll_day", np.zeros(n, dtype=np.bool_))
    out = run_kernel(arr["o"], arr["h"], arr["l"], arr["c"], arr["v"], arr["hh"], arr["mm"],
                     arr["in_rth"], arr["new_rth"], params, arr["sess"], mref, roll)
    keys = ["pos", "equity", "f_bar", "f_side", "f_qty", "f_px", "f_reason", "f_real", "counters", "target", "base", "diag"]
    res = dict(zip(keys, out))
    res["counter_dict"] = {k: float(res["counters"][j]) for k, j in C.items()}
    return res
