"""TEST100 VWAP trend-side state / acceptance (prereg b69e62e)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t100")


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def runall(X, K):
    """True at b if X[b-K+1..b] all True within the session."""
    c = np.zeros(X.shape, int); run = np.zeros(X.shape[0], int)
    for b in range(X.shape[1]):
        run = np.where(X[:, b], run + 1, 0); c[:, b] = run
    return c >= K


def main():
    M = P.markets(); E = {}; cache = {}
    for i in P.INSTS:
        m = M[i]; above = m.c > m.vwap; atr5 = m.atr5
        for K in (3, 6):
            v1 = first(runall(above, K)); E.setdefault(f"V1_K{K}", {})[i] = v1
            acc = np.cumsum(v1, 1) > 0; accp = np.concatenate([np.zeros((m.n, 1), bool), acc[:, :-1]], 1)
            hold = accp & (m.l <= m.vwap + 0.25 * atr5) & above
            E.setdefault(f"V3_K{K}", {})[i] = first(hold)
        for K in (6, 12):
            okb = above & (m.l >= m.vwap - 0.25 * atr5)
            cK = np.full(m.c.shape, np.nan); cK[:, K - 1:] = m.c[:, :m.c.shape[1] - K + 1]
            E.setdefault(f"V2_K{K}", {})[i] = first(runall(okb, K) & (m.c > cK))
        pop = above & m.valid
        cache[i] = dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - m.vwap) / m.a[:, None], 5), P.causal_bins(m, pop, (m.c - m.open0[:, None]) / m.a[:, None], 3)])

    def nullf(m, inst, ev, key):
        return P.cell_null(m, ev, cache[inst]["pop"], key, cache[inst]["b"])
    adj = {"V1_K3": ["V1_K6"], "V1_K6": ["V1_K3"], "V2_K6": ["V2_K12"], "V2_K12": ["V2_K6"], "V3_K3": ["V3_K6"], "V3_K6": ["V3_K3"]}
    evsets = {k: E[k] for k in ["V1_K3", "V1_K6", "V2_K6", "V2_K12", "V3_K3", "V3_K6"]}
    D, F, n = P.run_family("TEST100", "VWAP_TREND_SIDE", evsets, nullf, adj, outdir=OUT)
    pd.set_option("display.width", 250); print(F.round(4).to_string())
    json.dump({"ledger_rows": n, "definitions_new": 6, "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T100_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
