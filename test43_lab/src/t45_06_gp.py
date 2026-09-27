"""TEST45 Phase 17: restricted genetic programming of rule STRUCTURE (nested, same outer folds / fitness / selection as GA).

Two module types are evolved separately:
  GP_MORNING: trigger tree evaluated after an opening window w -> long m_q, exit at m_exit
  GP_CLOSE:   boost-condition tree at decision time c_time -> locked target c_boost if true else c_base; exit at next open
Primitives: inputs (below), GT/LT against a constant, AND, OR, NOT.  max depth 4 (<=5 allowed), <= 15 nodes, parsimony =
node count is an objective.  Disallowed: raw date/weekday/month/day/year, contract id, absolute price, timestamps."""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_feat as F  # noqa: E402
import t45_overlay as O  # noqa: E402
import t45_05_ga as GA  # noqa: E402

OUT = os.path.join(C.T45, "gp"); os.makedirs(OUT, exist_ok=True)
POP, GENS, MIG = 80, 30, 15
SEEDS = (303, 404)
ISL = 2
MAXD, MAXN = 4, 15
M_IN = ["gap_atr", "gap_pct", "gap_sigma", "opening_selloff_atr", "opening_recovery_atr", "current_RTH_return", "RTH_range_position",
        "distance_to_RTH_VWAP", "prior_day_return", "prior_day_range", "volatility_percentile", "ES_NQ_relative_strength",
        "current_V6_intensity", "portfolio_DD"]
C_IN = ["gap_atr", "current_RTH_return", "RTH_range_position", "distance_to_RTH_VWAP", "prior_day_return", "prior_day_range",
        "volatility_percentile", "ES_NQ_relative_strength", "current_V6_intensity", "portfolio_DD"]
M_W = [5, 15, 30, 60, 90]
FEAT = None


def gp_features(bank):
    Fm, Fc = {}, {}
    for k in (0, 1):
        pn = bank.sims[k].pn; o = bank.sims[1 - k].pn; I = bank.I[k]
        a = pn.atr
        for w in M_W:
            f = F.morning(pn, w); fo = F.morning(o, w)
            Fm[(k, w)] = {"gap_atr": pn.gap_lock / a, "gap_pct": 100 * pn.gap_lock / pn.p_lock, "gap_sigma": pn.gap_lock / pn.gap_sigma,
                          "opening_selloff_atr": f["selloff_w"], "opening_recovery_atr": f["recovery_w"], "current_RTH_return": f["ret_w"],
                          "RTH_range_position": f["range_pos_w"], "distance_to_RTH_VWAP": f["dist_vwap_w"], "prior_day_return": f["prior_ret"],
                          "prior_day_range": f["prior_range"], "volatility_percentile": I["vol_pct"],
                          "ES_NQ_relative_strength": f["ret_w"] - fo["ret_w"] + (pn.gap_lock / a - o.gap_lock / o.atr),
                          "current_V6_intensity": I["champ_open"], "portfolio_DD": I["champ_dd"]}
        for t in O.C_TIMES:
            j = C.g(t)
            f = F.late(pn, j); fo = F.late(o, j)
            Fc[(k, t)] = {"gap_atr": pn.gap_lock / a, "current_RTH_return": f["rth_ret"], "RTH_range_position": f["range_pos"],
                          "distance_to_RTH_VWAP": f["dist_vwap"], "prior_day_return": f["prior_ret"], "prior_day_range": f["prior_range"],
                          "volatility_percentile": I["vol_pct"], "ES_NQ_relative_strength": f["day_ret"] - fo["day_ret"],
                          "current_V6_intensity": I[f"champ_pos@{t}"], "portfolio_DD": I["champ_dd"]}
    return Fm, Fc


# ------------------------------------------------------------------ trees
def rand_leaf(rng, inputs, Q):
    f = inputs[rng.integers(len(inputs))]
    return (("GT", "LT")[rng.integers(2)], f, float(Q[f][rng.integers(len(Q[f]))]))


def rand_tree(rng, inputs, Q, depth):
    if depth <= 1 or rng.random() < 0.35:
        return rand_leaf(rng, inputs, Q)
    op = ("AND", "OR", "NOT", "AND")[rng.integers(4)]
    if op == "NOT":
        return ("NOT", rand_tree(rng, inputs, Q, depth - 1))
    return (op, rand_tree(rng, inputs, Q, depth - 1), rand_tree(rng, inputs, Q, depth - 1))


def size(t):
    if t[0] in ("GT", "LT"):
        return 1
    return 1 + sum(size(c) for c in t[1:])


def depth(t):
    if t[0] in ("GT", "LT"):
        return 1
    return 1 + max(depth(c) for c in t[1:])


def evalt(t, X):
    op = t[0]
    if op == "GT":
        return np.nan_to_num(X[t[1]], nan=-np.inf) > t[2]
    if op == "LT":
        return np.nan_to_num(X[t[1]], nan=np.inf) < t[2]
    if op == "NOT":
        return ~evalt(t[1], X)
    a, b = evalt(t[1], X), evalt(t[2], X)
    return a & b if op == "AND" else a | b


def subtrees(t, path=()):
    yield path, t
    if t[0] not in ("GT", "LT"):
        for i, c in enumerate(t[1:], start=1):
            yield from subtrees(c, path + (i,))


def replace(t, path, new):
    if not path:
        return new
    lst = list(t); lst[path[0]] = replace(t[path[0]], path[1:], new)
    return tuple(lst)


def show(t):
    if t[0] in ("GT", "LT"):
        return f"{t[1]} {'>' if t[0] == 'GT' else '<'} {t[2]:.3g}"
    if t[0] == "NOT":
        return f"NOT({show(t[1])})"
    return f"({show(t[1])} {t[0]} {show(t[2])})"


# ------------------------------------------------------------------ individuals
def rand_ind(rng, kind, Q):
    inputs = M_IN if kind == "GP_MORNING" else C_IN
    ind = {"kind": kind, "inst": ["ES", "MNQ", "BOTH"][rng.integers(3)], "tree": rand_tree(rng, inputs, Q[kind], MAXD)}
    if kind == "GP_MORNING":
        ind.update(w=M_W[rng.integers(len(M_W))], m_exit=O.M_EXITS[:-1][rng.integers(len(O.M_EXITS) - 1)], m_q=int(rng.integers(1, 3)))
    else:
        ind.update(c_time=O.C_TIMES[rng.integers(len(O.C_TIMES))], c_base=int(rng.integers(0, 2)), c_boost=int(rng.integers(1, 3)))
    return ind


def valid(ind):
    return depth(ind["tree"]) <= MAXD + 1 and size(ind["tree"]) <= MAXN


def mutate(ind, rng, Q):
    x = dict(ind)
    inputs = M_IN if x["kind"] == "GP_MORNING" else C_IN
    r = rng.random()
    if r < 0.4:
        ps = list(subtrees(x["tree"])); p, _ = ps[rng.integers(len(ps))]
        x["tree"] = replace(x["tree"], p, rand_tree(rng, inputs, Q[x["kind"]], 2))
    elif r < 0.75:                                          # point mutation of a leaf constant / feature / direction
        ps = [(p, s) for p, s in subtrees(x["tree"]) if s[0] in ("GT", "LT")]
        p, s = ps[rng.integers(len(ps))]
        q = Q[x["kind"]][s[1]]
        u = rng.random()
        if u < 0.6:
            i = int(np.clip(np.searchsorted(q, s[2]) + rng.integers(-2, 3), 0, len(q) - 1))
            new = (s[0], s[1], float(q[i]))
        elif u < 0.8:
            new = ("LT" if s[0] == "GT" else "GT", s[1], s[2])
        else:
            new = rand_leaf(rng, inputs, Q[x["kind"]])
        x["tree"] = replace(x["tree"], p, new)
    else:                                                   # module gene
        if x["kind"] == "GP_MORNING":
            which = rng.integers(4)
            if which == 0: x["w"] = M_W[rng.integers(len(M_W))]
            elif which == 1: x["m_exit"] = O.M_EXITS[:-1][rng.integers(len(O.M_EXITS) - 1)]
            elif which == 2: x["m_q"] = int(rng.integers(1, 3))
            else: x["inst"] = ["ES", "MNQ", "BOTH"][rng.integers(3)]
        else:
            which = rng.integers(4)
            if which == 0: x["c_time"] = O.C_TIMES[rng.integers(len(O.C_TIMES))]
            elif which == 1: x["c_base"] = int(rng.integers(0, 2))
            elif which == 2: x["c_boost"] = int(rng.integers(1, 3))
            else: x["inst"] = ["ES", "MNQ", "BOTH"][rng.integers(3)]
    return x if valid(x) else ind


def cross(a, b, rng):
    pa = list(subtrees(a["tree"])); pb = list(subtrees(b["tree"]))
    p, _ = pa[rng.integers(len(pa))]; _, s = pb[rng.integers(len(pb))]
    x = dict(a); x["tree"] = replace(a["tree"], p, s)
    return x if valid(x) else a


def key(ind):
    d = {k: (show(v) if k == "tree" else v) for k, v in sorted(ind.items())}
    return json.dumps(d, default=str)


def to_overlay(ind, Fm, Fc):
    ks = [0, 1] if ind["inst"] == "BOTH" else [C.INSTS.index(ind["inst"])]
    if ind["kind"] == "GP_MORNING":
        ge = O.G(inst=ind["inst"], m_on=1, m_w=ind["w"], m_exit=ind["m_exit"], m_q=ind["m_q"])
        return ge, {k: evalt(ind["tree"], Fm[(k, ind["w"])]) for k in ks}, None
    ge = O.G(inst=ind["inst"], c_on=1, c_time=ind["c_time"], c_base=ind["c_base"], c_boost=ind["c_boost"], c_feat="tree")
    return ge, None, {k: evalt(ind["tree"], Fc[(k, ind["c_time"])]) for k in ks}


_FM = _FC = _Q = None


def _init():
    global _FM, _FC
    GA._init()
    _FM, _FC = gp_features(GA._B)


def quantiles(Fm, Fc, s0, s1):
    Q = {"GP_MORNING": {}, "GP_CLOSE": {}}
    for f in M_IN:
        v = np.concatenate([Fm[(k, 30)][f][s0:s1] for k in (0, 1)])
        Q["GP_MORNING"][f] = np.unique(np.nanquantile(v, np.linspace(0.02, 0.98, 25)))
    for f in C_IN:
        v = np.concatenate([Fc[(k, "15:45")][f][s0:s1] for k in (0, 1)])
        Q["GP_CLOSE"][f] = np.unique(np.nanquantile(v, np.linspace(0.02, 0.98, 25)))
    return Q


def island(args):
    seed, iid, win, pop, gens, tag, kind = args
    rng = np.random.default_rng(seed * 1000 + iid)
    Q = quantiles(_FM, _FC, *win)
    cache, arch = {}, []

    def ev(ind):
        k = key(ind)
        if k not in cache:
            ge, mt, ct = to_overlay(ind, _FM, _FC)
            gn = {"_cx": size(ind["tree"]) + 1}
            obj, cv, info = GA.fitness(gn, win, mt, ct, ge)
            cache[k] = (obj, cv)
            arch.append({"key": k, "tag": tag, "kind": kind, "seed": seed, "island": iid, "rule": show(ind["tree"]),
                         "ind": json.dumps({kk: (vv if kk != "tree" else None) for kk, vv in ind.items()}), "tree": repr(ind["tree"]),
                         **{f"f{i}": obj[i] for i in range(GA.NOBJ)}, "cv": cv, **{kk: v for kk, v in info.items() if kk != "inner_folds"}})
        return cache[k]
    if pop is None:
        pop = []
        while len(pop) < POP:
            x = rand_ind(rng, kind, Q)
            if valid(x):
                pop.append(x)
    E = [ev(x) for x in pop]
    for _ in range(gens):
        Fo = np.array([e[0] for e in E]); CV = np.array([e[1] for e in E])
        rank = GA.nd_sort(Fo, CV); crowd = GA.crowding(Fo, rank)
        kids = []
        while len(kids) < POP:
            i, j = rng.integers(len(pop), size=2); a = i if (rank[i], -crowd[i]) < (rank[j], -crowd[j]) else j
            i, j = rng.integers(len(pop), size=2); b = i if (rank[i], -crowd[i]) < (rank[j], -crowd[j]) else j
            x = cross(pop[a], pop[b], rng) if rng.random() < 0.7 else dict(pop[a])
            kids.append(mutate(x, rng, Q))
        KE = [ev(x) for x in kids]
        allp = pop + kids; allE = E + KE
        seen, keep = set(), []
        for i, x in enumerate(allp):
            k = key(x)
            if k not in seen:
                seen.add(k); keep.append(i)
        allp = [allp[i] for i in keep]; allE = [allE[i] for i in keep]
        Fo = np.array([e[0] for e in allE]); CV = np.array([e[1] for e in allE])
        rank = GA.nd_sort(Fo, CV); crowd = GA.crowding(Fo, rank)
        order = sorted(range(len(allp)), key=lambda i: (rank[i], -crowd[i]))[:POP]
        pop = [allp[i] for i in order]; E = [allE[i] for i in order]
    return pop, arch, [key(x) for x in pop]


def main():
    P = C.build_panel()
    bank = O.Bank(P)
    Fm, Fc = gp_features(bank)
    sess = bank.sess
    folds = []
    for name, s, e in C.OUTER:
        s0 = int(np.searchsorted(sess.values, np.datetime64(s))); s1 = int(np.searchsorted(sess.values, np.datetime64(e), side="right"))
        folds.append((name, (20, s0), (s0, s1)))
    folds.append(("FINAL_ALL_TO_2026-05-27", (20, bank.n), None))
    arch_all, sel = [], []
    t0 = time.time()
    with Pool(4, initializer=_init) as pool:
        for tag, win, test in folds:
            for kind in ("GP_MORNING", "GP_CLOSE"):
                args = [(sd, i, win, None, MIG, tag, kind) for sd in SEEDS for i in range(ISL)]
                out = pool.map(island, args)
                pops = [o[0] for o in out]
                for s_i in range(len(SEEDS)):
                    b = s_i * ISL
                    mig = [pops[b + i][:3] for i in range(ISL)]
                    for i in range(ISL):
                        pops[b + i] = pops[b + i][:POP - 3] + mig[(i - 1) % ISL]
                out2 = pool.map(island, [(sd, 100 + i, win, pops[s_i * ISL + i], GENS - MIG, tag, kind) for s_i, sd in enumerate(SEEDS) for i in range(ISL)])
                A = pd.DataFrame([r for o in out + out2 for r in o[1]]).drop_duplicates("key")
                A["fold"] = tag
                arch_all.append(A)
                finals = A[A.key.isin(set(k for o in out2 for k in o[2]))]
                rk = GA.nd_sort(finals[[f"f{i}" for i in range(GA.NOBJ)]].values, finals.cv.values)
                front = finals[rk == 0]
                best, ranked = GA.select(front)
                if best is None:
                    sel.append({"fold": tag, "kind": kind, "selected": None}); continue
                for rnk, (_, r) in enumerate(ranked.head(5).iterrows()):
                    ind = json.loads(r.ind); ind["tree"] = eval(r.tree)  # noqa: S307 (own repr of tuples)
                    o = {"fold": tag, "kind": kind, "sel_rank": rnk, "rule": r.rule, "ind": r.ind, "tree": r.tree, "inner_median": r.median_inner,
                         "inner_worst": r.worst_inner, "train_mdd": r.train_mdd, "train_smb": r.train_smb, "complexity": r.complexity}
                    if test is not None:
                        ge, mt, ct = to_overlay(ind, Fm, Fc)
                        m = np.zeros(bank.n, bool); m[test[0]:test[1]] = True
                        from t45_sim import metrics
                        ot = metrics(O.run(ge, bank, 1.0, mt, ct), bank.bench, m)
                        o.update({f"outer_{k}": ot[k] for k in ("avg", "total", "max_dd", "worst", "matched_beta_excess", "session_matched_beta_excess",
                                                                "incr_avg", "incr_max_dd", "corr_champion", "sides")})
                        o["degradation_outer_minus_inner_median"] = o["outer_avg"] - r.median_inner
                    sel.append(o)
                print(tag, kind, len(A), f"{time.time() - t0:.0f}s", sel[-5]["rule"] if "rule" in sel[-5] else "", flush=True)
    AR = pd.concat(arch_all, ignore_index=True); AR.to_parquet(f"{OUT}/T45_15_gp_archive.parquet")
    SEL = pd.DataFrame(sel); SEL.to_csv(f"{OUT}/T45_15_gp_selected.csv", index=False)
    json.dump({"unique_programs_total": int(AR.key.nunique()), "per_fold": AR.groupby(["fold", "kind"]).key.nunique().astype(int).to_dict().__repr__(),
               "POP": POP, "GENS": GENS, "SEEDS": SEEDS, "ISLANDS": ISL, "MAX_DEPTH": MAXD, "MAX_NODES": MAXN, "morning_inputs": M_IN,
               "close_inputs": C_IN, "primitives": ["GT", "LT", "AND", "OR", "NOT"]}, open(f"{OUT}/T45_15_gp_spec.json", "w"), indent=1)


if __name__ == "__main__":
    main()
