"""TEST70+ ADAPTIVE BOX / RANGE-LADDER ALPHA LAB - program-wide preregistration (written BEFORE any box statistic is computed).
Fixes geometries, zones, event definitions, economic ranking, matched control, plateau neighbours, sample minimums, gates, the minimum
meaningful T61 increment and the ML / GA justification rules for TEST70..TEST77."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

LAB = os.path.abspath(C45.ROOT); BOX = os.path.join(LAB, "out", "ADAPTIVE_BOX_LAB")

# --------------------------------------------------------------------------- geometry grid (TEST70 atlas), per instrument (MNQ, ES separately)
GEOMETRIES = {
    # A: previous fixed window -> next life (clock tiles; box k observes the obs minutes before its birth; next box born at the previous box's death)
    **{f"A_OBS{o}_LIFE{l}": {"family": "A_FIXED_WINDOW", "obs": o, "life": l} for o, l in ((10, 30), (15, 30), (15, 60), (30, 60), (30, 120), (60, 120))},
    # B: frozen rolling extrema of the last N completed 5m bars; box lives until a confirmed break (5m close outside) then a new box is frozen at that bar
    **{f"B_ROLL{n}": {"family": "B_FROZEN_ROLLING", "nbars5": n} for n in (3, 6, 12, 24)},
    # C: ATR-anchored static session box: centre +/- K * vol
    **{f"C_{a}_K{k}": {"family": "C_ATR_ANCHOR", "anchor": a, "K": k} for a in ("OPEN", "PRIORCLOSE", "MID30") for k in (0.5, 0.75, 1.0, 1.5)},
    # D: confirmed 5m swing box (pivot needs p completed bars on each side; box born when the confirming bar completes)
    **{f"D_SWING{p}": {"family": "D_SWING", "p": p} for p in (2, 3)},
    # E: opening / session structure (static)
    **{f"E_{g}": {"family": "E_SESSION", "geom": g} for g in ("OR5", "OR15", "OR30", "PREV_HL", "PREV_BODY", "PREV_MID25")},
    # F: robust quantile boxes on completed windows (tiles like A with life = obs)
    **{f"F_Q{q}_W{w}": {"family": "F_QUANTILE", "q": q, "obs": w, "life": w} for q in ("10_90", "20_80", "MAD") for w in (30, 60)},
    # G: VWAP geometry only (frozen at birth; every 30 minutes): session VWAP +/- m * ATR_d
    **{f"G_VWAP_M{m}": {"family": "G_VWAP_GEOM", "m": m, "life": 30} for m in (0.15, 0.25)},
    # H: congestion / balance box on 5m bars (N-bar window)
    **{f"H_BAL{n}": {"family": "H_BALANCE", "nbars5": n} for n in (6, 12)},
    # I: range-packing: smallest interval containing f of the last N 1m closes (tiles, life = N)
    **{f"I_PACK{int(f * 100)}_N{n}": {"family": "I_PACKING", "frac": f, "obs": n, "life": n} for f in (0.7, 0.8) for n in (30, 60)},
}
DEFINITIONS = {
    "C_vol": "OPEN / PRIORCLOSE anchors: vol = 0.25 * prior-session ATR_d (hourly-scale); MID30 anchor: vol = completed 09:30-10:00 high-low range / 2; box = centre +/- K*vol",
    "E_geom": "OR5/OR15/OR30 = high/low of the first 5/15/30 minutes (born after the window); PREV_HL = prior RTH high/low; PREV_BODY = prior RTH open/close "
              "(min/max); PREV_MID25 = prior RTH midpoint +/- 0.25 x prior RTH range",
    "F_quantiles": "10_90 / 20_80 percentiles of the window's 1m closes; MAD = median +/- 2 x 1.4826 x MAD of 1m closes",
    "G": "session VWAP (1m typical price x volume, cumulative from 09:30) frozen every 30 min +/- m x ATR_d; VWAP is geometry only",
    "H_balance": "window of N completed 5m bars: efficiency |c_last - o_first| / sum(bar ranges) <= 0.30, >= 70% of consecutive bar pairs overlap, window "
                 "range <= 0.40 x ATR_d, >= 2 crossings of the window midpoint by 5m closes; box = window high/low; lives until a confirmed break, "
                 "then a new balance must be detected",
    "D_swing": "pivot high/low on 5m bars with p bars each side (confirmed when the p-th right bar completes); box = last confirmed swing low / swing high "
               "(requires low < high); replaced when a new swing confirms",
    "B_break": "confirmed break = 5m close above upper / below lower; a new box (last N completed 5m bars) is frozen at that bar close",
    "RTH_only": "all boxes live inside one RTH session; prior-session inputs only for C/E; no box persists overnight in TEST70-TEST75",
}
CLOCK = {"decision": "close of 1m bar j (END-stamped); box used at decision j must have birth <= j (built from bars < birth)", "fill": "open of bar j+1 (FP)",
         "exit fill": "FPb at the open of the minute after the exit decision", "costs": "commission 0.62 + 1 tick per side (MNQ 1.12 $, MES 1.87 $); SLIP4 = 4 ticks",
         "instruments": "MNQ 1 contract (2 $/pt) and MES 1 contract (5 $/pt) evaluated independently"}
ZONES = {"BOX_POS": "(close - lower) / (upper - lower)", "study_zones": [[0, .15], [.15, .30], [.30, .50], [.50, .70], [.70, .85], [.85, 1.0]],
         "coarse_levels": [0, .25, .5, .75, 1.0], "fib_diagnostic": [0, .382, .5, .618, 1.0], "LOWER_ZONE_base": 0.15, "UPPER_ZONE_base": 0.85}
EVENT = {"bottom_touch": "first 1m close with 0 <= BOX_POS <= LOWER_ZONE during the box life (one per box in the atlas)",
         "bottom_trade (PRIMARY ECONOMIC METRIC)": "buy at the next open; exit at the next open after the first close with BOX_POS >= UPPER_ZONE (TOP) or the first "
                                                  "close below lower (LOWER BREAK = invalidation), else 16:15; levels frozen at entry (never repainted)",
         "horizons": "+15, +30, +60, +120 min, 16:00, 16:15, next 09:31 open (net of costs)",
         "path_labels": "mid-before-lower-break, top-before-lower-break, time to mid / top, MFE, MAE, MFE/MAE in box widths",
         "top_study": "for bottom trades that reach TOP: incremental value of HOLD +15/+30/+60/16:00/16:15/next open vs EXIT NOW (raw and matched)",
         "zone_study": "first close in each of the 6 zones per box: +30m / 16:15 net and matched excess",
         "direction": "box sequence direction vs the previous box of the same geometry in the session: (mid - prev mid) / prev width > +0.25 RISING, "
                      "< -0.25 FALLING, else FLAT; width dynamics: width / prev width < 0.8 CONTRACTING, > 1.25 EXPANDING, else STABLE; "
                      "migration velocity = mid change over the last 3 boxes / ATR_d",
         "failure_map": "BOX_BOTTOM_SUCCESS (top before break) / FAILURE; TRUE / FALSE up- and down-breaks (break holds >= 30 min vs re-enters the box)"}
MATCHED = {"control": "long entered at the SAME grid minute and exited at the SAME exit minute (same holding horizon) on every session of the same "
                      "instrument x year x vol tercile x HTF-bull group (time-of-day matched by construction), net of the same costs; "
                      "EXCESS = event net - mean control net"}
RANKING = {"TEST70": "geometry economic score = fold-median (2021..2025-26) of bottom-trade matched EXCESS $/day; eligible if >= 4/5 folds excess > 0, "
                     ">= 300 events (2019-07+) and >= 40 per outer fold, excess > 0 at SLIP4-equivalent (costs x 4 ticks); hit rate / AUC diagnostics only",
           "TEST71_selection": "top 3 eligible geometries per instrument by score; if fewer than 3 eligible, fill with the best by score among >= 3/5 folds, labelled "
                               "EXPLORATORY; if none has positive full-sample excess -> TEST71 runs on the 3 best by score as a documented negative control"}
PLATEAU = {"neighbours_TEST71_plus": {"lower_zone": [0.10, 0.25], "upper_zone": [0.75, 0.95], "geometry_width_step": "one step on each side of the "
                                      "geometry's own grid (A/F/I obs or life, B/H nbars, C K, D p, G m, I frac); E: OR15 <-> OR5 / OR30",
                                      "break_buffer": [0.10, 0.20], "cycles": "max cycles 1 <-> 2"},
           "definition": "PASS iff every neighbour has total net > 0 AND >= 60% of the base total AND matched excess > 0 in >= 75% of neighbours",
           "sample_minimum": ">= 300 trades 2019-07+, >= 40 per outer fold"}
GATES = {"standalone": ["matched excess > 0", ">= 4/5 outer folds positive net", "remove-top3 > 0", "SLIP4 net > 0", "plateau PASS",
                        "+1 bar entry delay net > 0", "20% missed entries (seed 5) net > 0", "sample minimum"],
         "additive_T61": "TEST65 incremental gate (all items) on T61-R1C vs T61-R1C + BOX, T61 priority on MNQ cap 6 / MES total 8",
         "MINIMUM_MEANINGFUL_INCREMENT": "incremental avg/day >= 10 $/day (2019-07+) AND >= 10 $/day (2021+) AND combined ret/DD >= T61 ret/DD; anything smaller "
                                         "is NOT a survivor even if all other items pass (after ~1,394 prior hypotheses)"}
PROGRAM = {"TEST71": "B0 simple box: one position, 1 contract, buy lower zone, sell upper zone / lower break / 16:15; cycles per box 1, 2, 3 (separate modes)",
           "TEST72": "migration: UP1 ladder shift / UP2 rebuild from the next completed window / UP3 hybrid; up-break confirmation close beyond boundary + "
                     "{0, 0.10, 0.20} x width; DOWN1 shift lower one width / DOWN2 fresh completed-window box / DOWN3 fresh box stable for 5 completed "
                     "1m bars; never buy a broken floor without a newly valid box",
           "TEST73": "trend ladder: buy lower zone of a RISING box, exits A (sell top) vs C (hold while up-break valid, exit 16:15 / lower break) vs D "
                     "(trailing = lower boundary of the current migrated box); RANGE_RECYCLE and TREND_LADDER P&L reported separately",
           "TEST74": "nested: small (A_OBS15_LIFE30) bottom aligned with medium (A_OBS60_LIFE120) lower half and/or large (E_PREV_HL) lower half; "
                     "compare small / small+medium / small+large / all three",
           "TEST75": "T61 overlay ONLY if a standalone family passes: 0/+1 contract overlay, residual capacity only, sells only its own overlay",
           "TEST76": "ML ONLY if a deterministic box family has positive matched excess in >= 4/5 folds; economic targets (EV $), presets only",
           "TEST77": "GA ONLY if TEST76 or a deterministic family shows real economic signal; 30k-100k genomes per justified lane, nested",
           "stopping": "A survivor frozen, or B >= 4 distinct geometry / migration families without robust economic value and ML/GA not justified, or C all "
                       "gains = matched beta / friction"}

SPEC = {"test": "TEST70+ (program) / TEST70 atlas", "research_data_end": "2026-05-27", "t61_untouched": True, "T61_OOS_USED": "NO",
        "question": "Which causal box definition produces economically meaningful lower / upper locations, and can a causally migrating box system capture "
                    "range recycling and uptrend pullback participation with positive matched value after costs?",
        "geometries": GEOMETRIES, "definitions": DEFINITIONS, "clock": CLOCK, "zones": ZONES, "events": EVENT, "matched": MATCHED, "ranking": RANKING,
        "plateau": PLATEAU, "gates": GATES, "program": PROGRAM, "time_segments": ["09:30-10:30", "10:30-12:00", "12:00-14:00", "14:00-15:15", "15:15-16:15"],
        "outer_folds": ["2021", "2022", "2023", "2024", "2025-01..2026-05-27"], "prior_budget": {"hypotheses": 1394, "ml_configs": 189, "genomes": 777629},
        "atlas_cells": f"{len(GEOMETRIES)} geometries x 2 instruments = {2 * len(GEOMETRIES)}"}

if __name__ == "__main__":
    d = os.path.join(BOX, "TEST70"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "TEST70_PLUS_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("preregistration already written")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h, SPEC["atlas_cells"])
