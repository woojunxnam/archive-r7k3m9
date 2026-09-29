"""Bar container and canonical data loader.

All arrays are aligned to the full 1m series (RTH + ETH). `tradeable` marks bars
whose OPEN time is inside the trading window (bar-end 09:31..16:15 ET) on a
non-holiday day. See EXECUTION_SPEC.md sections 2-3.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import DATASET_SHA256

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_PATH = os.path.join(ROOT, "data", "canonical", "canonical_1m_ES.parquet")

WINDOW_FIRST_END = 9 * 60 + 31   # bar-end minute of first tradeable bar (open 09:30)
WINDOW_LAST_END = 16 * 60 + 15   # bar-end minute of last tradeable bar (open 16:14)


@dataclass
class Bars:
    dt: np.ndarray          # datetime64[ns], bar END, naive ET
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    adj: np.ndarray         # cum_adjustment; raw = price - adj
    contract: np.ndarray    # int codes
    contract_names: list
    day: np.ndarray         # int64 yyyymmdd of bar end
    minute: np.ndarray      # minute of day of bar end
    in_window: np.ndarray   # bool: bar-end in [09:31, 16:15]
    tradeable: np.ndarray   # bool: in_window & not holiday
    holiday_days: set

    def __len__(self):
        return len(self.c)

    @property
    def raw_c(self):
        return self.c - self.adj


def bars_from_frame(df: pd.DataFrame, holiday_filter: bool = True) -> Bars:
    """Build Bars from a frame with columns dt,o,h,l,c[,cum_adjustment,contract]."""
    df = df.reset_index(drop=True)
    dt = pd.to_datetime(df["dt"]).values.astype("datetime64[ns]")
    ts = pd.DatetimeIndex(dt)
    minute = (ts.hour * 60 + ts.minute).values.astype(np.int64)
    day = (ts.year * 10000 + ts.month * 100 + ts.day).values.astype(np.int64)
    in_window = (minute >= WINDOW_FIRST_END) & (minute <= WINDOW_LAST_END)
    adj = df["cum_adjustment"].values.astype(float) if "cum_adjustment" in df else np.zeros(len(df))
    if "contract" in df:
        codes, names = pd.factorize(df["contract"])
        contract, contract_names = codes.astype(np.int64), list(names)
    else:
        contract, contract_names = np.zeros(len(df), dtype=np.int64), ["X"]
    holidays = set()
    if holiday_filter:
        w = pd.DataFrame({"day": day[in_window], "m": minute[in_window]})
        g = w.groupby("day").m.agg(["size", "max"])
        holidays = set(g[(g["size"] <= 211) & (g["max"] <= 13 * 60)].index.tolist())
    hol_mask = np.isin(day, list(holidays)) if holidays else np.zeros(len(df), bool)
    return Bars(dt=dt, o=df["o"].values.astype(float), h=df["h"].values.astype(float),
                l=df["l"].values.astype(float), c=df["c"].values.astype(float), adj=adj,
                contract=contract, contract_names=contract_names, day=day, minute=minute,
                in_window=in_window, tradeable=in_window & ~hol_mask, holiday_days=holidays)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def load_canonical(path: str = CANONICAL_PATH, verify: bool = True, start=None, end=None) -> Bars:
    if verify:
        s = sha256_file(path)
        if s != DATASET_SHA256:
            raise RuntimeError(f"dataset hash mismatch: {s}")
    df = pd.read_parquet(path, columns=["dt", "o", "h", "l", "c", "cum_adjustment", "contract"])
    if start is not None:
        df = df[df.dt >= pd.Timestamp(start)]
    if end is not None:
        df = df[df.dt <= pd.Timestamp(end)]
    return bars_from_frame(df)
