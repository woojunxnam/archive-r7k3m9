"""V6 controlled-overfit search on the V6A allocator.  DEV-only objective; holdout never loaded.

Usage: python optimize_v6.py INST ARCH ENV N_TRIALS SEED OUT.csv
ARCH: A (exposure/risk, tactical OFF), C (A + low-turnover dip/reduction), E (vol-target sizing),
      F (vol-target + regime + DD governor), D (everything combined).
Score (feasible): 0.5*DEV avg_daily + 0.5*DEV avg_ex_top5.  Infeasible trials are penalised.
"""
import json
import os
import sys
import time

import numpy as np
import optuna
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import lab, v6lab  # noqa: E402

ENV = {"CONSERVATIVE": (10000, 2000), "MODERATE": (15000, 3000), "AGGRESSIVE": (20000, 5000), "EXPLORATORY": (1e12, 1e12)}
CAPMAX = {"ES": 24, "MNQ": 16}


def space(t, inst, arch):
    cm = CAPMAX[inst]
    p = {}
    use_tier = arch in ("A", "C", "F", "D")
    use_vol = arch in ("E", "F", "D")
    use_dd = arch in ("A", "C", "F", "D")
    use_tac = arch in ("C", "D")
    p["marginU"] = t.suggest_categorical("marginU", [0.35, 0.5, 0.65, 0.8])
    if use_vol:
        p["capRTH"] = t.suggest_int("capRTH", 1, cm * 2)
        p["capON"] = t.suggest_int("capON", 0, cm * 2)
        p["volBudget"] = t.suggest_float("volBudget", 300, 12000, log=True)
        if t.suggest_categorical("useVolON", [0, 1]):
            p["volBudgetON"] = t.suggest_float("volBudgetON", 300, 12000, log=True)
    else:
        p["capRTH"] = t.suggest_int("capRTH", 1, cm)
        p["capON"] = t.suggest_int("capON", 0, cm)
    if use_tier:
        p["fBear"] = t.suggest_float("fBear", 0, 1)
        p["fNeut"] = t.suggest_float("fNeut", 0, 1)
        p["fMed"] = t.suggest_float("fMed", 0, 1)
        p["fStrong"] = t.suggest_float("fStrong", 0, 1)
        p["trendMult"] = t.suggest_float("trendMult", 0, 1)
    p["onMode"] = t.suggest_int("onMode", 0, 5)
    p["onFrac"] = t.suggest_float("onFrac", 0, 1)
    p["onMinTier"] = t.suggest_int("onMinTier", 1, 3)
    if use_dd and t.suggest_categorical("useDD", [0, 1]):
        d1 = t.suggest_float("dd1", 1000, 15000, log=True)
        p["dd1"] = d1; p["dd2"] = d1 * t.suggest_float("dd2x", 1.2, 3.0)
        p["ddM1"] = t.suggest_float("ddM1", 0, 1); p["ddM2"] = t.suggest_float("ddM2", 0, 1) * p["ddM1"]
        p["ddRearmTier"] = t.suggest_int("ddRearmTier", 1, 3); p["ddCooldown"] = t.suggest_int("ddCooldown", 1, 15)
    if arch in ("A", "C", "F", "D"):
        if t.suggest_categorical("useDayStop", [0, 1]):
            p["dayStop"] = t.suggest_float("dayStop", 300, 8000, log=True)
        if t.suggest_categorical("useGap", [0, 1]):
            p["gapK"] = t.suggest_float("gapK", 0.3, 3.0)
        if t.suggest_categorical("useShock", [0, 1]):
            p["shockK"] = t.suggest_float("shockK", 0.15, 1.5)
        p["riskFloorFrac"] = t.suggest_float("riskFloorFrac", 0, 1)
    if use_tac:
        if t.suggest_categorical("dipOn", [0, 1]):
            p.update(dipOn=1, dipZ=t.suggest_float("dipZ", 0.5, 3.0), dipPos5d=t.suggest_float("dipPos5d", 0.0, 0.5),
                     dipBoost=t.suggest_float("dipBoost", 0.05, 1.0), dipNeedRev=t.suggest_categorical("dipNeedRev", [0, 1]),
                     dipExitZ=t.suggest_float("dipExitZ", -1.0, 1.5), dipMaxBars=t.suggest_int("dipMaxBars", 5, 130))
        if t.suggest_categorical("redOn", [0, 1]):
            p.update(redOn=1, redZ=t.suggest_float("redZ", 0.5, 3.5), redPosRth=t.suggest_float("redPosRth", 0.5, 1.0),
                     redCut=t.suggest_float("redCut", 0.05, 1.0), redExitZ=t.suggest_float("redExitZ", -0.5, 2.0))
    p["minDelta"] = t.suggest_int("minDelta", 1, 4)
    p["cooldownBars"] = t.suggest_int("cooldownBars", 0, 40)
    p["buyStartMod"] = t.suggest_categorical("buyStartMod", [570, 585, 600, 630, 660])
    p["buyEndMod"] = t.suggest_categorical("buyEndMod", [720, 840, 900, 930, 954])
    return p


ROBUST = os.environ.get("T43_ROBUST", "0") == "1"


def score_row(o, env):
    L, W = ENV[env]
    avg = o.get("DEV_avg_daily") or -1e3
    ex5 = o.get("DEV_avg_ex_top5") or -1e3
    if ROBUST:
        folds = [o.get(f"F{k}_avg_daily") or -1e3 for k in (1, 2, 3)]
        avg = 0.4 * float(np.mean(folds)) + 0.6 * float(np.min(folds))
        ex5 = avg
    dd = o.get("DEV_max_dd") or 1e9
    wd = -(o.get("DEV_worst_day") or -1e9)
    pen = 0.0
    if dd > L:
        pen += 200 + 400 * (dd / L - 1)
    if wd > W:
        pen += 200 + 400 * (wd / W - 1)
    if o["margin_breach"] or o["min_equity"] <= 0:
        pen += 2000
    return 0.5 * avg + 0.5 * ex5 - pen, pen == 0


def main(inst, arch, env, n, seed, out):
    v6lab.load(inst, lab.DEV_END)
    rows = []
    best_hist = []

    def obj(t):
        p = space(t, inst, arch)
        o = v6lab.evaluate(inst, dict(p), end=lab.DEV_END, periods=("DEV", "F1", "F2", "F3") if ROBUST else ("DEV",))
        sc, feas = score_row(o, env)
        rows.append({"trial": t.number, "inst": inst, "arch": arch, "env": env, "score": sc, "feasible": feas,
                     **{k: o[k] for k in o if k.startswith(("DEV_", "F1_avg", "F2_avg", "F3_avg"))}, "peak_margin_util": o["peak_margin_util"],
                     "min_equity": o["min_equity"], "fills": o["fills"], "friction": o["friction"],
                     "params": json.dumps(p)})
        if t.number % 100 == 99:
            pd.DataFrame(rows).to_csv(out, index=False)
        return sc

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    st = optuna.create_study(direction="maximize",
                             sampler=optuna.samplers.TPESampler(seed=seed, multivariate=True, group=True,
                                                                n_startup_trials=min(300, n // 5)))
    t0 = time.time()
    st.optimize(obj, n_trials=n)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    fb = df[df.feasible].sort_values("trial").score.cummax()
    sat = None
    if len(fb) > 1000:
        last = fb.iloc[-1]; before = df[df.feasible & (df.trial <= df.trial.max() - 1000)].score.max()
        sat = bool(before > 0 and (last - before) / abs(before) < 0.01)
    print(inst, arch, env, "trials", len(df), "feasible", int(df.feasible.sum()), "best", round(df.score.max(), 2),
          "saturated", sat, "sec", round(time.time() - t0))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
