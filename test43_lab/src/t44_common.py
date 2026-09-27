"""TEST44 shared setup: data through 2026-05-27 (former TEST43 holdout is now USED historical data), sleeves, periods.
No data after 2026-05-27 is ever loaded (hard assertion)."""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, instruments, lab, portfolio as PF, sleeves as S, v6lab  # noqa: E402

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(SRC, "..")
T44 = os.path.join(ROOT, "out", "t44")
END = pd.Timestamp("2026-05-27")
OOS_START = pd.Timestamp("2026-05-28")
DATA = {"ES": ("data/canonical_1m_ES.parquet", "2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116"),
        "MNQ": ("data/canonical_1m_MNQ.parquet", "66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2")}
CLUSTER = {"MNQ_arch_A_AGG_0": 1, "MNQ_robust_A_MOD_2": 1, "MNQ_r2_C_MOD_1": 2, "MNQ_robust_C_CON_0": 2,
           "ES_robust_A_MOD_1": 3, "ES_r2_F_MOD_2": 3, "ES_r2_A_CON_1": 3, "ES_robust_C_CON_4": 3}
ELIG = S.ELIGIBLE
SHADOW = S.SHADOW
PERIODS = {"ALL": (None, END), "F1_2019_2020": (None, "2020-12-31"), "F2_2021_2022": ("2021-01-01", "2022-12-31"),
           "F3_2023_2024": ("2023-01-01", "2024-12-31"), "F4_2025_2026": ("2025-01-01", END),
           "Y2020": ("2020-01-01", "2020-12-31"), "Y2022": ("2022-01-01", "2022-12-31"),
           "FORMER_HOLDOUT": ("2025-10-01", END), "ML_OOS_SPAN": ("2021-07-01", END)}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def setup(rebuild=False):
    """Point every loader at bars rebuilt from the hash-verified canonical files, truncated at END."""
    os.makedirs(f"{T44}/bars", exist_ok=True)
    for inst, (rel, e) in DATA.items():
        assert sha(os.path.join(ROOT, rel)) == e, f"canonical {inst} hash mismatch"
        pth = f"{T44}/bars/{inst}_3m.parquet"
        if rebuild or not os.path.exists(pth):
            m1 = B.normalise_1m(pd.read_parquet(os.path.join(ROOT, rel)))
            bb = B.add_clock(B.aggregate_3m(m1))
            if "cum_adjustment" in bb.columns:
                bb["raw_o"] = bb["o"] - bb["cum_adjustment"].astype(float)
            bb = bb[bb.session_date <= END].reset_index(drop=True)
            bb.to_parquet(pth)
        v6lab.BARS[inst] = pth; S.PATHS3[inst] = pth
    v6lab._S.clear(); v6lab._C1.clear()
    PF.PDIR = f"{T44}/sleeves"
    return True


def pslice(d, per):
    s, e = PERIODS[per]
    x = d if s is None else d[d.index >= pd.Timestamp(s)]
    return x[x.index <= pd.Timestamp(e)]


def stats(d, per, c1=None):
    x = pslice(d, per)
    if len(x) == 0:
        return {}
    pnl = x.pnl.values
    eq = np.r_[0.0, np.cumsum(pnl)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    avg = float(pnl.mean()); top = np.sort(pnl)[::-1]
    r = {f"{per}_days": len(x), f"{per}_total": float(pnl.sum()), f"{per}_avg": avg, f"{per}_max_dd": mdd,
         f"{per}_worst": float(pnl.min()), f"{per}_best": float(pnl.max()), f"{per}_ret_dd": avg / mdd if mdd > 0 else np.nan,
         f"{per}_ex_top3": float((pnl.sum() - top[:3].sum()) / len(x)), f"{per}_pos_share": float((pnl > 0).mean())}
    if c1 is not None and "pES" in x:
        mb = float((x.pES.mean() * c1["ES"].reindex(x.index).fillna(0) + x.pMNQ.mean() * c1["MNQ"].reindex(x.index).fillna(0)).mean())
        r[f"{per}_mb_avg"] = mb; r[f"{per}_excess_vs_mb"] = avg - mb
    for w, k in (("3m", 63), ("6m", 126), ("12m", 252)):
        rr = pd.Series(pnl).rolling(k).sum().dropna()
        r[f"{per}_roll{w}_pos"] = float((rr > 0).mean()) if len(rr) else np.nan
        r[f"{per}_roll{w}_min"] = float(rr.min()) if len(rr) else np.nan
    return r


def const1():
    return {i: v6lab.const1_daily(i, END).pnl for i in ("ES", "MNQ")}
