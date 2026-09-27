"""TEST43 research harness: frozen splits, period metrics, risk envelopes, margin."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import bars as B
from . import v6x
from .metrics import max_drawdown

INIT = 150000.0
PV = 5.0
# Frozen chronological splits (decided before any optimisation, from data coverage 2019-05-05..2026-05-27)
DEV_END = pd.Timestamp("2024-12-31")
VAL_END = pd.Timestamp("2025-09-30")
SPLITS = {
    "DEV": (None, DEV_END),
    "VAL": (DEV_END + pd.Timedelta(days=1), VAL_END),
    "HOLDOUT": (VAL_END + pd.Timedelta(days=1), None),
}
ENVELOPES = {  # name: (maxDD, worst day floor)
    "CONSERVATIVE": (10000, -2000),
    "MODERATE": (15000, -3000),
    "AGGRESSIVE": (20000, -5000),
}


def load(path_3m: str) -> tuple[pd.DataFrame, dict]:
    b = pd.read_parquet(path_3m)
    a = B.to_arrays(b)
    if "roll_adjacent" in b.columns:
        # a roll session is flagged on all its bars; kernel charges once per session
        a["roll_day"] = b["roll_adjacent"].fillna(False).astype(bool).values
    if "raw_o" in b.columns:
        a["mref"] = b["raw_o"].values.astype(np.float64)
        a["mref_c"] = (b["c"] - b["cum_adjustment"].astype(float)).values.astype(np.float64)
    return b, a


def truncate(b: pd.DataFrame, a: dict, end: pd.Timestamp | None):
    if end is None:
        return b, a
    m = (b["session_date"] <= end).values
    n = int(m.sum())
    b2 = b.iloc[:n].reset_index(drop=True)
    a2 = {k: (v[:n] if isinstance(v, np.ndarray) and len(v) == len(m) else v) for k, v in a.items()}
    return b2, a2


def daily(b: pd.DataFrame, res: dict) -> pd.DataFrame:
    df = pd.DataFrame({"day": b["session_date"].values, "eq": res["equity"], "pos": res["pos"]})
    g = df.groupby("day", sort=True)
    d = pd.DataFrame({"eq_end": g["eq"].last(), "avg_pos": g["pos"].mean(), "max_pos": g["pos"].max(),
                      "end_pos": g["pos"].last()})
    d["pnl"] = d["eq_end"].diff().fillna(d["eq_end"].iloc[0] - INIT)
    return d


def period_stats(d: pd.DataFrame, start=None, end=None) -> dict:
    x = d
    if start is not None:
        x = x[x.index >= start]
    if end is not None:
        x = x[x.index <= end]
    if len(x) == 0:
        return {}
    pnl = x["pnl"].values
    eq = np.concatenate([[0.0], np.cumsum(pnl)])
    dd = float((np.maximum.accumulate(eq) - eq).max())
    srt = np.sort(pnl)[::-1]
    tot = float(pnl.sum())
    return {
        "days": len(x), "total": tot, "avg_daily": float(pnl.mean()), "median": float(np.median(pnl)),
        "pos_pct": float((pnl > 0).mean() * 100), "worst_day": float(pnl.min()), "best_day": float(pnl.max()),
        "max_dd": dd, "avg_mes": float(x["avg_pos"].mean()), "max_mes": float(x["max_pos"].max()),
        "avg_on_mes": float(x["end_pos"].mean()), "max_on_mes": float(x["end_pos"].max()),
        "avg_ex_top1": float((tot - srt[:1].sum()) / len(x)), "avg_ex_top3": float((tot - srt[:3].sum()) / len(x)),
        "avg_ex_top5": float((tot - srt[:5].sum()) / len(x)),
        "ret_dd": tot / dd if dd > 0 else np.nan,
    }


def envelope(st: dict) -> str:
    for name, (mdd, wd) in ENVELOPES.items():
        if st.get("max_dd", 1e18) <= mdd and st.get("worst_day", -1e18) >= wd:
            return name
    return "EXPLORATORY"


def margin_util(b, a, res, pct=0.10):
    """max over bars of pos*rawPrice*5*pct / equity (TV-style 10% margin); >1 = breach."""
    px = a.get("mref_c", b["c"].values)
    req = res["pos"] * px * PV * pct
    eq = res["equity"]
    util = np.where(eq > 0, req / np.maximum(eq, 1.0), np.where(req > 0, np.inf, 0.0))
    return float(util.max())


def evaluate(b, a, prm, label="", periods=("DEV", "VAL", "HOLDOUT", "FULL"), extra=None):
    res = v6x.run(a, prm)
    d = daily(b, res)
    out = {"label": label}
    for p in periods:
        if p == "FULL":
            st = period_stats(d)
        else:
            s, e = SPLITS[p]
            st = period_stats(d, s, e)
        for k, v in st.items():
            out[f"{p}_{k}"] = v
        if st:
            out[f"{p}_env"] = envelope(st)
    out["margin_util"] = margin_util(b, a, res)
    out["margin_breach"] = bool(out["margin_util"] > 1.0)
    out["min_equity"] = float(res["equity"].min())
    out["contract_sides"] = float(res["f_qty"].sum())
    out["fills"] = int(len(res["f_qty"]))
    if extra:
        out.update(extra)
    return out, res, d


def matched_const(d_const1: pd.DataFrame, avg_mes: float, start=None, end=None) -> dict:
    """Constant-long benchmark scaled to a candidate's average MES (fractional allowed, frictionless scaling)."""
    x = d_const1.copy()
    x["pnl"] = x["pnl"] * avg_mes
    x["avg_pos"] = avg_mes; x["max_pos"] = avg_mes; x["end_pos"] = avg_mes
    return period_stats(x, start, end)
