"""TEST46 ML (T46_22..24).  ML-A bottom quality on a broad pool of structural-rebound events (Lane B, production-compatible);
ML-B hold extension and ML-D strategy-specific overnight on Lane A ledger trades (RESEARCH-ONLY, seeds PARITY_BLOCKED);
ML-C (pyramid add) and ML-E (next-open inventory) are not fitted: too few add events / no carried-inventory product (documented).
Chronological expanding walk-forward by calendar year (first test year 2021), 1-session purge; small fixed presets."""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t46_common as C  # noqa: E402
import t46_rebound as R  # noqa: E402
from t45_04_ml import models  # noqa: E402
from t46_03_laneB import setup  # noqa: E402

warnings.filterwarnings("ignore")
OUT = os.path.join(C.T46, "ml"); os.makedirs(OUT, exist_ok=True)
BROAD = dict(D=0.3, delta=0.0, k=1, N=12, rho=0.0, e0=2, e1=66, veto5=99.0, vetogap=99.0, need_bull=0, band=1.5, relx=0.3)


def event_pool(es, nq, rel):
    rows = []
    for fam in range(1, 8):
        for mk in (es, nq):
            if fam == 7 and mk is es:
                continue
            ev, brk = R.run_detect(mk, fam, BROAD, rel if fam == 7 else None)
            pnl, ji, jo = R.run_trades(mk, ev, brk, 1, 0, -1.0)
            s = np.where(ev >= 0)[0]
            for si in s:
                e = ev[si]; a = mk.atr[si]; j = 5 * (e + 1)
                if j >= C45.NG or np.isnan(mk.FP[si, j]):
                    continue
                rows.append({"s": si, "date": mk.pn.sess[si], "year": mk.pn.sess[si].year, "fam": fam, "inst": mk.inst, "pnl": pnl[si],
                             "y": (mk.FPb[si, C45.g("16:00")] - mk.FP[si, j]) / a,
                             "f_disp": (mk.open[si] - np.nanmin(mk.l[si, :e + 1])) / a, "f_depth": (brk[si] - np.nanmin(mk.l[si, :e + 1])) / a,
                             "f_time": e, "f_vwapdist": (mk.c[si, e] - mk.vw[si, e]) / a, "f_volpct": mk.volt[si], "f_bull": float(mk.bull[si]),
                             "f_ret5": mk.ret5[si], "f_gap": mk.gap[si], "f_rel": rel[si, e] if mk.inst == "MNQ" else 0.0,
                             "f_rng": (np.nanmax(mk.h[si, :e + 1]) - np.nanmin(mk.l[si, :e + 1])) / a, "f_inst": float(mk.inst == "MNQ"),
                             **{f"f_fam{q}": float(fam == q) for q in range(1, 8)}})
    E = pd.DataFrame(rows)
    # one event per (inst, session): keep the earliest
    E = E.sort_values(["inst", "s", "f_time"]).drop_duplicates(["inst", "s"]).reset_index(drop=True)
    return E


def wf(E, feats, mname, Z):
    pred = np.full(len(E), np.nan)
    for yv in range(2021, 2027):
        tr = E[E.year < yv].dropna(subset=feats + ["y"]); te = E.year == yv
        if len(tr) < 200 or te.sum() == 0:
            continue
        X = tr[feats].values; y = np.clip(tr.y.values, -3, 3)
        m = Z[mname]()
        if mname == "LOGISTIC":
            m.fit(X, (y > 0).astype(int)); p = m.predict_proba(E.loc[te, feats].values)[:, 1] - 0.5
        else:
            m.fit(X, y); p = m.predict(E.loc[te, feats].values)
        pred[te.values] = p
    return pred


def main():
    P, es, nq, rel = setup()
    E = event_pool(es, nq, rel)
    feats = [c for c in E.columns if c.startswith("f_")]
    Z = models()
    rows = []
    span = E.year >= 2021
    base = E[span]
    rows.append({"task": "ML-A bottom quality", "model": "SIMPLE CONTROL: take every broad event", "n": int(span.sum()),
                 "rankIC": np.nan, "taken": int(span.sum()), "avg_pnl_taken": base.pnl.mean(), "total_pnl_taken": base.pnl.sum(),
                 "years_positive": int((base.groupby("year").pnl.sum() > 0).sum())})
    abl = []
    for mname in Z:
        pred = wf(E, feats, mname, Z)
        ok = ~np.isnan(pred)
        t = E[ok & (pred > 0)]
        rows.append({"task": "ML-A bottom quality", "model": mname, "n": int(ok.sum()), "rankIC": spearmanr(pred[ok], E.y[ok]).statistic,
                     "taken": len(t), "avg_pnl_taken": t.pnl.mean(), "total_pnl_taken": t.pnl.sum(),
                     "years_positive": int((t.groupby("year").pnl.sum() > 0).sum())})
        if mname in ("RIDGE", "HIST_GB"):
            for fam_name, cols in (("displacement/structure", ["f_disp", "f_depth", "f_rng"]), ("regime", ["f_volpct", "f_bull", "f_ret5", "f_gap"]),
                                   ("relative ES/NQ", ["f_rel"]), ("family id", [f"f_fam{q}" for q in range(1, 8)]), ("VWAP/time", ["f_vwapdist", "f_time"])):
                fs = [f for f in feats if f not in cols]
                pr = wf(E, fs, mname, Z); ok2 = ~np.isnan(pr)
                t2 = E[ok2 & (pr > 0)]
                abl.append({"model": mname, "dropped": fam_name, "rankIC": spearmanr(pr[ok2], E.y[ok2]).statistic, "taken": len(t2),
                            "total_pnl_taken": t2.pnl.sum()})
        print(rows[-1], flush=True)
    # ML-B / ML-D research-only on Lane A trades
    T = pd.read_parquet(os.path.join(C.T46, "laneA", "laneA_trades.parquet"))
    T["year"] = pd.DatetimeIndex(T.date).year
    for task, target in (("ML-B hold extension (research-only)", T["H_16:00"] - T["e0"]), ("ML-D overnight carry (research-only)", T["H_next 09:30"] - T["H_16:15"])):
        D = T.assign(y=target.values, f_j=T.j, f_seed=T.seed.astype("category").cat.codes).dropna(subset=["y"])
        f2 = ["f_j", "f_seed"]
        for mname in ("RIDGE", "HIST_GB"):
            pred = np.full(len(D), np.nan)
            for yv in range(2021, 2027):
                tr = D[D.year < yv]; te = (D.year == yv).values
                if len(tr) < 100 or te.sum() == 0:
                    continue
                m = Z[mname](); m.fit(tr[f2].values, np.clip(tr.y.values, -3000, 3000)); pred[te] = m.predict(D.loc[te, f2].values)
            ok = ~np.isnan(pred)
            rows.append({"task": task, "model": mname, "n": int(ok.sum()), "rankIC": spearmanr(pred[ok], D.y[ok]).statistic,
                         "taken": int((pred[ok] > 0).sum()), "avg_pnl_taken": float(D.y[ok][pred[ok] > 0].mean()),
                         "total_pnl_taken": float(D.y[ok][pred[ok] > 0].sum()), "years_positive": np.nan})
        rows.append({"task": task, "model": "SIMPLE CONTROL: always extend", "n": int(len(D[D.year >= 2021])), "rankIC": np.nan,
                     "taken": int(len(D[D.year >= 2021])), "avg_pnl_taken": float(D[D.year >= 2021].y.mean()),
                     "total_pnl_taken": float(D[D.year >= 2021].y.sum()), "years_positive": np.nan})
    rows.append({"task": "ML-C pyramid add", "model": "NOT FITTED", "n": 0, "note": "add events per rule < 100 on 2019-2026 (T46_07..10)"})
    rows.append({"task": "ML-E next-open inventory", "model": "NOT FITTED", "n": 0, "note": "no carried-inventory product survives (Lane A research-only, Lane B intraday)"})
    R_ = pd.DataFrame(rows); R_.to_csv(f"{OUT}/T46_23_ml_walkforward.csv", index=False)
    pd.DataFrame(abl).to_csv(f"{OUT}/T46_24_ml_ablation.csv", index=False)
    E.to_parquet(f"{OUT}/mlA_event_pool.parquet")
    pd.set_option("display.width", 250)
    print(R_.round(3).to_string()); print(pd.DataFrame(abl).round(3).to_string())


if __name__ == "__main__":
    main()
