"""TEST63 hold-extension of TEST53 lots in T61-R1B, as preregistered."""
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
import t44_common as TC  # noqa: E402
from t43 import portfolio as PF  # noqa: E402
from t53_run import module_trades  # noqa: E402
from t61r1_validate import grid_positions, simulate_hard  # noqa: E402
from t61r1_x2audit import run_mult  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test63"); os.makedirs(OUT, exist_ok=True)

if __name__ == "__main__":
    TC.setup()
    fin = json.load(open(os.path.join(C45.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")))
    Pp = fin["portfolios"]["SECONDARY_2"]; w = {c: m["contract_weight"] for c, m in Pp["members"].items()}
    bk3 = PF.Book(TC.END, TC.ELIG)
    es, nq = E.setup(); sess = nq.pn.sess; full = sess >= H.START
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    base1 = run_mult(bk3, w, PD.gov_for(Pp["risk_envelope"]), 1)
    pE1, pM1 = grid_positions(bk3.T, base1["pos"], sess)
    hard = np.maximum(0, 6 - np.nan_to_num(2 * pM1, nan=6.0)).astype(int)
    cx2 = 2 * C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    TR = module_trades(nq, sess)
    out = {}
    for nm, cr in (("H0", None), ("H1_WINNER_CARRY", "winner"), ("H2_CARRY_ALL", "all")):
        res = []
        for slip in (1.0, 4.0):
            d, L, cnt, _ = simulate_hard(nq, TR, -1000.0, hard, hard, slip=slip, carry=cr)
            t = sum(d.values()); t[:s21] = 0; res.append(t)
        out[nm] = res
    rows = []
    h0 = cx2 + out["H0"][0]
    for nm, (t, t4) in out.items():
        p = cx2 + t; inc = t - out["H0"][0]; inc4 = t4 - out["H0"][1]
        fold = {}
        for fn, a, b in C45.OUTER:
            mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b)); fold[fn] = float(inc[mm].mean())
        r = P.risk(p[full])
        rows.append({"variant": nm, **r, "incr_vs_H0_day_2021": float(inc[s21:].mean()), "folds_pos": int(sum(v > 0 for v in fold.values())), **{f"f_{k}": v for k, v in fold.items()},
                     "SLIP4_incr_total": float(inc4[s21:].sum()), "p1_day": float(np.percentile(p[full], 1)), "p05_day": float(np.percentile(p[full], 0.5))})
    R = pd.DataFrame(rows)
    r0 = R.iloc[0]; r1 = R[R.variant == "H1_WINNER_CARRY"].iloc[0]
    crit = {"folds": r1.folds_pos >= 4, "ret_dd": r1.ret_dd >= r0.ret_dd, "env": r1.max_dd <= 30000 and r1.worst_day >= -6000, "slip4": r1.SLIP4_incr_total > 0}
    R.to_csv(f"{OUT}/T63_results.csv", index=False)
    json.dump({"criteria": {k: bool(v) for k, v in crit.items()}, "ADOPT_H1": bool(all(crit.values()))}, open(f"{OUT}/T63_decision.json", "w"), indent=1)
    pd.set_option("display.width", 250); print(R.round(4).to_string()); print(crit, "ADOPT", all(crit.values()))
    P.budget("TEST63", hypotheses=1, finalists=int(all(crit.values())), note="winner carry hold-extension")
