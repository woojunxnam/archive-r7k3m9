"""V6 research harness (DEV+VAL only; holdout is excluded by truncation)."""
from __future__ import annotations
import os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from . import features, instruments, lab, v6a

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "out")
BARS = {"ES": os.path.join(ROOT, "p123", "ES_3m_bars.parquet"), "MNQ": os.path.join(ROOT, "mnq", "MNQ_3m_bars.parquet")}
PROF = {"ES": "MES", "MNQ": "MNQ"}
PERIODS = {
    "DEV": lab.SPLITS["DEV"], "VAL": lab.SPLITS["VAL"], "DV": (None, lab.VAL_END),
    "PRE23": (None, pd.Timestamp("2022-12-31")), "P23": (pd.Timestamp("2023-01-01"), lab.VAL_END),
    "Y2020": (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31")),
    "Y2022": (pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31")),
}
_S = {}


def inst_params(inst):
    p = instruments.PROFILES[PROF[inst]]
    return dict(pointValue=p["point_value"], mIntraFrac=instruments.margin_frac(p, "intraday"),
                mOnFrac=instruments.margin_frac(p, "overnight"),
                rollCost=2 * (p["commission_side"] + p["tick_value"]), commission=p["commission_side"])


def load(inst, end=lab.VAL_END):
    key = (inst, str(end))
    if key not in _S:
        b = pd.read_parquet(BARS[inst])
        if end is not None:
            b = b[b.session_date <= end].reset_index(drop=True)
        f = features.build(b, instruments.PROFILES[PROF[inst]]["point_value"])
        _S[key] = (b, f)
    return _S[key]


def daily(b, r):
    return lab.daily(b, {"equity": r["equity"], "pos": r["pos"]})


def evaluate(inst, cfg, end=lab.VAL_END, periods=("DEV", "VAL", "DV", "PRE23", "P23", "Y2020", "Y2022"), keep=False):
    b, f = load(inst, end)
    p = inst_params(inst); p.update({k: v for k, v in cfg.items() if not k.startswith("_")})
    r = v6a.run(b, f, v6a.make_params(**p))
    d = daily(b, r)
    out = {"inst": inst, "label": cfg.get("_label", "")}
    for per in periods:
        s, e = PERIODS[per]
        st = lab.period_stats(d, s, e)
        for k in ("days", "total", "avg_daily", "median", "pos_pct", "worst_day", "max_dd", "avg_mes", "avg_on_mes",
                  "max_mes", "avg_ex_top5", "ret_dd"):
            out[f"{per}_{k}"] = st.get(k)
        out[f"{per}_env"] = lab.envelope(st) if st else None
    # IBKR-style margin check: intraday frac in RTH, overnight frac outside
    rawpx = (b.c - b.cum_adjustment.astype(float)).values
    frac = np.where(b.in_rth.values, p["mIntraFrac"], p["mOnFrac"])
    req = r["pos"] * rawpx * p["pointValue"] * frac
    eq = r["equity"]
    util = np.where(eq > 0, req / np.maximum(eq, 1.0), np.where(req > 0, np.inf, 0))
    out["peak_margin_util"] = float(util.max()); out["peak_margin_req"] = float(req.max())
    out["margin_breach"] = bool(util.max() > 1.0); out["min_equity"] = float(eq.min())
    sides = float(np.abs(r["f_qty"]).sum())
    out["contract_sides"] = sides; out["fills"] = int(len(r["f_qty"]))
    out["friction"] = sides * (p["commission"] + 0.25 * p["pointValue"])
    for k, v in cfg.items():
        if not k.startswith("_"):
            out["p_" + k] = v
    if keep:
        return out, r, d
    return out


def _init(inst, end):
    load(inst, end)


def _one(args):
    inst, cfg, end = args
    try:
        return evaluate(inst, cfg, end)
    except Exception as e:  # noqa: BLE001
        return {"inst": inst, "label": cfg.get("_label", ""), "error": repr(e)}


def run_many(inst, cfgs, end=lab.VAL_END, workers=4):
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(inst, end)) as ex:
        rows = list(ex.map(_one, [(inst, c, end) for c in cfgs], chunksize=max(1, len(cfgs) // (workers * 6))))
    return pd.DataFrame(rows)
