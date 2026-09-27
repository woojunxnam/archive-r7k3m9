"""Lane G: low-turnover tactical extraction on the V5.3.3/V6X target-ladder (REPAIR/PROFIT recycling suppressed).
Also runs lane B2 (full tactical, ROBUST2) when LANE=B.  DEV-only ROBUST2 objective.
Usage: python optimize_v6_G.py INST ENV N SEED OUT [LANE=G|B]
"""
import json, os, sys
import numpy as np, optuna, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, instruments, lab, robust, v6lab, v6x  # noqa: E402

BARS = {"ES": "../out/p123/ES_3m_bars.parquet", "MNQ": "../out/mnq/MNQ_3m_bars.parquet"}
PROF = {"ES": "MES", "MNQ": "MNQ"}
R = v6x.R
BASE_MASK = (1 << R["REPAIR_SELL"]) | (1 << R["PROFIT_SELL"]) | (1 << R["LOWER_REBUY"]) | (1 << R["FAILED_RESTORE"])


def setup(inst, end):
    b = pd.read_parquet(BARS[inst]); b = b[b.session_date <= end].reset_index(drop=True)
    a = B.to_arrays(b)
    a["roll_day"] = b.roll_adjacent.fillna(False).astype(bool).values
    a["mref"] = (b.o - b.cum_adjustment.astype(float)).values
    return b, a


def evaluate_v6x(inst, b, a, p, periods, end):
    prof = instruments.PROFILES[PROF[inst]]; pv = prof["point_value"]
    res = v6x.run(a, v6x.make_params(**p))
    d = lab.daily(b, res)
    o = v6lab.period_block(inst, d, periods, end, mb=True)
    rawpx = (b.c - b.cum_adjustment.astype(float)).values
    frac = np.where(b.in_rth.values, instruments.margin_frac(prof, "intraday"), instruments.margin_frac(prof, "overnight"))
    util = res["pos"] * rawpx * pv * frac / np.maximum(res["equity"], 1.0)
    o["peak_margin_util"] = float(util.max()); o["margin_breach"] = bool(util.max() > 1 or res["equity"].min() <= 0)
    o["min_equity"] = float(res["equity"].min()); o["fills"] = int(len(res["f_qty"]))
    o["friction"] = float(res["f_qty"].sum()) * (prof["commission_side"] + 0.25 * pv)
    return o, res, d


def space(t, inst, lane):
    prof = instruments.PROFILES[PROF[inst]]
    M = t.suggest_int("intradayMaxQty", 2, 24)
    K = int(round(t.suggest_float("coreFrac", 0, 1) * M))
    kb = int(round(t.suggest_float("tierBase", 0, 1) * K)); km = int(round(t.suggest_float("tierMid", 0, 1) * (K - kb)))
    p = dict(pointValue=prof["point_value"], rollCostPerContract=2 * (0.62 + prof["tick_value"]), intradayMaxQty=M,
             coreQty=K, coreBuildMode=1 if K > 0 else 0, coreTierMode=1, kBase=kb, kMid=km, kTop=K - kb - km, tacticalMode=1,
             overnightMode=t.suggest_int("overnightMode", 1, 3),
             lotQty=t.suggest_int("lotQty", 1, 3),
             targetDecayBars=t.suggest_int("targetDecayBars", 5, 120), decayMode=t.suggest_categorical("decayMode", [0, 2, 3]),
             oppositeSideCooldownBars=t.suggest_int("oppositeSideCooldownBars", 0, 60),
             minimumOppositeMoveATR=t.suggest_float("minimumOppositeMoveATR", 0.02, 3.0, log=True),
             addCooldownBars=t.suggest_int("addCooldownBars", 0, 30),
             maxActionsPerSess=t.suggest_categorical("maxActionsPerSess", [0, 2, 4, 6, 10, 20]),
             bottomRangePct=t.suggest_float("bottomRangePct", 0.1, 0.6),
             driftVWAPDeepSigma=t.suggest_float("driftVWAPDeepSigma", 0.5, 3.0))
    if t.suggest_categorical("useDD", [0, 1]):
        p.update(ddLimit=t.suggest_float("ddLimit", 1000, 15000, log=True), ddFloorQty=0,
                 ddRearmLen=t.suggest_categorical("ddRearmLen", [10, 20, 40]))
    if t.suggest_categorical("useEmergency", [0, 1]):
        p.update(emergencyLoss=t.suggest_float("emergencyLoss", 500, 15000, log=True), emergencyToCore=t.suggest_int("emergencyToCore", 0, 1))
    if lane == "G":
        extra = t.suggest_categorical("extraSuppress", ["none", "TARGET_TRIM", "PULLBACK"])
        m = BASE_MASK
        if extra == "TARGET_TRIM": m |= 1 << R["TARGET_TRIM"]
        if extra == "PULLBACK": m |= (1 << R["BASE_PULLBACK"]) | (1 << R["OVERLAY_PULLBACK"])
        p["disableMask"] = m
    else:
        p.update(recycleMinTicks=t.suggest_int("recycleMinTicks", 4, 80), overlayRepairSellTicks=t.suggest_int("overlayRepairSellTicks", 4, 80),
                 lowerRebuyTicks=t.suggest_int("lowerRebuyTicks", 4, 80), repairLifeBars=t.suggest_int("repairLifeBars", 3, 100))
    return p


def main(inst, env, n, seed, out, lane="G"):
    b, a = setup(inst, lab.DEV_END)
    v6lab.load(inst, lab.DEV_END)
    rows = []

    def obj(t):
        p = space(t, inst, lane)
        o, res, d = evaluate_v6x(inst, b, a, p, ("DEV", "F1", "F2", "F3"), lab.DEV_END)
        nm = sum(1 for k in ("ddLimit", "emergencyLoss") if p.get(k)) + (1 if p.get("maxActionsPerSess") else 0)
        sc, feas = robust.score2(o, env, nm)
        rows.append({"trial": t.number, "inst": inst, "arch": lane, "env": env, "score": sc, "feasible": feas,
                     **{k: v for k, v in o.items() if k.startswith(("DEV_", "F1_", "F2_", "F3_"))},
                     "peak_margin_util": o["peak_margin_util"], "fills": o["fills"], "friction": o["friction"],
                     "params": json.dumps(p)})
        if t.number % 100 == 99:
            pd.DataFrame(rows).to_csv(out, index=False)
        return sc

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed, multivariate=True, n_startup_trials=200))
    st.optimize(obj, n_trials=n)
    df = pd.DataFrame(rows); df.to_csv(out, index=False)
    print(inst, lane, env, len(df), int(df.feasible.sum()), round(df.score.max(), 2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "G")
