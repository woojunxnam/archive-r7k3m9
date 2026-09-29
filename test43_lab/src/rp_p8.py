"""P8 bounded recovery / winner pyramid (prereg 8b12009)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as R  # noqa: E402
from rp_p7 import CAND, prep  # noqa: E402

OUT = os.path.join(R.OUT, "p8"); os.makedirs(OUT, exist_ok=True)
BASES = ["C1_R1_TRAPPED_UNION", "C2_P2_FAILED_FIRST", "C7_L1_SWH60"]
INDEP = {"C1_R1_TRAPPED_UNION": ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"],
         "C2_P2_FAILED_FIRST": ["C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C7_L1_SWH60", "C8_CHOCH_15m"],
         "C7_L1_SWH60": ["C1_R1_TRAPPED_UNION", "C3_P1_H2", "C5_HTF1_30m", "C6_AV_OR30", "C8_CHOCH_15m"]}


def fold_of(y):
    for k, (a, b) in EC.FOLDS.items():
        if a <= y <= b:
            return k


def main():
    M = P.markets(); E = pd.read_parquet(os.path.join(R.OUT, "bank", "CANDIDATE_EVENTS.parquet")); res = []; led = []
    for base in BASES:
        T = prep(pd.read_parquet(os.path.join(R.OUT, "p6", f"ARM_{base}_{CAND[base]}.parquet")))
        ind = E[E.candidate.isin(INDEP[base]) & (E.year >= 2021)].sort_values(["inst", "s", "b"])
        ig = {k: g.b.values for k, g in ind.groupby(["inst", "s"])}
        rows = []
        for r in T.itertuples(index=False):
            m = M[r.inst]; I = m.I; s = r.s; u1 = (r.px_out - r.px_in) * r.pv - 2 * r.cs; u1_4 = (r.px_out - r.px_in) * r.pv - 2 * r.cs4
            lo1 = np.nanmin(I.L[s, r.j_in:r.j_out + 1]); mae1 = (r.px_in - lo1) * r.pv
            o = {"date": r.date, "year": r.year, "inst": r.inst, "unit1": u1, "unit1_4": u1_4, "mae1": mae1}
            # B blind DCA
            bb = [b for b in range(r.b + 1, 80) if 5 * b + 5 <= r.j_out and 5 * b + 4 >= r.j_in and m.c[s, b] <= r.px_in - 0.5 * r.atr]
            # C / D independent events
            evb = [b for b in ig.get((r.inst, s), []) if b > r.b and 5 * b + 5 < r.j_out and 5 * b + 5 > r.j_in]
            for arm, cand_b in (("B_BLIND_DCA", bb[:1]), ("C_FRESH_RECOVERY", [b for b in evb if m.c[s, b] < r.px_in][:1]), ("D_WINNER_PYRAMID", [b for b in evb if m.c[s, b] > r.px_in][:1])):
                if arm != "B_BLIND_DCA" and cand_b:
                    # only the FIRST independent event counts; its state decides C vs D
                    fb = evb[0]; cand_b = [fb] if ((arm == "C_FRESH_RECOVERY" and m.c[s, fb] < r.px_in) or (arm == "D_WINNER_PYRAMID" and m.c[s, fb] > r.px_in)) else []
                if cand_b:
                    ja = 5 * cand_b[0] + 5; pa = I.FP[s, ja]; add = (r.px_out - pa) * r.pv - 2 * r.cs; add4 = (r.px_out - pa) * r.pv - 2 * r.cs4
                    lo = np.nanmin(I.L[s, ja:r.j_out + 1]); bmae = (r.px_in - lo) * r.pv + (pa - lo) * r.pv
                    o[f"{arm}_add"] = add; o[f"{arm}_add4"] = add4; o[f"{arm}_bmae"] = bmae; o[f"{arm}_ja"] = ja; o[f"{arm}_pa"] = pa
                    if arm == "C_FRESH_RECOVERY":          # exit architectures R1 / R2 (evaluated only if the arm qualifies)
                        C1m = I.C[s, ja:r.j_out + 1]; cst = 2 * 2 * r.cs / r.pv; be = (r.px_in + pa) / 2 + cst / 2
                        k1 = np.where(C1m >= be)[0]
                        if len(k1):
                            xp = C1m[k1[0]]; o["R1_basket"] = (xp - r.px_in) * r.pv + (xp - pa) * r.pv - 4 * r.cs
                        else:
                            o["R1_basket"] = u1 + add
                        k2 = np.where(C1m >= r.px_in)[0]
                        o["R2_basket"] = u1 + (((C1m[k2[0]] - pa) * r.pv - 2 * r.cs) if len(k2) else add)
            rows.append(o)
        Dd = pd.DataFrame(rows); Dd.to_parquet(os.path.join(OUT, f"MGMT_{base}.parquet"))
        worst1 = Dd.unit1.min()
        for arm in ("A_SINGLE", "B_BLIND_DCA", "C_FRESH_RECOVERY", "D_WINNER_PYRAMID"):
            if arm == "A_SINGLE":
                o = {"candidate": base, "arm": arm, "n_base": len(Dd), "n_add": 0, "unit1_ev": Dd.unit1.mean(), "add1_marginal_ev": np.nan, "basket_ev": Dd.unit1.mean()}
            else:
                a = Dd[f"{arm}_add"]; ok = a.notna(); ad = a[ok].values
                lo, hi = P.boot(ad, Dd.date.values[ok]) if ok.sum() >= 20 else (np.nan, np.nan)
                folds = pd.Series(ad).groupby([fold_of(y) for y in Dd.year.values[ok]]).sum()
                bask = Dd.unit1.values[ok] + ad
                o = {"candidate": base, "arm": arm, "n_base": len(Dd), "n_add": int(ok.sum()), "unit1_ev": Dd.unit1.mean(), "add1_marginal_ev": float(ad.mean()) if ok.any() else np.nan,
                     "add1_ev_ci_lo": lo, "add1_ev_ci_hi": hi, "add1_slip4_ev": float(Dd[f"{arm}_add4"][ok].mean()) if ok.any() else np.nan,
                     "add_folds_pos": int((folds > 0).sum()), "basket_ev": float((Dd.unit1 + a.fillna(0)).mean()), "worst_basket": float(bask.min()) if ok.any() else np.nan,
                     "worst_unit1": float(worst1), "basket_mae_p95": float(np.nanpercentile(Dd[f"{arm}_bmae"][ok], 95)) if ok.any() else np.nan,
                     "basket_mae_p99": float(np.nanpercentile(Dd[f"{arm}_bmae"][ok], 99)) if ok.any() else np.nan,
                     "add_2022": float(ad[Dd.year.values[ok] == 2022].sum()) if ok.any() else np.nan}
                o["decision"] = ("STOP_RECOVERY (ADD1 EV <= 0)" if not (o["add1_marginal_ev"] > 0) else
                                 ("MANAGEMENT_IMPROVEMENT" if (o["add1_slip4_ev"] > 0 and o["add_folds_pos"] >= 3 and o["worst_basket"] >= 2 * worst1) else "ADD1_POSITIVE_BUT_NOT_ROBUST"))
                if arm == "C_FRESH_RECOVERY" and o["add1_marginal_ev"] > 0 and o["n_add"] >= 100:
                    o["R1_basket_ev_on_adds"] = float(Dd.R1_basket[ok].mean()); o["R2_basket_ev_on_adds"] = float(Dd.R2_basket[ok].mean()); o["base_basket_ev_on_adds"] = float(bask.mean())
            res.append(o); R.append("MANAGEMENT_LEDGER.csv", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in o.items() if k in ("candidate", "arm", "n_base", "n_add", "unit1_ev", "add1_marginal_ev", "basket_ev", "decision")})
            print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in o.items()}, flush=True)
    pd.DataFrame(res).to_csv(os.path.join(OUT, "P8_MANAGEMENT.csv"), index=False)


if __name__ == "__main__":
    main()
