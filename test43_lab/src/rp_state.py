"""INDEX_ML_GA_RECLAMATION_V1 bookkeeping."""
import csv
import json
import os

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(LAB, "reports", "INDEX_ML_GA_RECLAMATION_V1")
OUT = os.path.join(LAB, "out", "index_ml_ga_reclamation_v1")
FILES = {"CANDIDATE_BANK.csv": ["candidate", "source_test", "definition", "frozen_horizon", "n_events", "role", "tier_a", "note"],
         "ML_CONFIG_LEDGER.csv": ["family", "config", "model", "selection", "horizon", "stitched_avg_day", "slip4_avg_day", "folds_pos", "trades", "note"],
         "GA_GENOME_LEDGER.csv": ["family", "n_genomes", "space", "selected_by_fold", "stitched_avg_day", "stability", "note"],
         "MANAGEMENT_LEDGER.csv": ["candidate", "arm", "n_base", "n_add", "unit1_ev", "add1_marginal_ev", "basket_ev", "decision"],
         "PORTFOLIO_FRONTIER.csv": ["frontier", "members", "avg_day", "avg_day_2021", "max_dd", "worst_day", "ret_dd", "slip4_avg_day", "gap_to_600", "note"],
         "OVERFIT_DIAGNOSTICS.csv": ["family", "trials", "dsr", "pbo", "reality_check_p", "status"],
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
