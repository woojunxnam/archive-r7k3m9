"""TEST47 engine: causal NASSI meaningful-down-leg state machine on completed 5m RTH bars, entry resolution (E1..E5, NB),
exits, forward matrices, matched long baselines and the campaign / inventory-recycle simulator.

Timing: 5m bar b covers 1m grid [5b, 5b+5) (bars 09:30..16:10).  A decision at the close of 5m bar k fills at the open of
1m grid index 5(k+1).  1m decisions at grid i fill at the open of grid i+1.  No bar after the decision is ever read."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t45_sim as S45  # noqa: E402
import t46_rebound as R46  # noqa: E402
import t47_common as C  # noqa: E402

NB = 81
LEGDEF = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}
SIDE = {"KEEP": 0, "DECAY": 1, "RESET": 2}
NF = 24   # event feature columns
FCOLS = ["s", "b", "start", "ref", "c_last", "cum", "dur", "leg1", "leg2", "leg3", "leg4", "n_neutral", "max_rec", "n_up",
         "seq_low", "lastbar_h", "lastbar_l", "rally30", "ntick", "b_leg1", "b_leg2", "b_leg3", "b_leg4", "u5"]
J1615 = C45.g("16:15"); J1600 = C45.g("16:00"); J_LAST_ENTRY = 5 * 75   # last entry fill grid index (15:45 bar open)


@njit(cache=True)
def detect(o, h, l, c, u, legdef, x, ntick, side_mode, side_n, up_mode, up_frac, maxdur, r1, bmin, bmax, K):
    n, B = c.shape
    cnt = np.zeros((n, B), np.int8)
    legm = np.zeros((n, B))
    E = np.full((n * K, 24), np.nan)
    ne = 0
    for s in range(n):
        us = u[s]
        if not (us > 0):
            continue
        count = 0; ref = np.nan; lastc = np.nan; lastmag = 1.0; start = -1; neutral = 0; nneu = 0; maxrec = 0.0; nup = 0
        mags = np.zeros(8); bars = np.zeros(8, np.int64); kk = 0
        for b in range(1, B):
            cb = c[s, b]; cp = c[s, b - 1]
            if np.isnan(cb) or np.isnan(cp) or np.isnan(o[s, b]):
                continue
            dc = cb - cp
            rng = h[s, b] - l[s, b]
            mag = 0.0
            if legdef == 1:
                if -dc >= x * us:
                    mag = -dc
            elif legdef == 2:
                if cb < o[s, b] and (o[s, b] - cb) >= x * us and rng > 0 and (cb - l[s, b]) / rng <= 0.35:
                    mag = o[s, b] - cb
            elif legdef == 3:
                if cb < cp and l[s, b] < l[s, b - 1] and -dc >= x * us and rng > 0 and (cb - l[s, b]) / rng <= 0.5:
                    mag = -dc
            else:
                if count == 0:
                    rh = -1e18
                    for q in range(max(0, b - 6), b):
                        if not np.isnan(c[s, q]) and c[s, q] > rh:
                            rh = c[s, q]
                    refc = rh
                else:
                    refc = lastc
                if refc - cb >= x * us:
                    mag = refc - cb
            if legdef < 4 and r1 and count == 0 and mag > 0 and cp > o[s, b - 1]:
                mag = 0.0                                   # source rule 1: the turn bar does not count
            if mag > 0:
                if count == 0:
                    start = b; nneu = 0; maxrec = 0.0; nup = 0
                    if legdef < 4:
                        ref = cp
                    else:
                        ref = cb + mag
                if count < 8:
                    mags[count] = mag / us; bars[count] = b
                count += 1; lastc = cb; lastmag = mag; neutral = 0
                legm[s, b] = mag / us
                cnt[s, b] = count
                if count >= ntick:
                    if b >= bmin and b <= bmax and kk < K:
                        sl = 1e18
                        for q in range(max(0, start - 1), b + 1):
                            if l[s, q] < sl:
                                sl = l[s, q]
                        # prior rally: close before the sequence vs min low of the 6 bars before it
                        r30 = np.nan
                        if start >= 2:
                            ml = 1e18
                            for q in range(max(0, start - 7), start - 1):
                                if l[s, q] < ml:
                                    ml = l[s, q]
                            r30 = (c[s, start - 1] - ml) / us
                        e = E[ne]
                        e[0] = s; e[1] = b; e[2] = start; e[3] = ref; e[4] = cb; e[5] = (ref - cb) / us; e[6] = b - start + 1
                        for q in range(4):
                            e[7 + q] = mags[count - ntick + q] if q < ntick else np.nan
                            e[19 + q] = bars[count - ntick + q] if q < ntick else np.nan
                        e[11] = nneu; e[12] = maxrec; e[13] = nup; e[14] = sl; e[15] = h[s, b]; e[16] = l[s, b]; e[17] = r30
                        e[18] = ntick; e[23] = us
                        ne += 1; kk += 1
                    count = 0; neutral = 0                    # a completed sequence is consumed
                continue
            if count > 0:
                if dc > 0:
                    rec = (cb - lastc) / lastmag
                    if rec > maxrec:
                        maxrec = rec
                if dc >= 0.5 * us:
                    nup += 1
                    if (cb - lastc) / lastmag >= up_frac:
                        if up_mode == 1:
                            count -= 1
                        elif up_mode == 2:
                            count = 0
                else:
                    neutral += 1; nneu += 1
                    if side_mode == 1 and neutral >= side_n:
                        count -= 1; neutral = 0
                    elif side_mode == 2 and neutral >= side_n:
                        count = 0
                if count > 0 and cb >= ref:
                    count = 0
                if count > 0 and b - start > maxdur:
                    count = 0
                if count == 0:
                    neutral = 0
            cnt[s, b] = count
    return E[:ne], cnt, legm


def run_detect(mk, p):
    ld = LEGDEF[p.get("leg", "T1")]
    x = p.get("x", C.SPEC["x_default"][p.get("leg", "T1")])
    sm, sn = p.get("side", C.SPEC["sideways_default"])
    um, uf = p.get("up", C.SPEC["upbar_default"])
    E, cnt, legm = detect(mk.o, mk.h, mk.l, mk.c, mk.u5, ld, float(x), int(p.get("ntick", 3)), SIDE[sm], int(sn), SIDE[um], float(uf),
                          int(p.get("maxdur", 24)), bool(p.get("r1", True)), 1, int(p.get("bmax", 72)), 10)
    ev = pd.DataFrame(E, columns=FCOLS)
    ev[["s", "b", "start"]] = ev[["s", "b", "start"]].astype(int)
    return ev, cnt, legm


# --------------------------------------------------------------------------------------------- market wrapper
class Mkt(R46.Market):
    def __init__(self, P, inst):
        super().__init__(P, inst)
        sim = S45.Sim(P, inst)
        R46.attach_fills(self, sim)
        self.sim = sim
        self.u5 = C.u5(self)
        self.H1, self.L1_, self.C1, self.O1 = self.pn.H, self.pn.L, self.pn.C, self.pn.O
        # volume-free session TWAP of 5m closes (causal, through bar b)
        cs = np.nancumsum(self.c, 1); cn = np.cumsum(~np.isnan(self.c), 1)
        self.twap = cs / np.where(cn > 0, cn, np.nan)
        vt = np.digitize(self.volt, [1 / 3, 2 / 3])
        self.vt = vt
        self.year = self.pn.sess.year.values
        # 15m completed bars: m covers 5m bars 3m..3m+2
        M = NB // 3
        self.c15 = self.c[:, 2:3 * M:3]; self.o15 = self.o[:, 0:3 * M:3]
        self.cost = C45.cost_side(self.k, 1.0)


def setup():
    P = C45.build_panel()
    return Mkt(P, "ES"), Mkt(P, "MNQ")


# --------------------------------------------------------------------------------------------- entries
def entry_fill(mk, ev, mode):
    """grid fill index per event (-1 = no entry)."""
    s = ev.s.values; b = ev.b.values
    j = np.full(len(ev), -1, np.int64)
    for i in range(len(ev)):
        si, bi = s[i], b[i]
        if mode == "E1":
            j[i] = 5 * (bi + 1)
        elif mode == "E2":
            g0 = 5 * (bi + 1)
            if g0 < C45.NG and mk.C1[si, g0] >= mk.O1[si, g0]:
                j[i] = g0 + 1
        elif mode in ("E3", "E5", "NB"):
            for k in range(bi + 1, min(bi + 7, NB)):
                if np.isnan(mk.c[si, k]):
                    continue
                if mode == "E3" and mk.c[si, k] > mk.o[si, k]:
                    j[i] = 5 * (k + 1); break
                if mode == "E5" and mk.c[si, k] > ev.lastbar_h.values[i]:
                    j[i] = 5 * (k + 1); break
                if mode == "NB":
                    lo = np.nanmin(mk.l[si, ev.start.values[i] - 1 if ev.start.values[i] > 0 else 0:k])
                    rng = mk.h[si, k] - mk.l[si, k]
                    wick = (min(mk.o[si, k], mk.c[si, k]) - mk.l[si, k]) / rng if rng > 0 else 0
                    if mk.l[si, k] >= lo - 0.25 * mk.u5[si] and mk.c[si, k] >= mk.c[si, k - 1] and (wick >= 0.33 or mk.c[si, k] > mk.o[si, k]):
                        j[i] = 5 * (k + 1); break
        elif mode == "E4":
            j[i] = _e4(mk.O1[si], mk.H1[si], mk.L1_[si], mk.C1[si], 5 * (bi + 1), ev.lastbar_l.values[i])
    j = np.where((j > 0) & (j <= J_LAST_ENTRY), j, -1)
    return j


@njit(cache=True)
def _e4(O, H, L, Cc, g0, lvl):
    lowbar = -1; lo = lvl; hi = np.nan
    for i in range(g0, min(g0 + 30, O.shape[0] - 1)):
        if np.isnan(L[i]):
            continue
        if L[i] < lo:
            lo = L[i]; lowbar = i; hi = H[i]
            continue
        if lowbar >= 0 and i - lowbar >= 2 and Cc[i] > hi:
            return i + 1
    return -1


# --------------------------------------------------------------------------------------------- exits / pnl
def exit_index(mk, ev, j, rule):
    s = ev.s.values
    jx = np.full(len(ev), -1, np.int64)
    for i in range(len(ev)):
        if j[i] < 0:
            continue
        if rule in ("X30", "X60", "X120"):
            jx[i] = min(j[i] + int(rule[1:]), J1615)
        elif rule == "X1600":
            jx[i] = J1600
        elif rule == "X1615":
            jx[i] = J1615
        else:
            si = s[i]; k0 = j[i] // 5
            if rule == "REC50":
                tgt = ev.c_last.values[i] + 0.5 * (ev.ref.values[i] - ev.c_last.values[i])
            elif rule == "REF":
                tgt = ev.ref.values[i]
            elif rule == "OPEN":
                tgt = mk.open[si]
            else:
                tgt = np.nan
            jx[i] = J1615
            for k in range(k0, NB):
                t = mk.twap[si, k] if rule == "TWAP" else tgt
                if not np.isnan(mk.c[si, k]) and mk.c[si, k] >= t:
                    jx[i] = min(5 * (k + 1), J1615); break
        if jx[i] <= j[i]:
            jx[i] = -1
    return jx


def trades(mk, ev, entry="E1", exit_rule="X60", slip=1.0, overlap=False):
    """1-contract long trades; non-overlapping per instrument unless overlap=True.  Returns DataFrame (events with pnl)."""
    j = entry_fill(mk, ev, entry)
    jx = exit_index(mk, ev, j, exit_rule)
    cs = C45.cost_side(mk.k, slip)
    s = ev.s.values
    px_in = np.where(j >= 0, mk.FP[s, np.clip(j, 0, C45.NG - 1)], np.nan)
    px_out = np.where(jx >= 0, mk.FPb[s, np.clip(jx, 0, C45.NG - 1)], np.nan)
    pnl = (px_out - px_in) * mk.pv - 2 * cs
    T = ev.copy(); T["j"] = j; T["jx"] = jx; T["px_in"] = px_in; T["px_out"] = px_out; T["pnl"] = pnl
    T = T[(T.j >= 0) & (T.jx >= 0) & T.pnl.notna()].sort_values(["s", "j"])
    if not overlap:
        keep = []; last_s, last_x = -1, -1
        for i, r in zip(T.index, T[["s", "j", "jx"]].values):
            if r[0] != last_s:
                last_s, last_x = r[0], -1
            if r[1] >= last_x:
                keep.append(i); last_x = r[2]
        T = T.loc[keep]
    T["date"] = mk.pn.sess[T.s.values]; T["year"] = T.date.dt.year
    return T.reset_index(drop=True)


def daily(mk, T, col="pnl"):
    x = np.zeros(mk.n)
    np.add.at(x, T.s.values, T[col].values)
    return x


# --------------------------------------------------------------------------------------------- matched baselines
class Baseline:
    """unconditional long from every fill minute j with the same exit rule; matched on (year, vol tercile, HTF trend state).
    $-PnL incl. costs (1 contract).  For bar-relative exits (REC50/REF) the matched long uses +60m (reported)."""

    def __init__(self, mk):
        self.mk = mk
        self.key = mk.year * 100 + mk.vt * 10 + mk.bull.astype(int)
        self.cache = {}

    def table(self, rule, slip=1.0):
        kk = (rule, slip)
        if kk in self.cache:
            return self.cache[kk]
        mk = self.mk
        cs = C45.cost_side(mk.k, slip)
        js = np.arange(C45.NG)
        M = np.full((mk.n, C45.NG), np.nan)
        for j in js[::1]:
            if j > J_LAST_ENTRY:
                break
            if rule in ("X30", "X60", "X120"):
                jx = min(j + int(rule[1:]), J1615)
            elif rule == "X1600":
                jx = J1600
            elif rule == "X1615":
                jx = J1615
            else:
                jx = min(j + 60, J1615)
            if jx <= j:
                continue
            M[:, j] = (mk.FPb[:, jx] - mk.FP[:, j]) * mk.pv - 2 * cs
        df = pd.DataFrame(M); df["key"] = self.key
        G = df.groupby("key").mean()
        self.cache[kk] = (M, G)
        return M, G

    def excess(self, T, rule, slip=1.0):
        M, G = self.table(rule, slip)
        k = self.key[T.s.values]
        base = G.values[G.index.get_indexer(k), T.j.values]
        return T.pnl.values - base, base


# --------------------------------------------------------------------------------------------- campaign / recycle simulator
@njit(cache=True)
def _nbcond(o, h, l, c, s, k, lowref, us):
    rng = h[s, k] - l[s, k]
    wick = (min(o[s, k], c[s, k]) - l[s, k]) / rng if rng > 0 else 0.0
    return (l[s, k] >= lowref - 0.25 * us) and (c[s, k] >= c[s, k - 1]) and (wick >= 0.33 or c[s, k] > o[s, k])


@njit(cache=True)
def campaign(o, h, l, c, FP, FPb, legm, u, ev_s, ev_b, ev_ref, ev_cl, ev_start, entry_mode, exit_mode, H, rec_frac, add_mode, blind_x,
             trim, trim_x, rebuild, max_rebuild, max_camp, cs, pv, overnight, delay, p_miss_entry, p_miss_add, p_miss_trim, seed,
             j_last_entry, j1615):
    """Long-only inventory campaigns, q in {0,1,2}.  Lots: 0 INIT, 1 SECOND (NR-A / NR-B), 2 REBUILD (NR-D).
    exit_type: 0 FINAL, 1 TRIM, 2 OVERNIGHT (held 16:15 -> next 09:31 open).  Returns lots (m x 11) and campaign rows."""
    np.random.seed(seed)
    n, B = c.shape
    lots = np.full((n * 8, 11), np.nan); nl = 0
    camps = np.full((n * 2, 8), np.nan); nc = 0
    e_ptr = 0; ne = len(ev_s)
    for s in range(n):
        while e_ptr < ne and ev_s[e_ptr] < s:
            e_ptr += 1
        us = u[s]
        if not (us > 0):
            continue
        in_camp = False; q = 0; ncamp = 0
        lp = np.zeros(4); lt = np.zeros(4, np.int64); lj = np.zeros(4, np.int64); lid = np.zeros(4, np.int64); nopen = 0
        j0 = -1; target = np.nan; nreb = 0; trimmed = False; watch = -1; wlow = 0.0; pend = -1; plow = 0.0; ptarget = np.nan
        min_px = 1e18; cid = -1; entry_bar = -1; cum_ok = False
        ei = e_ptr
        for k in range(1, B):
            if np.isnan(c[s, k]):
                continue
            jf = 5 * (k + 1) + delay
            if jf > j1615:
                jf = j1615
            # ---- time-based campaign exit (grid precise)
            if in_camp and exit_mode == 0 and j0 + H <= jf:
                jx = min(j0 + H, j1615)
                for i in range(nopen):
                    px = FPb[s, jx]
                    lots[nl, 0] = s; lots[nl, 1] = lid[i]; lots[nl, 2] = lt[i]; lots[nl, 3] = lj[i]; lots[nl, 4] = lp[i]
                    lots[nl, 5] = jx; lots[nl, 6] = px; lots[nl, 7] = 0; lots[nl, 8] = (px - lp[i]) * pv - 2 * cs; lots[nl, 9] = cid
                    nl += 1
                camps[nc - 1, 5] = jx; camps[nc - 1, 6] = 0
                in_camp = False; nopen = 0; q = 0
            if in_camp:
                done = False
                if exit_mode == 1 and c[s, k] >= target and jf > j0:
                    done = True
                if done:
                    for i in range(nopen):
                        px = FPb[s, jf]
                        lots[nl, 0] = s; lots[nl, 1] = lid[i]; lots[nl, 2] = lt[i]; lots[nl, 3] = lj[i]; lots[nl, 4] = lp[i]
                        lots[nl, 5] = jf; lots[nl, 6] = px; lots[nl, 7] = 0; lots[nl, 8] = (px - lp[i]) * pv - 2 * cs; lots[nl, 9] = cid
                        nl += 1
                    camps[nc - 1, 5] = jf; camps[nc - 1, 6] = 0
                    in_camp = False; nopen = 0; q = 0
                    continue
                # ---- trim (NR-C): sell the most recent add once it rebounds trim_x*u5
                if trim and nopen >= 2 and k > entry_bar and c[s, k] >= lp[nopen - 1] + trim_x * us:
                    if np.random.random() >= p_miss_trim:
                        i = nopen - 1; px = FPb[s, jf]
                        lots[nl, 0] = s; lots[nl, 1] = lid[i]; lots[nl, 2] = lt[i]; lots[nl, 3] = lj[i]; lots[nl, 4] = lp[i]
                        lots[nl, 5] = jf; lots[nl, 6] = px; lots[nl, 7] = 1; lots[nl, 8] = (px - lp[i]) * pv - 2 * cs; lots[nl, 9] = cid
                        nl += 1; nopen -= 1; q -= 1; trimmed = True
                        continue
                # ---- adds
                if nopen < 2 and jf <= j_last_entry and k > entry_bar:
                    allow = (not trimmed) or (rebuild and nreb < max_rebuild)
                    if allow and add_mode == 2:
                        if c[s, k] <= lp[0] - blind_x * us:
                            if np.random.random() >= p_miss_add:
                                lp[nopen] = FP[s, jf]; lt[nopen] = 1 if not trimmed else 2; lj[nopen] = jf; lid[nopen] = nopen + 10 * nreb
                                nopen += 1; q += 1; entry_bar = k
                                if trimmed:
                                    nreb += 1; trimmed = False
                                continue
                    if allow and add_mode == 1:
                        if legm[s, k] > 0 and c[s, k] < min(lp[0], min_px):
                            watch = k; wlow = l[s, k]
                        elif watch >= 0:
                            if k - watch > 6:
                                watch = -1
                            elif _nbcond(o, h, l, c, s, k, wlow, us):
                                if np.random.random() >= p_miss_add:
                                    lp[nopen] = FP[s, jf]; lt[nopen] = 1 if not trimmed else 2; lj[nopen] = jf; lid[nopen] = nopen + 10 * nreb
                                    min_px = min(min_px, lp[nopen])
                                    nopen += 1; q += 1; entry_bar = k
                                    if trimmed:
                                        nreb += 1; trimmed = False
                                watch = -1
                                continue
                            else:
                                wlow = min(wlow, l[s, k])
                continue
            # ---- new campaign
            if ncamp >= max_camp or jf > j_last_entry:
                continue
            while ei < ne and ev_s[ei] == s and ev_b[ei] < k:
                if entry_mode == 1 and pend < 0 and k - ev_b[ei] <= 6:
                    pend = ev_b[ei]; plow = 1e18
                    for q2 in range(max(0, ev_start[ei] - 1), ev_b[ei] + 1):
                        plow = min(plow, l[s, q2])
                    ptarget = ev_cl[ei] + rec_frac * (ev_ref[ei] - ev_cl[ei])
                ei += 1
            go = False
            if ei < ne and ev_s[ei] == s and ev_b[ei] == k and entry_mode == 0:
                go = True; target = ev_cl[ei] + rec_frac * (ev_ref[ei] - ev_cl[ei])
            if entry_mode == 1 and ei < ne and ev_s[ei] == s and ev_b[ei] == k and pend < 0:
                pend = k; plow = 1e18
                for q2 in range(max(0, ev_start[ei] - 1), k + 1):
                    plow = min(plow, l[s, q2])
                ptarget = ev_cl[ei] + rec_frac * (ev_ref[ei] - ev_cl[ei])
            elif entry_mode == 1 and pend >= 0:
                if k - pend > 6:
                    pend = -1
                elif _nbcond(o, h, l, c, s, k, plow, us):
                    go = True; target = ptarget; pend = -1
                else:
                    plow = min(plow, l[s, k])
            if go:
                if np.random.random() < p_miss_entry:
                    continue
                px = FP[s, jf]
                if np.isnan(px):
                    continue
                in_camp = True; q = 1; nopen = 1; lp[0] = px; lt[0] = 0; lj[0] = jf; lid[0] = 0; j0 = jf; entry_bar = k
                nreb = 0; trimmed = False; watch = -1; min_px = px; ncamp += 1
                cid = nc; camps[nc, 0] = s; camps[nc, 1] = k; camps[nc, 2] = jf; camps[nc, 3] = px; camps[nc, 4] = target; camps[nc, 7] = 0
                nc += 1
        # ---- end of session: 16:15 lock
        if in_camp:
            unresolved = True
            hold = overnight and unresolved and s + 1 < n
            for i in range(nopen):
                if hold:
                    px = FP[s + 1, 0]
                    if np.isnan(px):
                        px = FPb[s, j1615]; et = 0; jx = j1615
                    else:
                        et = 2; jx = 10000
                else:
                    px = FPb[s, j1615]; et = 0; jx = j1615
                lots[nl, 0] = s; lots[nl, 1] = lid[i]; lots[nl, 2] = lt[i]; lots[nl, 3] = lj[i]; lots[nl, 4] = lp[i]
                lots[nl, 5] = jx; lots[nl, 6] = px; lots[nl, 7] = et; lots[nl, 8] = (px - lp[i]) * pv - 2 * cs; lots[nl, 9] = cid
                lots[nl, 10] = FPb[s, j1615]
                nl += 1
            camps[nc - 1, 5] = j1615; camps[nc - 1, 6] = 1 if hold else 0; camps[nc - 1, 7] = 1
    return lots[:nl], camps[:nc]


NR_DEFAULT = dict(entry="E1", exit="X60", rec_frac=0.5, add="none", blind_x=2.0, trim=False, trim_x=1.0, rebuild=False,
                  max_rebuild=2, max_camp=2, overnight=False, delay=0, p_miss_entry=0.0, p_miss_add=0.0, p_miss_trim=0.0, slip=1.0, seed=7)


def run_campaign(mk, ev, legm, **kw):
    p = dict(NR_DEFAULT); p.update(kw)
    ev = ev.sort_values(["s", "b"])
    em = {"X30": (0, 30), "X60": (0, 60), "X120": (0, 120), "REC50": (1, 0), "X1615": (2, 0)}[p["exit"]]
    cs = C45.cost_side(mk.k, p["slip"])
    L, Cm = campaign(mk.o, mk.h, mk.l, mk.c, mk.FP, mk.FPb, legm, mk.u5, ev.s.values.astype(np.int64), ev.b.values.astype(np.int64),
                     ev.ref.values, ev.c_last.values, ev.start.values.astype(np.int64), 1 if p["entry"] == "NB" else 0, em[0], em[1],
                     p["rec_frac"], {"none": 0, "confirmed": 1, "blind": 2}[p["add"]], p["blind_x"], bool(p["trim"]), p["trim_x"],
                     bool(p["rebuild"]), int(p["max_rebuild"]), int(p["max_camp"]), cs, mk.pv, bool(p["overnight"]), int(p["delay"]),
                     p["p_miss_entry"], p["p_miss_add"], p["p_miss_trim"], int(p["seed"]), J_LAST_ENTRY, J1615)
    lots = pd.DataFrame(L, columns=["s", "lot", "type", "j_in", "px_in", "j_out", "px_out", "exit_type", "pnl", "camp", "px_1615"])
    camps = pd.DataFrame(Cm, columns=["s", "b", "j0", "px0", "target", "j_end", "overnight", "unresolved"])
    camps["camp"] = np.arange(len(camps))
    # accounting session for overnight lots = next session
    lots.attrs["dropped_nan_lots"] = int(lots.pnl.isna().sum())          # fill missing (data gap) -> lot not executed
    lots = lots[lots.pnl.notna()].reset_index(drop=True)
    lots["acct_s"] = lots.s + (lots.exit_type == 2).astype(int)
    for df in (lots, camps):
        df["s"] = df.s.astype(int)
    return lots, camps
