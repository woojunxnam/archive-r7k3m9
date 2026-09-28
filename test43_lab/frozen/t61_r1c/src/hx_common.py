"""HIGH-EXPOSURE PROGRAM (TEST55+) shared layer.
Research data <= 2026-05-27 only.  Exposure is a research variable (per-symbol ceiling 24 MES / 24 MNQ, sparse ladders).
Margin (hard constraint) is computed separately from drawdown risk: per-contract IBKR initial margin (user reference values,
t43.instruments) scaled by the contract's RAW price relative to the reference price (constant fraction of notional, causal:
the session's own price).  ATR-dollar risk = previous-session RTH ATR14 x point value.  MES-equivalent risk units =
contracts x ATR$ / ATR$(MES).

LANE GATES (written and hashed BEFORE any TEST55+ candidate economics - hx_gate_spec.json):
  risk measured on the FULL history 2019-07-01 .. 2026-05-27 (includes the 2020 crash and 2022 bear); folds = 2021..2026 outer blocks.
  CORE     : MaxDD <= 15k, worst day >= -3k, ret/DD >= C43 ret/DD, + common items
  GROWTH   : MaxDD <= 30k, worst day >= -6k, incremental avg/day (2021+) >= +$20 over its base, ret/DD >= 0.6 x base ret/DD, + common items
  AGGRESSIVE (report only): MaxDD <= 50k, worst day >= -10k, + common items
  COMMON   : (c1) >= 4/5 outer folds with positive incremental $/day and median > 0; (c2) remove-top3 incremental days > 0;
             (c3) no single year > 50% of positive incremental P&L; (c4) parameter plateau PASS (supplied; +-10/20% continuous, adjacent
             discrete, all neighbours > 0 and >= 60% of base) ; (c5) 4-tick cost stress incremental > 0; (c6) NO margin breach: peak
             overnight initial margin <= 70% of $150k NLV at every lock (hard), intraday <= 90%; (c7) not a V5.3.3 repeat: fail if
             timing value <= 0 AND MaxDD >= $75k (half the account)."""
import datetime
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
from t43 import instruments  # noqa: E402

ROOT = C45.ROOT
HX = os.path.join(ROOT, "out", "HIGH_EXPOSURE_PROGRAM"); os.makedirs(HX, exist_ok=True)
REPX = os.path.join(ROOT, "reports", "HIGH_EXPOSURE_PROGRAM"); os.makedirs(REPX, exist_ok=True)
NLV = 150_000.0
START = pd.Timestamp("2019-07-01"); SPAN21 = pd.Timestamp("2021-01-01")
LADDER = [0, 1, 2, 3, 5, 8, 12, 18, 24]
PROF = {"ES": instruments.PROFILES["MES"], "MNQ": instruments.PROFILES["MNQ"]}
GATE = {"risk_window": "2019-07-01..2026-05-27 (full)", "fold_window": "2021-01-01..2026-05-27 (5 outer blocks)",
        "CORE": {"max_dd": 15000, "worst_day": -3000, "ret_dd_vs_C43": ">= 1.0x"},
        "GROWTH": {"max_dd": 30000, "worst_day": -6000, "min_incr_avg_day_2021": 20.0, "ret_dd_vs_base": ">= 0.6x"},
        "AGGRESSIVE": {"max_dd": 50000, "worst_day": -10000, "report_only": True},
        "COMMON": {"folds_pos_min": 4, "fold_median_pos": True, "remove_top3_pos": True, "max_year_share": 0.5, "plateau": "+-10/20%, >=60% of base",
                   "cost_stress_4tick_pos": True, "max_overnight_margin_frac": 0.70, "max_intraday_margin_frac": 0.90,
                   "v533_repeat": "fail if timing value <= 0 AND MaxDD >= 75000"},
        "margin_bands_reported": [0.25, 0.40, 0.55, 0.70]}


def write_gate_spec():
    p = os.path.join(HX, "hx_gate_spec.json")
    if os.path.exists(p):
        return open(p + ".sha256").read().strip()
    d = {"written_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z", **GATE}
    json.dump(d, open(p, "w"), indent=1)
    h = P.sha(p); open(p + ".sha256", "w").write(h + "\n")
    return h


# ------------------------------------------------------------------------------------------ price / margin / ATR panels
def session_raw_close(inst, sess):
    cache = os.path.join(HX, f"raw_close_{inst}.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache).raw.reindex(sess).values
    d = C45.load1m(inst)
    mod = d.dt.dt.hour * 60 + d.dt.dt.minute
    d = d[(mod >= 571) & (mod <= 975)]
    g = d.groupby("session_date").tail(1)
    s = pd.DataFrame({"raw": (g.c - g.cum_adjustment).values}, index=pd.DatetimeIndex(g.session_date.values))
    s.to_parquet(cache)
    return s.raw.reindex(sess).values


class Book:
    """per-session exposure economics for ES(MES) and MNQ."""

    def __init__(self, mks):
        self.mks = mks
        self.sess = mks["ES"].pn.sess
        self.raw = {k: pd.Series(session_raw_close(k, self.sess)).ffill().bfill().values for k in mks}
        self.m_on = {k: PROF[k]["ibkr_overnight"] * self.raw[k] / PROF[k]["ref_price"] for k in mks}
        self.m_in = {k: PROF[k]["ibkr_intraday"] * self.raw[k] / PROF[k]["ref_price"] for k in mks}
        self.atr_d = {k: np.nan_to_num(mks[k].atr, nan=np.nanmedian(mks[k].atr)) * mks[k].pv for k in mks}
        self.notional = {k: self.raw[k] * mks[k].pv for k in mks}

    def mes_units(self, qE, qN):
        return qE + qN * self.atr_d["MNQ"] / self.atr_d["ES"]


# ------------------------------------------------------------------------------------------ evaluation
def risk(x):
    return P.risk(x)


def lane_eval(name, d_cand, d_base, sess, on_margin_peak, in_margin_peak, timing_value, extra=None):
    """d_cand = candidate portfolio daily $ (incl. base), d_base = its base daily $.  Returns lane classification row."""
    extra = dict(extra or {})
    full = sess >= START; m21 = sess >= SPAN21
    inc = d_cand - d_base
    rc, rb = risk(d_cand[full]), risk(d_base[full])
    fold = {}
    for nm, a, b in C45.OUTER:
        mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b))
        fold[nm] = float(inc[mm].mean())
    act = inc[m21][inc[m21] != 0]; top = np.sort(act)[::-1]
    yr = pd.Series(inc[m21], index=sess[m21]).groupby(sess[m21].year).sum()
    c43 = risk(C45.champion_daily().pnl.reindex(sess).fillna(0.0).values[full])
    o = {"candidate": name, "avg_day_full": rc["avg_day"], "avg_day_2021": float(d_cand[m21].mean()), "max_dd": rc["max_dd"], "worst_day": rc["worst_day"],
         "ret_dd": rc["ret_dd"], "base_avg_day_2021": float(d_base[m21].mean()), "base_ret_dd": rb["ret_dd"], "incr_avg_day_2021": float(inc[m21].mean()),
         **{f"fold_{k}": v for k, v in fold.items()}, "folds_pos": int(sum(v > 0 for v in fold.values())), "fold_median": float(np.median(list(fold.values()))),
         "remove_top3_incr": float(act.sum() - top[:3].sum()) if len(top) >= 3 else np.nan, "remove_top5_incr": float(act.sum() - top[:5].sum()) if len(top) >= 5 else np.nan,
         "max_year_share": float(yr.clip(lower=0).max() / max(yr.clip(lower=0).sum(), 1e-9)), **{f"y{k}": v for k, v in pd.Series(d_cand[full], index=sess[full]).groupby(sess[full].year).mean().items()},
         "pre2023_avg": float(d_cand[full & (sess < pd.Timestamp("2023-01-01"))].mean()), "from2023_avg": float(d_cand[sess >= pd.Timestamp("2023-01-01")].mean()),
         "peak_on_margin_frac": on_margin_peak / NLV, "peak_in_margin_frac": in_margin_peak / NLV, "timing_value_day": timing_value}
    common = {"c1": o["folds_pos"] >= 4 and o["fold_median"] > 0, "c2": bool(o["remove_top3_incr"] > 0), "c3": o["max_year_share"] <= 0.5,
              "c4": bool(extra.pop("plateau_pass", False)), "c5": bool(extra.pop("stress4_pos", False)),
              "c6": o["peak_on_margin_frac"] <= 0.70 and o["peak_in_margin_frac"] <= 0.90,
              "c7": not (timing_value <= 0 and rc["max_dd"] >= 75000)}
    o.update(common)
    cm = all(common.values())
    o["CORE"] = cm and rc["max_dd"] <= 15000 and rc["worst_day"] >= -3000 and rc["ret_dd"] >= c43["ret_dd"]
    o["GROWTH"] = cm and rc["max_dd"] <= 30000 and rc["worst_day"] >= -6000 and o["incr_avg_day_2021"] >= 20 and rc["ret_dd"] >= 0.6 * rb["ret_dd"]
    o["AGGRESSIVE_REPORT"] = cm and rc["max_dd"] <= 50000 and rc["worst_day"] >= -10000
    o["margin_band"] = next((b for b in (0.25, 0.40, 0.55, 0.70) if o["peak_on_margin_frac"] <= b), ">0.70")
    o.update(extra)
    return o


def md(path, title, blocks):
    P.md(path, title, blocks, REPX)


def prereg(test, spec):
    return P.prereg(test, spec)
