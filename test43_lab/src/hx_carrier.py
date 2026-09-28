"""BETA-CARRIER-V2 engine: daily causal regime state -> sparse exposure tier (MES-equivalent units) -> integer MES/MNQ targets,
rebalanced ONLY at the session open (fill = 09:31 open, decision uses completed data through the previous session), inventory
locked overnight (no overnight stop).  Optional: vol targeting (ATR$), account-drawdown governor, margin cap, intraday-only.
P&L via the TEST45 event simulator (costs per contract side, roll costs, overnight carry)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t45_sim as S45  # noqa: E402
import hx_common as H  # noqa: E402

STATES = ["BEAR", "NEUTRAL", "BULL", "STRONG_BULL"]


def daily_state(mk, p=None):
    """state per session using data through the PREVIOUS session (known before the open)."""
    p = dict({"f": 20, "m": 50, "s": 100, "dd_bear": 5.0, "dd_strong": 1.5, "vol_strong": 0.6, "vol_crash": 0.9}, **(p or {}))
    c = pd.Series(mk.pn.cash_close).ffill()
    a = pd.Series(mk.pn.atr).ffill()
    f = c.rolling(p["f"], min_periods=int(p["f"] * 0.8)).mean(); m = c.rolling(p["m"], min_periods=int(p["m"] * 0.8)).mean()
    s = c.rolling(p["s"], min_periods=int(p["s"] * 0.8)).mean()
    dd = (c.rolling(60, min_periods=20).max() - c) / a
    sh = lambda x: x.shift(1).values
    c1, f1, m1, s1, dd1 = sh(c), sh(f), sh(m), sh(s), sh(dd)
    vol = pd.Series(mk.pn.vol_pct).fillna(0.5).values          # already through previous session
    ret5 = mk.ret5
    st = np.full(mk.n, 1)                                      # NEUTRAL
    bull = (c1 > m1) & (f1 > m1)
    strong = bull & (np.nan_to_num(s1, nan=-1e18) < m1) & (c1 > f1) & (dd1 <= p["dd_strong"]) & (vol <= p["vol_strong"])
    bear = ((c1 < m1) & ((f1 < m1) | (dd1 >= p["dd_bear"]))) | ((vol >= p["vol_crash"]) & (ret5 < 0))
    st[bull] = 2; st[strong] = 3; st[bear] = 0
    st[np.isnan(m1)] = 1
    return st


def units_to_contracts(bk, units, r_nq):
    """units = MES-equivalent risk units; r_nq = share of units allocated to MNQ."""
    ratio = bk.atr_d["ES"] / bk.atr_d["MNQ"]                   # MNQ contracts per MES-equivalent unit
    qE = np.round(units * (1 - r_nq)).astype(int)
    qN = np.round(units * r_nq * ratio).astype(int)
    return np.clip(qE, 0, 24), np.clip(qN, 0, 24)


def snap(u):
    L = np.array(H.LADDER)
    return L[np.clip(np.searchsorted(L, u, side="right") - 1, 0, len(L) - 1)]


def carrier(mks, bk, tier_map, r_nq=0.5, vol_target=False, dd_gov=None, margin_cap=0.40, intraday_only=False, slip=1.0, state_p=None,
            state_inst="ES", delay_open=False, return_detail=False):
    """tier_map: units per state (BEAR, NEUTRAL, BULL, STRONG_BULL).  dd_gov: (dd1, dd2) $ thresholds -> x0.5 / x0 (to ladder)."""
    es, nq = mks["ES"], mks["MNQ"]
    n = es.n
    st = daily_state(mks[state_inst], state_p)
    u = np.array(tier_map, float)[st]
    if vol_target:
        ref = pd.Series(bk.atr_d["ES"]).rolling(250, min_periods=60).median().shift(1).bfill().values
        u = u * np.clip(ref / bk.atr_d["ES"], 0.5, 1.5)
    u = snap(u)
    valid = (es.pn.sess >= H.START)
    u[~valid] = 0
    # margin cap (hard, overnight inventory): shrink units until margin fits
    qE, qN = units_to_contracts(bk, u, r_nq)
    mo = qE * bk.m_on["ES"] + qN * bk.m_on["MNQ"]
    over = mo > margin_cap * H.NLV
    while over.any():
        u = np.where(over, snap(np.maximum(u - 1, 0)), u)
        qE, qN = units_to_contracts(bk, u, r_nq)
        mo = qE * bk.m_on["ES"] + qN * bk.m_on["MNQ"]
        over = (mo > margin_cap * H.NLV) & (u > 0)
    # simulate; the DD governor needs the running equity -> sequential pass over sessions (open decision uses equity through prev session)
    j_open = 1 if delay_open else 0
    simE, simN = es.sim, nq.sim
    if dd_gov is None:
        rE, rN = _run(simE, simN, qE, qN, j_open, intraday_only, slip)
        d = rE["pnl"] + rN["pnl"]
    else:
        d = np.zeros(n); scale = np.ones(n)
        qE0, qN0 = qE.copy(), qN.copy()
        # one pass: governor decided from carrier equity through the previous session
        eq = 0.0; peak = 0.0
        qE, qN = qE0.copy(), qN0.copy()
        for s in range(n):
            ddv = peak - eq
            k = 0.0 if ddv >= dd_gov[1] else (0.5 if ddv >= dd_gov[0] else 1.0)
            scale[s] = k
            qE[s] = int(np.floor(qE0[s] * k)); qN[s] = int(np.floor(qN0[s] * k))
            # daily pnl of session s requires positions of s-1 (carry) and s -> compute incrementally with the vectorised sim on a 2-session window
            if s >= 1:
                rE, rN = _run(simE, simN, qE[:s + 1], qN[:s + 1], j_open, intraday_only, slip, last_only=True)
                d[s] = rE + rN
            eq += d[s]; peak = max(peak, eq)
        rE, rN = _run(simE, simN, qE, qN, j_open, intraday_only, slip)
        d = rE["pnl"] + rN["pnl"]                                   # final P&L always from the event simulator
    out = {"daily": d, "qE": qE, "qN": qN, "state": st, "units": u, "on_margin": qE * bk.m_on["ES"] + qN * bk.m_on["MNQ"],
           "cost": rE["cost"] + rN["cost"], "sides": rE["sides"] + rN["sides"], "gross": rE["gross"] + rN["gross"]}
    return out


def _run(simE, simN, qE, qN, j_open, intraday_only, slip, last_only=False):
    n = len(qE)
    K = 2
    evj = np.full((n, K), -1, np.int64); evq = np.zeros((n, K), np.int64)
    res = []
    for sim, q in ((simE, qE), (simN, qN)):
        ej, eq_ = evj.copy(), evq.copy()
        ej[:, 0] = j_open; eq_[:, 0] = q
        if intraday_only:
            ej[:, 1] = C45.LOCK_FILL_BAR; eq_[:, 1] = 0
        if last_only:
            ej = ej[-2:]; eq_ = eq_[-2:]
        if not last_only:
            res.append(sim.run(ej, eq_, slip))
    if last_only:
        return _last(simE, qE, j_open, intraday_only, slip), _last(simN, qN, j_open, intraday_only, slip)
    return res[0], res[1]


def _last(sim, q, j_open, intraday_only, slip):
    """P&L of the last session given positions for all sessions (carry from the previous session at its target)."""
    s = len(q) - 1
    pv = sim.pv; cs = C45.cost_side(sim.k, slip)
    FP, FPb, se = sim.FP, sim.FPb, sim.pn.se
    qprev = 0 if intraday_only else q[s - 1]
    pnl = 0.0
    px_open = FP[s, j_open]
    if np.isnan(px_open):
        return 0.0
    if qprev and not np.isnan(se[s - 1]):
        pnl += qprev * (px_open - se[s - 1]) * pv
    pnl -= abs(q[s] - qprev) * cs
    if intraday_only:
        px = FPb[s, C45.LOCK_FILL_BAR]
        pnl += q[s] * (px - px_open) * pv - q[s] * cs
    elif not np.isnan(se[s]):
        pnl += q[s] * (se[s] - px_open) * pv
    return pnl


def decompose(mks, bk, res, sess, mask):
    """PASSIVE_BETA (avg contracts x unconditional mean daily $ per contract), TIMING (gross - beta), FRICTION (cost)."""
    out = {}
    beta = 0.0
    for k, q in (("ES", res["qE"]), ("MNQ", res["qN"])):
        mk = mks[k]
        per = np.nan_to_num(np.r_[np.nan, np.diff(mk.pn.se)] * mk.pv)       # 1 contract held session-end to session-end
        beta += q[mask].mean() * per[mask].mean()
        out[f"avg_{k}"] = float(q[mask].mean()); out[f"max_{k}"] = int(q[mask].max())
    gross = res["gross"][mask].mean(); cost = res["cost"][mask].mean()
    out.update({"PASSIVE_BETA_day": float(beta), "TIMING_VALUE_day": float(gross - beta), "FRICTION_day": float(cost), "net_day": float(res["daily"][mask].mean()),
                "sides_per_day": float(res["sides"][mask].mean()), "cost_over_gross": float(cost / gross) if gross > 0 else np.nan,
                "avg_units": float(res["units"][mask].mean()), "max_units": float(res["units"][mask].max()),
                "avg_on_margin_frac": float(res["on_margin"][mask].mean() / H.NLV), "peak_on_margin_frac": float(res["on_margin"][mask].max() / H.NLV)})
    return out
