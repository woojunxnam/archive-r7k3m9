"""TEST70+ ADAPTIVE BOX LAB shared layer: data (<= 2026-05-27), causal box builders (families A-I), numba event / trade kernels,
matched-long control, registries.  T61-R1C frozen package verified on import (fail closed).  RTH only; grid j = 1m bar END-stamped 09:31+j.
Box contract: a box is built ONLY from bars with index < birth; decisions use closes of bars j in [birth, death); fills at the next open."""
import datetime
import json
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402  (verifies frozen/t61_r1c)
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402

LAB = K.LAB; BOX = os.path.join(LAB, "out", "ADAPTIVE_BOX_LAB"); REPB = os.path.join(LAB, "reports", "ADAPTIVE_BOX_LAB")
os.makedirs(BOX, exist_ok=True); os.makedirs(REPB, exist_ok=True)
NG = C45.NG; J15 = E.J1615; J16 = E.J1600
START, S21 = K.START, K.S21
REGS = ["BOX_RESEARCH_REGISTRY", "BOX_GEOMETRY_REGISTRY", "BOX_REJECT_REGISTRY", "BOX_CLUE_REGISTRY", "BOX_SURVIVOR_LIBRARY", "BOX_TRANSITION_MATRIX",
        "BOX_T61_INCREMENTAL_FRONTIER", "BOX_RESEARCH_BUDGET"]
FOLDS = [(nm, pd.Timestamp(a), pd.Timestamp(b)) for nm, a, b in C45.OUTER[:5]]
SEGS = {"S1_0930_1030": (0, C45.g("10:30") + 1), "S2_1030_1200": (C45.g("10:30") + 1, C45.g("12:00") + 1), "S3_1200_1400": (C45.g("12:00") + 1, C45.g("14:00") + 1),
        "S4_1400_1515": (C45.g("14:00") + 1, C45.g("15:15") + 1), "S5_1515_1615": (C45.g("15:15") + 1, NG)}


def reg_append(name, rows, key=None):
    p = os.path.join(BOX, f"{name}.csv")
    df = pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    if key:
        df = df.drop_duplicates(key, keep="last")
    df.to_csv(p, index=False)


def budget(test, hypotheses=0, ml_configs=0, genomes=0, note=""):
    reg_append("BOX_RESEARCH_BUDGET", [{"test": test, "hypotheses": hypotheses, "ml_configs": ml_configs, "valid_genomes": genomes, "note": note,
                                        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}])


def prereg(test, spec):
    import hashlib
    d = os.path.join(BOX, test); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{test}_PREREGISTRATION.json")
    if os.path.exists(p):
        return open(p + ".sha256").read().strip()
    json.dump({"test": test, "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "research_data_end": "2026-05-27",
               "program_prereg_sha256": open(os.path.join(BOX, "TEST70", "TEST70_PLUS_PREREGISTRATION.json.sha256")).read().strip(), **spec}, open(p, "w"), indent=1, default=str)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n")
    return h


def md(name, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(os.path.join(REPB, name), "w").write("\n".join(lines) + "\n")


def _ffill(a):
    return pd.DataFrame(a).T.ffill().T.values


def _bfill_row(a):
    return pd.DataFrame(a).T.bfill().T.values


class Inst:
    def __init__(self, mk, name):
        pn = mk.pn
        self.name = name; self.n = mk.n; self.sess = pn.sess; self.pv = float(mk.pv); self.k = mk.k
        self.cs = float(C45.cost_side(mk.k, 1.0)); self.cs4 = float(C45.cost_side(mk.k, 4.0))
        C = _ffill(pn.C); C = np.where(np.isnan(C), _bfill_row(C), C)
        self.C = C
        self.H = np.where(np.isnan(pn.H), C, pn.H); self.L = np.where(np.isnan(pn.L), C, pn.L)
        self.O = np.where(np.isnan(pn.O), C, pn.O)
        fp = np.where(np.isnan(mk.FP), _bfill_row(mk.FP), mk.FP); self.FP = np.where(np.isnan(fp), C, fp)
        fb = np.where(np.isnan(mk.FPb), _bfill_row(mk.FPb), mk.FPb); self.FPb = np.where(np.isnan(fb), C, fb)
        self.V = np.nan_to_num(pn.V)
        self.atr = pd.Series(mk.atr).ffill().bfill().values
        self.vt = mk.vt.astype(np.int64); self.bull = mk.bull.astype(np.int64); self.year = self.sess.year.values.astype(np.int64)
        self.grp = self.year * 100 + self.vt * 10 + self.bull
        self.full = np.asarray(self.sess >= START)
        self.nxt_open = np.r_[self.FP[1:, 0], np.nan]
        # 5m bars: b covers grid [5b, 5b+5), completes at 5b+4
        nb = NG // 5
        self.h5 = self.H[:, :5 * nb].reshape(self.n, nb, 5).max(2); self.l5 = self.L[:, :5 * nb].reshape(self.n, nb, 5).min(2)
        self.o5 = self.O[:, 0:5 * nb:5]; self.c5 = self.C[:, 4:5 * nb:5]
        tp = (self.H + self.L + self.C) / 3.0
        cv = np.cumsum(self.V, 1); self.vwap = np.where(cv > 0, np.cumsum(tp * self.V, 1) / np.where(cv > 0, cv, 1), np.cumsum(tp, 1) / np.arange(1, NG + 1))
        # matched control CSR (sessions per group)
        keys = np.unique(self.grp[self.full])
        self.gkeys = keys; order = []; ptr = [0]
        for kk in keys:
            ix = np.where((self.grp == kk) & self.full)[0]; order += list(ix); ptr.append(len(order))
        self.gidx = np.array(order, np.int64); self.gptr = np.array(ptr, np.int64)
        self.gpos = np.searchsorted(keys, self.grp)


_CACHE = {}


def load():
    if "I" not in _CACHE:
        es, nq = E.setup()
        _CACHE["I"] = {"MNQ": Inst(nq, "MNQ"), "ES": Inst(es, "ES")}
    return _CACHE["I"]


# ------------------------------------------------------------------------------------------------------------------ builders
def _box(rows, s, birth, death, lo, hi, prev):
    if death > birth and hi > lo and np.isfinite(lo) and np.isfinite(hi) and birth < J15:
        rows.append((s, birth, min(death, J15), lo, hi, prev))
        return len(rows) - 1
    return prev


def build(I, geo, spec):
    """returns DataFrame of boxes: s, birth, death, lo, hi, prev (row index of the previous box of this geometry in the session or -1)."""
    fam = spec["family"]; rows = []
    for s in np.where(I.full)[0]:
        H, L, C, O = I.H[s], I.L[s], I.C[s], I.O[s]; a = I.atr[s]; prev = -1
        if fam in ("A_FIXED_WINDOW", "F_QUANTILE", "I_PACKING"):
            o, life = spec["obs"], spec["life"]; b = o
            while b < J15:
                if fam == "A_FIXED_WINDOW":
                    lo, hi = L[b - o:b].min(), H[b - o:b].max()
                elif fam == "F_QUANTILE":
                    x = C[b - o:b]
                    if spec["q"] == "MAD":
                        med = np.median(x); m = 1.4826 * np.median(np.abs(x - med)); lo, hi = med - 2 * m, med + 2 * m
                    else:
                        ql, qh = (10, 90) if spec["q"] == "10_90" else (20, 80); lo, hi = np.percentile(x, ql), np.percentile(x, qh)
                else:
                    x = np.sort(C[b - o:b]); kk = int(np.ceil(spec["frac"] * o)); wds = x[kk - 1:] - x[:o - kk + 1]; i = int(np.argmin(wds))
                    lo, hi = x[i], x[i + kk - 1]
                prev = _box(rows, s, b, b + life, lo, hi, prev); b += life
        elif fam == "G_VWAP_GEOM":
            b = 30
            while b < J15:
                v = I.vwap[s, b - 1]; prev = _box(rows, s, b, b + 30, v - spec["m"] * a, v + spec["m"] * a, prev); b += 30
        elif fam == "C_ATR_ANCHOR":
            Kk = spec["K"]
            if spec["anchor"] == "OPEN":
                c, v, b = O[0], 0.25 * a, 0
            elif spec["anchor"] == "PRIORCLOSE":
                if s == 0:
                    continue
                c, v, b = I.C[s - 1, J15], 0.25 * a, 0
            else:
                hi30, lo30 = H[:30].max(), L[:30].min(); c, v, b = (hi30 + lo30) / 2, (hi30 - lo30) / 2, 30
            _box(rows, s, b, J15, c - Kk * v, c + Kk * v, -1)
        elif fam == "E_SESSION":
            g = spec["geom"]
            if g.startswith("OR"):
                m = int(g[2:]); _box(rows, s, m, J15, L[:m].min(), H[:m].max(), -1)
            elif s > 0:
                pH, pL, pO, pC = I.H[s - 1, :J15 + 1].max(), I.L[s - 1, :J15 + 1].min(), I.O[s - 1, 0], I.C[s - 1, J15]
                if g == "PREV_HL":
                    lo, hi = pL, pH
                elif g == "PREV_BODY":
                    lo, hi = min(pO, pC), max(pO, pC)
                else:
                    mid = (pH + pL) / 2; lo, hi = mid - 0.25 * (pH - pL), mid + 0.25 * (pH - pL)
                _box(rows, s, 0, J15, lo, hi, -1)
        elif fam in ("B_FROZEN_ROLLING", "H_BALANCE"):
            N = spec["nbars5"]; h5, l5, c5, o5 = I.h5[s], I.l5[s], I.c5[s], I.o5[s]; act = None
            for b in range(N - 1, len(c5)):
                jb = 5 * b + 4
                if act is not None:
                    lo, hi, ri = act
                    if c5[b] > hi or c5[b] < lo:
                        rows[ri] = rows[ri][:2] + (min(jb + 1, rows[ri][2]),) + rows[ri][3:]; act = None
                    else:
                        continue
                wh, wl = h5[b - N + 1:b + 1].max(), l5[b - N + 1:b + 1].min()
                if fam == "H_BALANCE":
                    rng = h5[b - N + 1:b + 1] - l5[b - N + 1:b + 1]
                    eff = abs(c5[b] - o5[b - N + 1]) / max(rng.sum(), 1e-9)
                    ov = np.mean(np.minimum(h5[b - N + 2:b + 1], h5[b - N + 1:b]) > np.maximum(l5[b - N + 2:b + 1], l5[b - N + 1:b]))
                    mid = (wh + wl) / 2; cc = c5[b - N + 1:b + 1] - mid; cross = int(np.sum(np.sign(cc[1:]) != np.sign(cc[:-1])))
                    if not (eff <= 0.30 and ov >= 0.70 and (wh - wl) <= 0.40 * a and cross >= 2):
                        continue
                ri = len(rows); pr = _box(rows, s, jb + 1, J15, wl, wh, prev)
                if pr == ri:
                    act = (wl, wh, ri); prev = ri
        elif fam == "D_SWING":
            p = spec["p"]; h5, l5, c5 = I.h5[s], I.l5[s], I.c5[s]; SH = SL = np.nan; act = None
            for b in range(2 * p, len(c5)):
                i = b - p; jb = 5 * b + 4; new = False
                if h5[i] > h5[i - p:i].max() and h5[i] >= h5[i + 1:b + 1].max():
                    SH = h5[i]; new = True
                if l5[i] < l5[i - p:i].min() and l5[i] <= l5[i + 1:b + 1].min():
                    SL = l5[i]; new = True
                if act is not None and (c5[b] > act[1] or c5[b] < act[0]):
                    rows[act[2]] = rows[act[2]][:2] + (min(jb + 1, rows[act[2]][2]),) + rows[act[2]][3:]; act = None
                if new and np.isfinite(SH) and np.isfinite(SL) and SL < SH and c5[b] >= SL and c5[b] <= SH:
                    if act is not None:
                        rows[act[2]] = rows[act[2]][:2] + (min(jb + 1, rows[act[2]][2]),) + rows[act[2]][3:]
                    ri = len(rows); pr = _box(rows, s, jb + 1, J15, SL, SH, prev)
                    if pr == ri:
                        act = (SL, SH, ri); prev = ri
    B = pd.DataFrame(rows, columns=["s", "birth", "death", "lo", "hi", "prev"])
    return B[B.death > B.birth].reset_index(drop=True) if len(B) else B


def annotate(B, I):
    """sequence direction / width dynamics / migration velocity vs previous boxes of the same geometry (causal: previous boxes are older)."""
    pv = B.prev.values; lo, hi = B.lo.values, B.hi.values; mid = (lo + hi) / 2; w = hi - lo
    dirn = np.full(len(B), "NONE", object); wd = np.full(len(B), "NONE", object); vel = np.full(len(B), np.nan); pdir = np.full(len(B), "NONE", object)
    for i in range(len(B)):
        p = pv[i]
        if p >= 0:
            x = (mid[i] - mid[p]) / max(w[p], 1e-9); dirn[i] = "RISING" if x > 0.25 else ("FALLING" if x < -0.25 else "FLAT")
            r = w[i] / max(w[p], 1e-9); wd[i] = "CONTRACTING" if r < 0.8 else ("EXPANDING" if r > 1.25 else "STABLE")
            pdir[i] = dirn[p]
            q = p; k = 0
            while k < 2 and pv[q] >= 0:
                q = pv[q]; k += 1
            vel[i] = (mid[i] - mid[q]) / I.atr[B.s.values[i]]
    B["dir"] = dirn; B["prev_dir"] = pdir; B["width_dyn"] = wd; B["velocity"] = vel; B["w_atr"] = w / I.atr[B.s.values]
    return B


# ------------------------------------------------------------------------------------------------------------------ kernels
@njit(cache=True)
def bottom_events(C, H, L, FP, FPb, bs, birth, death, lo, hi, LZ, UZ, J15_, J16_):
    """one bottom event per box: first close in [lo, lo+LZ*w] during life; trade to TOP (close >= lo+UZ*w) / BREAK (close < lo) / 16:15."""
    nbx = bs.shape[0]
    out = np.full((nbx, 16), np.nan)       # 0 j_touch 1 j_in 2 px_in 3 j_xdec 4 reason(1 top,2 break,3 eod) 5 j_xfill 6 px_x 7 mid_before_break 8 top_before_break
    #                                         9 t_mid 10 t_top 11 mfe_w 12 mae_w 13 j_topdec 14 px_topfill 15 j_topfill
    for b in range(nbx):
        s = bs[b]; w = hi[b] - lo[b]
        jt = -1
        for j in range(birth[b], death[b]):
            c = C[s, j]
            if c >= lo[b] and c <= lo[b] + LZ * w:
                jt = j; break
        if jt < 0 or jt + 1 >= J15_:
            continue
        ji = jt + 1; px = FP[s, ji]
        out[b, 0] = jt; out[b, 1] = ji; out[b, 2] = px
        reason = 3; jx = J15_; midb = 0.0; topb = 0.0; tmid = np.nan; ttop = np.nan; mfe = 0.0; mae = 0.0; jtop = -1
        for k in range(ji, J15_):
            if H[s, k] - px > mfe:
                mfe = H[s, k] - px
            if px - L[s, k] > mae:
                mae = px - L[s, k]
            c = C[s, k]
            if c >= lo[b] + 0.5 * w and midb == 0.0:
                midb = 1.0; tmid = k - ji
            if c >= lo[b] + UZ * w:
                reason = 1; jx = k + 1; topb = 1.0; ttop = k - ji; jtop = k; break
            if c < lo[b]:
                reason = 2; jx = k + 1; break
        if jx > J15_:
            jx = J15_
        out[b, 3] = jx - 1; out[b, 4] = reason; out[b, 5] = jx; out[b, 6] = FPb[s, jx]
        out[b, 7] = midb; out[b, 8] = topb; out[b, 9] = tmid; out[b, 10] = ttop; out[b, 11] = mfe / w; out[b, 12] = mae / w
        if jtop >= 0:
            out[b, 13] = jtop; out[b, 15] = min(jtop + 1, J15_); out[b, 14] = FPb[s, min(jtop + 1, J15_)]
    return out


@njit(cache=True)
def matched(FP, FPb, nxt, gidx, gptr, gpos_s, s_arr, jin, jx, kind, pv, cs):
    """mean net $ of the matched long control (same group, same entry / exit minute).  kind 0: exit FPb[., jx]; 1: exit next open."""
    m = s_arr.shape[0]; out = np.full(m, np.nan)
    for e in range(m):
        g = gpos_s[s_arr[e]]; a, b = gptr[g], gptr[g + 1]
        if b <= a or jin[e] < 0:
            continue
        tot = 0.0; cnt = 0
        for q in range(a, b):
            ss = gidx[q]
            if kind[e] == 1:
                xo = nxt[ss]
                if xo != xo:
                    continue
            else:
                xo = FPb[ss, jx[e]]
            xi = FP[ss, jin[e]]
            if xo != xo or xi != xi:
                continue
            tot += (xo - xi) * pv - 2 * cs; cnt += 1
        if cnt > 0:
            out[e] = tot / cnt
    return out


def fold_of(dates):
    f = np.full(len(dates), "", object); d = pd.DatetimeIndex(dates)
    for nm, a, b in FOLDS:
        f[(d >= a) & (d <= b)] = nm
    return f


def risk(x):
    x = np.asarray(x, float); eq = np.cumsum(x); dd = float((np.maximum.accumulate(np.r_[0, eq])[1:] - eq).max()) if len(x) else 0.0
    return {"avg_day": float(x.mean()) if len(x) else 0.0, "total": float(x.sum()), "max_dd": dd, "worst_day": float(x.min()) if len(x) else 0.0,
            "ret_dd": float(x.mean() / dd) if dd > 0 else np.nan}


# ------------------------------------------------------------------------------------------------------------------ sequential box trading
@njit(cache=True)
def sim_boxes(C, FP, FPb, bs, birth, death, lo, hi, LZ, UZ, buf, cycles, delay, miss_e, miss_x, J15_, mode):
    """one position at a time, 1 contract.  Boxes must be sorted by (s, birth).  mode 0 = RANGE (exit at TOP / lower break / 16:15),
    mode 1 = HOLD (ignore TOP; exit lower break / 16:15).  miss_e / miss_x: per-box / per-box random masks (1 = missed) for stress tests.
    returns ledger rows: s, j_in(fill), j_x(fill), px_in, px_x, reason(1 top 2 break 3 eod), box, cycle."""
    out = np.full((bs.shape[0] * cycles, 8), np.nan); m = 0; busy_s = -1; busy_j = -1
    for b in range(bs.shape[0]):
        s = bs[b]; w = hi[b] - lo[b]; cyc = 0
        j = birth[b]
        if busy_s == s and busy_j >= j:
            j = busy_j + 1
        while j < death[b] and cyc < cycles:
            jt = -1
            for k in range(j, death[b]):
                c = C[s, k]
                if c >= lo[b] and c <= lo[b] + LZ * w:
                    jt = k; break
            if jt < 0 or miss_e[b] == 1 and cyc == 0:
                break
            ji = jt + 1 + delay
            if ji >= J15_:
                break
            px = FP[s, ji]; reason = 3; jx = J15_; skipped = 0
            for k in range(ji, J15_):
                c = C[s, k]
                if mode == 0 and c >= lo[b] + UZ * w:
                    if miss_x[b] == 1 and skipped == 0:
                        skipped = 1
                    else:
                        reason = 1; jx = k + 1; break
                if c < lo[b] - buf * w:
                    reason = 2; jx = k + 1; break
            if jx > J15_:
                jx = J15_
            out[m, 0] = s; out[m, 1] = ji; out[m, 2] = jx; out[m, 3] = px; out[m, 4] = FPb[s, jx]; out[m, 5] = reason; out[m, 6] = b; out[m, 7] = cyc
            m += 1; cyc += 1; busy_s = s; busy_j = jx - 1; j = jx
            if reason != 1:
                break
    return out[:m]


def ledger_eval(I, L, cs=None):
    """daily net, matched excess per trade; L = sim_boxes output."""
    cs = I.cs if cs is None else cs
    D = pd.DataFrame(L, columns=["s", "j_in", "j_x", "px_in", "px_x", "reason", "box", "cycle"])
    if not len(D):
        return D, np.zeros(I.n)
    for c in ("s", "j_in", "j_x", "reason", "box", "cycle"):
        D[c] = D[c].astype(np.int64)
    D["gross"] = (D.px_x - D.px_in) * I.pv; D["net"] = D.gross - 2 * cs
    D["ctl"] = matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, D.s.values, D.j_in.values, D.j_x.values, np.zeros(len(D), np.int64), I.pv, cs)
    D["excess"] = D.net - D.ctl
    d = np.zeros(I.n); np.add.at(d, D.s.values, D.net.values)
    return D, d
