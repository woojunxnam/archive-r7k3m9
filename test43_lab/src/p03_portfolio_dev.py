"""TEST43-P Phases 5-16 on DEV only: risk normalisation, P0-P3, risk frontiers, leave-one-out, candidate-count
frontier, 2020/2022 stress, shared margin, robustness.  Writes out/p/*.csv and out/p/p_dev_spec.json (input to the
pre-VAL freeze).  VAL is NOT evaluated here.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments, lab, portfolio as PF, sleeves as S, v6lab  # noqa: E402
import p02_fingerprint as FP  # noqa: E402

OUT = PF.PDIR
DEV_END = lab.DEV_END
ENV = {"CONSERVATIVE": lab.ENVELOPES["CONSERVATIVE"], "MODERATE": lab.ENVELOPES["MODERATE"],
       "AGGRESSIVE": lab.ENVELOPES["AGGRESSIVE"]}
PERS = {"DEV": (None, DEV_END), "F1": (None, "2020-12-31"), "F2": ("2021-01-01", "2022-12-31"),
        "F3": ("2023-01-01", "2024-12-31"), "PRE23": (None, "2022-12-31"), "P23": ("2023-01-01", "2024-12-31"),
        "Y2020": ("2020-01-01", "2020-12-31"), "Y2022": ("2022-01-01", "2022-12-31"), "VAL": ("2025-01-01", "2025-09-30")}
L_GRID = np.round(np.geomspace(100, 12000, 60), 1)
TILT_ALPHAS = (0.25, 0.5)


# ------------------------------------------------------------------------------------ helpers
def load_daily():
    D = pd.read_csv(f"{OUT}/p03_daily_pnl_all_candidates_DV.csv", index_col=0, parse_dates=True)
    return D


def sigma_dev(D):
    return D[D.index <= DEV_END].std()


def c1(inst, end):
    return v6lab.const1_daily(inst, end).pnl


def pstats(d, per, end):
    s, e = PERS[per]
    x = d if s is None else d[d.index >= s]
    x = x if e is None else x[x.index <= pd.Timestamp(e)]
    if len(x) == 0:
        return {}
    eq = x.pnl.cumsum(); mdd = float((eq.cummax() - eq).max()); mdd = max(mdd, 0.0)
    avg = float(x.pnl.mean())
    mb = float((x.pES.mean() * c1("ES", end).reindex(x.index).fillna(0) + x.pMNQ.mean() * c1("MNQ", end).reindex(x.index).fillna(0)).mean())
    ps = x.pnl.sort_values(ascending=False)
    r = {f"{per}_days": len(x), f"{per}_total": float(x.pnl.sum()), f"{per}_avg": avg, f"{per}_median": float(x.pnl.median()),
         f"{per}_max_dd": mdd, f"{per}_worst": float(x.pnl.min()), f"{per}_ret_dd": avg / mdd if mdd > 0 else np.nan,
         f"{per}_mb_avg": mb, f"{per}_excess_vs_mb": avg - mb, f"{per}_pos_share": float((x.pnl > 0).mean()),
         f"{per}_avg_ex_top1": (x.pnl.sum() - ps.iloc[:1].sum()) / len(x), f"{per}_avg_ex_top3": (x.pnl.sum() - ps.iloc[:3].sum()) / len(x),
         f"{per}_avg_ex_top5": (x.pnl.sum() - ps.iloc[:5].sum()) / len(x),
         f"{per}_top1_share": float(ps.iloc[0] / x.pnl.sum()) if x.pnl.sum() > 0 else np.nan,
         f"{per}_mu_avg": float(x.mu_avg.mean()), f"{per}_mu_peak": float(x.mu_max.max()),
         f"{per}_mu_on_avg": float(x.mu_on_avg.mean()), f"{per}_mu_on_peak": float(x.mu_on_max.max()),
         f"{per}_atr_avg": float(x.atr_avg.mean()), f"{per}_atr_peak": float(x.atr_max.max()),
         f"{per}_avg_ES": float(x.pES.mean()), f"{per}_avg_MNQ": float(x.pMNQ.mean())}
    for w, k in (("3m", 63), ("6m", 126), ("12m", 252)):
        rr = x.pnl.rolling(k).sum().dropna()
        r[f"{per}_roll{w}_pos_share"] = float((rr > 0).mean()) if len(rr) else np.nan
        r[f"{per}_roll{w}_min"] = float(rr.min()) if len(rr) else np.nan
    r[f"{per}_worst20_sessions_sum"] = float(x.pnl.rolling(20).sum().min()) if len(x) >= 20 else np.nan
    return r


def env_of(r, per="DEV"):
    for name in ("CONSERVATIVE", "MODERATE", "AGGRESSIVE"):
        dd, w = lab.ENVELOPES[name]
        if r.get(f"{per}_max_dd", 1e18) <= dd and r.get(f"{per}_worst", -1e18) >= w:
            return name
    return "EXPLORATORY"


def gov_for(env, extra=None):
    dd, w = ENV[env]
    g = {"env_dd": dd, "day_stop": 0.8 * abs(w)}
    g.update(extra or {})
    return g


def weights(budgets, sig, L):
    return {cid: b * L / sig[cid] for cid, b in budgets.items() if b > 0}


def run_port(bk, budgets, sig, L, env, extra=None, tilt=None, end=DEV_END, pers=("DEV",)):
    w = weights(budgets, sig, L)
    r = bk.run(w, gov=gov_for(env, extra), weight_bars=tilt)
    d = bk.daily(r)
    d = d[d.index <= pd.Timestamp(end)]
    o = {"L": L}
    for p in pers:
        o.update(pstats(d, p, end))
    o["fills_per_day"] = float(r["fills"].sum() / max(1, len(d))); o["sides"] = float(r["sides"].sum())
    o["margin_breach"] = bool((d.mu_max > 1.0).any())
    o["env"] = env_of(o, pers[0])
    return o, d, r


def calibrate(bk, budgets, sig, env, tilt=None):
    """Largest L on the DEV grid with MaxDD <= 90% of the envelope DD, worst day >= 90% of the floor, no breach."""
    dd, w = ENV[env]
    best = None
    lo, hi = 0, len(L_GRID) - 1
    ok = lambda o: o.get("DEV_max_dd", 1e18) <= 0.9 * dd and o.get("DEV_worst", -1e18) >= 0.9 * w and not o["margin_breach"]  # noqa: E731
    # monotone-ish: binary search then local scan
    while lo <= hi:
        mid = (lo + hi) // 2
        o, _, _ = run_port(bk, budgets, sig, L_GRID[mid], env, tilt=tilt)
        if ok(o):
            best = mid; lo = mid + 1
        else:
            hi = mid - 1
    if best is None:
        return None
    for j in range(best + 1, min(best + 4, len(L_GRID))):   # guard against non-monotone steps
        o, _, _ = run_port(bk, budgets, sig, L_GRID[j], env, tilt=tilt)
        if ok(o):
            best = j
    return float(L_GRID[best])


# ------------------------------------------------------------------------------------ regime tilt (causal)
def regime_tilt(bk, ids, budgets, alpha, D):
    """Per-session multiplicative tilt from an EXPANDING (strictly prior sessions) regime-conditional estimate,
    shrunk by its own t-statistic; cells = trend tier (BEAR/NEUTRAL/BULL) x vol (HIVOL / not).  Renormalised so the
    total risk budget is unchanged.  No tilt before 250 prior sessions or with < 20 sessions in the cell."""
    regs = {i: FP.regimes(i) for i in ("ES", "MNQ")}
    sd = pd.DatetimeIndex(sorted(set(bk.T.sd.values)))
    tilt = pd.DataFrame(1.0, index=sd, columns=ids)
    for cid in ids:
        inst = bk.inst[cid]
        g = regs[inst].reindex(sd)
        cell = (g.tierlab.fillna("NEUTRAL") + "_" + np.where(g.vol == "HIVOL", "HV", "NV")).values
        p = D[cid].reindex(sd).fillna(0.0).values
        hist = {}
        allv = []
        for j in range(len(sd)):
            if len(allv) >= 250:
                v = hist.get(cell[j], [])
                if len(v) >= 20:
                    a = np.asarray(allv); vv = np.asarray(v)
                    diff = vv.mean() - a.mean()
                    t = diff / (vv.std(ddof=1) / np.sqrt(len(vv)))
                    tilt.iat[j, tilt.columns.get_loc(cid)] = 1.0 + alpha * float(np.clip(t / 2.0, -1, 1))
            hist.setdefault(cell[j], []).append(p[j]); allv.append(p[j])
    b = pd.Series(budgets)[ids]
    norm = (tilt * b).sum(1) / b.sum()
    tilt = tilt.div(norm, axis=0)
    sess_map = pd.Series(np.arange(len(sd)), index=sd)
    ix = sess_map.reindex(pd.DatetimeIndex(bk.T.sd.values)).values
    return {cid: tilt[cid].values[ix] for cid in ids}, tilt


# ------------------------------------------------------------------------------------ main
def main():
    C = S.candidates()
    D = load_daily()
    sig = sigma_dev(D)
    fp = pd.read_csv(f"{OUT}/p03_fingerprint_DEV.csv").set_index("id")
    cl = pd.read_csv(f"{OUT}/p05_clusters_DEV.csv"); cl = cl[cl.cut_distance == 0.5].set_index("id").cluster
    E = S.ELIGIBLE
    # ---- DEV fold matched-beta excess (stability) and cost robustness (SLIP4 on DEV)
    stab = []
    for cid in E:
        c = C[cid]
        _, _, d = S.run_sleeve(c, end=DEV_END)
        ex = []
        for per in ("F1", "F2", "F3"):
            st = lab.period_stats(d, *v6lab.PERIODS[per])
            ex.append(st["avg_daily"] - v6lab.matched_beta(c["inst"], d, per, DEV_END)["mb_avg"])
        _, _, d4 = S.run_sleeve(c, end=DEV_END, **({"slipTicks": 4} if c["arch"] not in ("B", "G") else {"slippageTicks": 4}))
        stab.append({"id": cid, "cluster": int(cl[cid]), "F1_excess": ex[0], "F2_excess": ex[1], "F3_excess": ex[2],
                     "min_fold_excess": min(ex), "slip4_retention": d4.pnl.mean() / d.pnl.mean(),
                     "ret_dd": fp.loc[cid, "ret_dd"], "sigma_daily_dev": sig[cid],
                     "avg_contracts": fp.loc[cid, "avg_contracts"]})
    stab = pd.DataFrame(stab)
    stab["p2_score"] = stab.min_fold_excess
    stab = stab.sort_values(["cluster", "p2_score", "ret_dd"], ascending=[True, False, False])
    stab.to_csv(f"{OUT}/p06_sleeve_stability_and_risk_units_DEV.csv", index=False)
    # ---- risk normalisation table (Phase 5)
    rn = []
    for cid in S.ELIGIBLE + S.SHADOW:
        c = C[cid]; inst = c["inst"]; prof = instruments.PROFILES[v6lab.PROF[inst]]
        s = pd.read_parquet(f"{OUT}/sleeve_{cid}.parquet"); s = s[s.sd <= DEV_END]
        b, f = v6lab.load(inst, DEV_END)
        raw = (b.c - b.cum_adjustment.astype(float)).values
        atrD = np.nan_to_num(f["d_ATR20"])
        pos = s.pos.values
        rn.append({"id": cid, "inst": inst, "sigma_daily_pnl_dev": sig[cid],
                   "avg_atr_dollar_exposure": float((pos * prof["point_value"] * atrD).mean()),
                   "avg_notional": float((pos * raw * prof["point_value"]).mean()),
                   "avg_intraday_margin": float((pos * raw * prof["point_value"] * instruments.margin_frac(prof, "intraday"))[b.in_rth.values].mean()),
                   "avg_overnight_margin": float((pos * raw * prof["point_value"] * instruments.margin_frac(prof, "overnight"))[~b.in_rth.values].mean()),
                   "contracts_per_risk_unit_$1000_daily_vol": 1000.0 / sig[cid]})
    pd.DataFrame(rn).to_csv(f"{OUT}/p06_risk_normalisation_DEV.csv", index=False)
    # ---- portfolio definitions
    clusters = sorted(stab.cluster.unique())
    reps = [stab[stab.cluster == k].iloc[0].id for k in clusters]
    P = {}
    P["P0_FULL_UNIVERSE_EQUAL_RISK"] = {cid: 1.0 / len(E) for cid in E}
    P["P1_CLUSTER_EQUAL_RISK"] = {}
    for k in clusters:
        mem = list(stab[stab.cluster == k].id)
        for cid in mem:
            P["P1_CLUSTER_EQUAL_RISK"][cid] = 1.0 / len(clusters) / len(mem)
    P["P2_STATIC_DIVERSIFIED"] = {cid: 1.0 / len(reps) for cid in reps}
    # candidate-count frontier order: round robin across clusters (best-first within cluster)
    order = []
    ranked = {k: list(stab[stab.cluster == k].id) for k in clusters}
    kord = sorted(clusters, key=lambda k: -stab[stab.cluster == k].p2_score.max())
    while any(ranked.values()):
        for k in kord:
            if ranked[k]:
                order.append(ranked[k].pop(0))
    bk = PF.Book(DEV_END, E)
    rows, dailies, Ls = [], {}, {}
    # tilt arrays for P3 (causal expanding estimates)
    tilts = {}
    for a in TILT_ALPHAS:
        tilts[a], tdf = regime_tilt(bk, reps, P["P2_STATIC_DIVERSIFIED"], a, D)
        tdf.to_csv(f"{OUT}/p10_regime_tilt_alpha{a}_DEV.csv")
    defs = [(n, bud, None) for n, bud in P.items()] + [(f"P3_REGIME_ADAPTIVE_{int(a*100)}", P["P2_STATIC_DIVERSIFIED"], a) for a in TILT_ALPHAS]
    for name, bud, a in defs:
        for env in ENV:
            L = calibrate(bk, bud, sig, env, tilt=tilts.get(a))
            Ls[(name, env)] = L
            if L is None:
                rows.append({"portfolio": name, "risk_env": env, "L": None}); continue
            o, d, r = run_port(bk, bud, sig, L, env, tilt=tilts.get(a), pers=tuple(k for k in PERS if k != "VAL"))
            rows.append({"portfolio": name, "risk_env": env, "members": "+".join(bud), **o})
            dailies[(name, env)] = d
            print(name, env, "L", L, "avg", round(o["DEV_avg"], 1), "dd", round(o["DEV_max_dd"]), flush=True)
    front = pd.DataFrame(rows)
    front.to_csv(f"{OUT}/p07_p12_portfolios_frontiers_DEV.csv", index=False)
    # ---- candidate count frontier (MODERATE)
    cnt = []
    for k in range(1, len(order) + 1):
        bud = {cid: 1.0 / k for cid in order[:k]}
        L = calibrate(bk, bud, sig, "MODERATE")
        if L is None:
            continue
        o, d, _ = run_port(bk, bud, sig, L, "MODERATE", pers=("DEV", "Y2020", "Y2022"))
        ncl = len({int(cl[c]) for c in order[:k]})
        cnt.append({"n_candidates": k, "members": "+".join(order[:k]), "effective_clusters": ncl, **o})
    pd.DataFrame(cnt).to_csv(f"{OUT}/p11_candidate_count_frontier_DEV.csv", index=False)
    # ---- leave-one-out (MODERATE)
    loo = []
    for name, bud, a in defs:
        L = Ls[(name, "MODERATE")]
        if L is None:
            continue
        base, _, _ = run_port(bk, bud, sig, L, "MODERATE", tilt=tilts.get(a), pers=("DEV", "Y2020", "Y2022"))
        for cid in bud:
            if len(bud) == 1:
                continue
            b2 = {x: v for x, v in bud.items() if x != cid}
            s_ = sum(b2.values()); b2 = {x: v / s_ for x, v in b2.items()}
            tl = None
            if a is not None:
                tl = regime_tilt(bk, list(b2), b2, a, D)[0]
            o, _, _ = run_port(bk, b2, sig, L, "MODERATE", tilt=tl, pers=("DEV", "Y2020", "Y2022"))
            r = {"portfolio": name, "removed": cid}
            for k in ("DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "DEV_excess_vs_mb", "Y2020_avg", "Y2022_avg",
                      "DEV_roll3m_min", "DEV_roll6m_min", "DEV_roll12m_min", "DEV_mu_peak"):
                r[f"d_{k}"] = o.get(k, np.nan) - base.get(k, np.nan)
            loo.append(r)
    pd.DataFrame(loo).to_csv(f"{OUT}/p13_leave_one_out_DEV.csv", index=False)
    # ---- robustness (MODERATE) + simultaneous-loss diagnostics
    rob = []
    for name, bud, a in defs:
        L = Ls[(name, "MODERATE")]
        if L is None:
            continue
        for lab_, ex in (("BASE", {}), ("SLIP2", {"slip_ticks": 2}), ("SLIP4", {"slip_ticks": 4}), ("COMM1.00", {"commission": 1.00}),
                         ("TIMING_BRITTLENESS_STRESS", {"delay": 1}), ("MARGINx1.5_INTRADAY", {"m_intra": 1.5}),
                         ("ON_MARGINx2", {"m_on": 2.0})):
            o, d, _ = run_port(bk, bud, sig, L, "MODERATE", extra=ex, tilt=tilts.get(a), pers=("DEV", "PRE23", "P23"))
            rob.append({"portfolio": name, "test": lab_, **o})
        d = dailies[(name, "MODERATE")]
        mem = list(bud)
        dd_ = D.loc[D.index <= DEV_END, mem]
        nl = (dd_ < 0).sum(1)
        j = d.pnl.reindex(dd_.index)
        rob.append({"portfolio": name, "test": "SIMULTANEOUS_LOSS",
                    "days_all_sleeves_lose": int((nl == len(mem)).sum()),
                    "days_majority_lose": int((nl > len(mem) / 2).sum()),
                    "portfolio_avg_on_all_lose_days": float(j[nl == len(mem)].mean()) if (nl == len(mem)).any() else np.nan,
                    "portfolio_worst_on_all_lose_days": float(j[nl == len(mem)].min()) if (nl == len(mem)).any() else np.nan,
                    "share_of_portfolio_loss_from_all_lose_days": float(j[nl == len(mem)].clip(upper=0).sum() / j.clip(upper=0).sum())})
    pd.DataFrame(rob).to_csv(f"{OUT}/p15_portfolio_robustness_DEV.csv", index=False)
    for (name, env), d in dailies.items():
        d.to_csv(f"{OUT}/daily_{name}_{env}_DEV.csv")
    spec = {"sigma_daily_dev": sig[E].to_dict(), "clusters_cut0.5": {k: int(v) for k, v in cl.items()},
            "portfolios": P, "p2_representatives": reps, "count_order": order, "tilt_alphas": list(TILT_ALPHAS),
            "L": {f"{n}|{e}": v for (n, e), v in Ls.items()}}
    json.dump(spec, open(f"{OUT}/p_dev_spec.json", "w"), indent=1)
    pd.set_option("display.width", 260)
    print(front[["portfolio", "risk_env", "L", "DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "DEV_excess_vs_mb",
                 "Y2020_avg", "Y2022_avg", "Y2022_max_dd", "DEV_mu_peak", "DEV_mu_on_peak", "fills_per_day", "env"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
