"""TEST64 preregistration: DELAYED CONFIRMATION ON POSITIVE BASES (M2, M4 entries require the TEST48 CF4 15m confirmation)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Does requiring a later independent confirmation (TEST48 CF4: completed 15m bullish bar closing above the previous 15m high, within 30 min) "
                "improve the positive-base modules M2 and M4 inside T61-R1B?",
    "rationale": "TEST48: delayed confirmation improved matched excess vs immediate entry in ~73% of cells, but its bases were negative; here the bases are the "
                 "validated-positive M2/M4 signals.",
    "difference": "CF4 rule fixed exactly as in TEST48 (no tuning); only M2/M4 entry timing / filtering changes; M1/M3, exits, caps, governor unchanged",
    "rule": "after the original M2/M4 signal fill minute j, scan completed 15m bars ending within the next 6 5m bars; first CF4 bar k -> entry at 5(k+1); none -> no trade",
    "decision": "adopt only if incremental vs T61-R1B > 0 in >= 4/5 outer folds, ret/DD >= T61-R1B ret/DD, envelope, SLIP4 incremental > 0",
}

if __name__ == "__main__":
    print(P.prereg("TEST64", SPEC))
