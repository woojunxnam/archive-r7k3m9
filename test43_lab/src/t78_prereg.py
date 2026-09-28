"""TEST78+ BOX-MOMENTUM INVERSION LAB - program preregistration (written before any upper-state statistic).  Discovery clue (TEST70 top-hold study) is
DISCOVERY evidence only; every economic number below is new."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402

GEOS = {"C_PRIORCLOSE_K0.75": "prior-close ATR box", "H_BAL6": "balance / congestion box", "A_OBS30_LIFE60": "fixed-window box", "F_QMAD_W60": "robust quantile box"}
EVENTS = {
    "Z70": "first close with 0.70 <= BOX_POS < 0.85 (diagnostic zone)",
    "A1_TOUCH": "first 1m bar whose HIGH reaches BOX_POS >= 0.85 (decision at that bar's close)",
    "A2_CLOSE": "first 1m close with BOX_POS >= 0.85 (upper zone or beyond)",
    "A3_TWO_CLOSES": "first second consecutive 1m close with BOX_POS >= 0.85",
    "A4_RISING": "A2_CLOSE in a box whose causal direction is RISING (mid > previous box mid + 0.25 x previous width)",
    "BRK0": "first close > upper", "BRK10 (base break)": "first close > upper + 0.10 w", "BRK20": "first close > upper + 0.20 w",
    "U4_RETEST": "after BRK10: first later bar with LOW <= upper + 0.10 w (pullback to the old top) and no close < upper - 0.25 w since the break; "
                 "entry at the first close >= upper after that pullback (reclaim), before 16:00",
    "SEQ2": "A2_CLOSE in a box that is RISING and whose previous box was also RISING (two consecutive higher midpoints)",
}
SPEC = {
    "program": "TEST78+ BOX-MOMENTUM INVERSION LAB", "research_data_end": "2026-05-27", "T61": "frozen, untouched; no forward OOS used",
    "rejected_not_reopened": ["bottom buy / top sell", "range recycling", "lower-box mean reversion", "generic box migration", "nested bottom confluence"],
    "geometries": GEOS, "geometry_note": "restricted discovery-safe set; boxes exactly as TEST70 (causal, never repainted); ES and MNQ separately",
    "events": EVENTS, "one_event_per_type_per_box": True,
    "clock": "decision = close of 1m bar j; entry = open of j+1; exit fills FPb; costs 0.62 + 1 tick per side (SLIP4 = 4 ticks); 1 contract",
    "horizons": ["+5m", "+15m", "+30m", "+60m", "+120m", "16:00", "16:15", "next open"],
    "controls": {"MATCHED_LONG": "same instrument, year, vol tercile, HTF-bull group; same entry / exit minute; same costs",
                 "MOMENTUM_NULL (critical)": "same instrument, year, vol tercile, HTF-bull, same entry / exit minute AND same session-return bucket at the "
                                             "entry minute: (close - RTH open) / ATR_d in (-inf,-0.5], (-0.5,-0.2], (-0.2,0], (0,0.2], (0.2,0.5], (0.5,inf); "
                                             "no box information; BOX_VS_GENERIC_MOMENTUM_EXCESS = event net - momentum-null net"},
    "conditioning": {"direction": "RISING / FLAT / FALLING (previous box of the same geometry; threshold 0.25 previous widths)",
                     "velocity": "(mid - mid 2 boxes earlier) / ATR_d / elapsed hours: NEGATIVE < -0.05, NEAR_ZERO [-0.05, 0.05], POSITIVE (0.05, 0.25], STRONG > 0.25",
                     "width": "CONTRACTING < 0.8 x previous width, EXPANDING > 1.25x, else STABLE"},
    "TEST78_qualification": "an (event type x instrument x horizon) cell QUALIFIES iff pooled over the 4 geometries: net per event > 0, SLIP4 net per event > 0, "
                            "MOMENTUM_NULL excess per event > 0 in >= 4/5 outer folds and overall, MATCHED_LONG excess > 0, >= 300 events 2019-07+",
    "TEST79_80_81_82": "strategy tests (first valid event per session per geometry, 1 contract, one position, hold to the preregistered horizon) ONLY for "
                       "qualifying mechanisms: TEST79 = upper-state (A1-A4, SEQ2), TEST80 = break hold policy (BRK), TEST81 = old-top retest (U4), "
                       "TEST82 = rising sequence (A4, SEQ2); horizon = the qualifying structural horizon in {30m, 60m, 16:00, 16:15} with the largest "
                       "fold-median momentum excess; next open only if RTH horizons qualify",
    "plateau": {"upper_zone_threshold": [0.80, 0.90], "break_buffer": [0.0, 0.20], "direction_threshold": [0.15, 0.35],
                "hold_horizon": "adjacent structural horizons", "geometry": "the other 3 geometries (information must generalise)",
                "definition": "all neighbours net > 0 and >= 60% of base, momentum excess > 0 in >= 75% of neighbours"},
    "gate": ["momentum-null excess > 0 (box adds information)", "matched-long excess > 0", ">= 4/5 folds net > 0", "remove-top3 > 0", "SLIP4 > 0",
             "+1 bar delay > 0", "20% missed entries > 0", "max year share <= 50%", "plateau PASS", ">= 300 trades, >= 40 per fold"],
    "TEST83": "T61 overlay only if a standalone module passes: 0/+1 contract, residual capacity only (MNQ: 6 - T61 MNQ; MES: 8 - T61 MES, module <= 1), "
              "never trims T61; TEST65 incremental gate + MINIMUM MEANINGFUL INCREMENT >= 10 $/day (2019-07+ and 2021+) and combined ret/DD >= T61",
    "ML_GA": "ML only if simple events qualify (economic target, causality audit first); GA only if deterministic economics clearly positive",
    "stopping": "A survivor frozen / B touch, acceptance, break, retest, rising-sequence all fail / C value explained by generic momentum",
    "prior_budget": {"hypotheses": 1542, "ml_configs": 207, "genomes": 777629},
}

if __name__ == "__main__":
    d = os.path.join(B.BOX, "TEST78"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "TEST78_PLUS_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
