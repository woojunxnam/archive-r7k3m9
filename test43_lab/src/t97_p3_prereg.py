"""TEST97 Phase 3/4 preregistration for the only Wave-2 family with EVENT_EDGE vs the multi-bar magnitude null."""
import datetime, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E
SPEC = {"candidate": "FT2 = N=12 rolling-high breakout STRONG bar at b, bar b+1 also STRONG (body >= .6, close pos >= .8, range >= 1.25 ATR5); "
                     "entry open of b+2 (signal on completed b+1); LONG 1 micro; ES->MES, NQ->MNQ, YM->MYM, RTY->M2K",
        "exits": {"X60": "fixed 60 min (open of bar b+2+12)", "X1615": "16:15 flat", "why": "event evidence: h12 xBk +0.037 (CI > 0), h16:15 xBk +0.053 (CI n/a)"},
        "stress": ["SLIP4", "+1 bar (5 min) delayed entry", "20% missed entries (seed 7)"],
        "plateau": "STRONG thresholds body .5/.7, close pos .7/.9, range 1.0/1.5 ATR5 and breakout window N 8/20 (one change at a time) - all > 0 and >= 60% of base",
        "walk_forward": "fixed rule (no fitted parameters) -> chronological fold results 2021..2025-26 reported; no refit",
        "gates": "TEST96 standalone gate (net, matched A, folds >= 4/5, remove-top3, SLIP4, delay, plateau, sample >= 200 & >= 25 per fold) + portfolio gate "
                 "vs MAIN_GROWTH_V1 (+10 $/day or DIVERSIFIER rule) on virtual positions (no capacity stolen from MAIN; overlap reported)",
        "position_management": {"population": "identical FT2 initial events, RTH only, flat 16:15, max units 2/3/4, equal adds",
                                "A_SINGLE": "1 unit", "B_BLIND_DCA": "add 1 each time price <= average - 0.5 ATR_d (control)",
                                "C_FRESH_RECOVERY": "add 1 when underwater (price < average) AND a fresh STRONG N=12 breakout bar completes",
                                "D_WINNER_PYRAMID": "add 1 when in profit AND a fresh STRONG N=12 breakout bar completes",
                                "accounting": "per-unit marginal EV (UNIT1, ADD1, ADD2, ADD3); stop deeper stacking if ADD1 <= 0"},
        "ML_GA": "not activated (431 < 600 events)", "2022": "adverse-regime survival table (absolute, matched-beta excess, loss capture)"}
if __name__ == "__main__":
    p = os.path.join(E.OUT, "TEST97_PHASE3_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
