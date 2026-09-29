"""Stress-window analysis: mandatory 2025-02..06 regression + top-N MTM drawdown windows."""
from __future__ import annotations

import numpy as np
import pandas as pd

REGRESSION_WINDOW = ("2025-02-01", "2025-07-31")


def window_report(engine, start, end) -> dict:
    st = engine.state
    b = engine.bars
    dt = pd.DatetimeIndex(st.dt)
    msk = (dt >= pd.Timestamp(start)) & (dt <= pd.Timestamp(end))
    s = st[msk]
    tr = engine.trades_df
    fl = engine.fills_df
    tm = b.tradeable[msk]
    q = s.qty.values
    maxq = engine.max_total
    at_max = q >= maxq
    first_max = str(s.dt[at_max].iloc[0]) if at_max.any() else None
    # longest lock inside window
    from .metrics import episodes
    ep = episodes(s.dt.values, at_max, top=1)
    eq = s.equity.values
    peak = np.maximum.accumulate(np.concatenate([[st.equity[~msk & (dt < pd.Timestamp(start))].max() if (dt < pd.Timestamp(start)).any() else eq[0]], eq]))[1:]
    dd = eq - peak
    k = int(np.argmin(dd))
    fw = fl[(pd.DatetimeIndex(fl.dt) >= pd.Timestamp(start)) & (pd.DatetimeIndex(fl.dt) <= pd.Timestamp(end))] if len(fl) else fl
    tw = tr[(pd.DatetimeIndex(tr.exit_dt) >= pd.Timestamp(start)) & (pd.DatetimeIndex(tr.exit_dt) <= pd.Timestamp(end))] if len(tr) else tr
    lanes = {}
    for ln in engine.lanes:
        lq = s[f"qty_{ln}"].values
        lt = tw[tw.lane == ln] if len(tw) else tw
        lanes[ln] = dict(trades=int(len(lt)), pnl=float(lt.net.sum()) if len(lt) else 0.0,
                         full_share_rth=float((lq[tm] >= engine.lanes[ln].spec.capacity).mean()) if tm.any() else None)
    return dict(window=[start, end], buys=int((fw.side == "BUY").sum()) if len(fw) else 0,
                sells=int((fw.side == "SELL").sum()) if len(fw) else 0,
                realized_in_window=float(tw.net.sum()) if len(tw) else 0.0,
                first_time_at_max=first_max, longest_max_lock_in_window=ep[0] if ep else None,
                share_rth_at_max=float(at_max[tm].mean()) if tm.any() else None,
                worst_unrealized=float(s.unrealized.min()), worst_unrealized_dt=str(s.dt.iloc[int(np.argmin(s.unrealized.values))]),
                mtm_dd_from_prior_peak=float(dd[k]), mtm_dd_trough_dt=str(s.dt.iloc[k]),
                equity_start=float(eq[0]), equity_end=float(eq[-1]), min_equity=float(eq.min()),
                lanes=lanes)


def top_drawdowns(engine, n=10) -> list[dict]:
    """Non-overlapping MTM drawdown episodes on daily closing equity (peak -> trough -> recovery)."""
    st = engine.state
    day = pd.DatetimeIndex(st.dt).normalize()
    daily = st.groupby(day).agg(equity=("equity", "last"), qty=("qty", "max"))
    eq = daily["equity"].values
    idx = daily.index
    peak = np.maximum.accumulate(eq)
    under = eq < peak - 1e-9
    out = []
    i = 0
    N = len(eq)
    while i < N:
        if not under[i]:
            i += 1
            continue
        s = i
        while i < N and under[i]:
            i += 1
        e = i - 1
        seg = eq[s:e + 1]
        k = s + int(np.argmin(seg))
        pk = s - 1 if s > 0 else s
        out.append(dict(peak=str(idx[pk].date()), trough=str(idx[k].date()),
                        recovered=str(idx[i].date()) if i < N else "NOT RECOVERED",
                        depth=float(eq[k] - peak[k]), days_to_trough=int((idx[k] - idx[pk]).days),
                        days_underwater=int(((idx[i] if i < N else idx[-1]) - idx[pk]).days),
                        max_qty=int(daily.qty.values[s:e + 1].max())))
    out.sort(key=lambda x: x["depth"])
    return out[:n]
