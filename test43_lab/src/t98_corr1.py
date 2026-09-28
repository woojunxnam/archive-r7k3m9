"""TEST98_AUDIT_CORRECTION_1 (prereg b1ac158): recompute ONLY PQ2_bullrun12 / PQ2_hlrun12 with the true within-window longest run; everything
else re-uses Phase-1 machinery unchanged (t98_phase1)."""
import ast, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(__file__))
import t98_phase1 as P
import t97_wave1 as W1

M, INSTS, NB, HK, PRIMARY = P.M, P.INSTS, P.NB, P.HK, P.PRIMARY


def runmax_window(x, W=12):
    r = np.zeros(len(x)); c = 0
    for i, v in enumerate(x):
        c = c + 1 if v else 0; r[i] = c
    rs = pd.Series(r); out = np.zeros(len(x))
    for q in range(W):
        out = np.maximum(out, np.minimum(rs.shift(q).fillna(0).values, W - q))   # run ending at i-q truncated to the window start i-11
    return out


def main():
    FE, EV, XF = {}, {}, {}
    for i in INSTS:
        m = M[i]; F = P.features(m); ev = P.fresh_events(m) & (np.arange(m.n)[:, None] >= P.WARM); EV[i] = ev
        c, o, l = (pd.Series(x.ravel()) for x in (m.c, m.o, m.l))
        F["PQ2_bullrun12_CORR"] = runmax_window((c > o).values).reshape(m.n, NB); F["PQ2_hlrun12_CORR"] = runmax_window((l > l.shift(1)).values).reshape(m.n, NB)
        assert np.nanmax(F["PQ2_bullrun12_CORR"]) <= 12 and np.nanmax(F["PQ2_hlrun12_CORR"]) <= 12
        FE[i] = F
        for key in HK:
            nul, lev, ok = P.family_null(m, ev, F, key); XF[(i, key)] = m.R[key] - nul
    nxt = {}
    for i in INSTS:
        m = M[i]; st = W1.strong(m); nb_bull, nb_body, nb_st = np.roll(m.bull, -1, 1), np.roll(m.body_pct, -1, 1), np.roll(st, -1, 1)
        lab = np.where(~nb_bull, 0, np.where(nb_body < 0.5, 1, np.where(nb_st, 3, 2))).astype(float); lab[:, -1] = np.nan; nxt[i] = lab
    rows, curves = [], []
    for f in ("PQ2_bullrun12", "PQ2_hlrun12", "PQ2_bullrun12_CORR", "PQ2_hlrun12_CORR"):
        bins = {i: P.causal_bins(M[i], EV[i], FE[i][f], 5) for i in INSTS}
        res = {"feature": f, "max_value_at_events": float(max(np.nanmax(FE[i][f][EV[i]]) for i in INSTS))}
        for key in PRIMARY:
            per = []
            for bq in range(5):
                vals = [XF[(i, key)][EV[i] & (bins[i] == bq)] for i in INSTS]; v = np.concatenate(vals)
                per.append({"bin": bq, "n": int((~np.isnan(v)).sum()), "xF": float(np.nanmean(v)) if len(v) else np.nan, **{f"xF_{i}": float(np.nanmean(x_)) if len(x_) else np.nan for i, x_ in zip(INSTS, vals)}})
                curves.append({"feature": f, "horizon": key, **per[-1]})
            ne = [p for p in per if p["n"] > 0 and p["xF"] == p["xF"]]
            rho = spearmanr(range(len(ne)), [p["xF"] for p in ne]).correlation if len(ne) >= 3 else np.nan
            top, bot = max(p["bin"] for p in ne), min(p["bin"] for p in ne)
            sel = {i: EV[i] & np.isin(bins[i], [top, bot]) for i in INSTS}
            v = np.concatenate([XF[(i, key)][sel[i]] for i in INSTS]); g = np.concatenate([(bins[i][sel[i]] == top).astype(float) for i in INSTS])
            cl = np.concatenate([M[i].date[sel[i]] for i in INSTS]); yr = np.concatenate([M[i].year[sel[i]] for i in INSTS])
            lo, hi = P.boot_diff(v, g, cl); diff = float(np.nanmean(v[g == 1]) - np.nanmean(v[g == 0]))
            ys = [np.nanmean(v[(yr == y) & (g == 1)]) - np.nanmean(v[(yr == y) & (g == 0)]) for y in np.unique(yr)]
            ysame = int(sum(np.sign(y_) == np.sign(diff) for y_ in ys if y_ == y_))
            pt, pb = next(p for p in per if p["bin"] == top), next(p for p in per if p["bin"] == bot)
            isame = int(sum(np.sign(pt[f"xF_{i}"] - pb[f"xF_{i}"]) == np.sign(diff) for i in INSTS))
            vs = np.concatenate([(nxt[i] == 3)[sel[i]].astype(float) for i in INSTS]); l2, h2 = P.boot_diff(vs, g, cl)
            res.update({f"{key}_rho": rho, f"{key}_top_minus_bottom": diff, f"{key}_ci_lo": lo, f"{key}_ci_hi": hi, f"{key}_years_same": ysame, f"{key}_inst_same": isame,
                        f"{key}_COHERENT": bool(abs(rho) >= 0.9 and (lo > 0 or hi < 0) and ysame >= 5 and isame >= 3), f"{key}_pstrong_diff": float(np.nanmean(vs[g == 1]) - np.nanmean(vs[g == 0])),
                        f"{key}_pstrong_ci": (l2, h2)})
        rows.append(res)
    R = pd.DataFrame(rows); Cv = pd.DataFrame(curves); D = P.OUT
    R.to_csv(f"{D}/CORR1_RUN_FEATURES.csv", index=False); Cv.to_csv(f"{D}/CORR1_RUN_CURVES.csv", index=False)
    # ledger: append corrected rows (distinct definitions unchanged: corrected features replace the two defective ones)
    pd.DataFrame([{"variant": f"{r['feature']}|q{r['bin']}", "horizon": r["horizon"], "instrument": "POOLED", "n": r["n"], "xF": r["xF"], "note": "CORR1"} for r in curves if "CORR" in r["feature"]]).to_csv(
        f"{D}/TEST98_RESEARCH_LEDGER.csv", mode="a", header=False, index=False)
    any_coh = bool(R[R.feature.str.endswith("CORR")][["h6_COHERENT", "h12_COHERENT"]].any().any())
    S = {"CORRECTION": "TEST98_AUDIT_CORRECTION_1", "PREREG_COMMIT": "b1ac158", "PHASE1_RESULT_COMMIT": "91dbf4a",
         "CORRECTED_RUN_FEATURES_COHERENT": any_coh,
         "PHASE1_CROSS_VALIDATION": "NOT RUN (Phase 1 used prior-session monthly expanding quantile boundaries, date-clustered bootstrap and calendar-year consistency; no chronological CV folds; ML not opened)",
         "FOLLOW_THROUGH_22_OF_37": "RAW_NEXT_BAR_STRONG_ASSOCIATION - not residualised against null F, not evaluated as chronological OOS prediction, not a deployable model",
         "PRECONFIRM_FEATURES_PREDICT_FOLLOWTHROUGH": "NO (preregistered economic definition)",
         "MULTIPLE_TESTING_NOTE": "74 primary coherence tests inspected; a naive 5% CI-only reference implies ~3.7 nominal CI hits under independence; the full coherence "
                                  "gate is much stricter and the tests are correlated, so 3.7 is NOT the expected number of full passes; actual full coherence passes = 0 "
                                  "(unchanged after this correction); no multiplicity threshold changed",
         "TEST98_STATUS": "CLOSED" if not any_coh else "CLOSED_WITH_CORRECTED_CLUE", "TEST98_SIMPLE_PRECONFIRM_PATH_FAMILY": "SATURATED" if not any_coh else "CORRECTED_CLUE_ONLY",
         "TEST98_PORTFOLIO_SURVIVOR": "NO", "OPEN_ACCEPTANCE": "WEAK_RESEARCH_CLUE_ONLY", "ML_OPENED": "NO", "GA_OPENED": "NO",
         "DISTINCT_VARIANTS_TESTED": 37, "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO",
         "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1"}
    json.dump(S, open(f"{D}/TEST98_FINAL_STATUS.json", "w"), indent=1, default=str)
    cols = ["feature", "max_value_at_events", "h6_rho", "h6_top_minus_bottom", "h6_ci_lo", "h6_ci_hi", "h6_COHERENT", "h12_rho", "h12_top_minus_bottom", "h12_ci_lo", "h12_ci_hi",
            "h12_years_same", "h12_inst_same", "h12_COHERENT", "h12_pstrong_diff"]
    md = ["# TEST98_AUDIT_CORRECTION_1 - results (prereg b1ac158)", "", "```json", json.dumps(S, indent=1), "```", "",
          "## Old (defective runmax) vs corrected within-window runs (pooled; excess vs null F)", R[cols].to_markdown(floatfmt=".4f"), "",
          "## Corrected response curves", Cv[Cv.feature.str.endswith("CORR")].to_markdown(floatfmt=".4f")]
    open(os.path.join(P.REP, "TEST98_AUDIT_CORRECTION_1_REPORT.md"), "w").write("\n".join(md) + "\n")
    # Phase-1 status wording fixes (no economics)
    p = f"{D}/TEST98_PHASE1_STATUS.json"; st = json.load(open(p))
    st["PQ2_bullrun12 / PQ2_hlrun12"] = "defective in Phase 1 (runs could exceed the 12-bar window); superseded by TEST98_AUDIT_CORRECTION_1"
    st["PHASE1_CROSS_VALIDATION"] = S["PHASE1_CROSS_VALIDATION"]; st["FOLLOW_THROUGH_22_OF_37"] = S["FOLLOW_THROUGH_22_OF_37"]; st["MULTIPLE_TESTING_NOTE"] = S["MULTIPLE_TESTING_NOTE"]
    st["SUPERSEDED_BY"] = "TEST98_FINAL_STATUS.json"; json.dump(st, open(p, "w"), indent=1, default=str)
    pd.set_option("display.width", 250); print(R[cols].round(4).to_string()); print(json.dumps(S, indent=1))


if __name__ == "__main__":
    main()
