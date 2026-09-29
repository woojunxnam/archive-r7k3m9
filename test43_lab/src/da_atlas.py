"""PH2 causal level atlas + state features (prereg 13ca487)."""
import copy
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import t104_levels as T4  # noqa: E402
from t99_htf import htf  # noqa: E402

NB = P.NB; OUT = os.path.join(R.OUT, "atlas"); os.makedirs(OUT, exist_ok=True)
SUP = ["PDL", "PWL", "SW30L", "SW60L", "R2HL", "R4HL", "ORL", "BRS"]; RES = ["PDH", "PWH", "SW30H", "SW60H", "R2HH", "R4HH", "ORH", "BSR"]


def swings(m, m5):
    O, H, L, C, nk, _ = htf(m, m5); n = m.n; Hf, Lf = H.ravel(), L.ravel(); sh = np.full(Hf.shape, np.nan); sl = np.full(Lf.shape, np.nan); ch = cl = np.nan
    for t in range(len(Hf)):
        if t >= 4:
            p = t - 2
            if Hf[p] > max(Hf[p - 2], Hf[p - 1], Hf[p + 1], Hf[p + 2]):
                ch = Hf[p]
            if Lf[p] < min(Lf[p - 2], Lf[p - 1], Lf[p + 1], Lf[p + 2]):
                cl = Lf[p]
        sh[t] = ch; sl[t] = cl
    sh = sh.reshape(n, nk); sl = sl.reshape(n, nk); ph = np.r_[np.nan, sh[:-1, -1]]; pl = np.r_[np.nan, sl[:-1, -1]]
    oh = np.full((n, NB), np.nan); ol = np.full((n, NB), np.nan)
    for b in range(NB):
        k = (b + 1) // m5 - 1; k = min(k, nk - 1)
        oh[:, b] = sh[:, k] if k >= 0 else ph; ol[:, b] = sl[:, k] if k >= 0 else pl
    return oh, ol


def broken(m, lv, up):
    """most recent level (of the given types) closed through in the session; invalidated when price closes back through it."""
    n = m.n; out = np.full((n, NB), np.nan); c = m.c
    for s in range(n):
        cur = np.nan
        for b in range(1, NB):
            if cur == cur and ((up and c[s, b] < cur) or (not up and c[s, b] > cur)):
                cur = np.nan
            for L in lv:
                a, p = L[s, b], L[s, b - 1]
                if a == a and p == p and ((up and c[s, b] > a and c[s, b - 1] <= p) or (not up and c[s, b] < a and c[s, b - 1] >= p)):
                    cur = a
            out[s, b] = cur
    return out


def levels(m):
    base = T4.levels(m); n = m.n; Lv = {}
    Lv["PDL"], Lv["PDH"], Lv["PWL"], Lv["PWH"] = base["PDL"], base["PDH"], base["PWL"], base["PWH"]
    orh = base["ORH"].copy(); orl = base["ORL"].copy(); orh[:, :6] = np.nan; orl[:, :6] = np.nan; Lv["ORH"], Lv["ORL"] = orh, orl
    Lv["SW60H"], Lv["SW60L"] = base["SWH60"], base["SWL60"]; Lv["SW30H"], Lv["SW30L"] = swings(m, 6)
    Hs = pd.Series(m.h.ravel()); Ls = pd.Series(m.l.ravel())
    Lv["R2HH"], Lv["R2HL"] = base["H2H"], base["L2H"]
    Lv["R4HH"] = Hs.rolling(48, min_periods=48).max().shift(1).values.reshape(n, NB); Lv["R4HL"] = Ls.rolling(48, min_periods=48).min().shift(1).values.reshape(n, NB)
    Lv["BRS"] = broken(m, [Lv[k] for k in ("PDH", "PWH", "SW30H", "SW60H")], True); Lv["BSR"] = broken(m, [Lv[k] for k in ("PDL", "PWL", "SW30L", "SW60L")], False)
    return Lv


def age(L):
    f = L.ravel(); a = np.zeros(f.shape); cur = 0
    for i in range(1, len(f)):
        cur = cur + 1 if (f[i] == f[i - 1]) else 0; a[i] = min(cur, 5 * NB)
    return a.reshape(L.shape)


def state(m, Lv):
    n = m.n; c = m.c; A = m.a[:, None]; F = {}
    S = np.stack([Lv[k] for k in SUP]); Rr = np.stack([Lv[k] for k in RES])
    Sb = np.where(S < c[None], S, -np.inf); si = np.argmax(Sb, 0); Sn = np.take_along_axis(Sb, si[None], 0)[0]; Sn[~np.isfinite(Sn)] = np.nan
    Ra = np.where(Rr > c[None], Rr, np.inf); ri = np.argmin(Ra, 0); Rn = np.take_along_axis(Ra, ri[None], 0)[0]; Rn[~np.isfinite(Rn)] = np.nan
    F["sup"] = Sn; F["sup_type"] = np.where(np.isnan(Sn), -1, si); F["res"] = Rn; F["res_type"] = np.where(np.isnan(Rn), -1, ri)
    F["down_room"] = (c - Sn) / A; F["up_room"] = (Rn - c) / A; F["no_res"] = np.isnan(Rn).astype(float)
    F["room_asym"] = F["up_room"] / (F["up_room"] + F["down_room"])
    for r in (0.10, 0.15, 0.20):
        F[f"conf_sup_{int(r*100)}"] = np.nansum(np.abs(S - Sn[None]) <= r * A[None], 0).astype(float); F[f"conf_res_{int(r*100)}"] = np.nansum(np.abs(Rr - Rn[None]) <= r * A[None], 0).astype(float)
    S2 = np.where(S < Sn[None] - 1e-9, S, -np.inf).max(0); S2[~np.isfinite(S2)] = np.nan; F["sup_spacing"] = (Sn - S2) / A
    ages = np.stack([age(Lv[k]) for k in SUP]); F["sup_age"] = np.take_along_axis(ages, si[None], 0)[0]
    tc = np.zeros((n, NB)); band = 0.25 * m.atr5
    for b in range(1, NB):
        tc[:, b] = ((m.l[:, :b] <= (Sn[:, b] + band[:, b])[:, None]) & (c[:, :b] > Sn[:, b][:, None])).sum(1)
    F["sup_touch"] = tc
    cs = pd.Series(c.ravel()); F["disp6"] = (cs - cs.shift(6)).values.reshape(n, NB) / A
    hib = np.zeros((n, NB)); cur = np.zeros(n); hv = np.full(n, -np.inf)
    for b in range(NB):
        nh = m.h[:, b] > hv; hv = np.where(nh, m.h[:, b], hv); cur = np.where(nh, b, cur); hib[:, b] = b - cur
    F["bars_since_high"] = hib
    bear = (m.c < m.o).astype(float); bs = pd.Series(bear.ravel()); F["bear_frac6"] = bs.rolling(6).mean().values.reshape(n, NB)
    run = np.zeros(bear.size); bf = bear.ravel()
    for i in range(bf.size):
        run[i] = run[i - 1] + 1 if (bf[i] and i) else (1 if bf[i] else 0)
    F["consec_bear"] = run.reshape(n, NB)
    rg = pd.Series((m.h - m.l).ravel()); F["range_contract"] = (rg.rolling(3).mean() / rg.shift(3).rolling(6).mean()).values.reshape(n, NB)
    F["lower_wick"] = np.where(m.h > m.l, (np.minimum(m.o, m.c) - m.l) / np.where(m.h > m.l, m.h - m.l, 1), 0.0)
    cp = pd.Series(m.cpos.ravel()); F["cpos_chg3"] = (cp - cp.shift(3)).values.reshape(n, NB)
    return F


def build(m):
    Lv = levels(m); F = state(m, Lv); return Lv, F


def proxy(m, cut_idx, seed=3):
    """copy of m with every session >= cut_idx replaced by noise (prefix-invariance audit)."""
    q = copy.copy(m); I = copy.copy(m.I); rng = np.random.default_rng(seed)
    for nm in ("o", "h", "l", "c"):
        a = getattr(m, nm).copy(); a[cut_idx:] = a[cut_idx:] * (1 + rng.normal(0, 0.01, a[cut_idx:].shape)); setattr(q, nm, a)
    q.h = np.maximum.reduce([q.h, q.o, q.c, q.l]); q.l = np.minimum.reduce([q.l, q.o, q.c, q.h])
    for nm in ("H", "L", "C", "O"):
        a = getattr(m.I, nm).copy(); a[cut_idx:] = a[cut_idx:] * (1 + rng.normal(0, 0.01, a[cut_idx:].shape)); setattr(I, nm, a)
    q.I = I; return q


def main():
    M = P.markets(); summ = {}; audit = {}
    for i in P.INSTS:
        m = M[i]; Lv, F = build(m)
        np.savez_compressed(os.path.join(OUT, f"ATLAS_{i}.npz"), **{f"L_{k}": v.astype(np.float32) for k, v in Lv.items()}, **{f"F_{k}": v.astype(np.float32) for k, v in F.items()})
        v = m.valid & (m.bidx <= 67)
        summ[i] = {"level_availability": {k: float(np.mean(~np.isnan(Lv[k][v]))) for k in SUP + RES},
                   "up_room_quantiles": [float(x) for x in np.nanpercentile(F["up_room"][v], [10, 25, 50, 75, 90])],
                   "down_room_quantiles": [float(x) for x in np.nanpercentile(F["down_room"][v], [10, 25, 50, 75, 90])],
                   "no_res_share": float(np.mean(F["no_res"][v])), "conf_sup_15_dist": {int(k): int(c) for k, c in pd.Series(F["conf_sup_15"][v]).value_counts().sort_index().items()},
                   "sup_type_share": {SUP[k] if k >= 0 else "none": float(c) for k, c in pd.Series(F["sup_type"][v]).value_counts(normalize=True).items()}}
        if i == "ES":
            cut = int(np.searchsorted(m.I.sess.values, np.datetime64("2025-01-01")))
            q = proxy(m, cut); Lq, Fq = build(q)
            audit = {k: int(np.sum(~((Lv[k][:cut] == Lq[k][:cut]) | (np.isnan(Lv[k][:cut]) & np.isnan(Lq[k][:cut]))))) for k in Lv}
            audit.update({f"F_{k}": int(np.sum(~((F[k][:cut] == Fq[k][:cut]) | (np.isnan(F[k][:cut]) & np.isnan(Fq[k][:cut]))))) for k in F})
        print(i, "done", flush=True)
    json.dump({"summary": summ, "prefix_invariance_mismatches_ES": audit, "PREFIX_INVARIANCE": "PASS" if sum(audit.values()) == 0 else "FAIL"},
              open(os.path.join(OUT, "ATLAS_SUMMARY.json"), "w"), indent=1)
    print(json.dumps(audit), sum(audit.values()))


if __name__ == "__main__":
    main()
