"""Stage B/C controlled-overfit search: Optuna TPE per risk envelope on DEV only (holdout excluded)."""
import sys, os, json, time
import numpy as np, pandas as pd, optuna
sys.path.insert(0, os.path.dirname(__file__))
from t43 import lab, v6x, grid

ENV = {"CONSERVATIVE": (10000, 2000), "MODERATE": (15000, 3000), "AGGRESSIVE": (20000, 5000), "EXPLORATORY": (1e12, 1e12)}

def space(t):
    M = t.suggest_int("intradayMaxQty", 2, 40, step=2)
    cfrac = t.suggest_float("coreFrac", 0.0, 1.0)
    K = int(round(cfrac * M))
    p = dict(intradayMaxQty=M, coreQty=K)
    p["coreBuildMode"] = t.suggest_categorical("coreBuildMode", [1, 2]) if K > 0 else 0
    p["coreStep"] = t.suggest_categorical("coreStep", [1, 2, 4, 40])
    tier = t.suggest_categorical("coreTierMode", [0, 1])
    if tier and K > 0:
        tb = t.suggest_float("tierBase", 0, 1); tm = t.suggest_float("tierMid", 0, 1)
        kb = int(round(tb * K)); km = int(round(tm * (K - kb))); kt = K - kb - km
        p.update(coreTierMode=1, kBase=kb, kMid=km, kTop=kt)
    p["tacticalMode"] = t.suggest_categorical("tacticalMode", [0, 1])
    on = t.suggest_categorical("overnightMode", [0, 1, 2, 3]); p["overnightMode"] = on
    if on == 0:
        p["overnightMaxQty"] = t.suggest_int("overnightMaxQty", 0, M)
    p["regimeLen"] = t.suggest_categorical("regimeLen", [10, 20, 50])
    if t.suggest_categorical("useRegimeCap", [0, 1]):
        p["regimeMaxQty"] = max(1, int(round(t.suggest_float("regimeCapFrac", 0.0, 1.0) * M)))
    if t.suggest_categorical("useDD", [0, 1]):
        p["ddLimit"] = t.suggest_float("ddLimit", 1000, 20000, log=True)
        p["ddFloorQty"] = int(round(t.suggest_float("ddFloorFrac", 0, 1) * K))
        p["ddRearmLen"] = t.suggest_categorical("ddRearmLen", [5, 10, 20, 40])
    if t.suggest_categorical("useDayStop", [0, 1]):
        p["dayStop"] = t.suggest_float("dayStop", 300, 8000, log=True)
    if t.suggest_categorical("useEmergency", [0, 1]):
        p["emergencyLoss"] = t.suggest_float("emergencyLoss", 500, 20000, log=True)
        p["emergencyToCore"] = t.suggest_categorical("emergencyToCore", [0, 1])
    if p["tacticalMode"]:
        p["rfThreshold"] = t.suggest_categorical("rfThreshold", [0.0, 0.382, 0.5, 0.618])
        p["rfLookback"] = t.suggest_categorical("rfLookback", [10, 20, 40])
        p["decayMode"] = t.suggest_categorical("decayMode", [0, 2, 3])
        p["targetDecayBars"] = t.suggest_int("targetDecayBars", 5, 80)
        p["profitRefMode"] = t.suggest_int("profitRefMode", 0, 3)
        p["recycleMinTicks"] = t.suggest_int("recycleMinTicks", 4, 60)
        p["recycleTPATR"] = t.suggest_float("recycleTPATR", 0.04, 1.0, log=True)
        p["fastSellRSI"] = t.suggest_float("fastSellRSI", 50, 100)
        p["profitZ"] = t.suggest_categorical("profitZ", [0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
        p["profitZMinTicks"] = t.suggest_int("profitZMinTicks", 2, 24)
        p["reductionLock"] = t.suggest_categorical("reductionLock", [0, 1])
        p["rearmATR"] = t.suggest_float("rearmATR", 0.2, 3.0)
        p["useRepairLocationGate"] = t.suggest_categorical("useRepairLocationGate", [0, 1])
        p["repairMinVWAPZ"] = t.suggest_float("repairMinVWAPZ", -3.0, 1.0)
        p["repairMin60Pos"] = t.suggest_float("repairMin60Pos", 0.0, 0.9)
        p["repairMinSessionPos"] = t.suggest_float("repairMinSessionPos", 0.0, 0.9)
        p["repairMin5DPos"] = t.suggest_float("repairMin5DPos", 0.0, 0.9)
        p["overlayRepairSellTicks"] = t.suggest_int("overlayRepairSellTicks", 4, 60)
        p["baseRepairSellTicks"] = t.suggest_int("baseRepairSellTicks", 6, 80)
        p["lowerRebuyTicks"] = t.suggest_int("lowerRebuyTicks", 4, 60)
        p["repairLifeBars"] = t.suggest_int("repairLifeBars", 3, 100)
        p["failedRepairRestoreTicks"] = t.suggest_int("failedRepairRestoreTicks", 2, 60)
        p["easyAddRSI"] = t.suggest_float("easyAddRSI", 5, 70)
        p["bottomRangePct"] = t.suggest_float("bottomRangePct", 0.1, 0.7)
        p["driftVWAPDeepSigma"] = t.suggest_float("driftVWAPDeepSigma", 0.5, 3.0)
        p["driftRangeLowPct"] = t.suggest_float("driftRangeLowPct", 0.1, 0.45)
        p["driftMinLocationScore"] = t.suggest_int("driftMinLocationScore", 1, 4)
        p["oppositeSideCooldownBars"] = t.suggest_int("oppositeSideCooldownBars", 0, 20)
        p["minimumOppositeMoveATR"] = t.suggest_float("minimumOppositeMoveATR", 0.02, 1.0, log=True)
        p["antiStallBars"] = t.suggest_int("antiStallBars", 5, 60)
        p["buyStartMod"] = t.suggest_categorical("buyStartMod", [570, 585, 600, 630, 660])
        p["buyEndMod"] = t.suggest_categorical("buyEndMod", [720, 780, 840, 900, 930, 954])
    return p

def main(env, n_trials, seed, out):
    L, W = ENV[env]
    grid._init(lab.DEV_END)   # DEV only
    rows = []
    def obj(t):
        p = space(t)
        pp = dict(grid.RESEARCH_DEFAULTS); pp.update(p)
        o, res, d = lab.evaluate(grid._B, grid._A, v6x.make_params(**pp), periods=("DEV",))
        avg = o.get("DEV_avg_daily", -1e3); dd = o.get("DEV_max_dd", 1e9); wd = -o.get("DEV_worst_day", -1e9)
        breach = o["margin_breach"] or o["min_equity"] <= 0
        pen = 0.0
        if dd > L: pen += 200 + 400 * (dd / L - 1)
        if wd > W: pen += 200 + 400 * (wd / W - 1)
        if breach: pen += 2000
        score = avg - pen
        r = {"trial": t.number, "env": env, "score": score, **{k: o.get(k) for k in o if k.startswith("DEV_")},
             "margin_util": o["margin_util"], "margin_breach": breach, "fills": o["fills"], "params": json.dumps(p)}
        rows.append(r)
        if t.number % 100 == 0:
            pd.DataFrame(rows).to_csv(out, index=False)
        return score
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed, multivariate=True, n_startup_trials=200))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    st.optimize(obj, n_trials=n_trials)
    pd.DataFrame(rows).to_csv(out, index=False)

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
