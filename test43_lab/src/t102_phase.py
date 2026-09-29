"""TEST102 ATR phase / EMA ribbon (prereg 3a389ea)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t102")


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def main():
    M = P.markets(); feat, pops, E, cache = {}, {}, {}, {}
    for i in P.INSTS:
        m = M[i]; n = m.n; cs = pd.Series(m.c.ravel())
        e8, e21, e34 = (cs.ewm(span=s, adjust=False).mean().values.reshape(n, P.NB) for s in (8, 21, 34))
        ph = (m.c - e21) / m.a[:, None]; mv = (m.c - m.open0[:, None]) / m.a[:, None]
        allb = m.valid.copy(); feat[i] = ph; pops[i] = allb
        stk = (e8 > e21) & (e21 > e34); pstk = np.r_[False, stk.ravel()[:-1]].reshape(n, P.NB)
        E.setdefault("S2_RIBBON_ONSET", {})[i] = first(stk & ~pstk & (m.bidx >= 1))
        E.setdefault("S3_E21", {})[i] = first(stk & (m.l <= e21) & (m.c > e21))
        E.setdefault("S3_E8", {})[i] = first(stk & (m.l <= e8) & (m.c > e8))
        cache[i] = dict(mvb=P.causal_bins(m, allb, mv, 3), phb=P.causal_bins(m, allb, ph, 5))

    def s1null(m, inst, ev, key):
        return P.cell_null(m, np.zeros_like(ev), pops[inst], key, [cache[inst]["mvb"]], target=ev)

    def fnull(m, inst, ev, key):
        return P.cell_null(m, ev, pops[inst], key, [cache[inst]["phb"], cache[inst]["mvb"]])
    rc, coh = P.response_curve("S1_PHASE", feat, pops, s1null)
    os.makedirs(OUT, exist_ok=True); rc.to_csv(os.path.join(OUT, "TEST102_S1_CURVES.csv"), index=False); coh.to_csv(os.path.join(OUT, "TEST102_S1_COHERENCE.csv"), index=False)
    pd.set_option("display.width", 250); print(coh.round(4).to_string())
    adj = {"S3_E21": ["S3_E8"], "S3_E8": ["S3_E21"], "S2_RIBBON_ONSET": ["S3_E21", "S3_E8"]}
    D, F, n = P.run_family("TEST102", "ATR_PHASE_RIBBON", E, fnull, adj, outdir=OUT)
    print(F.round(4).to_string())
    n += len(rc)
    json.dump({"ledger_rows": n, "definitions_new": 4, "S1_COHERENT": coh.COHERENT.tolist(), "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T102_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
