"""TEST103 complex pullback / second entry (prereg b9d9db6)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t103"); NAMES = ["P1_H2", "P2_FAILED_FIRST", "P3_EMA21_SECOND", "P1_H1_COMPARATOR"]


def detect(m, e21):
    n = m.n; ev = {k: np.zeros((n, P.NB), bool) for k in NAMES}; ctx = np.zeros((n, P.NB), bool); shm = np.full((n, P.NB), np.nan); c0 = np.full(n, np.nan)
    brk = m.c > m.prevhi[12]; pb = np.r_[False, brk.ravel()[:-1]].reshape(n, P.NB); fresh = brk & ~pb
    h, l_, c = m.h, m.l, m.c
    for s in range(n):
        a = m.a[s]
        if not a > 0:
            continue
        bb = np.where(fresh[s, 1:56])[0]
        if not len(bb):
            continue
        b0 = int(bb[0]) + 1; end = min(b0 + 24, 67); c0[s] = c[s, b0]; SH = h[s, b0]; ps = None; pl = np.inf
        h1 = None; leg2 = False; pl_at_h1 = None; r1 = None; failed = False; ftouch = 0; done = {k: False for k in NAMES}; alive = True
        for b in range(b0 + 1, end + 1):
            ctx[s, b] = True
            if ps is None:
                if h[s, b] < h[s, b - 1]:
                    ps = b; pl = l_[s, b]
                else:
                    SH = max(SH, h[s, b])
            shm[s, b] = SH
            # P3 (independent of pullback structure)
            if l_[s, b] <= e21[s, b] and c[s, b] > e21[s, b]:
                ftouch += 1
                if ftouch == 2 and not done["P3_EMA21_SECOND"]:
                    ev["P3_EMA21_SECOND"][s, b] = True; done["P3_EMA21_SECOND"] = True
            if ps is None or b == ps or not alive:
                continue
            if l_[s, b] < SH - a:
                alive = False; continue
            if h[s, b] > SH:
                alive = False; continue           # trend resumed with a new high: context resolved
            up_close = c[s, b] > h[s, b - 1]
            # H1 comparator / P2 first resumption
            if r1 is None and up_close:
                r1 = b
                if not done["P1_H1_COMPARATOR"]:
                    ev["P1_H1_COMPARATOR"][s, b] = True; done["P1_H1_COMPARATOR"] = True
            elif r1 is not None and not failed and b <= r1 + 3 and c[s, b] < l_[s, r1]:
                failed = True
            elif failed and up_close and not done["P2_FAILED_FIRST"]:
                ev["P2_FAILED_FIRST"][s, b] = True; done["P2_FAILED_FIRST"] = True
            # P1 H2
            if h1 is None:
                if h[s, b] > h[s, b - 1]:
                    h1 = b; pl_at_h1 = pl
            elif not leg2:
                if l_[s, b] < pl_at_h1:
                    leg2 = True
            elif not done["P1_H2"] and h[s, b] > h[s, b - 1] and up_close:
                ev["P1_H2"][s, b] = True; done["P1_H2"] = True
            pl = min(pl, l_[s, b])
    return ev, ctx, shm, c0


def main():
    M = P.markets(); E = {k: {} for k in NAMES}; cache = {}
    for i in P.INSTS:
        m = M[i]; e21 = pd.Series(m.c.ravel()).ewm(span=21, adjust=False).mean().values.reshape(m.n, P.NB)
        ev, ctx, shm, c0 = detect(m, e21)
        for k in NAMES:
            E[k][i] = ev[k]
        pop = ctx & m.valid
        cache[i] = dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - shm) / m.a[:, None], 3), P.causal_bins(m, pop, (m.c - c0[:, None]) / m.a[:, None], 3)])

    def nullf(m, inst, ev, key):
        return P.cell_null(m, ev, cache[inst]["pop"], key, cache[inst]["b"])
    adj = {"P1_H2": ["P2_FAILED_FIRST"], "P2_FAILED_FIRST": ["P1_H2"]}
    D, F, n = P.run_family("TEST103", "COMPLEX_PULLBACK", E, nullf, adj, outdir=OUT)
    Pm = D[D.instrument == "POOLED"].set_index("variant")
    cmp = [{"second": v, "horizon": k, "second_mean": Pm.loc[v, f"{k}_mean"], "first_mean": Pm.loc["P1_H1_COMPARATOR", f"{k}_mean"],
            "second_minus_first": Pm.loc[v, f"{k}_mean"] - Pm.loc["P1_H1_COMPARATOR", f"{k}_mean"]} for v in ("P1_H2", "P2_FAILED_FIRST") for k in P.HZ]
    pd.DataFrame(cmp).to_csv(os.path.join(OUT, "TEST103_SECOND_VS_FIRST.csv"), index=False)
    pd.set_option("display.width", 250); print(F.round(4).to_string()); print(pd.DataFrame(cmp).round(4).to_string())
    json.dump({"ledger_rows": n, "definitions_new": 4, "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T103_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
