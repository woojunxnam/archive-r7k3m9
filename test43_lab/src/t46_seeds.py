"""TEST46 local-engine reconstruction of the frozen INDEX6-LONG seed signals (from the frozen Pine sources) on canonical
5m RTH bars.  Each function returns the list of entry bar indices (signal on bar i close -> entry at bar i+1 open) and a
common frozen shell simulator reproduces the original exit (2 x ATR stop, 120-min time exit, RTH flatten).
Sources: authorities/index6/FROZEN_STRATEGY_LC02.pine, FROZEN_FACTORY_T07_LC03.pine (T07-01, T07-11),
TEST22_BATCHED_NATIVE_MASTER_V1 (T22-07), TEST30_REGIME_CONTEXT_MASTER_V1_PRECOMPILE (T30-L1)."""
import numpy as np
import pandas as pd

import t46_common as C

TICK = 0.25


def _clock(b):
    m = (b.t.dt.hour * 60 + b.t.dt.minute).values
    first = np.r_[True, b.date.values[1:] != b.date.values[:-1]]
    return m, first


def tod_rvol(b):
    """same-time-of-day RVOL: volume / average of the same 5m slot over the prior <=20 sessions (>=10 required)."""
    m, first = _clock(b)
    v = b.v.values.astype(float)
    slot = (m - 570) // 5
    hist = np.full((81, 20), np.nan)
    ptr = 0; seen = False
    out = np.full(len(b), np.nan)
    for i in range(len(b)):
        if first[i]:
            if seen:
                ptr = (ptr + 1) % 20
            seen = True
        s = slot[i]
        if 0 <= s < 81:
            h = hist[s]
            cnt = np.sum(~np.isnan(h))
            if cnt >= 10:
                avg = np.nansum(h) / cnt
                out[i] = v[i] / avg if avg > 0 else np.nan
            hist[s, ptr] = v[i]
    return out


def rth_vwap(b):
    m, first = _clock(b)
    tp = (b.h + b.l + b.c).values / 3; v = b.v.values.astype(float)
    grp = np.cumsum(first)
    pv = pd.Series(tp * v).groupby(grp).cumsum().values; vv = pd.Series(v).groupby(grp).cumsum().values
    return np.where(vv > 0, pv / vv, np.nan)


def lc02(b):
    m, first = _clock(b)
    o, h, l, c = b.o.values, b.h.values, b.l.values, b.c.values
    atr = C.pine_atr(h, l, c, 14)
    rv = tod_rvol(b); vw = rth_vwap(b)
    rng = np.maximum(h - l, TICK); cloc = (c - l) / rng
    sig = np.zeros(len(b), bool)
    seen_c02 = False; orh = np.nan; broke = False; brk = -1
    for i in range(len(b)):
        if first[i]:
            seen_c02 = False; orh = h[i]; broke = False; brk = -1
        elif 570 <= m[i] < 600:
            orh = max(orh, h[i])
        can = 570 <= m[i] < 845
        c02 = can and not np.isnan(vw[i]) and not np.isnan(atr[i]) and l[i] < vw[i] - 1.25 * atr[i] and c[i] > vw[i] - 1.25 * atr[i] \
            and c[i] > o[i] and cloc[i] >= 0.55 and not np.isnan(rv[i]) and rv[i] >= 0.80
        if not (570 <= m[i] < 600) and not np.isnan(orh) and c[i] > orh:
            if not broke:
                brk = i
            broke = True
        bfb = 100000 if brk < 0 else i - brk
        c05 = can and broke and 1 <= bfb <= 6 and not np.isnan(atr[i]) and l[i] <= orh + 0.20 * atr[i] and l[i] >= orh - 0.25 * atr[i] \
            and c[i] > orh and c[i] > o[i]
        sig[i] = c05 and seen_c02
        if c02:
            seen_c02 = True
    return sig, atr


def t07(b, which):
    m, first = _clock(b)
    o, h, l, c = b.o.values, b.h.values, b.l.values, b.c.values
    atr = C.pine_atr(h, l, c, 14)
    ema20 = C.pine_ema(c, 20); ema50 = C.pine_ema(c, 50)
    rv = tod_rvol(b); vw = rth_vwap(b)
    rng = np.maximum(h - l, TICK); cloc = (c - l) / rng
    sig = np.zeros(len(b), bool)
    sh = sl = np.nan; prevH = prevL = prevC = np.nan; topen = np.nan
    fhH = fhL = np.nan; fhMove = fhRange = np.nan
    for i in range(len(b)):
        if first[i]:
            if not np.isnan(sh):
                prevH, prevL, prevC = sh, sl, c[i - 1]
            sh, sl, topen = h[i], l[i], o[i]
            fhH, fhL = h[i], l[i]; fhMove = fhRange = np.nan
        else:
            sh = max(sh, h[i]); sl = min(sl, l[i])
        if 570 <= m[i] < 630:
            fhH = max(fhH, h[i]); fhL = min(fhL, l[i])
        if m[i] == 625 and atr[i] > 0:
            fhMove = (c[i] - topen) / atr[i]; fhRange = (fhH - fhL) / atr[i]
        if which == "T07-01":
            ev = 600 <= m[i] < 870 and not np.isnan(prevH) and c[i] > prevH + 0.10 * atr[i] and ema20[i] > ema50[i] and c[i] > vw[i] \
                and cloc[i] >= 0.70 and not np.isnan(rv[i]) and rv[i] >= 1.0
        else:                                                      # T07-11 first-hour trend day, signal bar 12:55
            ev = m[i] == 775 and not np.isnan(fhMove) and not np.isnan(fhRange) and fhMove >= 0.80 and fhRange >= 1.20 \
                and c[i] > vw[i] + 0.35 * atr[i] and ema20[i] > ema50[i] and cloc[i] >= 0.60
        sig[i] = bool(ev)
    return sig, atr


def simulate_shell(b, sig, atr, hold_min=120, flat_m=970, stop_atr=2.0, slip=1, max_per_day=1):
    """frozen shell: signal at bar i close -> market entry bar i+1 open (+slip tick); stop = round(2*atr/tick) ticks
    from fill; time exit when bar close time >= entry time + hold -> exit at that bar close (-slip); flatten on the bar
    opening at flat_m (16:10) at its close.  One position, max one entry per day."""
    m, first = _clock(b)
    o, h, l, c = b.o.values, b.h.values, b.l.values, b.c.values
    raw_off = (b.o - b.raw_o).values
    tms = b.t.values
    trades = []
    pos = False; entries = 0
    for i in range(len(b) - 1):
        if first[i]:
            entries = 0
        if pos:
            stop_px = ep - stop_t * TICK
            hit = False
            if l[i] <= stop_px and i > ei - 1:
                fill = min(o[i], stop_px) if i > ei else stop_px
                trades.append((ei, i, ep, fill - slip * TICK, "SL")); hit = True
            elif (m[i] + 5 - em) >= hold_min or (b.date.values[i] != b.date.values[ei]):
                trades.append((ei, i, ep, c[i] - slip * TICK, "TIME")); hit = True
            elif m[i] == flat_m:
                trades.append((ei, i, ep, c[i] - slip * TICK, "RTH")); hit = True
            if hit:
                pos = False
        if not pos and sig[i] and entries < max_per_day and not np.isnan(atr[i]) and b.date.values[i + 1] == b.date.values[i]:
            ei = i + 1; ep = o[ei] + slip * TICK; em = m[ei]
            stop_t = max(1, int(round(stop_atr * atr[i] / TICK)))
            pos = True; entries += 1
            # stop may trigger on the entry bar itself
            if l[ei] <= ep - stop_t * TICK:
                pass
    out = pd.DataFrame(trades, columns=["ei", "xi", "entry_px", "exit_px", "reason"])
    out["entry_time"] = b.t.values[out.ei]; out["exit_time"] = b.t.values[out.xi]
    out["raw_entry_px"] = out.entry_px - raw_off[out.ei]
    return out
