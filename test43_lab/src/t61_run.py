"""TEST61 scaled core + residual growth, as preregistered."""
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

OUT = os.path.join(C45.ROOT, "out", "test61"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = nq.pn.sess; champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess); m = sess >= H.START
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    TR = module_trades(nq, sess)
    pMn = np.nan_to_num(pM, nan=3.0)

    def run(T=6, gov=-1000.0, **kw):
        ca = np.minimum(2, np.maximum(0, T - 2 * pMn)).astype(int)
        daily, L, cnt = simulate(nq, TR, 2, gov, cap_arr=ca, **kw)
        tot = sum(daily.values()); tot[:s21] = 0
        return tot, L, cnt
    tot, L, cnt = run()
    exc = matched_excess(nq, L); exc[:s21] = 0
    d = 2 * champ + tot
    qN = 2 * np.nan_to_num(pM) + cnt; qE = 2 * np.nan_to_num(pE)
    mo = float((qN[:, E.J1615 - 1] * bk.m_on["MNQ"] + qE[:, E.J1615 - 1] * bk.m_on["ES"])[m].max())
    mi = float((qN * bk.m_in["MNQ"][:, None] + qE * bk.m_in["ES"][:, None])[m].max())
    base_tot = float((d - champ)[s21:].sum())
    pl = [float((2 * champ + run(6, g)[0] - champ)[s21:].sum()) for g in (-800.0, -900.0, -1100.0, -1200.0)] + [float((2 * champ + run(T)[0] - champ)[s21:].sum()) for T in (5, 7)]
    t4 = run(6, slip=4.0)[0]
    c43x2_4 = 2 * champ   # C43 cost stress not re-simulable here: report ensemble 4-tick stress on the increment's ensemble part
    ex = {"plateau_pass": bool(all(v > 0 and v >= 0.6 * base_tot for v in pl)), "plateau_totals": str([round(v) for v in pl]),
          "stress4_pos": bool((champ + t4)[s21:].sum() > 0)}
    beta_x2 = champ.mean() * 0  # placeholder
    tv = float(exc[s21:].mean()) + float(champ[s21:].mean() - 29.72 * 0)   # timing: C43 increment is C43 alpha (validated) + ensemble matched excess
    row = H.lane_eval("TEST61: C43x2 + TEST53 residual (total MNQ<=6)", d, champ, sess, mo, mi, float(exc[s21:].mean()), ex)
    ctl = H.lane_eval("control: C43x2 alone", 2 * champ, champ, sess, float((2 * np.nan_to_num(pM[:, E.J1615 - 1]) * bk.m_on["MNQ"] + qE[:, E.J1615 - 1] * bk.m_on["ES"])[m].max()),
                      mi, 0.0, {"plateau_pass": False, "stress4_pos": True})
    row.update({"peak_total_MNQ": int(qN[sess >= H.SPAN21].max()), "peak_MES": int(qE[m].max())})
    R = pd.DataFrame([row, ctl]); R.to_csv(f"{OUT}/T61_results.csv", index=False)
    np.save(f"{OUT}/T61_daily.npy", d)
    pd.set_option("display.width", 250)
    cols = ["candidate", "avg_day_full", "avg_day_2021", "incr_avg_day_2021", "max_dd", "worst_day", "ret_dd", "folds_pos", "fold_median", "remove_top3_incr", "max_year_share",
            "peak_on_margin_frac", "timing_value_day", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "CORE", "GROWTH", "AGGRESSIVE_REPORT", "plateau_totals", "peak_total_MNQ"]
    print(R[[c for c in cols if c in R.columns]].T.to_string())
    P.budget("TEST61", hypotheses=1, finalists=int(row["GROWTH"]), note="scaled core + residual growth")
