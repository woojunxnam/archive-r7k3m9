"""TEST45 Phases 9-12 + 25 (ML part): controlled model zoo on identical session-level causal panels.
Tasks: A overnight carry (15:45 decision -> next RTH open), B gap rebound (09:31 decision -> 16:00), C opening-flush
rebound (10:00 decision -> 16:00), D open inventory (09:31 decision -> 12:00: KEEP/ADD/EXIT value of a carried long),
E session regime (Gaussian HMM, causal filtered posteriors) used as a regime feature / regime classifier.
Chronological expanding walk-forward only: FIRST_TRAIN 500 sessions, blocks of 63, purge 1 session.  Small fixed
regularised presets per family (no hyper-parameter search).  Pooled ES+MNQ rows with an instrument flag."""
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_feat as F  # noqa: E402
import t45_overlay as O  # noqa: E402

warnings.filterwarnings("ignore")
OUT = os.path.join(C.T45, "ml"); os.makedirs(OUT, exist_ok=True)
FIRST, BLOCK, PURGE = 500, 63, 1
g = C.g


def hmm_posteriors(bank, n_states=3):
    """E: causal regime posteriors.  Refit on the expanding window at every block start; forward-filtered (no smoothing)."""
    from hmmlearn.hmm import GaussianHMM
    pn = [bank.sims[k].pn for k in (0, 1)]
    X = np.column_stack([pn[0].gap_lock / pn[0].atr, (pn[0].cash_close - pn[0].open) / pn[0].atr,
                         (pn[0].rth_h - pn[0].rth_l) / pn[0].atr, pn[1].gap_lock / pn[1].atr, (pn[1].cash_close - pn[1].open) / pn[1].atr])
    # the day-t row is only complete at 16:00 of day t -> features for decisions on day t use rows <= t-1 (morning) or t (15:45: row t
    # partially unknown) -> we use rows <= t-1 for every task (strictly causal)
    X = np.nan_to_num(np.clip(X, -5, 5))
    n = len(X)
    post = np.full((n, n_states), np.nan)
    for b0 in range(FIRST, n, BLOCK):
        m = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=100, random_state=7).fit(X[:b0 - PURGE])
        order = np.argsort(m.means_[:, 2])                              # order states by RTH range (calm -> volatile)
        b1 = min(b0 + BLOCK, n)
        # forward filter over rows [0, b1-1) to get P(state_t | x_<=t) then shift by one day
        lp = m._compute_log_likelihood(X[:b1])
        a = np.log(m.startprob_ + 1e-300); A = np.log(m.transmat_ + 1e-300)
        f = np.zeros((b1, n_states))
        f[0] = a + lp[0]; f[0] -= np.logaddexp.reduce(f[0])
        for t in range(1, b1):
            f[t] = np.logaddexp.reduce(f[t - 1][:, None] + A, axis=0) + lp[t]; f[t] -= np.logaddexp.reduce(f[t])
        pr = np.exp(f)[:, order]
        post[b0:b1] = pr[b0 - 1:b1 - 1]                                 # posterior through the PREVIOUS session
        if b0 == FIRST:                                                  # training rows: filtered with the first fit (in-sample
            post[1:b0] = pr[0:b0 - 1]                                    # transform of TRAINING data only)
    return post


def build_tasks(bank, post):
    T = {}
    for k in (0, 1):
        sm = bank.sims[k]; pn = sm.pn; FP = sm.FP; o = bank.sims[1 - k].pn
        st = bank.I[k]
        base = {"inst": np.full(pn.n, k), "sidx": np.arange(pn.n)}
        reg = {f"hmm_p{i}": post[:, i] for i in range(post.shape[1])}
        # ---- A: carry, decision 15:45 (fill 15:46) -> next open print
        fl = F.late(pn, g("15:45")); flo = F.late(o, g("15:45"))
        yA = (np.r_[FP[1:, 0], np.nan] - FP[:, g("15:45") + 1]) / pn.atr
        A = {**base, **{f"L_{kk}": v for kk, v in fl.items() if kk not in ("gap_lock", "prior_ret", "prior_range", "trend20", "vol_pct")},
             "G_gap_lock": fl["gap_lock"], "T_prior_ret": fl["prior_ret"], "T_trend20": fl["trend20"], "V_prior_range": fl["prior_range"],
             "V_vol_pct": fl["vol_pct"], "X_rel_rth_ret": fl["rth_ret"] - flo["rth_ret"], "X_rel_day_ret": fl["day_ret"] - flo["day_ret"],
             "X_rel_mom60": fl["mom60"] - flo["mom60"], "S_champ_pos": st["champ_1612"], "S_champ_dd": st["champ_dd"], **reg, "y": yA}
        # ---- B: gap rebound, decision 09:31 (fill 09:32) -> 16:00
        fm = F.morning(pn, 0)
        yB = (FP[:, g("16:00")] - FP[:, 1]) / pn.atr
        gapf = {f"G_{kk}": fm[kk] for kk in fm if kk.startswith("gap_")}
        Bd = {**base, **gapf, "T_prior_ret": fm["prior_ret"], "T_trend20": fm["trend20"], "V_prior_range": fm["prior_range"],
              "V_vol_pct": fm["vol_pct"], "X_rel_gap": st["rel_gap"], "S_champ_open": st["champ_open"], "S_champ_dd": st["champ_dd"], **reg, "y": yB}
        # ---- C: flush rebound, decision 10:00 (fill 10:01) -> 16:00
        f3 = F.morning(pn, 30); f3o = F.morning(o, 30)
        yC = (FP[:, g("16:00")] - FP[:, 30]) / pn.atr
        Cd = {**{kk: v for kk, v in Bd.items() if kk != "y"}, **{f"F_{kk}": f3[kk] for kk in ("ret_w", "selloff_w", "recovery_w", "reclaim_frac",
                                                                                            "range_pos_w", "disp_total", "dist_vwap_w")},
              "X_rel_selloff": f3["selloff_w"] - f3o["selloff_w"], "X_rel_ret30": f3["ret_w"] - f3o["ret_w"], "y": yC}
        # ---- D: open inventory (value of keeping a carried long from 09:32 to 12:00)
        yD = (FP[:, g("12:00")] - FP[:, 1]) / pn.atr
        Dd = {**{kk: v for kk, v in Bd.items() if kk != "y"}, "y": yD}
        for nm, dd in (("A_CARRY", A), ("B_GAP", Bd), ("C_FLUSH", Cd), ("D_INVENTORY", Dd)):
            T.setdefault(nm, []).append(pd.DataFrame(dd))
    return {k: pd.concat(v, ignore_index=True) for k, v in T.items()}


def fams(cols):
    fam = {}
    for c in cols:
        if c in ("inst", "sidx", "y"):
            continue
        fam.setdefault("R_regime" if c.startswith("hmm_") else c.split("_")[0], []).append(c)
    return fam


def models():
    from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    Z = {"RIDGE": lambda: make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
         "ELASTIC_NET": lambda: make_pipeline(StandardScaler(), ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=5000)),
         "LOGISTIC": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000)),
         "RANDOM_FOREST": lambda: RandomForestRegressor(n_estimators=300, max_depth=4, min_samples_leaf=50, max_features=0.5, n_jobs=4, random_state=7),
         "EXTRA_TREES": lambda: ExtraTreesRegressor(n_estimators=300, max_depth=4, min_samples_leaf=50, max_features=0.5, n_jobs=4, random_state=7),
         "HIST_GB": lambda: HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, l2_regularization=1.0, min_samples_leaf=50, random_state=7),
         "XGBOOST": lambda: xgb.XGBRegressor(max_depth=2, learning_rate=0.05, n_estimators=300, subsample=0.8, colsample_bytree=0.8,
                                             min_child_weight=20, reg_lambda=5.0, n_jobs=4, random_state=7)}
    try:
        import lightgbm as lgb
        Z["LIGHTGBM"] = lambda: lgb.LGBMRegressor(num_leaves=7, learning_rate=0.05, n_estimators=300, min_child_samples=50, subsample=0.8,
                                                  subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0, random_state=7, verbose=-1, n_jobs=4)
    except ImportError:
        pass
    try:
        from catboost import CatBoostRegressor
        Z["CATBOOST"] = lambda: CatBoostRegressor(depth=3, iterations=300, learning_rate=0.05, l2_leaf_reg=10, verbose=0, random_seed=7, thread_count=4)
    except ImportError:
        pass
    return Z


def walk_forward(D, feats, mname, Z, nS):
    pred = np.full(len(D), np.nan)
    for b0 in range(FIRST, nS, BLOCK):
        tr = D[(D.sidx < b0 - PURGE)].dropna(subset=feats + ["y"])
        if len(tr) < 200:
            continue
        te = (D.sidx >= b0) & (D.sidx < b0 + BLOCK)
        tex = D[te][feats]
        ok = tex.notna().all(1).values
        if ok.sum() == 0:
            continue
        X = tr[feats].values; y = np.clip(tr.y.values, -3, 3)
        m = Z[mname]()
        if mname == "LOGISTIC":
            m.fit(X, (y > 0).astype(int)); p = m.predict_proba(tex.values[ok])[:, 1] - 0.5
        else:
            m.fit(X, y); p = m.predict(tex.values[ok])
        idx = np.where(te.values)[0][ok]
        pred[idx] = p
    return pred


def score(D, pred, sess):
    ok = ~np.isnan(pred) & ~np.isnan(D.y.values)
    y = D.y.values[ok]; p = pred[ok]
    o = {"n_oof": int(ok.sum()), "IC": float(np.corrcoef(p, y)[0, 1]), "rankIC": float(spearmanr(p, y).statistic)}
    q = pd.qcut(pd.Series(p).rank(method="first"), 3, labels=False).values
    o["top_minus_bottom_tercile_atr"] = float(y[q == 2].mean() - y[q == 0].mean())
    o["mean_y_pred_pos"] = float(y[p > 0].mean()) if (p > 0).any() else np.nan
    o["share_pred_pos"] = float((p > 0).mean())
    dq = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False).values
    mp = pd.Series(p).groupby(dq).mean().values; my = pd.Series(y).groupby(dq).mean().values
    o["calibration_slope"] = float(np.polyfit(mp, my, 1)[0]) if np.std(mp) > 0 else np.nan
    blk = D.sidx.values[ok] // BLOCK
    ics = [spearmanr(p[blk == b], y[blk == b]).statistic for b in np.unique(blk) if (blk == b).sum() > 30]
    o["block_rankIC_pos_share"] = float(np.mean(np.array(ics) > 0)); o["n_blocks"] = len(ics)
    return o


def to_overlay(task, D, pred, bank, mapping="POS1"):
    """map OOF predictions to integer targets and run through the SAME overlay engine."""
    n = bank.n
    q = {}
    for k in (0, 1):
        p = np.full(n, np.nan)
        m = D.inst.values == k
        p[D.sidx.values[m]] = pred[m]
        if mapping == "POS1":
            q[k] = np.where(p > 0, 1, 0)
        else:                                            # POS2: 1 if p>0, 2 if p above the expanding 80th pct of past predictions
            thr = pd.Series(p).expanding(min_periods=63).quantile(0.8).shift(1).values
            q[k] = np.where(p > 0, np.where((p > thr) & ~np.isnan(thr), 2, 1), 0)
        q[k] = np.where(np.isnan(p), 0, q[k]).astype(np.int64)
    if task == "A_CARRY":
        ge = O.G(c_on=1, c_time="15:45")
        return ge, dict(qc_ext=q)
    w = {"B_GAP": 0, "C_FLUSH": 30, "D_INVENTORY": 0}[task]
    ex = "12:00" if task == "D_INVENTORY" else "16:00"
    ge = O.G(m_on=1, m_w=w, m_exit=ex, m_q=1)
    return ge, dict(qm_ext=q, m_tree={0: q[0] > 0, 1: q[1] > 0})


def main():
    from t45_common import build_panel
    P = build_panel()
    bank = O.Bank(P)
    t0 = time.time()
    post = hmm_posteriors(bank)
    TK = build_tasks(bank, post)
    Z = models()
    nS = bank.n
    span = np.zeros(nS, bool); span[FIRST:] = True
    rows, pnl_rows = [], []
    preds = {}
    for task, D in TK.items():
        allf = [c for c in D.columns if c not in ("sidx", "y")]
        feats_noreg = [c for c in allf if not c.startswith("hmm_")]
        for mname in Z:
            for fs_name, fs in (("ALL_NO_REGIME", feats_noreg), ("ALL+HMM_REGIME", allf)):
                if fs_name == "ALL+HMM_REGIME" and mname not in ("RIDGE", "HIST_GB"):
                    continue
                t1 = time.time()
                pred = walk_forward(D, fs, mname, Z, nS)
                preds[(task, mname, fs_name)] = pred
                o = {"task": task, "model": mname, "features": fs_name, **score(D, pred, bank.sess), "fit_sec": time.time() - t1}
                for mp in ("POS1", "POS2"):
                    ge, kw = to_overlay(task, D, pred, bank, mp)
                    r, _, pnl = O.report(ge, bank, f"{task}|{mname}|{fs_name}|{mp}", periods=False, mask=span, **kw)
                    o.update({f"{mp}_{k}": r[k] for k in ("avg", "max_dd", "worst", "session_matched_beta_excess", "matched_beta_excess",
                                                          "incr_avg", "incr_max_dd", "corr_champion", "SLIP4_total", "outer_blocks_median",
                                                          "outer_blocks_min", "outer_blocks_pos", "sides")})
                    pnl_rows.append(pd.Series(pnl, index=bank.sess, name=f"{task}|{mname}|{fs_name}|{mp}"))
                rows.append(o)
                print(task, mname, fs_name, round(o["rankIC"], 4), round(o["POS1_avg"], 2), round(o["POS1_max_dd"]), f"{time.time() - t0:.0f}s", flush=True)
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T45_10_model_walkforward.csv", index=False)
    pd.concat(pnl_rows, axis=1).to_parquet(f"{OUT}/T45_10_model_daily.parquet")
    # regime classifier view (E): mean target by most-likely regime state (causal posterior)
    er = []
    st = np.nanargmax(np.nan_to_num(post, nan=-1), 1); st[np.isnan(post[:, 0])] = -1
    for task, D in TK.items():
        for k in (0, 1):
            m = D.inst.values == k
            y = D.y.values[m]
            for s in range(post.shape[1]):
                mm = (st == s) & ~np.isnan(y)
                er.append({"task": task, "inst": C.INSTS[k], "hmm_state(calm->volatile)": s, "n": int(mm.sum()),
                           "mean_y_atr": float(y[mm].mean()) if mm.any() else np.nan,
                           "t": float(y[mm].mean() / y[mm].std() * np.sqrt(mm.sum())) if mm.sum() > 2 else np.nan})
    pd.DataFrame(er).to_csv(f"{OUT}/T45_10_regime_states.csv", index=False)
    # ---------------------------------------------------------- ablation (Phase 11/25): best tree + ridge per task, drop one family
    ab = []
    for task, D in TK.items():
        allf = [c for c in D.columns if c not in ("sidx", "y") and not c.startswith("hmm_")]
        fam = fams(allf)
        sub = R[(R.task == task) & (R.features == "ALL_NO_REGIME")]
        best_tree = sub[~sub.model.isin(["RIDGE", "ELASTIC_NET", "LOGISTIC"])].sort_values("rankIC").iloc[-1].model
        for mname in ("RIDGE", best_tree):
            for fname, cols in fam.items():
                if fname == "inst":
                    continue
                fs = [c for c in allf if c not in cols]
                pred = walk_forward(D, fs, mname, Z, nS)
                o = {"task": task, "model": mname, "dropped_family": fname, **score(D, pred, bank.sess)}
                ge, kw = to_overlay(task, D, pred, bank, "POS1")
                r, _, _ = O.report(ge, bank, "abl", periods=False, mask=span, **kw)
                o.update({f"POS1_{k}": r[k] for k in ("avg", "max_dd", "session_matched_beta_excess")})
                ab.append(o)
            print("ablation", task, mname, f"{time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(ab).to_csv(f"{OUT}/T45_11_model_ablation.csv", index=False)
    json.dump({"FIRST_TRAIN": FIRST, "BLOCK": BLOCK, "PURGE": PURGE, "models": list(Z), "tasks": list(TK),
               "features": {t: [c for c in D.columns if c not in ("sidx", "y")] for t, D in TK.items()}},
              open(f"{OUT}/T45_09_model_zoo_spec.json", "w"), indent=1)
    np.save(f"{OUT}/hmm_post.npy", post)


if __name__ == "__main__":
    main()
