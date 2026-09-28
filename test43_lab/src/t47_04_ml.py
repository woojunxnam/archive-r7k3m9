"""TEST47 ML (T47_29 .. T47_32).  Separate tasks, chronological expanding walk-forward by calendar year (test years 2021 ..
2026-05-27, training = all earlier years from 2019-07), identical folds for every model, small fixed presets (TEST45 zoo).
ML-A  rebound value after N3 (event pool = union of T1..T4 default N3 events, E1 fill, target = +60m matched excess, ATRd)
ML-B  value after NB true-bottom confirmation (C4 events, NB fill)
ML-C  incremental value of the SECOND contract (NR-A confirmed adds, REC50 campaign exit): target = second-lot P&L
ML-D  incremental value of the recycle TRIM (NR-C): target = trim price - final campaign exit price (value of trimming)
ML-E  conditional overnight value of unresolved inventory (REC50 campaigns unresolved at 16:15)
Sequence diagnostic: small regularised 1D CNN on the 24 completed 5m bars ending at the trigger (pooled ES+NQ), same folds.
PREDECLARED sequence rule: justified only if (a) first-fold training sample >= 2000 events and (b) it beats the best tabular
model on outer-fold rank IC AND on taken-P&L."""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_common as C  # noqa: E402
import t47_engine as E  # noqa: E402
from t45_04_ml import models  # noqa: E402
from t47_02_n3 import START, Fwd, cfg, ctx15, event_table  # noqa: E402

warnings.filterwarnings("ignore")
OUT = os.path.join(C.T47, "ml"); os.makedirs(OUT, exist_ok=True)
YEARS = range(2021, 2027)


def feats(mk, e):
    s = e.s.values; b = e.b.values; u = mk.u5[s]; a = mk.atr[s]
    rng = mk.h[s, b] - mk.l[s, b]
    l15, b15 = ctx15(mk, e)
    rv = np.array([np.nanstd(np.diff(mk.c[si, max(0, bi - 12):bi + 1])) for si, bi in zip(s, b)]) / u
    F = pd.DataFrame({
        "f_leg1": e.leg1.values, "f_leg2": e.leg2.values, "f_leg3": e.leg3.values,
        "f_r21": e.leg2.values / e.leg1.values, "f_r32": e.leg3.values / e.leg2.values, "f_cum": e.cum.values, "f_dur": e.dur.values,
        "f_vel": e.cum.values / e.dur.values, "f_neutral": e.n_neutral.values, "f_maxrec": np.clip(e.max_rec.values, -2, 2), "f_nup": e.n_up.values,
        "f_wick": np.where(rng > 0, (np.minimum(mk.o[s, b], mk.c[s, b]) - mk.l[s, b]) / np.where(rng > 0, rng, 1), 0),
        "f_body": (mk.c[s, b] - mk.o[s, b]) / u, "f_cloc": np.where(rng > 0, (mk.c[s, b] - mk.l[s, b]) / np.where(rng > 0, rng, 1), 0.5),
        "f_rv5": rv, "f_l15": l15, "f_b15": b15.astype(float), "f_tod": b.astype(float),
        "f_dopen": (mk.c[s, b] - mk.open[s]) / a, "f_dtwap": (mk.c[s, b] - mk.twap[s, b]) / u, "f_rally": np.nan_to_num(e.rally30.values),
        "f_accel": (e.leg3.values >= 2 * e.leg2.values).astype(float), "f_gap": mk.gap[s], "f_ret5": mk.ret5[s], "f_volt": mk.volt[s],
        "f_bull": mk.bull[s].astype(float), "f_u5atr": u / a, "f_inst": float(mk.inst == "MNQ")})
    return F.replace([np.inf, -np.inf], np.nan)


def seq_tensor(mk, e, W=24):
    X = np.zeros((len(e), 3, W))
    for i, (s, b) in enumerate(zip(e.s.values, e.b.values)):
        u = mk.u5[s]
        for q in range(W):
            k = b - W + 1 + q
            if k < 1 or np.isnan(mk.c[s, k]):
                continue
            X[i, 0, q] = (mk.c[s, k] - mk.c[s, k - 1]) / u
            X[i, 1, q] = (mk.h[s, k] - mk.l[s, k]) / u
            r = mk.h[s, k] - mk.l[s, k]
            X[i, 2, q] = (mk.c[s, k] - mk.l[s, k]) / r - 0.5 if r > 0 else 0
    return np.clip(np.nan_to_num(X), -5, 5)


def wf(D, fcols, mname, Z, target="y"):
    pred = np.full(len(D), np.nan)
    for yv in YEARS:
        tr = D[D.year < yv].dropna(subset=fcols + [target]); te = (D.year == yv).values
        if len(tr) < 150 or te.sum() == 0:
            continue
        X = tr[fcols].fillna(0).values; y = np.clip(tr[target].values, -3, 3)
        m = Z[mname]()
        if mname == "LOGISTIC":
            m.fit(X, (y > 0).astype(int)); p = m.predict_proba(D.loc[te, fcols].fillna(0).values)[:, 1] - 0.5
        else:
            m.fit(X, y); p = m.predict(D.loc[te, fcols].fillna(0).values)
        pred[te] = p
    return pred


def cnn_wf(D, X):
    import torch
    torch.set_num_threads(4)
    pred = np.full(len(D), np.nan); ntrain = {}
    for yv in YEARS:
        tr = np.where((D.year < yv).values & D.y.notna().values)[0]; te = np.where((D.year == yv).values)[0]
        ntrain[yv] = len(tr)
        if len(tr) < 500 or len(te) == 0:
            continue
        ps = []
        for seed in (1, 2, 3):
            torch.manual_seed(seed)
            net = torch.nn.Sequential(torch.nn.Conv1d(3, 8, 3), torch.nn.ReLU(), torch.nn.Dropout(0.3), torch.nn.Conv1d(8, 8, 3), torch.nn.ReLU(),
                                      torch.nn.AdaptiveAvgPool1d(1), torch.nn.Flatten(), torch.nn.Linear(8, 1))
            opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=0.05)
            xt = torch.tensor(X[tr], dtype=torch.float32); yt = torch.tensor(np.clip(D.y.values[tr], -3, 3), dtype=torch.float32)[:, None]
            for ep in range(30):
                perm = torch.randperm(len(tr))
                for i0 in range(0, len(tr), 256):
                    idx = perm[i0:i0 + 256]
                    opt.zero_grad(); loss = torch.nn.functional.mse_loss(net(xt[idx]), yt[idx]); loss.backward(); opt.step()
            net.eval()
            with torch.no_grad():
                ps.append(net(torch.tensor(X[te], dtype=torch.float32)).numpy().ravel())
        pred[te] = np.mean(ps, 0)
    return pred, ntrain


def evaluate(D, pred, name, task, pnl="pnl", yv="y"):
    ok = ~np.isnan(pred)
    d = D[ok]; p = pred[ok]
    if len(d) < 20:
        return {"task": task, "model": name, "n": int(len(d))}
    dec = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False).values
    top = d[yv].values[dec == 9].mean(); bot = d[yv].values[dec == 0].mean()
    cal = np.polyfit(p, np.clip(d[yv].values, -3, 3), 1)[0] if np.std(p) > 0 else np.nan
    t = d[p > 0]
    daily = t.groupby("date")[pnl].sum()
    eq = np.r_[0, np.cumsum(daily.values)]; mdd = float((np.maximum.accumulate(eq) - eq).max()) if len(daily) else 0
    yr = t.groupby("year")[pnl].sum()
    return {"task": task, "model": name, "n": int(len(d)), "rankIC": spearmanr(p, d[yv]).statistic, "calib_slope": cal,
            "top_decile_y": top, "bottom_decile_y": bot, "taken": len(t), "taken_pnl": float(t[pnl].sum()), "all_pnl": float(d[pnl].sum()),
            "incr_vs_take_all": float(t[pnl].sum() - d[pnl].sum()), "taken_maxdd": mdd, "years_pos": int((yr > 0).sum()), "years": len(yr),
            "cost_taken": float(t.get("cost", pd.Series(0, index=t.index)).sum())}


def main():
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    Z = models()
    zoo = [m for m in ("RIDGE", "ELASTIC_NET", "LOGISTIC", "EXTRA_TREES", "RANDOM_FOREST", "HIST_GB", "XGBOOST", "CATBOOST", "LIGHTGBM") if m in Z]
    res, abl = [], []
    pools, seqs = [], []
    for k, mk in mks.items():
        fw = Fwd(mk)
        evs = []
        for leg in ("T1", "T2", "T3", "T4"):
            ev, _, _ = E.run_detect(mk, cfg(leg=leg)); ev["leg_def"] = leg; evs.append(ev)
        ev = pd.concat(evs).drop_duplicates(["s", "b"]).sort_values(["s", "b"]).reset_index(drop=True)
        ev = ev[mk.pn.sess[ev.s.values] >= START].reset_index(drop=True)
        T = event_table(mk, fw, ev)
        Tt = E.trades(mk, ev, "E1", "X60", overlap=True)
        T = T.merge(Tt[["s", "b", "pnl"]], on=["s", "b"], how="inner")
        T["y"] = T["+60m"] - T["+60m_base"]; T["inst"] = k
        F = feats(mk, T); F.index = T.index
        D = pd.concat([T[["s", "b", "date", "year", "inst", "leg_def", "y", "pnl"]], F], axis=1)
        pools.append(D); seqs.append(seq_tensor(mk, T))
    DA = pd.concat(pools, ignore_index=True); XS = np.concatenate(seqs)
    DA["cost"] = np.where(DA.inst == "ES", 2 * C45.cost_side(0), 2 * C45.cost_side(1))
    fc = [c for c in DA.columns if c.startswith("f_")]
    # deterministic control C2 inside the pool (T1 events) and take-all
    for inst in ("ES", "MNQ", "ALL"):
        d = DA if inst == "ALL" else DA[DA.inst == inst]
        d = d[d.year >= 2021]
        res.append({"task": "ML-A", "model": f"CONTROL take-all pool [{inst}]", "n": len(d), "taken": len(d), "taken_pnl": d.pnl.sum(),
                    "years_pos": int((d.groupby("year").pnl.sum() > 0).sum())})
        c2 = d[d.leg_def == "T1"]
        res.append({"task": "ML-A", "model": f"CONTROL C2 (T1 N3) [{inst}]", "n": len(c2), "taken": len(c2), "taken_pnl": c2.pnl.sum(),
                    "years_pos": int((c2.groupby("year").pnl.sum() > 0).sum())})
    preds = {}
    for mname in zoo:
        p = wf(DA, fc, mname, Z); preds[mname] = p
        res.append(evaluate(DA, p, mname, "ML-A"))
        for inst in ("ES", "MNQ"):
            m = (DA.inst == inst).values
            res.append(evaluate(DA[m], p[m], f"{mname} [{inst}]", "ML-A"))
        print(res[-3], flush=True)
    # ablation (RIDGE, HIST_GB): path-shape vs context blocks
    blocks = {"path shape (legs, ratios, cum, dur, vel, neutral, rec, nup)": ["f_leg1", "f_leg2", "f_leg3", "f_r21", "f_r32", "f_cum", "f_dur", "f_vel", "f_neutral", "f_maxrec", "f_nup"],
              "bar structure (wick, body, cloc)": ["f_wick", "f_body", "f_cloc"], "15m context": ["f_l15", "f_b15"],
              "regime (gap, ret5, volt, bull, rv5, u5atr)": ["f_gap", "f_ret5", "f_volt", "f_bull", "f_rv5", "f_u5atr"],
              "location (tod, dopen, dtwap, rally)": ["f_tod", "f_dopen", "f_dtwap", "f_rally"]}
    for mname in ("RIDGE", "HIST_GB"):
        for bn, cols in blocks.items():
            p = wf(DA, [c for c in fc if c not in cols], mname, Z)
            ev_ = evaluate(DA, p, mname, "ML-A"); abl.append({"model": mname, "dropped": bn, "rankIC": ev_["rankIC"], "taken_pnl": ev_["taken_pnl"]})
        p = wf(DA, blocks["path shape (legs, ratios, cum, dur, vel, neutral, rec, nup)"], mname, Z)
        ev_ = evaluate(DA, p, mname, "ML-A"); abl.append({"model": mname, "dropped": "ONLY path shape kept", "rankIC": ev_["rankIC"], "taken_pnl": ev_["taken_pnl"]})
    # sequence model diagnostic
    ps, ntr = cnn_wf(DA, XS)
    seq = evaluate(DA, ps, "SEQ_CNN_1D (24x3 bars)", "SEQ")
    seq["first_fold_train_n"] = ntr[2021]
    res.append(seq)
    # ---------------- ML-B (NB)
    poolsB = []
    for k, mk in mks.items():
        fw = Fwd(mk)
        ev, _, _ = E.run_detect(mk, cfg()); ev = ev[mk.pn.sess[ev.s.values] >= START].reset_index(drop=True)
        T = event_table(mk, fw, ev, "NB")
        Tt = E.trades(mk, ev, "NB", "X60", overlap=True)
        T = T.merge(Tt[["s", "b", "pnl"]], on=["s", "b"], how="inner")
        T["y"] = T["+60m"] - T["+60m_base"]; T["inst"] = k
        F = feats(mk, T); F.index = T.index
        poolsB.append(pd.concat([T[["s", "b", "date", "year", "inst", "y", "pnl"]], F], axis=1))
    DB = pd.concat(poolsB, ignore_index=True)
    d = DB[DB.year >= 2021]
    res.append({"task": "ML-B", "model": "CONTROL C4 take-all NB", "n": len(d), "taken": len(d), "taken_pnl": d.pnl.sum(), "years_pos": int((d.groupby("year").pnl.sum() > 0).sum())})
    for mname in zoo:
        res.append(evaluate(DB, wf(DB, fc, mname, Z), mname, "ML-B"))
    # ---------------- ML-C / ML-D / ML-E (campaign decisions)
    pc, pd_, pe = [], [], []
    for k, mk in mks.items():
        ev, _, legm = E.run_detect(mk, cfg()); ev = ev[mk.pn.sess[ev.s.values] >= START].reset_index(drop=True)
        F = feats(mk, ev); F["s"] = ev.s.values; F["b"] = ev.b.values
        base = {"s": ev.s.values}
        L, Cm = E.run_campaign(mk, ev, legm, exit="REC50", add="confirmed")
        L = L.merge(Cm[["camp", "b", "px0"]], on="camp")
        sec = L[L.type == 1].copy()
        sec["y"] = sec.pnl / (mk.pv * mk.atr[sec.s.values]); sec["dd_add"] = (sec.px_in - sec.px0) / mk.u5[sec.s.values]
        sec["min_since"] = sec.j_in - Cm.set_index("camp").j0.reindex(sec.camp).values
        pc.append(sec.merge(F, on=["s", "b"]).assign(inst=k))
        L2, C2 = E.run_campaign(mk, ev, legm, exit="REC50", add="confirmed", trim=True)
        fin = L2[(L2.type == 0)].set_index("camp").px_out
        tr = L2[L2.exit_type == 1].copy()
        tr = tr.merge(C2[["camp", "b"]], on="camp")
        tr["value"] = (tr.px_out - fin.reindex(tr.camp).values) * mk.pv
        tr["y"] = tr.value / (mk.pv * mk.atr[tr.s.values]); tr["gain_trim"] = (tr.px_out - tr.px_in) / mk.u5[tr.s.values]
        pd_.append(tr.merge(F, on=["s", "b"]).assign(inst=k, pnl=tr.value.values))
        L3, C3 = E.run_campaign(mk, ev, legm, exit="REC50")
        un = C3[(C3.unresolved == 1) & (C3.s + 1 < mk.n)].copy()
        on = (mk.FP[un.s.values + 1, 0] - mk.FPb[un.s.values, E.J1615]) * mk.pv - 2 * C45.cost_side(mk.k)
        un["pnl"] = on; un["y"] = on / (mk.pv * mk.atr[un.s.values])
        un["dist_tgt"] = (un.target - mk.FPb[un.s.values, E.J1615]) / mk.u5[un.s.values]
        un["day_ret"] = (mk.FPb[un.s.values, E.J1615] - mk.open[un.s.values]) / mk.atr[un.s.values]
        pe.append(un.merge(F, on=["s", "b"]).assign(inst=k))
    small = ["RIDGE", "LOGISTIC", "EXTRA_TREES", "HIST_GB"]
    for task, parts, extra in (("ML-C second contract", pc, ["dd_add", "min_since"]), ("ML-D recycle trim", pd_, ["gain_trim"]),
                               ("ML-E unresolved overnight", pe, ["dist_tgt", "day_ret"])):
        D = pd.concat(parts, ignore_index=True)
        D["date"] = D.s.map(lambda x: x); D["year"] = pd.DatetimeIndex(es.pn.sess[D.s.values]).year
        fcx = fc + extra
        d = D[D.year >= 2021]
        res.append({"task": task, "model": "CONTROL always (add / trim / hold)", "n": len(d), "taken": len(d), "taken_pnl": d.pnl.sum(),
                    "years_pos": int((d.groupby("year").pnl.sum() > 0).sum())})
        for mname in small:
            res.append(evaluate(D, wf(D, fcx, mname, Z), mname, task))
    R = pd.DataFrame(res); R.to_csv(f"{OUT}/T47_29_30_ml_walkforward.csv", index=False)
    A = pd.DataFrame(abl); A.to_csv(f"{OUT}/T47_31_ml_ablation.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
    print(R[["task", "model", "n", "rankIC", "calib_slope", "top_decile_y", "bottom_decile_y", "taken", "taken_pnl", "incr_vs_take_all", "years_pos"]].round(3).to_string())
    print(A.round(3).to_string())


if __name__ == "__main__":
    main()
