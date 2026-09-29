"""TEST108 range budget veto (prereg 4951038)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t108"); NB = P.NB


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def main():
    M = P.markets(); bases = {"BRK12": {}, "ORB15": {}}; F = {"RB1": {}, "RB2": {}}
    for i in P.INSTS:
        m = M[i]; n = m.n
        brk = m.c > m.prevhi[12]; pb = np.r_[False, brk.ravel()[:-1]].reshape(n, NB)
        bases["BRK12"][i] = brk & ~pb & (m.bidx >= 1)
        bases["ORB15"][i] = first((m.c > np.max(m.h[:, :3], 1)[:, None]) & (m.bidx >= 3) & (m.bidx <= 60))
        hi = np.maximum.accumulate(m.h, 1); lo = np.minimum.accumulate(m.l, 1)
        F["RB1"][i] = (hi - lo) / m.a[:, None]; F["RB2"][i] = (m.c - lo) / m.a[:, None]

    def nullf(m, inst, ev, key):
        return P.cell_null(m, np.zeros_like(ev), m.valid, key, [], target=ev)
    curves, cohs, veto = [], [], []
    for bn, B in bases.items():
        for fn, X in F.items():
            name = f"{fn}_{bn}"; rc, coh = P.response_curve(name, X, B, nullf); curves.append(rc); cohs.append(coh)
            for key in ("h12", "h24", "h1615"):
                pr = rc[(rc.instrument == "POOLED") & (rc.horizon == key)].sort_values("bin"); allx = np.average(pr.xN, weights=pr.n)
                keep = pr[pr.bin < 4]; kx = np.average(keep.xN, weights=keep.n)
                veto.append({"curve": name, "horizon": key, "base_xN": allx, "vetoed_xN": kx, "improvement": kx - allx, "frac_removed": pr[pr.bin == 4].n.sum() / pr.n.sum(),
                             "top_bin_xN": float(pr[pr.bin == 4].xN.iloc[0])})
    C = pd.concat(cohs); V = pd.DataFrame(veto); os.makedirs(OUT, exist_ok=True)
    R = pd.concat(curves); R.to_csv(os.path.join(OUT, "TEST108_CURVES.csv"), index=False); C.to_csv(os.path.join(OUT, "TEST108_COHERENCE.csv"), index=False); V.to_csv(os.path.join(OUT, "TEST108_VETO.csv"), index=False)
    C["VETO_HAS_VALUE"] = C.COHERENT & (C.top_minus_bottom < 0) & C.apply(lambda r: V[(V.curve == r.feature) & (V.horizon == r.horizon)].top_bin_xN.iloc[0] < 0, axis=1)
    C.to_csv(os.path.join(OUT, "TEST108_COHERENCE.csv"), index=False)
    pd.set_option("display.width", 250); print(C.round(4).to_string()); print(V.round(4).to_string())
    json.dump({"ledger_rows": len(R), "definitions_new": 4, "veto_value": C.VETO_HAS_VALUE.tolist()}, open(os.path.join(OUT, "T108_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
