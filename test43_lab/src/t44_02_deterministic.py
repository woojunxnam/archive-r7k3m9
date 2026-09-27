"""TEST44 Phases 1-8: deterministic integer allocators on all history through 2026-05-27 (broad predeclared grid only)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t44_alloc as A  # noqa: E402
import t44_common as TC  # noqa: E402

OUT = TC.T44
CAPS = (1, 2, 3, 4)
THETAS = (0.33, 0.5, 0.67)
THETA0 = (0.0, 0.1, 0.2)
FEAS = dict(max_dd=15000.0, worst=-3000.0)   # MODERATE envelope on the whole history


def feasible(o):
    return (o["ALL_max_dd"] <= FEAS["max_dd"] and o["ALL_worst"] >= FEAS["worst"] and o["peak_margin"] <= 0.5
            and all(o.get(f"{f}_avg", -1) > 0 for f in ("F1_2019_2020", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026")))


def main():
    E = A.Engine()
    rows = []
    n = len(E.T)

    def go(family, name, mode, REQ, X, dem, caps, **kw):
        pr = E.priority(kw.pop("rule", "LOW_DD"), dem)
        r = E.run(mode, REQ, X, pr, caps=caps, **kw)
        o, d = E.summary(r)
        o.update(family=family, config=name, caps=f"{caps[0]}/{caps[1]}", mode=mode, feasible=feasible(o))
        rows.append(o)
        return r, d, o
    for cap in CAPS:
        caps = (cap, cap)
        for t0 in THETA0:
            REQ, X, dem = E.requests("D1", theta0=t0)
            go("D1_ONE_CONTRACT", f"D1|off{t0}|max{cap}", 0, REQ, X, dem, caps)
            for th in THETAS:
                REQ, X, dem = E.requests("D2", th, theta0=t0)
                go("D2_TWO_CONTRACT", f"D2|off{t0}|th{th}|max{cap}", 0, REQ, X, dem, caps)
            for S, base, th in ((1, "D1", 0.5), (2, "D2", 0.33), (2, "D2", 0.5), (2, "D2", 0.67)):
                for agg in ("max", "mean"):
                    REQ, X, dem = E.requests(base, th, slots=S, agg=agg, theta0=t0)
                    go("D3_CLUSTER_SLOT", f"D3|off{t0}|slots{S}|{base}|th{th}|{agg}|max{cap}", 0, REQ, X, dem, caps)
            REQ, X, dem = E.requests("D2", 0.5, theta0=t0)
            for lam in (0.0, 0.25, 0.5):
                for mu in (0.0, 1.0):
                    go("D4_INTEGER_TRACKING", f"D4|off{t0}|lam{lam}|mu{mu}|max{cap}", 1, REQ, X, dem, caps, lam=lam, mu=mu)
            for H in (10, 40, 130):
                for K in (1, 2):
                    go("RESIDUAL", f"RES|off{t0}|H{H}|K{K}|max{cap}", 2, REQ, X, dem, caps, H=H, K=K)
        print("cap", cap, "done", len(rows), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/t44_deterministic_grid.csv", index=False)
    # benchmarks with identical metric code
    bench = []
    for tag in ("CHAMPION_CONTROL_V1", "D0_CURRENT_TEST43", "D0b_TEST43_P2"):
        d = pd.read_csv(f"{OUT}/daily_{tag}.csv", index_col=0, parse_dates=True)
        o = {"family": "BENCHMARK", "config": tag}
        for p in ("ALL", "F1_2019_2020", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026", "Y2020", "Y2022", "FORMER_HOLDOUT"):
            o.update(TC.stats(d, p, E.c1))
        o["peak_margin"] = float(d.mu_max.max())
        bench.append(o)
    pd.DataFrame(bench).to_csv(f"{OUT}/t44_benchmarks.csv", index=False)
    # best feasible per family (predeclared rule: max ALL ret/DD, then fewer max contracts)
    best = {}
    for fam, g in df[df.feasible].groupby("family"):
        g = g.assign(maxc=g.caps.str.split("/").str[0].astype(int)).sort_values(["ALL_ret_dd", "maxc"], ascending=[False, True])
        best[fam] = g.iloc[0].config
    json.dump(best, open(f"{OUT}/t44_best_per_family.json", "w"), indent=1)
    pd.set_option("display.width", 260)
    cols = ["family", "config", "ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd", "ALL_excess_vs_mb", "Y2020_avg", "Y2022_avg",
            "FORMER_HOLDOUT_avg", "fills_per_day", "avg_MES", "avg_MNQ", "feasible"]
    print(pd.DataFrame(bench)[[c for c in cols if c in pd.DataFrame(bench)]].round(3).to_string(index=False))
    print(df.sort_values("ALL_ret_dd", ascending=False).groupby("family").head(3)[cols].round(3).to_string(index=False))
    print(best)


if __name__ == "__main__":
    main()
