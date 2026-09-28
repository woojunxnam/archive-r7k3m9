"""TEST47 GA (T47_33 .. T47_38): three SEPARATE nested chronological island NSGA-II lanes over NASSI path grammar.
  GA-N3  entry-sequence grammar (leg definition, normalised size, leg count, sideways / up-bar handling, max duration,
         prior-rally, crash veto, deceleration, 15m confirmation, entry form, exit, instrument)
  GA-NB  bottom confirmation on the FIXED predeclared C2 sequence (window, extension tolerance, wick, close improvement,
         bullish-bar requirement, deceleration, veto, exit, instrument)
  GA-NR  inventory recycle on the FIXED C2 sequence (entry E1/NB, add mode, blind distance, trim, trim size, rebuild,
         campaign exit, recovery fraction, instrument)
Same nested design as TEST45/46: evolution sees only sessions before each outer block (2021, 2022, 2023, 2024, 2025-26);
fitness (minimised) = [-median inner-fold $/day, -worst inner-fold $/day, training MaxDD, -matched-long excess $/day
(GA-NR: -incremental $/day over R0 on the same entries), complexity]; constraints >= 60 trades in training, |corr C43| <= 0.6.
Per-fold selection (predeclared, identical to TEST45/46): feasible rank-0, worst inner > 0, max median/max(MDD, 1000)."""
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
import t47_common as C  # noqa: E402
import t47_engine as E  # noqa: E402
from t47_02_n3 import START, cfg, ctx15  # noqa: E402

OUT = os.path.join(C.T47, "ga"); os.makedirs(OUT, exist_ok=True)
POP, GENS, MIG, NMIG = 48, 26, 13, 4
SEEDS = (11, 22); ISL = 3; INNER = 4; NOBJ = 5
EXITS = ["X30", "X60", "X120", "X1600", "REC50"]
SPACES = {
    "N3": [("inst", "cat", ["ES", "MNQ"]), ("leg", "cat", ["T1", "T2", "T3", "T4"]), ("xm", "num", (0.5, 2.0)), ("ntick", "cat", [2, 3, 4]),
           ("side", "cat", ["KEEP", "DECAY", "RESET"]), ("side_n", "cat", [3, 6]), ("up", "cat", ["KEEP", "DECAY", "RESET"]), ("up_frac", "cat", [0.5, 1.0]),
           ("maxdur", "cat", [12, 24, 36]), ("rally", "cat", ["NONE", "NOTRADE", "CONFIRM15"]), ("veto", "cat", [0, 1]), ("decel", "cat", [0, 1]),
           ("c15", "cat", [0, 1]), ("entry", "cat", ["E1", "E2", "E3", "E4", "E5", "NB"]), ("exit", "cat", EXITS)],
    "NB": [("inst", "cat", ["ES", "MNQ"]), ("win", "cat", [3, 6, 9]), ("tol", "num", (0.0, 0.75)), ("wick", "num", (0.1, 0.6)), ("ci", "cat", [0, 1]),
           ("bull", "cat", [0, 1]), ("decel", "cat", [0, 1]), ("veto", "cat", [0, 1]), ("exit", "cat", EXITS)],
    "NR": [("inst", "cat", ["ES", "MNQ"]), ("entry", "cat", ["E1", "NB"]), ("add", "cat", ["none", "confirmed", "blind"]), ("blind_x", "num", (1.0, 3.0)),
           ("trim", "cat", [0, 1]), ("trim_x", "num", (0.5, 2.0)), ("rebuild", "cat", [0, 1]), ("exit", "cat", ["X60", "X120", "REC50", "X1615"]),
           ("rec_frac", "num", (0.3, 0.75))],
}
_ctx = {}


def _init():
    es, nq = E.setup()
    champ = C45.champion_daily().pnl.reindex(es.pn.sess).fillna(0.0).values
    base = {}
    for mk in (es, nq):
        bl = E.Baseline(mk)
        for ex in EXITS + ["X1615"]:
            base[(mk.inst, ex)] = bl.table(ex)[0]
    c2 = {}
    for mk in (es, nq):
        ev, cnt, legm = E.run_detect(mk, cfg())
        ev = ev[mk.pn.sess[ev.s.values] >= START].reset_index(drop=True)
        c2[mk.inst] = (ev, legm)
    _ctx.update(mk={"ES": es, "MNQ": nq}, champ=champ, base=base, c2=c2, r0={})


def nb_fill(mk, ev, win, tol, wick, ci, bull):
    j = np.full(len(ev), -1, np.int64)
    for i, (s, b, st) in enumerate(zip(ev.s.values, ev.b.values, ev.start.values)):
        lo = np.nanmin(mk.l[s, max(st - 1, 0):b + 1])
        for k in range(b + 1, min(b + 1 + win, E.NB)):
            if np.isnan(mk.c[s, k]):
                continue
            r = mk.h[s, k] - mk.l[s, k]
            wk = (min(mk.o[s, k], mk.c[s, k]) - mk.l[s, k]) / r if r > 0 else 0
            okc = (mk.c[s, k] >= mk.c[s, k - 1]) or not ci
            okb = (mk.c[s, k] > mk.o[s, k]) if bull else (wk >= wick or mk.c[s, k] > mk.o[s, k])
            if mk.l[s, k] >= lo - tol * mk.u5[s] and okc and okb:
                j[i] = 5 * (k + 1); break
            lo = min(lo, mk.l[s, k])
    return np.where((j > 0) & (j <= E.J_LAST_ENTRY), j, -1)


def veto_mask(mk, ev):
    return ((ev.leg3 >= 2.0 * ev.leg2) | (ev.cum >= 10) | (mk.gap[ev.s.values] <= -1.5) | (mk.ret5[ev.s.values] <= -3.0)
            | (mk.volt[ev.s.values] >= 0.9)).values


def trades_from_j(mk, ev, j, rule, slip=1.0):
    jx = E.exit_index(mk, ev, j, rule)
    s = ev.s.values; cs = C45.cost_side(mk.k, slip)
    ok = (j >= 0) & (jx >= 0)
    s, j, jx = s[ok], j[ok], jx[ok]
    pnl = (mk.FPb[s, jx] - mk.FP[s, j]) * mk.pv - 2 * cs
    o = np.lexsort((j, s)); s, j, jx, pnl = s[o], j[o], jx[o], pnl[o]
    keep = np.zeros(len(s), bool); ls, lx = -1, -1
    for i in range(len(s)):
        if s[i] != ls:
            ls, lx = s[i], -1
        if j[i] >= lx and not np.isnan(pnl[i]):
            keep[i] = True; lx = jx[i]
    return s[keep], j[keep], jx[keep], pnl[keep]


def run(lane, g, slip=1.0):
    """returns daily pnl, daily 'excess' (matched-long or incremental over R0), #trades."""
    mk = _ctx["mk"][g["inst"]]
    n = mk.n
    if lane == "N3":
        leg = g["leg"]
        p = cfg(leg=leg, x=C.SPEC["x_default"][leg] * g["xm"], ntick=g["ntick"], side=[g["side"], g["side_n"] if g["side"] != "KEEP" else 0],
                up=[g["up"], g["up_frac"]], maxdur=g["maxdur"])
        ev, _, _ = E.run_detect(mk, p)
        ev = ev[mk.pn.sess[ev.s.values] >= START].reset_index(drop=True)
        m = np.ones(len(ev), bool)
        if g["veto"] and len(ev):
            m &= ~veto_mask(mk, ev)
        if g["decel"] and len(ev) and g["ntick"] >= 3:
            m &= (ev.leg3 <= ev.leg2).values
        if (g["c15"] or g["rally"] != "NONE") and len(ev):
            _, b15 = ctx15(mk, ev)
            large = (ev.rally30 >= 4.0).values
            if g["c15"]:
                m &= b15
            if g["rally"] == "NOTRADE":
                m &= ~large
            elif g["rally"] == "CONFIRM15":
                m &= (~large) | b15
        ev = ev[m].reset_index(drop=True)
        j = E.entry_fill(mk, ev, g["entry"]) if len(ev) else np.zeros(0, np.int64)
        rule = g["exit"]
    elif lane == "NB":
        ev = _ctx["c2"][g["inst"]][0]
        m = np.ones(len(ev), bool)
        if g["veto"]:
            m &= ~veto_mask(mk, ev)
        if g["decel"]:
            m &= (ev.leg3 <= ev.leg2).values
        ev = ev[m].reset_index(drop=True)
        j = nb_fill(mk, ev, g["win"], g["tol"], g["wick"], g["ci"], g["bull"])
        rule = g["exit"]
    else:
        ev, legm = _ctx["c2"][g["inst"]]
        L, Cm = E.run_campaign(mk, ev, legm, entry=g["entry"], exit=g["exit"], rec_frac=g["rec_frac"], add=g["add"], blind_x=g["blind_x"],
                               trim=bool(g["trim"]), trim_x=g["trim_x"], rebuild=bool(g["rebuild"]), slip=slip)
        d = np.zeros(n); np.add.at(d, L.acct_s.values.astype(int), L.pnl.values)
        kk = (g["inst"], g["entry"], g["exit"], round(g["rec_frac"], 2), slip)
        if kk not in _ctx["r0"]:
            L0, _ = E.run_campaign(mk, ev, legm, entry=g["entry"], exit=g["exit"], rec_frac=g["rec_frac"], slip=slip)
            d0 = np.zeros(n); np.add.at(d0, L0.acct_s.values.astype(int), L0.pnl.values)
            _ctx["r0"][kk] = d0
        return d, d - _ctx["r0"][kk], len(Cm)
    if len(ev) == 0:
        return np.zeros(n), np.zeros(n), 0
    s, j, jx, pnl = trades_from_j(mk, ev, j, rule, slip)
    d = np.zeros(n); np.add.at(d, s, pnl)
    M = _ctx["base"][(g["inst"], rule if rule in EXITS else "X60")]
    return d, (s, j, pnl, M), len(s)


def excess_daily(n, exc, s0, s1, fold_base_rows):
    s, j, pnl, M = exc
    bl = np.nanmean(M[fold_base_rows[0]:fold_base_rows[1]], axis=0)
    x = np.zeros(n); np.add.at(x, s, pnl - np.nan_to_num(bl[j]))
    return x[s0:s1]


def complexity(lane, g):
    if lane == "N3":
        return int(1 + (g["side"] != "KEEP") + (g["up"] != "KEEP") + (g["rally"] != "NONE") + g["veto"] + g["decel"] + g["c15"]
                   + (g["entry"] != "E1") + (g["leg"] == "T4"))
    if lane == "NB":
        return int(1 + g["ci"] + g["bull"] + g["decel"] + g["veto"] + (g["tol"] > 0.05))
    return int(1 + (g["add"] != "none") + 2 * (g["add"] == "blind") + g["trim"] + g["rebuild"] + (g["entry"] == "NB"))


def fitness(lane, g, win):
    d, exc, ntr = run(lane, g)
    s0, s1 = win
    x = d[s0:s1]
    xe = exc[s0:s1] if lane == "NR" else excess_daily(len(d), exc, s0, s1, (s0, s1)) if ntr else np.zeros(s1 - s0)
    ntr_w = int((x != 0).sum())
    chunks = np.array_split(np.arange(len(x)), INNER)
    fa = np.array([x[c].mean() for c in chunks])
    eq = np.r_[0.0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    ch = _ctx["champ"][s0:s1]
    corr = float(np.corrcoef(ch, x)[0, 1]) if x.std() > 0 else 0.0
    cx = complexity(lane, g)
    obj = np.array([-np.median(fa), -fa.min(), mdd, -xe.mean(), cx], float)
    cv = max(0, 60 - ntr_w) / 60 + max(0.0, abs(corr) - 0.6)
    return obj, cv, {"median_inner": float(np.median(fa)), "worst_inner": float(fa.min()), "train_avg": float(x.mean()), "train_mdd": mdd,
                     "train_excess_day": float(xe.mean()), "train_days_active": ntr_w, "corr": corr, "complexity": cx}


def rand_gene(rng, spec):
    nm, t, d = spec
    if t == "cat":
        return d[rng.integers(len(d))]
    return float(rng.uniform(*d))


def key(g):
    return json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in g.items()}, sort_keys=True, default=str)


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


def native(v):
    return v.item() if hasattr(v, "item") else v


def island(args):
    lane, seed, iid, win, pop, gens, tag = args
    space = SPACES[lane]
    rng = np.random.default_rng(seed * 1000 + iid)
    cache, arch = {}, []

    def ev_(gn):
        gn = {k: native(v) for k, v in gn.items()}
        kk = key(gn)
        if kk not in cache:
            obj, cv, info = fitness(lane, gn, win)
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


def outer_eval(lane, g, s0, s1):
    d, exc, ntr = run(lane, g)
    x = d[s0:s1]
    xe = exc[s0:s1] if lane == "NR" else (excess_daily(len(d), exc, s0, s1, (20, s0)) if ntr else np.zeros(s1 - s0))
    eq = np.r_[0.0, np.cumsum(x)]
    return {"outer_avg": float(x.mean()), "outer_total": float(x.sum()), "outer_days_active": int((x != 0).sum()),
            "outer_mdd": float((np.maximum.accumulate(eq) - eq).max()), "outer_excess_day": float(xe.mean()),
            "outer_corr_C43": float(np.corrcoef(_ctx["champ"][s0:s1], x)[0, 1]) if x.std() > 0 else np.nan}


def cluster(lane, g):
    if lane == "N3":
        return f"{g['inst']}|{g['leg']}|n{g['ntick']}|{g['entry']}|{g['exit']}"
    if lane == "NB":
        return f"{g['inst']}|bull{g['bull']}|decel{g['decel']}|veto{g['veto']}|{g['exit']}"
    return f"{g['inst']}|{g['entry']}|{g['add']}|trim{g['trim']}|reb{g['rebuild']}|{g['exit']}"


def main(lanes=("N3", "NB", "NR")):
    _init()
    sess = _ctx["mk"]["ES"].pn.sess
    folds = []
    for name, s, e in C45.OUTER:
        s0 = int(np.searchsorted(sess.values, np.datetime64(s))); s1 = int(np.searchsorted(sess.values, np.datetime64(e), side="right"))
        folds.append((name, (20, s0), (s0, s1)))
    folds.append(("FINAL_ALL_TO_2026-05-27", (20, len(sess)), None))
    spec = {"POP": POP, "GENS": GENS, "SEEDS": SEEDS, "ISLANDS": ISL, "spaces": {k: [(a, b, str(c)) for a, b, c in v] for k, v in SPACES.items()}, "unique": {}}
    with Pool(4, initializer=_init) as pool:
        for lane in lanes:
            sel = []
            for tag, win, test in folds:
                t0 = time.time()
                out = pool.map(island, [(lane, sd, i, win, None, MIG, tag) for sd in SEEDS for i in range(ISL)])
                pops = [o[0] for o in out]
                for si in range(len(SEEDS)):
                    b = si * ISL; mig = [pops[b + i][:NMIG] for i in range(ISL)]
                    for i in range(ISL):
                        pops[b + i] = pops[b + i][:POP - NMIG] + [dict(x) for x in mig[(i - 1) % ISL]]
                out2 = pool.map(island, [(lane, sd, 100 + i, win, pops[si * ISL + i], GENS - MIG, tag) for si, sd in enumerate(SEEDS) for i in range(ISL)])
                A = pd.DataFrame([r for o in out + out2 for r in o[1]]).drop_duplicates("key"); A["fold"] = tag
                fin = A[A.key.isin(set(k for o in out2 for k in o[2]))]
                rk = G45.nd_sort(fin[[f"f{i}" for i in range(NOBJ)]].values, fin.cv.values)
                front = fin[rk == 0].copy()
                best, ranked = G45.select(front)
                A.to_parquet(f"{OUT}/archive_{lane}_{tag}.parquet"); front.to_parquet(f"{OUT}/front_{lane}_{tag}.parquet")
                spec["unique"][f"{lane}_{tag}"] = int(A.key.nunique())
                if best is None:
                    sel.append({"lane": lane, "fold": tag, "sel_rank": 0, "selected": "NONE (no feasible front member with worst inner > 0)"})
                else:
                    for rnk, (_, r) in enumerate(ranked.head(5).iterrows()):
                        g = json.loads(r.genome)
                        o = {"lane": lane, "fold": tag, "sel_rank": rnk, "genome": r.genome, "cluster": cluster(lane, g), "inner_median": r.median_inner,
                             "inner_worst": r.worst_inner, "train_mdd": r.train_mdd, "train_excess_day": r.train_excess_day, "complexity": r.complexity}
                        if test is not None:
                            o.update(outer_eval(lane, g, *test))
                        sel.append(o)
                print(lane, tag, len(A), f"{time.time() - t0:.0f}s", flush=True)
            S = pd.DataFrame(sel); S.to_csv(f"{OUT}/T47_GA_{lane}_selected.csv", index=False)
            print(S.drop(columns=["genome"], errors="ignore").round(2).to_string(), flush=True)
    json.dump(spec, open(f"{OUT}/T47_33_ga_spec.json", "w"), indent=1)


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("N3", "NB", "NR"))
