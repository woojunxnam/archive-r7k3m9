"""PH5 action values, response-speed management, discretionary-emulator ML (prereg 89d85e2)."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_bank as B  # noqa: E402
import rp_econ as EC  # noqa: E402

OUT = os.path.join(R.OUT, "ph5"); os.makedirs(OUT, exist_ok=True)
ATL = ["up_room", "down_room", "no_res", "conf_sup_15", "sup_type", "sup_touch", "sup_age"]; STATE = ["ret", "mfe", "mae", "newhigh", "elapsed", "remaining", "retain"]
GRID = {"RIDGE": [1, 10, 100, 1000], "ENET": [0.01, 0.1, 1], "LOGIT": [0.01, 0.1, 1], "HGB": [100, 200], "HGBCLS": [100, 200]}


def mdl(kind, hp):
    return {"RIDGE": lambda: Ridge(alpha=hp), "ENET": lambda: ElasticNet(alpha=hp, l1_ratio=0.5, max_iter=5000), "LOGIT": lambda: LogisticRegression(C=hp, max_iter=2000),
            "HGB": lambda: HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, min_samples_leaf=50, l2_regularization=1.0, max_iter=hp, random_state=7),
            "HGBCLS": lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, min_samples_leaf=50, l2_regularization=1.0, max_iter=hp, random_state=7)}[kind]()


def prep_x(Xtr, Xte):
    Xtr = Xtr.replace([np.inf, -np.inf], np.nan); Xte = Xte.replace([np.inf, -np.inf], np.nan); med = Xtr.median().fillna(0); A = Xtr.fillna(med); mu = A.mean(); sd = A.std().replace(0, 1).fillna(1)
    return ((A - mu) / sd).values, ((Xte.fillna(med) - mu) / sd).values


def fitpred(kind, hp, Xtr, y, Xte):
    A, T = prep_x(Xtr, Xte)
    if kind in ("LOGIT", "HGBCLS"):
        m = mdl(kind, hp).fit(A, (y > 0).astype(int)); return m.predict_proba(A)[:, 1], m.predict_proba(T)[:, 1]
    sy = y.std() if kind == "ENET" else 1.0; m = mdl(kind, hp).fit(A, y / sy); return m.predict(A), m.predict(T)


def nested(D, cols, ycol, kind, rule):
    """returns test rows with policy decision; rule: ('top', frac) or ('zero',)."""
    outs = []
    for f, ye in EC.TRAIN_END.items():
        a, b = EC.FOLDS[f]; tr = D[D.year <= ye]; te = D[(D.year >= a) & (D.year <= b)]
        if len(tr) < 100 or not len(te):
            continue
        ly = tr.year.max(); ti, va = tr[tr.year < ly], tr[tr.year == ly]; best, bv = GRID[kind][len(GRID[kind]) // 2], -np.inf
        if len(ti) >= 100 and len(va) >= 20:
            for hp in GRID[kind]:
                s_tr, s_va = fitpred(kind, hp, ti[cols], ti[ycol].values, va[cols])
                sel = s_va >= np.quantile(s_tr, 1 - rule[1]) if rule[0] == "top" else (s_va > (0.5 if kind in ("LOGIT", "HGBCLS") else 0))
                v = va[ycol].values[sel].sum()
                if v > bv:
                    bv, best = v, hp
        s_tr, s_te = fitpred(kind, best, tr[cols], tr[ycol].values, te[cols])
        dec = s_te >= np.quantile(s_tr, 1 - rule[1]) if rule[0] == "top" else (s_te > (0.5 if kind in ("LOGIT", "HGBCLS") else 0))
        t = te.copy(); t["dec"] = dec; t["score"] = s_te; t["fold"] = f; outs.append(t)
    return pd.concat(outs) if outs else None


def daily_stats(dates, usd, usd4=None):
    c = EC.ctx(); w = c["win"]; yrs = c["sess"][w].year; d = EC.daily(dates, usd)[w]
    fold = {k: float(d[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in EC.FOLDS.items()}
    o = {"value_day": float(d.mean()), "folds_pos": int(sum(v > 0 for v in fold.values())), "worst_fold": float(min(fold.values())), "n": int(len(usd))}
    if usd4 is not None:
        o["slip4_value_day"] = float(EC.daily(dates, usd4)[w].mean())
    return o


def main():
    M = P.markets(); X = pd.read_parquet(os.path.join(R.OUT, "ph4", "PH4_EXIT_DATASET.parquet")); parts = []
    for i in P.INSTS:
        F = B.features(M[i]); xi = X[X.inst == i].copy()
        for k in B.FEATS:
            xi[k] = F[k][xi.s.values, xi.b.values]
        parts.append(xi)
    X = pd.concat(parts, ignore_index=True)
    for i in P.INSTS:
        X[f"inst_{i}"] = (X.inst == i).astype(float)
    EF = B.FEATS + [f"inst_{i}" for i in P.INSTS] + ATL
    res = []; av = []
    # ---------- ENTRY ----------
    for pop, defs in (("D2", ["D2"]), ("D3", ["D3"]), ("D7", ["D7"]), ("D8", ["D8"]), ("C2", ["D1B", "D1B_P"])):
        D = X[X["def"].isin(defs) & X.usd_X1615.notna()].copy()
        D["y"] = D.usd_X1615; W = D[D.year >= 2021]; base = daily_stats(W.date.values, W.usd_X1615.values, W.usd4_X1615.values)
        av.append({"action": "ENTRY_TAKE_ALL", "population": pop, **base})
        for kind in ("RIDGE", "LOGIT", "HGB"):
            T = nested(D, EF, "y", kind, ("top", 0.5)); S = T[T.dec]
            o = daily_stats(S.date.values, S.usd_X1615.values, S.usd4_X1615.values); inc = o["value_day"] - base["value_day"]
            res.append({"task": "E", "population": pop, "config": f"{kind}_TOP50", **o, "incr_vs_take_all": inc})
            R.append("ML_LEDGER.csv", {"task": "E", "population": pop, "config": f"{kind}_TOP50", "stitched_value_day": round(o["value_day"], 3), "slip4_value_day": round(o["slip4_value_day"], 3),
                                       "folds_pos": o["folds_pos"], "n": o["n"], "note": f"take-all {base['value_day']:.2f}"})
        print("E", pop, round(base["value_day"], 2), [round(r["value_day"], 2) for r in res[-3:]], flush=True)
    # ---------- HOLD (response speed) ----------
    C2 = X[X["def"].isin(["D1B", "D1B_P"])].copy(); rows = []
    for r in C2.itertuples(index=False):
        m = M[r.inst]; I = m.I; s = int(r.s)
        for t in (2, 4, 6):
            k = int(r.b) + t; ja = 5 * k + 5
            if ja >= 404:
                continue
            hi = np.nanmax(I.H[s, 5 * r.b + 5:ja]); lo = np.nanmin(I.L[s, 5 * r.b + 5:ja]); c = m.c[s, k]
            d = {kk: getattr(r, kk) for kk in EF if not kk.startswith("inst_")}
            d.update({"t": t, "date": r.date, "year": r.year, "inst": r.inst, "ret": (c - r.entry) / r.atr, "mfe": (hi - r.entry) / r.atr, "mae": (r.entry - lo) / r.atr,
                      "newhigh": float(hi > m.h[s, int(r.b)]), "elapsed": t, "remaining": (404 - ja) / 5, "retain": float(c > r.struct_level) if r.struct_level == r.struct_level else np.nan,
                      "hold": (r.px_X1615 - I.FP[s, ja]) * r.pv})
            rows.append(d)
    H = pd.DataFrame(rows)
    for i in P.INSTS:
        H[f"inst_{i}"] = (H.inst == i).astype(float)
    HF = EF + STATE; curves = []
    for t in (2, 4, 6):
        Ht = H[H.t == t]; W = Ht[Ht.year >= 2021]
        rule = W[W.ret <= 0]; o = daily_stats(rule.date.values, -rule.hold.values)
        av.append({"action": f"EXIT_IF_NOT_WORKING_{5*t}m", "population": "C2", **o})
        # response curve of hold value by quintile of current return (full sample, causal-free descriptive quintiles on training-free pooled data)
        q = pd.qcut(W.ret, 5, labels=False, duplicates="drop"); bm = W.groupby(q).hold.mean().values
        curves.append({"checkpoint_min": 5 * t, "hold_by_ret_quintile": [round(v, 2) for v in bm], "spearman": float(spearmanr(range(len(bm)), bm)[0])})
        for kind in ("RIDGE", "LOGIT", "HGB"):
            T = nested(Ht, HF, "hold", kind, ("zero",)); S = T[~T.dec & (T.year >= 2021)]       # dec = predicted hold > 0 -> exit where not
            o = daily_stats(S.date.values, -S.hold.values)
            res.append({"task": "H", "population": f"C2_{5*t}m", "config": kind, **o})
            R.append("ML_LEDGER.csv", {"task": "H", "population": f"C2_{5*t}m", "config": kind, "stitched_value_day": round(o["value_day"], 3), "slip4_value_day": "", "folds_pos": o["folds_pos"], "n": o["n"], "note": "incremental of early exits"})
        print("H", t, [round(r["value_day"], 2) for r in res[-3:]], flush=True)
    # ---------- ADD ----------
    Tt = C2[C2.year >= 2019].copy(); Tt["j_in"] = 5 * Tt.b + 5; Tt["j_out"] = 404; Tt["px_in"] = Tt.entry; Tt["px_out"] = Tt.px_X1615
    Ck = MG.checkpoints(Tt.reset_index(drop=True), min_left=30); Ck["add"] = Ck.add_usd
    for i in P.INSTS:
        Ck[f"inst_{i}"] = (Ck.inst == i).astype(float)
    AF = ["elapsed", "remaining", "upnl_atr", "mfe_atr", "mae_atr", "sess_ret", "vt", "tod3"] + [f"inst_{i}" for i in P.INSTS]
    for sub, msk in (("WINNER", Ck.winner), ("UNDERWATER", Ck.under)):
        Cs = Ck[msk].copy()
        for kind in ("RIDGE", "LOGIT", "HGB"):
            T = nested(Cs, AF, "add", kind, ("zero",)); S = T[T.dec & (T.year >= 2021)].sort_values(["trade", "k"]).groupby("trade").head(1)
            o = daily_stats(S.date.values, S.add_usd.values, S.add_usd4.values)
            res.append({"task": "A", "population": f"C2_{sub}", "config": kind, **o})
            R.append("ML_LEDGER.csv", {"task": "A", "population": f"C2_{sub}", "config": kind, "stitched_value_day": round(o["value_day"], 3), "slip4_value_day": round(o["slip4_value_day"], 3), "folds_pos": o["folds_pos"], "n": o["n"], "note": "ADD1 first positive-prediction checkpoint"})
        first = Cs[Cs.year >= 2021].sort_values(["trade", "k"]).groupby("trade").head(1); o = daily_stats(first.date.values, first.add_usd.values, first.add_usd4.values)
        av.append({"action": f"ADD1_FIRST_{sub}_GENERIC", "population": "C2", **o})
        print("A", sub, [round(r["value_day"], 2) for r in res[-3:]], flush=True)
    # ---------- EXIT architecture ----------
    ex = ["X60", "X120", "X1615", "XRES", "XSTRUCT"]; C2e = C2.dropna(subset=[f"usd_{k}" for k in ex]).copy()
    for k in ex:
        C2e[f"inc_{k}"] = C2e[f"usd_{k}"] - C2e.usd_X1615
    for kind in ("RIDGE", "HGB", "ENET"):
        preds = {}
        for k in ex:
            if k == "X1615":
                continue
            T = nested(C2e, EF, f"inc_{k}", kind, ("zero",)); preds[k] = T.set_index(T.index)["score"]
        P_ = pd.DataFrame(preds); best = P_.idxmax(axis=1); bestv = P_.max(axis=1); choose = np.where(bestv > 0, best, "X1615")
        Tt2 = C2e.loc[P_.index]; inc = np.array([Tt2.loc[ix, f"inc_{c}"] for ix, c in zip(P_.index, choose)]); Wm = Tt2.year.values >= 2021
        o = daily_stats(Tt2.date.values[Wm], inc[Wm]); res.append({"task": "X", "population": "C2", "config": kind, **o})
        R.append("ML_LEDGER.csv", {"task": "X", "population": "C2", "config": kind, "stitched_value_day": round(o["value_day"], 3), "slip4_value_day": "", "folds_pos": o["folds_pos"], "n": o["n"], "note": "incremental vs X1615"})
    for k in ex:
        W = C2e[C2e.year >= 2021]; o = daily_stats(W.date.values, W[f"inc_{k}"].values); av.append({"action": f"EXIT_{k}_vs_X1615", "population": "C2", **o})
    Rr = pd.DataFrame(res); A_ = pd.DataFrame(av)
    for r in A_.itertuples(index=False):
        R.append("ACTION_VALUE_LEDGER.csv", {"action": r.action, "population": r.population, "n": r.n, "incremental_ev": round(r.value_day, 3), "folds_pos": r.folds_pos,
                                             "slip4_ev": round(getattr(r, "slip4_value_day", np.nan), 3) if hasattr(r, "slip4_value_day") else "", "note": "$/day on stitched window"})
    Rr.to_csv(os.path.join(OUT, "PH5_ML.csv"), index=False); A_.to_csv(os.path.join(OUT, "PH5_ACTION_VALUES.csv"), index=False)
    json.dump({"hold_curves": curves, "n_ml_configs": len(Rr)}, open(os.path.join(OUT, "PH5_META.json"), "w"), indent=1)
    pd.set_option("display.width", 250); print(Rr.round(2).to_string()); print(A_.round(2).to_string()); print(curves)


if __name__ == "__main__":
    main()
