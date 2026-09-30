"""Causal derived timeframes from canonical ES 1m (RTH window only, session-anchored at 09:30 open).

A k-minute bar groups 1m bars with bar-end minutes 09:31+k*j .. 09:30+k*(j+1) of one day. It is COMPLETE at the close
of its final clock minute; if that minute is missing it is only known at the next available 1m bar of the same day
(no hindsight about missing data). A partial last bucket of the session (e.g. 10m: 16:11-16:15) never completes
inside the day and therefore never produces a tradeable signal. `comp[j]` = full-array index of the 1m bar at whose
close MTF bar j is known; -1 if not inside the same day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FIRST_END = 571  # 09:31 bar-end


def mtf_bars(b, k: int) -> dict:
    W = np.flatnonzero(b.in_window)
    minute = b.minute[W]
    day = b.day[W]
    bucket = (minute - FIRST_END) // k
    key = day.astype(np.int64) * 1000 + bucket
    new = np.concatenate([[True], key[1:] != key[:-1]])
    starts = np.flatnonzero(new)
    ends = np.concatenate([starts[1:] - 1, [len(W) - 1]])
    hw, lw = b.h[W], b.l[W]
    vw = b.v[W] if b.v is not None else np.ones(len(W))
    o = b.o[W][starts]
    c = b.c[W][ends]
    h = np.maximum.reduceat(hw, starts)
    l = np.minimum.reduceat(lw, starts)
    v = np.add.reduceat(vw, starts)
    bk = bucket[starts]
    dd = day[starts]
    end_min = FIRST_END + k * bk + (k - 1)
    at_end = minute[ends] >= end_min
    comp_pos = np.where(at_end, ends, ends + 1)
    ok = comp_pos < len(W)
    cp = np.minimum(comp_pos, len(W) - 1)
    ok &= day[cp] == dd
    comp = np.where(ok, W[cp], -1)
    newday = np.concatenate([[True], dd[1:] != dd[:-1]])
    nb = np.zeros(len(dd), np.int64)          # bar number within the day (0 = first)
    run = -1
    for j in range(len(dd)):
        run = 0 if newday[j] else run + 1
        nb[j] = run
    return dict(k=k, o=o, h=h, l=l, c=c, v=v, day=dd, bucket=bk, comp=comp, first=W[starts], last=W[ends],
                newday=newday, nb=nb)


def add_basic_features(m: dict) -> dict:
    """per-timeframe causal features on the MTF sequence (value at j uses bars <= j)."""
    o, h, l, c, v, nd = m["o"], m["h"], m["l"], m["c"], m["v"], m["newday"]
    rng = h - l
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.where(nd, rng, np.maximum(rng, np.maximum(np.abs(h - pc), np.abs(l - pc))))
    m["rng"] = rng
    m["body"] = c - o
    m["cl"] = np.where(rng > 0, (c - l) / np.where(rng > 0, rng, 1), 0.5)
    m["atr"] = pd.Series(tr).rolling(14, min_periods=5).mean().values
    m["ravg"] = pd.Series(rng).rolling(20, min_periods=5).mean().values
    vm = pd.Series(v).rolling(20, min_periods=5).mean().values
    m["vrel"] = np.where(vm > 0, v / np.where(vm > 0, vm, 1), np.nan)
    m["ema20"] = pd.Series(c).ewm(span=20, adjust=False).mean().values
    m["pc"] = pc
    m["ph"] = np.concatenate([[np.nan], h[:-1]])
    m["pl"] = np.concatenate([[np.nan], l[:-1]])
    return m


def prior_max(x, N, nb):
    """max of x over the N PRIOR bars of the same day (NaN if fewer than N prior bars today)."""
    r = pd.Series(x).shift(1).rolling(N, min_periods=N).max().values
    return np.where(nb >= N, r, np.nan)


def prior_min(x, N, nb):
    r = pd.Series(x).shift(1).rolling(N, min_periods=N).min().values
    return np.where(nb >= N, r, np.nan)


def to_1m(m: dict, mask, n: int):
    """map MTF-bar event mask to the 1m full grid at completion indices (drops incomplete / cross-day)."""
    j = np.flatnonzero(np.asarray(mask, bool) & (m["comp"] >= 0))
    out = np.zeros(n, bool)
    out[m["comp"][j]] = True
    return out
