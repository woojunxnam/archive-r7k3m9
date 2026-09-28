"""TEST97 Wave 3 (prereg 0e027b59): Williams volatility breakout, Crabel daily-NR x ORB, Raschke first pullback."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E  # noqa: E402

M = E.markets(); INSTS = E.INSTS; ROWS = []; NOTES = {}


def run(name, evs, fam, nulls=("A", "B1"), family_null=None):
    rows, _ = E.study(name, evs, nulls=nulls, family_null=family_null)
    P = rows[-1]
    for key in ("h6", "h12", "h1615"):
        P[f"EDGE_{key}_A"] = E.edge(P, key, "A")
    for r in rows:
        r["family"] = fam
    ROWS.extend(rows); E.ledger(rows, fam, "Wave 3", "WAVE3"); return rows


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def main():
    win = lambda m: (m.bidx >= 1) & (m.bidx <= 65)
    # V1 Williams volatility breakout
    for k in (0.0, 0.1, 0.2, 0.3, 0.5, 0.75):
        evs = {}
        for i in INSTS:
            m = M[i]; pr = np.r_[np.nan, (np.nanmax(m.I.H, 1) - np.nanmin(m.I.L, 1))[:-1]]
            evs[i] = first((m.c > m.open0[:, None] + k * pr[:, None]) & win(m))
        run(f"W3_V1_VOLBRK_k{k}", evs, "W3_V1", family_null=None)
    # V2 Crabel daily NR x ORB15 (close-confirmed)
    inc = []
    for lab in ("NR4", "NR7", "INSIDE"):
        a_ev, n_ev = {}, {}
        for i in INSTS:
            m = M[i]; Hd, Ld = np.nanmax(m.I.H, 1), np.nanmin(m.I.L, 1); rg = Hd - Ld
            if lab == "INSIDE":
                st = np.r_[False, (Hd[1:] <= Hd[:-1]) & (Ld[1:] >= Ld[:-1])]
            else:
                w = int(lab[2:]); st = (pd.Series(rg).rolling(w).min().values == rg)
            prior = np.r_[False, st[:-1]]
            orh = np.max(m.h[:, :3], 1)[:, None]; orb = first((m.c > orh) & (m.bidx >= 3) & (m.bidx < 18))
            a_ev[i] = orb & prior[:, None]; n_ev[i] = orb & ~prior[:, None]
        ra = run(f"W3_V2_ORB15_after_{lab}", a_ev, "W3_V2")[-1]; rn = E.study(f"W3_V2_ORB15_not_{lab}", n_ev)[0][-1]
        inc.append({"prior_state": lab, "n_state": ra["n_events"], "n_other": rn["n_events"], **{f"{h}_incr_xA": ra[f"{h}_xA"] - rn[f"{h}_xA"] for h in ("h6", "h12", "h1615")}})
    NOTES["W3_V2_NR_incremental"] = inc
    # V3 Raschke first pullback after a new 60-bar high thrust (same session) vs chase at the thrust
    fp, ch = {}, {}
    for i in INSTS:
        m = M[i]; thrust = m.c > m.prevhi[60]; ev = np.zeros_like(thrust); chase = np.zeros_like(thrust)
        for s in np.where(m.full)[0]:
            tb = np.where(thrust[s, :60])[0]
            if not len(tb):
                continue
            b0 = tb[0]; chase[s, b0] = True; touched = False
            for b in range(b0 + 1, 66):
                if not touched and (m.l[s, b] <= m.ema20[s, b] or m.l[s, b] <= m.vwap[s, b]):
                    touched = True; continue
                if touched and m.bull[s, b] and m.c[s, b] > m.h[s, b - 1]:
                    ev[s, b] = True; break
        fp[i], ch[i] = ev, chase
    run("W3_V3_FIRST_PULLBACK_ENTRY", fp, "W3_V3", family_null=ch)
    run("W3_V3_CHASE_AT_THRUST", ch, "W3_V3")
    R = pd.DataFrame(ROWS); R.to_csv(os.path.join(E.OUT, "WAVE3_EVENTS.csv"), index=False); json.dump(NOTES, open(os.path.join(E.OUT, "WAVE3_NOTES.json"), "w"), indent=1, default=float)
    P = R[R.instrument == "POOLED"]
    cols = ["variant", "n_events", "h6_mean", "h12_mean", "h1615_mean", "h6_xA", "h12_xA", "h12_xA_lo", "h12_xA_years_pos", "h12_xB1", "h1615_xA", "h1615_xA_lo", "cost_atr",
            "EDGE_h6_A", "EDGE_h12_A", "EDGE_h1615_A"]
    E.md("T97_W3_EVENTS.md", "TEST97 Wave 3 (prereg 0e027b59)", [P[cols], "## per instrument", R[R.instrument != "POOLED"][["variant", "instrument", "n_events", "h12_mean", "h12_xA", "h1615_xA", "cost_atr"]],
                                                                  "## NR incremental", pd.DataFrame(inc)])
    pd.set_option("display.width", 250); print(P[cols].round(4).to_string()); print(pd.DataFrame(inc).round(4).to_string())
    fv = R[R.variant == "W3_V3_FIRST_PULLBACK_ENTRY"]; print(fv[["instrument", "n_events", "h12_mean", "h12_x_family" if "h12_x_family" in fv else "h12_mean", "h1615_mean"]].round(4))


if __name__ == "__main__":
    main()
