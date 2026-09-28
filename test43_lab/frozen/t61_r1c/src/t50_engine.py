"""TEST50 compression -> upside expansion engine (numba).  All decisions on completed 5m bars; fills at grid 5(k+1)."""
import os
import sys

import numpy as np
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402
from t47_02_n3 import START  # noqa: E402

KTYPES = {"K1_RANGE": 1, "K2_RVOL": 2, "K3_CONTRACTION": 3, "NONE": 0}
XTYPES = {"X1_BOX_BREAK": 1, "X2_EXP_BAR": 2, "X3_HL_BREAK": 3, "X4_BREAK_RETEST": 4, "COMP_ONLY": 0}


@njit(cache=True)
def scan(o, h, l, c, u, valid, ktype, kthr, L, xtype, xsize, W, bmin, bmax_arm, bmax_ent):
    """returns entry bar, box low, box high per session (-1 none)."""
    n, B = c.shape
    ent = np.full(n, -1, np.int64); blo = np.full(n, np.nan); bhi = np.full(n, np.nan)
    for s in range(n):
        us = u[s]
        if not valid[s] or not (us > 0):
            continue
        b = max(bmin, L)
        while b <= bmax_arm:
            if np.isnan(c[s, b]):
                b += 1; continue
            # --- compression at bar b (window b-L+1 .. b)
            hi = -1e18; lo = 1e18; nv = 0
            for q in range(b - L + 1, b + 1):
                if not np.isnan(h[s, q]):
                    nv += 1
                if h[s, q] > hi:
                    hi = h[s, q]
                if l[s, q] < lo:
                    lo = l[s, q]
            if nv < L - 1:
                b += 1; continue
            comp = False
            if ktype == 0:
                comp = True
            elif ktype == 1:
                comp = (hi - lo) <= kthr * us
            elif ktype == 2:
                m = 0.0; m2 = 0.0; cnt = 0
                for q in range(b - L + 1, b + 1):
                    if q >= 1 and not np.isnan(c[s, q]) and not np.isnan(c[s, q - 1]):
                        d = c[s, q] - c[s, q - 1]; m += d; m2 += d * d; cnt += 1
                if cnt > 3:
                    var = m2 / cnt - (m / cnt) ** 2
                    comp = np.sqrt(max(var, 0.0)) <= kthr * us
            else:
                shi = -1e18; slo = 1e18
                for q in range(0, b + 1):
                    if h[s, q] > shi:
                        shi = h[s, q]
                    if l[s, q] < slo:
                        slo = l[s, q]
                comp = shi > slo and (hi - lo) <= kthr * (shi - slo)
            if not comp:
                b += 1; continue
            if xtype == 0:
                if b <= bmax_ent:
                    ent[s] = b; blo[s] = lo; bhi[s] = hi
                break
            # --- expansion search within W bars
            found = -1; hmax = hi; lmin = 1e18; broke = -1; held = 0
            for k in range(b + 1, min(b + 1 + W, B)):
                if k > bmax_ent or np.isnan(c[s, k]):
                    break
                if ktype == 0 and xtype != 2:
                    pass
                if xtype == 1:
                    if c[s, k] > hi:
                        found = k; break
                elif xtype == 2:
                    r = h[s, k] - l[s, k]
                    if c[s, k] - o[s, k] >= xsize * us and r > 0 and (c[s, k] - l[s, k]) / r >= 0.7:
                        found = k; break
                elif xtype == 3:
                    lmin = min(lmin, l[s, k])
                    if lmin < lo:
                        break
                    if k >= b + 2 and c[s, k] > hmax:
                        found = k; break
                    hmax = max(hmax, h[s, k])
                else:
                    if broke < 0:
                        if c[s, k] > hi:
                            broke = k; hmax = h[s, k]
                        continue
                    if l[s, k] < 0.5 * (hi + lo):
                        break
                    if held < 2:
                        held += 1; hmax = max(hmax, h[s, k]); continue
                    if c[s, k] > hmax:
                        found = k; break
                    hmax = max(hmax, h[s, k])
            if found >= 0:
                ent[s] = found; blo[s] = lo; bhi[s] = hi
                break
            b += max(W, 1)
    return ent, blo, bhi


@njit(cache=True)
def trade(ent, blo, FP, FPb, L1, u, stop_on, buf, jx_rule, pv, cs, j1600, j1615, nxt):
    """1 lot; exit rule 0=X120 1=X1600 2=X1615 3=NEXTOPEN (nxt = next-session open array).  Stop (if on) = box low - buf*u5 on 1m lows
    during RTH of the entry session only (no overnight stop).  Returns pnl, exit-session offset (0/1)."""
    n = ent.shape[0]
    pnl = np.full(n, np.nan); off = np.zeros(n, np.int64); jin = np.full(n, -1, np.int64)
    for s in range(n):
        if ent[s] < 0:
            continue
        j = 5 * (ent[s] + 1)
        if j > 5 * 72:
            continue
        px = FP[s, j]
        if np.isnan(px):
            continue
        if jx_rule == 0:
            jx = min(j + 120, j1615)
        elif jx_rule == 1:
            jx = j1600
        else:
            jx = j1615
        stp = blo[s] - buf * u[s]
        xp = np.nan
        if stop_on:
            for jj in range(j, jx):
                lo = L1[s, jj]
                if not np.isnan(lo) and lo <= stp:
                    op = FP[s, jj]
                    xp = min(stp, op) if (jj > j and not np.isnan(op)) else stp
                    break
        if np.isnan(xp):
            if jx_rule == 3:
                if s + 1 < n and not np.isnan(nxt[s]):
                    xp = nxt[s]; off[s] = 1
                else:
                    xp = FPb[s, j1615]
            else:
                xp = FPb[s, jx]
        if np.isnan(xp):
            continue
        pnl[s] = (xp - px) * pv - 2 * cs
        jin[s] = j
    return pnl, off, jin


RULES = {"X120": 0, "X1600": 1, "X1615": 2, "NEXTOPEN": 3}


def run(mk, ktype, kthr, L, xtype, xsize=1.0, W=12, stop_on=True, buf=0.5, rule="X1600", slip=1.0, t_start="10:30", mask=None):
    valid = (mk.pn.sess >= START) & (mk.atr > 0)
    if mask is not None:
        valid = valid & mask
    bmin = (C45.g(t_start) + 1) // 5 - 1
    ent, blo, bhi = scan(mk.o, mk.h, mk.l, mk.c, mk.u5, valid, KTYPES[ktype], float(kthr), int(L), XTYPES[xtype], float(xsize), int(W),
                         bmin, (C45.g("14:30") + 1) // 5 - 1, (C45.g("15:00") + 1) // 5 - 1)
    nxt = np.r_[mk.FP[1:, 0], np.nan]
    pnl, off, jin = trade(ent, blo, mk.FP, mk.FPb, mk.pn.L, mk.u5, bool(stop_on), float(buf), RULES[rule], mk.pv, C45.cost_side(mk.k, slip),
                          E.J1600, E.J1615, nxt)
    s = np.where(~np.isnan(pnl))[0]
    d = np.zeros(mk.n); np.add.at(d, s + off[s], pnl[s])
    return d, s, jin[s], pnl[s], off[s]
