"""TEST76 BOX ML (justified by the literal program rule: atlas geometries with matched excess > 0 in >= 4/5 folds exist).
ML-A: regress the NET $ of the TEST70 bottom trade (costs included); trade iff predicted net > threshold; one position at a time per instrument.
ML-C: at TOP, regress the incremental $ of holding to 16:15 vs exiting; hold iff predicted > 0 (diagnostic on the ML-A selected trades).
Ranking = economics (net, matched excess, folds); AUC / rank-IC diagnostics only."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402

QUAL = {"MNQ": ["C_PRIORCLOSE_K1.0", "C_MID30_K1.5", "E_OR5", "H_BAL6"], "ES": ["C_OPEN_K0.5", "C_OPEN_K1.5", "C_PRIORCLOSE_K1.5", "G_VWAP_M0.15"]}
FEATS = ["w_atr", "age_at_touch", "dir_c", "prev_dir_c", "wd_c", "velocity", "tod", "ret_open", "ret15", "ret60", "prior_day", "gap", "volt", "bull",
         "dist_hi", "dist_lo", "geo_c"]


def models():
    import lightgbm as lgb
    import xgboost as xgb
    from catboost import CatBoostRegressor
    return {"HGB (PRIMARY)": HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=50, random_state=5),
            "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)), "ElasticNet": make_pipeline(StandardScaler(), ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=5000)),
            "ExtraTrees": ExtraTreesRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=5),
            "RandomForest": RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=5),
            "XGBoost": xgb.XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, min_child_weight=50, verbosity=0, random_state=5),
            "LightGBM": lgb.LGBMRegressor(n_estimators=200, num_leaves=15, learning_rate=0.05, min_child_samples=50, verbose=-1, random_state=5),
            "CatBoost": CatBoostRegressor(iterations=300, depth=4, learning_rate=0.05, verbose=0, random_seed=5)}


SPEC = {"justification": "program rule TEST76: atlas cells with matched excess > 0 in >= 4/5 folds (8 cells listed in QUAL); note: none net-positive after SLIP4",
        "qualifying": QUAL, "features": FEATS, "target_ML_A": "net $ of the TEST70 bottom trade (1 contract, costs incl.)",
        "walk_forward": "outer folds 2021..2025-26; train on events before the fold (>= 2019-07-01)", "trade": "predicted net > 0; greedy one position per instrument",
        "models": "PRIMARY HistGradientBoosting; reported: Ridge, ElasticNet, ExtraTrees, RandomForest, XGBoost, LightGBM, CatBoost (fixed presets)",
        "plateau_ML": "thresholds -0.5 $ and +1.0 $ (all > 0 and >= 60% of base)", "ML_ADDS_VALUE": "primary passes the standalone gate AND >= half of the other models "
        "have net > 0", "ML_C": "HGB on hold-to-16:15 incremental $ at TOP (diagnostic)", "budget": {"ml_configs": 18}}


def features(I, E, geos):
    s = E.s.values.astype(int); j = E.j_touch.values.astype(int); a = I.atr[s]
    c = I.C[s, j]; o = I.FP[s, 0]
    X = pd.DataFrame({"w_atr": E.w_atr.values, "age_at_touch": E.age_at_touch.values,
                      "dir_c": E.dir.map({"RISING": 1, "FLAT": 0, "FALLING": -1}).fillna(2).values, "prev_dir_c": E.prev_dir.map({"RISING": 1, "FLAT": 0, "FALLING": -1}).fillna(2).values,
                      "wd_c": E.width_dyn.map({"CONTRACTING": -1, "STABLE": 0, "EXPANDING": 1}).fillna(2).values, "velocity": E.velocity.fillna(0).values, "tod": j / B.NG,
                      "ret_open": (c - o) / a, "ret15": (c - I.C[s, np.maximum(j - 15, 0)]) / a, "ret60": (c - I.C[s, np.maximum(j - 60, 0)]) / a,
                      "prior_day": np.where(s > 0, (I.C[np.maximum(s - 1, 0), B.J15] - I.FP[np.maximum(s - 1, 0), 0]) / a, 0),
                      "gap": np.where(s > 0, (o - I.C[np.maximum(s - 1, 0), B.J15]) / a, 0), "volt": I.vt[s], "bull": I.bull[s],
                      "dist_hi": np.array([(I.H[ss, :jj + 1].max() - cc) for ss, jj, cc in zip(s, j, c)]) / a,
                      "dist_lo": np.array([(cc - I.L[ss, :jj + 1].min()) for ss, jj, cc in zip(s, j, c)]) / a,
                      "geo_c": E.geometry.map({g: i for i, g in enumerate(geos)}).values})
    return X.fillna(0.0)


def greedy(E, sel):
    """one position at a time: take selected events in entry order, skip those entering before the previous exit."""
    e = E[sel].sort_values(["s", "j_in"]); keep = []; last = (-1, -1)
    for i, r in zip(e.index, e.itertuples(index=False)):
        if (r.s, r.j_in) > last:
            keep.append(i); last = (r.s, r.j_x)
    return E.loc[keep]


def econ(I, T, delay_net=None):
    nd = int(I.full.sum()); d = np.zeros(I.n); np.add.at(d, T.s.values.astype(int), T.net.values)
    x = np.zeros(I.n); np.add.at(x, T.s.values.astype(int), T.excess.values)
    fn = {nm: float(d[np.asarray((I.sess >= a) & (I.sess <= b))].mean()) for nm, a, b in B.FOLDS}
    fc = {nm: int(((T.date >= a) & (T.date <= b)).sum()) for nm, a, b in B.FOLDS}
    act = d[I.full & (d != 0)]; top = np.sort(act)[::-1]; r = B.risk(d[I.full])
    return {"trades": len(T), "avg_day": r["avg_day"], "excess_day": float(x[I.full].mean()), "max_dd": r["max_dd"], "worst_day": r["worst_day"],
            "slip4_day": float((T.net4.sum()) / nd), "folds_net_pos": int(sum(v > 0 for v in fn.values())), "min_fold_n": min(fc.values()),
            "remove_top3": float(act.sum() - top[:3].sum()) if len(act) else 0.0, **{f"fold_net_{k}": v for k, v in fn.items()}}, d


def main():
    print(B.prereg("TEST76", SPEC))
    import json, hashlib
    ad = os.path.join(B.BOX, "TEST76", "TEST76_ADDENDUM_LEAKAGE_FIX.json")
    if not os.path.exists(ad):
        json.dump({"issue": "feature 'life' (box death - birth) is LOOK-AHEAD for B/H/D-type boxes whose death is the (future) break; the first run "
                   "(HGB +21.85 $/day, 5/5 folds) was contaminated and is VOID", "fix": "feature removed; NaN -> 0 for linear models; nothing else changed",
                   "void_result": {"MNQ HGB avg_day": 21.85, "excess_day": 24.77}}, open(ad, "w"), indent=1)
        open(ad + ".sha256", "w").write(hashlib.sha256(open(ad, "rb").read()).hexdigest() + "\n")
    Is = B.load(); rows = []; mlc = []
    for inst, geos in QUAL.items():
        I = Is[inst]
        E = pd.concat([pd.read_parquet(os.path.join(B.BOX, "TEST70", f"events_{inst}_{g}.parquet")).assign(geometry=g) for g in geos], ignore_index=True)
        E["date"] = I.sess[E.s.values.astype(int)]
        # +1 bar delay net (entry one minute later, same exit)
        s = E.s.values.astype(int); ji = np.minimum(E.j_in.values.astype(int) + 1, B.J15)
        E["net_delay"] = (E.px_x - I.FP[s, ji]) * I.pv - 2 * I.cs
        X = features(I, E, geos); y = E.net.values
        for mname, mdl in models().items():
            pred = np.full(len(E), np.nan)
            for nm, a, b in B.FOLDS:
                tr = (E.date < a).values; te = ((E.date >= a) & (E.date <= b)).values
                mdl.fit(X[tr], y[tr]); pred[te] = mdl.predict(X[te])
            E[f"p_{mname}"] = pred
            res = {}
            for thr in (0.0, -0.5, 1.0):
                sel = np.nan_to_num(pred, nan=-1e9) > thr
                T = greedy(E, sel); o, d = econ(I, T); res[thr] = (o, T)
            o, T = res[0.0]
            base = o["avg_day"] * I.full.sum()
            pl = [res[t][0]["avg_day"] * I.full.sum() for t in (-0.5, 1.0)]
            o.update({"instrument": inst, "model": mname, "plateau_totals": str([round(v) for v in pl]), "plateau_pass": bool(base > 0 and all(v > 0 and v >= 0.6 * base for v in pl)),
                      "delay1_day": float(T.net_delay.sum() / I.full.sum()), "rank_ic": float(pd.Series(pred).corr(pd.Series(y), method="spearman"))})
            rng = np.random.default_rng(5); Tm = T[rng.random(len(T)) >= 0.2]; o["miss20_day"] = float(Tm.net.sum() / I.full.sum())
            o["PASS"] = bool(o["excess_day"] > 0 and o["folds_net_pos"] >= 4 and o["remove_top3"] > 0 and o["slip4_day"] > 0 and o["plateau_pass"]
                             and o["delay1_day"] > 0 and o["miss20_day"] > 0 and o["trades"] >= 300 and o["min_fold_n"] >= 40)
            rows.append(o); print(inst, mname, round(o["avg_day"], 2), round(o["excess_day"], 2), o["folds_net_pos"], o["trades"], o["PASS"], flush=True)
        # ML-C (diagnostic): at TOP, hold to 16:15 vs exit, HGB on the same features, on all top-reaching events
        Tt = E[(E.reason == 1)].copy()
        st = Tt.s.values.astype(int); jt = Tt.j_topfill.values.astype(int)
        Tt["hold_incr"] = (I.FPb[st, B.J15] - I.FPb[st, jt]) * I.pv
        Xt = features(I, Tt, geos); pr = np.full(len(Tt), np.nan)
        for nm, a, b in B.FOLDS:
            tr = (Tt.date < a).values; te = ((Tt.date >= a) & (Tt.date <= b)).values
            if tr.sum() > 100 and te.any():
                m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=50, random_state=5).fit(Xt[tr], Tt.hold_incr.values[tr])
                pr[te] = m.predict(Xt[te])
        ok = ~np.isnan(pr); nd = I.full.sum()
        mlc.append({"instrument": inst, "top_events_2021p": int(ok.sum()), "always_exit_incr_day": 0.0, "always_hold_incr_day": float(Tt.hold_incr[ok].sum() / nd),
                    "ml_hold_incr_day": float(Tt.hold_incr[ok & (pr > 0)].sum() / nd), "ml_hold_share": float((pr[ok] > 0).mean()) if ok.any() else np.nan})
    R = pd.DataFrame(rows); C = pd.DataFrame(mlc)
    R.to_csv(os.path.join(B.BOX, "TEST76", "TEST76_ML_A_RESULTS.csv"), index=False); C.to_csv(os.path.join(B.BOX, "TEST76", "TEST76_ML_C_TOP_HOLD.csv"), index=False)
    pd.set_option("display.width", 250); print(R.drop(columns=[c for c in R.columns if c.startswith("fold_net")]).round(3).to_string()); print(C.round(3).to_string())
    B.budget("TEST76", ml_configs=18, note="ML-A 8 models x 2 instruments (economic target) + ML-C HGB x 2")
    B.md("TEST76_BOX_ML.md", "TEST76 - box ML (economic targets)", [str(SPEC), R.round(3), "ML-C top hold:", C.round(3)])


if __name__ == "__main__":
    main()
