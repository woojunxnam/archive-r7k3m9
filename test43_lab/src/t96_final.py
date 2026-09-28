"""TEST96+ final status: Track D required outputs (D17), Track A2 factory summary, Track B statuses (B15), Track C (YM legacy).  No new economics."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t96_common as W  # noqa: E402


def J(n):
    p = os.path.join(W.OUT, n)
    return json.load(open(p)) if os.path.exists(p) else {}


def row(R, m):
    r = R[R.module.str.split(" ").str[0] == m]
    return r.iloc[0] if len(r) else None


def verdict(r):
    if r is None:
        return "NOT RUN"
    tag = "PASS_STANDALONE" if r.STANDALONE_PASS else "FAIL"
    return f"{tag} (avg {r.avg_day:+.2f} $/day @1 micro, A {r.matched_A_day:+.2f}, B {r.momentum_B_day if r.momentum_B_day == r.momentum_B_day else float('nan'):+.2f}, folds {int(r.folds_pos)}/5, n {int(r.trades)}; portfolio {'PASS' if r.PORTFOLIO_PASS else 'FAIL'}, diversifier {'PASS' if r.DIVERSIFIER_PASS else 'FAIL'})"


def main():
    S = pd.read_csv(os.path.join(W.OUT, "PORT_STAGE_A.csv")); M = pd.read_csv(os.path.join(W.OUT, "PORT_T66_ML.csv")); P = J("T96_D_PORTFOLIOS.json")
    tb = {r["portfolio"]: r for r in P.get("table", [])}
    out = {"PREREG": {"TEST96": open(os.path.join(W.OUT, "TEST96_PREREGISTRATION.json.sha256")).read().strip(),
                      "GEN2": open(os.path.join(W.OUT, "TEST96_GEN2_PREREGISTRATION.json.sha256")).read().strip(),
                      "GEN3": open(os.path.join(W.OUT, "TEST96_GEN3_PREREGISTRATION.json.sha256")).read().strip(),
                      "B": open(os.path.join(W.OUT, "TEST96_B_PREREGISTRATION.json.sha256")).read().strip()},
           "DATA": {"NQ_SHA256_MATCH": "YES", "YM_SHA256_MATCH": "YES", "RTY_SHA256_MATCH": "YES", "RESEARCH_DATA_END": "2026-05-27"},
           "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO", "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged)"}
    D = {"C43_PORTABLE_TO_YM": "NO (8 transferred V6 sleeves: excess vs exposure-matched long < 0; at source C43 is itself mostly managed beta)",
         "C43_PORTABLE_TO_RTY": "NO (sum of 8 sleeves net negative)"}
    for m in ("M1", "M2", "M3", "M4"):
        for x in ("YM", "RTY"):
            D[f"T53_{m}_{x}"] = verdict(row(S, f"T53_{m}_{x}"))
    for k, key in (("T68", "T68"), ("T67", "T67"), ("PG12", "PG12")):
        for x in ("YM", "RTY"):
            D[f"{k}_{x}"] = verdict(row(S, f"{key}_{x}"))
    for x in ("YM", "RTY"):
        D[f"T66_{x}_ML"] = verdict(row(M, f"T66_ML_{x}"))
    D["BEST_YM_TRANSFER"] = "T68_YM (secondary session-high breakout; +1.52 $/day per MYM, A +1.59, B +0.98, 4/5 folds) - standalone pass, no portfolio / diversifier pass"
    D["BEST_RTY_TRANSFER"] = "none passes; closest T53_M2_RTY (+1.85 $/day per M2K, fails momentum-null B -0.24)"
    ym = P.get("FIXED_YM_TRANSFER_BUNDLE", {}); rty = P.get("FIXED_RTY_TRANSFER_BUNDLE", {})
    D["FIXED_YM_TRANSFER_BUNDLE"] = ym; D["FIXED_RTY_TRANSFER_BUNDLE"] = rty
    D["YM_TRANSFER_AVG_DAY"] = tb.get("P1_MAIN+YM", {}).get("incr_avg_day"); D["RTY_TRANSFER_AVG_DAY"] = tb.get("P2_MAIN+RTY", {}).get("incr_avg_day")
    D["YM_CORR_TO_MAIN"] = tb.get("P1_MAIN+YM", {}).get("corr_add_to_main"); D["RTY_CORR_TO_MAIN"] = "n/a (empty bundle)"
    D["MAIN_PLUS_YM_AVG_DAY"] = tb.get("P1_MAIN+YM", {}).get("avg_day"); D["MAIN_PLUS_RTY_AVG_DAY"] = tb.get("P2_MAIN+RTY", {}).get("avg_day")
    D["MAIN_PLUS_YM_RTY_AVG_DAY"] = tb.get("P3_MAIN+YM+RTY", {}).get("avg_day"); D["MAIN_PLUS_YM_RTY_MAXDD"] = tb.get("P3_MAIN+YM+RTY", {}).get("max_dd")
    D["MAIN_PLUS_YM_RTY_WORST_DAY"] = tb.get("P3_MAIN+YM+RTY", {}).get("worst_day"); D["MAIN_PLUS_YM_RTY_RET_DD"] = tb.get("P3_MAIN+YM+RTY", {}).get("ret_dd")
    D["MAIN_RET_DD"] = tb.get("P0_CURRENT_MAIN", {}).get("ret_dd"); D["MAIN_MAXDD"] = tb.get("P0_CURRENT_MAIN", {}).get("max_dd")
    D["NEW_YM_SURVIVOR"] = "NO"; D["NEW_RTY_SURVIVOR"] = "NO"; D["PORTFOLIO_EXPANSION_SURVIVOR"] = "NO"
    D["D10_D11"] = "causal confirmation value mixed (YM +17, RTY +7, ES +2, MNQ -9 $/trade; n 36-69); an initial non-causal version was caught and discarded"
    out["TRACK_D"] = D
    G1, G2, G3 = (pd.read_csv(os.path.join(W.OUT, f)) for f in ("GEN1_RESULTS.csv", "GEN2_RESULTS.csv", "GEN3_RESULTS.csv"))
    out["TRACK_A2"] = {"generations": 3, "cells": int(len(G1) + len(G2) + len(G3)), "standalone_pass": int(G1.STANDALONE_PASS.sum() + G2.STANDALONE_PASS.sum() + G3.STANDALONE_PASS.sum()),
                       "strongest_clue": "BREADTH EXPANSION (4-index weak -> full breadth within 30 min): positive in all four indices vs static-breadth null; MNQ "
                                         "+8.8 $/day, A +7.4, B +2.8, 4/5 folds; FAILS plateau (58% < 60%) and is 2022-negative / 2023 + 2025-26 concentrated; "
                                         "Ridge TRADE/SKIP filter lifts $/trade in all four indices (MNQ 88 vs 39) but only 139-147 trades (sample gate)",
                       "saturated_families": ["reaction-resumption", "next-day reaction", "level acceptance", "multi-session congestion", "acceleration",
                                              "broad confirmation", "breadth expansion", "volume participation", "cross-index catch-up", "daily breadth thrust"],
                       "ML": "run on the Q2 base (629 events) per prereg; GA not run (no coherent passing mechanism with >= 600 events and >= 3 structural dims)",
                       "STOP_REASON": "Gen-3 was the preregistered last generation; no survivor; families saturated",
                       "fragility_finding": "frozen T66 ML member of FIXED_CLUE_BASKET_V1 is threshold-fragile (8 extra training sessions flip 81 / 231 signals, "
                                            "+1.96 -> -0.37 $/day) - basket NOT modified; flagged for forward shadow review"}
    out["TRACK_B"] = {**J("T96_B_STATUS.json")}
    out["TRACK_C"] = J("T96_C1_LEGACY_YM.json") | {"TS13_PARITY": J("T96_C1_TS13_PARITY.json")}
    W.save("TEST96_PLUS_FINAL_STATUS.json", out)
    W.md("TEST96_PLUS_FINAL_REPORT.md", "TEST96+ - data unblocked, thesis-expansion factory, Track D portability, Track B resume", ["```json\n" + json.dumps(out, indent=1, default=str) + "\n```"])
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
