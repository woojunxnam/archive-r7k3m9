"""PH10B NR2_MAJOR stress + PH11 final synthesis + full-selection diagnostics (prereg 23be78a)."""
import glob
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

sys.path.insert(0, os.path.dirname(__file__))
import da_ph4 as P4  # noqa: E402
import da_ph9 as P9  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as RP  # noqa: E402
from rp_p6 import control_tables  # noqa: E402
from rp_p7 import MICRO  # noqa: E402
from rp_p9 import allocate, module_orders, stats  # noqa: E402

OUT = os.path.join(R.OUT, "ph11"); os.makedirs(OUT, exist_ok=True); NB = P.NB
SP = {"ES": 100, "NQ": 500, "YM": 1000, "RTY": 50}


def nr2_trades():
    M = P.markets(); rows = []
    for i in P.INSTS:
        m = M[i]; pc = np.concatenate([np.full((m.n, 1), np.nan), m.c[:, :-1]], 1); sp = SP[i]
        cross = (np.floor(m.c / sp) > np.floor(pc / sp)) & (m.bidx >= 1) & m.valid & (m.bidx <= 67); ev = cross & (np.cumsum(cross, 1) == 1); ss, bb = np.where(ev)
        rows.append(pd.DataFrame({"inst": i, "s": ss, "b": bb, "date": m.date[ss, bb], "year": m.year[ss, bb], "j_in": 5 * bb + 5, "j_out": 404, "px_in": m.entry[ss, bb],
                                  "px_out": m.I.FP[ss, 404], "px_in_d1": m.I.FP[ss, np.minimum(5 * bb + 10, 404)], "pv": m.I.pv, "cs": m.I.cs, "cs4": m.I.cs4}))
    return pd.concat(rows, ignore_index=True)


def main():
    c = EC.ctx(); w = c["win"]; yrs = c["sess"][w].year; mw = c["main"][w]; rm = EC.risk(mw)
    T = nr2_trades(); W = T[T.year >= 2021]; out = {}
    for tag, kw in (("base", {}), ("slip4", {"slip4": True}), ("delay1", {"delay": True}), ("missed20", {"missed": True})):
        d, nt, co = P4.capacity_daily(W, **kw); out[tag] = (d[w], nt)
    dw = out["base"][0]; r_ = EC.risk(dw); rc = EC.risk(mw + dw); top = np.sort(dw)[::-1]; fold = {k: float(dw[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in EC.FOLDS.items()}
    corr = float(np.corrcoef(dw, mw)[0, 1])
    st = {"trades": out["base"][1], "avg_day": r_["avg_day"], "slip4": float(out["slip4"][0].mean()), "delay1": float(out["delay1"][0].mean()), "missed20": float(out["missed20"][0].mean()),
          "remove_top3": float(dw.sum() - top[:3].sum()), "folds": fold, "folds_pos": int(sum(v > 0 for v in fold.values())), "y2022": float(dw[yrs == 2022].sum()), "max_dd": r_["max_dd"],
          "worst_day": r_["worst_day"], "corr_main": corr, "incr": rc["avg_day"] - rm["avg_day"], "comb_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"], "comb_max_dd": rc["max_dd"], "comb_worst": rc["worst_day"]}
    st["STRESS_PASS"] = bool(st["avg_day"] > 0 and st["slip4"] > 0 and st["delay1"] > 0 and st["missed20"] > 0 and st["remove_top3"] > 0 and st["folds_pos"] >= 3)
    st["ROUTE_A"] = bool(st["STRESS_PASS"] and st["incr"] >= 5 and rc["ret_dd"] >= rm["ret_dd"] and rc["max_dd"] <= 1.10 * rm["max_dd"] and rc["worst_day"] >= -5000)
    st["ROUTE_B"] = bool(st["STRESS_PASS"] and st["incr"] >= 1.5 and abs(corr) <= 0.35 and rc["ret_dd"] >= 1.02 * rm["ret_dd"] and rc["max_dd"] <= 1.03 * rm["max_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
    b5 = mw <= np.percentile(mw, 5); st["ROUTE_C"] = bool(st["incr"] >= -0.5 and (rc["max_dd"] <= 0.95 * rm["max_dd"] or (mw + dw)[b5].mean() >= mw[b5].mean() + 0.05 * abs(mw[b5].mean())) and rc["ret_dd"] > rm["ret_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
    C2 = pd.read_parquet(os.path.join(RP.OUT, "p6", "ARM_C2_P2_FAILED_FIRST_A_TAKE_ALL.parquet")); k2 = set(zip(C2.inst, C2.date)); st["overlap_with_C2_sessions"] = float(np.mean([(i, d) in k2 for i, d in zip(W.inst, W.date)]))
    print("NR2", json.dumps(st, default=float), flush=True)
    # ---------- PH11 final synthesis ----------
    Tctl = control_tables(); base = module_orders("C2_P2_FAILED_FIRST", False, Tctl); a1, a2 = P9.add_orders()
    nr2 = [dict(mod="NR2_MAJOR", key=f"NR2#{k}", parent=None, date=int(r.date), inst=r.inst, j_in=int(r.j_in), j_out=404, px_in=r.px_in, px_out=r.px_out, pv=r.pv, cs=r.cs, cs4=r.cs4, ctl=np.nan, year=int(r.year))
           for k, r in enumerate(W.itertuples(index=False))]
    c2opt = {"none": [], "C2": base, "C2+W1": base + a1, "C2+W1+W2": base + a1 + a2}; res = []; incs = {}
    n = len(c["sess"]); G = c["occ"]["MNQ"].shape[1]
    for (cn, co_), use_nr2 in itertools.product(c2opt.items(), (False, True)):
        orders = list(co_) + (nr2 if use_nr2 else []); name = "+".join([x for x in (cn if cn != "none" else "", "NR2" if use_nr2 else "") if x]) or "MAIN_ONLY"
        if orders:
            d, d4, dadd, dctl, cc = allocate(orders, {"C2_P2_FAILED_FIRST": 1, "NR2_MAJOR": 1}); dc = sum(d.values()); d4c = sum(d4.values())
        else:
            dc = d4c = dadd = dctl = np.zeros(n); cc = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}; d = {}
        o = {"portfolio": name, **stats(c["main"], dc, d4c, dadd, dctl, cc, [], c["occ"])}
        if len(d) == 2:
            a_, b_ = [v[w] for v in d.values()]; o["pair_corr"] = float(np.corrcoef(a_, b_)[0, 1])
        res.append(o); incs[name] = dc[w]
        print(name, round(o["avg_day"], 2), round(o["incr"], 2), round(o["max_dd"]), round(o["ret_dd"], 5), o["route_A"], o["route_B"], o["route_C"], flush=True)
    D = pd.DataFrame(res).set_index("portfolio"); D.to_csv(os.path.join(OUT, "PH11_PORTFOLIOS.csv"))
    mdd = D.loc["MAIN_ONLY", "max_dd"]; fr = {"FRONTIER_A": D[(D.max_dd <= 1.10 * mdd) & (D.worst_day >= -5000)].avg_day.idxmax(), "FRONTIER_B": D.ret_dd.idxmax(),
                                              "FRONTIER_C": D[D.incr > 0].max_dd.idxmin(), "FRONTIER_D": D[D.worst_day >= -5000].avg_day.idxmax()}
    # ---------- full-selection diagnostic (PH9 matrix + PH10 / PH11 series) ----------
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
    for dn, g in X4.groupby("def"):
        for ex in ("X60", "X120", "X1615", "XRES", "XSTRUCT"):
            gg = g[g[f"usd_{ex}"].notna()]; ser[f"PH4_{dn}_{ex}"] = EC.daily(gg.date.values, gg[f"usd_{ex}"].values)[w]
    ser["PH10_NR2_MAJOR"] = dw
    for k, v in incs.items():
        if k != "MAIN_ONLY":
            ser[f"PH11_{k}"] = v
    Mx = np.vstack([ser[k] for k in sorted(ser)] + [np.load(os.path.join(R.OUT, "ph6", "GENOME_WINDOW_DAILY.npy")).astype(float)]); Mx = Mx[Mx.std(1) > 0]
    Ntot = Mx.shape[0] + 2592 + 33 + 7; sel = fr["FRONTIER_B"]; x = incs[sel]
    srs = Mx.mean(1) / Mx.std(1); V = srs.var(ddof=1); g_ = 0.5772156649; sr = x.mean() / x.std()
    sr0 = np.sqrt(V) * ((1 - g_) * norm.ppf(1 - 1 / Ntot) + g_ * norm.ppf(1 - 1 / (Ntot * np.e)))
    dsr = float(norm.cdf((sr - sr0) * np.sqrt(len(x) - 1) / np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2)))
    pb = P9.pbo_blocks(Mx); rcp = P9.rc(Mx)
    diag = {"selected": sel, "series_in_matrix": int(Mx.shape[0]), "N_trials": int(Ntot), "daily_sharpe": float(sr), "sr0": float(sr0), "DSR": dsr, "PBO": pb, "reality_check_p": rcp,
            "status": "COMPUTED_WITH_LIMITATION (nested per-fold choices, 33 PH5 ML policies, 2,592 reclamation genomes and NR1 / NR3 counted in N only)"}
    R.append("OVERFIT_DIAGNOSTICS.csv", {"scope": f"FULL CHAIN FINAL -> {sel}", "trials": Ntot, "dsr": round(dsr, 4), "pbo": round(pb, 4), "reality_check_p": round(rcp, 4), "status": "COMPUTED_WITH_LIMITATION"})
    for k, v in fr.items():
        r = D.loc[v]; R.append("PORTFOLIO_FRONTIER.csv", {"frontier": f"FINAL_{k}", "members": "MAIN + " + v, "avg_day": round(r.avg_day, 2), "slip4_avg_day": round(r.slip4_avg_day, 2), "max_dd": round(r.max_dd),
                                                          "worst_day": round(r.worst_day), "ret_dd": round(r.ret_dd, 5), "gap_to_600": round(600 - r.avg_day, 2), "note": f"routes A={r.route_A} B={r.route_B} C={r.route_C}"})
    json.dump({"NR2_STRESS": st, "frontiers": fr, "diag": diag}, open(os.path.join(OUT, "PH11_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps({"frontiers": fr, "diag": diag}, indent=1, default=float))


if __name__ == "__main__":
    main()
