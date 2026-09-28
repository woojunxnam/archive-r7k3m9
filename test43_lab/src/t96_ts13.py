"""TEST96 Track B/C1: TS13-S01 (T13-07 '3D up-pressure EMA20 pullback LONG', YM -> MYM) exact port of the frozen TEST13 Pine factory V1 on canonical
YM 5m RTH bars (open-stamped 09:30..15:40).  Rules copied verbatim: RTH-bar ATR14 (5m) and EMA20 / EMA50 over research-RTH bars, RTH VWAP,
same-slot 20-day RVOL (min 10), threeDayUpPressure (c0 > c1 > c2 and c0 - c2 >= 0.75 x avg3 day range), window 10:00-13:30 (bar open),
next-bar market entry, 2 x rthAtr stop, 120-min time exit (bar close), 15:45 flat, 1 entry / day.  Also TS17-S01 structural status."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t96_data as X  # noqa: E402
X.register()
import t46_common as C  # noqa: E402
import t96_common as W  # noqa: E402


def bars(inst="YM"):
    b = C.bars5(inst).copy(); b["mod"] = b.t.dt.hour * 60 + b.t.dt.minute
    return b[(b["mod"] >= 570) & (b["mod"] <= 940)].reset_index(drop=True)          # 09:30 .. 15:40 open-stamped


def replay(b, pv=0.5, tick=1.0, cs=1.12):
    o, h, l, c, v, mod = [b[k].values.astype(float) if k != "mod" else b[k].values for k in ("o", "h", "l", "c", "v", "mod")]
    date = b.date.values; n = len(b)
    tr_hist = []; atr = np.full(n, np.nan); e20 = np.full(n, np.nan); e50 = np.full(n, np.nan); pc = np.nan; a20, a50 = 2 / 21, 2 / 51; E20 = E50 = np.nan
    vw = np.full(n, np.nan); pv_c = v_c = 0.0
    tod = {}; rv = np.full(n, np.nan)
    day_rng, day_cls = [], []; sh = sl = scl = np.nan
    up3 = np.zeros(n, bool); cur = None; hist = {}
    for i in range(n):
        first = mod[i] == 570
        if first:
            if cur is not None and sh == sh:
                day_rng.append(sh - sl); day_cls.append(scl); day_rng[:] = day_rng[-20:]; day_cls[:] = day_cls[-20:]
            cur = date[i]; sh, sl, scl = h[i], l[i], c[i]; pv_c = (h[i] + l[i] + c[i]) / 3 * v[i]; v_c = v[i]
        else:
            sh, sl, scl = max(sh, h[i]), min(sl, l[i]), c[i]; pv_c += (h[i] + l[i] + c[i]) / 3 * v[i]; v_c += v[i]
        trn = (h[i] - l[i]) if pc != pc else max(h[i] - l[i], abs(h[i] - pc), abs(l[i] - pc))
        tr_hist.append(trn); tr_hist[:] = tr_hist[-14:]; atr[i] = np.mean(tr_hist) if len(tr_hist) >= 14 else np.nan
        E20 = c[i] if E20 != E20 else a20 * c[i] + (1 - a20) * E20; E50 = c[i] if E50 != E50 else a50 * c[i] + (1 - a50) * E50
        e20[i], e50[i] = E20, E50; pc = c[i]
        vw[i] = pv_c / v_c if v_c > 0 else np.nan
        slot = (mod[i] - 570) // 5; q = hist.setdefault(slot, [])
        prior = q[-20:]; rv[i] = v[i] / np.mean(prior) if len(prior) >= 10 and np.mean(prior) > 0 else np.nan
        q.append(v[i]); hist[slot] = q[-20:]
        if len(day_cls) >= 3 and len(day_rng) >= 3:
            c0, c1, c2 = day_cls[-1], day_cls[-2], day_cls[-3]; a3 = np.mean(day_rng[-3:])
            up3[i] = a3 > 0 and c0 > c1 > c2 and (c0 - c2) >= 0.75 * a3
    rng = np.maximum(h - l, tick); cloc = (c - l) / rng
    sig = (mod >= 600) & (mod < 810) & up3 & (e20 > e50) & (l <= e20) & (c > e20) & (c > o) & (c > vw) & (cloc >= 0.65) & (rv >= 0.80) & ~np.isnan(atr) & (atr > 0)
    trades = []; i = 0; last_day = None
    while i < n - 1:
        if sig[i] and date[i] != last_day and date[i + 1] == date[i]:
            ei = i + 1; ep = o[ei]; stp = ep - max(1, round(2.0 * atr[i] / tick)) * tick; last_day = date[i]; xi = None
            for k in range(ei, n):
                if date[k] != date[ei]:
                    xi, xp, why = k - 1, c[k - 1], "EOD"; break
                if l[k] <= stp:
                    xi, xp, why = k, min(stp, o[k]) if k > ei else stp, "SL"; break
                if (mod[k] + 5) - mod[ei] >= 120:
                    xi, xp, why = k, c[k], "TIME"; break
                if mod[k] == 940:
                    xi, xp, why = k, c[k], "FLAT_1545"; break
            if xi is None:
                break
            trades.append((b.t.iloc[ei], ep, b.t.iloc[xi] + pd.Timedelta(minutes=5), xp, why)); i = xi + 1; continue
        i += 1
    T = pd.DataFrame(trades, columns=["entry_time", "entry_px", "exit_time", "exit_px", "why"])
    T["net"] = (T.exit_px - T.entry_px) * pv - 2 * cs
    return T


def main():
    b = bars("YM"); T = replay(b); T.to_csv(os.path.join(W.OUT, "TS13_S01_YM_REPLAY.csv"), index=False)
    ctx = W.main_ctx(); I = ctx["Is"]["YM"]; si = pd.Index(I.sess)
    d = np.zeros(I.n); np.add.at(d, si.get_indexer(T.entry_time.dt.normalize()), T.net.values); d[~I.full] = 0
    import box_common as B
    r = B.risk(d[I.full]); fd = {nm: float(d[np.asarray((I.sess >= a) & (I.sess <= b_))].mean()) for nm, a, b_ in B.FOLDS}
    rm, rc = B.risk(ctx["main"][I.full]), B.risk((ctx["main"] + d)[I.full])
    o = {"module": "TS13_S01_YM_T13-07_REPLAY", "status": "PORTED FROM FROZEN PINE (parity vs ledger: see LEDGER field)", "trades": len(T),
         "avg_day": r["avg_day"], "usd_per_trade": float(T.net.mean()), "max_dd": r["max_dd"], "folds": fd, "corr_to_main": float(np.corrcoef(d[I.full], ctx["main"][I.full])[0, 1]),
         "main_plus_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"], "main_plus_maxdd": rc["max_dd"], "main_maxdd": rm["max_dd"], "exit_mix": T.why.value_counts().to_dict(),
         "LEDGER": "none recovered for TS13 (see recovery report) -> RESEARCH_ONLY_APPROX (unverified port)",
         "TS17_S01": "BLOCKED_STRUCTURAL: T17-03 requires TradingView request.footprint() buy/sell delta and imbalance rows (order-flow data not in canonical OHLCV)",
         "TS21_S01": "OUT OF SCOPE: YM SHORT (LONG-only research lane)"}
    W.save("T96_C1_LEGACY_YM.json", o); print(o)


if __name__ == "__main__":
    main()
