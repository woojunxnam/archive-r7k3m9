"""TEST45 Phases 3-7 + 16 (descriptive, predeclared broad buckets; nothing optimised):
3 late-RTH features vs locked overnight target, 4 gap-down rebound (H1/H2/H5), 5 opening flush (H3/H4),
6 gap x flush matrix, 7 open inventory management, 16 ES/NQ cross-index information."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_feat as F  # noqa: E402
import t45_sim as S  # noqa: E402

OUT = os.path.join(C.T45, "morning"); os.makedirs(OUT, exist_ok=True)
g = C.g
# predeclared buckets (addendum/prompt; not searched)
GAP_BUCKETS = {"atr": [np.inf, 0.25, 0.0, -0.25, -0.5, -0.75, -1.0, -1.5, -np.inf],
               "range": [np.inf, 0.25, 0.0, -0.25, -0.5, -0.75, -1.0, -1.5, -np.inf],
               "sigma": [np.inf, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0, -3.0, -np.inf],
               "pct": [np.inf, 0.25, 0.0, -0.25, -0.5, -0.75, -1.0, -1.5, -np.inf]}
FLUSH_BUCKETS = [0.001, -0.15, -0.3, -0.5, -0.8, -np.inf]          # selloff = (low of window - open)/ATR
HORIZONS = {"+15m": 15, "+30m": 30, "+60m": 60, "+120m": 120, "to 12:00": "12:00", "to 15:00": "15:00", "to 16:00 close": "16:00"}
WINDOWS = [5, 15, 30, 60, 90]


def exit_idx(j_fill, h):
    return min(j_fill + h - 1, g("16:00")) if isinstance(h, int) else g(h)


def bucket_labels(edges):
    return [f"({edges[i + 1]:+.2f},{edges[i]:+.2f}]" for i in range(len(edges) - 1)]


def cut(x, edges):
    lab = bucket_labels(edges)
    idx = np.full(len(x), -1)
    for i in range(len(edges) - 1):
        idx[(x <= edges[i]) & (x > edges[i + 1])] = i
    return idx, lab


def path_stats(pn, FP, j_fill, ref_price, gap_pts, mask):
    """MFE/MAE to 16:00 and recovery statistics for longs filled at j_fill (rows where mask)."""
    e = g("16:00")
    ent = FP[:, j_fill]
    H = pn.H[:, j_fill:e + 1]; L = pn.L[:, j_fill:e + 1]
    Hc = np.fmax.accumulate(np.where(np.isnan(H), -np.inf, H), 1)
    o = {}
    a = pn.atr
    o["MFE_atr"] = np.nanmean(((np.nanmax(H, 1) - ent) / a)[mask])
    o["MAE_atr"] = np.nanmean(((np.nanmin(L, 1) - ent) / a)[mask])
    o["p_touch_prior_ref"] = np.nanmean((np.nanmax(H, 1) >= ref_price)[mask])
    for f in (0.25, 0.5, 0.75, 1.0):
        tgt = pn.open + f * np.abs(gap_pts)
        hit = Hc >= tgt[:, None]
        rec = hit.any(1)
        o[f"p_recover_{int(f * 100)}%_gap"] = np.nanmean(rec[mask]) if mask.any() else np.nan
        if f == 0.5:
            t = np.where(rec, hit.argmax(1), np.nan)
            o["median_min_to_50%"] = np.nanmedian(t[mask & rec]) if (mask & rec).any() else np.nan
            # worst excursion before 50% recovery (ATR)
            wx = []
            for s in np.where(mask & rec)[0]:
                k = int(t[s]); wx.append((np.nanmin(L[s, : k + 1]) - ent[s]) / a[s])
            o["mean_worst_exc_before_50%_atr"] = np.nanmean(wx) if wx else np.nan
    return o


def fwd_table(pn, FP, j_fill, mask, cs_pts):
    o = {}
    for hn, h in HORIZONS.items():
        r = (pn.Cf[:, exit_idx(j_fill, h)] - FP[:, j_fill])
        x = r[mask & ~np.isnan(r)]; z = (r / pn.atr)[mask & ~np.isnan(r)]
        o[f"{hn}_atr"] = z.mean() if len(z) else np.nan
        o[f"{hn}_t"] = z.mean() / z.std() * np.sqrt(len(z)) if len(z) > 2 and z.std() > 0 else np.nan
        o[f"{hn}_net$"] = (x.mean() - cs_pts) * 1.0 if len(x) else np.nan
    return o


def gap_study(P, sims):
    rows = []
    for sm in sims:
        pn = sm.pn; FP = sm.FP; pv = sm.pv
        cs_pts = 2 * C.cost_side(sm.k) / pv
        jf = 1                                                         # decision 09:31 (open known) -> fill 09:32
        for kind in ("lock", "cash"):
            ref = pn.p_lock if kind == "lock" else pn.p_cash
            gp = pn.gap_lock if kind == "lock" else pn.gap_cash
            for norm, edges in GAP_BUCKETS.items():
                x = C.normalise(gp, norm, pn, ref)
                idx, lab = cut(x, edges)
                for b, lb in enumerate(lab):
                    m = (idx == b) & ~np.isnan(FP[:, jf])
                    if m.sum() == 0:
                        continue
                    o = {"inst": pn.inst, "gap": f"GAP_{kind.upper()}", "norm": norm, "bucket": lb, "n": int(m.sum())}
                    o.update(fwd_table(pn, FP, jf, m, cs_pts))
                    o = {k: (v * pv if k.endswith("net$") else v) for k, v in o.items()}
                    o.update(path_stats(pn, FP, jf, ref, gp, m))
                    rows.append(o)
    return pd.DataFrame(rows)


def flush_study(P, sims):
    rows = []
    for sm in sims:
        pn = sm.pn; FP = sm.FP; pv = sm.pv
        cs_pts = 2 * C.cost_side(sm.k) / pv
        gl = pn.gap_lock / pn.atr
        for w in WINDOWS:
            f = F.morning(pn, w); jf = F.decision_fill(w)
            idx, lab = cut(f["selloff_w"], FLUSH_BUCKETS)
            sets = {f"selloff {lb}": idx == b for b, lb in enumerate(lab)}
            sets.update({"A flat/up gap (>=-0.1) + flush (<=-0.3)": (gl >= -0.1) & (f["selloff_w"] <= -0.3),
                         "B down gap (<=-0.5) + stable open (>-0.15)": (gl <= -0.5) & (f["selloff_w"] > -0.15),
                         "C down gap (<=-0.5) + further flush (<=-0.3)": (gl <= -0.5) & (f["selloff_w"] <= -0.3),
                         "D extreme gap (<=-1.0) + extreme flush (<=-0.5)": (gl <= -1.0) & (f["selloff_w"] <= -0.5),
                         "E flush (<=-0.3) + reclaim >=50%": (f["selloff_w"] <= -0.3) & (f["reclaim_frac"] >= 0.5),
                         "E' flush (<=-0.3) + no reclaim (<25%)": (f["selloff_w"] <= -0.3) & (f["reclaim_frac"] < 0.25),
                         "ALL sessions": np.ones(pn.n, bool)})
            for nm, m in sets.items():
                m = m & ~np.isnan(FP[:, jf]) & ~np.isnan(gl)
                if m.sum() < 5:
                    rows.append({"inst": pn.inst, "window": w, "state": nm, "n": int(m.sum())}); continue
                o = {"inst": pn.inst, "window": w, "state": nm, "n": int(m.sum())}
                o.update(fwd_table(pn, FP, jf, m, cs_pts))
                o = {k: (v * pv if k.endswith("net$") else v) for k, v in o.items()}
                r = pn.Cf[:, g("16:00")]
                o["p_close_above_open"] = np.nanmean((r > pn.open)[m])
                o["p_close_above_prior_lock"] = np.nanmean((r > pn.p_lock)[m])
                o.update(path_stats(pn, FP, jf, pn.p_lock, np.minimum(pn.gap_lock, 0) + (pn.runlow[:, max(w - 1, 0)] - pn.open), m))
                rows.append(o)
    return pd.DataFrame(rows)


GB = [np.inf, -0.2, -0.5, -1.0, -np.inf]
FB = [0.001, -0.15, -0.35, -0.6, -np.inf]


def matrix_study(P, sims, w=30):
    rows = []
    for sm in sims:
        pn = sm.pn; FP = sm.FP
        f = F.morning(pn, w); jf = F.decision_fill(w)
        gi, gl = cut(pn.gap_lock / pn.atr, GB); fi, fl = cut(f["selloff_w"], FB)
        y = (pn.Cf[:, g("16:00")] - FP[:, jf]) / pn.atr
        ok = ~np.isnan(y) & (gi >= 0) & (fi >= 0)
        half = np.arange(pn.n) < pn.n // 2
        for a in range(len(gl)):
            for b in range(len(fl)):
                m = ok & (gi == a) & (fi == b)
                rows.append({"inst": pn.inst, "gap_bin": gl[a], "flush30_bin": fl[b], "n": int(m.sum()),
                             "mean_to_close_atr": y[m].mean() if m.sum() else np.nan,
                             "t": y[m].mean() / y[m].std() * np.sqrt(m.sum()) if m.sum() > 2 else np.nan,
                             "first_half_mean": y[m & half].mean() if (m & half).sum() else np.nan,
                             "second_half_mean": y[m & ~half].mean() if (m & ~half).sum() else np.nan,
                             "min_sample_ok(>=20)": bool(m.sum() >= 20)})
        # variance explained (eta^2, df-adjusted) 1D vs 2D
        yy = y[ok]
        for nm, lab in (("gap only", gi[ok]), ("flush only", fi[ok]), ("gap x flush", gi[ok] * 10 + fi[ok])):
            ss_t = ((yy - yy.mean()) ** 2).sum()
            grp = pd.Series(yy).groupby(lab)
            ss_b = (grp.count() * (grp.mean() - yy.mean()) ** 2).sum()
            k = grp.ngroups
            rows.append({"inst": pn.inst, "gap_bin": "ETA2", "flush30_bin": nm, "n": len(yy), "mean_to_close_atr": ss_b / ss_t,
                         "t": (ss_b / ss_t) - (k - 1) / (len(yy) - 1)})
        # total displacement (prior lock -> opening-window low)
        di, dl = cut(f["disp_total"], [np.inf, -0.25, -0.75, -1.25, -2.0, -np.inf])
        for a, lb in enumerate(dl):
            m = ok & (di == a)
            rows.append({"inst": pn.inst, "gap_bin": "TOTAL_DISPLACEMENT", "flush30_bin": lb, "n": int(m.sum()),
                         "mean_to_close_atr": y[m].mean() if m.sum() else np.nan,
                         "t": y[m].mean() / y[m].std() * np.sqrt(m.sum()) if m.sum() > 2 else np.nan})
    return pd.DataFrame(rows)


def inventory_study(P, sims):
    """existing overnight long (1 contract, carried from the 16:14 lock) - value of actions at the next RTH open,
    relative to EXIT at the open print (pre-planned).  All numbers $ per contract, net of the incremental cost."""
    rows = []
    for sm in sims:
        pn = sm.pn; FP = sm.FP; pv = sm.pv; cs = C.cost_side(sm.k)
        gl = pn.gap_lock / pn.atr
        states = {"favorable gap (>+0.25)": gl > 0.25, "neutral (-0.25..+0.25]": (gl <= 0.25) & (gl > -0.25),
                  "adverse (-0.75..-0.25]": (gl <= -0.25) & (gl > -0.75), "extreme adverse (<=-0.75)": gl <= -0.75,
                  "ALL": ~np.isnan(gl)}
        op = FP[:, 0]
        acts = {}
        for w in (1, 5, 15, 30, 60):
            acts[f"KEEP -> exit after {w}m"] = (FP[:, w] - op) * pv                     # delaying the exit: no extra cost
        for t in ("12:00", "15:00", "16:00"):
            acts[f"KEEP -> exit {t}"] = (FP[:, g(t)] - op) * pv
        for w in (1, 15, 30):
            acts[f"ADD +1 after {w}m -> exit both 16:00"] = (FP[:, g("16:00")] - op) * pv + (FP[:, g("16:00")] - FP[:, w]) * pv - 2 * cs
            acts[f"(no overnight) ENTER 1 after {w}m -> exit 16:00"] = (FP[:, g("16:00")] - FP[:, w]) * pv - 2 * cs
        for sn, m in states.items():
            for an, v in acts.items():
                x = v[m & ~np.isnan(v)]
                if len(x) < 3:
                    continue
                rows.append({"inst": pn.inst, "state": sn, "action_vs_EXIT_AT_OPEN": an, "n": len(x), "mean$": x.mean(),
                             "median$": np.median(x), "t": x.mean() / x.std() * np.sqrt(len(x)), "p5$": np.percentile(x, 5),
                             "worst$": x.min()})
    return pd.DataFrame(rows)


LATE_TIMES = ["15:00", "15:30", "15:45", "16:14"]


def late_study(P, sims, st):
    rows = []
    fe = {}
    for sm in sims:
        pn = sm.pn; FP = sm.FP
        other = sims[1 - sm.k].pn
        for t in LATE_TIMES:
            j = g(t)
            f = F.late(pn, j)
            fo = F.late(other, j)
            f["rel_rth_ret_vs_other"] = f["rth_ret"] - fo["rth_ret"]
            f["rel_day_ret_vs_other"] = f["day_ret"] - fo["day_ret"]
            f["champ_pos_1612"] = st[f"p{'ES' if sm.k == 0 else 'MNQ'}_1612"].values
            f["champ_dd_prev"] = st["champ_dd_prev"].values
            y = (np.r_[FP[1:, 0], np.nan] - FP[:, j + 1]) / pn.atr            # fill t+1 -> next RTH open (locked)
            fe[(sm.k, t)] = (f, y)
            for nm, x in f.items():
                ok = ~np.isnan(x) & ~np.isnan(y)
                if ok.sum() < 100:
                    continue
                ic = np.corrcoef(x[ok], y[ok])[0, 1]; ric = spearmanr(x[ok], y[ok]).statistic
                q = pd.qcut(pd.Series(x[ok]).rank(method="first"), 5, labels=False).values
                yo = y[ok]
                spread = yo[q == 4].mean() - yo[q == 0].mean()
                # fold stability: sign of rank IC per outer block + pre-2021
                blocks = [("pre2021", "2019-01-01", "2020-12-31")] + [(a, b, c) for a, b, c in C.OUTER]
                sg = []
                for _, b0, b1 in blocks:
                    mb = ok & (pn.sess >= pd.Timestamp(b0)) & (pn.sess <= pd.Timestamp(b1))
                    if mb.sum() > 30:
                        sg.append(spearmanr(x[mb], y[mb]).statistic)
                rows.append({"inst": pn.inst, "decision": t, "feature": nm, "n": int(ok.sum()), "IC": ic, "rankIC": ric,
                             "q5_minus_q1_atr": spread, "block_rankIC_same_sign_share": float(np.mean(np.sign(sg) == np.sign(ric))),
                             "block_rankIC_min": float(np.min(sg)), "block_rankIC_max": float(np.max(sg))})
    return pd.DataFrame(rows)


def cross_index(P, sims):
    """does the ES/NQ relative state add information to gap rebound / flush / carry beyond the own-instrument state?"""
    import statsmodels.api as sm_
    rows = []
    for sm in sims:
        pn = sm.pn; FP = sm.FP; o = sims[1 - sm.k].pn
        f0 = F.morning(pn, 30); fo = F.morning(o, 30)
        tasks = {
            "gap rebound (09:32 -> 16:00)": ((pn.Cf[:, g("16:00")] - FP[:, 1]) / pn.atr,
                                             {"own_gap": pn.gap_lock / pn.atr}, {"rel_gap": pn.gap_lock / pn.atr - o.gap_lock / o.atr}),
            "flush rebound (10:01 -> 16:00)": ((pn.Cf[:, g("16:00")] - FP[:, 30]) / pn.atr,
                                               {"own_gap": pn.gap_lock / pn.atr, "own_selloff30": f0["selloff_w"], "own_ret30": f0["ret_w"]},
                                               {"rel_selloff30": f0["selloff_w"] - fo["selloff_w"], "rel_ret30": f0["ret_w"] - fo["ret_w"]}),
        }
        fl = F.late(pn, g("15:45")); flo = F.late(o, g("15:45"))
        tasks["carry (15:46 -> next open)"] = ((np.r_[FP[1:, 0], np.nan] - FP[:, g("15:45") + 1]) / pn.atr,
                                               {"own_rth_ret": fl["rth_ret"], "own_dist_vwap": fl["dist_vwap"], "own_mom60": fl["mom60"]},
                                               {"rel_rth_ret": fl["rth_ret"] - flo["rth_ret"], "rel_mom60": fl["mom60"] - flo["mom60"]})
        for tn, (y, own, rel) in tasks.items():
            X0 = pd.DataFrame(own); X1 = pd.concat([X0, pd.DataFrame(rel)], axis=1)
            ok = ~np.isnan(y) & X1.notna().all(1).values
            yy = np.clip(y[ok], -3, 3)
            r0 = sm_.OLS(yy, sm_.add_constant(X0[ok].values)).fit(cov_type="HC1")
            r1 = sm_.OLS(yy, sm_.add_constant(X1[ok].values)).fit(cov_type="HC1")
            # chronological out-of-sample R2 (expanding, yearly)
            yrs = pn.sess[ok].year
            pr0 = np.full(ok.sum(), np.nan); pr1 = pr0.copy()
            for yv in range(2021, 2027):
                tr = yrs < yv; te = yrs == yv
                if tr.sum() < 200 or te.sum() == 0:
                    continue
                pr0[te] = sm_.OLS(yy[tr], sm_.add_constant(X0[ok].values[tr])).fit().predict(sm_.add_constant(X0[ok].values[te], has_constant="add"))
                pr1[te] = sm_.OLS(yy[tr], sm_.add_constant(X1[ok].values[tr])).fit().predict(sm_.add_constant(X1[ok].values[te], has_constant="add"))
            mm = ~np.isnan(pr0)
            oos = lambda p: 1 - ((yy[mm] - p[mm]) ** 2).sum() / ((yy[mm] - yy[mm].mean()) ** 2).sum()
            rows.append({"inst": pn.inst, "task": tn, "n": int(ok.sum()), "R2_own": r0.rsquared, "R2_own+rel": r1.rsquared,
                         "rel_coef_t": ", ".join(f"{k}:{t:.2f}" for k, t in zip(rel, r1.tvalues[-len(rel):])),
                         "OOS_R2_own": oos(pr0), "OOS_R2_own+rel": oos(pr1), "rel_adds_OOS": bool(oos(pr1) > oos(pr0))})
    return pd.DataFrame(rows)


def main():
    P = C.build_panel()
    sims = [S.Sim(P, i) for i in C.INSTS]
    st = F.champion_state(sims[0].pn.sess)
    gs = gap_study(P, sims); gs.to_csv(f"{OUT}/T45_04_gap_buckets.csv", index=False)
    fs = flush_study(P, sims); fs.to_csv(f"{OUT}/T45_05_flush.csv", index=False)
    ms = matrix_study(P, sims); ms.to_csv(f"{OUT}/T45_06_matrix.csv", index=False)
    inv = inventory_study(P, sims); inv.to_csv(f"{OUT}/T45_07_inventory.csv", index=False)
    ls = late_study(P, sims, st); ls.to_csv(f"{OUT}/T45_03_late_features.csv", index=False)
    cx = cross_index(P, sims); cx.to_csv(f"{OUT}/T45_16_cross_index.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
    print(gs[(gs.norm == "atr")][["inst", "gap", "bucket", "n", "+60m_atr", "to 12:00_atr", "to 16:00 close_atr", "to 16:00 close_t", "to 16:00 close_net$", "p_recover_50%_gap", "MAE_atr"]].to_string())
    print(fs[fs.window.isin([15, 30])][["inst", "window", "state", "n", "+60m_atr", "to 16:00 close_atr", "to 16:00 close_t", "to 16:00 close_net$"]].to_string())
    print(ms.to_string())
    print(inv[inv.state != "ALL"].to_string())
    print(ls.sort_values("rankIC").to_string())
    print(cx.to_string())


if __name__ == "__main__":
    main()
