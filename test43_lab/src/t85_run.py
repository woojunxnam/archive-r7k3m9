"""TEST85 AUCTION-STATE + MOMENTUM EVENT ATLAS (program prereg 9caacd4a).  Profile events under 3 allocation proxies, momentum events price-only
(M9 / M10 per proxy); horizons + controls A (matched) / B (momentum) / C (volume) / D (short momentum)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
from t84_run import features  # noqa: E402

OUT = os.path.join(A.AP, "TEST85"); os.makedirs(OUT, exist_ok=True)
SPEC = {"events": "exactly the program preregistration lists (profile PA1..PJ, momentum M1..M68); first occurrence per session",
        "qualification_rule_clarified_before_run": "profile cell (event x instrument x horizon) QUALIFIES iff >= 2 of 3 proxies each satisfy ALL: net > 0, "
        "SLIP4 net > 0, B > 0 and >= 4/5 folds, A > 0, C > 0, D > 0, n >= 300, min fold n >= 40.  Momentum cell: same without the proxy / C requirement.",
        "PH_PRICE_NULL": "P4-window high-low range 30 min earlier < 0.20 ATR_d AND the 60m range midpoint up >= 0.05 ATR_d since",
        "M4_DECAY_EXIT": "diagnostic: M3_PERSIST entries, exit at the first 1m close below session VWAP (next open) vs hold to 16:15",
        "budget": {"hypotheses": "profile 20 event types x 3 proxies x 2 instruments x 9 horizons; momentum 21 event types x 2 x 9 (reported)"}}


def first(mask):
    """first True slot per session (-1 none)."""
    has = mask.any(1); return np.where(has, mask.argmax(1), -1)


def ev(name, bslot, extra=None):
    s = np.where(bslot >= 0)[0]
    return pd.DataFrame({"event": name, "s": s, "j": A.DEC[bslot[s]]})


def grid(I, other):
    a = I.atr[:, None]; D = A.DEC
    c5 = I.C[:, D]; h5 = I.h5; l5 = I.l5; o = I.FP[:, :1]
    rh = np.maximum.accumulate(h5, 1); vw = I.vwap[:, D]
    ro = (c5 - o) / a
    path = np.cumsum(np.abs(np.diff(I.C, axis=1, prepend=I.C[:, :1])), 1)[:, D]
    eff = np.abs(c5 - o) / np.maximum(path, 1e-9)
    oth = (other.C[:, D] - other.FP[:, :1]) / other.atr[:, None]
    hi60 = pd.DataFrame(I.H.T).rolling(60, min_periods=1).max().T.values[:, D]; lo60 = pd.DataFrame(I.L.T).rolling(60, min_periods=1).min().T.values[:, D]
    prevhi60 = np.concatenate([np.full((I.n, 1), np.inf), pd.DataFrame(I.H.T).rolling(60, min_periods=1).max().T.values[:, :-1]], 1)[:, D]
    above = (I.C > I.vwap).astype(float)
    return dict(a=a, c5=c5, h5=h5, l5=l5, rh=rh, vw=vw, ro=ro, eff=eff, oth=oth, mid60=(hi60 + lo60) / 2, rng60=hi60 - lo60, prevhi60=prevhi60, above=above)


def lag(x, k):
    if k == 0:
        return x.astype(float)
    return np.concatenate([np.full((x.shape[0], k), np.nan), x[:, :-k]], 1)


def profile_events(I, g, P1, F, HV, LV):
    a = g["a"]; c5, h5, l5, rh = g["c5"], g["h5"], g["l5"], g["rh"]
    f = lambda k: F[..., A.FEAT[k]]
    P2P, P4P, P4H, P4L = f("P2_POC"), f("P4_POC"), f("P4_VAH"), f("P4_VAL")
    b = np.arange(A.NB5)[None, :]
    vah1 = P1[:, 1][:, None]; val1 = P1[:, 2][:, None]
    d4 = P4P - lag(P4P, 6); d2 = P2P - lag(P2P, 6)
    E = []
    E.append(ev("PA1_POC_UP", first((d4 >= 0.05 * a) & (b >= 12))))
    E.append(ev("PA2_VALUE_UP_ALL", first((d4 > 0) & (P4H > lag(P4H, 6)) & (P4L > lag(P4L, 6)) & (b >= 12))))
    E.append(ev("PB1_VAH_POKE", first((h5 > vah1) & (b >= 1))))
    E.append(ev("PB2_VAH_CLOSE", first((c5 > vah1) & (b >= 1))))
    E.append(ev("PB3_VAH_TWO", first((c5 > vah1) & (lag(c5, 1) > vah1) & (b >= 2))))
    E.append(ev("PB4_VAH_ACCEPT", first((c5 > vah1) & (f("P2_ABOVE_P1VAH") >= 0.30) & (b >= 1))))
    E.append(ev("PC1_DPOC_UP", first((d2 >= 0.05 * a) & (b >= 6))))
    ups = np.zeros_like(d2); dns = np.zeros_like(d2); st = P2P - lag(P2P, 1)
    for k in range(12):
        x = lag(st, k); ups += np.nan_to_num(x > 0); dns += np.nan_to_num(x < 0)
    E.append(ev("PC2_DPOC_MULTI", first((ups >= 2) & (dns == 0) & (b >= 12))))
    pc1 = (d2 >= 0.05 * a)
    rec = np.zeros_like(pc1)
    for k in range(7):
        rec |= np.nan_to_num(lag(pc1.astype(float), k)).astype(bool)
    newhi_recent = rh[:, :] > np.nan_to_num(lag(rh, 6), nan=np.inf)
    newhi_recent = np.nan_to_num(lag(rh.astype(float), 1)) > np.nan_to_num(lag(rh, 7), nan=np.inf)
    E.append(ev("PF_RISING_POC_PULLBACK", first(rec & (P4L > lag(P4L, 6)) & (l5 <= f("P2_VAH")) & (c5 >= P2P) & newhi_recent & (b >= 12))))
    E.append(ev("PG_UP_STACK", first((f("P2_VAL") > vah1) & (b >= 11))))
    b12 = 29
    st12 = np.where(f("P2_VAL")[:, b12] > P1[:, 1], "UP_STACK", np.where(f("P2_VAH")[:, b12] < P1[:, 2], "DOWN_STACK", "OVERLAP"))
    for nm in ("UP_STACK", "OVERLAP", "DOWN_STACK"):
        sl = np.where((st12 == nm) & ~np.isnan(P1[:, 1]) & ~np.isnan(f("P2_VAL")[:, b12]), b12, -1); E.append(ev(f"PG12_{nm}", sl))
    E.append(ev("PH_VALUE_COMPRESS_EXPAND", first((lag(f("P4_WIDTH"), 6) < 0.10 * a) & (d4 >= 0.05 * a) & (b >= 18))))
    E.append(ev("PH_PRICE_NULL", first((lag(g["rng60"], 6) < 0.20 * a) & (g["mid60"] - lag(g["mid60"], 6) >= 0.05 * a) & (b >= 18))))
    nh = (c5 > np.nan_to_num(lag(rh, 1), nan=np.inf)) & (b >= 11)
    E.append(ev("PI_PRICE_POC_CONFIRM", first(nh & (d2 >= 0.05 * a))))
    E.append(ev("PI_DIVERGE", first(nh & ~(d2 >= 0.05 * a))))
    E.append(ev("PJ_VOLUME_MOMENT_LEAD", first((f("P4_VWMED") - lag(f("P4_VWMED"), 6) >= 0.05 * a) & (c5 <= g["prevhi60"]) & (b >= 18))))
    # node events (P1 HVN / LVN)
    pd_rows, pe_rows = [], []
    C1 = I.C
    for s in np.where(I.full)[0]:
        hv = HV[s][~np.isnan(HV[s][:, 0])]; lv = LV[s][~np.isnan(LV[s][:, 0])]
        if len(hv) >= 2:
            for bb in range(1, A.NB5 - 1):
                c, cp = c5[s, bb], c5[s, bb - 1]; hit = False
                for k in range(len(hv) - 1):
                    if cp <= hv[k, 2] < c < hv[k + 1, 1]:
                        pd_rows.append((s, A.DEC[bb], hv[k, 2], hv[k + 1, 1])); hit = True; break
                if hit:
                    break
        if len(lv):
            for bb in range(3, A.NB5 - 1):
                j = A.DEC[bb]; c = C1[s, j]; mn = C1[s, j - 15:j].min(); r15 = (c - C1[s, j - 15]) / I.atr[s]
                m = (c > lv[:, 0]) & (mn < lv[:, 0]) & (r15 >= 0.10)
                if m.any():
                    pe_rows.append((s, j)); break
    PD = pd.DataFrame(pd_rows, columns=["s", "j", "floor", "target"]).assign(event="PD_HVN_LVN_TRAVEL")
    E.append(PD[["event", "s", "j"]]); E.append(pd.DataFrame(pe_rows, columns=["s", "j"]).assign(event="PE_LVN_BREAK"))
    return pd.concat(E, ignore_index=True), PD


def momentum_events(I, g, F_by_proxy):
    a = g["a"]; c5, h5, l5, rh, ro, eff, vw = g["c5"], g["h5"], g["l5"], g["rh"], g["ro"], g["eff"], g["vw"]
    n = I.n; E = []
    b10, b1100, b1130, b1030 = 5, 17, 23, 11
    m1 = ro[:, b10] >= 0.30
    sl = lambda m, b_: np.where(m & I.full, b_, -1)
    E.append(ev("M1_OPEN_IMPULSE", sl(m1, b10)))
    E.append(ev("M2_QUALITY_HI", sl(m1 & (eff[:, b10] >= 0.5), b10))); E.append(ev("M2_QUALITY_LO", sl(m1 & (eff[:, b10] < 0.5), b10)))
    share = g["above"][:, 29:120].mean(1)
    base3 = ro[:, b1130] >= 0.30
    E.append(ev("M3_PERSIST", sl(base3 & (share >= 0.8), b1130))); E.append(ev("M3_ONE_TIME", sl(base3 & (share < 0.5), b1130)))
    E.append(ev("M8_AGREE", sl(m1 & (g["oth"][:, b10] >= 0.30), b10))); E.append(ev("M8_DIVERGE", sl(m1 & (g["oth"][:, b10] < 0.30), b10)))
    r1 = ro[:, b10]; r2 = ro[:, b1100] - ro[:, b10]
    E.append(ev("M68_ACCEL", sl((r2 > r1) & (r1 > 0), b1100))); E.append(ev("M68_DECEL", sl((r2 > 0) & (r2 < r1), b1100)))
    b = np.arange(A.NB5)[None, :]
    r5 = c5 - lag(c5, 1); r15 = c5 - lag(c5, 3); r60 = c5 - lag(c5, 12)
    E.append(ev("M7_MTF_5", first((r5 > 0) & (b >= 12)))); E.append(ev("M7_MTF_5_15", first((r5 > 0) & (r15 > 0) & (b >= 12))))
    E.append(ev("M7_MTF_5_60", first((r5 > 0) & (r60 > 0) & (b >= 12)))); E.append(ev("M7_MTF_5_15_60", first((r5 > 0) & (r15 > 0) & (r60 > 0) & (b >= 12))))
    # M5 second impulse, M6 failed pullback (sequential per session on the 5m grid)
    m5, m6 = np.full(n, -1), np.full(n, -1)
    for s in np.where(I.full)[0]:
        at = I.atr[s]; st = 0; imp = 0.0; c_imp = 0.0; pause = 0; lowp = np.inf
        for bb in range(3, A.NB5 - 1):
            if st == 0 and c5[s, bb] - c5[s, bb - 3] >= 0.25 * at:
                st = 1; imp = c5[s, bb] - c5[s, bb - 3]; c_imp = c5[s, bb]; hi_ref = rh[s, bb]; pause = 0; lowp = np.inf; continue
            if st == 1:
                lowp = min(lowp, l5[s, bb])
                if lowp < c_imp - 0.5 * imp:
                    st = 0; continue
                if h5[s, bb] > hi_ref:
                    if pause >= 2 and c5[s, bb] > hi_ref:
                        m5[s] = bb; break
                    hi_ref = h5[s, bb]; pause = 0
                else:
                    pause += 1
        st = 0; pl = np.inf
        for bb in range(1, A.NB5 - 1):
            trend = ro[s, bb] >= 0.40 and c5[s, bb] > vw[s, bb]
            if st == 0 and trend:
                st = 1; hi_ref = rh[s, bb]; pl = np.inf; continue
            if st == 1:
                hi_ref = max(hi_ref, h5[s, bb]) if pl == np.inf else hi_ref
                if l5[s, bb] <= vw[s, bb]:
                    st = 0; continue
                if hi_ref - l5[s, bb] >= 0.15 * at:
                    pl = min(pl, l5[s, bb])
                if pl < np.inf and c5[s, bb] >= pl + 0.5 * (hi_ref - pl):
                    m6[s] = bb; break
    E.append(ev("M5_SECOND_IMPULSE", m5)); E.append(ev("M6_FAILED_PULLBACK", m6))
    base = pd.concat(E, ignore_index=True); base["proxy"] = "PRICE"
    PV = []
    for px, F in F_by_proxy.items():
        P2P = F[..., A.FEAT["P2_POC"]]
        up60 = (P2P[:, b1130] - P2P[:, b1130 - 12]) >= 0.05 * I.atr
        x = [ev("M9_PRICE_VALUE", sl(base3 & (share >= 0.8) & up60, b1130)), ev("M9_PRICE_ONLY", sl(base3 & (share >= 0.8), b1130)),
             ev("M10_VALUE_FOLLOWS", sl(base3 & (P2P[:, b1130] > P2P[:, b1030]), b1130)), ev("M10_VALUE_LAGS", sl(base3 & ~(P2P[:, b1130] > P2P[:, b1030]), b1130))]
        PV.append(pd.concat(x, ignore_index=True).assign(proxy=px))
    return pd.concat([base] + PV, ignore_index=True)


def main():
    print(A.prereg("TEST85", SPEC))
    Is = B.load(); allP, allM, travel, decay = [], [], [], []
    for inst, I in Is.items():
        other = Is["ES" if inst == "MNQ" else "MNQ"]; g = grid(I, other); BK = A.buckets(I); nd = int(I.full.sum())
        Fp = {}
        for px in A.PROXY:
            P1, F = features(I, px); Fp[px] = F
            HV, LV = A.p1_nodes(I.H, I.L, I.C, I.V.astype(float), I.atr, 0.02, A.PROXY[px], A.J15, 16)
            E, PD = profile_events(I, g, P1, F, HV, LV)
            E = E[I.full[E.s.values] & (E.j.values + 1 < A.J15)].reset_index(drop=True)
            E = A.label(I, E, BK); E["proxy"] = px; E["instrument"] = inst; E["date"] = I.sess[E.s.values]; allP.append(E)
            # HVN travel study (target exit vs time hold)
            for r in PD.itertuples(index=False):
                s, j = int(r.s), int(r.j)
                if j + 1 >= A.J15:
                    continue
                px_in = I.FP[s, j + 1]; hit = -1; brk = -1
                for k in range(j + 1, A.J15):
                    if I.H[s, k] >= r.target:
                        hit = k; break
                    if I.C[s, k] < r.floor:
                        brk = k; break
                xk = hit if hit >= 0 else (brk + 1 if brk >= 0 else A.J15); xp = r.target if hit >= 0 else I.FPb[s, min(xk, A.J15)]
                travel.append({"instrument": inst, "proxy": px, "date": I.sess[s], "hit": hit >= 0, "time_min": (hit - j) if hit >= 0 else np.nan,
                               "target_exit_net": (xp - px_in) * I.pv - 2 * I.cs, "hold1615_net": (I.FPb[s, A.J15] - px_in) * I.pv - 2 * I.cs,
                               "mfe_atr": (I.H[s, j + 1:A.J15 + 1].max() - px_in) / I.atr[s], "mae_atr": (px_in - I.L[s, j + 1:A.J15 + 1].min()) / I.atr[s]})
        M = momentum_events(I, g, Fp)
        M = M[I.full[M.s.values] & (M.j.values + 1 < A.J15)].reset_index(drop=True)
        M = A.label(I, M, BK); M["instrument"] = inst; M["date"] = I.sess[M.s.values]; allM.append(M)
        # M4 decay exit diagnostic
        for r in M[(M.event == "M3_PERSIST")].itertuples(index=False):
            s, j = int(r.s), int(r.j); pxin = I.FP[s, j + 1]; xk = A.J15
            for k in range(j + 1, A.J15):
                if I.C[s, k] < I.vwap[s, k]:
                    xk = k + 1; break
            decay.append({"instrument": inst, "decay_exit_net": (I.FPb[s, min(xk, A.J15)] - pxin) * I.pv - 2 * I.cs, "hold_net": (I.FPb[s, A.J15] - pxin) * I.pv - 2 * I.cs})
        print(inst, "events", flush=True)
    P = pd.concat(allP, ignore_index=True); M = pd.concat(allM, ignore_index=True)
    nd = int(Is["MNQ"].full.sum())
    SP = A.summarize(P, nd, ["instrument", "event", "proxy"]); SM = A.summarize(M, nd, ["instrument", "event", "proxy"])
    ok = lambda S: (S.net > 0) & (S.net4 > 0) & (S.B > 0) & (S.folds_B_pos >= 4) & (S.A > 0) & (S.D > 0) & (S.n >= 300) & (S.min_fold_n >= 40)
    SP["cell_ok"] = ok(SP) & (SP.C > 0); SM["cell_ok"] = ok(SM)
    q = SP.groupby(["instrument", "event", "horizon"]).agg(proxies_ok=("cell_ok", "sum"), proxies_Bpos=("B", lambda v: int((v > 0).sum()))).reset_index()
    q["QUALIFIES"] = q.proxies_ok >= 2
    SP = SP.merge(q, on=["instrument", "event", "horizon"])
    SM["QUALIFIES"] = SM.cell_ok
    SP.to_csv(os.path.join(OUT, "T85_PROFILE_ATLAS.csv"), index=False); SM.to_csv(os.path.join(OUT, "T85_MOMENTUM_ATLAS.csv"), index=False)
    T = pd.DataFrame(travel); Dc = pd.DataFrame(decay)
    TS = T.groupby(["instrument", "proxy"]).agg(n=("hit", "size"), travel_prob=("hit", "mean"), med_time=("time_min", "median"), target_exit=("target_exit_net", "mean"),
                                                hold1615=("hold1615_net", "mean"), mfe=("mfe_atr", "mean"), mae=("mae_atr", "mean")).reset_index()
    DS = Dc.groupby("instrument").mean().reset_index()
    TS.to_csv(os.path.join(OUT, "T85_HVN_TRAVEL.csv"), index=False); DS.to_csv(os.path.join(OUT, "T85_DECAY_EXIT.csv"), index=False)
    P.drop(columns=["date"]).to_parquet(os.path.join(A.AP, "cache", "T85_profile_events.parquet")); M.drop(columns=["date"]).to_parquet(os.path.join(A.AP, "cache", "T85_momentum_events.parquet"))
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 500)
    cols = ["instrument", "event", "proxy", "horizon", "n", "net", "net4", "A", "B", "C", "D", "folds_B_pos"]
    print("PROFILE QUALIFYING:", q[q.QUALIFIES][["instrument", "event", "horizon"]].values.tolist())
    print("MOMENTUM QUALIFYING:", SM[SM.QUALIFIES][["instrument", "event", "proxy", "horizon"]].values.tolist())
    sel = ["h60", "h1600", "h1615"]
    print(SP[SP.horizon.isin(sel) & (SP.proxy == "VP-B")][cols].round(2).to_string())
    print(SM[SM.horizon.isin(sel + ["h1100", "h1300"])][cols].round(2).to_string())
    print(TS.round(3).to_string()); print(DS.round(2).to_string())


if __name__ == "__main__":
    main()
