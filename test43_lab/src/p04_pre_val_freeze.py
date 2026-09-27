"""TEST43-P Phases 9/10 (regime matrix, complementarity) + Phase 18 pre-VAL freeze.
Writes out/p/p09_regime_matrix_DEV.csv, p10_complementarity_DEV.csv and out/p/freeze/TEST43P_PRE_VAL_FREEZE.json (+sha256).
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments, lab, portfolio as PF, sleeves as S, v6lab  # noqa: E402
import p02_fingerprint as FP  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402

OUT = PF.PDIR
FZ = f"{OUT}/freeze"
K_SHRINK = 60   # sessions of prior weight toward the unconditional mean


def regime_matrix(D):
    rows = []
    C = S.candidates()
    regs = {i: FP.regimes(i) for i in ("ES", "MNQ")}
    for cid in S.ELIGIBLE + S.SHADOW:
        inst = C[cid]["inst"]
        d = D[cid][D.index <= lab.DEV_END]
        g = regs[inst].reindex(d.index)
        cell = g.tierlab.fillna("NEUTRAL") + "_" + np.where(g.vol == "HIVOL", "HIVOL", "NOT_HIVOL")
        mu = d.mean()
        for cname, x in d.groupby(cell.values):
            n = len(x); eq = x.cumsum(); mdd = float((eq.cummax() - eq).max())
            rows.append({"id": cid, "regime": cname, "n_sessions": n, "avg": x.mean(), "median": x.median(),
                         "shrunk_avg": (n * x.mean() + K_SHRINK * mu) / (n + K_SHRINK), "max_dd_within_cell": mdd,
                         "worst": x.min(), "t_vs_uncond": (x.mean() - mu) / (x.std(ddof=1) / np.sqrt(n)) if n > 2 else np.nan})
    return pd.DataFrame(rows)


def main():
    os.makedirs(FZ, exist_ok=True)
    D = PD.load_daily()
    rm = regime_matrix(D)
    rm.to_csv(f"{OUT}/p09_regime_matrix_DEV.csv", index=False)
    piv = rm[rm.id.isin(S.ELIGIBLE)].pivot(index="id", columns="regime", values="shrunk_avg")
    # complementarity: rank of each sleeve within each regime (1 = best), and sign of shrunk average
    comp = piv.rank(ascending=False).add_prefix("rank_").join(piv.add_prefix("shrunk_avg_"))
    comp.to_csv(f"{OUT}/p10_complementarity_DEV.csv")
    spec = json.load(open(f"{OUT}/p_dev_spec.json"))
    sig = pd.Series(spec["sigma_daily_dev"])
    # P2B: the DEV candidate-count frontier saturation point (first 4 of the deterministic order)
    order = spec["count_order"]
    P = dict(spec["portfolios"])
    P["P2B_STATIC_4SLEEVE"] = {cid: 0.25 for cid in order[:4]}
    bk = PF.Book(lab.DEV_END, S.ELIGIBLE)
    L = dict(spec["L"])
    for env in PD.ENV:
        L[f"P2B_STATIC_4SLEEVE|{env}"] = PD.calibrate(bk, P["P2B_STATIC_4SLEEVE"], sig, env)
    C = S.candidates()
    frozen = {
        "program": "TEST43-P multi-strategy regime ensemble",
        "frozen_before_any_VAL_portfolio_outcome": True,
        "holdout_opened": False,
        "data": {"DEV": ["2019-05-06", "2024-12-31"], "VAL": ["2025-01-01", "2025-09-30"], "HOLDOUT": "closed"},
        "eligible": S.ELIGIBLE,
        "shadow_controls": {"ES_robust_F_AGG_0": "downgraded: cost sensitivity + neighbour DD p90 $28k",
                            "MNQ_arch_E_AGG_0": "downgraded: neighbour DD p90 $26k",
                            "ES_r2_G_AGG_0": "wall-clock fix exact on 3m; FAILED 5m (DEV DD $20.5k > $20k AGG) and MNQ transfer (DD $23.4k, VAL excess -40.6)"},
        "candidates": {cid: {"inst": C[cid]["inst"], "arch": C[cid]["arch"], "params": C[cid]["params"],
                             "sha256": S.cand_hash(C[cid])} for cid in S.ELIGIBLE + S.SHADOW},
        "clusters": {"method": "average linkage on 1 - (0.5 daily corr + 0.25 30-min position corr + 0.25 drawdown overlap), cut 0.5",
                     "membership": spec["clusters_cut0.5"]},
        "risk_normalisation": {"unit": "sleeve standalone DEV daily P&L standard deviation ($)",
                               "sigma_daily_dev": spec["sigma_daily_dev"],
                               "sleeve_contract_weight": "w_s = budget_s * L / sigma_s (float); instrument target = sum_s w_s * desired_s; integer only at execution"},
        "portfolios": P,
        "p2_rule": "one representative per behavioural cluster = max min(F1,F2,F3 matched-beta excess) on DEV, tie -> DEV ret/DD; equal risk",
        "p2b_rule": "first 4 of the deterministic round-robin cluster order (DEV candidate-count frontier saturation)",
        "regime_tilt": {"base": "P2_STATIC_DIVERSIFIED", "alphas": spec["tilt_alphas"],
                        "cells": "trend tier (BEAR / NEUTRAL / BULL, lagged completed sessions) x vol (ATR20 pct >= 2/3 HIVOL)",
                        "estimate": "expanding strictly-prior sessions; tilt = 1 + alpha * clip(t/2, -1, 1); none before 250 sessions or < 20 cell sessions; renormalised to constant total budget",
                        "forbidden_inputs": "no TEST43-M directional signal; C6 compression not used"},
        "risk_scale_L": L,
        "L_calibration": "largest L on a 60-point geometric grid (100..12000) with DEV MaxDD <= 90% envelope DD, DEV worst day >= 90% envelope floor, no margin breach",
        "governor": dict(PF.GOV_DEFAULT, env_dd="envelope DD", dd_tiers="0.6*envDD -> x0.5, 0.85*envDD -> x0.25; rearm at a new session when DD < 0.3*envDD",
                         day_stop="0.8*|envelope worst-day floor| -> x0.5 for the rest of the session"),
        "envelopes": {k: list(v) for k, v in lab.ENVELOPES.items()},
        "costs": {"commission_side": 0.62, "slippage_ticks": 1, "roll_cost": {"MES": 3.74, "MNQ": 2.24}},
        "margin": {"MES": {"intraday_frac": instruments.margin_frac(instruments.PROFILES["MES"], "intraday"),
                           "overnight_frac": instruments.margin_frac(instruments.PROFILES["MES"], "overnight")},
                   "MNQ": {"intraday_frac": instruments.margin_frac(instruments.PROFILES["MNQ"], "intraday"),
                           "overnight_frac": instruments.margin_frac(instruments.PROFILES["MNQ"], "overnight")},
                   "note": "raw (unadjusted) price for notional/margin; adjusted canonical price for P&L; marginU 0.5 of equity"},
        "val_pass_rule": "VAL avg/day > 0 AND VAL MaxDD <= envelope DD AND VAL worst day >= envelope floor AND no margin breach AND VAL matched-beta excess reported",
        "final_selection_rule": {
            "PRIMARY": "among MODERATE variants passing VAL: highest DEV ret/DD; ties -> fewer sleeves",
            "SECONDARY_1": "simplest static diversified: P2_STATIC_DIVERSIFIED|MODERATE if it passes VAL, else P2B",
            "SECONDARY_2": "defensive: CONSERVATIVE variant passing VAL with the lowest DEV MaxDD",
            "note": "P3 is eligible for PRIMARY only if it also beats P2 on VAL after cost (avg/day and ret/DD); no rescue"},
        "code": {f: hashlib.sha256(open(os.path.join(os.path.dirname(__file__), f), "rb").read()).hexdigest()
                 for f in ("t43/portfolio.py", "t43/sleeves.py", "p03_portfolio_dev.py", "p04_pre_val_freeze.py", "t43/v6a.py", "t43/v6x.py")},
    }
    fn = f"{FZ}/TEST43P_PRE_VAL_FREEZE.json"
    json.dump(frozen, open(fn, "w"), indent=1, default=float)
    h = hashlib.sha256(open(fn, "rb").read()).hexdigest()
    open(fn.replace(".json", ".sha256"), "w").write(f"{h}  TEST43P_PRE_VAL_FREEZE.json\n")
    print("PRE_VAL_FREEZE_SHA256", h)
    print(pd.Series(L).round(1).to_string())
    pd.set_option("display.width", 250)
    print(piv.round(1).to_string())


if __name__ == "__main__":
    main()
