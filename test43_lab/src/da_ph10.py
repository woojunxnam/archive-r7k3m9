"""PH10 novelty reserve: NR1 intraday periodicity, NR2 round numbers, NR3 pre-holiday (prereg 8547410)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_ph3_eval as EV  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402

OUT = os.path.join(R.OUT, "ph10"); os.makedirs(OUT, exist_ok=True); NB = P.NB; HZ = ["h6", "h12", "h24", "h1615"]
SPACING = {"ES": (100, 25), "NQ": (500, 100), "YM": (1000, 250), "RTY": (50, 10)}


def econ(dates, usd, usd4, npop):
    m = EC.metrics(np.asarray(dates), np.asarray(usd), np.asarray(usd4), npop); m["tier_b"] = EC.tier_b(m); return m


def summarize_x(x, r, dates, years, insts, cost):
    ok = ~np.isnan(x); lo, hi = P.boot(x[ok], dates[ok]) if ok.sum() >= 20 else (np.nan, np.nan)
    yy = pd.Series(x[ok]).groupby(years[ok]).mean(); ii = pd.Series(x[ok]).groupby(insts[ok]).mean()
    return {"n": int(ok.sum()), "R": float(np.nanmean(r)), "x": float(np.nanmean(x)), "lo": lo, "hi": hi, "years_pos": int((yy > 0).sum()), "inst_pos": int((ii > 0).sum()), "cost_atr": float(np.nanmean(cost))}


def main():
    M = P.markets(); res = {}
    # ---------------- NR1 ----------------
    rows = []
    for i in P.INSTS:
        m = M[i]; I = m.I; js = 30 + 30 * np.arange(12); je = js + 30
        r = (I.FP[:, je] - I.FP[:, js]) / m.a[:, None]; ok = m.full & (m.a > 0)
        for L in (5, 20):
            sig = np.full(r.shape, False)
            rr = np.where(ok[:, None], r, np.nan); roll = pd.DataFrame(rr).rolling(L, min_periods=L).mean().shift(1).values; sig = roll > 0
            for k in range(12):
                d = pd.DataFrame({"def": f"NR1_L{L}", "inst": i, "s": np.arange(m.n), "slot": k, "sig": sig[:, k], "R": r[:, k], "year": I.year, "vt": I.vt, "ok": ok,
                                  "date": np.asarray(I.sess.values, "datetime64[D]").astype(np.int64), "atr": m.a, "pv": I.pv, "cs": I.cs, "cs4": I.cs4, "cost": m.cost})
                rows.append(d)
    N1 = pd.concat(rows); N1 = N1[N1.ok & N1.R.notna()]
    N1["null"] = N1.groupby(["def", "inst", "year", "vt", "slot"]).R.transform("mean"); N1["x"] = N1.R - N1["null"]
    for L in (5, 20):
        E = N1[(N1["def"] == f"NR1_L{L}") & N1.sig]
        o = summarize_x(E.x.values, E.R.values, E.date.values, E.year.values, E.inst.values, E.cost.values)
        W = E[E.year >= 2021]; usd = W.R * W.atr * W.pv - 2 * W.cs; usd4 = W.R * W.atr * W.pv - 2 * W.cs4
        o["econ"] = econ(W.date.values, usd.values, usd4.values, int((N1[(N1['def'] == f'NR1_L{L}') & (N1.year >= 2021)]).shape[0]))
        o["gate"] = bool(o["x"] > 0 and o["years_pos"] >= 5 and o["inst_pos"] >= 3 and o["R"] >= 0.9 * o["cost_atr"]); res[f"NR1_L{L}"] = o
    # ---------------- NR2 ----------------
    T2 = []
    for i in P.INSTS:
        m = M[i]; A = m.a[:, None]
        rng12 = (pd.Series(m.h.ravel()).rolling(12).max() - pd.Series(m.l.ravel()).rolling(12).min()).values.reshape(m.n, NB) / A
        d6 = (pd.Series(m.c.ravel()) - pd.Series(m.c.ravel()).shift(6)).values.reshape(m.n, NB) / A; pop = m.valid.copy()
        bins = [P.causal_bins(m, pop, d6, 3), P.causal_bins(m, pop, rng12, 3)]
        X = {h: m.R[h] - P.cell_null(m, np.zeros_like(pop), pop, h, bins, target=pop)[0] for h in HZ}
        pc = np.concatenate([np.full((m.n, 1), np.nan), m.c[:, :-1]], 1)
        for cls, sp in (("MAJOR", SPACING[i][0]), ("MINOR", SPACING[i][1])):
            for tag, off in (("NR2", 0.0), ("NR2P", 0.5)):
                k_prev = np.floor((pc - off * sp) / sp); k_now = np.floor((m.c - off * sp) / sp); cross = (k_now > k_prev) & (m.bidx >= 1) & m.valid & (m.bidx <= 67)
                ev = cross & (np.cumsum(cross, 1) == 1); ss, bb = np.where(ev)
                d = pd.DataFrame({"def": f"{tag}_{cls}", "inst": i, "s": ss, "b": bb, "date": m.date[ss, bb], "year": m.year[ss, bb], "cost": m.cost[ss], "atr": m.a[ss], "pv": m.I.pv, "cs": m.I.cs, "cs4": m.I.cs4})
                for h in HZ:
                    d[f"R_{h}"] = m.R[h][ss, bb]; d[f"x_{h}"] = X[h][ss, bb]
                T2.append(d)
    T2 = pd.concat(T2, ignore_index=True); cmp = []
    for dn, d in T2.groupby("def"):
        o = {h: summarize_x(d[f"x_{h}"].values, d[f"R_{h}"].values, d.date.values, d.year.values, d.inst.values, d.cost.values) for h in HZ}
        pos = [h for h in HZ if o[h]["x"] > 0]
        g = len(pos) >= 2 and max(o[h]["years_pos"] for h in pos) >= 5 and max(o[h]["inst_pos"] for h in pos) >= 3 and max(o[h]["R"] for h in ("h12", "h24", "h1615")) >= 0.9 * o["h1615"]["cost_atr"]
        res[dn] = {"by_horizon": o, "gate": bool(g)}
        if dn.startswith("NR2_"):
            W = d[d.year >= 2021]; usd = W.R_h1615 * W.atr * W.pv - 2 * W.cs; usd4 = W.R_h1615 * W.atr * W.pv - 2 * W.cs4
            res[dn]["econ_1615"] = econ(W.date.values, usd.values, usd4.values, len(W))
    for cls in ("MAJOR", "MINOR"):
        for h in HZ:
            dd, lo, hi = EV.cmpdiff(T2, f"NR2_{cls}", f"NR2P_{cls}", h); cmp.append({"class": cls, "horizon": h, "round_minus_pseudo": dd, "ci_lo": lo, "ci_hi": hi})
    res["NR2_ROUND_MINUS_PSEUDO"] = cmp
    # ---------------- NR3 ----------------
    rows = []
    for i in P.INSTS:
        m = M[i]; I = m.I; sess = pd.DatetimeIndex(I.sess); d64 = sess.values.astype("datetime64[D]"); nxt = np.r_[d64[1:], d64[-1] + 1]
        pre = np.busday_count(d64, nxt) > 1; pre[-1] = False; r = (I.FP[:, 404] - I.FP[:, 0]) / m.a; ok = m.full & (m.a > 0) & ~np.isnan(r)
        rows.append(pd.DataFrame({"inst": i, "pre": pre, "R": r, "ok": ok, "year": I.year, "vt": I.vt, "date": d64.astype(np.int64), "atr": m.a, "pv": I.pv, "cs": I.cs, "cs4": I.cs4, "cost": m.cost}))
    N3 = pd.concat(rows); N3 = N3[N3.ok]; base = N3[~N3.pre].groupby(["inst", "year", "vt"]).R.mean()
    E3 = N3[N3.pre].copy(); E3["x"] = E3.R - base.reindex(pd.MultiIndex.from_frame(E3[["inst", "year", "vt"]])).values
    o = summarize_x(E3.x.values, E3.R.values, E3.date.values, E3.year.values, E3.inst.values, E3.cost.values)
    W = E3[E3.year >= 2021]; o["econ"] = econ(W.date.values, (W.R * W.atr * W.pv - 2 * W.cs).values, (W.R * W.atr * W.pv - 2 * W.cs4).values, len(W))
    o["gate"] = bool(o["x"] > 0 and o["years_pos"] >= 5 and o["inst_pos"] >= 3 and o["R"] >= 0.9 * o["cost_atr"]); res["NR3_PREHOLIDAY"] = o
    json.dump(res, open(os.path.join(OUT, "PH10_RESULTS.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
