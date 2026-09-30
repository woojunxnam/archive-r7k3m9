"""RUN-4 numba kernels. Every kernel follows EXECUTION_SPEC.md (EXEC-1.1 conservative) exactly:

- signal on the close of bar i -> order valid only for bar i+1 (same trading day, tradeable), else discarded;
- market BUY/SELL fill at open +/- slippage ticks; TP limit SELL: gap-through at open (O >= T + tick -> max(T, O - slip)),
  intrabar H >= T + penetration -> T. A position entered AT THE OPEN may take its TP in the same bar (spec §5.1);
  an intrabar limit BUY may not (spec §5.2);
- no fills outside tradeable bars. Costs: commission per side per contract, slippage via fill prices.

Kernels:
  sim_single      - Sleeve B single-position momentum trade simulator (TP / time / close-based stop & trail / EOD)
  bracket_outcomes- event-study outcomes (P(+U before -D) with same-bar ambiguity = loss, MFE/MAE, returns)
  first_ge / range_min with block indices (O(n/B + B) queries) for long-horizon recycle outcomes
  rec_outcomes    - hypothetical 1-lot recycle trade per signal: time-to-TP, MAE before TP (trap-risk labels)
  shadow_sim      - one EXTRA recycle slot fed only by signals the real book could not take (opportunity cost)
  tranche_mae     - MAE of arbitrary [entry, exit] intervals (Sleeve A dead-slot metrics)
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

TICK = 0.25


@njit(cache=True)
def _ceil_tick(x):
    return math.ceil(round(x / 0.25, 9)) * 0.25


@njit(cache=True)
def _floor_tick(x):
    return math.floor(round(x / 0.25, 9)) * 0.25


def day_structure(b):
    """nxt_same[i]: bar i+1 is tradeable and in the same trading day (an order placed at the close of i can fill);
    last_td[i]: i is the last tradeable bar of its day. next_is_last[i] = nxt_same[i] & last_td[i+1]."""
    n = len(b)
    tr = b.tradeable
    nxt = np.zeros(n, bool)
    nxt[:-1] = tr[1:] & (b.day[1:] == b.day[:-1]) & tr[:-1]
    idx = np.flatnonzero(tr)
    last_td = np.zeros(n, bool)
    if len(idx):
        d = b.day[idx]
        is_last = np.concatenate([d[1:] != d[:-1], [True]])
        last_td[idx[is_last]] = True
    nil = np.zeros(n, bool)
    nil[:-1] = nxt[:-1] & last_td[1:]
    dtm = (b.dt.astype("int64") // 60_000_000_000).astype(np.int64)
    return nxt, last_td, nil, dtm


# ----------------------------------------------------------------------------------------------- Sleeve B
@njit(cache=True)
def sim_single(sig, o, h, l, c, trad, nxt, nil, dtm, tp, tmax, stop, trail, cooldown, slip_ticks, pen_ticks,
               strict_entry_bar, cap, size):
    """One position at a time. tp/stop/trail in points (inf = off), tmax minutes (large = off), cooldown bars after
    an exit before a new signal is accepted. cap[i] (int) = contracts available to this sleeve at the close of bar i
    (portfolio global budget); entry only if cap[i] >= size. Returns trade arrays + signal accounting."""
    n = len(o)
    slip = slip_ticks * 0.25
    pen = pen_ticks * 0.25
    maxt = 0
    for i in range(n):
        if sig[i]:
            maxt += 1
    e_idx = np.empty(maxt, np.int64)
    x_idx = np.empty(maxt, np.int64)
    e_px = np.empty(maxt, np.float64)
    x_px = np.empty(maxt, np.float64)
    reason = np.empty(maxt, np.int64)      # 1 tp_gap 2 tp 3 time 4 stop 5 trail 6 eod
    k = 0
    pos = False
    pe = -1          # pending entry bar
    px_ = -1         # pending exit bar
    px_reason = 0
    cool = -1
    ei = -1
    ep = 0.0
    tpx = 0.0
    maxc = 0.0
    n_sig = 0
    n_ignored = 0
    n_cap_block = 0
    for i in range(n):
        if not trad[i]:
            continue
        # ---------------- fills on bar i
        if pos and i > ei and o[i] >= tpx + 0.25:
            x_idx[k] = i; x_px[k] = max(tpx, o[i] - slip); reason[k] = 1
            k += 1; pos = False; cool = i + cooldown; px_ = -1
        if pos and px_ == i:
            x_idx[k] = i; x_px[k] = o[i] - slip; reason[k] = px_reason
            k += 1; pos = False; cool = i + cooldown
        px_ = -1
        if pe == i and not pos:
            ei = i; ep = o[i] + slip; pos = True
            e_idx[k] = i; e_px[k] = ep
            tpx = _ceil_tick(ep + tp) if tp < 1e9 else 1e18
            maxc = c[i]
        pe = -1
        if pos:
            if (i > ei or not strict_entry_bar) and h[i] >= tpx + pen:
                x_idx[k] = i; x_px[k] = tpx; reason[k] = 2
                k += 1; pos = False; cool = i + cooldown
        # ---------------- decisions at the close of bar i (orders for i+1)
        if sig[i]:
            n_sig += 1
        if not nxt[i]:
            if sig[i]:
                n_ignored += 1
            continue
        if pos:
            if sig[i]:
                n_ignored += 1
            held = dtm[i] - dtm[ei] + 1
            if c[i] > maxc:
                maxc = c[i]
            r = 0
            if nil[i]:
                r = 6
            elif held >= tmax:
                r = 3
            elif c[i] <= ep - stop:
                r = 4
            elif c[i] <= maxc - trail:
                r = 5
            if r:
                px_ = i + 1
                px_reason = r
        elif sig[i]:
            if i < cool or nil[i]:
                n_ignored += 1
            elif cap[i] < size:
                n_cap_block += 1
            else:
                pe = i + 1
    if pos:      # cannot happen for intraday rules (EOD exit); keep for safety: mark at last close
        x_idx[k] = n - 1; x_px[k] = c[n - 1]; reason[k] = 9
        k += 1
    return e_idx[:k], x_idx[:k], e_px[:k], x_px[:k], reason[:k], n_sig, n_ignored, n_cap_block


@njit(cache=True)
def bracket_outcomes(ev, o, h, l, c, nxt, dtm, ups, dns, horizons, win_mfe, target_t, slip_ticks, pen_ticks):
    """For each event bar s (signal at close of s), entry at open of e=s+1 (same day only) at o[e] + slip.
    Bracket (U, D): win if h >= entry + U + pen strictly before l <= entry - D; both in one bar = loss;
    neither before session end = NaN. Returns wins[n_ev, n_pairs], rets[n_ev, n_h] (gross from o[e]),
    mfe, mae (within win_mfe minutes, gross from o[e]), t_mfe, t_target (minutes, NaN if not reached)."""
    m = len(ev)
    npair = len(ups)
    nh = len(horizons)
    wins = np.full((m, npair), np.nan)
    rets = np.full((m, nh), np.nan)
    mfe = np.full(m, np.nan)
    mae = np.full(m, np.nan)
    t_mfe = np.full(m, np.nan)
    t_tg = np.full(m, np.nan)
    slip = slip_ticks * 0.25
    pen = pen_ticks * 0.25
    n = len(o)
    for q in range(m):
        s = ev[q]
        if s < 0 or s >= n - 1 or not nxt[s]:
            continue
        e = s + 1
        o0 = o[e]
        ent = o0 + slip
        done = np.zeros(npair, np.bool_)
        t0 = dtm[e]
        best = -1e18
        worst = -1e18
        tb = 0.0
        hi_h = 0
        j = e
        while True:
            el = dtm[j] - t0 + 1           # minutes elapsed at the close of bar j
            for p in range(npair):
                if not done[p]:
                    up = h[j] >= ent + ups[p] + pen
                    dn = l[j] <= ent - dns[p]
                    if dn:
                        wins[q, p] = 0.0; done[p] = True
                    elif up:
                        wins[q, p] = 1.0; done[p] = True
            while hi_h < nh and el >= horizons[hi_h]:
                rets[q, hi_h] = c[j] - o0
                hi_h += 1
            if el <= win_mfe:
                if h[j] - o0 > best:
                    best = h[j] - o0; tb = el
                if o0 - l[j] > worst:
                    worst = o0 - l[j]
            if np.isnan(t_tg[q]) and h[j] >= o0 + target_t:
                t_tg[q] = el
            if j + 1 >= n or not nxt[j]:
                break
            j += 1
        mfe[q] = best
        mae[q] = worst
        t_mfe[q] = tb
    return wins, rets, mfe, mae, t_mfe, t_tg


# ----------------------------------------------------------------------------------------------- block index
def block_max(a, B=1024):
    n = len(a)
    nb = (n + B - 1) // B
    pad = np.full(nb * B, -np.inf)
    pad[:n] = a
    return pad.reshape(nb, B).max(1)


def block_min(a, B=1024):
    n = len(a)
    nb = (n + B - 1) // B
    pad = np.full(nb * B, np.inf)
    pad[:n] = a
    return pad.reshape(nb, B).min(1)


@njit(cache=True)
def first_ge(a, bmax, B, start, thr):
    """first index j >= start with a[j] >= thr, else -1"""
    n = len(a)
    if start >= n:
        return -1
    j = start
    end_blk = (j // B + 1) * B
    while j < n and j < end_blk:
        if a[j] >= thr:
            return j
        j += 1
    bi = j // B
    nb = len(bmax)
    while bi < nb and bmax[bi] < thr:
        bi += 1
    if bi >= nb:
        return -1
    j = bi * B
    while j < n:
        if a[j] >= thr:
            return j
        j += 1
    return -1


@njit(cache=True)
def range_min(a, bmin, B, i0, i1):
    """min(a[i0..i1]) inclusive"""
    if i1 < i0:
        return np.inf
    m = np.inf
    j = i0
    while j <= i1 and j % B != 0:
        if a[j] < m:
            m = a[j]
        j += 1
    while j + B - 1 <= i1:
        if bmin[j // B] < m:
            m = bmin[j // B]
        j += B
    while j <= i1:
        if a[j] < m:
            m = a[j]
        j += 1
    return m


def tp_trigger_array(b, pen_ticks=1):
    """g[j] = highest TP level T that bar j would fill (tradeable bars only): intrabar needs H >= T + pen,
    gap-through needs O >= T + tick. first_ge(g, ., start, T) = first bar >= start whose TP limit at T fills."""
    g = np.maximum(b.h - pen_ticks * TICK, b.o - TICK)
    return np.where(b.tradeable, g, -np.inf)


@njit(cache=True)
def _tp_exit(i_start, tpx, allow_first, o, h, g, bmax_g, B, trad, slip, pen):
    """Exit bar/price of a TP limit sell resting from the entry bar i_start. At the entry bar only an intrabar fill
    is possible (entry happened at/after the open). Returns (-1, nan) if never filled."""
    if allow_first and trad[i_start] and h[i_start] >= tpx + pen:
        return i_start, tpx
    j = first_ge(g, bmax_g, B, i_start + 1, tpx)
    if j < 0:
        return -1, np.nan
    if o[j] >= tpx + 0.25:
        return j, max(tpx, o[j] - slip)
    return j, tpx


@njit(cache=True)
def rec_outcomes(sig_idx, tp, o, h, l, g, bmax_g, lmin, B, trad, nxt, dtm, slip_ticks, pen_ticks):
    """Hypothetical 1-lot recycle trade per signal (market entry next open). Returns entry_idx, exit_idx (-1 = never),
    entry px, hold minutes (to exit or to data end), MAE points before exit (all bars incl. ETH)."""
    m = len(sig_idx)
    n = len(o)
    slip = slip_ticks * 0.25
    pen = pen_ticks * 0.25
    ei = np.full(m, -1, np.int64)
    xi = np.full(m, -1, np.int64)
    ep = np.full(m, np.nan)
    hold = np.full(m, np.nan)
    mae = np.full(m, np.nan)
    for q in range(m):
        s = sig_idx[q]
        if s >= n - 1 or not nxt[s]:
            continue
        e = s + 1
        ent = o[e] + slip
        tpx = _ceil_tick(ent + tp)
        j, _ = _tp_exit(e, tpx, True, o, h, g, bmax_g, B, trad, slip, pen)
        ei[q] = e
        ep[q] = ent
        end = j if j >= 0 else n - 1
        xi[q] = j
        hold[q] = dtm[end] - dtm[e] + 1
        mae[q] = ent - range_min(l, lmin, B, e, end)
    return ei, xi, ep, hold, mae


@njit(cache=True)
def shadow_sim(sig_idx, sig_tp, limit_mode, o, h, l, c, g, bmax_g, B, trad, nxt, slip_ticks, pen_ticks):
    """ONE extra recycle slot. Takes the first blocked signal when the shadow slot is free, holds to its TP (or data
    end), then waits for the next blocked signal. limit_mode: resting limit at floor_tick(close) for 1 bar."""
    m = len(sig_idx)
    n = len(o)
    slip = slip_ticks * 0.25
    pen = pen_ticks * 0.25
    out_e = np.full(m, -1, np.int64)
    out_x = np.full(m, -1, np.int64)
    out_ep = np.full(m, np.nan)
    out_xp = np.full(m, np.nan)
    k = 0
    free_from = -1
    for q in range(m):
        s = sig_idx[q]
        if s < free_from or s >= n - 1 or not nxt[s]:
            continue
        e = s + 1
        if limit_mode:
            L = _floor_tick(c[s])
            if o[e] <= L - 0.25:
                ent = min(L, o[e] + slip)
                at_open = True
            elif l[e] <= L - pen:
                ent = L
                at_open = False
            else:
                continue
        else:
            ent = o[e] + slip
            at_open = True
        tpx = _ceil_tick(ent + sig_tp[q])
        j, xp = _tp_exit(e, tpx, at_open, o, h, g, bmax_g, B, trad, slip, pen)
        out_e[k] = e
        out_ep[k] = ent
        out_x[k] = j
        out_xp[k] = xp
        k += 1
        if j < 0:
            break
        free_from = j
    return out_e[:k], out_x[:k], out_ep[:k], out_xp[:k]


@njit(cache=True)
def tranche_mae(entry_idx, exit_idx, entry_px, l, lmin, B):
    m = len(entry_idx)
    out = np.empty(m)
    for q in range(m):
        out[q] = entry_px[q] - range_min(l, lmin, B, entry_idx[q], exit_idx[q])
    return out


@njit(cache=True)
def dist_dead_bars(entry_idx, exit_idx, entry_px, c, datr, trad, x):
    """number of tradeable bars in [entry, exit) where entry_px - close >= x * daily ATR"""
    m = len(entry_idx)
    out = np.zeros(m, np.int64)
    for q in range(m):
        cnt = 0
        for j in range(entry_idx[q], exit_idx[q]):
            if trad[j] and entry_px[q] - c[j] >= x * datr[j]:
                cnt += 1
        out[q] = cnt
    return out
