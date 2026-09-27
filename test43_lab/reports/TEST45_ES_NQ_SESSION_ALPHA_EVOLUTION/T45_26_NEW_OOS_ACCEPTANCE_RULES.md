# T45_26 New-OOS acceptance rules

`out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json` sha256 **76941f63465306928e535df74641a29b172c9420c9e0a69852a4f1b0ed5356da**

```json
{
 "program": "TEST45",
 "written_before_new_oos_data": true,
 "pre_oos_freeze_sha256": "185d1ef91ddffe494ce5826a5142af31644a4816bb2a4db72d110909ed1c2987",
 "benchmark": "CHAMPION_CONTROL_V1 (unchanged)",
 "challenger": "NONE",
 "evaluation_gate": {
  "TEST44_session_count_rule": "UNCHANGED (>= 120 completed RTH sessions from 2026-05-28 per the frozen TEST44 16:00 rule)",
  "TEST45_execution_data_completeness": "additionally, each counted session must contain in BOTH ES and MNQ the 1m bars end-stamped at the decision minute, decision+1, 16:00, 16:15 and the next session's 09:31; sessions lacking them are reported, not silently filled",
  "data_protocol": "TEST44_OOS_DATA_PROTOCOL (f50902ba...) unchanged; hash-validate before parsing"
 },
 "absolute_pass (Champion + overlay, same account)": {
  "net_pnl": "> 0",
  "margin": "no breach (peak <= 0.5 equity, overnight included)",
  "max_dd": "<= $15,000",
  "worst_day": ">= -$3,000",
  "remove_top3_avg": "> 0",
  "best_day": "<= 35% of net P&L",
  "SLIP4_net": "> 0"
 },
 "promotion_over_CHAMPION (all required)": {
  "net_pnl": ">= 1.10 x Champion OOS net P&L",
  "ret_dd": ">= Champion OOS return/MaxDD",
  "matched_beta_excess": ">= Champion per day",
  "session_matched_beta_excess": ">= Champion per day",
  "overnight_lock": "lock governor never breached; worst locked night of the overlay >= -$1,500 (historical worst 1 MNQ locked night -$2,006 is a STRESS reference)"
 },
 "not_a_promotion_reason": "reducing exposure; a pass qualifies only for a paper/live readiness review",
 "reported_only": [
  "overlay standalone P&L",
  "incremental $/day",
  "correlation to Champion",
  "loss-day overlap",
  "locked-night distribution",
  "sessions skipped for data completeness",
  "SLIP4",
  "rolling 3m"
 ],
 "prohibited_after_opening": [
  "any change of decision time, threshold, instrument, quantity, governor, costs",
  "switching to a shadow candidate",
  "re-labelling the OOS window"
 ],
 "if_FINAL_is_NONE": "no TEST45 promotion test is run; shadow overlays may be reported descriptively only",
 "live_authorization": "NO"
}
```

