"""TEST96: TS22 T22-07 exact port of frozen TEST22_BATCHED_NATIVE_MASTER_V1.pine (signal s07, LONG) on canonical NQ 5m RTH bars, executed as 1 MNQ.

s07 = ready and distAtr < 0 and distAtr >= -0.50 and macdLine > macdSignal and prevMacdLine <= prevMacdSignal and close > open
  ready   = inUs (bar open 09:30..15:40) and warm and after1000 (bar open 10:00..14:25) and vwap and not flattenNow
  warm    = completedSessions >= 60 and atrPrev (Wilder ATR14 of completed US-session daily H/L/C ranges, >=14 sessions) > 0
  vwap    = US-session hlc3*volume VWAP reset at the 09:30 bar;  distAtr = (close - vwap) / atrPrev
  MACD    = EMA12/EMA26/signal9 (alpha 2/(n+1), seeded with first value) updated on US bars only, continuous across days
Execution: completed-bar signal -> market entry next bar open; stop = entry_fill - ceil(2*atrPrev/tick) ticks (Pine strategy.exit loss=,
  referenced to the slipped Pine entry fill = open + 1 tick); 1 entry/day; MAXHOLD close at bar whose close >= entry open + 120 min;
  1545_FLAT at close of the 15:40 bar; SESSION_LAST at close of the day's last bar (early-close days).
Economics: prices are raw bar prices; cost per side = $0.62 + 1 tick ($1.12), SLIP4 = $0.62 + 4 ticks ($2.62). 1 MNQ = $2/pt.
"""
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t96_data as X  # noqa: E402
X.register()
import t46_common as C  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "t96")
TICK, PV = 0.25, 2.0
COST, COST4 = 0.62 + 1 * TICK * PV, 0.62 + 4 * TICK * PV


def bars(inst="NQ"):
    b = C.bars5(inst).copy()
    b["mod"] = b.t.dt.hour * 60 + b.t.dt.minute
    b = b[(b["mod"] >= 570) & (b["mod"] <= 940) & (b.t.dt.dayofweek < 5)].reset_index(drop=True)  # inUs: 0930-1545 session (open-stamped)
    return b


def indicators(b):
    o, h, l, c, v = (b[k].values.astype(float) for k in ("o", "h", "l", "c", "v"))
    mod = b["mod"].values; n = len(b)
    aH = aL = aC = prevSC = atr14 = np.nan; atrCount = completed = 0
    cumV = cumPV = 0.0
    e12 = e26 = sig = np.nan
    atrPrev = np.full(n, np.nan); warm = np.zeros(n, bool); vwap = np.full(n, np.nan)
    macd = np.full(n, np.nan); macds = np.full(n, np.nan)
    for i in range(n):
        first = mod[i] == 570
        if first:
            if not (np.isnan(aH) or np.isnan(aL) or np.isnan(aC)):
                trp = aH - aL if np.isnan(prevSC) else max(aH - aL, abs(aH - prevSC), abs(aL - prevSC))
                atr14 = trp if np.isnan(atr14) else (atr14 * 13.0 + trp) / 14.0
                atrCount += 1; completed += 1; prevSC = aC
            aH, aL, aC = h[i], l[i], c[i]
        else:
            aH = h[i] if np.isnan(aH) else max(aH, h[i]); aL = l[i] if np.isnan(aL) else min(aL, l[i]); aC = c[i]
        ap = atr14 if atrCount >= 14 else np.nan
        atrPrev[i] = ap; warm[i] = completed >= 60 and not np.isnan(ap) and ap > 0
        if first:
            cumV = cumPV = 0.0
        cumV += v[i]; cumPV += (h[i] + l[i] + c[i]) / 3.0 * v[i]
        vwap[i] = cumPV / cumV if cumV > 0 else np.nan
        e12 = c[i] if np.isnan(e12) else e12 + 2.0 / 13.0 * (c[i] - e12)
        e26 = c[i] if np.isnan(e26) else e26 + 2.0 / 27.0 * (c[i] - e26)
        m = e12 - e26
        sig = m if np.isnan(sig) else sig + 2.0 / 10.0 * (m - sig)
        macd[i], macds[i] = m, sig
    return atrPrev, warm, vwap, macd, macds


def replay(b):
    o, h, l, c = (b[k].values.astype(float) for k in ("o", "h", "l", "c"))
    mod = b["mod"].values; date = b.date.values; t = b.t; n = len(b)
    atrPrev, warm, vwap, macd, macds = indicators(b)
    last_of_day = np.r_[date[1:] != date[:-1], True]
    pm = np.r_[np.nan, macd[:-1]]; ps = np.r_[np.nan, macds[:-1]]
    with np.errstate(invalid="ignore"):
        dist = np.where(warm & ~np.isnan(vwap), (c - vwap) / atrPrev, np.nan)
        ready = warm & (mod >= 600) & (mod < 870) & ~np.isnan(vwap) & (mod != 940)
        s07 = ready & (dist < 0) & (dist >= -0.50) & (macd > macds) & ~np.isnan(pm) & ~np.isnan(ps) & (pm <= ps) & (c > o)
    # enteredToday resets only on the 09:30 (firstUs) bar, exactly as in the Pine
    sess_id = np.cumsum(mod == 570)
    trades = []; i = 0; entered_sess = -1
    while i < n - 1:
        if s07[i] and sess_id[i] != entered_sess and not last_of_day[i]:
            entered_sess = sess_id[i]
            ei = i + 1                                           # next bar (same session: signal bar is never the day's last bar)
            ticks = max(1, int(math.ceil(2.0 * atrPrev[i] / TICK - 1e-9)))
            ep = o[ei]; stp = (ep + TICK) - ticks * TICK         # Pine loss= measured from slipped fill (open + 1 tick)
            et_ms = t.iloc[ei]; xi = None
            for k in range(ei, n):
                if date[k] != date[ei]:
                    raise RuntimeError("unreachable")
                if l[k] <= stp:
                    xi, xp, why = k, (min(stp, o[k]) if k > ei else stp), "STOP"; break
                bar_close = t.iloc[k] + pd.Timedelta(minutes=5)
                if bar_close >= et_ms + pd.Timedelta(minutes=120):
                    xi, xp, why = k, c[k], "MAXHOLD"; break
                if mod[k] == 940:
                    xi, xp, why = k, c[k], "1545_FLAT"; break
                if last_of_day[k]:
                    xi, xp, why = k, c[k], "SESSION_LAST"; break
            trades.append((t.iloc[ei], ep, t.iloc[xi] + pd.Timedelta(minutes=5), xp, why))
            i = xi + 1; continue
        i += 1
    T = pd.DataFrame(trades, columns=["entry_time", "entry_px", "exit_time", "exit_px", "exit_reason"])
    T["gross_usd"] = (T.exit_px - T.entry_px) * PV
    T["net_usd"] = T.gross_usd - 2 * COST
    T["net_usd_slip4"] = T.gross_usd - 2 * COST4
    return T


def main():
    b = bars("NQ"); T = replay(b)
    os.makedirs(OUT, exist_ok=True)
    T[["entry_time", "entry_px", "exit_time", "exit_px", "exit_reason", "net_usd"]].to_csv(os.path.join(OUT, "TS22_T2207_REPLAY.csv"), index=False)
    first_warm = b.t.iloc[np.argmax(indicators(b)[1])]
    yrs = (b.t.iloc[-1] - first_warm).days / 365.25
    print(f"TS22 T22-07 NQ LONG -> 1 MNQ   data {b.t.iloc[0].date()}..{b.t.iloc[-1].date()}  warm from {first_warm}")
    print(f"trades {len(T)}  per year {len(T)/yrs:.1f}  net ${T.net_usd.sum():,.0f}  $/trade {T.net_usd.mean():.2f}  "
          f"net SLIP4 ${T.net_usd_slip4.sum():,.0f} ({T.net_usd_slip4.mean():.2f}/tr)  win% {100*(T.net_usd>0).mean():.1f}")
    print("exit mix", T.exit_reason.value_counts().to_dict())
    y = T.groupby(T.entry_time.dt.year).agg(trades=("net_usd", "size"), net=("net_usd", "sum"), net_slip4=("net_usd_slip4", "sum"))
    print(y.round(0).to_string())
    print("LEDGER: none exists locally for TS22 -> parity NOT checked (unverified port)")


if __name__ == "__main__":
    main()
