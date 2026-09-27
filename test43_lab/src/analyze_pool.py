"""Candidate pool across all lanes: top-K feasible per lane re-evaluated on DEV+VAL with matched beta,
timing decomposition and turnover bucket.  VAL is reported for filtering only (never optimised).
Usage: python analyze_pool.py OUT.csv DIR [DIR ...]
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import decomp, instruments, lab, v6a, v6lab  # noqa: E402
import optimize_v6_G as G  # noqa: E402

K = int(os.environ.get("POOL_K", "5"))
PER = ("DEV", "F1", "F2", "F3", "VAL", "DV", "PRE23", "P23", "Y2020", "Y2022")
_setup = {}


def eval_cfg(inst, arch, p):
    if arch in ("B", "G"):
        if inst not in _setup:
            _setup[inst] = G.setup(inst, lab.VAL_END)
        b, a = _setup[inst]
        o, res, d = G.evaluate_v6x(inst, b, a, p, PER, lab.VAL_END)
    else:
        o, res, d = v6lab.evaluate(inst, p, periods=PER, keep=True, mb=True)
        b, _ = v6lab.load(inst)
    pv = instruments.PROFILES[G.PROF[inst]]["point_value"]
    dc = decomp.decompose(b, res, pv=pv)
    o["gross_mtm"] = dc["gross_mtm"]; o["beta_at_avg_pos"] = dc["beta_at_avg_pos"]; o["timing"] = dc["timing"]
    days = o.get("DV_days") or 1
    o["fills_per_day"] = o["fills"] / days
    o["friction_per_day"] = o["friction"] / days
    fpd = o["fills_per_day"]
    o["turnover_bucket"] = "VERY_LOW" if fpd < 0.5 else "LOW" if fpd < 2 else "MEDIUM" if fpd < 10 else "HIGH"
    return o


def main(out, dirs):
    rows = []
    for dr in dirs:
        for f in sorted(glob.glob(f"{dr}/*_*_*.csv")):
            d = pd.read_csv(f)
            if d.empty or "feasible" not in d:
                continue
            inst, arch, env = d.inst.iloc[0], str(d.arch.iloc[0]), d.env.iloc[0]
            fe = d[d.feasible == True].sort_values("score", ascending=False).head(K)  # noqa: E712
            lane = os.path.basename(dr)
            for rank, (_, r) in enumerate(fe.iterrows()):
                p = json.loads(r.params)
                o = eval_cfg(inst, arch, p)
                o.update(lane=lane, inst=inst, arch=arch, env=env, rank=rank, trial=int(r.trial), dev_score=r.score,
                         params=r.params)
                rows.append(o)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print("pool", len(df))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
