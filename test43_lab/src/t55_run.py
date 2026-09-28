"""T55 CAPACITY AUDIT (C43, C43-GROWTH) + TEST55 residual-capacity allocator, as preregistered."""
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

OUT = os.path.join(C45.ROOT, "out", "test55"); os.makedirs(OUT, exist_ok=True)
PCT = [50, 75, 90, 95, 99, 100]


def dist(x, name):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return {"metric": name, "mean": x.mean(), **{f"p{p}" if p < 100 else "max": np.percentile(x, p) for p in PCT}}


def audit(bk, qE, qN, label, sess):
    """qE/qN: per session x grid positions.  Intraday margin over RTH minutes, overnight margin at the 16:14 lock."""
    m = np.asarray(sess >= H.START)
    qE, qN = np.nan_to_num(qE[m]), np.nan_to_num(qN[m])
    mi = qE * bk.m_in["ES"][m, None] + qN * bk.m_in["MNQ"][m, None]
    lock = E.J1615 - 1
    mo = qE[:, lock] * bk.m_on["ES"][m] + qN[:, lock] * bk.m_on["MNQ"][m]
    atr = qE * bk.atr_d["ES"][m, None] + qN * bk.atr_d["MNQ"][m, None]
    notional = qE * bk.notional["ES"][m, None] + qN * bk.notional["MNQ"][m, None]
    units = bk.mes_units(qE, qN) if False else qE + qN * (bk.atr_d["MNQ"][m] / bk.atr_d["ES"][m])[:, None]
    rows = [dist(qE.ravel(), "MES contracts (RTH minutes)"), dist(qN.ravel(), "MNQ contracts (RTH minutes)"),
            dist(units.ravel(), "MES-equivalent risk units"), dist(mi.ravel() / H.NLV, "intraday initial margin / NLV"),
            dist(mo / H.NLV, "overnight initial margin / NLV (16:15 lock)"), dist(atr.ravel(), "ATR-dollar exposure ($)"),
            dist(notional.ravel(), "notional exposure ($)")]
    D = pd.DataFrame(rows); D.insert(0, "portfolio", label)
    share = {"portfolio": label, **{f"time_intraday_margin_lt_{int(b * 100)}%": float((mi.ravel() / H.NLV < b).mean()) for b in (0.2, 0.3, 0.4, 0.5)},
             **{f"sessions_overnight_margin_lt_{int(b * 100)}%": float((mo / H.NLV < b).mean()) for b in (0.2, 0.3, 0.4, 0.5)}}
    return D, share, float(mo.max()), float(mi.max())


def main():
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    bk = H.Book(mks)
    sess = nq.pn.sess
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess)
    TR = module_trades(nq, sess)
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))

    def ens(cap_total=None, gov=-1000.0, **kw):
        ca = None if cap_total is None else np.maximum(0, cap_total - np.nan_to_num(pM, nan=float(cap_total))).astype(int)
        daily, L, cnt = simulate(nq, TR, 2, gov, cap_arr=ca, **kw)
        tot = sum(daily.values()); tot[:s21] = 0
        return tot, L, cnt
    # ---------------- capacity audit
    Dc, sc, moc, mic = audit(bk, pE, pM, "C43-CORE", sess)
    tG, LG, cG = ens(None)
    cG = cG.astype(float); cG[:s21] = 0
    Dg, sg, mog, mig = audit(bk, pE, np.nan_to_num(pM) + cG, "C43-GROWTH (C43 + TEST53, 2021+ ensemble)", sess)
    AUD = pd.concat([Dc, Dg], ignore_index=True); SH = pd.DataFrame([sc, sg])
    AUD.to_csv(f"{H.HX}/CAPACITY_AUDIT.csv", index=False); SH.to_csv(f"{H.HX}/MARGIN_UTILIZATION.csv", index=False)
    AUD[AUD.metric.str.contains("contracts|units")].to_csv(f"{H.HX}/EXPOSURE_UTILIZATION.csv", index=False)
    AUD[AUD.metric.str.contains("ATR")].to_csv(f"{H.HX}/ATR_RISK_UTILIZATION.csv", index=False)
    pd.set_option("display.width", 250)
    print(AUD.round(3).to_string()); print(SH.round(3).to_string())
    # ---------------- TEST55
    rows = []
    variants = [("C43 + TEST53 (no total cap) = C43-GROWTH shadow", None), ("total MNQ<=2 (TEST54)", 2), ("total MNQ<=3 PRIMARY", 3),
                ("total MNQ<=4 (report only)", 4), ("total MNQ<=5 (reference)", 5)]
    res = {}
    for nm, cap in variants:
        tot, L, cnt = ens(cap)
        exc = matched_excess(nq, L); exc[:s21] = 0
        qN = np.nan_to_num(pM) + cnt
        mo = (qN[:, E.J1615 - 1] * bk.m_on["MNQ"] + np.nan_to_num(pE[:, E.J1615 - 1]) * bk.m_on["ES"])[sess >= H.START].max()
        mi = ((qN * bk.m_in["MNQ"][:, None] + np.nan_to_num(pE) * bk.m_in["ES"][:, None])[sess >= H.START]).max()
        extra = {}
        if cap == 3:
            pl = [float(ens(3, g)[0][s21:].sum()) for g in (-800.0, -900.0, -1100.0, -1200.0)] + [float(ens(c)[0][s21:].sum()) for c in (2, 4)]
            base = float(tot[s21:].sum())
            extra["plateau_pass"] = bool(all(v > 0 and v >= 0.6 * base for v in pl)); extra["plateau_totals"] = str([round(v) for v in pl])
            extra["stress4_pos"] = bool(ens(3, slip=4.0)[0][s21:].sum() > 0)
        else:
            extra["plateau_pass"] = False; extra["stress4_pos"] = bool(ens(cap, slip=4.0)[0][s21:].sum() > 0)
        row = H.lane_eval(nm, champ + tot, champ, sess, mo, mi, float(exc[s21:].mean()), extra)
        row.update({"peak_total_MNQ": int(qN[sess >= H.SPAN21].max()), "ensemble_trades": int(len(L[L.s_in >= s21]))})
        rows.append(row); res[nm] = tot
    c43row = H.lane_eval("C43 only", champ, champ, sess, moc, mic, 0.0, {})
    R = pd.DataFrame([c43row] + rows); R.to_csv(f"{OUT}/T55_results.csv", index=False)
    cols = ["candidate", "avg_day_full", "avg_day_2021", "incr_avg_day_2021", "max_dd", "worst_day", "ret_dd", "folds_pos", "fold_median", "remove_top3_incr",
            "max_year_share", "peak_on_margin_frac", "peak_total_MNQ", "timing_value_day", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "CORE", "GROWTH", "AGGRESSIVE_REPORT"]
    print(R[[c for c in cols if c in R.columns]].round(4).to_string())
    print(R.get("plateau_totals"))
    P.budget("TEST55", hypotheses=1, finalists=int(R.GROWTH.sum() + R.CORE.sum()), note="residual capacity allocator")


if __name__ == "__main__":
    main()
