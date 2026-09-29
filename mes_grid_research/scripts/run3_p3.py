"""RUN-3 Phase 3: execution realism (strategy logic frozen). Entry A market / B limit(same-bar TP allowed) / C limit(conservative)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from run3_lib import FQ, run_batch

CANDS = {"C32": FQ(16, 16, True), "C14": FQ(8, 6, True), "C10": FQ(5, 5, False)}
if __name__ == "__main__":
    jobs = []
    for cn, base in CANDS.items():
        for ent in ("A", "B", "C"):
            for slip in (1, 2, 3, 4):
                for tp in (2.5, 3.0, 4.0, 5.0):
                    cfg = dict(base, rec_tp=tp)
                    ex = dict(slippage_ticks=slip)
                    if ent != "A":
                        cfg["rec_entry_mode"] = "limit_close"
                    if ent == "B":
                        ex["allow_same_bar_tp_after_intrabar_buy"] = True
                    fresh = (ent == "A" and tp == 3.0)
                    jobs.append((f"{cn}_{ent}_s{slip}_tp{tp}", cfg, ex, fresh, None))
    print(len(jobs))
    run_batch("RUN3_P3_EXEC", jobs)
