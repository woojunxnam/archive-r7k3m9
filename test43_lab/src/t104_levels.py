"""TEST104 level interaction factory (prereg 3ead923)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t104"); NB = P.NB
RES = ["PDH", "PWH", "ORH", "SWH60", "H2H"]; SUP = ["PDL", "PWL", "ORL", "SWL60", "L2H"]


def levels(m):
    I = m.I; n = m.n; Hd = np.nanmax(I.H, 1); Ld = np.nanmin(I.L, 1); rep = lambda v: np.repeat(v[:, None], NB, 1).astype(float)
    wk = pd.Series(I.sess).dt.isocalendar(); key = (wk.year * 100 + wk.week).values
    dfw = pd.DataFrame({"k": key, "H": Hd, "L": Ld}).groupby("k").agg({"H": "max", "L": "min"}); ks = dfw.index.values
    pos = np.searchsorted(ks, key); pwh = np.where(pos > 0, dfw.H.values[np.clip(pos - 1, 0, None)], np.nan); pwl = np.where(pos > 0, dfw.L.values[np.clip(pos - 1, 0, None)], np.nan)
    Lv = {"PDH": rep(np.r_[np.nan, Hd[:-1]]), "PDL": rep(np.r_[np.nan, Ld[:-1]]), "PWH": rep(pwh), "PWL": rep(pwl)}
    orh = np.full((n, NB), np.nan); orl = np.full((n, NB), np.nan); orh[:, 5:] = np.max(m.h[:, :6], 1)[:, None]; orl[:, 5:] = np.min(m.l[:, :6], 1)[:, None]
    Lv["ORH"], Lv["ORL"] = orh, orl
    # causal 60m swings on chained complete 60m bars (completion at 5m bar 12k+11)
    nk = 6; H6 = np.stack([m.h[:, 12 * k:12 * k + 12].max(1) for k in range(nk)], 1).ravel(); L6 = np.stack([m.l[:, 12 * k:12 * k + 12].min(1) for k in range(nk)], 1).ravel()
    sh = np.full(H6.shape, np.nan); sl = np.full(L6.shape, np.nan); cur_h = np.nan; cur_l = np.nan
    for t in range(len(H6)):
        if t >= 4:
            p = t - 2
            if H6[p] > max(H6[p - 2], H6[p - 1], H6[p + 1], H6[p + 2]):
                cur_h = H6[p]
            if L6[p] < min(L6[p - 2], L6[p - 1], L6[p + 1], L6[p + 2]):
                cur_l = L6[p]
        sh[t] = cur_h; sl[t] = cur_l
    sh = sh.reshape(n, nk); sl = sl.reshape(n, nk); swh = np.full((n, NB), np.nan); swl = np.full((n, NB), np.nan)
    prev_h = np.r_[np.nan, sh[:-1, -1]]; prev_l = np.r_[np.nan, sl[:-1, -1]]
    for b in range(NB):
        k = (b + 1) // 12 - 1                                    # last 60m bar completed at or before 5m bar b
        swh[:, b] = sh[:, k] if k >= 0 else prev_h; swl[:, b] = sl[:, k] if k >= 0 else prev_l
    Lv["SWH60"], Lv["SWL60"] = swh, swl
    Hs = pd.Series(m.h.ravel()); Ls = pd.Series(m.l.ravel())
    Lv["H2H"] = Hs.rolling(24, min_periods=24).max().shift(1).values.reshape(n, NB); Lv["L2H"] = Ls.rolling(24, min_periods=24).min().shift(1).values.reshape(n, NB)
    return Lv


def detect(m, Lv):
    n = m.n; c, l_, h = m.c, m.l, m.h; A5 = m.atr5; ev = {}; brk_bars = {}
    for nm in RES:
        L = Lv[nm]; e = np.zeros((n, NB), bool); bk = np.zeros((n, NB), bool); lvlb = np.full((n, NB), np.nan)
        for s in range(n):
            row = L[s]
            for b in range(1, 61):
                if row[b] == row[b] and row[b - 1] == row[b - 1] and c[s, b] > row[b] and c[s, b - 1] <= row[b - 1]:
                    lv = row[b]; bk[s, b] = True; lvlb[s, b] = lv
                    for b2 in range(b + 1, 68):
                        if c[s, b2] < lv:
                            break
                        if l_[s, b2] <= lv + 0.25 * A5[s, b2]:
                            e[s, b2] = True; break
                    break
        ev[f"L1_{nm}"] = e; brk_bars[nm] = (bk, lvlb)
    for nm in SUP:
        L = Lv[nm]; e = np.zeros((n, NB), bool)
        for s in range(n):
            row = L[s]
            for b in range(1, 61):
                if row[b] == row[b] and row[b - 1] == row[b - 1] and c[s, b] < row[b] and c[s, b - 1] >= row[b - 1]:
                    lv = row[b]; rec = None
                    for b2 in range(b + 1, 68):
                        if rec is None:
                            if c[s, b2] > lv:
                                rec = b2
                        else:
                            if c[s, b2] < lv:
                                break
                            if l_[s, b2] <= lv + 0.25 * A5[s, b2]:
                                e[s, b2] = True; break
                    break
        ev[f"L2_{nm}"] = e
    for nm in ("PWL", "SWL60", "L2H"):
        L = Lv[nm]; pc = np.concatenate([np.full((n, 1), np.nan), c[:, :-1]], 1); pL = np.concatenate([np.full((n, 1), np.nan), L[:, :-1]], 1)
        sw = (l_ < L) & (c > L) & (pc > pL) & (m.bidx >= 1)
        ev[f"L3_{nm}"] = sw & (np.cumsum(sw, 1) == 1)
    return ev, brk_bars


def main():
    M = P.markets(); E = {}; cache = {}; feats = {"L4_APPROACH_SPEED": {}, "L5_TOUCH_COUNT": {}}; pops = {}; lvl_of = {}
    for i in P.INSTS:
        m = M[i]; Lv = levels(m); ev, bb = detect(m, Lv)
        for k, v in ev.items():
            E.setdefault(k, {})[i] = v
        for nm in RES + SUP:
            L = Lv[nm]; pop = (m.c > L) & m.valid; mv = (m.c - m.open0[:, None]) / m.a[:, None]
            cache[(nm, i)] = dict(pop=pop, b=[P.causal_bins(m, pop, (m.c - L) / m.a[:, None], 5), P.causal_bins(m, pop, mv, 3)])
        # L4 / L5 on the union of R break bars (per bar keep the first level type in RES order)
        brk = np.zeros((m.n, NB), bool); lvl = np.full((m.n, NB), np.nan); src = np.full((m.n, NB), "", object)
        for nm in RES:
            bk, lv = bb[nm]; new = bk & ~brk; brk |= bk; lvl[new] = lv[new]; src[new] = nm
        c6 = np.concatenate([np.full((m.n, 6), np.nan), m.c[:, :-6]], 1)
        feats["L4_APPROACH_SPEED"][i] = np.where(brk, (m.c - c6) / m.a[:, None], np.nan)
        tc = np.full((m.n, NB), np.nan)
        for s, b in zip(*np.where(brk)):
            lv = lvl[s, b]; tc[s, b] = float(np.sum((m.h[s, :b] >= lv - 0.25 * m.atr5[s, :b]) & (m.c[s, :b] <= lv)))
        feats["L5_TOUCH_COUNT"][i] = tc; pops[i] = brk; lvl_of[i] = src

    def nullf(m, inst, ev, key):
        nm = CUR[0].split("_", 1)[1]; c = cache[(nm, inst)]; return P.cell_null(m, ev, c["pop"], key, c["b"])

    def brknull(m, inst, ev, key):                   # break bars: null from their own level type's pool
        out = np.full(m.R[key].shape, np.nan); lv = np.full(out.shape, -1)
        for nm in RES:
            sel = ev & (lvl_of[inst] == nm); c = cache[(nm, inst)]; a, b = P.cell_null(m, sel, c["pop"], key, c["b"]); out[sel] = a[sel]; lv[sel] = b[sel]
        return out, lv
    global CUR
    names = [f"L1_{x}" for x in RES] + [f"L2_{x}" for x in SUP] + [f"L3_{x}" for x in ("PWL", "SWL60", "L2H")]
    allD, pooled = [], {}
    for nm in names:
        CUR = [nm]; rows = P.evaluate(nm, E[nm], nullf, meta={"family": nm[:2]}); allD += rows; pooled[nm] = rows[-1]
        print(nm, rows[-1]["n_events"], {k: round(rows[-1][f"{k}_xF"], 4) for k in P.HZ}, flush=True)
    fin = []
    for nm, r in pooled.items():
        fam = nm[:2]; others = [o for o in pooled if o[:2] == fam and o != nm]
        for key in ("h12", "h24", "h1615"):
            x = r[f"{key}_xF"]; aok = any(np.sign(pooled[o][f"{key}_xF"]) == np.sign(x) and abs(pooled[o][f"{key}_xF"]) >= 0.5 * abs(x) for o in others)
            fin.append({"variant": nm, "horizon": key, "n": r[f"{key}_n"], "mean": r[f"{key}_mean"], "cost_atr": r["cost_atr"], "xF": x, "xF_lo": r[f"{key}_xF_lo"],
                        "xF_hi": r[f"{key}_xF_hi"], "years_pos": r[f"{key}_years_pos"], "inst_pos": r[f"{key}_inst_pos"], "xF_2021": r[f"{key}_xF_2021"],
                        "x2022": r[f"{key}_x2022"], "xA": r[f"{key}_xA"], "xC": r[f"{key}_xC"], "adjacent_ok": aok, "fallback": r[f"{key}_fallback"],
                        "class": P.classify(r, key, adjacent_ok=aok)})
    F = pd.DataFrame(fin); os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(allD).to_csv(os.path.join(OUT, "TEST104_EVENTS.csv"), index=False); F.to_csv(os.path.join(OUT, "TEST104_CLASSIFICATION.csv"), index=False)
    n = P.ledger(allD, "TEST104", "LEVELS", "PHASE1"); cohs = []
    for fn in ("L4_APPROACH_SPEED", "L5_TOUCH_COUNT"):
        rc, coh = P.response_curve(fn, feats[fn], pops, brknull); rc.to_csv(os.path.join(OUT, f"TEST104_{fn}_CURVE.csv"), index=False); cohs.append(coh); n += len(rc)
    C = pd.concat(cohs); C.to_csv(os.path.join(OUT, "TEST104_CURVE_COHERENCE.csv"), index=False)
    pd.set_option("display.width", 250); print(F.round(4).to_string()); print(C.round(4).to_string())
    json.dump({"ledger_rows": n, "definitions_new": 15, "classes": F["class"].value_counts().to_dict(), "curves_coherent": C.COHERENT.tolist()}, open(os.path.join(OUT, "T104_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
