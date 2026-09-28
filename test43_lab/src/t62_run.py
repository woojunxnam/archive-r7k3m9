"""TEST62 ES diversification (frozen TEST53 rules on ES), as preregistered."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t53_run import matched_excess, module_trades  # noqa: E402
from t61r1_validate import simulate_hard  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test62"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    es, nq = E.setup(); sess = es.pn.sess; full = sess >= H.START
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    base = np.load(os.path.join(C45.ROOT, "out/test61r1/T61R1_AB_daily.npz"))["X2_B_INT"]
    ens_mnq = np.load(os.path.join(C45.ROOT, "out/test61r1/T61R1_daily.npz"))["ens_r1"]
    TRe = module_trades(es, sess, check_inst=False)
    big = np.full((es.n, C45.NG), 2, int)

    def run(gov_lot=-1000.0, slip=1.0):
        d, L, cnt, _ = simulate_hard(es, TRe, gov_lot / 2.0, big, big, slip=slip)
        tot = {k: 2 * v for k, v in d.items()}
        t = sum(tot.values()); t[:s21] = 0
        return t, tot, L
    t, per, L = run()
    exc = 2 * matched_excess(es, L); exc[:s21] = 0
    fold = {}
    for nm, a, b in C45.OUTER:
        mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b)); fold[nm] = float(t[mm].mean())
    comb = base + t
    rb, rc = P.risk(base[full]), P.risk(comb[full])
    pl = [float(run(g)[0][s21:].sum()) for g in (-800.0, -900.0, -1100.0, -1200.0)]
    base_tot = float(t[s21:].sum())
    t4 = run(slip=4.0)[0]
    m21 = sess >= H.SPAN21
    res = {"ES_ensemble_avg_day_2021": float(t[m21].mean()), "ES_matched_excess_day": float(exc[m21].mean()), "folds": fold,
           "folds_pos": int(sum(v > 0 for v in fold.values())), "per_module_2021": {k: float(v[m21].sum()) for k, v in per.items()},
           "corr_ES_vs_MNQ_ensemble": float(np.corrcoef(t[m21], ens_mnq[m21])[0, 1]), "corr_ES_vs_C43": float(np.corrcoef(t[m21], champ[m21])[0, 1]),
           "T61R1B": rb, "T61R1B_plus_ES": rc, "plateau_totals": pl, "SLIP4_incr_2021_total": float(t4[s21:].sum())}
    crit = {"i_excess_and_folds": res["ES_matched_excess_day"] > 0 and res["folds_pos"] >= 4, "ii_ret_dd": rc["ret_dd"] >= rb["ret_dd"],
            "iii_envelope": rc["max_dd"] <= 30000 and rc["worst_day"] >= -6000, "iv_plateau": all(v > 0 and v >= 0.6 * base_tot for v in pl) if base_tot > 0 else False,
            "v_slip4": res["SLIP4_incr_2021_total"] > 0}
    res["criteria"] = crit; res["ADOPT_ES_LEG"] = all(crit.values())
    json.dump(res, open(f"{OUT}/T62_results.json", "w"), indent=1, default=float)
    np.save(f"{OUT}/T62_es_ensemble_daily.npy", t)
    print(json.dumps(res, indent=1, default=float))
    P.budget("TEST62", hypotheses=1, finalists=int(res["ADOPT_ES_LEG"]), note="ES portability of TEST53 modules")
