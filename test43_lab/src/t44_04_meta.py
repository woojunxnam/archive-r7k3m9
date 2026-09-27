"""TEST44 Phases 9-15: session-level Ridge and XGBoost meta allocators (relative sleeve value), strictly chronological
expanding walk-forward with a 1-session purge, feature-family ablation, allocation through the integer engine.

Sample = (sleeve, session).  Target y[s,t] = session-t P&L of holding ONE contract whenever sleeve s is ON (its frozen
state, off-band 0.1), minus (ON share x one-contract passive P&L), in instrument daily-ATR units.  Features use only
information available at the close of session t-1.  No calendar features.  Meta models output a score; the integer
allocator gates a sleeve's demand to 0 for the session when its score <= 0 (no fractional contracts, no extra leverage).
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

sys.path.insert(0, os.path.dirname(__file__))
import t44_alloc as A  # noqa: E402
import t44_common as TC  # noqa: E402
from t43 import v6lab  # noqa: E402
from t44_03_priority_loo import parse  # noqa: E402

OUT = TC.T44
OFF0 = 0.1
FIRST_TRAIN = 500        # sessions of history before the first out-of-sample block
BLOCK = 63               # re-fit every ~quarter
PURGE = 1                # sessions dropped between train end and block start
FAM = {"A": ["inten_last", "inten_mean", "on_share_prev", "on_last", "is_MNQ", "cl1", "cl2", "cl3"],
       "B": ["tier", "atr_pct", "trend20", "trend100"],
       "C": ["y_roll20", "y_roll60", "y_sd60", "y_dd120"],
       "D": ["acct_dd", "acct_mu", "acct_ret20"]}
XGB_PRESETS = {
    "XGB_SHALLOW": dict(max_depth=2, learning_rate=0.03, n_estimators=400, min_child_weight=50, reg_lambda=10.0, subsample=1.0, colsample_bytree=1.0),
    "XGB_REGULARIZED": dict(max_depth=3, learning_rate=0.03, n_estimators=400, min_child_weight=100, reg_lambda=30.0, subsample=0.7, colsample_bytree=0.7),
    "XGB_VERY_REGULARIZED": dict(max_depth=1, learning_rate=0.02, n_estimators=200, min_child_weight=200, reg_lambda=50.0, subsample=0.7, colsample_bytree=0.7),
}
RIDGE_ALPHA = 10.0


def panel(E):
    T = E.T
    sd = pd.DatetimeIndex(T.sd.values)
    sess = pd.Index(sorted(set(sd)))
    six = sess.get_indexer(sd)
    first = np.r_[True, six[1:] != six[:-1]]
    last = np.r_[six[1:] != six[:-1], True]
    feats = {}
    for inst in ("ES", "MNQ"):
        b, f = v6lab.load(inst, TC.END)
        g = pd.DataFrame({"sd": b.session_date.values, "tier": f["d_TIER"], "atr_pct": f["d_ATR20_pct"], "trend20": f["d_TREND20"],
                          "trend100": f["d_TREND100"]}).groupby("sd").first()
        feats[inst] = g.reindex(sess)            # completed-session regime (already lagged by one session in features.py)
    # account state from the simple deterministic reference allocator (known at the close of t-1)
    simple = json.load(open(f"{OUT}/t44_simple_selection.json"))["SIMPLE_BEST_FEASIBLE"]
    mode, rq, rk, cap = parse(simple)
    REQ, X, dem = E.requests(**rq)
    r = E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), **rk)
    d = E.daily(r).reindex(sess)
    eq = d.eq_end.ffill()
    acct = pd.DataFrame({"acct_dd": (eq.cummax() - eq) / 10000.0, "acct_mu": d.mu_max.fillna(0), "acct_ret20": d.pnl.rolling(20).sum() / 10000.0}, index=sess).shift(1)
    rows = []
    for cid in E.ids:
        k = A.INSTS.index(E.inst[cid]); inst = A.INSTS[k]
        on = ((E.des[cid] > 0) & (E.inten[cid] >= OFF0)).astype(float)
        held = np.r_[0.0, on[:-1]]
        dc = np.r_[0.0, np.diff(E.arr["c"][:, k])] * E.pv[k]
        atr = pd.Series(E.arr["atr"][:, k]).groupby(six).first().values
        pnl = pd.Series(held * dc).groupby(six).sum().values
        on_share = pd.Series(held).groupby(six).mean().values
        c1 = E.c1[inst].reindex(sess).fillna(0).values
        unit = np.where(atr > 0, atr * E.pv[k], np.nan)
        y = (pnl - on_share * c1) / unit
        it = pd.Series(E.inten[cid]); on_s = pd.Series(on)
        df = pd.DataFrame({"sess": sess, "sleeve": cid, "y": y,
                           "inten_last": it.groupby(six).last().values, "inten_mean": it.groupby(six).mean().values,
                           "on_share": on_s.groupby(six).mean().values, "on_last": on_s.groupby(six).last().values})
        # everything below is shifted: features of row t use session t-1 information only
        df["inten_last"] = df.inten_last.shift(1); df["inten_mean"] = df.inten_mean.shift(1)
        df["on_share_prev"] = df.on_share.shift(1); df["on_last"] = df.on_last.shift(1)
        ys = df.y.shift(1)
        df["y_roll20"] = ys.rolling(20).mean(); df["y_roll60"] = ys.rolling(60).mean(); df["y_sd60"] = ys.rolling(60).std()
        cum = ys.fillna(0).cumsum(); df["y_dd120"] = (cum.rolling(120, min_periods=20).max() - cum)
        df["is_MNQ"] = float(inst == "MNQ")
        for c in (1, 2, 3):
            df[f"cl{c}"] = float(TC.CLUSTER[cid] == c)
        m = feats[inst]
        for col in FAM["B"]:
            df[col] = m[col].values
        for col in FAM["D"]:
            df[col] = acct[col].values
        rows.append(df)
    P = pd.concat(rows, ignore_index=True)
    P["sess_ix"] = sess.get_indexer(P.sess)
    return P, sess, six


def walk_forward(P, model, feats):
    """Expanding chronological walk-forward; returns out-of-sample predictions and block metadata."""
    nS = P.sess_ix.max() + 1
    pred = pd.Series(np.nan, index=P.index)
    meta = []
    for b0 in range(FIRST_TRAIN, nS, BLOCK):
        tr = P[(P.sess_ix < b0 - PURGE)].dropna(subset=feats + ["y"])
        te = P[(P.sess_ix >= b0) & (P.sess_ix < b0 + BLOCK)]
        te_ok = te.dropna(subset=feats)
        if len(tr) < 1000 or len(te_ok) == 0:
            continue
        Xtr = tr[feats].values; ytr = np.clip(tr.y.values, -3, 3)
        if model == "RIDGE":
            sc = StandardScaler().fit(Xtr)
            m = Ridge(alpha=RIDGE_ALPHA).fit(sc.transform(Xtr), ytr)
            p = m.predict(sc.transform(te_ok[feats].values))
            info = {"coef": dict(zip(feats, np.round(m.coef_, 5))), "intercept": float(m.intercept_)}
        else:
            prm = dict(XGB_PRESETS[model])
            cut = int(len(tr) * 0.8)                     # chronological early-stopping split inside the training window
            order = np.argsort(tr.sess_ix.values, kind="stable")
            itr, iva = order[:cut], order[cut:]
            m = xgb.XGBRegressor(objective="reg:squarederror", random_state=7, n_jobs=4, early_stopping_rounds=40, **prm)
            m.fit(Xtr[itr], ytr[itr], eval_set=[(Xtr[iva], ytr[iva])], verbose=False)
            p = m.predict(te_ok[feats].values)
            info = {"best_iteration": int(m.best_iteration)}
        pred.loc[te_ok.index] = p
        meta.append({"block_start_sess": b0, "train_rows": len(tr), "test_rows": len(te_ok), "train_last_sess": int(tr.sess_ix.max()), **info})
    return pred, meta


def ic_report(P, pred):
    m = pred.notna() & P.y.notna()
    x = P[m].assign(p=pred[m])
    x["mon"] = x.sess.dt.to_period("M")
    mic = x.groupby("mon").apply(lambda g: spearmanr(g.p, g.y)[0] if len(g) > 30 else np.nan).dropna()
    top = x.groupby("sess").apply(lambda g: g.sort_values("p").y.iloc[-3:].mean() - g.sort_values("p").y.iloc[:3].mean() if len(g) >= 6 else np.nan)
    return {"n": int(m.sum()), "IC_pooled": float(spearmanr(x.p, x.y)[0]), "IC_monthly_mean": float(mic.mean()),
            "IC_monthly_t": float(mic.mean() / (mic.std() / np.sqrt(len(mic)))), "share_positive_scores": float((x.p > 0).mean()),
            "top3_minus_bottom3_y_atr": float(top.mean()), "gated_mean_y": float(x[x.p <= 0].y.mean()), "kept_mean_y": float(x[x.p > 0].y.mean())}


USAGES = ("GATE_POS", "TOP_HALF", "DROP_BOTTOM_Q")


def score_arrays(E, P, pred, six, usage="GATE_POS"):
    """Session-level keep(+1)/drop(-1) indicator per sleeve from the OOS scores.
    GATE_POS: keep if predicted excess > 0.  TOP_HALF: keep sleeves at/above the session's cross-sectional median score.
    DROP_BOTTOM_Q: drop only sleeves below the session's 25th percentile score.  No prediction -> keep."""
    x = P[["sleeve", "sess_ix"]].assign(p=pred.values)
    if usage == "GATE_POS":
        x["keep"] = np.where(x.p.isna(), 1.0, np.where(x.p > 0, 1.0, -1.0))
    else:
        q = 0.5 if usage == "TOP_HALF" else 0.25
        thr = x.groupby("sess_ix").p.transform(lambda v: v.quantile(q))
        x["keep"] = np.where(x.p.isna(), 1.0, np.where(x.p >= thr, 1.0, -1.0))
    sc = {}
    for cid in E.ids:
        s = pd.Series(1.0, index=range(six.max() + 1))
        xx = x[x.sleeve == cid]
        s.loc[xx.sess_ix.values] = xx.keep.values
        sc[cid] = s.values[six]
    return sc


def main():
    E = A.Engine()
    P, sess, six = panel(E)
    P.to_csv(f"{OUT}/t44_meta_panel.csv", index=False)
    simple = json.load(open(f"{OUT}/t44_simple_selection.json"))
    alloc_cfgs = {k: v for k, v in simple.items() if v}
    all_feats = sum(FAM.values(), [])
    sets = {"E_ALL": all_feats}
    for fam in FAM:
        sets[f"E_minus_{fam}"] = [f for f in all_feats if f not in FAM[fam]]
    sets["A_ONLY"] = FAM["A"]
    models = ["RIDGE"] + list(XGB_PRESETS)
    info_rows, perf_rows, metas, preds = [], [], {}, {}
    for model in models:
        for sname, feats in sets.items():
            if model != "RIDGE" and model != "XGB_REGULARIZED" and sname != "E_ALL":
                continue                                          # ablation on Ridge and one XGB preset only
            pred, meta = walk_forward(P, model, feats)
            key = f"{model}|{sname}"
            preds[key] = pred; metas[key] = meta
            info_rows.append({"model": model, "features": sname, **ic_report(P, pred)})
            for usage in USAGES:
              if usage != "GATE_POS" and sname not in ("E_ALL", "A_ONLY"):
                  continue
              sc = score_arrays(E, P, pred, six, usage)
              for tag, cfg in alloc_cfgs.items():
                mode, rq, rk, cap = parse(cfg)
                REQ, X, dem = E.requests(**rq, score=sc)
                r = E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), **rk)
                o, d = E.summary(r, pers=("ALL", "ML_OOS_SPAN", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026", "Y2022", "FORMER_HOLDOUT"))
                s4 = E.summary(E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), slip_ticks=4, **rk), pers=("ALL", "ML_OOS_SPAN"))[0]
                perf_rows.append({"model": model, "features": sname, "usage": usage, "allocator": tag, "alloc_cfg": cfg, **o,
                                  "SLIP4_ML_OOS_SPAN_avg": s4["ML_OOS_SPAN_avg"]})
                d.to_csv(f"{OUT}/daily_META_{model}_{sname}_{usage}_{tag}.csv")
            print(key, info_rows[-1]["IC_pooled"], flush=True)
    # deterministic references on the same span
    for tag, cfg in alloc_cfgs.items():
        mode, rq, rk, cap = parse(cfg)
        REQ, X, dem = E.requests(**rq)
        r = E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), **rk)
        o, _ = E.summary(r, pers=("ALL", "ML_OOS_SPAN", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026", "Y2022", "FORMER_HOLDOUT"))
        s4 = E.summary(E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), slip_ticks=4, **rk), pers=("ALL", "ML_OOS_SPAN"))[0]
        perf_rows.append({"model": "NONE(simple integer)", "features": "-", "usage": "-", "allocator": tag, "alloc_cfg": cfg, **o, "SLIP4_ML_OOS_SPAN_avg": s4["ML_OOS_SPAN_avg"]})
    pd.DataFrame(info_rows).to_csv(f"{OUT}/t44_meta_information.csv", index=False)
    pd.DataFrame(perf_rows).to_csv(f"{OUT}/t44_meta_performance.csv", index=False)
    json.dump(metas, open(f"{OUT}/t44_meta_walkforward_blocks.json", "w"), indent=1, default=str)
    pd.DataFrame(preds).to_csv(f"{OUT}/t44_meta_oos_predictions.csv")
    pd.set_option("display.width", 260)
    print(pd.DataFrame(info_rows).round(4).to_string(index=False))
    print(pd.DataFrame(perf_rows)[["model", "features", "usage", "allocator", "ML_OOS_SPAN_avg", "ML_OOS_SPAN_max_dd", "ML_OOS_SPAN_worst", "ML_OOS_SPAN_ret_dd",
                                  "ML_OOS_SPAN_excess_vs_mb", "Y2022_avg", "FORMER_HOLDOUT_avg", "SLIP4_ML_OOS_SPAN_avg", "fills_per_day"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
