"""TEST96 Track A2 Generation 1 (prereg 492152fd): six transition mechanisms derived from Livermore / Hougaard priors, on ES->MES, NQ->MNQ,
YM->MYM, RTY->M2K.  Primary exit 16:15; secondary exits reported.  Family-specific nulls isolate the transition from the static state.
G6 also measures D10 / D11 cross-index confirmation value (confirmed vs unconfirmed leader breaks)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
import t95_common as T  # noqa: E402
import t96_common as W  # noqa: E402

INSTS = ("ES", "MNQ", "YM", "RTY")
B10, B1430, B15 = 5, 59, 65          # 5m bar indices: decision 5b+4 -> 10:00, 14:30, 15:00
J1030, J16 = C45.g("10:30"), B.J16


def pre(I):
    O0 = I.FP[:, 0]; a = I.atr
    absd = np.cumsum(np.abs(np.diff(I.C, axis=1, prepend=I.C[:, :1])), 1)
    r5 = I.h5 - I.l5
    return O0, a, absd, r5


def ev(rows):
    return pd.DataFrame(rows, columns=["s", "j", "s_out", "j_out"]) if rows else pd.DataFrame(columns=["s", "j", "s_out", "j_out"], dtype=int)


def row(s, b):
    return (s, 5 * b + 5, s, T.J15)


# ------------------------------------------------------------------------------------------------------------ G1
def g1(I):
    O0, a, absd, _ = pre(I); rows, ctl = [], []
    for s in np.where(I.full)[0]:
        if not a[s] > 0:
            continue
        hi = -np.inf; bh = -1; trend_at_hi = False; lo_after = np.inf; done_ctl = False
        for b in range(0, B15 + 1):
            if I.h5[s, b] > hi:
                hi = I.h5[s, b]; bh = b; lo_after = np.inf
                trend_at_hi = (I.c5[s, b] - O0[s]) / a[s] >= 0.5 and abs(I.c5[s, b] - O0[s]) / max(absd[s, 5 * b + 4], 1e-9) >= 0.4
                continue
            lo_after = min(lo_after, I.l5[s, b])
            tr = (I.c5[s, b] - O0[s]) / a[s] >= 0.5 and abs(I.c5[s, b] - O0[s]) / max(absd[s, 5 * b + 4], 1e-9) >= 0.4
            if tr and not done_ctl and b >= B10:
                ctl.append(row(s, b)); done_ctl = True
            if b < B10 or not trend_at_hi or hi <= O0[s]:
                continue
            depth = (hi - lo_after) / (hi - O0[s])
            if b - bh >= 4 and 0.25 <= depth <= 0.60 and I.c5[s, b] > I.h5[s, b - 1]:
                rows.append(row(s, b)); break
    return ev(rows), ev(ctl)


# ------------------------------------------------------------------------------------------------------------ G2
def g2(I):
    O0, a, _, _ = pre(I); rows, ctl = [], []
    Hd = np.nanmax(I.H, 1); Ld = np.nanmin(I.L, 1); Cd = I.C[:, T.J15]
    for s in np.where(I.full)[0]:
        p = s - 1
        if p < 0 or not a[p] > 0 or not (Hd[p] > Ld[p]):
            continue
        if not ((Cd[p] - I.FP[p, 0]) / a[p] >= 0.7 and (Cd[p] - Ld[p]) / (Hd[p] - Ld[p]) >= 0.8):
            continue
        ctl.append(row(s, B10))
        orh = np.max(I.h5[s, :6]); low = np.inf; reacted = False
        for b in range(0, B1430 + 1):
            low = min(low, I.l5[s, b])
            if low <= Cd[p] - 0.25 * a[s]:
                reacted = True
            if b >= B10 and reacted and I.c5[s, b] > orh and I.l5[s, b] > low - 1e-9 and np.argmin(I.l5[s, :b + 1]) < b:
                rows.append(row(s, b)); break
    return ev(rows), ev(ctl)


# ------------------------------------------------------------------------------------------------------------ G3
def g3(I):
    O0, a, _, _ = pre(I); rows, ctl = [], []
    PDH = np.r_[np.nan, np.nanmax(I.H, 1)[:-1]]
    for s in np.where(I.full)[0]:
        if not a[s] > 0 or np.isnan(PDH[s]):
            continue
        bk = -1; retest = False; mx = -np.inf
        for b in range(0, B15 + 1):
            if bk < 0:
                if I.c5[s, b] > PDH[s]:
                    bk = b; mx = I.h5[s, b]; ctl.append(row(s, b))
                continue
            if I.c5[s, b] < PDH[s] - 0.1 * a[s]:
                break
            if I.l5[s, b] <= PDH[s] + 0.1 * a[s]:
                retest = True
            if retest and b - bk >= 3 and I.c5[s, b] > mx:
                rows.append(row(s, b)); break
            mx = max(mx, I.h5[s, b])
    return ev(rows), ev(ctl)


# ------------------------------------------------------------------------------------------------------------ G4
def g4(I):
    O0, a, _, _ = pre(I); rows, ctl = [], []
    Hd = np.nanmax(I.H, 1); Ld = np.nanmin(I.L, 1)
    for s in np.where(I.full)[0]:
        if s < 20 or not a[s] > 0:
            continue
        h5d, l5d = np.nanmax(Hd[s - 5:s]), np.nanmin(Ld[s - 5:s]); h20 = np.nanmax(Hd[s - 20:s])
        cong = (h5d - l5d) <= 1.5 * a[s]
        for b in range(0, B15 + 1):
            if I.c5[s, b] > h20:
                ctl.append(row(s, b)); break
        if cong:
            for b in range(0, B15 + 1):
                if I.c5[s, b] > h5d:
                    rows.append(row(s, b)); break
    return ev(rows), ev(ctl)


# ------------------------------------------------------------------------------------------------------------ G5
def g5(I):
    _, _, _, r5 = pre(I); rows, ctl = [], []
    for s in np.where(I.full)[0]:
        b1 = -1
        for b in range(12, B15 + 1):
            med = np.median(r5[s, b - 12:b]); rng = r5[s, b]
            imp = med > 0 and rng >= 1.8 * med and I.c5[s, b] > I.o5[s, b] and (I.c5[s, b] - I.l5[s, b]) >= 0.75 * rng
            if not imp:
                continue
            if b1 < 0:
                b1 = b; ctl.append(row(s, b)); continue
            if b - b1 >= 3 and I.c5[s, b] > I.c5[s, b1] and rng >= r5[s, b1]:
                rows.append(row(s, b)); break
    return ev(rows), ev(ctl)


# ------------------------------------------------------------------------------------------------------------ G6 (+ D10 / D11)
def sec_break(I):
    """first secondary session-high break minute (T68 definition) per session; -1 if none; plus first new-high minute after any minute."""
    out = np.full(I.n, -1)
    for s in np.where(I.full)[0]:
        H = I.H[s]; rh = np.fmax.accumulate(np.nan_to_num(H, nan=-np.inf)); last = 0
        for j in range(1, J16):
            if H[j] > rh[j - 1]:
                if j >= J1030 and j - last >= 60 and j + 1 < J16:
                    out[s] = j; break
                last = j
    return out


def new_high_after(I, s, j0, j1):
    H = I.H[s]; rh = np.fmax.accumulate(np.nan_to_num(H, nan=-np.inf))
    for j in range(j0 + 1, min(j1, J16 - 1) + 1):
        if H[j] > rh[j - 1]:
            return j
    return -1


def g6(Is):
    sb = {k: sec_break(Is[k]) for k in INSTS}; n = Is["ES"].n
    lag = {k: [] for k in INSTS}; lead = {k: [] for k in INSTS}; lead_unc = {k: [] for k in INSTS}; lead_raw = {k: [] for k in INSTS}
    for s in range(n):
        cand = [(sb[k][s], k) for k in INSTS if sb[k][s] >= 0 and Is[k].full[s]]
        if not cand:
            continue
        jL, L = min(cand); lead_raw[L].append((s, jL + 1, s, T.J15))
        conf = {}
        for k in INSTS:
            if k == L:
                continue
            conf[k] = new_high_after(Is[k], s, jL - 1, jL + 30)
        if all(v >= 0 for v in conf.values()):
            jc = max(conf.values()); lg = max(conf, key=conf.get)
            if jc + 1 < J16:
                lag[lg].append((s, jc + 1, s, T.J15)); lead[L].append((s, jc + 1, s, T.J15))
        else:
            lead_unc[L].append((s, jL + 1, s, T.J15))
    return {k: (ev(lag[k]), ev(lead[k]), ev(lead_unc[k]), ev(lead_raw[k])) for k in INSTS}


def horizons(I, TR):
    """secondary exits (per trade $): 30 / 60 / 120 m, 16:00, 16:15, next open."""
    o = {}
    if not len(TR):
        return o
    for nm, fn in (("h30", lambda j: np.minimum(j + 30, T.J15)), ("h60", lambda j: np.minimum(j + 60, T.J15)), ("h120", lambda j: np.minimum(j + 120, T.J15)),
                   ("h1600", lambda j: np.full(len(j), J16)), ("h1615", lambda j: np.full(len(j), T.J15))):
        t = TR.copy(); t["j_out"] = fn(TR.j.values); t = t[t.j_out > t.j]
        o[f"usd_trade_{nm}"] = float(W.simulate(I, t).net.mean())
    t = TR.copy(); t["s_out"] = TR.s + 1; t["j_out"] = 0; t = t[t.s_out < I.n]
    o["usd_trade_nextopen"] = float(W.simulate(I, t).net.mean())
    return o


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]; main_d = ctx["main"]; res = []; daily = {}
    G = {"G1_REACTION_RESUMPTION": g1, "G2_TRENDDAY_NEXTDAY_REACTION": g2, "G3_PDH_ACCEPTED_SUPPORT": g3, "G4_CONGESTION_BREAK": g4, "G5_STRONG_TO_STRONGER": g5}
    for inst in INSTS:
        I = Is[inst]; bk = A.buckets(I); occ = ctx["occ"].get(inst)
        for gname, fn in G.items():
            TR, CT = fn(I)
            cd = W.daily(I, W.simulate(I, CT, occ=occ)); cD = W.simulate(I, CT, occ=occ)
            o, D, d = W.run_module(I, f"{gname}_{inst}", TR, bk, main_d, occ=occ,
                                   extra={"ctl_family_null_day": float(cd[I.full].mean()), "ctl_family_null_usd_trade": float(cD.net.mean()) if len(cD) else np.nan,
                                          **horizons(I, TR)})
            o["usd_trade_minus_null"] = o["usd_per_trade"] - o["ctl_family_null_usd_trade"]
            res.append(o); daily[o["module"]] = d; print(o["module"], o["trades"], round(o["avg_day"], 2), round(o["usd_trade_minus_null"], 1), o["STANDALONE_PASS"], flush=True)
    six = g6(Is)
    for inst in INSTS:
        I = Is[inst]; bk = A.buckets(I); occ = ctx["occ"].get(inst); lagT, leadT, uncT, rawT = six[inst]
        for nm, TR in (("G6_BROAD_CONF_LAGGARD", lagT), ("G6_BROAD_CONF_LEADER", leadT)):
            if not len(TR):
                continue
            nul = W.simulate(I, uncT, occ=occ) if nm.endswith("LEADER") else W.simulate(I, rawT, occ=occ)
            o, D, d = W.run_module(I, f"{nm}_{inst}", TR, bk, main_d, occ=occ, extra={"ctl_family_null_usd_trade": float(nul.net.mean()) if len(nul) else np.nan,
                                                                                    "ctl_family_null_n": len(nul), **horizons(I, TR)})
            o["usd_trade_minus_null"] = o["usd_per_trade"] - o["ctl_family_null_usd_trade"]
            res.append(o); daily[o["module"]] = d; print(o["module"], o["trades"], round(o["avg_day"], 2), round(o["usd_trade_minus_null"], 1), o["STANDALONE_PASS"], flush=True)
        # D10 (causal): leader breaks confirmed within 30 min (entry at confirmation + 1) vs unconfirmed (entry at break + 31, when non-confirmation
        # becomes known) -> incremental confirmation value per trade, each vs its own matched-A control (same entry / exit minute).
        uncT31 = uncT.assign(j=uncT.j + 30); uncT31 = uncT31[uncT31.j < J16]
        Dc = W.simulate(I, leadT, occ=occ); Du = W.simulate(I, uncT31, occ=occ)
        if len(Dc) and len(Du):
            nd = I.full.sum(); cA = W.controls(I, Dc, bk)["A"] * nd / len(Dc); uA = W.controls(I, Du, bk)["A"] * nd / len(Du)
            res.append({"module": f"D10_CONFIRMATION_VALUE_{inst}", "instrument": inst, "trades": len(Dc), "usd_per_trade": float(Dc.net.mean()),
                        "ctl_family_null_usd_trade": float(Du.net.mean()), "usd_trade_minus_null": float(Dc.net.mean() - Du.net.mean()),
                        "matched_excess_per_trade_confirmed": cA, "matched_excess_per_trade_unconfirmed": uA, "unconfirmed_n": len(Du), "STANDALONE_PASS": False})
    R = pd.DataFrame(res); R.to_csv(os.path.join(W.OUT, "GEN1_RESULTS.csv"), index=False); np.savez_compressed(os.path.join(W.OUT, "GEN1_daily.npz"), **daily)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "usd_trade_minus_null", "matched_A_day", "momentum_B_day", "folds_pos", "min_fold_n",
            "remove_top3", "slip4_day", "delay1_day", "corr_to_main", "main_plus_ret_dd", "STANDALONE_PASS", "PORTFOLIO_PASS", "DIVERSIFIER_PASS"]
    hz = ["module"] + [c for c in R.columns if c.startswith("usd_trade_h") or c == "usd_trade_nextopen"]
    d10 = R[R.module.str.startswith("D10")][["module", "trades", "unconfirmed_n", "usd_per_trade", "ctl_family_null_usd_trade", "usd_trade_minus_null",
                                             "matched_excess_per_trade_confirmed", "matched_excess_per_trade_unconfirmed"]]
    R = R[~R.module.str.startswith("D10")]
    W.md("T96_A2_GEN1_D10_CONFIRMATION.md", "TEST96 D10 - causal cross-index confirmation value of leader breaks", [d10]); print(d10.to_string())
    W.md("T96_A2_GEN1_RESULTS.md", "TEST96 Track A2 - Generation 1 thesis mechanisms (prereg 492152fd)", [R[[c for c in cols if c in R]], "## Exit-horizon diagnostics ($/trade)", R[hz]])
    pd.set_option("display.width", 260); print(R[[c for c in cols if c in R]].to_string())


if __name__ == "__main__":
    main()
