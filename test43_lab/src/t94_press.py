"""TEST94 PRESS-WINNER LANE (Livermore / Hougaard principle, systematic).  No momentum base qualified at TEST85, so per the program preregistration
this runs as a NON-PROMOTABLE DIAGNOSTIC on M1_OPEN_IMPULSE (10:00, return since open >= 0.30 ATR_d) to measure MARGINAL ADD EV.
Campaign: 1-unit probe; adds only while the campaign is in profit, close > session VWAP, a NEW trigger fires, spacing / speed satisfied; exits R0 / R1.
Per-unit ledger; FRONTLOAD and CONSTANT controls; convexity / give-back / loser-exposure diagnostics; SLIP4."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
from t84_run import features  # noqa: E402

OUT = os.path.join(A.AP, "TEST94_PRESS_WINNER"); os.makedirs(OUT, exist_ok=True)
LADDERS = {"L1": [1, 2, 3], "L2": [1, 2, 3, 4], "L3": [1, 2, 4, 6], "L4": [1, 2, 3, 4, 6]}
TRIG = {"A_NEW_HIGH": 0, "B_SECOND_IMPULSE": 1, "C_SHALLOW_PULLBACK": 2, "D_VALUE_ACCEPT": 3, "E_CROSS_INDEX": 4}
SPEED = {"FAST": 0, "MEDIUM": 5, "SLOW": 15}; SPACING = [0.0, 0.10, 0.25]; EXITS = {"R0": 0, "R1": 1}


@njit(cache=True)
def campaign(C, FP, FPb, VW, POCUP, OTHERHI, s, j0, atr, ladder, trig, speed, spacing, exit_mode, pv, cs, J15_, frontload):
    """one campaign; returns unit ledger rows (level, entry px, exit px, units) and path stats (max units, peak open pnl, final pnl, violations)."""
    L = ladder.shape[0]; units = np.zeros(8); epx = np.zeros(8); lvl_units = np.zeros(8); nl = 0
    first = ladder[L - 1] if frontload > 0 else 1
    if frontload > 0:
        first = frontload
    px0 = FP[s, j0]; units[0] = first; epx[0] = px0; lvl_units[0] = first; nl = 1; cur = first; li = 0
    if frontload > 0:
        li = L - 1
    last_add_j = j0; last_add_px = px0; camp_hi = C[s, j0]; hi_j = j0; pb_low = 1e18; viol = 0
    peak = 0.0; maxu = cur; exit_px = np.zeros(8); reduced = False
    xj = J15_
    for k in range(j0, J15_):
        c = C[s, k]
        # mark
        op = 0.0
        for u in range(nl):
            op += (c - epx[u]) * pv * units[u]
        if op > peak:
            peak = op
        # exits
        if c < VW[s, k]:
            if exit_mode == 0 or (exit_mode == 1 and c < px0):
                xj = k + 1; break
            if exit_mode == 1 and not reduced and cur > 1:
                # reduce to 1 unit: close the latest units first (keep the probe)
                need = cur - 1; u = nl - 1
                while need > 0 and u >= 0:
                    q = min(units[u], need)
                    if q > 0:
                        exit_px[u] += q * FPb[s, min(k + 1, J15_)]; units[u] -= q; need -= q
                    u -= 1
                cur = 1; reduced = True
        newhi = c > camp_hi
        if newhi:
            gap = k - hi_j; camp_hi = c; hi_j = k
        else:
            gap = 0
            if camp_hi - c >= 0.10 * atr and c < pb_low:
                pb_low = c
        if frontload > 0 or reduced or li >= L - 1 or k + 1 >= J15_:
            continue
        fire = False
        if trig == 0:
            fire = newhi
        elif trig == 1:
            fire = newhi and gap >= 10
        elif trig == 2:
            fire = pb_low < 1e17 and pb_low > last_add_px and c >= pb_low + 0.5 * (camp_hi - pb_low)
        elif trig == 3:
            fire = newhi and POCUP[s, k] == 1
        else:
            fire = newhi and OTHERHI[s, k] == 1
        if not fire:
            continue
        if not (op > 0 and c > VW[s, k] and k - last_add_j >= speed and c - last_add_px >= spacing * atr):
            continue
        add = ladder[li + 1] - ladder[li]
        if op <= 0:
            viol += 1
        units[nl] = add; epx[nl] = FP[s, k + 1]; lvl_units[nl] = add; nl += 1; li += 1; cur += add
        last_add_j = k; last_add_px = c; pb_low = 1e18
        if cur > maxu:
            maxu = cur
    xp = FPb[s, min(xj, J15_)]
    out = np.zeros((nl, 4)); fin = 0.0
    for u in range(nl):
        rem = units[u]; val = exit_px[u] + rem * xp
        out[u, 0] = u; out[u, 1] = epx[u]; out[u, 2] = lvl_units[u]
        out[u, 3] = (val - lvl_units[u] * epx[u]) * pv - 2 * cs * lvl_units[u]
        fin += out[u, 3]
    return out, maxu, peak, fin, viol, xj


def run(I, ev, POCUP, OTHERHI, ladder, trig, speed, spacing, ex, cs, frontload=0):
    units, rows = [], []
    for s, j in ev:
        out, maxu, peak, fin, viol, xj = campaign(I.C, I.FP, I.FPb, I.vwap, POCUP, OTHERHI, s, j + 1, I.atr[s], np.array(ladder, np.int64), trig, speed, spacing, ex,
                                                  I.pv, cs, A.J15, frontload)
        rows.append({"s": s, "final": fin, "maxu": maxu, "peak": peak, "viol": viol, "exit_j": xj, "adds": out.shape[0] - 1})
        for r in out:
            units.append({"s": s, "level": int(r[0]), "units": r[2], "pnl": r[3]})
    return pd.DataFrame(rows), pd.DataFrame(units)


def stats(I, Cm, U):
    full = I.full; d = np.zeros(I.n); np.add.at(d, Cm.s.values, Cm.final.values); r = B.risk(d[full])
    act = d[full & (d != 0)]; top = np.sort(act)[::-1]
    w = Cm.final > 0; big = Cm.final >= Cm.final.quantile(0.9)
    fin = Cm.final.values; srt = np.sort(fin)[::-1]; tot = fin.sum()
    lv = {f"ADD{k}_MARGINAL_EV": float(U[U.level == k].pnl.mean()) if (U.level == k).any() else np.nan for k in range(1, 5)}
    return {"campaigns": len(Cm), "avg_day": r["avg_day"], "max_dd": r["max_dd"], "worst_day": r["worst_day"], "remove_top3_day": float(act.sum() - top[:3].sum()),
            "PROBE_EV": float(U[U.level == 0].pnl.mean()), **lv, "win_rate": float(w.mean()), "avg_winner": float(Cm.final[w].mean()) if w.any() else np.nan,
            "avg_loser": float(Cm.final[~w].mean()) if (~w).any() else np.nan, "payoff": float(Cm.final[w].mean() / -Cm.final[~w].mean()) if w.any() and (~w).any() else np.nan,
            "expectancy": float(fin.mean()), "profit_factor": float(fin[fin > 0].sum() / -fin[fin < 0].sum()) if (fin < 0).any() else np.nan, "skew": float(pd.Series(fin).skew()),
            "loser_avg_max_units": float(Cm.maxu[~w].mean()) if (~w).any() else np.nan, "winner_avg_max_units": float(Cm.maxu[w].mean()) if w.any() else np.nan,
            "big_winner_avg_max_units": float(Cm.maxu[big].mean()), "violations": int(Cm.viol.sum()),
            "giveback_fraction": float(((Cm.peak - Cm.final).clip(lower=0).sum()) / max(Cm.peak.clip(lower=0).sum(), 1e-9)),
            "top10pct_share": float(srt[:max(1, len(srt) // 10)].sum() / tot) if tot > 0 else np.nan, "avg_units_time": float(U.units.sum() / len(Cm)),
            "folds_pos": int(sum(d[np.asarray((I.sess >= a) & (I.sess <= b))].mean() > 0 for nm, a, b in B.FOLDS))}


def main():
    spec = {"status": "NON-PROMOTABLE DIAGNOSTIC (no qualifying momentum base at TEST85; base = M1_OPEN_IMPULSE as preregistered)",
            "grid": {"triggers": list(TRIG), "ladders": LADDERS, "speed": SPEED, "spacing_ATR": SPACING, "exits": list(EXITS)}, "controls": ["FRONTLOAD", "CONSTANT_1", "CONSTANT_2"],
            "note": "overnight carry not studied (RTH press must pass first)", "budget": {"hypotheses": 5 * 4 * 3 * 3 * 2}}
    print(A.prereg("TEST94_PRESS_WINNER", spec))
    Is = B.load(); rows = []
    for inst, I in Is.items():
        other = Is["ES" if inst == "MNQ" else "MNQ"]
        ro = (I.C[:, 29] - I.FP[:, 0]) / I.atr
        ev = [(s, 29) for s in np.where(I.full & (ro >= 0.30))[0]]
        P1, F = features(I, "VP-B"); P2 = F[..., A.FEAT["P2_POC"]]
        up = (P2 - np.concatenate([np.full((I.n, 6), np.nan), P2[:, :-6]], 1)) >= 0.05 * I.atr[:, None]
        POCUP = np.zeros((I.n, A.NG), np.int64)
        for k in range(A.NG):
            b = (k - 4) // 5
            if b >= 0:
                POCUP[:, k] = up[:, min(b, A.NB5 - 1)]
        OTHERHI = (other.C >= np.maximum.accumulate(other.H, 1) - 1e-9).astype(np.int64)
        base_ctl = {}
        for ex, exv in EXITS.items():
            for cn, u in (("CONSTANT_1", 1), ("CONSTANT_2", 2)):
                Cm, U = run(I, ev, POCUP, OTHERHI, [u], 0, 0, 0.0, exv, I.cs, frontload=u)
                base_ctl[(ex, cn)] = stats(I, Cm, U)
        for tn, tv in TRIG.items():
            for ln, lad in LADDERS.items():
                for sn, sv in SPEED.items():
                    for sp in SPACING:
                        for ex, exv in EXITS.items():
                            Cm, U = run(I, ev, POCUP, OTHERHI, lad, tv, sv, sp, exv, I.cs)
                            st = stats(I, Cm, U)
                            d4 = np.zeros(I.n); np.add.at(d4, Cm.s.values, Cm.final.values - 2 * (I.cs4 - I.cs) * U.groupby("s").units.sum().reindex(Cm.s.values).values)
                            fl = int(round(st["avg_units_time"]))
                            Cf, Uf = run(I, ev, POCUP, OTHERHI, [max(fl, 1)], 0, 0, 0.0, exv, I.cs, frontload=max(fl, 1)); sf = stats(I, Cf, Uf)
                            rows.append({"instrument": inst, "trigger": tn, "ladder": ln, "speed": sn, "spacing": sp, "exit": ex, **st,
                                         "slip4_avg_day": float(d4[I.full].mean()), "frontload_units": max(fl, 1), "frontload_avg_day": sf["avg_day"],
                                         "pyramid_vs_frontload_day": st["avg_day"] - sf["avg_day"], "pyramid_vs_constant1_day": st["avg_day"] - base_ctl[(ex, "CONSTANT_1")]["avg_day"],
                                         "pyramid_vs_constant2_day": st["avg_day"] - base_ctl[(ex, "CONSTANT_2")]["avg_day"],
                                         "ret_dd": st["avg_day"] / st["max_dd"] if st["max_dd"] > 0 else np.nan, "frontload_ret_dd": sf["avg_day"] / sf["max_dd"] if sf["max_dd"] > 0 else np.nan})
        print(inst, len(ev), "campaigns", {k: round(v["avg_day"], 2) for k, v in base_ctl.items()}, flush=True)
        pd.DataFrame([{"instrument": inst, "exit": k[0], "control": k[1], **v} for k, v in base_ctl.items()]).to_csv(os.path.join(OUT, f"T94_CONTROLS_{inst}.csv"), index=False)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "T94_PRESS_GRID.csv"), index=False)
    pd.set_option("display.width", 260)
    agg = R.groupby(["instrument", "trigger"])[["ADD1_MARGINAL_EV", "ADD2_MARGINAL_EV", "ADD3_MARGINAL_EV", "pyramid_vs_frontload_day", "pyramid_vs_constant1_day", "avg_day"]].median()
    print(agg.round(2).to_string())
    cols = ["instrument", "trigger", "ladder", "speed", "spacing", "exit", "avg_day", "slip4_avg_day", "max_dd", "worst_day", "PROBE_EV", "ADD1_MARGINAL_EV", "ADD2_MARGINAL_EV",
            "ADD3_MARGINAL_EV", "win_rate", "payoff", "loser_avg_max_units", "winner_avg_max_units", "big_winner_avg_max_units", "violations", "giveback_fraction",
            "pyramid_vs_frontload_day", "pyramid_vs_constant1_day", "folds_pos", "remove_top3_day"]
    print(R.sort_values("avg_day", ascending=False).groupby("instrument").head(5)[cols].round(2).to_string())
    A.budget("TEST94_PRESS_WINNER", hypotheses=len(R), note="press-winner diagnostic grid (non-promotable)")
    A.md("TEST94_PRESS_WINNER.md", "TEST94 - press-winner lane (diagnostic)", [str(spec), agg.round(2), R[cols].round(2)])


if __name__ == "__main__":
    main()
