"""TEST95+ shared layer: MAIN_GROWTH_V1 baseline (T61-R1C + FIXED_CLUE_BASKET_V1, frozen), capacity occupancy, intraday trade kernels with
stop / breakeven / trailing management, standalone + portfolio gates.  Research data <= 2026-05-27."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402

LAB = B.LAB; CL = os.path.join(LAB, "out", "CANONICAL_LAB"); os.makedirs(CL, exist_ok=True)
REPC = os.path.join(LAB, "reports", "CANONICAL_LAB"); os.makedirs(REPC, exist_ok=True)
NG, J15 = A.NG, A.J15


def main_baseline(I):
    """daily $ of MAIN = T61 + basket, and MNQ / MES occupancy (T61 target + basket open lots) per session x minute."""
    sess = I.sess
    t61 = K.t61_daily()["T61-R1C"].daily_pnl.reindex(sess).fillna(0).values
    z = np.load(os.path.join(LAB, "out", "PRESS_BASKET_LAB", "LANE_B_BASKET", "BASKET_daily.npz"))
    bas = z["basket"]; assert len(bas) == len(sess)
    cp = os.path.join(A.AP, "cache", "t61_minutes_full.npz"); zz = np.load(cp); ts = pd.DatetimeIndex(zz["sess"]); ix = pd.Index(ts).get_indexer(sess)
    al = lambda a: np.where(ix[:, None] >= 0, a[np.clip(ix, 0, None)], 0).astype(np.int64)
    occN, occE = al(zz["final_target_MNQ"]), al(zz["final_target_MES"])
    L = pd.read_csv(os.path.join(LAB, "out", "PRESS_BASKET_LAB", "LANE_B_BASKET", "BASKET_LEDGER.csv"))
    for r in L.itertuples(index=False):
        (occN if r.inst == "MNQ" else occE)[int(r.s), int(r.j_in):int(r.j_x)] += int(r.lots)
    return t61 + bas, t61, bas, occN, occE


@njit(cache=True)
def run_intraday(C, H, L, FP, FPb, sig_s, sig_j, stop_px, OCC, cap, lots, be_R, trail_n, tgt_px, mode, J15_, delay, maxd):
    """sequential intraday trades.  sig_j = decision minute (fill at j+1+delay).  mode 0: stop / breakeven(be_R) / trail(lowest low of last trail_n
    completed 5m bars) / 16:15; mode 1: fixed target & stop (T2A, stop first on same bar).  Capacity: skip if OCC + lots > cap at fill; cut if later.
    returns rows: s, j_in, j_x, px_in, px_x, reason(1 stop 2 target 3 eod 4 cap)."""
    n = sig_s.shape[0]; out = np.full((n, 6), np.nan); m = 0; busy_s = -1; busy_j = -1; cnt_s = -1; cnt = 0
    for e in range(n):
        s = sig_s[e]; ji = sig_j[e] + 1 + delay
        if s != cnt_s:
            cnt_s = s; cnt = 0
        if ji >= J15_ or (s == busy_s and ji <= busy_j) or cnt >= maxd:
            continue
        if OCC[s, ji] + lots > cap:
            continue
        px = FP[s, ji]
        if px != px:
            continue
        stp = stop_px[e]; risk = px - stp
        if not risk > 0:
            continue
        tgt = tgt_px[e]; be = False; jx = J15_; xp = FPb[s, J15_]; why = 3
        for k in range(ji, J15_):
            if OCC[s, k] + lots > cap and k > ji:
                jx = k; xp = FPb[s, k]; why = 4; break
            if L[s, k] <= stp:
                jx = k; xp = min(stp, FP[s, k]) if k > ji else stp; why = 1; break
            if mode == 1 and H[s, k] >= tgt:
                jx = k; xp = tgt; why = 2; break
            if mode == 0:
                if not be and H[s, k] >= px + be_R * risk:
                    be = True
                    if stp < px:
                        stp = px
                if be and (k + 1) % 5 == 0 and k >= 5 * trail_n:
                    lo = 1e18
                    for q in range(k + 1 - 5 * trail_n, k + 1):
                        if L[s, q] < lo:
                            lo = L[s, q]
                    if lo > stp:
                        stp = lo
        out[m, 0] = s; out[m, 1] = ji; out[m, 2] = jx; out[m, 3] = px; out[m, 4] = xp; out[m, 5] = why; m += 1
        busy_s = s; busy_j = jx; cnt += 1
    return out[:m]


@njit(cache=True)
def _manage(H, L, FP, FPb, OCC, cap, lots, s, ji, px, stp, tgt, be_px, trail_n, mode, J15_, same_bar_stop):
    """shared exit loop from bar ji (entry bar).  mode 1 target/stop, mode 0 stop -> breakeven at be_px -> trail.  entry bar: stop only."""
    be = False
    for k in range(ji, J15_):
        if OCC[s, k] + lots > cap and k > ji:
            return k, FPb[s, k], 4
        if L[s, k] <= stp and (k > ji or same_bar_stop):
            return k, (min(stp, FP[s, k]) if k > ji else stp), 1
        if k == ji:
            continue
        if mode == 1 and H[s, k] >= tgt:
            return k, tgt, 2
        if mode == 0:
            if not be and H[s, k] >= be_px:
                be = True
                if stp < px:
                    stp = px
            if be and (k + 1) % 5 == 0 and k >= 5 * trail_n:
                lo = 1e18
                for q in range(k + 1 - 5 * trail_n, k + 1):
                    if L[s, q] < lo:
                        lo = L[s, q]
                if lo > stp:
                    stp = lo
    return J15_, FPb[s, J15_], 3


@njit(cache=True)
def run_stop_entry(O, H, L, FP, FPb, ev_s, lvl, j0, j1, stop_d, tgt_d, be_d, OCC, cap, lots, trail_n, mode, J15_, delay):
    """one resting buy stop per event: level lvl active on bars j0..j1 (inclusive); gap above at j0 -> open fill.  fill = max(open, level)
    (delay: next bar open).  stop = px - stop_d, target = px + tgt_d, breakeven trigger px + be_d.  rows s, j_in, j_x, px_in, px_x, why."""
    n = ev_s.shape[0]; out = np.full((n, 6), np.nan); m = 0
    for e in range(n):
        s = ev_s[e]; ji = -1
        for k in range(j0[e], j1[e] + 1):
            if H[s, k] >= lvl[e]:
                ji = k; break
        if ji < 0:
            continue
        if delay > 0:
            ji += delay
            if ji >= J15_:
                continue
            px = FP[s, ji]
        else:
            px = max(O[s, ji], lvl[e])
        if px != px or OCC[s, ji] + lots > cap:
            continue
        jx, xp, why = _manage(H, L, FP, FPb, OCC, cap, lots, s, ji, px, px - stop_d[e], px + tgt_d[e], px + be_d[e], trail_n, mode, J15_, delay > 0 or O[s, ji] >= lvl[e])
        out[m, 0] = s; out[m, 1] = ji; out[m, 2] = jx; out[m, 3] = px; out[m, 4] = xp; out[m, 5] = why; m += 1
    return out[:m]


def ledger(I, rows, lots=1, cs=None):
    cs = I.cs if cs is None else cs
    D = pd.DataFrame(rows, columns=["s", "j_in", "j_x", "px_in", "px_x", "why"])
    for c in ("s", "j_in", "j_x", "why"):
        D[c] = D[c].astype(np.int64)
    D["net"] = lots * ((D.px_x - D.px_in) * I.pv - 2 * cs)
    d = np.zeros(I.n); np.add.at(d, D.s.values, D.net.values)
    return D, d


def gate(I, name, d, D, main, d4, dl, plateau_totals, controls=None, sample=(300, 40), lots=1, bk=None):
    """standalone + MAIN portfolio gate.  D must have s, j_in, j_x (same session) for matched / momentum controls (None -> skipped)."""
    full = I.full; s21 = np.asarray(I.sess >= K.S21); nd = int(full.sum())
    r = B.risk(d[full]); act = d[full & (d != 0)]; top = np.sort(act)[::-1]
    fd = {nm: float(d[np.asarray((I.sess >= a) & (I.sess <= b))].mean()) for nm, a, b in B.FOLDS}
    fn = {nm: int(((I.sess[D.s.values] >= a) & (I.sess[D.s.values] <= b)).sum()) for nm, a, b in B.FOLDS} if len(D) else {nm: 0 for nm, _, _ in B.FOLDS}
    exA = exB = np.nan
    if D is not None and len(D) and "j_in" in D and bk is not None:
        s = D.s.values.astype(np.int64); ji = D.j_in.values.astype(np.int64); jx = np.maximum(D.j_x.values.astype(np.int64), ji)
        cA = A.ctl_bucket(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, bk["B"], s, ji, jx, np.zeros(len(D), np.int64), I.pv, I.cs, False) * lots
        cB = A.ctl_bucket(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, bk["B"], s, ji, jx, np.zeros(len(D), np.int64), I.pv, I.cs, True) * lots
        exA = float(np.nansum(D.net.values - cA) / nd); exB = float(np.nansum(D.net.values - cB) / nd)
    base = float(d[full].sum())
    comb = main + d; rc, rm = B.risk(comb[full]), B.risk(main[full])
    am = full & (d != 0)
    o = {"module": name, "instrument": I.name, "trades": len(D), "trades_per_day": len(D) / nd, "avg_day": r["avg_day"], "avg_day_2021": float(d[s21].mean()),
         "usd_per_trade": float(D.net.mean()) if len(D) else np.nan, "max_dd": r["max_dd"], "worst_day": r["worst_day"], "matched_A_day": exA, "momentum_B_day": exB,
         **{f"fold_{k}": v for k, v in fd.items()}, "folds_pos": int(sum(v > 0 for v in fd.values())), "min_fold_n": min(fn.values()),
         "remove_top3": float(act.sum() - top[:3].sum()) if len(act) else 0.0, "slip4_day": float(d4[full].mean()), "delay1_day": float(dl[full].mean()),
         "plateau": str([round(v) for v in plateau_totals]), "plateau_pass": bool(base > 0 and len(plateau_totals) > 0 and all(v > 0 and v >= 0.6 * base for v in plateau_totals)),
         "corr_to_main": float(np.corrcoef(d[full], main[full])[0, 1]) if d[full].std() > 0 else 0.0,
         "loss_jaccard": float(((d < 0) & (main < 0) & am).sum() / max(((d < 0) | (main < 0))[am].sum(), 1)),
         "tail_overlap": float(d[full & (main <= np.percentile(main[full], 5))].mean()),
         "main_avg_day": rm["avg_day"], "main_maxdd": rm["max_dd"], "main_worst": rm["worst_day"], "main_ret_dd": rm["ret_dd"],
         "main_plus_avg_day": rc["avg_day"], "main_plus_maxdd": rc["max_dd"], "main_plus_worst": rc["worst_day"], "main_plus_ret_dd": rc["ret_dd"], **(controls or {})}
    g = {"g_net": o["avg_day"] > 0, "g_A": (exA > 0) if exA == exA else True, "g_B": (exB > 0) if exB == exB else True, "g_folds": o["folds_pos"] >= 4,
         "g_top3": o["remove_top3"] > 0, "g_slip4": o["slip4_day"] > 0, "g_delay": o["delay1_day"] > 0, "g_plateau": o["plateau_pass"],
         "g_sample": o["trades"] >= sample[0] and o["min_fold_n"] >= sample[1]}
    o.update(g); o["STANDALONE_PASS"] = bool(all(g.values()))
    o["PORTFOLIO_PASS"] = bool(o["STANDALONE_PASS"] and o["avg_day"] >= 10 and o["avg_day_2021"] >= 10 and rc["ret_dd"] >= rm["ret_dd"]
                               and rc["max_dd"] <= 1.10 * rm["max_dd"] and rc["worst_day"] >= -5000)
    return o


def md(name, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(os.path.join(REPC, name), "w").write("\n".join(lines) + "\n")
