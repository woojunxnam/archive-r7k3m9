"""TEST84+ AUCTION-PROFILE LAB shared layer.  1m OHLCV -> APPROXIMATE volume profiles (explicit allocation proxies VP-A/B/C), causal profile
features on the 5m decision grid, controls A-D, event labelling, registries.  Research data <= 2026-05-27; T61 frozen (verified on import)."""
import datetime
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402  (loads data, verifies frozen T61)
import t45_common as C45  # noqa: E402

AP = os.path.join(B.LAB, "out", "AUCTION_PROFILE_LAB"); REPA = os.path.join(B.LAB, "reports", "AUCTION_PROFILE_LAB")
os.makedirs(AP, exist_ok=True); os.makedirs(REPA, exist_ok=True)
NG, J15, J16 = B.NG, B.J15, B.J16
NB5 = NG // 5                                 # 81 decision slots: j = 5b+4
DEC = np.arange(NB5) * 5 + 4
PROXY = {"VP-A": 0, "VP-B": 1, "VP-C": 2}
RET_EDGES = np.array([-0.5, -0.2, 0.0, 0.2, 0.5]); R15_EDGES = np.array([-0.1, -0.03, 0.03, 0.1]); RV_EDGES = np.array([0.8, 1.25])


def reg_append(name, rows, key=None):
    p = os.path.join(AP, f"{name}.csv")
    df = pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    if key:
        df = df.drop_duplicates(key, keep="last")
    df.to_csv(p, index=False)


def budget(test, hypotheses=0, ml_configs=0, genomes=0, note=""):
    reg_append("PROFILE_RESEARCH_BUDGET", [{"test": test, "hypotheses": hypotheses, "ml_configs": ml_configs, "valid_genomes": genomes, "note": note,
                                           "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}], key="test")


def prereg(test, spec):
    d = os.path.join(AP, test); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{test}_PREREGISTRATION.json")
    if os.path.exists(p):
        return open(p + ".sha256").read().strip()
    json.dump({"test": test, "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "program_prereg_sha256": open(os.path.join(AP, "TEST84", "TEST84_PLUS_PREREGISTRATION.json.sha256")).read().strip(), **spec},
              open(p, "w"), indent=1, default=str)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n")
    return h


def md(name, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(os.path.join(REPA, name), "w").write("\n".join(lines) + "\n")


# ------------------------------------------------------------------------------------------------------------------ profile kernels
@njit(cache=True)
def _hist(H, L, C, V, a, b, bw, proxy):
    """histogram over absolute bins for bars a..b-1 (one session row).  returns (bin0, hist) ; empty -> (0, zeros(1))."""
    bmin = 1 << 60; bmax = -(1 << 60)
    for k in range(a, b):
        if V[k] <= 0 or H[k] != H[k]:
            continue
        lo = int(np.floor(L[k] / bw)); hi = int(np.floor(H[k] / bw))
        if lo < bmin:
            bmin = lo
        if hi > bmax:
            bmax = hi
    if bmax < bmin:
        return 0, np.zeros(1)
    h = np.zeros(bmax - bmin + 1)
    for k in range(a, b):
        v = V[k]
        if v <= 0 or H[k] != H[k]:
            continue
        tp = (H[k] + L[k] + C[k]) / 3.0; lo = int(np.floor(L[k] / bw)); hi = int(np.floor(H[k] / bw)); t = int(np.floor(tp / bw))
        if proxy == 0 or hi == lo:
            h[t - bmin] += v
        elif proxy == 1:
            w = v / (hi - lo + 1)
            for q in range(lo, hi + 1):
                h[q - bmin] += w
        else:
            half = max(t - lo, hi - t) + 1.0; tot = 0.0
            for q in range(lo, hi + 1):
                tot += 1.0 - abs(q - t) / half
            for q in range(lo, hi + 1):
                h[q - bmin] += v * (1.0 - abs(q - t) / half) / tot
    return bmin, h


@njit(cache=True)
def _stats(bmin, h, bw, pct, above):
    """POC, VAH, VAL, volume-weighted median, width, share of volume with bin centre > above."""
    tot = h.sum()
    if tot <= 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan
    cum = 0.0; med = 0
    for i in range(h.shape[0]):
        cum += h[i]
        if cum >= 0.5 * tot:
            med = i; break
    mx = h.max(); poc = -1; best = 1 << 30
    for i in range(h.shape[0]):
        if h[i] == mx and abs(i - med) < best:
            best = abs(i - med); poc = i
    lo = poc; hi = poc; acc = h[poc]; n = h.shape[0]
    while acc < pct * tot and (lo > 0 or hi < n - 1):
        dn = h[lo - 1] if lo > 0 else -1.0; up = h[hi + 1] if hi < n - 1 else -1.0
        if up >= dn:
            hi += 1; acc += up
        else:
            lo -= 1; acc += dn
    ab = 0.0
    for i in range(n):
        if (bmin + i + 0.5) * bw > above:
            ab += h[i]
    return (bmin + poc + 0.5) * bw, (bmin + hi + 1) * bw, (bmin + lo) * bw, (bmin + med + 0.5) * bw, (hi - lo + 1) * bw, ab / tot


@njit(cache=True)
def session_features(H, L, C, V, atr, f_bin, proxy, pct, J15_):
    """per session s and decision slot b (j = 5b+4): P1 (prior RTH) POC/VAH/VAL (per session), P2 developing, P4 rolling 60 (+P3 30, P5 120) POC/VAH/VAL/
    VWMED/width, P2 share above P1 VAH, P4 high-low range.  Only bars <= j (and prior sessions) are read."""
    n = H.shape[0]; nb = (J15_ + 1) // 5
    P1 = np.full((n, 3), np.nan)
    F = np.full((n, nb, 17), np.nan)
    for s in range(1, n):
        bw = f_bin * atr[s]
        if not bw > 0:
            continue
        b0, h = _hist(H[s - 1], L[s - 1], C[s - 1], V[s - 1], 0, J15_ + 1, bw, proxy)
        p = _stats(b0, h, bw, pct, 1e18); P1[s, 0] = p[0]; P1[s, 1] = p[1]; P1[s, 2] = p[2]
        for b in range(nb):
            j = 5 * b + 4
            if j > J15_:
                break
            for q, win in enumerate((0, 30, 60, 120)):
                a = 0 if win == 0 else max(0, j + 1 - win)
                bb, hh = _hist(H[s], L[s], C[s], V[s], a, j + 1, bw, proxy)
                st = _stats(bb, hh, bw, pct, P1[s, 1] if P1[s, 1] == P1[s, 1] else 1e18)
                if q == 0:
                    F[s, b, 0] = st[0]; F[s, b, 1] = st[1]; F[s, b, 2] = st[2]; F[s, b, 3] = st[3]; F[s, b, 4] = st[4]; F[s, b, 5] = st[5]
                elif q == 2:
                    F[s, b, 6] = st[0]; F[s, b, 7] = st[1]; F[s, b, 8] = st[2]; F[s, b, 9] = st[3]; F[s, b, 10] = st[4]
                    hi_ = -1e18; lo_ = 1e18
                    for k in range(a, j + 1):
                        if H[s, k] > hi_:
                            hi_ = H[s, k]
                        if L[s, k] < lo_:
                            lo_ = L[s, k]
                    F[s, b, 11] = hi_ - lo_
                elif q == 1:
                    F[s, b, 12] = st[0]; F[s, b, 13] = st[4]
                else:
                    F[s, b, 14] = st[0]; F[s, b, 15] = st[4]
            F[s, b, 16] = j
    return P1, F


FEAT = {"P2_POC": 0, "P2_VAH": 1, "P2_VAL": 2, "P2_VWMED": 3, "P2_WIDTH": 4, "P2_ABOVE_P1VAH": 5, "P4_POC": 6, "P4_VAH": 7, "P4_VAL": 8, "P4_VWMED": 9,
        "P4_WIDTH": 10, "P4_RANGE": 11, "P3_POC": 12, "P3_WIDTH": 13, "P5_POC": 14, "P5_WIDTH": 15}


@njit(cache=True)
def p1_nodes(H, L, C, V, atr, f_bin, proxy, J15_, maxn):
    """HVN / LVN of the prior RTH profile (3-bin smoothed): arrays (n, maxn, 3) = centre, lower edge, upper edge (nan padded)."""
    n = H.shape[0]; HV = np.full((n, maxn, 3), np.nan); LV = np.full((n, maxn, 3), np.nan)
    for s in range(1, n):
        bw = f_bin * atr[s]
        if not bw > 0:
            continue
        b0, h = _hist(H[s - 1], L[s - 1], C[s - 1], V[s - 1], 0, J15_ + 1, bw, proxy)
        m = h.shape[0]
        if m < 5:
            continue
        sm = np.zeros(m)
        for i in range(m):
            a = max(0, i - 1); b = min(m, i + 2); sm[i] = h[a:b].mean()
        nz = sm[sm > 0]
        if nz.shape[0] == 0:
            continue
        med = np.median(nz); nh = 0; hidx = np.full(m, -1)
        for i in range(1, m - 1):
            if sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1] and sm[i] >= 1.5 * med and nh < maxn:
                lo = i
                while lo > 0 and sm[lo - 1] >= 0.75 * sm[i]:
                    lo -= 1
                hi = i
                while hi < m - 1 and sm[hi + 1] >= 0.75 * sm[i]:
                    hi += 1
                HV[s, nh, 0] = (b0 + i + 0.5) * bw; HV[s, nh, 1] = (b0 + lo) * bw; HV[s, nh, 2] = (b0 + hi + 1) * bw; hidx[nh] = i; nh += 1
        nl = 0
        for k in range(nh - 1):
            a = hidx[k]; b = hidx[k + 1]
            if b - a < 2:
                continue
            mi = a + 1
            for i in range(a + 1, b):
                if sm[i] < sm[mi]:
                    mi = i
            if sm[mi] <= 0.5 * med and nl < maxn:
                LV[s, nl, 0] = (b0 + mi + 0.5) * bw; LV[s, nl, 1] = (b0 + mi) * bw; LV[s, nl, 2] = (b0 + mi + 1) * bw; nl += 1
    return HV, LV


def rel_volume(I):
    """last-30m volume / median of the same window over the previous 20 sessions (causal); n x NG."""
    cv = np.cumsum(I.V, 1); w30 = cv - np.concatenate([np.zeros((I.n, 30)), cv[:, :-30]], 1)
    ref = pd.DataFrame(w30).rolling(20, min_periods=10).median().shift(1).values
    return np.where(ref > 0, w30 / ref, np.nan)


def buckets(I):
    r = (I.C - I.FP[:, :1]) / I.atr[:, None]
    r15 = (I.C - np.concatenate([I.C[:, :1].repeat(15, 1), I.C[:, :-15]], 1)) / I.atr[:, None]
    rv = rel_volume(I)
    return {"B": np.digitize(r, RET_EDGES).astype(np.int64), "D": np.digitize(r15, R15_EDGES).astype(np.int64),
            "C": np.where(np.isnan(rv), 9, np.digitize(rv, RV_EDGES)).astype(np.int64)}


@njit(cache=True)
def ctl_bucket(FP, FPb, nxt, gidx, gptr, gpos_s, BK, s_arr, jin, jx, kind, pv, cs, use_bk):
    m = s_arr.shape[0]; out = np.full(m, np.nan)
    for e in range(m):
        g = gpos_s[s_arr[e]]; a, b = gptr[g], gptr[g + 1]; bk = BK[s_arr[e], jin[e] - 1]
        tot = 0.0; cnt = 0
        for q in range(a, b):
            ss = gidx[q]
            if use_bk and BK[ss, jin[e] - 1] != bk:
                continue
            xo = nxt[ss] if kind[e] == 1 else FPb[ss, jx[e]]
            xi = FP[ss, jin[e]]
            if xo != xo or xi != xi:
                continue
            tot += (xo - xi) * pv - 2 * cs; cnt += 1
        if cnt > 0:
            out[e] = tot / cnt
    return out


HZ = {"h15": 15, "h30": 30, "h60": 60, "h120": 120, "h1100": ("abs", "11:00"), "h1300": ("abs", "13:00"), "h1600": ("abs", "16:00"), "h1615": ("abs", "16:15"),
      "hNEXTOPEN": "NXT"}


def label(I, E, BK):
    """E: DataFrame with s, j (decision minute).  Adds per-horizon net, net4 and excess vs controls A/B/C/D."""
    s = E.s.values.astype(np.int64); ji = E.j.values.astype(np.int64) + 1; px = I.FP[s, ji]
    for h, v in HZ.items():
        valid = np.ones(len(E), bool)
        if v == "NXT":
            xo = I.nxt_open[s]; jj = np.full(len(E), J15, np.int64); kind = np.ones(len(E), np.int64)
        else:
            if isinstance(v, tuple):
                ja = C45.g(v[1]) if v[1] != "16:15" else J15
                ja = min(ja, J15); jj = np.full(len(E), ja, np.int64); valid = ji < ja
            else:
                jj = np.minimum(ji + v, J15)
            jj = np.maximum(jj, ji); xo = I.FPb[s, jj]; kind = np.zeros(len(E), np.int64)
        g = (xo - px) * I.pv
        net = np.where(valid, g - 2 * I.cs, np.nan); E[f"{h}_net"] = net; E[f"{h}_net4"] = np.where(valid, g - 2 * I.cs4, np.nan)
        E[f"{h}_A"] = net - ctl_bucket(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, BK["B"], s, ji, jj, kind, I.pv, I.cs, False)
        for c in ("B", "C", "D"):
            E[f"{h}_{c}"] = net - ctl_bucket(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, BK[c], s, ji, jj, kind, I.pv, I.cs, True)
    return E


def summarize(E, nd, keys):
    rows = []
    for k, g in E.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        for h in HZ:
            x = g.dropna(subset=[f"{h}_net"])
            if len(x) < 30:
                continue
            fb = {nm: x[(x.date >= a) & (x.date <= b)][f"{h}_B"].mean() for nm, a, b in B.FOLDS}
            fn = {nm: int(((x.date >= a) & (x.date <= b)).sum()) for nm, a, b in B.FOLDS}
            rows.append({**dict(zip(keys, k)), "horizon": h, "n": len(x), "per_day": len(x) / nd, "net": x[f"{h}_net"].mean(), "net4": x[f"{h}_net4"].mean(),
                         "A": x[f"{h}_A"].mean(), "B": x[f"{h}_B"].mean(), "C": x[f"{h}_C"].mean(), "D": x[f"{h}_D"].mean(), "B_day": x[f"{h}_B"].sum() / nd,
                         "folds_B_pos": int(sum(v > 0 for v in fb.values() if v == v)), "fold_median_B": float(np.nanmedian(list(fb.values()))),
                         "min_fold_n": min(fn.values()), **{f"B_{nm}": v for nm, v in fb.items()}})
    return pd.DataFrame(rows)
