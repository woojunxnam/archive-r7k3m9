"""RESERVE_R1 trapped-seller failure union (prereg 1ce475c).  Constituents use the exact frozen code of TEST103 / TEST104 / TEST106."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402
import t103_pullback as T3  # noqa: E402
import t104_levels as T4  # noqa: E402

OUT = os.path.join(S.OUT, "r1"); os.makedirs(OUT, exist_ok=True); NB = P.NB


def a3_events(m):
    I = m.I; n = m.n
    rg = np.nanmax(I.H, 1) - np.nanmin(I.L, 1); av = 0.10 * pd.Series(rg).rolling(10, min_periods=10).mean().shift(1).values
    orh = np.max(m.h[:, :3], 1); orl = np.min(m.l[:, :3], 1); Ad = (orl - av)[:, None]; win = (m.bidx >= 3) & (m.bidx <= 60)
    a3 = np.zeros((n, NB), bool)
    for s in range(n):
        if not av[s] > 0:
            continue
        dn = np.where((m.c[s] <= Ad[s, 0]) & win[s])[0]
        if len(dn):
            d0 = dn[0]
            for b in range(d0 + 1, min(d0 + 7, 61)):
                if m.c[s, b] > orl[s]:
                    a3[s, b] = True; break
    wid = np.repeat(((orh - orl) / m.a)[:, None], NB, 1); pop = (m.c > orl[:, None]) & m.valid
    return a3, dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - orl[:, None]) / m.a[:, None], 5), P.causal_bins(m, pop, wid, 3)])


def main():
    M = P.markets(); U, NUL, SRC = {}, {}, {}
    for i in P.INSTS:
        m = M[i]; cons = {}
        e21 = pd.Series(m.c.ravel()).ewm(span=21, adjust=False).mean().values.reshape(m.n, NB)
        ev3, ctx, shm, c0 = T3.detect(m, e21); pop = ctx & m.valid
        cons["P2"] = (ev3["P2_FAILED_FIRST"], dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - shm) / m.a[:, None], 3), P.causal_bins(m, pop, (m.c - c0[:, None]) / m.a[:, None], 3)]))
        Lv = T4.levels(m); ev4, _ = T4.detect(m, Lv); mv = (m.c - m.open0[:, None]) / m.a[:, None]
        for nm in T4.SUP:
            L = Lv[nm]; pp = (m.c > L) & m.valid
            cons[f"L2_{nm}"] = (ev4[f"L2_{nm}"], dict(pop=pp, b=[P.causal_bins(m, pp, (m.c - L) / m.a[:, None], 5), P.causal_bins(m, pp, mv, 3)]))
        cons["A3"] = a3_events(m)
        # per-horizon null of each constituent on its own events (pool excludes its own events, as in the original tests)
        nul = {k: np.full((m.n, NB), np.nan) for k in P.HZ}; src = np.full((m.n, NB), "", object); union = np.zeros((m.n, NB), bool)
        firstb = np.full(m.n, 10 ** 6); owner = {}
        for nm, (ev, c) in cons.items():
            e = ev & m.valid & (m.bidx <= 67)
            for s, b in zip(*np.where(e)):
                if b < firstb[s]:
                    firstb[s] = b; owner[s] = nm
        for s, nm in owner.items():
            union[s, firstb[s]] = True; src[s, firstb[s]] = nm
        for nm, (ev, c) in cons.items():
            sel = union & (src == nm)
            if not sel.any():
                continue
            for k in P.HZ:
                nl, _ = P.cell_null(m, ev & m.valid, c["pop"], k, c["b"], target=sel); nul[k][sel] = nl[sel]
        U[i], NUL[i], SRC[i] = union, nul, src

    def nullf(m, inst, ev, key):
        return NUL[inst][key], np.zeros(ev.shape, int)
    rows = P.evaluate("R1_TRAPPED_UNION", U, nullf, meta={"family": "RESERVE_R1"}); Pp = rows[-1]
    grp = lambda s: "L2" if s.startswith("L2") else s
    comp = []
    for key in P.HZ:
        xs = {"P2": [], "L2": [], "A3": []}
        for i in P.INSTS:
            m = M[i]; e = U[i] & m.valid & (m.bidx <= 67); x = (m.R[key] - NUL[i][key])[e]; g = np.array([grp(s) for s in SRC[i][e]])
            for G in xs:
                xs[G].append(x[g == G])
        comp.append({"horizon": key, **{f"{G}_n": int(sum(len(v) for v in xs[G])) for G in xs}, **{f"{G}_xF": float(np.nanmean(np.concatenate(xs[G]))) for G in xs}})
    Cp = pd.DataFrame(comp); fin = []
    for key in ("h12", "h24", "h1615"):
        x = Pp[f"{key}_xF"]; c = Cp.set_index("horizon").loc[key]
        aok = sum((c[f"{G}_xF"] > 0) and (c[f"{G}_xF"] >= 0.5 * x) for G in ("P2", "L2", "A3")) >= 2 if x > 0 else False
        fin.append({"variant": "R1_TRAPPED_UNION", "horizon": key, "n": Pp[f"{key}_n"], "mean": Pp[f"{key}_mean"], "cost_atr": Pp["cost_atr"], "xF": x, "xF_lo": Pp[f"{key}_xF_lo"],
                    "xF_hi": Pp[f"{key}_xF_hi"], "years_pos": Pp[f"{key}_years_pos"], "inst_pos": Pp[f"{key}_inst_pos"], "xF_2021": Pp[f"{key}_xF_2021"], "x2022": Pp[f"{key}_x2022"],
                    "xA": Pp[f"{key}_xA"], "xC": Pp[f"{key}_xC"], "adjacent_ok": bool(aok), "class": P.classify(Pp, key, adjacent_ok=bool(aok))})
    F = pd.DataFrame(fin); pd.DataFrame(rows).to_csv(os.path.join(OUT, "RESERVE_R1_EVENTS.csv"), index=False); F.to_csv(os.path.join(OUT, "RESERVE_R1_CLASSIFICATION.csv"), index=False)
    Cp.to_csv(os.path.join(OUT, "RESERVE_R1_CONSTITUENTS.csv"), index=False); n = P.ledger(rows, "RESERVE_R1", "TRAPPED", "RESERVE")
    pd.set_option("display.width", 250); print(pd.DataFrame(rows)[["instrument", "n_events", "h12_xF", "h24_xF", "h1615_xF", "h1615_mean"]].round(4)); print(F.round(4).to_string()); print(Cp.round(4).to_string())
    json.dump({"ledger_rows": n, "definitions_new": 1, "classes": F["class"].tolist()}, open(os.path.join(OUT, "R1_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
