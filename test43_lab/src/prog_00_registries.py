"""Seed the master registries from TEST45 / TEST46 / TEST47 outcomes (before TEST48)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

TESTS = [
    {"test": "TEST45", "hypothesis": "ES/NQ session alpha: gap / opening flush / overnight carry / cross-index overlays + ML/GA/GP", "prereg_hash": "185d1ef9 (freeze)",
     "result": "CHALLENGER NONE", "survivor_count": 0, "best_clue": "champion-state carry recurrence (mostly beta amplification)", "next_test_reason": "structural rebound (TEST46)"},
    {"test": "TEST46", "hypothesis": "INDEX6 long evolution (Lane A) + structural failed-selling rebound B1-B6 (Lane B) + ML/GA", "prereg_hash": "e0724e20 (freeze)",
     "result": "CHALLENGER NONE (Lane A PARITY_BLOCKED)", "survivor_count": 0, "best_clue": "LC03 hold-to-16:00 (parity blocked); ML-A Ridge weak filter", "next_test_reason": "path-dependent exhaustion (TEST47)"},
    {"test": "TEST47", "hypothesis": "NASSI N3 serial-leg selling exhaustion, true bottom, inventory recycle", "prereg_hash": "94ad9f6d (spec) / ecec4587 (freeze)",
     "result": "CHALLENGER NONE", "survivor_count": 0, "best_clue": "ML-C second-contract logistic (rank-IC 0.09, 5/6 yrs) on a negative base",
     "next_test_reason": "ARM -> later confirmation (TEST48)"},
]
REJ = [
    ("gap_down_rebound", "buy after negative opening gap", "TEST45", "no matched excess, outer folds fail", "~800", "negative/flat", "YES", "a new causal conditioning variable with independent rationale"),
    ("opening_flush_rebound", "buy after large first-30m selloff", "TEST45", "no edge", "~600", "negative", "YES", "-"),
    ("gap_plus_flush", "combined gap + flush", "TEST45", "no edge", "~300", "negative", "YES", "-"),
    ("unconditional_overnight_carry", "hold long 16:15->09:30", "TEST45", "mostly beta", "all sessions", "beta only", "YES", "conditional on a validated module"),
    ("es_nq_cross_state", "generic ES/NQ relative state overlay", "TEST45", "no incremental value", "-", "flat", "YES", "-"),
    ("structural_rebound_B1_B6", "failed break of PDL/5dL/ORL/VWAP band/range exhaustion/HTF pullback + reclaim", "TEST46", "no edge; reclaim adds no info", "150-900/family", "negative/flat", "YES", "-"),
    ("vwap_lower_band_rebound", "VWAP -k sigma excursion + reclaim", "TEST46", "significantly negative on MNQ", "~500", "negative (t -2.9)", "YES", "-"),
    ("range_exhaustion", "session range >= D ATR then reversal", "TEST46", "no edge", "~40-300", "flat", "YES", "-"),
    ("htf_bull_pullback_vwap", "HTF bull + pullback to VWAP", "TEST46", "no edge", "~300", "flat", "YES", "-"),
    ("nassi_n3_serial_legs", "3 meaningful 5m down legs -> long", "TEST47", "negative matched excess all leg defs / both instruments", "~1000/inst", "0-1/5 folds", "YES", "-"),
    ("path_order_information", "order of down legs beyond total displacement", "TEST47", "path-order null + shuffle null", "~1000/inst", "none", "YES", "-"),
    ("deterministic_true_bottom", "deceleration / wick / close-improvement confirmation after N3", "TEST47", "no improvement", "~900/inst", "0-1/5", "YES", "-"),
    ("inventory_recycling_nassi", "second buy / trim / rebuild on N3 campaigns", "TEST47", "no incremental value after costs", "~900 campaigns/inst", "0-2/5", "YES", "a validated positive base entry"),
    ("blind_dca", "add after -X ATR", "TEST47", "diagnostic only; no value", "-", "-", "YES", "-"),
]
CLUES = [
    ("H46_LC03_HOLD", "TEST46", "LC03 NQ-NOON hold extension to 16:00", "matched excess t 2.37 in canonical replay", "PARITY_BLOCKED seed; ledger-driven", "local re-implementation of the NOON entry with hold-curve plateau test"),
    ("R46_RIDGE_FILTER", "TEST46", "Ridge filter on structural-rebound pool with ES/NQ relative feature", "rank-IC 0.038, beats take-all", "economics fail gate; fragile to one feature", "meta-labeling on a positive base event set"),
    ("C47_MLC_SECOND_CONTRACT", "TEST47", "second-contract selection after a later confirmed bottom", "logistic rank-IC 0.09, 5/6 yrs positive on second lots", "base campaign negative", "ARM -> later-bottom / later-confirmation entry as the PRIMARY entry (TEST48)"),
    ("C47_15M_SLOW_SELLING", "TEST47", "MNQ slow sequences with >=2 15m legs", "+8.75 $/trade n=115", "t 0.87, tiny", "only inside a broader multi-timeframe transition test"),
    ("C45_CHAMP_STATE_CARRY", "TEST45", "champion-state carry recurrence", "recurrent across folds", "beta amplification", "second-contract meta-labeling vs matched beta"),
    ("C47_EXTREME_STATE_REBOUND", "TEST47", "N3 events in vol>=0.9 / ret5<=-3 states rebounded more", "excess +20-48 $/trade, n 60-140", "ex-post subset of vetoed events, t<2", "regime-specific test preregistered with discovery-only thresholds"),
]


def main():
    P.reg_append("AUTONOMOUS_TEST_REGISTRY", TESTS, key="test")
    P.reg_append("REJECTED_FAMILY_REGISTRY", [dict(zip(["family", "mechanism", "test", "reason_rejected", "sample_size", "outer_fold_result",
                                                       "retest_forbidden", "reopen_requires"], r)) for r in REJ], key="family")
    P.reg_append("SHADOW_CLUE_REGISTRY", [dict(zip(["clue_id", "source_test", "mechanism", "why_interesting", "why_not_promotable",
                                                   "future_prereg_test"], r)) for r in CLUES], key="clue_id")
    for t, h, ml, g in (("TEST45", 12, 60, 71000), ("TEST46", 10, 40, 213000), ("TEST47", 25, 60, 132000)):
        P.budget(t, hypotheses=h, ml_configs=ml, genomes=g, finalists=0, note="approximate, from test reports")
    print("seeded")


if __name__ == "__main__":
    main()
