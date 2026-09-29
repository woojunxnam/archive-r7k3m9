"""P1 CANDIDATE_BANK_V1 (prereg f7eff97): exact frozen event reproduction (with MASTER parity), frozen features, targets."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as MS  # noqa: E402
import rp_state as R  # noqa: E402
import t103_pullback as T3  # noqa: E402
import t104_levels as T4  # noqa: E402
import r1_trapped as R1  # noqa: E402
from t99_htf import htf, to5  # noqa: E402
from t115_trend import feats as htf_daily  # noqa: E402

NB = P.NB; OUT = os.path.join(R.OUT, "bank"); os.makedirs(OUT, exist_ok=True)
CANDS = ["C1_R1_TRAPPED_UNION", "C2_P2_FAILED_FIRST", "C3_P1_H2", "C4_L2_FAMILY", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m", "REF_A2_ACD", "REF_ORB15"]


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def shift2(X, k):
    n, nk = X.shape; f = X.ravel().astype(float); o = np.full(f.shape, np.nan); o[k:] = f[:-k]; return o.reshape(n, nk)


def events(m):
    """returns {candidate: (mask, label array)} for one instrument, exact frozen code."""
    n = m.n; out = {}; lab = lambda s: np.full((n, NB), s, object)
    e21 = pd.Series(m.c.ravel()).ewm(span=21, adjust=False).mean().values.reshape(n, NB)
    ev3, _, _, _ = T3.detect(m, e21)
    out["C2_P2_FAILED_FIRST"] = (ev3["P2_FAILED_FIRST"], lab("P2")); out["C3_P1_H2"] = (ev3["P1_H2"], lab("P1_H2"))
    Lv = T4.levels(m); ev4, _ = T4.detect(m, Lv)
    l2 = np.zeros((n, NB), bool); l2lab = lab("")
    for nm in T4.SUP:                                        # one population; a bar that is an event for several levels is one row (first level in SUP order)
        e = ev4[f"L2_{nm}"]; new = e & ~l2; l2lab[new] = f"L2_{nm}"; l2 |= e
    out["C4_L2_FAMILY"] = (l2, l2lab); out["C7_L1_SWH60"] = (ev4["L1_SWH60"], lab("L1_SWH60"))
    a3, _ = R1.a3_events(m)
    # C1 union: earliest event per session among P2, L2_*, A3 (same order / rule as r1_trapped.main)
    cons = [("P2", ev3["P2_FAILED_FIRST"])] + [(f"L2_{nm}", ev4[f"L2_{nm}"]) for nm in T4.SUP] + [("A3", a3)]
    firstb = np.full(n, 10 ** 6); owner = {}
    for nm, ev in cons:
        e = ev & m.valid & (m.bidx <= 67)
        for s, b in zip(*np.where(e)):
            if b < firstb[s]:
                firstb[s] = b; owner[s] = nm
    u = np.zeros((n, NB), bool); ul = lab("")
    for s, nm in owner.items():
        u[s, firstb[s]] = True; ul[s, firstb[s]] = nm
    out["C1_R1_TRAPPED_UNION"] = (u, ul)
    # C5 HTF1 30m (t99 code)
    O, H, L, C, nk, _ = htf(m, 6); fl = lambda X: pd.Series(X.ravel())
    rng = H - L; body = C - O; cpos = np.where(rng > 0, (C - L) / np.where(rng > 0, rng, 1), 0.5)
    mr20 = fl(rng).rolling(20, min_periods=20).mean().shift(1).values.reshape(n, nk)
    h1 = (body > 0) & (np.where(rng > 0, body / np.where(rng > 0, rng, 1), 0) >= 0.60) & (cpos >= 0.80) & (rng >= 1.25 * mr20)
    out["C5_HTF1_30m"] = (to5(m, h1, 6, nk), lab("HTF1_30m"))
    # C6 AV_OR30 (t101 code)
    I = m.I; tp = (I.H + I.L + I.C) / 3.0; V = I.V
    CS = np.concatenate([np.zeros((n, 1)), np.cumsum(tp * V, 1)], 1); CV = np.concatenate([np.zeros((n, 1)), np.cumsum(V, 1)], 1); CT = np.concatenate([np.zeros((n, 1)), np.cumsum(tp, 1)], 1)
    A = first((m.c > np.max(m.h[:, :6], 1)[:, None]) & (m.bidx >= 6) & (m.bidx <= 60)); b_end = 5 * np.arange(NB) + 5
    has = A.any(1); a = np.where(has, A.argmax(1), 10 ** 6); after = (m.bidx > a[:, None]); j0 = np.clip(5 * a, 0, 5 * NB)[:, None]
    num = CS[:, b_end] - np.take_along_axis(CS, j0, 1); den = CV[:, b_end] - np.take_along_axis(CV, j0, 1)
    tpm = (CT[:, b_end] - np.take_along_axis(CT, j0, 1)) / np.maximum(b_end[None, :] - j0, 1)
    av = np.where(den > 0, num / np.where(den > 0, den, 1), tpm); av[~after] = np.nan
    out["C6_AV_OR30"] = (first(after & (m.c > av) & (m.l <= av + 0.25 * m.atr5)), lab("AV_OR30"))
    # C8 CHOCH 15m (t109 code)
    O, H, L, C, nk, _ = htf(m, 3); fh = H.ravel(); ph = np.full(fh.shape, np.nan)
    for t in range(4, len(fh)):
        p = t - 2
        if fh[p] > max(fh[p - 2], fh[p - 1], fh[p + 1], fh[p + 2]):
            ph[t] = fh[p]
    last2 = pd.Series(ph).ffill().values; piv = pd.Series(ph).dropna(); pv = pd.Series(np.nan, index=range(len(fh))); pv[piv.index] = piv.shift(1).values
    prevp = pv.ffill().values; cf = C.ravel(); pcf = np.r_[np.nan, cf[:-1]]
    ch = ((last2 < prevp) & (cf > last2) & (pcf <= last2)).reshape(n, nk); ch = ch & (np.cumsum(ch, 1) == 1)
    out["C8_CHOCH_15m"] = (to5(m, ch, 3, nk), lab("CHOCH_15m"))
    # references (t106 code)
    rgd = np.nanmax(I.H, 1) - np.nanmin(I.L, 1); avd = 0.10 * pd.Series(rgd).rolling(10, min_periods=10).mean().shift(1).values
    orh = np.max(m.h[:, :3], 1); win = (m.bidx >= 3) & (m.bidx <= 60)
    out["REF_A2_ACD"] = (first((m.c >= (orh + avd)[:, None]) & win), lab("A2")); out["REF_ORB15"] = (first((m.c > orh[:, None]) & win), lab("ORB15"))
    return out


def features(m):
    I = m.I; n = m.n; a = m.a[:, None]; c = m.c; F = {}
    F["tod"] = m.bidx / 80.0; F["disp1"] = m.disp; F["rng_atr5"] = m.rng_atr5; F["body_pct"] = m.body_pct; F["cpos"] = m.cpos
    cs = pd.Series(c.ravel()); hs = pd.Series(m.h.ravel()); ls = pd.Series(m.l.ravel())
    F["disp6"] = (cs - cs.shift(6)).values.reshape(n, NB) / a; F["disp12"] = (cs - cs.shift(12)).values.reshape(n, NB) / a
    F["rng12"] = (hs.rolling(12).max() - ls.rolling(12).min()).values.reshape(n, NB) / a
    hi = np.fmax.accumulate(m.h, 1); lo = np.fmin.accumulate(m.l, 1); op = m.open0[:, None]
    F["sess_ret"] = (c - op) / a; F["sess_range"] = (hi - lo) / a; F["dist_hi"] = (hi - c) / a; F["dist_lo"] = (c - lo) / a
    orh = np.max(m.h[:, :6], 1)[:, None]; orl = np.min(m.l[:, :6], 1)[:, None]
    F["or_pos"] = np.where(m.bidx >= 6, (c - orl) / np.where(orh - orl > 0, orh - orl, np.nan), np.nan)
    pcl = np.r_[np.nan, I.C[:-1, 389]][:, None]; F["gap"] = np.repeat((m.open0[:, None] - pcl) / a, NB, 1)
    lowbar = np.zeros((n, NB)); cur = np.zeros(n); curv = np.full(n, np.inf)
    for b in range(NB):
        nl = m.l[:, b] < curv; curv = np.where(nl, m.l[:, b], curv); cur = np.where(nl, b, cur); lowbar[:, b] = (b - cur) / 80.0
    F["bars_since_low"] = lowbar
    F["vwap_dist"] = (c - m.vwap) / a; vw = pd.Series(m.vwap.ravel()); F["vwap_slope6"] = (vw - vw.shift(6)).values.reshape(n, NB) / a
    ab = (c > m.vwap).astype(float); sh = np.zeros((n, NB))
    for b in range(NB):
        lo_ = max(0, b - 11); sh[:, b] = ab[:, lo_:b + 1].mean(1)
    F["share_above_vwap12"] = sh
    d = htf_daily(m)                        # already shifted: known before session d
    Hd = np.nanmax(I.H, 1); Ld = np.nanmin(I.L, 1); Cd = I.FP[:, P.E.J15]; s = pd.Series(Cd)
    up_ = np.r_[np.nan, np.diff(Hd)]; dn_ = np.r_[np.nan, -np.diff(Ld)]; pc = np.r_[np.nan, Cd[:-1]]
    pdm = np.where((up_ > dn_) & (up_ > 0), up_, 0.0); mdm = np.where((dn_ > up_) & (dn_ > 0), dn_, 0.0)
    tr = np.nanmax(np.stack([Hd - Ld, np.abs(Hd - pc), np.abs(Ld - pc)]), 0); w = lambda x: pd.Series(x).ewm(alpha=1 / 14, adjust=False).mean().values
    atr = w(np.nan_to_num(tr)); pdi = 100 * w(pdm) / atr; mdi = 100 * w(mdm) / atr; adx = w(100 * np.abs(pdi - mdi) / np.maximum(pdi + mdi, 1e-9))
    sma150 = s.rolling(150).mean()
    daily = pd.DataFrame({"up50": d["UP50"].values, "adx14": pd.Series(adx).shift(1).values, "di_up": pd.Series((pdi > mdi).astype(float)).shift(1).values,
                          "stage_slope": ((sma150 - sma150.shift(20)).shift(1) / m.a).values, "tsmom12": d["T3_TSMOM_12M"].values, "tsmom1": d["T4_TSMOM_1M"].values,
                          "prev_ret": ((s - s.shift(1)).shift(1) / m.a).values, "vt": m.I.vt.astype(float),
                          "atr_ratio": (pd.Series(Hd - Ld).rolling(5).mean() / pd.Series(Hd - Ld).rolling(60).mean()).shift(1).values})
    for k in daily:
        F[k] = np.repeat(daily[k].values[:, None], NB, 1)
    F["atr5_rel"] = m.atr5 / a
    return F


FEATS = ["tod", "disp1", "rng_atr5", "body_pct", "cpos", "disp6", "disp12", "rng12", "sess_ret", "sess_range", "dist_hi", "dist_lo", "or_pos", "gap",
         "bars_since_low", "vwap_dist", "vwap_slope6", "share_above_vwap12", "up50", "adx14", "di_up", "stage_slope", "tsmom12", "tsmom1", "prev_ret", "vt",
         "atr_ratio", "atr5_rel"]


def master_counts():
    rd = lambda p: pd.read_csv(os.path.join(MS.OUT, p))
    t99, t101, t103, t104, t106, t109, r1 = (rd("t99/T99_EVENTS.csv"), rd("t101/TEST101_EVENTS.csv"), rd("t103/TEST103_EVENTS.csv"), rd("t104/TEST104_EVENTS.csv"),
                                             rd("t106/TEST106_EVENTS.csv"), rd("t109/TEST109_EVENTS.csv"), rd("r1/RESERVE_R1_EVENTS.csv"))
    g = lambda D, v: D[(D.variant == v) & (D.instrument != "POOLED")].set_index("instrument").n_events.to_dict()
    return {"C1_R1_TRAPPED_UNION": g(r1, "R1_TRAPPED_UNION"), "C2_P2_FAILED_FIRST": g(t103, "P2_FAILED_FIRST"), "C3_P1_H2": g(t103, "P1_H2"),
            "C5_HTF1_30m": g(t99, "T99_HTF1_30m"), "C6_AV_OR30": g(t101, "AV_OR30"), "C7_L1_SWH60": g(t104, "L1_SWH60"), "C8_CHOCH_15m": g(t109, "CHOCH_15m"),
            "REF_A2_ACD": g(t106, "A2_A_UP_IMMEDIATE"), "REF_ORB15": g(t106, "ORB_COMPARATOR"),
            **{f"L2_{x}": g(t104, f"L2_{x}") for x in T4.SUP}}


def main():
    M = P.markets(); rows = []; par = {}; mc = master_counts()
    for i in P.INSTS:
        m = M[i]; I = m.I; ev = events(m); F = features(m)
        for cand, (mask, labl) in ev.items():
            e = mask & m.valid & (m.bidx <= 67)
            if cand == "C4_L2_FAMILY":
                for nm in T4.SUP:          # parity per constituent level (a bar shared by 2 levels counts once in the family)
                    par.setdefault(f"L2_{nm}", {})[i] = None
            else:
                par.setdefault(cand, {})[i] = (int(e.sum()), int(mc[cand][i]))
            ss, bb = np.where(e)
            d = pd.DataFrame({"candidate": cand, "inst": i, "s": ss, "b": bb, "label": labl[ss, bb], "date": m.date[ss, bb], "year": m.year[ss, bb],
                              "cost_atr": m.cost[ss], "atr": m.a[ss], "pv": I.pv, "cs": I.cs, "cs4": I.cs4, "entry": m.entry[ss, bb]})
            for h in ("h12", "h24", "h1615"):
                rr = m.R[h][ss, bb]; d[f"R_{h}"] = rr; d[f"net_{h}"] = rr - m.cost[ss]
                d[f"usd_{h}"] = rr * m.a[ss] * I.pv - 2 * I.cs; d[f"usd4_{h}"] = rr * m.a[ss] * I.pv - 2 * I.cs4
            for k in FEATS:
                d[k] = F[k][ss, bb]
            rows.append(d)
        # L2 constituent parity (each level's own events)
        Lv = T4.levels(m); ev4, _ = T4.detect(m, Lv)
        for nm in T4.SUP:
            par[f"L2_{nm}"][i] = (int((ev4[f"L2_{nm}"] & m.valid & (m.bidx <= 67)).sum()), int(mc[f"L2_{nm}"][i]))
    D = pd.concat(rows, ignore_index=True)
    ok = {k: all(a == b for a, b in v.values()) for k, v in par.items()}
    D.to_parquet(os.path.join(OUT, "CANDIDATE_EVENTS.parquet"), index=False)
    json.dump({"parity": {k: {i: list(v) for i, v in d.items()} for k, d in par.items()}, "parity_ok": ok}, open(os.path.join(OUT, "BANK_PARITY.json"), "w"), indent=1)
    print(json.dumps(ok, indent=0)); print(D.groupby("candidate").size())


if __name__ == "__main__":
    main()
