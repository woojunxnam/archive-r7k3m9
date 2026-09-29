"""AUDIT 3: NR1 / NR3 strictly historical causal nulls (prereg 05a17c8)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, "out", "final_index_closure_audit_v1")


def prior_mean(pool, keys, target):
    """mean of pool.R over rows with the same keys and date strictly before each target row's date."""
    g = pool.groupby(keys + ["date"]).R.agg(["sum", "count"]).reset_index().sort_values(keys + ["date"])
    g["ps"] = g.groupby(keys)["sum"].cumsum() - g["sum"]; g["pc"] = g.groupby(keys)["count"].cumsum() - g["count"]
    t = target[keys + ["date"]].copy(); t["_i"] = np.arange(len(t)); t = t.sort_values("date")
    out = np.full(len(target), np.nan); cnt = np.zeros(len(target))
    for key, tt in t.groupby(keys):
        gg = g[(g[keys] == pd.Series(key if isinstance(key, tuple) else (key,), index=keys)).all(1)] if keys else g
        if not len(gg):
            continue
        idx = np.searchsorted(gg.date.values, tt.date.values, side="left") - 1          # last pool date strictly before
        ok = idx >= 0; ps = np.where(ok, gg.ps.values[np.maximum(idx, 0)] + gg["sum"].values[np.maximum(idx, 0)], 0)
        pc = np.where(ok, gg.pc.values[np.maximum(idx, 0)] + gg["count"].values[np.maximum(idx, 0)], 0)
        out[tt._i.values] = np.where(pc > 0, ps / np.maximum(pc, 1), np.nan); cnt[tt._i.values] = pc
    return out, cnt


def causal_null(pool, target, levels, minn=20):
    null = np.full(len(target), np.nan); lev = np.full(len(target), -1)
    for li, keys in enumerate(levels):
        m, c = prior_mean(pool, keys, target); sel = np.isnan(null) & (c >= minn); null[sel] = m[sel]; lev[sel] = li
    return null, lev


def summ(E, x):
    ok = ~np.isnan(x); lo, hi = P.boot(x[ok], E.date.values[ok])
    yy = pd.Series(x[ok]).groupby(E.year.values[ok]).mean(); ii = pd.Series(x[ok]).groupby(E.inst.values[ok]).mean()
    return {"n": int(ok.sum()), "R": float(E.R.mean()), "x": float(np.nanmean(x)), "ci_lo": lo, "ci_hi": hi, "years_pos": int((yy > 0).sum()), "years": int(yy.size), "inst_pos": int((ii > 0).sum()),
            "cost_atr": float(E.cost.mean())}


def main():
    M = P.markets(); res = {}
    rows = []
    for i in P.INSTS:
        m = M[i]; I = m.I; js = 30 + 30 * np.arange(12); je = js + 30; r = (I.FP[:, je] - I.FP[:, js]) / m.a[:, None]; ok = m.full & (m.a > 0)
        rr = np.where(ok[:, None], r, np.nan)
        sig = {L: pd.DataFrame(rr).rolling(L, min_periods=L).mean().shift(1).values > 0 for L in (5, 20)}
        for k in range(12):
            rows.append(pd.DataFrame({"inst": i, "slot": k, "R": r[:, k], "ok": ok, "sig5": sig[5][:, k], "sig20": sig[20][:, k], "year": I.year, "vt": I.vt,
                                      "date": np.asarray(I.sess.values, "datetime64[D]").astype(np.int64), "atr": m.a, "pv": I.pv, "cs": I.cs, "cs4": I.cs4, "cost": m.cost}))
    A = pd.concat(rows, ignore_index=True); A = A[A.ok & A.R.notna()].reset_index(drop=True)
    A["old_null"] = A.groupby(["inst", "year", "vt", "slot"]).R.transform("mean")
    for L in (5, 20):
        E = A[A[f"sig{L}"]].reset_index(drop=True)
        nl, lev = causal_null(A, E, [["inst", "vt", "slot"], ["inst", "slot"], ["slot"]]); x = E.R.values - nl
        o = summ(E, x); o["old_within_year_x"] = float((E.R - E.old_null).mean()); o["fallback"] = {int(k): int(v) for k, v in pd.Series(lev).value_counts().items()}
        W = E[E.year >= 2021]; usd = (W.R * W.atr * W.pv - 2 * W.cs).values; usd4 = (W.R * W.atr * W.pv - 2 * W.cs4).values
        econ = EC.metrics(W.date.values, usd, usd4, len(A[A.year >= 2021]) // 1); econ["tier_b"] = EC.tier_b(econ); o["econ"] = {k: econ[k] for k in ("avg_day", "slip4_avg_day", "folds_pos", "trades", "tier_b", "max_dd")}
        gate = o["x"] > 0 and o["years_pos"] >= 5 and o["inst_pos"] >= 3 and o["R"] >= 0.9 * o["cost_atr"]
        o["class"] = "NR1_CAUSAL_REJECT" if o["x"] <= 0 else ("NR1_CAUSAL_ECONOMIC_CANDIDATE" if gate and econ["tier_b"] else "NR1_CAUSAL_CLUE"); res[f"NR1_L{L}"] = o
    rows = []
    for i in P.INSTS:
        m = M[i]; I = m.I; d64 = pd.DatetimeIndex(I.sess).values.astype("datetime64[D]"); nxt = np.r_[d64[1:], d64[-1] + 1]
        pre = np.busday_count(d64, nxt) > 1; pre[-1] = False; r = (I.FP[:, 404] - I.FP[:, 0]) / m.a; ok = m.full & (m.a > 0) & ~np.isnan(r)
        rows.append(pd.DataFrame({"inst": i, "pre": pre, "R": r, "ok": ok, "year": I.year, "vt": I.vt, "date": d64.astype(np.int64), "atr": m.a, "pv": I.pv, "cs": I.cs, "cs4": I.cs4, "cost": m.cost}))
    B = pd.concat(rows, ignore_index=True); B = B[B.ok].reset_index(drop=True); pool = B[~B.pre]; E = B[B.pre].reset_index(drop=True)
    old = pool.groupby(["inst", "year", "vt"]).R.mean(); E["old_null"] = old.reindex(pd.MultiIndex.from_frame(E[["inst", "year", "vt"]])).values
    nl, lev = causal_null(pool, E, [["inst", "vt"], ["inst"]]); x = E.R.values - nl
    o = summ(E, x); o["old_within_year_x"] = float((E.R - E.old_null).mean()); o["fallback"] = {int(k): int(v) for k, v in pd.Series(lev).value_counts().items()}
    W = E[E.year >= 2021]; econ = EC.metrics(W.date.values, (W.R * W.atr * W.pv - 2 * W.cs).values, (W.R * W.atr * W.pv - 2 * W.cs4).values, len(W)); econ["tier_b"] = EC.tier_b(econ)
    o["econ"] = {k: econ[k] for k in ("avg_day", "slip4_avg_day", "folds_pos", "trades", "tier_b", "max_dd", "remove_top3", "worst_fold")}
    gate = o["x"] > 0 and o["years_pos"] >= 5 and o["inst_pos"] >= 3 and o["R"] >= 0.9 * o["cost_atr"]
    o["class"] = "NR3_CAUSAL_REJECT" if o["x"] <= 0 else ("NR3_CAUSAL_ECONOMIC_CANDIDATE" if gate and econ["tier_b"] else "NR3_CAUSAL_CLUE"); res["NR3_PREHOLIDAY"] = o
    json.dump(res, open(os.path.join(OUT, "AUDIT3_CAUSAL_NULL.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
