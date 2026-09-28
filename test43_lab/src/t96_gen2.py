"""TEST96 Track A2 Generation 2 (prereg 0ee0c6e5): participation-expansion transitions - Q1 acceleration (G5 clue-follow), Q2 breadth expansion,
Q3 volume participation expansion, Q4 cross-index catch-up (D11).  Primary exit 16:15, predeclared plateau neighbours."""
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
import t96_gen1 as G1  # noqa: E402

INSTS = ("ES", "MNQ", "YM", "RTY")
J1000, J1030, J1430, J1500 = (C45.g(t) for t in ("10:00", "10:30", "14:30", "15:00"))
DEC = [j for j in range(4, T.J15, 5)]


def px(I, j):
    """close at grid j (j < 0 -> session open)."""
    return I.C[:, j] if j >= 0 else I.FP[:, 0]


def rmax(X, w):
    return pd.DataFrame(X.T).rolling(w, min_periods=1).max().T.values


def ev(rows):
    return G1.ev(rows)


# ------------------------------------------------------------------------------------------------------------ Q1
def q1(I, rp=0.10, ratio=2.0):
    a = I.atr; rows, nul = [], []; done = np.zeros(I.n, bool); dn = np.zeros(I.n, bool)
    for jn in range(J1030, J1500 + 1, 30):
        rn = (px(I, jn) - px(I, jn - 30)) / a; rpv = (px(I, jn - 30) - px(I, jn - 60)) / a
        acc = (rpv >= rp) & (rn >= ratio * rpv) & (rn >= 0.20) & I.full & ~done
        st = (rn >= 0.20) & ~((rpv >= rp) & (rn >= ratio * rpv)) & I.full & ~dn
        for s in np.where(acc)[0]:
            rows.append((s, jn + 1, s, T.J15))
        for s in np.where(st)[0]:
            nul.append((s, jn + 1, s, T.J15))
        done |= acc; dn |= st
    return ev(rows), ev(nul)


# ------------------------------------------------------------------------------------------------------------ Q2
def breadth_cond(I):
    hi30 = rmax(I.H, 30); hi5 = rmax(I.H, 5)
    return (I.C > I.FP[:, :1] + 0.1 * I.atr[:, None]) & (hi5 >= hi30)


def q2(Is, lb=30):
    cond = {k: breadth_cond(Is[k]) for k in INSTS}; br = sum(cond[k].astype(int) for k in INSTS)
    out = {k: ([], []) for k in INSTS}; n = Is["ES"].n; full = np.all([Is[k].full for k in INSTS], 0)
    for s in np.where(full)[0]:
        got = gotn = False
        for j in DEC:
            if j < J1000 or j > J1500:
                continue
            if not got and br[s, j] == 4 and br[s, j - lb] <= 1:
                for k in INSTS:
                    out[k][0].append((s, j + 1, s, T.J15))
                got = True
            if not gotn and br[s, j] == 4 and br[s, j - lb] >= 3:
                for k in INSTS:
                    out[k][1].append((s, j + 1, s, T.J15))
                gotn = True
    return {k: (ev(v[0]), ev(v[1])) for k, v in out.items()}


# ------------------------------------------------------------------------------------------------------------ Q3
def q3(I, lo=0.9, hi=1.3):
    rv = A.rel_volume(I); h60 = rmax(I.H, 60); h5 = rmax(I.H, 5); rows, nul = [], []
    for s in np.where(I.full)[0]:
        got = gotn = False
        for j in DEC:
            if j < J1030 or j > J1500:
                continue
            base = h5[s, j] >= h60[s, j] and I.C[s, j] - I.C[s, j - 30] > 0
            if not base:
                continue
            ex = rv[s, j - 30] < lo and rv[s, j] > hi
            if ex and not got:
                rows.append((s, j + 1, s, T.J15)); got = True
            if not ex and not gotn and rv[s, j] == rv[s, j]:
                nul.append((s, j + 1, s, T.J15)); gotn = True
    return ev(rows), ev(nul)


# ------------------------------------------------------------------------------------------------------------ Q4
def q4(L, X, lead=0.4):
    h30 = rmax(X.H, 30); h5 = rmax(X.H, 5); rows, nul = [], []
    for s in np.where(L.full & X.full)[0]:
        if not (L.atr[s] > 0 and X.atr[s] > 0):
            continue
        for j in DEC:
            if j < J1030 or j > J1430:
                continue
            rl = (L.C[s, j] - L.C[s, j - 60]) / L.atr[s]; rx = (X.C[s, j] - X.C[s, j - 60]) / X.atr[s]
            if rl >= lead and rx <= 0.1:
                nul.append((s, j + 1, s, T.J15))
                for j2 in DEC:
                    if j < j2 <= j + 60 and h5[s, j2] >= h30[s, j2] and X.C[s, j2] > X.C[s, j2 - 5]:
                        rows.append((s, j2 + 1, s, T.J15)); break
                break
    return ev(rows), ev(nul)


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]; main_d = ctx["main"]; res = []; daily = {}

    def one(I, name, TR, NUL, pls):
        bk = A.buckets(I); occ = ctx["occ"].get(I.name); nD = W.simulate(I, NUL, occ=occ)
        o, D, d = W.run_module(I, name, TR, bk, main_d, occ=occ, plateau_TRs=pls,
                               extra={"ctl_family_null_usd_trade": float(nD.net.mean()) if len(nD) else np.nan, "ctl_family_null_n": len(nD), **G1.horizons(I, TR)})
        o["usd_trade_minus_null"] = o["usd_per_trade"] - o["ctl_family_null_usd_trade"]
        res.append(o); daily[name] = d; print(name, o["trades"], round(o["avg_day"], 2), round(o["usd_trade_minus_null"], 1), o["STANDALONE_PASS"], flush=True)

    b2 = q2(Is); b2n = {lb: q2(Is, lb) for lb in (20, 40)}
    for inst in INSTS:
        I = Is[inst]
        TR, NUL = q1(I); one(I, f"Q1_ACCELERATION_30M_{inst}", TR, NUL, [q1(I, rp=0.08)[0], q1(I, rp=0.12)[0], q1(I, ratio=1.75)[0], q1(I, ratio=2.25)[0]])
        one(I, f"Q2_BREADTH_EXPANSION_{inst}", b2[inst][0], b2[inst][1], [b2n[20][inst][0], b2n[40][inst][0]])
        TR, NUL = q3(I); one(I, f"Q3_VOLUME_EXPANSION_{inst}", TR, NUL, [q3(I, lo=0.8)[0], q3(I, lo=1.0)[0], q3(I, hi=1.2)[0], q3(I, hi=1.4)[0]])
    for Ln, Xn in (("MNQ", "ES"), ("MNQ", "YM"), ("MNQ", "RTY"), ("YM", "MNQ"), ("RTY", "MNQ")):
        L, X_ = Is[Ln], Is[Xn]; TR, NUL = q4(L, X_)
        one(X_, f"Q4_CATCHUP_{Ln}_LEADS_{Xn}", TR, NUL, [q4(L, X_, 0.3)[0], q4(L, X_, 0.5)[0]])
    R = pd.DataFrame(res); R.to_csv(os.path.join(W.OUT, "GEN2_RESULTS.csv"), index=False); np.savez_compressed(os.path.join(W.OUT, "GEN2_daily.npz"), **daily)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "usd_trade_minus_null", "ctl_family_null_n", "matched_A_day", "momentum_B_day", "folds_pos",
            "min_fold_n", "remove_top3", "slip4_day", "delay1_day", "plateau", "corr_to_main", "main_plus_ret_dd", "STANDALONE_PASS", "PORTFOLIO_PASS", "DIVERSIFIER_PASS"]
    hz = ["module"] + [c for c in R.columns if c.startswith("usd_trade_h") or c == "usd_trade_nextopen"]
    W.md("T96_A2_GEN2_RESULTS.md", "TEST96 Track A2 - Generation 2 participation-expansion transitions (prereg 0ee0c6e5)", [R[cols], "## Exit-horizon diagnostics ($/trade)", R[hz]])
    pd.set_option("display.width", 260); print(R[cols].to_string())


if __name__ == "__main__":
    main()
