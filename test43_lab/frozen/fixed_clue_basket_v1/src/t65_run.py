"""TEST65 - T61 residual opportunity / early continuation map (ALPHA_GAP_MAP_V3_T61) exactly as preregistered (c25145de + addendum).
Labels, potentials and causal detectability only; no trading-rule economics."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402
from t65_prereg import WINDOWS  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test65")
FEATS = ["ret_since_open_MNQ", "ret_since_open_ES", "ES_minus_NQ_ret", "ret_last5_MNQ", "ret_last15_MNQ", "path_efficiency_since_open",
         "range_position", "gap", "prior_day_ret", "ret_5_sessions", "volt", "bull", "t61_exposure_u", "dist_twap"]
J15 = E.J1615


def ffill2(a):
    a = pd.DataFrame(a).T.ffill().T.values
    return a


class Ctx:
    def __init__(self):
        es, nq = E.setup(); self.es, self.nq = es, nq
        self.sess = nq.pn.sess; self.n = nq.n
        tsess, tm = K.t61_minutes()
        ix = pd.Index(tsess).get_indexer(self.sess)
        assert (ix[self.sess >= K.START] >= 0).all()
        g = lambda a: np.where(ix[:, None] >= 0, a[np.clip(ix, 0, None)], 0.0)
        self.qE, self.qN = g(tm["final_target_MES"]), g(tm["final_target_MNQ"])
        self.ratio = (es.atr * es.pv) / (nq.atr * nq.pv)
        self.u = self.qN + self.qE * self.ratio[:, None]
        self.C = {"MNQ": ffill2(nq.pn.C), "ES": ffill2(es.pn.C)}
        self.O = {"MNQ": nq.pn.O, "ES": es.pn.O}
        self.H = {"MNQ": ffill2(nq.pn.H)}; self.L = {"MNQ": ffill2(nq.pn.L)}
        self.FP = {"MNQ": nq.FP, "ES": es.FP}; self.atr = {"MNQ": nq.atr, "ES": es.atr}; self.pv = {"MNQ": nq.pv, "ES": es.pv}
        self.o0 = {k: np.array([row[~np.isnan(row)][0] if (~np.isnan(row)).any() else np.nan for row in self.O[k]]) for k in ("MNQ", "ES")}
        self.cl = {k: self.C[k][:, J15] for k in ("MNQ", "ES")}
        self.volt, self.bull = nq.volt, nq.bull.astype(float)
        self.cm = np.nancumsum(np.where(np.isnan(nq.pn.C), 0, nq.pn.C), 1) / np.maximum(1, np.cumsum(~np.isnan(nq.pn.C), 1))
        self.absd = np.nancumsum(np.abs(np.diff(self.C["MNQ"], axis=1, prepend=self.C["MNQ"][:, :1])), 1)
        self.year = self.sess.year.values
        t61 = K.t61_daily()["T61-R1C"].daily_pnl
        self.t61 = t61.reindex(self.sess).fillna(0.0).values

    def fp(self, k, s, j):
        v = self.FP[k][s, j]
        return v if not np.isnan(v) else self.C[k][s, max(j - 1, 0)]

    def feats(self, s, j):
        """causal: bars ending at grid index <= j-1 (decision minute), fill at j."""
        a, b = self.atr["MNQ"][s], self.atr["ES"][s]; jm = max(j - 1, 0)
        c, ce = self.C["MNQ"][s], self.C["ES"][s]
        r = (c[jm] - self.o0["MNQ"][s]) / a; re = (ce[jm] - self.o0["ES"][s]) / b
        hi, lo = np.nanmax(self.H["MNQ"][s, :jm + 1]), np.nanmin(self.L["MNQ"][s, :jm + 1])
        pc = self.cl["MNQ"][s - 1] if s > 0 else np.nan
        return [r, re, re - r, (c[jm] - c[max(jm - 5, 0)]) / a, (c[jm] - c[max(jm - 15, 0)]) / a,
                abs(c[jm] - self.o0["MNQ"][s]) / max(self.absd[s, jm], 1e-9), (c[jm] - lo) / (hi - lo) if hi > lo else 0.5,
                (self.o0["MNQ"][s] - pc) / a if s > 0 else 0.0, (self.cl["MNQ"][s - 1] - self.o0["MNQ"][s - 1]) / a if s > 0 else 0.0,
                (c[jm] - self.cl["MNQ"][s - 5]) / a if s >= 5 else 0.0, self.volt[s], self.bull[s], self.u[s, jm], (c[jm] - self.cm[s, jm]) / a]

    def horizons(self, k, s, j):
        f = self.fp(k, s, j); a = self.atr[k][s]; c = self.C[k][s]
        nx = self.FP[k][s + 1, 0] if s + 1 < self.n else np.nan
        return {f"h{h}": (c[min(j + h, J15)] - f) / a for h in (30, 60, 120)} | {"h1600": (c[E.J1600] - f) / a, "h1615": (c[J15] - f) / a,
                                                                            "hNEXTOPEN": (nx - f) / a}


def idx(t):
    return C45.g(t) + 1


def build(X):
    n = X.n; full = np.asarray(X.sess >= K.START); rows = []; ev = []
    for w, (t0, t1) in WINDOWS.items():
        j0 = 0 if t0 == "09:31" else idx(t0); j1 = C45.g(t1); L = j1 - j0 + 1
        jd = j0 + 5
        for s in np.where(full)[0]:
            if np.isnan(X.atr["MNQ"][s]) or np.isnan(X.o0["MNQ"][s]):
                continue
            rN = (X.C["MNQ"][s, j1] - X.O["MNQ"][s, j0]) / X.atr["MNQ"][s] if not np.isnan(X.O["MNQ"][s, j0]) else np.nan
            rE = (X.C["ES"][s, j1] - X.O["ES"][s, j0]) / X.atr["ES"][s] if not np.isnan(X.O["ES"][s, j0]) else np.nan
            thr = 0.5 * np.sqrt(L / 390); thr_b = thr * np.sqrt((j1 - jd + 1) / L)
            fN = (X.C["MNQ"][s, j1] - X.fp("MNQ", s, jd)) / X.atr["MNQ"][s]; fE = (X.C["ES"][s, j1] - X.fp("ES", s, jd)) / X.atr["ES"][s]
            uavg = float(X.u[s, j0:j1 + 1].mean()); mes = float(X.qE[s, j0:j1 + 1].mean())
            up_at_start = (X.C["MNQ"][s, max(j0 - 1, 0)] - X.o0["MNQ"][s]) > 0 if j0 > 0 else True
            pre = X.C["MNQ"][s, max(j0 - 60, 0):j0]; oh = X.C["MNQ"][s, 0:60]
            comp = (j0 >= 120) and (np.nanmax(pre) - np.nanmin(pre)) < 0.5 * (np.nanmax(oh) - np.nanmin(oh))
            base = {"s": s, "date": X.sess[s], "year": X.year[s], "window": w, "rN": rN, "rE": rE, "u_avg": uavg, "mes_avg": mes, "thr": thr,
                    "fwdN": fN, "fwdE": fE, "thr_b": thr_b, "up_at_start": bool(up_at_start), "compression": bool(comp),
                    "movN$": rN * X.atr["MNQ"][s] * X.pv["MNQ"], "movE$": rE * X.atr["ES"][s] * X.pv["ES"]}
            rows.append({**base, **dict(zip(FEATS, X.feats(s, jd))), **X.horizons("MNQ", s, jd)})
    W = pd.DataFrame(rows)
    # ---------------- event-conditioned triggers
    for s in np.where(full)[0]:
        a = X.atr["MNQ"][s]
        if np.isnan(a) or np.isnan(X.o0["MNQ"][s]):
            continue
        c = X.C["MNQ"][s]; u = X.u[s]
        # EARLY_EXIT: total MNQ-eq drop >= 1 intraday
        dj = np.where((np.diff(u[:E.J1600]) <= -1 + 1e-9))[0] + 1
        for j in dj:
            f = X.fp("MNQ", s, j)
            ev.append({"cat": "EARLY_EXIT_CONTINUATION", "s": s, "j": j, "drop": float(u[j - 1] - u[j]), "fwd": (c[J15] - f) / a, "thr": 0.35,
                       "pot$": float(u[j - 1] - u[j]) * max(0.0, c[J15] - f) * X.pv["MNQ"], "under": True})
        # MULTI_SESSION
        if s + 1 < X.n and (X.cl["MNQ"][s] - X.o0["MNQ"][s]) / a >= 0.5:
            nx = X.FP["MNQ"][s + 1, 0]; m = X.C["MNQ"][s + 1, C45.g("10:30")]
            if not np.isnan(nx):
                ev.append({"cat": "MULTI_SESSION_CONTINUATION", "s": s, "j": J15, "fwd": (m - nx) / X.atr["MNQ"][s + 1], "thr": 0.25,
                           "pot$": max(0.0, 6 - u[J15 - 1]) * max(0.0, m - nx) * X.pv["MNQ"], "under": bool(u[J15 - 1] < 1)})
        # NQ_SECONDARY_BREAKOUT: first new session high after 10:30 that is >= 60 min after the previous high
        rh = np.fmax.accumulate(np.nan_to_num(X.H["MNQ"][s], nan=-np.inf))
        last_hi_j = 0
        for j in range(1, E.J1600):
            if X.H["MNQ"][s, j] > rh[j - 1]:
                if j >= C45.g("10:30") and j - last_hi_j >= 60 and j + 1 < E.J1600:
                    f = X.fp("MNQ", s, j + 1)
                    ev.append({"cat": "NQ_SECONDARY_BREAKOUT", "s": s, "j": j + 1, "fwd": (c[J15] - f) / a, "thr": 0.3,
                               "pot$": max(0.0, 6 - u[j]) * max(0.0, c[J15] - f) * X.pv["MNQ"], "under": bool(u[j] < 3)})
                    break
                last_hi_j = j
        # PULLBACK_RESUMPTION
        j12 = C45.g("12:00")
        if (c[j12] - X.o0["MNQ"][s]) / a >= 0.5:
            jh = int(np.nanargmax(X.H["MNQ"][s, :j12 + 1])); hi = X.H["MNQ"][s, jh]
            if jh < j12 and np.nanmin(X.L["MNQ"][s, jh:j12 + 1]) <= hi - 0.25 * a:
                br = np.where(X.H["MNQ"][s, j12 + 1:E.J1600] > hi)[0]
                if len(br) and j12 + 2 + br[0] < E.J1600:
                    jb = j12 + 2 + int(br[0]); f = X.fp("MNQ", s, jb)
                    ev.append({"cat": "PULLBACK_RESUMPTION", "s": s, "j": jb, "fwd": (c[J15] - f) / a, "thr": 0.25,
                               "pot$": max(0.0, 6 - u[jb - 1]) * max(0.0, c[J15] - f) * X.pv["MNQ"], "under": bool(u[jb - 1] < 3)})
    EV = pd.DataFrame(ev)
    EV["date"] = X.sess[EV.s.values]; EV["year"] = X.year[EV.s.values]
    F = np.array([X.feats(s, j) for s, j in zip(EV.s, EV.j)]); EV[FEATS] = F
    return W, EV


def fold_of(dates):
    f = np.full(len(dates), "", object)
    for nm, a, b in C45.OUTER[:5]:
        f[(dates >= pd.Timestamp(a)) & (dates <= pd.Timestamp(b))] = nm
    return f


def detect(df, label):
    """walk-forward L2 logistic over the outer folds; train = all rows before the fold."""
    df = df.dropna(subset=FEATS + [label]).copy(); y = df[label].astype(int).values
    res = {}
    for nm, a, b in C45.OUTER[:5]:
        tr = (df.date < pd.Timestamp(a)).values; te = ((df.date >= pd.Timestamp(a)) & (df.date <= pd.Timestamp(b))).values
        if tr.sum() < 60 or len(set(y[tr])) < 2 or len(set(y[te])) < 2:
            continue
        sc = StandardScaler().fit(df.loc[tr, FEATS]); m = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(df.loc[tr, FEATS]), y[tr])
        p = m.predict_proba(sc.transform(df.loc[te, FEATS]))[:, 1]
        q = p >= np.quantile(p, 0.8)
        res[nm] = {"auc": roc_auc_score(y[te], p), "base": y[te].mean(), "lift_top20": (y[te][q].mean() / max(y[te].mean(), 1e-9))}
    if not res:
        return {"n": int(len(df)), "base_rate": float(y.mean()), "folds_scored": 0, "median_auc": np.nan, "folds_auc_gt_052": 0, "median_lift_top20": np.nan, "detectable": False}
    auc = np.array([v["auc"] for v in res.values()])
    return {"n": int(len(df)), "base_rate": float(y.mean()), "folds_scored": len(res), "median_auc": float(np.median(auc)), "folds_auc_gt_052": int((auc > 0.52).sum()),
            "median_lift_top20": float(np.median([v["lift_top20"] for v in res.values()])),
            **{f"auc_{k}": v["auc"] for k, v in res.items()}, "detectable": bool(np.median(auc) >= 0.56 and (auc > 0.52).sum() >= 4)}


def main():
    X = Ctx()
    W, EV = build(X)
    W["fold"] = fold_of(W.date); EV["fold"] = fold_of(EV.date)
    W["strongN"] = W.rN >= W.thr; W["strongE"] = W.rE >= W.thr; W["under"] = W.u_avg < 3
    W["fwd_strongN"] = W.fwdN >= W.thr_b; W["fwd_strongE"] = W.fwdE >= W.thr_b
    W["potN$"] = np.maximum(0, 6 - W.u_avg) * np.maximum(0, W["movN$"]); W["potE$"] = np.maximum(0, 2 - W.mes_avg) * np.maximum(0, W["movE$"])
    cats = {}
    w1 = W.window == "W1_0930_1030"; wmid = W.window.isin(["W2_1030_1200", "W3_1200_1400"]); wlate = W.window.isin(["W4_1400_1515", "W5_1515_1615"])
    cats["MISSED_OPENING_TREND"] = (W[w1], "strongN", "fwd_strongN", "potN$")
    cats["MISSED_MIDDAY_CONTINUATION"] = (W[wmid & W.up_at_start], "strongN", "fwd_strongN", "potN$")
    cats["MISSED_LATE_RTH_CONTINUATION"] = (W[wlate & W.up_at_start], "strongN", "fwd_strongN", "potN$")
    W["esind"] = W.strongE & (W.rE - W.rN >= 0.25); W["fwd_esind"] = W.fwd_strongE & (W.fwdE > W.fwdN)
    cats["ES_INDEPENDENT_OPPORTUNITY"] = (W.assign(under=W.mes_avg < 2), "esind", "fwd_esind", "potE$")
    cats["VOLATILITY_TRANSITION"] = (W[W.window.isin(["W3_1200_1400", "W4_1400_1515"]) & W.compression], "strongN", "fwd_strongN", "potN$")
    EV["hit"] = EV.fwd >= EV.thr
    rows = []; gap = []
    nsess = int((X.sess >= K.START).sum())
    for c, (d, lab_a, lab_b, pot) in cats.items():
        ev_ = d[d[lab_a] & d.under]
        fp = ev_.groupby("fold")[pot].sum()
        det = detect(d, lab_b); deta = detect(d, lab_a)
        rows.append({"category": c, "events": len(ev_), "events_per_year": len(ev_) / (nsess / 252), "potential_$_total": float(ev_[pot].sum()),
                     "potential_$_per_day": float(ev_[pot].sum() / nsess), "folds_pot_pos": int((fp > 0).sum()), "fold_median_pot$": float(fp.median()) if len(fp) else 0.0,
                     "mean_move_ATR": float(ev_["rN" if pot == "potN$" else "rE"].mean()), "t61_u_avg_in_events": float(ev_.u_avg.mean()),
                     **{f"B_{k}": v for k, v in det.items()}, "A_median_auc": deta["median_auc"]})
        gap.append(ev_.assign(category=c)[["category", "date", "window", "u_avg", pot, "rN", "rE"]].rename(columns={pot: "pot$"}))
    for c in ("EARLY_EXIT_CONTINUATION", "MULTI_SESSION_CONTINUATION", "NQ_SECONDARY_BREAKOUT", "PULLBACK_RESUMPTION"):
        d = EV[EV.cat == c]; ev_ = d[d.hit & d.under]
        fp = ev_.groupby("fold")["pot$"].sum(); det = detect(d, "hit")
        rows.append({"category": c, "events": len(ev_), "events_per_year": len(ev_) / (nsess / 252), "potential_$_total": float(ev_["pot$"].sum()),
                     "potential_$_per_day": float(ev_["pot$"].sum() / nsess), "folds_pot_pos": int((fp > 0).sum()), "fold_median_pot$": float(fp.median()) if len(fp) else 0.0,
                     "mean_move_ATR": float(ev_.fwd.mean()), "t61_u_avg_in_events": np.nan, "triggers": len(d), "trigger_hit_rate": float(d.hit.mean()),
                     "trigger_mean_fwd_ATR": float(d.fwd.mean()), **{f"B_{k}": v for k, v in det.items()}})
        gap.append(ev_.assign(category=c, window="event")[["category", "date", "window", "pot$"]])
    # diagnostics: LOSS_ALT / OTHER
    full = np.asarray(X.sess >= K.START); oc = (X.cl["MNQ"] - X.o0["MNQ"]) / X.atr["MNQ"]
    q10 = np.percentile(X.t61[full], 10)
    la = full & (X.t61 <= q10) & (oc > 0); ot = full & (oc >= 1.0) & (X.t61 < np.median(X.t61[full]))
    ud = X.u[:, :J15].mean(1)
    for c, m, pot in (("LOSS_ALT", la, -X.t61), ("OTHER", ot, np.maximum(0, 6 - ud) * np.maximum(0, (X.cl["MNQ"] - X.o0["MNQ"])) * X.pv["MNQ"])):
        rows.append({"category": c, "events": int(m.sum()), "events_per_year": m.sum() / (nsess / 252), "potential_$_total": float(np.nansum(pot[m])),
                     "potential_$_per_day": float(np.nansum(pot[m]) / nsess), "folds_pot_pos": np.nan, "B_detectable": False, "note": "diagnostic"})
    R = pd.DataFrame(rows)
    # under-exposure vs forward drift (multi-horizon, excess over same year x window mean): is T61 flat when drift is positive?
    hz = ["h30", "h60", "h120", "h1600", "h1615", "hNEXTOPEN"]
    for h in hz:
        W[h + "_x"] = W[h] - W.groupby(["year", "window"])[h].transform("mean")
    W["u_bucket"] = pd.cut(W.t61_exposure_u, [-0.1, 0.5, 1.5, 3, 7], labels=["0", "1", "2-3", "4-6"])
    DR = W.groupby(["window", "u_bucket"], observed=True)[[h + "_x" for h in hz]].mean().round(4)
    DR["n"] = W.groupby(["window", "u_bucket"], observed=True).size()
    # selection rule
    elig = R[(R.B_detectable == True) & (R.folds_pot_pos >= 4)].copy()  # noqa: E712
    tot = R.loc[R.category.isin(list(cats) + ["EARLY_EXIT_CONTINUATION", "MULTI_SESSION_CONTINUATION", "NQ_SECONDARY_BREAKOUT", "PULLBACK_RESUMPTION"]), "potential_$_total"].sum()
    R["score"] = (R.B_median_auc - 0.5) * R["potential_$_total"] / tot
    if len(elig):
        pick = R.loc[elig.index].sort_values("score", ascending=False).category.iloc[0]; how = "detectable & stable, max score"
    else:
        cand = R[R.folds_pot_pos >= 4].sort_values("potential_$_total", ascending=False)
        pick = cand.category.iloc[0] if len(cand) else "NONE"; how = "no detectable category -> strongest potential, simple rule only"
    es_pick = R[R.category == "ES_INDEPENDENT_OPPORTUNITY"].iloc[0]
    R.to_csv(os.path.join(K.OUT, "ALPHA_GAP_MAP_V3_T61.csv"), index=False)
    pd.concat(gap, ignore_index=True).to_csv(os.path.join(OUT, "T65_gap_events.csv.gz"), index=False, compression="gzip")
    DR.to_csv(os.path.join(OUT, "T65_exposure_vs_forward_drift.csv"))
    W.drop(columns=["s"]).to_parquet(os.path.join(OUT, "T65_window_labels.parquet")); EV.to_parquet(os.path.join(OUT, "T65_event_labels.parquet"))
    st = {"TEST66_mechanism": pick, "selection": how, "TEST67_ES_candidate": {"B_median_auc": es_pick.B_median_auc, "potential_$_per_day": es_pick["potential_$_per_day"],
                                                                              "detectable": bool(es_pick.B_detectable)}}
    K.jdump(st, os.path.join(OUT, "T65_SELECTION.json"))
    K.reg_append("TEST65_PLUS_RESEARCH_REGISTRY", [{"test": "TEST65", "family": "T61 residual opportunity map (labels only)", "prereg_sha": open(os.path.join(OUT, "TEST65_PREREGISTRATION.json.sha256")).read().strip(),
                                                   "result": f"map built; TEST66 -> {pick} ({how})", "status": "MAP", "utc": K.now()}], key="test")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    show = ["category", "events", "events_per_year", "potential_$_per_day", "folds_pot_pos", "mean_move_ATR", "t61_u_avg_in_events", "B_base_rate", "B_median_auc",
            "B_folds_auc_gt_052", "B_median_lift_top20", "B_detectable", "A_median_auc", "trigger_hit_rate", "trigger_mean_fwd_ATR", "score"]
    print(R[[c for c in show if c in R]].round(3).to_string()); print(DR.to_string()); print(st)
    K.md("TEST65_ALPHA_GAP_MAP_V3_T61.md", "TEST65 - T61-R1C residual opportunity / early continuation map (ALPHA_GAP_MAP_V3_T61)",
         ["Preregistered (sha c25145de + addendum). Labels / potentials / detectability only - potentials are NOT strategy P&L.",
          R[[c for c in show if c in R]].round(3), "Forward drift (excess over same year x window mean, ATR units) by T61 exposure bucket at the decision minute:", DR,
          "```json\n" + str(st) + "\n```"])


if __name__ == "__main__":
    main()
