"""TEST47 N3 / NB event research (T47_01 .. T47_18): data & causal QA, tick-definition catalogue, forward response, matched
nulls, path-order null, sequence-shuffle, N-tick frontier, entry timing, sideways / up-bar state, prior-rally filter,
true-bottom, deceleration, crash veto, 1m and 15m confirmation, simple controls C0..C4.  All settings come from the
predeclared SPEC (t47_common); nothing here is tuned on the results it reports."""
import json
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_common as C  # noqa: E402
import t47_engine as E  # noqa: E402

OUT = os.path.join(C.T47, "n3"); os.makedirs(OUT, exist_ok=True)
HOR = {"+5m": 5, "+15m": 15, "+30m": 30, "+60m": 60, "+120m": 120, "to16:00": "16:00", "to16:15": "16:15"}
START = pd.Timestamp("2019-07-01")          # u5 / ATR warm-up
DEFAULT = dict(leg="T1", ntick=3, side=["RESET", 6], up=["RESET", 1.0], maxdur=24, r1=True)


def cfg(**kw):
    d = dict(DEFAULT); d.update(kw)
    if "x" not in kw:
        d["x"] = C.SPEC["x_default"][d["leg"]]
    return d


# ------------------------------------------------------------------------------------------------ forward matrices
class Fwd:
    def __init__(self, mk):
        self.mk = mk
        self.F = {}
        J = np.arange(C45.NG)
        for lab, h in HOR.items():
            jx = np.minimum(J + h, E.J1615) if isinstance(h, int) else np.full(C45.NG, C45.g(h))
            X = (mk.FPb[:, jx] - mk.FP) / mk.atr[:, None]
            X[:, jx <= J] = np.nan
            self.F[lab] = X
        key = mk.year * 100 + mk.vt * 10 + mk.bull.astype(int)
        self.key = key
        self.G = {}
        for lab, X in self.F.items():
            df = pd.DataFrame(X); df["key"] = key
            self.G[lab] = df.groupby("key").mean()

    def event(self, s, j, matched=True):
        out = {}
        for lab, X in self.F.items():
            v = X[s, j]
            out[lab] = v
            if matched:
                G = self.G[lab]
                out[lab + "_base"] = G.values[G.index.get_indexer(self.key[s]), j]
        return pd.DataFrame(out)


def tstat(x, groups=None):
    x = pd.Series(np.asarray(x, float)).dropna()
    if len(x) < 5:
        return np.nan
    if groups is not None:
        # event-mean t with session-clustered standard error (same estimand as the reported event mean)
        g = pd.Series(np.asarray(groups)).iloc[x.index].values
        mu = x.mean(); r = (x - mu).groupby(g).sum().values; G = len(r)
        se = np.sqrt(G / max(G - 1, 1) * (r ** 2).sum()) / len(x)
        return float(mu / se) if se > 0 else np.nan
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if x.std() > 0 else np.nan


def path_stats(mk, s, j):
    """MFE / MAE to +120m, time-to-target and first passage (ATRd units) - unresolved stays unresolved."""
    rows = []
    for si, ji in zip(s, j):
        a = mk.atr[si]; px = mk.FP[si, ji]
        H = mk.pn.H[si, ji:E.J1615]; L = mk.pn.L[si, ji:E.J1615]
        Hw = H[:120]; Lw = L[:120]
        r = {"MFE120": (np.nanmax(Hw) - px) / a, "MAE120": (px - np.nanmin(Lw)) / a}
        for th in (0.25, 0.5, 1.0):
            up = np.where(H >= px + th * a)[0]
            r[f"t_up{th}"] = float(up[0] + 1) if len(up) else np.nan
        for th in (0.5, 1.0):
            up = np.where(H >= px + th * a)[0]; dn = np.where(L <= px - th * a)[0]
            u_ = up[0] if len(up) else 10 ** 9; d_ = dn[0] if len(dn) else 10 ** 9
            r[f"fp{th}"] = 1.0 if u_ < d_ else (0.0 if d_ < u_ else np.nan)
        rows.append(r)
    return pd.DataFrame(rows)


def event_table(mk, fw, ev, entry="E1"):
    j = E.entry_fill(mk, ev, entry)
    ok = (j >= 0) & (mk.pn.sess[ev.s.values] >= START)
    e = ev[ok].reset_index(drop=True); j = j[ok]
    F = fw.event(e.s.values, j)
    out = pd.concat([e, F], axis=1); out["j"] = j
    out["date"] = mk.pn.sess[out.s.values]; out["year"] = out.date.dt.year
    return out


def summarise_fwd(T, lab, extra=None):
    o = {"events": len(T), "sessions": T.s.nunique() if len(T) else 0}
    for h in HOR:
        x = T[h]; b = T[h + "_base"]
        o[f"{h}_mean"] = x.mean(); o[f"{h}_excess"] = (x - b).mean(); o[f"{h}_t_exc"] = tstat(x - b, T.s)
    o.update(extra or {})
    return {"config": lab, **o}


def pnl_summary(mk, T, bl, rule, lab, slip=1.0):
    """1-contract non-overlapping trade economics + matched-long excess ($)."""
    if len(T) == 0:
        return {"config": lab, "trades": 0}
    exc, base = bl.excess(T, rule, slip)
    T = T.assign(excess=exc)
    sess = mk.pn.sess; m21 = sess >= pd.Timestamp("2021-01-01"); m19 = sess >= START
    d = E.daily(mk, T); dx = E.daily(mk, T, "excess")
    yr = T.groupby("year").pnl.sum(); yx = T.groupby("year").excess.sum()
    fold = {}
    for nm, a, b in C45.OUTER:
        mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b))
        fold[nm] = float(d[mm].mean())
    top = np.sort(T.pnl.values)[::-1]
    return {"config": lab, "trades": len(T), "avg_trade": T.pnl.mean(), "total": T.pnl.sum(), "avg_day_2019": d[m19].mean(),
            "avg_day_2021": d[m21].mean(), "excess_trade": T.excess.mean(), "t_excess": tstat(T.excess, T.s),
            "excess_day_2021": dx[m21].mean(), "win%": (T.pnl > 0).mean(), "years_pos": int((yr > 0).sum()), "years": len(yr),
            "years_exc_pos": int((yx > 0).sum()), "folds_pos": int(sum(v > 0 for v in fold.values())),
            "fold_median": float(np.median(list(fold.values()))), **{f"f_{k}": v for k, v in fold.items()},
            "remove_top3": float(T.pnl.sum() - top[:3].sum()), "max_year_share": float(yr.clip(lower=0).max() / max(yr.clip(lower=0).sum(), 1e-9))}


# ------------------------------------------------------------------------------------------------ causal QA
def causal_qa(mk):
    """perturb every bar after b0 and verify: events with trigger bar < b0 and their E1/E3/E5/NB fills decided < b0 are unchanged."""
    rng = np.random.default_rng(3)
    res = []
    for b0 in (20, 40, 60):
        base_ev, _, _ = E.run_detect(mk, cfg())
        sav = {k: getattr(mk, k).copy() for k in ("o", "h", "l", "c")}
        for k in ("o", "h", "l", "c"):
            A = getattr(mk, k); A[:, b0:] = A[:, b0:] + rng.normal(0, 5, A[:, b0:].shape)
        pe, _, _ = E.run_detect(mk, cfg())
        for k, v in sav.items():
            setattr(mk, k, v)
        a = base_ev[base_ev.b < b0][["s", "b", "cum", "leg3"]].reset_index(drop=True)
        bb = pe[pe.b < b0][["s", "b", "cum", "leg3"]].reset_index(drop=True)
        res.append({"inst": mk.inst, "perturb_from_bar": b0, "events_before": len(a), "identical": bool(a.equals(bb))})
    return res


# ------------------------------------------------------------------------------------------------ path-order null
def path_order_null(mk, fw, ev_tab, cnt, ntick, labs=("+30m", "+60m", "to16:00")):
    n = mk.n; c = mk.c; u = mk.u5
    rows = []
    for d in range(2, 25):
        b = np.arange(d, 73)
        drop = (c[:, b - d] - c[:, b]) / u[:, None]
        ok = (cnt[:, b] < ntick) & np.isfinite(drop) & (drop > 0)
        ss, bi = np.nonzero(ok)
        rows.append(pd.DataFrame({"s": ss, "b": b[bi], "d": d, "bin": np.floor(drop[ss, bi] / 0.5).astype(int)}))
    P = pd.concat(rows, ignore_index=True)
    P = P[mk.pn.sess[P.s.values] >= START]
    P["hb"] = P.b // 12; P["vt"] = mk.vt[P.s.values]
    j = 5 * (P.b.values + 1)
    for lab in labs:
        P[lab] = fw.F[lab][P.s.values, j]
    G = P.groupby(["d", "bin", "hb", "vt"])[list(labs)].agg(["mean", "count"])
    e = ev_tab.copy()
    e["d"] = e.b - e.start + 1
    e["drop"] = (c[e.s.values, e.b.values - e.d.values] - c[e.s.values, e.b.values]) / u[e.s.values]
    e["bin"] = np.floor(e["drop"] / 0.5).astype(int); e["hb"] = e.b // 12; e["vt"] = mk.vt[e.s.values]
    e = e[(e.d >= 2) & (e.d <= 24)]
    idx = pd.MultiIndex.from_frame(e[["d", "bin", "hb", "vt"]])
    out = {"events_matched": 0}
    for lab in labs:
        mu = G[(lab, "mean")].reindex(idx).values; cntc = G[(lab, "count")].reindex(idx).values
        okm = np.isfinite(mu) & (cntc >= 5)
        x = e[lab].values[okm] - mu[okm]
        out[f"{lab}_event"] = float(np.nanmean(e[lab].values[okm])); out[f"{lab}_ctrl"] = float(np.nanmean(mu[okm]))
        out[f"{lab}_order_excess"] = float(np.nanmean(x)); out[f"{lab}_t"] = tstat(x, e.s.values[okm])
        out["events_matched"] = int(okm.sum()); out["median_controls_per_event"] = float(np.nanmedian(cntc[okm]))
    return out


# ------------------------------------------------------------------------------------------------ sequence shuffle
@njit(cache=True)
def _shuffle_windows(o, h, l, c, S, Bv, W, perm):
    N = len(S)
    O = np.empty((N, W + 1)); H = np.empty((N, W + 1)); L = np.empty((N, W + 1)); Cc = np.empty((N, W + 1))
    for i in range(N):
        s = S[i]; b = Bv[i]; b0 = b - W
        O[i, 0] = o[s, b0]; H[i, 0] = h[s, b0]; L[i, 0] = l[s, b0]; Cc[i, 0] = c[s, b0]
        prev = c[s, b0]
        for q in range(W):
            src = b0 + 1 + perm[i, q]
            cp = c[s, src - 1]
            O[i, q + 1] = prev + (o[s, src] - cp); H[i, q + 1] = prev + (h[s, src] - cp)
            L[i, q + 1] = prev + (l[s, src] - cp); Cc[i, q + 1] = prev + (c[s, src] - cp)
            prev = Cc[i, q + 1]
    return O, H, L, Cc


def shuffle_test(mk, fw, p, W=12, nperm=20, lab="+60m"):
    rng = np.random.default_rng(47)
    ss, bb = np.meshgrid(np.arange(mk.n), np.arange(W, 73), indexing="ij")
    ss = ss.ravel(); bb = bb.ravel()
    ok = (mk.pn.sess[ss] >= START) & np.isfinite(mk.u5[ss]) & ~np.isnan(mk.c[ss, bb]) & ~np.isnan(mk.c[ss, bb - W])
    ss, bb = ss[ok], bb[ok]
    fwd = fw.F[lab][ss, 5 * (bb + 1)] - fw.G[lab].values[fw.G[lab].index.get_indexer(fw.key[ss]), 5 * (bb + 1)]
    u = mk.u5[ss]
    ld = E.LEGDEF[p["leg"]]

    def trig(O, H, L, Cc):
        Ev, _, _ = E.detect(O, H, L, Cc, u, ld, float(p["x"]), int(p["ntick"]), E.SIDE[p["side"][0]], int(p["side"][1]),
                            E.SIDE[p["up"][0]], float(p["up"][1]), int(p["maxdur"]), bool(p["r1"]), W, W, 1)
        t = np.zeros(len(ss), bool); t[Ev[:, 0].astype(int)] = True
        return t
    ident = np.tile(np.arange(W), (len(ss), 1))
    real = trig(*_shuffle_windows(mk.o, mk.h, mk.l, mk.c, ss, bb, W, ident))
    r_mean = float(np.nanmean(fwd[real]))
    sh = []
    for k in range(nperm):
        perm = np.argsort(rng.random((len(ss), W)), axis=1)
        t = trig(*_shuffle_windows(mk.o, mk.h, mk.l, mk.c, ss, bb, W, perm))
        sh.append(float(np.nanmean(fwd[t])))
    sh = np.array(sh)
    return {"windows": len(ss), "real_triggers": int(real.sum()), "real_fwd_excess_atr": r_mean, "shuffled_mean": float(sh.mean()),
            "shuffled_sd": float(sh.std()), "order_effect": r_mean - float(sh.mean()), "perm_p_one_sided": float((sh >= r_mean).mean())}


# ------------------------------------------------------------------------------------------------ 15m context
def ctx15(mk, ev):
    """completed 15m bars at the trigger: # of 15m T1 legs in the last 4 completed 15m bars and last 15m bar bullish."""
    m = (ev.b.values + 1) // 3 - 1
    legs = np.zeros(len(ev)); bull = np.zeros(len(ev), bool)
    x = 0.75 * np.sqrt(3)
    for i, (s, mi) in enumerate(zip(ev.s.values, m)):
        if mi < 1:
            continue
        cc = mk.c15[s, max(0, mi - 4):mi + 1]
        d = -np.diff(cc) / mk.u5[s]
        legs[i] = np.nansum(d >= x)
        bull[i] = mk.c15[s, mi] > mk.o15[s, mi]
    return legs, bull


# ------------------------------------------------------------------------------------------------ C0: ordinary 3 red bars
def three_red(mk, bmax=72):
    rows = []
    red = mk.c < mk.o
    for s in range(mk.n):
        run = 0
        for b in range(NB5 := mk.c.shape[1]):
            run = run + 1 if red[s, b] else 0
            if run == 3 and 1 <= b <= bmax:
                rows.append((s, b)); run = 0
    ev = pd.DataFrame(rows, columns=["s", "b"])
    for col in E.FCOLS:
        if col not in ev:
            ev[col] = np.nan
    ev["lastbar_h"] = mk.h[ev.s, ev.b]; ev["lastbar_l"] = mk.l[ev.s, ev.b]; ev["start"] = ev.b - 2
    ev["c_last"] = mk.c[ev.s, ev.b]; ev["ref"] = mk.c[ev.s, ev.b - 3]
    return ev


def main():
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    FW = {k: Fwd(m) for k, m in mks.items()}
    BL = {k: E.Baseline(m) for k, m in mks.items()}
    R = {}
    # ---------------- T47_01 data & causal QA
    qa = []
    for k, mk in mks.items():
        qa.append({"inst": k, "sessions": mk.n, "first": str(mk.pn.sess[0].date()), "last": str(mk.pn.sess[-1].date()),
                   "last_le_cutoff": bool(mk.pn.sess[-1] <= C.END), "full_81bar_sessions": int((~np.isnan(mk.c)).all(1).sum()),
                   "u5_median_pts": float(np.nanmedian(mk.u5)), "atrd_median_pts": float(np.nanmedian(mk.atr)),
                   "canonical_sha256": C45.DATA[k][1], "volume_used_by_signals": "NO"})
    cq = causal_qa(es) + causal_qa(nq)
    pd.DataFrame(qa).to_csv(f"{OUT}/T47_01_data_qa.csv", index=False); pd.DataFrame(cq).to_csv(f"{OUT}/T47_01_causal_qa.csv", index=False)
    R["qa"] = (pd.DataFrame(qa), pd.DataFrame(cq))
    print(pd.DataFrame(cq), flush=True)

    # ---------------- T47_03/04/05 catalogue, forward response, matched nulls per leg definition
    cat, fr, pn_rows, fp_rows = [], [], [], []
    evtabs = {}
    for k, mk in mks.items():
        for leg in ("T1", "T2", "T3", "T4"):
            p = cfg(leg=leg)
            ev, cnt, legm = E.run_detect(mk, p)
            T = event_table(mk, FW[k], ev)
            T["inst"] = k; T["leg"] = leg
            evtabs[(k, leg)] = (T, cnt, legm, ev)
            cat.append(T)
            fr.append({"inst": k, **summarise_fwd(T, leg)})
            ps = path_stats(mk, T.s.values, T.j.values)
            fp_rows.append({"inst": k, "config": leg, **ps.mean().to_dict(),
                            **{f"median_{c}": ps[c].median() for c in ps if c.startswith("t_up")},
                            **{f"hit_{c}": ps[c].notna().mean() for c in ps if c.startswith("t_up")},
                            "unresolved_fp0.5": ps["fp0.5"].isna().mean(), "unresolved_fp1.0": ps["fp1.0"].isna().mean()})
            Tt = E.trades(mk, ev[mk.pn.sess[ev.s.values] >= START], "E1", "X60")
            pn_rows.append({"inst": k, **pnl_summary(mk, Tt, BL[k], "X60", leg)})
    CAT = pd.concat(cat, ignore_index=True)
    CAT.to_parquet(f"{OUT}/T47_03_event_catalog.parquet")
    R["fr"] = pd.DataFrame(fr); R["fp"] = pd.DataFrame(fp_rows); R["pn_leg"] = pd.DataFrame(pn_rows)
    R["cat_year"] = CAT.groupby(["inst", "leg", "year"]).size().unstack(0).unstack(0)
    print(R["fr"][["inst", "config", "events", "+30m_excess", "+60m_excess", "+60m_t_exc", "to16:00_excess", "to16:00_t_exc"]].round(3), flush=True)
    print(R["pn_leg"][["inst", "config", "trades", "avg_trade", "excess_trade", "t_excess", "folds_pos"]].round(2), flush=True)

    # ---------------- T47_06 path-order null, T47_07 shuffle
    po, shf = [], []
    for k, mk in mks.items():
        for leg in ("T1", "T2", "T3", "T4"):
            T, cnt, _, _ = evtabs[(k, leg)]
            po.append({"inst": k, "leg": leg, **path_order_null(mk, FW[k], T, cnt, 3)})
            if leg in ("T1", "T4"):
                shf.append({"inst": k, "leg": leg, **shuffle_test(mk, FW[k], cfg(leg=leg))})
                print(shf[-1], flush=True)
    R["po"] = pd.DataFrame(po); R["shf"] = pd.DataFrame(shf)
    print(R["po"].round(3).to_string(), flush=True)

    # ---------------- T47_08 N-tick frontier, T47_09 entries, T47_10 sideways / up-bar, T47_11 prior rally
    fr8, en9, sw10, ra11 = [], [], [], []
    for k, mk in mks.items():
        for leg in ("T1", "T2", "T3", "T4"):
            for nt in (2, 3, 4):
                p = cfg(leg=leg, ntick=nt)
                ev, cnt, _ = E.run_detect(mk, p)
                T = event_table(mk, FW[k], ev)
                po_ = path_order_null(mk, FW[k], T, cnt, nt, labs=("+60m",))
                Tt = E.trades(mk, ev[mk.pn.sess[ev.s.values] >= START], "E1", "X60")
                fr8.append({"inst": k, "leg": leg, "ntick": nt, **{kk: v for kk, v in summarise_fwd(T, f"{leg}-{nt}").items() if kk != "config"},
                            "order_excess_60": po_["+60m_order_excess"], "order_t_60": po_["+60m_t"],
                            **{f"pnl_{kk}": v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos")}})
        ev = evtabs[(k, "T1")][3]; ev = ev[mk.pn.sess[ev.s.values] >= START]
        for ent in ("E1", "E2", "E3", "E4", "E5", "NB"):
            T = event_table(mk, FW[k], ev, ent)
            Tt = E.trades(mk, ev, ent, "X60")
            en9.append({"inst": k, "entry": ent, **{kk: v for kk, v in summarise_fwd(T, ent).items() if kk in ("events", "+30m_excess", "+60m_excess", "+60m_t_exc", "to16:00_excess", "to16:00_t_exc")},
                        **pnl_summary(mk, Tt, BL[k], "X60", ent)})
        for sm, grid in C.SPEC["sideways_grid"].items():
            for sn in grid:
                for um in ("KEEP", "DECAY", "RESET"):
                    for uf in C.SPEC["upbar_frac_grid"]:
                        if um == "KEEP" and uf != 1.0:
                            continue
                        p = cfg(side=[sm, max(sn, 1)], up=[um, uf])
                        ev, cnt, _ = E.run_detect(mk, p)
                        ev = ev[mk.pn.sess[ev.s.values] >= START]
                        T = event_table(mk, FW[k], ev)
                        Tt = E.trades(mk, ev, "E1", "X60")
                        sw10.append({"inst": k, "sideways": f"{sm}{sn if sm != 'KEEP' else ''}", "upbar": f"{um}{uf if um != 'KEEP' else ''}",
                                     "events": len(T), "+60m_excess": (T["+60m"] - T["+60m_base"]).mean(), "+60m_t": tstat(T["+60m"] - T["+60m_base"], T.s),
                                     **{kk: v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos")}})
        # prior rally (T1 default, rally30 >= 4 u5 = LARGE)
        ev3 = evtabs[(k, "T1")][3]; ev3 = ev3[mk.pn.sess[ev3.s.values] >= START]
        ev4, _, _ = E.run_detect(mk, cfg(ntick=4)); ev4 = ev4[mk.pn.sess[ev4.s.values] >= START]
        large = ev3.rally30 >= 4.0
        l15, b15 = ctx15(mk, ev3)
        large4 = ev4.rally30 >= 4.0
        variants = {"NONE": ev3, "LARGE_ONLY (diagnostic)": ev3[large], "NOTRADE": ev3[~large],
                    "NEED4": pd.concat([ev3[~large], ev4[large4]]), "CONFIRM15": ev3[(~large) | b15]}
        for nm, e_ in variants.items():
            T = event_table(mk, FW[k], e_)
            Tt = E.trades(mk, e_, "E1", "X60")
            ra11.append({"inst": k, "variant": nm, "events": len(T), "+60m_excess": (T["+60m"] - T["+60m_base"]).mean(),
                         "+60m_t": tstat(T["+60m"] - T["+60m_base"], T.s),
                         **{kk: v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos")}})
    R["fr8"] = pd.DataFrame(fr8); R["en9"] = pd.DataFrame(en9); R["sw10"] = pd.DataFrame(sw10); R["ra11"] = pd.DataFrame(ra11)
    print(R["fr8"][["inst", "leg", "ntick", "events", "+60m_excess", "+60m_t_exc", "order_excess_60", "order_t_60", "pnl_excess_trade", "pnl_t_excess"]].round(3).to_string(), flush=True)
    print(R["en9"][["inst", "entry", "trades", "avg_trade", "excess_trade", "t_excess", "folds_pos"]].round(2).to_string(), flush=True)

    # ---------------- T47_12..16 true bottom, deceleration, crash veto, 1m, 15m
    nb, dec, cv, m1, m15 = [], [], [], [], []
    for k, mk in mks.items():
        T, cnt, _, ev = evtabs[(k, "T1")]
        ev = ev[mk.pn.sess[ev.s.values] >= START].reset_index(drop=True)
        decel = (ev.leg3 <= ev.leg2).values
        accel = (ev.leg3 >= 2.0 * ev.leg2).values
        cum = (ev.cum >= 10).values
        gap = (mk.gap[ev.s.values] <= -1.5); r5 = (mk.ret5[ev.s.values] <= -3.0); vol = (mk.volt[ev.s.values] >= 0.9)
        veto = accel | cum | gap | r5 | vol
        l15, b15 = ctx15(mk, ev)
        slow = (ev.dur >= 12).values | (mk.volt[ev.s.values] <= 1 / 3)
        subsets = {"ALL": np.ones(len(ev), bool), "DECEL (leg3<=leg2)": decel, "ACCEL (not decel)": ~decel}
        for ent in ("E1", "NB"):
            for nm, m in subsets.items():
                Tt = E.trades(mk, ev[m], ent, "X60")
                dec.append({"inst": k, "entry": ent, "subset": nm, **{kk: v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos", "years_exc_pos")}})
        for nm, m in {"no veto": np.zeros(len(ev), bool), "accel": accel, "cum>=10": cum, "gap<=-1.5": gap, "ret5<=-3": r5, "vol>=0.9": vol, "ANY (predeclared veto)": veto}.items():
            for side, mm in (("kept", ~m), ("vetoed", m)):
                if nm == "no veto" and side == "vetoed":
                    continue
                Tt = E.trades(mk, ev[mm], "E1", "X60")
                cv.append({"inst": k, "veto": nm, "side": side, **{kk: v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos")}})
        for ent in ("E1", "E4", "NB"):
            Tt = E.trades(mk, ev, ent, "X60")
            m1.append({"inst": k, "entry": ent, **{kk: v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos", "years_exc_pos")}})
        for nm, m in {"ALL": np.ones(len(ev), bool), "15m bullish confirm": b15, "15m not bullish": ~b15, ">=2 15m legs": l15 >= 2,
                      "slow/low-vol seq": slow, "slow & 15m>=2 legs": slow & (l15 >= 2), "slow & 15m<2 legs": slow & (l15 < 2)}.items():
            Tt = E.trades(mk, ev[m], "E1", "X60")
            m15.append({"inst": k, "context": nm, **{kk: v for kk, v in pnl_summary(mk, Tt, BL[k], "X60", "").items() if kk in ("trades", "avg_trade", "excess_trade", "t_excess", "folds_pos")}})
        nbT = E.trades(mk, ev, "NB", "X60")
        nb.append({"inst": k, "NB_fill_rate": len(nbT) / max(len(ev), 1), "median_bars_to_confirm": float(np.median(nbT.j // 5 - nbT.b - 1)) if len(nbT) else np.nan})
    R["dec"] = pd.DataFrame(dec); R["cv"] = pd.DataFrame(cv); R["m1"] = pd.DataFrame(m1); R["m15"] = pd.DataFrame(m15); R["nb"] = pd.DataFrame(nb)
    for kk in ("dec", "cv", "m1", "m15"):
        print(R[kk].round(2).to_string(), flush=True)

    # ---------------- T47_17 simple controls C0..C4 (T47_18 = NB controls by instrument)
    ctl = []
    for k, mk in mks.items():
        def keep(e):
            return e[mk.pn.sess[e.s.values] >= START]
        c0 = keep(three_red(mk))
        c1, _, _ = E.run_detect(mk, cfg(side=["KEEP", 0], up=["RESET", 1.0]))
        c2, _, _ = E.run_detect(mk, cfg())
        L = {"C0 3 red bars": (keep(c0), "E1"), "C1 3 meaningful legs": (keep(c1), "E1"), "C2 C1+sideways reset": (keep(c2), "E1"),
             "C3 C2+bullish 5m confirm": (keep(c2), "E3"), "C4 C2+true-bottom (NB)": (keep(c2), "NB")}
        for nm, (e_, ent) in L.items():
            for rule in ("X60", "X1600", "REC50"):
                Tt = E.trades(mk, e_, ent, rule)
                ctl.append({"inst": k, "control": nm, "exit": rule, **pnl_summary(mk, Tt, BL[k], rule, nm)})
    R["ctl"] = pd.DataFrame(ctl)
    print(R["ctl"][["inst", "control", "exit", "trades", "avg_trade", "avg_day_2021", "excess_trade", "t_excess", "folds_pos", "remove_top3"]].round(2).to_string(), flush=True)
    for kk, v in R.items():
        if isinstance(v, pd.DataFrame):
            v.to_csv(f"{OUT}/{kk}.csv")
    return R


if __name__ == "__main__":
    main()
