"""TEST95 Track A - Tom Hougaard canonical families (preregistered ba552115): T1 HTF->LTF trend-pattern-execution, T2 59-min pre-market breakout
(T2A target / stop, T2B runner) with generic OR5 control.  Evaluated standalone and vs MAIN_GROWTH_V1.  Research data <= 2026-05-27."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
import t95_common as T  # noqa: E402

OUT = os.path.join(T.CL, "TOM"); os.makedirs(OUT, exist_ok=True)
CAP = {"MNQ": 6, "ES": 8}
HB = [(0, 59), (60, 119), (120, 179), (180, 239), (240, 299), (300, 359), (360, T.J15)]   # RTH 60m bars (last = 15:31-16:15)


# ---------------------------------------------------------------------------------------------------------------- features
def premarket_high(inst, a, b):
    """max high of 1m bars END-stamped in [a, b] (HH:MM) of each session (pre-RTH), indexed to I.sess."""
    d = C45.load1m(inst); mod = (d.dt.dt.hour * 60 + d.dt.dt.minute).values
    ha, hb = [int(x[:2]) * 60 + int(x[3:]) for x in (a, b)]
    m = (mod >= ha) & (mod <= hb)
    return d[m].groupby("session_date").h.max()


def htf_up(I, fr=1):
    """HTF_UP state after each completed 60m bar (chained across sessions) -> per session x minute permission (last completed bar)."""
    hh = np.array([[I.H[s, a:b + 1].max() for a, b in HB] for s in range(I.n)]).ravel()
    ll = np.array([[I.L[s, a:b + 1].min() for a, b in HB] for s in range(I.n)]).ravel()
    cc = np.array([[I.C[s, b] for a, b in HB] for s in range(I.n)]).ravel()
    N = len(hh); up = np.zeros(N, bool); sh, sl = [], []; lastlo_bar = -1
    for g in range(N):
        c = g - fr                                   # candidate confirmed when bar g completes
        if c - fr >= 0:
            if all(hh[c] > hh[c - q] for q in range(1, fr + 1)) and all(hh[c] > hh[c + q] for q in range(1, fr + 1)):
                sh.append(hh[c])
            if all(ll[c] < ll[c - q] for q in range(1, fr + 1)) and all(ll[c] < ll[c + q] for q in range(1, fr + 1)):
                sl.append(ll[c]); lastlo_bar = c
        ok = len(sh) >= 2 and len(sl) >= 2 and sh[-1] > sh[-2] and sl[-1] > sl[-2]
        if ok:
            ok = bool((cc[lastlo_bar + 1:g + 1] >= sl[-1]).all())
        up[g] = ok
    up = up.reshape(I.n, len(HB)); P = np.zeros((I.n, T.NG), bool)
    for s in range(I.n):
        prev = up[s - 1, -1] if s > 0 else False
        for j in range(T.NG):
            k = -1
            for q, (a, b) in enumerate(HB):
                if b <= j:
                    k = q
            P[s, j] = up[s, k] if k >= 0 else prev
    return P


def t1_signals(I, pat, P):
    """5m pattern decisions 09:40-15:30 (decision minute 5b+4) under HTF permission P; stop = min low of signal & prior bar."""
    o5, h5, l5, c5 = I.o5, I.h5, I.l5, I.c5
    psh = np.r_[np.nan, I.H.max(1)[:-1]]
    rows = []
    for b in range(3, 72):
        j = 5 * b + 4
        if j < 9 or j > 359:
            continue
        if pat == "P_ENGULF":
            hit = (c5[:, b] > o5[:, b]) & (c5[:, b - 1] < o5[:, b - 1]) & (o5[:, b] <= c5[:, b - 1]) & (c5[:, b] >= o5[:, b - 1])
        elif pat == "P_RESUME":
            hit = (h5[:, b - 1] < h5[:, b - 2]) & (h5[:, b - 2] < h5[:, b - 3]) & (c5[:, b] > h5[:, b - 1])
        else:
            hit = (c5[:, b] > psh) & (c5[:, b - 1] <= psh)
        hit &= P[:, j] if P is not None else True
        for s in np.where(hit)[0]:
            rows.append((s, j, min(l5[s, b], l5[s, b - 1])))
    E = pd.DataFrame(rows, columns=["s", "j", "stop"]).sort_values(["s", "j"]).reset_index(drop=True)
    return E


# ---------------------------------------------------------------------------------------------------------------- runs
def run_t1(I, E, occ, be_R=1.0, trail=3, delay=0):
    r = T.run_intraday(I.C, I.H, I.L, I.FP, I.FPb, E.s.values.astype(np.int64), E.j.values.astype(np.int64), E.stop.values.astype(float), occ, CAP[I.name], 1,
                       be_R, trail, np.full(len(E), np.inf), 0, T.J15, delay, 2)
    return r


def t2_events(I, pmh, stop_a, tgt_a, be_a, j0=0, j1=59):
    lvl = pmh.reindex(I.sess).values; ok = ~np.isnan(lvl) & I.full
    s = np.where(ok)[0].astype(np.int64); at = I.atr[s]
    return dict(ev_s=s, lvl=lvl[s].astype(float), j0=np.full(len(s), j0, np.int64), j1=np.full(len(s), j1, np.int64), stop_d=stop_a * at, tgt_d=tgt_a * at, be_d=be_a * at)


def run_t2(I, ev, occ, mode, trail=3, delay=0):
    return T.run_stop_entry(I.O, I.H, I.L, I.FP, I.FPb, ev["ev_s"], ev["lvl"], ev["j0"], ev["j1"], ev["stop_d"], ev["tgt_d"], ev["be_d"], occ, CAP[I.name], 1,
                            trail, mode, T.J15, delay)


def evaluate(I, name, runner, plateau_runners, main, bk, extra=None):
    rows = runner(0); D, d = T.ledger(I, rows); _, d4 = T.ledger(I, rows, cs=I.cs4); _, dl = T.ledger(I, runner(1))
    pt = [float(T.ledger(I, pr())[1][I.full].sum()) for pr in plateau_runners]
    o = T.gate(I, name, d, D, main, d4, dl, pt, controls=extra, bk=bk)
    o["exit_mix"] = str(D.why.value_counts().sort_index().to_dict()) if len(D) else "{}"
    return o, D, d


def main():
    Is = B.load(); I0 = Is["MNQ"]
    main_d, t61, bas, occN, occE = T.main_baseline(I0)
    OCC = {"MNQ": occN, "ES": occE}
    res = []; daily = {}
    for inst in ("ES", "MNQ"):
        I = Is[inst]; bk = A.buckets(I); occ = OCC[inst]
        # ---------------- T1
        P1 = htf_up(I, 1); P2 = htf_up(I, 2)
        print(inst, "HTF_UP share", float(P1[I.full, 200].mean()))
        for pat in ("P_ENGULF", "P_RESUME", "P_BREAK"):
            E = t1_signals(I, pat, P1); E2 = t1_signals(I, pat, P2); E0 = t1_signals(I, pat, None)
            nop = T.ledger(I, run_t1(I, E0, occ))[1]
            o, D, d = evaluate(I, f"T1_{pat}_{inst}", lambda dl: run_t1(I, E, occ, delay=dl),
                               [lambda: run_t1(I, E2, occ), lambda: run_t1(I, E, occ, trail=2), lambda: run_t1(I, E, occ, trail=4),
                                lambda: run_t1(I, E, occ, be_R=0.5), lambda: run_t1(I, E, occ, be_R=1.5)], main_d, bk,
                               {"ctl_no_HTF_day": float(nop[I.full].mean())})
            o["htf_increment_day"] = o["avg_day"] - o["ctl_no_HTF_day"]
            res.append(o); daily[o["module"]] = d; D.to_csv(os.path.join(OUT, f"{o['module']}_ledger.csv"), index=False); print(o["module"], round(o["avg_day"], 2), o["STANDALONE_PASS"])
        # ---------------- T2
        inst_raw = "ES" if inst == "ES" else "MNQ"
        pm59, pm30, pm90 = premarket_high(inst_raw, "08:31", "09:29"), premarket_high(inst_raw, "09:01", "09:29"), premarket_high(inst_raw, "08:01", "09:29")
        or5 = pd.Series(I.H[:, :5].max(1), index=I.sess)
        for var, mode in (("T2A", 1), ("T2B", 0)):
            def ev(pm=pm59, st=0.06, tg=0.04, j0=0):
                return t2_events(I, pm, st, tg, 0.04 if mode == 0 else 0.0, j0=j0)
            base = ev()
            if mode == 1:
                pl = [lambda: run_t2(I, ev(pm30), occ, 1), lambda: run_t2(I, ev(pm90), occ, 1), lambda: run_t2(I, ev(st=0.04), occ, 1),
                      lambda: run_t2(I, ev(st=0.08), occ, 1), lambda: run_t2(I, ev(tg=0.03), occ, 1), lambda: run_t2(I, ev(tg=0.06), occ, 1)]
            else:
                pl = [lambda: run_t2(I, ev(pm30), occ, 0), lambda: run_t2(I, ev(pm90), occ, 0), lambda: run_t2(I, ev(st=0.04), occ, 0),
                      lambda: run_t2(I, ev(st=0.08), occ, 0), lambda: run_t2(I, ev(), occ, 0, trail=2), lambda: run_t2(I, ev(), occ, 0, trail=4)]
            orb = T.ledger(I, run_t2(I, t2_events(I, or5, 0.06, 0.04, 0.04 if mode == 0 else 0.0, j0=5), occ, mode))[1]
            o, D, d = evaluate(I, f"{var}_PREMKT59_{inst}", lambda dl: run_t2(I, base, occ, mode, delay=dl), pl, main_d, bk,
                               {"ctl_C_ORB_day": float(orb[I.full].mean()), "excess_vs_ORB_day": float(d[I.full].mean() - orb[I.full].mean()),
                                "trigger_rate": float(len(D) / max(len(base["ev_s"]), 1))})
            res.append(o); daily[o["module"]] = d; D.to_csv(os.path.join(OUT, f"{o['module']}_ledger.csv"), index=False); print(o["module"], round(o["avg_day"], 2), o["STANDALONE_PASS"])
    R = pd.DataFrame(res); R.to_csv(os.path.join(OUT, "TOM_RESULTS.csv"), index=False)
    np.savez_compressed(os.path.join(OUT, "TOM_daily.npz"), **daily)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "matched_A_day", "momentum_B_day", "folds_pos", "remove_top3", "slip4_day", "delay1_day",
            "plateau", "plateau_pass", "corr_to_main", "main_plus_ret_dd", "main_ret_dd", "STANDALONE_PASS", "PORTFOLIO_PASS"]
    ctl = [c for c in R.columns if c.startswith("ctl_") or c.startswith("excess_vs") or c.startswith("htf_inc") or c == "exit_mix"]
    T.md("TEST95_TOM_RESULTS.md", "TEST95 Track A - Tom Hougaard canonical families (prereg ba552115)", [R[cols], R[["module"] + ctl]])
    print(R[cols].to_string())
    json.dump({"any_standalone_pass": bool(R.STANDALONE_PASS.any()), "any_portfolio_pass": bool(R.PORTFOLIO_PASS.any())}, open(os.path.join(OUT, "TOM_STATUS.json"), "w"))


if __name__ == "__main__":
    main()
