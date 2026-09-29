"""PH7 management with matched controls (prereg 9e7fe2e)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_state as RP  # noqa: E402
from rp_p7 import prep  # noqa: E402

OUT = os.path.join(R.OUT, "ph7"); os.makedirs(OUT, exist_ok=True)
INDEP = ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"]


def main():
    M = P.markets(); T = prep(pd.read_parquet(os.path.join(RP.OUT, "p6", "ARM_C2_P2_FAILED_FIRST_A_TAKE_ALL.parquet"))).reset_index(drop=True)
    E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet")); ind = E[E.candidate.isin(INDEP) & (E.year >= 2021)]
    ig = {k: sorted(g.b.values) for k, g in ind.groupby(["inst", "s"])}
    C = MG.checkpoints(T, min_left=30); indep = {(t, b) for t, r in enumerate(T.itertuples(index=False)) for b in ig.get((r.inst, int(r.s)), [])}
    C["is_indep"] = [(t, k) in indep for t, k in zip(C.trade, C.k)]; res = {}
    # (a) fresh-signal recovery
    sig = []
    for t, r in enumerate(T.itertuples(index=False)):
        evb = [b for b in ig.get((r.inst, int(r.s)), []) if b > r.b and 5 * b + 5 < r.j_out and 5 * b + 5 > r.j_in]
        if evb and M[r.inst].c[int(r.s), evb[0]] < r.px_in:
            sig.append((t, evb[0]))
    Cs = MG.checkpoints(T, min_left=0); Cs = Cs[[(t, k) in set(sig) for t, k in zip(Cs.trade, Cs.k)]].copy(); Cs["is_indep"] = True; Cs["is_sig"] = True
    C["is_sig"] = False; A = pd.concat([C, Cs], ignore_index=True); A["is_sig"] = A.is_sig.astype(bool); A["is_indep"] = A.is_indep.astype(bool)
    pool = (A.under & ~A.is_sig & ~A.is_indep).values; ctl, lev = MG.matched_control(A, A.is_sig.values, pool)
    A["ctl"] = ctl * A.atr * A.pv - 2 * A.cs; S = A[A.is_sig]
    res["A_FRESH_SIGNAL_RECOVERY"] = MG.summarize(S.add_usd, S.date, S.year, S.inst, S.add_usd4)
    res["A_MATCHED_UNDERWATER_CONTROL"] = MG.summarize(S.ctl, S.date, S.year, S.inst)
    res["A_SIGNAL_MINUS_MATCHED"] = MG.summarize(S.add_usd - S.ctl, S.date, S.year, S.inst)
    fu = C[C.under & ~C.is_indep].sort_values(["trade", "k"]).groupby("trade").head(1)
    res["A_BLIND_FIRST_UNDERWATER_CONTROL"] = MG.summarize(fu.add_usd, fu.date, fu.year, fu.inst, fu.add_usd4)
    # (b) winner-press state specificity: first winner checkpoint vs matched ALL checkpoints (no winner condition)
    C2 = C.copy(); fw = C2[C2.winner & ~C2.is_indep].sort_values(["trade", "k"]).groupby("trade").head(1).index
    C2["is_sig"] = False; C2.loc[fw, "is_sig"] = True; pool = (~C2.is_sig & ~C2.is_indep).values
    ctl, lev = MG.matched_control(C2, C2.is_sig.values, pool); C2["ctl"] = ctl * C2.atr * C2.pv - 2 * C2.cs; W = C2[C2.is_sig]
    res["B_FIRST_WINNER_ADD"] = MG.summarize(W.add_usd, W.date, W.year, W.inst, W.add_usd4)
    res["B_MATCHED_ANY_CHECKPOINT"] = MG.summarize(W.ctl, W.date, W.year, W.inst)
    res["B_WINNER_MINUS_MATCHED"] = MG.summarize(W.add_usd - W.ctl, W.date, W.year, W.inst)
    # (c) tails for the winner press basket
    unit1 = (T.px_out - T.px_in) * T.pv - 2 * T.cs; addmap = W.set_index("trade").add_usd; bask = unit1.values + np.array([addmap.get(t, 0.0) for t in range(len(T))])
    res["C_TAILS"] = {"worst_unit1": float(unit1.min()), "worst_basket": float(bask.min()), "basket_2022": float(bask[T.year.values == 2022].sum()), "unit1_2022": float(unit1[T.year.values == 2022].sum())}
    b = res["B_FIRST_WINNER_ADD"]; bx = res["B_WINNER_MINUS_MATCHED"]
    elig = b["mean"] > 0 and b["slip4_mean"] > 0 and b["folds_pos"] >= 4 and b["n"] >= 150 and bx["mean"] > 0 and res["C_TAILS"]["worst_basket"] >= 2 * res["C_TAILS"]["worst_unit1"]
    a = res["A_SIGNAL_MINUS_MATCHED"]; af = res["A_FRESH_SIGNAL_RECOVERY"]
    res["RECOVERY_CLASS"] = "STOP (ADD1 EV <= 0)" if not af["mean"] > 0 else ("SIGNAL_SPECIFIC_RECOVERY" if (a["mean"] > 0 and (a["ci_lo"] > 0 or (a["folds_pos"] >= 4 and a["inst_pos"] >= 3))) else "NO_SIGNAL_VALUE (generic averaging)")
    res["WINNER_PRESS_CLASS"] = "STATE_SPECIFIC_WINNER_PRESS" if bx["mean"] > 0 else "GENERIC_ADD_ANY_STATE"
    res["ADD2_ELIGIBLE"] = bool(elig)
    for arm, o, mx in (("FRESH_SIGNAL_RECOVERY", af, a), ("FIRST_WINNER_PRESS", b, bx)):
        R.append("MANAGEMENT_LEDGER.csv", {"candidate": "C2", "arm": arm, "n": o["n"], "marginal_ev": round(o["mean"], 3), "matched_excess": round(mx["mean"], 3), "ci_lo": round(mx["ci_lo"], 3) if mx["ci_lo"] == mx["ci_lo"] else "",
                                           "ci_hi": round(mx["ci_hi"], 3) if mx["ci_hi"] == mx["ci_hi"] else "", "slip4": round(o["slip4_mean"], 3), "folds_pos": o["folds_pos"], "decision": res["RECOVERY_CLASS"] if arm.startswith("FRESH") else res["WINNER_PRESS_CLASS"]})
    json.dump(res, open(os.path.join(OUT, "PH7_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
