"""TEST64 delayed confirmation on M2/M4, as preregistered."""
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
import p03_portfolio_dev as PD  # noqa: E402
from t43 import portfolio as PF  # noqa: E402
from t53_run import module_trades  # noqa: E402
from t61r1_validate import grid_positions, simulate_hard  # noqa: E402
from t61r1_x2audit import run_mult  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test64"); os.makedirs(OUT, exist_ok=True)


def cf4(mk, s, j):
    b0 = j // 5 - 1
    for k in range(b0 + 1, min(b0 + 7, 81)):
        if (k + 1) % 3 == 0 and k >= 5 and not np.isnan(mk.c[s, k]):
            hp = np.nanmax(mk.h[s, k - 5:k - 2])
            if mk.c[s, k] > mk.o[s, k - 2] and mk.c[s, k] > hp:
                return 5 * (k + 1)
    return -1


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
    TD = TR.copy(); keep = []
    for i, r in TD.iterrows():
        if r["mod"] in ("M2", "M4"):
            jn = cf4(nq, int(r.s), int(r.j))
            if jn < 0 or jn > E.J_LAST_ENTRY or (r.s_out == r.s and jn >= r.j_out):
                continue
            TD.at[i, "j"] = jn
        keep.append(i)
    TD = TD.loc[keep].sort_values(["s", "j", "mod"]).reset_index(drop=True)
    out = {}
    for nm, T in (("BASE_T61R1B", TR), ("CF4_M2M4", TD)):
        out[nm] = []
        for slip in (1.0, 4.0):
            d, L, cnt, _ = simulate_hard(nq, T, -1000.0, hard, hard, slip=slip)
            t = sum(d.values()); t[:s21] = 0; out[nm].append((t, d))
    b, v = out["BASE_T61R1B"][0][0], out["CF4_M2M4"][0][0]
    inc = v - b; inc4 = out["CF4_M2M4"][1][0] - out["BASE_T61R1B"][1][0]
    fold = {fn: float(inc[(sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(e))].mean()) for fn, a, e in C45.OUTER}
    rb, rv = P.risk((cx2 + b)[full]), P.risk((cx2 + v)[full])
    crit = {"folds": sum(x > 0 for x in fold.values()) >= 4, "ret_dd": rv["ret_dd"] >= rb["ret_dd"], "env": rv["max_dd"] <= 30000 and rv["worst_day"] >= -6000,
            "slip4": float(inc4[s21:].sum()) > 0}
    res = {"trades_base": int(len(TR)), "trades_cf4": int(len(TD)), "M2_M4_kept_share": float((TD["mod"].isin(["M2", "M4"])).sum() / max((TR["mod"].isin(["M2", "M4"])).sum(), 1)),
           "incr_day_2021": float(inc[s21:].mean()), "folds": fold, "base": rb, "cf4": rv, "per_module_cf4_2021": {k: float(x[s21:].sum()) for k, x in out["CF4_M2M4"][0][1].items()},
           "per_module_base_2021": {k: float(x[s21:].sum()) for k, x in out["BASE_T61R1B"][0][1].items()}, "criteria": {k: bool(x) for k, x in crit.items()}, "ADOPT": bool(all(crit.values()))}
    json.dump(res, open(f"{OUT}/T64_results.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
    P.budget("TEST64", hypotheses=1, finalists=int(res["ADOPT"]), note="CF4 delayed confirmation on M2/M4")
