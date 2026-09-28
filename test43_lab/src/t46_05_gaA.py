"""TEST46 GA-A: nested chronological island NSGA-II over STRUCTURAL REBOUND genomes (Lane B only; Lane A seeds are
PARITY_BLOCKED and are never evolved).  Same nested design as TEST45: evolution sees only sessions before each outer block.
Fitness (minimised): -median inner-fold $/day, -worst inner-fold $/day, training MaxDD, -matched-long excess $/day, complexity.
Matched long baseline per trade = mean over TRAINING sessions of an unconditional long with the identical entry bar and exit
rule (costs included on both sides).  Constraints: >= 60 trades in training, |corr C43| <= 0.6.
Selection per outer fold (predeclared, identical to TEST45): feasible rank-0, worst inner > 0, max median/max(MDD,1000)."""
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
import t46_common as C  # noqa: E402
import t46_rebound as R  # noqa: E402
from t46_03_laneB import setup  # noqa: E402

OUT = os.path.join(C.T46, "gaA"); os.makedirs(OUT, exist_ok=True)
POP, GENS, MIG, NMIG = 120, 50, 25, 4
SEEDS = (11, 22); ISL = 3; INNER = 4; NOBJ = 5
SPACE = [("fam", "cat", [1, 2, 3, 4, 5, 6, 7]), ("inst", "cat", ["ES", "MNQ"]), ("D", "num", (0.0, 2.0)), ("delta", "num", (0.0, 0.5)),
         ("k", "int", (0, 6)), ("N", "int", (3, 24)), ("rho", "num", (-0.2, 0.5)), ("e0", "int", (1, 24)), ("span", "int", (6, 70)),
         ("veto5", "opt", (1.0, 6.0)), ("vetogap", "opt", (0.5, 3.0)), ("need_bull", "cat", [0, 1]), ("band", "num", (1.0, 3.0)),
         ("relx", "num", (0.2, 1.5)), ("exit_mode", "cat", [0, 1, 2]), ("hold", "cat", [30, 60, 120, 180]), ("stop", "cat", [-1.0, 0.0, 0.25, 0.5])]
_ctx = {}


def _init():
    P, es, nq, rel = setup()
    champ = C45.champion_daily().pnl.reindex(es.pn.sess).fillna(0.0).values
    base = {}
    for mk in (es, nq):
        # unconditional long $ for every 5m entry bar and exit spec (per session), used for matched baselines
        for em, hold in ((0, 30), (0, 60), (0, 120), (0, 180), (1, 0), (2, 0)):
            M = np.full((mk.n, R.NB), np.nan)
            for e in range(R.NB - 1):
                j = 5 * (e + 1)
                if j >= C45.NG:
                    continue
                jx = min(j + hold, C45.g("16:15")) if em == 0 else (C45.g("16:00") if em == 1 else C45.g("16:15"))
                if jx <= j:
                    continue
                M[:, e] = (mk.FPb[:, jx] - mk.FP[:, j]) * mk.pv - 2 * C45.cost_side(mk.k)
            base[(mk.inst, em, hold)] = M
    _ctx.update(es=es, nq=nq, rel=rel, champ=champ, base=base)


def rand_gene(rng, spec):
    nm, t, d = spec
    if t == "cat":
        return d[rng.integers(len(d))]
    if t == "int":
        return int(rng.integers(d[0], d[1] + 1))
    v = float(rng.uniform(*d))
    return (v if rng.random() < 0.5 else None) if t == "opt" else v


def random_genome(rng):
    return {nm: rand_gene(rng, (nm, t, d)) for nm, t, d in SPACE}


def fix(g):
    g = dict(g)
    if g["fam"] == 7:
        g["inst"] = "MNQ"
    return g


def key(g):
    g = fix(g)
    x = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in g.items()}
    if g["fam"] != 3:
        x["band"] = 0
    if g["fam"] != 7:
        x["relx"] = 0
    if g["exit_mode"] != 0:
        x["hold"] = 0
    return json.dumps(x, sort_keys=True, default=str)


def params(g):
    return dict(D=g["D"], delta=g["delta"], k=g["k"], N=g["N"], rho=g["rho"], e0=g["e0"], e1=min(g["e0"] + g["span"], 75),
                veto5=g["veto5"] if g["veto5"] is not None else 99.0, vetogap=g["vetogap"] if g["vetogap"] is not None else 99.0,
                need_bull=g["need_bull"], band=g["band"], relx=g["relx"])


def complexity(g):
    return int(1 + (g["D"] > 0.05) + (g["delta"] > 0.02) + (g["k"] > 0) + (g["rho"] > 0.02) + (g["veto5"] is not None)
               + (g["vetogap"] is not None) + (g["need_bull"] == 1) + (g["stop"] >= 0))


def run_genome(g, slip=1.0):
    g = fix(g)
    mk = _ctx["es"] if g["inst"] == "ES" else _ctx["nq"]
    ev, brk = R.run_detect(mk, g["fam"], params(g), _ctx["rel"] if g["fam"] == 7 else None)
    pnl, ji, jo = R.run_trades(mk, ev, brk, g["exit_mode"], g["hold"], g["stop"], slip)
    return mk, ev, pnl


def fitness(g, win):
    mk, ev, pnl = run_genome(g)
    s0, s1 = win
    x = pnl[s0:s1]
    chunks = np.array_split(np.arange(len(x)), INNER)
    fa = np.array([x[c].mean() for c in chunks])
    eq = np.r_[0.0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    em, hold = g["exit_mode"], (g["hold"] if g["exit_mode"] == 0 else 0)
    M = _ctx["base"][(fix(g)["inst"], em, hold)]
    bl = np.nanmean(M[s0:s1], axis=0)                       # training-window baseline per entry bar
    evw = ev[s0:s1]; has = evw >= 0
    exc = np.where(has, x - np.nan_to_num(bl[np.clip(evw, 0, R.NB - 1)]), 0.0)
    trades = int(has.sum())
    ch = _ctx["champ"][s0:s1]
    corr = float(np.corrcoef(ch, x)[0, 1]) if x.std() > 0 else 0.0
    cx = complexity(g)
    obj = np.array([-np.median(fa), -fa.min(), mdd, -exc.mean(), cx], float)
    cv = max(0, 60 - trades) / 60 + max(0.0, abs(corr) - 0.6)
    return obj, cv, {"median_inner": float(np.median(fa)), "worst_inner": float(fa.min()), "train_avg": float(x.mean()), "train_mdd": mdd,
                     "train_excess_day": float(exc.mean()), "train_trades": trades, "corr": corr, "complexity": cx}


def mutate(g, rng, rate):
    x = dict(g)
    for nm, t, d in SPACE:
        if rng.random() >= rate:
            continue
        if t == "cat":
            x[nm] = d[rng.integers(len(d))]
        elif t == "int":
            x[nm] = int(np.clip(x[nm] + rng.integers(-3, 4), d[0], d[1]))
        elif t == "opt" and (x[nm] is None or rng.random() < 0.2):
            x[nm] = float(rng.uniform(*d)) if x[nm] is None else None
        else:
            lo, hi = d
            x[nm] = float(np.clip(x[nm] + rng.normal(0, 0.1 * (hi - lo)), lo, hi))
    return x


def island(args):
    seed, iid, win, pop, gens, tag = args
    rng = np.random.default_rng(seed * 1000 + iid)
    cache, arch = {}, []

    def ev_(gn):
        kk = key(gn)
        if kk not in cache:
            obj, cv, info = fitness(gn, win)
            cache[kk] = (obj, cv)
            arch.append({"key": kk, "tag": tag, "seed": seed, "island": iid, "genome": json.dumps(fix(gn)), **{f"f{i}": obj[i] for i in range(NOBJ)}, "cv": cv, **info})
        return cache[kk]
    if pop is None:
        pop = [random_genome(rng) for _ in range(POP)]
    E = [ev_(x) for x in pop]
    for _ in range(gens):
        F = np.array([e[0] for e in E]); CV = np.array([e[1] for e in E])
        rk = G45.nd_sort(F, CV); cr = G45.crowding(F, rk)
        kids = []
        while len(kids) < POP:
            i, j = rng.integers(len(pop), size=2); a = i if (rk[i], -cr[i]) < (rk[j], -cr[j]) else j
            i, j = rng.integers(len(pop), size=2); b = i if (rk[i], -cr[i]) < (rk[j], -cr[j]) else j
            ch = {nm: (pop[a][nm] if rng.random() < 0.5 else pop[b][nm]) for nm, _, _ in SPACE} if rng.random() < 0.9 else dict(pop[a])
            kids.append(mutate(ch, rng, 2.0 / len(SPACE)))
        KE = [ev_(x) for x in kids]
        allp = pop + kids; allE = E + KE
        seen, keep = set(), []
        for i, x in enumerate(allp):
            kk = key(x)
            if kk not in seen:
                seen.add(kk); keep.append(i)
        allp = [allp[i] for i in keep]; allE = [allE[i] for i in keep]
        F = np.array([e[0] for e in allE]); CV = np.array([e[1] for e in allE])
        rk = G45.nd_sort(F, CV); cr = G45.crowding(F, rk)
        order = sorted(range(len(allp)), key=lambda i: (rk[i], -cr[i]))[:POP]
        pop = [allp[i] for i in order]; E = [allE[i] for i in order]
    return pop, arch, [key(x) for x in pop]


def outer_eval(g, s0, s1):
    mk, ev, pnl = run_genome(g)
    x = pnl[s0:s1]
    em, hold = g["exit_mode"], (g["hold"] if g["exit_mode"] == 0 else 0)
    M = _ctx["base"][(fix(g)["inst"], em, hold)]
    bl = np.nanmean(M[:s0], axis=0)                          # baseline from data BEFORE the block (causal)
    evw = ev[s0:s1]; has = evw >= 0
    exc = np.where(has, x - np.nan_to_num(bl[np.clip(evw, 0, R.NB - 1)]), 0.0)
    eq = np.r_[0.0, np.cumsum(x)]
    return {"outer_avg": float(x.mean()), "outer_total": float(x.sum()), "outer_trades": int(has.sum()),
            "outer_mdd": float((np.maximum.accumulate(eq) - eq).max()), "outer_excess_day": float(exc.mean()),
            "outer_corr_C43": float(np.corrcoef(_ctx["champ"][s0:s1], x)[0, 1]) if x.std() > 0 else np.nan}


def main():
    _init()
    sess = _ctx["es"].pn.sess
    folds = []
    for name, s, e in C45.OUTER:
        s0 = int(np.searchsorted(sess.values, np.datetime64(s))); s1 = int(np.searchsorted(sess.values, np.datetime64(e), side="right"))
        folds.append((name, (20, s0), (s0, s1)))
    folds.append(("FINAL_ALL_TO_2026-05-27", (20, len(sess)), None))
    archs, sel = [], []
    with Pool(4, initializer=_init) as pool:
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
            fin = A[A.key.isin(set(k for o in out2 for k in o[2]))]
            rk = G45.nd_sort(fin[[f"f{i}" for i in range(NOBJ)]].values, fin.cv.values)
            front = fin[rk == 0].copy()
            best, ranked = G45.select(front)
            A.to_parquet(f"{OUT}/archive_{tag}.parquet"); archs.append(A[["key", "fold"]])
            front.to_parquet(f"{OUT}/front_{tag}.parquet")
            if best is None:
                sel.append({"fold": tag, "selected": "NONE (no feasible front member with worst inner fold > 0)"})
            else:
                for rnk, (_, r) in enumerate(ranked.head(5).iterrows()):
                    g = json.loads(r.genome)
                    o = {"fold": tag, "sel_rank": rnk, "genome": r.genome, "inner_median": r.median_inner, "inner_worst": r.worst_inner,
                         "train_mdd": r.train_mdd, "train_excess_day": r.train_excess_day, "train_trades": r.train_trades, "complexity": r.complexity}
                    if test is not None:
                        o.update(outer_eval(g, *test))
                        o["degradation"] = o["outer_avg"] - r.median_inner
                    sel.append(o)
            print(tag, len(A), f"{time.time() - t0:.0f}s", flush=True)
    SEL = pd.DataFrame(sel); SEL.to_csv(f"{OUT}/T46_26_gaA_selected.csv", index=False)
    AR = pd.concat(archs); json.dump({"unique_genomes_total": int(AR.key.nunique()), "per_fold": AR.groupby("fold").key.nunique().to_dict(),
                                      "POP": POP, "GENS": GENS, "SEEDS": SEEDS, "ISLANDS": ISL, "space": [(a, b, str(c)) for a, b, c in SPACE]},
                                     open(f"{OUT}/T46_25_gaA_spec.json", "w"), indent=1)
    print(SEL.drop(columns=["genome"], errors="ignore").round(2).to_string())


if __name__ == "__main__":
    main()
