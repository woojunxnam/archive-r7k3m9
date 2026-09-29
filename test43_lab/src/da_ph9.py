"""PH9 portfolio synthesis + full-selection overfit diagnostics (prereg 6d83b2c)."""
import glob
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as RP  # noqa: E402
from rp_p6 import control_tables  # noqa: E402
from rp_p7 import MICRO, prep  # noqa: E402
from rp_p9 import allocate, module_orders, stats  # noqa: E402

OUT = os.path.join(R.OUT, "ph9"); os.makedirs(OUT, exist_ok=True); CAND = "C2_P2_FAILED_FIRST"
INDEP = ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"]


def add_orders():
    M = P.markets(); T = prep(pd.read_parquet(os.path.join(RP.OUT, "p6", "ARM_C2_P2_FAILED_FIRST_A_TAKE_ALL.parquet"))).reset_index(drop=True)
    E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet")); ind = E[E.candidate.isin(INDEP) & (E.year >= 2021)]
    ig = {k: set(g.b.values) for k, g in ind.groupby(["inst", "s"])}
    C = MG.checkpoints(T, min_left=30); C["is_indep"] = [k in ig.get((i, s), set()) for i, s, k in zip(C.inst, C.s, C.k)]
    a1, a2 = [], []
    for t, g in C.groupby("trade"):
        g = g.sort_values("k"); w = g[g.winner & ~g.is_indep]
        if not len(w):
            continue
        r = T.iloc[t]; m = M[r.inst]; s = int(r.s); k1 = int(w.iloc[0].k); p1 = m.I.FP[s, 5 * k1 + 5]
        base = dict(mod=CAND, date=int(r.date), inst=r.inst, j_out=int(r.j_out), px_out=r.px_out, pv=r.pv, cs=r.cs, cs4=r.cs4, ctl=np.nan, year=int(r.year))
        a1.append(dict(base, key=f"{CAND}#{t}+1", parent=f"{CAND}#{t}", j_in=5 * k1 + 5, px_in=p1))
        avg = (r.px_in + p1) / 2; later = g[(g.k > k1) & (np.array([m.c[s, int(k)] for k in g.k]) > avg)]
        if len(later):
            k2 = int(later.iloc[0].k); a2.append(dict(base, key=f"{CAND}#{t}+2", parent=f"{CAND}#{t}+1", j_in=5 * k2 + 5, px_in=m.I.FP[s, 5 * k2 + 5]))
    return a1, a2


def pbo_blocks(Mx, S=16):
    T = Mx.shape[1]; bl = np.array_split(np.arange(T), S); s1 = np.stack([Mx[:, b].sum(1) for b in bl], 1); s2 = np.stack([(Mx[:, b] ** 2).sum(1) for b in bl], 1); nb = np.array([len(b) for b in bl])
    lam = []
    for comb in itertools.combinations(range(S), S // 2):
        ci = list(comb); co = [k for k in range(S) if k not in comb]
        def sr(ix):
            n = nb[ix].sum(); mu = s1[:, ix].sum(1) / n; var = s2[:, ix].sum(1) / n - mu ** 2; return mu / np.sqrt(np.maximum(var, 1e-12))
        si, so = sr(ci), sr(co); best = np.argmax(si); w = ((so < so[best]).sum() + 1) / (len(so) + 1); lam.append(np.log(w / (1 - w)))
    return float(np.mean(np.array(lam) <= 0))


def rc(Mx, reps=1000, blk=10, seed=7):
    rng = np.random.default_rng(seed); T = Mx.shape[1]; mu = Mx.mean(1, keepdims=True); stat = np.sqrt(T) * mu.max(); Z = (Mx - mu).astype(np.float32); cnt = 0
    for _ in range(reps):
        idx = np.empty(T, int); t = rng.integers(T)
        for k in range(T):
            idx[k] = t; t = rng.integers(T) if rng.random() < 1 / blk else (t + 1) % T
        cnt += np.sqrt(T) * Z[:, idx].mean(1).max() >= stat
    return float(cnt / reps)


def main():
    c = EC.ctx(); w = c["win"]; Tctl = control_tables(); base = module_orders(CAND, False, Tctl); a1, a2 = add_orders()
    opts = {"C2": base, "C2+W1": base + a1, "C2+W1+W2": base + a1 + a2}; res = []; incs = {}
    n = len(c["sess"]); G = c["occ"]["MNQ"].shape[1]
    z = np.zeros(n); co0 = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}
    o = {"portfolio": "MAIN_ONLY", **stats(c["main"], z, z, z, z, co0, [], c["occ"])}; res.append(o)
    for nm, L in itertools.product(opts, (1, 2)):
        d, d4, dadd, dctl, co = allocate(opts[nm], {CAND: L}); dc = sum(d.values()); d4c = sum(d4.values())
        o = {"portfolio": f"{nm}x{L}", **stats(c["main"], dc, d4c, dadd, dctl, co, [], c["occ"])}; res.append(o); incs[f"{nm}x{L}"] = dc[w]
        print(o["portfolio"], round(o["avg_day"], 2), round(o["incr"], 2), round(o["max_dd"]), round(o["ret_dd"], 5), o["route_A"], o["route_B"], round(o["add_units_avg_day"], 2), flush=True)
    D = pd.DataFrame(res).set_index("portfolio"); D.to_csv(os.path.join(OUT, "PH9_PORTFOLIOS.csv"))
    mdd = D.loc["MAIN_ONLY", "max_dd"]; A = D[(D.max_dd <= 1.10 * mdd) & (D.worst_day >= -5000)].avg_day.idxmax(); Bf = D.ret_dd.idxmax(); Cf = D[D.incr > 0].max_dd.idxmin(); Df = D[D.worst_day >= -5000].avg_day.idxmax()
    fr = {"FRONTIER_A": A, "FRONTIER_B": Bf, "FRONTIER_C": Cf, "FRONTIER_D": Df}
    # ---------- full-selection diagnostic ----------
    ser = {}
    E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet"))
    for f in glob.glob(os.path.join(RP.OUT, "ml", "TRADES_*.parquet")):
        X = pd.read_parquet(f); ser["REC_" + os.path.basename(f)[7:-8]] = EC.daily(X.date.values, X.usd.values)[w]
    for cnd, g in E[E.usd_h1615.notna() & (E.year >= 2021)].groupby("candidate"):
        ser[f"REC_TAKEALL_{cnd}"] = EC.daily(g.date.values, g.usd_h1615.values)[w]
    for f in glob.glob(os.path.join(RP.OUT, "ga", "GA_TRADES_*.parquet")):
        X = pd.read_parquet(f); ser["REC_" + os.path.basename(f)[:-8]] = EC.daily(X.date.values, X.usd.values)[w]
    for f in glob.glob(os.path.join(RP.OUT, "p8", "MGMT_*.parquet")):
        X = pd.read_parquet(f); nm = os.path.basename(f)[5:-8]
        for arm in ("B_BLIND_DCA", "C_FRESH_RECOVERY", "D_WINNER_PYRAMID"):
            ser[f"REC_MGMT_{nm}_{arm}"] = EC.daily(X.date.values, (X.unit1 + X[f"{arm}_add"].fillna(0)).values)[w]
    zz = np.load(os.path.join(RP.OUT, "p9", "P9_DAILY.npz"))
    for k in zz.files:
        if k != "MAIN_ONLY":
            ser[f"REC_P9_{k}"] = zz[k][w]
    X4 = pd.read_parquet(os.path.join(R.OUT, "ph4", "PH4_EXIT_DATASET.parquet")); X4 = X4[X4.year >= 2021]
    for (dn, ), g in X4.groupby(["def"]):
        for ex in ("X60", "X120", "X1615", "XRES", "XSTRUCT"):
            gg = g[g[f"usd_{ex}"].notna()]; ser[f"PH4_{dn}_{ex}"] = EC.daily(gg.date.values, gg[f"usd_{ex}"].values)[w]
    for k, v in incs.items():
        ser[f"PH9_{k}"] = v
    names = sorted(ser); Mx = np.vstack([ser[k] for k in names]); GM = np.load(os.path.join(R.OUT, "ph6", "GENOME_WINDOW_DAILY.npy")).astype(float)
    Mx = np.vstack([Mx, GM]); Mx = Mx[Mx.std(1) > 0]; Ntot = Mx.shape[0] + 2592 + 33
    sel = fr["FRONTIER_B"] if fr["FRONTIER_B"] != "MAIN_ONLY" else fr["FRONTIER_A"]; x = incs.get(sel, np.zeros(w.sum()))
    srs = Mx.mean(1) / Mx.std(1); V = srs.var(ddof=1); g_ = 0.5772156649; sr = x.mean() / x.std() if x.std() > 0 else 0
    sr0 = np.sqrt(V) * ((1 - g_) * norm.ppf(1 - 1 / Ntot) + g_ * norm.ppf(1 - 1 / (Ntot * np.e)))
    dsr = float(norm.cdf((sr - sr0) * np.sqrt(len(x) - 1) / np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2)))
    pb = pbo_blocks(Mx); rcp = rc(Mx)
    diag = {"selected": sel, "series_in_matrix": int(Mx.shape[0]), "N_trials": int(Ntot), "daily_sharpe": float(sr), "sr0": float(sr0), "DSR": dsr, "PBO": pb, "reality_check_p": rcp,
            "status": "COMPUTED_WITH_LIMITATION (nested per-fold choices and 33 PH5 ML policies and 2,592 reclamation genomes counted in N only)"}
    R.append("OVERFIT_DIAGNOSTICS.csv", {"scope": f"FULL CHAIN (reclamation + discretionary) -> {sel}", "trials": Ntot, "dsr": round(dsr, 4), "pbo": round(pb, 4), "reality_check_p": round(rcp, 4), "status": "COMPUTED_WITH_LIMITATION"})
    for k, v in fr.items():
        r = D.loc[v]; R.append("PORTFOLIO_FRONTIER.csv", {"frontier": k, "members": "MAIN + " + v, "avg_day": round(r.avg_day, 2), "slip4_avg_day": round(r.slip4_avg_day, 2), "max_dd": round(r.max_dd),
                                                          "worst_day": round(r.worst_day), "ret_dd": round(r.ret_dd, 5), "gap_to_600": round(600 - r.avg_day, 2), "note": f"routes A={r.route_A} B={r.route_B} C={r.route_C}"})
    json.dump({"frontiers": fr, "diag": diag}, open(os.path.join(OUT, "PH9_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps({"frontiers": fr, "diag": diag}, indent=1, default=float))


if __name__ == "__main__":
    main()
