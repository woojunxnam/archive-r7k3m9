"""PH3 D1-D8 location x context x trigger event studies (prereg 33f1203)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import da_atlas as AT  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_state as RP  # noqa: E402

NB = P.NB; OUT = os.path.join(R.OUT, "ph3"); os.makedirs(OUT, exist_ok=True); HZ = ["h6", "h12", "h24", "h1615"]


def near_any(Lstack, x, A, r=0.15):
    return np.any(np.abs(Lstack - x) <= r * A, axis=0)


def sup_machines(m, lvl, band):
    n = m.n; c, h, l_ = m.c, m.h, m.l; out = {k: np.zeros((n, NB), bool) for k in ("D1", "D2", "LN1", "LN2")}; aux = {}
    for s in range(n):
        st = 0; L0 = fb = q = 0
        for b in range(1, 68):
            L = lvl[s, b - 1]
            if st and b > fb + 24:
                st = 0
            if st == 0:
                if L == L and c[s, b] < L and c[s, b - 1] >= L:
                    st, L0, fb = 1, L, b
                continue
            if st == 1:
                if b > fb + 12:
                    st = 0
                elif c[s, b] > L0:
                    out["LN1"][s, b] = True; st = 2
                continue
            if c[s, b] < L0:
                st = 0; continue
            if st == 2 and c[s, b] > h[s, b - 1]:
                q = b; st = 3
            elif st == 3:
                if c[s, b] < l_[s, q]:
                    st = 4
                elif b > q + 3:
                    st = 0
            elif st == 4 and c[s, b] > h[s, b - 1]:
                out["D1"][s, b] = True; aux[("D1", s, b)] = (L0, fb); st = 0
        st = 0
        for b in range(1, 68):
            L = lvl[s, b - 1]
            if st == 0:
                if L == L and l_[s, b] < L and c[s, b] > L and c[s, b - 1] > L:
                    L0, sl, sr, fb = L, l_[s, b], b, b; out["LN2"][s, b] = True; st = 2
                elif L == L and c[s, b] < L and c[s, b - 1] >= L:
                    L0, sl, fb = L, l_[s, b], b; st = 1
                continue
            if st == 1:
                sl = min(sl, l_[s, b])
                if c[s, b] > L0:
                    sr = b; out["LN2"][s, b] = True; st = 2
                elif b > fb + 3:
                    st = 0
                continue
            if c[s, b] < L0:
                st = 0; continue
            if st == 2:
                if b > sr + 12:
                    st = 0
                elif b > sr and l_[s, b] <= L0 + band[s, b] and l_[s, b] > sl:
                    rt = b; st = 3
            elif st == 3:
                if c[s, b] > h[s, rt]:
                    out["D2"][s, b] = True; aux[("D2", s, b)] = (L0, fb); st = 0
                elif b > rt + 6:
                    st = 0
    return out, aux


def brk_machines(m, lvl, band):
    n = m.n; c, h, l_ = m.c, m.h, m.l; out = {k: np.zeros((n, NB), bool) for k in ("D3", "D7", "LN3")}
    for s in range(n):
        for kind in ("D3", "D7"):
            st = 0
            for b in range(1, 68):
                L = lvl[s, b - 1]
                if st and b > bb + 24:
                    st = 0
                if st == 0:
                    if L == L and c[s, b] > L and c[s, b - 1] <= L:
                        st, L0, bb, mh = 1, L, b, h[s, b]
                        if kind == "D3":
                            out["LN3"][s, b] = True
                    continue
                mprev = mh; mh = max(mh, h[s, b])
                if kind == "D3":
                    if c[s, b] < L0:
                        st = 0
                    elif st == 1:
                        if b > bb + 12:
                            st = 0
                        elif l_[s, b] <= L0 + band[s, b]:
                            st = 2
                    elif st == 2 and c[s, b] > h[s, b - 1]:
                        st = 3
                    elif st == 3 and c[s, b] < c[s, b - 1]:
                        st = 4
                    elif st == 4 and c[s, b] > mprev:
                        out["D3"][s, b] = True; st = 0
                else:
                    if st == 1:
                        if c[s, b] < L0:
                            st, fb = 2, b
                        elif b > bb + 6:
                            st = 0
                    elif st == 2:
                        if c[s, b] > L0:
                            st = 3
                        elif b > fb + 6:
                            st = 0
                    elif st == 3:
                        if c[s, b] < L0:
                            st = 0
                        elif c[s, b] > mprev:
                            out["D7"][s, b] = True; st = 0
    return out


def main():
    M = P.markets(); E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet")); rows = []
    for i in P.INSTS:
        m = M[i]; A = m.a[:, None]; Lv, F = AT.build(m); band = 0.25 * m.atr5
        Ss = np.stack([Lv[k] for k in AT.SUP]); Rs = np.stack([Lv[k] for k in AT.RES])
        # level "standing on" at b-1 is evaluated inside the machines as lvl[s, b-1]
        sup_lvl = F["sup"]; res_lvl = F["res"].copy()
        res_lvl[F["res_type"] == AT.RES.index("ORH")] = np.nan
        g6l = pd.Series(m.l.ravel()).rolling(6).min().shift(1).values.reshape(m.n, NB).copy(); g6h = pd.Series(m.h.ravel()).rolling(6).max().shift(1).values.reshape(m.n, NB).copy()
        g6l[near_any(Ss, g6l[None], A[None])] = np.nan; g6h[near_any(Rs, g6h[None], A[None])] = np.nan
        ev, aux = sup_machines(m, sup_lvl, band); evp, _ = sup_machines(m, g6l, band)
        bk = brk_machines(m, res_lvl, band); bkp = brk_machines(m, g6h, band)
        D = {"D1": ev["D1"], "D1P": evp["D1"], "LN1": ev["LN1"], "D2": ev["D2"], "D2P": evp["D2"], "LN2": ev["LN2"],
             "D3": bk["D3"], "D3P": bkp["D3"], "LN3": bk["LN3"], "D7": bk["D7"], "D7P": bkp["D7"]}
        pl12 = pd.Series(m.l.ravel()).rolling(13).min().values.reshape(m.n, NB); atloc = near_any(Ss, pl12[None], A[None])
        for nm, cand in (("D1B", "C2_P2_FAILED_FIRST"), ("D8", "C3_P1_H2")):
            e = E[(E.candidate == cand) & (E.inst == i)]; mk = np.zeros((m.n, NB), bool); mk[e.s.values, e.b.values] = True
            D[nm] = mk & atloc; D[nm + "_P"] = mk & ~atloc
        prv = np.concatenate([np.full((m.n, 1), np.nan), sup_lvl[:, :-1]], 1); tch = (m.l <= prv + band) & (m.c > prv) & (m.bidx >= 1)
        D["TOUCH"] = tch & (np.cumsum(tch, 1) == 1)
        # magnitude null over all valid bars
        pop = m.valid.copy(); rng12 = (pd.Series(m.h.ravel()).rolling(12).max() - pd.Series(m.l.ravel()).rolling(12).min()).values.reshape(m.n, NB) / A
        bins = [P.causal_bins(m, pop, F["disp6"], 3), P.causal_bins(m, pop, rng12, 3)]
        X = {h: m.R[h] - P.cell_null(m, np.zeros_like(pop), pop, h, bins, target=pop)[0] for h in HZ}
        for nm, mk in D.items():
            ss, bb = np.where(mk & m.valid & (m.bidx <= 67))
            d = pd.DataFrame({"def": nm, "inst": i, "s": ss, "b": bb, "date": m.date[ss, bb], "year": m.year[ss, bb], "vt": m.vt[ss, bb], "cost": m.cost[ss],
                              "atr": m.a[ss], "pv": m.I.pv, "cs": m.I.cs, "cs4": m.I.cs4, "entry": m.entry[ss, bb],
                              "mfe60": m.P["mfe60"][ss, bb], "mae60": m.P["mae60"][ss, bb], "t_mfe": m.P["t_mfe"][ss, bb]})
            for h in HZ:
                d[f"R_{h}"] = m.R[h][ss, bb]; d[f"x_{h}"] = X[h][ss, bb]
            for k in ("up_room", "down_room", "no_res", "conf_sup_15", "sup_type", "res_type", "disp6", "sup_age", "sup_touch"):
                d[k] = F[k][ss, bb]
            # event-level confluence around the event level and approach features at the failure bar (D1 / D2)
            lvl_ev = np.full(len(d), np.nan); fbar = np.full(len(d), -1)
            if nm in ("D1", "D2"):
                for j, (s_, b_) in enumerate(zip(ss, bb)):
                    lvl_ev[j], fbar[j] = aux[(nm, s_, b_)]
            elif nm in ("D1B", "D8"):
                lvl_ev = pl12[ss, bb]
            for r in (10, 15, 20):
                d[f"ev_conf_{r}"] = [np.nansum(np.abs(Ss[:, s_, b_] - lv) <= r / 100 * m.a[s_]) if lv == lv else np.nan for s_, b_, lv in zip(ss, bb, lvl_ev)]
            for k in ("disp6", "bars_since_high", "bear_frac6", "consec_bear", "range_contract", "lower_wick", "cpos_chg3", "sup_touch"):
                d[f"ap_{k}"] = [F[k][s_, f_] if f_ >= 0 else np.nan for s_, f_ in zip(ss, fbar)]
            rows.append(d)
        print(i, {k: int(v.sum()) for k, v in D.items()}, flush=True)
    T = pd.concat(rows, ignore_index=True); T.to_parquet(os.path.join(OUT, "PH3_EVENTS.parquet"))


if __name__ == "__main__":
    main()
