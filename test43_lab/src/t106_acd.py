"""TEST106 Fisher ACD (prereg 7363e7c)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t106"); NB = P.NB
NAMES = ["A1_A_UP_HELD", "A2_A_UP_IMMEDIATE", "A3_FAILED_A_DOWN", "A4_C_UP", "ORB_COMPARATOR"]


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def main():
    M = P.markets(); E = {k: {} for k in NAMES}; cache = {}
    for i in P.INSTS:
        m = M[i]; I = m.I; n = m.n
        rg = np.nanmax(I.H, 1) - np.nanmin(I.L, 1); av = 0.10 * pd.Series(rg).rolling(10, min_periods=10).mean().shift(1).values
        orh = np.max(m.h[:, :3], 1); orl = np.min(m.l[:, :3], 1); Au = (orh + av)[:, None]; Ad = (orl - av)[:, None]
        win = (m.bidx >= 3) & (m.bidx <= 60)
        a2 = first((m.c >= Au) & win); E["A2_A_UP_IMMEDIATE"][i] = a2
        a1 = np.zeros((n, NB), bool); a3 = np.zeros((n, NB), bool); a4 = np.zeros((n, NB), bool)
        for s in range(n):
            if not av[s] > 0:
                continue
            t = np.where(a2[s])[0]
            if len(t) and t[0] + 2 <= 60 and np.all(m.c[s, t[0] + 1:t[0] + 3] >= Au[s, 0]):
                a1[s, t[0] + 2] = True
            dn = np.where((m.c[s] <= Ad[s, 0]) & win[s])[0]
            if len(dn):
                d0 = dn[0]
                for b in range(d0 + 1, min(d0 + 7, 61)):
                    if m.c[s, b] > orl[s]:
                        a3[s, b] = True; break
                up = np.where((m.c[s, d0 + 1:61] >= Au[s, 0]))[0]
                if len(up):
                    a4[s, d0 + 1 + up[0]] = True
        E["A1_A_UP_HELD"][i] = a1; E["A3_FAILED_A_DOWN"][i] = a3; E["A4_C_UP"][i] = a4; E["ORB_COMPARATOR"][i] = first((m.c > orh[:, None]) & win)
        wid = np.repeat(((orh - orl) / m.a)[:, None], NB, 1)
        for side, lv in (("H", orh), ("L", orl)):
            pop = (m.c > lv[:, None]) & m.valid
            cache[(side, i)] = dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - lv[:, None]) / m.a[:, None], 5), P.causal_bins(m, pop, wid, 3)])

    def nullf(m, inst, ev, key):
        c = cache[("L" if CUR[0] == "A3_FAILED_A_DOWN" else "H", inst)]; return P.cell_null(m, ev, c["pop"], key, c["b"])
    global CUR
    allD, pooled = [], {}
    for nm in NAMES:
        CUR = [nm]; rows = P.evaluate(nm, E[nm], nullf, meta={"family": "ACD"}); allD += rows; pooled[nm] = rows[-1]
        print(nm, rows[-1]["n_events"], {k: round(rows[-1][f"{k}_xF"], 4) for k in P.HZ}, flush=True)
    adj = {"A1_A_UP_HELD": ["A2_A_UP_IMMEDIATE"], "A2_A_UP_IMMEDIATE": ["A1_A_UP_HELD"], "A3_FAILED_A_DOWN": ["A4_C_UP"], "A4_C_UP": ["A3_FAILED_A_DOWN"], "ORB_COMPARATOR": []}
    fin = []
    for nm, r in pooled.items():
        for key in ("h12", "h24", "h1615"):
            x = r[f"{key}_xF"]; aok = any(np.sign(pooled[o][f"{key}_xF"]) == np.sign(x) and abs(pooled[o][f"{key}_xF"]) >= 0.5 * abs(x) for o in adj[nm])
            fin.append({"variant": nm, "horizon": key, "n": r[f"{key}_n"], "mean": r[f"{key}_mean"], "cost_atr": r["cost_atr"], "xF": x, "xF_lo": r[f"{key}_xF_lo"],
                        "xF_hi": r[f"{key}_xF_hi"], "years_pos": r[f"{key}_years_pos"], "inst_pos": r[f"{key}_inst_pos"], "xF_2021": r[f"{key}_xF_2021"],
                        "x2022": r[f"{key}_x2022"], "xA": r[f"{key}_xA"], "xC": r[f"{key}_xC"], "adjacent_ok": aok, "fallback": r[f"{key}_fallback"],
                        "class": P.classify(r, key, adjacent_ok=aok)})
    F = pd.DataFrame(fin); os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(allD).to_csv(os.path.join(OUT, "TEST106_EVENTS.csv"), index=False); F.to_csv(os.path.join(OUT, "TEST106_CLASSIFICATION.csv"), index=False)
    # paired ACD vs ORB (sessions where both fire), raw pooled means
    cmp = []
    for nm in NAMES[:4]:
        for key in P.HZ:
            a, o = [], []
            for i in P.INSTS:
                m = M[i]; ea = E[nm][i] & m.valid & (m.bidx <= 67); eo = E["ORB_COMPARATOR"][i] & m.valid & (m.bidx <= 67); both = ea.any(1) & eo.any(1)
                a.append(np.nansum(np.where(ea[both], m.R[key][both], 0), 1)); o.append(np.nansum(np.where(eo[both], m.R[key][both], 0), 1))
            a = np.concatenate(a); o = np.concatenate(o); cmp.append({"acd": nm, "horizon": key, "n_sessions": len(a), "acd_mean": a.mean(), "orb_mean": o.mean(), "acd_minus_orb": (a - o).mean()})
    pd.DataFrame(cmp).to_csv(os.path.join(OUT, "TEST106_ACD_VS_ORB.csv"), index=False)
    n = P.ledger(allD, "TEST106", "ACD", "PHASE1")
    pd.set_option("display.width", 250); print(F.round(4).to_string()); print(pd.DataFrame(cmp).round(4).to_string())
    json.dump({"ledger_rows": n, "definitions_new": 5, "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T106_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
