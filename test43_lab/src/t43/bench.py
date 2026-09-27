"""Constant-exposure long benchmarks (long beta) for MES.

Constant N MES long: enter at the first bar's open (+1 tick, commission), hold through history.
Back-adjusted prices make rolls P&L-neutral; an explicit roll cost of
2 sides x (commission + 1 tick) per contract is charged on every roll session.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import daily_table, max_drawdown

PV = 5.0
TICK = 0.25


def constant_long(bars: pd.DataFrame, n: float, comm=0.62, slip_ticks=1.0, roll_day=None, init=150000.0, pv=PV):
    o = bars["o"].values
    c = bars["c"].values
    entry = o[0] + slip_ticks * TICK
    eq = init + n * pv * (c - entry) - n * comm
    roll_cost = 0.0
    if roll_day is not None:
        per = 2 * (comm + slip_ticks * TICK * pv)
        sess = bars["session_date"].values
        first = np.concatenate([[True], sess[1:] != sess[:-1]])
        hits = roll_day & first
        cum = np.cumsum(hits) * n * per
        eq = eq - cum
        roll_cost = float(cum[-1])
    pos = np.full(len(c), n)
    return eq, pos, roll_cost


def summarize_const(bars, n, **kw):
    eq, pos, rc = constant_long(bars, n, **kw)
    init = kw.get("init", 150000.0)
    d = daily_table(bars, eq, pos.astype(float), "session")
    pnl = d["pnl"].values
    return {
        "label": f"CONST_{n:g}_MES",
        "days": len(d),
        "total_pnl": float(eq[-1] - init),
        "avg_daily": float(pnl.mean()),
        "median_daily": float(np.median(pnl)),
        "pos_day_pct": float((pnl > 0).mean() * 100),
        "worst_day": float(pnl.min()),
        "best_day": float(pnl.max()),
        "max_dd": max_drawdown(eq, init),
        "avg_mes": float(n),
        "max_mes": float(n),
        "roll_cost": rc,
        "ret_over_dd": float((eq[-1] - init) / max(max_drawdown(eq, init), 1e-9)),
    }, d
