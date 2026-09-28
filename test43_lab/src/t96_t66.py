"""TEST96 Track D9: T66 opening-state ML - MECHANISM transfer (not model transfer) to YM / RTY (prereg 492152fd).
Frozen: 14-feature architecture (target index replaces MNQ, ES stays the 'other' index), label = fwd from 09:36 fill to 10:30 >= thr_b (W1 window),
L2 logistic C=1 + standard scaler, chronological outer folds (train < fold start), threshold = 70th pct of train probabilities, filter
ret_since_open > 0, fill 09:36 (j = 5), exit 10:31 open.  Retrained separately per index; no pooling.  The MNQ-capacity filter (T61 exposure < 3)
is an MNQ capacity rule, not part of the signal, and is dropped for MYM / M2K (kept for the MNQ reference row)."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import t45_common as C45  # noqa: E402
import t65_common as K  # noqa: E402
import t95_common as T  # noqa: E402
import t96_common as W  # noqa: E402
import t96_data as X  # noqa: E402

J = 5; J1 = C45.g("10:30"); JX = J1 + 1


def ff(a):
    return pd.DataFrame(a).T.ffill().T.values


def feats(inst, ctx):
    Is = ctx["Is"]; I = Is[inst]; E_ = Is["ES"]; mk = X.mkt(inst)
    C, Ce = ff(I.C), ff(E_.C); Hh, Ll = ff(I.H), ff(I.L); a, b = I.atr, E_.atr
    o0 = np.array([r[~np.isnan(r)][0] if (~np.isnan(r)).any() else np.nan for r in mk.pn.O]); oe = np.array([r[~np.isnan(r)][0] if (~np.isnan(r)).any() else np.nan for r in X.mkt("ES").pn.O])
    cl = C[:, T.J15]; absd = np.nancumsum(np.abs(np.diff(C, axis=1, prepend=C[:, :1])), 1)
    cm = np.nancumsum(np.nan_to_num(mk.pn.C), 1) / np.maximum(1, np.cumsum(~np.isnan(mk.pn.C), 1))
    tsess, tm = K.t61_minutes(); ix = pd.Index(tsess).get_indexer(I.sess)          # frozen feature = T61-only exposure (as TEST65 / TEST66)
    g = lambda q: np.where(ix[:, None] >= 0, q[np.clip(ix, 0, None)], 0.0)
    ratio = (E_.atr * E_.pv) / (Is["MNQ"].atr * Is["MNQ"].pv); u = g(tm["final_target_MNQ"]) + g(tm["final_target_MES"]) * ratio[:, None]
    jm = J - 1; rows = []
    for s in range(I.n):
        if not I.full[s] or np.isnan(a[s]) or np.isnan(o0[s]) or s < 5:
            continue
        c = C[s]; hi, lo = np.nanmax(Hh[s, :jm + 1]), np.nanmin(Ll[s, :jm + 1])
        r = (c[jm] - o0[s]) / a[s]; re = (Ce[s, jm] - oe[s]) / b[s]
        f = [r, re, re - r, (c[jm] - c[max(jm - 5, 0)]) / a[s], (c[jm] - c[max(jm - 15, 0)]) / a[s], abs(c[jm] - o0[s]) / max(absd[s, jm], 1e-9),
             (c[jm] - lo) / (hi - lo) if hi > lo else 0.5, (o0[s] - cl[s - 1]) / a[s], (cl[s - 1] - o0[s - 1]) / a[s], (c[jm] - cl[s - 5]) / a[s],
             mk.volt[s], float(mk.bull[s]), u[s, jm], (c[jm] - cm[s, jm]) / a[s]]
        fp = I.FP[s, J] if not np.isnan(I.FP[s, J]) else c[J - 1]
        L_ = J1 + 1; thr = 0.5 * np.sqrt(L_ / 390); thr_b = thr * np.sqrt((J1 - J + 1) / L_)
        rows.append([s, I.sess[s], *f, (c[J1] - fp) / a[s] >= thr_b])
    cols = ["s", "date"] + [f"f{i}" for i in range(14)] + ["y"]
    return pd.DataFrame(rows, columns=cols).dropna().reset_index(drop=True)


def signals(Wd, cap_filter):
    F = [f"f{i}" for i in range(14)]; rows = []
    for nm, a, b in C45.OUTER[:5]:
        tr = (Wd.date < pd.Timestamp(a)).values; te = ((Wd.date >= pd.Timestamp(a)) & (Wd.date <= pd.Timestamp(b))).values
        if tr.sum() < 100 or te.sum() == 0:
            continue
        sc = StandardScaler().fit(Wd.loc[tr, F]); m = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(Wd.loc[tr, F]), Wd.y[tr].astype(int))
        thr = np.quantile(m.predict_proba(sc.transform(Wd.loc[tr, F]))[:, 1], 0.7); p = m.predict_proba(sc.transform(Wd.loc[te, F]))[:, 1]
        for i, pp in zip(np.where(te)[0], p):
            if pp >= thr and Wd.f0[i] > 0 and (not cap_filter or Wd.f12[i] < 3):
                rows.append((int(Wd.s[i]), J, int(Wd.s[i]), JX))
    return pd.DataFrame(rows, columns=["s", "j", "s_out", "j_out"])


def main():
    import t65_run as R
    global ELIG
    Wt = pd.read_parquet(os.path.join(C45.ROOT, "out", "test65", "T65_window_labels.parquet"))
    ELIG = set(Wt[Wt.window == "W1_0930_1030"].dropna(subset=R.FEATS + ["fwd_strongN"]).date)
    ctx = W.main_ctx(); res = []; daily = {}
    for inst in ("YM", "RTY", "MNQ"):
        I = ctx["Is"][inst]; Wd = feats(inst, ctx)
        Wd = Wd[Wd.date.isin(ELIG)].reset_index(drop=True)          # frozen TEST65 W1 session-eligibility set (validation procedure)
        TR = signals(Wd, inst == "MNQ")
        o, D, d = W.run_module(I, f"T66_ML_{inst}" + (" [REFERENCE]" if inst == "MNQ" else ""), TR, A.buckets(I), ctx["main"], occ=ctx["occ"].get(inst),
                               extra={"label_base_rate": float(Wd.y.mean()), "events": len(Wd)})
        res.append(o); daily[o["module"].split(" ")[0]] = d; print(o["module"], o["trades"], round(o["avg_day"], 2), o["STANDALONE_PASS"])
    R = pd.DataFrame(res); R.to_csv(os.path.join(W.OUT, "PORT_T66_ML.csv"), index=False)
    np.savez_compressed(os.path.join(W.OUT, "PORT_T66_daily.npz"), **daily)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "matched_A_day", "momentum_B_day", "folds_pos", "min_fold_n", "remove_top3", "slip4_day", "delay1_day",
            "corr_to_main", "STANDALONE_PASS", "PORTFOLIO_PASS", "DIVERSIFIER_PASS", "label_base_rate"]
    note = ("FRAGILITY FINDING (MNQ reference): adding the 8 sessions that the frozen TEST65 eligibility rule excludes (1729 vs 1721 training rows) "
            "changes 81 of 231 signals and turns the MNQ reference from +1.96 to -0.37 $/day.  The frozen T66 member of FIXED_CLUE_BASKET_V1 is therefore "
            "threshold-fragile; it is NOT modified (frozen), but this is recorded as a forward-shadow caveat.")
    W.md("T96_D9_T66_ML_TRANSFER.md", "TEST96 D9 - T66 opening-state ML mechanism transfer", [R[cols], note]); print(R[cols].to_string())


if __name__ == "__main__":
    main()
