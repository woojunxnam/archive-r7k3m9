"""TEST43-P virtual sleeves: standalone frozen-candidate runs (own virtual ledger) -> per-bar desired exposure.

desired[i] = the sleeve's position after the decision taken at the close of bar i (= pos[i+1]); it is known at the
close of bar i, so a portfolio that trades toward it at the open of bar i+1 has the same timing as the sleeve itself.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from . import bars as B, instruments, lab, v6a, v6lab, v6x

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SHORTLIST = os.path.join(ROOT, "out", "v6", "shortlist.json")
ELIGIBLE = ["MNQ_arch_A_AGG_0", "MNQ_robust_A_MOD_2", "MNQ_r2_C_MOD_1", "MNQ_robust_C_CON_0",
            "ES_robust_A_MOD_1", "ES_r2_F_MOD_2", "ES_r2_A_CON_1", "ES_robust_C_CON_4"]
SHADOW = ["ES_robust_F_AGG_0", "MNQ_arch_E_AGG_0", "ES_r2_G_AGG_0"]
PATHS3 = {"ES": os.path.join(ROOT, "out", "p123", "ES_3m_bars.parquet"), "MNQ": os.path.join(ROOT, "out", "mnq", "MNQ_3m_bars.parquet")}


def candidates():
    return {c["id"]: c for c in json.load(open(SHORTLIST))}


def cand_hash(c):
    return __import__("hashlib").sha256(json.dumps({"id": c["id"], "inst": c["inst"], "arch": c["arch"], "params": c["params"]},
                                                   sort_keys=True).encode()).hexdigest()


def run_sleeve(c, end=lab.VAL_END, **over):
    """Frozen candidate run; returns bars, res (pos/equity/f_qty...), daily table."""
    inst = c["inst"]
    if c["arch"] in ("B", "G"):
        b = pd.read_parquet(PATHS3[inst]); b = b[b.session_date <= end].reset_index(drop=True)
        a = B.to_arrays(b)
        a["roll_day"] = b.roll_adjacent.fillna(False).astype(bool).values
        a["mref"] = (b.o - b.cum_adjustment.astype(float)).values
        p = dict(c["params"]); p.update(over)
        res = v6x.run(a, v6x.make_params(**p))
    else:
        b, f = v6lab.load(inst, end)
        p = v6lab.inst_params(inst); p.update(c["params"]); p.update(over)
        res = v6a.run(b, f, v6a.make_params(**p))
    d = lab.daily(b, res)
    return b, res, d


def desired(res):
    pos = res["pos"].astype(float)
    return np.r_[pos[1:], pos[-1]]
