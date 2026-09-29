"""Causal features aligned to the full bar array.

RTH features are computed ONLY from trading-window bars (bar-end 09:31..16:15, incl. holidays for continuity);
value at bar i uses bars <= i only (decisions are taken at bar close). ETH-context features are computed from
non-window bars and are namespaced `eth_*` — they must only be used by explicitly labelled ETH experiments.
Values are NaN outside the window.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import Bars


def _roll(x, n, fn):
    return getattr(pd.Series(x).rolling(n, min_periods=max(2, n // 2)), fn)().values


def compute_features(b: Bars, volume: np.ndarray | None = None) -> dict:
    n = len(b)
    W = np.flatnonzero(b.in_window)
    o, h, l, c = b.o[W], b.h[W], b.l[W], b.c[W]
    day = b.day[W]
    minute = b.minute[W]
    v = volume[W].astype(float) if volume is not None else np.ones(len(W))
    new_day = np.concatenate([[True], day[1:] != day[:-1]])
    day_id = np.cumsum(new_day) - 1

    f = {}
    # --- VWAP (RTH session)
    tp = (h + l + c) / 3.0
    df = pd.DataFrame({"d": day_id, "pv": tp * v, "v": v, "h": h, "l": l, "c": c, "o": o})
    cpv = df.groupby("d").pv.cumsum().values
    cv = df.groupby("d").v.cumsum().values
    f["vwap"] = cpv / np.maximum(cv, 1e-9)
    # --- session high / day open / prev RTH close
    f["sess_high"] = df.groupby("d").h.cummax().values
    f["sess_low"] = df.groupby("d").l.cummin().values
    day_open = df.groupby("d").o.transform("first").values
    last_close = df.groupby("d").c.last().values
    prev_close_by_day = np.concatenate([[np.nan], last_close[:-1]])
    f["prev_close"] = prev_close_by_day[day_id]
    f["day_open"] = day_open
    # --- 15m RTH bars -> ATR14 (known at completion bar)
    bucket = (minute - 571) // 15
    key = day_id * 100 + bucket
    g = pd.DataFrame({"k": key, "h": h, "l": l, "c": c, "i": np.arange(len(W))}).groupby("k", sort=True)
    m15 = pd.DataFrame({"h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "last": g.i.max(), "b": g.k.first() % 100})
    # a 15m bar is known complete at the close of its final clock minute; if that minute is missing,
    # only at the next available bar (no hindsight about missing data)
    last_i = m15["last"].values
    end_min = 571 + 15 * m15.b.values + 14
    m15["end"] = np.where(minute[last_i] >= end_min, last_i, last_i + 1)
    pc = m15.c.shift()
    tr = np.maximum(m15.h - m15.l, np.maximum((m15.h - pc).abs(), (m15.l - pc).abs())).fillna(m15.h - m15.l)
    atr15 = tr.rolling(14, min_periods=1).mean().values
    ends = m15.end.values
    pos = np.searchsorted(ends, np.arange(len(W)), side="right") - 1   # last completed 15m bar at/before i
    a15 = np.where(pos >= 0, atr15[np.maximum(pos, 0)], np.nan)
    f["atr15"] = np.where(np.isfinite(a15), a15, 10.0)   # constant prior before first completed 15m bar
    # atr15 relative to its trailing 20-day median (~26 bars/day)
    med = pd.Series(atr15).rolling(26 * 20, min_periods=26 * 5).median().values
    rel = atr15 / med
    f["atr15_rel"] = np.where(pos >= 0, rel[np.maximum(pos, 0)], np.nan)
    # lower lows: last 3 completed 15m lows strictly decreasing
    lw = m15.l.values
    ll = np.zeros(len(lw), bool)
    ll[3:] = (lw[3:] < lw[2:-1]) & (lw[2:-1] < lw[1:-2]) & (lw[1:-2] < lw[:-3])
    f["lower_lows"] = np.where(pos >= 0, ll[np.maximum(pos, 0)], False)
    # --- daily RTH ATR (previous days only) and its percentile over trailing 252 days
    dh = df.groupby("d").h.max().values
    dl = df.groupby("d").l.min().values
    dc = last_close
    dpc = np.concatenate([[np.nan], dc[:-1]])
    dtr = np.maximum(dh - dl, np.nan_to_num(np.maximum(np.abs(dh - dpc), np.abs(dl - dpc)), nan=0))
    datr = pd.Series(dtr).rolling(14, min_periods=5).mean().shift(1).values        # prior days only
    dpct = pd.Series(datr).rolling(252, min_periods=40).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True).values
    f["datr"] = np.where(np.isfinite(datr), datr, 60.0)[day_id]   # constant prior for first days
    f["datr_pct"] = np.nan_to_num(dpct, nan=0.5)[day_id]
    # --- rolling windows on RTH sequence
    for N in (30, 60, 120):
        f[f"low{N}"] = _roll(l, N, "min")
        f[f"high{N}"] = _roll(h, N, "max")
    rng = f["high120"] - f["low120"]
    f["rangepos120"] = np.where(rng > 0, (c - f["low120"]) / rng, 0.5)
    sma = _roll(c, 60, "mean"); sd = _roll(c, 60, "std")
    f["bb_lower"] = sma - 2 * sd
    pcw = np.concatenate([[c[0]], c[:-1]])
    tr1 = np.maximum(h - l, np.maximum(np.abs(h - pcw), np.abs(l - pcw)))
    ema = pd.Series(c).ewm(span=60, adjust=False).mean().values
    f["kelt_lower"] = ema - 2 * _roll(tr1, 60, "mean")
    for N in (15, 30, 60):
        f[f"mom{N}"] = c - np.concatenate([np.full(N, np.nan), c[:-N]])
    f["range30"] = f["high30"] - f["low30"]
    r = np.diff(np.log(c), prepend=np.log(c[0]))
    f["rvol_ratio"] = _roll(r, 30, "std") / np.maximum(_roll(r, 390, "std"), 1e-12)
    f["prev_high"] = np.concatenate([[np.nan], h[:-1]])
    f["prev_low"] = np.concatenate([[np.nan], l[:-1]])
    f["prev_open"] = np.concatenate([[np.nan], o[:-1]])
    f["prev_c"] = pcw
    f["prev_low2"] = np.concatenate([[np.nan, np.nan], l[:-2]])
    f["range1"] = h - l
    f["range1_avg20"] = _roll(h - l, 20, "mean")

    # --- ETH context (explicitly labelled): overnight between previous window end and today's first window bar
    full_idx_first = W[new_day]                       # full index of first window bar of each window-day
    full_idx_last = W[np.concatenate([new_day[1:], [True]])]
    on_hi = np.full(len(full_idx_first), np.nan); on_lo = on_hi.copy(); on_last = on_hi.copy()
    for k in range(1, len(full_idx_first)):
        s, e = full_idx_last[k - 1] + 1, full_idx_first[k]
        if e > s:
            on_hi[k] = b.h[s:e].max(); on_lo[k] = b.l[s:e].min(); on_last[k] = b.c[e - 1]
    f["eth_on_high"] = on_hi[day_id]; f["eth_on_low"] = on_lo[day_id]
    f["eth_on_ret"] = (on_last - prev_close_by_day)[day_id]
    f["eth_on_range"] = (on_hi - on_lo)[day_id]
    f["eth_open_loc"] = ((day_open[new_day] - on_lo) / np.maximum(on_hi - on_lo, 0.25))[day_id]
    f["gap"] = (day_open - f["prev_close"])  # RTH-only definition: today's 09:30 open vs prev RTH close

    out = {}
    for k, arr in f.items():
        full = np.full(n, np.nan) if arr.dtype != bool else np.zeros(n, bool)
        full[W] = arr
        out[k] = full
    return out
