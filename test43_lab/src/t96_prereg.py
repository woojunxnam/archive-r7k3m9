"""TEST96+ preregistration (written BEFORE any NQ-full / YM / RTY economics and before any Generation-1 thesis-factory economics).
Program: DATA UNBLOCKED + THESIS-EXPANSION CORRECTION + TRACK D (CURRENT-MAIN mechanism portability to YM / RTY) + Track B resume.
Baseline MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (frozen, unmodified).  Research data <= 2026-05-27."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

OUT = os.path.join(os.path.abspath(C45.ROOT), "out", "t96")

SPEC = {
    "program": "TEST96+", "research_data_end": "2026-05-27", "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO",
    "baseline": "MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1 (daily $ from frozen artefacts; occupancy MNQ <= 6, MES <= 8)",
    "data": {"NQ": "e6298965... full contract (signals; MNQ execution uses MNQ prices)", "YM": "edde4419... -> MYM $0.5/pt tick 1.0 ($0.50)",
             "RTY": "7539af44... -> M2K $5/pt tick 0.1 ($0.50)", "costs": "0.62 + 1 tick per side (MYM / M2K 1.12 $/side); SLIP4 = 0.62 + 4 ticks",
             "grid": "same TEST45 session grid as ES / MNQ (sessions = ES & MNQ canonical sessions); same fill convention (next 1m open)"},
    "correction": "Tom Hougaard / Jesse Livermore are ECONOMIC / BEHAVIOURAL PRIORS, not templates (TEST95 literal forms failed and are not rescued)",
    # ---------------------------------------------------------------------------------------------------------------- TRACK D
    "TRACK_D_STAGE_A_EXACT": {
        "rule": "original dimensionless / ATR-normalised definitions and frozen genomes unchanged; NO threshold change; 1 micro per signal "
                "(MYM / M2K); each mechanism evaluated standalone (no shared cap, no MNQ dollar governor); controls as listed",
        "T53_M1": "TEST48 GA-AC per-fold frozen genomes (nested outer, sel_rank 0) applied to the YM / RTY market object (check_inst off)",
        "T53_M2": "TEST49 GA-CT per-fold frozen genomes (compression / strength state -> late-morning entry -> genome exit incl. next open)",
        "T53_M3": "TEST50 GA-VX per-fold frozen genomes (compression -> upside volatility expansion, genome stop)",
        "T53_M4": "opening drive at 10:00: ret >= 0.25 ATR_d & efficiency >= 0.5 -> hold 16:15 (2021+)",
        "T68": "first new RTH session high after 10:30 that is >= 60 min after the previous session high, fill next 1m open, hold 16:15 (2021+ primary, "
               "2019-07+ report); controls: ordinary first new session high after 10:30 (no 60-min condition), momentum-null B, matched A",
        "T67": "frozen turn-of-month calendar (enter 16:15 fill... exactly tom_signals(td_in=-1, td_out=3), entry j=0 of the last session of the month, "
               "exit 16:15 of the 3rd session of the new month); unchanged dates; 1 micro",
        "PG12": "TEST86 deterministic PG12_DOWN_STACK (VP-B proxy, f_bin 0.02, VA 0.70, 12:00 decision, hold 16:00) on TRUE full-contract volume; "
                "controls: momentum-null B, price-only profile (unit volume), relative-volume null",
        "T66_ML": "MECHANISM transfer: TEST66 opening-state feature architecture + economic target + chronological fold procedure retrained inside YM / "
                  "RTY folds separately; frozen MNQ weights NOT applied; no pooling",
        "C43": "structural audit of the V6 sleeves; transfer only if mechanism logic separable from ES/NQ dollar constants; dollar constants normalised "
               "by the ratio of median $ATR (micro) over sessions < 2021-01-01; named C43_MECH_YM / C43_MECH_RTY",
        "STAGE_B": "only after Stage A, only for mechanisms with economic direction (net > 0 and matched A > 0) that miss a gate for an interpretable "
                   "reason; requires a NEW preregistration",
        "bundle_rule_P1_P2": "FIXED_YM_TRANSFER_BUNDLE / FIXED_RTY_TRANSFER_BUNDLE = all Stage-A mechanisms of that index that pass the STANDALONE gate "
                             "(or the DIVERSIFIER gate), each at lots = max(1, round(median $ATR(MES) / median $ATR(micro))) measured on sessions < 2021-01-01; "
                             "defined BEFORE portfolio P&L is opened; no subset search",
        "portfolios": {"P0": "CURRENT_MAIN", "P1": "+ FIXED_YM_TRANSFER_BUNDLE", "P2": "+ FIXED_RTY_TRANSFER_BUNDLE", "P3": "+ both"},
        "D10_D11": "cross-index confirmation / leader-follower evaluated only after single-index Stage A; measured as INCREMENTAL value over the "
                   "unconfirmed signal on the same sessions (confirmed-minus-unconfirmed and vs a beta-matched null)"},
    # ---------------------------------------------------------------------------------------------------------------- TRACK A2
    "TRACK_A2_THESIS_FACTORY": {
        "mechanism_map": "reports/CANONICAL_LAB/THESIS_MECHANISM_MAP.md (written with this prereg)",
        "GEN1": {
            "G1_REACTION_RESUMPTION [LV4 / LV7 / TH6]": "intraday proven trend (open->5m close >= 0.5 ATR_d, efficiency >= 0.4) -> natural reaction "
                                                         "(pullback from the session high of 25-60% of the open->high move, lasting >= 3 5m bars) -> "
                                                         "resumption = first 5m close above the high of the last reaction bar; decisions 10:00-15:00; "
                                                         "control: same trend state entered at the first bar the trend condition held (no reaction)",
            "G2_PRIORDAY_TREND_NEXTDAY_REACTION [LV12]": "day-1 trend day (RTH ret >= 0.7 ATR_d, close in top 20% of range) -> day-2 reaction (day-2 low <= "
                                                         "day-1 close - 0.25 ATR_d before the decision) -> resumption = first 5m close above the day-2 "
                                                         "opening 30m high after the reaction low; decisions 10:00-14:30; control: day-1 trend day only (enter "
                                                         "same minute distribution via matched A) and momentum-null B",
            "G3_OLD_RESISTANCE_ACCEPTED_SUPPORT [LV6 / LV13]": "break above prior RTH high -> retest: a later 5m low within 0.1 ATR_d of PDH while no 5m "
                                                               "close < PDH - 0.1 ATR_d -> acceptance >= 3 5m bars since the break -> entry at the first 5m "
                                                               "close to a new post-break high; decisions to 15:00; control: plain first PDH break",
            "G4_CONGESTION_LINE_OF_LEAST_RESISTANCE [LV3]": "prior 5 RTH sessions high-low <= 1.5 x ATR_d (multi-session congestion) -> first RTH 5m "
                                                            "close above the 5-session high; control: 20-session-high first break without congestion",
            "G5_STRONG_TO_STRONGER [TH8 / TH9]": "two impulse 5m bars (range >= 1.8 x median range of the prior 12 bars, close in top 25%) in the same "
                                                 "session, the second at a higher close with range >= the first and >= 3 bars apart; entry after the "
                                                 "second; control: first impulse only",
            "G6_BROAD_CONFIRMATION [TH18 / TH19 / D11]": "leader = first of {ES, NQ, YM, RTY} to make a new session high after 10:30 >= 60 min after "
                                                         "its previous high; broad confirmation = all other three make a new session high within the next "
                                                         "30 min; trade: the LAST confirming index (laggard) and separately the leader, entry at "
                                                         "confirmation; control: same event without confirmation (leader only) and T68 raw"},
        "instruments": ["ES->MES", "NQ->MNQ", "YM->MYM", "RTY->M2K"],
        "primary_exit": "16:15 (flat); secondary exits reported: 30m / 60m / 120m / 16:00 / next RTH open (overnight measured only if intraday value)",
        "next_generation_rule": "each later generation is preregistered from Gen-1 failure analysis; it must be a different mechanism / state "
                                "transition, not a threshold variant",
        "ML": "allowed on a base event with >= 600 events and heterogeneous outcomes (outcome IQR test); economic target $ after friction; "
              "chronological outer folds; TRADE/SKIP, HOLD, OVERNIGHT, ADD questions; no AUC promotion",
        "GA": "only with a coherent mechanism, >= 600 events and >= 3 structural dimensions; nested chronological"},
    # ---------------------------------------------------------------------------------------------------------------- TRACK B
    "TRACK_B": {"parity_rule": "unchanged TEST46 (recall >= 98%, precision >= 98%, price within 1 tick after quarterly offset >= 95%)",
                "retries": {"LC03": "T07-11 on canonical NQ (was MNQ proxy)", "LC05": "T07-01 on canonical NQ with true NQ volume",
                            "LC02": "no new information (ES unchanged) -> stays BLOCKED", "TS22": "T22-07 if Pine + ledger recovered",
                            "T30": "W01 selector with ES / YM / RTY context if recovered", "TEST20": "V1 (TS20-E01A) and L2-only from Pine + docs"},
                "selection_bias": "all legacy members were selected on data that includes the sealed window; historical replay <= 2026-05-27 is "
                                  "in-sample for selection -> labelled SELECTION-BIASED"},
    # ---------------------------------------------------------------------------------------------------------------- GATES
    "GATE_STANDALONE": ["net > 0", "matched A > 0", "momentum-null B > 0 (intraday single entry)", ">= 4/5 outer folds net > 0", "remove-top3 > 0",
                        "SLIP4 > 0", "+1 bar delay > 0", "plateau: listed neighbours all > 0 and >= 60% of base (Stage A: none - exact transfer; "
                                                         "report fold stability instead)",
                        "sample >= 200 trades and >= 25 per fold (calendar T67: >= 60 and >= 8 per fold)"],
    "GATE_PORTFOLIO": "incremental >= +10 $/day (2019-07+ and 2021+) AND MAIN+X ret/DD >= MAIN ret/DD AND MaxDD <= 1.10 x MAIN AND worst >= -5000",
    "GATE_DIVERSIFIER (YM / RTY / low-corr sleeves)": "standalone pass AND |corr to MAIN| <= 0.30 AND MAIN+X ret/DD >= 1.05 x MAIN ret/DD AND "
                                                      "MaxDD <= 1.05 x MAIN AND worst >= -5000 AND incremental >= +3 $/day",
    "multiple_testing": "Gen-1: 6 mechanisms x 4 instruments = 24 cells; Track D Stage A: 7 mechanisms x 2 = 14 cells; with ~38 cells expect ~2 "
                        "chance single-gate passes -> full gate conjunction + fold consistency required",
    "stopping": "robust portfolio-additive survivor, or thesis families saturated, or near-neighbours only, or hard data limitation"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "TEST96_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
