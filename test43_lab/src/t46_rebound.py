"""TEST46 Lane B: structural failed-selling rebound engine (ES / MNQ, LONG only, intraday, no overnight path).
Mechanism grammar (every family): DISPLACEMENT (session open -> low >= D x ATRd) + STRUCTURAL LOCATION (a causal level) +
FAILURE (no new low for k bars after the break) + RECLAIM (5m close back above the level + rho x ATRd, within N bars)
+ REGIME (crash veto on 5-day return / opening gap; optional HTF-bull requirement).
Families: 1 B1 prior-day RTH low, 2 B1 5-session low, 3 B2 VWAP lower band (k sigma), 4 B3 30-min opening-range low,
5 B4 range exhaustion (level = session low once >= D ATR consumed), 6 B5 HTF-bull pullback (level = VWAP, requires HTF bull),
7 B6 NQ relative exhaustion (NQ underperforms ES by >= X ATR at the break; NQ only).
Timing: signal at the close of 5m bar e -> fill at the open of bar e+1 (1m grid index 5*(e+1)).  All levels use completed
information only; ATRd = previous-session RTH ATR14; no bar after the decision is read."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t46_common as C  # noqa: E402

NB = 81          # 5m RTH bars 09:30..16:10
FAMS = {1: "B1 failed break of prior-day low", 2: "B1 failed break of 5-session low", 3: "B2 VWAP lower-band excursion + reclaim",
        4: "B3 opening-range (30m) failed breakdown", 5: "B4 range exhaustion + structural reversal", 6: "B5 HTF-bull pullback + VWAP reclaim",
        7: "B6 NQ relative exhaustion (vs ES) + reclaim"}


class Market:
    """per-instrument session x 5m-bar arrays aligned to the TEST45 1m panel sessions."""

    def __init__(self, P, inst):
        self.inst = inst
        pn = C45.Panel(P, inst)
        self.pn = pn
        n = pn.n
        O, H, L, Cc, V = pn.O, pn.H, pn.L, pn.C, pn.V
        # 5m bar b covers 1m grid [5b, 5b+5)
        idx = np.arange(NB)[:, None] * 5 + np.arange(5)[None, :]
        idx = np.minimum(idx, C45.NG - 1)
        self.o = O[:, idx[:, 0]]
        self.h = np.nanmax(H[:, idx], axis=2)
        self.l = np.nanmin(L[:, idx], axis=2)
        cc = Cf = pn.Cf
        self.c = Cf[:, idx[:, -1]]
        self.vw = pn.vwap[:, idx[:, -1]]
        tp = np.nan_to_num((H + L + Cc) / 3); vv = np.nan_to_num(V)
        cv = np.cumsum(vv, 1); cpv = np.cumsum(tp * vv, 1); cp2 = np.cumsum(tp * tp * vv, 1)
        var = np.where(cv > 0, cp2 / np.where(cv > 0, cv, 1) - (cpv / np.where(cv > 0, cv, 1)) ** 2, np.nan)
        self.vsd = np.sqrt(np.maximum(var, 0))[:, idx[:, -1]]
        self.atr = pn.atr
        self.open = pn.open
        self.pdl = pn.p_l
        lows = pd.Series(pn.rth_l)
        self.l5 = lows.rolling(5, min_periods=5).min().shift(1).values
        ma20 = pd.Series(pn.cash_close).rolling(20, min_periods=15).mean()
        self.bull = ((pd.Series(pn.cash_close) > ma20) & (ma20 > ma20.shift(5))).shift(1).fillna(False).values.astype(np.bool_)
        self.ret5 = ((pd.Series(pn.cash_close) - pd.Series(pn.cash_close).shift(5)) / pd.Series(pn.atr)).shift(1).fillna(0).values
        self.gap = np.nan_to_num(pn.gap_lock / pn.atr)
        self.or30 = np.nanmin(self.l[:, :6], 1)
        self.volt = pd.Series(pn.vol_pct).fillna(0.5).values
        self.FP = None
        self.n = n


def attach_fills(mk, sim):
    mk.FP = sim.FP; mk.FPb = sim.FPb; mk.L1 = sim.pn.L; mk.pv = sim.pv; mk.k = sim.k


@njit(cache=True)
def detect(o, h, l, c, vw, vsd, atr, opn, pdl, l5, or30, bull, ret5, gap, rel,
           fam, D, delta, k, N, rho, e0, e1, veto5, vetogap, need_bull, band, relx):
    """returns per-session event bar (-1 none) and break-low price."""
    n = o.shape[0]
    ev = np.full(n, -1, np.int64); brk = np.full(n, np.nan)
    for s in range(n):
        a = atr[s]
        if not (a > 0) or np.isnan(opn[s]):
            continue
        if ret5[s] < -veto5 or gap[s] < -vetogap:
            continue
        if need_bull and not bull[s]:
            continue
        if fam == 6 and not bull[s]:
            continue
        broke = -1; blow = 1e18; last_new_low = -1; slow = 1e18; shigh = -1e18; brk_lev = np.nan
        for b in range(o.shape[1]):
            if np.isnan(l[s, b]):
                continue
            # level (causal: uses information through bar b-1 for intraday levels, prior sessions for daily levels)
            if fam == 1:
                lev = pdl[s]
            elif fam == 2:
                lev = l5[s]
            elif fam == 3:
                lev = (vw[s, b - 1] - band * vsd[s, b - 1]) if b > 0 else np.nan
            elif fam == 4:
                lev = or30[s] if b >= 6 else np.nan
            elif fam == 5:
                lev = slow if (opn[s] - slow) >= D * a else np.nan
            elif fam == 6:
                lev = vw[s, b - 1] if b > 0 else np.nan
            else:
                lev = slow if (rel[s, b] <= -relx) else np.nan
            prev_slow = slow
            slow = min(slow, l[s, b]); shigh = max(shigh, h[s, b])
            disp = ((shigh - slow) if fam == 6 else (opn[s] - slow)) / a
            if broke < 0:
                if not np.isnan(lev) and l[s, b] <= lev - delta * a and disp >= D and b >= e0 and b <= e1:
                    broke = b; blow = l[s, b]; last_new_low = b; brk_lev = lev
                continue
            if l[s, b] < blow:
                blow = l[s, b]; last_new_low = b
            if b - broke > N:
                broke = -1; blow = 1e18
                continue
            lv = brk_lev if (fam == 1 or fam == 2 or fam == 4 or fam == 5 or fam == 7) else lev
            if np.isnan(lv):
                continue
            if b - last_new_low >= k and c[s, b] > lv + rho * a and c[s, b] > o[s, b] and b <= e1:
                if b + 1 < o.shape[1]:
                    ev[s] = b; brk[s] = blow
                break
    return ev, brk


@njit(cache=True)
def trade_pnl(ev, brk, FP, FPb, L1, atr, exit_mode, hold_min, stop_atr, pv, cs, ng, j1600, j1615):
    """1 contract long from fill 5*(ev+1); exit after hold_min minutes or at 16:00 / 16:15 (exit_mode 0/1/2); optional stop
    at break-low - stop_atr*ATR (checked on 1m lows, filled at the stop or the bar open if lower).  Returns daily $ P&L."""
    n = ev.shape[0]
    pnl = np.zeros(n); jin = np.full(n, -1, np.int64); jout = np.full(n, -1, np.int64)
    for s in range(n):
        if ev[s] < 0:
            continue
        j = 5 * (ev[s] + 1)
        if j >= ng:
            continue
        px = FP[s, j]
        if np.isnan(px):
            continue
        if exit_mode == 0:
            jx = min(j + hold_min, j1615)
        elif exit_mode == 1:
            jx = j1600
        else:
            jx = j1615
        if jx <= j:
            continue
        stop = brk[s] - stop_atr * atr[s] if stop_atr >= 0 else -1e18
        xp = np.nan
        for jj in range(j, jx):
            lo = L1[s, jj]
            if not np.isnan(lo) and lo <= stop:
                op = FP[s, jj]
                xp = min(stop, op) if (not np.isnan(op) and jj > j) else stop
                jx = jj
                break
        if np.isnan(xp):
            xp = FPb[s, jx]
        if np.isnan(xp):
            continue
        pnl[s] = (xp - px) * pv - 2 * cs
        jin[s] = j; jout[s] = jx
    return pnl, jin, jout


def rel_array(mnq, es):
    """NQ minus ES return since the open, each in own ATRd units, at bar close (NQ only; causal)."""
    r_n = (mnq.c - mnq.open[:, None]) / mnq.atr[:, None]
    r_e = (es.c - es.open[:, None]) / es.atr[:, None]
    return np.nan_to_num(r_n - r_e, nan=0.0)


DEFAULTS = {  # predeclared simple controls (T46_21): broad, round values, chosen before any Lane-B result
    1: dict(D=0.5, delta=0.10, k=2, N=12, rho=0.0, e0=2, e1=60, veto5=3.0, vetogap=1.5, need_bull=0, band=2.0, relx=0.5),
    2: dict(D=0.5, delta=0.10, k=2, N=12, rho=0.0, e0=2, e1=60, veto5=3.0, vetogap=1.5, need_bull=0, band=2.0, relx=0.5),
    3: dict(D=0.5, delta=0.0, k=2, N=12, rho=0.0, e0=3, e1=60, veto5=3.0, vetogap=1.5, need_bull=0, band=2.0, relx=0.5),
    4: dict(D=0.3, delta=0.05, k=2, N=12, rho=0.0, e0=6, e1=60, veto5=3.0, vetogap=1.5, need_bull=0, band=2.0, relx=0.5),
    5: dict(D=1.0, delta=0.0, k=3, N=12, rho=0.25, e0=3, e1=60, veto5=3.0, vetogap=1.5, need_bull=0, band=2.0, relx=0.5),
    6: dict(D=0.75, delta=0.0, k=2, N=12, rho=0.0, e0=3, e1=60, veto5=3.0, vetogap=1.5, need_bull=1, band=2.0, relx=0.5),
    7: dict(D=0.5, delta=0.0, k=3, N=12, rho=0.25, e0=3, e1=60, veto5=3.0, vetogap=1.5, need_bull=0, band=2.0, relx=0.5),
}


def run_detect(mk, fam, p, rel=None):
    r = rel if rel is not None else np.zeros_like(mk.c)
    return detect(mk.o, mk.h, mk.l, mk.c, mk.vw, mk.vsd, mk.atr, mk.open, mk.pdl, mk.l5, mk.or30, mk.bull, mk.ret5, mk.gap, r,
                  fam, p["D"], p["delta"], int(p["k"]), int(p["N"]), p["rho"], int(p["e0"]), int(p["e1"]), p["veto5"], p["vetogap"],
                  bool(p["need_bull"]), p["band"], p["relx"])


def run_trades(mk, ev, brk, exit_mode=1, hold=120, stop_atr=-1.0, slip=1.0):
    cs = C45.cost_side(mk.k, slip) / 1.0
    return trade_pnl(ev, brk, mk.FP, mk.FPb, mk.L1, mk.atr, exit_mode, hold, stop_atr, mk.pv, cs, C45.NG, C45.g("16:00"), C45.g("16:15"))
