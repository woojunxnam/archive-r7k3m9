"""Architecture B: existing V5.3.3/V6X tactical engine (tacticalMode=1) with a frozen exposure frame.

Frozen exposure frame per instrument (from the passive-control study): tiered core via coreTierMode,
DD governor, roll cost, instrument point value.  Only tactical parameters are searched.
Usage: python optimize_v6_B.py INST ENV N SEED OUT
"""
import json
import os
import sys

import numpy as np
import optuna
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, instruments, lab, v6x  # noqa: E402
from optimize_v6 import ENV  # noqa: E402

BARS = {"ES": "../out/p123/ES_3m_bars.parquet", "MNQ": "../out/mnq/MNQ_3m_bars.parquet"}
PROF = {"ES": "MES", "MNQ": "MNQ"}


def main(inst, env, n, seed, out):
    b = pd.read_parquet(BARS[inst]); b = b[b.session_date <= lab.DEV_END].reset_index(drop=True)
    a = B.to_arrays(b)
    a["roll_day"] = b.roll_adjacent.fillna(False).astype(bool).values
    a["mref"] = (b.o - b.cum_adjustment.astype(float)).values
    prof = instruments.PROFILES[PROF[inst]]
    pv = prof["point_value"]
    L, W = ENV[env]
    rows = []

    def obj(t):
        M = t.suggest_int("intradayMaxQty", 2, 24, step=1)
        K = int(round(t.suggest_float("coreFrac", 0, 1) * M))
        kb = int(round(t.suggest_float("tierBase", 0, 1) * K)); km = int(round(t.suggest_float("tierMid", 0, 1) * (K - kb)))
        p = dict(pointValue=pv, rollCostPerContract=2 * (0.62 + prof["tick_value"]), intradayMaxQty=M, coreQty=K,
                 coreBuildMode=1 if K > 0 else 0, coreTierMode=1, kBase=kb, kMid=km, kTop=K - kb - km, tacticalMode=1,
                 overnightMode=t.suggest_int("overnightMode", 1, 3),
                 ddLimit=t.suggest_float("ddLimit", 1000, 15000, log=True), ddFloorQty=0,
                 ddRearmLen=t.suggest_categorical("ddRearmLen", [10, 20, 40]),
                 recycleMinTicks=t.suggest_int("recycleMinTicks", 4, 80), recycleTPATR=t.suggest_float("recycleTPATR", 0.04, 1.0, log=True),
                 profitRefMode=t.suggest_int("profitRefMode", 0, 3), reductionLock=t.suggest_int("reductionLock", 0, 1),
                 rfThreshold=t.suggest_categorical("rfThreshold", [0.0, 0.382, 0.5, 0.618]),
                 overlayRepairSellTicks=t.suggest_int("overlayRepairSellTicks", 4, 80),
                 baseRepairSellTicks=t.suggest_int("baseRepairSellTicks", 6, 100),
                 lowerRebuyTicks=t.suggest_int("lowerRebuyTicks", 4, 80), repairLifeBars=t.suggest_int("repairLifeBars", 3, 100),
                 oppositeSideCooldownBars=t.suggest_int("oppositeSideCooldownBars", 0, 30),
                 minimumOppositeMoveATR=t.suggest_float("minimumOppositeMoveATR", 0.02, 1.5, log=True),
                 targetDecayBars=t.suggest_int("targetDecayBars", 5, 100), decayMode=t.suggest_categorical("decayMode", [0, 2, 3]))
        res = v6x.run(a, v6x.make_params(**p))
        d = lab.daily(b, res)
        st = lab.period_stats(d, None, lab.DEV_END)
        rawpx = (b.c - b.cum_adjustment.astype(float)).values
        frac = np.where(b.in_rth.values, instruments.margin_frac(prof, "intraday"), instruments.margin_frac(prof, "overnight"))
        util = (res["pos"] * rawpx * pv * frac / np.maximum(res["equity"], 1.0)).max()
        pen = 0.0
        if st["max_dd"] > L: pen += 200 + 400 * (st["max_dd"] / L - 1)
        if -st["worst_day"] > W: pen += 200 + 400 * (-st["worst_day"] / W - 1)
        if util > 1 or res["equity"].min() <= 0: pen += 2000
        sc = 0.5 * st["avg_daily"] + 0.5 * st["avg_ex_top5"] - pen
        rows.append({"trial": t.number, "inst": inst, "arch": "B", "env": env, "score": sc, "feasible": pen == 0,
                     **{f"DEV_{k}": v for k, v in st.items()}, "peak_margin_util": float(util),
                     "fills": int(len(res["f_qty"])), "params": json.dumps(p)})
        if t.number % 100 == 99:
            pd.DataFrame(rows).to_csv(out, index=False)
        return sc

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed, multivariate=True, n_startup_trials=150))
    st.optimize(obj, n_trials=n)
    df = pd.DataFrame(rows); df.to_csv(out, index=False)
    print(inst, "B", env, len(df), int(df.feasible.sum()), round(df.score.max(), 2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
