"""FACTORY_WF: anchored walk-forward of parameter choice within a family.
For each fold, pick the family member with best IS (MTM P&L / |IS max DD|) and report its OOS result.
Paths come from full-period runs (inventory carries across folds, as in live trading)."""
import os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import factory_lib as fl
from factory_lib import ROOT
from stage56 import temporal_job
from stage1 import INF

FAM = {
    "EXPO": {f"cap{c}": (dict(cap_total=c) if c < 32 else {}) for c in (16, 20, 24, 28, 32)},
    "GOV": dict({f"x{x}": dict(gov="atr_spike", gov_x=x, gov_action="core") for x in (1.2, 1.35, 1.5, 1.65, 1.8)}, off={}),
    "AGE": dict({f"age{a}": dict(state=dict(t=(1, 33, 33), age=a, mult=(1, 1, 1, INF), recovery_exit="all_ind", rec_exit_x=5.0,
                                          recovery_until=1)) for a in (12.0, 13.5, 15.0, 16.5, 18.0)}, off={}),
    "TIERS": dict({f"top{t}": dict(spacing="tiers", tiers=((8, 5.0), (16, 10.0), (t, 20.0))) for t in (20, 22, 24, 26, 28)}, off={}),
}
FOLDS = [("2019-05-01", "2021-12-31", "2022-01-01", "2022-12-31"), ("2019-05-01", "2022-12-31", "2023-01-01", "2023-12-31"),
         ("2019-05-01", "2023-12-31", "2024-01-01", "2024-12-31"), ("2019-05-01", "2024-12-31", "2025-01-01", "2026-05-31")]


def seg_stats(eq, s, t):
    x = eq[(eq.index >= s) & (eq.index <= t)]
    prev = eq[eq.index < s]
    base = prev.iloc[-1] if len(prev) else 150000.0
    v = np.concatenate([[base], x.values])
    dd = (v - np.maximum.accumulate(v)).min()
    return float(v[-1] - base), float(dd)


if __name__ == "__main__":
    jobs = [(f"WF_{f}_{k}", c) for f, mem in FAM.items() for k, c in mem.items()]
    os.makedirs(os.path.join(ROOT, "results", "FACTORY_S5"), exist_ok=True)
    with Pool(4, initializer=fl.init) as p:
        p.map(temporal_job, jobs)
    rows = []
    for f, mem in FAM.items():
        eqs = {k: pd.read_csv(os.path.join(ROOT, "results", "FACTORY_S5", f"WF_{f}_{k}", "daily.csv"), index_col=0, parse_dates=True).equity
               for k in mem}
        for is_s, is_t, oo_s, oo_t in FOLDS:
            sc = {}
            for k, eq in eqs.items():
                pnl, dd = seg_stats(eq, is_s, is_t)
                sc[k] = pnl / max(-dd, 1.0)
            pick = max(sc, key=sc.get)
            oos = {k: seg_stats(eq, oo_s, oo_t) for k, eq in eqs.items()}
            ctrl = "cap32" if f == "EXPO" else "off"
            rows.append(dict(family=f, is_end=is_t, oos=f"{oo_s}..{oo_t}", pick=pick, is_score=sc[pick],
                             oos_pnl=oos[pick][0], oos_dd=oos[pick][1], ctrl=ctrl, ctrl_oos_pnl=oos[ctrl][0], ctrl_oos_dd=oos[ctrl][1],
                             family_median_oos_dd=float(np.median([v[1] for v in oos.values()])),
                             oos_rank_by_dd=int(sorted(oos, key=lambda k: -oos[k][1]).index(pick) + 1), n=len(oos)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(ROOT, "results", "FACTORY_S5", "walkforward.csv"), index=False)
    print(df.round(0).to_string())
