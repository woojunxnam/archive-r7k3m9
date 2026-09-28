"""TEST94A LANE A - PRESS1 on the frozen T61-R1C sponsor campaign (preregistered da885810).  One overlay contract per campaign, only while the
campaign is in profit; residual capacity; controls FRONTLOAD / RANDOM_TIMING / SAME_EXPOSURE (matched); T61 + PRESS1 portfolio gate."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
from t84_run import features  # noqa: E402

PW = os.path.join(B.LAB, "out", "PRESS_BASKET_LAB"); OUT = os.path.join(PW, "LANE_A_PRESS1"); os.makedirs(OUT, exist_ok=True)
TRIG = {"A_NEW_HIGH": 0, "B_SECOND_IMPULSE": 1, "C_SHALLOW_PULLBACK": 2, "D_T61_ADDS": 3, "E_VALUE_PROXY": 4, "F_PURE_PROFIT": 5}
EXITS = {"E1": 1, "E2": 2, "E3": 3, "E4": 4}


@njit(cache=True)
def press(T, C43, T53, C, FP, VW, ATR, POCUP, TOV, CO, FPo, FPbo, OHI, full, trig, theta, exit_mode, delay, cap, uncon, cross, J15_):
    """campaign on leg prices (C, FP), overlay on overlay prices (FPo / FPbo, target TOV, cap).  returns trades (s, j_in, j_x, px_in, px_x, source, s0, j0, win)
    and counters (first_triggers, blocked)."""
    n, NGx = T.shape
    out = np.full((n * 4, 9), np.nan); m = 0; ft = 0; blocked = 0
    active = False; avg = 0.0; units = 0; hi = 0.0; hi_g = 0; minc = 1e18; pb = 1e18; pressed = False; had43 = False; had53 = False
    s0 = 0; j0 = 0; ov = False; ovi = -1; prev = 0; last_s = -10; cid_start = 0
    for s in range(n):
        if not full[s]:
            continue
        if s != last_s + 1 and active:
            active = False
        last_s = s
        for j in range(J15_ + 1):
            g = s * NGx + j; t = T[s, j]; incr_profit = False
            # overlay exits decided by T61 state at this minute (atomic with T61's own fill at the open of j)
            if ov:
                xj = -1
                if exit_mode in (1, 2) and t == 0:
                    xj = j
                if exit_mode == 1 and t < prev:
                    xj = j
                if uncon == 0 and TOV[s, j] + 1 > cap:
                    xj = j
                if xj >= 0:
                    out[ovi, 2] = xj; out[ovi, 4] = FPbo[s, xj]; ov = False
            if t > 0 and not active:
                active = True; avg = FP[s, j]; units = t; hi = C[s, j]; hi_g = g; minc = 1e18; pb = 1e18; pressed = False
                had43 = C43[s, j] > 0; had53 = T53[s, j] > 0; s0 = s; j0 = j; cid_start = m
            elif active and t == 0:
                win = 1.0 if FP[s, j] > avg else 0.0
                for q in range(cid_start, m):
                    out[q, 8] = win
                active = False
            elif active:
                if t > prev:
                    incr_profit = (C[s, j - 1] - avg) >= theta * ATR[s] if j > 0 else False
                    avg = (avg * units + FP[s, j] * (t - units)) / t
                units = t
                had43 = had43 or C43[s, j] > 0; had53 = had53 or T53[s, j] > 0
            prev = t
            if ov:
                if (exit_mode == 3 and C[s, j] < VW[s, j]) or j >= J15_ - 1:
                    xj = min(j + 1, J15_); out[ovi, 2] = xj; out[ovi, 4] = FPbo[s, xj]; ov = False
            if not active:
                continue
            c = C[s, j]; u = c - avg
            newhi = c > hi
            prof = (u > 0) if theta <= 0 else (u >= theta * ATR[s])
            fire = False
            if not pressed and prof and j + 1 + delay < J15_:
                if trig == 0:
                    fire = newhi and c > VW[s, j]
                elif trig == 1:
                    fire = newhi and (g - hi_g) >= 10 and (hi - minc) <= 0.15 * ATR[s]
                elif trig == 2:
                    fire = pb < 1e17 and pb > avg and c >= pb + 0.5 * (hi - pb)
                elif trig == 3:
                    fire = incr_profit
                elif trig == 4:
                    fire = newhi and c > VW[s, j] and POCUP[s, j] == 1
                else:
                    fire = True
                if fire and cross == 1:
                    fire = OHI[s, j] == 1
            if fire:
                pressed = True; ft += 1; ji = j + 1 + delay
                if uncon == 0 and TOV[s, ji] + 1 > cap:
                    blocked += 1
                else:
                    src = 0.0 if not had53 else (1.0 if not had43 else 2.0)
                    out[m, 0] = s; out[m, 1] = ji; out[m, 2] = J15_; out[m, 3] = FPo[s, ji]; out[m, 4] = FPbo[s, J15_]; out[m, 5] = src
                    out[m, 6] = s0; out[m, 7] = j0; out[m, 8] = np.nan; ovi = m; m += 1; ov = True
            if newhi:
                hi = c; hi_g = g; minc = 1e18; pb = 1e18
            else:
                if c < minc:
                    minc = c
                if hi - c >= 0.10 * ATR[s] and c < pb:
                    pb = c
    return out[:m], ft, blocked


def main():
    Is = B.load(); nd = int(Is["MNQ"].full.sum())
    cols = ("final_target_MES", "final_target_MNQ", "clamped_TEST53", "virtual_C43_MNQ", "virtual_C43_MES")
    cp = os.path.join(A.AP, "cache", "t61_minutes_full.npz")
    if not os.path.exists(cp):
        Lg = pd.read_csv(os.path.join(K.T61H, "session_log_T61-R1C.csv.gz"), usecols=["session", *cols], parse_dates=["session"])
        ss = pd.DatetimeIndex(Lg.session.unique()); np.savez_compressed(cp, sess=ss.values, **{c: Lg[c].values.reshape(len(ss), A.NG) for c in cols})
    z = np.load(cp); ts = pd.DatetimeIndex(z["sess"]); tm = {c: z[c] for c in cols}
    sess = Is["MNQ"].sess; ix = pd.Index(ts).get_indexer(sess)
    al = lambda a: np.where(ix[:, None] >= 0, a[np.clip(ix, 0, None)], 0).astype(np.int64)
    TN, TE, T53, C43N, C43E = (al(tm[k]) for k in ("final_target_MNQ", "final_target_MES", "clamped_TEST53", "virtual_C43_MNQ", "virtual_C43_MES"))
    t61 = K.t61_daily()["T61-R1C"].daily_pnl.reindex(sess).fillna(0).values
    pocup = {}
    for inst in ("MNQ", "ES"):
        I = Is[inst]; _, F = features(I, "VP-B"); P2 = F[..., A.FEAT["P2_POC"]]
        up = (P2 - np.concatenate([np.full((I.n, 6), np.nan), P2[:, :-6]], 1)) >= 0.05 * I.atr[:, None]
        pu = np.zeros((I.n, A.NG), np.int64)
        for k in range(A.NG):
            b = (k - 4) // 5
            if b >= 0:
                pu[:, k] = up[:, min(b, A.NB5 - 1)]
        pocup[inst] = pu
    ohi = {i: (Is[i].C >= np.maximum.accumulate(Is[i].H, 1) - 1e-9).astype(np.int64) for i in Is}
    LEGS = {"MNQ": dict(T=TN, C43=C43N, T53=T53, leg="MNQ", ov="MNQ", TOV=TN, cap=6, cross=0),
            "MES": dict(T=TE, C43=C43E, T53=np.zeros_like(TE), leg="ES", ov="ES", TOV=TE, cap=8, cross=0),
            "MES_ON_MNQ_CROSS": dict(T=TN, C43=C43N, T53=T53, leg="MNQ", ov="ES", TOV=TE, cap=8, cross=1)}
    rng = np.random.default_rng(5); rows = []; keep = {}

    def run(L, trig, theta=0.10, ex=2, delay=0, uncon=0, slip4=False):
        I, O = Is[L["leg"]], Is[L["ov"]]
        tr, ft, bl = press(L["T"], L["C43"], L["T53"], I.C, I.FP, I.vwap, I.atr, pocup[L["leg"]], L["TOV"], O.C, O.FP, O.FPb, ohi[L["ov"]], I.full,
                           trig, theta, ex, delay, L["cap"], uncon, L["cross"], A.J15)
        D = pd.DataFrame(tr, columns=["s", "j_in", "j_x", "px_in", "px_x", "src", "s0", "j0", "win"])
        for c in ("s", "j_in", "j_x", "s0", "j0"):
            D[c] = D[c].astype(np.int64)
        D = D[D.j_x > D.j_in].reset_index(drop=True)
        cs = O.cs4 if slip4 else O.cs
        D["net"] = (D.px_x - D.px_in) * O.pv - 2 * cs
        d = np.zeros(O.n); np.add.at(d, D.s.values, D.net.values)
        return D, d, ft, bl, O

    for ln, L in LEGS.items():
        for tn, tv in TRIG.items():
            D, d, ft, bl, O = run(L, tv)
            if not len(D):
                rows.append({"leg": ln, "trigger": tn, "events": 0}); continue
            full = O.full; s = D.s.values; ji = D.j_in.values; jx = D.j_x.values
            # controls
            jf = np.where(D.s0.values == s, D.j0.values, 0); jf = np.minimum(jf, ji)
            fl = (O.FPb[s, jx] - O.FP[s, jf]) * O.pv - 2 * O.cs
            rnd = np.zeros(len(D))
            for i in range(len(D)):
                lo = jf[i]; hi_ = max(lo + 1, jx[i] - 1); jr = rng.integers(lo, hi_, 20)
                rnd[i] = ((O.FPb[s[i], jx[i]] - O.FP[s[i], jr]) * O.pv - 2 * O.cs).mean()
            mt = B.matched(O.FP, O.FPb, O.nxt_open, O.gidx, O.gptr, O.gpos, s, ji, jx, np.zeros(len(D), np.int64), O.pv, O.cs)
            day = lambda v: float(np.nansum(v) / nd)
            r = B.risk(d[full]); act = d[full & (d != 0)]; top = np.sort(act)[::-1]
            fd = [d[np.asarray((O.sess >= a) & (O.sess <= b))].mean() for _, a, b in B.FOLDS]
            fn = [int(((O.sess[s] >= a) & (O.sess[s] <= b)).sum()) for _, a, b in B.FOLDS]
            pl = {}
            for lab, kw in (("theta=0.0", {"theta": 0.0}), ("theta=0.25", {"theta": 0.25}), ("exit=E1", {"ex": 1})):
                pl[lab] = float(run(L, tv, **kw)[1][full].sum())
            extra = {f"theta=0.50": float(run(L, tv, theta=0.50)[1][full].mean()), "E3_day": float(run(L, tv, ex=3)[1][full].mean()),
                     "E4_day": float(run(L, tv, ex=4)[1][full].mean()), "delay1_day": float(run(L, tv, delay=1)[1][full].mean())}
            Du, du, ftu, _, _ = run(L, tv, uncon=1)
            d4 = run(L, tv, slip4=True)[1]
            base = float(d[full].sum())
            comb = t61 + d; rc, rb = B.risk(comb[full]), B.risk(t61[full])
            o = {"leg": ln, "trigger": tn, "events": len(D), "first_triggers": ft, "cap_block_rate": bl / max(ft, 1), "trades_per_day": len(D) / nd,
                 "marginal_avg_day": r["avg_day"], "marginal_ev_trade": float(D.net.mean()), "win_rate": float((D.net > 0).mean()), "folds_pos": int(sum(v > 0 for v in fd)),
                 "min_fold_n": min(fn), "remove_top3": float(act.sum() - top[:3].sum()) if len(act) else 0.0, "slip4_day": float(d4[full].mean()),
                 "frontload_excess_day": day(D.net.values - fl), "random_timing_excess_day": day(D.net.values - rnd), "matched_excess_day": day(D.net.values - mt),
                 "EV_if_campaign_wins": float(D.net[D.win == 1].mean()) if (D.win == 1).any() else np.nan,
                 "EV_if_campaign_loses": float(D.net[D.win == 0].mean()) if (D.win == 0).any() else np.nan,
                 **{f"src_{k}_ev": float(D.net[D.src == v].mean()) if (D.src == v).any() else np.nan for k, v in (("C43", 0), ("TEST53", 1), ("MIXED", 2))},
                 **{f"src_{k}_n": int((D.src == v).sum()) for k, v in (("C43", 0), ("TEST53", 1), ("MIXED", 2))},
                 "plateau": str({k: round(v) for k, v in pl.items()}), "plateau_pass": bool(base > 0 and all(v > 0 and v >= 0.6 * base for v in pl.values())), **extra,
                 "unconstrained_avg_day": float(du[full].mean()), "unconstrained_events": len(Du),
                 "incr_maxdd": r["max_dd"], "incr_worst": r["worst_day"], "corr_to_t61": float(np.corrcoef(d[full], t61[full])[0, 1]) if d[full].std() > 0 else 0.0,
                 "t61_plus_avg_day": rc["avg_day"], "t61_plus_maxdd": rc["max_dd"], "t61_plus_worst": rc["worst_day"], "t61_plus_ret_dd": rc["ret_dd"], "t61_ret_dd": rb["ret_dd"]}
            g = {"g_avg": o["marginal_avg_day"] > 0, "g_trade": o["marginal_ev_trade"] > 0, "g_folds": o["folds_pos"] >= 4, "g_top3": o["remove_top3"] > 0,
                 "g_slip4": o["slip4_day"] > 0, "g_plateau": o["plateau_pass"], "g_frontload": o["frontload_excess_day"] > 0, "g_random": o["random_timing_excess_day"] > 0,
                 "g_matched": o["matched_excess_day"] > 0, "g_sample": o["events"] >= 300 and o["min_fold_n"] >= 40,
                 "g_portfolio": bool(rc["ret_dd"] >= 1.03 * rb["ret_dd"] and o["marginal_avg_day"] >= 3 and rc["max_dd"] <= 1.10 * rb["max_dd"] and rc["worst_day"] >= -5000)}
            o.update(g); o["PRESS1_PASS"] = bool(all(g.values()))
            rows.append(o); keep[f"{ln}_{tn}"] = d
            print(ln, tn, len(D), round(o["marginal_avg_day"], 2), round(o["marginal_ev_trade"], 2), o["folds_pos"], round(o["frontload_excess_day"], 2),
                  round(o["random_timing_excess_day"], 2), round(o["matched_excess_day"], 2), o["PRESS1_PASS"], flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "PRESS1_RESULTS.csv"), index=False); np.savez_compressed(os.path.join(OUT, "PRESS1_daily.npz"), **keep)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 80)
    cols = ["leg", "trigger", "events", "cap_block_rate", "trades_per_day", "marginal_avg_day", "marginal_ev_trade", "folds_pos", "remove_top3", "slip4_day",
            "frontload_excess_day", "random_timing_excess_day", "matched_excess_day", "EV_if_campaign_wins", "EV_if_campaign_loses", "src_C43_ev", "src_TEST53_ev", "src_MIXED_ev",
            "plateau", "unconstrained_avg_day", "t61_plus_ret_dd", "PRESS1_PASS"]
    print(R[cols].round(3).to_string())
    A.md("../PRESS_BASKET_LAB_LANE_A.md", "TEST94A - PRESS1 on the validated T61 campaign", [R[cols].round(3), R.T])


if __name__ == "__main__":
    main()
