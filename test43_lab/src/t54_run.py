"""TEST54: TEST53 ensemble inside one total MNQ target (C43 + ensemble <= 2), exactly as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t53_run import matched_excess, module_trades, simulate  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test54"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    es, nq = E.setup()
    sess = nq.pn.sess
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess)
    capa = np.maximum(0, 2 - np.nan_to_num(pM, nan=2.0)).astype(int)
    TR = module_trades(nq, sess)
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))

    def run(gov=-1000.0, **kw):
        daily, L, cnt = simulate(nq, TR, 2, gov, cap_arr=capa, **kw)
        tot = sum(daily.values()); tot[:s21] = 0
        return tot, daily, L, cnt
    tot, daily, L, cnt = run()
    L.to_csv(f"{OUT}/T54_ledger.csv", index=False)
    exc = matched_excess(nq, L); exc[:s21] = 0
    PL = pd.DataFrame([{"gov": g, "total_2021": float(run(g)[0][s21:].sum())} for g in (-800.0, -900.0, -1000.0, -1100.0, -1200.0)])
    base = float(tot[s21:].sum())
    plateau = bool((PL.total_2021 > 0).all() and (PL.total_2021 >= 0.6 * base).all())
    ST = pd.DataFrame([{"stress": nm, "avg_day": float(run(**kw)[0][s21:].mean())} for nm, kw in
                       (("base", {}), ("+5min entry delay", {"delay": 5}), ("4-tick slippage", {"slip": 4.0}), ("20% missed entries", {"miss": 0.2}))])
    rec = sum(daily[m][s21:].sum() > 0 for m in daily)
    row = P.evaluate_module("TEST54 ensemble in total MNQ<=2", tot, exc, sess, champ,
                            {"plateau_pass": plateau, "recurrence_pass": rec >= 3, "stress4_pos": bool(ST.avg_day[2] > 0)})
    tm = np.nan_to_num(pM) + cnt
    row.update({"peak_total_MNQ_incl_C43": int(tm[s21:].max()), "minutes_total_gt2_share": float((tm[s21:] > 2).mean()),
                "minutes_total_gt2_due_to_C43_alone": float((np.nan_to_num(pM)[s21:] > 2).mean()), "modules_positive": int(rec),
                "trades": int(len(L[L.s_in >= s21])), "signals": int(len(TR[TR.s >= s21]))})
    pd.DataFrame([row]).to_csv(f"{OUT}/T54_gate.csv", index=False); PL.to_csv(f"{OUT}/T54_plateau.csv", index=False); ST.to_csv(f"{OUT}/T54_stress.csv", index=False)
    attr = pd.DataFrame({m: {"total_2021": float(d[s21:].sum()), "avg_day": float(d[s21:].mean())} for m, d in daily.items()}).T
    attr.to_csv(f"{OUT}/T54_attribution.csv"); np.save(f"{OUT}/T54_daily.npy", np.stack([tot, exc]))
    yr = pd.Series(tot[s21:], index=sess[s21:]).groupby(sess[s21:].year).agg(["sum", "mean"]); yr.to_csv(f"{OUT}/T54_years.csv")
    for k in ["folds_pos", "fold_median", "fold_worst", "standalone_avg_day", "standalone_max_dd", "standalone_worst_day", "matched_excess_day", "corr_C43",
              "comb_avg_day", "comb_max_dd", "comb_worst_day", "comb_ret_dd", "C43_ret_dd", "max_year_share", "remove_top3", "remove_top5", "roll12m_pos_share",
              "peak_total_MNQ_incl_C43", "minutes_total_gt2_share", "minutes_total_gt2_due_to_C43_alone", "modules_positive", "trades", "signals"] + [f"G{i}" for i in range(1, 10)] + ["PASS"]:
        print(k, round(row[k], 4) if isinstance(row[k], float) else row[k])
    print(attr.round(2)); print(PL.round(1)); print(ST.round(2)); print(yr.round(1))
    P.budget("TEST54", hypotheses=1, finalists=int(row["PASS"]), note="ensemble in total MNQ<=2")
