"""Bottom event study infrastructure (RUN-3 addendum A-E, AA-AC, X-Z).

- `event_features(b, F)`: causal boolean/continuous features at bar t (known at bar-t close), full-array aligned.
  RTH window bars only; ETH is not used (except explicitly named eth_* already in F, not used here).
- `forward_outcomes(b)`: for every tradeable bar t, outcomes of a hypothetical long entered at open of bar t+1
  (ES price as MES proxy), measured only within the same RTH session. Same-bar ambiguity (target and stop both
  inside one 1m bar) is scored as a LOSS (conservative).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import Bars

HORIZONS = (5, 10, 15, 30, 60, 120)
PAIRS = ((2.5, 2.5), (3.0, 3.0), (5.0, 5.0), (5.0, 10.0), (10.0, 5.0))


def _rth(b: Bars):
    W = np.flatnonzero(b.in_window)
    return W


def forward_outcomes(b: Bars, H: int = 120, chunk: int = 20000) -> pd.DataFrame:
    W = _rth(b)
    o, h, l, c, day = b.o[W], b.h[W], b.l[W], b.c[W], b.day[W]
    n = len(W)
    res = {f"ret{k}": np.full(n, np.nan) for k in HORIZONS}
    for k in (15, 60, 120):
        res[f"mfe{k}"] = np.full(n, np.nan)
        res[f"mae{k}"] = np.full(n, np.nan)
    for up, dn in PAIRS:
        res[f"win_{up}_{dn}"] = np.full(n, np.nan)
    res["t_reb2.5"] = np.full(n, np.nan)
    res["newlow30"] = np.full(n, np.nan)
    res["t_mfe60"] = np.full(n, np.nan)
    res["entry"] = np.full(n, np.nan)
    ar = np.arange(1, H + 1)
    for s in range(0, n - 1, chunk):
        t = np.arange(s, min(s + chunk, n - 1))
        e_idx = t + 1
        ok_e = day[np.minimum(e_idx, n - 1)] == day[t]
        entry = np.where(ok_e, o[np.minimum(e_idx, n - 1)], np.nan)
        J = t[:, None] + ar[None, :]                       # forward bars t+1..t+H (entry bar included)
        Jc = np.minimum(J, n - 1)
        valid = (J < n) & (day[Jc] == day[t][:, None])
        HH = np.where(valid, h[Jc], np.nan)
        LL = np.where(valid, l[Jc], np.nan)
        CC = np.where(valid, c[Jc], np.nan)
        up_ = HH - entry[:, None]
        dn_ = entry[:, None] - LL
        for k in HORIZONS:
            res[f"ret{k}"][t] = CC[:, k - 1] - entry
        for k in (15, 60, 120):
            res[f"mfe{k}"][t] = np.nanmax(up_[:, :k], axis=1)
            res[f"mae{k}"][t] = np.nanmax(dn_[:, :k], axis=1)
        for U, D in PAIRS:
            hit_u = up_ >= U
            hit_d = dn_ >= D
            fu = np.where(hit_u.any(1), hit_u.argmax(1), H + 1)
            fd = np.where(hit_d.any(1), hit_d.argmax(1), H + 1)
            win = (fu < fd).astype(float)                 # same bar (fu == fd) -> loss
            res[f"win_{U}_{D}"][t] = np.where((fu > H) & (fd > H), np.nan, win)   # neither hit within session -> NaN
        hit = up_ >= 2.5
        res["t_reb2.5"][t] = np.where(hit.any(1), hit.argmax(1) + 1, np.nan)
        res["t_mfe60"][t] = np.nanargmax(np.where(np.isnan(up_[:, :60]), -np.inf, up_[:, :60]), axis=1) + 1
        low_t = l[t]
        res["newlow30"][t] = (np.nanmin(LL[:, :30], axis=1) < low_t).astype(float)
        res["entry"][t] = entry
    df = pd.DataFrame(res)
    df["idx"] = W
    df["tradeable"] = b.tradeable[W]
    df["year"] = (b.day[W] // 10000).astype(int)
    df["minute"] = b.minute[W]
    return df


def _consec(x):
    """length of current run of True ending at each position"""
    out = np.zeros(len(x), dtype=np.int32)
    run = 0
    for k, v in enumerate(x):
        run = run + 1 if v else 0
        out[k] = run
    return out


def event_features(b: Bars, F: dict) -> pd.DataFrame:
    W = _rth(b)
    o, h, l, c, v = b.o[W], b.h[W], b.l[W], b.c[W], (b.v[W] if b.v is not None else np.ones(len(W)))
    day = b.day[W]
    g = lambda k: F[k][W]  # noqa: E731
    a15 = np.maximum(g("atr15"), 0.25)
    vw = g("vwap")
    new_day = np.concatenate([[True], day[1:] != day[:-1]])
    did = np.cumsum(new_day) - 1
    pc = np.concatenate([[np.nan], c[:-1]])
    ph, pl, po = np.concatenate([[np.nan], h[:-1]]), np.concatenate([[np.nan], l[:-1]]), np.concatenate([[np.nan], o[:-1]])
    pl2 = np.concatenate([[np.nan, np.nan], l[:-2]])
    rng = h - l
    body = np.abs(c - o)
    lw = np.minimum(o, c) - l
    ravg = pd.Series(rng).rolling(20, min_periods=5).mean().values
    X = {}
    # ---- location
    dev = (c - vw) / a15
    X["vwap_dev_atr"] = dev
    sd = pd.Series(c - vw).groupby(did).transform(lambda s: s.expanding(10).std()).values
    X["vwap_z"] = (c - vw) / np.where(sd > 0, sd, np.nan)
    sl = g("sess_low"); sh = g("sess_high")
    X["sess_dd_atr"] = (c - sh) / a15
    X["near_sess_low"] = (c - sl) <= 0.25 * a15
    X["prev_close_dd_atr"] = (c - g("prev_close")) / a15
    dfd = pd.DataFrame({"d": did, "h": h, "l": l})
    dh = dfd.groupby("d").h.max().values; dl = dfd.groupby("d").l.min().values
    pdl = np.concatenate([[np.nan], dl[:-1]])[did]; pdh = np.concatenate([[np.nan], dh[:-1]])[did]
    X["below_pdl"] = c < pdl
    X["dist_pdl_atr"] = (c - pdl) / a15
    wk = pd.Series(pd.to_datetime(day.astype(str))).dt.to_period("W").astype(str).values
    wl = pd.Series(l).groupby(wk).min()
    wkeys = pd.Index(wl.index)
    prev_wl = pd.Series(wl.shift(1).values, index=wkeys)
    X["below_pwl"] = c < prev_wl.reindex(wk).values
    for N in (15, 30, 60, 120):
        lo = pd.Series(l).rolling(N, min_periods=N // 2).min().values
        hi = pd.Series(h).rolling(N, min_periods=N // 2).max().values
        X[f"rpos{N}"] = np.where(hi - lo > 0, (c - lo) / (hi - lo), 0.5)
        X[f"newlow{N}"] = l <= pd.Series(l).shift(1).rolling(N, min_periods=N // 2).min().values
    lo390 = pd.Series(l).rolling(390, min_periods=100).min().values; hi390 = pd.Series(h).rolling(390, min_periods=100).max().values
    X["rpos1d"] = np.where(hi390 - lo390 > 0, (c - lo390) / (hi390 - lo390), 0.5)
    lo5d = pd.Series(l).rolling(1950, min_periods=400).min().values; hi5d = pd.Series(h).rolling(1950, min_periods=400).max().values
    X["rpos5d"] = np.where(hi5d - lo5d > 0, (c - lo5d) / (hi5d - lo5d), 0.5)
    # ---- exhaustion
    down = c < o
    X["consec_down"] = _consec(down)
    X["big_bear"] = down & (rng > 2 * ravg)
    X["atr_spike"] = g("atr15_rel") > 1.5
    X["rvol_spike"] = g("rvol_ratio") > 2.0
    ema20 = pd.Series(c).ewm(span=20, adjust=False).mean().values
    X["dist_ema20_atr"] = (c - ema20) / a15
    m15 = np.nan_to_num(g("mom15")) / a15; m5 = (c - np.concatenate([np.full(5, np.nan), c[:-5]])) / a15
    X["decel"] = (m15 < -1.5) & (m5 > m15 / 3)
    X["shrinking_bodies"] = down & (np.concatenate([[np.nan], down[:-1]]) == 1) & (body < np.concatenate([[np.nan], body[:-1]])) & (np.concatenate([[np.nan], body[:-1]]) < np.concatenate([[np.nan, np.nan], body[:-2]]))
    lwp = np.concatenate([[np.nan], lw[:-1]])
    X["growing_lower_wicks"] = (lw > lwp) & (lwp > np.concatenate([[np.nan, np.nan], lw[:-2]]))
    nl30 = X["newlow30"]
    X["failed_new_low"] = (pl < pl2) & (l > pl) & (c > pc)
    X["newlow_weak_close"] = nl30 & ((c - l) <= 0.25 * np.maximum(rng, 0.25))
    X["newlow_reclaim"] = nl30 & (c > ph)
    X["rex_contract"] = (np.concatenate([[np.nan], rng[:-1]]) > 2 * np.concatenate([[np.nan], ravg[:-1]])) & (rng < np.concatenate([[np.nan], rng[:-1]]))
    # ---- candles / microstructure
    X["close_upper25"] = (rng > 0) & (c >= l + 0.75 * rng)
    X["close_upper33"] = (rng > 0) & (c >= l + 0.67 * rng)
    X["long_lower_wick"] = (rng > 0) & (lw >= 0.5 * rng)
    X["wick_body_ratio"] = lw / np.maximum(body, 0.25)
    X["bull_engulf"] = (pc < po) & (c > o) & (c >= po) & (o <= pc)
    X["outside_rev"] = (h > ph) & (l < pl) & (c > ph)
    X["inside_after_sell"] = (h <= ph) & (l >= pl) & (m15 < -1.0)
    X["prev_high_reclaim"] = c > ph
    X["two_bar_hc"] = (c > pc) & (pc > np.concatenate([[np.nan, np.nan], c[:-2]]))
    X["two_bar_rev"] = (pc < po) & (c > o) & (c > po)
    X["ll_higher_close"] = (l < pl) & (c > o)
    X["ll_close_gt_pc"] = (l < pl) & (c > pc)
    lo10 = pd.Series(l).rolling(10, min_periods=5).min().values
    X["micro_double_bottom"] = (np.abs(l - pd.Series(l).shift(3).rolling(10, min_periods=5).min().values) <= 0.5) & (c > o)
    X["sweep_reclaim30"] = (l < pd.Series(l).shift(1).rolling(30, min_periods=15).min().values) & (c > pd.Series(l).shift(1).rolling(30, min_periods=15).min().values)
    X["sweep_reclaim_sess"] = (l <= np.concatenate([[np.nan], sl[:-1]])) & (c > np.concatenate([[np.nan], sl[:-1]])) & ~new_day
    X["sweep_reclaim_pdl"] = (l < pdl) & (c > pdl)
    # ---- multi-timeframe context (continuous, causal)
    X["slope60_atr"] = np.nan_to_num(g("mom60")) / a15
    X["slope30_atr"] = np.nan_to_num(g("mom30")) / a15
    er_n = 30
    net = np.abs(c - np.concatenate([np.full(er_n, np.nan), c[:-er_n]]))
    path = pd.Series(np.abs(np.diff(c, prepend=c[0]))).rolling(er_n).sum().values
    X["eff_ratio30"] = net / np.maximum(path, 0.25)
    X["down_trend_persist"] = (X["eff_ratio30"] > 0.5) & (X["slope30_atr"] < -1.0)
    X["gap_atr"] = g("gap") / np.maximum(g("datr"), 1)
    X["datr_pct"] = g("datr_pct")
    X["tod"] = pd.cut(b.minute[W], [0, 600, 690, 810, 900, 2000], labels=["0930_1000", "1000_1130", "1130_1330", "1330_1500", "1500_1615"]).astype(str)
    X["volreg"] = pd.cut(g("datr_pct"), [-1, 0.25, 0.75, 0.9, 2], labels=["LOW", "NORMAL", "HIGH", "EXTREME"]).astype(str)
    df = pd.DataFrame(X)
    df["idx"] = W
    return df
