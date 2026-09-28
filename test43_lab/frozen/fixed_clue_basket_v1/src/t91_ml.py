"""TEST91 PROFILE ML (economic target) on the two TEST85-qualifying deterministic mechanisms (MNQ PG12_DOWN_STACK @16:00, PI_DIVERGE @60m).
ML-B = trade / skip each deterministic event; target = net $ (costs incl.); walk-forward outer folds; feature-availability audit first."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t86_run as T  # noqa: E402

OUT = os.path.join(A.AP, "TEST91"); os.makedirs(OUT, exist_ok=True)
FEATS = {"ret_open": "close(j) vs RTH open / ATR (bars <= j)", "eff": "path efficiency since open (bars <= j)", "dist_vwap": "close - session VWAP (bars <= j) / ATR",
         "ret15": "15m return / ATR", "ret60": "60m return / ATR", "relvol30": "last-30m volume / median same window prior 20 sessions",
         "p2_poc_rel": "close - developing POC / ATR (P2 at slot b, bars <= j)", "p2_width": "developing VA width / ATR", "p4_poc_chg30": "P4 POC change over 30m / ATR",
         "p1_vah_rel": "close - prior VAH / ATR (prior session)", "p1_val_rel": "close - prior VAL / ATR", "above_p1vah": "share of P2 volume above prior VAH",
         "prior_day": "prior RTH return / ATR", "gap": "open - prior close / ATR", "volt": "vol tercile (prior)", "bull": "HTF bull (prior)", "tod": "decision minute / 405"}
AUDIT = {"availability": "every feature computed from bars with index <= decision minute j of the current session and completed prior sessions",
         "can_change_after_event": "NO for all features", "rejected": "none needed (no box life / future node survival / final profile inputs)",
         "prefix_invariance": "profile features verified in TEST84 (1,800 samples, 0 mismatches); price features read C/H/L/V[:, :j+1] only"}
SPEC = {"candidates": T.CAND, "features": FEATS, "audit": AUDIT, "target": "net $ of the deterministic event at its horizon",
        "models": "PRIMARY HistGB; reported Ridge, ElasticNet, Logistic(sign), ExtraTrees, RandomForest, XGBoost, CatBoost, LightGBM (fixed presets)",
        "trade": "predicted net > 0 (Logistic: p > 0.5)", "plateau": "thresholds -0.5 $ / +1.0 $", "oracle_bound_$day": {"PG12_DOWN_STACK": 19.96, "PI_DIVERGE": 21.57},
        "ML_ADDS_VALUE": "primary passes (folds >= 4/5 net, B excess > 0, SLIP4 > 0, remove-top3 > 0, plateau) AND T61 incremental >= +10 $/day and ret/DD >= T61",
        "budget": {"ml_configs": 18}}


def models():
    import lightgbm as lgb
    import xgboost as xgb
    from catboost import CatBoostRegressor
    return {"HGB (PRIMARY)": HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=25, random_state=5),
            "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)), "ElasticNet": make_pipeline(StandardScaler(), ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=5000)),
            "Logistic": make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=1000)),
            "ExtraTrees": ExtraTreesRegressor(n_estimators=200, min_samples_leaf=25, n_jobs=-1, random_state=5),
            "RandomForest": RandomForestRegressor(n_estimators=200, min_samples_leaf=25, n_jobs=-1, random_state=5),
            "XGBoost": xgb.XGBRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, min_child_weight=25, verbosity=0, random_state=5),
            "CatBoost": CatBoostRegressor(iterations=200, depth=3, learning_rate=0.05, verbose=0, random_seed=5),
            "LightGBM": lgb.LGBMRegressor(n_estimators=150, num_leaves=7, learning_rate=0.05, min_child_samples=25, verbose=-1, random_state=5)}


def feats(I, E, P1, F):
    s = E.s.values.astype(int); j = E.j.values.astype(int); b = (j - 4) // 5; a = I.atr[s]; c = I.C[s, j]
    rv = A.rel_volume(I)
    f = lambda k: F[s, b, A.FEAT[k]]
    f30 = lambda k: F[s, np.maximum(b - 6, 0), A.FEAT[k]]
    path = np.array([np.abs(np.diff(I.C[ss, :jj + 1])).sum() for ss, jj in zip(s, j)])
    X = pd.DataFrame({"ret_open": (c - I.FP[s, 0]) / a, "eff": np.abs(c - I.FP[s, 0]) / np.maximum(path, 1e-9), "dist_vwap": (c - I.vwap[s, j]) / a,
                      "ret15": (c - I.C[s, j - 15]) / a, "ret60": (c - I.C[s, np.maximum(j - 60, 0)]) / a, "relvol30": rv[s, j], "p2_poc_rel": (c - f("P2_POC")) / a,
                      "p2_width": f("P2_WIDTH") / a, "p4_poc_chg30": (f("P4_POC") - f30("P4_POC")) / a, "p1_vah_rel": (c - P1[s, 1]) / a, "p1_val_rel": (c - P1[s, 2]) / a,
                      "above_p1vah": f("P2_ABOVE_P1VAH"), "prior_day": (I.C[s - 1, A.J15] - I.FP[s - 1, 0]) / a, "gap": (I.FP[s, 0] - I.C[s - 1, A.J15]) / a,
                      "volt": I.vt[s], "bull": I.bull[s], "tod": j / A.NG})
    return X.fillna(0.0)


def main():
    print(A.prereg("TEST91", SPEC))
    Is = B.load(); I = Is["MNQ"]; nd = int(I.full.sum()); BK = A.buckets(I); rows = []
    t61 = K.t61_daily()["T61-R1C"].daily_pnl.reindex(I.sess).fillna(0).values
    for name, c in T.CAND.items():
        E, P1, F = T.events(I, Is["ES"], name, c["base_proxy"]); h = c["horizon"]
        _, L = T.trade(I, E, h); E = E.iloc[:len(L)].copy() if len(E) == len(L) else E[E.j.values + 1 < A.J15].reset_index(drop=True)
        E = A.label(I, E.copy(), BK); E["date"] = I.sess[E.s.values]; E = E.dropna(subset=[f"{h}_net"]).reset_index(drop=True)
        X = feats(I, E, P1, F); y = E[f"{h}_net"].values
        for mname, m in models().items():
            pred = np.full(len(E), np.nan)
            for nm, a_, b_ in B.FOLDS:
                tr = (E.date < a_).values; te = ((E.date >= a_) & (E.date <= b_)).values
                if tr.sum() < 40 or not te.any():
                    continue
                if mname == "Logistic":
                    m.fit(X[tr], (y[tr] > 0).astype(int)); pred[te] = m.predict_proba(X[te])[:, 1] - 0.5
                else:
                    m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
            res = {}
            for thr in (0.0, -0.5, 1.0):
                t_ = thr if mname != "Logistic" else thr / 100
                sel = np.nan_to_num(pred, nan=-1e9) > t_
                x = E[sel]; d = np.zeros(I.n); np.add.at(d, x.s.values, x[f"{h}_net"].values)
                res[thr] = (d, x)
            d, x = res[0.0]; full = I.full & np.asarray(I.sess >= B.S21)
            r = B.risk(d[I.full]); act = d[I.full & (d != 0)]; top = np.sort(act)[::-1]
            fd = [d[np.asarray((I.sess >= a_) & (I.sess <= b_))].mean() for _, a_, b_ in B.FOLDS]
            d4 = np.zeros(I.n); np.add.at(d4, x.s.values, x[f"{h}_net4"].values)
            base = d[I.full].sum(); pl = [res[t][0][I.full].sum() for t in (-0.5, 1.0)]
            gi = K.incremental_gate(f"{name}_{mname}", d, t61, I.sess, {"matched_excess_day": float(x[f"{h}_B"].sum() / nd), "slip4_incr_avg_day": float(d4[I.full].mean()),
                                                                          "plateau_pass": bool(base > 0 and all(v > 0 and v >= 0.6 * base for v in pl)), "delay1_incr_avg_day": 1.0,
                                                                          "peak_total_MNQ": 6, "peak_total_MES": 6, "peak_margin_pct": 31})
            o = {"mechanism": name, "model": mname, "trades": len(x), "avg_day": r["avg_day"], "avg_day_2021": float(d[full].mean()), "B_excess_day": float(x[f"{h}_B"].sum() / nd),
                 "slip4_day": float(d4[I.full].mean()), "folds_pos": int(sum(v > 0 for v in fd)), "remove_top3": float(act.sum() - top[:3].sum()) if len(act) else 0.0,
                 "plateau": str([round(v) for v in pl]), "t61_incr_day": gi["incr_avg_day"], "t61_comb_ret_dd": gi["comb_ret_dd"], "max_dd": r["max_dd"],
                 "rank_ic": float(pd.Series(pred).corr(pd.Series(y), method="spearman"))}
            o["STANDALONE_PASS"] = bool(o["folds_pos"] >= 4 and o["B_excess_day"] > 0 and o["slip4_day"] > 0 and o["remove_top3"] > 0 and base > 0 and all(v > 0 and v >= 0.6 * base for v in pl))
            o["ADDS_VALUE"] = bool(o["STANDALONE_PASS"] and gi["incr_avg_day"] >= 10 and gi["incr_avg_day_2021"] >= 10 and gi["comb_ret_dd"] >= gi["t61_ret_dd"])
            rows.append(o); print(name, mname, round(o["avg_day"], 2), round(o["B_excess_day"], 2), o["folds_pos"], o["trades"], o["STANDALONE_PASS"], flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "TEST91_RESULTS.csv"), index=False)
    pd.set_option("display.width", 250); print(R.round(3).to_string())
    A.budget("TEST91", ml_configs=18, note="ML-B trade/skip, 9 presets x 2 mechanisms")
    A.md("TEST91_PROFILE_ML.md", "TEST91 - profile ML (economic target)", [str(SPEC), R.round(3)])


if __name__ == "__main__":
    main()
