"""TEST98_PRECONFIRM_PATH_QUALITY Phase 1 event study (prereg commit 12d9765, reports/TEST98_PLUS/TEST98_PHASE1_PREREGISTRATION.md).
Fresh N=12 close-confirmed breakouts on ES / NQ / YM / RTY; pre-confirmation path features (bars <= b only); causal quintile response curves vs
the within-breakout magnitude-matched family null F; follow-through as a TARGET-only diagnostic."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E  # noqa: E402
import t97_wave1 as W1  # noqa: E402

OUT = os.path.join(E.B.LAB, "out", "t98"); os.makedirs(OUT, exist_ok=True)
REP = os.path.join(E.B.LAB, "reports", "TEST98_PLUS"); os.makedirs(REP, exist_ok=True)
M = E.markets(); INSTS = E.INSTS; NB = E.NB
HK = ["h2", "h3", "h4", "h6", "h9", "h12", "h1615"]; PRIMARY = ["h6", "h12"]; WARM = 120; REPS = 2000
FAMILY = {}


@njit(cache=True)
def _damage(c, h, l, o, a_flat, W):
    n = c.shape[0]; out = np.full((n, 5), np.nan)
    for i in range(W, n):
        rc = -1e18; rh = -1e18; ddc = 0.0; ddl = 0.0; bear = 0.0; path = 0.0; below = 0.0
        for t in range(i - W + 1, i + 1):
            if c[t] > rc:
                rc = c[t]
            if h[t] > rh:
                rh = h[t]
            ddc = max(ddc, rc - c[t]); ddl = max(ddl, rh - l[t])
            if c[t] < o[t]:
                bear = max(bear, o[t] - c[t])
            path += abs(c[t] - c[t - 1])
            if c[t] < 0.5 * (h[t - 1] + l[t - 1]):
                below += 1.0
        net = abs(c[i] - c[i - W]); a = a_flat[i]
        out[i, 0] = ddc / a; out[i, 1] = ddl / a; out[i, 2] = bear / a; out[i, 3] = path / net if net > 0 else np.nan; out[i, 4] = below
    return out


def runmax(x, W):
    """longest run of True within the trailing W bars (flat series)."""
    run = np.zeros(len(x)); r = 0
    for i, v in enumerate(x):
        r = r + 1 if v else 0; run[i] = r
    return pd.Series(run).rolling(W, min_periods=1).max().values          # a run crossing the window start is capped below by construction


def features(m):
    n = m.n; sh = (n, NB)
    c, h, l, o = (pd.Series(x.ravel()) for x in (m.c, m.h, m.l, m.o)); a = np.repeat(m.a, NB)
    dc = c.diff().abs(); F = {}
    for k in (3, 6, 12):
        F[f"PQ1_ER{k}"] = (np.abs(c - c.shift(k)) / dc.rolling(k).sum()).values
        F[f"PQ1_disp{k}"] = ((c - c.shift(k)) / a).values
        F[f"PQ2_bull_frac{k}"] = (c > o).astype(float).rolling(k).mean().values
        F[f"PQ2_hclose_frac{k}"] = (c > c.shift(1)).astype(float).rolling(k).mean().values
        F[f"PQ2_hlow_frac{k}"] = (l > l.shift(1)).astype(float).rolling(k).mean().values
        F[f"PQ2_upper_frac{k}"] = (((c - l) / (h - l).replace(0, np.nan)) >= 0.5).astype(float).rolling(k).mean().values
    F["PQ2_bullrun12"] = runmax((c > o).values, 12); F["PQ2_hlrun12"] = runmax((l > l.shift(1)).values, 12)
    D = _damage(c.values, h.values, l.values, o.values, a, 12)
    for i, nm in enumerate(("PQ3_close_dd12", "PQ3_low_dd12", "PQ3_max_bear_body12", "PQ3_path_over_net12", "PQ3_below_mid12")):
        F[nm] = D[:, i]
    F = {k: v.reshape(sh) for k, v in F.items()}
    prevrange = np.r_[np.nan, (np.nanmax(m.I.H, 1) - np.nanmin(m.I.L, 1))[:-1]]
    F["PQ4_overshoot"] = (m.c - m.prevhi[12]) / m.a[:, None]; F["PQ4_range_atr5"] = m.rng_atr5; F["PQ4_body_pct"] = m.body_pct; F["PQ4_close_pos"] = m.cpos
    F["PQ4_vwap_dist"] = (m.c - m.vwap) / m.a[:, None]; F["PQ4_open_dist"] = (m.c - m.open0[:, None]) / m.a[:, None]
    F["PQ4_open_dist_over_pdr"] = (m.c - m.open0[:, None]) / prevrange[:, None]
    above_v = (m.c > m.vwap).astype(float); above_o = (m.c > m.open0[:, None]).astype(float); cnt = np.minimum(np.arange(NB) + 1, 12)[None, :]
    rs = lambda x: pd.DataFrame(x.T).rolling(12, min_periods=1).sum().T.values
    F["PQ5_vwap_share12"] = rs(above_v) / cnt; F["PQ5_open_share12"] = rs(above_o) / cnt
    F["PQ5_open_share_session"] = np.cumsum(above_o, 1) / (np.arange(NB) + 1)[None, :]
    L = m.prevhi[12]; band = 0.25 * m.atr5
    hf, cf = pd.Series(m.h.ravel()), pd.Series(m.c.ravel()); Lf, bf = L.ravel(), band.ravel()
    probes = np.zeros(n * NB); near = np.zeros(n * NB)
    for q in range(1, 13):
        hq, cq = hf.shift(q).values, cf.shift(q).values
        probes += ((hq >= Lf - bf) & (cq <= Lf)).astype(float); near += (cq >= Lf - bf).astype(float)
    F["PQ5_failed_probes12"] = probes.reshape(sh); F["PQ5_near_high_closes12"] = near.reshape(sh)
    F["_disp12"] = F["PQ1_disp12"]
    hi12 = pd.Series(m.h.ravel()).rolling(12).max().values; lo12 = pd.Series(m.l.ravel()).rolling(12).min().values
    F["_range12"] = ((hi12 - lo12).reshape(sh)) / m.a[:, None]
    return F


def fresh_events(m):
    brk = m.c > m.prevhi[12]; prev = np.concatenate([np.zeros((m.n, 1), bool), brk[:, :-1]], 1)
    flat_prev = np.r_[False, brk.ravel()[:-1]].reshape(brk.shape)                     # chained: bar 0 looks at the prior session's last bar
    return brk & ~flat_prev & m.valid & (m.bidx >= 1) & (m.bidx <= E.BMAX_COMMON)


def causal_bins(m, ev, x, q):
    """per-instrument quantile bins with edges from events in sessions strictly before the event's month; warm-up sessions -> -1."""
    per = m.I.sess.to_period("M"); out = np.full(x.shape, -1); ok_s = np.arange(m.n) >= WARM
    for mo in per.unique():
        rows = np.where(per == mo)[0]; prior = np.arange(m.n) < rows[0]
        v = x[ev & prior[:, None]]; v = v[~np.isnan(v)]
        if not ok_s[rows[0]] or len(v) < 50:
            continue
        edges = np.nanpercentile(v, np.linspace(0, 100, q + 1)[1:-1])
        sub = x[rows]; b = np.digitize(np.nan_to_num(sub, nan=np.nan), edges); b = np.where(np.isnan(sub), -1, b); out[rows] = b
    return out


def family_null(m, ev, F, key):
    r = m.R[key]; d_t = causal_bins(m, ev, F["_disp12"], 3); r_t = causal_bins(m, ev, F["_range12"], 3); o_t = causal_bins(m, ev, F["PQ4_overshoot"], 3)
    tod3 = np.digitize(m.bidx, [12, 54]); ok = ev & ~np.isnan(r) & (d_t >= 0) & (r_t >= 0) & (o_t >= 0)
    levels = [((((m.year * 10 + m.vt) * 10 + tod3) * 10 + d_t) * 10 + r_t) * 10 + o_t,
              (((m.vt * 10 + tod3) * 10 + d_t) * 10 + r_t) * 10 + o_t, ((tod3 * 10 + d_t) * 10 + r_t) * 10 + o_t]
    null = np.full(r.shape, np.nan); lev = np.full(r.shape, -1)
    for li, cell in enumerate(levels):
        s = pd.Series(r[ok]).groupby(cell[ok]).agg(["sum", "count"])
        cs = s["sum"].reindex(cell[ok]).values; cn = s["count"].reindex(cell[ok]).values
        loo = (cs - r[ok]) / (cn - 1); good = (cn - 1 >= 10) & np.isnan(null[ok])
        tmp = null[ok]; tl = lev[ok]; tmp[good] = loo[good]; tl[good] = li; null[ok] = tmp; lev[ok] = tl
    return null, lev, ok


def boot_diff(v, g, cl, reps=REPS, seed=7):
    """date-clustered bootstrap CI of mean(v | g==1) - mean(v | g==0)."""
    ok = ~np.isnan(v); v, g, cl = v[ok], g[ok], cl[ok]
    u, inv = np.unique(cl, return_inverse=True)
    s1 = np.bincount(inv, v * g); c1 = np.bincount(inv, g); s0 = np.bincount(inv, v * (1 - g)); c0 = np.bincount(inv, 1 - g)
    rng = np.random.default_rng(seed); out = np.empty(reps)
    for r in range(reps):
        i = rng.integers(0, len(u), len(u)); out[r] = s1[i].sum() / max(c1[i].sum(), 1) - s0[i].sum() / max(c0[i].sum(), 1)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def main():
    FE = {}; EV = {}; XF = {}; LEV = {}
    for i in INSTS:
        m = M[i]; F = features(m); ev = fresh_events(m) & (np.arange(m.n)[:, None] >= WARM); FE[i] = F; EV[i] = ev
        for key in HK:
            nul, lev, ok = family_null(m, ev, F, key); XF[(i, key)] = m.R[key] - nul; LEV[(i, key)] = lev
    # ---------------- base event table (nulls A / C and path statistics) + null-F excess
    rows, _ = E.study("T98_FRESH_BRK12", EV, nulls=("A", "C"), horizons=HK)
    for r_ in rows:
        inst = r_["instrument"]
        for key in HK:
            if inst == "POOLED":
                v = np.concatenate([XF[(k, key)][EV[k]] for k in INSTS]); r_[f"{key}_xF"] = float(np.nanmean(v))
            else:
                r_[f"{key}_xF"] = float(np.nanmean(XF[(inst, key)][EV[inst]]))
    BASE = pd.DataFrame(rows)
    levshare = {key: pd.Series(np.concatenate([LEV[(k, key)][EV[k]] for k in INSTS])).value_counts(normalize=True).sort_index().to_dict() for key in PRIMARY}
    # ---------------- response curves
    feats = [f for f in FE[INSTS[0]] if not f.startswith("_")]
    curve_rows = []; verdict = []; ledger = []
    nxt = {}
    for i in INSTS:
        m = M[i]; st = W1.strong(m); lab = np.full((m.n, NB), np.nan)
        nb_bull, nb_body = np.roll(m.bull, -1, 1), np.roll(m.body_pct, -1, 1); nb_st = np.roll(st, -1, 1)
        lab = np.where(~nb_bull, 0, np.where(nb_body < 0.5, 1, np.where(nb_st, 3, 2))).astype(float); lab[:, -1] = np.nan; nxt[i] = lab
    for f in feats:
        bins = {i: causal_bins(M[i], EV[i], FE[i][f], 5) for i in INSTS}
        res = {"feature": f, "family": f.split("_")[0]}
        for key in HK:
            per_bin = []
            for bq in range(5):
                vals = [XF[(i, key)][EV[i] & (bins[i] == bq)] for i in INSTS]; v = np.concatenate(vals)
                gross = np.concatenate([M[i].R[key][EV[i] & (bins[i] == bq)] for i in INSTS])
                ps = np.concatenate([(nxt[i] == 3)[EV[i] & (bins[i] == bq)] for i in INSTS]); pb = np.concatenate([(nxt[i] == 0)[EV[i] & (bins[i] == bq)] for i in INSTS])
                row = {"feature": f, "horizon": key, "bin": bq, "n": int((~np.isnan(v)).sum()), "xF": float(np.nanmean(v)) if len(v) else np.nan,
                       "gross": float(np.nanmean(gross)) if len(gross) else np.nan, "p_next_strong": float(ps.mean()) if len(ps) else np.nan,
                       "p_next_bear": float(pb.mean()) if len(pb) else np.nan, **{f"xF_{i}": float(np.nanmean(x_)) if len(x_) else np.nan for i, x_ in zip(INSTS, vals)}}
                curve_rows.append(row); per_bin.append(row)
                for i, x_ in zip(INSTS, vals):
                    ledger.append({"variant": f"{f}|q{bq}", "horizon": key, "instrument": i, "n": int((~np.isnan(x_)).sum()), "xF": float(np.nanmean(x_)) if len(x_) else np.nan})
                ledger.append({"variant": f"{f}|q{bq}", "horizon": key, "instrument": "POOLED", "n": row["n"], "xF": row["xF"]})
            if key in PRIMARY:
                means = [r_["xF"] for r_ in per_bin if r_["n"] > 0 and r_["xF"] == r_["xF"]]
                rho = spearmanr(range(len(means)), means).correlation if len(means) >= 3 else np.nan
                top, bot = max(b_ for b_ in range(5) if per_bin[b_]["n"] > 0), min(b_ for b_ in range(5) if per_bin[b_]["n"] > 0)
                v = np.concatenate([XF[(i, key)][EV[i] & np.isin(bins[i], [top, bot])] for i in INSTS])
                g = np.concatenate([(bins[i][EV[i] & np.isin(bins[i], [top, bot])] == top).astype(float) for i in INSTS])
                cl = np.concatenate([M[i].date[EV[i] & np.isin(bins[i], [top, bot])] for i in INSTS]); yr = np.concatenate([M[i].year[EV[i] & np.isin(bins[i], [top, bot])] for i in INSTS])
                lo, hi = boot_diff(v, g, cl); diff = float(np.nanmean(v[g == 1]) - np.nanmean(v[g == 0]))
                ys = [np.nanmean(v[(yr == y) & (g == 1)]) - np.nanmean(v[(yr == y) & (g == 0)]) for y in np.unique(yr)]
                ysame = int(sum(np.sign(y_) == np.sign(diff) for y_ in ys if y_ == y_))
                isame = int(sum(np.sign(per_bin[top][f"xF_{i}"] - per_bin[bot][f"xF_{i}"]) == np.sign(diff) for i in INSTS))
                coherent = bool(abs(rho) >= 0.9 and (lo > 0 or hi < 0) and ysame >= 5 and isame >= 3)
                best = max(per_bin, key=lambda r_: r_["xF"] if r_["n"] > 0 and r_["xF"] == r_["xF"] else -9)
                # follow-through target diagnostic (top vs bottom P(next STRONG))
                vs = np.concatenate([(nxt[i] == 3)[EV[i] & np.isin(bins[i], [top, bot])].astype(float) for i in INSTS]); l2, h2 = boot_diff(vs, g, cl)
                res.update({f"{key}_rho": rho, f"{key}_top_minus_bottom": diff, f"{key}_ci_lo": lo, f"{key}_ci_hi": hi, f"{key}_years_same": ysame,
                            f"{key}_inst_same": isame, f"{key}_COHERENT": coherent, f"{key}_best_bin": best["bin"], f"{key}_best_xF": best["xF"],
                            f"{key}_best_gross": best["gross"], f"{key}_pstrong_diff": float(np.nanmean(vs[g == 1]) - np.nanmean(vs[g == 0])), f"{key}_pstrong_ci": (l2, h2)})
        verdict.append(res)
    C = pd.DataFrame(curve_rows); V = pd.DataFrame(verdict); Lg = pd.DataFrame(ledger)
    C.to_csv(os.path.join(OUT, "P1_RESPONSE_CURVES.csv"), index=False); V.to_csv(os.path.join(OUT, "P1_FEATURE_VERDICTS.csv"), index=False)
    Lg.to_csv(os.path.join(OUT, "TEST98_RESEARCH_LEDGER.csv"), index=False); BASE.to_csv(os.path.join(OUT, "P1_BASE_EVENT.csv"), index=False)
    cost = float(BASE[BASE.instrument == "POOLED"].cost_atr.iloc[0])
    json.dump({"levels_share": levshare, "cost_atr_pooled": cost, "n_features": len(feats)}, open(os.path.join(OUT, "P1_META.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
    b = BASE[["instrument", "n_events"] + [f"{k}_mean" for k in HK] + ["h6_xA", "h12_xA", "h12_xC", "h6_xF", "h12_xF", "h1615_xF", "cost_atr", "mfe60", "mae60", "bar050", "newhigh60"]]
    print(b.round(4).to_string()); print(levshare)
    vc = ["feature", "h6_rho", "h6_top_minus_bottom", "h6_ci_lo", "h6_ci_hi", "h6_COHERENT", "h12_rho", "h12_top_minus_bottom", "h12_ci_lo", "h12_ci_hi", "h12_years_same",
          "h12_inst_same", "h12_COHERENT", "h12_best_bin", "h12_best_xF", "h12_best_gross", "h12_pstrong_diff"]
    print(V[vc].round(4).to_string())


if __name__ == "__main__":
    main()
