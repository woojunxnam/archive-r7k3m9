"""TEST43-M — qualified balance / range detection, frozen-range state machines, outcomes.

Everything is causal: the value at bar i uses completed bars <= i only.  Qualification thresholds are
per-session percentiles of the PREVIOUS `lookback` sessions (never the current or future sessions).
A qualified range is FROZEN at the bar it qualifies; its boundaries never move afterwards.
Events are stamped at the completed bar that confirms the state; outcomes are measured from the NEXT bar open.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from numba import njit

# event codes ---------------------------------------------------------------------------------------------
EV = [
    "NONE",
    # lower-boundary sweep machine (bullish reclaim candidates)
    "L_SWEEP", "L_RECLAIM", "L_RETEST", "L_RETEST_HOLD", "L_RESUMPTION", "L_FAILED_RECLAIM", "L_FAILED_RETEST",
    "L_RANGE_REENTRY",
    # upper-boundary sweep machine (bearish rejection candidates)
    "U_SWEEP", "U_RECLAIM", "U_RETEST", "U_RETEST_HOLD", "U_RESUMPTION", "U_FAILED_RECLAIM", "U_FAILED_RETEST",
    "U_RANGE_REENTRY",
    # upside breakout machine
    "UB_BREAK", "UB_ACCEPT", "UB_RETEST", "UB_RETEST_HOLD", "UB_RESUMED", "UB_FAILED_ACCEPT", "UB_REENTRY",
    # downside breakout machine (descriptive)
    "DB_BREAK", "DB_ACCEPT", "DB_RETEST", "DB_RETEST_HOLD", "DB_RESUMED", "DB_FAILED_ACCEPT", "DB_REENTRY",
    # balance lifecycle
    "BAL_NEW", "BAL_REFREEZE", "BAL_NEW_AFTER_EXP",
]
EVI = {n: i for i, n in enumerate(EV)}
STATES = ["NONE", "BALANCE", "COMPRESSION", "BREAKOUT_ATTEMPT", "ACCEPTED_EXPANSION", "FAILED_BREAK", "RETEST",
          "RANGE_REENTRY", "NEW_BALANCE"]
HORIZONS = {"15m": 5, "30m": 10, "60m": 20, "120m": 40}  # in 3m bars


@njit(cache=True)
def window_metrics(h, l, c, atr14, H):
    """Trailing-window balance metrics over bars [i-H+1, i]."""
    n = len(c)
    hi = np.full(n, np.nan); lo = np.full(n, np.nan); eff = np.full(n, np.nan); ovl = np.full(n, np.nan)
    rvr = np.full(n, np.nan); cdisp = np.full(n, np.nan); tl = np.zeros(n, np.int64); th = np.zeros(n, np.int64)
    wn = np.full(n, np.nan)
    L = 4 * H
    for i in range(L, n):
        a = i - H + 1
        mx = -1e18; mn = 1e18
        for j in range(a, i + 1):
            if h[j] > mx:
                mx = h[j]
            if l[j] < mn:
                mn = l[j]
        w = mx - mn
        hi[i] = mx; lo[i] = mn
        path = 0.0; ov = 0.0; s1 = 0.0; s2 = 0.0; cs = 0.0; cs2 = 0.0
        for j in range(a, i + 1):
            d = c[j] - c[j - 1]
            path += abs(d); s1 += d; s2 += d * d
            u = max(h[j], h[j - 1]) - min(l[j], l[j - 1])
            if u > 0:
                ov += max(0.0, min(h[j], h[j - 1]) - max(l[j], l[j - 1])) / u
            cs += c[j]; cs2 += c[j] * c[j]
            if w > 0:
                if l[j] <= mn + 0.25 * w:
                    tl[i] += 1
                if h[j] >= mx - 0.25 * w:
                    th[i] += 1
        eff[i] = abs(c[i] - c[a - 1]) / path if path > 0 else 0.0
        ovl[i] = ov / H
        # realised-vol contraction: sd of H-window changes vs sd over the 4H window
        sd_s = math.sqrt(max(s2 / H - (s1 / H) ** 2, 0.0))
        t1 = 0.0; t2 = 0.0
        for j in range(i - L + 1, i + 1):
            d = c[j] - c[j - 1]
            t1 += d; t2 += d * d
        sd_l = math.sqrt(max(t2 / L - (t1 / L) ** 2, 0.0))
        rvr[i] = sd_s / sd_l if sd_l > 0 else np.nan
        mc = cs / H
        cdisp[i] = math.sqrt(max(cs2 / H - mc * mc, 0.0)) / w if w > 0 else np.nan
        wn[i] = w / (atr14[i] * math.sqrt(H)) if atr14[i] > 0 else np.nan
    return hi, lo, eff, ovl, rvr, cdisp, tl, th, wn


def causal_quantiles(x, sess_code, rth, qs, lookback=60, min_sessions=20):
    """Per-bar thresholds = quantiles of x over the previous `lookback` sessions (same RTH/ON side)."""
    n = len(x)
    out = np.full((n, len(qs)), np.nan)
    df = pd.DataFrame({"s": sess_code, "r": rth, "x": x})
    for side in (True, False):
        m = df.r.values == side
        g = df[m].groupby("s").x.apply(lambda v: v.dropna().values[::2])
        keys = g.index.values; vals = list(g.values)
        thr = {}
        for k in range(len(keys)):
            if k < min_sessions:
                continue
            pool = np.concatenate(vals[max(0, k - lookback):k])
            if len(pool) > 50:
                thr[keys[k]] = np.quantile(pool, qs)
        idx = np.where(m)[0]
        sk = sess_code[idx]
        for k, t in thr.items():
            out[idx[sk == k]] = t
    return out


@njit(cache=True)
def state_machine(o, h, l, c, atrD, hi, lo, qual, comp, H, sess, maxAge):
    """Frozen-range lifecycle + sweep (both edges) + breakout (both sides) machines for one horizon.

    Returns per-bar arrays (active, rL, rH, state, range id) and an event list (bar, code, rid, rL, rH, extreme, age).
    """
    n = len(c)
    act = np.zeros(n, np.bool_); RL = np.full(n, np.nan); RH = np.full(n, np.nan); st = np.zeros(n, np.int64)
    rid_arr = np.full(n, -1, np.int64)
    cap = 3 * n + 1000
    e_bar = np.zeros(cap, np.int64); e_code = np.zeros(cap, np.int64); e_rid = np.zeros(cap, np.int64)
    e_rl = np.zeros(cap); e_rh = np.zeros(cap); e_x = np.zeros(cap); e_age = np.zeros(cap, np.int64)
    ne = 0
    M = max(2, H // 2)           # bars allowed for reclaim
    A = max(2, H // 5)           # consecutive closes outside for acceptance
    N = H                        # bars allowed for retest / resumption
    active = False; rL = 0.0; rH = 0.0; rid = -1; frozeAt = -1; expanded = False
    # machine states: 0 idle
    ls = 0; lx = 0.0; lbar = 0; lref = 0; lmax = 0.0; ldep = False      # lower sweep
    us = 0; ux = 0.0; ubar = 0; uref = 0; umin = 0.0; udep = False      # upper sweep
    bs = 0; bcnt = 0; bbar = 0; bmax = 0.0; bdep = False                # up-break
    ds = 0; dcnt = 0; dbar = 0; dmin = 0.0; ddep = False                # down-break
    curstate = 0
    for i in range(n):
        # ---------------- range lifecycle (freeze at the qualifying bar close)
        busy = ls != 0 or us != 0 or bs != 0 or ds != 0
        if qual[i] and not np.isnan(hi[i]):
            code = 0
            if not active:
                code = 31
            elif expanded and not busy:
                code = 33
            elif (not busy) and i - frozeAt >= max(1, H // 2) and c[i] <= rH and c[i] >= rL:
                code = 32
            if code != 0 and ne < cap:
                active = True; rL = lo[i]; rH = hi[i]; rid += 1; frozeAt = i; expanded = False
                ls = 0; us = 0; bs = 0; ds = 0
                curstate = 8 if code == 33 else (2 if comp[i] else 1)
                e_bar[ne] = i; e_code[ne] = code; e_rid[ne] = rid; e_rl[ne] = rL; e_rh[ne] = rH; e_x[ne] = 0.0
                e_age[ne] = 0; ne += 1
                act[i] = True; RL[i] = rL; RH[i] = rH; st[i] = curstate; rid_arr[i] = rid
                continue
        if active and (not busy) and i - frozeAt > maxAge:
            active = False; curstate = 0
        if not active:
            st[i] = 0
            continue
        w = rH - rL
        tol = 0.1 * w
        age = i - frozeAt
        codes = np.zeros(8, np.int64); nc = 0
        xs = np.zeros(8)
        # ---------------- lower sweep machine
        if ls == 0:
            if l[i] < rL and not expanded:
                ls = 1; lx = l[i]; lbar = i
                codes[nc] = 1; xs[nc] = lx; nc += 1
                if c[i] >= rL:
                    ls = 2; lref = i; lmax = h[i]; ldep = False
                    codes[nc] = 2; xs[nc] = lx; nc += 1
        elif ls == 1:
            lx = min(lx, l[i])
            if c[i] >= rL:
                ls = 2; lref = i; lmax = h[i]; ldep = False
                codes[nc] = 2; xs[nc] = lx; nc += 1
            elif i - lbar >= M:
                ls = 0
                codes[nc] = 6; xs[nc] = lx; nc += 1
        elif ls == 2:
            lmax = max(lmax, h[i])
            if i > lref and l[i] > rL + tol:
                ldep = True
            if ldep and l[i] <= rL + tol:
                codes[nc] = 3; xs[nc] = lx; nc += 1
                if c[i] >= rL and l[i] > lx:
                    ls = 4
                    codes[nc] = 4; xs[nc] = lx; nc += 1
                else:
                    ls = 0
                    codes[nc] = 7; xs[nc] = lx; nc += 1
            elif c[i] < rL:
                ls = 0
                codes[nc] = 7; xs[nc] = lx; nc += 1
            elif c[i] >= rL + 0.5 * w and ls == 2:
                codes[nc] = 8; xs[nc] = lx; nc += 1
                ls = 5  # re-entered to mid without retest: retest window continues silently
            elif i - lref >= N:
                ls = 0
        elif ls == 5:
            lmax = max(lmax, h[i])
            if l[i] <= rL + tol:
                codes[nc] = 3; xs[nc] = lx; nc += 1
                if c[i] >= rL and l[i] > lx:
                    ls = 4
                    codes[nc] = 4; xs[nc] = lx; nc += 1
                else:
                    ls = 0
                    codes[nc] = 7; xs[nc] = lx; nc += 1
            elif i - lref >= N:
                ls = 0
        elif ls == 4:
            if c[i] > lmax:
                ls = 0
                codes[nc] = 5; xs[nc] = lx; nc += 1
            elif c[i] < rL or i - lref >= 2 * N:
                ls = 0
            lmax = max(lmax, h[i])
        # ---------------- upper sweep machine (mirror)
        if us == 0:
            if h[i] > rH and not expanded:
                us = 1; ux = h[i]; ubar = i
                codes[nc] = 9; xs[nc] = ux; nc += 1
                if c[i] <= rH:
                    us = 2; uref = i; umin = l[i]; udep = False
                    codes[nc] = 10; xs[nc] = ux; nc += 1
        elif us == 1:
            ux = max(ux, h[i])
            if c[i] <= rH:
                us = 2; uref = i; umin = l[i]; udep = False
                codes[nc] = 10; xs[nc] = ux; nc += 1
            elif i - ubar >= M:
                us = 0
                codes[nc] = 14; xs[nc] = ux; nc += 1
        elif us == 2 or us == 5:
            umin = min(umin, l[i])
            if i > uref and h[i] < rH - tol:
                udep = True
            if udep and h[i] >= rH - tol:
                codes[nc] = 11; xs[nc] = ux; nc += 1
                if c[i] <= rH and h[i] < ux:
                    us = 4
                    codes[nc] = 12; xs[nc] = ux; nc += 1
                else:
                    us = 0
                    codes[nc] = 15; xs[nc] = ux; nc += 1
            elif c[i] > rH:
                us = 0
                codes[nc] = 15; xs[nc] = ux; nc += 1
            elif us == 2 and c[i] <= rH - 0.5 * w:
                codes[nc] = 16; xs[nc] = ux; nc += 1
                us = 5
            elif i - uref >= N:
                us = 0
        elif us == 4:
            if c[i] < umin:
                us = 0
                codes[nc] = 13; xs[nc] = ux; nc += 1
            elif c[i] > rH or i - uref >= 2 * N:
                us = 0
            umin = min(umin, l[i])
        # ---------------- upside breakout machine
        if bs == 0:
            if c[i] > rH and not expanded:
                bs = 1; bcnt = 1; bbar = i; bmax = h[i]
                codes[nc] = 17; xs[nc] = h[i]; nc += 1
                curstate = 3
        elif bs == 1:
            bmax = max(bmax, h[i])
            if c[i] > rH:
                bcnt += 1
                if bcnt >= A:
                    bs = 2; expanded = True; curstate = 4; bdep = False
                    codes[nc] = 18; xs[nc] = bmax; nc += 1
            else:
                bs = 0; curstate = 5
                codes[nc] = 22; xs[nc] = bmax; nc += 1
        elif bs == 2:
            if l[i] > rH + tol:
                bdep = True
            if bdep and l[i] <= rH + tol:
                codes[nc] = 19; xs[nc] = bmax; nc += 1
                curstate = 6
                if c[i] > rH:
                    bs = 3
                    codes[nc] = 20; xs[nc] = bmax; nc += 1
                else:
                    bs = 0; curstate = 7
                    codes[nc] = 23; xs[nc] = bmax; nc += 1
            elif c[i] <= rH:
                bs = 0; curstate = 7
                codes[nc] = 23; xs[nc] = bmax; nc += 1
            elif i - bbar >= 2 * N:
                bs = 0
            bmax = max(bmax, h[i])
        elif bs == 3:
            if c[i] > bmax:
                bs = 0; curstate = 4
                codes[nc] = 21; xs[nc] = bmax; nc += 1
            elif c[i] <= rH:
                bs = 0; curstate = 7
                codes[nc] = 23; xs[nc] = bmax; nc += 1
            elif i - bbar >= 3 * N:
                bs = 0
            bmax = max(bmax, h[i])
        # ---------------- downside breakout machine (descriptive mirror)
        if ds == 0:
            if c[i] < rL and not expanded:
                ds = 1; dcnt = 1; dbar = i; dmin = l[i]
                codes[nc] = 24; xs[nc] = l[i]; nc += 1
                curstate = 3
        elif ds == 1:
            dmin = min(dmin, l[i])
            if c[i] < rL:
                dcnt += 1
                if dcnt >= A:
                    ds = 2; expanded = True; curstate = 4; ddep = False
                    codes[nc] = 25; xs[nc] = dmin; nc += 1
            else:
                ds = 0; curstate = 5
                codes[nc] = 29; xs[nc] = dmin; nc += 1
        elif ds == 2:
            if h[i] < rL - tol:
                ddep = True
            if ddep and h[i] >= rL - tol:
                codes[nc] = 26; xs[nc] = dmin; nc += 1
                curstate = 6
                if c[i] < rL:
                    ds = 3
                    codes[nc] = 27; xs[nc] = dmin; nc += 1
                else:
                    ds = 0; curstate = 7
                    codes[nc] = 30; xs[nc] = dmin; nc += 1
            elif c[i] >= rL:
                ds = 0; curstate = 7
                codes[nc] = 30; xs[nc] = dmin; nc += 1
            elif i - dbar >= 2 * N:
                ds = 0
            dmin = min(dmin, l[i])
        elif ds == 3:
            if c[i] < dmin:
                ds = 0; curstate = 4
                codes[nc] = 28; xs[nc] = dmin; nc += 1
            elif c[i] >= rL:
                ds = 0; curstate = 7
                codes[nc] = 30; xs[nc] = dmin; nc += 1
            elif i - dbar >= 3 * N:
                ds = 0
            dmin = min(dmin, l[i])
        if bs == 0 and ds == 0 and curstate in (3, 5, 6, 7) and c[i] <= rH and c[i] >= rL:
            curstate = 1
        if curstate == 0:
            curstate = 1
        for k in range(nc):
            if ne < cap:
                e_bar[ne] = i; e_code[ne] = codes[k]; e_rid[ne] = rid; e_rl[ne] = rL; e_rh[ne] = rH; e_x[ne] = xs[k]
                e_age[ne] = age; ne += 1
        act[i] = True; RL[i] = rL; RH[i] = rH; st[i] = curstate; rid_arr[i] = rid
    return act, RL, RH, st, rid_arr, e_bar[:ne], e_code[:ne], e_rid[:ne], e_rl[:ne], e_rh[:ne], e_x[:ne], e_age[:ne]


@njit(cache=True)
def outcomes(o, h, l, c, atrD, sess, in_rth, hs):
    """Forward outcomes from entry at o[i+1], in daily-ATR units.  NaN when the window runs past the data."""
    n = len(c)
    K = len(hs)
    ret = np.full((n, K), np.nan); mfe = np.full((n, K), np.nan); mae = np.full((n, K), np.nan)
    fp05 = np.full(n, np.nan); fp10 = np.full(n, np.nan)
    rthc = np.full(n, np.nan); on = np.full(n, np.nan); nxo = np.full(n, np.nan)
    # last RTH close index per session and next-session first RTH open
    last_rth = np.full(n, -1, np.int64); next_open = np.full(n, -1, np.int64)
    lr = -1
    for i in range(n - 1, -1, -1):
        if i == n - 1 or sess[i + 1] != sess[i]:
            lr = -1
        if lr == -1 and in_rth[i]:
            lr = i
        last_rth[i] = lr
    nx = -1; cur_first = -1
    for i in range(n - 1, -1, -1):
        if in_rth[i] and (i == 0 or not in_rth[i - 1] or sess[i - 1] != sess[i]):
            cur_first = i
        if i == n - 1 or sess[i + 1] != sess[i]:
            nx = cur_first
        next_open[i] = nx if (nx >= 0 and sess[nx] != sess[i]) else -1
    Hmax = hs[K - 1]
    for i in range(n - 1):
        a = atrD[i]
        if not (a > 0):
            continue
        e = o[i + 1]
        mx = -1e18; mn = 1e18
        k = 0
        r05 = 0; r10 = 0
        for j in range(i + 1, min(n, i + 1 + Hmax)):
            if h[j] > mx:
                mx = h[j]
            if l[j] < mn:
                mn = l[j]
            up = (mx - e) / a; dn = (mn - e) / a
            if r05 == 0:
                if dn <= -0.5:
                    r05 = -1
                elif up >= 0.5:
                    r05 = 1
            if r10 == 0:
                if dn <= -0.5:
                    r10 = -1
                elif up >= 1.0:
                    r10 = 1
            step = j - i
            while k < K and step == hs[k]:
                ret[i, k] = (c[j] - e) / a; mfe[i, k] = up; mae[i, k] = dn
                k += 1
        # first passage, conditional on resolution inside the window (unresolved = NaN, avoids a volatility artefact)
        if i + Hmax < n:
            fp05[i] = 1.0 if r05 == 1 else (0.0 if r05 == -1 else np.nan)
            fp10[i] = 1.0 if r10 == 1 else (0.0 if r10 == -1 else np.nan)
        lri = last_rth[i]
        if in_rth[i] and lri > i:
            rthc[i] = (c[lri] - e) / a
        nxi = next_open[i]
        if nxi > 0:
            nxo[i] = (o[nxi] - e) / a
            if lri >= 0:
                on[i] = (o[nxi] - c[lri]) / a
    return ret, mfe, mae, fp05, fp10, rthc, on, nxo


@njit(cache=True)
def destinations(o, h, l, atrD, e_bar, e_dir, e_inval, e_mid, e_opp, e_w, Hmax):
    """Per event: first passage to mid / opposite boundary / +k*range / +k*ATR before invalidation.

    e_dir=+1 long-side destinations (above), -1 below.  invalidation = price trading through e_inval.
    Returns hit flags / bars-to-hit for mid, opposite and multiples (0.5,1,1.5,2) of width and of ATR, plus MAE
    before mid and MFE after mid (ATR units)."""
    ne = len(e_bar); n = len(o)
    mults = np.array([0.5, 1.0, 1.5, 2.0])
    hit_mid = np.full(ne, np.nan); t_mid = np.full(ne, np.nan); hit_opp = np.full(ne, np.nan); t_opp = np.full(ne, np.nan)
    mae_pre = np.full(ne, np.nan); mfe_post = np.full(ne, np.nan); mfe_all = np.full(ne, np.nan)
    hitR = np.full((ne, 4), np.nan); hitA = np.full((ne, 4), np.nan)
    for q in range(ne):
        i = e_bar[q]
        if i + Hmax >= n or not (atrD[i] > 0):
            continue
        a = atrD[i]; d = e_dir[q]; e = o[i + 1]
        hm = 0; ho = 0; tm = -1; to = -1; worst = 0.0; bestpost = 0.0; best = 0.0
        inval = False
        hr = np.zeros(4); ha = np.zeros(4)
        for j in range(i + 1, i + 1 + Hmax):
            fav = (h[j] - e) if d > 0 else (e - l[j])
            adv = (l[j] - e) if d > 0 else (e - h[j])
            if not inval:
                if (d > 0 and l[j] < e_inval[q]) or (d < 0 and h[j] > e_inval[q]):
                    inval = True
            if inval:
                break
            best = max(best, fav)
            if hm == 0:
                worst = min(worst, adv)
                if (d > 0 and h[j] >= e_mid[q]) or (d < 0 and l[j] <= e_mid[q]):
                    hm = 1; tm = j - i
            else:
                bestpost = max(bestpost, fav)
            if ho == 0 and ((d > 0 and h[j] >= e_opp[q]) or (d < 0 and l[j] <= e_opp[q])):
                ho = 1; to = j - i
            for k in range(4):
                if fav >= mults[k] * e_w[q]:
                    hr[k] = 1
                if fav >= mults[k] * a:
                    ha[k] = 1
        hit_mid[q] = hm; hit_opp[q] = ho
        t_mid[q] = tm if hm else np.nan; t_opp[q] = to if ho else np.nan
        mfe_all[q] = best / a
        mae_pre[q] = worst / a; mfe_post[q] = bestpost / a if hm else np.nan
        for k in range(4):
            hitR[q, k] = hr[k]; hitA[q, k] = ha[k]
    return hit_mid, t_mid, hit_opp, t_opp, mae_pre, mfe_post, mfe_all, hitR, hitA
