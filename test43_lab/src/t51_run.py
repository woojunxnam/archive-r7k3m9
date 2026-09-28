"""TEST51 position-sizing meta-labeling on C43 (1->2 ADD, 1->0 CUT), exactly as preregistered."""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t45_04_ml import models  # noqa: E402
from prog_01_gapmap import features  # noqa: E402
from t47_02_n3 import START, tstat  # noqa: E402

warnings.filterwarnings("ignore")
OUT = os.path.join(C45.ROOT, "out", "test51"); os.makedirs(OUT, exist_ok=True)
TIMES = [f"{h:02d}:{m:02d}" for h in range(10, 16) for m in (0, 30)]


def build():
    es, nq = E.setup()
    sess = es.pn.sess
    pE, pM = P.c43_positions(sess)
    rows = []
    for mk, pos, pos_o, other in ((es, pE, pM, nq), (nq, pM, pE, es)):
        key = mk.year * 100 + mk.vt * 10 + mk.bull.astype(int)
        groups = {k: np.where(key == k)[0] for k in np.unique(key)}
        cs = C45.cost_side(mk.k)
        for s in np.where((sess >= START) & (mk.atr > 0))[0]:
            for t in TIMES:
                j = C45.g(t); jf = j + 1
                if pos[s, j] != 1 or np.isnan(mk.FP[s, jf]):
                    continue
                ch = np.where(pos[s, jf:E.J1615] != pos[s, j])[0]
                jx = jf + int(ch[0]) if len(ch) else E.J1615
                if jx <= jf:
                    continue
                mv = (mk.FPb[s, jx] - mk.FP[s, jf]) * mk.pv
                idx = groups[key[s]]
                mbase = np.nanmean((mk.FPb[idx, jx] - mk.FP[idx, jf]) * mk.pv)
                last = np.where(pos[s, :j + 1] != pos[s, j])[0]
                r = {"inst": mk.inst, "s": s, "date": sess[s], "year": sess[s].year, "time": t, "j": j, "jx": jx,
                     "add_pnl": mv - 2 * cs, "cut_pnl": -mv - 2 * cs, "add_exc": mv - mbase, "y": (mv - mbase) / (mk.pv * mk.atr[s]),
                     "f_pos_other": pos_o[s, j], "f_since_change": j - (int(last[-1]) if len(last) else -30), "f_tod": j}
                ro = (mk.pn.Cf[s, j] - mk.open[s]) / mk.atr[s] - (other.pn.Cf[s, j] - other.open[s]) / other.atr[s]
                try:
                    r.update({("f" + k[1:]): v for k, v in features(mk, s, j, ro).items()})
                except ValueError:                                  # no RTH bars yet in this session (data gap)
                    continue
                rows.append(r)
    D = pd.DataFrame(rows)
    D.to_parquet(f"{OUT}/T51_sizing_rows.parquet")
    return D, es, nq


def wf(D, fc, mname, Z):
    pred = np.full(len(D), np.nan)
    for yv in range(2021, 2027):
        tr = D[(D.year < yv)].dropna(subset=["y"]); te = (D.year == yv).values
        if len(tr) < 300 or te.sum() == 0:
            continue
        X = tr[fc].fillna(0).values; y = np.clip(tr.y.values, -3, 3)
        m = Z[mname]()
        if mname == "LOGISTIC":
            m.fit(X, (y > 0).astype(int)); p = m.predict_proba(D.loc[te, fc].fillna(0).values)[:, 1] - 0.5
        else:
            m.fit(X, y); p = m.predict(D.loc[te, fc].fillna(0).values)
            p = p - np.median(m.predict(X))                    # standardise within training: 0 = training median prediction
        pred[te] = p
    return pred


def module(D, take, col, n):
    """first qualifying decision per (inst, session) -> daily $ (both instruments summed) and daily matched excess."""
    T = D[take].sort_values(["inst", "s", "j"]).drop_duplicates(["inst", "s"])
    d = np.zeros(n); x = np.zeros(n)
    np.add.at(d, T.s.values, T[col].values)
    sign = 1 if col == "add_pnl" else -1
    np.add.at(x, T.s.values, sign * T.add_exc.values - (0 if sign == 1 else 0))
    return d, x, T


def main():
    D, es, nq = build()
    sess = es.pn.sess; champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    fc = [c for c in D.columns if c.startswith("f_")]
    Z = models()
    zoo = [m for m in ("RIDGE", "ELASTIC_NET", "LOGISTIC", "RANDOM_FOREST", "EXTRA_TREES", "HIST_GB", "XGBOOST", "CATBOOST", "LIGHTGBM") if m in Z]
    rows, preds = [], {}
    oos = D.year >= 2021
    for inst_sel in ("ALL", "ES", "MNQ"):
        Dm = D if inst_sel == "ALL" else D[D.inst == inst_sel]
        ctl = {"ALWAYS_ADD": np.ones(len(Dm), bool), "SIMPLE_RULE (ret>0 & bull)": ((Dm.x_ret_open if "x_ret_open" in Dm else Dm.f_ret_open) > 0).values & (Dm.f_bull > 0).values}
        for nm, take in ctl.items():
            d, x, T = module(Dm, take & (Dm.year >= 2019).values, "add_pnl", len(sess))
            rows.append({"inst": inst_sel, "decision": "ADD", "model": nm, **P.evaluate_module(nm, d, x, sess, champ, {"plateau_pass": True})})
    for mname in zoo:
        p = wf(D, fc, mname, Z); preds[mname] = p
        ok = ~np.isnan(p)
        ic = spearmanr(p[ok], D.y.values[ok]).statistic
        for dec, take, col in (("ADD", p > 0, "add_pnl"), ("CUT", p < 0, "cut_pnl")):
            for inst_sel in ("ALL", "ES", "MNQ"):
                m = ok & take & ((D.inst == inst_sel).values if inst_sel != "ALL" else True)
                d, x, T = module(D, m, col, len(sess))
                if dec == "CUT":
                    x = -x
                o = P.evaluate_module(f"{mname} {dec} [{inst_sel}]", d, x, sess, champ, {"plateau_pass": True})
                rows.append({"inst": inst_sel, "decision": dec, "model": mname, "rankIC": ic, "overlays": len(T), **o})
        print(mname, round(ic, 4), flush=True)
    # simple ensemble (only if both Ridge and Logistic have positive IC)
    icr = spearmanr(preds["RIDGE"][oos], D.y[oos]).statistic; icl = spearmanr(preds["LOGISTIC"][oos], D.y[oos]).statistic
    if icr > 0 and icl > 0:
        z = lambda a: (a - np.nanmean(a)) / np.nanstd(a)
        pe = 0.5 * (z(preds["RIDGE"]) + z(preds["LOGISTIC"]))
        d, x, T = module(D, ~np.isnan(pe) & (pe > 0), "add_pnl", len(sess))
        rows.append({"inst": "ALL", "decision": "ADD", "model": "ENSEMBLE ridge+logistic", "rankIC": spearmanr(pe[oos], D.y[oos]).statistic,
                     "overlays": len(T), **P.evaluate_module("ENSEMBLE ADD", d, x, sess, champ, {"plateau_pass": True})})
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T51_results.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    cols = ["inst", "decision", "model", "rankIC", "overlays", "standalone_avg_day", "matched_excess_day", "folds_pos", "fold_median", "corr_C43",
            "comb_ret_dd", "C43_ret_dd", "comb_worst_day", "remove_top3", "G1", "G2", "G4", "G7", "G8", "PASS"]
    print(R[[c for c in cols if c in R.columns]].round(4).to_string())
    P.budget("TEST51", hypotheses=2, ml_configs=len(zoo) + 1, finalists=int(R.PASS.sum()), note="sizing meta-labeling on C43")


if __name__ == "__main__":
    main()
