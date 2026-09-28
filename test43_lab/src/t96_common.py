"""TEST96 shared evaluation: generic trade simulator (planned exits incl. next open / multi-session, optional same-session stop), controls
(matched A, momentum-null B, relative-volume null), preregistered standalone / portfolio / diversifier gates vs MAIN_GROWTH_V1.
Research data <= 2026-05-27."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t95_common as T  # noqa: E402
import t96_data as X  # noqa: E402

OUT = os.path.join(B.LAB, "out", "t96"); os.makedirs(OUT, exist_ok=True)
REP = os.path.join(B.LAB, "reports", "TEST96_PLUS"); os.makedirs(REP, exist_ok=True)
CAP = {"MNQ": 6, "NQ": 6, "ES": 8}
_M = {}


def main_ctx():
    if "m" not in _M:
        Is = X.load(); main, t61, bas, occN, occE = T.main_baseline(Is["MNQ"])
        _M["m"] = dict(Is=Is, main=main, t61=t61, bas=bas, occ={"MNQ": occN, "NQ": occN, "ES": occE})
    return _M["m"]


def simulate(I, TR, cs=None, delay=0, occ=None):
    """TR: DataFrame s, j (fill minute), s_out, j_out (planned exit minute; j_out == 0 -> open fill), optional stop (same-session only).
    One position per (module) row; capacity: skip if occ + 1 > cap at fill (ES / MNQ only).  Returns ledger (s, j_in, s_x, j_x, px_in, px_x, net)."""
    cs = I.cs if cs is None else cs; cap = CAP.get(I.name); rows = []
    stop = TR["stop"].values if "stop" in TR else np.full(len(TR), np.nan)
    for r, st in zip(TR.itertuples(index=False), stop):
        s, j = int(r.s), int(r.j) + delay; so, jo = int(r.s_out), int(r.j_out)
        if j > T.J15 or (so == s and jo <= j):
            continue
        if occ is not None and cap is not None and occ[s, min(j, T.J15)] + 1 > cap:
            continue
        px = I.FP[s, j]
        if px != px:
            continue
        xs, xj = so, jo; xp = I.FP[so, 0] if jo == 0 else I.FPb[so, jo]
        if st == st:
            last = T.J15 if so > s else jo
            hit = np.where(I.L[s, j + 1:last] <= st)[0]
            if len(hit):
                k = j + 1 + int(hit[0]); xs, xj = s, k; xp = min(st, I.FP[s, k])
        if xp != xp:
            continue
        rows.append((s, j, xs, xj, px, xp))
    D = pd.DataFrame(rows, columns=["s", "j_in", "s_x", "j_x", "px_in", "px_x"])
    D["net"] = (D.px_x - D.px_in) * I.pv - 2 * cs
    return D


def daily(I, D, lots=1):
    d = np.zeros(I.n)
    if len(D):
        np.add.at(d, D.s_x.values.astype(int), lots * D.net.values)
    return d


def controls(I, D, bk):
    """matched A (year x vol tercile x bull) and momentum-null B (+ session-return bucket) and relative-volume null C, per trade $."""
    if not len(D):
        return {"A": 0.0, "B": 0.0, "C": 0.0}
    s = D.s.values.astype(np.int64); ji = D.j_in.values.astype(np.int64); multi = (D.s_x.values != D.s.values)
    kind = (multi & (D.j_x.values == 0) & (D.s_x.values == D.s.values + 1)).astype(np.int64)
    jx = np.where(kind == 1, 0, np.where(multi, T.J15, D.j_x.values)).astype(np.int64)
    nd = int(I.full.sum()); o = {}
    same = ~multi | (kind == 1)
    for key, arr, use in (("A", bk["B"], False), ("B", bk["B"], True), ("C", bk["C"], True)):
        c = A.ctl_bucket(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, arr, s, np.maximum(ji, 1), jx, kind, I.pv, I.cs, use)
        c = np.where(same, c, np.nan)
        o[key] = float(np.nansum(np.where(np.isnan(c), np.nan, D.net.values - c)) / nd)
    if same.sum() == 0:
        o["B"] = o["C"] = np.nan
    if (~same).any():                      # multi-session holds: matched A over the same holding length
        import t95_liv as V
        Dm = D[~same].rename(columns={})
        cm = V.matched_multi(I, Dm)
        o["A"] += float(np.nansum(Dm.net.values - cm) / nd)
    return o


def gate(I, name, D, d, d4, dl, main, bk, sample=(200, 25), extra=None, plateau=None):
    full = I.full; s21 = np.asarray(I.sess >= K.S21); nd = int(full.sum())
    r = B.risk(d[full]); act = d[full & (d != 0)]; top = np.sort(act)[::-1]
    fd = {nm: float(d[np.asarray((I.sess >= a) & (I.sess <= b))].mean()) for nm, a, b in B.FOLDS}
    fn = {nm: int(((I.sess[D.s.values] >= a) & (I.sess[D.s.values] <= b)).sum()) for nm, a, b in B.FOLDS} if len(D) else {nm: 0 for nm, _, _ in B.FOLDS}
    c = controls(I, D, bk)
    rc, rm = B.risk((main + d)[full]), B.risk(main[full])
    am = full & (d != 0)
    corr = float(np.corrcoef(d[full], main[full])[0, 1]) if d[full].std() > 0 else 0.0
    o = {"module": name, "instrument": I.name, "trades": len(D), "avg_day": r["avg_day"], "avg_day_2021": float(d[s21].mean()),
         "usd_per_trade": float(D.net.mean()) if len(D) else np.nan, "max_dd": r["max_dd"], "worst_day": r["worst_day"],
         "matched_A_day": c["A"], "momentum_B_day": c["B"], "relvol_C_day": c["C"], **{f"fold_{k}": v for k, v in fd.items()},
         "folds_pos": int(sum(v > 0 for v in fd.values())), "min_fold_n": min(fn.values()),
         "remove_top3": float(act.sum() - top[:3].sum()) if len(act) else 0.0, "slip4_day": float(d4[full].mean()), "delay1_day": float(dl[full].mean()),
         "corr_to_main": corr, "loss_jaccard": float(((d < 0) & (main < 0) & am).sum() / max(((d < 0) | (main < 0))[am].sum(), 1)),
         "bottom5_overlap": float(((main <= np.percentile(main[full], 5)) & full & (d < 0)).sum() / max(((main <= np.percentile(main[full], 5)) & full).sum(), 1)),
         "tail_mean_on_main_bottom5": float(d[full & (main <= np.percentile(main[full], 5))].mean()),
         "main_avg_day": rm["avg_day"], "main_maxdd": rm["max_dd"], "main_worst": rm["worst_day"], "main_ret_dd": rm["ret_dd"],
         "main_plus_avg_day": rc["avg_day"], "main_plus_maxdd": rc["max_dd"], "main_plus_worst": rc["worst_day"], "main_plus_ret_dd": rc["ret_dd"], **(extra or {})}
    base = float(d[full].sum())
    pl = plateau if plateau is not None else []
    g = {"g_net": o["avg_day"] > 0, "g_A": c["A"] > 0, "g_B": (c["B"] > 0) if c["B"] == c["B"] else True, "g_folds": o["folds_pos"] >= 4, "g_top3": o["remove_top3"] > 0,
         "g_slip4": o["slip4_day"] > 0, "g_delay": o["delay1_day"] > 0,
         "g_plateau": True if plateau is None else bool(base > 0 and all(v > 0 and v >= 0.6 * base for v in pl)),
         "g_sample": o["trades"] >= sample[0] and o["min_fold_n"] >= sample[1]}
    o.update(g); o["plateau"] = str([round(v) for v in pl]); o["STANDALONE_PASS"] = bool(all(g.values()))
    o["PORTFOLIO_PASS"] = bool(o["STANDALONE_PASS"] and o["avg_day"] >= 10 and o["avg_day_2021"] >= 10 and rc["ret_dd"] >= rm["ret_dd"]
                               and rc["max_dd"] <= 1.10 * rm["max_dd"] and rc["worst_day"] >= -5000)
    o["DIVERSIFIER_PASS"] = bool(o["STANDALONE_PASS"] and abs(corr) <= 0.30 and rc["ret_dd"] >= 1.05 * rm["ret_dd"] and rc["max_dd"] <= 1.05 * rm["max_dd"]
                                 and rc["worst_day"] >= -5000 and o["avg_day"] >= 3)
    return o


def run_module(I, name, TR, bk, main, sample=(200, 25), extra=None, occ=None, plateau_TRs=None, lots=1):
    D = simulate(I, TR, occ=occ); d = daily(I, D, lots)
    d4 = daily(I, simulate(I, TR, cs=I.cs4, occ=occ), lots); dl = daily(I, simulate(I, TR, delay=1, occ=occ), lots)
    pl = None if plateau_TRs is None else [float(daily(I, simulate(I, t, occ=occ), lots)[I.full].sum()) for t in plateau_TRs]
    o = gate(I, name, D, d, d4, dl, main, bk, sample, extra, pl)
    return o, D, d


def md(name, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(os.path.join(REP, name), "w").write("\n".join(lines) + "\n")


def save(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=str)
