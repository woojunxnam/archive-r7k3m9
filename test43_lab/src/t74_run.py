"""TEST74 NESTED BOX ALIGNMENT: small A_OBS15_LIFE30 bottom events filtered by position in the medium (A_OBS60_LIFE120) and large (E_PREV_HL)
box in force at the touch (lower half = 0 <= BOX_POS < 0.5).  Event-level economics (TEST70 bottom trade) with matched excess."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
from box_prereg import GEOMETRIES  # noqa: E402

SPEC = {"small": "A_OBS15_LIFE30", "medium": "A_OBS60_LIFE120", "large": "E_PREV_HL", "aligned": "touch close in the lower half [0, 0.5) of the box in force",
        "variants": ["SMALL_ONLY", "SMALL+MEDIUM", "SMALL+LARGE", "SMALL+MEDIUM+LARGE"], "metric": "bottom-trade net $/day, matched excess $/day, folds",
        "note": "hierarchy fixed by the program preregistration; no other hierarchy is searched", "budget": {"hypotheses": 8}}


def pos_in(I, Bx, s, j):
    """BOX_POS of close (s, j) in the box of geometry Bx in force at j (nan if none)."""
    out = np.full(len(s), np.nan)
    g = {k: v for k, v in Bx.groupby("s")}
    for i, (ss, jj) in enumerate(zip(s, j)):
        b = g.get(ss)
        if b is None:
            continue
        m = (b.birth.values <= jj) & (b.death.values > jj)
        if m.any():
            r = b[m].iloc[-1]; out[i] = (I.C[ss, jj] - r.lo) / (r.hi - r.lo)
    return out


def main():
    print(B.prereg("TEST74", SPEC))
    Is = B.load(); rows = []
    for inst, I in Is.items():
        E = pd.read_parquet(os.path.join(B.BOX, "TEST70", f"events_{inst}_{SPEC['small']}.parquet"))
        s = E.s.values.astype(int); j = E.j_touch.values.astype(int)
        pm = pos_in(I, B.build(I, SPEC["medium"], GEOMETRIES[SPEC["medium"]]), s, j)
        pl = pos_in(I, B.build(I, SPEC["large"], GEOMETRIES[SPEC["large"]]), s, j)
        am = (pm >= 0) & (pm < 0.5); al = (pl >= 0) & (pl < 0.5)
        dates = I.sess[s]; nd = int(I.full.sum())
        for lab, m in (("SMALL_ONLY", np.ones(len(E), bool)), ("SMALL+MEDIUM", am), ("SMALL+LARGE", al), ("SMALL+MEDIUM+LARGE", am & al)):
            e = E[m]; dd = dates[m]
            fx = {nm: float(e.excess[(dd >= a) & (dd <= b)].sum() / max(1, ((I.sess >= a) & (I.sess <= b)).sum())) for nm, a, b in B.FOLDS}
            fn = {nm: float(e.net[(dd >= a) & (dd <= b)].sum() / max(1, ((I.sess >= a) & (I.sess <= b)).sum())) for nm, a, b in B.FOLDS}
            rows.append({"instrument": inst, "variant": lab, "events": int(m.sum()), "net_per_event": float(e.net.mean()), "excess_per_event": float(e.excess.mean()),
                         "net_day": float(e.net.sum() / nd), "excess_day": float(e.excess.sum() / nd), "net4_day": float(e.net4.sum() / nd),
                         "top_before_break": float(e.top_before_break.mean()), "folds_net_pos": int(sum(v > 0 for v in fn.values())),
                         "folds_x_pos": int(sum(v > 0 for v in fx.values()))})
    R = pd.DataFrame(rows); R.to_csv(os.path.join(B.BOX, "TEST74", "TEST74_RESULTS.csv"), index=False)
    pd.set_option("display.width", 250); print(R.round(3).to_string())
    B.budget("TEST74", hypotheses=8, note="nested alignment 4 variants x 2")
    B.md("TEST74_NESTED_BOX.md", "TEST74 - nested box alignment", [str(SPEC), R.round(3)])


if __name__ == "__main__":
    main()
