"""TEST48 ARM -> CONFIRM engine (numba).  Arms (setups) and confirmations on completed 5m RTH bars; entry fills at the open of
grid 5(k+1) after the confirming bar k.  Every quantity is causal (bars <= decision bar)."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402
from t47_02_n3 import START, cfg  # noqa: E402

NB = 81
SETUPS = ["S1_N3", "S2_PDL_BREAK", "S3_UPDAY_PULLBACK", "S4_ORB", "S5_COMPRESSION"]
CONFS = ["CF0_IMMEDIATE", "CF1_LOWER_LOW_RECLAIM", "CF2_HIGHER_LOW_BREAKOUT", "CF3_EXPANSION_BAR", "CF4_15M_CONFIRM", "CF5_OTHER_FAMILY"]


@njit(cache=True)
def arms_simple(o, h, l, c, u, atr, opn, pdl, src, xm, bmin, bmax):
    """first arm bar per session for setups 2..5 (-1 none).  xm scales the setup threshold."""
    n, B = c.shape
    arm = np.full(n, -1, np.int64)
    for s in range(n):
        a = atr[s]; us = u[s]
        if not (a > 0) or not (us > 0) or np.isnan(opn[s]):
            continue
        hi = -1e18; orh = -1e18
        for b in range(B):
            if np.isnan(c[s, b]):
                continue
            if h[s, b] > hi:
                hi = h[s, b]
            if b < 6 and h[s, b] > orh:
                orh = h[s, b]
            if b < bmin or b > bmax:
                continue
            ok = False
            if src == 2:
                ok = not np.isnan(pdl[s]) and l[s, b] < pdl[s] - 0.10 * xm * a
            elif src == 3:
                ok = (hi - opn[s]) >= 0.5 * xm * a and (hi - c[s, b]) >= 0.4 * xm * a and c[s, b] > opn[s]
            elif src == 4:
                ok = b >= 6 and c[s, b] > orh
            elif src == 5:
                if b >= 12:
                    mx = -1e18; mn = 1e18
                    for q in range(b - 11, b + 1):
                        if h[s, q] > mx:
                            mx = h[s, q]
                        if l[s, q] < mn:
                            mn = l[s, q]
                    ok = (mx - mn) <= 4.0 * xm * us
            if ok:
                arm[s] = b
                break
    return arm


@njit(cache=True)
def confirm(o, h, l, c, u, arm, other_arm, ctype, W, expx, bmax):
    """entry (confirming) bar per session or -1."""
    n, B = c.shape
    ent = np.full(n, -1, np.int64)
    for s in range(n):
        b0 = arm[s]
        if b0 < 0:
            continue
        us = u[s]
        if ctype == 0:
            if b0 <= bmax:
                ent[s] = b0
            continue
        alow = l[s, b0]; lowest = alow; lowbar = -1; hmax = h[s, b0]; lmin = 1e18
        for k in range(b0 + 1, min(b0 + 1 + W, B)):
            if k > bmax:
                break
            if np.isnan(c[s, k]):
                continue
            if ctype == 1:
                if l[s, k] < lowest:
                    lowest = l[s, k]; lowbar = k
                elif lowbar >= 0 and c[s, k] > h[s, lowbar]:
                    ent[s] = k; break
            elif ctype == 2:
                lmin = min(lmin, l[s, k])
                if lmin < alow:
                    break
                if k >= b0 + 2 and c[s, k] > hmax:
                    ent[s] = k; break
                hmax = max(hmax, h[s, k])
            elif ctype == 3:
                r = h[s, k] - l[s, k]
                if c[s, k] - o[s, k] >= expx * us and r > 0 and (c[s, k] - l[s, k]) / r >= 0.7:
                    ent[s] = k; break
            elif ctype == 4:
                if (k + 1) % 3 == 0 and k >= 5:
                    o15 = o[s, k - 2]; c15 = c[s, k]
                    hp = max(h[s, k - 5], max(h[s, k - 4], h[s, k - 3]))
                    if c15 > o15 and c15 > hp:
                        ent[s] = k; break
            elif ctype == 5:
                if other_arm[s] == k:
                    ent[s] = k; break
    return ent


class ArmBook:
    """per-instrument arms for all setups (first arm per session; S1 = first TEST47 C2 event of the session)."""

    def __init__(self, mk, xm=1.0, bmax=72):
        self.mk = mk
        self.arms = {}
        ev, _, _ = E.run_detect(mk, cfg())
        a1 = np.full(mk.n, -1, np.int64)
        f = ev.groupby("s").b.min()
        a1[f.index.values] = f.values
        self.arms["S1_N3"] = a1
        for i, nm in enumerate(SETUPS[1:], start=2):
            self.arms[nm] = arms_simple(mk.o, mk.h, mk.l, mk.c, mk.u5, mk.atr, mk.open, mk.pdl, i, float(xm), 1, bmax)
        valid = mk.pn.sess >= START
        for k in self.arms:
            self.arms[k] = np.where(valid, self.arms[k], -1)

    def other(self, setup):
        """earliest arm of any OTHER family strictly after this family's arm."""
        a = self.arms[setup]
        out = np.full(len(a), -1, np.int64)
        for k, v in self.arms.items():
            if k == setup:
                continue
            m = (v > a) & (a >= 0)
            out = np.where(m & ((out < 0) | (v < out)), v, out)
        return out


def entries(ab, setup, conf, W=12, expx=1.0, arm=None, bmax=74):
    mk = ab.mk
    a = ab.arms[setup] if arm is None else arm
    return confirm(mk.o, mk.h, mk.l, mk.c, mk.u5, a, ab.other(setup), CONFS.index(conf), int(W), float(expx), bmax)


def trade_daily(mk, ent, rule, slip=1.0, base_M=None, base_rows=None):
    """1 lot, one entry per session; returns daily $ pnl, daily excess vs matched unconditional long (training rows mean), s, j."""
    s = np.where(ent >= 0)[0]
    j = 5 * (ent[s] + 1)
    ok = j <= E.J_LAST_ENTRY
    s, j = s[ok], j[ok]
    if rule in ("X30", "X60", "X120"):
        jx = np.minimum(j + int(rule[1:]), E.J1615)
    elif rule == "X1600":
        jx = np.full(len(j), E.J1600)
    else:
        jx = np.full(len(j), E.J1615)
    cs = C45.cost_side(mk.k, slip)
    pnl = (mk.FPb[s, jx] - mk.FP[s, j]) * mk.pv - 2 * cs
    good = ~np.isnan(pnl) & (jx > j)
    s, j, pnl = s[good], j[good], pnl[good]
    d = np.zeros(mk.n); d[s] = pnl
    return d, s, j, pnl
