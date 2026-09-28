"""TEST97 event-study engine (prereg d6fb544b).  5m RTH bars b = 0..80; signal on completed bar b -> entry at the open of bar b+1 (grid 5b+5).
Precomputes, for EVERY (session, bar): forward returns at bar horizons / 16:00 / 16:15 (ATR_d units), 1m path statistics (60-min MFE / MAE, time to
MFE, barrier races, new-high, underwater at 16:15, time to first positive, time to recovery), bar-shape features and the null cells (A time/regime,
B magnitude, C basic momentum).  Event studies are then masked reductions with date-clustered bootstrap inference pooled across instruments."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import t96_data as X  # noqa: E402

OUT = os.path.join(B.LAB, "out", "t97"); os.makedirs(OUT, exist_ok=True)
REP = os.path.join(B.LAB, "reports", "TEST97_PLUS"); os.makedirs(REP, exist_ok=True)
INSTS = ("ES", "NQ", "YM", "RTY")
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K"}
HB = [1, 2, 3, 4, 6, 9, 12]; HZ = [f"h{h}" for h in HB] + ["h1600", "h1615"]
J15, J16 = B.J15, B.J16; NB = 81; BMAX_COMMON = 67
TOD_EDGES = [6, 18, 30, 48, 66]          # 09:30-10:00 / 10-11 / 11-12 / 12-13:30 / 13:30-15 / 15-16:15


@njit(cache=True)
def _paths(H, L, C, FP, a, hi5, cost_pts):
    n = H.shape[0]; out = np.full((n, NB, 12), np.nan)
    for s in range(n):
        if not a[s] > 0:
            continue
        for b in range(NB - 1):
            e = 5 * b + 5
            if e > J15:
                continue
            px = FP[s, e]
            if px != px:
                continue
            w1 = min(e + 60, J15 + 1); mfe = -1e18; mae = -1e18; tm = 0; tmae = e
            for k in range(e, w1):
                if H[s, k] - px > mfe:
                    mfe = H[s, k] - px; tm = k - e
                if px - L[s, k] > mae:
                    mae = px - L[s, k]; tmae = k
            nh = 0.0
            for k in range(e, w1):
                if H[s, k] > hi5[s, b]:
                    nh = 1.0; break
            res = np.zeros(3)
            for q, lv in enumerate((0.25, 0.5, 1.0)):
                up = px + lv * a[s]; dn = px - lv * a[s]; r = np.nan
                for k in range(e, J15 + 1):
                    if L[s, k] <= dn:
                        r = 0.0; break
                    if H[s, k] >= up:
                        r = 1.0; break
                res[q] = r
            tpos = np.nan
            for k in range(e, J15 + 1):
                if C[s, k] >= px + cost_pts[s]:
                    tpos = k - e; break
            trec = np.nan
            if mae > 0:
                for k in range(tmae + 1, J15 + 1):
                    if C[s, k] >= px:
                        trec = k - e; break
            out[s, b, 0] = mfe / a[s]; out[s, b, 1] = mae / a[s]; out[s, b, 2] = tm; out[s, b, 3] = nh
            out[s, b, 4] = res[0]; out[s, b, 5] = res[1]; out[s, b, 6] = res[2]
            out[s, b, 7] = 1.0 if FP[s, J15] < px else 0.0; out[s, b, 8] = tpos; out[s, b, 9] = trec
            out[s, b, 10] = px
    return out


PATH = ["mfe60", "mae60", "t_mfe", "newhigh60", "bar025", "bar050", "bar100", "underwater_1615", "t_first_pos", "t_recover"]


class Mkt:
    """all per-(session, bar) matrices for one instrument."""

    def __init__(self, I, name):
        self.I = I; self.name = name; self.n = I.n; n = I.n
        a = I.atr.copy(); a[~(a > 0)] = np.nan; self.a = a
        self.o, self.h, self.l, self.c = I.o5, I.h5, I.l5, I.c5
        rng = self.h - self.l
        flat = pd.Series(rng.ravel())
        self.atr5 = flat.rolling(20, min_periods=10).mean().shift(1).values.reshape(n, NB)
        self.medr20 = flat.rolling(20, min_periods=10).median().shift(1).values.reshape(n, NB)
        H = pd.Series(self.h.ravel())
        self.prevhi = {N: H.rolling(N, min_periods=N).max().shift(1).values.reshape(n, NB) for N in (2, 4, 6, 8, 12, 20, 30, 60)}
        L_ = pd.Series(self.l.ravel()); self.prevlo12 = L_.rolling(12, min_periods=12).min().shift(1).values.reshape(n, NB)
        cs = pd.Series(self.c.ravel()); self.ema20 = cs.ewm(span=20, adjust=False).mean().values.reshape(n, NB)
        self.body = self.c - self.o; self.bull = self.body > 0
        self.body_pct = np.where(rng > 0, self.body / np.where(rng > 0, rng, 1), 0.0)
        self.cpos = np.where(rng > 0, (self.c - self.l) / np.where(rng > 0, rng, 1), 0.5)
        self.rng_atr5 = rng / self.atr5
        self.vwap = I.vwap[:, 4::5][:, :NB]; self.open0 = I.FP[:, 0]
        self.pdh = np.r_[np.nan, np.nanmax(I.H, 1)[:-1]]
        self.disp = (self.c - np.concatenate([np.full((n, 1), np.nan), self.c[:, :-1]], 1)) / a[:, None]
        self.disp[:, 0] = (self.c[:, 0] - self.open0) / a
        # forward returns (ATR_d)
        ent = np.full((n, NB), np.nan); ent[:, :NB - 1] = I.FP[:, 5 * np.arange(1, NB)]
        self.entry = ent; self.R = {}
        for h in HB:
            ex = np.full((n, NB), np.nan); jj = 5 * (np.arange(NB) + 1 + h); ok = jj <= J15
            ex[:, ok] = I.FP[:, jj[ok]]; self.R[f"h{h}"] = (ex - ent) / a[:, None]
        for key, j in (("h1600", J16), ("h1615", J15)):
            ex = np.repeat(I.FP[:, j:j + 1], NB, 1); ok = 5 * (np.arange(NB) + 1) < j
            r = (ex - ent) / a[:, None]; r[:, ~ok] = np.nan; self.R[key] = r
        self.cost = 2 * I.cs / (I.pv * a)                                       # round-trip cost in ATR_d units (per session)
        cost_pts = 2 * I.cs / I.pv * np.ones(n)
        P = _paths(I.H, I.L, I.C, I.FP, np.nan_to_num(a), self.h, cost_pts)
        self.P = {k: P[..., i] for i, k in enumerate(PATH)}
        self.full = I.full & (a > 0)
        self.year = np.repeat(I.year[:, None], NB, 1); self.vt = np.repeat(I.vt[:, None], NB, 1); self.bullday = np.repeat(I.bull[:, None], NB, 1)
        self.bidx = np.repeat(np.arange(NB)[None, :], n, 0); self.tod = np.digitize(self.bidx, TOD_EDGES)
        self.date = np.repeat(np.asarray(I.sess.values, "datetime64[D]").astype(np.int64)[:, None], NB, 1)
        dq = pd.Series(self.disp[self.full].ravel()).quantile(np.linspace(0.1, 0.9, 9)).values
        self.dispdec = np.digitize(np.nan_to_num(self.disp), dq)
        rq = pd.Series((rng / a[:, None])[self.full].ravel()).quantile([1 / 3, 2 / 3]).values
        self.rngter = np.digitize(np.nan_to_num(rng / a[:, None]), rq)
        self.mom4 = self.c > self.prevhi[4]
        self.valid = self.full[:, None] & ~np.isnan(ent) & (self.bidx >= 1)
        self._cellA = {}

    def kbar(self, k):
        if k not in self._cellA:
            n = self.n; cf = pd.Series(self.c.ravel()); hf = pd.Series(self.h.ravel()); lf = pd.Series(self.l.ravel())
            disp = ((cf - cf.shift(k)).values.reshape(n, NB)) / self.a[:, None]
            rg = ((hf.rolling(k).max() - lf.rolling(k).min()).values.reshape(n, NB)) / self.a[:, None]
            v = self.valid
            dq = np.nanpercentile(disp[v], np.linspace(10, 90, 9)); rq = np.nanpercentile(rg[v], [100 / 3, 200 / 3])
            self._cellA[k] = (np.digitize(np.nan_to_num(disp), dq), np.digitize(np.nan_to_num(rg), rq))
        return self._cellA[k]

    def null(self, kind, key, ev):
        """per-event null mean for horizon key.  A: all bars in cell; B / C: non-event bars in cell."""
        r = self.R[key] if key in self.R else self.P[key]
        base = self.valid & ~np.isnan(r)
        if kind == "A":
            cell = ((self.year * 10 + self.vt) * 2 + self.bullday.astype(int)) * 100 + self.bidx; pool = base
        elif kind == "B":
            cell = ((self.year * 10 + self.tod) * 10 + self.dispdec) * 10 + self.rngter; pool = base & ~ev
        elif kind.startswith("B"):                                 # multi-bar magnitude null (Wave 2): k-bar displacement decile x k-bar range tercile
            dd, rt = self.kbar(int(kind[1:]))
            cell = ((self.year * 10 + self.tod) * 10 + dd) * 10 + rt; pool = base & ~ev
        else:
            cell = self.year * 10 + self.tod; pool = base & ~ev & self.mom4
        c = cell[pool]; v = r[pool]
        s = pd.Series(v).groupby(c).agg(["sum", "count"])
        m = (s["sum"] / s["count"]).where(s["count"] >= 20)
        return pd.Series(m).reindex(cell[ev]).values


_M = {}


def markets():
    if not _M:
        Is = X.load(INSTS)
        for k in INSTS:
            _M[k] = Mkt(Is[k], k)
    return _M


def boot_ci(v, cl, reps=500, seed=7):
    ok = ~np.isnan(v); v, cl = v[ok], cl[ok]
    if len(v) < 20:
        return np.nan, np.nan
    u, inv = np.unique(cl, return_inverse=True); sums = np.bincount(inv, v); cnt = np.bincount(inv)
    rng = np.random.default_rng(seed); k = len(u); out = np.empty(reps)
    for r in range(reps):
        idx = rng.integers(0, k, k); out[r] = sums[idx].sum() / max(cnt[idx].sum(), 1)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def study(name, evs, nulls=("A",), horizons=None, family_null=None, common=True, extra=None):
    """evs: {inst: bool mask (n x 81)}.  Returns (summary rows per instrument + POOLED, per-year table).  family_null: {inst: mask} compared
    with the same horizon (difference of means, clustered CI on the pooled difference is not computed - reported as means)."""
    M = markets(); horizons = horizons or HZ; rows = []; yrs = []
    pooled = {k: {"r": [], "cl": [], "yr": [], **{f"x{nl}": [] for nl in nulls}} for k in horizons}
    for inst, ev in evs.items():
        m = M[inst]; ev = ev & m.valid
        if common:
            ev = ev & (m.bidx <= BMAX_COMMON)
        o = {"variant": name, "instrument": inst, "n_events": int(ev.sum()), "events_per_year": float(ev.sum() / max(len(np.unique(m.year[ev])), 1))}
        for key in horizons:
            r = m.R[key][ev]; ok = ~np.isnan(r)
            o[f"{key}_n"] = int(ok.sum()); o[f"{key}_mean"] = float(np.nanmean(r)) if ok.any() else np.nan
            o[f"{key}_median"] = float(np.nanmedian(r)) if ok.any() else np.nan; o[f"{key}_p_pos"] = float((r[ok] > 0).mean()) if ok.any() else np.nan
            pooled[key]["r"].append(r); pooled[key]["cl"].append(m.date[ev]); pooled[key]["yr"].append(m.year[ev])
            for nl in nulls:
                x = r - m.null(nl, key, ev); o[f"{key}_x{nl}"] = float(np.nanmean(x)); pooled[key][f"x{nl}"].append(x)
            if family_null is not None:
                fe = family_null[inst] & m.valid & ((m.bidx <= BMAX_COMMON) if common else True)
                o[f"{key}_family_null_mean"] = float(np.nanmean(m.R[key][fe])); o[f"{key}_x_family"] = o[f"{key}_mean"] - o[f"{key}_family_null_mean"]
        o["cost_atr"] = float(np.nanmean(np.repeat(m.cost[:, None], NB, 1)[ev]))
        for k in PATH:
            v = m.P[k][ev]
            o[k] = float(np.nanmean(v))
        for q in (50, 75, 90, 95, 99):
            o[f"mae60_p{q}"] = float(np.nanpercentile(m.P["mae60"][ev], q)) if ev.any() else np.nan
        for q in (50, 75, 90, 95):
            o[f"mfe60_p{q}"] = float(np.nanpercentile(m.P["mfe60"][ev], q)) if ev.any() else np.nan
        o.update(extra or {}); rows.append(o)
    P = {"variant": name, "instrument": "POOLED"}
    for key in horizons:
        r = np.concatenate(pooled[key]["r"]); cl = np.concatenate(pooled[key]["cl"]); yr = np.concatenate(pooled[key]["yr"])
        P[f"{key}_n"] = int((~np.isnan(r)).sum()); P[f"{key}_mean"] = float(np.nanmean(r)) if P[f"{key}_n"] else np.nan
        for nl in nulls:
            x = np.concatenate(pooled[key][f"x{nl}"]); P[f"{key}_x{nl}"] = float(np.nanmean(x)); lo, hi = boot_ci(x, cl)
            P[f"{key}_x{nl}_lo"], P[f"{key}_x{nl}_hi"] = lo, hi
            by = pd.Series(x).groupby(yr).mean(); P[f"{key}_x{nl}_years_pos"] = int((by > 0).sum()); P[f"{key}_x{nl}_years"] = int(by.notna().sum())
            yrs.append({"variant": name, "horizon": key, "null": nl, **{int(k): float(v) for k, v in by.items()}})
    P["n_events"] = sum(r_["n_events"] for r_ in rows); P["cost_atr"] = float(np.mean([r_["cost_atr"] for r_ in rows]))
    rows.append(P)
    return rows, yrs


def edge(P, key, nl):
    """preregistered EVENT_EDGE test on a pooled row."""
    return bool(P.get(f"{key}_x{nl}_lo", np.nan) > 0 and P.get(f"{key}_x{nl}_years_pos", 0) >= 5 and P.get(f"{key}_mean", 0) > P.get("cost_atr", 1))


def ledger(rows, family, source, cls, params=""):
    p = os.path.join(OUT, "TEST97_RESEARCH_LEDGER.csv"); recs = []
    for r in rows:
        recs.append({"candidate_id": f"{r['variant']}|{r['instrument']}", "family": family, "parameters": params or r["variant"], "source_inspiration": source,
                     "classification": cls, "instrument": r["instrument"], "event_count": r.get("n_events"), "h12_mean": r.get("h12_mean"),
                     "h12_xA": r.get("h12_xA"), "h12_xB": r.get("h12_xB"), "h1615_mean": r.get("h1615_mean"), "h1615_xA": r.get("h1615_xA"),
                     "h12_xA_lo": r.get("h12_xA_lo"), "h12_xA_years_pos": r.get("h12_xA_years_pos"), "cost_atr": r.get("cost_atr"), "status": r.get("status", "")})
    df = pd.DataFrame(recs)
    df.to_csv(p, mode="a", header=not os.path.exists(p), index=False)


def md(name, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".4f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(os.path.join(REP, name), "w").write("\n".join(lines) + "\n")
