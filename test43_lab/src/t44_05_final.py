"""TEST44 Phases 16-20: challenger selection (predeclared rules), stress/attribution of the final set, TEST43 failure
attribution, final meta-model fits for OOS, TEST44_PRE_OOS_FREEZE.json and TEST44_NEW_OOS_ACCEPTANCE_RULES.json.
No data after 2026-05-27 is loaded."""
import hashlib
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

sys.path.insert(0, os.path.dirname(__file__))
import t44_alloc as A  # noqa: E402
import t44_common as TC  # noqa: E402
import t44_04_meta as MM  # noqa: E402
from t44_03_priority_loo import parse  # noqa: E402

OUT = TC.T44
FZ = f"{OUT}/freeze"
PERS = ("ALL", "ML_OOS_SPAN", "F1_2019_2020", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026", "Y2020", "Y2022", "FORMER_HOLDOUT")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def select(M):
    """Predeclared: within a model family, max ML_OOS_SPAN ret/DD subject to F2, F3, F4 avg > 0, ML-span matched-beta
    excess > 0 and ML-span MaxDD <= $15k; ties -> fewer features (A_ONLY < E_minus_* < E_ALL)."""
    ok = M[(M.F2_2021_2022_avg > 0) & (M.F3_2023_2024_avg > 0) & (M.F4_2025_2026_avg > 0) & (M.ML_OOS_SPAN_excess_vs_mb > 0)
           & (M.ML_OOS_SPAN_max_dd <= 15000)].copy()
    ok["nfeat"] = ok.features.map(lambda f: 0 if f == "A_ONLY" else (1 if f.startswith("E_minus") else 2))
    return ok.sort_values(["ML_OOS_SPAN_ret_dd", "nfeat"], ascending=[False, True]).iloc[0]


def main():
    os.makedirs(FZ, exist_ok=True)
    E = A.Engine()
    simple_sel = json.load(open(f"{OUT}/t44_simple_selection.json"))
    SIMPLE = simple_sel["SIMPLE_BEST_FEASIBLE"]
    M = pd.read_csv(f"{OUT}/t44_meta_performance.csv")
    ridge = select(M[M.model == "RIDGE"])
    xg = select(M[M.model.str.startswith("XGB")])
    ch = {"SIMPLE_INTEGER_CHALLENGER": {"alloc_cfg": SIMPLE, "model": None},
          "RIDGE_CHALLENGER": {"alloc_cfg": ridge.alloc_cfg, "model": "RIDGE", "features": ridge.features, "usage": ridge.usage},
          "XGBOOST_CHALLENGER": {"alloc_cfg": xg.alloc_cfg, "model": xg.model, "features": xg.features, "usage": xg.usage}}
    print(ch)
    # ---------------------------------------------------------------- rerun final set: stats, stress, attribution
    P, sess, six = MM.panel(E)
    all_feats = sum(MM.FAM.values(), [])
    fsets = {"E_ALL": all_feats, "A_ONLY": MM.FAM["A"], **{f"E_minus_{k}": [f for f in all_feats if f not in v] for k, v in MM.FAM.items()}}
    rows, stress, attr, dailies = [], [], [], {}
    for role, spec in ch.items():
        mode, rq, rk, cap = parse(spec["alloc_cfg"])
        sc = None
        if spec["model"]:
            pred, _ = MM.walk_forward(P, spec["model"], fsets[spec["features"]])
            sc = MM.score_arrays(E, P, pred, six, spec["usage"])
        REQ, X, dem = E.requests(**rq, score=sc)
        pr = E.priority("LOW_DD", dem)
        for tag, ex in (("BASE", {}), ("SLIP2", dict(slip_ticks=2)), ("SLIP4", dict(slip_ticks=4)), ("COMM1.00", dict(commission=1.0)),
                        ("TIMING_BRITTLENESS_STRESS", dict(delay=1)), ("MARGINx1.5_INTRADAY", dict(m_intra=1.5)), ("ON_MARGINx2", dict(m_on=2.0))):
            r = E.run(mode, REQ, X, pr, caps=(cap, cap), **rk, **ex)
            o, d = E.summary(r, pers=PERS)
            (rows if tag == "BASE" else stress).append({"candidate": role, "test": tag, **o})
            if tag == "BASE":
                dailies[role] = d; d.to_csv(f"{OUT}/daily_FINAL_{role}.csv")
                at = E.attribution(r, dem, "LOW_DD"); at.insert(0, "candidate", role); attr.append(at)
    for tag in ("CHAMPION_CONTROL_V1", "D0_CURRENT_TEST43"):
        d = pd.read_csv(f"{OUT}/daily_{tag}.csv", index_col=0, parse_dates=True)
        o = {"candidate": tag, "test": "BASE"}
        for p in PERS:
            o.update(TC.stats(d, p, E.c1))
        o["peak_margin"] = float(d.mu_max.max())
        rows.append(o)
    F = pd.DataFrame(rows); F.to_csv(f"{OUT}/t44_final_comparison.csv", index=False)
    pd.DataFrame(stress).to_csv(f"{OUT}/t44_final_stress.csv", index=False)
    pd.concat(attr).to_csv(f"{OUT}/t44_final_integer_attribution.csv", index=False)
    # session-matched beta (report only) on ALL / FORMER_HOLDOUT for the final set is produced by the report script
    # ---------------------------------------------------------------- TEST43 failure attribution on full history (D0)
    pos = np.load(f"{OUT}/pos_D0_CURRENT_TEST43.npy"); D = np.load(f"{OUT}/D_D0_CURRENT_TEST43.npy")
    sd = pd.DatetimeIndex(E.T.sd.values)
    rows_f = []
    for per in ("ALL", "F1_2019_2020", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026", "FORMER_HOLDOUT"):
        s, e = TC.PERIODS[per]
        m = (sd <= pd.Timestamp(e)) & ((sd >= pd.Timestamp(s)) if s else True)
        r_ = {"period": per}
        for k, inst in enumerate(A.INSTS):
            dc = np.r_[0.0, np.diff(E.arr["c"][:, k])] * E.pv[k]
            virt = np.r_[0.0, D[:-1, k]]
            r_[f"{inst}_virtual_fractional_gross"] = float((virt * dc)[m].sum())
            r_[f"{inst}_realised_integer_gross"] = float((pos[:, k] * dc)[m].sum())
            r_[f"{inst}_avg_desired"] = float(D[m, k].mean()); r_[f"{inst}_avg_held"] = float(pos[m, k].mean())
            r_[f"{inst}_share_bars_desired_lt_0.5_held_0"] = float(((D[m, k] > 0) & (D[m, k] < 0.5) & (pos[m, k] == 0)).mean())
        r_["gap_total"] = sum(r_[f"{i}_realised_integer_gross"] - r_[f"{i}_virtual_fractional_gross"] for i in A.INSTS)
        rows_f.append(r_)
    pd.DataFrame(rows_f).to_csv(f"{OUT}/t44_test43_failure_attribution.csv", index=False)
    # ---------------------------------------------------------------- final meta fits (all labelled history) for the OOS
    fits = {}
    for role in ("RIDGE_CHALLENGER", "XGBOOST_CHALLENGER"):
        spec = ch[role]; feats = fsets[spec["features"]]
        tr = P[P.sess_ix <= P.sess_ix.max() - MM.PURGE].dropna(subset=feats + ["y"])
        Xtr = tr[feats].values; ytr = np.clip(tr.y.values, -3, 3)
        if spec["model"] == "RIDGE":
            scl = StandardScaler().fit(Xtr); m = Ridge(alpha=MM.RIDGE_ALPHA).fit(scl.transform(Xtr), ytr)
            obj = {"scaler_mean": scl.mean_.tolist(), "scaler_scale": scl.scale_.tolist(), "coef": m.coef_.tolist(), "intercept": float(m.intercept_), "features": feats}
            fn = f"{FZ}/ridge_final.json"; json.dump(obj, open(fn, "w"), indent=1)
        else:
            order = np.argsort(tr.sess_ix.values, kind="stable"); cut = int(len(tr) * 0.8)
            m = xgb.XGBRegressor(objective="reg:squarederror", random_state=7, n_jobs=4, early_stopping_rounds=40, **MM.XGB_PRESETS[spec["model"]])
            m.fit(Xtr[order[:cut]], ytr[order[:cut]], eval_set=[(Xtr[order[cut:]], ytr[order[cut:]])], verbose=False)
            fn = f"{FZ}/xgb_final.json"; m.save_model(fn)
            obj = {"best_iteration": int(m.best_iteration), "features": feats}
        fits[role] = {"file": os.path.relpath(fn, TC.ROOT), "sha256": sha(fn), "train_last_session": str(sess[int(tr.sess_ix.max())].date()),
                      "train_rows": len(tr), **{k: v for k, v in obj.items() if k in ("best_iteration", "intercept")}}
    # ---------------------------------------------------------------- PRE-OOS FREEZE
    meta = json.load(open(f"{OUT}/sleeve_meta.json"))
    C = __import__("t43.sleeves", fromlist=["x"]).candidates()
    code = {f: sha(os.path.join(TC.SRC, f)) for f in ("t43/intport.py", "t43/portfolio.py", "t43/sleeves.py", "t43/v6a.py", "t43/v6x.py", "t43/v6lab.py",
                                                       "t43/features.py", "t43/lab.py", "t43/instruments.py", "t43/bars.py", "t44_common.py", "t44_alloc.py",
                                                       "t44_02_deterministic.py", "t44_03_priority_loo.py", "t44_04_meta.py", "t44_05_final.py")}
    freeze = {
        "program": "TEST44 discrete contract + meta allocator lab", "frozen_before_any_data_after": "2026-05-27",
        "research_data": ["2019-05-06", "2026-05-27"], "former_TEST43_holdout": "2025-10-01..2026-05-27 = USED historical data",
        "new_oos_start": "2026-05-28", "new_oos_data_acquired": False, "new_oos_opened": False,
        "canonical_data_sha256": {k: v[1] for k, v in TC.DATA.items()},
        "sleeves": {c: {"inst": meta[c]["inst"], "cluster": TC.CLUSTER[c], "params": C[c]["params"], "sha256": meta[c]["cand_sha256"],
                        "max_desired_DEV": meta[c]["max_desired_DEV"]} for c in TC.ELIG},
        "shadow_controls": TC.SHADOW,
        "CHAMPION_CONTROL_V1": {"definition": "TEST43-P SECONDARY_2 P1_CLUSTER_EQUAL_RISK|CONSERVATIVE, byte-identical frozen implementation",
                                "final_portfolios_sha256": "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7"},
        "integer_mapping": {"intensity": "desired_target / sleeve max desired target on DEV (<=2024-12-31)",
                            "OFF": "desired <= 0 or intensity < off-band", "NORMAL": "1 contract", "STRONG": "2 contracts when intensity >= theta"},
        "challengers": {role: {**spec, "caps_per_symbol": parse(spec["alloc_cfg"])[3],
                               "engine_mode": {0: "REQUEST", 1: "TRACK", 2: "RESIDUAL"}[parse(spec["alloc_cfg"])[0]],
                               "request_kwargs": parse(spec["alloc_cfg"])[1], "engine_kwargs": parse(spec["alloc_cfg"])[2]} for role, spec in ch.items()},
        "cluster_rules": {"clusters": {1: "MNQ A family", 2: "MNQ C family", 3: "ES family"}, "desired_state": "sum over clusters of mean member demand (cluster-equal)"},
        "governor": {"account": 150000.0, "envelope": "MODERATE", "dd_tiers": "0.6*15000 -> $ATR budget x0.5; 0.85*15000 -> x0.25",
                     "rearm": "after 20 sessions at a reduced tier (HWM reset) or DD < 0.3*15000", "day_stop": "0.8*3000 -> x0.5 rest of session",
                     "atr_budget": "budget_frac 1.0 x $ATR of the per-symbol caps", "margin": "<= 0.5 equity; overnight fraction when next bar not RTH",
                     "cut_order": "lowest-priority instrument first (LOW_DD static priority)"},
        "meta_models": {"sample": "(sleeve, session)", "target": "1-contract ON P&L minus ON-share x passive 1-contract P&L, in daily-ATR units, clipped +-3",
                        "features": MM.FAM, "calendar_features": "none", "walk_forward": {"first_train_sessions": MM.FIRST_TRAIN, "refit_every_sessions": MM.BLOCK,
                                                                                            "purge_sessions": MM.PURGE, "expanding": True},
                        "ridge_alpha": MM.RIDGE_ALPHA, "xgb_presets": MM.XGB_PRESETS, "score_usages": MM.USAGES,
                        "oos_procedure": "start from the final fits below; refit every 63 OOS sessions on all labelled sessions (expanding, 1-session purge), identical hyper-parameters",
                        "final_fits": fits},
        "costs": {"commission_side": 0.62, "slippage_ticks": 1, "roll_cost": {"MES": 3.74, "MNQ": 2.24}},
        "margin_fracs": {"MES": [float(E.fin[0]), float(E.fon[0])], "MNQ": [float(E.fin[1]), float(E.fon[1])]},
        "code_sha256": code,
    }
    fn = f"{FZ}/TEST44_PRE_OOS_FREEZE.json"
    json.dump(freeze, open(fn, "w"), indent=1, default=float)
    pre_sha = sha(fn); open(fn.replace(".json", ".sha256"), "w").write(f"{pre_sha}  TEST44_PRE_OOS_FREEZE.json\n")
    # ---------------------------------------------------------------- NEW OOS ACCEPTANCE RULES
    rules = {
        "program": "TEST44", "written_before_new_oos_data": True, "pre_oos_freeze_sha256": pre_sha,
        "new_oos_window": {"start": "2026-05-28", "end": "open-ended; first evaluation after >= 120 RTH sessions, then quarterly"},
        "evaluated": ["CHAMPION_CONTROL_V1", "SIMPLE_INTEGER_CHALLENGER", "RIDGE_CHALLENGER", "XGBOOST_CHALLENGER"],
        "integrity (before any result)": ["canonical OOS data hash-recorded before parsing; DEV/VAL/2026-05-27 prefix reproduces frozen daily P&L exactly",
                                          "code SHA256 equal to the pre-OOS freeze", "meta refits follow the frozen procedure only"],
        "absolute_pass (each candidate, MODERATE envelope)": {"net_pnl": "> 0 after costs", "margin": "no breach; peak <= 0.5 equity",
                                                              "max_dd": "<= $15,000", "worst_day": ">= -$3,000", "remove_top3_avg": "> 0",
                                                              "best_day": "<= 35% of net P&L"},
        "promotion_over_CHAMPION (challenger must pass absolute AND all of)": {
            "ret_dd": ">= 1.25 x champion OOS return/MaxDD",
            "matched_beta_excess": ">= champion OOS matched-beta excess per day",
            "session_matched_beta_excess": ">= champion OOS session-matched-beta excess per day",
            "net_pnl": ">= 0.8 x champion OOS net P&L (no tiny-return 'win' by shrinking exposure)",
            "cost_robust": "SLIP4 net P&L > 0"},
        "XGB_vs_RIDGE": "XGB may be promoted only if it also beats RIDGE by >= 1.25x on OOS return/MaxDD and on net P&L",
        "reported_only": ["avg/day", "median/day", "remove-top-1/3/5", "friction", "contract sides", "turnover", "average/peak margin",
                          "average RTH/ON contracts per symbol", "rolling 3m", "TIMING_BRITTLENESS_STRESS", "integer attribution per sleeve"],
        "prohibited_after_opening": ["any parameter/feature/threshold/cap/governor change", "membership or model rescue", "re-labelling the same OOS window"],
        "live_authorization": "NO (a pass only qualifies for paper/live readiness review)",
    }
    fn2 = f"{FZ}/TEST44_NEW_OOS_ACCEPTANCE_RULES.json"
    json.dump(rules, open(fn2, "w"), indent=1)
    rules_sha = sha(fn2); open(fn2.replace(".json", ".sha256"), "w").write(f"{rules_sha}  TEST44_NEW_OOS_ACCEPTANCE_RULES.json\n")
    print("PRE_OOS_FREEZE_SHA256", pre_sha); print("NEW_OOS_RULES_SHA256", rules_sha)
    pd.set_option("display.width", 260)
    print(F[["candidate", "ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd", "ALL_excess_vs_mb", "ML_OOS_SPAN_avg", "ML_OOS_SPAN_max_dd",
             "ML_OOS_SPAN_ret_dd", "ML_OOS_SPAN_excess_vs_mb", "Y2020_avg", "Y2022_avg", "FORMER_HOLDOUT_avg", "F4_2025_2026_avg"]].round(3).to_string(index=False))
    print(pd.DataFrame(rows_f).round(0).to_string(index=False))


if __name__ == "__main__":
    main()
