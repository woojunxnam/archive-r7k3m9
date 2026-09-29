"""checkpoint / action-value machinery for management audits (INDEX_DISCRETIONARY_ALPHA_CONTINUOUS_V1)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402

FOLD_OF = {y: k for k, (a, b) in EC.FOLDS.items() for y in range(a, b + 1)}


def checkpoints(T, min_left=30):
    """all completed 5m checkpoints of each base trade with causal state and hypothetical ADD1 outcome (to the frozen base exit)."""
    M = P.markets(); rows = []
    for t, r in enumerate(T.itertuples(index=False)):
        m = M[r.inst]; I = m.I; s = int(r.s)
        for k in range(int(r.b) + 1, 80):
            ja = 5 * k + 5
            if ja > r.j_out - min_left:
                break
            pa = I.FP[s, ja]; c = m.c[s, k]
            hi = np.nanmax(I.H[s, r.j_in:5 * k + 5]); lo = np.nanmin(I.L[s, r.j_in:5 * k + 5])
            rows.append({"trade": t, "inst": r.inst, "s": s, "k": k, "date": int(r.date), "year": int(r.year), "vt": int(r.vt), "tod3": int(np.digitize(k, [30, 54])),
                         "elapsed": k - int(r.b), "remaining": (r.j_out - ja) / 5.0, "upnl_atr": (c - r.px_in) / r.atr, "mfe_atr": (hi - r.px_in) / r.atr,
                         "mae_atr": (r.px_in - lo) / r.atr, "sess_ret": (c - m.open0[s]) / r.atr, "winner": bool(c > r.px_in), "under": bool(c < r.px_in),
                         "add_R": (r.px_out - pa) / r.atr, "add_usd": (r.px_out - pa) * r.pv - 2 * r.cs, "add_usd4": (r.px_out - pa) * r.pv - 2 * r.cs4,
                         "atr": r.atr, "pv": r.pv, "cs": r.cs, "cs4": r.cs4, "px_out": r.px_out})
    return pd.DataFrame(rows)


def causal_terciles(C, col, pop):
    per = pd.to_datetime(C.date, unit="D").dt.to_period("M").values; out = np.full(len(C), -1); x = C[col].values
    for mo in np.unique(per):
        rows = np.where(per == mo)[0]; start = C.date.values[rows].min(); prior = x[(C.date.values < start) & pop]; prior = prior[~np.isnan(prior)]
        if len(prior) < 50:
            continue
        e = np.percentile(prior, [100 / 3, 200 / 3]); out[rows] = np.digitize(x[rows], e)
    return out


def matched_control(C, sig, pool, cols=("elapsed", "upnl_atr", "remaining")):
    """per signal row: cell-mean add_R of pool rows; cells inst x vt x tod3 x terciles(cols); fallback drop vt, then inst."""
    T = {c: causal_terciles(C, c, pool) for c in cols}; ok = np.all([T[c] >= 0 for c in cols], 0)
    ctl = np.full(len(C), np.nan); lev = np.full(len(C), -1)
    keys = [["inst", "vt", "tod3"], ["inst", "tod3"], ["tod3"]]
    for li, kk in enumerate(keys):
        key = C[kk].astype(str).agg("|".join, axis=1) + "|" + pd.Series(list(zip(*[T[c] for c in cols]))).astype(str)
        g = pd.DataFrame({"k": key[pool & ok], "r": C.add_R[pool & ok]}).groupby("k").r.agg(["mean", "count"]); g = g[g["count"] >= 10]
        mv = g["mean"].reindex(key).values; sel = sig & ok & np.isnan(ctl) & ~np.isnan(mv); ctl[sel] = mv[sel]; lev[sel] = li
    return ctl, lev


def summarize(v, dates, years, insts, v4=None):
    v = np.asarray(v, float); ok = ~np.isnan(v); lo, hi = P.boot(v[ok], np.asarray(dates)[ok]) if ok.sum() >= 20 else (np.nan, np.nan)
    fy = pd.Series(v[ok]).groupby([FOLD_OF.get(int(y), "NA") for y in np.asarray(years)[ok]]).sum(); iy = pd.Series(v[ok]).groupby(np.asarray(insts)[ok]).mean()
    yy = pd.Series(v[ok]).groupby(np.asarray(years)[ok]).mean()
    o = {"n": int(ok.sum()), "mean": float(v[ok].mean()) if ok.any() else np.nan, "ci_lo": lo, "ci_hi": hi, "folds_pos": int((fy > 0).sum()),
         "inst_pos": int((iy > 0).sum()), "years_pos": int((yy > 0).sum()), "years": int(yy.size)}
    if v4 is not None:
        o["slip4_mean"] = float(np.nanmean(np.asarray(v4, float)[ok]))
    return o
