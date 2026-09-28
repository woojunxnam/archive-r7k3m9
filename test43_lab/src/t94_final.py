"""TEST94+ final: Lane A PRESS1 verdict, Lane B FIXED_CLUE_BASKET_V1 freeze (forward-shadow candidate, own OOS start), registries, report."""
import datetime
import glob
import hashlib
import json
import os
import pickle
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402

PW = os.path.join(B.LAB, "out", "PRESS_BASKET_LAB"); FZ = os.path.join(B.LAB, "frozen", "fixed_clue_basket_v1")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def freeze_models():
    """final forward models trained on ALL research data <= 2026-05-27 (no forward data)."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    import t65_run as R
    import t86_run as T86
    import t91_ml as T91
    Is = B.load(); I = Is["MNQ"]; BK = A.buckets(I); c = T86.CAND["PG12_DOWN_STACK"]; h = c["horizon"]
    E, P1, F = T86.events(I, Is["ES"], "PG12_DOWN_STACK", c["base_proxy"])
    E = A.label(I, E.copy(), BK); E = E.dropna(subset=[f"{h}_net"]).reset_index(drop=True)
    X = T91.feats(I, E, P1, F)
    pg = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=25, random_state=5).fit(X, E[f"{h}_net"].values)
    W = pd.read_parquet(os.path.join(C45.ROOT, "out", "test65", "T65_window_labels.parquet"))
    W = W[W.window == "W1_0930_1030"].dropna(subset=R.FEATS + ["fwd_strongN"])
    sc = StandardScaler().fit(W[R.FEATS]); lg = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(W[R.FEATS]), W.fwd_strongN.astype(int))
    thr = float(np.quantile(lg.predict_proba(sc.transform(W[R.FEATS]))[:, 1], 0.7))
    os.makedirs(os.path.join(FZ, "models"), exist_ok=True)
    pickle.dump({"model": pg, "features": list(X.columns), "rule": "trade PG12_DOWN_STACK (VP-B, bins 0.02, VA 70%) iff prediction > 0; 1 MNQ; next open -> 16:00"},
                open(os.path.join(FZ, "models", "PG12_HGB_FINAL.pkl"), "wb"))
    pickle.dump({"scaler": sc, "model": lg, "threshold": thr, "features": R.FEATS, "rule": "09:35 W1 features; trade iff p >= threshold AND ret_since_open > 0 AND T61 u < 3; "
                 "1 MNQ; fill 09:36 -> 10:30"}, open(os.path.join(FZ, "models", "T66_ML_FINAL.pkl"), "wb"))
    return {"PG12_train_events": len(E), "T66_train_rows": len(W), "T66_threshold": thr}


def main():
    P1 = pd.read_csv(os.path.join(PW, "LANE_A_PRESS1", "PRESS1_RESULTS.csv")); BR = json.load(open(os.path.join(PW, "LANE_B_BASKET", "BASKET_RESULT.json")))
    best = P1[P1.leg == "MNQ"].sort_values("marginal_avg_day", ascending=False).iloc[0]
    now = datetime.datetime.now(datetime.timezone.utc); oos = first_rth_after(now)
    minfo = freeze_models()
    srcs = ["t94b_basket.py", "t94p_prereg.py", "t66_run.py", "t67_run.py", "t68_run.py", "t86_run.py", "t91_ml.py", "t85_run.py", "t84_run.py", "ap_common.py", "box_common.py",
            "t65_common.py", "t65_mod.py", "t65_run.py", "t94_final.py"]
    os.makedirs(os.path.join(FZ, "src"), exist_ok=True)
    for f in srcs:
        shutil.copy2(os.path.join(B.LAB, "src", f), os.path.join(FZ, "src", f))
    arts = {"prereg": os.path.join(PW, "TEST94_PLUS_PREREGISTRATION.json"), "basket_result": os.path.join(PW, "LANE_B_BASKET", "BASKET_RESULT.json"),
            "basket_ledger": os.path.join(PW, "LANE_B_BASKET", "BASKET_LEDGER.csv"), "t65_windows": os.path.join(C45.ROOT, "out", "test65", "T65_window_labels.parquet"),
            "t65_events": os.path.join(C45.ROOT, "out", "test65", "T65_event_labels.parquet")}
    os.makedirs(os.path.join(FZ, "artifacts"), exist_ok=True)
    for k, p in arts.items():
        shutil.copy2(p, os.path.join(FZ, "artifacts", os.path.basename(p)))
    files = sorted(glob.glob(os.path.join(FZ, "**", "*"), recursive=True))
    HI = pd.DataFrame({"file": [os.path.relpath(p, FZ) for p in files if os.path.isfile(p)], "sha256": [sha(p) for p in files if os.path.isfile(p)]})
    HI.to_csv(os.path.join(FZ, "HASH_INDEX.csv"), index=False)
    man = {"candidate": "T61_PLUS_FIXED_CLUE_BASKET_V1", "status": "FORWARD SHADOW CANDIDATE ONLY (historical preregistered gate PASS; SELECTION-BIASED members; recent-year concentrated)",
           "freeze_utc": now.isoformat(timespec="seconds"), "BASKET_OOS_START": oos, "T61": "unchanged, frozen; basket is a separate overlay with T61 priority on capacity",
           "members": BR["FIXED_CLUE_BASKET_MEMBERS"], "sizes": {"T66_ML_OPENING": "1 MNQ", "T68_RAW_BREAKS": "1 MNQ", "T67_TOM_INTRADAY": "2 MES", "PG12_ML": "1 MNQ"},
           "capacity": "MNQ T61 + basket <= 6 (T61 priority, latest basket trade cut at the same fill); MES T61 + basket <= 8; no shared governor",
           "forward_models": minfo, "historical": {k: BR[k] for k in ("basket_avg_day", "basket_avg_day_2021", "basket_maxdd", "basket_worst", "t61_plus_avg_day", "t61_plus_maxdd",
                                                                     "t61_plus_worst", "t61_plus_ret_dd", "t61_ret_dd", "basket_corr_to_t61")},
           "forward_gate": ">= 250 OOS sessions; basket incremental > 0 and >= +10 $/day; T61+basket ret/DD >= T61 forward ret/DD; MaxDD <= 20k; worst >= -5k; no retuning",
           "forward_runner": "NOT YET BUILT: member generators + frozen models are packaged; a forward-shadow integration into shadow/forward_shadow.py is a pending task",
           "hash_index_sha256": sha(os.path.join(FZ, "HASH_INDEX.csv")), "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(man, open(os.path.join(FZ, "MANIFEST.json"), "w"), indent=1, default=str)
    open(os.path.join(FZ, "MANIFEST.sha256"), "w").write(sha(os.path.join(FZ, "MANIFEST.json")) + "  MANIFEST.json\n")
    st = {"T61_R1C_FROZEN": "YES", "T61_OOS_START": "2026-09-29", "T61_OOS_USED": "NO",
          # Lane A
          "PRESS1_RESULT": "FAIL (0/18 cells): marginal extra MNQ unit is positive (best F_PURE_PROFIT +23.6 $/trade, +7.4 $/day, 4/5 folds) BUT waiting for market proof LOSES "
                           "to frontloading the same unit at campaign entry (-22.7 $/day) and adds ~0 vs random timing -> no timing value; value = extra exposure to the T61 campaign",
          "BEST_SPONSOR_BASE": "C43-derived campaigns: highest overlay EV per trade (A_NEW_HIGH: C43 +44, MIXED +29, TEST53 +15 $/trade; attribution only, not selected)",
          "BEST_PRESS1_TRIGGER": f"{best.trigger} (MNQ, non-passing)", "PRESS1_EVENTS": int(best.events), "PRESS1_TRADES_PER_DAY": round(best.trades_per_day, 3),
          "PRESS1_MARGINAL_AVG_DAY": round(best.marginal_avg_day, 2), "PRESS1_MARGINAL_EV_PER_TRADE": round(best.marginal_ev_trade, 2), "PRESS1_FOLDS_POS": int(best.folds_pos),
          "PRESS1_REMOVE_TOP3": round(best.remove_top3), "PRESS1_SLIP4_DAY": round(best.slip4_day, 2), "PRESS1_FRONTLOAD_EXCESS": round(best.frontload_excess_day, 2),
          "PRESS1_MATCHED_TIMING_EXCESS": f"random-timing {best.random_timing_excess_day:+.2f} / matched-long {best.matched_excess_day:+.2f} $/day",
          "PRESS1_CORR_TO_T61": round(best.corr_to_t61, 3), "PRESS1_INCREMENTAL_MAXDD": round(best.incr_maxdd), "PRESS1_INCREMENTAL_WORST_DAY": round(best.incr_worst),
          "PRESS1_CAP_BLOCK_RATE": round(best.cap_block_rate, 3), "PRESS1_UNCONSTRAINED_AVG_DAY": round(best.unconstrained_avg_day, 2),
          "PRESS1_EV_IF_CAMPAIGN_WINS / LOSES": f"{best.EV_if_campaign_wins:+.1f} / {best.EV_if_campaign_loses:+.1f} $/trade (labels only)",
          "PRESS1_PASS": "NO", "PRESS2_RUN": "NO", "PRESS_ML": "NO (timing value absent)", "PRESS_GA": "NO",
          # Lane B
          "FIXED_CLUE_BASKET_MEMBERS": BR["FIXED_CLUE_BASKET_MEMBERS"], "BASKET_STANDALONE_AVG_DAY": round(BR["basket_avg_day"], 2), "BASKET_STANDALONE_AVG_DAY_2021": round(BR["basket_avg_day_2021"], 2),
          "BASKET_FOLDS_POS": BR["basket_folds_pos"], "BASKET_CORR_TO_T61": round(BR["basket_corr_to_t61"], 3), "BASKET_LOSS_JACCARD": round(BR["loss_day_jaccard"], 3),
          "T61_PLUS_BASKET_AVG_DAY": round(BR["t61_plus_avg_day"], 2), "T61_PLUS_BASKET_INCREMENTAL_DAY": round(BR["t61_plus_incr_day"], 2),
          "T61_PLUS_BASKET_MAXDD": round(BR["t61_plus_maxdd"]), "T61_PLUS_BASKET_WORST_DAY": round(BR["t61_plus_worst"]), "T61_PLUS_BASKET_RET_DD": round(BR["t61_plus_ret_dd"], 5),
          "T61_PLUS_BASKET_MARGIN": f"{BR['peak_margin_pct_t61_plus']:.1f}% NLV (T61 {BR['peak_margin_pct_t61']:.1f}%)", "T61_PLUS_BASKET_SLIP4": round(BR["t61_plus_slip4_incr_day"], 2),
          "FIXED_CLUE_BASKET_PASS": "YES (preregistered historical gate) - FORWARD SHADOW CANDIDATE ONLY",
          "BASKET_CAVEATS": ["members selected after their individual results were known (selection bias across ~3,300 prior hypotheses)",
                             "recent-year concentration: 2025-26 ~ 72% of basket P&L; 2024 -3.3 $/day; 2019 -15.9 $/day; max-year-share check passed narrowly (~0.47)",
                             "T61+basket MaxDD +10.5% (13,936 vs 12,607); worst day -4,666 vs -4,347",
                             "robustness (report-only): +1 min delay +16.9 $/day, 20% missed +14.3 $/day, remove-top5 total +16.3k of 31.6k"],
          "FINAL_SELECTION": "FIXED CLUE BASKET ONLY (forward shadow); PRESS1 none", "BASKET_OOS_START": oos,
          "BASKET_FREEZE_MANIFEST_SHA256": sha(os.path.join(FZ, "MANIFEST.json")), "PROFILE_NQ_RESEARCH": "DATA-LIMITED",
          "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(st, open(os.path.join(PW, "TEST94_PLUS_FINAL_STATUS.json"), "w"), indent=1, default=str)
    reg = lambda n, rows, key: (lambda p: pd.concat([pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(), pd.DataFrame(rows)]).drop_duplicates(key, keep="last").to_csv(p, index=False))(os.path.join(PW, f"{n}.csv"))
    reg("PRESS_BASKET_RESEARCH_REGISTRY", [{"test": "TEST94A_PRESS1", "result": st["PRESS1_RESULT"]}, {"test": "TEST94B_FIXED_CLUE_BASKET", "result": st["FIXED_CLUE_BASKET_PASS"]}], "test")
    reg("PRESS_BASKET_SURVIVOR_LIBRARY", [{"module": "T61_PLUS_FIXED_CLUE_BASKET_V1", "status": "FORWARD_SHADOW_CANDIDATE", "oos_start": oos, "manifest": st["BASKET_FREEZE_MANIFEST_SHA256"]}], "module")
    reg("PRESS_BASKET_REJECT_REGISTRY", [{"family": "PRESS1 on validated T61 campaign (6 triggers x MNQ/MES/cross)", "reason": "no timing value vs frontload / random; PRESS2 not run"}], "family")
    A.reg_append("PROFILE_T61_FRONTIER", [{"test": "TEST94B", "module": "FIXED_CLUE_BASKET_V1", "incr_avg_day": BR["t61_plus_incr_day"], "comb_avg_day": BR["t61_plus_avg_day"],
                                          "comb_maxdd": BR["t61_plus_maxdd"], "comb_worst": BR["t61_plus_worst"], "comb_ret_dd": BR["t61_plus_ret_dd"], "corr": BR["basket_corr_to_t61"],
                                          "SURVIVOR": "FORWARD_SHADOW_CANDIDATE"}], key="module")
    A.md("../PRESS_BASKET_LAB_FINAL_REPORT.md", "TEST94+ VALIDATED-WINNER PRESS + FIXED CLUE-BASKET - final report", ["```json\n" + json.dumps(st, indent=1, default=str) + "\n```"])
    print(json.dumps(st, indent=1, default=str))


if __name__ == "__main__":
    main()
