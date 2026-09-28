"""TEST95+ final: Market Key state-transition diagnostic (descriptive only, no trading claim), Track A stopping decision, Track B / C blocker
statuses, final status JSON + report.  Research data <= 2026-05-27; NEW_OOS_OPENED = NO; LIVE_AUTHORIZATION = NO."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import t95_common as T  # noqa: E402
import t95_liv as V  # noqa: E402

NAMES = ["UT", "NRE", "NRA", "DT"]


def transitions(I):
    a20 = V.atr20(I); Hd, Ld = I.H[:, :T.J15 + 1].max(1), I.L[:, :T.J15 + 1].min(1)
    st = V.market_key(Hd, Ld, 2.0 * a20); col = st[0]
    mk = I.FPb[:, T.J15]; fwd = (np.r_[mk[1:], np.nan] - mk) / a20; fwd5 = (np.r_[mk[5:], [np.nan] * 5] - mk) / a20
    ok = I.full & ~np.isnan(fwd) & ~np.isnan(mk)
    prev = np.r_[-1, col[:-1]]
    rows = []
    for key, m in [("ALL", ok)] + [(f"in_{NAMES[c]}", ok & (col == c)) for c in range(4)] + \
                  [(f"{NAMES[a]}->{NAMES[b]}", ok & (prev == a) & (col == b)) for a in range(4) for b in range(4) if a != b]:
        x = fwd[m]; x5 = fwd5[m & ~np.isnan(fwd5)]
        if len(x) >= 5:
            rows.append({"instrument": I.name, "state": key, "n": int(len(x)), "fwd1_atr": float(x.mean()), "t1": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))),
                         "fwd5_atr": float(x5.mean()) if len(x5) else np.nan, "up1_share": float((x > 0).mean())})
    return pd.DataFrame(rows)


def main():
    Is = B.load()
    TR = pd.concat([transitions(Is[k]) for k in ("ES", "MNQ")]); TR.to_csv(os.path.join(T.CL, "MKEY_STATE_TRANSITIONS.csv"), index=False)
    tom = pd.read_csv(os.path.join(T.CL, "TOM", "TOM_RESULTS.csv")); liv = pd.read_csv(os.path.join(T.CL, "LIVERMORE", "LIV_RESULTS.csv"))
    U = pd.read_csv(os.path.join(T.CL, "LIVERMORE", "L5_UNITS.csv"))
    allr = pd.concat([tom, liv], ignore_index=True)
    pre = open(os.path.join(T.CL, "TEST95_PLUS_PREREGISTRATION.json.sha256")).read().strip()
    st = {
        "PREREGISTRATION_SHA256": pre, "RESEARCH_DATA_END": "2026-05-27", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO",
        "CURRENT_MAIN": "MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged)",
        "TRACK_A": {
            "families_tested": ["T1_HTF_LTF (ENGULF / RESUME / BREAK)", "T2_PREMARKET59 (T2A / T2B) vs C_ORB", "L1-L4 daily Market Key (L2 / L2B / L3, state exit vs fixed holds)",
                                "L3 intraday 5m Market Key [HYP]", "L5 staged accumulation"],
            "cells": int(len(allr)), "standalone_pass": int(allr.STANDALONE_PASS.sum()), "portfolio_pass": int(allr.PORTFOLIO_PASS.sum()),
            "best_net_cell": allr.sort_values("avg_day").iloc[-1][["module", "avg_day", "trades", "matched_A_day"]].to_dict(),
            "T3_WINNER_PRESS": "NOT RUN - no T1 / T2 base passed (prereg condition)",
            "L5_ADD1": {r.module: round(float(r.usd_per_trade), 1) for r in U[U.unit == 2].itertuples()},
            "L5_verdict": "ES ADD1 <= 0 on L3 -> ladder stops (prereg); MNQ / L2 ADD1 > 0 but n = 2-9 units -> not estimable",
            "ML_GA": "NOT RUN - no deterministic family with positive net AND positive matched excess AND the minimum sample (only L2_MKEY_MNQ: +7.1/day, "
                     "matched +5.7/day but 15 trades vs >= 150 floor); ML on 15 events is not estimable",
            "STOP_REASON": ">= 4 distinct canonical families failed without a new clue (prereg stopping rule)",
            "CANONICAL_SURVIVOR": "NONE"},
        "TRACK_B": {
            "INDEX6_PARITY_STATUS": {"LC02": "BLOCKED (precision 0.978 < threshold)", "LC03": "BLOCKED (recall 0.970, price parity 0.771)",
                                     "LC05": "BLOCKED (needs canonical NQ volume; NQ transfer blocked)", "TS16-S01": "STRUCTURALLY EXCLUDED (OI unavailable; amendment)",
                                     "TS22-S01": "BLOCKED (ledger / TradingView parity export not recovered)", "T30-W01": "BLOCKED (needs YM / RTY + exact W01 selector)"},
            "RECOVERED_EXACT": [], "RESEARCH_ONLY_APPROX": ["LC02", "LC03 (TEST46 sanitized ledgers, not authorizing)"],
            "BLOCKED": ["LC05", "TS22-S01", "T30-W01"],
            "TEST20_L2_ONLY": "BLOCKED - semantics live in Google Docs dated after 2026-05-27 (sealed-window risk; not read)",
            "T20_V1_TS20_E01A": "BLOCKED - same reason; Pine source located (metadata only)",
            "INDEX5_NOOI_RECOVERED": "NO", "INDEX6_CURRENT_MAIN_COMBINATION_TESTED": "NO", "INDEX5_CURRENT_MAIN_COMBINATION_TESTED": "NO",
            "B0-B5_candidates": "only B0 (MAIN) evaluable; B1-B5 NOT TESTED (no exact member ledgers)", "INDEX_PORTFOLIO_PROMOTABLE": "NO"},
        "TRACK_C": {
            "C0_YM_DATA": "BLOCKED - canonical_1m_YM.parquet exists (manifest SHA edde4419...) as 6 x 7.5 MB Drive chunks; every chunk download fails "
                          "('MCP server Google_Drive session expired', retried after reconnect this session); RTY identical",
            "C0_REQUIRED_USER_ACTION": "re-split YM / RTY / NQ parquet into <= 1 MB chunks (exact bytes) with a SPLIT_MANIFEST (sha256 per chunk + whole file)",
            "C1_LEGACY_YM (TS13-S01 / TS21-S01)": "NOT RECOVERED - no YM data", "C2-C5": "NOT RUN", "YM_DIVERSIFIER_FOUND": "NO"}}
    json.dump(st, open(os.path.join(T.CL, "TEST95_PLUS_FINAL_STATUS.json"), "w"), indent=1, default=str)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "matched_A_day", "momentum_B_day", "folds_pos", "slip4_day", "plateau_pass", "corr_to_main",
            "main_plus_ret_dd", "main_ret_dd", "STANDALONE_PASS", "PORTFOLIO_PASS"]
    T.md("TEST95_PLUS_FINAL_REPORT.md", "TEST95+ canonical momentum / trend / breakout + INDEX6 integration - final", [
        "Prereg sha256 `" + pre + "`.  Baseline MAIN_GROWTH_V1 (frozen, unmodified).  Research data <= 2026-05-27.  NEW_OOS_OPENED = NO, LIVE_AUTHORIZATION = NO.",
        "## Track A - all preregistered cells", allr[cols],
        "## L5 per-unit ledger", U,
        "## Market Key state-transition diagnostic (daily, R = 2 ATR20; forward 16:15 -> 16:15 return in ATR; descriptive only)", TR,
        "## Status", "```json\n" + json.dumps(st, indent=1, default=str) + "\n```"])
    print(json.dumps(st, indent=1, default=str)); print(TR.to_string())


if __name__ == "__main__":
    main()
