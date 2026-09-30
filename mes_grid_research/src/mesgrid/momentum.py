"""Sleeve B: long-only momentum / breakout / follow-through event definitions (B1-B12), all causal.

Each event is a boolean on the 1m full grid at the CLOSE of the bar where the condition is known (for k-minute bars:
the completion 1m bar, see mtf.py). A strategy enters at the next 1m open (EXEC-1.1). Families:
 B1 strong bar follow-through   B2 N-bar breakout          B3 rolling/prior-interval range breakout
 B4 opening range               B5 compression->expansion  B6 breakout + pullback continuation
 B7 first vs second leg         B8 failed breakdown->reclaim  B9 VWAP reclaim
 B10 micro channel              B11 volatility burst       B12 momentum after selloff
Values are coarse by design (no fine tuning). Returns (events: name -> 1m index array, meta: name -> dict).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit

from .mtf import add_basic_features, mtf_bars, prior_max, prior_min, to_1m


def _fget(F, key, m):
    return F[key][np.maximum(m["comp"], 0)]


@njit(cache=True)
def _orb_states(h, l, c, nb, newday, orn, band):
    """per RTH 1m bar: ORB first close above ORH, ORB strong, ORB pullback-reclaim, OR failed-downside reclaim."""
    n = len(c)
    brk = np.zeros(n, np.bool_)
    rt = np.zeros(n, np.bool_)
    fdr = np.zeros(n, np.bool_)
    orh = np.nan
    orl = np.nan
    done_b = False
    stage = 0      # 0 none, 1 broke out, 2 retested
    hi_since = -1e18
    below = False
    done_f = False
    for j in range(n):
        if newday[j]:
            orh = -1e18
            orl = 1e18
            done_b = False
            stage = 0
            below = False
            done_f = False
        if nb[j] < orn:
            if h[j] > orh:
                orh = h[j]
            if l[j] < orl:
                orl = l[j]
            continue
        if not done_b and c[j] > orh:
            brk[j] = True
            done_b = True
            stage = 1
            hi_since = h[j]
            continue
        if stage == 1:
            if h[j] > hi_since:
                hi_since = h[j]
            if l[j] <= orh + band:
                stage = 2
        elif stage == 2:
            if c[j] > hi_since:
                rt[j] = True
                stage = 3
            elif h[j] > hi_since:
                hi_since = h[j]
        if not done_f:
            if l[j] < orl:
                below = True
            if below and c[j] > orl:
                fdr[j] = True
                done_f = True
    return brk, rt, fdr


@njit(cache=True)
def _brk_pullback(h, l, c, ph, nb, newday, hh, ll, depth, M):
    """breakout (c > prior-N high) -> pullback >= depth*(BH-SL) staying above SL within M bars -> close > prev high."""
    n = len(c)
    out = np.zeros(n, np.bool_)
    act = False
    bh = 0.0
    sl = 0.0
    t0 = 0
    pulled = False
    for j in range(n):
        if newday[j]:
            act = False
        if act:
            if j - t0 > M or l[j] <= sl:
                act = False
            else:
                if h[j] > bh and not pulled:
                    bh = h[j]
                if not pulled and l[j] <= bh - depth * (bh - sl):
                    pulled = True
                elif pulled and c[j] > ph[j]:
                    out[j] = True
                    act = False
        if not act and np.isfinite(hh[j]) and c[j] > hh[j] and np.isfinite(ll[j]):
            act = True
            bh = h[j]
            sl = ll[j]
            t0 = j
            pulled = False
    return out


@njit(cache=True)
def _second_leg(h, l, c, newday, ll10, atr, kmult, retr):
    """first entry: bar where c - ll10 >= k*atr first becomes true; second entry: after a >= retr pullback of the
    impulse (low stays above impulse low), first close above the impulse high."""
    n = len(c)
    first = np.zeros(n, np.bool_)
    second = np.zeros(n, np.bool_)
    prev_on = False
    act = False
    ih = 0.0
    il = 0.0
    pulled = False
    for j in range(n):
        if newday[j]:
            prev_on = False
            act = False
        on = np.isfinite(ll10[j]) and np.isfinite(atr[j]) and (c[j] - ll10[j] >= kmult * atr[j])
        if on and not prev_on and not act:
            first[j] = True
            act = True
            ih = h[j]
            il = ll10[j]
            pulled = False
        elif act:
            if l[j] <= il:
                act = False
            elif not pulled:
                if h[j] > ih:
                    ih = h[j]
                if l[j] <= ih - retr * (ih - il):
                    pulled = True
            elif c[j] > ih:
                second[j] = True
                act = False
        prev_on = on
    return first, second


@njit(cache=True)
def _break_reclaim(l, c, pc, level, newday, W):
    """a level is broken (l < level; the FIRST broken level is kept while the break is active) and within W bars of
    the latest break bar the close comes back above it (W=1: same-bar sweep & reclaim)."""
    n = len(c)
    out = np.zeros(n, np.bool_)
    lv = np.nan
    tb = -10**9
    active = False
    for j in range(n):
        if newday[j]:
            active = False
        if np.isfinite(level[j]) and l[j] < level[j]:
            if not active:
                lv = level[j]
                active = True
            tb = j
        if active:
            if j - tb > W - 1:
                active = False
            elif c[j] > lv and (j == tb or pc[j] <= lv):
                out[j] = True
                active = False
    return out


def build_events(b, F):
    n = len(b)
    ev, meta = {}, {}

    def add(name, fam, arr, **kw):
        idx = np.flatnonzero(arr)
        ev[name] = idx.astype(np.int64)
        meta[name] = dict(family=fam, **kw)

    M = {}
    for k in (1, 2, 3, 5, 10, 15, 30, 60):
        M[k] = add_basic_features(mtf_bars(b, k))
    m1 = M[1]
    vw1 = _fget(F, "vwap", m1)
    a15 = np.maximum(_fget(F, "atr15", m1), 0.25)
    mom60 = np.nan_to_num(_fget(F, "mom60", m1))
    # ---------------- B1 strong bar follow-through
    for k in (1, 3, 5, 10):
        m = M[k]
        vw = _fget(F, "vwap", m)
        trend = (m["c"] > m["ema20"]) & (np.nan_to_num(_fget(F, "mom60", m)) > 0)
        for x in (0.8, 1.2, 1.8):
            base = (m["body"] >= x * m["atr"]) & (m["cl"] >= 0.8)
            add(f"B1_tf{k}_body{x}", "B1", to_1m(m, base, n), tf=k, x=x)
            if x == 1.2:
                add(f"B1_tf{k}_body{x}_vol", "B1", to_1m(m, base & (m["vrel"] >= 1.5), n), tf=k, x=x, var="vol")
                add(f"B1_tf{k}_body{x}_vwap", "B1", to_1m(m, base & (m["c"] > vw), n), tf=k, x=x, var="vwap")
                add(f"B1_tf{k}_body{x}_trend", "B1", to_1m(m, base & trend, n), tf=k, x=x, var="trend")
    # ---------------- B2 N-bar breakout
    for k in (1, 3, 5):
        m = M[k]
        vw = _fget(F, "vwap", m)
        for N in (2, 3, 4, 6, 8, 12, 20):
            hh = prior_max(m["h"], N, m["nb"])
            base = m["c"] > hh
            add(f"B2_tf{k}_N{N}", "B2", to_1m(m, base, n), tf=k, N=N)
            if N in (4, 8, 12):
                add(f"B2_tf{k}_N{N}_strong", "B2", to_1m(m, base & (m["cl"] >= 0.75), n), tf=k, N=N, var="strong")
                add(f"B2_tf{k}_N{N}_rngexp", "B2", to_1m(m, base & (m["rng"] >= 1.5 * m["ravg"]), n), tf=k, N=N, var="rngexp")
                add(f"B2_tf{k}_N{N}_vol", "B2", to_1m(m, base & (m["vrel"] >= 1.5), n), tf=k, N=N, var="vol")
                add(f"B2_tf{k}_N{N}_vwap", "B2", to_1m(m, base & (m["c"] > vw), n), tf=k, N=N, var="vwap")
    # ---------------- B3 rolling range breakout (1m) and prior completed interval range
    for L in (5, 10, 15, 30, 60):
        hh = prior_max(m1["h"], L, m1["nb"])
        add(f"B3_roll{L}", "B3", to_1m(m1, m1["c"] > hh, n), L=L)
    for I in (15, 30, 60):
        mI = M[I]
        # high of the previous COMPLETED I-bucket of the same day, known from its completion bar onward
        prevH = np.full(n, np.nan)
        comp = mI["comp"]
        for j in range(len(comp)):
            if comp[j] >= 0:
                prevH[comp[j]] = mI["h"][j]
        W1 = np.flatnonzero(b.in_window)
        ph = pd.Series(prevH[W1]).groupby(b.day[W1]).ffill().values
        # a bar that completes a bucket starts the next interval: exclude breakouts on the completion bar itself
        c1 = m1["c"]
        first_in_bucket = pd.Series((c1 > ph) & np.isfinite(ph)).groupby(
            pd.Series(b.day[W1]).astype(str).values + "_" + ((b.minute[W1] - 571) // I).astype(str)).cumsum().values == 1
        ev_ = np.zeros(n, bool)
        ev_[W1] = (c1 > ph) & np.isfinite(ph) & first_in_bucket
        add(f"B3_prev{I}m_range", "B3", ev_, I=I)
    # ---------------- B4 opening range
    for orn in (5, 10, 15, 30):
        brk, rt, fdr = _orb_states(m1["h"], m1["l"], m1["c"], m1["nb"], m1["newday"], orn, 0.5)
        add(f"B4_or{orn}_break", "B4", to_1m(m1, brk, n), orn=orn)
        add(f"B4_or{orn}_break_strong", "B4", to_1m(m1, brk & (m1["cl"] >= 0.75), n), orn=orn, var="strong")
        add(f"B4_or{orn}_pullback", "B4", to_1m(m1, rt, n), orn=orn, var="pullback")
        add(f"B4_or{orn}_faildown_reclaim", "B4", to_1m(m1, fdr, n), orn=orn, var="faildown")
    # ---------------- B5 compression -> expansion
    for k, N in ((1, 15), (5, 6)):
        m = M[k]
        hh = prior_max(m["h"], N, m["nb"]); ll = prior_min(m["l"], N, m["nb"])
        box = hh - ll
        med = pd.Series(box).rolling(500, min_periods=100).median().values
        for q in (0.5, 0.7):
            comp_ = pd.Series(box <= q * med).shift(1).fillna(False).values.astype(bool) | (box <= q * med)
            add(f"B5_tf{k}_q{q}_boxbreak", "B5", to_1m(m, comp_ & (m["c"] > hh), n), tf=k, q=q, var="boxbreak")
            add(f"B5_tf{k}_q{q}_expbar", "B5", to_1m(m, comp_ & (m["rng"] >= 2 * m["ravg"]) & (m["cl"] >= 0.75) & (m["body"] > 0), n),
                tf=k, q=q, var="expbar")
    # ---------------- B6 breakout + pullback continuation
    for k in (1, 3, 5):
        m = M[k]
        hh = prior_max(m["h"], 6, m["nb"]); ll = prior_min(m["l"], 6, m["nb"])
        for d in (0.25, 0.33, 0.5):
            out = _brk_pullback(m["h"], m["l"], m["c"], m["ph"], m["nb"], m["newday"], hh, ll, d, 12)
            add(f"B6_tf{k}_pb{d}", "B6", to_1m(m, out, n), tf=k, depth=d)
    # ---------------- B7 first vs second leg
    for k in (1, 3):
        m = M[k]
        ll10 = prior_min(m["l"], 10, m["nb"])
        for km in (3.0, 5.0):
            first, second = _second_leg(m["h"], m["l"], m["c"], m["newday"], ll10, m["atr"], km, 0.3)
            add(f"B7_tf{k}_k{km}_first", "B7", to_1m(m, first, n), tf=k, kmult=km, var="first")
            add(f"B7_tf{k}_k{km}_second", "B7", to_1m(m, second, n), tf=k, kmult=km, var="second")
    # ---------------- B8 failed breakdown -> reclaim (1m)
    W1 = np.flatnonzero(b.in_window)
    sl_prev = np.concatenate([[np.nan], _fget(F, "sess_low", m1)[:-1]])
    sl_prev = np.where(m1["newday"], np.nan, sl_prev)
    dfd = pd.DataFrame({"d": b.day[W1], "l": b.l[W1]})
    dl = dfd.groupby("d").l.min()
    pdl = dfd.d.map(dl.shift(1)).values
    levels = {"sesslow": sl_prev, "low15": prior_min(m1["l"], 15, m1["nb"]), "low30": prior_min(m1["l"], 30, m1["nb"]),
              "low60": prior_min(m1["l"], 60, m1["nb"]), "pdl": pdl}
    for nm, lv in levels.items():
        for Wn in (1, 5):
            out = _break_reclaim(m1["l"], m1["c"], m1["pc"], lv, m1["newday"], Wn)
            add(f"B8_{nm}_W{Wn}", "B8", to_1m(m1, out, n), level=nm, W=Wn)
    # ---------------- B9 VWAP reclaim
    pvw = np.concatenate([[np.nan], vw1[:-1]])
    cross = (m1["pc"] <= pvw) & (m1["c"] > vw1) & ~m1["newday"]
    dev = (m1["c"] - vw1) / a15
    mindev = pd.Series(dev).shift(1).rolling(30, min_periods=10).min().values
    firstx = pd.Series(cross).groupby(b.day[W1]).cumsum().values == 1
    add("B9_vwap_cross", "B9", to_1m(m1, cross, n))
    add("B9_vwap_first", "B9", to_1m(m1, cross & firstx, n), var="first")
    add("B9_vwap_deep", "B9", to_1m(m1, cross & (mindev <= -1.5), n), var="deep")
    add("B9_vwap_rngexp", "B9", to_1m(m1, cross & (m1["rng"] >= 1.5 * m1["ravg"]), n), var="rngexp")
    add("B9_vwap_slope", "B9", to_1m(m1, cross & (mom60 > 0), n), var="slope")
    m5 = M[5]
    vw5 = _fget(F, "vwap", m5)
    pvw5 = np.concatenate([[np.nan], vw5[:-1]])
    cross5 = (m5["pc"] <= pvw5) & (m5["c"] > vw5) & ~m5["newday"]
    dev5 = (m5["c"] - vw5) / np.maximum(_fget(F, "atr15", m5), 0.25)
    mind5 = pd.Series(dev5).shift(1).rolling(6, min_periods=3).min().values
    add("B9_tf5_vwap_cross", "B9", to_1m(m5, cross5, n), tf=5)
    add("B9_tf5_vwap_deep", "B9", to_1m(m5, cross5 & (mind5 <= -1.5), n), tf=5, var="deep")
    # ---------------- B10 micro channel
    for k in (1, 3):
        m = M[k]
        hl = (m["l"] > m["pl"]) & (m["c"] > m["pc"]) & ~m["newday"]
        run = pd.Series(hl.astype(int)).groupby((~hl).cumsum()).cumsum().values
        for kk in (2, 3, 4):
            add(f"B10_tf{k}_hl{kk}", "B10", to_1m(m, run == kk, n), tf=k, k=kk)
            hh = prior_max(m["h"], kk + 2, m["nb"])
            add(f"B10_tf{k}_hl{kk}_brk", "B10", to_1m(m, (run >= kk) & (m["c"] > hh), n), tf=k, k=kk, var="brk")
    # ---------------- B11 volatility burst
    for k in (1, 5):
        m = M[k]
        rel = _fget(F, "atr15_rel", m)
        hh5 = prior_max(m["h"], 5, m["nb"])
        lowv = (rel < 0.8) & (m["rng"] >= 2.5 * m["ravg"]) & (m["cl"] >= 0.75) & (m["body"] > 0)
        highv = (rel > 1.3) & (m["rng"] >= 2.0 * m["ravg"]) & (m["cl"] >= 0.75) & (m["c"] > hh5)
        add(f"B11_tf{k}_lowvol_burst", "B11", to_1m(m, lowv, n), tf=k, var="lowvol")
        add(f"B11_tf{k}_highvol_burst", "B11", to_1m(m, highv, n), tf=k, var="highvol")
    # ---------------- B12 momentum after selloff
    sdd = (m1["c"] - _fget(F, "sess_high", m1)) / a15
    mom30 = np.nan_to_num(_fget(F, "mom30", m1)) / a15
    sell_dd = pd.Series(sdd).rolling(30, min_periods=1).min().values <= -3.0
    sell_mom = pd.Series(mom30).rolling(30, min_periods=1).min().values <= -2.0
    for k in (1, 3):
        m = M[k]
        cidx = np.maximum(m["comp"], 0)
        # map 1m selloff flags (known at the completion bar) onto the MTF sequence
        full_dd = np.zeros(n, bool); full_dd[W1] = sell_dd
        full_mm = np.zeros(n, bool); full_mm[W1] = sell_mom
        hh5 = prior_max(m["h"], 5, m["nb"])
        imp = (m["c"] > hh5) & (m["body"] >= 1.0 * m["atr"]) & (m["cl"] >= 0.75)
        add(f"B12_tf{k}_after_ddsell", "B12", to_1m(m, imp & full_dd[cidx], n), tf=k, var="sessdd")
        add(f"B12_tf{k}_after_momsell", "B12", to_1m(m, imp & full_mm[cidx], n), tf=k, var="mom30")
    # restrict to tradeable decision bars with a valid next bar is done by the simulators
    return ev, meta, M
