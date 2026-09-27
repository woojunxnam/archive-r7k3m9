"""TEST43 V6A — low-turnover exposure allocator.  STATE -> TARGET EXPOSURE -> RISK GOVERNOR.

Per completed 3m bar:
  allowed  = min(hardCap[RTH|ON], marginCap, volCap)            (contracts, instrument-normalised)
  frac     = tierFrac[regime tier] * trend multiplier
             + dip boost (bottom/reversal evidence, low-turnover state, RTH only)
             - upper reduction (upper VWAP/range state, RTH only)
  frac    *= drawdown-tier multiplier  (equity HWM governor, deterministic rearm)
  target   = round(frac * allowed)
  overnight: target is re-evaluated at the last RTH bar by overnight mode O0..O5
  risk cuts: day stop, gap emergency, vol-shock -> floor for the rest of the session
Orders: market at NEXT bar open for the whole delta (large state transitions),
only when |delta| >= minDelta and cooldown elapsed (risk cuts bypass both).
Long only; target clipped to [0, allowed].
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

PARAM_NAMES = [
    "pointValue", "commission", "slipTicks", "initCap", "rollCost",
    "capRTH", "capON", "marginU", "mIntraFrac", "mOnFrac", "volBudget", "volBudgetON",
    "fBear", "fNeut", "fMed", "fStrong", "trendMult",
    "dipOn", "dipZ", "dipPos5d", "dipBoost", "dipNeedRev", "dipExitZ", "dipMaxBars",
    "redOn", "redZ", "redPosRth", "redCut", "redExitZ",
    "onMode", "onFrac", "onMinTier",
    "dd1", "dd2", "dd3", "ddM1", "ddM2", "ddM3", "ddRearmTier", "ddCooldown",
    "dayStop", "gapK", "shockK", "riskFloorFrac",
    "minDelta", "cooldownBars", "buyStartMod", "buyEndMod", "tickSize", "delayBars", "lastBarMod",
]
P = {n: i for i, n in enumerate(PARAM_NAMES)}
DEFAULTS = dict(
    pointValue=5.0, commission=0.62, slipTicks=1.0, initCap=150000.0, rollCost=3.74,
    capRTH=4, capON=4, marginU=0.5, mIntraFrac=0.0642, mOnFrac=0.0917, volBudget=0.0, volBudgetON=0.0,
    fBear=1.0, fNeut=1.0, fMed=1.0, fStrong=1.0, trendMult=1.0,
    dipOn=0, dipZ=2.0, dipPos5d=0.15, dipBoost=0.0, dipNeedRev=1, dipExitZ=0.0, dipMaxBars=60,
    redOn=0, redZ=2.0, redPosRth=0.9, redCut=0.0, redExitZ=0.5,
    onMode=1, onFrac=1.0, onMinTier=2,
    dd1=0.0, dd2=0.0, dd3=0.0, ddM1=1.0, ddM2=1.0, ddM3=0.0, ddRearmTier=2, ddCooldown=1,
    dayStop=0.0, gapK=0.0, shockK=0.0, riskFloorFrac=0.0,
    minDelta=1, cooldownBars=0, buyStartMod=570, buyEndMod=954, tickSize=0.25, delayBars=0, lastBarMod=957,
)
REASONS = ["NONE", "REBAL_UP", "REBAL_DOWN", "ON_TRIM", "DD_CUT", "DAYSTOP", "GAP_EMERG", "VOLSHOCK"]


def make_params(**kw):
    d = dict(DEFAULTS)
    for k, v in kw.items():
        if k not in P:
            raise KeyError(k)
        d[k] = v
    return np.array([float(d[k]) for k in PARAM_NAMES])


@njit(cache=True)
def kernel(o, h, l, c, mref, roll_day, sess, mod, in_rth, new_rth, tier, atrD, vwap_z, pos5d, pos_rth,
           rsi2, gap_atr, bar_range_atr, trend_ok, prm):
    n = len(c)
    PV = prm[0]; COMM = prm[1]; SLIP = prm[2] * prm[48]; INIT = prm[3]; ROLL = prm[4]
    capRTH = int(prm[5]); capON = int(prm[6]); mU = prm[7]; mIn = prm[8]; mOn = prm[9]
    vB = prm[10]; vBon = prm[11]
    fT = np.array([prm[12], prm[13], prm[14], prm[15]]); trendMult = prm[16]
    dipOn = prm[17] > 0.5; dipZ = prm[18]; dipPos = prm[19]; dipBoost = prm[20]; dipRev = prm[21] > 0.5
    dipExitZ = prm[22]; dipMax = int(prm[23])
    redOn = prm[24] > 0.5; redZ = prm[25]; redPos = prm[26]; redCut = prm[27]; redExitZ = prm[28]
    onMode = int(prm[29]); onFrac = prm[30]; onMinTier = int(prm[31])
    dd1 = prm[32]; dd2 = prm[33]; dd3 = prm[34]; m1 = prm[35]; m2 = prm[36]; m3 = prm[37]
    rearmTier = int(prm[38]); ddCool = int(prm[39])
    dayStop = prm[40]; gapK = prm[41]; shockK = prm[42]; floorF = prm[43]
    minDelta = int(prm[44]); cool = int(prm[45]); bStart = int(prm[46]); bEnd = int(prm[47])
    delay = int(prm[49]); lastMod = int(prm[50])
    pendAge = 0

    pos = 0
    realized = 0.0
    avgpx = 0.0
    pend = 0; pend_reason = 0
    pos_arr = np.zeros(n, dtype=np.int64); eq_arr = np.zeros(n); tgt_arr = np.zeros(n, dtype=np.int64)
    f_bar = np.zeros(n, dtype=np.int64); f_qty = np.zeros(n, dtype=np.int64); f_px = np.zeros(n)
    f_reason = np.zeros(n, dtype=np.int64); nf = 0
    hwm = INIT; ddLevel = 0; ddSince = 0
    dipActive = False; dipBars = 0; redActive = False
    sessStartEq = INIT; riskCut = False
    lastTradeBar = -100000
    prev_eq = INIT
    lastRollSess = -1
    for i in range(n):
        # ---- fill pending order at this bar's open
        if pend != 0 and pendAge < delay:
            pendAge += 1
        elif pend != 0:
            px = o[i] + SLIP if pend > 0 else o[i] - SLIP
            q = pend
            if q > 0:
                avgpx = (avgpx * pos + px * q) / (pos + q)
            else:
                realized += (px - avgpx) * PV * (-q)
            pos += q
            realized -= abs(q) * COMM
            f_bar[nf] = i; f_qty[nf] = q; f_px[nf] = px; f_reason[nf] = pend_reason; nf += 1
            pend = 0
            lastTradeBar = i
            if pos == 0:
                avgpx = 0.0
        newSess = i == 0 or sess[i] != sess[i - 1]
        if newSess:
            sessStartEq = prev_eq
            riskCut = False
            dipActive = False; redActive = False
        if roll_day[i] and sess[i] != lastRollSess:
            lastRollSess = sess[i]
            realized -= pos * ROLL
        eq = INIT + realized + (c[i] - avgpx) * PV * pos if pos > 0 else INIT + realized
        inR = in_rth[i]
        # ---- drawdown governor (tiers) with deterministic rearm at new RTH
        if eq > hwm and ddLevel == 0:
            hwm = eq
        dd = hwm - eq
        lvl = 0
        if dd3 > 0 and dd >= dd3:
            lvl = 3
        elif dd2 > 0 and dd >= dd2:
            lvl = 2
        elif dd1 > 0 and dd >= dd1:
            lvl = 1
        if lvl > ddLevel:
            ddLevel = lvl; ddSince = 0
        if new_rth[i] and ddLevel > 0:
            ddSince += 1
            if ddSince >= ddCool and tier[i] >= rearmTier:
                ddLevel = 0; hwm = eq
        ddMult = 1.0
        if ddLevel == 1:
            ddMult = m1
        elif ddLevel == 2:
            ddMult = m2
        elif ddLevel == 3:
            ddMult = m3
        # ---- caps
        rawpx = mref[i]
        lastR = (inR and mod[i] >= lastMod) or ((not inR) and i > 0 and in_rth[i - 1])
        onSide = (not inR) or lastR
        cap = capON if onSide else capRTH
        mfrac = mOn if onSide else mIn
        mcap = int(math.floor(mU * max(eq, 0.0) / (rawpx * PV * mfrac))) if rawpx > 0 else 0
        allowed = min(cap, mcap)
        vb = (vBon if vBon > 0 else vB) if onSide else vB
        if vb > 0 and atrD[i] > 0:
            allowed = min(allowed, int(math.floor(vb / (PV * atrD[i]))))
        if allowed < 0:
            allowed = 0
        # ---- state fraction
        t = tier[i]
        if t < 0:
            t = 1
        frac = fT[t]
        if not trend_ok[i]:
            frac *= trendMult
        if inR:
            if dipOn:
                if not dipActive:
                    cond = vwap_z[i] <= -dipZ or pos5d[i] <= dipPos
                    rev = True
                    if dipRev:
                        rev = (i > 0 and c[i] > h[i - 1]) or (i > 0 and rsi2[i] > rsi2[i - 1] and rsi2[i - 1] < 15.0)
                    if cond and rev:
                        dipActive = True; dipBars = 0
                else:
                    dipBars += 1
                    if vwap_z[i] >= dipExitZ or dipBars >= dipMax:
                        dipActive = False
                if dipActive:
                    frac += dipBoost
            if redOn:
                if not redActive:
                    if vwap_z[i] >= redZ and pos_rth[i] >= redPos:
                        redActive = True
                elif vwap_z[i] < redExitZ:
                    redActive = False
                if redActive:
                    frac -= redCut
        frac *= ddMult
        if frac < 0:
            frac = 0.0
        if frac > 1:
            frac = 1.0
        # ---- session risk cuts
        if not riskCut:
            if dayStop > 0 and eq - sessStartEq <= -dayStop:
                riskCut = True
            if gapK > 0 and new_rth[i] and gap_atr[i] <= -gapK:
                riskCut = True
            if shockK > 0 and bar_range_atr[i] >= shockK:
                riskCut = True
        if riskCut:
            frac = min(frac, floorF)
        target = int(math.floor(frac * allowed + 0.5))
        reason = 0
        # ---- overnight decision: last RTH bar (15:57) or first non-RTH bar after RTH (half days)
        if onSide:
            onT = target
            if onMode == 0:
                onT = 0
            elif onMode == 1:
                onT = int(math.floor(fT[t] * min(capON, allowed) * onFrac + 0.5))
            elif onMode == 2:
                onT = int(math.floor(min(frac, onFrac) * allowed + 0.5))
            elif onMode == 3:
                onT = target if t >= onMinTier else int(math.floor(onFrac * target + 0.5))
            elif onMode == 4:
                onT = target  # vol-target handled by volBudgetON in allowed
            elif onMode == 5:
                onT = target if (t >= onMinTier and ddLevel == 0) else int(math.floor(onFrac * target + 0.5))
            if riskCut:
                onT = min(onT, int(math.floor(floorF * allowed + 0.5)))
            target = min(onT, pos) if (not lastR) else onT  # outside RTH never add
            if target < 0:
                target = 0
        delta = target - pos
        risk = riskCut or ddLevel > 0 or lastR or (not inR)
        if delta != 0 and pend == 0:
            ok = False
            if delta < 0:
                if risk or (abs(delta) >= minDelta and i - lastTradeBar >= cool):
                    ok = True
                    reason = 2
                    if lastR or not inR:
                        reason = 3
                    if riskCut:
                        reason = 5
                    elif ddLevel > 0 and not lastR:
                        reason = 4
            else:
                if inR and (not lastR) and mod[i] >= bStart and mod[i] <= bEnd and abs(delta) >= minDelta \
                        and i - lastTradeBar >= cool and not riskCut:
                    ok = True
                    reason = 1
            if ok:
                pend = delta; pend_reason = reason; pendAge = 0
        pos_arr[i] = pos; eq_arr[i] = eq; tgt_arr[i] = target
        prev_eq = eq
    return pos_arr, eq_arr, tgt_arr, f_bar[:nf], f_qty[:nf], f_px[:nf], f_reason[:nf]


def run(b, f, prm, mref=None, roll_day=None):
    n = len(b)
    if mref is None:
        mref = (b["c"] - b["cum_adjustment"].astype(float)).values if "cum_adjustment" in b else b["c"].values
    if roll_day is None:
        roll_day = b["roll_adjacent"].fillna(False).astype(bool).values if "roll_adjacent" in b else np.zeros(n, bool)
    trend_ok = np.nan_to_num(f["d_TREND20"], nan=1.0) > 0.5
    atrD = np.nan_to_num(f["d_ATR20"], nan=0.0)
    out = kernel(b.o.values, b.h.values, b.l.values, b.c.values, np.asarray(mref, float), roll_day, f["sess"], f["mod"],
                 f["in_rth"], f["new_rth"], f["d_TIER"], atrD, f["vwap_z"], f["pos_5d"], f["pos_rth"],
                 np.nan_to_num(f["rsi2"], nan=50.0), f["gap_atr"], f["bar_range_atr"], trend_ok, prm)
    keys = ["pos", "equity", "target", "f_bar", "f_qty", "f_px", "f_reason"]
    r = dict(zip(keys, out))
    r["f_side"] = np.sign(r["f_qty"]).astype(np.int64)
    r["f_absqty"] = np.abs(r["f_qty"])
    return r
