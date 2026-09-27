"""TEST44 Phases 5, 7, 8, 16: priority rules under a binding shared budget, contract-count frontier summary, stress,
integer leave-one-out and integer attribution for the best deterministic allocators."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t44_alloc as A  # noqa: E402
import t44_common as TC  # noqa: E402
import t44_02_deterministic as DET  # noqa: E402

OUT = TC.T44
RULES = ("EQUAL", "LOW_DD", "HIGH_MB_EXCESS", "INTENSITY", "CLUSTER_DIVERSITY")


def parse(cfg):
    """Rebuild (mode, request kwargs, run kwargs, caps) from a grid config string."""
    p = cfg.split("|")
    kv = {x[:3]: x for x in p}
    cap = int(p[-1].replace("max", ""))
    t0 = float([x for x in p if x.startswith("off")][0][3:])
    if p[0] == "D1":
        return 0, dict(kind="D1", theta0=t0), {}, cap
    if p[0] == "D2":
        th = float([x for x in p if x.startswith("th")][0][2:])
        return 0, dict(kind="D2", theta=th, theta0=t0), {}, cap
    if p[0] == "D3":
        S = int([x for x in p if x.startswith("slots")][0][5:]); base = p[3]; th = float(p[4][2:]); agg = p[5]
        return 0, dict(kind=base, theta=th, slots=S, agg=agg, theta0=t0), {}, cap
    if p[0] == "D4":
        lam = float([x for x in p if x.startswith("lam")][0][3:]); mu = float([x for x in p if x.startswith("mu")][0][2:])
        return 1, dict(kind="D2", theta=0.5, theta0=t0), dict(lam=lam, mu=mu), cap
    H = int([x for x in p if x.startswith("H")][0][1:]); K = int([x for x in p if x.startswith("K")][0][1:])
    return 2, dict(kind="D2", theta=0.5, theta0=t0), dict(H=H, K=K), cap


def main():
    E = A.Engine()
    grid = pd.read_csv(f"{OUT}/t44_deterministic_grid.csv")
    feas = grid[grid.feasible].copy()
    feas["maxc"] = feas.caps.str.split("/").str[0].astype(int)
    best_by_cap = feas.sort_values(["ALL_ret_dd"], ascending=False).groupby("maxc").head(1)
    keys = list(best_by_cap.config)
    simple = feas.sort_values(["ALL_ret_dd", "maxc"], ascending=[False, True]).iloc[0].config
    best2 = feas[feas.maxc == 2].sort_values("ALL_ret_dd", ascending=False).iloc[0].config if (feas.maxc == 2).any() else None
    sel = {"SIMPLE_BEST_FEASIBLE": simple, "BEST_MAX2_FEASIBLE": best2}
    json.dump(sel, open(f"{OUT}/t44_simple_selection.json", "w"), indent=1)
    print(sel)
    # ---- Phase 5 priority rules with a binding shared $ATR budget (75% of caps) and the base budget
    pri = []
    for cfg in {simple, best2} - {None}:
        mode, rq, rk, cap = parse(cfg)
        REQ, X, dem = E.requests(**rq)
        for bf in (1.0, 0.75):
            for rule in RULES:
                r = E.run(mode, REQ, X, E.priority(rule, dem), caps=(cap, cap), budget_frac=bf, **rk)
                o, _ = E.summary(r)
                pri.append({"config": cfg, "budget_frac": bf, "priority": rule, **o})
    pd.DataFrame(pri).to_csv(f"{OUT}/t44_priority_rules.csv", index=False)
    # ---- stress + LOO + attribution for the selected simple allocators
    stress, loo, attr = [], [], []
    for cfg in {simple, best2} - {None}:
        mode, rq, rk, cap = parse(cfg)
        REQ, X, dem = E.requests(**rq)
        pr = E.priority("LOW_DD", dem)
        base_r = E.run(mode, REQ, X, pr, caps=(cap, cap), **rk)
        base, d = E.summary(base_r)
        d.to_csv(f"{OUT}/daily_{cfg.replace('|', '_')}.csv")
        for tag, ex in (("BASE", {}), ("SLIP2", dict(slip_ticks=2)), ("SLIP4", dict(slip_ticks=4)), ("COMM1.00", dict(commission=1.0)),
                        ("TIMING_BRITTLENESS_STRESS", dict(delay=1)), ("MARGINx1.5_INTRADAY", dict(m_intra=1.5)), ("ON_MARGINx2", dict(m_on=2.0))):
            r = E.run(mode, REQ, X, pr, caps=(cap, cap), **rk, **ex)
            o, _ = E.summary(r)
            stress.append({"config": cfg, "test": tag, **o})
        for cid in E.ids:
            ids = [c for c in E.ids if c != cid]
            REQ2, X2, dem2 = E.requests(**rq, ids=ids)
            r = E.run(mode, REQ2, X2, E.priority("LOW_DD", dem2), caps=(cap, cap), **rk)
            o, _ = E.summary(r)
            loo.append({"config": cfg, "removed": cid, **{f"d_{k}": o[k] - base[k] for k in ("ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd",
                                                                                              "ALL_excess_vs_mb", "Y2020_avg", "Y2022_avg", "FORMER_HOLDOUT_avg")}})
        at = E.attribution(base_r, dem, "LOW_DD"); at.insert(0, "config", cfg); attr.append(at)
    pd.DataFrame(stress).to_csv(f"{OUT}/t44_simple_stress.csv", index=False)
    pd.DataFrame(loo).to_csv(f"{OUT}/t44_integer_loo.csv", index=False)
    pd.concat(attr).to_csv(f"{OUT}/t44_integer_attribution.csv", index=False)
    # ---- contract frontier: best per cap (all families), feasible or not, and best feasible per cap
    fr = grid.assign(maxc=grid.caps.str.split("/").str[0].astype(int))
    rows = []
    for cap, g in fr.groupby("maxc"):
        a = g.sort_values("ALL_ret_dd", ascending=False).iloc[0]
        f_ = g[g.feasible].sort_values("ALL_ret_dd", ascending=False)
        rows.append({"max_contracts_per_symbol": cap, "best_any": a.config, "best_any_avg": a.ALL_avg, "best_any_dd": a.ALL_max_dd,
                     "best_any_worst": a.ALL_worst, "best_any_ret_dd": a.ALL_ret_dd, "best_any_Y2020": a.Y2020_avg, "best_any_Y2022": a.Y2022_avg,
                     "best_any_former_holdout": a.FORMER_HOLDOUT_avg, "n_feasible": len(f_),
                     "best_feasible": f_.iloc[0].config if len(f_) else None, "best_feasible_avg": f_.iloc[0].ALL_avg if len(f_) else None,
                     "best_feasible_dd": f_.iloc[0].ALL_max_dd if len(f_) else None, "best_feasible_ret_dd": f_.iloc[0].ALL_ret_dd if len(f_) else None,
                     "best_feasible_excess": f_.iloc[0].ALL_excess_vs_mb if len(f_) else None,
                     "best_feasible_roll12m_pos": f_.iloc[0].ALL_roll12m_pos if len(f_) else None})
    pd.DataFrame(rows).to_csv(f"{OUT}/t44_contract_frontier.csv", index=False)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print(pd.DataFrame(pri)[["config", "budget_frac", "priority", "ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd", "FORMER_HOLDOUT_avg"]].round(3).to_string(index=False))
    print(pd.DataFrame(stress)[["config", "test", "ALL_avg", "ALL_max_dd", "ALL_worst", "peak_margin"]].round(2).to_string(index=False))
    print(pd.DataFrame(loo).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
