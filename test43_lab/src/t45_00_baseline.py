"""TEST45 Phase 0: authority + baseline QA.  Re-runs CHAMPION_CONTROL_V1 and the three frozen TEST44 challengers through
2026-05-27 with the frozen code and compares daily P&L / positions with the frozen TEST44 outputs.  Writes champion
per-session state (positions at 16:14 decision time and at session end) for TEST45 overlap/margin accounting."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t44_common as TC  # noqa: E402
import t45_common as C  # noqa: E402

AUTH = {"out/t44/freeze/TEST44_PRE_OOS_FREEZE.json": "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4",
        "out/t44/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json": "2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236",
        "out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.json": "f50902babcbc848574984abb59c4e9cd435e2a3d20878a66955686b6429d7cc3",
        "out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.md": "a7e846c4fdfbef214cbd46cb4dc08a661d3344b3b48328ea212f121628decdc3",
        "src/t44_oos_evaluator.py": "dde908ea03ae93d31f827c21366f7a2088c8027ab711f86d64dbce37fafa3b29",
        "out/p/freeze/TEST43P_FINAL_PORTFOLIOS.json": "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7",
        "out/p/freeze/TEST43P_HOLDOUT_ACCEPTANCE_RULES.json": "62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0",
        "out/p/freeze/TEST43P_PRE_VAL_FREEZE.json": "18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817",
        "data/canonical_1m_ES.parquet": C.DATA["ES"][1], "data/canonical_1m_MNQ.parquet": C.DATA["MNQ"][1]}


def main():
    out = os.path.join(C.T45, "baseline"); os.makedirs(out, exist_ok=True)
    auth = {k: {"expected": v, "actual": C.sha(os.path.join(C.ROOT, k))} for k, v in AUTH.items()}
    for v in auth.values():
        v["ok"] = v["expected"] == v["actual"]
    assert all(v["ok"] for v in auth.values()), auth
    oos_dirs = [p for p in ("out/t44/oos_eval/new_oos",) if os.path.exists(os.path.join(C.ROOT, p))]
    assert not oos_dirs, "a new-OOS evaluation directory exists"
    from t44_oos_evaluator import CANDIDATES
    import t44_alloc as A
    import t44_04_meta as MM
    import p03_portfolio_dev as PD
    from t44_03_priority_loo import parse
    E = A.Engine()
    fz = json.load(open(os.path.join(C.ROOT, "out/t44/freeze/TEST44_PRE_OOS_FREEZE.json")))
    fin = json.load(open(os.path.join(C.ROOT, "out/p/freeze/TEST43P_FINAL_PORTFOLIOS.json")))
    champ = fin["portfolios"]["SECONDARY_2"]
    w = {c: m["contract_weight"] for c, m in champ["members"].items()}
    runs = {}
    runs["CHAMPION_CONTROL_V1"] = E.bk.run(w, gov=PD.gov_for(champ["risk_envelope"], {}))
    P, sess, six = MM.panel(E)
    allf = sum(MM.FAM.values(), [])
    fsets = {"E_ALL": allf, "A_ONLY": MM.FAM["A"], **{f"E_minus_{k}": [f for f in allf if f not in v] for k, v in MM.FAM.items()}}
    for role in CANDIDATES[1:]:
        spec = fz["challengers"][role]
        mode, rq, rk, cap = parse(spec["alloc_cfg"])
        sc = None
        if spec.get("model"):
            pred, _ = MM.walk_forward(P, spec["model"], fsets[spec["features"]])
            sc = MM.score_arrays(E, P, pred, six, spec["usage"])
        REQ, X, dem = E.requests(**rq, score=sc)
        runs[role] = E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), **rk)
    ref = {"CHAMPION_CONTROL_V1": "daily_CHAMPION_CONTROL_V1.csv", "SIMPLE_INTEGER_CHALLENGER": "daily_FINAL_SIMPLE_INTEGER_CHALLENGER.csv",
           "RIDGE_CHALLENGER": "daily_FINAL_RIDGE_CHALLENGER.csv", "XGBOOST_CHALLENGER": "daily_FINAL_XGBOOST_CHALLENGER.csv"}
    rows = []
    T = E.T; sdT = pd.DatetimeIndex(T.sd.values); t = pd.DatetimeIndex(T.index)
    for role, r in runs.items():
        d = E.daily(r)
        old = pd.read_csv(os.path.join(TC.T44, ref[role]), index_col=0, parse_dates=True)
        diff = float((d.pnl - old.pnl.reindex(d.index)).abs().max())
        cols = [c for c in old.columns if c in d.columns]
        cdiff = float(max((d[c] - old[c].reindex(d.index)).abs().max() for c in cols))
        o = {"candidate": role, "daily_pnl_max_abs_diff": diff, "all_daily_columns_max_abs_diff": cdiff, "days": len(d)}
        o.update(C.dstats(d.pnl.values, d.index, "ALL", "ALL_")); o.update(C.dstats(d.pnl.values, d.index, "FORMER_HOLDOUT_USED", "FH_"))
        o["peak_margin_util"] = float(d.mu_max.max())
        rows.append(o)
        d.to_csv(f"{out}/daily_{role}.csv")
        pos = np.asarray(r["pos"], float)
        if role == "CHAMPION_CONTROL_V1":
            p_old = np.load(os.path.join(TC.T44, "pos_CHAMPION_CONTROL_V1.npy"))
            o["positions_max_abs_diff_vs_frozen"] = float(np.abs(pos - p_old).max())
            # per-session champion position: last 3m bar starting <= 16:12 (covers 16:12-16:15) and last bar of session
            mins = t.hour * 60 + t.minute
            df = pd.DataFrame({"sd": sdT, "m": mins, "pES": pos[:, 0], "pMNQ": pos[:, 1]})
            last = df.groupby("sd").tail(1).set_index("sd")
            rth = df[(df.m >= 570) & (df.m <= 972)]
            lk = rth.groupby("sd").tail(1).set_index("sd")
            opn = df[df.m == 570].groupby("sd").head(1).set_index("sd")
            st = pd.DataFrame({"pES_1612": lk.pES, "pMNQ_1612": lk.pMNQ, "pES_end": last.pES, "pMNQ_end": last.pMNQ,
                               "pES_0930": opn.pES, "pMNQ_0930": opn.pMNQ})
            st.to_csv(f"{out}/champion_session_state.csv")
    B = pd.DataFrame(rows)
    B.to_csv(f"{out}/T45_00_baseline_reproduction.csv", index=False)
    ok = bool((B.daily_pnl_max_abs_diff < 1e-6).all())
    C.jdump({"authority_hashes": auth, "reproduction_ok": ok, "new_oos_dirs_present": oos_dirs, "rows": rows}, f"{out}/T45_00_baseline_qa.json")
    print(B.T); print("REPRO_OK", ok)
    assert ok


if __name__ == "__main__":
    main()
