"""Generic nested chronological island NSGA-II for the autonomous program (same design as TEST45/46/47).
A LANE module provides: NAME, SPACE, init() -> ctx dict, run(g, ctx, slip=1.0) -> (daily $, s, j, pnl, rule),
complexity(g), cluster(g).  Fitness (minimised) on the training window: [-median inner-fold $/day, -worst inner-fold $/day,
training MaxDD, -matched-long excess $/day (unconditional long with identical entry minute and exit, mean over the
TRAINING window only), complexity]; constraints >= MIN_TRADES trades in training and |corr C43| <= 0.5 (novelty).
Outer evaluation: frozen per-fold selection evaluated once on the next block; excess baseline = sessions before the block."""
import importlib
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t45_05_ga as G45  # noqa: E402
import t47_engine as E  # noqa: E402

POP, GENS, MIG, NMIG = 64, 40, 20, 4
SEEDS = (11, 22); ISL = 3; INNER = 4; NOBJ = 5; MIN_TRADES = 60; MAXCORR = 0.5
_ctx = {}


def base_tables(mks, rules):
    out = {}
    for mk in mks.values():
        bl = E.Baseline(mk)
        for r in rules:
            out[(mk.inst, r)] = bl.table(r)[0]
    return out


def _init(lane_name):
    L = importlib.import_module(lane_name)
    _ctx.clear()
    _ctx["L"] = L
    _ctx.update(L.init())
    if "champ" not in _ctx:
        _ctx["champ"] = C45.champion_daily().pnl.reindex(_ctx["sess"]).fillna(0.0).values


def native(v):
    return v.item() if hasattr(v, "item") else v


def key(g):
    return json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in g.items()}, sort_keys=True, default=str)


def excess_window(res, s0, s1, b0, b1):
    d, s, j, pnl, M = res
    x = np.zeros(len(d))
    if len(s):
        bl = np.nanmean(M[b0:b1], axis=0)
        np.add.at(x, s, pnl - np.nan_to_num(bl[j]))
    return x[s0:s1]


def evaluate(g):
    L = _ctx["L"]
    d, s, j, pnl, rule = L.run(g, _ctx)
    M = _ctx["base"][(g.get("inst", "MNQ"), rule)]
    return (d, s, j, pnl, M)


def fitness(g, win):
    res = evaluate(g)
    s0, s1 = win
    x = res[0][s0:s1]
    xe = excess_window(res, s0, s1, s0, s1)
    ntr = int(((res[1] >= s0) & (res[1] < s1)).sum())
    chunks = np.array_split(np.arange(len(x)), INNER)
    fa = np.array([x[c].mean() for c in chunks])
    eq = np.r_[0.0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    ch = _ctx["champ"][s0:s1]
    corr = float(np.corrcoef(ch, x)[0, 1]) if x.std() > 0 else 0.0
    cx = _ctx["L"].complexity(g)
    obj = np.array([-np.median(fa), -fa.min(), mdd, -xe.mean(), cx], float)
    cv = max(0, MIN_TRADES - ntr) / MIN_TRADES + max(0.0, abs(corr) - MAXCORR)
    return obj, cv, {"median_inner": float(np.median(fa)), "worst_inner": float(fa.min()), "train_avg": float(x.mean()), "train_mdd": mdd,
                     "train_excess_day": float(xe.mean()), "train_trades": ntr, "corr": corr, "complexity": cx}


def rand_gene(rng, spec):
    nm, t, d = spec
    if t == "cat":
        return d[rng.integers(len(d))]
    return float(rng.uniform(*d))


def mutate(space, g, rng, rate):
    x = dict(g)
    for nm, t, d in space:
        if rng.random() >= rate:
            continue
        if t == "cat":
            x[nm] = d[rng.integers(len(d))]
        else:
            lo, hi = d
            x[nm] = float(np.clip(x[nm] + rng.normal(0, 0.12 * (hi - lo)), lo, hi))
    return x


def island(args):
    seed, iid, win, pop, gens, tag = args
    space = _ctx["L"].SPACE
    rng = np.random.default_rng(seed * 1000 + iid)
    cache, arch = {}, []

    def ev_(gn):
        gn = {k: native(v) for k, v in gn.items()}
        kk = key(gn)
        if kk not in cache:
            obj, cv, info = fitness(gn, win)
            cache[kk] = (obj, cv)
            arch.append({"key": kk, "tag": tag, "seed": seed, "island": iid, "genome": json.dumps(gn), **{f"f{i}": obj[i] for i in range(NOBJ)}, "cv": cv, **info})
        return cache[kk]
    if pop is None:
        pop = [{nm: native(rand_gene(rng, (nm, t, d))) for nm, t, d in space} for _ in range(POP)]
    E_ = [ev_(x) for x in pop]
    for _ in range(gens):
        F = np.array([e[0] for e in E_]); CV = np.array([e[1] for e in E_])
        rk = G45.nd_sort(F, CV); cr = G45.crowding(F, rk)
        kids = []
        while len(kids) < POP:
            i, j = rng.integers(len(pop), size=2); a = i if (rk[i], -cr[i]) < (rk[j], -cr[j]) else j
            i, j = rng.integers(len(pop), size=2); b = i if (rk[i], -cr[i]) < (rk[j], -cr[j]) else j
            ch = {nm: (pop[a][nm] if rng.random() < 0.5 else pop[b][nm]) for nm, _, _ in space} if rng.random() < 0.9 else dict(pop[a])
            kids.append({k: native(v) for k, v in mutate(space, ch, rng, 2.0 / len(space)).items()})
        KE = [ev_(x) for x in kids]
        allp = pop + kids; allE = E_ + KE
        seen, keep = set(), []
        for i, x in enumerate(allp):
            kk = key(x)
            if kk not in seen:
                seen.add(kk); keep.append(i)
        allp = [allp[i] for i in keep]; allE = [allE[i] for i in keep]
        F = np.array([e[0] for e in allE]); CV = np.array([e[1] for e in allE])
        rk = G45.nd_sort(F, CV); cr = G45.crowding(F, rk)
        order = sorted(range(len(allp)), key=lambda i: (rk[i], -cr[i]))[:POP]
        pop = [allp[i] for i in order]; E_ = [allE[i] for i in order]
    return pop, arch, [key(x) for x in pop]


def outer_eval(g, s0, s1):
    res = evaluate(g)
    x = res[0][s0:s1]
    xe = excess_window(res, s0, s1, 20, s0)
    eq = np.r_[0.0, np.cumsum(x)]
    return {"outer_avg": float(x.mean()), "outer_total": float(x.sum()), "outer_trades": int(((res[1] >= s0) & (res[1] < s1)).sum()),
            "outer_mdd": float((np.maximum.accumulate(eq) - eq).max()), "outer_excess_day": float(xe.mean()),
            "outer_corr_C43": float(np.corrcoef(_ctx["champ"][s0:s1], x)[0, 1]) if x.std() > 0 else np.nan}


def stitched(lane_name, S):
    """stitched outer daily $ and excess from the per-fold rank-0 selections."""
    _init(lane_name)
    sess = _ctx["sess"]
    st = np.zeros(len(sess)); ex = np.zeros(len(sess)); clusters = []
    for name, a, b in C45.OUTER:
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        if not len(r) or not isinstance(r.iloc[0].get("genome"), str):
            clusters.append("NONE"); continue
        g = json.loads(r.iloc[0].genome); clusters.append(_ctx["L"].cluster(g))
        s0 = int(np.searchsorted(sess.values, np.datetime64(a))); s1 = int(np.searchsorted(sess.values, np.datetime64(b), side="right"))
        res = evaluate(g)
        st[s0:s1] = res[0][s0:s1]; ex[s0:s1] = excess_window(res, s0, s1, 20, s0)
    return st, ex, clusters


def run_lane(lane_name, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    _init(lane_name)
    L = _ctx["L"]; sess = _ctx["sess"]
    folds = []
    for name, s, e in C45.OUTER:
        s0 = int(np.searchsorted(sess.values, np.datetime64(s))); s1 = int(np.searchsorted(sess.values, np.datetime64(e), side="right"))
        folds.append((name, (20, s0), (s0, s1)))
    folds.append(("FINAL_ALL_TO_2026-05-27", (20, len(sess)), None))
    sel, uniq = [], {}
    with Pool(4, initializer=_init, initargs=(lane_name,)) as pool:
        for tag, win, test in folds:
            t0 = time.time()
            out = pool.map(island, [(sd, i, win, None, MIG, tag) for sd in SEEDS for i in range(ISL)])
            pops = [o[0] for o in out]
            for si in range(len(SEEDS)):
                b = si * ISL; mig = [pops[b + i][:NMIG] for i in range(ISL)]
                for i in range(ISL):
                    pops[b + i] = pops[b + i][:POP - NMIG] + [dict(x) for x in mig[(i - 1) % ISL]]
            out2 = pool.map(island, [(sd, 100 + i, win, pops[si * ISL + i], GENS - MIG, tag) for si, sd in enumerate(SEEDS) for i in range(ISL)])
            A = pd.DataFrame([r for o in out + out2 for r in o[1]]).drop_duplicates("key"); A["fold"] = tag
            uniq[tag] = int(A.key.nunique())
            fin = A[A.key.isin(set(k for o in out2 for k in o[2]))]
            rk = G45.nd_sort(fin[[f"f{i}" for i in range(NOBJ)]].values, fin.cv.values)
            front = fin[rk == 0].copy()
            best, ranked = G45.select(front)
            front.to_parquet(f"{out_dir}/front_{L.NAME}_{tag}.parquet")
            A[["key", "fold", "median_inner", "worst_inner", "train_excess_day", "cv"]].to_parquet(f"{out_dir}/archive_{L.NAME}_{tag}.parquet")
            if best is None:
                sel.append({"lane": L.NAME, "fold": tag, "sel_rank": 0, "selected": "NONE (no feasible front member with worst inner > 0)"})
            else:
                for rnk, (_, r) in enumerate(ranked.head(5).iterrows()):
                    g = json.loads(r.genome)
                    o = {"lane": L.NAME, "fold": tag, "sel_rank": rnk, "genome": r.genome, "cluster": L.cluster(g), "inner_median": r.median_inner,
                         "inner_worst": r.worst_inner, "train_mdd": r.train_mdd, "train_excess_day": r.train_excess_day, "complexity": r.complexity}
                    if test is not None:
                        o.update(outer_eval(g, *test)); o["degradation"] = o["outer_avg"] - r.median_inner
                    sel.append(o)
            print(L.NAME, tag, len(A), f"{time.time() - t0:.0f}s", flush=True)
    S = pd.DataFrame(sel); S.to_csv(f"{out_dir}/{L.NAME}_selected.csv", index=False)
    json.dump({"POP": POP, "GENS": GENS, "SEEDS": SEEDS, "ISL": ISL, "unique_per_fold": uniq, "total_unique": int(sum(uniq.values())),
               "space": [(a, b, str(c)) for a, b, c in L.SPACE]}, open(f"{out_dir}/{L.NAME}_spec.json", "w"), indent=1)
    return S, int(sum(uniq.values()))


def plateau(lane_name, g, s_from, num_params, disc_params=None):
    """+-10/20% for continuous params; adjacent values for discrete ones; totals on sessions >= s_from."""
    _init(lane_name)
    base = evaluate(g)[0][s_from:].sum()
    rows = []
    for nm in num_params:
        for f in (0.8, 0.9, 1.1, 1.2):
            h = dict(g); h[nm] = g[nm] * f
            rows.append({"param": nm, "value": h[nm], "total": float(evaluate(h)[0][s_from:].sum())})
    for nm, vals in (disc_params or {}).items():
        for v in vals:
            if v != g[nm]:
                h = dict(g); h[nm] = v
                rows.append({"param": nm, "value": v, "total": float(evaluate(h)[0][s_from:].sum())})
    R = pd.DataFrame(rows)
    ok = bool(base > 0 and len(R) and (R.total > 0).all() and (R.total >= 0.6 * base).all())
    return ok, float(base), R
