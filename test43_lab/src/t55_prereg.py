"""TEST55 preregistration: RESIDUAL-CAPACITY ALLOCATOR (C43 priority, TEST53 fills residual MNQ capacity, total MNQ <= 3)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Can TEST53 use only the exposure capacity C43 leaves unused while total MNQ stays at C43's own historical peak (3)?",
    "rationale": "C43 is risk-gate limited, not margin limited; its historical peak raw MNQ is 3, so a total cap of 3 never exceeds exposure the validated control "
                 "already carried, while TEST53 (low corr to C43) fills idle capacity.",
    "difference": "portfolio engineering only: C43 unchanged with priority; TEST53 modules/governor frozen (TEST53 prereg 3d65a85c); only the shared cap changes.",
    "architecture": "per minute capacity = max(0, CAP_TOTAL - C43 MNQ position); TEST53 signals taken only while ensemble count < min(2, capacity); no reduction "
                    "of open ensemble lots when C43 later increases (report-only overlap)",
    "primary": "CAP_TOTAL = 3 (C43 historical peak raw MNQ)",
    "controls": ["C43 only", "C43 + TEST53 (ensemble cap 2, no total cap) = historical C43-GROWTH shadow", "total 2 (= TEST54)", "total 4 (report only)", "total 5 (reference)"],
    "gate": "hx_gate_spec.json lanes (CORE / GROWTH / AGGRESSIVE-report); plateau = governor {-800,-900,-1100,-1200} and adjacent total caps {2,4}",
    "falsification": "total-3 architecture fails both CORE and GROWTH lanes",
}

if __name__ == "__main__":
    print(P.prereg("TEST55", SPEC))
