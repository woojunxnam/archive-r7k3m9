"""PH7B ADD2 on C2 winner press (prereg 5383968)."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG, da_state as R, mp_engine as P, rp_state as RP
from rp_p7 import prep

OUT = os.path.join(R.OUT, "ph7"); INDEP = ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"]


def main():
    M = P.markets(); T = prep(pd.read_parquet(os.path.join(RP.OUT, "p6", "ARM_C2_P2_FAILED_FIRST_A_TAKE_ALL.parquet"))).reset_index(drop=True)
    E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet")); ind = E[E.candidate.isin(INDEP) & (E.year >= 2021)]
    ig = {k: set(g.b.values) for k, g in ind.groupby(["inst", "s"])}
    C = MG.checkpoints(T, min_left=30); C["is_indep"] = [k in ig.get((i, s), set()) for i, s, k in zip(C.inst, C.s, C.k)]
    rows = []
    for t, g in C.groupby("trade"):
        g = g.sort_values("k"); w = g[g.winner & ~g.is_indep]
        if not len(w):
            continue
        a1 = w.iloc[0]; r = T.iloc[t]; m = M[r.inst]; pa1 = m.I.FP[int(r.s), 5 * int(a1.k) + 5]; avg = (r.px_in + pa1) / 2
        later = g[(g.k > a1.k) & (np.array([m.c[int(r.s), int(k)] for k in g.k]) > avg)]
        u1 = (r.px_out - r.px_in) * r.pv - 2 * r.cs; ad1 = a1.add_usd
        o = {"trade": t, "date": r.date, "year": r.year, "inst": r.inst, "unit1": u1, "add1": ad1, "add2": np.nan, "add2_4": np.nan, "mae3": np.nan}
        if len(later):
            a2 = later.iloc[0]; o["add2"] = a2.add_usd; o["add2_4"] = a2.add_usd4; pa2 = m.I.FP[int(r.s), 5 * int(a2.k) + 5]
            lo = np.nanmin(m.I.L[int(r.s), 5 * int(a2.k) + 5:r.j_out + 1]); o["mae3"] = ((r.px_in - lo) + (pa1 - lo) + (pa2 - lo)) * r.pv
        rows.append(o)
    D = pd.DataFrame(rows); ok = D.add2.notna()
    s = MG.summarize(D.add2[ok], D.date[ok], D.year[ok], D.inst[ok], D.add2_4[ok])
    b3 = (D.unit1 + D.add1 + D.add2.fillna(0)); allu1 = (T.px_out - T.px_in) * T.pv - 2 * T.cs
    res = {"ADD2": s, "worst_unit1": float(allu1.min()), "worst_3unit_basket": float(b3.min()), "mae3_p95": float(np.nanpercentile(D.mae3, 95)), "mae3_p99": float(np.nanpercentile(D.mae3, 99)),
           "add2_2022": float(D.add2[ok & (D.year == 2022)].sum()), "decision": "STOP (ADD2 EV <= 0)" if not s["mean"] > 0 else "ADD2_POSITIVE (GENERIC WINNER PRESS / LEVERAGE)"}
    R.append("MANAGEMENT_LEDGER.csv", {"candidate": "C2", "arm": "ADD2_WINNER_PRESS", "n": s["n"], "marginal_ev": round(s["mean"], 3), "matched_excess": "", "ci_lo": round(s["ci_lo"], 3), "ci_hi": round(s["ci_hi"], 3),
                                       "slip4": round(s["slip4_mean"], 3), "folds_pos": s["folds_pos"], "decision": res["decision"]})
    D.to_parquet(os.path.join(OUT, "PH7B_ADD2.parquet")); json.dump(res, open(os.path.join(OUT, "PH7B_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
