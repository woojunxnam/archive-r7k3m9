"""RUN-4 Sleeve A §12: "will this recycle entry become deeply trapped?" (NOT bottom prediction).

Signals: every RTH decision bar where the FQ recycle anchor fires (low60 touch + >= 0.25 ATR15 bounce), policy
independent. Outcome of a hypothetical 1-lot recycle trade (market entry next open + 1 tick, TP +3 limit, EXEC-1.1
fills, held until TP or data end): hold time, MAE before TP.
Labels: hold > 1/5/20/60 days, MAE > 10/20 pts, MAE > 0.5/1/2 ATR15 (before TP).
Chronological walk-forward folds (test year Y = 2021..2026, train on signals whose label was RESOLVED before Jan 1 of
Y: purged). Models: single-feature rules, additive flag score, logistic, L1-logistic, depth-3 tree.
Outputs: results/RUN4_OVERNIGHT/trap/*.csv and data/cache/r4_trap_scores.npz (causal per-bar percentile scores used
by the soft price-improvement filter; NaN where no prior-fold model exists)."""
import os, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.events import event_features
from mesgrid import fastsim as fs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "RUN4_OVERNIGHT", "trap")
os.makedirs(OUT, exist_ok=True)
DAY = 1440.0


def main():
    t0 = time.time()
    b = load_canonical()
    F = compute_features(b, b.v)
    nxt, last_td, nil, dtm = fs.day_structure(b)
    W = np.flatnonzero(b.in_window)
    lo_prev = np.concatenate([[np.nan], F["low60"][W][:-1]])
    anc = (b.l[W] <= lo_prev) & (b.c[W] >= b.l[W] + 0.25 * F["atr15"][W])
    sig = W[anc]
    sig = sig[nxt[sig] & ~nil[sig] & b.tradeable[sig]]
    B = 1024
    g = fs.tp_trigger_array(b, 1)
    ei, xi, ep, hold, mae = fs.rec_outcomes(sig, 3.0, b.o, b.h, b.l, g, fs.block_max(g, B), fs.block_min(b.l, B), B,
                                           b.tradeable, nxt, dtm, 1, 1)
    ok = ei >= 0
    sig, ei, xi, ep, hold, mae = sig[ok], ei[ok], xi[ok], ep[ok], hold[ok], mae[ok]
    a15 = np.maximum(F["atr15"][sig], 0.25)
    resolved_t = np.where(xi >= 0, dtm[np.maximum(xi, 0)], np.iinfo(np.int64).max)     # minute when TP happened
    ent_t = dtm[ei]
    lab = {"hold_1d": hold > 1 * DAY, "hold_5d": hold > 5 * DAY, "hold_20d": hold > 20 * DAY, "hold_60d": hold > 60 * DAY,
           "mae_10pt": mae > 10, "mae_20pt": mae > 20, "mae_0.5atr": mae > 0.5 * a15, "mae_1atr": mae > 1 * a15, "mae_2atr": mae > 2 * a15}
    # ---------------- causal features at the signal bar
    X = event_features(b, F).set_index("idx")
    Xs = X.loc[sig]
    fe = pd.DataFrame(index=np.arange(len(sig)))
    fe["rpos1d"] = Xs.rpos1d.values
    fe["rpos5d"] = Xs.rpos5d.values
    sh, sl = F["sess_high"][sig], F["sess_low"][sig]
    fe["sess_rpos"] = np.where(sh - sl > 0, (b.c[sig] - sl) / np.maximum(sh - sl, 0.25), 0.5)
    fe["vwap_dev_atr"] = Xs.vwap_dev_atr.values
    fe["sess_ret_atr"] = (b.c[sig] - F["day_open"][sig]) / a15
    dfd = pd.DataFrame({"d": b.day[W], "c": b.c[W]}).groupby("d").c.last()
    prevret = (dfd - dfd.shift(1)).shift(1)                 # previous day's RTH return (known before today)
    fe["prevday_ret_datr"] = pd.Series(b.day[sig]).map(prevret).values / np.maximum(F["datr"][sig], 1)
    fe["datr_pct"] = F["datr_pct"][sig]
    fe["rvol_ratio"] = F["rvol_ratio"][sig]
    fe["tod_min"] = b.minute[sig]
    for N in (15, 30, 60):
        fe[f"mom{N}_atr"] = np.nan_to_num(F[f"mom{N}"][sig]) / a15
    fe["lower_lows"] = F["lower_lows"][sig].astype(float)
    fe["down_persist"] = Xs.down_trend_persist.values.astype(float)
    fe["dist_sesslow_atr"] = (b.c[sig] - sl) / a15
    fe["dist_pdl_atr"] = Xs.dist_pdl_atr.values
    fe["gap_atr"] = Xs.gap_atr.values
    fe["atr15"] = a15
    fe = fe.replace([np.inf, -np.inf], np.nan).fillna(fe.median())
    year = (b.day[sig] // 10000).astype(int)
    rows, fold_rows = [], []
    scores = {}
    feats = list(fe.columns)
    for ln, y in lab.items():
        y = y.astype(int)
        base = y.mean()
        # single-feature pooled AUC (direction-free |AUC-0.5|) as transparent-rule screen
        for f in feats:
            try:
                a = roc_auc_score(y, fe[f])
            except ValueError:
                a = np.nan
            rows.append(dict(label=ln, model="single:" + f, auc_pooled=a, base_rate=base))
        oof = {m: np.full(len(y), np.nan) for m in ("logit", "l1", "tree", "flags")}
        for Y in range(2021, 2027):
            start = np.int64(pd.Timestamp(f"{Y}-01-01").value // 60_000_000_000)
            end = np.int64(pd.Timestamp(f"{Y + 1}-01-01").value // 60_000_000_000)
            test = (ent_t >= start) & (ent_t < end)
            # purge: training label must be known before the test year starts
            if ln.startswith("hold_"):
                H = float(ln.split("_")[1][:-1]) * DAY
                known = (resolved_t < start) | (ent_t + H < start)
            else:
                known = resolved_t < start          # MAE-before-TP fully known only once TP happened
            tr = (ent_t < start) & known
            if tr.sum() < 500 or y[tr].min() == y[tr].max() or test.sum() < 50:
                continue
            sc = StandardScaler().fit(fe[tr])
            Xtr, Xte = sc.transform(fe[tr]), sc.transform(fe[test])
            m1 = LogisticRegression(max_iter=500).fit(Xtr, y[tr])
            m2 = LogisticRegression(max_iter=500, penalty="l1", C=0.05, solver="liblinear").fit(Xtr, y[tr])
            m3 = DecisionTreeClassifier(max_depth=3, min_samples_leaf=200).fit(fe[tr], y[tr])
            # additive flags: sign-aligned top-5 single features chosen on TRAIN only, split at train median
            aucs = {f: roc_auc_score(y[tr], fe[f][tr]) for f in feats}
            top = sorted(feats, key=lambda f: -abs(aucs[f] - 0.5))[:5]
            fl = np.zeros(test.sum())
            for f in top:
                med = fe[f][tr].median()
                fl += (fe[f][test] > med).values if aucs[f] > 0.5 else (fe[f][test] <= med).values
            oof["logit"][test] = m1.predict_proba(Xte)[:, 1]
            oof["l1"][test] = m2.predict_proba(Xte)[:, 1]
            oof["tree"][test] = m3.predict_proba(fe[test])[:, 1]
            oof["flags"][test] = fl
            for mname in oof:
                s_ = oof[mname][test]
                try:
                    a = roc_auc_score(y[test], s_)
                except ValueError:
                    a = np.nan
                # top-decile trap rate vs base
                q = np.quantile(s_, 0.9)
                fold_rows.append(dict(label=ln, model=mname, test_year=Y, n_train=int(tr.sum()), n_test=int(test.sum()),
                                      base_rate_test=float(y[test].mean()), auc=a,
                                      top10_rate=float(y[test][s_ >= q].mean()), bottom50_rate=float(y[test][s_ <= np.median(s_)].mean())))
            if ln in ("hold_5d", "hold_20d", "mae_2atr", "mae_20pt"):
                # causal per-bar score for the test year: percentile of the model's probability vs the TRAIN distribution
                ptr = np.sort(m1.predict_proba(Xtr)[:, 1])
                for kind, mdl in (("lr", m1),):
                    key = f"trap_{kind}_{ln}"
                    if key not in scores:
                        scores[key] = np.full(len(b), np.nan)
                    # score every RTH bar of year Y (features at all bars) -> only the recycle-signal bars matter in use
                    scores[key][sig[test]] = np.searchsorted(ptr, mdl.predict_proba(Xte)[:, 1]) / len(ptr)
        for mname, s_ in oof.items():
            mm = np.isfinite(s_)
            if mm.sum() > 100 and y[mm].min() != y[mm].max():
                rows.append(dict(label=ln, model="oof:" + mname, auc_pooled=roc_auc_score(y[mm], s_[mm]), base_rate=float(y[mm].mean()),
                                 n=int(mm.sum())))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "trap_auc_summary.csv"), index=False)
    pd.DataFrame(fold_rows).to_csv(os.path.join(OUT, "trap_folds.csv"), index=False)
    out = pd.DataFrame(dict(sig=sig, year=year, hold_min=hold, mae=mae, **{k: v.astype(int) for k, v in lab.items()}))
    out.to_parquet(os.path.join(OUT, "recycle_signal_outcomes.parquet"), index=False)
    # the score is only defined at recycle-signal bars; carry it to the next decision bars (score known at signal close)
    np.savez_compressed(os.path.join(ROOT, "data", "cache", "r4_trap_scores.npz"), **scores)
    print("signals", len(sig), "labels base rates", {k: round(float(v.mean()), 3) for k, v in lab.items()})
    fr = pd.DataFrame(fold_rows)
    print(fr.groupby(["label", "model"]).auc.agg(["mean", "min", "max"]).round(3).to_string())
    print(pd.DataFrame(rows).query("model.str.startswith('oof')", engine="python").round(3).to_string(index=False))
    print("total", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
