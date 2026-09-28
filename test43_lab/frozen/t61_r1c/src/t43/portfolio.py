"""TEST43-P shared-account portfolio simulator.

virtual sleeves (frozen standalone candidates, own virtual ledgers)
  -> risk-unit weights (per-sleeve $ daily-vol normalisation, optional regime tilt)
  -> ONE desired float target per instrument (MES, MNQ)
  -> account governor (portfolio DD tiers, day loss, gross $ATR cap, instrument concentration, intraday/overnight margin)
  -> integer NET target per instrument, traded at the next bar open (1 tick slippage, commission, roll cost).
One shared $150k account: shared equity, drawdown and margin.  Adjusted prices for P&L; raw prices for notional/margin.
"""
from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd
from numba import njit

from . import instruments, lab, v6lab

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
PDIR = os.path.join(ROOT, "out", "p")
INSTS = ("ES", "MNQ")
GOV_DEFAULT = dict(marginU=0.5, dd1_frac=0.6, dd2_frac=0.85, m1=0.5, m2=0.25, day_frac=0.8, day_mult=0.5,
                   atr_cap=0.0, inst_share=0.85, deadband=0.6, slip_ticks=1.0, commission=0.62,
                   m_intra=1.0, m_on=1.0, delay=0)


def timeline(end):
    """Union 3m timeline of ES and MNQ bars (<= end).  Missing bars: price forward-filled, not tradable."""
    fr = {}
    for inst in INSTS:
        b, f = v6lab.load(inst, end)
        prof = instruments.PROFILES[v6lab.PROF[inst]]
        x = pd.DataFrame({"t": b.t.values, "o": b.o.values, "c": b.c.values,
                          "raw": (b.c - b.cum_adjustment.astype(float)).values,
                          "roll": b.roll_adjacent.fillna(False).astype(bool).values, "rth": b.in_rth.values,
                          "sd": b.session_date.values, "atrD": np.nan_to_num(f["d_ATR20"], nan=0.0)}).set_index("t")
        fr[inst] = x
    t = fr["ES"].index.union(fr["MNQ"].index)
    T = pd.DataFrame(index=t)
    for inst, x in fr.items():
        y = x.reindex(t)
        T[f"{inst}_valid"] = y.o.notna().values
        for k in ("o", "c", "raw", "atrD"):
            T[f"{inst}_{k}"] = y[k].ffill().bfill().values
        T[f"{inst}_roll"] = y.roll.fillna(False).astype(bool).values
        T[f"{inst}_rth"] = y.rth.fillna(False).astype(bool).values
        T[f"{inst}_sd"] = y.sd.values
    T["sd"] = pd.Series(T["ES_sd"].values, index=t).fillna(pd.Series(T["MNQ_sd"].values, index=t)).ffill().values
    T["rth"] = T["ES_rth"].values | T["MNQ_rth"].values
    return T


def sleeve_desired(T, cid):
    s = pd.read_parquet(f"{PDIR}/sleeve_{cid}.parquet").set_index("t")
    return s.desired.reindex(T.index).ffill().fillna(0.0).values


@njit(cache=True)
def kernel(o, c, raw, valid, roll, atrD, rth, sessid, D, pv, fin, fon, rollc, INIT, marginU, dd1, dd2, m1, m2,
           dayStop, dayMult, atrCap, instShare, deadband, slip, comm, delay):
    n, K = o.shape
    pos = np.zeros(K, np.int64); avg = np.zeros(K); realized = 0.0
    pend = np.zeros(K, np.int64); pendAt = np.full(K, -1, np.int64)
    pos_arr = np.zeros((n, K), np.int64); eq_arr = np.zeros(n); mu_arr = np.zeros(n); atr_arr = np.zeros(n)
    gov_arr = np.zeros(n); tgt_arr = np.zeros((n, K))
    sides = np.zeros(K); fills = np.zeros(K, np.int64)
    hwm = INIT; level = 0; sessStart = INIT; dayCut = False; prev_eq = INIT
    for i in range(n):
        newSess = i == 0 or sessid[i] != sessid[i - 1]
        # ---- fills at this bar open
        for k in range(K):
            if pend[k] != 0 and valid[i, k] and i - pendAt[k] >= 1 + delay:
                q = pend[k]
                px = o[i, k] + slip if q > 0 else o[i, k] - slip
                if q > 0:
                    avg[k] = (avg[k] * pos[k] + px * q) / (pos[k] + q)
                else:
                    realized += (px - avg[k]) * pv[k] * (-q)
                pos[k] += q
                realized -= abs(q) * comm
                sides[k] += abs(q); fills[k] += 1
                if pos[k] == 0:
                    avg[k] = 0.0
                pend[k] = 0; pendAt[k] = -1
        if newSess:
            for k in range(K):
                if roll[i, k] and pos[k] > 0:
                    realized -= pos[k] * rollc[k]
        eq = INIT + realized
        for k in range(K):
            if pos[k] > 0:
                eq += (c[i, k] - avg[k]) * pv[k] * pos[k]
        if newSess:
            sessStart = prev_eq; dayCut = False
            # governor rearm at a new session once the drawdown has healed below half of tier 1
            if level > 0 and hwm - eq < 0.5 * dd1:
                level = 0; hwm = max(hwm, eq)
        if level == 0 and eq > hwm:
            hwm = eq
        dd = hwm - eq
        if dd2 > 0 and dd >= dd2:
            level = max(level, 2)
        elif dd1 > 0 and dd >= dd1:
            level = max(level, 1)
        g = 1.0 if level == 0 else (m1 if level == 1 else m2)
        if dayStop > 0 and eq - sessStart <= -dayStop:
            dayCut = True
        if dayCut:
            g *= dayMult
        # ---- desired float targets -> caps
        x = np.zeros(K)
        capped = False
        onSide = (not rth[i]) or (i + 1 < n and not rth[i + 1])
        for k in range(K):
            x[k] = max(D[i, k] * g, 0.0)
        if atrCap > 0:
            tot = 0.0
            for k in range(K):
                tot += x[k] * pv[k] * atrD[i, k]
            if tot > atrCap:
                capped = True
                for k in range(K):
                    x[k] *= atrCap / tot
            for k in range(K):
                ek = x[k] * pv[k] * atrD[i, k]
                if ek > instShare * atrCap:
                    capped = True
                    x[k] *= instShare * atrCap / ek
        req = 0.0
        for k in range(K):
            req += x[k] * raw[i, k] * pv[k] * (fon[k] if onSide else fin[k])
        lim = marginU * max(eq, 0.0)
        if req > lim and req > 0:
            capped = True
            for k in range(K):
                x[k] *= lim / req
        # ---- integer net targets with hysteresis (never exceed the capped float target)
        for k in range(K):
            tk = pos[k]
            if abs(x[k] - pos[k]) >= deadband or x[k] < pos[k] - 1e-9 and math.floor(x[k]) < pos[k]:
                tk = int(math.floor(x[k] + 0.5))
            if tk > x[k] + 0.5:
                tk = int(math.floor(x[k] + 0.5))
            if capped and tk > x[k]:
                tk = int(math.floor(x[k]))        # a binding cap is never exceeded by rounding
            if tk < 0:
                tk = 0
            if tk != pos[k] and pend[k] == 0:
                pend[k] = tk - pos[k]; pendAt[k] = i
            tgt_arr[i, k] = x[k]
        u = 0.0; a = 0.0
        for k in range(K):
            u += pos[k] * raw[i, k] * pv[k] * (fon[k] if not rth[i] else fin[k])
            a += pos[k] * pv[k] * atrD[i, k]
        mu_arr[i] = u / max(eq, 1.0); atr_arr[i] = a; gov_arr[i] = g
        for k in range(K):
            pos_arr[i, k] = pos[k]
        eq_arr[i] = eq
        prev_eq = eq
    return pos_arr, eq_arr, mu_arr, atr_arr, gov_arr, tgt_arr, sides, fills


class Book:
    """Holds the aligned timeline and sleeve desired arrays for one end date."""

    def __init__(self, end, sleeve_ids):
        self.end = end
        self.T = timeline(end)
        self.ids = list(sleeve_ids)
        self.inst = {}
        from . import sleeves as S
        C = S.candidates()
        for cid in self.ids:
            self.inst[cid] = C[cid]["inst"]
        self.des = {cid: sleeve_desired(self.T, cid) for cid in self.ids}
        self.sess_codes = pd.factorize(self.T.sd.values)[0]

    def run(self, weights, gov=None, weight_bars=None):
        """weights: {cid: contracts-multiplier}.  weight_bars: optional {cid: per-bar multiplier array} (regime tilt)."""
        gp = dict(GOV_DEFAULT); gp.update(gov or {})
        T = self.T; n = len(T)
        D = np.zeros((n, 2))
        for cid, w in weights.items():
            k = INSTS.index(self.inst[cid])
            m = weight_bars[cid] if weight_bars is not None and cid in weight_bars else 1.0
            D[:, k] += w * m * self.des[cid]
        profs = [instruments.PROFILES[v6lab.PROF[i]] for i in INSTS]
        pv = np.array([p["point_value"] for p in profs])
        fin = np.array([instruments.margin_frac(p, "intraday") for p in profs]) * gp["m_intra"]
        fon = np.array([instruments.margin_frac(p, "overnight") for p in profs]) * gp["m_on"]
        rollc = np.array([2 * (p["commission_side"] + p["tick_value"]) for p in profs])
        env = gp.get("env_dd", 0.0)
        out = kernel(np.stack([T.ES_o.values, T.MNQ_o.values], 1), np.stack([T.ES_c.values, T.MNQ_c.values], 1),
                     np.stack([T.ES_raw.values, T.MNQ_raw.values], 1), np.stack([T.ES_valid.values, T.MNQ_valid.values], 1),
                     np.stack([T.ES_roll.values, T.MNQ_roll.values], 1), np.stack([T.ES_atrD.values, T.MNQ_atrD.values], 1),
                     T.rth.values, self.sess_codes, D, pv, fin, fon, rollc, lab.INIT, gp["marginU"],
                     gp["dd1_frac"] * env, gp["dd2_frac"] * env, gp["m1"], gp["m2"],
                     gp.get("day_stop", 0.0), gp["day_mult"], gp["atr_cap"], gp["inst_share"], gp["deadband"],
                     gp["slip_ticks"] * 0.25, gp["commission"], int(gp["delay"]))
        keys = ["pos", "equity", "margin_util", "atr_exposure", "gov", "target", "sides", "fills"]
        r = dict(zip(keys, out))
        r["D"] = D
        return r

    def daily(self, r):
        T = self.T
        df = pd.DataFrame({"sd": T.sd.values, "eq": r["equity"], "mu": r["margin_util"], "atr": r["atr_exposure"],
                           "pES": r["pos"][:, 0], "pMNQ": r["pos"][:, 1], "rth": T.rth.values})
        g = df.groupby("sd", sort=True)
        d = pd.DataFrame({"eq_end": g.eq.last(), "avg_pos": g.pES.mean() + g.pMNQ.mean(), "max_pos": (df.pES + df.pMNQ).groupby(df.sd).max(),
                          "end_pos": g.pES.last() + g.pMNQ.last(), "mu_avg": g.mu.mean(), "mu_max": g.mu.max(),
                          "atr_avg": g.atr.mean(), "atr_max": g.atr.max(),
                          "mu_on_avg": df[~df.rth].groupby("sd").mu.mean(), "mu_on_max": df[~df.rth].groupby("sd").mu.max(),
                          "pES": g.pES.mean(), "pMNQ": g.pMNQ.mean()})
        d.index = pd.DatetimeIndex(d.index)
        d["pnl"] = d.eq_end.diff().fillna(d.eq_end.iloc[0] - lab.INIT)
        return d
