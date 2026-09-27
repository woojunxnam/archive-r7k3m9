"""TEST43-M causal walk-forward historical-analog (kNN) engine.

Decision points: RTH bars closing on the quarter hour from 10:00 to 16:00 (25 per session).
Representation (never raw price):
  SHAPE  ATR-normalised path   (c[t_k] - c[start]) / ATR20_daily   at 5 evenly spaced points of the window
         or range-normalised   (c[t_k] - lowW) / (highW - lowW)     at 6 evenly spaced points
  STATE  families: RANGE (60m / RTH / prior-RTH location), REGIME (tier, trend20/100), VOL (ATR pct, width, eff),
         NESTED (low/high alignment counts, 5D position), VWAP (z), CLOCK (time of day)
Context hierarchy: same broad regime tier and same volatility tercile are enforced by a large distance penalty
(so they act as a first-level filter that degrades gracefully when the cell is thin), then similarity distance.
Library for a query in session s: decision points from sessions <= s - 1 - EMBARGO (strictly before T; the
120m outcome of every library point is resolved long before the query).  Walk-forward in blocks of BLOCK sessions,
library frozen at block start (more conservative than per-session).
Dependence control: at most PER_SESS neighbours per library session; independent campaigns = distinct sessions.
Standardisation constants come from the warm-up library only (first WARMUP sessions).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WARMUP = 250
BLOCK = 20
EMBARGO = 1
PER_SESS = 2
KS = (25, 50, 100, 200)
PENALTY = 25.0
FAMILIES = {
    "RANGE": ["loc60", "pos_rth", "pos_prior"],
    "REGIME": ["tier", "trend20", "trend100"],
    "VOL": ["atr_pct", "wn_60m", "eff_60m"],
    "NESTED": ["n_low", "n_high", "pos_5d"],
    "VWAP": ["vwap_z"],
    "CLOCK": ["clock_min"],
}
TARGETS = ["ret30", "ret60", "ret120", "mfe60", "mae60", "fp05"]


def decision_points(df, bm):
    close_mod = df["mod"].values + bm
    m = df.rth.values & ((close_mod % 15) == 0) & (close_mod >= 600) & (close_mod <= 960)
    return np.where(m)[0]


def shape_matrix(c, lo_hi, atrD, idx, W_bars, norm):
    """Normalised path over the trailing window ending at each decision bar."""
    offs = np.linspace(W_bars, 0, 6).round().astype(int)   # start ... now
    P = np.stack([c[idx - o] for o in offs], 1)
    if norm == "ATR":
        return (P[:, 1:] - P[:, [0]]) / atrD[idx][:, None]
    lo, hi = lo_hi
    w = np.where(hi[idx] - lo[idx] > 0, hi[idx] - lo[idx], np.nan)
    return (P - lo[idx][:, None]) / w[:, None]


def state_matrix(df, idx, families):
    cols = []
    for fam in families:
        for k in FAMILIES[fam]:
            if k == "loc60":
                v = df["rpos_60m"].values[idx]
                v = np.where(np.isnan(v), df["tpos_60m"].values[idx], v)
                v = np.clip(v, -0.5, 1.5)
            elif k == "clock_min":
                v = (df["mod"].values[idx] - 570) / 390.0
            elif k == "vwap_z":
                v = np.clip(df["vwap_z"].values[idx], -3, 3)
            else:
                v = df[k].values[idx].astype(float)
            cols.append((fam, k, v))
    return cols


def assemble(blocks):
    """blocks: list of (family_name, matrix) -> weighted matrix where each family has total weight 1."""
    mats = []
    for fam, M in blocks:
        M = np.asarray(M, float)
        if M.ndim == 1:
            M = M[:, None]
        mats.append((fam, M))
    return mats


def standardise(mats, warm_mask):
    out = []
    for fam, M in mats:
        mu = np.nanmean(M[warm_mask], 0); sd = np.nanstd(M[warm_mask], 0)
        sd = np.where(sd > 1e-9, sd, 1.0)
        Z = (M - mu) / sd
        Z = np.nan_to_num(Z, nan=0.0)
        out.append(Z / np.sqrt(M.shape[1]))     # family total weight = 1
    return np.hstack(out).astype(np.float32)


def knn_walkforward(X, sess_idx, Y, ctx=None, ks=KS, random_ctl=False, seed=7):
    """X: (n, d) features; sess_idx: session ordinal per point; Y: (n, m) targets (NaN allowed).
    ctx: (n, 2) int context (tier, volT) for the hierarchy penalty, or None.
    Returns dict of per-point arrays for each k: mean/std/pup + distance, independent sessions, library meta."""
    n = len(X)
    rng = np.random.default_rng(seed)
    K = max(ks)
    res = {k: {"pred": np.full((n, Y.shape[1]), np.nan), "sd": np.full(n, np.nan), "pup": np.full(n, np.nan),
               "dist": np.full(n, np.nan), "indep": np.zeros(n, int), "nraw": np.zeros(n, int)} for k in ks}
    meta = []
    ok_y = ~np.isnan(Y[:, 1])
    sess_u = np.unique(sess_idx)
    first = sess_u.min()
    for s0 in range(first + WARMUP, sess_u.max() + 1, BLOCK):
        q = np.where((sess_idx >= s0) & (sess_idx < s0 + BLOCK))[0]
        lib = np.where((sess_idx <= s0 - 1 - EMBARGO) & ok_y)[0]
        if len(q) == 0 or len(lib) < 500:
            continue
        meta.append({"block_first_sess": int(s0), "lib_last_sess": int(sess_idx[lib].max()), "n_lib": len(lib),
                     "n_query": len(q)})
        L = X[lib]; ln = (L * L).sum(1)
        for a in range(0, len(q), 400):
            qq = q[a:a + 400]
            Q = X[qq]
            if random_ctl:
                D = rng.random((len(qq), len(lib)), dtype=np.float32)       # random neighbours within context cell
            else:
                D = (Q * Q).sum(1)[:, None] + ln[None, :] - 2.0 * Q @ L.T
                np.maximum(D, 0, out=D)
            if ctx is not None:
                D += PENALTY * (ctx[qq, 0][:, None] != ctx[lib, 0][None, :])
                D += PENALTY * (ctx[qq, 1][:, None] != ctx[lib, 1][None, :])
            C = min(len(lib) - 1, K * 8)
            part = np.argpartition(D, C, axis=1)[:, :C]
            for r, qi in enumerate(qq):
                cand = part[r][np.argsort(D[r, part[r]])]
                ss = sess_idx[lib[cand]]
                # per-session cap (dependence control)
                keep = np.zeros(len(cand), bool); cnt = {}
                for j, s in enumerate(ss):
                    c_ = cnt.get(s, 0)
                    if c_ < PER_SESS:
                        keep[j] = True; cnt[s] = c_ + 1
                sel = cand[keep]
                for k in ks:
                    nb = sel[:k]
                    y = Y[lib[nb]]
                    o = res[k]
                    o["pred"][qi] = np.nanmean(y, 0)
                    o["sd"][qi] = np.nanstd(y[:, 1])
                    o["pup"][qi] = np.nanmean(y[:, 1] > 0)
                    o["dist"][qi] = float(np.sqrt(np.median(D[r, nb]))) if not random_ctl else 0.0
                    o["indep"][qi] = len(np.unique(sess_idx[lib[nb]]))
                    o["nraw"][qi] = len(nb)
    return res, pd.DataFrame(meta)


def confidence(pred, sd, dist, indep, k, sess_idx):
    """HIGH / MED / LOW / NO_MATCH.  Distance thresholds are causal: quantiles of the distances observed in
    PREVIOUS blocks (sessions strictly before the current block)."""
    n = len(pred)
    conf = np.array(["NO_MATCH"] * n, dtype=object)
    agree = np.abs(pred) / (sd / np.sqrt(np.maximum(indep, 1)))
    order = np.argsort(sess_idx, kind="stable")
    seen = []
    sess_sorted = sess_idx[order]
    blocks = np.unique(sess_sorted[~np.isnan(pred[order])] // BLOCK) if np.any(~np.isnan(pred)) else []
    for bk in blocks:
        m = (sess_idx // BLOCK == bk) & ~np.isnan(pred)
        if len(seen) >= 200:
            ref = np.concatenate(seen)
            q50, q75, q90 = np.quantile(ref, [0.5, 0.75, 0.9])
        else:
            q50 = q75 = q90 = np.inf
        d = dist[m]; a = agree[m]; ind = indep[m]
        c = np.where(np.isnan(d) | (ind < max(10, k // 5)) | (d > q90), "NO_MATCH",
                     np.where((d <= q50) & (a >= 2.0) & (ind >= k // 3), "HIGH",
                              np.where((d <= q75) & (a >= 1.0), "MED", "LOW")))
        if not np.isfinite(q90):
            c = np.where(np.isnan(d) | (ind < max(10, k // 5)), "NO_MATCH", np.where(a >= 2.0, "MED", "LOW"))
        conf[m] = c
        seen.append(d[~np.isnan(d)])
    return conf
