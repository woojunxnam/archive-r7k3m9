"""TEST58 lot-size ladder of the TEST53 modules in the residual architecture, as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t53_run import matched_excess, module_trades, simulate  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test58"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = nq.pn.sess; champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess)
    TR = module_trades(nq, sess)
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    pMn = np.nan_to_num(pM, nan=3.0)

    def run(k, gov=-1000.0, **kw):
        T = 3 + 2 * (k - 1)
        ca = np.minimum(2, np.floor(np.maximum(0, T - pMn) / k)).astype(int)
        daily, L, cnt = simulate(nq, TR, 2, gov, cap_arr=ca, **kw)
        tot = k * sum(daily.values()); tot[:s21] = 0
        return tot, L, k * cnt
    rows, curve = [], []
    prev = None
    for k in (1, 2, 3, 5):
        tot, L, cnt = run(k)
        exc = k * matched_excess(nq, L); exc[:s21] = 0
        qN = np.nan_to_num(pM) + cnt
        m = sess >= H.START
        mo = float((qN[:, E.J1615 - 1] * bk.m_on["MNQ"] + np.nan_to_num(pE[:, E.J1615 - 1]) * bk.m_on["ES"])[m].max())
        mi = float((qN * bk.m_in["MNQ"][:, None] + np.nan_to_num(pE) * bk.m_in["ES"][:, None])[m].max())
        ex = {"stress4_pos": bool(run(k, slip=4.0)[0][s21:].sum() > 0)}
        if k == 2:
            base = float(tot[s21:].sum())
            pl = [float(run(kk)[0][s21:].sum()) for kk in (1, 3)] + [float(run(2, g)[0][s21:].sum()) for g in (-800.0, -1200.0)]
            ex["plateau_pass"] = bool(all(v > 0 and v >= 0.6 * base for v in pl)); ex["plateau_totals"] = str([round(v) for v in pl])
        row = H.lane_eval(f"C43 + TEST53 x{k} (residual)", champ + tot, champ, sess, mo, mi, float(exc[s21:].mean()), ex)
        row.update({"k": k, "peak_total_MNQ": int(qN[sess >= H.SPAN21].max()), "avg_ensemble_MNQ_rth": float(cnt[s21:].mean())})
        rows.append(row)
        r = P.risk(tot[s21:])
        curve.append({"k": k, "incr_avg_day_2021": r["avg_day"], "module_max_dd": r["max_dd"], "module_worst_day": r["worst_day"],
                      "marginal_avg_day_vs_prev": r["avg_day"] - (prev or 0), "comb_max_dd_full": row["max_dd"], "comb_worst_full": row["worst_day"]})
        prev = r["avg_day"]
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T58_results.csv", index=False)
    CV = pd.DataFrame(curve); CV.to_csv(f"{H.HX}/MARGINAL_EXPOSURE_CURVE_TEST53.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["candidate", "avg_day_full", "avg_day_2021", "incr_avg_day_2021", "max_dd", "worst_day", "ret_dd", "folds_pos", "fold_median", "remove_top3_incr",
            "max_year_share", "peak_on_margin_frac", "peak_total_MNQ", "timing_value_day", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "CORE", "GROWTH", "AGGRESSIVE_REPORT"]
    print(R[cols].round(4).to_string()); print(R.get("plateau_totals")); print(CV.round(2))
    P.budget("TEST58", hypotheses=1, finalists=int(R.GROWTH.sum()), note="TEST53 lot ladder")
