"""RUN-3 Phase 7 finalists: base exec (daily equity saved) + 2-tick + 3-tick slippage, all with fresh starts.
ES-signal / MES-economics proxy backtests."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from run3_lib import FQ, run_batch

FIN = {
    "BASE": {},
    "C32_mkt": FQ(16, 16, True),
    "C32_lmt": dict(FQ(16, 16, True), rec_entry_mode="limit_close"),
    "C32_harv5": dict(FQ(16, 16, True), harvest="all_prof", harvest_x=5.0),
    "C32_harv5_lmt": dict(FQ(16, 16, True), harvest="all_prof", harvest_x=5.0, rec_entry_mode="limit_close"),
    "C24_mkt": FQ(12, 12, True),
    "C20_mkt": FQ(10, 10, True),
    "C14_mkt": FQ(8, 6, True),
    "C14_lmt": dict(FQ(8, 6, True), rec_entry_mode="limit_close"),
    "C10_mkt": FQ(5, 5, False),
    "C10_lmt": dict(FQ(5, 5, False), rec_entry_mode="limit_close"),
}
extra_cfgs = json.loads(os.environ.get("EXTRA_FINALISTS", "{}"))
FIN.update(extra_cfgs)

if __name__ == "__main__":
    json.dump(FIN, open(os.path.join(os.path.dirname(__file__), "..", "results", "RUN3_FINALISTS.json"), "w"), indent=1, default=str)
    jobs = []
    for n, c in FIN.items():
        jobs.append((n, c, {}, True, "RUN3_FINAL"))
        jobs.append((f"{n}__slip2", c, dict(slippage_ticks=2), True, None))
        jobs.append((f"{n}__slip3", c, dict(slippage_ticks=3), True, None))
    print(len(jobs))
    run_batch("RUN3_FINAL", jobs, procs=3)
