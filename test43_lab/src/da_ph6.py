"""PH6 structural discretionary grammar search, exhaustive (prereg f85f648)."""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_bank as B  # noqa: E402
import rp_econ as EC  # noqa: E402

OUT = os.path.join(R.OUT, "ph6"); os.makedirs(OUT, exist_ok=True)
TRIG = ["C2", "D1", "D2", "D3", "D7", "D8", "LN1", "LN2", "LN3", "TOUCH"]; TREND = ["any", "up"]; VOL = ["any", "lowmid", "high"]; TOD = ["any", "am", "pm"]
CONF = ["any", "conf2"]; ROOM = ["any", "room"]; EXIT = ["X60", "X120", "X1615", "XRES", "XSTRUCT"]
DOM = [TRIG, TREND, VOL, TOD, CONF, ROOM, EXIT]


def room_tercile(G):
    per = pd.to_datetime(G.date, unit="D").dt.to_period("M").values; x = G.up_room.values; top = np.zeros(len(G), bool)
    for mo in np.unique(per):
        rows = np.where(per == mo)[0]; st = G.date.values[rows].min(); pr = x[(G.date.values < st) & ~np.isnan(x)]
        if len(pr) < 50:
            continue
        e = np.percentile(pr, 200 / 3); top[rows] = (x[rows] >= e) | (G.no_res.values[rows] > 0)
    return top


def nrestr(g):
    return sum(v != DOM[i][0] for i, v in enumerate(g) if i not in (0, 6)) + int(g[6] != "X1615")


def main():
    M = P.markets(); X = pd.read_parquet(os.path.join(R.OUT, "ph4", "PH4_EXIT_DATASET.parquet"))
    X["trig"] = X["def"].replace({"D1B": "C2", "D1B_P": "C2"}); G = X[X.trig.isin(TRIG)].reset_index(drop=True)
    up = np.zeros(len(G))
    for i in P.INSTS:
        F = B.features(M[i]); sel = (G.inst == i).values; up[sel] = F["up50"][G.s.values[sel], G.b.values[sel]]
    G["up50"] = up; G = G.sort_values("date").reset_index(drop=True); G["room_top"] = room_tercile(G)
    c = EC.ctx(); pos = np.array([c["pos"].get(int(d), -1) for d in G.date]); nS = len(c["sess"]); full = np.asarray(EC.C.main_ctx()["Is"]["MNQ"].full); yrs = c["sess"].year.values
    mainD = c["main"]; w = c["win"]
    Mk = {("t", t): (G.trig == t).values for t in TRIG}
    Mk.update({("h", "any"): np.ones(len(G), bool), ("h", "up"): G.up50.values == 1, ("v", "any"): np.ones(len(G), bool), ("v", "lowmid"): G.vt.values <= 1, ("v", "high"): G.vt.values == 2,
               ("d", "any"): np.ones(len(G), bool), ("d", "am"): G.b.values < 30, ("d", "pm"): G.b.values >= 30, ("c", "any"): np.ones(len(G), bool), ("c", "conf2"): G.conf_sup_15.values >= 2,
               ("r", "any"): np.ones(len(G), bool), ("r", "room"): G.room_top.values})
    genomes = list(itertools.product(*DOM)); dc = {}; d4c = {}; sel = {}
    for g in genomes:
        m = Mk[("t", g[0])] & Mk[("h", g[1])] & Mk[("v", g[2])] & Mk[("d", g[3])] & Mk[("c", g[4])] & Mk[("r", g[5])] & G[f"usd_{g[6]}"].notna().values & (pos >= 0)
        sel[g] = m; dc[g] = np.bincount(pos[m], G[f"usd_{g[6]}"].values[m], minlength=nS); d4c[g] = np.bincount(pos[m], G[f"usd4_{g[6]}"].values[m], minlength=nS)
    np.save(os.path.join(OUT, "GENOME_WINDOW_DAILY.npy"), np.vstack([dc[g][w] for g in genomes]).astype(np.float32))
    json.dump([list(g) for g in genomes], open(os.path.join(OUT, "GENOME_LIST.json"), "w"))
    picks = {}; stab = []; eyear = G.year.values
    for f, ye in EC.TRAIN_END.items():
        ti_years = [y for y in range(2019, ye) if (full & (yrs == y)).sum() > 20]; ti_days = full & (yrs < ye) & (c["sess"] >= "2019-07-01"); va = full & (yrs == ye); fit = {}; val = {}
        for g in genomes:
            if (sel[g] & (eyear < ye)).sum() < 100 or not ti_years:
                continue
            d = dc[g]; ya = [d[full & (yrs == y)].mean() for y in ti_years]; cr = np.corrcoef(d[ti_days], mainD[ti_days])[0, 1] if d[ti_days].std() > 0 else 0.0
            fit[g] = float(np.mean(ya) - (0.5 * np.std(ya) if len(ya) > 1 else 0) - 0.5 * nrestr(g) - 5 * max(0.0, cr - 0.35)); val[g] = (float(d[va].mean()), int((sel[g] & (eyear == ye)).sum()))
        top = sorted(fit, key=lambda g: -fit[g])[:20]; cands = [g for g in top if val[g][1] >= 20 and val[g][0] > 0]
        pick = max(cands, key=lambda g: (val[g][0], -nrestr(g))) if cands else None; picks[f] = pick
        if pick:
            nb = [tuple(pick[:i]) + (v,) + tuple(pick[i + 1:]) for i, dom in enumerate(DOM) for v in dom if v != pick[i]]
            stab.append(float(np.mean([fit.get(n, -1) > 0 for n in nb])))
    rows = []
    for f, pick in picks.items():
        if pick is None:
            continue
        a, b = EC.FOLDS[f]; m = sel[pick] & (eyear >= a) & (eyear <= b); rows.append(pd.DataFrame({"date": G.date.values[m], "usd": G[f"usd_{pick[6]}"].values[m], "usd4": G[f"usd4_{pick[6]}"].values[m]}))
    T = pd.concat(rows); npop = int((eyear >= 2021).sum()); met = EC.metrics(T.date.values, T.usd.values, T.usd4.values, npop); st = float(np.mean(stab)) if stab else 0.0
    tb = EC.tier_b(met); cls = "GRAMMAR_PASS" if tb and st >= 0.5 else ("GRAMMAR_OVERFIT_CLUE_ONLY" if tb else "GRAMMAR_FAIL")
    # best fixed genome on the stitched window (selection-exposed, diagnostic only)
    wavg = {g: dc[g][w].mean() for g in genomes}; best_fixed = sorted(wavg, key=lambda g: -wavg[g])[:10]
    out = {"n_genomes": len(genomes), "picks": {k: (list(v) if v else None) for k, v in picks.items()}, "stability": st, "class": cls, **met, "tier_b": tb,
           "top10_fixed_genomes_selection_exposed": [[list(g), round(wavg[g], 2)] for g in best_fixed]}
    T.to_parquet(os.path.join(OUT, "GRAMMAR_NESTED_TRADES.parquet"))
    R.append("GRAMMAR_SEARCH_LEDGER.csv", {"space": "trigger x trend x vol x TOD x confluence x room x exit", "n_candidates": len(genomes), "selected_by_fold": json.dumps(out["picks"]),
                                           "stitched_avg_day": round(met["avg_day"], 3), "stability": round(st, 3), "class": cls})
    json.dump(out, open(os.path.join(OUT, "PH6_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
