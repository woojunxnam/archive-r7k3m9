"""P3 nested walk-forward ML (prereg 903cfa0)."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import rp_bank as B  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as R  # noqa: E402

OUT = os.path.join(R.OUT, "ml"); os.makedirs(OUT, exist_ok=True); H = "h1615"
CANDS = ["C1_R1_TRAPPED_UNION", "C2_P2_FAILED_FIRST", "C3_P1_H2", "C4_L2_FAMILY", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"]
CONF = {"K1": ("RIDGE", "T1", 0.5), "K2": ("RIDGE", "T1", 0.25), "K3": ("ENET", "T1", 0.5), "K4": ("LOGIT", "T2", 0.5), "K5": ("LOGIT", "T2", 0.25),
        "K6": ("HGB", "T1", 0.5), "K7": ("HGB", "T1", 0.25), "K8": ("HGBCLS", "T2", 0.5)}
GRID = {"RIDGE": [1, 10, 100, 1000], "ENET": [0.01, 0.1, 1], "LOGIT": [0.01, 0.1, 1], "HGB": [100, 200], "HGBCLS": [100, 200]}


def design(D):
    X = D[B.FEATS].astype(float).copy()
    for i in ("ES", "NQ", "YM", "RTY"):
        X[f"inst_{i}"] = (D.inst == i).astype(float)
    if D.candidate.iloc[0] in ("C1_R1_TRAPPED_UNION", "C4_L2_FAMILY"):
        for lab in sorted(D.label.unique()):
            X[f"con_{lab}"] = (D.label == lab).astype(float)
    return X


class Prep:
    def fit(self, X):
        X = X.replace([np.inf, -np.inf], np.nan); self.med = X.median().fillna(0.0); Z = X.fillna(self.med); self.mu = Z.mean(); self.sd = Z.std().replace(0, 1).fillna(1); return self

    def __call__(self, X):
        return ((X.replace([np.inf, -np.inf], np.nan).fillna(self.med) - self.mu) / self.sd).values


def model(kind, hp):
    return {"RIDGE": lambda: Ridge(alpha=hp), "ENET": lambda: ElasticNet(alpha=hp, l1_ratio=0.5, max_iter=5000), "LOGIT": lambda: LogisticRegression(C=hp, max_iter=2000),
            "HGB": lambda: HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, min_samples_leaf=50, l2_regularization=1.0, max_iter=hp, random_state=7),
            "HGBCLS": lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, min_samples_leaf=50, l2_regularization=1.0, max_iter=hp, random_state=7)}[kind]()


def fit_score(kind, tgt, hp, Xtr, ytr, Xte):
    pp = Prep().fit(Xtr); A, T = pp(Xtr), pp(Xte); y = ytr.values
    if tgt == "T2":
        mdl = model(kind, hp).fit(A, (y > 0).astype(int)); return mdl.predict_proba(A)[:, 1], mdl.predict_proba(T)[:, 1]
    sy = y.std() if kind == "ENET" else 1.0
    mdl = model(kind, hp).fit(A, y / sy); return mdl.predict(A), mdl.predict(T)


def run_config(kind, tgt, frac, tr, te, X):
    """inner choice of hp on the last training year; refit on full training; cutoff = (1-frac) quantile of training scores."""
    ly = tr.year.max(); ti, va = tr[tr.year < ly], tr[tr.year == ly]; best, bv = None, -np.inf
    for hp in GRID[kind]:
        if len(ti) < 100 or len(va) < 20:
            best = GRID[kind][len(GRID[kind]) // 2]; break
        s_tr, s_va = fit_score(kind, tgt, hp, X.loc[ti.index], ti.usd, X.loc[va.index])
        v = va.usd.values[s_va >= np.quantile(s_tr, 1 - frac)].sum()
        if v > bv:
            bv, best = v, hp
    s_tr, s_te = fit_score(kind, tgt, best, X.loc[tr.index], tr.usd, X.loc[te.index])
    return s_te >= np.quantile(s_tr, 1 - frac), best, bv


def main():
    E = pd.read_parquet(os.path.join(R.OUT, "bank", "CANDIDATE_EVENTS.parquet")); E = E[E[f"usd_{H}"].notna()].copy()
    E["usd"] = E[f"usd_{H}"]; E["usd4"] = E[f"usd4_{H}"]; res, sel_log = [], []
    for cand in CANDS + ["REF_A2_ACD", "REF_ORB15"]:
        D = E[E.candidate == cand].reset_index(drop=True); X = design(D); npop = int((D.year >= 2021).sum())
        te_all = D[D.year >= 2021]; m0 = EC.metrics(te_all.date, te_all.usd, te_all.usd4, npop)
        res.append({"family": cand, "config": "TAKE_ALL", **m0, "tier_b": EC.tier_b(m0)})
        if cand.startswith("REF"):
            continue
        picks = {k: [] for k in CONF}; inner = {k: {} for k in CONF}
        for f, ye in EC.TRAIN_END.items():
            a, b = EC.FOLDS[f]; tr = D[D.year <= ye]; te = D[(D.year >= a) & (D.year <= b)]
            for k, (kind, tgt, frac) in CONF.items():
                s, hp, iv = run_config(kind, tgt, frac, tr, te, X); picks[k].append(te[s]); inner[k][f] = iv
                sel_log.append({"family": cand, "config": k, "fold": f, "hp": hp, "inner_val_usd": iv, "n_sel": int(s.sum()), "n_test": len(te)})
        for k in CONF:
            P_ = pd.concat(picks[k]); m = EC.metrics(P_.date, P_.usd, P_.usd4, npop)
            res.append({"family": cand, "config": k, **m, "tier_b": EC.tier_b(m)})
            R.append("ML_CONFIG_LEDGER.csv", {"family": cand, "config": k, "model": CONF[k][0], "selection": f"{CONF[k][1]}_top{int(CONF[k][2]*100)}", "horizon": H,
                                              "stitched_avg_day": round(m["avg_day"], 3), "slip4_avg_day": round(m["slip4_avg_day"], 3), "folds_pos": m["folds_pos"], "trades": m["trades"]})
        # nested-selected: per fold config with best inner-validation dollars
        ns = []
        for fi, f in enumerate(EC.TRAIN_END):
            kb = max(CONF, key=lambda k: inner[k][f]); ns.append(picks[kb][fi]); sel_log.append({"family": cand, "config": "NESTED_SELECTED", "fold": f, "hp": kb})
        P_ = pd.concat(ns); m = EC.metrics(P_.date, P_.usd, P_.usd4, npop)
        res.append({"family": cand, "config": "NESTED_SELECTED", **m, "tier_b": EC.tier_b(m)}); P_.to_parquet(os.path.join(OUT, f"NESTED_TRADES_{cand}.parquet"))
        for k in CONF:
            pd.concat(picks[k]).to_parquet(os.path.join(OUT, f"TRADES_{cand}_{k}.parquet"))
        print(cand, "take-all", round(m0["avg_day"], 2), "nested", round(m["avg_day"], 2), m["folds_pos"], round(m["slip4_avg_day"], 2), EC.tier_b(m), flush=True)
    Rr = pd.DataFrame(res); Rr.to_csv(os.path.join(OUT, "P3_ML_RESULTS.csv"), index=False); pd.DataFrame(sel_log).to_csv(os.path.join(OUT, "P3_SELECTION_LOG.csv"), index=False)
    pd.set_option("display.width", 250)
    print(Rr[["family", "config", "avg_day", "slip4_avg_day", "trades", "folds_pos", "worst_fold", "remove_top3", "y2022", "max_dd", "corr_main", "coverage", "tier_b"]].round(2).to_string())


if __name__ == "__main__":
    main()
