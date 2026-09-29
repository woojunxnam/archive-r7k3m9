"""MASTER program bookkeeping: state + registries (AUTONOMOUS_ALPHA_RESEARCH_MASTER_PROGRAM_V1)."""
import csv
import json
import os

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(LAB, "reports", "AUTONOMOUS_ALPHA_RESEARCH_MASTER_V1")
OUT = os.path.join(LAB, "out", "index_alpha_master_v1")
MAIN = {"avg_day": 143.207, "avg_day_2021": 151.78, "max_dd": 13936.3, "worst_day": -4666.44, "ret_dd": 0.010276}
FILES = {
    "MASTER_TEST_REGISTRY.csv": ["test", "family", "status", "classification", "prereg_sha", "result_sha", "distinct_definitions", "ledger_rows", "ml_configs", "ga_genomes", "best_clue", "note"],
    "MASTER_FAMILY_REGISTRY.csv": ["family", "test", "attribution", "source_tier", "novelty_delta", "status"],
    "MASTER_REJECT_REGISTRY.csv": ["test", "variant", "reason"],
    "MASTER_CLUE_LIBRARY.csv": ["test", "variant", "label", "horizon", "excess", "ci_lo", "years_pos", "note"],
    "MASTER_SURVIVOR_LIBRARY.csv": ["test", "module", "label", "avg_day", "route", "selection_exposed"],
    "MASTER_RESEARCH_BUDGET.csv": ["test", "definitions", "ml_configs", "ga_genomes", "cum_definitions", "cum_ml", "cum_ga"],
    "MASTER_PORTFOLIO_FRONTIER.csv": ["step", "members", "avg_day", "avg_day_2021", "max_dd", "worst_day", "ret_dd", "gap_to_600", "selection_exposed"],
    "MASTER_COMMIT_LEDGER.csv": ["sha", "kind", "test", "message"],
}


def _p(name):
    return os.path.join(REP, name)


def init():
    os.makedirs(REP, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for f, h in FILES.items():
        if not os.path.exists(_p(f)):
            with open(_p(f), "w", newline="") as fh:
                csv.writer(fh).writerow(h)


def append(name, row):
    with open(_p(name), "a", newline="") as fh:
        csv.writer(fh).writerow([row.get(k, "") for k in FILES[name]])


def load_state():
    return json.load(open(_p("MASTER_STATE.json")))


def save_state(st):
    for d in (REP, OUT):
        json.dump(st, open(os.path.join(d, "MASTER_STATE.json"), "w"), indent=1, default=str)


def budget_add(st, test, defs=0, ml=0, ga=0, rows=0):
    st["CUM_DISTINCT_HYPOTHESES"] += defs; st["CUM_ML_CONFIGS"] += ml; st["CUM_GA_GENOMES"] += ga; st["CUM_LEDGER_ROWS"] += rows
    append("MASTER_RESEARCH_BUDGET.csv", {"test": test, "definitions": defs, "ml_configs": ml, "ga_genomes": ga, "cum_definitions": st["CUM_DISTINCT_HYPOTHESES"],
                                           "cum_ml": st["CUM_ML_CONFIGS"], "cum_ga": st["CUM_GA_GENOMES"]})
