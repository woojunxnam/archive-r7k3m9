"""TEST52 preregistration: SHADOW-MODULE COMBINATION (diversification test).  Written before the combination economics are computed."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Do the individually non-passing shadow modules of TEST48-51 combine into a diversified module that passes the program gate?",
    "why_mechanism_could_exist": "Several small, partly independent edges can pass jointly when their errors are uncorrelated.",
    "prior_result_motivating_it": "TEST48 GA-AC, TEST49 GA-CT, TEST50 GA-VX each 4/5 outer folds but failing G4/G8; TEST49 MNQ opening drive 5/5 folds.",
    "difference_from_failed_families": "Combination Q; no module is modified; weights fixed equal (1 contract each), no optimisation.",
    "falsification": "pairwise daily correlation of the modules > 0.5 (redundant) or the equal-weight combination fails the program gate.",
    "modules": {"M1": "GA-AC nested stitched outer (TEST48)", "M2": "GA-CT nested stitched outer (TEST49)", "M3": "GA-VX nested stitched outer (TEST50)",
                "M4": "MNQ T1 opening drive 10:00 k=0.25 -> X1615 (TEST49 simple, frozen)"},
    "weights": "equal, 1 MNQ contract per module; shared cap 2 MNQ simultaneously is NOT enforced in this diagnostic (reported: peak MNQ)",
    "evaluation": "program gate on the summed daily $ (2021..2026-05-27 stitched nested outer folds), + correlation matrix, loss-day Jaccard, peak MNQ",
    "multiple_testing": "exactly ONE combination is evaluated (no subset search)",
}

if __name__ == "__main__":
    print(P.prereg("TEST52", SPEC))
