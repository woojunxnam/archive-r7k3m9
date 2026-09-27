"""Performance metrics shared by all TEST43 engines."""
from __future__ import annotations

import numpy as np
import pandas as pd

PV = 5.0
TICK = 0.25


def daily_table(bars: pd.DataFrame, equity: np.ndarray, pos: np.ndarray, anchor: str = "session") -> pd.DataFrame:
    """Daily MTM P&L.

    anchor='session': CME session date (18:00 -> 17:00 ET), MTM at the session's last bar close.
    anchor='rth'    : TradingView-dashboard style, day boundary at the close of the first RTH bar.
    """
    df = pd.DataFrame({"equity": equity, "pos": pos, "in_rth": bars["in_rth"].values})
    if anchor == "session":
        df["day"] = bars["session_date"].values
    else:
        nr = bars["in_rth"].values & ~np.concatenate([[False], bars["in_rth"].values[:-1]])
        df["day"] = np.cumsum(nr)
    g = df.groupby("day", sort=True)
    out = pd.DataFrame({
        "eq_end": g["equity"].last(),
        "max_pos": g["pos"].max(),
        "avg_pos": g["pos"].mean(),
        "end_pos": g["pos"].last(),
    })
    prev = out["eq_end"].shift(1)
    first_eq = df["equity"].iloc[0]
    out["pnl"] = out["eq_end"] - prev.fillna(first_eq)
    return out


def max_drawdown(equity: np.ndarray, init: float) -> float:
    e = np.concatenate([[init], equity])
    peak = np.maximum.accumulate(e)
    return float((peak - e).max())


def summarize(bars: pd.DataFrame, res: dict, init: float = 150000.0, commission: float = 0.62,
              slip_ticks: float = 1.0, label: str = "", pv: float = PV) -> dict:
    eq = res["equity"]
    pos = res["pos"]
    d = daily_table(bars, eq, pos, "session")
    # skip days with no bars in RTH? keep all sessions with bars.
    pnl = d["pnl"].values
    total = float(eq[-1] - init)
    sides = float(res["f_qty"].sum()) if len(res["f_qty"]) else 0.0
    comm = sides * commission
    slip = sides * slip_ticks * TICK * pv
    rth = bars["in_rth"].values
    on_mask = ~rth
    out = {
        "label": label,
        "days": int(len(d)),
        "total_pnl": total,
        "avg_daily": float(pnl.mean()) if len(pnl) else 0.0,
        "median_daily": float(np.median(pnl)) if len(pnl) else 0.0,
        "pos_day_pct": float((pnl > 0).mean() * 100) if len(pnl) else 0.0,
        "worst_day": float(pnl.min()) if len(pnl) else 0.0,
        "best_day": float(pnl.max()) if len(pnl) else 0.0,
        "max_dd": max_drawdown(eq, init),
        "avg_mes": float(pos.mean()),
        "avg_mes_rth": float(pos[rth].mean()) if rth.any() else 0.0,
        "max_mes": int(pos.max()) if len(pos) else 0,
        "avg_overnight_mes": float(d["end_pos"].mean()),
        "max_overnight_mes": int(d["end_pos"].max()),
        "contract_sides": sides,
        "commission": comm,
        "slippage": slip,
        "friction": comm + slip,
        "gross_before_cost": total + comm + slip,
        "buy_fills": int((res["f_side"] == 1).sum()),
        "sell_fills": int((res["f_side"] == -1).sum()),
    }
    out["ret_over_dd"] = out["total_pnl"] / out["max_dd"] if out["max_dd"] > 0 else np.nan
    out["pnl_per_avg_mes"] = out["total_pnl"] / out["avg_mes"] if out["avg_mes"] > 0 else np.nan
    return out


def reason_attribution(res: dict, reasons: list[str]) -> pd.DataFrame:
    """Realised P&L (FIFO, net of that fill's commission) and counts per fill reason."""
    df = pd.DataFrame({"reason": [reasons[k] for k in res["f_reason"]], "side": res["f_side"],
                       "qty": res["f_qty"], "real": res["f_real"]})
    g = df.groupby(["reason", "side"]).agg(fills=("qty", "size"), contracts=("qty", "sum"), realized=("real", "sum"))
    return g.reset_index()
