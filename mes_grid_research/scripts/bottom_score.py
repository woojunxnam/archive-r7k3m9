"""RUN-3 F/U: transparent BottomScore and chronological-fold logistic / shallow tree models.
Component selection uses ONLY 2019-2021 evidence; later splits are evaluation (NOT true OOS: whole dataset was seen in RUN-2)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = pd.read_parquet(os.path.join(ROOT, "data", "cache", "fwd_outcomes.parquet"))
X = pd.read_parquet(os.path.join(ROOT, "data", "cache", "event_features.parquet"))
D = pd.concat([O.reset_index(drop=True), X.drop(columns=["idx"]).reset_index(drop=True)], axis=1)
D = D[D.tradeable & D["win_3.0_3.0"].notna()].copy()
D["split"] = pd.cut(D.year, [2018, 2021, 2022, 2024, 2026], labels=["s1_2019_21", "s2_2022", "s3_2023_24", "s4_2025_26"]).astype(str)
base = D.groupby("split")["win_3.0_3.0"].mean()
# candidate binary components (one per family)
cand = {
    "LOC rpos60<=0.05": D.rpos60 <= 0.05, "LOC rpos120<=0.05": D.rpos120 <= 0.05, "LOC vwap_dev<=-1.5": D.vwap_dev_atr <= -1.5,
    "EXH newlow_weak_close": D.newlow_weak_close.astype(bool), "EXH consec_down>=4": D.consec_down >= 4,
    "REV bull_engulf": D.bull_engulf.astype(bool), "REV close_upper25": D.close_upper25.astype(bool), "REV sweep_reclaim_sess": D.sweep_reclaim_sess.astype(bool),
    "VOL normal": D.volreg == "NORMAL", "TOD 1000-1330": D.tod.isin(["1000_1130", "1130_1330"]), "CTX not_persist": ~D.down_trend_persist.astype(bool),
}
s1 = D.split == "s1_2019_21"
sel = {}
for k, v in cand.items():
    lift = D.loc[s1 & v, "win_3.0_3.0"].mean() - D.loc[s1, "win_3.0_3.0"].mean()
    if lift > 0:
        sel[k] = v
print("components selected on 2019-21 only:", list(sel))
fam = {}
for k, v in sel.items():
    fam.setdefault(k.split()[0], []).append(v)
comp = pd.DataFrame({f: np.logical_or.reduce(vs) for f, vs in fam.items()})
D["score"] = 100 * comp.mean(axis=1).values
rows = []
for thr in (0, 50, 60, 70, 80, 100):
    m = D.score >= thr
    for sp in ["s1_2019_21", "s2_2022", "s3_2023_24", "s4_2025_26"]:
        ss = D[m & (D.split == sp)]
        rows.append(dict(model="BottomScore_equal", thr=thr, split=sp, n=len(ss), p3=ss["win_3.0_3.0"].mean(), lift=ss["win_3.0_3.0"].mean() - base[sp],
                         p5_10=ss["win_5.0_10.0"].mean(), mae15=ss.mae15.mean(), t_reb=ss["t_reb2.5"].median()))
sc = pd.DataFrame(rows)
# chronological models
feats = ["vwap_dev_atr", "vwap_z", "sess_dd_atr", "prev_close_dd_atr", "dist_pdl_atr", "rpos15", "rpos30", "rpos60", "rpos120", "rpos1d", "rpos5d",
         "consec_down", "dist_ema20_atr", "wick_body_ratio", "slope30_atr", "slope60_atr", "eff_ratio30", "gap_atr", "datr_pct", "minute"]
Z = D[feats].replace([np.inf, -np.inf], np.nan).fillna(0).clip(-20, 20)
y = D["win_3.0_3.0"].astype(int)
mr = []
folds = [(["s1_2019_21"], "s2_2022"), (["s1_2019_21", "s2_2022"], "s3_2023_24"), (["s1_2019_21", "s2_2022", "s3_2023_24"], "s4_2025_26")]
for tr_sp, te_sp in folds:
    tr = D.split.isin(tr_sp).values; te = (D.split == te_sp).values
    for nm, mdl in (("logit_l2", LogisticRegression(C=0.1, max_iter=500)), ("tree_d3", DecisionTreeClassifier(max_depth=3, min_samples_leaf=5000)),
                    ("gbm_shallow", HistGradientBoostingClassifier(max_depth=3, max_iter=100, learning_rate=0.05))):
        mdl.fit(Z[tr], y[tr])
        p = mdl.predict_proba(Z[te])[:, 1]
        auc = roc_auc_score(y[te], p)
        q = np.quantile(p, [0.8, 0.95])
        top = p >= q[1]; top20 = p >= q[0]
        mr.append(dict(model=nm, train=",".join(tr_sp), test=te_sp, auc=auc, base_p3=y[te].mean(),
                       top20_p3=y[te][top20].mean(), top5_p3=y[te][top].mean(), top5_mae15=D.mae15.values[te][top].mean()))
mr = pd.DataFrame(mr)
os.makedirs(os.path.join(ROOT, "results", "RUN3_BOTTOM"), exist_ok=True)
sc.to_csv(os.path.join(ROOT, "results", "RUN3_BOTTOM", "bottom_score.csv"), index=False)
mr.to_csv(os.path.join(ROOT, "results", "RUN3_BOTTOM", "chrono_models.csv"), index=False)
pd.set_option("display.width", 220)
print(sc.pivot(index="thr", columns="split", values="lift").round(4)); print(sc.pivot(index="thr", columns="split", values="n"))
print(mr.round(4).to_string(index=False))
