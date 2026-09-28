"""TEST96 Track D Stage A: EXACT portability of CURRENT_MAIN mechanisms to YM (MYM) and RTY (M2K) - prereg 492152fd.
T53 M1-M4 (frozen genomes / definitions), T68 secondary session-high breakout, T67 turn-of-month calendar, PG12 profile down-stack.
MNQ rows are REFERENCE only (mechanism already inside MAIN).  No thresholds changed."""
import copy
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
import t65_common as K  # noqa: E402
import t95_common as T  # noqa: E402
import t96_common as W  # noqa: E402
import t96_data as X  # noqa: E402

J1030, J16 = C45.g("10:30"), B.J16


def t53_trades(mk, sess):
    import t53_run as T53
    TR = T53.module_trades(mk, sess, check_inst=False)
    return {m: g.rename(columns={}).reset_index(drop=True) for m, g in TR.groupby("mod")}


def t68_trades(I, secondary=True, from21=True):
    rows = []
    for s in range(I.n):
        if not I.full[s] or (from21 and I.sess[s] < K.S21):
            continue
        H = I.H[s]; rh = np.fmax.accumulate(np.nan_to_num(H, nan=-np.inf)); last = 0
        for j in range(1, J16):
            if H[j] > rh[j - 1]:
                if j >= J1030 and (not secondary or j - last >= 60) and j + 1 < J16:
                    rows.append((s, j + 1, s, T.J15)); break
                last = j
    return pd.DataFrame(rows, columns=["s", "j", "s_out", "j_out"])


def t67_trades(I):
    import t67_run as T67
    tom = T67.tom_signals(I.sess)
    return pd.DataFrame({"s": tom.s, "j": tom.j_in, "s_out": tom.s_out, "j_out": tom.j_out})


def pg12_trades(I, other, price_only=False):
    import t86_run as T86
    J = I
    if price_only:
        J = copy.copy(I); J.name = I.name + "_PO"; J.V = (I.V > 0).astype(float)
    E, _, _ = T86.events(J, other, "PG12_DOWN_STACK", "VP-B")
    return pd.DataFrame({"s": E.s.values, "j": E.j.values + 1, "s_out": E.s.values, "j_out": np.full(len(E), J16)})


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]; main_d = ctx["main"]
    res = []; daily = {}
    for inst in ("YM", "RTY", "MNQ"):
        I = Is[inst]; bk = A.buckets(I); mk = X.mkt(inst); occ = ctx["occ"].get(inst)
        ref = " [REFERENCE: in MAIN]" if inst == "MNQ" else ""
        # ---- T53 M1-M4
        for m, TR in t53_trades(mk, I.sess).items():
            o, D, d = W.run_module(I, f"T53_{m}_{inst}{ref}", TR, bk, main_d, occ=occ)
            res.append(o); daily[o["module"]] = d; D.to_csv(os.path.join(W.OUT, f"PORT_T53_{m}_{inst}.csv"), index=False)
        # ---- T68
        TR = t68_trades(I); TRo = t68_trades(I, secondary=False)
        ord_d = W.daily(I, W.simulate(I, TRo, occ=occ)); all19 = W.daily(I, W.simulate(I, t68_trades(I, from21=False), occ=occ))
        o, D, d = W.run_module(I, f"T68_{inst}{ref}", TR, bk, main_d, occ=occ,
                               extra={"ctl_ordinary_session_high_day": float(ord_d[I.full].mean()), "t68_2019_07_plus_day": float(all19[I.full].mean())})
        o["excess_vs_ordinary_day"] = o["avg_day"] - o["ctl_ordinary_session_high_day"]
        res.append(o); daily[o["module"]] = d
        # ---- T67
        o, D, d = W.run_module(I, f"T67_{inst}{ref}", t67_trades(I), bk, main_d, occ=occ, sample=(60, 8))
        res.append(o); daily[o["module"]] = d
        # ---- PG12
        TR = pg12_trades(I, Is["ES"]); po = W.daily(I, W.simulate(I, pg12_trades(I, Is["ES"], True), occ=occ))
        o, D, d = W.run_module(I, f"PG12_{inst}{ref}", TR, bk, main_d, occ=occ, extra={"ctl_price_only_profile_day": float(po[I.full].mean())})
        res.append(o); daily[o["module"]] = d
        print(inst, "done", flush=True)
    R = pd.DataFrame(res); R.to_csv(os.path.join(W.OUT, "PORT_STAGE_A.csv"), index=False)
    np.savez_compressed(os.path.join(W.OUT, "PORT_STAGE_A_daily.npz"), **{k.split(" ")[0]: v for k, v in daily.items()})
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "matched_A_day", "momentum_B_day", "relvol_C_day", "folds_pos", "min_fold_n",
            "remove_top3", "slip4_day", "delay1_day", "corr_to_main", "loss_jaccard", "bottom5_overlap", "main_plus_ret_dd", "main_ret_dd",
            "STANDALONE_PASS", "PORTFOLIO_PASS", "DIVERSIFIER_PASS"]
    ctl = [c for c in R.columns if c.startswith("ctl_") or c.startswith("excess_vs") or c.startswith("t68_")]
    W.md("T96_D_STAGE_A_PORTABILITY.md", "TEST96 Track D Stage A - exact portability to YM / RTY (prereg 492152fd)", [R[cols], R[["module"] + ctl]])
    pd.set_option("display.width", 250); print(R[cols].to_string())


if __name__ == "__main__":
    main()
