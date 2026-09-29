"""TEST101 event-anchored VWAP (prereg 53bc874)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t101")


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


def main():
    M = P.markets(); E = {}; cache = {}
    for i in P.INSTS:
        m = M[i]; I = m.I; n = m.n; NB = P.NB
        tp = (I.H + I.L + I.C) / 3.0; V = I.V
        CS = np.concatenate([np.zeros((n, 1)), np.cumsum(tp * V, 1)], 1); CV = np.concatenate([np.zeros((n, 1)), np.cumsum(V, 1)], 1)
        CT = np.concatenate([np.zeros((n, 1)), np.cumsum(tp, 1)], 1)
        brk = m.c > m.prevhi[12]; pb = np.concatenate([np.zeros((n, 1), bool), brk[:, :-1]], 1)
        anchors = {"BRK12": first(brk & ~pb & (m.bidx >= 1) & (m.bidx <= 60)), "PDH": first((m.c > m.pdh[:, None]) & (m.bidx <= 60)),
                   "OR30": first((m.c > np.max(m.h[:, :6], 1)[:, None]) & (m.bidx >= 6) & (m.bidx <= 60))}
        b_end = 5 * np.arange(NB) + 5                     # exclusive 1m index end of 5m bar b
        for an, A in anchors.items():
            has = A.any(1); a = np.where(has, A.argmax(1), 10 ** 6); after = (m.bidx > a[:, None])
            j0 = np.clip(5 * a, 0, 5 * NB)[:, None]
            num = CS[:, b_end] - np.take_along_axis(CS, j0, 1); den = CV[:, b_end] - np.take_along_axis(CV, j0, 1)
            cnt = b_end[None, :] - j0; tpm = (CT[:, b_end] - np.take_along_axis(CT, j0, 1)) / np.maximum(cnt, 1)
            av = np.where(den > 0, num / np.where(den > 0, den, 1), tpm); av[~after] = np.nan
            ac = np.where(has, m.c[np.arange(n), np.clip(a, 0, NB - 1)], np.nan)
            for tag, line in (("AV", av), ("SV", np.where(after, m.vwap, np.nan))):
                ab = after & (m.c > line)
                E[f"{tag}_{an}"] = E.get(f"{tag}_{an}", {}); E[f"{tag}_{an}"][i] = first(ab & (m.l <= line + 0.25 * m.atr5))
                pop = ab & m.valid
                cache[(f"{tag}_{an}", i)] = dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - line) / m.a[:, None], 5), P.causal_bins(m, pop, (m.c - ac[:, None]) / m.a[:, None], 3)])
    R = {}
    for name in E:
        def nullf(m, inst, ev, key, name=name):
            c = cache[(name, inst)]; return P.cell_null(m, ev, c["pop"], key, c["b"])
        R[name] = nullf
    D, F, nrows = [], [], 0
    adj = {f"AV_{a}": [f"AV_{b}" for b in ("BRK12", "PDH", "OR30") if b != a] for a in ("BRK12", "PDH", "OR30")}
    adj.update({f"SV_{a}": [f"SV_{b}" for b in ("BRK12", "PDH", "OR30") if b != a] for a in ("BRK12", "PDH", "OR30")})
    # run each definition with its own null (run_family takes one nullf -> dispatch on variant)
    def disp(m, inst, ev, key):
        return R[CUR[0]](m, inst, ev, key)
    global CUR
    allD, allF = [], []
    rows_by = {}
    for name in ["AV_BRK12", "SV_BRK12", "AV_PDH", "SV_PDH", "AV_OR30", "SV_OR30"]:
        CUR = [name]
        rows = P.evaluate(name, E[name], disp, meta={"family": "AVWAP"}); rows_by[name] = rows[-1]; allD += rows
        print(name, rows[-1]["n_events"], {k: round(rows[-1][f"{k}_xF"], 4) for k in P.HZ}, {k: round(rows[-1][f"{k}_mean"], 4) for k in P.HZ}, flush=True)
    fin = []
    for name, r in rows_by.items():
        for key in ("h12", "h24", "h1615"):
            x = r[f"{key}_xF"]; aok = any(np.sign(rows_by[a][f"{key}_xF"]) == np.sign(x) and abs(rows_by[a][f"{key}_xF"]) >= 0.5 * abs(x) for a in adj[name])
            fin.append({"variant": name, "horizon": key, "n": r[f"{key}_n"], "mean": r[f"{key}_mean"], "cost_atr": r["cost_atr"], "xF": x, "xF_lo": r[f"{key}_xF_lo"],
                        "xF_hi": r[f"{key}_xF_hi"], "years_pos": r[f"{key}_years_pos"], "inst_pos": r[f"{key}_inst_pos"], "xF_2021": r[f"{key}_xF_2021"],
                        "x2022": r[f"{key}_x2022"], "xA": r[f"{key}_xA"], "xC": r[f"{key}_xC"], "adjacent_ok": aok, "fallback": r[f"{key}_fallback"],
                        "class": P.classify(r, key, adjacent_ok=aok)})
    F = pd.DataFrame(fin); os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(allD).to_csv(os.path.join(OUT, "TEST101_EVENTS.csv"), index=False); F.to_csv(os.path.join(OUT, "TEST101_CLASSIFICATION.csv"), index=False)
    cmp = [{"anchor": a, "horizon": k, "AV_mean": rows_by[f"AV_{a}"][f"{k}_mean"], "SV_mean": rows_by[f"SV_{a}"][f"{k}_mean"],
            "AV_minus_SV_raw": rows_by[f"AV_{a}"][f"{k}_mean"] - rows_by[f"SV_{a}"][f"{k}_mean"], "AV_xF": rows_by[f"AV_{a}"][f"{k}_xF"], "SV_xF": rows_by[f"SV_{a}"][f"{k}_xF"]}
           for a in ("BRK12", "PDH", "OR30") for k in P.HZ]
    pd.DataFrame(cmp).to_csv(os.path.join(OUT, "TEST101_AV_VS_SV.csv"), index=False)
    nrows = P.ledger(allD, "TEST101", "AVWAP", "PHASE1")
    pd.set_option("display.width", 250); print(F.round(4).to_string()); print(pd.DataFrame(cmp).round(4).to_string())
    json.dump({"ledger_rows": nrows, "definitions_new": 6, "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T101_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
