"""P5 structural GA via exhaustive enumeration (prereg f1e2b05)."""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import rp_econ as EC  # noqa: E402
import rp_state as R  # noqa: E402

OUT = os.path.join(R.OUT, "ga"); os.makedirs(OUT, exist_ok=True)
EXITS = ["h12", "h24", "h1615"]; TODS = ["any", "early", "mid", "late"]; VTS = ["any", 0, 1, 2]; VW = ["any", "above", "below"]


def spaces():
    c1 = [s for r in (1, 2, 3) for s in itertools.combinations(["P2", "L2", "A3"], r)]
    return {"C1_R1_TRAPPED_UNION": ("group", c1), "C4_L2_FAMILY": ("level", ["all", "L2_PDL", "L2_PWL", "L2_ORL", "L2_SWL60", "L2_L2H"]),
            "C7_L1_SWH60": ("market", ["all", "ES", "NQ", "YM", "RTY"])}


def masks(D, gname, gvals):
    tod = np.digitize(D.b.values, [12, 54]); M = {}
    for v in gvals:
        if gname == "group":
            grp = np.where(D.label.str.startswith("L2"), "L2", D.label.values); M[("g", v)] = np.isin(grp, v)
        elif gname == "level":
            M[("g", v)] = np.ones(len(D), bool) if v == "all" else (D.label.values == v)
        else:
            M[("g", v)] = np.ones(len(D), bool) if v == "all" else (D.inst.values != v)
    for k, t in enumerate(TODS):
        M[("t", t)] = np.ones(len(D), bool) if t == "any" else (tod == k - 1)
    for v in VTS:
        M[("v", v)] = np.ones(len(D), bool) if v == "any" else (D.vt.values == v)
    M[("w", "any")] = np.ones(len(D), bool); M[("w", "above")] = D.vwap_dist.values > 0; M[("w", "below")] = ~(D.vwap_dist.values > 0)
    return M


def nrestr(g, gdef):
    return int(g[0] != gdef) + int(g[1] != "any") + int(g[2] != "any") + int(g[3] != "any")


def main():
    c = EC.ctx(); sess = c["sess"]; full = np.asarray(EC.C.main_ctx()["Is"]["MNQ"].full); yrs_s = sess.year.values; mainD = c["main"]
    E = pd.read_parquet(os.path.join(R.OUT, "bank", "CANDIDATE_EVENTS.parquet")); summary = []; total = 0
    for cand, (gname, gvals) in spaces().items():
        D = E[E.candidate == cand].reset_index(drop=True); M = masks(D, gname, gvals); gdef = gvals[0] if gname != "group" else ("P2", "L2", "A3")
        pos = np.array([c["pos"].get(int(x), -1) for x in D.date]); genomes = list(itertools.product(gvals, TODS, VTS, VW, EXITS)); total += len(genomes)
        # daily matrix per genome (all sessions) -> cached as sparse via event selection
        sel = {}; usd = {h: D[f"usd_{h}"].values for h in EXITS}; usd4 = {h: D[f"usd4_{h}"].values for h in EXITS}
        for g in genomes:
            m = M[("g", g[0])] & M[("t", g[1])] & M[("v", g[2])] & M[("w", g[3])] & ~np.isnan(usd[g[4]]) & (pos >= 0); sel[g] = m
        def daily(g, ymask_days):
            d = np.zeros(len(sess)); m = sel[g]; np.add.at(d, pos[m], usd[g[4]][m]); return d
        dc = {g: daily(g, None) for g in genomes}
        fold_pick = {}; out_rows = []; stab = []
        for f, ye in EC.TRAIN_END.items():
            ti_days = full & (yrs_s < ye) & (sess >= "2019-07-01"); va_days = full & (yrs_s == ye)
            ti_years = [y for y in range(2019, ye) if (full & (yrs_s == y)).sum() > 20]
            fit = {}; val = {}
            for g in genomes:
                d = dc[g]; m = sel[g]; ev_year = D.year.values
                ntr = int((m & (ev_year < ye)).sum()); nva = int((m & (ev_year == ye)).sum())
                if ntr < 100 or not ti_years:
                    continue
                ya = [d[full & (yrs_s == y)].mean() for y in ti_years]
                cr = np.corrcoef(d[ti_days], mainD[ti_days])[0, 1] if d[ti_days].std() > 0 else 0.0
                fit[g] = float(np.mean(ya) - (0.5 * np.std(ya) if len(ya) > 1 else 0) - 0.5 * nrestr(g, gdef) - 5 * max(0.0, cr - 0.35))
                val[g] = (float(d[va_days].mean()), nva)
            top = sorted(fit, key=lambda g: -fit[g])[:20]
            cands = [g for g in top if val[g][1] >= 20 and val[g][0] > 0]
            pick = max(cands, key=lambda g: (val[g][0], -nrestr(g, gdef))) if cands else None
            fold_pick[f] = pick
            if pick is not None:
                nb = [tuple(pick[:i]) + (v,) + tuple(pick[i + 1:]) for i, dom in enumerate([gvals, TODS, VTS, VW, EXITS]) for v in dom if v != pick[i]]
                stab.append(float(np.mean([fit.get(n, -1) > 0 for n in nb])))
        # stitched outer
        rows = []
        for f, pick in fold_pick.items():
            a, b = EC.FOLDS[f]
            if pick is None:
                continue
            m = sel[pick] & (D.year.values >= a) & (D.year.values <= b)
            rows.append(pd.DataFrame({"date": D.date.values[m], "usd": usd[pick[4]][m], "usd4": usd4[pick[4]][m], "fold": f}))
        T = pd.concat(rows) if rows else pd.DataFrame({"date": [], "usd": [], "usd4": []})
        npop = int((D.year >= 2021).sum()); met = EC.metrics(T.date.values, T.usd.values, T.usd4.values, npop)
        st = float(np.mean(stab)) if stab else 0.0; tb = EC.tier_b(met)
        cls = "GA_PASS" if tb and st >= 0.5 else ("GA_OVERFIT_CLUE_ONLY" if tb else "GA_FAIL")
        # outer-test neighbour positivity diagnostic
        diag = []
        for f, pick in fold_pick.items():
            if pick is None:
                continue
            a, b = EC.FOLDS[f]; nb = [tuple(pick[:i]) + (v,) + tuple(pick[i + 1:]) for i, dom in enumerate([gvals, TODS, VTS, VW, EXITS]) for v in dom if v != pick[i]]
            for n_ in nb:
                mm = sel[n_] & (D.year.values >= a) & (D.year.values <= b); diag.append(usd[n_[4]][mm].sum() > 0)
        T.to_parquet(os.path.join(OUT, f"GA_TRADES_{cand}.parquet"))
        summary.append({"family": cand, "n_genomes": len(genomes), **met, "ga_stability": st, "outer_neighbour_pos_diag": float(np.mean(diag)) if diag else np.nan,
                        "tier_b": tb, "class": cls, "picks": json.dumps({k: (list(map(str, v)) if v else None) for k, v in fold_pick.items()})})
        R.append("GA_GENOME_LEDGER.csv", {"family": cand, "n_genomes": len(genomes), "space": f"{gname} x TOD x vt x VWAP x exit", "selected_by_fold": summary[-1]["picks"],
                                          "stitched_avg_day": round(met["avg_day"], 3), "stability": round(st, 3), "note": cls})
        print(cand, round(met["avg_day"], 2), round(met["slip4_avg_day"], 2), met["folds_pos"], met["trades"], round(st, 2), cls, summary[-1]["picks"], flush=True)
    S = pd.DataFrame(summary); S.to_csv(os.path.join(OUT, "P5_GA_RESULTS.csv"), index=False)
    json.dump({"total_genomes": total}, open(os.path.join(OUT, "P5_META.json"), "w"))


if __name__ == "__main__":
    main()
