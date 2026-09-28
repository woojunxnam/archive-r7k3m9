"""TEST57 preregistration: GA-EXPOSURE (nested) over the Beta-Carrier-V2 exposure grammar."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Can a nested evolutionary search over the exposure grammar (state thresholds, tier map, vol target, governor, overnight permission, MNQ share) "
                "find an exposure policy with POSITIVE outer-fold timing value and a GROWTH-quality portfolio with C43?",
    "rationale": "TEST56 deterministic maps had negative timing; a search may find a structure (e.g. low exposure only in crash states) that generalises - "
                 "or confirm that timing cannot be learned from these states.",
    "genes": {"f_m": "SMA pair from {(10,30),(20,50),(30,100)}", "dd_bear": "(2.0, 8.0) ATRd", "vol_crash": "{0.8,0.9,0.95,1.01(off)}",
              "tier_bear/neutral/bull/strong": "ladder indices 0..6 of {0,1,2,3,5,8,12} (monotone enforced: sorted)", "vol_target": "{0,1}",
              "dd_gov": "{off, (8k,16k), (15k,30k)}", "intraday_only": "{0,1}", "r_nq": "{0, 0.5, 1.0}", "state_inst": "{ES, MNQ}"},
    "fitness": "prog_ga generic: minimise [-median inner $/day of C43+carrier INCREMENT, -worst inner, training MaxDD of C43+carrier, -training TIMING value "
               "(carrier gross - constant long with the same average contracts, training window), complexity]; constraints: training worst day of C43+carrier >= -6000, "
               "peak overnight margin <= 40% NLV",
    "budget": "POP 64, GENS 40, 2 seeds x 3 islands, 6 folds",
    "outer": "per-fold rank-0 frozen policy evaluated once on the next block; stitched outer daily increment -> hx lanes (base C43-CORE and C43-GROWTH T55)",
    "falsification": "stitched outer timing value <= 0 or no lane pass",
}

if __name__ == "__main__":
    print(P.prereg("TEST57", SPEC))
