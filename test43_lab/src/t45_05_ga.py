"""TEST45 Phases 13-16: island-model NSGA-II over SESSION-OVERLAY genomes with NESTED chronological validation.

For every outer fold O_k (2021, 2022, 2023, 2024, 2025-01..2026-05-27) the evolution sees ONLY sessions before the
outer block.  Fitness = walk-forward style inner objectives on the training window (4 chronological inner folds):
  minimise [-median inner-fold $/day, -worst inner-fold $/day, training MaxDD, -session-matched-beta excess, complexity]
  constraints: >= 30 active sessions, sides/day <= 4, |corr with Champion| <= 0.6.
Selection of the ONE candidate per outer fold (predeclared): feasible rank-0 members with worst inner fold > 0, maximise
median_inner_avg / max(train MaxDD, 1000), tie-break lower complexity.  A final evolution on all data <= 2026-05-27 uses
the identical procedure.  Frozen V6 parameters are never touched: genomes only describe the overlay."""
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_overlay as O  # noqa: E402
import t45_sim as S  # noqa: E402

OUT = os.path.join(C.T45, "ga"); os.makedirs(OUT, exist_ok=True)
POP, GENS, MIG_EVERY, N_MIG = 120, 50, 25, 4
SEEDS = (101, 202)
ISLANDS = 3
INNER = 4
NOBJ = 5

# ------------------------------------------------------------------ genome space
SPACE = [("inst", "cat", ["ES", "MNQ", "BOTH"]),
         ("m_on", "cat", [0, 1]), ("m_gap_kind", "cat", O.GAP_KINDS), ("m_gap_norm", "cat", O.GAP_NORMS),
         ("m_gap_hi", "opt", (-2.5, 0.25)), ("m_gap_lo", "opt", (-5.0, -0.75)), ("m_w", "cat", O.WINDOWS),
         ("m_flush_hi", "opt", (-1.2, 0.0)), ("m_flush_lo", "opt", (-3.0, -0.4)), ("m_reclaim", "opt", (0.05, 1.0)),
         ("m_exit", "cat", O.M_EXITS), ("m_q", "cat", [1, 2]), ("m_vol_max", "opt", (0.3, 0.99)),
         ("m_trend", "cat", [-1, 0, 1]), ("m_rel", "cat", [-1, 0, 1]), ("m_v6", "cat", [-1, 0, 1]), ("m_dd_max", "opt", (500.0, 5000.0)),
         ("c_on", "cat", [0, 1]), ("c_time", "cat", O.C_TIMES), ("c_base", "cat", [0, 1]), ("c_feat", "cat", O.C_FEATS),
         ("c_dir", "cat", [-1, 1]), ("c_thr", "num", (-1.5, 1.5)), ("c_boost", "cat", [1, 2]), ("c_vol_max", "opt", (0.3, 0.99)),
         ("o_rule", "cat", O.O_RULES), ("o_thr", "num", (-2.0, 0.0)), ("o_until", "cat", O.O_UNTIL), ("o_w", "cat", O.O_W)]
OFF = {"m_gap_hi": np.inf, "m_gap_lo": -np.inf, "m_flush_hi": np.inf, "m_flush_lo": -np.inf, "m_reclaim": 0.0, "m_vol_max": 1.0,
       "m_dd_max": np.inf, "c_vol_max": 1.0}


def rand_gene(rng, spec):
    nm, t, dom = spec
    if t == "cat":
        return dom[rng.integers(len(dom))]
    v = float(rng.uniform(*dom))
    if t == "opt":
        return v if rng.random() < 0.4 else None                      # None = gate off
    return v


def random_genome(rng):
    g = {nm: rand_gene(rng, (nm, t, d)) for nm, t, d in SPACE}
    if g["m_on"] == 0 and g["c_on"] == 0:
        g["m_on" if rng.random() < 0.5 else "c_on"] = 1
    return g


def decode(gn):
    x = dict(O.DEFAULT)
    for nm, t, d in SPACE:
        v = gn[nm]
        x[nm] = OFF[nm] if (t == "opt" and v is None) else v
    return x


def key(gn):
    x = decode(gn)
    # canonical: genes of inactive modules do not matter
    if not x["m_on"]:
        for k in list(x):
            if k.startswith("m_") and k != "m_on":
                x[k] = O.DEFAULT[k]
    if not x["c_on"]:
        for k in list(x):
            if (k.startswith("c_") or k.startswith("o_")) and k != "c_on":
                x[k] = O.DEFAULT[k]
    if x["c_on"] and x["c_feat"] == "none":
        x["c_dir"] = 1; x["c_thr"] = 0.0; x["c_boost"] = 1
    if x["c_on"] and x["o_rule"] != "KEEP_ADVERSE":
        x["o_thr"] = O.DEFAULT["o_thr"]
    if x["c_on"] and x["o_rule"] not in ("KEEP_ADVERSE", "KEEP_UNTIL"):
        x["o_until"] = O.DEFAULT["o_until"]
    if x["c_on"] and x["o_rule"] != "EXIT_AFTER":
        x["o_w"] = O.DEFAULT["o_w"]
    s = json.dumps({k: (round(v, 2) if isinstance(v, float) and np.isfinite(v) else str(v)) for k, v in sorted(x.items())})
    return hashlib.md5(s.encode()).hexdigest()


def mutate(gn, rng, rate):
    g = dict(gn)
    for nm, t, dom in SPACE:
        if rng.random() >= rate:
            continue
        if t == "cat":
            g[nm] = dom[rng.integers(len(dom))]
        else:
            lo, hi = dom
            if t == "opt" and (g[nm] is None or rng.random() < 0.2):
                g[nm] = float(rng.uniform(lo, hi)) if g[nm] is None else None
            else:
                g[nm] = float(np.clip(g[nm] + rng.normal(0, 0.1 * (hi - lo)), lo, hi))
    if g["m_on"] == 0 and g["c_on"] == 0:
        g["m_on" if rng.random() < 0.5 else "c_on"] = 1
    return g


def crossover(a, b, rng):
    return {nm: (a[nm] if rng.random() < 0.5 else b[nm]) for nm, _, _ in SPACE}


# ------------------------------------------------------------------ fitness
_B = None


def _init():
    global _B
    _B = O.Bank(C.build_panel())


def light_metrics(res, bank, m):
    pnl = sum(r["pnl"] for r in res.values())[m]
    smb = 0.0; sides = 0.0
    for k, r in res.items():
        q_on = np.r_[0.0, r["q_end"][:-1]][m]; q_rth = r["q_rth"][m]
        smb += q_rth.mean() * bank.bench.rth[k][m].mean() + q_on.mean() * bank.bench.on[k][m].mean()
        sides = max(sides, r["sides"][m].mean())
    return pnl, pnl.mean() - smb, sides


def fitness(gn, win, m_tree=None, c_tree=None, ge=None):
    bank = _B
    ge = ge or decode(gn)
    s0, s1 = win
    m = np.zeros(bank.n, bool); m[s0:s1] = True
    res = O.run(ge, bank, 1.0, m_tree, c_tree)
    pnl, smb, sides = light_metrics(res, bank, m)
    chunks = np.array_split(np.arange(len(pnl)), INNER)
    fa = np.array([pnl[c].mean() for c in chunks])
    eq = np.r_[0.0, np.cumsum(pnl)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    ch = bank.bench.champ[m]
    corr = float(np.corrcoef(ch, pnl)[0, 1]) if pnl.std() > 0 else 0.0
    active = int((pnl != 0).sum())
    cx = O.complexity(ge) if m_tree is None and c_tree is None else gn.get("_cx", O.complexity(ge))
    obj = np.array([-np.median(fa), -fa.min(), mdd, -smb, cx], float)
    cv = max(0, 30 - active) / 30 + max(0.0, abs(corr) - 0.6) + max(0.0, sides - 4.0)
    return obj, cv, {"median_inner": float(np.median(fa)), "worst_inner": float(fa.min()), "train_avg": float(pnl.mean()), "train_mdd": mdd,
                     "train_smb": float(smb), "corr": corr, "active": active, "sides_day": float(sides), "complexity": cx,
                     "inner_folds": fa.tolist()}


# ------------------------------------------------------------------ NSGA-II
def dominates(a, b):
    return np.all(a <= b) and np.any(a < b)


def nd_sort(F, CV):
    n = len(F)
    feas = CV <= 0
    rank = np.full(n, -1)
    # constrained domination (Deb): feasible beats infeasible; infeasible compared by violation
    dF = (F[:, None, :] <= F[None, :, :]).all(2) & (F[:, None, :] < F[None, :, :]).any(2)
    fi, fj = feas[:, None], feas[None, :]
    dom = (fi & ~fj) | (fi & fj & dF) | (~fi & ~fj & (CV[:, None] < CV[None, :]))
    np.fill_diagonal(dom, False)
    cnt = dom.sum(0)
    r = 0
    cur = np.where(cnt == 0)[0]
    rem = cnt.copy()
    while len(cur):
        rank[cur] = r
        for i in cur:
            rem[dom[i]] -= 1
        rem[cur] = 10 ** 9
        cur = np.where(rem == 0)[0]
        r += 1
    rank[rank < 0] = r
    return rank


def crowding(F, rank):
    d = np.zeros(len(F))
    for r in np.unique(rank):
        idx = np.where(rank == r)[0]
        if len(idx) <= 2:
            d[idx] = np.inf; continue
        for k in range(F.shape[1]):
            o = idx[np.argsort(F[idx, k])]
            rng_ = F[o[-1], k] - F[o[0], k]
            d[o[0]] = d[o[-1]] = np.inf
            if rng_ > 0:
                d[o[1:-1]] += (F[o[2:], k] - F[o[:-2], k]) / rng_
    return d


def island(args):
    """run one island for `gens` generations starting from `pop` (list of genomes) -> (pop, archive rows)."""
    seed, iid, win, pop, gens, tag = args
    rng = np.random.default_rng(seed * 1000 + iid)
    cache = {}
    arch = []

    def ev(gn):
        k = key(gn)
        if k not in cache:
            obj, cv, info = fitness(gn, win)
            cache[k] = (obj, cv, info)
            arch.append({"key": k, "tag": tag, "seed": seed, "island": iid, **{f"g_{nm}": gn[nm] for nm, _, _ in SPACE},
                         **{f"f{i}": obj[i] for i in range(NOBJ)}, "cv": cv, **{kk: v for kk, v in info.items() if kk != "inner_folds"}})
        return cache[k]
    if pop is None:
        pop = [random_genome(rng) for _ in range(POP)]
    E = [ev(g) for g in pop]
    for gen in range(gens):
        F = np.array([e[0] for e in E]); CV = np.array([e[1] for e in E])
        rank = nd_sort(F, CV); crowd = crowding(F, rank)
        kids = []
        while len(kids) < POP:
            i, j = rng.integers(len(pop), size=2)
            a = i if (rank[i], -crowd[i]) < (rank[j], -crowd[j]) else j
            i, j = rng.integers(len(pop), size=2)
            b = i if (rank[i], -crowd[i]) < (rank[j], -crowd[j]) else j
            ch = crossover(pop[a], pop[b], rng) if rng.random() < 0.9 else dict(pop[a])
            kids.append(mutate(ch, rng, 2.0 / len(SPACE)))
        KE = [ev(g) for g in kids]
        allp = pop + kids; allE = E + KE
        # de-duplicate by key
        seen = set(); keep = []
        for i, g in enumerate(allp):
            k = key(g)
            if k not in seen:
                seen.add(k); keep.append(i)
        allp = [allp[i] for i in keep]; allE = [allE[i] for i in keep]
        F = np.array([e[0] for e in allE]); CV = np.array([e[1] for e in allE])
        rank = nd_sort(F, CV); crowd = crowding(F, rank)
        order = sorted(range(len(allp)), key=lambda i: (rank[i], -crowd[i]))[:POP]
        pop = [allp[i] for i in order]; E = [allE[i] for i in order]
    return pop, arch, [key(g) for g in pop]


def select(front_rows):
    f = front_rows[(front_rows.cv <= 0) & (front_rows.worst_inner > 0)].copy()
    if len(f) == 0:
        return None, f
    f["sel_score"] = f.median_inner / np.maximum(f.train_mdd, 1000.0)
    f = f.sort_values(["sel_score", "complexity"], ascending=[False, True])
    return f.iloc[0], f


def row_to_genome(r):
    g = {}
    for nm, t, d in SPACE:
        v = r[f"g_{nm}"]
        if t == "opt" and (v is None or (isinstance(v, float) and np.isnan(v))):
            v = None
        elif t == "cat" and isinstance(d[0], int):
            v = int(v)
        elif t in ("num", "opt"):
            v = float(v)
        g[nm] = v
    return g


def outer_eval(gn, bank, s0, s1):
    ge = decode(gn)
    m = np.zeros(bank.n, bool); m[s0:s1] = True
    res = O.run(ge, bank, 1.0)
    o = S.metrics(res, bank.bench, m)
    return o


def run_fold(tag, win, test, pool):
    t0 = time.time()
    args = [(sd, i, win, None, MIG_EVERY, tag) for sd in SEEDS for i in range(ISLANDS)]
    out = pool.map(island, args)
    arch = [r for o in out for r in o[1]]
    # ring migration inside each seed: best N_MIG (by rank/crowding order = first in list) -> next island
    pops = [o[0] for o in out]
    for s_i, sd in enumerate(SEEDS):
        base = s_i * ISLANDS
        mig = [pops[base + i][:N_MIG] for i in range(ISLANDS)]
        for i in range(ISLANDS):
            pops[base + i] = pops[base + i][:POP - N_MIG] + [dict(g) for g in mig[(i - 1) % ISLANDS]]
    args = [(sd, 100 + i, win, pops[s_i * ISLANDS + i], GENS - MIG_EVERY, tag) for s_i, sd in enumerate(SEEDS) for i in range(ISLANDS)]
    out2 = pool.map(island, args)
    arch += [r for o in out2 for r in o[1]]
    A = pd.DataFrame(arch).drop_duplicates("key")
    finals = []
    for idx, o in enumerate(out2):
        sd = args[idx][0]; iid = idx % ISLANDS
        ks = set(o[2])
        fr = A[A.key.isin(ks)].copy()
        F = fr[[f"f{i}" for i in range(NOBJ)]].values; CV = fr.cv.values
        rk = nd_sort(F, CV)
        fr = fr[rk == 0].copy(); fr["run_seed"] = sd; fr["run_island"] = iid
        finals.append(fr)
    FR = pd.concat(finals, ignore_index=True)
    # overall front across islands
    Fall = FR.drop_duplicates("key")
    rk = nd_sort(Fall[[f"f{i}" for i in range(NOBJ)]].values, Fall.cv.values)
    front = Fall[rk == 0].copy()
    best, ranked = select(front)
    print(f"{tag}: evaluated {len(A)} unique genomes, front {len(front)}, {time.time() - t0:.0f}s", flush=True)
    return A, FR, front, best, ranked


def main():
    os.makedirs(OUT, exist_ok=True)
    P = C.build_panel()
    bank = O.Bank(P)
    sess = bank.sess
    folds = []
    for name, s, e in C.OUTER:
        s0 = int(np.searchsorted(sess.values, np.datetime64(s)))
        s1 = int(np.searchsorted(sess.values, np.datetime64(e), side="right"))
        folds.append((name, (20, s0), (s0, s1)))                         # training starts after ATR warm-up (20 sessions)
    folds.append(("FINAL_ALL_TO_2026-05-27", (20, bank.n), None))
    res_rows, sel_rows, fronts, archives = [], [], [], []
    with Pool(4, initializer=_init) as pool:
        for tag, win, test in folds:
            A, FR, front, best, ranked = run_fold(tag, win, test, pool)
            A["fold"] = tag; FR["fold"] = tag; front["fold"] = tag
            archives.append(A); fronts.append(FR)
            if best is None:
                sel_rows.append({"fold": tag, "selected": None}); continue
            top = ranked.head(5)
            for rnk, (_, r) in enumerate(top.iterrows()):
                gn = row_to_genome(r)
                o = {"fold": tag, "sel_rank": rnk, "key": r.key, "genome": json.dumps({k: v for k, v in gn.items()}),
                     "inner_median": r.median_inner, "inner_worst": r.worst_inner, "train_avg": r.train_avg, "train_mdd": r.train_mdd,
                     "train_smb": r.train_smb, "complexity": r.complexity}
                if test is not None:
                    ot = outer_eval(gn, bank, *test)
                    o.update({f"outer_{k}": ot[k] for k in ("avg", "total", "max_dd", "worst", "matched_beta_excess", "session_matched_beta_excess",
                                                            "incr_avg", "incr_max_dd", "corr_champion", "sides")})
                    o["degradation_outer_minus_inner_median"] = o["outer_avg"] - r.median_inner
                sel_rows.append(o)
            print(pd.DataFrame(sel_rows).tail(5)[["fold", "sel_rank", "inner_median", "train_mdd"] + (["outer_avg", "outer_max_dd"] if test else [])].to_string(), flush=True)
    AR = pd.concat(archives, ignore_index=True)
    AR.to_parquet(f"{OUT}/T45_13_ga_archive.parquet")
    pd.concat(fronts, ignore_index=True).to_parquet(f"{OUT}/T45_13_ga_island_fronts.parquet")
    SEL = pd.DataFrame(sel_rows); SEL.to_csv(f"{OUT}/T45_13_ga_selected.csv", index=False)
    meta = {"unique_genomes_total": int(AR.key.nunique()), "unique_per_fold": AR.groupby("fold").key.nunique().to_dict(),
            "evaluations_per_fold_upper_bound": POP * (GENS + 1) * ISLANDS * len(SEEDS), "POP": POP, "GENS": GENS, "ISLANDS": ISLANDS,
            "SEEDS": SEEDS, "MIG_EVERY": MIG_EVERY, "N_MIG": N_MIG, "INNER": INNER, "space": [(a, b, str(c)) for a, b, c in SPACE],
            "lock_governor": {"LOCK_K": O.LOCK_K, "LOCK_BUDGET": O.LOCK_BUDGET}, "QMAX": O.QMAX}
    json.dump(meta, open(f"{OUT}/T45_12_ga_spec.json", "w"), indent=1)
    print(json.dumps(meta, indent=1)[:600])


if __name__ == "__main__":
    main()
