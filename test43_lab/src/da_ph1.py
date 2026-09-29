"""PH1 C2 winner-add specificity audit + final-selection overfit re-audit (prereg 0702ab8)."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import da_state as R  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as RP  # noqa: E402
from rp_p6 import pbo, reality_check  # noqa: E402
from rp_p7 import prep  # noqa: E402

OUT = os.path.join(R.OUT, "ph1"); os.makedirs(OUT, exist_ok=True)
INDEP = ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"]


def main():
    T = prep(pd.read_parquet(os.path.join(RP.OUT, "p6", "ARM_C2_P2_FAILED_FIRST_A_TAKE_ALL.parquet"))).reset_index(drop=True)
    E = pd.read_parquet(os.path.join(RP.OUT, "bank", "CANDIDATE_EVENTS.parquet")); ind = E[E.candidate.isin(INDEP) & (E.year >= 2021)]
    ig = {k: sorted(g.b.values) for k, g in ind.groupby(["inst", "s"])}
    C = MG.checkpoints(T, min_left=30)
    # fresh-signal winner adds (frozen P8 rule: first independent event; winner test at its decision close)
    import mp_engine as P
    M = P.markets(); sig_rows = []
    for t, r in enumerate(T.itertuples(index=False)):
        evb = [b for b in ig.get((r.inst, int(r.s)), []) if b > r.b and 5 * b + 5 < r.j_out and 5 * b + 5 > r.j_in]
        if evb:
            fb = evb[0]; m = M[r.inst]
            if m.c[int(r.s), fb] > r.px_in:
                sig_rows.append((t, fb))
    sig_set = set(sig_rows); indep_bars = {(t, b) for t, r in enumerate(T.itertuples(index=False)) for b in ig.get((r.inst, int(r.s)), [])}
    C["is_indep"] = [(t, k) in indep_bars for t, k in zip(C.trade, C.k)]
    # signal rows may fall outside the >=30min window: build them explicitly with the same state fields
    Cs = MG.checkpoints(T, min_left=0); Cs = Cs[[(t, k) in sig_set for t, k in zip(Cs.trade, Cs.k)]].copy(); Cs["is_sig"] = True; Cs["is_indep"] = True
    C["is_sig"] = False; A = pd.concat([C, Cs], ignore_index=True)
    A["is_indep"] = A.is_indep.astype(bool); A["is_sig"] = A.is_sig.astype(bool); pool = (A.winner & ~A.is_sig & ~A.is_indep).values; sig = A.is_sig.values
    ctl, lev = MG.matched_control(A, sig, pool)
    A["ctl_usd"] = ctl * A.atr * A.pv - 2 * A.cs; A["ctl_usd4"] = ctl * A.atr * A.pv - 2 * A.cs4
    S = A[sig]; diff = (S.add_usd - S.ctl_usd).values; diff4 = (S.add_usd4 - S.ctl_usd4).values
    res = {"n_trades": len(T), "n_checkpoints": int(len(C)), "n_winner_checkpoints": int(C.winner.sum()), "n_signal_adds": int(sig.sum()),
           "match_levels": {int(k): int(v) for k, v in pd.Series(lev[sig]).value_counts().items()}}
    res["C_FRESH_SIGNAL_WINNER_ADD"] = MG.summarize(S.add_usd, S.date, S.year, S.inst, S.add_usd4)
    res["MATCHED_GENERIC_CONTROL"] = MG.summarize(S.ctl_usd, S.date, S.year, S.inst, S.ctl_usd4)
    res["SIGNAL_MINUS_MATCHED"] = MG.summarize(diff, S.date, S.year, S.inst, diff4)
    first = C[C.winner & ~C.is_indep].sort_values(["trade", "k"]).groupby("trade").head(1)
    res["B_GENERIC_WINNER_ADD_FIRST"] = MG.summarize(first.add_usd, first.date, first.year, first.inst, first.add_usd4)
    res["ALL_GENERIC_WINNER_CHECKPOINTS"] = MG.summarize(C[C.winner].add_usd, C[C.winner].date, C[C.winner].year, C[C.winner].inst, C[C.winner].add_usd4)
    d = res["SIGNAL_MINUS_MATCHED"]; b = res["B_GENERIC_WINNER_ADD_FIRST"]; c = res["C_FRESH_SIGNAL_WINNER_ADD"]
    spec = d["mean"] > 0 and (d["ci_lo"] > 0 or (d["folds_pos"] >= 4 and d["inst_pos"] >= 3)) and c["slip4_mean"] > 0
    gen = b["mean"] > 0 and b["slip4_mean"] > 0 and b["folds_pos"] >= 3
    res["C2_WINNER_ADD_SPECIFICITY"] = "SIGNAL_SPECIFIC_WINNER_ADD" if spec else ("GENERIC_WINNER_PRESS" if gen else "NO_ADD_VALUE")
    res["C2_FREEZE"] = {"SIGNAL_SPECIFIC_WINNER_ADD": "C2_SIGNAL_WINNER_ADD", "GENERIC_WINNER_PRESS": "C2_GENERIC_WINNER_PRESS"}.get(res["C2_WINNER_ADD_SPECIFICITY"], "C2_BASE_ONLY")
    for arm, o in (("C_FRESH_SIGNAL_WINNER_ADD", c), ("B_GENERIC_WINNER_ADD_FIRST", b)):
        R.append("MANAGEMENT_LEDGER.csv", {"candidate": "C2", "arm": arm, "n": o["n"], "marginal_ev": round(o["mean"], 3), "matched_excess": round(d["mean"], 3) if arm.startswith("C") else "",
                                           "ci_lo": round(o["ci_lo"], 3), "ci_hi": round(o["ci_hi"], 3), "slip4": round(o["slip4_mean"], 3), "folds_pos": o["folds_pos"], "decision": res["C2_WINNER_ADD_SPECIFICITY"]})
    A.to_parquet(os.path.join(OUT, "C2_CHECKPOINTS.parquet"))
    # ---------- final-selection overfit re-audit over the reclamation chain ----------
    c_ = EC.ctx(); w = c_["win"]; ser = {}
    for f in glob.glob(os.path.join(RP.OUT, "ml", "TRADES_*.parquet")):
        D = pd.read_parquet(f); ser[os.path.basename(f)[7:-8]] = EC.daily(D.date.values, D.usd.values)[w]
    Eb = E[E.usd_h1615.notna() & (E.year >= 2021)]
    for cnd, g in Eb.groupby("candidate"):
        ser[f"TAKEALL_{cnd}"] = EC.daily(g.date.values, g.usd_h1615.values)[w]
    for f in glob.glob(os.path.join(RP.OUT, "ga", "GA_TRADES_*.parquet")):
        D = pd.read_parquet(f); ser[os.path.basename(f)[:-8]] = EC.daily(D.date.values, D.usd.values)[w]
    for f in glob.glob(os.path.join(RP.OUT, "p8", "MGMT_*.parquet")):
        D = pd.read_parquet(f); nm = os.path.basename(f)[5:-8]
        for arm in ("B_BLIND_DCA", "C_FRESH_RECOVERY", "D_WINNER_PYRAMID"):
            ser[f"MGMT_{nm}_{arm}"] = EC.daily(D.date.values, (D.unit1 + D[f"{arm}_add"].fillna(0)).values)[w]
    z = np.load(os.path.join(RP.OUT, "p9", "P9_DAILY.npz")); mainw = c_["main"][w]
    for k in z.files:
        if k != "MAIN_ONLY":
            ser[f"P9_{k}"] = z[k][w]
    names = sorted(ser); Mx = np.vstack([ser[k] for k in names]); sel_name = "P9_C2+MGMTx1"; x = ser[sel_name]
    srs = np.array([s.mean() / s.std() for s in Mx if s.std() > 0]); N = len(names) + 2592; V = srs.var(ddof=1); g = 0.5772156649
    sr = x.mean() / x.std(); sr0 = np.sqrt(V) * ((1 - g) * norm.ppf(1 - 1 / N) + g * norm.ppf(1 - 1 / (N * np.e)))
    dsr = float(norm.cdf((sr - sr0) * np.sqrt(len(x) - 1) / np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2)))
    Mxv = Mx[Mx.std(1) > 0]; pb = pbo(Mxv); rc = reality_check(Mxv)
    res["FINAL_SELECTION_OVERFIT_DIAGNOSTIC"] = {"status": "COMPUTED_WITH_LIMITATION (genome-level series not stored; N includes 2,592 genomes, V from the stored matrix)",
                                                 "matrix_series": len(names), "N_trials": N, "selected": sel_name, "daily_sharpe": float(sr), "sr0": float(sr0), "DSR": dsr, "PBO": pb, "reality_check_p": rc}
    R.append("OVERFIT_DIAGNOSTICS.csv", {"scope": "reclamation chain -> C2+MGMTx1 increment", "trials": N, "dsr": round(dsr, 4), "pbo": round(pb, 4), "reality_check_p": round(rc, 4), "status": "COMPUTED_WITH_LIMITATION"})
    json.dump(res, open(os.path.join(OUT, "PH1_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
