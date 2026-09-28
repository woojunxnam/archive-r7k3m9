"""TEST45 session-overlay genome -> integer MES/MNQ events -> simulator.  Shared by deterministic overlays, ML mapping,
GA and GP so every candidate is evaluated by exactly the same execution code.

Genome (dict).  Morning module (m_*): trigger at decision (bar end 09:30+w, w=0 -> 09:31 using the open print) if all active
gates pass; long m_q contracts filled at the next bar open; exit filled at bar end m_exit (or handed to the close module).
Close module (c_*): at decision time c_time (fill next bar) set the locked target c_base, or c_boost when the condition
c_feat c_dir c_thr holds.  Open manager (o_*): what happens to the carried (locked) position at the next RTH open.
Final target per instrument = min(QMAX, carry + max(morning, close)).  Hard frozen lock governor (not evolved): the locked
inventory stress sum(q * LOCK_K * ATR * $/pt) must be <= LOCK_BUDGET, otherwise the locked target is cut (largest first)."""
import numpy as np

import t45_common as C
import t45_feat as F
import t45_sim as S

g = C.g
WINDOWS = [0, 5, 15, 30, 60, 90]
M_EXITS = ["10:30", "11:00", "12:00", "13:00", "14:00", "15:00", "15:45", "16:00", "CARRY"]
C_TIMES = ["14:30", "15:00", "15:15", "15:30", "15:45", "16:00", "16:14"]
C_FEATS = ["none", "rth_ret", "day_ret", "dist_vwap", "range_pos", "mom15", "mom60", "accel", "champ_pos"]
GAP_KINDS = ["lock", "cash"]
GAP_NORMS = ["atr", "range", "sigma", "pct"]
O_RULES = ["EXIT_OPEN", "KEEP_ADVERSE", "EXIT_AFTER", "KEEP_UNTIL"]
O_UNTIL = ["10:30", "11:00", "12:00", "15:00", "16:00"]
O_W = [1, 5, 15, 30, 60]
QMAX = 2
LOCK_K = 2.5            # frozen: ~p0.5 locked loss in ATR units (T45_17)
LOCK_BUDGET = 4000.0    # frozen: $ stress budget for the overlay's locked inventory


class Bank:
    """all causal feature arrays needed by any genome, per instrument k."""

    def __init__(self, P):
        self.sims = [S.Sim(P, i) for i in C.INSTS]
        self.bench = S.Bench(self.sims)
        self.sess = self.sims[0].pn.sess
        self.n = self.sims[0].n
        st = F.champion_state(self.sess)
        self.I = []
        for k, sm in enumerate(self.sims):
            pn = sm.pn; o = self.sims[1 - k].pn
            d = {"atr": pn.atr, "vol_pct": np.nan_to_num(pn.vol_pct, nan=0.5), "trend": np.sign(np.nan_to_num(pn.p_trend20)),
                 "rel_gap": pn.gap_lock / pn.atr - o.gap_lock / o.atr,
                 "champ_open": st[f"p{C.INSTS[k]}_0930"].values, "champ_1612": st[f"p{C.INSTS[k]}_1612"].values,
                 "champ_dd": st["champ_dd_prev"].values, "gap_lock_atr": pn.gap_lock / pn.atr}
            for kind in GAP_KINDS:
                gp = pn.gap_lock if kind == "lock" else pn.gap_cash
                ref = pn.p_lock if kind == "lock" else pn.p_cash
                for nm in GAP_NORMS:
                    d[f"gap_{kind}_{nm}"] = C.normalise(gp, nm, pn, ref)
            for w in WINDOWS:
                f = F.morning(pn, w)
                d[f"selloff_{w}"] = f["selloff_w"]; d[f"reclaim_{w}"] = f["reclaim_frac"]
            for t in C_TIMES:
                f = F.late(pn, g(t))
                for nm in C_FEATS[1:-1]:
                    d[f"{nm}@{t}"] = f[nm]
                d[f"champ_pos@{t}"] = st[f"p{C.INSTS[k]}_{t.replace(':', '')}"].values      # champion position in effect at t
            d["fill_ok"] = ~np.isnan(sm.FP)
            self.I.append(d)


DEFAULT = {"inst": "BOTH", "m_on": 0, "m_gap_kind": "lock", "m_gap_norm": "atr", "m_gap_hi": np.inf, "m_gap_lo": -np.inf, "m_w": 0,
           "m_flush_hi": np.inf, "m_flush_lo": -np.inf, "m_reclaim": 0.0, "m_exit": "16:00", "m_q": 1, "m_vol_max": 1.0,
           "m_trend": 0, "m_rel": 0, "m_v6": 0, "m_dd_max": np.inf,
           "c_on": 0, "c_time": "16:14", "c_base": 1, "c_feat": "none", "c_dir": 1, "c_thr": 0.0, "c_boost": 1, "c_vol_max": 1.0,
           "o_rule": "EXIT_OPEN", "o_thr": -0.75, "o_until": "12:00", "o_w": 1}


def G(**kw):
    x = dict(DEFAULT); x.update(kw)
    return x


def complexity(ge):
    c = 0
    if ge["m_on"]:
        c += 1 + sum([np.isfinite(ge["m_gap_hi"]), np.isfinite(ge["m_gap_lo"]), np.isfinite(ge["m_flush_hi"]), np.isfinite(ge["m_flush_lo"]),
                      ge["m_reclaim"] > 0, ge["m_vol_max"] < 1.0, ge["m_trend"] != 0, ge["m_rel"] != 0, ge["m_v6"] != 0,
                      np.isfinite(ge["m_dd_max"])])
    if ge["c_on"]:
        c += 1 + (ge["c_feat"] != "none") + (ge["c_vol_max"] < 1.0)
        c += ge["o_rule"] != "EXIT_OPEN"
    return int(c)


def insts(ge):
    return [0, 1] if ge["inst"] == "BOTH" else [C.INSTS.index(ge["inst"])]


def morning_trigger(ge, d, cond_tree=None):
    x = d[f"gap_{ge['m_gap_kind']}_{ge['m_gap_norm']}"]
    w = ge["m_w"]
    so = d[f"selloff_{w}"]
    t = (x <= ge["m_gap_hi"]) & (x > ge["m_gap_lo"]) & (so <= ge["m_flush_hi"]) & (so > ge["m_flush_lo"])
    t &= d[f"reclaim_{w}"] >= ge["m_reclaim"]
    t &= d["vol_pct"] <= ge["m_vol_max"]
    if ge["m_trend"]:
        t &= d["trend"] == ge["m_trend"]
    if ge["m_rel"]:
        t &= np.sign(d["rel_gap"]) == -ge["m_rel"]           # m_rel=+1: own gap weaker (more negative) than the other index
    if ge["m_v6"] == 1:
        t &= d["champ_open"] > 0
    elif ge["m_v6"] == -1:
        t &= d["champ_open"] <= 0
    t &= d["champ_dd"] <= ge["m_dd_max"]
    if cond_tree is not None:
        t &= cond_tree
    return t & ~np.isnan(x) & ~np.isnan(d["atr"])


def close_target(ge, d, cond_tree=None):
    n = len(d["atr"])
    base = np.full(n, ge["c_base"], np.int64)
    if cond_tree is not None:
        cond = cond_tree
    elif ge["c_feat"] == "none":
        cond = np.zeros(n, bool)
    else:
        f = d[f"{ge['c_feat']}@{ge['c_time']}"]
        cond = (f > ge["c_thr"]) if ge["c_dir"] > 0 else (f < ge["c_thr"])
        cond &= ~np.isnan(f)
    q = np.where(cond, max(ge["c_boost"], ge["c_base"]), base)
    q = np.where(d["vol_pct"] <= ge["c_vol_max"], q, 0)
    return np.where(np.isnan(d["atr"]), 0, q)


def build(ge, bank, m_tree=None, c_tree=None, qc_ext=None, qm_ext=None):
    """-> {k: (ev_j, ev_q)}"""
    ks = insts(ge)
    n = bank.n
    qc = {}; mt = {}
    jc = g(ge["c_time"]) + 1
    for k in ks:
        d = bank.I[k]
        qc[k] = close_target(ge, d, None if c_tree is None else c_tree[k]) if ge["c_on"] else np.zeros(n, np.int64)
        if qc_ext is not None:
            qc[k] = np.where(np.isnan(d["atr"]), 0, qc_ext[k]).astype(np.int64)
        qc[k] = np.where(d["fill_ok"][:, jc], qc[k], 0)                # cannot build the lock if the bar does not exist
        mt[k] = morning_trigger(ge, d, None if m_tree is None else m_tree[k]) if ge["m_on"] else np.zeros(n, bool)
    # frozen lock governor (joint)
    if ge["c_on"]:
        stress = sum(qc[k] * LOCK_K * np.nan_to_num(bank.I[k]["atr"]) * C.PV[k] for k in ks)
        over = stress > LOCK_BUDGET
        if over.any():
            for _ in range(4):
                for k in sorted(ks, key=lambda k: -C.PV[k] * np.nanmean(bank.I[k]["atr"])):
                    stress = sum(qc[kk] * LOCK_K * np.nan_to_num(bank.I[kk]["atr"]) * C.PV[kk] for kk in ks)
                    cut = (stress > LOCK_BUDGET) & (qc[k] > 0)
                    qc[k] = np.where(cut, qc[k] - 1, qc[k])
    out = {}
    jm = max(ge["m_w"], 1)
    m_exit = ge["m_exit"]
    if m_exit == "CARRY" and not ge["c_on"]:
        m_exit = "16:00"
    jme = jc if m_exit == "CARRY" else g(m_exit)
    for k in ks:
        d = bank.I[k]
        carry = np.r_[0, qc[k][:-1]]
        # carried-position exit index
        if ge["o_rule"] == "EXIT_OPEN":
            jx = np.zeros(n, np.int64)
        elif ge["o_rule"] == "EXIT_AFTER":
            jx = np.full(n, ge["o_w"], np.int64)
        elif ge["o_rule"] == "KEEP_UNTIL":
            jx = np.full(n, g(ge["o_until"]), np.int64)
        else:                                                       # KEEP_ADVERSE: decided after the open print (fill 09:32)
            adv = d["gap_lock_atr"] <= ge["o_thr"]
            jx = np.where(adv, g(ge["o_until"]), 1).astype(np.int64)
        qm = np.where(mt[k] & (jm < jme), ge["m_q"], 0)
        if qm_ext is not None:
            qm = np.where(mt[k] & (jm < jme), qm_ext[k], 0)
        pts = np.stack([np.zeros(n, np.int64), jx, np.full(n, jm), np.full(n, jme), np.full(n, jc)], 1)
        pts = np.sort(pts, 1)
        tq = np.zeros_like(pts)
        for c in range(pts.shape[1]):
            j = pts[:, c]
            cy = np.where(j < jx, carry, 0)
            mo = np.where((j >= jm) & (j < jme), qm, 0)
            cl = np.where(j >= jc, qc[k], 0) if ge["c_on"] else 0
            late_part = np.where(j >= jc, cl, mo) if ge["c_on"] else mo
            tq[:, c] = np.minimum(QMAX, cy + late_part)
        if not ge["c_on"] and not ge["m_on"]:
            tq[:] = 0
        out[k] = (pts, tq)
    return out


def run(ge, bank, slip=1.0, m_tree=None, c_tree=None, qc_ext=None, qm_ext=None):
    ev = build(ge, bank, m_tree, c_tree, qc_ext, qm_ext)
    return {k: bank.sims[k].run(j, q, slip) for k, (j, q) in ev.items()}


def daily(res, n):
    return sum((r["pnl"] for r in res.values()), np.zeros(n))


BLOCKS = [("PRE_2021", "2019-01-01", "2020-12-31")] + list(C.OUTER)


def block_avgs(pnl, sess):
    return {b: float(np.mean(pnl[(sess >= np.datetime64(s)) & (sess <= np.datetime64(e))])) for b, s, e in BLOCKS}


def report(ge, bank, name, m_tree=None, c_tree=None, periods=True, qc_ext=None, qm_ext=None, mask=None):
    res = run(ge, bank, 1.0, m_tree, c_tree, qc_ext, qm_ext)
    res4 = run(ge, bank, 4.0, m_tree, c_tree, qc_ext, qm_ext)
    if mask is not None:
        o = {"name": name, **S.metrics(res, bank.bench, mask)}
        pnl = daily(res, bank.n)
        o["SLIP4_total"] = float(daily(res4, bank.n)[mask].sum())
        ob = [float(np.mean(pnl[(bank.sess.values >= np.datetime64(s_)) & (bank.sess.values <= np.datetime64(e_)) & mask]))
              for _, s_, e_ in C.OUTER if ((bank.sess.values >= np.datetime64(s_)) & (bank.sess.values <= np.datetime64(e_)) & mask).any()]
        o["outer_blocks_median"] = float(np.median(ob)); o["outer_blocks_min"] = float(np.min(ob)); o["outer_blocks_pos"] = int(np.sum(np.array(ob) > 0))
        o["complexity"] = complexity(ge)
        return o, [], pnl
    o = {"name": name, **S.metrics(res, bank.bench)}
    pnl = daily(res, bank.n)
    o["SLIP4_total"] = float(daily(res4, bank.n).sum())
    ba = block_avgs(pnl, bank.sess.values)
    o.update({f"blk_{k}": v for k, v in ba.items()})
    ob = [ba[b] for b, _, _ in C.OUTER]
    o["outer_blocks_median"] = float(np.median(ob)); o["outer_blocks_min"] = float(np.min(ob)); o["outer_blocks_pos"] = int(np.sum(np.array(ob) > 0))
    o["complexity"] = complexity(ge)
    rows = []
    if periods:
        for p in C.PERIODS:
            m = C.mask_period(bank.sess, p)
            rows.append({"name": name, "period": p, **S.metrics(res, bank.bench, m)})
    return o, rows, pnl
