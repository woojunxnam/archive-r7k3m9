"""Parallel evaluation of V6X configs on DEV+VAL (holdout excluded by truncation)."""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from . import lab, v6x

_B = None
_A = None
BARS = os.path.join(os.path.dirname(__file__), "..", "..", "out", "p123", "ES_3m_bars.parquet")
RESEARCH_DEFAULTS = dict(rollCostPerContract=2 * (0.62 + 1.25))


def _init(end):
    global _B, _A
    b, a = lab.load(BARS)
    if end is not None:
        b, a = lab.truncate(b, a, pd.Timestamp(end))
    _B, _A = b, a


def _one(cfg):
    p = dict(RESEARCH_DEFAULTS)
    p.update({k: v for k, v in cfg.items() if not k.startswith("_")})
    prm = v6x.make_params(**p)
    out, res, d = lab.evaluate(_B, _A, prm, label=cfg.get("_label", ""),
                               periods=cfg.get("_periods", ("DEV", "VAL")))
    for k, v in cfg.items():
        out["p_" + k] = v
    cd = res["counter_dict"]
    out["roll_cost"] = cd["rollCost"]
    return out


def run_grid(cfgs, end=lab.VAL_END, workers=4):
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(end,)) as ex:
        rows = list(ex.map(_one, cfgs, chunksize=max(1, len(cfgs) // (workers * 8))))
    return pd.DataFrame(rows)
