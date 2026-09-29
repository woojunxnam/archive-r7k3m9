"""Metrics for a finished Engine run. All money in USD (MES $5/pt)."""
from __future__ import annotations

import numpy as np
import pandas as pd

MARGIN_SCENARIOS = (1500.0, 2500.0, 3500.0)


def max_drawdown(equity: np.ndarray):
    """Return (max_dd <= 0, peak_idx, trough_idx)."""
    eq = np.asarray(equity, dtype=float)
    if len(eq) == 0:
        return 0.0, 0, 0
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    t = int(np.argmin(dd))
    p = int(np.argmax(eq[: t + 1])) if t > 0 else 0
    return float(dd[t]), p, t


def longest_underwater(dt: np.ndarray, equity: np.ndarray):
    """Longest period (days) from a peak until equity regains it (or end)."""
    eq = np.asarray(equity, float)
    peak = np.maximum.accumulate(eq)
    under = eq < peak - 1e-9
    runs = runs_of(under)
    best = (0.0, None, None, False)
    for s, e in runs:
        start = dt[s - 1] if s > 0 else dt[s]
        recovered = e + 1 < len(eq)
        end = dt[e + 1] if recovered else dt[e]
        d = (end - start) / np.timedelta64(1, "D")
        if d > best[0]:
            best = (float(d), str(start), str(end), recovered)
    return best


def runs_of(mask: np.ndarray):
    m = np.asarray(mask, bool)
    if not m.any():
        return []
    d = np.diff(np.concatenate([[0], m.astype(np.int8), [0]]))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1) - 1
    return list(zip(starts, ends))


def episodes(dt, mask, top=5):
    out = []
    for s, e in runs_of(mask):
        end = dt[e + 1] if e + 1 < len(dt) else dt[e]
        out.append((float((end - dt[s]) / np.timedelta64(1, "D")), str(dt[s]), str(end), e + 1 >= len(dt)))
    out.sort(key=lambda x: -x[0])
    return out[:top]


def compute(engine, label: str = "") -> dict:
    b = engine.bars
    st = engine.state
    cfg = engine.cfg
    tr = engine.trades_df
    dt = st.dt.values
    eq = st.equity.values
    cap = cfg.initial_capital
    trade_days = np.unique(b.day[b.tradeable])
    n_days = len(trade_days)
    m: dict = {"label": label}

    # ---------------- return
    unreal_end = float(st.unrealized.iloc[-1])
    m["realized_net"] = float(engine.realized_net)
    m["realized_gross_trades"] = float(engine.realized_gross)
    m["unrealized_end"] = unreal_end
    m["total_mtm_pnl"] = float(eq[-1] - cap)
    m["open_qty_end"] = int(st.qty.iloc[-1])
    if len(tr):
        wins = tr.net[tr.net > 0].sum()
        losses = -tr.net[tr.net < 0].sum()
        m["profit_factor"] = float(wins / losses) if losses > 0 else float("inf")
        m["avg_trade"] = float(tr.net.mean())
        m["median_trade"] = float(tr.net.median())
        m["win_rate"] = float((tr.net > 0).mean())
    else:
        m.update(profit_factor=np.nan, avg_trade=np.nan, median_trade=np.nan, win_rate=np.nan)
    m["trades"] = int(len(tr))
    m["entries"] = int((engine.fills_df.side == "BUY").sum()) if len(engine.fills_df) else 0
    m["trading_days"] = int(n_days)
    m["trades_per_day"] = m["trades"] / max(n_days, 1)
    years = (dt[-1] - dt[0]) / np.timedelta64(1, "D") / 365.25
    m["years"] = float(years)
    end_eq = eq[-1]
    m["cagr_mtm"] = float((end_eq / cap) ** (1 / years) - 1) if years > 0 and end_eq > 0 else np.nan
    # annual
    yr = pd.DatetimeIndex(dt).year
    s_eq = pd.Series(eq, index=yr)
    y_end = s_eq.groupby(level=0).last()
    y_start = pd.concat([pd.Series({y_end.index[0]: cap}), y_end.iloc[:-1]]).values
    real_series = pd.Series(st.realized_net.values, index=yr).groupby(level=0).last()
    real_start = np.concatenate([[0.0], real_series.values[:-1]])
    m["annual"] = {int(y): {"mtm_pnl": float(y_end[y] - y_start[k]), "realized": float(real_series[y] - real_start[k])}
                   for k, y in enumerate(y_end.index)}

    # ---------------- cost
    m["commission"] = float(engine.commission)
    m["slippage_cost"] = float(engine.slippage)
    m["roll_cost"] = float(engine.roll_cost)
    m["total_cost"] = m["commission"] + m["slippage_cost"] + m["roll_cost"]
    gross_profit = float(tr.gross[tr.gross > 0].sum()) if len(tr) else 0.0
    m["cost_over_gross_profit"] = m["total_cost"] / gross_profit if gross_profit > 0 else np.nan

    # ---------------- risk
    dd, p, t = max_drawdown(eq)
    m["max_mtm_dd"] = dd
    m["max_mtm_dd_peak"] = str(dt[p]); m["max_mtm_dd_trough"] = str(dt[t])
    dd_l, _, tl = max_drawdown(np.minimum(st.equity_low.values, eq))
    m["max_mtm_dd_intrabar_low"] = dd_l
    m["max_mtm_dd_low_trough"] = str(dt[tl])
    real_eq = cap + st.realized_net.values
    m["max_realized_dd"] = max_drawdown(real_eq)[0]
    m["min_equity"] = float(eq.min()); m["min_equity_dt"] = str(dt[int(np.argmin(eq))])
    uw = longest_underwater(dt, eq)
    m["longest_mtm_underwater_days"] = uw[0]; m["longest_underwater_span"] = (uw[1], uw[2], "recovered" if uw[3] else "NOT recovered")
    day_idx = pd.DatetimeIndex(dt).normalize()
    daily = pd.Series(eq, index=day_idx).groupby(level=0).last()
    dchg = daily.diff().fillna(daily.iloc[0] - cap)
    m["worst_day"] = (float(dchg.min()), str(dchg.idxmin().date()))
    wk = daily.resample("W-FRI").last().dropna()
    wchg = wk.diff().fillna(wk.iloc[0] - cap)
    m["worst_week"] = (float(wchg.min()), str(wchg.idxmin().date()))
    mo = daily.resample("ME").last().dropna()
    mchg = mo.diff().fillna(mo.iloc[0] - cap)
    m["worst_month"] = (float(mchg.min()), str(mchg.idxmin().date()))
    cyc = engine.cycles_df
    worst_cycle = []
    if len(cyc):
        worst_cycle.append((float(cyc.worst_mtm.min()), int(cyc.loc[cyc.worst_mtm.idxmin(), "cycle"]), "closed"))
    if engine.open_cycle:
        worst_cycle.append((float(engine.open_cycle["worst_mtm"]), int(engine.open_cycle["cycle"]), "OPEN"))
    m["worst_cycle_mtm"] = min(worst_cycle) if worst_cycle else None
    m["cycles_completed"] = int(len(cyc))
    if len(cyc):
        dur = (cyc.end_dt - cyc.start_dt).dt.total_seconds() / 86400
        m["cycle_duration_days"] = {"median": float(dur.median()), "p95": float(dur.quantile(.95)), "max": float(dur.max())}
        m["cycles_profitable_share"] = float((cyc.realized > 0).mean())
        m["contracts_per_cycle_avg"] = float(cyc.entries.mean())

    # ---------------- inventory (time-weighted over tradeable RTH bars, and over all bars)
    q = st.qty.values
    qr = q[b.tradeable]
    maxq = engine.max_total
    m["inv_avg_rth"] = float(qr.mean()); m["inv_median_rth"] = float(np.median(qr))
    m["inv_max"] = int(q.max()); m["inv_p95_rth"] = float(np.percentile(qr, 95)); m["inv_p99_rth"] = float(np.percentile(qr, 99))
    m["inv_share_rth_ge"] = {k: float((qr >= k).mean()) for k in (8, 16, 20, 24, 28, 32)}
    m["longest_max_lock"] = episodes(dt, q >= maxq, top=5)
    m["longest_gt24"] = episodes(dt, q > 24, top=5)

    # ---------------- exposure / margin
    notional = q * st.raw_c.values * cfg.point_value
    m["peak_notional"] = float(notional.max()); m["avg_notional_rth"] = float(notional[b.tradeable].mean())
    with np.errstate(divide="ignore", invalid="ignore"):
        lev = np.where(eq > 0, notional / eq, np.inf)
    m["peak_notional_over_equity"] = float(np.nanmax(lev))
    m["margin_stress"] = {}
    for mg in MARGIN_SCENARIOS:
        excess = eq - q * mg
        k = int(np.argmin(excess))
        m["margin_stress"][int(mg)] = {"min_excess_liquidity": float(excess[k]), "at": str(dt[k]),
                                       "bars_negative": int((excess < 0).sum())}

    # ---------------- lanes
    m["lanes"] = {}
    for lnm, ln in engine.lanes.items():
        lt = tr[tr.lane == lnm] if len(tr) else tr
        d = {"capacity": ln.spec.capacity, "exit_mode": ln.spec.exit_mode, "tp_pts": ln.spec.tp_pts}
        d["trades"] = int(len(lt))
        if len(lt):
            hold = (lt.exit_dt - lt.entry_dt).dt.total_seconds() / 60
            d.update(pnl_net=float(lt.net.sum()), win_rate=float((lt.net > 0).mean()), trades_per_day=len(lt) / n_days,
                     pnl_per_day=float(lt.net.sum()) / n_days, avg_hold_min=float(hold.mean()), median_hold_min=float(hold.median()))
        lq = st[f"qty_{lnm}"].values
        d["full_share_rth"] = float((lq[b.tradeable] >= ln.spec.capacity).mean())
        d["longest_full"] = episodes(dt, lq >= ln.spec.capacity, top=3)
        d["open_qty_end"] = int(lq[-1])
        m["lanes"][lnm] = d
    m["open_inventory"] = engine.open_df.to_dict("records") if len(engine.open_df) else []
    m["open_cycle"] = {k: (str(v) if isinstance(v, np.datetime64) else v) for k, v in engine.open_cycle.items()} if engine.open_cycle else None
    m["ambiguous_bars"] = engine.ambiguous_bars
    m["cancelled_capacity"] = engine.cancelled_capacity
    return m
