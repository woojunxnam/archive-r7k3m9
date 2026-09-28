"""TEST49 continuation engine: causal per-5m-bar strength state (session x bar) and first-trigger entries.
State at 5m bar b uses completed bars <= b only: ret since open (ATRd), path efficiency, share of 5m closes above the running
session TWAP of closes, position in the session range, ORB retention counter."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402
from t47_02_n3 import START  # noqa: E402

NB = 81


class State:
    def __init__(self, mk):
        self.mk = mk
        c, h, l = mk.c, mk.h, mk.l
        o0 = mk.open[:, None]; a = mk.atr[:, None]
        self.ret = (c - o0) / a
        steps = np.abs(np.diff(np.concatenate([o0, c], 1), axis=1))
        path = np.nancumsum(steps, 1)
        self.eff = np.where(path > 0, np.abs(c - o0) / path, 0)
        tw = mk.twap
        prev_tw = np.concatenate([np.full((mk.n, 1), np.nan), tw[:, :-1]], 1)
        ab = (c > prev_tw).astype(float); ab[np.isnan(prev_tw)] = np.nan
        cnt = np.cumsum(~np.isnan(ab), 1)
        self.above = np.where(cnt > 0, np.nancumsum(ab, 1) / np.maximum(cnt, 1), np.nan)
        hi = np.fmax.accumulate(np.where(np.isnan(h), -np.inf, h), 1); lo = np.fmin.accumulate(np.where(np.isnan(l), np.inf, l), 1)
        self.pos = np.where(hi > lo, (c - lo) / (hi - lo), 0.5)
        self.hi, self.lo = hi, lo
        orh = np.nanmax(h[:, :6], 1)
        inside = c <= orh[:, None]
        self.orh = orh
        # bars since first ORB close with no close back inside
        ret_cnt = np.zeros_like(c)
        for s in range(mk.n):
            k = -1
            for b in range(6, NB):
                if np.isnan(c[s, b]):
                    continue
                if k < 0 and c[s, b] > orh[s]:
                    k = b
                if k >= 0:
                    if inside[s, b]:
                        ret_cnt[s, b:] = -1; break
                    ret_cnt[s, b] = b - k + 1
        self.retain = ret_cnt
        self.valid = (mk.pn.sess >= START) & (mk.atr > 0)


def first_trigger(st, cond, b0, b1):
    """first 5m bar in [b0, b1] where cond[s, b] is True (per session)."""
    c = cond.copy(); c[:, :b0] = False; c[:, b1 + 1:] = False
    c &= st.valid[:, None]
    has = c.any(1)
    b = np.where(has, c.argmax(1), -1)
    return b


def family_entries(st, fam, **p):
    """predeclared families (TEST49 prereg).  Returns entry bar per session (-1 none)."""
    g = lambda t: (C45.g(t) + 1) // 5 - 1        # 5m bar whose close is at time t
    if fam == "T1_OPENING_DRIVE":
        t = p.get("t", "10:00"); k = p.get("k", 0.5)
        b = g(t)
        cond = np.zeros_like(st.ret, bool); cond[:, b] = (st.ret[:, b] >= k) & (st.eff[:, b] >= 0.5)
        return first_trigger(st, cond, b, b)
    if fam == "T2_TREND_DAY":
        cond = (st.above >= 0.8) & (st.pos >= 0.7) & (st.ret >= 0.5)
        return first_trigger(st, cond, g("11:00"), g("14:00"))
    if fam == "T3_LATE_STRENGTH":
        b = g(p.get("t", "14:30"))
        cond = np.zeros_like(st.ret, bool); cond[:, b] = (st.ret[:, b] >= 0.5) & (st.pos[:, b] >= 0.8)
        return first_trigger(st, cond, b, b)
    if fam == "T5_BREAKOUT_RETENTION":
        cond = st.retain == 6
        return first_trigger(st, cond, 6, g("15:00"))
    raise ValueError(fam)


def close_strength(st):
    """T4: decision at 16:14 using the 16:14 close (1m) - returns bool per session."""
    mk = st.mk
    c = mk.pn.Cf[:, E.J1615 - 1]
    hi = np.nanmax(mk.pn.H[:, :E.J1615], 1); lo = np.nanmin(mk.pn.L[:, :E.J1615], 1)
    ret = (c - mk.open) / mk.atr
    pos = np.where(hi > lo, (c - lo) / (hi - lo), 0.5)
    return st.valid & (ret >= 0.5) & (pos >= 0.75), ret, pos


def trades(mk, ent_j, rule, slip=1.0):
    """ent_j: fill grid index per session (-1 none).  rule: X1600 / X1615 / NEXTOPEN / NEXT1000.
    Overnight exits are accounted on the exit session (s+1).  Returns daily $, s, j, pnl, exit session."""
    s = np.where(ent_j >= 0)[0]
    j = ent_j[s]
    cs = C45.cost_side(mk.k, slip)
    if rule == "X1600":
        px_out = mk.FPb[s, E.J1600]; s_out = s
    elif rule == "X1615":
        px_out = mk.FPb[s, E.J1615]; s_out = s
    else:
        s = s[s + 1 < mk.n]; j = ent_j[s]
        px_out = mk.FP[s + 1, 0] if rule == "NEXTOPEN" else mk.FPb[s + 1, C45.g("10:00")]
        s_out = s + 1
    pnl = (px_out - mk.FP[s, j]) * mk.pv - 2 * cs
    ok = ~np.isnan(pnl)
    s, j, pnl, s_out = s[ok], j[ok], pnl[ok], s_out[ok]
    d = np.zeros(mk.n); np.add.at(d, s_out, pnl)
    return d, s, j, pnl, s_out


def overnight_base(mk, rule, slip=1.0):
    """unconditional long from grid j to the next open / next 10:00 for every session (matched-null table M, n x NG)."""
    cs = C45.cost_side(mk.k, slip)
    nxt = np.r_[mk.FP[1:, 0], np.nan] if rule == "NEXTOPEN" else np.r_[mk.FPb[1:, C45.g("10:00")], np.nan]
    return (nxt[:, None] - mk.FP) * mk.pv - 2 * cs
