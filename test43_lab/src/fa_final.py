"""Final selection diagnostics for FINAL_INDEX_CLOSURE_AUDIT_V1 (prereg 4edf957)."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import da_ph9 as P9  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as RP  # noqa: E402
from fa_audit12 import setup  # noqa: E402
from fa_audit4 import allocate  # noqa: E402
from rp_p6 import control_tables  # noqa: E402
from rp_p9 import module_orders  # noqa: E402

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, "out", "final_index_closure_audit_v1")
DA = os.path.join(LAB, "out", "index_discretionary_alpha_continuous_v1")


def base_series(w):
    ser = {}; E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet"))
    for f in glob.glob(os.path.join(RP.OUT, "ml", "TRADES_*.parquet")):
        X = pd.read_parquet(f); ser["REC_" + os.path.basename(f)[7:-8]] = EC.daily(X.date.values, X.usd.values)[w]
    for cnd, g in E[E.usd_h1615.notna() & (E.year >= 2021)].groupby("candidate"):
        ser[f"REC_TAKEALL_{cnd}"] = EC.daily(g.date.values, g.usd_h1615.values)[w]
    for f in glob.glob(os.path.join(RP.OUT, "ga", "GA_TRADES_*.parquet")):
        X = pd.read_parquet(f); ser["REC_" + os.path.basename(f)[:-8]] = EC.daily(X.date.values, X.usd.values)[w]
    for f in glob.glob(os.path.join(RP.OUT, "p8", "MGMT_*.parquet")):
        X = pd.read_parquet(f); nm = os.path.basename(f)[5:-8]
        for arm in ("B_BLIND_DCA", "C_FRESH_RECOVERY", "D_WINNER_PYRAMID"):
            ser[f"REC_MGMT_{nm}_{arm}"] = EC.daily(X.date.values, (X.unit1 + X[f"{arm}_add"].fillna(0)).values)[w]
    zz = np.load(os.path.join(RP.OUT, "p9", "P9_DAILY.npz"))
    for k in zz.files:
        if k != "MAIN_ONLY":
            ser[f"REC_P9_{k}"] = zz[k][w]
    X4 = pd.read_parquet(os.path.join(DA, "ph4", "PH4_EXIT_DATASET.parquet")); X4 = X4[X4.year >= 2021]
    for dn, g in X4.groupby("def"):
        for ex in ("X60", "X120", "X1615", "XRES", "XSTRUCT"):
            gg = g[g[f"usd_{ex}"].notna()]; ser[f"PH4_{dn}_{ex}"] = EC.daily(gg.date.values, gg[f"usd_{ex}"].values)[w]
    return ser


def main():
    c = EC.ctx(); w = c["win"]; M = P.markets(); ser = base_series(w)
    # audit 1 / 2 signal adds
    T, ig = setup(); C = MG.checkpoints(T, min_left=30)
    for mode in ("winner", "recovery"):
        rows = []
        for t, r in enumerate(T.itertuples(index=False)):
            evb = [b for b in ig.get((r.inst, int(r.s)), []) if b > r.b and 5 * b + 5 < r.j_out and 5 * b + 5 > r.j_in]
            if evb:
                cc = M[r.inst].c[int(r.s), evb[0]]
                if (mode == "winner" and cc > r.px_in) or (mode == "recovery" and cc < r.px_in):
                    rows.append((t, evb[0]))
        S = C[[(t, k) in set(rows) for t, k in zip(C.trade, C.k)]]; ser[f"AUD_{mode}_signal_add"] = EC.daily(S.date.values, S.add_usd.values)[w]
    # NR1 / NR3 raw
    for L in (5, 20):
        dd = np.zeros(len(c["sess"]))
        for i in P.INSTS:
            m = M[i]; I = m.I; js = 30 + 30 * np.arange(12); r = (I.FP[:, js + 30] - I.FP[:, js]) / m.a[:, None]; ok = m.full & (m.a > 0)
            sig = pd.DataFrame(np.where(ok[:, None], r, np.nan)).rolling(L, min_periods=L).mean().shift(1).values > 0
            usd = np.where(sig & ok[:, None] & ~np.isnan(r), r * m.a[:, None] * I.pv - 2 * I.cs, 0).sum(1)
            dts = np.asarray(I.sess.values, "datetime64[D]").astype(np.int64); dd += EC.daily(dts, usd)
        ser[f"AUD_NR1_L{L}"] = dd[w]
    dd = np.zeros(len(c["sess"]))
    for i in P.INSTS:
        m = M[i]; I = m.I; d64 = pd.DatetimeIndex(I.sess).values.astype("datetime64[D]"); nxt = np.r_[d64[1:], d64[-1] + 1]; pre = np.busday_count(d64, nxt) > 1; pre[-1] = False
        r = (I.FP[:, 404] - I.FP[:, 0]) / m.a; ok = m.full & (m.a > 0) & ~np.isnan(r) & pre; dd += EC.daily(d64.astype(np.int64)[ok], (r * m.a * I.pv - 2 * I.cs)[ok])
    ser["AUD_NR3"] = dd[w]
    # audit 4 variants
    Tctl = control_tables(); base = module_orders("C2_P2_FAILED_FIRST", False, Tctl); a1, _ = P9.add_orders()
    front = [dict(o, key=o["key"] + "F", parent=o["key"]) for o in base]; b2 = [dict(o, lots=2) for o in base]
    for nm, ords in {"A4_A": base, "A4_B1": base + front, "A4_B2": b2, "A4_C": base + a1}.items():
        ser[nm] = allocate(ords, True)[0][w]
    z = np.load(os.path.join(OUT, "AUDIT5_PORTFOLIO_INCREMENTS.npz"))
    for k in z.files:
        ser[f"A5_{k}"] = z[k]
    names = sorted(ser); Mx = np.vstack([ser[k] for k in names] + [np.load(os.path.join(DA, "ph6", "GENOME_WINDOW_DAILY.npy")).astype(float)]); Mx = Mx[Mx.std(1) > 0]
    Ntot = Mx.shape[0] + 2592 + 33; x = ser["A4_C"]
    srs = Mx.mean(1) / Mx.std(1); V = srs.var(ddof=1); g_ = 0.5772156649; sr = x.mean() / x.std()
    sr0 = np.sqrt(V) * ((1 - g_) * norm.ppf(1 - 1 / Ntot) + g_ * norm.ppf(1 - 1 / (Ntot * np.e)))
    dsr = float(norm.cdf((sr - sr0) * np.sqrt(len(x) - 1) / np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2)))
    pb = P9.pbo_blocks(Mx); rcp = P9.rc(Mx)
    res = {"selected": "MAIN + C2 + WINNER_ADD1 (increment series A4_C)", "series_in_matrix": int(Mx.shape[0]), "N_trials": int(Ntot), "daily_sharpe": float(sr), "sr0": float(sr0),
           "DSR": dsr, "PBO": pb, "reality_check_p": rcp,
           "LIMITATION": "2,592 reclamation GA genomes and 33 PH5 ML policies have no stored return series (counted in N only); nested per-fold selection paths are represented by their stitched outcomes only; older programs (MASTER, TEST45-98) are not in the matrix."}
    json.dump(res, open(os.path.join(OUT, "FINAL_SELECTION_DIAGNOSTICS.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
