"""TEST63 preregistration: HOLD-EXTENSION (conditional winner carry) of TEST53 lots inside T61-R1B."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Does carrying end-of-day TEST53 lots (M1/M3/M4, planned exits 16:00/16:15) to the next 09:31 open add return without proportionally more tail?",
    "rationale": "TEST59: M2's validated overnight hold beat a 16:15 exit; continuation states may leave unfinished demand into the next open, and a lot that is "
                 "profitable at 16:14 is the validated-positive subset (hold-extension of positive signals, not unconditional carry).",
    "difference": "not unconditional carry (TEST45) nor close-strength carry (TEST49 T4, rejected): only already-open, validated-module lots; entries/sizes unchanged",
    "variants": {"H0": "T61-R1B as frozen", "H1_WINNER_CARRY": "lot with 16:14 close > entry price -> exit at next 09:31 open instead", "H2_CARRY_ALL (report)": "all end-of-day lots carried"},
    "cap": "carried lots count against the global MNQ target <= 6 (reduced at 09:31+1m if C43 is higher)",
    "decision": "adopt H1 into 'T61-R1B-H1' only if: incremental vs H0 > 0 in >= 4/5 outer folds, ret/DD >= H0 ret/DD, MaxDD <= 30k, worst >= -6k, full SLIP4 incremental > 0",
}

if __name__ == "__main__":
    print(P.prereg("TEST63", SPEC))
