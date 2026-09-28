"""TEST46 shared layer.  Research data <= 2026-05-27 only (canonical ES / MNQ 1m, hash-verified via t45_common).
Legacy ledgers: ONLY sanitized files ending `_TO_20260527.csv` may be read, and any timestamp > 2026-05-27 aborts (fail closed).
5m RTH bars are TradingView-style: open-stamped, 09:30 .. 16:10 (session 0930-1615), built from END-stamped 1m bars."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

SRC = C45.SRC
ROOT = C45.ROOT
T46 = os.path.join(ROOT, "out", "t46")
REP = os.path.join(ROOT, "reports", "TEST46_ES_NQ_LONG_ALPHA_EVOLUTION")
LEDGER_DIR = os.path.join(ROOT, "data_legacy")
END = pd.Timestamp("2026-05-27")
CUTOFF = "2026-05-27"
TEST46_NEW_OOS_START = "2026-09-28"


class ResearchInputViolation(RuntimeError):
    pass


def load_ledger(name):
    """fail-closed guard for legacy ledgers."""
    fn = f"{name}_TO_20260527.csv"
    p = os.path.join(LEDGER_DIR, fn)
    if not fn.endswith("_TO_20260527.csv") or not os.path.exists(p):
        raise ResearchInputViolation(f"research ledger must be a sanitized *_TO_20260527.csv file: {fn}")
    d = pd.read_csv(p)
    ts = pd.to_datetime(d["Date and time"])
    if (ts > pd.Timestamp(CUTOFF) + pd.Timedelta(hours=23, minutes=59)).any():
        raise ResearchInputViolation(f"{fn} contains a timestamp after {CUTOFF} - STOP")
    ent = d[d.Type.str.startswith("Entry")].set_index("Trade number")
    ex = d[d.Type.str.startswith("Exit")].set_index("Trade number")
    t = pd.DataFrame({"entry_time": pd.to_datetime(ent["Date and time"]), "entry_px": ent["Price USD"].astype(float),
                      "exit_time": pd.to_datetime(ex["Date and time"]).reindex(ent.index), "exit_px": ex["Price USD"].reindex(ent.index).astype(float),
                      "exit_reason": ex["Signal"].reindex(ent.index), "net": ent["Net PnL USD"].astype(float), "signal": ent["Signal"]})
    return t.sort_values("entry_time").reset_index()


def bars5(inst):
    """TradingView-style 5m RTH bars (open-stamped 09:30..16:10) with adjusted and raw OHLC + volume."""
    cache = os.path.join(T46, f"bars5_{inst}.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    d = C45.load1m(inst)
    mod = d.dt.dt.hour * 60 + d.dt.dt.minute
    d = d[(mod >= 571) & (mod <= 975)].copy()                       # 1m bars ending 09:31..16:15
    start = d.dt - pd.Timedelta(minutes=1)
    d["t"] = start.dt.floor("5min")
    d["raw_c"] = d.c - d.cum_adjustment
    g = d.groupby("t")
    b = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "v": g.v.sum(),
                      "adj": g.cum_adjustment.last(), "sd": g.session_date.last(), "n1": g.o.size()})
    b = b.reset_index()
    b["raw_o"] = b.o - b.adj; b["raw_c"] = b.c - b.adj
    b["date"] = b.t.dt.normalize()
    b = b[b.sd <= END].reset_index(drop=True)
    os.makedirs(T46, exist_ok=True)
    b.to_parquet(cache)
    return b


def rma(x, n):
    out = np.full(len(x), np.nan); a = np.nan
    for i, v in enumerate(x):
        if np.isnan(v):
            out[i] = a; continue
        a = v if np.isnan(a) else (a * (n - 1) + v) / n
        out[i] = a
    return out


def pine_atr(h, l, c, n=14):
    """ta.atr: RMA of true range, first value = SMA of first n TRs (TradingView)."""
    pc = np.r_[np.nan, c[:-1]]
    tr = np.where(np.isnan(pc), h - l, np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc))))
    out = np.full(len(tr), np.nan)
    if len(tr) >= n:
        out[n - 1] = tr[:n].mean()
        for i in range(n, len(tr)):
            out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def pine_ema(x, n):
    a = 2.0 / (n + 1); out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1] = np.mean(x[:n])
        for i in range(n, len(x)):
            out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


def md(path, title, blocks):
    os.makedirs(REP, exist_ok=True)
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b))
        lines.append("")
    open(os.path.join(REP, path), "w").write("\n".join(lines) + "\n")
