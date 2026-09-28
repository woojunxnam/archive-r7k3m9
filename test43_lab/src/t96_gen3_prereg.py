"""TEST96 Track A2 Generation-3 preregistration (FINAL generation) - after Gen-2, BEFORE any Gen-3 economics."""
import datetime, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import t96_common as W

SPEC = {
    "gen2_analysis": {"clue": "Q2 breadth expansion (<= 1 of 4 indices strong 30 min earlier -> all 4 strong) is positive in all four indices, beats the "
                              "static-breadth null (+5.1 / +13.7 / +1.8 / +0.2 $/trade ES / MNQ / YM / RTY), matched A and momentum B > 0 everywhere",
                      "failures": "preregistered plateau fails (MNQ 40-min lookback 58% of base; ES 48%); 2022 negative in all four; P&L concentrated in 2023 "
                                  "and 2025-26 -> NOT a survivor; not rescued",
                      "others": "Q1 acceleration and Q3 volume expansion: samples 50-270, mostly negative outside MNQ; Q4 catch-up: small / mixed"},
    "GEN3": {
        "R1_ML_Q2_TRADE_SKIP": {"base": "Q2 base events (lookback 30, frozen), 629 sessions; question TRADE/SKIP per index",
                                "features (causal at decision)": ["minute of day", "breadth 10 / 20 min earlier", "per-index return since open / ATR (4)",
                                                                  "per-index last-30m return / ATR (4)", "cross-index dispersion of 30m returns",
                                                                  "relative 30m volume of the traded index", "gap / ATR", "prior-day return / ATR", "vol tercile",
                                                                  "bull flag", "MAIN MNQ-eq exposure (T61) at decision"],
                                "target": "$ net per trade at 16:15 after 1-tick friction", "validation": "chronological outer folds 2021..2025-26, train < fold start "
                                "(min 150 train events), no tuning inside the outer fold",
                                "models": {"PRIMARY": "Ridge (alpha 10, standardised)", "reported": ["ElasticNet", "HistGB", "RF", "ExtraTrees", "XGB", "LightGBM", "CatBoost"]},
                                "rule": "trade if predicted $ > 0", "plateau": "HistGB and ElasticNet decision rules must each be > 0 and >= 60% of the PRIMARY total",
                                "gate": "TEST96 standalone + portfolio / diversifier; must also beat the unfiltered Q2 base per trade"},
        "R2_Q2_OVERNIGHT_INCREMENT [diagnostic]": "next-open minus 16:15 $ per Q2 trade vs the matched overnight control (same year x vol x bull group); reported "
                                                  "only - Q2 is not a survivor so no overnight promotion",
        "R3_DAILY_BREADTH_THRUST [new timescale]": "# of {ES, NQ, YM, RTY} whose 16:15 close is a 20-session closing high goes from <= 1 three sessions earlier "
                                                   "to 4 today -> next session: buy at the 09:31 open, exit 16:15 (and next-open reported); null: 4 of 4 today "
                                                   "with >= 3 three sessions earlier; plateau lookback 2 / 5 sessions; sample floor 60 / 8 per fold"},
    "stop_rule": "Gen-3 is the last generation of the TEST96 factory: after it, families (reaction, acceptance, congestion, acceleration, confirmation, "
                 "breadth, volume participation, catch-up) are declared saturated unless a survivor appears"}

if __name__ == "__main__":
    p = os.path.join(W.OUT, "TEST96_GEN3_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
