"""Data loading and 3-minute aggregation for TEST43.

Canonical convention (TEST32 inventory, proven by volume/range matching):
  * ``dt`` is tz-naive America/New_York and is the bar END minute
    (a 1m bar stamped 09:31 covers [09:30, 09:31)).
  * TradingView stamps bars by OPEN time.  A TradingView 3m bar stamped T is
    reproduced from canonical 1m bars with dt in (T, T+3].

The 3m bar grid is aligned to clock multiples of 3 minutes (CME session open
18:00 and RTH open 09:30 are both on the grid), which matches TradingView.
Buckets with zero observed 1m bars simply do not exist (TradingView prints no
bar either).  Nothing is interpolated.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MES_POINT_VALUE = 5.0
TICK = 0.25


def load_canonical_1m(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return df


def normalise_1m(df: pd.DataFrame) -> pd.DataFrame:
    """Return a 1m frame with columns dt,o,h,l,c,v (+contract/cum_adjustment/roll_adjacent if present)."""
    cols = {c.lower(): c for c in df.columns}
    out = pd.DataFrame()
    dtcol = cols.get("dt") or cols.get("timestamp") or cols.get("ts")
    out["dt"] = pd.to_datetime(df[dtcol])
    for k, alts in {"o": ["o", "open"], "h": ["h", "high"], "l": ["l", "low"],
                    "c": ["c", "close"], "v": ["v", "volume"]}.items():
        for a in alts:
            if a in cols:
                out[k] = df[cols[a]].astype("float64").values
                break
    for extra in ("contract", "cum_adjustment", "roll_adjacent", "session_date"):
        if extra in cols:
            out[extra] = df[cols[extra]].values
    out = out.sort_values("dt", kind="mergesort").reset_index(drop=True)
    return out


def aggregate_3m(m1: pd.DataFrame) -> pd.DataFrame:
    """Aggregate END-stamped 1m bars into OPEN-stamped 3m bars (TradingView convention)."""
    open_minute = m1["dt"] - pd.Timedelta(minutes=1)
    t = open_minute.dt.floor("3min")
    g = m1.assign(t=t).groupby("t", sort=True)
    agg = {
        "o": ("o", "first"),
        "h": ("h", "max"),
        "l": ("l", "min"),
        "c": ("c", "last"),
        "v": ("v", "sum"),
        "n1m": ("o", "size"),
    }
    if "contract" in m1.columns:
        agg["contract"] = ("contract", "last")
    if "cum_adjustment" in m1.columns:
        agg["cum_adjustment"] = ("cum_adjustment", "last")
    if "roll_adjacent" in m1.columns:
        agg["roll_adjacent"] = ("roll_adjacent", "max")
    if "session_date" in m1.columns:
        agg["canon_sd"] = ("session_date", "last")
    b = g.agg(**agg).reset_index()
    return b


def add_clock(b: pd.DataFrame) -> pd.DataFrame:
    """Add NY clock fields.  ``t`` is the bar OPEN time (NY, tz-naive)."""
    t = b["t"]
    b["hh"] = t.dt.hour.astype(np.int64)
    b["mm"] = t.dt.minute.astype(np.int64)
    b["mod"] = (b["hh"] * 60 + b["mm"]).astype(np.int64)  # minute-of-day of bar open
    # CME trading/session date: bars opening at/after 18:00 belong to next day's session.
    sd = t.dt.normalize()
    sd = sd.where(b["mod"] < 18 * 60, sd + pd.Timedelta(days=1))
    # prefer the canonical CME trading date (holiday mornings belong to the next trading date)
    b["session_date"] = pd.to_datetime(b["canon_sd"]) if "canon_sd" in b.columns else sd
    b["in_rth"] = (b["mod"] >= 570) & (b["mod"] < 960)
    return b


def to_arrays(b: pd.DataFrame) -> dict:
    """Numpy views used by the numba kernels."""
    in_rth = b["in_rth"].values.astype(np.bool_)
    prev = np.concatenate([[False], in_rth[:-1]])
    new_rth = in_rth & ~prev
    sess = b["session_date"].values.astype("datetime64[D]").astype(np.int64)
    return dict(
        o=b["o"].values.astype(np.float64),
        h=b["h"].values.astype(np.float64),
        l=b["l"].values.astype(np.float64),
        c=b["c"].values.astype(np.float64),
        v=b["v"].values.astype(np.float64),
        hh=b["hh"].values.astype(np.int64),
        mm=b["mm"].values.astype(np.int64),
        mod=b["mod"].values.astype(np.int64),
        in_rth=in_rth,
        new_rth=new_rth,
        sess=sess,
        t=b["t"].values.astype("datetime64[m]").astype(np.int64),
    )
