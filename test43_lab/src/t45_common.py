"""TEST45 shared layer: canonical 1-minute ES/MNQ session panel (data <= 2026-05-27 ONLY), execution clock, costs, stats.

Minute semantics (canonical files are END-stamped, NY-naive): the bar stamped HH:MM covers [HH:MM-1, HH:MM).
  * o of bar 09:31  = first RTH trade  = RTH_OPEN
  * c of bar 16:00  = last trade before 16:00:00 = CASH_REFERENCE_CLOSE
  * o of bar 16:15  = first trade after 16:14:00 = fill price of the LAST CAUSAL EXECUTION (decision on bars <= 16:14)
Execution clock (TEST45): a decision at minute T may use bars end-stamped <= T only and is filled at the OPEN of the bar
end-stamped T+1 (+/- slippage).  Fills must satisfy 09:31 <= fill bar <= 16:15, so the last decision minute is 16:14.
An order decided BEFORE the open without using the open print (e.g. a planned exit) may fill at RTH_OPEN (bar 09:31 open).
Position is LOCKED from the 16:15 fill until the next RTH open; no strategy order exists in that interval.
No bar outside [09:31, 16:15] of the CURRENT session is ever used by a TEST45 feature (no overnight path)."""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments  # noqa: E402

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(SRC, "..")
T45 = os.path.join(ROOT, "out", "t45")
REP = os.path.join(ROOT, "reports", "TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION")
END = pd.Timestamp("2026-05-27")
DATA = {"ES": ("data/canonical_1m_ES.parquet", "2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116"),
        "MNQ": ("data/canonical_1m_MNQ.parquet", "66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2")}
INSTS = ("ES", "MNQ")
PROF = {"ES": instruments.PROFILES["MES"], "MNQ": instruments.PROFILES["MNQ"]}
PV = np.array([PROF[i]["point_value"] for i in INSTS])          # $/pt: MES 5, MNQ 2
TICK = 0.25
TICKV = np.array([PROF[i]["tick_value"] for i in INSTS])
COMM = 0.62
CAPITAL = 150_000.0
M0 = 9 * 60 + 31          # first grid minute (bar end 09:31)
M1 = 16 * 60 + 15         # last grid minute (bar end 16:15)
NG = M1 - M0 + 1          # 405 grid points


def g(hhmm):
    """grid index of bar END-stamped hh:mm"""
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m - M0


CASH_CLOSE_BAR = g("16:00")       # c of this bar
LOCK_FILL_BAR = g("16:15")        # o of this bar
LAST_DECISION_BAR = g("16:14")
OPEN_BAR = g("09:31")             # o of this bar

PERIODS = {"ALL": ("2019-01-01", END), "Y2019": ("2019-01-01", "2019-12-31"), "Y2020": ("2020-01-01", "2020-12-31"),
           "Y2021": ("2021-01-01", "2021-12-31"), "Y2022": ("2022-01-01", "2022-12-31"), "Y2023": ("2023-01-01", "2023-12-31"),
           "Y2024": ("2024-01-01", "2024-12-31"), "Y2025": ("2025-01-01", "2025-12-31"), "Y2026_TO_0527": ("2026-01-01", END),
           "FORMER_HOLDOUT_USED": ("2025-10-01", END)}
# nested outer folds (evolution/fit uses ONLY sessions before the outer block)
OUTER = [("O1_2021", "2021-01-01", "2021-12-31"), ("O2_2022", "2022-01-01", "2022-12-31"), ("O3_2023", "2023-01-01", "2023-12-31"),
         ("O4_2024", "2024-01-01", "2024-12-31"), ("O5_2025_26", "2025-01-01", str(END.date()))]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load1m(inst):
    rel, h = DATA[inst]
    p = os.path.join(ROOT, rel)
    assert sha(p) == h, f"canonical {inst} hash mismatch"
    d = pd.read_parquet(p)
    d = d[d.session_date <= END].reset_index(drop=True)
    assert d.session_date.max() <= END
    return d


def _panel_inst(inst, sessions):
    d = load1m(inst)
    mod = (d.dt.dt.hour * 60 + d.dt.dt.minute).values
    sd = d.session_date.values
    si = pd.Index(sessions).get_indexer(sd)
    n = len(sessions)
    A = {k: np.full((n, NG), np.nan) for k in ("o", "h", "l", "c", "v")}
    m = (mod >= M0) & (mod <= M1) & (si >= 0)
    r, j = si[m], mod[m] - M0
    for k in ("o", "h", "l", "c"):
        A[k][r, j] = d[k].values[m]
    A["v"][r, j] = d.v.values[m].astype(float)
    # session-end mark (accounting only, never a feature): close of last bar <= 17:00 of the session
    last = d.groupby("session_date").tail(1)
    se = pd.Series(last.c.values, index=last.session_date.values).reindex(sessions).values
    sw = d.contract.values[1:] != d.contract.values[:-1]
    sw_sess = set(d.session_date.values[1:][sw])
    roll_in = np.array([s in sw_sess for s in sessions])          # contract switched at the 18:01 bar of this session
    return A, se, roll_in


def fill_price(O, j):
    """open of bar j, else first existing open in (j, j+3]  (conservative: never earlier)."""
    x = O[:, j].copy()
    for k in range(1, 4):
        if j + k < NG:
            x = np.where(np.isnan(x), O[:, j + k], x)
    return x


def build_panel(rebuild=False):
    os.makedirs(T45, exist_ok=True)
    pth = os.path.join(T45, "panel.npz")
    if os.path.exists(pth) and not rebuild:
        z = np.load(pth, allow_pickle=True)
        return {k: z[k] for k in z.files}
    ss = [set(pd.read_parquet(os.path.join(ROOT, DATA[i][0]), columns=["session_date"]).session_date.unique()) for i in INSTS]
    sessions = np.array(sorted(s for s in ss[0] & ss[1] if s <= END.to_datetime64()), dtype="datetime64[ns]")
    out = {"sessions": sessions}
    for k, inst in enumerate(INSTS):
        A, se, roll_in = _panel_inst(inst, sessions)
        for f in A:
            out[f"{inst}_{f}"] = A[f]
        out[f"{inst}_se"] = se; out[f"{inst}_roll_in"] = roll_in
    np.savez_compressed(pth, **out)
    return out


def ffill_row(X):
    """forward-fill along minutes (causal: last known value)"""
    df = pd.DataFrame(X)
    return df.ffill(axis=1).values


class Panel:
    """Session-level causal quantities for one instrument (index s = session)."""

    def __init__(self, P, inst):
        self.inst = inst; self.k = INSTS.index(inst)
        self.sess = pd.DatetimeIndex(P["sessions"])
        self.O, self.H, self.L, self.C, self.V = (P[f"{inst}_{f}"] for f in ("o", "h", "l", "c", "v"))
        self.Cf = ffill_row(self.C)                     # last known close at each minute
        self.se = P[f"{inst}_se"]; self.roll_in = P[f"{inst}_roll_in"]
        n = len(self.sess)
        self.open = fill_price(self.O, OPEN_BAR)       # RTH open (first RTH trade)
        self.cash_close = self.Cf[:, CASH_CLOSE_BAR]
        self.lock = fill_price(self.O, LOCK_FILL_BAR)  # last causal execution fill
        self.lock_ok = ~np.isnan(self.O[:, LOCK_FILL_BAR]) | ~np.isnan(self.O[:, min(LOCK_FILL_BAR, NG - 1)])
        self.full = ~np.isnan(self.C[:, CASH_CLOSE_BAR]) & ~np.isnan(self.O[:, LOCK_FILL_BAR]) & ~np.isnan(self.open)
        # RTH window (09:30-16:15) high/low/close for daily-state features (all known at 16:15)
        Hm = np.nanmax(np.where(np.isnan(self.H), -np.inf, self.H), 1); Lm = np.nanmin(np.where(np.isnan(self.L), np.inf, self.L), 1)
        self.rth_h = np.where(np.isfinite(Hm), Hm, np.nan); self.rth_l = np.where(np.isfinite(Lm), Lm, np.nan)
        self.rth_last = self.Cf[:, LAST_DECISION_BAR]
        prev = lambda x: np.r_[np.nan, x[:-1]]
        self.p_cash = prev(self.cash_close); self.p_lock = prev(self.lock); self.p_h = prev(self.rth_h); self.p_l = prev(self.rth_l)
        self.p_open = prev(self.open)
        tr = np.fmax(self.rth_h, self.p_cash) - np.fmin(self.rth_l, self.p_cash)
        tr = np.where(np.isnan(tr), self.rth_h - self.rth_l, tr)
        atr = pd.Series(tr).rolling(14, min_periods=10).mean().values
        self.atr = prev(atr)                            # ATR14 of RTH true range through the PREVIOUS session
        self.p_range = self.p_h - self.p_l
        self.gap_lock = self.open - self.p_lock
        self.gap_cash = self.open - self.p_cash
        gs = pd.Series(self.gap_lock).rolling(60, min_periods=30).std().values
        self.gap_sigma = prev(gs)
        self.ret_cash_day = self.cash_close - self.p_cash
        self.p_ret = prev(self.cash_close - self.p_cash)
        ma20 = pd.Series(self.cash_close).rolling(20, min_periods=15).mean().values
        self.p_trend20 = prev(self.cash_close - ma20)                 # prior close vs its 20d mean (points)
        rv = pd.Series(tr).rolling(20, min_periods=15).mean()
        self.vol_pct = prev(rv.rolling(250, min_periods=120).rank(pct=True).values)   # ATR20 percentile vs past year
        self.vwap = ffill_row(np.nancumsum(np.nan_to_num((self.H + self.L + self.C) / 3) * np.nan_to_num(self.V), 1)
                              / np.where(np.nancumsum(np.nan_to_num(self.V), 1) > 0, np.nancumsum(np.nan_to_num(self.V), 1), np.nan))
        self.runlow = np.fmin.accumulate(np.where(np.isnan(self.L), np.inf, self.L), 1); self.runlow[np.isinf(self.runlow)] = np.nan
        self.runhigh = np.fmax.accumulate(np.where(np.isnan(self.H), -np.inf, self.H), 1); self.runhigh[np.isinf(self.runhigh)] = np.nan
        self.n = n

    def fill(self, j):
        return fill_price(self.O, j)

    def gap(self, kind="lock", norm="atr"):
        gp = self.gap_lock if kind == "lock" else self.gap_cash
        ref = self.p_lock if kind == "lock" else self.p_cash
        return normalise(gp, norm, self, ref)


def normalise(x, norm, p, ref=None):
    if norm == "atr":
        return x / p.atr
    if norm == "range":
        return x / p.p_range
    if norm == "sigma":
        return x / p.gap_sigma
    if norm == "pct":
        return 100 * x / (ref if ref is not None else p.p_cash)
    if norm == "pts":
        return x
    raise ValueError(norm)


def cost_side(k, slip_ticks=1.0):
    return COMM + slip_ticks * TICKV[k]


def mask_period(sess, per):
    s, e = PERIODS[per]
    return (sess >= pd.Timestamp(s)) & (sess <= pd.Timestamp(e))


def dstats(pnl, sess=None, per=None, prefix=""):
    x = np.asarray(pnl, float)
    if sess is not None and per is not None:
        x = x[mask_period(sess, per)]
    x = np.nan_to_num(x)
    if len(x) == 0:
        return {}
    eq = np.r_[0.0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    top = np.sort(x)[::-1]
    return {f"{prefix}days": len(x), f"{prefix}total": float(x.sum()), f"{prefix}avg": float(x.mean()), f"{prefix}max_dd": mdd,
            f"{prefix}worst": float(x.min()), f"{prefix}best": float(x.max()), f"{prefix}ret_dd": float(x.mean() / mdd) if mdd > 0 else np.nan,
            f"{prefix}ex_top3_avg": float((x.sum() - top[:3].sum()) / len(x)), f"{prefix}active_share": float((x != 0).mean()),
            f"{prefix}sharpe_ann": float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan}


def champion_daily():
    d = pd.read_csv(os.path.join(ROOT, "out", "t44", "daily_CHAMPION_CONTROL_V1.csv"), index_col=0, parse_dates=True)
    return d


def md(path, title, blocks):
    os.makedirs(REP, exist_ok=True)
    lines = [f"# {title}", ""]
    for b in blocks:
        if isinstance(b, pd.DataFrame):
            lines.append(b.to_markdown(floatfmt=".3f") if len(b) else "(empty)")
        else:
            lines.append(str(b))
        lines.append("")
    open(os.path.join(REP, path), "w").write("\n".join(lines) + "\n")


def jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
