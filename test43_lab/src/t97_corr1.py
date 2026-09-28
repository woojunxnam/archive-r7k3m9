"""TEST97_AUDIT_CORRECTION_1 execution (prereg commit 85f5bdc, reports/TEST97_PLUS/TEST97_AUDIT_CORRECTION_1_PREREGISTRATION.md).
No new parameters.  Sections B, C, D, E, F, G, H exactly as preregistered."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import ap_common as AP  # noqa: E402
import box_common as B  # noqa: E402
import t96_common as W  # noqa: E402
import t97_engine as E  # noqa: E402
import t97_phase3 as P3  # noqa: E402
import t97_wave1 as W1  # noqa: E402

M = E.markets(); INSTS = E.INSTS; OUTD = os.path.join(E.OUT, "corr1"); os.makedirs(OUTD, exist_ok=True)
KEYS = ["h6", "h12", "h1615"]; OUT = {}


def boot(v, cl, reps=2000, seed=7):
    ok = ~np.isnan(v); v, cl = v[ok], cl[ok]
    if len(v) < 10:
        return np.nan, np.nan
    u, inv = np.unique(cl, return_inverse=True); s = np.bincount(inv, v); c = np.bincount(inv); rng = np.random.default_rng(seed); out = np.empty(reps)
    for r in range(reps):
        i = rng.integers(0, len(u), len(u)); out[r] = s[i].sum() / c[i].sum()
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def years_pos(v, yr):
    ok = ~np.isnan(v); by = pd.Series(v[ok]).groupby(yr[ok]).mean(); return int((by > 0).sum()), int(by.notna().sum())


def summarize(label, parts, reps=2000):
    """parts: {inst: (values, dates, years)} -> per-instrument + pooled mean, CI, years."""
    rows = []
    for inst, (v, d, y) in parts.items():
        rows.append({"label": label, "instrument": inst, "n": int((~np.isnan(v)).sum()), "mean": float(np.nanmean(v)) if len(v) else np.nan})
    v = np.concatenate([p[0] for p in parts.values()]); d = np.concatenate([p[1] for p in parts.values()]); y = np.concatenate([p[2] for p in parts.values()])
    lo, hi = boot(v, d, reps); yp, yn = years_pos(v, y)
    rows.append({"label": label, "instrument": "POOLED", "n": int((~np.isnan(v)).sum()), "mean": float(np.nanmean(v)), "ci_lo": lo, "ci_hi": hi, "years_pos": yp, "years": yn})
    return rows


def first(mask):
    return mask & (np.cumsum(mask, 1) == 1)


# ------------------------------------------------------------------------------------------------ B
def section_b():
    L = pd.read_csv(os.path.join(E.OUT, "TEST97_RESEARCH_LEDGER.csv"))
    OUT["B"] = {"TOTAL_TEST97_LEDGER_ROWS": int(len(L)), "TOTAL_TEST97_DISTINCT_VARIANTS": int(L.candidate_id.str.split("|").str[0].nunique()),
                "TOTAL_TEST97_ML_CONFIGS": 0, "TOTAL_TEST97_GA_GENOMES": 0,
                "note": "each distinct definition normally yields ES / NQ / YM / RTY / POOLED rows; 570 are ledger rows, not distinct variants"}


# ------------------------------------------------------------------------------------------------ C
def section_c():
    rows = []; drop = {}
    ev = {}
    for i in INSTS:
        m = M[i]; pr = np.r_[np.nan, (np.nanmax(m.I.H, 1) - np.nanmin(m.I.L, 1))[:-1]]; win = (m.bidx >= 1) & (m.bidx <= 65)
        ev[i] = {k: first((m.c > m.open0[:, None] + k * pr[:, None]) & win) & m.valid & (m.bidx <= E.BMAX_COMMON) for k in (0.0, 0.1, 0.2, 0.3, 0.5, 0.75)}
    for k in (0.1, 0.2, 0.3, 0.5, 0.75):
        for key in KEYS:
            parts = {}; gross = {}; xa = {}; xb = {}; XA, XB = [], []
            for i in INSTS:
                m = M[i]; r = m.R[key]; e0 = ev[i][0.0] & ~np.isnan(r); ek = ev[i][k] & ~np.isnan(r)
                s0 = np.bincount(m.bidx[e0], r[e0], minlength=E.NB); c0 = np.bincount(m.bidx[e0], minlength=E.NB)
                ss, bb = np.where(ek); own = e0[ss, bb]                       # same-session k=0 event at the same bar (excluded from its null)
                num = s0[bb] - np.where(own, r[ss, bb], 0); den = c0[bb] - own.astype(int)
                fam = np.where(den > 0, num / np.maximum(den, 1), np.nan)
                x = r[ss, bb] - fam; drop[f"k{k}_{i}_{key}"] = int(np.isnan(fam).sum())
                parts[i] = (x, m.date[ss, bb], m.year[ss, bb]); gross[i] = float(np.nanmean(r[ss, bb]))
                va = r[ss, bb] - m.null("A", key, ek); vb = r[ss, bb] - m.null("B1", key, ek); XA.append(va); XB.append(vb)
                xa[i] = float(np.nanmean(va)) if len(ss) else np.nan; xb[i] = float(np.nanmean(vb)) if len(ss) else np.nan
            S = summarize(f"W3_V1_k{k}_{key}_familynull", parts)
            for srow in S:
                inst = srow["instrument"]
                srow.update({"k": k, "horizon": key, "gross_mean": gross.get(inst, np.nan), "xA": xa.get(inst, np.nan), "xB1": xb.get(inst, np.nan)})
            P = S[-1]; P["xA"] = float(np.nanmean(np.concatenate(XA))); P["xB1"] = float(np.nanmean(np.concatenate(XB)))
            P["gross_mean"] = float(np.nanmean(np.concatenate([M[i].R[key][ev[i][k]] for i in INSTS])))
            P["cost_atr"] = float(np.nanmean(np.concatenate([np.repeat(M[i].cost[:, None], E.NB, 1)[ev[i][k]] for i in INSTS])))
            P["CLUE"] = bool(P["ci_lo"] > 0 and P["years_pos"] >= 5 and P["gross_mean"] > P["cost_atr"])
            rows += S
    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUTD, "C_W3_V1_FAMILY_NULL.csv"), index=False)
    OUT["C"] = {"unmatched_dropped": drop, "any_CORRECTED_HISTORICAL_CLUE": bool(R.get("CLUE", pd.Series(dtype=bool)).fillna(False).any())}
    return R


# ------------------------------------------------------------------------------------------------ D
def w3v3_sessions(m):
    thrust = m.c > m.prevhi[60]; out = []
    for s in np.where(m.full)[0]:
        tb = np.where(thrust[s, :60])[0]
        if not len(tb):
            continue
        b0 = tb[0]; touched = False
        for b in range(b0 + 1, 66):
            if not touched and (m.l[s, b] <= m.ema20[s, b] or m.l[s, b] <= m.vwap[s, b]):
                touched = True; continue
            if touched and m.bull[s, b] and m.c[s, b] > m.h[s, b - 1]:
                out.append((s, b0, b)); break
    return out


def section_d():
    rows = []; res = {}
    for lab in ("own_h6", "own_h12", "own_h1615", "same_exit_pullback_h12", "same_exit_1615"):
        res[lab] = {}
    mfe = []
    for i in INSTS:
        m = M[i]; I = m.I; seq = w3v3_sessions(m); a = m.a
        S_ = np.array([q[0] for q in seq]); b0 = np.array([q[1] for q in seq]); b1 = np.array([q[2] for q in seq])
        ja, jb = 5 * (b0 + 1), 5 * (b1 + 1); okb = jb < B.J15
        S_, b0, b1, ja, jb = S_[okb], b0[okb], b1[okb], ja[okb], jb[okb]
        d, y = m.date[S_, 0], m.year[S_, 0]
        for key in ("h6", "h12", "h1615"):
            ra, rb = m.R[key][S_, b0], m.R[key][S_, b1]
            res[f"own_{key}"][i] = (rb - ra, d, y); rows.append({"instrument": i, "comparison": f"own_{key}", "n": int(np.sum(~np.isnan(rb - ra))),
                                                               "chase_mean": float(np.nanmean(ra)), "pullback_mean": float(np.nanmean(rb))})
        for lab, jx in (("same_exit_pullback_h12", jb + 60), ("same_exit_1615", np.full(len(jb), B.J15))):
            ok = jx <= B.J15; px = np.where(ok, I.FP[S_, np.minimum(jx, B.J15)], np.nan)
            ra = (px - I.FP[S_, ja]) / a[S_]; rb = (px - I.FP[S_, jb]) / a[S_]
            res[lab][i] = (rb - ra, d, y); rows.append({"instrument": i, "comparison": lab, "n": int(np.sum(~np.isnan(rb - ra))),
                                                        "chase_mean": float(np.nanmean(ra)), "pullback_mean": float(np.nanmean(rb))})
        mfe.append({"instrument": i, "sessions": len(S_), "chase_mfe60": float(np.nanmean(m.P["mfe60"][S_, b0])), "chase_mae60": float(np.nanmean(m.P["mae60"][S_, b0])),
                    "pullback_mfe60": float(np.nanmean(m.P["mfe60"][S_, b1])), "pullback_mae60": float(np.nanmean(m.P["mae60"][S_, b1]))})
    paired = []
    for lab, parts in res.items():
        paired += summarize(f"W3_V3_{lab}_pullback_minus_chase", parts)
    T = pd.DataFrame(rows); PD = pd.DataFrame(paired); MF = pd.DataFrame(mfe)
    T.to_csv(os.path.join(OUTD, "D_W3_V3_MEANS.csv"), index=False); PD.to_csv(os.path.join(OUTD, "D_W3_V3_PAIRED.csv"), index=False); MF.to_csv(os.path.join(OUTD, "D_W3_V3_PATH.csv"), index=False)
    pooled = PD[PD.instrument == "POOLED"].set_index("label")
    OUT["D"] = {"matched_sessions": int(MF.sessions.sum()), "paired_pooled": pooled[["n", "mean", "ci_lo", "ci_hi", "years_pos"]].to_dict("index")}
    return T, PD, MF


# ------------------------------------------------------------------------------------------------ E
def section_e():
    rows = []; info = []
    for cname, fn, lag in (("B_next_bull", lambda m: m.bull, 1), ("C_next_close_gt", lambda m: m.c > np.concatenate([m.c[:, :1], m.c[:, :-1]], 1), 1),
                           ("E_next_HH_HL", lambda m: (m.h > np.concatenate([m.h[:, :1], m.h[:, :-1]], 1)) & (m.l > np.concatenate([m.l[:, :1], m.l[:, :-1]], 1)), 1),
                           ("F_next_STRONG", lambda m: W1.strong(m), 1), ("D_two_bull", None, 2)):
        tparts = {"same_exit_conf_h12": {}, "same_exit_1615": {}}; iparts = {"h6": {}, "h12": {}}
        for i in INSTS:
            m = M[i]; I = m.I; base = W1.strong(m) & (m.c > m.prevhi[12])
            if cname == "D_two_bull":
                conf_at = W1.shift(base, 2) & m.bull & W1.shift(m.bull, 1); unconf_at = W1.shift(base, 2) & ~(m.bull & W1.shift(m.bull, 1))
            else:
                conf_at = W1.shift(base, 1) & fn(m); unconf_at = W1.shift(base, 1) & ~fn(m)
            ce = conf_at & m.valid & (m.bidx <= E.BMAX_COMMON); ue = unconf_at & m.valid & (m.bidx <= E.BMAX_COMMON)
            for key in ("h6", "h12"):                               # information: confirmed vs unconfirmed at the same decision minute
                vc, vu = m.R[key][ce], m.R[key][ue]
                iparts[key][i] = (np.r_[vc, vu], np.r_[m.date[ce], m.date[ue]], np.r_[np.ones(len(vc)), np.zeros(len(vu))])
            s, bc = np.where(ce); b0 = bc - lag                         # original breakout bar
            jo, jc = 5 * (b0 + 1), 5 * (bc + 1)
            for lab, jx in (("same_exit_conf_h12", jc + 60), ("same_exit_1615", np.full(len(jc), B.J15))):
                ok = (jx <= B.J15) & (jc < B.J15); px = np.where(ok, I.FP[s, np.minimum(jx, B.J15)], np.nan)
                ro = (px - I.FP[s, jo]) / m.a[s]; rc = (px - I.FP[s, jc]) / m.a[s]
                tparts[lab][i] = (rc - ro, m.date[s, bc], m.year[s, bc])
                rows.append({"confirm": cname, "instrument": i, "exit": lab, "n": int(np.sum(~np.isnan(rc - ro))), "orig_entry_mean": float(np.nanmean(ro)),
                             "conf_entry_mean": float(np.nanmean(rc))})
        for lab, parts in tparts.items():
            for r_ in summarize(f"M04_{cname}_{lab}_conf_minus_orig", parts):
                r_["confirm"] = cname; r_["exit"] = lab; info.append(r_)
        for key, parts in iparts.items():                            # information difference with clustered bootstrap of the difference
            v = np.concatenate([p[0] for p in parts.values()]); d = np.concatenate([p[1] for p in parts.values()]); g = np.concatenate([p[2] for p in parts.values()])
            ok = ~np.isnan(v); v, d, g = v[ok], d[ok], g[ok]; u, inv = np.unique(d, return_inverse=True)
            sc = np.bincount(inv, v * g); cc = np.bincount(inv, g); su = np.bincount(inv, v * (1 - g)); cu = np.bincount(inv, 1 - g)
            rng = np.random.default_rng(7); bs = []
            for _ in range(2000):
                ix = rng.integers(0, len(u), len(u)); bs.append(sc[ix].sum() / max(cc[ix].sum(), 1) - su[ix].sum() / max(cu[ix].sum(), 1))
            info.append({"label": f"M04_{cname}_INFO_{key}_confirmed_minus_unconfirmed", "instrument": "POOLED", "n": int(g.sum()), "n_unconf": int((1 - g).sum()),
                         "mean": float(v[g == 1].mean() - v[g == 0].mean()), "ci_lo": float(np.percentile(bs, 2.5)), "ci_hi": float(np.percentile(bs, 97.5)), "confirm": cname, "exit": key})
    T = pd.DataFrame(rows); I_ = pd.DataFrame(info)
    T.to_csv(os.path.join(OUTD, "E_M04_TIMING_MEANS.csv"), index=False); I_.to_csv(os.path.join(OUTD, "E_M04_INFO_TIMING.csv"), index=False)
    OUT["E"] = I_[I_.instrument == "POOLED"][["label", "n", "mean", "ci_lo", "ci_hi"]].to_dict("records")
    return T, I_


# ------------------------------------------------------------------------------------------------ F
def y2022(I, D, bk, d):
    y = np.asarray(I.sess.year == 2022); D22 = D[np.asarray(I.sess[D.s.values].year == 2022)] if len(D) else D
    pnl = float(d[y].sum()); exA = W.controls(I, D22, bk)["A"] * int(I.full.sum()) if len(D22) else 0.0
    matched = pnl - exA; eq = np.cumsum(d); i21 = np.where(np.asarray(I.sess <= pd.Timestamp("2021-12-31")))[0][-1]; lvl = eq[i21]
    after = np.where((np.arange(len(eq)) > np.where(y)[0][-1]) & (eq >= lvl))[0]
    dur = (D22.j_x - D22.j_in).clip(lower=0).sum() if len(D22) else 0
    return {"y2022_pnl": pnl, "y2022_matched_long_pnl": matched, "y2022_excess_A": exA, "y2022_loss_capture": (pnl / matched) if matched < 0 else np.nan,
            "y2022_maxdd": B.risk(d[y])["max_dd"], "y2022_worst_day": float(d[y].min()), "y2022_avg_exposure_contracts": float(dur / (y.sum() * B.J15)),
            "peak_exposure_contracts": "NOT_COMPUTED / VIRTUAL_DIAGNOSTIC_ONLY", "recovery_date": str(I.sess[after[0]].date()) if len(after) else "not recovered"}


def section_f():
    ctx = W.main_ctx(); Is = ctx["Is"]; rows = []; daily = {}
    for i in INSTS:
        m = M[i]; I = Is[i]; bk = AP.buckets(I); ev = P3.ft2(m); s, b = np.where(ev); j = 5 * (b + 1)
        common = int((ev & (m.bidx <= E.BMAX_COMMON)).sum()); allr = j < B.J15; strict = j + 60 <= B.J15; late = allr & ~strict
        pops = {"STRICT_X60": (strict, j + 60), "X60_CLIPPED_ALL": (allr, np.minimum(j + 60, B.J15)), "LATE_X60_CLIPPED": (late, np.minimum(j + 60, B.J15)),
                "X1615_ALL": (allr, np.full(len(j), B.J15)), "LATE_X1615": (late, np.full(len(j), B.J15)), "STRICT_X1615": (strict, np.full(len(j), B.J15))}
        for nm, (mask, jo) in pops.items():
            TR = pd.DataFrame({"s": s[mask], "j": j[mask], "s_out": s[mask], "j_out": jo[mask]}); TR = TR[TR.j_out > TR.j]
            D = W.simulate(I, TR); d = W.daily(I, D); d4 = W.daily(I, W.simulate(I, TR, cs=I.cs4))
            o = {"population": nm, "instrument": i, "trades": len(D), "avg_day": float(d[I.full].mean()), "usd_per_trade": float(D.net.mean()) if len(D) else np.nan,
                 "slip4_day": float(d4[I.full].mean()), "common_pop_events_b<=67": common, "all_rth_events": int(allr.sum()), "strict_x60_events": int(strict.sum()),
                 "late_excluded": int(late.sum())}
            if nm in ("STRICT_X60", "X1615_ALL"):
                o.update(y2022(I, D, bk, d)); daily[f"{nm}_{i}"] = d
            rows.append(o)
    T = pd.DataFrame(rows)
    full = Is["ES"].full; main = ctx["main"]; port = []
    for nm in ("STRICT_X60", "X1615_ALL"):
        x = sum(daily[f"{nm}_{i}"] for i in INSTS); rm, rc = B.risk(main[full]), B.risk((main + x)[full]); am = full & (x != 0); bot = full & (main <= np.percentile(main[full], 5))
        port.append({"label": f"FT2_{nm}_4INDEX (VIRTUAL_ADDITIVE_DIAGNOSTIC - not capacity valid)", "standalone_avg_day": float(x[full].mean()),
                     "main_plus_avg_day": rc["avg_day"], "main_plus_maxdd": rc["max_dd"], "main_plus_worst": rc["worst_day"], "main_plus_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"],
                     "corr": float(np.corrcoef(x[full], main[full])[0, 1]), "loss_jaccard": float(((x < 0) & (main < 0) & am).sum() / max(((x < 0) | (main < 0))[am].sum(), 1)),
                     "bottom5_overlap": float(((x < 0) & bot).sum() / max(bot.sum(), 1)), "active_days": int(am.sum()), "peak_MES_MNQ_MYM_M2K": "NOT_COMPUTED / VIRTUAL_DIAGNOSTIC_ONLY"})
    PT = pd.DataFrame(port); T.to_csv(os.path.join(OUTD, "F_FT2_POPULATION_AUDIT.csv"), index=False); PT.to_csv(os.path.join(OUTD, "F_FT2_VIRTUAL_PORTFOLIO.csv"), index=False)
    OUT["F"] = {"explanation": "Wave-2 EVENT_EDGE used the common population (confirmation bar <= 67, all bar horizons complete): 431 pooled; Phase 3 used "
                               "every RTH FT2 event with entry before 16:15 (no bar cap): ~602; Phase-3 'X60' clipped late events at 16:15 -> relabelled X60_CLIPPED",
                "counts": T[T.population == "STRICT_X60"][["instrument", "common_pop_events_b<=67", "all_rth_events", "strict_x60_events", "late_excluded"]].to_dict("records")}
    return T, PT


# ------------------------------------------------------------------------------------------------ G
def causal_kbar(m, k=2, warm=120):
    n = m.n; cf = pd.Series(m.c.ravel()); hf = pd.Series(m.h.ravel()); lf = pd.Series(m.l.ravel())
    disp = ((cf - cf.shift(k)).values.reshape(n, E.NB)) / m.a[:, None]; rg = ((hf.rolling(k).max() - lf.rolling(k).min()).values.reshape(n, E.NB)) / m.a[:, None]
    dd = np.full((n, E.NB), -1); rt = np.full((n, E.NB), -1); per = m.I.sess.to_period("M")
    for mo in per.unique():
        rows = np.where(per == mo)[0]; prior = np.arange(n) < rows[0]
        if prior.sum() < warm:
            continue
        v = m.valid & prior[:, None]
        dq = np.nanpercentile(disp[v], np.linspace(10, 90, 9)); rq = np.nanpercentile(rg[v], [100 / 3, 200 / 3])
        dd[rows] = np.digitize(np.nan_to_num(disp[rows]), dq); rt[rows] = np.digitize(np.nan_to_num(rg[rows]), rq)
    return dd, rt


def null_custom(m, key, ev, dd, rt):
    r = m.R[key]; base = m.valid & ~np.isnan(r) & (dd >= 0); cell = ((m.year * 10 + m.tod) * 10 + dd) * 10 + rt; pool = base & ~ev
    s = pd.Series(r[pool]).groupby(cell[pool]).agg(["sum", "count"]); mm = (s["sum"] / s["count"]).where(s["count"] >= 20)
    return pd.Series(mm).reindex(cell[ev]).values


def section_g():
    rows = []
    for method in ("OLD_full_sample_edges", "CAUSAL_BIN_EDGE_MATCHING_SENSITIVITY"):
        for key in KEYS:
            parts = {}
            for i in INSTS:
                m = M[i]; ev = P3.ft2(m) & (m.bidx <= E.BMAX_COMMON)
                if method.startswith("OLD"):
                    x = m.R[key][ev] - m.null("B2", key, ev)
                else:
                    dd, rt = causal_kbar(m); ev = ev & (dd >= 0); x = m.R[key][ev] - null_custom(m, key, ev, dd, rt)
                parts[i] = (x, m.date[ev], m.year[ev])
            for r_ in summarize(f"FT2_{method}_{key}", parts, reps=5000):
                r_["method"] = method; r_["horizon"] = key; rows.append(r_)
    T = pd.DataFrame(rows); T.to_csv(os.path.join(OUTD, "G_FT2_NULL_ROBUSTNESS.csv"), index=False)
    c = T[(T.instrument == "POOLED") & (T.method.str.startswith("CAUSAL")) & (T.horizon == "h12")].iloc[0]
    OUT["G"] = {"pooled": T[T.instrument == "POOLED"][["method", "horizon", "n", "mean", "ci_lo", "ci_hi", "years_pos"]].to_dict("records"),
                "DOWNGRADE": bool(not (c.ci_lo > 0 and c.years_pos >= 5))}
    return T


def main():
    section_b(); C = section_c(); D = section_d(); Et = section_e(); F = section_f(); G = section_g()
    OUT["H"] = {"RECOVERY_STACK": "REJECT on the FT2 initial population (ADD1 < 0 in ES / NQ / YM / RTY); no ADD2 / ADD3 research",
                "standing_rule": "if ADD1 <= 0 -> stop deeper stacking automatically",
                "blind_DCA_note": "existing code used average - 0.5 ATR x units for deeper adds (prereg: average - 0.5 ATR per add) -> deeper blind-DCA outputs NOT USABLE"}
    json.dump(OUT, open(os.path.join(OUTD, "CORR1_RESULTS.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(json.dumps(OUT["B"])); print(C[C.instrument == "POOLED"][["k", "horizon", "n", "gross_mean", "xA", "xB1", "mean", "ci_lo", "ci_hi", "years_pos", "cost_atr", "CLUE"]].round(4).to_string())
    print(C[C.instrument != "POOLED"][["k", "horizon", "instrument", "n", "mean"]].pivot_table(index=["k", "horizon"], columns="instrument", values="mean").round(4).to_string())
    print(D[1].round(4).to_string()); print(D[2].round(4).to_string())
    print(Et[1][Et[1].instrument == "POOLED"].round(4).to_string())
    print(F[0].round(2).to_string()); print(F[1].round(4).to_string()); print(G[G.instrument == "POOLED"].round(4).to_string())


if __name__ == "__main__":
    main()
