"""TEST60 marginal-exposure ML, as preregistered."""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import hx_carrier as X  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t45_04_ml import models  # noqa: E402

warnings.filterwarnings("ignore")
OUT = os.path.join(C45.ROOT, "out", "test60"); os.makedirs(OUT, exist_ok=True)


def feats(mk, prefix):
    c = pd.Series(mk.pn.cash_close).ffill(); a = pd.Series(mk.pn.atr).ffill()
    F = pd.DataFrame({f"{prefix}_r1": (c - c.shift(1)) / a, f"{prefix}_r5": (c - c.shift(5)) / a, f"{prefix}_r20": (c - c.shift(20)) / a,
                      f"{prefix}_d20": (c - c.rolling(20).mean()) / a, f"{prefix}_d50": (c - c.rolling(50).mean()) / a, f"{prefix}_d100": (c - c.rolling(100, min_periods=60).mean()) / a,
                      f"{prefix}_dd60": (c.rolling(60, min_periods=20).max() - c) / a, f"{prefix}_atrchg": a / a.shift(5) - 1,
                      f"{prefix}_cloc": (pd.Series(mk.pn.rth_last) - pd.Series(mk.pn.rth_l)) / (pd.Series(mk.pn.rth_h) - pd.Series(mk.pn.rth_l)),
                      f"{prefix}_rng": (pd.Series(mk.pn.rth_h) - pd.Series(mk.pn.rth_l)) / a})
    F = F.shift(1)                              # known before the open
    F[f"{prefix}_volp"] = pd.Series(mk.pn.vol_pct).values     # already previous-session
    return F


def main():
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = es.pn.sess; champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    st = pd.read_csv(os.path.join(C45.ROOT, "out/t45/baseline/champion_session_state.csv"), index_col=0, parse_dates=True).reindex(sess).fillna(0)
    D = pd.concat([feats(es, "es"), feats(nq, "nq")], axis=1)
    D["c43_pES"] = st.pES_end.shift(1).values; D["c43_pMNQ"] = st.pMNQ_end.shift(1).values; D["wd"] = sess.weekday
    # label: open->next open P&L of 1 MES-eq unit (0.5 ES + 0.5 unit MNQ)
    ratio = bk.atr_d["ES"] / bk.atr_d["MNQ"]
    nE = np.r_[es.FP[1:, 0], np.nan] - es.FP[:, 0]; nN = np.r_[nq.FP[1:, 0], np.nan] - nq.FP[:, 0]
    D["y_raw"] = 0.5 * nE * es.pv + 0.5 * ratio * nN * nq.pv
    D["year"] = sess.year; D["ok"] = (sess >= H.START) & D.y_raw.notna().values
    fc = [c for c in D.columns if c not in ("y_raw", "year", "ok")]
    Z = models(); zoo = ["RIDGE", "LOGISTIC", "EXTRA_TREES", "HIST_GB"]
    preds = {}
    for mn in zoo:
        p = np.full(len(D), np.nan)
        for yv in range(2021, 2027):
            tr = D[D.ok & (D.year < yv)]; te = (D.ok & (D.year == yv)).values
            if len(tr) < 250 or te.sum() == 0:
                continue
            y = tr.y_raw.values - tr.y_raw.mean(); y = y / y.std()
            m = Z[mn]()
            if mn == "LOGISTIC":
                m.fit(tr[fc].fillna(0).values, (y > 0).astype(int)); p[te] = m.predict_proba(D.loc[te, fc].fillna(0).values)[:, 1] - 0.5
            else:
                m.fit(tr[fc].fillna(0).values, np.clip(y, -3, 3)); p[te] = m.predict(D.loc[te, fc].fillna(0).values) - np.median(m.predict(tr[fc].fillna(0).values))
        preds[mn] = p
    preds["CONSENSUS"] = np.where(np.isnan(preds["RIDGE"]), np.nan, np.where((preds["RIDGE"] > 0) & (preds["LOGISTIC"] > 0), 1.0, -1.0))
    base = X.carrier(mks, bk, [3] * 4)
    rows = []
    for mn, p in preds.items():
        ok = ~np.isnan(p)
        ic = spearmanr(p[ok], D.y_raw.values[ok]).statistic if mn != "CONSENSUS" else np.nan
        for pol in ("ML-B_ADD", "ML-C_REDUCE"):
            u = np.full(len(D), 3.0)
            if pol == "ML-B_ADD":
                u[ok & (p > 0)] = 5.0
            else:
                u[ok & (p < 0)] = 1.0
            u[sess < H.SPAN21] = 3.0
            r = X.carrier(mks, bk, [0, 0, 0, 0])  # placeholder to get structure
            qE, qN = X.units_to_contracts(bk, u, 0.5)
            rE, rN = X._run(es.sim, nq.sim, qE, qN, 0, False, 1.0)
            d = rE["pnl"] + rN["pnl"]
            inc = d - base["daily"]
            yrs = pd.Series(inc[sess >= H.SPAN21], index=sess[sess >= H.SPAN21]).groupby(sess[sess >= H.SPAN21].year).mean()
            rows.append({"model": mn, "policy": pol, "rankIC": ic, "timing_vs_CONST3_day": float(inc[sess >= H.SPAN21].mean()),
                         "years_pos": int((yrs > 0).sum()), "years": len(yrs), **{f"y{k}": v for k, v in yrs.items()},
                         "policy_avg_day_2021": float(d[sess >= H.SPAN21].mean()), "policy_worst_2021": float(d[sess >= H.SPAN21].min())})
        print(mn, round(ic, 4) if ic == ic else ic, flush=True)
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T60_results.csv", index=False)
    pd.set_option("display.width", 250); print(R.round(3).to_string())
    P.budget("TEST60", hypotheses=2, ml_configs=len(zoo) + 1, note="marginal exposure ML")


if __name__ == "__main__":
    main()
