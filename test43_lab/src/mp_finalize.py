"""finalize a MASTER test: status json, report md, registries."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402


def finalize(test, tdir, prereg, family, classification, status, defs, clues=(), rejects=(), next_test="", interp="", saturated=True, extra_blocks=()):
    meta = json.load(open(os.path.join(S.OUT, tdir, f"{test.replace('TEST', 'T')}_META.json"))) if os.path.exists(os.path.join(S.OUT, tdir, f"{test.replace('TEST', 'T')}_META.json")) else {}
    rows = meta.get("ledger_rows", 0)
    st = {f"{test}_CLASSIFICATION": classification, **status, "DISTINCT_NEW_DEFINITIONS": defs, "LEDGER_ROWS": rows, "ML_CONFIGS": 0, "GA_GENOMES": 0,
          "STRATEGY_PHASE_OPENED": status.get("STRATEGY_PHASE_OPENED", "NO"), "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"}
    json.dump(st, open(os.path.join(S.OUT, tdir, f"{test}_STATUS.json"), "w"), indent=1)
    cp = os.path.join(S.OUT, tdir, f"{test}_CLASSIFICATION.csv"); blocks = ["```json\n" + json.dumps(st, indent=1) + "\n```"]
    if os.path.exists(cp):
        blocks += ["## Classification (pooled, family null; excess in ATR_d units)", pd.read_csv(cp)]
    blocks += list(extra_blocks) + [f"Per-instrument rows: out/index_alpha_master_v1/{tdir}/.", interp]
    os.makedirs(os.path.join(S.REP, test), exist_ok=True)
    P.md(os.path.join(S.REP, test, f"{test}_REPORT.md"), f"{test} {family} — results (prereg {prereg})", blocks)
    S.close_test(test, family, classification, prereg, defs, rows, clues[0]["variant"] if clues else "none", clues, rejects, next_test=next_test, saturated=saturated)
