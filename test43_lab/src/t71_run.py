"""TEST71 SIMPLE BOX (B0) + RANGE RECYCLING on the TEST70-selected geometries (EXPLORATORY: no geometry was TEST70-eligible)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import box_eval as V  # noqa: E402
from box_prereg import GEOMETRIES  # noqa: E402

OUT = os.path.join(B.BOX, "TEST71")
# preregistered TEST70 selection (top 3 by fold-median excess among >= 3/5 folds; none eligible) and their grid neighbours
SEL = {"MNQ": {"F_QMAD_W60": ["F_QMAD_W30"], "C_PRIORCLOSE_K0.75": ["C_PRIORCLOSE_K0.5", "C_PRIORCLOSE_K1.0"], "H_BAL6": ["H_BAL12"]},
       "ES": {"G_VWAP_M0.15": ["G_VWAP_M0.25"], "C_PRIORCLOSE_K1.5": ["C_PRIORCLOSE_K1.0"], "C_OPEN_K0.5": ["C_OPEN_K0.75"]}}
BASE = {"LZ": 0.15, "UZ": 0.85, "buf": 0.0, "cycles": 1}
SPEC = {"status": "EXPLORATORY (TEST70: 0/88 cells eligible; selection by the preregistered fallback rule)", "selection": SEL,
        "B0": "flat -> first close in lower zone (0..0.15) -> buy 1 contract next open -> exit next open after close >= 0.85 (TOP) or close < lower (BREAK) "
              "or 16:15; one position; no DCA / pyramiding / ML / GA",
        "recycling": "separate modes: max cycles per box 1, 2, 3 (re-arm only after a TOP exit; a BREAK kills the box)",
        "plateau": "neighbours: lower zone 0.10 / 0.25, upper zone 0.75 / 0.95, break buffer 0.10 / 0.20, geometry grid neighbours, cycles 1 <-> 2 "
                   "(program prereg definition)", "gate": "program standalone gate (455ffc57)", "budget": {"hypotheses": 18}}


def neigh(I, geo, base):
    Bx = V.boxes(I, geo, GEOMETRIES[geo]); out = []
    for k, vals in (("LZ", (0.10, 0.25)), ("UZ", (0.75, 0.95)), ("buf", (0.10, 0.20))):
        out += [(f"{k}={v}", Bx, {**base, k: v}) for v in vals]
    out += [(f"geo={g}", V.boxes(I, g, GEOMETRIES[g]), base) for g in SEL[I.name][geo]]
    out.append(("cycles=2" if base["cycles"] == 1 else "cycles=1", Bx, {**base, "cycles": 2 if base["cycles"] == 1 else 1}))
    return out


def main():
    print(B.prereg("TEST71", SPEC))
    Is = B.load(); rows = []
    for inst, sel in SEL.items():
        I = Is[inst]
        for geo in sel:
            Bx = V.boxes(I, geo, GEOMETRIES[geo])
            for cyc in (1, 2, 3):
                p = {**BASE, "cycles": cyc}
                o, D, d = V.evaluate(I, Bx, f"B0_{geo}_C{cyc}", p, neigh(I, geo, p))
                o["geometry"] = geo; rows.append(o)
                if len(D):
                    o["cycle2plus_net_per_trade"] = float(D.net[D.cycle >= 1].mean()) if (D.cycle >= 1).any() else np.nan
                    o["cycle2plus_x_per_trade"] = float(D.excess[D.cycle >= 1].mean()) if (D.cycle >= 1).any() else np.nan
                print(inst, geo, cyc, round(o.get("avg_day", 0), 2), round(o.get("excess_day", 0), 2), o.get("folds_net_pos"), o.get("PASS"), flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "TEST71_RESULTS.csv"), index=False)
    pd.set_option("display.width", 250)
    cols = ["config", "instrument", "trades_per_day", "gross_day", "avg_day", "excess_day", "slip4_day", "max_dd", "worst_day", "folds_net_pos", "folds_x_pos", "p_top",
            "p_break", "friction_over_gross", "cycle2plus_net_per_trade", "plateau_pass", "PASS"]
    print(R[cols].round(3).to_string())
    B.budget("TEST71", hypotheses=18, note="B0 simple box x 6 geometries x cycles 1/2/3 (+ plateau neighbours)")
    B.md("TEST71_SIMPLE_BOX.md", "TEST71 - simple box B0 and range recycling (EXPLORATORY selection)", [str(SPEC), R[cols].round(3), R.T])


if __name__ == "__main__":
    main()
