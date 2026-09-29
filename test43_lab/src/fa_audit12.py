"""FINAL_INDEX_CLOSURE_AUDIT_V1 audits 1 / 2: >= 30 min eligibility for signal rows (preregs e81e3fd / audit-2 prereg)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_state as RP  # noqa: E402
from rp_p7 import prep  # noqa: E402

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, "out", "final_index_closure_audit_v1"); os.makedirs(OUT, exist_ok=True)
INDEP = ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"]


def setup():
    T = prep(pd.read_parquet(os.path.join(RP.OUT, "p6", "ARM_C2_P2_FAILED_FIRST_A_TAKE_ALL.parquet"))).reset_index(drop=True)
    E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet")); ind = E[E.candidate.isin(INDEP) & (E.year >= 2021)]
    ig = {k: sorted(g.b.values) for k, g in ind.groupby(["inst", "s"])}
    return T, ig


def run(mode):
    M = P.markets(); T, ig = setup(); sig = []
    for t, r in enumerate(T.itertuples(index=False)):
        evb = [b for b in ig.get((r.inst, int(r.s)), []) if b > r.b and 5 * b + 5 < r.j_out and 5 * b + 5 > r.j_in]
        if evb:
            c = M[r.inst].c[int(r.s), evb[0]]
            if (mode == "winner" and c > r.px_in) or (mode == "recovery" and c < r.px_in):
                sig.append((t, evb[0]))
    S0 = set(sig); C = MG.checkpoints(T, min_left=30); indep = {(t, b) for t, r in enumerate(T.itertuples(index=False)) for b in ig.get((r.inst, int(r.s)), [])}
    C["is_indep"] = [(t, k) in indep for t, k in zip(C.trade, C.k)]; C["is_sig"] = [(t, k) in S0 for t, k in zip(C.trade, C.k)]
    C["is_indep"] = C.is_indep.astype(bool); C["is_sig"] = C.is_sig.astype(bool)
    state = C.winner if mode == "winner" else C.under
    pool = (state & ~C.is_sig & ~C.is_indep).values; ctl, lev = MG.matched_control(C, C.is_sig.values, pool)
    C["ctl"] = ctl * C.atr * C.pv - 2 * C.cs; C["ctl4"] = ctl * C.atr * C.pv - 2 * C.cs4; S = C[C.is_sig]
    res = {"original_signal_n": len(sig), "corrected_signal_n": int(C.is_sig.sum()), "removed_lt_30min": len(sig) - int(C.is_sig.sum()), "generic_control_pool_n": int(pool.sum()),
           "match_levels": {int(k): int(v) for k, v in pd.Series(lev[C.is_sig.values]).value_counts().items()}}
    res["SIGNAL_ADD"] = MG.summarize(S.add_usd, S.date, S.year, S.inst, S.add_usd4)
    res["MATCHED_GENERIC"] = MG.summarize(S.ctl, S.date, S.year, S.inst, S.ctl4)
    res["SIGNAL_MINUS_MATCHED"] = MG.summarize(S.add_usd - S.ctl, S.date, S.year, S.inst, S.add_usd4 - S.ctl4)
    first = C[state & ~C.is_indep].sort_values(["trade", "k"]).groupby("trade").head(1)
    res["FIRST_GENERIC"] = MG.summarize(first.add_usd, first.date, first.year, first.inst, first.add_usd4)
    d, c_, g = res["SIGNAL_MINUS_MATCHED"], res["SIGNAL_ADD"], res["FIRST_GENERIC"]
    if mode == "winner":
        spec = d["mean"] > 0 and (d["ci_lo"] > 0 or (d["folds_pos"] >= 4 and d["inst_pos"] >= 3)) and c_["slip4_mean"] > 0
        gen = g["mean"] > 0 and g["slip4_mean"] > 0 and g["folds_pos"] >= 3
        res["PH1_CORRECTED_WINNER_SPECIFICITY"] = "SIGNAL_SPECIFIC_WINNER_ADD" if spec else ("GENERIC_WINNER_PRESS" if gen else "NO_ADD_VALUE")
    else:
        spec = c_["mean"] > 0 and d["mean"] > 0 and (d["ci_lo"] > 0 or (d["folds_pos"] >= 4 and d["inst_pos"] >= 3)) and c_["slip4_mean"] > 0
        gen = (c_["mean"] > 0 or g["mean"] > 0) and not spec
        res["PH7_CORRECTED_RECOVERY_SPECIFICITY"] = "SIGNAL_SPECIFIC_RECOVERY" if spec else ("GENERIC_AVERAGING" if gen else "NO_RECOVERY_VALUE")
    json.dump(res, open(os.path.join(OUT, f"AUDIT_{mode.upper()}.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    run(sys.argv[1])
