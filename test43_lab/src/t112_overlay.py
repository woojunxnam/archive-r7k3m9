"""TEST112 reduce-only portfolio risk overlay on MAIN (prereg 91532f1)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t96_common as C  # noqa: E402
import box_common as B  # noqa: E402
import master_state as S  # noqa: E402
import mp_engine as P  # noqa: E402

OUT = os.path.join(S.OUT, "t112"); os.makedirs(OUT, exist_ok=True)
FOLDS = [("2019-01-01", "2020-12-31"), ("2021-01-01", "2021-12-31"), ("2022-01-01", "2022-12-31"), ("2023-01-01", "2024-12-31"), ("2025-01-01", "2026-12-31")]


def main():
    mc = C.main_ctx(); I = mc["Is"]["MNQ"]; main = mc["main"]; sess = pd.DatetimeIndex(I.sess); full = I.full
    es = P.markets()["ES"].I; es_s = pd.DatetimeIndex(es.sess)
    Hd, Ld = np.nanmax(es.H, 1), np.nanmin(es.L, 1); Cd = es.C[:, P.E.J15]
    df = pd.DataFrame({"rg": Hd - Ld, "c": Cd}, index=es_s)
    st = pd.DataFrame(index=es_s)
    st["R1"] = (df.rg.rolling(5).mean() / df.rg.rolling(60).mean()).shift(1)
    st["R2"] = (df.c / df.c.rolling(50).mean() - 1).shift(1)
    st["R3"] = (df.c / df.c.rolling(20).max() - 1).shift(1)
    st = st.reindex(sess)
    per = sess.to_period("M"); rows, cur = [], []
    for k in ("R1", "R2", "R3"):
        x = st[k].values; q = np.full(len(x), -1)
        for mo in per.unique():
            r = np.where(per == mo)[0]
            if r[0] < 120:
                continue
            v = x[:r[0]][full[:r[0]]]; v = v[~np.isnan(v)]
            e = np.percentile(v, [20, 40, 60, 80]); q[r] = np.where(np.isnan(x[r]), -1, np.digitize(np.nan_to_num(x[r]), e))
        ok = full & (q >= 0); bm = [float(main[ok & (q == b)].mean()) for b in range(5)]
        for b in range(5):
            cur.append({"state": k, "bin": b, "n": int((ok & (q == b)).sum()), "main_mean": bm[b]})
        rho = float(spearmanr(range(5), bm)[0]); wb, bb = int(np.argmin(bm)), int(np.argmax(bm))
        rng = np.random.default_rng(7); w = main[ok & (q == wb)]; bt = main[ok & (q == bb)]
        bs = [rng.choice(bt, len(bt)).mean() - rng.choice(w, len(w)).mean() for _ in range(2000)]; lo, hi = np.percentile(bs, [2.5, 97.5])
        yrs = sess.year.values; ys = [np.sign(main[ok & (q == bb) & (yrs == y)].mean() - main[ok & (q == wb) & (yrs == y)].mean()) for y in np.unique(yrs[ok])]
        coh = abs(rho) >= 0.9 and (lo > 0) and sum(s > 0 for s in ys) >= 5
        o = {"state": k, "spearman": rho, "worst_bin": wb, "worst_mean": bm[wb], "best_minus_worst": bm[bb] - bm[wb], "ci_lo": lo, "ci_hi": hi,
             "years_same_sign": int(sum(s > 0 for s in ys)), "COHERENT": bool(coh)}
        if coh and bm[wb] < 0:
            red = ok & (q == wb); d = np.where(red, 0.5 * main, main); rm, ro = B.risk(main[full]), B.risk(d[full])
            fm = [float(main[red & (sess >= a) & (sess <= b)].mean()) for a, b in FOLDS]
            o.update({"overlay_avg_day": ro["avg_day"], "overlay_maxdd": ro["max_dd"], "overlay_worst": ro["worst_day"], "overlay_ret_dd": ro["ret_dd"],
                      "main_ret_dd": rm["ret_dd"], "halved_fold_means": str([round(v, 1) for v in fm]),
                      "OVERLAY_VALUE": bool(ro["ret_dd"] >= 1.05 * rm["ret_dd"] and ro["max_dd"] <= rm["max_dd"] and ro["worst_day"] >= rm["worst_day"] and sum(v < 0 for v in fm) >= 4)})
        else:
            o["OVERLAY_VALUE"] = False; o["rule"] = "NOT APPLIED (not coherent or worst bin >= 0)"
        rows.append(o)
    R = pd.DataFrame(rows); Cu = pd.DataFrame(cur); R.to_csv(os.path.join(OUT, "TEST112_OVERLAY.csv"), index=False); Cu.to_csv(os.path.join(OUT, "TEST112_CURVES.csv"), index=False)
    pd.set_option("display.width", 250); print(Cu.round(2).to_string()); print(R.round(4).to_string())
    json.dump({"ledger_rows": len(Cu), "definitions_new": 3, "overlay_value": R.OVERLAY_VALUE.tolist()}, open(os.path.join(OUT, "T112_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
