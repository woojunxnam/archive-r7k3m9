"""RUN-3 Phase 2: capital / max-contract frontier with FROZEN FQ mechanism."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from run3_lib import FQ, run_batch

SPLITS = {10: [(6, 4), (5, 5)], 12: [(8, 4), (6, 6)], 14: [(8, 6), (10, 4)], 16: [(8, 8), (10, 6), (12, 4)],
          18: [(10, 8), (12, 6)], 20: [(12, 8), (10, 10), (14, 6)], 24: [(16, 8), (12, 12)]}
REF = [(16, 16), (12, 20)]   # RUN-2 originals (32 total)

if __name__ == "__main__":
    jobs = []
    for add in (False, True):
        for tot, sp in SPLITS.items():
            for cc, rc in sp:
                jobs.append((f"FQ{'A' if add else ''}_{tot}_{cc}_{rc}", FQ(cc, rc, add), {}, True, None))
        for cc, rc in REF:
            jobs.append((f"FQ{'A' if add else ''}_32_{cc}_{rc}", FQ(cc, rc, add), {}, True, None))
    print(len(jobs))
    run_batch("RUN3_P2_FRONTIER", jobs)
