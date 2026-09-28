"""TEST94+ VALIDATED-WINNER PRESS (Lane A) + FIXED SHADOW-CLUE BASKET (Lane B) - preregistration, written before any economics of either lane."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

PW = os.path.join(os.path.abspath(C45.ROOT), "out", "PRESS_BASKET_LAB")

SPEC = {
    "program": "TEST94+ VALIDATED-WINNER PRESS + FIXED CLUE-BASKET", "research_data_end": "2026-05-27", "T61": "frozen sponsor; never modified; no forward OOS",
    "prior_diagnostic_note": "TEST94_PRESS_WINNER (M1 base) was a non-promotable diagnostic; this program tests pressing the VALIDATED T61 campaign",
    "LANE_A": {
        "sponsor": "frozen T61-R1C broker-model targets (fail-closed shadow replay out/test65/t61_hist): MNQ leg (C43 x2 MNQ + clamped TEST53) and MES leg (C43 x2 MES)",
        "campaign": "maximal run of consecutive RTH grid minutes with T61 target > 0 for the leg; continues across sessions if held at 16:15 and at the next 09:31; "
                    "average entry price from T61 target increases at the fill-minute open (FP); unrealised per unit = close - average; causal only",
        "source_attribution": "C43 (TEST53 zero so far in the campaign) / TEST53 (C43 MNQ zero so far) / MIXED - attribution only, never selected on",
        "PRESS1": "ONE overlay contract per campaign (first trigger), never while campaign unrealised <= threshold; overlay exits never touch T61",
        "profit_threshold": {"theta_ATR": "base 0.10 (per-unit unrealised >= theta x ATR_d)", "plateau": [0.0, 0.25], "report": [0.50]},
        "triggers": {"A_NEW_HIGH": "close > campaign-high close AND close > session VWAP",
                     "B_SECOND_IMPULSE": "new campaign-high close after >= 10 min without a new high and the pause drawdown <= 0.15 ATR_d",
                     "C_SHALLOW_PULLBACK": "pullback >= 0.10 ATR_d from the campaign high with the low still above the campaign average entry, then close >= low + 50% of the pullback",
                     "D_T61_ADDS": "T61 leg target increases at minute j while the campaign was already profitable (threshold) before the increase",
                     "E_VALUE_PROXY": "A_NEW_HIGH AND developing P2 POC (VP-B) up >= 0.05 ATR_d over 30 min; MNQ = PROXY volume (label PROXY, not primary)",
                     "F_PURE_PROFIT": "first minute the campaign reaches the profit threshold (control: 'winner is already winning')"},
        "entry_speed": {"IMMEDIATE": "next 1m open after the trigger close (primary)", "DELAY1": "one bar later (report / stress)"},
        "exits": {"E2 (PRIMARY)": "T61 leg campaign ends (target 0) or 16:15", "E1": "T61 leg reduces exposure", "E3": "close below session VWAP", "E4": "16:15"},
        "overlay_horizon": "RTH only: overlay always flat by 16:15 (no overnight overlay)",
        "capacity": {"MNQ": "residual only: T61 MNQ + overlay <= 6 at the fill minute else BLOCKED; overlay cut at the same fill if T61 later needs the slot; "
                            "report-only UNCONSTRAINED diagnostic measures the cap-blocked opportunity",
                     "MES": "T61 MES + overlay <= 8", "cross": "MES +1 on an MNQ campaign only when ES is also at a new session high (report, independent MES economics)"},
        "controls": {"FRONTLOAD": "+1 at the campaign entry (or 09:31 of the press session if the campaign began earlier), same exit",
                     "RANDOM_TIMING": "+1 at uniformly random campaign minutes of the same session before the exit (20 draws, seed 5), same exit; mean",
                     "SAME_EXPOSURE_BETA": "matched long (year x vol tercile x bull, same entry / exit minute), i.e. timing value vs unconditional exposure"},
        "gate_PRESS1": {"standalone": ["marginal avg/day > 0", "marginal $/trade > 0", ">= 4/5 outer folds > 0", "remove-top3 > 0", "SLIP4 > 0",
                                       "plateau: theta 0.0 and 0.25 and exit E1 all > 0 and >= 60% of base", "frontload excess > 0", "random-timing excess > 0",
                                       "same-exposure (matched) excess > 0", ">= 300 events, >= 40 per fold"],
                        "portfolio (frozen, replaces +10 $/day for PRESS1 only)": "T61 + PRESS1: combined ret/DD >= 1.03 x T61 ret/DD AND incremental >= +3 $/day "
                                                                                  "AND combined MaxDD <= 1.10 x T61 MaxDD AND worst day >= -5,000",
                        "multiplicity": "6 triggers x {MNQ, MES}; each judged separately, all reported"},
        "PRESS2": "only if a PRESS1 cell passes (new preregistration); larger ladders only after PRESS2",
        "ML_GA": "ML only if deterministic PRESS1 shows positive marginal EV (target = marginal overlay $); GA only if PRESS1 clearly positive"},
    "LANE_B": {
        "members_fixed_before_economics": {
            "PG12_ML": "TEST91 MNQ PG12_DOWN_STACK HGB (PRIMARY) meta-selected (walk-forward, 2021+ trades only), 1 MNQ, 12:00 -> 16:00",
            "T67_TOM_INTRADAY": "TEST67 report variant: TOM sessions (td -1 .. +3) 09:31 -> 16:15, 2 MES",
            "T68_RAW_BREAKS": "TEST68 report variant: all MNQ secondary session-high breaks (2021+), 1 MNQ, -> 16:15",
            "T66_ML_OPENING": "TEST66 E66ML meta-labeled opening entry (2021+), 1 MNQ, 09:35 -> 10:30"},
        "rules": "each member's historical rule frozen exactly (no retuning); weights = original unit sizes (1 MNQ / 2 MES / 1 MNQ / 1 MNQ)",
        "per_module_cap": "one open trade per member", "portfolio_cap": "shared MNQ capacity with T61 (T61 + basket MNQ <= 6, first-come; latest basket MNQ trade cut "
                                                                            "at the same fill when T61 needs the slot); MES T61 + basket <= 8",
        "shared_daily_governor": "NONE (declared)", "run": "exactly once; no subset search; no component removal afterwards; NO ML / GA",
        "gate": "T61 + basket vs T61: TEST65 incremental gate items (folds, SLIP4, top5, regime, corr, caps) AND MINIMUM MEANINGFUL INCREMENT >= +10 $/day "
                "(2019-07+ and 2021+) AND combined ret/DD >= T61 ret/DD; component verdicts unchanged (they remain shadow clues)",
        "note": "PG12 / T66 / T68 components trade only 2021+ by construction (walk-forward / report span) -> basket judged on 2021+ as well as full span"},
    "PROFILE_NQ_RESEARCH": "DATA-LIMITED (no full NQ volume); no further MNQ-proxy profile refinement",
    "no_more": ["generic momentum atlas", "bottom / rebound families"],
    "final_selection": "NONE / PRESS1 ONLY / BASKET ONLY / BOTH (combination only with a new preregistration)",
    "OOS": "any survivor gets its own OOS start (first full RTH session after its own freeze); T61 OOS 2026-09-29 untouched",
    "prior_budget": {"hypotheses": 3300, "ml_configs": 225, "genomes": 777629}}

if __name__ == "__main__":
    os.makedirs(PW, exist_ok=True); p = os.path.join(PW, "TEST94_PLUS_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
