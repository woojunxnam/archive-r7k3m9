"""AUDIT 4: C2 winner press vs frontload — pure timing + capacity decomposition (prereg dacb1cb)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_mgmt as MG  # noqa: E402
import da_ph9 as P9  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
from rp_p6 import control_tables  # noqa: E402
from rp_p7 import CAP, MICRO  # noqa: E402
from rp_p9 import module_orders, stats  # noqa: E402

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, "out", "final_index_closure_audit_v1"); CAND = "C2_P2_FAILED_FIRST"


def allocate(orders, capped=True):
    c = EC.ctx(); n = len(c["sess"]); G = c["occ"]["MNQ"].shape[1]; mo = {"MNQ": c["occ"]["MNQ"], "MES": c["occ"]["ES"]}; co = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}
    orders = sorted(orders, key=lambda o: (o["date"], o["j_in"], o["parent"] is not None)); filled = set(); d = np.zeros(n); d4 = np.zeros(n); cnt = {"base_filled": 0, "base_skipped": 0, "second_filled": 0, "second_blocked": 0, "second_no_parent": 0}
    for o in orders:
        is2 = o["parent"] is not None
        if is2 and o["parent"] not in filled:
            cnt["second_no_parent"] += 1; continue
        si = c["pos"].get(o["date"], -1)
        if si < 0:
            continue
        L = o.get("lots", 1); mi = MICRO[o["inst"]]; ji, jo = o["j_in"], o["j_out"]; base = mo[mi][si, ji:jo + 1] if mi in mo else 0
        if capped and np.max(base + co[mi][si, ji:jo + 1]) + L > CAP[mi]:
            cnt["second_blocked" if is2 else "base_skipped"] += 1; continue
        co[mi][si, ji:jo + 1] += L; filled.add(o["key"]); cnt["second_filled" if is2 else "base_filled"] += 1
        d[si] += L * ((o["px_out"] - o["px_in"]) * o["pv"] - 2 * o["cs"]); d4[si] += L * ((o["px_out"] - o["px_in"]) * o["pv"] - 2 * o["cs4"])
    return d, d4, co, cnt


def main():
    c = EC.ctx(); w = c["win"]; yrs = c["sess"][w].year; M = P.markets(); Tctl = control_tables()
    base = module_orders(CAND, False, Tctl); a1, _ = P9.add_orders(); a1map = {o["parent"]: o for o in a1}
    front = [dict(o, key=o["key"] + "F", parent=o["key"]) for o in base]; b2 = [dict(o, lots=2) for o in base]
    # ---------- 4A pure timing ----------
    rows = []
    for o in base:
        u = (o["px_out"] - o["px_in"]) * o["pv"]; fl = u - 2 * o["cs"]; fl4 = u - 2 * o["cs4"]; a = a1map.get(o["key"])
        wp = ((a["px_out"] - a["px_in"]) * a["pv"] - 2 * a["cs"]) if a else 0.0; wp4 = ((a["px_out"] - a["px_in"]) * a["pv"] - 2 * a["cs4"]) if a else 0.0
        m = M[o["inst"]]; s = int(np.where(np.asarray(m.date[:, 0]) == o["date"])[0][0]); lo = np.nanmin(m.I.L[s, o["j_in"]:o["j_out"] + 1])
        mae_fl = 2 * (o["px_in"] - lo) * o["pv"]
        mae_wp = (o["px_in"] - lo) * o["pv"] + ((a["px_in"] - np.nanmin(m.I.L[s, a["j_in"]:a["j_out"] + 1])) * o["pv"] if a else 0.0)
        rows.append({"date": o["date"], "year": o["year"], "inst": o["inst"], "unit1": fl, "front": fl, "front4": fl4, "winner": wp, "winner4": wp4, "has_winner": a is not None,
                     "marg": wp - fl, "marg4": wp4 - fl4, "mae_front": mae_fl, "mae_winner": mae_wp})
    D = pd.DataFrame(rows); s4a = MG.summarize(D.marg, D.date, D.year, D.inst, D.marg4)
    dd = lambda v: EC.daily(D.date.values, v)[w]
    dF = dd((D.unit1 + D.front).values); dW = dd((D.unit1 + D.winner).values); rF, rW = EC.risk(dF), EC.risk(dW)
    T = float(dd(D.marg.values).mean()); T4 = float(dd(D.marg4.values).mean()); Tfold = {k: float(dd(D.marg.values)[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in EC.FOLDS.items()}
    a4 = {"per_trade": s4a, "T_day": T, "T_slip4_day": T4, "T_folds": Tfold, "T_folds_pos": int(sum(v > 0 for v in Tfold.values())), "n_base": len(D), "n_with_winner_checkpoint": int(D.has_winner.sum()),
          "front_add_ev": float(D.front.mean()), "winner_add_ev_all_opportunities": float(D.winner.mean()), "winner_add_ev_when_added": float(D.winner[D.has_winner].mean()),
          "module_front": {"avg_day": rF["avg_day"], "max_dd": rF["max_dd"], "worst_day": rF["worst_day"], "ret_dd": rF["ret_dd"], "worst_trade": float((D.unit1 + D.front).min()), "mae_p95": float(np.percentile(D.mae_front, 95))},
          "module_winner": {"avg_day": rW["avg_day"], "max_dd": rW["max_dd"], "worst_day": rW["worst_day"], "ret_dd": rW["ret_dd"], "worst_trade": float((D.unit1 + D.winner).min()), "mae_p95": float(np.percentile(D.mae_winner, 95))}}
    # ---------- 4B capacity ----------
    variants = {"A_C2x1": base, "B1_C2x2_FRONT_SEPARATE": base + front, "B2_C2x2_ALL_OR_NONE": b2, "C_C2_WINNER_ADD1": base + a1}; out = {}
    for nm, ords in variants.items():
        dcap, d4cap, co, cnt = allocate(ords, True); dunc, _, _, cntu = allocate(ords, False)
        st = stats(c["main"], dcap, d4cap, np.zeros_like(dcap), np.zeros_like(dcap), co, [], c["occ"])
        out[nm] = {"counts": cnt, "capped_cand_day": float(dcap[w].mean()), "uncapped_cand_day": float(dunc[w].mean()), "pnl_lost_to_capacity_day": float(dunc[w].mean() - dcap[w].mean()),
                   **{k: st[k] for k in ("avg_day", "incr", "slip4_avg_day", "max_dd", "worst_day", "ret_dd", "peak_MNQ", "peak_MES", "peak_MYM", "peak_M2K", "route_A", "route_B")}}
        print(nm, json.dumps(out[nm], default=float), flush=True)
    TOT = out["C_C2_WINNER_ADD1"]["capped_cand_day"] - out["B1_C2x2_FRONT_SEPARATE"]["capped_cand_day"]; TUNC = out["C_C2_WINNER_ADD1"]["uncapped_cand_day"] - out["B1_C2x2_FRONT_SEPARATE"]["uncapped_cand_day"]
    K = TOT - TUNC; dec = {"TOTAL_WINNER_MINUS_FRONTLOAD_capped_day": TOT, "PURE_TIMING_uncapped_day": TUNC, "CAPACITY_EFFECT_day": K, "check_T_4A": T,
                           "additive": "YES (definitionally; interaction absorbed in CAPACITY_EFFECT)", "ret_dd_C_minus_B1": out["C_C2_WINNER_ADD1"]["ret_dd"] - out["B1_C2x2_FRONT_SEPARATE"]["ret_dd"]}
    CmA = out["C_C2_WINNER_ADD1"]["capped_cand_day"] - out["A_C2x1"]["capped_cand_day"]
    if CmA <= 0:
        cls = "NO_VALUE"
    elif TOT <= 0 or out["C_C2_WINNER_ADD1"]["ret_dd"] <= out["B1_C2x2_FRONT_SEPARATE"]["ret_dd"]:
        cls = "SIMPLE_EXPOSURE_SCALING"
    elif TUNC > 0 and T4 > 0 and a4["T_folds_pos"] >= 3 and TUNC >= 0.75 * TOT:
        cls = "TRUE_MANAGEMENT_TIMING_VALUE"
    elif TUNC <= 0.25 * TOT:
        cls = "CAPACITY_TIMING_VALUE"
    else:
        cls = "MIXED_TIMING_AND_CAPACITY_VALUE"
    res = {"4A_PURE_TIMING": a4, "4B_CAPACITY": out, "DECOMPOSITION": dec, "C_minus_A_capped_day": CmA, "C2_WINNER_PRESS_TIMING_CLASS": cls}
    json.dump(res, open(os.path.join(OUT, "AUDIT4_WINNER_PRESS.json"), "w"), indent=1, default=float); print(json.dumps({k: res[k] for k in ("DECOMPOSITION", "C_minus_A_capped_day", "C2_WINNER_PRESS_TIMING_CLASS")}, indent=1, default=float))
    print(json.dumps(a4, indent=1, default=float))


if __name__ == "__main__":
    main()
