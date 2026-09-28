"""TEST48 preregistration: DELAYED CONFIRMATION / ARM-ONLY ENTRY.  Written and hashed BEFORE any TEST48 economics."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Is the FIRST signal useful mainly as an ARM state, while a later independent confirmation contains the entry alpha?",
    "why_mechanism_could_exist": "Early signals mark a state change (selling pressure, breakout attempt, compression) but also catch continuation against the "
                                 "position; waiting for a second, independent piece of evidence filters out the continuation cases (TEST47: second-contract "
                                 "selection after a later confirmed bottom had rank-IC 0.09, the initial entry lost).",
    "prior_result_motivating_it": "C47_MLC_SECOND_CONTRACT clue; TEST46/47 immediate entries all negative.",
    "difference_from_failed_families": "Failed families entered AT the first event or on a same-event reclaim. TEST48 never enters at the arm; entry requires a "
                                       "LATER event of a different kind within a bounded window, and continuation-type arms (ORB, pullback-in-uptrend, compression) "
                                       "are included, not only rebounds.",
    "falsification": "No setup x confirmation has positive matched excess with >= 4/5 positive outer folds AND delayed - immediate > 0, or the only positive "
                     "combos do not survive the multiple-testing threshold (t >= 3.0 across the 5x6x3x2 grid) / nested GA outer generalisation.",
    "setups": {"S1_N3": "TEST47 C2 event (T1 default N3, frozen)", "S2_PDL_BREAK": "first 5m low < prior-day RTH low - 0.10 ATRd",
               "S3_UPDAY_PULLBACK": "session high - open >= 0.5 ATRd and high - close >= 0.4 ATRd while close > open (first time)",
               "S4_ORB": "first 5m close above the 30m opening-range high (bar >= 6)",
               "S5_COMPRESSION": "12-bar range <= 4.0 u5 after 10:30 (first time)"},
    "confirmations": {"CF0_IMMEDIATE": "entry after the arm bar (control)",
                      "CF1_LOWER_LOW_RECLAIM": "a later low below the arm-bar low, then a 5m close above the high of the lowest bar",
                      "CF2_HIGHER_LOW_BREAKOUT": "low since arm stays >= arm-bar low and a 5m close exceeds the high made since the arm (>= 2 bars after arm)",
                      "CF3_EXPANSION_BAR": "bullish 5m bar with body >= 1.0 u5 and close location >= 0.7",
                      "CF4_15M_CONFIRM": "completed 15m bar bullish and closing above the previous 15m high",
                      "CF5_OTHER_FAMILY": "a DIFFERENT setup family arms within the window"},
    "window_bars": 12, "entry_timing": "fill at the open of the first 1m bar after the confirming 5m close; last entry fill 15:45",
    "exits": ["X60", "X120", "X1600"], "primary_exit": "X120", "instruments": ["ES->MES", "NQ->MNQ (price only)"], "size": "1 contract, non-overlapping",
    "costs": "0.62 + 1 tick / side; stress 4 ticks",
    "matched_null": "same instrument, fill minute, year, vol tercile, HTF trend, same exit",
    "program_gate": "prog_common.evaluate_module G1..G9 (fixed for the program)",
    "multiple_testing": "grid = 5 setups x 6 confirmations x 3 exits x 2 instruments = 180 simple combos; a simple combo is a finalist only if t(matched excess) >= 3.0 "
                        "AND it passes the program gate. Otherwise the ARM->CONFIRM grammar goes to a nested GA lane (GA-AC) whose stitched outer result must pass.",
    "ga_lane": {"name": "GA-AC", "genes": "setup, setup threshold (x0.5-2), confirmation, window 6/12/24, expansion size, exit, instrument, trend permission (bull 0/1), "
                                          "vol permission (volt max)", "budget": "POP 64, GENS 40, 2 seeds x 3 islands, 6 folds (~75k genomes)",
                "novelty": "|corr C43| <= 0.5 constraint; objective includes -matched excess"},
    "discovery_only_design": "no parameter above was chosen from 2021+ data; thresholds are round values",
}

if __name__ == "__main__":
    print(P.prereg("TEST48", SPEC))
