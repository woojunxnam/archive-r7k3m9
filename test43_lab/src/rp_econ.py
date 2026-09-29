"""shared stitched-economics helpers for INDEX_ML_GA_RECLAMATION_V1."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t96_common as C  # noqa: E402

FOLDS = {"O1": (2021, 2021), "O2": (2022, 2022), "O3": (2023, 2023), "O4": (2024, 2024), "O5": (2025, 2026)}
TRAIN_END = {"O1": 2020, "O2": 2021, "O3": 2022, "O4": 2023, "O5": 2024}
_C = {}


def ctx():
    if not _C:
        mc = C.main_ctx(); I = mc["Is"]["MNQ"]; sess = pd.DatetimeIndex(I.sess)
        win = np.asarray(I.full & (sess >= "2021-01-01") & (sess <= "2026-05-27"))
        dkey = np.asarray(sess.values, "datetime64[D]").astype(np.int64)
        _C.update(main=mc["main"], sess=sess, win=win, dkey=dkey, pos={d: k for k, d in enumerate(dkey)}, occ=mc["occ"], Is=mc["Is"])
    return _C


def daily(dates, usd):
    c = ctx(); d = np.zeros(len(c["sess"]))
    idx = np.array([c["pos"].get(int(x), -1) for x in dates]); ok = idx >= 0
    np.add.at(d, idx[ok], np.asarray(usd)[ok]); return d


def risk(x):
    cum = np.cumsum(x); dd = np.maximum.accumulate(np.r_[0, cum])[1:] - cum
    return {"avg_day": float(x.mean()), "max_dd": float(dd.max()), "worst_day": float(x.min()), "ret_dd": float(x.mean() / dd.max()) if dd.max() > 0 else np.inf}


def metrics(dates, usd, usd4, n_pop=None):
    c = ctx(); d = daily(dates, usd)[c["win"]]; d4 = daily(dates, usd4)[c["win"]]; yrs = c["sess"][c["win"]].year
    r = risk(d); fold = {k: float(d[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in FOLDS.items()}
    top = np.sort(d)[::-1]; mw = c["main"][c["win"]]
    rm = risk(mw); rc = risk(mw + d)
    return {"avg_day": r["avg_day"], "trades": int(len(usd)), "usd_per_trade": float(np.mean(usd)) if len(usd) else np.nan, "slip4_avg_day": float(d4.mean()),
            "y2022": float(d[yrs == 2022].sum()), "folds_pos": int(sum(v > 0 for v in fold.values())), "worst_fold": float(min(fold.values())),
            **{f"fold_{k}": v for k, v in fold.items()}, "max_dd": r["max_dd"], "worst_day": r["worst_day"], "remove_top3": float(d.sum() - top[:3].sum()),
            "corr_main": float(np.corrcoef(d, mw)[0, 1]) if d.std() > 0 else 0.0, "coverage": float(len(usd) / n_pop) if n_pop else np.nan,
            "main_avg_day": rm["avg_day"], "main_max_dd": rm["max_dd"], "main_worst": rm["worst_day"], "main_ret_dd": rm["ret_dd"],
            "comb_avg_day": rc["avg_day"], "comb_max_dd": rc["max_dd"], "comb_worst": rc["worst_day"], "comb_ret_dd": rc["ret_dd"]}


def tier_b(m):
    return bool(m["avg_day"] > 0 and m["slip4_avg_day"] > 0 and m["folds_pos"] >= 3 and m["remove_top3"] > 0 and m["worst_fold"] >= -2 * abs(m["avg_day"])
                and m["trades"] >= 150 and (m["coverage"] != m["coverage"] or m["coverage"] >= 0.10))
