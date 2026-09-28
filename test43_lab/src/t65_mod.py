"""TEST65+ module simulator + full incremental evaluation against the frozen T61-R1C (T61 has priority on the global MNQ cap 6)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import t47_engine as E  # noqa: E402
from t53_run import matched_excess  # noqa: E402
from t65_run import Ctx  # noqa: E402


class Env:
    def __init__(self):
        self.X = Ctx(); X = self.X
        self.mk = {"MNQ": X.nq, "ES": X.es}
        self.bk = H.Book({"ES": X.es, "MNQ": X.nq})
        self.full = np.asarray(X.sess >= K.START)


def simulate(env, sig, inst="MNQ", slip=1.0, delay=0, lots=1):
    """sig: DataFrame s, j_in, s_out, j_out (grid; entry fill at open of j_in).  MNQ lots are cut at the same fill whenever T61 MNQ + module > 6."""
    X = env.X; mk = env.mk[inst]; n = X.n; pv = mk.pv; cs = C45.cost_side(mk.k, slip)
    q61 = X.qN if inst == "MNQ" else X.qE; cap = K.MNQ_CAP if inst == "MNQ" else K.MES_CAP_TOTAL
    daily = np.zeros(n); led = []; cnt = np.zeros((n, C45.NG), np.int8)
    busy_until = {}
    for r in sig.itertuples(index=False):
        s, j = int(r.s), int(r.j_in) + delay
        so, jo = int(r.s_out), int(r.j_out)
        if j >= min(jo, E.J1615) if so == s else j >= E.J1615:
            continue
        if busy_until.get(s, -1) >= j:
            continue
        if q61[s, j] + lots > cap:
            continue
        px = mk.FP[s, j]
        if np.isnan(px):
            continue
        # hold; intraday only in this layer (so == s)
        jx, why = jo, "planned"
        for jj in range(j + 1, jo):
            if q61[s, jj] + lots > cap:
                jx, why = jj, "t61_priority_cut"; break
        cnt[s, j:jx] += lots
        pxo = mk.FPb[s, jx]
        if np.isnan(pxo):
            row = mk.FPb[s, jx:]; ok = np.where(~np.isnan(row))[0]; pxo = row[ok[0]] if len(ok) else px
        pnl = lots * ((pxo - px) * pv - 2 * cs)
        daily[s] += pnl; busy_until[s] = jx
        led.append({"s_in": s, "j_in": j, "s_x": s, "j_x": jx, "px": px, "px_x": pxo, "pnl": pnl, "why": why})
    return daily, pd.DataFrame(led, columns=["s_in", "j_in", "s_x", "j_x", "px", "px_x", "pnl", "why"]), cnt


def evaluate(env, name, sig, inst="MNQ", plateau=None, from21=False):
    X = env.X; sess = X.sess
    msk = np.asarray(sess >= K.S21) if from21 else np.ones(X.n, bool)
    d, L, cnt = simulate(env, sig, inst); d = d * msk
    d4, _, _ = simulate(env, sig, inst, slip=4.0); d1, _, _ = simulate(env, sig, inst, delay=1); d5, _, _ = simulate(env, sig, inst, delay=5)
    ex = matched_excess(env.mk[inst], L) * msk if len(L) else np.zeros(X.n)
    pl = []
    for s_ in (plateau or []):
        x, _, _ = simulate(env, s_, inst); pl.append(float((x * msk)[env.full].sum()))
    base = float(d[env.full].sum())
    qN = X.qN + (cnt if inst == "MNQ" else 0); qE = X.qE + (cnt if inst == "ES" else 0)
    mi = (qE * env.bk.m_in["ES"][:, None] + qN * env.bk.m_in["MNQ"][:, None])[env.full].max()
    extra = {"matched_excess_day": float(ex[env.full].mean()), "slip4_incr_avg_day": float((d4 * msk)[env.full].mean()),
             "delay1_incr_avg_day": float((d1 * msk)[env.full].mean()), "delay5_incr_avg_day": float((d5 * msk)[env.full].mean()),
             "plateau_pass": bool(len(pl) > 0 and all(v > 0 and v >= 0.6 * base for v in pl)), "plateau_totals": str([round(v) for v in pl]),
             "peak_total_MNQ": int(qN[env.full].max()), "peak_total_MES": int(qE[env.full].max()), "peak_margin_pct": float(mi / H.NLV * 100),
             "trades": int(len(L)), "win_rate": float((L.pnl > 0).mean()) if len(L) else np.nan, "priority_cuts": int((L.why == "t61_priority_cut").sum()) if len(L) else 0,
             "turnover_sides_per_day": 2 * len(L) / env.full.sum()}
    o = K.incremental_gate(name, d, X.t61, sess, extra)
    return o, d


def simulate_multi(env, sig, inst="ES", slip=1.0, delay=0, lots=2):
    """multi-session holds, close-to-close mark-to-market (16:14 close marks) so daily $ / worst day include overnight gaps.
    sig: s, j_in, s_out, j_out.  MES: total MES <= 8 (T61 MES <= 6).  MNQ: T61 priority cut as in simulate()."""
    X = env.X; mk = env.mk[inst]; n = X.n; pv = mk.pv; cs = C45.cost_side(mk.k, slip)
    q61 = X.qN if inst == "MNQ" else X.qE; cap = K.MNQ_CAP if inst == "MNQ" else K.MES_CAP_TOTAL
    Cc = X.C[inst]; daily = np.zeros(n); led = []; cnt = np.zeros((n, C45.NG), np.int8); busy = -1
    for r in sig.itertuples(index=False):
        s, j, so, jo = int(r.s), int(r.j_in) + delay, int(r.s_out), int(r.j_out)
        if s <= busy or so >= n or q61[s, j] + lots > cap:
            continue
        px = mk.FP[s, j]
        if np.isnan(px):
            continue
        mark = px; sx, jx, why = so, jo, "planned"
        for ss in range(s, so + 1):
            j0 = j if ss == s else 0; j1 = jo if ss == so else C45.NG
            bad = np.where(q61[ss, j0 + (1 if ss == s else 0):j1] + lots > cap)[0]
            if len(bad):
                sx, jx, why = ss, j0 + (1 if ss == s else 0) + int(bad[0]), "t61_priority_cut"
            if sx == ss:
                pxo = mk.FPb[ss, jx]
                if np.isnan(pxo):
                    row = mk.FPb[ss, jx:]; ok = np.where(~np.isnan(row))[0]; pxo = row[ok[0]] if len(ok) else (Cc[ss, E.J1615] if not np.isnan(Cc[ss, E.J1615]) else mark)
                cnt[ss, j0:jx] += lots
                daily[ss] += lots * (pxo - mark) * pv - lots * 2 * cs
                break
            cnt[ss, j0:] += lots
            cm = Cc[ss, E.J1615]
            if np.isnan(cm):                                   # session without prints: carry the mark
                continue
            daily[ss] += lots * (cm - mark) * pv; mark = cm
        busy = sx
        led.append({"s_in": s, "j_in": j, "s_x": sx, "j_x": jx, "px": px, "px_x": pxo, "pnl": lots * ((pxo - px) * pv - 2 * cs), "why": why})
    return daily, pd.DataFrame(led, columns=["s_in", "j_in", "s_x", "j_x", "px", "px_x", "pnl", "why"]), cnt


def evaluate_multi(env, name, sig, inst="ES", lots=2, plateau=None):
    X = env.X
    f = lambda **kw: simulate_multi(env, sig, inst, lots=lots, **kw)
    d, L, cnt = f(); d4 = f(slip=4.0)[0]; d1 = f(delay=1)[0]; d5 = f(delay=5)[0]
    ex = matched_excess(env.mk[inst], L) if len(L) else np.zeros(X.n)
    pl = [float(simulate_multi(env, s_, inst, lots=lots)[0][env.full].sum()) for s_ in (plateau or [])]
    base = float(d[env.full].sum())
    qN = X.qN + (cnt if inst == "MNQ" else 0); qE = X.qE + (cnt if inst == "ES" else 0)
    lock = E.J1615 - 1
    mi = max((qE * env.bk.m_in["ES"][:, None] + qN * env.bk.m_in["MNQ"][:, None])[env.full].max(),
             (qE[:, lock] * env.bk.m_on["ES"] + qN[:, lock] * env.bk.m_on["MNQ"])[env.full].max())
    extra = {"matched_excess_day": float(ex[env.full].mean()), "slip4_incr_avg_day": float(d4[env.full].mean()), "delay1_incr_avg_day": float(d1[env.full].mean()),
             "delay5_incr_avg_day": float(d5[env.full].mean()), "plateau_pass": bool(len(pl) > 0 and all(v > 0 and v >= 0.6 * base for v in pl)),
             "plateau_totals": str([round(v) for v in pl]), "peak_total_MNQ": int(qN[env.full].max()), "peak_total_MES": int(qE[env.full].max()),
             "peak_margin_pct": float(mi / H.NLV * 100), "trades": int(len(L)), "win_rate": float((L.pnl > 0).mean()) if len(L) else np.nan,
             "priority_cuts": int((L.why == "t61_priority_cut").sum()) if len(L) else 0, "turnover_sides_per_day": 2 * lots * len(L) / env.full.sum()}
    return K.incremental_gate(name, d, X.t61, X.sess, extra), d, L
