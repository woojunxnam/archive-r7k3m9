"""TEST96 Track A2 Generation-2 preregistration - written after Gen-1 results, BEFORE any Gen-2 economics."""
import datetime, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import t96_common as W

SPEC = {
    "gen1_failure_analysis": {
        "F1_sample": "strict multi-condition intraday transitions (G1, G2, G4, G5, G6) produced 23-114 trades per instrument: not testable at the 200 / 25 floor",
        "F2_static_beta": "the large-sample level transition (G3 PDH retest, 300+ trades) is explained by the session-return momentum null (MNQ B = -3.0 $/day) "
                          "and adds ~0 $/trade over the plain PDH break -> static strength again",
        "F3_market": "per-contract YM / RTY edges are small; MNQ carries most of the intraday continuation edge and is already inside MAIN",
        "F4_lookahead_caught": "a first D10 diagnostic entered at the leader break but conditioned on confirmation up to 30 min later (look-ahead); the causal "
                               "version (entry at confirmation vs at break+31 for unconfirmed) is mixed: YM +17, RTY +7, ES +2, MNQ -9 $/trade",
        "clues": ["G5 strong->stronger beats its first-impulse null in ES (+17 $/trade), MNQ (+47), YM (+5); matched A >= 0 in all four",
                  "participation / breadth increase (G5 range expansion, G6 confirmation in YM / RTY) is the common thread of the positive increments"]},
    "GEN2_mechanisms": {
        "Q1_ACCELERATION_30M [clue-follow of G5 family, labelled as such]": "30m checkpoints 10:30..15:00; r_prev = prior 30m return / ATR_d, r_now = last 30m "
            "return / ATR_d; transition r_prev >= 0.10 AND r_now >= 2 x r_prev AND r_now >= 0.20; first per session; hold 16:15; family null: r_now >= 0.20 "
            "without acceleration (first such checkpoint); plateau: r_prev 0.08 / 0.12, ratio 1.75 / 2.25",
        "Q2_BREADTH_EXPANSION [new]": "breadth(t) = # of {ES, NQ, YM, RTY} with close > session open + 0.1 ATR_d AND close = 30m high (within the bar); transition "
            "breadth 30 min earlier <= 1 AND breadth now = 4; 5m decisions 10:00..15:00, first per session, trade each index; null: breadth = 4 now with breadth "
            ">= 3 thirty minutes earlier (static breadth); plateau: lookback 20 / 40 min",
        "Q3_VOLUME_PARTICIPATION_EXPANSION [new; true full-contract volume; MNQ uses its own volume]": "30m relative volume (vs median of the same window over the "
            "prior 20 sessions) < 0.9 in the prior 30m and > 1.3 in the last 30m, close at a new 60m high, last-30m return > 0; 10:30..15:00 5m decisions, "
            "first per session; null: new 60m high & 30m return > 0 with relative volume NOT expanding; plateau: 0.8 / 1.0 and 1.2 / 1.4",
        "Q4_CROSS_INDEX_CATCH_UP [D11]": "leader L 60m return >= 0.4 ATR_d while laggard X 60m return <= 0.1 ATR_d (divergence); transition: X closes at a new 30m "
            "high within 60 min after divergence -> buy X; pairs L=NQ -> X in {ES, YM, RTY} and L in {YM, RTY} -> X = NQ; null: enter X at divergence "
            "(no catch-up); plateau: leader 0.3 / 0.5"},
    "exits": "primary 16:15; 30 / 60 / 120 / 16:00 / next open reported", "gates": "unchanged TEST96 (standalone incl. predeclared plateau, portfolio, diversifier)",
    "cells": "Q1 4 + Q2 4 + Q3 4 + Q4 6 = 18 cells (cumulative program cells ~ 56 + 18)", "stop_rule": "if Gen-2 yields no survivor and no new clue, stop the factory (families saturated)"}

if __name__ == "__main__":
    p = os.path.join(W.OUT, "TEST96_GEN2_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
