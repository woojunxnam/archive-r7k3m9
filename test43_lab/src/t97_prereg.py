"""TEST97+ Wave-1 preregistration (event study; written BEFORE any TEST97 economics)."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

OUT = os.path.join(os.path.abspath(C45.ROOT), "out", "t97")

SPEC = {
    "program": "TEST97+ multi-index momentum burst / breakout / trend-following factory (LONG only)", "research_data_end": "2026-05-27",
    "baseline": "MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (unchanged; PORTFOLIO_MEMBERSHIP_CHANGED = NO)",
    "data": "canonical 1m full contracts ES / NQ / YM / RTY (SHA verified); economics MES / MNQ / MYM / M2K",
    "clock": {"bars": "5m RTH bars b = 0..80 (b covers 1m grid [5b, 5b+5), completed at 09:34+5b ET)",
              "entry": "signal on completed bar b -> long at the OPEN of bar b+1 (grid 5b+5); no buy stops, no intrabar lookahead",
              "horizons": {"bars": [1, 2, 3, 4, 6, 9, 12], "exit": "open of bar b+1+h (grid 5(b+1+h))", "absolute": ["16:00 (grid J1600)", "16:15 (grid J1615)"],
                           "next_open": "CLOSED in Wave 1"},
              "eligibility": "each horizon uses only events whose exit grid <= J1615 (N reported per horizon); the PRIMARY comparison population is the "
                             "COMMON population with signal bar b <= 67 (all bar horizons complete)"},
    "units": {"ATR_d": "ATR14 of prior RTH sessions (return normalisation)", "ATR5": "mean range of the prior 20 completed 5m RTH bars (bar-shape features)",
              "cost": "round trip 2 x (0.62 + 1 tick micro) expressed in ATR_d units per event"},
    "path_stats": ["MFE / MAE over 60 min (1m highs / lows, ATR_d)", "time to MFE", "barrier races +-0.25 / +-0.50 / +-1.00 ATR_d to 16:14 (same-minute tie = loss)",
                   "new-high probability within 60 min (> signal bar high)", "underwater at 16:15", "time to first positive net", "time to recover entry after MAE"],
    "nulls": {"A_TIME_REGIME": "mean forward return of ALL bars in the same cell (year x vol tercile x bull x bar index)",
              "B_MAGNITUDE": "mean forward return of NON-event bars in the same cell (year x 6 time buckets x displacement decile x range tercile); displacement = "
                             "(c5[b] - c5[b-1]) / ATR_d, range = (h5 - l5) / ATR_d",
              "C_BASIC_MOMENTUM": "mean forward return of NON-event bars with close > prior 4-bar high in the same cell (year x 6 time buckets)",
              "family_specific": "listed per family"},
    "inference": "pooled ATR-normalised excess across ES / NQ / YM / RTY with date-clustered bootstrap (500 reps, instruments on the same date form one "
                 "cluster); per-instrument results; year-by-year (chronological folds 2019H2..2026)",
    "EVENT_EDGE_rule": "a family variant has EVENT_EDGE at a horizon iff pooled excess vs its PRIMARY null (A, and B for bar-structure families) > 0 with "
                       "clustered 95% CI lower bound > 0 AND >= 5 of 8 years positive AND pooled mean gross return > round-trip cost; a FAMILY needs a coherent "
                       "(>= 3 adjacent bins same sign) response, not an isolated cell",
    "WAVE1": {
        "M01_STRONG_BULL_BAR": "all bull bars; 1D response curves over body_pct [.5,.6,.7,.8,.9,1], close_position [.7,.8,.9,.95,1], range/ATR5 [.75,1,1.25,1.5,2,inf); "
                               "sparse 2D body x range; canonical STRONG = body_pct >= 0.6 & close_pos >= 0.8 & range >= 1.25 ATR5 (representative, not optimised); "
                               "primary null B (does structure add beyond displacement)",
        "M02_STRONG_BREAKOUT": "canonical STRONG & close > prior N-bar high (5m RTH chain), N in 2,4,6,8,12,20,30,60; family null: STRONG without an N=12 breakout",
        "M03_COMPRESSION_SURPRISE": "surprise burst = bull & range >= 2 x median range of prior 20 bars & close_pos >= 0.8 & close > prior 12-bar high; compression = "
                                    "prior-12-bar high-low / ATR_d in the lowest tercile of its (instrument, bar index) distribution over the prior 60 sessions; "
                                    "family null: same bursts in the middle / top tercile, matched on burst range decile",
        "M04_FOLLOW_THROUGH": "base = M02 N=12; B next bar bull, C next close > breakout close, D two bull follow-through bars, E next bar HH & HL, F next bar also "
                              "STRONG; entry after confirmation; attribution: (i) confirmed vs unconfirmed entered at the SAME minute (information), (ii) "
                              "confirm-entry vs original-entry held to the same exit minute (timing value)",
        "M05_SECOND_LEG": "impulse = M02 N=12 event; pullback = 1-6 bars not exceeding the impulse high; depth buckets 0-25/25-38.2/38.2-50/50-61.8/61.8-75/>75% "
                          "of impulse range; resumption = first bar closing above the prior bar high and bullish; entry next open; family null: holding the impulse "
                          "from its own entry to the same exit minute, and all impulses entered at the same minute",
        "M06_FAILED_FIRST_FRESH_SECOND": "first = M02 N=12 event; failure = a close back below the breakout level within 6 bars; second = next fresh M02 N=12 event "
                                         "the same session after failure; compare second vs first vs null A; outcome classes A-D",
        "M07_MICROCHANNEL": "k = 2 / 3 / 4 consecutive bars each bull, higher low, close in upper half, low >= prior close - 0.1 ATR5; family null: single bars with "
                            "the same cumulative k-bar displacement decile (null B over k-bar displacement)",
        "M08_OPENING_MOMENTUM": "OR = first 1 / 2 / 3 / 6 bars; event = first completed bar before 11:00 closing above OR high; conditioned on STRONG, gap up; "
                                "comparison: first close above the session high after 11:00",
        "M09_HTF_ALIGNMENT": "M02 N=12 events split by (a) above VWAP, (b) above session open, (c) above prior-day high, (d) last completed 60m bar up; incremental = "
                             "aligned minus non-aligned excess (clustered CI)",
        "M10_EXTENSION_CURVE": "STRONG events by distance from VWAP / EMA20 (5m chain) / session open in ATR_d buckets 0-.5/.5-1/1-1.5/1.5-2/>2"},
    "position_management": "NOT in Wave 1; activated only for a family with EVENT_EDGE (single / blind DCA control / fresh-signal recovery / winner pyramid on "
                           "identical initial populations, marginal-unit accounting)",
    "ML_GA": "ML only with >= 600 events, >= 150 pre-fold training events, visible heterogeneity; GA only with a coherent mechanism and >= 3 structural "
             "dimensions; nested chronological",
    "2022_governance": "negative 2022 is an adverse-regime survival test (report matched-beta excess, loss capture), not automatic failure",
    "ledger": "every variant logged in out/t97/TEST97_RESEARCH_LEDGER.csv"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "TEST97_WAVE1_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
