"""TEST99 HTF momentum scaling (prereg b8da734): Phase 0 aggregation parity + Phase 1 HTF1-3 event study vs F99 null."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t99"); REP = os.path.join(S.REP, "TEST99"); os.makedirs(OUT, exist_ok=True)
TFS = {5: 1, 15: 3, 30: 6, 60: 12}; N2 = {5: 24, 15: 8, 30: 4, 60: 2}


def htf(m, m5):
    nk = P.NB // m5; I = m.I
    idx = lambda k: slice(k * m5, (k + 1) * m5)
    O = np.stack([m.o[:, k * m5] for k in range(nk)], 1); H = np.stack([m.h[:, idx(k)].max(1) for k in range(nk)], 1)
    L = np.stack([m.l[:, idx(k)].min(1) for k in range(nk)], 1); C = np.stack([m.c[:, (k + 1) * m5 - 1] for k in range(nk)], 1)
    j = lambda k: slice(k * m5 * 5, (k + 1) * m5 * 5)
    O1 = np.stack([I.O[:, k * m5 * 5] for k in range(nk)], 1); H1 = np.stack([I.H[:, j(k)].max(1) for k in range(nk)], 1)
    L1 = np.stack([I.L[:, j(k)].min(1) for k in range(nk)], 1); C1 = np.stack([I.C[:, (k + 1) * m5 * 5 - 1] for k in range(nk)], 1)
    par = max(np.nanmax(np.abs(a - b)) for a, b in ((O, O1), (H, H1), (L, L1), (C, C1)))
    return O, H, L, C, nk, float(par)


def parity_5m(m):
    I = m.I; nb = P.NB
    o = I.O[:, 0:5 * nb:5]; h = I.H[:, :5 * nb].reshape(m.n, nb, 5).max(2); l_ = I.L[:, :5 * nb].reshape(m.n, nb, 5).min(2); c = I.C[:, 4:5 * nb:5]
    return float(max(np.nanmax(np.abs(a - b)) for a, b in ((o, m.o), (h, m.h), (l_, m.l), (c, m.c))))


def to5(m, X, m5, nk):
    out = np.full((m.n, P.NB), np.nan) if X.dtype != bool else np.zeros((m.n, P.NB), bool)
    for k in range(nk):
        out[:, (k + 1) * m5 - 1] = X[:, k]
    return out


def main():
    M = P.markets(); par = {}; evs = {}; feats = {}
    for i in P.INSTS:
        m = M[i]; par[i] = {"5m": parity_5m(m)}
        for tf, m5 in TFS.items():
            O, H, L, C, nk, pp = htf(m, m5); par[i][f"{tf}m"] = pp
            n = m.n; fl = lambda X: pd.Series(X.ravel())
            rng = H - L; body = C - O; cpos = np.where(rng > 0, (C - L) / np.where(rng > 0, rng, 1), 0.5)
            mr20 = fl(rng).rolling(20, min_periods=20).mean().shift(1).values.reshape(n, nk)
            h1 = (body > 0) & (np.where(rng > 0, body / np.where(rng > 0, rng, 1), 0) >= 0.60) & (cpos >= 0.80) & (rng >= 1.25 * mr20)
            ph = fl(H).rolling(N2[tf], min_periods=N2[tf]).max().shift(1).values.reshape(n, nk)
            brk = C > ph; prevb = fl(brk).shift(1).fillna(False).values.reshape(n, nk).astype(bool); h2 = brk & ~prevb
            up = (body > 0) & (cpos >= 0.5); u1 = fl(up).shift(1).fillna(False).values.reshape(n, nk).astype(bool); u2 = fl(up).shift(2).fillna(False).values.reshape(n, nk).astype(bool)
            h3 = up & u1 & ~u2
            pc = fl(C).shift(1).values.reshape(n, nk)
            disp = (C - pc) / m.a[:, None]; rga = rng / m.a[:, None]
            pop = to5(m, np.ones((n, nk), bool), m5, nk)
            feats[(i, tf)] = dict(pop=pop, disp=to5(m, disp, m5, nk), rng=to5(m, rga, m5, nk))
            for fam, X in (("HTF1", h1), ("HTF2", h2), ("HTF3", h3)):
                evs.setdefault((fam, tf), {})[i] = to5(m, X, m5, nk)
    json.dump(par, open(os.path.join(OUT, "PHASE0_PARITY.json"), "w"), indent=1)
    ok = all(v == 0 for d in par.values() for v in d.values())
    print("PARITY", par, ok)
    if not ok:
        json.dump({"TEST99": "PARITY_BLOCKED"}, open(os.path.join(OUT, "TEST99_STATUS.json"), "w")); return
    bins_cache = {}

    def nullf_for(tf):
        def f(m, inst, ev, key):
            F = feats[(inst, tf)]
            if (inst, tf) not in bins_cache:
                bins_cache[(inst, tf)] = [P.causal_bins(m, F["pop"], F["disp"], 5), P.causal_bins(m, F["pop"], F["rng"], 3)]
            return P.cell_null(m, ev, F["pop"], key, bins_cache[(inst, tf)])
        return f
    R = []
    for (fam, tf), ev in evs.items():
        rows = P.evaluate(f"T99_{fam}_{tf}m", ev, nullf_for(tf), meta={"family": fam, "tf": tf, "reference": tf == 5})
        R.extend(rows); print(fam, tf, {k: round(rows[-1][f"{k}_xF"], 4) for k in P.HZ}, rows[-1]["n_events"])
    D = pd.DataFrame(R); Pd = D[D.instrument == "POOLED"].set_index(["family", "tf"])
    # adjacency + final classification
    adj = {5: [15], 15: [5, 30], 30: [15, 60], 60: [30]}; fin = []
    for (fam, tf), r in Pd.iterrows():
        if tf == 5:
            continue
        for key in ("h12", "h24", "h1615"):
            x = r[f"{key}_xF"]
            aok = any((np.sign(Pd.loc[(fam, a), f"{key}_xF"]) == np.sign(x)) and abs(Pd.loc[(fam, a), f"{key}_xF"]) >= 0.5 * abs(x) for a in adj[tf])
            cls = P.classify(r.to_dict() | {"cost_atr": r["cost_atr"]}, key, adjacent_ok=aok)
            fin.append({"variant": r["variant"], "family": fam, "tf": tf, "horizon": key, "n": r[f"{key}_n"], "mean": r[f"{key}_mean"], "cost_atr": r["cost_atr"],
                        "xF": x, "xF_lo": r[f"{key}_xF_lo"], "xF_hi": r[f"{key}_xF_hi"], "years_pos": r[f"{key}_years_pos"], "inst_pos": r[f"{key}_inst_pos"],
                        "xF_2021": r[f"{key}_xF_2021"], "x2022": r[f"{key}_x2022"], "xA": r[f"{key}_xA"], "xC": r[f"{key}_xC"], "adjacent_ok": aok,
                        "fallback": r[f"{key}_fallback"], "class": cls})
    F = pd.DataFrame(fin); D.to_csv(os.path.join(OUT, "T99_EVENTS.csv"), index=False); F.to_csv(os.path.join(OUT, "T99_CLASSIFICATION.csv"), index=False)
    nrows = P.ledger(R, "TEST99", "HTF", "PHASE1")
    pd.set_option("display.width", 250); print(F.round(4).to_string())
    json.dump({"ledger_rows": nrows, "definitions_new": 9, "reference_rows": 3, "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T99_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
