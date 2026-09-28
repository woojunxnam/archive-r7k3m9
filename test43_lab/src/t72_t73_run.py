"""TEST72 BOX MIGRATION (range mode, 9 UP x DOWN policies) and TEST73 TREND LADDER (rising boxes, exits A / C / D).
Both preregistrations are written before either is run."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import box_eval as V  # noqa: E402
import box_migr as M  # noqa: E402

BASE = {"obs": 30, "ub": 0.10, "db": 0.10, "up": 1, "dn": 2, "stable": 5, "LZ": 0.15, "UZ": 0.85, "buf": 0.0, "exit": 0, "dir": 9, "cycles": 1,
        "delay": 0, "miss": 0.0, "mig_delay": 0}
SPEC72 = {"question": "Does a stateful migrating box (never buying a broken floor without a newly valid box) create positive range-trading economics?",
          "machine": "initial box = first completed 30-min window (09:30-10:00, born 10:00); UP break = close > upper + 0.10 w; DOWN break = close < lower - 0.10 w; "
                     "UP1 ladder shift / UP2 fresh completed 30-min window / UP3 shift then fresh window; DOWN1 shift lower / DOWN2 fresh window / DOWN3 fresh "
                     "window + 5 completed bars before tradable",
          "trade": "RANGE: buy 1 contract at the next open after a close in the lower 15% of the box in force; exit TOP (>= 85% of the ENTRY box) / close below "
                   "the entry box lower / 16:15; one entry per box id",
          "policies": "9 = UP{1,2,3} x DOWN{1,2,3} per instrument", "selection": "best policy per instrument by full-sample net $/day",
          "plateau": {"obs": [15, 60], "ub=db": [0.0, 0.20], "LZ": [0.10, 0.25], "UZ": [0.75, 0.95], "buf": [0.10, 0.20]},
          "stress": "+1 bar entry delay, +1 bar migration delay, SLIP4, 20% missed entries", "gate": "program standalone gate", "budget": {"hypotheses": 18}}
SPEC73 = {"question": "Does a TREND LADDER (buy pullbacks into the lower zone of RISING boxes, hold through upward migrations) capture uptrend participation "
                      "with positive matched value?",
          "base": "machine UP1 + DOWN2 (obs 30, confirm 0.10 w); entries only in boxes with direction RISING (mid > previous box mid + 0.25 x previous width)",
          "exits": {"A": "sell at TOP of the entry box", "C": "hold; exit on a close below the entry box lower or 16:15",
                    "D (PRIMARY)": "trailing box: exit on a close below the CURRENT (upward-ratcheted) box lower - 0.10 w, else 16:15"},
          "plateau_D": {"policy": ["UP3+DOWN2", "UP1+DOWN3"], "obs": [15, 60], "ub=db": [0.0, 0.20], "LZ": [0.10, 0.25], "trail buf": [0.0, 0.20]},
          "report": ["RANGE_RECYCLE (TEST72 best, any direction) vs TREND_LADDER (D) avg/day", "RISING / FLAT / FALLING box edge (range mode, dir filter)"],
          "gate": "program standalone gate", "budget": {"hypotheses": 16}}

_MC = {}


def runner_for(I):
    rng = np.random.default_rng(5); U = rng.random((I.n, B.NG))

    def run(p):
        k = (p["obs"], p["ub"], p["db"], p["up"], p["dn"], p["stable"], p["mig_delay"])
        if (I.name, k) not in _MC:
            LO, HI, ID, DIR, TRD = M.machine(I.C, I.H, I.L, p["obs"], p["ub"], p["db"], p["up"], p["dn"], p["stable"], B.J15, p["mig_delay"])
            TRD = TRD * I.full[:, None]
            _MC[(I.name, k)] = (LO, HI, ID, DIR, TRD)
        LO, HI, ID, DIR, TRD = _MC[(I.name, k)]
        miss = (U < p["miss"]).astype(np.int64)
        return M.trade(I.C, I.FP, I.FPb, LO, HI, ID, DIR, TRD, p["LZ"], p["UZ"], p["buf"], p["exit"], p["dir"], p["cycles"], p["delay"], miss, B.J15)
    return run


def plateau(base, spec):
    out = []
    for k, vals in spec.items():
        for v in vals:
            if k == "ub=db":
                out.append((f"ub=db={v}", {**base, "ub": v, "db": v}))
            elif k == "policy":
                u, d = v.split("+"); out.append((v, {**base, "up": int(u[2]), "dn": int(d[4])}))
            elif k == "trail buf":
                out.append((f"buf={v}", {**base, "buf": v}))
            else:
                out.append((f"{k}={v}", {**base, k: v}))
    return out


def main():
    h72, h73 = B.prereg("TEST72", SPEC72), B.prereg("TEST73", SPEC73); print(h72, h73)
    Is = B.load(); r72, r73, dirs = [], [], []
    best = {}
    for inst, I in Is.items():
        run = runner_for(I); full = I.full
        tab = []
        for up in (1, 2, 3):
            for dn in (1, 2, 3):
                p = {**BASE, "up": up, "dn": dn}
                D, d = B.ledger_eval(I, run(p)); tab.append((up, dn, float(d[full].mean()), float(D.excess.sum() / full.sum()) if len(D) else 0.0, len(D)))
        T = pd.DataFrame(tab, columns=["up", "dn", "avg_day", "excess_day", "trades"]); T["instrument"] = inst
        T.to_csv(os.path.join(B.BOX, "TEST72", f"TEST72_POLICY_TABLE_{inst}.csv"), index=False); print(T.round(3).to_string())
        bp = T.sort_values("avg_day", ascending=False).iloc[0]
        p = {**BASE, "up": int(bp.up), "dn": int(bp.dn)}; best[inst] = p
        o, D, d = V.evaluate_fn(I, f"T72_RANGE_UP{int(bp.up)}_DOWN{int(bp.dn)}", run, p, plateau(p, SPEC72["plateau"]))
        o["policy_table"] = T[["up", "dn", "avg_day", "excess_day"]].round(2).values.tolist(); r72.append(o)
        # box direction edge (range mode)
        for dv, nm in ((1, "RISING"), (0, "FLAT"), (-1, "FALLING")):
            Dd, dd = B.ledger_eval(I, run({**p, "dir": dv}))
            dirs.append({"instrument": inst, "dir": nm, "trades": len(Dd), "avg_day": float(dd[full].mean()), "excess_day": float(Dd.excess.sum() / full.sum()) if len(Dd) else 0.0,
                         "usd_per_trade": float(Dd.net.mean()) if len(Dd) else np.nan, "x_per_trade": float(Dd.excess.mean()) if len(Dd) else np.nan})
        # TEST73 trend ladder
        base73 = {**BASE, "up": 1, "dn": 2, "dir": 1}
        for ex, lab in ((0, "A_TOP_EXIT"), (1, "C_HOLD"), (2, "D_TRAILING")):
            pp = {**base73, "exit": ex, "buf": 0.10 if ex == 2 else 0.0}
            o, D, d = V.evaluate_fn(I, f"T73_TREND_{lab}", run, pp, plateau(pp, SPEC73["plateau_D"]) if ex == 2 else ())
            r73.append(o)
        print(inst, "done", flush=True)
    R72, R73, DR = pd.DataFrame(r72), pd.DataFrame(r73), pd.DataFrame(dirs)
    R72.to_csv(os.path.join(B.BOX, "TEST72", "TEST72_RESULTS.csv"), index=False); R73.to_csv(os.path.join(B.BOX, "TEST73", "TEST73_RESULTS.csv"), index=False)
    DR.to_csv(os.path.join(B.BOX, "TEST73", "TEST73_BOX_DIRECTION_EDGE.csv"), index=False)
    cols = ["config", "instrument", "trades_per_day", "gross_day", "avg_day", "excess_day", "slip4_day", "max_dd", "worst_day", "folds_net_pos", "folds_x_pos",
            "p_top", "p_break", "avg_hold_min", "friction_over_gross", "delay1_day", "mig_delay1_day", "plateau", "plateau_pass", "PASS"]
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 120)
    print(R72[cols].round(3).to_string()); print(R73[cols].round(3).to_string()); print(DR.round(3).to_string())
    B.budget("TEST72", hypotheses=18, note="9 migration policies x 2 instruments (+ plateau)"); B.budget("TEST73", hypotheses=16, note="trend ladder exits A/C/D x 2 (+ plateau)")
    B.md("TEST72_BOX_MIGRATION.md", "TEST72 - box migration (range mode)", [str(SPEC72), R72[cols].round(3), R72.T])
    B.md("TEST73_TREND_LADDER.md", "TEST73 - trend box ladder", [str(SPEC73), R73[cols].round(3), "Box direction edge (range mode):", DR.round(3), R73.T])


if __name__ == "__main__":
    for t in ("TEST72", "TEST73", "TEST74", "TEST75", "TEST76", "TEST77"):
        os.makedirs(os.path.join(B.BOX, t), exist_ok=True)
    main()
