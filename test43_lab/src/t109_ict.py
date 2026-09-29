"""TEST109 ICT falsification mini-lane (prereg a05fae4)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402
from t99_htf import htf, to5  # noqa: E402

OUT = os.path.join(S.OUT, "t109"); NB = P.NB; TF = {"5m": 1, "15m": 3}; RW = {"5m": 12, "15m": 4}


def shift(X, k, fill=np.nan):
    n, nk = X.shape; f = X.ravel().astype(float); o = np.full(f.shape, fill); o[k:] = f[:-k]; return o.reshape(n, nk)


def main():
    M = P.markets(); E = {}; cache = {}
    for i in P.INSTS:
        m = M[i]; n = m.n
        for tf, m5 in TF.items():
            if m5 == 1:
                O, H, L, C, nk = m.o, m.h, m.l, m.c, NB
            else:
                O, H, L, C, nk, _ = htf(m, m5)
            kk = np.repeat(np.arange(nk)[None, :], n, 0); same = kk >= 2
            bull = C > O; mid_bull = shift(bull.astype(float), 1) == 1
            fvg = same & (shift(H, 2) < L) & mid_bull
            trip = same & mid_bull
            ret = np.zeros((n, nk), bool)
            for s in range(n):
                last = None
                for k in range(nk):
                    if fvg[s, k]:
                        last = k; continue
                    if last is not None and k <= last + RW[tf] and L[s, k] <= L[s, last] and C[s, k] > H[s, last - 2]:
                        ret[s, k] = True; last = None
            fl = H.ravel(); ph = np.full(fl.shape, np.nan)
            for t in range(4, len(fl)):
                p = t - 2
                if fl[p] > max(fl[p - 2], fl[p - 1], fl[p + 1], fl[p + 2]):
                    ph[t] = fl[p]
            last2 = pd.Series(ph).ffill().values; prev = pd.Series(np.where(np.isnan(ph), np.nan, pd.Series(ph).ffill().shift(1).values)).ffill().values
            # prev confirmed pivot before the last one
            piv = pd.Series(ph).dropna(); pv = pd.Series(np.nan, index=range(len(fl))); pv[piv.index] = piv.shift(1).values; prevp = pv.ffill().values
            desc = last2 < prevp; cf = C.ravel(); pcf = np.r_[np.nan, cf[:-1]]
            ch = (desc & (cf > last2) & (pcf <= last2)).reshape(n, nk)
            ch = ch & (np.cumsum(ch, 1) == 1)
            d3 = (C - shift(C, 3)) / m.a[:, None]; mr = shift(H - L, 1) / m.a[:, None]; mv = (C - O[:, :1]) / m.a[:, None] if m5 > 1 else (C - m.open0[:, None]) / m.a[:, None]
            E.setdefault(f"FVG_DISP_{tf}", {})[i] = to5(m, fvg, m5, nk) if m5 > 1 else fvg
            E.setdefault(f"FVG_RETRACE_{tf}", {})[i] = to5(m, ret, m5, nk) if m5 > 1 else ret
            E.setdefault(f"CHOCH_{tf}", {})[i] = to5(m, ch, m5, nk) if m5 > 1 else ch
            g = (lambda X: to5(m, X, m5, nk)) if m5 > 1 else (lambda X: X)
            popA = g(trip) & m.valid; popB = g(np.ones((n, nk), bool)) & m.valid
            cache[("A", tf, i)] = dict(pop=popA, b=[P.causal_bins(m, popA, g(d3), 5), P.causal_bins(m, popA, g(mr), 3)])
            cache[("B", tf, i)] = dict(pop=popB, b=[P.causal_bins(m, popB, g(d3), 5), P.causal_bins(m, popB, g(mv), 3)])

    def nullf(m, inst, ev, key):
        nm = CUR[0]; tf = nm.rsplit("_", 1)[1]; c = cache[("A" if nm.startswith("FVG_DISP") else "B", tf, inst)]
        return P.cell_null(m, ev, c["pop"], key, c["b"])
    global CUR
    names = [f"{a}_{t}" for a in ("FVG_DISP", "FVG_RETRACE", "CHOCH") for t in ("5m", "15m")]
    allD, pooled = [], {}
    for nm in names:
        CUR = [nm]; rows = P.evaluate(nm, E[nm], nullf, meta={"family": "ICT"}); allD += rows; pooled[nm] = rows[-1]
        print(nm, rows[-1]["n_events"], {k: round(rows[-1][f"{k}_xF"], 4) for k in P.HZ}, flush=True)
    fin = []
    for nm, r in pooled.items():
        base, tf = nm.rsplit("_", 1); o = f"{base}_{'15m' if tf == '5m' else '5m'}"
        for key in ("h12", "h24", "h1615"):
            x = r[f"{key}_xF"]; aok = bool(np.sign(pooled[o][f"{key}_xF"]) == np.sign(x) and abs(pooled[o][f"{key}_xF"]) >= 0.5 * abs(x))
            fin.append({"variant": nm, "horizon": key, "n": r[f"{key}_n"], "mean": r[f"{key}_mean"], "cost_atr": r["cost_atr"], "xF": x, "xF_lo": r[f"{key}_xF_lo"],
                        "xF_hi": r[f"{key}_xF_hi"], "years_pos": r[f"{key}_years_pos"], "inst_pos": r[f"{key}_inst_pos"], "xF_2021": r[f"{key}_xF_2021"],
                        "x2022": r[f"{key}_x2022"], "xA": r[f"{key}_xA"], "xC": r[f"{key}_xC"], "adjacent_ok": aok, "fallback": r[f"{key}_fallback"],
                        "class": P.classify(r, key, adjacent_ok=aok)})
    F = pd.DataFrame(fin); os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(allD).to_csv(os.path.join(OUT, "TEST109_EVENTS.csv"), index=False); F.to_csv(os.path.join(OUT, "TEST109_CLASSIFICATION.csv"), index=False)
    n = P.ledger(allD, "TEST109", "ICT", "PHASE1")
    pd.set_option("display.width", 250); print(F.round(4).to_string())
    json.dump({"ledger_rows": n, "definitions_new": 6, "classes": F["class"].value_counts().to_dict()}, open(os.path.join(OUT, "T109_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
