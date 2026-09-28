"""TEST95 Track A - Jesse Livermore canonical families (preregistered ba552115): L1 Market Key state machine (daily RTH bars, R = 2 ATR20, C = R/2),
L2 primary pivot (+ L2B) vs generic 20-session breakout control, L3 continuation pivot, L4 sit-tight state exit vs fixed holds, L5 staged accumulation
(per-unit ledger), intraday [HYP] adaptation on 5m bars.  Evaluated standalone and vs MAIN_GROWTH_V1.  Research data <= 2026-05-27."""
import json
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t95_common as T  # noqa: E402

OUT = os.path.join(T.CL, "LIVERMORE"); os.makedirs(OUT, exist_ok=True)
CAP = {"MNQ": 6, "ES": 8}
UT, NRE, NRA, DT = 0, 1, 2, 3          # secondary columns merged into natural columns [FORMAL]; secondary vs natural only changes recording, not pivots


# ------------------------------------------------------------------------------------------------------------ Market Key
@njit(cache=True)
def market_key(Hb, Lb, Rb):
    """chained bars.  returns per bar (state AFTER the bar): col, trend(1 up / -1 down), pivUT (last UT top when reaction began), pivNRa (last
    natural-rally high, reset at DT), pivDT (last DT bottom), lastlow (latest low pivot: DT bottom or reaction low), ext (current column extreme)."""
    N = Hb.shape[0]; col = np.zeros(N, np.int64); tr = np.zeros(N, np.int64)
    pUT = np.full(N, np.nan); pNR = np.full(N, np.nan); pDT = np.full(N, np.nan); ll = np.full(N, np.nan); ex = np.full(N, np.nan)
    c = UT; t = 1; e = Hb[0]; put = np.nan; pnr = np.nan; pdt = np.nan; lo = np.nan
    for i in range(N):
        R = Rb[i]; C = R / 2.0; h = Hb[i]; l = Lb[i]
        if R == R and h == h:
            if c == UT:
                if h > e:
                    e = h
                if l <= e - R:
                    put = e; c = NRE; e = l
                    if lo == lo and l <= lo - C:
                        c = DT; t = -1; pnr = np.nan
            elif c == DT:
                if l < e:
                    e = l
                if h >= e + R:
                    pdt = e; lo = e; c = NRA; e = h
            elif c == NRE:
                if l < e:
                    e = l
                if (t == 1 and lo == lo and l <= lo - C) or (t == -1 and pdt == pdt and l <= pdt - C):
                    c = DT; t = -1; pnr = np.nan
                elif h >= e + R:
                    lo = e; c = NRA; e = h
                    if (t == 1 and put == put and h >= put + C) or (t == -1 and pnr == pnr and h >= pnr + C):
                        c = UT; t = 1; put = np.nan
            else:  # NRA
                if h > e:
                    e = h
                if (t == 1 and put == put and h >= put + C) or (t == -1 and pnr == pnr and h >= pnr + C):
                    c = UT; t = 1; put = np.nan
                elif l <= e - R:
                    pnr = e; c = NRE; e = l
                    if (t == 1 and lo == lo and l <= lo - C) or (t == -1 and pdt == pdt and l <= pdt - C):
                        c = DT; t = -1; pnr = np.nan
        col[i] = c; tr[i] = t; pUT[i] = put; pNR[i] = pnr; pDT[i] = pdt; ll[i] = lo; ex[i] = e
    return col, tr, pUT, pNR, pDT, ll, ex


def atr20(I):
    Hd, Ld, Cd = I.H.max(1), I.L.min(1), I.C[:, T.J15]
    pc = np.r_[np.nan, Cd[:-1]]; tr = np.nanmax(np.c_[Hd - Ld, np.abs(Hd - pc), np.abs(Ld - pc)], 1)
    return pd.Series(tr).rolling(20, min_periods=15).mean().shift(1).values


def levels(st, Cn, kind):
    """entry level for the NEXT bar from the state after this bar (arrays aligned so that out[i] is active on bar i)."""
    col, tr, pUT, pNR, pDT, ll, ex = [np.r_[np.nan, a[:-1].astype(float)] for a in st]
    inr = (col == NRE) | (col == NRA)
    if kind == "L3":
        lv = np.where((tr == 1) & inr, pUT + Cn, np.nan)
    elif kind == "L2":
        lv = np.where((tr == -1) & inr, pNR + Cn, np.nan)
    elif kind == "L2B":
        lv = np.where((tr == -1) & (col == NRE) & ~np.isnan(pNR) & (ex > pDT - Cn), ex + Cn, np.nan)
    else:
        raise KeyError(kind)
    stop = np.where(kind == "L2B", ex - Cn, ll - Cn) if kind == "L2B" else ll - Cn
    dtf = col == DT
    return lv, stop, dtf


# ------------------------------------------------------------------------------------------------------------ daily simulation
def sim_daily(I, lv, stop0, ratchet, dtf, occ, exit_mode="state", delay=0, staged=0, add_lv=None, cs=None):
    """one campaign at a time.  entry: resting buy stop lv[s] (fill max(open, level) at the first 1m bar with high >= level; delay -> next session open).
    exit_mode 'state': sell stop max(stop0 at entry, ratchet[s]) (fill min(open, stop)), DT state at a close -> exit that 16:15;  'h1600' / 'h1' /
    'h5' / 'h10': time exits (sessions).  staged k: up to k extra units at later add_lv triggers while price > first entry.  Returns ledger, MTM daily."""
    cs = I.cs if cs is None else cs; pv = I.pv; cap = CAP[I.name]; n = I.n
    daily = np.zeros(n); rows = []; pos = []   # pos: list of dict units
    stop = -np.inf; s0 = -1; pend = False
    for s in range(1, n):
        if np.isnan(I.FPb[s, T.J15]):              # session without RTH bars: carry positions, no marks
            continue
        # ------------------------------------------------ holding: manage exits across the session
        if pos:
            if exit_mode == "state":
                stop = max(stop, ratchet[s]) if ratchet[s] == ratchet[s] else stop
            xk = -1; xp = np.nan; why = 0
            hz = {"h1": 1, "h5": 5, "h10": 10}.get(exit_mode)
            for k in range(T.J15):
                u = len(pos)
                if occ[s, k] + u > cap:
                    xk, xp, why = k, I.FPb[s, k], 4; break
                if exit_mode == "state" and I.L[s, k] <= stop:
                    xk, xp, why = k, min(stop, I.FP[s, k]), 1; break
                if staged and exit_mode == "state" and add_lv is not None and len(pos) < 1 + staged and add_lv[s] == add_lv[s] and I.H[s, k] >= add_lv[s] \
                        and not any(p["s"] == s for p in pos) and max(I.O[s, k], add_lv[s]) > pos[0]["px"] and occ[s, k] + u + 1 <= cap:
                    px = max(I.O[s, k], add_lv[s]); pos.append({"s": s, "j": k, "px": px, "unit": len(pos) + 1, "mk": px})
            if xk < 0:
                if exit_mode == "state" and dtf[s + 1] if s + 1 < n else False:
                    xk, xp, why = T.J15, I.FPb[s, T.J15], 5
                elif hz is not None and s - s0 + 1 >= hz:
                    xk, xp, why = T.J15, I.FPb[s, T.J15], 3
                elif exit_mode == "h1600" or s == n - 1:
                    xk, xp, why = B.J16 if exit_mode == "h1600" else T.J15, I.FPb[s, B.J16 if exit_mode == "h1600" else T.J15], 3
            end = xp if xk >= 0 else I.FPb[s, T.J15]
            for p in pos:
                daily[s] += (end - p["mk"]) * pv - (cs if p["s"] == s else 0) - (cs if xk >= 0 else 0); p["mk"] = end
            if xk >= 0:
                for p in pos:
                    rows.append((p["unit"], p["s"], p["j"], s, xk, p["px"], xp, why))
                pos = []; stop = -np.inf
            continue
        # ------------------------------------------------ flat: resting entry
        if lv[s] != lv[s]:
            continue
        hit = np.where(I.H[s] [:T.J15] >= lv[s])[0]
        if not len(hit):
            continue
        k = int(hit[0])
        if delay:                                   # +1 bar (1m) execution delay: next minute open
            if k + 1 >= T.J15:
                continue
            s_e, k = s, k + 1; px = I.FP[s, k]
        else:
            s_e, px = s, max(I.O[s, k], lv[s])
        if occ[s_e, k] + 1 > cap:
            continue
        stop = stop0[s] if exit_mode == "state" else -np.inf
        s0 = s_e; pos = [{"s": s_e, "j": k, "px": px, "unit": 1, "mk": px}]
        # same-session management after the fill (stop / time exits evaluated from the next minute)
        xk = -1; xp = np.nan; why = 0
        for q in range(k + 1, T.J15):
            if occ[s_e, q] + 1 > cap:
                xk, xp, why = q, I.FPb[s_e, q], 4; break
            if exit_mode == "state" and I.L[s_e, q] <= stop:
                xk, xp, why = q, min(stop, I.FP[s_e, q]), 1; break
            if exit_mode == "h1600" and q == B.J16:
                xk, xp, why = q, I.FPb[s_e, q], 3; break
        if xk < 0 and (exit_mode in ("h1", "h1600") or (exit_mode == "state" and s_e + 1 < n and dtf[s_e + 1]) or s_e == n - 1):
            xk, xp, why = T.J15, I.FPb[s_e, T.J15], 3 if exit_mode == "h1" else 5
        end = xp if xk >= 0 else I.FPb[s_e, T.J15]
        daily[s_e] += (end - px) * pv - cs - (cs if xk >= 0 else 0)
        if xk >= 0:
            rows.append((1, s_e, k, s_e, xk, px, xp, why)); pos = []; stop = -np.inf
        else:
            pos[0]["mk"] = end
    D = pd.DataFrame(rows, columns=["unit", "s", "j_in", "s_x", "j_x", "px_in", "px_x", "why"])
    D["net"] = (D.px_x - D.px_in) * pv - 2 * cs
    return D, daily


def matched_multi(I, D):
    """matched long: same year x vol tercile x bull sessions, same entry minute, same holding length (sessions) and exit minute."""
    out = np.full(len(D), np.nan)
    for i, r in enumerate(D.itertuples(index=False)):
        g = I.gpos[r.s]; ss = I.gidx[I.gptr[g]:I.gptr[g + 1]]; h = r.s_x - r.s; ss = ss[ss + h < I.n]
        v = (I.FPb[ss + h, r.j_x] - I.FP[ss, r.j_in]) * I.pv - 2 * I.cs
        v = v[~np.isnan(v)]
        if len(v):
            out[i] = v.mean()
    return out


def daily_gate(I, name, D, d, main, d4, dl, pt, extra, sample=(150, 15)):
    Dg = D.rename(columns={}).copy()
    o = T.gate(I, name, d, Dg, main, d4, dl, pt, controls=extra, sample=sample)
    nd = int(I.full.sum()); c = matched_multi(I, D) if len(D) else np.array([])
    o["matched_A_day"] = float(np.nansum(D.net.values - c) / nd) if len(D) else np.nan; o["momentum_B_day"] = np.nan
    o["g_A"] = bool(o["matched_A_day"] > 0); o["g_B"] = True
    g = {k: v for k, v in o.items() if k.startswith("g_")}; o["STANDALONE_PASS"] = bool(all(g.values()))
    rc = B.risk((main + d)[I.full]); rm = B.risk(main[I.full])
    o["PORTFOLIO_PASS"] = bool(o["STANDALONE_PASS"] and o["avg_day"] >= 10 and o["avg_day_2021"] >= 10 and rc["ret_dd"] >= rm["ret_dd"] and rc["max_dd"] <= 1.10 * rm["max_dd"]
                               and rc["worst_day"] >= -5000)
    o["avg_hold_sessions"] = float((D.s_x - D.s).mean() + 1) if len(D) else np.nan
    return o


# ------------------------------------------------------------------------------------------------------------ intraday [HYP]
@njit(cache=True)
def sim_intraday(O, H, L, FP, FPb, lv5, st5, dt5, OCC, cap, mode, hz_abs, hz_rel, J15_, delay):
    """5m-armed resting buy stops (lv5[s, b] active during bar b), exits: mode 0 state (sell stop max(stop, st5 ratchet), DT known at bar start -> exit
    at bar open), mode 1 time (hz_rel minutes after fill or hz_abs minute), always flat J15.  one position at a time, no re-entry in the exit bar."""
    n = O.shape[0]; out = np.full((n * 20, 6), np.nan); m = 0
    for s in range(n):
        k = 0; lastx_b = -1
        while k < J15_:
            b = k // 5
            lv = lv5[s, b]
            if lv == lv and b > lastx_b and H[s, k] >= lv:
                ji = k + delay
                if ji >= J15_:
                    break
                px = max(O[s, k], lv) if delay == 0 else FP[s, ji]
                if OCC[s, ji] + 1 > cap:
                    k += 1; continue
                stp = st5[s, b]; jx = J15_; xp = FPb[s, J15_]; why = 3
                tx = J15_
                if mode == 1:
                    tx = min(J15_, ji + hz_rel) if hz_rel > 0 else min(J15_, hz_abs)
                for q in range(ji + 1, J15_ + 1):
                    if q == J15_ or q >= tx:
                        jx = q; xp = FPb[s, q]; why = 3; break
                    if OCC[s, q] + 1 > cap:
                        jx = q; xp = FPb[s, q]; why = 4; break
                    if mode == 0:
                        bb = q // 5
                        if st5[s, bb] == st5[s, bb] and st5[s, bb] > stp:
                            stp = st5[s, bb]
                        if q % 5 == 0 and dt5[s, bb]:
                            jx = q; xp = FP[s, q]; why = 5; break
                        if L[s, q] <= stp:
                            jx = q; xp = min(stp, FP[s, q]); why = 1; break
                if m < out.shape[0]:
                    out[m, 0] = s; out[m, 1] = ji; out[m, 2] = jx; out[m, 3] = px; out[m, 4] = xp; out[m, 5] = why; m += 1
                lastx_b = jx // 5; k = jx + 1
                continue
            k += 1
    return out[:m]


def intraday_arrays(I, a20, mult):
    nb = I.h5.shape[1]; Hb = I.h5.ravel(); Lb = I.l5.ravel(); Rb = np.repeat(mult * a20, nb)
    st = market_key(Hb, Lb, Rb)
    lv, stop, dtf = levels(st, Rb / 2.0, "L3")
    return lv.reshape(I.n, nb), stop.reshape(I.n, nb), dtf.reshape(I.n, nb)


# ------------------------------------------------------------------------------------------------------------ main
def main():
    Is = B.load(); I0 = Is["MNQ"]
    main_d, t61, bas, occN, occE = T.main_baseline(I0); OCC = {"MNQ": occN, "ES": occE}
    res = []; daily = {}; units = []; states = []
    for inst in ("ES", "MNQ"):
        I = Is[inst]; occ = OCC[inst]; a20 = atr20(I)
        Hd, Ld = I.H[:, :T.J15 + 1].max(1), I.L[:, :T.J15 + 1].min(1)

        def arrays(mult, kind):
            st = market_key(Hd, Ld, mult * a20); lv, stop0, dtf = levels(st, mult * a20 / 2.0, kind)
            ratchet = np.r_[np.nan, st[5][:-1]] - mult * a20 / 2.0
            return st, lv, stop0, ratchet, dtf
        st, _, _, _, _ = arrays(2.0, "L3")
        cnt = pd.Series(st[0][I.full]).value_counts().sort_index()
        states.append({"instrument": inst, **{["UT", "NRE", "NRA", "DT"][k]: int(v) for k, v in cnt.items()},
                       "col_changes": int((np.diff(st[0][I.full]) != 0).sum())})
        # generic breakout control: prior-20-session high buy stop, same L4 exit
        hi20 = pd.Series(Hd).rolling(20).max().shift(1).values
        for kind in ("L3", "L2", "L2B"):
            st, lv, stop0, rat, dtf = arrays(2.0, kind)

            def run(mode="state", delay=0, mult=2.0, cs=None, lvl=None, staged=0):
                _, lv_, s0_, r_, d_ = arrays(mult, kind)
                add = arrays(mult, "L3")[1] if staged else None
                return sim_daily(I, lv_ if lvl is None else lvl, s0_, r_, d_, occ, mode, delay, staged, add, cs)
            D, d = run(); _, d4 = run(cs=I.cs4); _, dl = run(delay=1)
            pt = [float(run(mult=m)[1][I.full].sum()) for m in (1.5, 2.5)]
            ctl = {f"ctl_{m}_day": float(run(mode=m)[1][I.full].mean()) for m in ("h1600", "h1", "h5", "h10")}
            if kind == "L2":
                ctl["ctl_BREAK20_day"] = float(sim_daily(I, hi20, stop0, rat, dtf, occ)[1][I.full].mean())
            o = daily_gate(I, f"{kind}_MKEY_{inst}", D, d, main_d, d4, dl, pt, ctl)
            o["exit_mix"] = str(D.why.value_counts().sort_index().to_dict())
            res.append(o); daily[o["module"]] = d; D.to_csv(os.path.join(OUT, f"{o['module']}_ledger.csv"), index=False)
            print(o["module"], o["trades"], round(o["avg_day"], 2), round(o["matched_A_day"], 2), o["STANDALONE_PASS"], {k: round(v, 2) for k, v in ctl.items()})
            # L5 staged on this entry family (per-unit ledger; ADD1 marginal EV first)
            DS, dS = run(staged=3)
            for u, g in DS.groupby("unit"):
                units.append({"module": f"L5_{kind}_{inst}", "unit": int(u), "n": len(g), "usd_per_trade": float(g.net.mean()), "total": float(g.net.sum()),
                              "per_day": float(g.net.sum() / I.full.sum())})
        # ---------------- intraday [HYP] Market Key on 5m bars
        for mult in (0.5,):
            lv5, st5, dt5 = intraday_arrays(I, a20, mult)

            def ri(mode=0, hr=0, ha=T.J15, delay=0, lv5=lv5, st5=st5, dt5=dt5):
                return T.ledger(I, sim_intraday(I.O, I.H, I.L, I.FP, I.FPb, np.nan_to_num(lv5, nan=np.nan), np.nan_to_num(st5, nan=np.nan), dt5,
                                                occ, CAP[inst], mode, ha, hr, T.J15, delay))
            D, d = ri(); _, dl = ri(delay=1)
            rows = sim_intraday(I.O, I.H, I.L, I.FP, I.FPb, lv5, st5, dt5, occ, CAP[inst], 0, T.J15, 0, T.J15, 0); _, d4 = T.ledger(I, rows, cs=I.cs4)
            pt = []
            for m2 in (0.35, 0.7):
                a, b_, c_ = intraday_arrays(I, a20, m2); pt.append(float(ri(lv5=a, st5=b_, dt5=c_)[1][I.full].sum()))
            ctl = {"ctl_h60_day": float(ri(1, 60)[1][I.full].mean()), "ctl_h120_day": float(ri(1, 120)[1][I.full].mean()),
                   "ctl_h1600_day": float(ri(1, 0, B.J16)[1][I.full].mean()), "ctl_h1615_day": float(ri(1, 0, T.J15)[1][I.full].mean())}
            import ap_common as A
            o = T.gate(I, f"L3_INTRADAY5M_{inst}", d, D, main_d, d4, dl, pt, controls=ctl, bk=A.buckets(I))
            o["exit_mix"] = str(D.why.value_counts().sort_index().to_dict())
            res.append(o); daily[o["module"]] = d; D.to_csv(os.path.join(OUT, f"{o['module']}_ledger.csv"), index=False)
            print(o["module"], o["trades"], round(o["avg_day"], 2), o["STANDALONE_PASS"], {k: round(v, 2) for k, v in ctl.items()})
    R = pd.DataFrame(res); R.to_csv(os.path.join(OUT, "LIV_RESULTS.csv"), index=False); U = pd.DataFrame(units); U.to_csv(os.path.join(OUT, "L5_UNITS.csv"), index=False)
    S = pd.DataFrame(states); S.to_csv(os.path.join(OUT, "MKEY_STATE_COUNTS.csv"), index=False)
    np.savez_compressed(os.path.join(OUT, "LIV_daily.npz"), **daily)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "matched_A_day", "momentum_B_day", "folds_pos", "min_fold_n", "remove_top3", "slip4_day",
            "delay1_day", "plateau", "plateau_pass", "corr_to_main", "main_plus_ret_dd", "main_ret_dd", "STANDALONE_PASS", "PORTFOLIO_PASS"]
    ctl = [c for c in R.columns if c.startswith("ctl_") or c in ("exit_mix", "avg_hold_sessions")]
    T.md("TEST95_LIVERMORE_RESULTS.md", "TEST95 Track A - Jesse Livermore canonical families (prereg ba552115)", [R[cols], R[["module"] + ctl], "## L5 per-unit ledger", U,
                                                                                                                "## Market Key column counts (daily, R = 2 ATR20)", S])
    print(R[cols].to_string()); print(U.to_string()); print(S)
    json.dump({"any_standalone_pass": bool(R.STANDALONE_PASS.any()), "any_portfolio_pass": bool(R.PORTFOLIO_PASS.any())}, open(os.path.join(OUT, "LIV_STATUS.json"), "w"))


if __name__ == "__main__":
    main()
