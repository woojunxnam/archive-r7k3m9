"""TEST45 event simulator on the 1-minute execution grid (one instrument, long-only integer targets 0..Qmax).

Per session s a strategy supplies up to K events (grid fill index j, target q).  Events must be in increasing j.
Fill price = open of the bar end-stamped at grid j (forward fallback <= 3 min; if the session already ended, e.g. early close,
the last existing bar's open - reductions only; an entry whose bar does not exist is skipped).  Position between events is constant; the position after the last event is carried
(LOCKED) into the next session until that session's first event.  Accounting marks at the session-end close (17:00 bar;
accounting only).  Costs: commission + slippage ticks per contract side; a carried position into a contract-switch session
pays one roll (2 sides) on the previous session (rolled during RTH before the lock)."""
import numpy as np
from numba import njit

import t45_common as C


def fill_matrix(pn):
    O = pn.O
    n, G = O.shape
    FP = O.copy()
    for k in range(1, 4):
        sh = np.full_like(O, np.nan); sh[:, :-k] = O[:, k:]
        FP = np.where(np.isnan(FP), sh, FP)
    # backward fallback after the last existing bar (early close / data end): last existing open
    last_open = np.full(n, np.nan)
    lastj = np.full(n, -1)
    for s in range(n):
        idx = np.where(~np.isnan(O[s]))[0]
        if len(idx):
            last_open[s] = O[s, idx[-1]]; lastj[s] = idx[-1]
    after = np.arange(G)[None, :] > lastj[:, None]
    FPb = FP.copy()
    for k in range(4, 16):                       # reductions: forward fallback up to 15 min (data gap), never earlier
        sh = np.full_like(O, np.nan); sh[:, :-k] = O[:, k:]
        FPb = np.where(np.isnan(FPb), sh, FPb)
    FPb = np.where(np.isnan(FPb) & after, last_open[:, None], FPb)
    return FP, FPb, lastj


@njit(cache=True)
def _sim(FP, FPb, se, roll_next, ev_j, ev_q, cs, q0init):
    n, K = ev_j.shape
    G = FP.shape[1]
    pnl = np.zeros(n); pnl_on = np.zeros(n); cost = np.zeros(n); sides = np.zeros(n)
    q_end = np.zeros(n); q_rth = np.zeros(n); q_open = np.zeros(n)
    q = q0init
    prev_se = np.nan
    for s in range(n):
        qin = q
        q_open[s] = qin
        last_px = prev_se
        first = True
        acc_q_time = 0.0
        last_j = 0
        cur_q = qin
        for k in range(K):
            j = ev_j[s, k]
            if j < 0:
                continue
            tq = ev_q[s, k]
            if tq == cur_q:
                continue
            # entries/adds: forward fills only; reductions may use the last existing bar of an (early-)closed session
            px = FP[s, j] if tq > cur_q else FPb[s, j]
            if np.isnan(px):
                continue
            if not np.isnan(last_px):
                seg = cur_q * (px - last_px)
                if first:
                    pnl_on[s] += seg
                pnl[s] += seg
            first = False
            acc_q_time += cur_q * (j - last_j); last_j = j
            dq = abs(tq - cur_q)
            cost[s] += dq * cs; sides[s] += dq
            cur_q = tq
            last_px = px
        acc_q_time += cur_q * (G - last_j)
        q_rth[s] = acc_q_time / G
        if not np.isnan(se[s]) and not np.isnan(last_px):
            seg = cur_q * (se[s] - last_px)
            pnl[s] += seg
            if first:
                pnl_on[s] += seg
        if cur_q > 0 and roll_next[s]:
            cost[s] += 2 * cur_q * cs; sides[s] += 2 * cur_q
        q = cur_q
        q_end[s] = cur_q
        if not np.isnan(se[s]):
            prev_se = se[s]
    return pnl, pnl_on, cost, sides, q_end, q_rth, q_open


class Sim:
    def __init__(self, P, inst):
        self.pn = C.Panel(P, inst)
        self.k = C.INSTS.index(inst)
        self.FP, self.FPb, self.lastj = fill_matrix(self.pn)
        self.pv = C.PV[self.k]
        self.roll_next = np.r_[self.pn.roll_in[1:], False]
        self.n = self.pn.n

    def run(self, ev_j, ev_q, slip_ticks=1.0):
        cs = C.cost_side(self.k, slip_ticks)
        ev_j = np.ascontiguousarray(ev_j, np.int64); ev_q = np.ascontiguousarray(ev_q, np.int64)
        pnl, pon, cost, sides, qe, qr, qo = _sim(self.FP, self.FPb, self.pn.se, self.roll_next, ev_j, ev_q, cs / self.pv, 0)
        pv = self.pv
        return {"gross": pnl * pv, "carry_in": pon * pv, "cost": cost * pv, "pnl": (pnl - cost) * pv, "sides": sides,
                "q_end": qe, "q_rth": qr, "q_open": qo}


def events(n, K=4):
    return np.full((n, K), -1, np.int64), np.zeros((n, K), np.int64)


# ---------------------------------------------------------------------------------------------- metrics
RTH_W = C.NG / 1380.0          # share of the 23h trading day inside the 09:31..16:15 grid
ON_W = 1.0 - RTH_W


class Bench:
    """Passive benchmarks per instrument ($ for 1 contract, no cost): whole-day (session-end to session-end),
    RTH segment (open -> 16:15 fill) and LOCK segment (previous 16:15 fill -> open)."""

    def __init__(self, sims):
        self.sims = sims
        self.sess = sims[0].pn.sess
        self.day = {}; self.rth = {}; self.on = {}
        for sm in sims:
            pn = sm.pn; pv = sm.pv
            self.day[sm.k] = np.nan_to_num(np.r_[np.nan, np.diff(pn.se)] * pv)
            self.rth[sm.k] = np.nan_to_num((sm.FP[:, C.LOCK_FILL_BAR] - sm.FP[:, C.OPEN_BAR]) * pv)
            self.on[sm.k] = np.nan_to_num((sm.FP[:, C.OPEN_BAR] - np.r_[np.nan, sm.FP[:-1, C.LOCK_FILL_BAR]]) * pv)
        self.champ = C.champion_daily().pnl.reindex(self.sess).fillna(0.0).values


def metrics(results, bench, mask=None, champion=True):
    """results: {k: sim-run dict}.  Portfolio metrics of the overlay alone, betas, and incremental vs champion."""
    n = len(bench.sess)
    m = np.ones(n, bool) if mask is None else mask
    pnl = sum(r["pnl"] for r in results.values())[m]
    o = C.dstats(pnl)
    mb = smb = 0.0
    for k, r in results.items():
        q_on = np.r_[0.0, r["q_end"][:-1]][m]          # position held through the lock INTO session s
        q_rth = r["q_rth"][m]
        expo = RTH_W * q_rth.mean() + ON_W * q_on.mean()
        mb += expo * bench.day[k][m].mean()
        smb += q_rth.mean() * bench.rth[k][m].mean() + q_on.mean() * bench.on[k][m].mean()
        o[f"avg_on_contracts_k{k}"] = float(q_on.mean()); o[f"avg_rth_contracts_k{k}"] = float(q_rth.mean())
    o["matched_beta_excess"] = o["avg"] - mb
    o["session_matched_beta_excess"] = o["avg"] - smb
    o["gross"] = float(sum(r["gross"] for r in results.values())[m].sum())
    o["cost"] = float(sum(r["cost"] for r in results.values())[m].sum())
    o["sides"] = float(sum(r["sides"] for r in results.values())[m].sum())
    o["carry_in_pnl"] = float(sum(r["carry_in"] for r in results.values())[m].sum())
    if champion:
        ch = bench.champ[m]
        cmb = ch + pnl
        co = C.dstats(cmb, prefix="comb_")
        chs = C.dstats(ch)
        o.update(co)
        o["incr_avg"] = co["comb_avg"] - chs["avg"]
        o["incr_max_dd"] = co["comb_max_dd"] - chs["max_dd"]
        o["corr_champion"] = float(np.corrcoef(ch, pnl)[0, 1]) if pnl.std() > 0 else np.nan
        worst = np.argsort(ch)[:20]
        o["worst20_champion_overlay_loss_share"] = float((pnl[worst] < 0).mean())
        o["worst20_champion_overlay_sum"] = float(pnl[worst].sum())
        both = (ch < 0) & (pnl < 0)
        o["loss_day_overlap"] = float(both.sum() / max((pnl < 0).sum(), 1))
    return o


def period_table(results, bench, pers=None, champion=True):
    pers = pers or list(C.PERIODS)
    rows = []
    for p in pers:
        m = C.mask_period(bench.sess, p)
        if m.sum() == 0:
            continue
        rows.append({"period": p, **metrics(results, bench, m, champion)})
    return rows
