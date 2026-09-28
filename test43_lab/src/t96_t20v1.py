"""TEST96: Python port of TEST20 Native Factory V1.1 (Margin Fix), variant V1_SURVIVOR_STACK_3X, target NQ, and parity vs the
sanitized TradingView ledger TEST20_V1_1_MARGINFIX_NQ_V1_45ce0_TO_20260527.csv (unchanged TEST46 parity rule).

Source (frozen): authorities/legacy_pine/TEST20_NATIVE_FACTORY_V1_1_MARGIN_FIX.pine.  No rule is changed.
Chart = 5m RTH (us_regular) bars open-stamped 09:30..16:10; inRth = "0930-1545" -> bar opens 09:30..15:40.
Broker emulation: process_orders_on_close=false (entries queued at bar close fill at next bar open), slippage 1 tick,
commission 2.24 / contract / side, pyramiding 3, strategy.exit stop active from the bar after the fill bar,
strategy.close / close_all(immediately=true) fill at the current bar close.

Pine history semantics for math.sum / ta.lowest called inside `cond ? f(...) : na` (only executed on bars where cond is true):
  SUM_MODE = "lazy"  -> the function's private series only advances on bars where it is executed (TradingView behaviour);
  SUM_MODE = "eager" -> every chart bar is fed (as if the call were hoisted).  Both are reported; "lazy" is the primary port.
Ledger rows are never printed; only aggregate parity statistics."""
import json
import os
import sys
from collections import deque

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t96_data as X  # noqa: E402
X.register()
import t45_common as C45  # noqa: E402
import t46_common as C  # noqa: E402
import t46_01_parity as P  # noqa: E402
import t96_parity as T96P  # noqa: E402

LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(LAB, "out", "t96")
LEDGER = "TEST20_V1_1_MARGINFIX_NQ_V1_45ce0"
TICK = 0.25
SLIP = 1 * TICK
COMM = 2.24
PV = 20.0            # NQ point value (for the per-leg net P&L column only)
LEGS, FAMS = 3, 28
CONFIRM_MIN = 30
VARIANT = "V1_SURVIVOR_STACK_3X"
VCODE = 1

# NQ module table (order as in the Pine): (name, dir, family, survivor)
NQ_MODS = [("T18-03", 1, 1, False), ("T18-05", 1, 2, False), ("T18-07", 1, 3, True), ("T18-09", 1, 4, True),
           ("T18-20", -1, 9, False), ("T18-23", 1, 11, True), ("T18-28", -1, 13, True), ("T19-06", -1, 16, True),
           ("T19-07", 1, 17, True), ("T19-08", -1, 17, False), ("T19-13", 1, 20, False), ("T19-15", 1, 21, False),
           ("T19-16", -1, 21, True), ("T19-23", 1, 25, True), ("T19-28", -1, 27, False)]
NAN = float("nan")


def isna(x):
    return x != x


class Win:
    """Pine math.sum / ta.lowest private history.  eager: push every bar; lazy: push only when executed."""

    def __init__(self, n, kind, eager):
        self.b = deque(maxlen=n); self.n = n; self.kind = kind; self.eager = eager

    def step(self, x, called):
        if self.eager or called:
            self.b.append(x)
        if not called:
            return NAN
        if len(self.b) < self.n:
            return NAN
        if self.kind == "sum":
            s = 0.0
            for v in self.b:
                if isna(v):
                    return NAN
                s += v
            return s
        vals = [v for v in self.b if not isna(v)]
        return min(vals) if vals else NAN


def run(b, sum_mode="lazy", dbg=None, atr_scale=1.0):
    eager = sum_mode == "eager"
    t = pd.to_datetime(b.t).values.astype("datetime64[m]").astype(np.int64)   # minutes since epoch (NY wall clock)
    tt = pd.to_datetime(b.t)
    O, H, L, Cc, V = (b[k].to_numpy(float) for k in ("o", "h", "l", "c", "v"))
    mod_a = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
    dow = tt.dt.dayofweek.to_numpy()
    month = tt.dt.month.to_numpy()
    dates = tt.dt.normalize().to_numpy()
    n = len(b)
    # session.islastbar: bar whose close is the us_regular session end (16:15), i.e. the 16:10 bar.
    islast = mod_a == 16 * 60 + 10

    inRth_a = (mod_a >= 570) & (mod_a < 945) & (dow <= 4)
    # series needed with history
    vwap_a = np.full(n, NAN); side_a = np.zeros(n, int); z18_a = np.full(n, NAN); slope_a = np.full(n, NAN)
    bw_a = np.full(n, NAN); ss_a = np.zeros(n, int); cu_a = np.zeros(n, bool); cd_a = np.zeros(n, bool)

    # state
    aH = aL = aC = prevSC = atr14 = NAN; atrCount = 0; rthBarCount = 0
    cumV = cumPV = cumPV2 = 0.0; lastSessVwap = prevDayVwap = NAN
    signedStreak = 0
    lRA = sRA = False; lHB = sHB = 0
    SLOTS, DAYS = 75, 20
    slotSum = [0.0] * SLOTS; slotCount = [0] * SLOTS; ring = [NAN] * (SLOTS * DAYS); dayPtr = -1
    w_press = Win(12, "sum", eager); w_low = Win(12, "min", eager)
    w_pv6, w_v6 = Win(6, "sum", eager), Win(6, "sum", eager)
    w_pv12, w_v12 = Win(12, "sum", eager), Win(12, "sum", eager)
    w_pv24, w_v24 = Win(24, "sum", eager), Win(24, "sum", eager)
    w_cross, w_above, w_below = Win(12, "sum", eager), Win(12, "sum", eager), Win(12, "sum", eager)

    familySeenL = [False] * FAMS; familySeenS = [False] * FAMS
    campStarted = False; campDir = 0; campStart = None; nCreated = 0
    usedFam = [False] * FAMS; legStop = [NAN] * LEGS; legDir = [0] * LEGS; legFam = [-1] * LEGS
    campaign_id = 0
    pending = []          # orders queued at previous bar close: (leg, dir, fam, campaign_id)
    opent = []            # open trades: dict
    closed = []

    def close_trade(tr, i, px, reason):
        tr.update(exit_time=tt.iloc[i], exit_px=px, exit_reason=reason)
        closed.append(tr)

    for i in range(n):
        o, h, lo, c, v = O[i], H[i], L[i], Cc[i], V[i]
        mod = int(mod_a[i]); inRth = bool(inRth_a[i])
        # ---------------- broker emulator: fills during this bar ----------------
        if pending:
            for (lg, d, fam, cid) in pending:
                if sum(1 for x in opent if x["dir"] == d) < 3 and not any(x["dir"] == -d for x in opent):
                    opent.append(dict(campaign_id=cid, leg_index=lg + 1, direction="LONG" if d == 1 else "SHORT", dir=d, family=fam,
                                      entry_time=tt.iloc[i], entry_px=o + d * SLIP, et=t[i], stop=NAN, sd=NAN))
            pending = []
        still = []
        for tr in opent:
            sp = tr["stop"]
            if not isna(sp):
                if tr["dir"] == 1 and lo <= sp:
                    close_trade(tr, i, min(o, sp) - SLIP, f"STOP|L{tr['leg_index']}"); continue
                if tr["dir"] == -1 and h >= sp:
                    close_trade(tr, i, max(o, sp) + SLIP, f"STOP|L{tr['leg_index']}"); continue
            still.append(tr)
        opent = still

        # ---------------- script execution on bar close ----------------
        firstRth = inRth and mod == 570
        flattenNow = inRth and (mod + 5) == 945
        signalWindow = inRth and 600 <= mod < 870
        if firstRth:
            if not (isna(aH) or isna(aL) or isna(aC)):
                trp = aH - aL if isna(prevSC) else max(aH - aL, max(abs(aH - prevSC), abs(aL - prevSC)))
                atr14 = trp if isna(atr14) else (atr14 * 13.0 + trp) / 14.0
                atrCount += 1; prevSC = aC
            aH, aL, aC = h, lo, c; rthBarCount = 1
        elif inRth:
            rthBarCount += 1
            aH = max(h if isna(aH) else aH, h); aL = min(lo if isna(aL) else aL, lo); aC = c
        atrPrev = atr14 * atr_scale if atrCount >= 14 else NAN
        atrOK = (not isna(atrPrev)) and atrPrev > 0

        tp = (h + lo + c) / 3.0; vz = 0.0 if isna(v) else v
        if firstRth:
            prevDayVwap = lastSessVwap; cumV = cumPV = cumPV2 = 0.0
        if inRth:
            cumV += vz; cumPV += tp * vz; cumPV2 += tp * tp * vz
        vwap = cumPV / cumV if (inRth and cumV > 0) else NAN
        var = max(cumPV2 / cumV - vwap * vwap, 0.0) if (inRth and cumV > 0) else NAN
        vwapSd = NAN if isna(var) else var ** 0.5
        if inRth and not isna(vwap):
            lastSessVwap = vwap
        vwap_a[i] = vwap

        distAtr = (c - vwap) / atrPrev if (inRth and atrOK) else NAN
        slope6 = (vwap - vwap_a[i - 6]) / atrPrev if (inRth and rthBarCount > 6 and atrOK) else NAN
        slope_a[i] = slope6
        bwAtr = vwapSd / atrPrev if (inRth and atrOK and not isna(vwapSd)) else NAN
        bw_a[i] = bwAtr
        bw6 = bw_a[i - 6] if i >= 6 else NAN
        bwRatio6 = bwAtr / bw6 if (inRth and rthBarCount > 6 and not isna(bw6) and bw6 > 0) else NAN
        prior12 = w_low.step(bw_a[i - 7] if i >= 7 else NAN, inRth and rthBarCount > 19)
        pressure12 = w_press.step(distAtr, inRth and rthBarCount >= 12)

        side = 0 if (not inRth or isna(vwap)) else (1 if c > vwap else (-1 if c < vwap else 0))
        side_a[i] = side
        s1 = side_a[i - 1] if i >= 1 else 0
        crossUp = inRth and not firstRth and side == 1 and s1 <= 0
        crossDown = inRth and not firstRth and side == -1 and s1 >= 0
        cu_a[i] = crossUp; cd_a[i] = crossDown
        crossEvent = crossUp or crossDown
        if firstRth:
            signedStreak = side
        elif inRth:
            if side > 0:
                signedStreak = signedStreak + 1 if signedStreak > 0 else 1
            elif side < 0:
                signedStreak = signedStreak - 1 if signedStreak < 0 else -1
            else:
                signedStreak = 0
        ss_a[i] = signedStreak

        reclaimRetestLong = reclaimRetestShort = False
        if firstRth:
            lRA = sRA = False; lHB = sHB = 0
        if signalWindow:
            if crossUp:
                lRA = True; lHB = 0
            elif lRA:
                if side > 0:
                    lHB += 1
                    if lHB >= 2 and lo <= vwap and c > vwap and c > o:
                        reclaimRetestLong = True; lRA = False
                else:
                    lRA = False
            if crossDown:
                sRA = True; sHB = 0
            elif sRA:
                if side < 0:
                    sHB += 1
                    if sHB >= 2 and h >= vwap and c < vwap and c < o:
                        reclaimRetestShort = True; sRA = False
                else:
                    sRA = False

        ss2 = ss_a[i - 2] if i >= 2 else 0
        acceptanceFailLong = signalWindow and rthBarCount >= 3 and ss2 <= -12 and bool(cu_a[i - 1]) and side > 0
        acceptanceFailShort = signalWindow and rthBarCount >= 3 and ss2 >= 12 and bool(cd_a[i - 1]) and side < 0
        sqBase = signalWindow and rthBarCount > 19 and not isna(prior12) and prior12 > 0 and bw6 <= prior12 * 1.10 and bwRatio6 >= 1.25
        squeezeReleaseShort = sqBase and side < 0 and slope6 <= 0

        pv = tp * vz
        s_pv6 = w_pv6.step(pv, inRth and rthBarCount >= 6); s_v6 = w_v6.step(vz, inRth and rthBarCount >= 6)
        s_pv12 = w_pv12.step(pv, inRth and rthBarCount >= 12); s_v12 = w_v12.step(vz, inRth and rthBarCount >= 12)
        s_pv24 = w_pv24.step(pv, inRth and rthBarCount >= 24); s_v24 = w_v24.step(vz, inRth and rthBarCount >= 24)
        rv30 = s_pv6 / s_v6 if (not isna(s_v6) and s_v6 != 0) else NAN
        rv60 = s_pv12 / s_v12 if (not isna(s_v12) and s_v12 != 0) else NAN
        rv120 = s_pv24 / s_v24 if (not isna(s_v24) and s_v24 != 0) else NAN
        term = (rv30 - rv120) / atrPrev if (inRth and not isna(rv120) and atrOK) else NAN

        # same-time-of-day RVOL (prior 20 sessions)
        if firstRth:
            dayPtr = (dayPtr + 1) % DAYS
            for s in range(SLOTS):
                ri = dayPtr * SLOTS + s; old = ring[ri]
                if not isna(old):
                    slotSum[s] -= old; slotCount[s] = max(0, slotCount[s] - 1); ring[ri] = NAN
        slot = (mod - 570) // 5 if inRth else -1
        rvol = NAN
        if inRth and 0 <= slot < SLOTS:
            cnt = slotCount[slot]; avgP = slotSum[slot] / cnt if cnt >= 5 else NAN
            rvol = v / avgP if (not isna(avgP) and avgP > 0) else NAN
            ri = dayPtr * SLOTS + slot; ring[ri] = v; slotSum[slot] += v; slotCount[slot] += 1

        if dbg is not None:
            dbg.setdefault("rows", []).append((i, pressure12, atrPrev, distAtr, rthBarCount, term, slope6))
        ready = signalWindow and atrOK and not isna(vwap) and not isna(vwapSd)
        z18 = (c - vwap) / vwapSd if (inRth and not isna(vwapSd) and vwapSd > 0) else NAN
        z18_a[i] = z18
        spread3 = ((c - vwap) - (Cc[i - 3] - vwap_a[i - 3])) / atrPrev if (inRth and rthBarCount > 3 and atrOK) else NAN
        cross12 = w_cross.step(1.0 if crossEvent else 0.0, inRth and rthBarCount >= 12)
        a12 = w_above.step(1.0 if side > 0 else 0.0, inRth and rthBarCount >= 12)
        above12 = a12 / 12.0 if not isna(a12) else NAN
        _ = w_below.step(1.0 if side < 0 else 0.0, inRth and rthBarCount >= 12)
        s2 = side_a[i - 2] if i >= 2 else 0; s3 = side_a[i - 3] if i >= 3 else 0
        failedBearBreak = signalWindow and rthBarCount >= 4 and crossUp and ((s1 == -1 and s2 == 1) or (s1 == -1 and s2 == -1 and s3 == 1))
        prevClose = Cc[i - 1] if rthBarCount > 1 else NAN
        z18p = z18_a[i - 1] if i >= 1 else NAN

        sig = {}
        if ready:
            sig["T18-03"] = signedStreak == 8 and slope6 >= 0.04
            sig["T18-05"] = failedBearBreak
            sig["T18-07"] = cross12 >= 3 and z18 <= -1.0 and c > o
            sig["T18-09"] = cross12 <= 1 and above12 >= 10.0 / 12.0 and z18 >= 1.0 and z18 <= 2.0 and slope6 >= 0.04 and c > o
            sig["T18-20"] = distAtr <= -0.20 and spread3 <= -0.10 and slope6 <= -0.04 and c < o
            sig["T18-23"] = rthBarCount > 1 and z18p <= -1.5 and z18 > -1.0 and c > o
            sig["T18-28"] = (not isna(prevDayVwap)) and (not isna(prevClose)) and prevClose >= prevDayVwap and c < prevDayVwap and c < vwap and slope6 <= 0
            sig["T19-06"] = squeezeReleaseShort
            sig["T19-07"] = pressure12 >= 2.50 and side > 0 and slope6 >= 0
            sig["T19-08"] = pressure12 <= -2.50 and side < 0 and slope6 <= 0
            sig["T19-13"] = reclaimRetestLong
            sig["T19-15"] = acceptanceFailLong
            sig["T19-16"] = acceptanceFailShort
            sig["T19-23"] = rv30 > rv60 and rv60 > rv120 and term >= 0.15
            sig["T19-28"] = crossDown and rvol >= 1.50

        if firstRth:
            familySeenL = [False] * FAMS; familySeenS = [False] * FAMS
        barAnyL = [False] * FAMS; barAnyS = [False] * FAMS; barSurvL = [False] * FAMS; barSurvS = [False] * FAMS
        if signalWindow and not islast[i] and sig:
            for (nm, d, fam, surv) in NQ_MODS:
                if sig.get(nm, False):
                    if d == 1 and not familySeenL[fam]:
                        familySeenL[fam] = True; barAnyL[fam] = True
                        if surv:
                            barSurvL[fam] = True
                    if d == -1 and not familySeenS[fam]:
                        familySeenS[fam] = True; barAnyS[fam] = True
                        if surv:
                            barSurvS[fam] = True

        if firstRth:
            campStarted = False; campDir = 0; campStart = None; nCreated = 0
            usedFam = [False] * FAMS; legStop = [NAN] * LEGS; legDir = [0] * LEGS; legFam = [-1] * LEGS
        nL = sum(barSurvL); nS = sum(barSurvS)
        stopTicks = max(1, int(np.ceil(2.0 * atrPrev / TICK))) if atrOK else 0
        stopDist = stopTicks * TICK
        place = []

        def queue(d, fam, sd):
            nonlocal nCreated
            if nCreated < LEGS:
                place.append((nCreated, d, fam)); legStop[nCreated] = sd; legDir[nCreated] = d; legFam[nCreated] = fam
                if fam >= 0:
                    usedFam[fam] = True
                nCreated += 1

        if ready and stopTicks > 0 and not campStarted:
            if nL > 0 and nS == 0:
                campStarted = True; campDir = 1; campStart = t[i]; campaign_id += 1
                for f in range(FAMS):
                    if nCreated < LEGS and barSurvL[f]:
                        queue(1, f, stopDist)
            if nS > 0 and nL == 0:
                campStarted = True; campDir = -1; campStart = t[i]; campaign_id += 1
                for f in range(FAMS):
                    if nCreated < LEGS and barSurvS[f]:
                        queue(-1, f, stopDist)
        possz = sum(x["dir"] for x in opent)
        alive = (campDir == 1 and possz > 0) or (campDir == -1 and possz < 0)
        if campStarted and nCreated < LEGS and alive and t[i] - campStart <= CONFIRM_MIN:
            for f in range(FAMS):
                survEv = barSurvL[f] if campDir == 1 else barSurvS[f]
                if survEv and not usedFam[f] and nCreated < LEGS:
                    queue(campDir, f, stopDist)
        pending = [(lg, d, fam, campaign_id) for (lg, d, fam) in place]

        # per-trade stop maintenance and 120m clock
        still = []
        for tr in opent:
            lg = tr["leg_index"] - 1
            sd = legStop[lg]; d = legDir[lg]
            if not isna(sd):
                tr["stop"] = tr["entry_px"] - sd if d == 1 else tr["entry_px"] + sd
            if t[i] + 5 >= tr["et"] + 120:
                close_trade(tr, i, c - tr["dir"] * SLIP, f"MAXHOLD|L{tr['leg_index']}")
            else:
                still.append(tr)
        opent = still
        if flattenNow and opent:
            for tr in opent:
                close_trade(tr, i, c - tr["dir"] * SLIP, "1545_FLAT")
            opent = []
        if islast[i] and opent:
            for tr in opent:
                close_trade(tr, i, c - tr["dir"] * SLIP, "SESSION_LAST")
            opent = []

    df = pd.DataFrame(closed + opent)
    df = df.sort_values(["entry_time", "leg_index"]).reset_index(drop=True)
    df["net_usd"] = (df.exit_px - df.entry_px) * df.dir * PV - 2 * COMM
    return df[["campaign_id", "leg_index", "direction", "family", "entry_time", "entry_px", "exit_time", "exit_px", "exit_reason", "net_usd"]]


# ------------------------------------------------------------------ parity
def ledger_legs():
    t = C.load_ledger(LEDGER)
    sig = t.signal.str.extract(r"\|L(\d)\|(LONG|SHORT)\|FAM=(\w+)")
    t["leg_index"] = sig[0].astype(int); t["direction"] = sig[1]; t["family"] = pd.to_numeric(sig[2], errors="coerce")
    return t


def _window(df, cov):
    et = pd.to_datetime(df.entry_time)
    return df[(et >= P.W0) & (et.dt.normalize() <= C.END) & et.dt.normalize().isin(cov)]


def _ms(a, b):
    """multiset recall / precision of key tuples."""
    ca, cb = pd.Series(a).value_counts(), pd.Series(b).value_counts()
    m = int(pd.concat([ca, cb], axis=1).fillna(0).min(axis=1).sum()) if len(ca) and len(cb) else 0
    return dict(ledger=int(len(a)), engine=int(len(b)), matched=m, recall=m / max(len(a), 1), precision=m / max(len(b), 1))


def price_diag(Lw, Ew):
    """diagnostic: per-contract median offset (ledger - engine) on timestamp-matched first legs."""
    m = Lw.drop_duplicates("entry_time").merge(Ew.drop_duplicates("entry_time"), on="entry_time", suffixes=("_l", "_e"))
    if not len(m):
        return {}
    con = C45.load1m("NQ")[["session_date", "contract"]].drop_duplicates("session_date").set_index("session_date").contract
    m["contract"] = pd.to_datetime(m.entry_time).dt.normalize().map(con)
    off = m.entry_px_l - m.entry_px_e
    med = off.groupby(m.contract).transform("median")
    dv = (off - med).abs()
    return {"n": int(len(m)), "contracts": int(m.contract.nunique()), "within_1tick_share_per_contract_median": float((dv <= TICK + 1e-9).mean()),
            "exact_share": float((dv <= 1e-9).mean()), "median_abs_diff": float(dv.median())}


def parity(eng, cov):
    led = ledger_legs()
    Lw, Ew = _window(led, cov), _window(eng, cov)
    Lw = Lw.assign(entry_time=pd.to_datetime(Lw.entry_time)); Ew = Ew.assign(entry_time=pd.to_datetime(Ew.entry_time))
    o = {}
    # timestamp level: TEST46 compare on unique entry timestamps (first leg per timestamp)
    P.COV = cov
    lt = Lw.sort_values(["entry_time", "leg_index"]).drop_duplicates("entry_time")[["entry_time", "entry_px"]]
    et = Ew.sort_values(["entry_time", "leg_index"]).drop_duplicates("entry_time")[["entry_time", "entry_px"]]
    o["timestamp_level_TEST46"] = P.compare("T20_V1_NQ", lt.reset_index(drop=True), et.reset_index(drop=True))
    k = lambda d, cols: list(map(tuple, d[cols].astype(str).values))  # noqa: E731
    o["timestamp_dir"] = _ms(k(Lw.drop_duplicates("entry_time"), ["entry_time", "direction"]), k(Ew.drop_duplicates("entry_time"), ["entry_time", "direction"]))
    o["leg_level_time_dir"] = _ms(k(Lw, ["entry_time", "direction"]), k(Ew, ["entry_time", "direction"]))
    o["leg_level_time_dir_leg"] = _ms(k(Lw, ["entry_time", "direction", "leg_index"]), k(Ew, ["entry_time", "direction", "leg_index"]))
    o["leg_level_time_dir_leg_fam"] = _ms(k(Lw, ["entry_time", "direction", "leg_index", "family"]), k(Ew, ["entry_time", "direction", "leg_index", "family"]))
    Ll, El = Lw[Lw.direction == "LONG"], Ew[Ew.direction == "LONG"]
    o["long_only_timestamp"] = _ms(k(Ll.drop_duplicates("entry_time"), ["entry_time"]), k(El.drop_duplicates("entry_time"), ["entry_time"]))
    o["long_only_leg_level"] = _ms(k(Ll, ["entry_time", "leg_index", "family"]), k(El, ["entry_time", "leg_index", "family"]))
    Ls, Es = Lw[Lw.direction == "SHORT"], Ew[Ew.direction == "SHORT"]
    o["short_only_timestamp"] = _ms(k(Ls.drop_duplicates("entry_time"), ["entry_time"]), k(Es.drop_duplicates("entry_time"), ["entry_time"]))
    o["short_only_leg_level"] = _ms(k(Ls, ["entry_time", "leg_index", "family"]), k(Es, ["entry_time", "leg_index", "family"]))
    for li in (1, 2, 3):
        a, b2 = Lw[Lw.leg_index == li], Ew[Ew.leg_index == li]
        o[f"L{li}_only"] = _ms(k(a, ["entry_time", "direction", "family"]), k(b2, ["entry_time", "direction", "family"]))
    a, b2 = Lw[Lw.leg_index == 2], Ew[Ew.leg_index == 2]
    o["L2_only_time_dir"] = _ms(k(a, ["entry_time", "direction"]), k(b2, ["entry_time", "direction"]))
    # L2 created later than L1 (add-on legs) vs on the start bar
    def addon(d):
        f = d.groupby(d.entry_time.dt.normalize()).entry_time.transform("min")
        return d[(d.leg_index >= 2) & (d.entry_time > f)]
    o["addon_legs_only"] = _ms(k(addon(Lw), ["entry_time", "direction", "leg_index", "family"]), k(addon(Ew), ["entry_time", "direction", "leg_index", "family"]))
    # exits (diagnostic): matched legs with identical exit time and reason class
    m = Lw.merge(Ew, on=["entry_time", "direction", "leg_index"], suffixes=("_l", "_e"))
    if len(m):
        rl = m.exit_reason_l.str.replace("TEST20|", "", regex=False)
        o["exit_diag"] = {"matched_legs": int(len(m)), "same_exit_time": float((pd.to_datetime(m.exit_time_l) == pd.to_datetime(m.exit_time_e)).mean()),
                          "same_exit_reason": float((rl == m.exit_reason_e).mean())}
    o["price_diag_per_contract"] = price_diag(Lw, Ew)
    o["ledger_legs_total_window"] = int(len(Lw)); o["engine_legs_total_window"] = int(len(Ew))
    return o


def main():
    os.makedirs(OUT, exist_ok=True)
    b = C.bars5("NQ")
    cov = T96P.covered_dates_nq()
    res = {"strategy": "TEST20 V1.1 MARGIN FIX", "variant": VARIANT, "target": "NQ",
           "window": [str(P.W0.date()), str(C.END.date())], "coverage": "ES+MNQ+NQ complete 81-bar sessions (t96_parity.covered_dates_nq)",
           "primary_sum_mode": "lazy"}
    for mode in ("lazy", "eager"):
        eng = run(b, mode)
        if mode == "lazy":
            eng.to_csv(os.path.join(OUT, "T20_V1_ENGINE_LEGS.csv"), index=False)
        else:
            eng.to_csv(os.path.join(OUT, "T20_V1_ENGINE_LEGS_eagersum.csv"), index=False)
        res[mode] = parity(eng, cov)
        ts = res[mode]["timestamp_level_TEST46"]; lg = res[mode]["leg_level_time_dir_leg_fam"]
        print(f"[{mode}] ts recall={ts['ledger_recall']:.4f} prec={ts['engine_precision']:.4f} px1t={ts['price_within_1tick_share']:.4f} {ts['PARITY']} | "
              f"legs recall={lg['recall']:.4f} prec={lg['precision']:.4f}", flush=True)
    json.dump(res, open(os.path.join(OUT, "T20_V1_PARITY.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
