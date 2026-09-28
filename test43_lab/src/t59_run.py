"""TEST59 hold / overnight inventory, as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import hx_carrier as X  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t53_run import matched_excess, module_trades, simulate  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test59"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = nq.pn.sess; champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess); m = sess >= H.START
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    TR = module_trades(nq, sess)
    TRa = TR.copy(); sel = (TRa["mod"] == "M2") & (TRa.s_out > TRa.s)
    TRa.loc[sel, "s_out"] = TRa.loc[sel, "s"]; TRa.loc[sel, "j_out"] = E.J1615
    ca = np.maximum(0, 3 - np.nan_to_num(pM, nan=3.0)).astype(int)
    rows = []
    for nm, T in (("TEST55 (M2 holds to next open)", TR), ("A: M2 exits 16:15", TRa)):
        daily, L, cnt = simulate(nq, T, 2, -1000.0, cap_arr=ca)
        tot = sum(daily.values()); tot[:s21] = 0
        exc = matched_excess(nq, L); exc[:s21] = 0
        d4 = sum(simulate(nq, T, 2, -1000.0, cap_arr=ca, slip=4.0)[0].values()); d4[:s21] = 0
        qN = np.nan_to_num(pM) + cnt
        mo = float((qN[:, E.J1615 - 1] * bk.m_on["MNQ"] + np.nan_to_num(pE[:, E.J1615 - 1]) * bk.m_on["ES"])[m].max())
        mi = float((qN * bk.m_in["MNQ"][:, None] + np.nan_to_num(pE) * bk.m_in["ES"][:, None])[m].max())
        rows.append({**H.lane_eval(nm, champ + tot, champ, sess, mo, mi, float(exc[s21:].mean()), {"stress4_pos": bool(d4[s21:].sum() > 0), "plateau_pass": True}),
                     "M2_pnl_2021": float(daily["M2"][s21:].sum())})
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T59_M2_hold.csv", index=False)
    diag = []
    for u in (1, 2, 3, 5):
        for intr in (False, True):
            r = X.carrier(mks, bk, [u] * 4, intraday_only=intr)
            d = r["daily"][m]
            on = []
            diag.append({"units": u, "mode": "intraday-only" if intr else "overnight", **{k: v for k, v in P.risk(d).items()},
                         "p5_day": float(np.percentile(d, 5)), "p1_day": float(np.percentile(d, 1)), "p05_day": float(np.percentile(d, 0.5)),
                         "avg_2021": float(r["daily"][sess >= H.SPAN21].mean()), "pre2023": float(r["daily"][m & (sess < pd.Timestamp('2023-01-01'))].mean()),
                         "from2023": float(r["daily"][sess >= pd.Timestamp('2023-01-01')].mean()), "cost_day": float(r["cost"][m].mean())})
    D = pd.DataFrame(diag); D.to_csv(f"{OUT}/T59_overnight_vs_intraday.csv", index=False)
    # locked-overnight gap distribution per 1 MES-eq unit (ES and MNQ legs)
    gaps = {}
    for k, mk in mks.items():
        g = (mk.FP[1:, 0] - mk.FPb[:-1, C45.LOCK_FILL_BAR]) * mk.pv
        g = g[(sess[1:] >= H.START)]; g = g[~np.isnan(g)]
        gaps[k] = {"p5": np.percentile(g, 5), "p1": np.percentile(g, 1), "p0.5": np.percentile(g, 0.5), "worst": g.min(), "mean": g.mean()}
    G = pd.DataFrame(gaps).T; G.to_csv(f"{H.HX}/GAP_LOCK_TAIL_PER_CONTRACT.csv")
    pd.set_option("display.width", 250)
    print(R[["candidate", "incr_avg_day_2021", "max_dd", "worst_day", "ret_dd", "folds_pos", "M2_pnl_2021", "timing_value_day", "GROWTH", "CORE"]].round(3).to_string())
    print(D.round(1).to_string()); print(G.round(1))
    P.budget("TEST59", hypotheses=1, note="hold/overnight")
