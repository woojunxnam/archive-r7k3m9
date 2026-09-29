"""TEST106 audit: date-clustered CI of (A2 excess - ORB excess) vs F106; replaces the selection-biased same-session raw comparison for inference."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import t106_acd as T, mp_engine as P, master_state as S
import pandas as pd

def main():
    M = P.markets(); src = open(T.__file__).read()
    # rebuild events/cache by running T.main's detection portion
    E = {k: {} for k in T.NAMES}; cache = {}
    exec_ns = {}
    import types
    T.CUR = ["A2_A_UP_IMMEDIATE"]
    # reuse: run main-like detection
    for i in P.INSTS:
        m = M[i]; I = m.I; n = m.n
        rg = np.nanmax(I.H, 1) - np.nanmin(I.L, 1); av = 0.10 * pd.Series(rg).rolling(10, min_periods=10).mean().shift(1).values
        orh = np.max(m.h[:, :3], 1); Au = (orh + av)[:, None]; win = (m.bidx >= 3) & (m.bidx <= 60)
        E["A2_A_UP_IMMEDIATE"][i] = T.first((m.c >= Au) & win); E["ORB_COMPARATOR"][i] = T.first((m.c > orh[:, None]) & win)
        wid = np.repeat(((orh - np.min(m.l[:, :3], 1)) / m.a)[:, None], P.NB, 1); pop = (m.c > orh[:, None]) & m.valid
        cache[i] = dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - orh[:, None]) / m.a[:, None], 5), P.causal_bins(m, pop, wid, 3)])
    out = []
    for key in P.HZ:
        xs, gs, cls = [], [], []
        for g, nm in ((1, "A2_A_UP_IMMEDIATE"), (0, "ORB_COMPARATOR")):
            for i in P.INSTS:
                m = M[i]; ev = E[nm][i] & m.valid & (m.bidx <= 67); nl, _ = P.cell_null(m, ev, cache[i]["pop"], key, cache[i]["b"])
                x = (m.R[key] - nl)[ev]; xs.append(x); gs.append(np.full(len(x), g)); cls.append(m.date[ev])
        x = np.concatenate(xs); g = np.concatenate(gs); cl = np.concatenate(cls); lo, hi = P.boot_diff(x, g, cl)
        out.append({"horizon": key, "A2_xF": float(np.nanmean(x[g == 1])), "ORB_xF": float(np.nanmean(x[g == 0])), "diff": float(np.nanmean(x[g == 1]) - np.nanmean(x[g == 0])), "ci_lo": lo, "ci_hi": hi})
    D = pd.DataFrame(out); D.to_csv(os.path.join(T.OUT, "TEST106_A2_MINUS_ORB_EXCESS.csv"), index=False); print(D.round(4).to_string())

if __name__ == "__main__":
    main()
