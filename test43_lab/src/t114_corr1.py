"""TEST114 academic intraday momentum (TEST114_AUDIT_CORRECTION_1, prereg 132379e; exact 16:00 close)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "..", "index_ml_ga_reclamation_v1", "t114_corr1"); os.makedirs(OUT, exist_ok=True)


def main():
    M = P.markets(); recs = []
    for i in P.INSTS:
        m = M[i]; I = m.I; a = m.a
        pc = np.r_[np.nan, I.C[:-1, 389]]; p10 = I.C[:, 29]; p1530 = I.C[:, 359]; o = I.FP[:, 0]
        ent = I.FP[:, 360]; x16 = I.C[:, 389]; x1615 = I.C[:, 404]
        d = pd.DataFrame({"inst": i, "date": np.asarray(I.sess.values, "datetime64[D]").astype(np.int64), "year": I.year, "vt": I.vt,
                          "r1": (p10 - pc) / a, "r12": (p1530 - p10) / a, "ro": (p1530 - o) / a, "R16": (x16 - ent) / a, "R1615": (x1615 - ent) / a,
                          "cost": m.cost, "ok": m.full & (a > 0) & ~np.isnan(pc)})
        recs.append(d[d.ok])
    D = pd.concat(recs, ignore_index=True)
    for k in ("R16", "R1615"):
        D[f"N{k}"] = D.groupby(["inst", "year", "vt"])[k].transform("mean")
    defs = {"G1_R1": (D.r1 > 0, "R16"), "G2_R1_R12": ((D.r1 > 0) & (D.r12 > 0), "R16"), "G1_R1_X1615": (D.r1 > 0, "R1615"), "TB_OPEN_CONTROL": (D.ro > 0, "R16")}
    rows = []
    for nm, (msk, k) in defs.items():
        e = D[msk & D[k].notna()]; x = (e[k] - e[f"N{k}"]).values; lo, hi = P.boot(x, e.date.values)
        by = pd.Series(x).groupby(e.year.values).mean(); ins = pd.Series(x).groupby(e.inst.values).mean()
        r = {"variant": nm, "horizon": k, "n": len(e), "mean": e[k].mean(), "net_mean": (e[k] - e.cost).mean(), "cost_atr": e.cost.mean(), "xN": x.mean(), "ci_lo": lo, "ci_hi": hi,
             "years_pos": int((by > 0).sum()), "inst_pos": int((ins > 0).sum()), "x2021": x[e.year.values >= 2021].mean(), "x2022": by.get(2022, np.nan),
             **{f"x_{j}": v for j, v in ins.items()}}
        ev = lo > 0 and r["years_pos"] >= 5 and r["inst_pos"] >= 3 and r["mean"] > r["cost_atr"]
        r["class"] = "EVENT_CLUE" if ev else ("WEAK_RESEARCH_CLUE_ONLY" if r["xN"] > 0 and r["years_pos"] >= 5 else "REJECT"); rows.append(r)
    R = pd.DataFrame(rows)
    g1, g2 = R.set_index("variant").loc["G1_R1"], R.set_index("variant").loc["G2_R1_R12"]
    for idx in R.index:
        if R.loc[idx, "class"] == "EVENT_CLUE" and R.loc[idx, "variant"] in ("G1_R1", "G2_R1_R12"):
            o = g2 if R.loc[idx, "variant"] == "G1_R1" else g1; x = R.loc[idx, "xN"]
            if np.sign(o.xN) == np.sign(x) and abs(o.xN) >= 0.5 * abs(x) and R.loc[idx, "x2021"] > 0:
                R.loc[idx, "class"] = "STRONG_CLUE"
    tb = D[D.ro > 0]; v = tb.R16.values; g = (tb.r1 > 0).values.astype(float); lo, hi = P.boot_diff(v, g, tb.date.values)
    dup = {"within_TB_true_r1pos_minus_r1neg": float(v[g == 1].mean() - v[g == 0].mean()), "ci_lo": lo, "ci_hi": hi, "n_r1pos": int(g.sum()), "n_r1neg": int((1 - g).sum()),
           "G1_xN": float(g1.xN), "TB_xN": float(R.set_index("variant").loc["TB_OPEN_CONTROL", "xN"])}
    dup["RESEARCH_DUPLICATE"] = bool(lo <= 0 <= hi and dup["G1_xN"] <= dup["TB_xN"])
    R.to_csv(os.path.join(OUT, "TEST114_CLASSIFICATION.csv"), index=False); json.dump(dup, open(os.path.join(OUT, "TEST114_DUPLICATION.json"), "w"), indent=1)
    pd.set_option("display.width", 250); print(R.round(4).to_string()); print(dup)
    json.dump({"ledger_rows": len(R), "definitions_new": 4, "classes": R["class"].tolist()}, open(os.path.join(OUT, "T114_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
