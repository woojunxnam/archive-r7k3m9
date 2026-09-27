"""TEST43-P Phase 19: ONE-TIME VAL confirmation of the frozen portfolio set (no retune), then Phase 20 selection by the
pre-registered rule.  Usage: python p05_val_confirm.py"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import lab, portfolio as PF, sleeves as S  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402

OUT = PF.PDIR
FZ = f"{OUT}/freeze/TEST43P_PRE_VAL_FREEZE.json"


def main():
    h = hashlib.sha256(open(FZ, "rb").read()).hexdigest()
    assert h == open(FZ.replace(".json", ".sha256")).read().split()[0], "pre-VAL freeze changed"
    fz = json.load(open(FZ))
    sig = pd.Series(fz["risk_normalisation"]["sigma_daily_dev"])
    D = PD.load_daily()                      # standalone sleeve daily P&L (DEV+VAL) for the causal expanding tilt
    bk = PF.Book(lab.VAL_END, S.ELIGIBLE)
    rows, daily = [], {}
    defs = [(n, b, None) for n, b in fz["portfolios"].items()]
    base = fz["portfolios"]["P2_STATIC_DIVERSIFIED"]
    for a in fz["regime_tilt"]["alphas"]:
        defs.append((f"P3_REGIME_ADAPTIVE_{int(a * 100)}", base, a))
    tilts = {a: PD.regime_tilt(bk, list(base), base, a, D)[0] for a in fz["regime_tilt"]["alphas"]}
    for name, bud, a in defs:
        for env in PD.ENV:
            L = fz["risk_scale_L"].get(f"{name}|{env}")
            if L is None:
                continue
            o, d, r = PD.run_port(bk, bud, sig, L, env, tilt=tilts.get(a), end=lab.VAL_END,
                                  pers=("VAL", "DEV", "Y2020", "Y2022"))
            o["VAL_env"] = PD.env_of(o, "VAL"); o["DEV_env"] = PD.env_of(o, "DEV")
            dd_, w_ = lab.ENVELOPES[env]
            o["VAL_PASS"] = bool(o["VAL_avg"] > 0 and o["VAL_max_dd"] <= dd_ and o["VAL_worst"] >= w_ and not o["margin_breach"])
            for lab_, ex in (("SLIP4", {"slip_ticks": 4}), ("TIMING_BRITTLENESS_STRESS", {"delay": 1})):
                o2, _, _ = PD.run_port(bk, bud, sig, L, env, extra=ex, tilt=tilts.get(a), end=lab.VAL_END, pers=("VAL",))
                o[f"{lab_}_VAL_avg"] = o2["VAL_avg"]; o[f"{lab_}_VAL_max_dd"] = o2["VAL_max_dd"]
            rows.append({"portfolio": name, "risk_env": env, "n_sleeves": len(bud), "members": "+".join(bud), **o})
            daily[(name, env)] = d
            print(name, env, "VAL avg", round(o["VAL_avg"], 1), "dd", round(o["VAL_max_dd"]), "pass", o["VAL_PASS"], flush=True)
    V = pd.DataFrame(rows)
    V.to_csv(f"{OUT}/p18_val_confirmation.csv", index=False)
    for (n, e), d in daily.items():
        d.to_csv(f"{OUT}/daily_{n}_{e}_DV.csv")
    # ---------------- Phase 20: pre-registered selection
    ok = V[V.VAL_PASS]
    mod = ok[ok.risk_env == "MODERATE"].copy()
    p2m = V[(V.portfolio == "P2_STATIC_DIVERSIFIED") & (V.risk_env == "MODERATE")].iloc[0]
    def p3_ok(r):
        if not r.portfolio.startswith("P3"):
            return True
        return r.VAL_avg > p2m.VAL_avg and r.VAL_ret_dd > p2m.VAL_ret_dd
    mod = mod[mod.apply(p3_ok, axis=1)]
    mod = mod.sort_values(["DEV_ret_dd", "n_sleeves"], ascending=[False, True])
    primary = mod.iloc[0] if len(mod) else None
    s1 = V[(V.portfolio == "P2_STATIC_DIVERSIFIED") & (V.risk_env == "MODERATE") & V.VAL_PASS]
    if not len(s1):
        s1 = V[(V.portfolio == "P2B_STATIC_4SLEEVE") & (V.risk_env == "MODERATE") & V.VAL_PASS]
    cons = ok[ok.risk_env == "CONSERVATIVE"].sort_values("DEV_max_dd")
    sel = {"PRIMARY": None if primary is None else f"{primary.portfolio}|{primary.risk_env}",
           "SECONDARY_1": f"{s1.iloc[0].portfolio}|MODERATE" if len(s1) else None,
           "SECONDARY_2": f"{cons.iloc[0].portfolio}|CONSERVATIVE" if len(cons) else None}
    if sel["SECONDARY_1"] == sel["PRIMARY"]:   # distinct secondary: next static MODERATE passing VAL
        alt = mod[(~mod.portfolio.str.startswith("P3")) & (mod.portfolio + "|" + mod.risk_env != sel["PRIMARY"])]
        sel["SECONDARY_1"] = f"{alt.iloc[0].portfolio}|MODERATE" if len(alt) else None
    json.dump(sel, open(f"{OUT}/p20_selection.json", "w"), indent=1)
    pd.set_option("display.width", 260)
    print(V[["portfolio", "risk_env", "DEV_avg", "DEV_max_dd", "DEV_ret_dd", "VAL_avg", "VAL_max_dd", "VAL_worst", "VAL_excess_vs_mb",
             "VAL_ret_dd", "SLIP4_VAL_avg", "TIMING_BRITTLENESS_STRESS_VAL_avg", "VAL_env", "VAL_PASS"]].round(3).to_string(index=False))
    print(sel)


if __name__ == "__main__":
    main()
