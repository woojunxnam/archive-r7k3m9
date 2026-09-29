"""INDEX_DISCRETIONARY_ALPHA_CONTINUOUS_V1 bookkeeping."""
import csv
import json
import os

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(LAB, "reports", "INDEX_DISCRETIONARY_ALPHA_CONTINUOUS_V1")
OUT = os.path.join(LAB, "out", "index_discretionary_alpha_continuous_v1")
FILES = {"MECHANISM_REGISTRY.csv": ["mechanism", "phase", "definition", "n_events", "status", "value_type", "note"],
         "EVENT_LEDGER.csv": ["phase", "mechanism", "null", "horizon", "n", "mean", "excess", "ci_lo", "ci_hi", "years_pos", "inst_pos", "note"],
         "ML_LEDGER.csv": ["task", "population", "config", "stitched_value_day", "slip4_value_day", "folds_pos", "n", "note"],
         "GRAMMAR_SEARCH_LEDGER.csv": ["space", "n_candidates", "selected_by_fold", "stitched_avg_day", "stability", "class"],
         "ACTION_VALUE_LEDGER.csv": ["action", "population", "n", "incremental_ev", "ci_lo", "ci_hi", "slip4_ev", "folds_pos", "note"],
         "MANAGEMENT_LEDGER.csv": ["candidate", "arm", "n", "marginal_ev", "matched_excess", "ci_lo", "ci_hi", "slip4", "folds_pos", "decision"],
         "PORTFOLIO_FRONTIER.csv": ["frontier", "members", "avg_day", "slip4_avg_day", "max_dd", "worst_day", "ret_dd", "gap_to_600", "note"],
         "OVERFIT_DIAGNOSTICS.csv": ["scope", "trials", "dsr", "pbo", "reality_check_p", "status"],
         "REJECT_REGISTRY.csv": ["phase", "item", "reason"], "CLUE_LIBRARY.csv": ["phase", "item", "label", "note"],
         "SURVIVOR_LIBRARY.csv": ["phase", "item", "route", "avg_day", "note"], "NOVELTY_RESERVE_REGISTRY.csv": ["family", "memo", "status", "note"],
         "FEATURE_DICTIONARY.csv": ["feature", "definition", "available_at", "normalization", "group"],
         "COMMIT_LEDGER.csv": ["sha", "kind", "phase", "message"]}


def init():
    os.makedirs(REP, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for f, h in FILES.items():
        if not os.path.exists(os.path.join(REP, f)):
            csv.writer(open(os.path.join(REP, f), "w", newline="")).writerow(h)


def append(name, row):
    with open(os.path.join(REP, name), "a", newline="") as fh:
        csv.writer(fh).writerow([row.get(k, "") for k in FILES[name]])


def state():
    return json.load(open(os.path.join(REP, "PROGRAM_STATE.json")))


def save(st):
    for d in (REP, OUT):
        json.dump(st, open(os.path.join(d, "PROGRAM_STATE.json"), "w"), indent=1, default=str)


def upd(**kw):
    st = state(); st.update(kw); save(st); return st
