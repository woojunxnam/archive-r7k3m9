"""V6 causal feature matrix (per 3m bar).  Every value at bar i uses bars <= i only.

Daily/regime values use COMPLETED sessions only (value for session d uses sessions < d).
Units are normalised (ATR, sigma, percentile, fraction) so ES and MNQ share thresholds.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from numba import njit

from .v533 import pine_atr, pine_rsi


@njit(cache=True)
def _intraday(o, h, l, c, v, in_rth, new_rth):
    n = len(c)
    vwap = np.full(n, np.nan); sig = np.full(n, np.nan); z = np.zeros(n)
    rth_hi = np.full(n, np.nan); rth_lo = np.full(n, np.nan)
    cv = 0.0; cpv = 0.0; cp2v = 0.0; hi = np.nan; lo = np.nan
    bars_above = np.zeros(n); run = 0.0
    for i in range(n):
        src = (h[i] + l[i] + c[i]) / 3.0
        if new_rth[i]:
            cv = v[i]; cpv = v[i] * src; cp2v = v[i] * src * src; hi = h[i]; lo = l[i]; run = 0.0
        elif in_rth[i]:
            cv += v[i]; cpv += v[i] * src; cp2v += v[i] * src * src
            hi = max(hi, h[i]); lo = min(lo, l[i])
        if in_rth[i] and cv > 0:
            vw = cpv / cv
            s = math.sqrt(max(cp2v / cv - vw * vw, 0.0))
            vwap[i] = vw; sig[i] = s
            if s > 0.25:
                z[i] = (c[i] - vw) / s
            rth_hi[i] = hi; rth_lo[i] = lo
            if c[i] >= vw:
                run = run + 1 if run >= 0 else 1
            else:
                run = run - 1 if run <= 0 else -1
            bars_above[i] = run
    return vwap, sig, z, rth_hi, rth_lo, bars_above


def build(b: pd.DataFrame, pv: float) -> dict:
    o = b.o.values; h = b.h.values; l = b.l.values; c = b.c.values; v = b.v.values.astype(float)
    in_rth = b.in_rth.values; prev = np.concatenate([[False], in_rth[:-1]]); new_rth = in_rth & ~prev
    n = len(c)
    f = {}
    f["atr14"] = pine_atr(h, l, c, 14)
    f["rsi2"] = pine_rsi(c, 2)
    f["rsi14"] = pine_rsi(c, 14)
    vwap, sig, z, rhi, rlo, above = _intraday(o, h, l, c, v, in_rth, new_rth)
    f["vwap"], f["vwap_sig"], f["vwap_z"], f["bars_vs_vwap"] = vwap, sig, z, above
    w = np.where(rhi - rlo > 0.25, rhi - rlo, np.nan)
    f["pos_rth"] = np.nan_to_num((c - rlo) / w, nan=0.5)
    vw = pd.Series(vwap)
    f["vwap_slope"] = ((vw - vw.shift(10)) / pd.Series(f["atr14"])).fillna(0).values
    cs = pd.Series(c)
    f["ret60m_atr"] = ((cs - cs.shift(20)) / pd.Series(f["atr14"])).fillna(0).values
    # ---- session-level (completed sessions only)
    sd = b.session_date.values
    df = pd.DataFrame({"sd": sd, "h": h, "l": l, "c": c, "rth": in_rth})
    sess = df.groupby("sd", sort=True).agg(H=("h", "max"), L=("l", "min"), C=("c", "last"))
    rthc = df[df.rth].groupby("sd").c.last()
    rthh = df[df.rth].groupby("sd").h.max(); rthl = df[df.rth].groupby("sd").l.min()
    sess["RC"] = rthc; sess["RH"] = rthh; sess["RL"] = rthl
    sess["RC"] = sess["RC"].ffill()
    pc = sess["C"].shift(1)
    tr = np.maximum(sess["H"], pc.fillna(sess["H"])) - np.minimum(sess["L"], pc.fillna(sess["L"]))
    sess["TR"] = tr
    sess["ATR20"] = tr.rolling(20, min_periods=5).mean()
    sess["RV20"] = sess["C"].diff().rolling(20, min_periods=5).std()
    for k in (10, 20, 50, 100, 200):
        sess[f"EMA{k}"] = sess["RC"].ewm(span=k, adjust=False).mean()
    sess["SMA50"] = sess["RC"].rolling(50).mean(); sess["SMA200"] = sess["RC"].rolling(200).mean()
    sess["H5"] = sess["RH"].rolling(5, min_periods=1).max(); sess["L5"] = sess["RL"].rolling(5, min_periods=1).min()
    sess["ATR20_pct"] = sess["ATR20"].rolling(250, min_periods=50).rank(pct=True)
    # regime tier on completed sessions (value for session d from info through d)
    med = (sess["RC"] > sess["EMA50"]) & (sess["EMA50"] >= sess["EMA50"].shift(1))
    strong = med & (sess["EMA20"] > sess["EMA50"]) & (sess["EMA20"] > sess["EMA20"].shift(1))
    bear = (sess["RC"] < sess["SMA200"]) & (sess["SMA50"] < sess["SMA200"]) & (sess["SMA200"] < sess["SMA200"].shift(1))
    tier = np.where(bear, 0, np.where(strong, 3, np.where(med, 2, 1)))
    sess["TIER"] = tier
    sess["TREND20"] = (sess["RC"] > sess["EMA20"]).astype(float)
    sess["TREND100"] = (sess["RC"] > sess["EMA100"]).astype(float)
    # shift by one session => strictly completed-session information for session d
    lag = sess.shift(1)
    idx = pd.Index(sess.index).get_indexer(sd)
    for col in ("ATR20", "RV20", "EMA10", "EMA20", "EMA50", "EMA100", "EMA200", "TIER", "TREND20", "TREND100",
                "RC", "H5", "L5", "ATR20_pct", "RH", "RL"):
        f["d_" + col] = lag[col].values[idx]
    f["d_TIER"] = np.nan_to_num(f["d_TIER"], nan=1).astype(np.int64)
    # 5-day range incl. today's RTH so far
    hi5 = np.fmax(f["d_H5"], np.where(np.isnan(rhi), -np.inf, rhi))
    lo5 = np.fmin(f["d_L5"], np.where(np.isnan(rlo), np.inf, rlo))
    w5 = np.where(hi5 - lo5 > 0.25, hi5 - lo5, np.nan)
    f["pos_5d"] = np.nan_to_num((c - lo5) / w5, nan=0.5)
    wp = np.where(f["d_RH"] - f["d_RL"] > 0.25, f["d_RH"] - f["d_RL"], np.nan)
    f["pos_prior"] = np.nan_to_num((c - f["d_RL"]) / wp, nan=0.5)
    f["c_vs_ema20_atr"] = np.nan_to_num((c - f["d_EMA20"]) / f["d_ATR20"])
    f["c_vs_ema50_atr"] = np.nan_to_num((c - f["d_EMA50"]) / f["d_ATR20"])
    f["gap_atr"] = np.nan_to_num((o - f["d_RC"]) / f["d_ATR20"])
    f["bar_range_atr"] = np.nan_to_num((h - l) / f["d_ATR20"])
    f["in_rth"] = in_rth; f["new_rth"] = new_rth
    f["mod"] = b["mod"].values.astype(np.int64)
    f["sess"] = sd.astype("datetime64[D]").astype(np.int64)
    return f
