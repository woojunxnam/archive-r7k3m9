"""TEST97 Wave 2 (prereg 9136fe6c): persistence ladder, follow-through gradient, shallow second leg - vs MULTI-BAR magnitude null Bk."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E  # noqa: E402
import t97_wave1 as W1  # noqa: E402

M = E.markets(); INSTS = E.INSTS; ROWS = []; TOD = []


def run(name, evs, k, fam):
    nl = f"B{k}"
    rows, _ = E.study(name, evs, nulls=("A", nl))
    P = rows[-1]
    for key in ("h6", "h12", "h1615"):
        P[f"EDGE_{key}_A"] = E.edge(P, key, "A"); P[f"EDGE_{key}_Bk"] = E.edge(P, key, nl)
        for r in rows:
            r[f"{key}_xBk"] = r.get(f"{key}_x{nl}"); r[f"{key}_xBk_lo"] = r.get(f"{key}_x{nl}_lo"); r[f"{key}_xBk_years_pos"] = r.get(f"{key}_x{nl}_years_pos")
    for r in rows:
        r["family"] = fam; r["k"] = k
    ROWS.extend(rows); E.ledger(rows, fam, "persistence clue (OURS)", "WAVE2")
    for t in range(6):                                       # time-of-day map (descriptive)
        rr, _ = E.study(f"{name}|tod{t}", {i: evs[i] & (M[i].tod == t) for i in INSTS}, nulls=("A",), horizons=["h6", "h12"])
        TOD.append({"variant": name, "tod": t, "n": rr[-1]["n_events"], "h6_xA": rr[-1]["h6_xA"], "h12_xA": rr[-1]["h12_xA"]})
    return rows


def main():
    # P1 persistence ladder
    for i in INSTS:
        m = M[i]; prevl = np.concatenate([m.l[:, :1], m.l[:, :-1]], 1); ok = m.bull & (m.cpos >= 0.5) & (m.l > prevl)
        ok[:, 0] = False; L = np.zeros(ok.shape, int)
        for b in range(1, E.NB):
            L[:, b] = np.where(ok[:, b], L[:, b - 1] + 1, 0)
        m.runlen = L
    for Lk in (1, 2, 3, 4, 5):
        run(f"W2_P1_RUN_L{Lk}", {i: M[i].runlen == Lk for i in INSTS}, Lk, "W2_P1")
    # P2 follow-through gradient on N=12 breakouts (entry after b+1)
    base = {i: W1.strong(M[i]) & (M[i].c > M[i].prevhi[12]) for i in INSTS}
    tiers = {"bear": lambda m: ~m.bull, "weak_bull": lambda m: m.bull & (m.body_pct < 0.5), "bull_body50": lambda m: m.bull & (m.body_pct >= 0.5) & ~W1.strong(m),
             "STRONG": lambda m: W1.strong(m)}
    for tn, fn in tiers.items():
        run(f"W2_P2_FT_{tn}", {i: W1.shift(base[i], 1) & fn(M[i]) for i in INSTS}, 2, "W2_P2")
    # P3 shallow second leg from any STRONG impulse
    for i in INSTS:
        m = M[i]; imp = W1.strong(m) & m.valid; ev = np.zeros_like(imp); depth = np.full(imp.shape, np.nan); klen = np.zeros(imp.shape, int)
        for s, b0 in zip(*np.where(imp)):
            H0, L0 = m.h[s, b0], m.l[s, b0]; lo = np.inf
            for b in range(b0 + 1, min(b0 + 8, E.NB - 1)):
                if b == b0 + 1 and m.h[s, b] > H0:
                    break
                if b >= b0 + 2 and m.c[s, b] > m.h[s, b - 1] and m.bull[s, b]:
                    ev[s, b] = True; depth[s, b] = (H0 - lo) / max(H0 - L0, 1e-9); klen[s, b] = b - b0 + 1; break
                lo = min(lo, m.l[s, b])
                if m.h[s, b] > H0:
                    break
        m.p3, m.p3d, m.p3k = ev, depth, klen
    for lab, lo_, hi_ in (("shallow<38.2", 0, .382), ("mid38-62", .382, .618), ("deep>61.8", .618, 99)):
        for k in (3, 4, 5):                                  # null length = impulse -> resumption bars (stratified by k)
            run(f"W2_P3_{lab}_k{k}", {i: M[i].p3 & (M[i].p3d >= lo_) & (M[i].p3d < hi_) & (M[i].p3k == k) for i in INSTS}, k, "W2_P3")
    R = pd.DataFrame(ROWS); R.to_csv(os.path.join(E.OUT, "WAVE2_EVENTS.csv"), index=False); T = pd.DataFrame(TOD); T.to_csv(os.path.join(E.OUT, "WAVE2_TOD.csv"), index=False)
    P = R[R.instrument == "POOLED"]
    cols = ["variant", "n_events", "h6_mean", "h12_mean", "h1615_mean", "h6_xA", "h12_xA", "h6_xBk", "h12_xBk", "h12_xBk_lo", "h12_xBk_years_pos", "h1615_xBk",
            "cost_atr", "EDGE_h6_Bk", "EDGE_h12_Bk", "EDGE_h1615_Bk"]
    ci = ["variant", "instrument", "n_events", "h6_mean", "h12_mean", "h12_xA", "h12_xBk", "h1615_xBk", "cost_atr", "mfe60", "mae60", "bar050", "newhigh60"]
    E.md("T97_W2_EVENTS.md", "TEST97 Wave 2 - persistence vs multi-bar magnitude null (prereg 9136fe6c)", [P[cols], "## per instrument", R[R.instrument != "POOLED"][ci],
                                                                                                            "## time-of-day map (pooled xA)", T.pivot(index="variant", columns="tod", values="h12_xA")])
    pd.set_option("display.width", 250); print(P[cols].round(4).to_string()); print(T.pivot(index="variant", columns="tod", values="h12_xA").round(4).to_string())


if __name__ == "__main__":
    main()
