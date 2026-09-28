"""TEST97 Phase 3/4 (prereg 985955df): FT2 = 12-bar breakout STRONG bar followed by a second STRONG bar -> next-open long.
Strategy economics per instrument and as a 4-index virtual sleeve, stress, plateau, folds, 2022 survival, portfolio gate vs MAIN, and position
management (single / blind DCA / fresh-signal recovery / winner pyramid) on identical initial events."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import ap_common as AP  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t96_common as W  # noqa: E402
import t97_engine as E  # noqa: E402
import t97_wave1 as W1  # noqa: E402

M = E.markets(); INSTS = E.INSTS


def ft2(m, bp=0.6, cp=0.8, ra=1.25, N=12):
    s_ = lambda: m.bull & (m.body_pct >= bp) & (m.cpos >= cp) & (m.rng_atr5 >= ra)
    st = s_(); return W1.shift(st & (m.c > m.prevhi[N]), 1) & st & m.valid


def trades(m, ev, exit_kind):
    s, b = np.where(ev); j = 5 * (b + 1)
    jo = np.minimum(j + 60, B.J15) if exit_kind == "X60" else np.full(len(j), B.J15)
    ok = j < jo
    return pd.DataFrame({"s": s[ok], "j": j[ok], "s_out": s[ok], "j_out": jo[ok]})


def pm_sim(m, ev, mode, maxu, fresh):
    """position management on identical initial events; RTH flat 16:15; adds on completed 5m bar -> next open."""
    I = m.I; rows = []; units = []
    for s, b in zip(*np.where(ev)):
        j0 = 5 * (b + 1)
        if j0 >= B.J15:
            continue
        ent = [(j0, I.FP[s, j0])]; a = m.a[s]
        for bb in range(b + 1, 80):
            jn = 5 * (bb + 1)
            if jn >= B.J15 or len(ent) >= maxu:
                break
            avg = np.mean([p for _, p in ent]); px = m.c[s, bb]
            add = False
            if mode == "B_BLIND_DCA":
                add = px <= avg - 0.5 * a * len(ent)
            elif mode == "C_FRESH_RECOVERY":
                add = px < avg and fresh[s, bb]
            elif mode == "D_WINNER_PYRAMID":
                add = px > avg and fresh[s, bb]
            if add:
                ent.append((jn, I.FP[s, jn]))
        xp = I.FP[s, B.J15]; lows = I.L[s, j0:B.J15]
        cum_q = np.zeros(B.J15 - j0); cum_c = np.zeros(B.J15 - j0)
        for (jj, p) in ent:
            cum_q[jj - j0:] += 1; cum_c[jj - j0:] += p
        mae = float(np.nanmax(np.where(cum_q > 0, cum_c - cum_q * lows, 0)) * I.pv)
        for u, (jj, p) in enumerate(ent):
            rows.append({"s": s, "unit": u + 1, "net": (xp - p) * I.pv - 2 * I.cs})
        avg_fin = np.mean([p for _, p in ent]); rec = bool(np.nanmax(I.H[s, ent[-1][0]:B.J15 + 1]) >= avg_fin) if len(ent) > 1 else np.nan
        units.append({"s": s, "units": len(ent), "basket_mae_usd": mae, "basket_net": sum(r["net"] for r in rows[-len(ent):]), "recovered_to_avg": rec})
    return pd.DataFrame(rows), pd.DataFrame(units)


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]; main_d = ctx["main"]; res = []; daily = {}
    for inst in INSTS:
        m = M[inst]; I = Is[inst]; bk = AP.buckets(I); ev = ft2(m)
        for xk in ("X60", "X1615"):
            TR = trades(m, ev, xk)
            pls = [trades(m, ft2(m, **kw), xk) for kw in ({"bp": .5}, {"bp": .7}, {"cp": .7}, {"cp": .9}, {"ra": 1.0}, {"ra": 1.5}, {"N": 8}, {"N": 20})]
            rng = np.random.default_rng(7); miss = TR[rng.random(len(TR)) >= 0.2]
            o, D, d = W.run_module(I, f"FT2_{xk}_{inst}", TR, bk, main_d, occ=None, plateau_TRs=pls,
                                   extra={"missed20_day": float(W.daily(I, W.simulate(I, miss))[I.full].mean()),
                                          "y2022_net": float(d_[np.asarray(I.sess.year == 2022)].sum()) if (d_ := W.daily(I, W.simulate(I, TR))) is not None else np.nan})
            y22 = np.asarray(I.sess.year == 2022); c = W.controls(I, D[np.asarray(I.sess[D.s.values].year == 2022)], bk) if len(D) else {"A": np.nan}
            o["y2022_matched_A_day"] = c["A"] * I.full.sum() / max(y22.sum(), 1)
            res.append(o); daily[o["module"]] = d
            print(o["module"], o["trades"], round(o["avg_day"], 2), round(o["usd_per_trade"], 1), o["plateau"], o["STANDALONE_PASS"], flush=True)
    R = pd.DataFrame(res)
    # 4-index virtual sleeve (sum) per exit
    full = Is["ES"].full; s21 = np.asarray(Is["ES"].sess >= K.S21); port = []
    for xk in ("X60", "X1615"):
        dsum = sum(daily[f"FT2_{xk}_{i}"] for i in INSTS); rm, rc = B.risk(main_d[full]), B.risk((main_d + dsum)[full]); am = full & (dsum != 0)
        port.append({"sleeve": f"FT2_{xk}_4INDEX", "avg_day": float(dsum[full].mean()), "avg_day_2021": float(dsum[s21].mean()), "max_dd": B.risk(dsum[full])["max_dd"],
                     "corr_to_main": float(np.corrcoef(dsum[full], main_d[full])[0, 1]), "loss_jaccard": float(((dsum < 0) & (main_d < 0) & am).sum() / max(((dsum < 0) | (main_d < 0))[am].sum(), 1)),
                     "main_plus_avg_day": rc["avg_day"], "main_plus_maxdd": rc["max_dd"], "main_plus_worst": rc["worst_day"], "main_plus_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"],
                     "active_days": int(am.sum()), "PORTFOLIO_PASS": bool(dsum[full].mean() >= 10 and dsum[s21].mean() >= 10 and rc["ret_dd"] >= rm["ret_dd"] and rc["max_dd"] <= 1.1 * rm["max_dd"])})
    PT = pd.DataFrame(port)
    # position management
    pm = []
    for inst in INSTS:
        m = M[inst]; ev = ft2(m); fresh = W1.strong(m) & (m.c > m.prevhi[12])
        for mode in ("A_SINGLE", "B_BLIND_DCA", "C_FRESH_RECOVERY", "D_WINNER_PYRAMID"):
            for mu in ((1,) if mode == "A_SINGLE" else (2, 3, 4)):
                U, BK = pm_sim(m, ev, mode, mu, fresh)
                row = {"instrument": inst, "mode": mode, "max_units": mu, "baskets": len(BK), "total_net": float(U.net.sum()),
                       **{f"unit{u}_ev": float(U[U.unit == u].net.mean()) if (U.unit == u).any() else np.nan for u in (1, 2, 3, 4)},
                       **{f"unit{u}_n": int((U.unit == u).sum()) for u in (1, 2, 3, 4)},
                       "basket_mae_p95": float(BK.basket_mae_usd.quantile(.95)), "basket_mae_p99": float(BK.basket_mae_usd.quantile(.99)), "basket_mae_max": float(BK.basket_mae_usd.max()),
                       "worst_basket": float(BK.basket_net.min()), "recovery_rate_multi": float(BK.recovered_to_avg.dropna().mean()) if BK.recovered_to_avg.notna().any() else np.nan,
                       "depth_dist": str(BK.units.value_counts().sort_index().to_dict())}
                pm.append(row)
    PM = pd.DataFrame(pm)
    R.to_csv(os.path.join(E.OUT, "PHASE3_FT2.csv"), index=False); PT.to_csv(os.path.join(E.OUT, "PHASE3_FT2_PORTFOLIO.csv"), index=False); PM.to_csv(os.path.join(E.OUT, "PHASE4_FT2_PM.csv"), index=False)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "matched_A_day", "momentum_B_day", "folds_pos", "min_fold_n", "remove_top3", "slip4_day", "delay1_day",
            "missed20_day", "plateau", "y2022_net", "y2022_matched_A_day", "corr_to_main", "STANDALONE_PASS", "PORTFOLIO_PASS", "DIVERSIFIER_PASS"]
    E.md("T97_P3_FT2_STRATEGY.md", "TEST97 Phase 3/4 - FT2 (breakout + strong follow-through) strategy, stress, portfolio, position management (prereg 985955df)",
         [R[cols], "## 4-index virtual sleeve vs MAIN", PT, "## Position management (identical initial events, RTH flat)", PM])
    pd.set_option("display.width", 260); print(R[cols].round(3).to_string()); print(PT.round(4).to_string()); print(PM.round(1).to_string())


if __name__ == "__main__":
    main()
