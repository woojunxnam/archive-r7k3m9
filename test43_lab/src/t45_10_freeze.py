"""TEST45 Phases 27-28: pre-OOS freeze + new-OOS acceptance rules (written BEFORE any data after 2026-05-27 exists here).
TEST44 authorities are verified unchanged and are not modified."""
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_overlay as O  # noqa: E402

FZ = os.path.join(C.T45, "freeze")
T44 = {"out/t44/freeze/TEST44_PRE_OOS_FREEZE.json": "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4",
       "out/t44/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json": "2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236",
       "out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.json": "f50902babcbc848574984abb59c4e9cd435e2a3d20878a66955686b6429d7cc3",
       "src/t44_oos_evaluator.py": "dde908ea03ae93d31f827c21366f7a2088c8027ab711f86d64dbce37fafa3b29",
       "out/p/freeze/TEST43P_FINAL_PORTFOLIOS.json": "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7"}


def spec_for(name):
    if name.startswith("V6_STATE_CARRY|"):
        _, inst, t, thr = name.split("|")
        return O.G(inst=inst, c_on=1, c_time=t, c_base=0, c_feat="champ_pos", c_dir=1, c_thr=float(thr.split(">")[1]), c_boost=1)
    raise ValueError(name)


def clean(x):
    return {k: (str(v) if isinstance(v, float) and not np.isfinite(v) else v) for k, v in x.items()}


def main():
    os.makedirs(FZ, exist_ok=True)
    for p, h in T44.items():
        assert C.sha(os.path.join(C.ROOT, p)) == h, f"TEST44/43 authority changed: {p}"
    assert not os.path.exists(os.path.join(C.T45, "new_oos")), "new-OOS directory exists"
    sel = json.load(open(os.path.join(C.T45, "final", "T45_24_final_selection.json")))
    final = sel["FINAL_TEST45_CHALLENGER"]
    audit = pd.read_csv(os.path.join(C.T45, "final", "T45_24_candidate_rule_audit.csv"))
    code = {os.path.relpath(f, C.ROOT): C.sha(f) for f in sorted(glob.glob(os.path.join(C.SRC, "t45_*.py")))}
    for f in ("t43/instruments.py", "t43/bars.py", "t43/portfolio.py", "t44_common.py", "t44_alloc.py", "p03_portfolio_dev.py"):
        code["src/" + f] = C.sha(os.path.join(C.SRC, f))
    fz = {"program": "TEST45 ES/NQ session alpha + multi-model ML + genetic evolution",
          "written_before_new_oos_data": True, "research_data_end": "2026-05-27", "new_oos_start": "2026-05-28",
          "test44_authorities_verified_unchanged": T44,
          "data": {i: {"file": C.DATA[i][0], "sha256": C.DATA[i][1]} for i in C.INSTS},
          "FINAL_TEST45_CHALLENGER": final,
          "structure": "CHAMPION_CONTROL_V1 (unchanged, TEST43-P SECONDARY_2 P1_CLUSTER_EQUAL_RISK|CONSERVATIVE) + TEST45 overlay in the SAME $150k account",
          "execution_clock": {"CASH_REFERENCE_CLOSE": "16:00:00 ET = close of the 1m bar end-stamped 16:00",
                              "LAST_ALLOWED_EXECUTION": "16:15:00 ET",
                              "LAST_CAUSAL_EXECUTION_BAR": "decision on bars end-stamped <= 16:14, fill at the OPEN of the 1m bar end-stamped 16:15 (first trade after 16:14:00)",
                              "LOCKED_OVERNIGHT_INTERVAL": "from the 16:15-bar-open fill to the next RTH open (open of the 1m bar end-stamped 09:31); no strategy order in between",
                              "NEXT_EXECUTABLE_OPEN": "09:30 ET; a pre-planned exit fills at the RTH open print; any decision using the open fills at the open of the bar end-stamped 09:32",
                              "generic_rule": "decision at minute T uses bars end-stamped <= T; fill at the open of bar T+1 +/- 1 tick; entries never use an earlier price; if the bar is missing, the entry is skipped (forward fallback <= 3 min)",
                              "early_close_sessions": "entries whose bar does not exist are skipped; reductions may fill at the last existing bar",
                              "overnight_path_features": "NONE", "overnight_trading": "NONE (position locked)"},
          "overlay_spec": clean(spec_for(final)) if final != "NONE" else None,
          "overlay_description": ("At the decision minute (bar end-stamped c_time) read the Champion's MNQ/MES target IN EFFECT at that minute "
                                  "(3m bar open-stamped at c_time).  If it is > c_thr contracts, the overlay targets +1 contract of that instrument, "
                                  "filled at the open of the next 1m bar, carried LOCKED overnight and exited by a pre-planned order at the next RTH "
                                  "open print.  Otherwise the overlay is flat.") if final != "NONE" else None,
          "integer_mapping": {"per_instrument_overlay_target": "0 / 1", "max_overlay_contracts": O.QMAX, "combined_with_champion": "separate virtual sleeve; broker net target = champion target + overlay target (no fractional execution)"},
          "lock_governor": {"LOCK_K_ATR": O.LOCK_K, "LOCK_BUDGET_usd": O.LOCK_BUDGET,
                            "rule": "sum(q * LOCK_K * ATR14_RTH(prev) * $/pt) over locked overlay inventory <= budget, else cut the largest"},
          "costs": {"commission_per_side": C.COMM, "slippage_ticks_per_side": 1, "stress": "SLIP4", "roll": "2 sides x (commission + 1 tick) when carried into a contract-switch session (rolled during RTH before the lock)"},
          "margin": {"source": "IBKR reference (t43/instruments.py) scaled by raw notional", "overnight_check": "before 16:14 decision: champion + overlay overnight margin <= 0.5 x equity"},
          "features": {"champ_pos@t": "Champion (frozen) target position in effect at decision minute t (3m bar open-stamped t; 16:14 -> 16:12)",
                       "no_other_features": final.startswith("V6_STATE_CARRY") if final != "NONE" else None},
          "model_training_refit": "NONE - deterministic rule; no parameters are refit; the Champion is the frozen TEST43-P implementation",
          "code_sha256": code,
          "shadow_only (not evaluated for promotion)": ["all other TEST45 overlays, ML models, GA/GP genomes (see T45_24 audit)"],
          "shadow_forward_monitoring (REPORT ONLY, frozen now, cannot be promoted by the coming OOS)": {
              "V6_STATE_CARRY|MNQ|15:45|champ>0": clean(O.G(inst="MNQ", c_on=1, c_time="15:45", c_base=0, c_feat="champ_pos", c_dir=1, c_thr=0.0, c_boost=1)),
              "V6_STATE_CARRY|BOTH|16:00|champ>1": clean(O.G(inst="BOTH", c_on=1, c_time="16:00", c_base=0, c_feat="champ_pos", c_dir=1, c_thr=1.0, c_boost=1)),
              "reason": "concept recurred in every nested GA/GP outer fold; failed the predeclared rule (R3 corr/R4 worst-day, resp. R5 vs unconditional carry)"},
          "selection_audit": {"n_candidates": sel["n_candidates"], "n_eligible": sel["n_eligible"],
                              "eligible": audit[audit.ELIGIBLE].candidate.tolist()},
          "new_oos_data_acquired": False, "new_oos_opened": False, "live_authorization": "NO"}
    fj = os.path.join(FZ, "TEST45_PRE_OOS_FREEZE.json")
    json.dump(fz, open(fj, "w"), indent=1, default=str)
    hf = C.sha(fj)
    rules = {"program": "TEST45", "written_before_new_oos_data": True, "pre_oos_freeze_sha256": hf,
             "benchmark": "CHAMPION_CONTROL_V1 (unchanged)", "challenger": f"CHAMPION_CONTROL_V1 + {final}" if final != "NONE" else "NONE",
             "evaluation_gate": {"TEST44_session_count_rule": "UNCHANGED (>= 120 completed RTH sessions from 2026-05-28 per the frozen TEST44 16:00 rule)",
                                 "TEST45_execution_data_completeness": "additionally, each counted session must contain in BOTH ES and MNQ the 1m bars end-stamped at the "
                                 "decision minute, decision+1, 16:00, 16:15 and the next session's 09:31; sessions lacking them are reported, not silently filled",
                                 "data_protocol": "TEST44_OOS_DATA_PROTOCOL (f50902ba...) unchanged; hash-validate before parsing"},
             "absolute_pass (Champion + overlay, same account)": {"net_pnl": "> 0", "margin": "no breach (peak <= 0.5 equity, overnight included)",
                                                                   "max_dd": "<= $15,000", "worst_day": ">= -$3,000", "remove_top3_avg": "> 0",
                                                                   "best_day": "<= 35% of net P&L", "SLIP4_net": "> 0"},
             "promotion_over_CHAMPION (all required)": {"net_pnl": ">= 1.10 x Champion OOS net P&L", "ret_dd": ">= Champion OOS return/MaxDD",
                                                        "matched_beta_excess": ">= Champion per day", "session_matched_beta_excess": ">= Champion per day",
                                                        "overnight_lock": "lock governor never breached; worst locked night of the overlay >= -$1,500 (historical worst 1 MNQ locked night -$2,006 is a STRESS reference)"},
             "not_a_promotion_reason": "reducing exposure; a pass qualifies only for a paper/live readiness review",
             "reported_only": ["overlay standalone P&L", "incremental $/day", "correlation to Champion", "loss-day overlap", "locked-night distribution",
                               "sessions skipped for data completeness", "SLIP4", "rolling 3m"],
             "prohibited_after_opening": ["any change of decision time, threshold, instrument, quantity, governor, costs", "switching to a shadow candidate",
                                          "re-labelling the OOS window"],
             "if_FINAL_is_NONE": "no TEST45 promotion test is run; shadow overlays may be reported descriptively only",
             "live_authorization": "NO"}
    fr = os.path.join(FZ, "TEST45_NEW_OOS_ACCEPTANCE_RULES.json")
    json.dump(rules, open(fr, "w"), indent=1)
    hr = C.sha(fr)
    open(os.path.join(FZ, "TEST45_PRE_OOS_FREEZE.sha256"), "w").write(f"{hf}  TEST45_PRE_OOS_FREEZE.json\n")
    open(os.path.join(FZ, "TEST45_NEW_OOS_ACCEPTANCE_RULES.sha256"), "w").write(f"{hr}  TEST45_NEW_OOS_ACCEPTANCE_RULES.json\n")
    print("TEST45_PRE_OOS_FREEZE_SHA256", hf); print("TEST45_NEW_OOS_RULES_SHA256", hr); print("FINAL", final)


if __name__ == "__main__":
    main()
