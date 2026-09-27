"""TEST43-P Phases 21-22: holdout acceptance rules and final portfolio freeze manifest (holdout NOT loaded)."""
import hashlib
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import lab, portfolio as PF, sleeves as S  # noqa: E402

OUT = PF.PDIR
FZ = f"{OUT}/freeze"


def sha(fn):
    return hashlib.sha256(open(fn, "rb").read()).hexdigest()


def main():
    pre = json.load(open(f"{FZ}/TEST43P_PRE_VAL_FREEZE.json"))
    pre_sha = open(f"{FZ}/TEST43P_PRE_VAL_FREEZE.sha256").read().split()[0]
    assert pre_sha == sha(f"{FZ}/TEST43P_PRE_VAL_FREEZE.json")
    sel = json.load(open(f"{OUT}/p20_selection.json"))
    V = pd.read_csv(f"{OUT}/p18_val_confirmation.csv")
    sig = pre["risk_normalisation"]["sigma_daily_dev"]
    ports = {}
    for role, key in sel.items():
        name, env = key.split("|")
        bud = pre["portfolios"][name]
        L = pre["risk_scale_L"][key]
        row = V[(V.portfolio == name) & (V.risk_env == env)].iloc[0]
        ports[role] = {
            "portfolio": name, "risk_envelope": env, "envelope": list(lab.ENVELOPES[env]),
            "members": {cid: {"inst": pre["candidates"][cid]["inst"], "risk_budget": b,
                              "cluster": pre["clusters"]["membership"][cid],
                              "sigma_daily_dev": sig[cid], "contract_weight": b * L / sig[cid],
                              "candidate_sha256": pre["candidates"][cid]["sha256"],
                              "params": pre["candidates"][cid]["params"]} for cid, b in bud.items()},
            "risk_scale_L": L,
            "regime_rules": "none (static); P3 regime tilt not selected (did not beat P2 on VAL after cost at MODERATE)",
            "governor": dict(pre["governor"], env_dd=lab.ENVELOPES[env][0], day_stop=0.8 * abs(lab.ENVELOPES[env][1])),
            "DEV": {k: float(row[k]) for k in ("DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "DEV_excess_vs_mb")},
            "VAL": {k: float(row[k]) for k in ("VAL_avg", "VAL_total", "VAL_max_dd", "VAL_worst", "VAL_ret_dd", "VAL_excess_vs_mb")},
        }
    rules = {
        "program": "TEST43-P", "written_before_holdout": True, "holdout_opened": False,
        "holdout_window": ["2025-10-01", "2026-05-27"],
        "evaluated_portfolios": {r: sel[r] for r in sel},
        "data_and_implementation_QA (all required before reading results)": [
            "canonical ES and MNQ 1m files pass exact SHA256 validation BEFORE parsing (ES 2b4f41b1..., MNQ 66204b12...)",
            "rebuilt DEV+VAL outputs from the full file reproduce the frozen DEV/VAL portfolio daily P&L exactly (prefix invariance)",
            "code SHA256 equal to TEST43P_FINAL_PORTFOLIOS.json 'code' section",
            "no missing RTH sessions beyond the exchange calendar; roll dates as in canonical roll map",
        ],
        "per_portfolio_acceptance (each evaluated at its frozen envelope; ALL must hold)": {
            "net_pnl": "HOLDOUT total net P&L > 0 after commission, 1-tick slippage and roll cost",
            "margin": "no intraday or overnight margin breach (IBKR fractions frozen); peak margin utilisation <= 0.5 of equity",
            "max_drawdown": "HOLDOUT MaxDD <= envelope DD (CONSERVATIVE $10k, MODERATE $15k, AGGRESSIVE $20k)",
            "worst_day": "HOLDOUT worst day >= envelope floor (CONSERVATIVE -$2k, MODERATE -$3k, AGGRESSIVE -$5k)",
            "remove_top3": "HOLDOUT average daily P&L after removing the 3 best days > 0",
            "single_day_concentration": "best single day <= 35% of HOLDOUT total net P&L",
            "matched_beta": "matched-beta excess (same average MES/MNQ exposure, constant long) is REPORTED; not a pass condition",
            "stress_report": "SLIP4 and TIMING_BRITTLENESS_STRESS reported; not pass conditions",
        },
        "decision": {"PRIMARY passes": "candidate for paper/live readiness review (still LIVE_AUTHORIZATION = NO)",
                     "PRIMARY fails, a SECONDARY passes": "report; no automatic promotion of the secondary without a new review",
                     "all fail": "TEST43-P portfolios rejected; no rescue"},
        "prohibited_after_holdout": ["parameter changes", "portfolio membership rescue", "weight / risk-budget rescue",
                                     "regime-rule rescue", "envelope or L re-calibration", "cost/margin assumption changes",
                                     "re-running the holdout with modified code"],
        "one_shot": "the holdout is opened once; results are final",
    }
    fn = f"{FZ}/TEST43P_HOLDOUT_ACCEPTANCE_RULES.json"
    json.dump(rules, open(fn, "w"), indent=1)
    rules_sha = sha(fn)
    open(fn.replace(".json", ".sha256"), "w").write(f"{rules_sha}  TEST43P_HOLDOUT_ACCEPTANCE_RULES.json\n")
    src = os.path.dirname(__file__)
    final = {
        "program": "TEST43-P multi-strategy regime ensemble", "holdout_opened": False,
        "portfolio_membership_changed_vs_V6_candidates": False, "live_authorization": False,
        "pre_val_freeze_sha256": pre_sha, "holdout_rules_sha256": rules_sha,
        "selection_rule": pre["final_selection_rule"], "selection": sel, "portfolios": ports,
        "clusters": pre["clusters"], "risk_normalisation": pre["risk_normalisation"],
        "costs": pre["costs"], "margin": pre["margin"], "envelopes": pre["envelopes"],
        "execution": "local engine computes every sleeve's virtual desired exposure and ledger; aggregation to ONE net "
                     "integer target per instrument; only the net target is sent to IBKR. TradingView/webhook = sentinel only.",
        "shadow_controls": pre["shadow_controls"],
        "code": {f: sha(os.path.join(src, f)) for f in ("t43/portfolio.py", "t43/sleeves.py", "t43/v6a.py", "t43/v6x.py",
                                                         "p02_fingerprint.py", "p03_portfolio_dev.py", "p04_pre_val_freeze.py",
                                                         "p05_val_confirm.py", "p06_final_freeze.py")},
    }
    fn2 = f"{FZ}/TEST43P_FINAL_PORTFOLIOS.json"
    json.dump(final, open(fn2, "w"), indent=1, default=float)
    final_sha = sha(fn2)
    open(fn2.replace(".json", ".sha256"), "w").write(f"{final_sha}  TEST43P_FINAL_PORTFOLIOS.json\n")
    print("PRE_VAL_FREEZE_SHA256", pre_sha); print("HOLDOUT_RULES_SHA256", rules_sha); print("FINAL_FREEZE_SHA256", final_sha)
    for r, p in ports.items():
        print(r, p["portfolio"], p["risk_envelope"], {c: round(m["contract_weight"], 3) for c, m in p["members"].items()})


if __name__ == "__main__":
    main()
