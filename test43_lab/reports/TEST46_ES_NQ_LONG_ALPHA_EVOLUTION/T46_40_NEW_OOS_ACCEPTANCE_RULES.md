# T46_40 New-OOS acceptance rules

sha256 **b0c16814f78b197a5d0414ee597e1212568ef05fe51546c228f01da1bf0d97a8**

```json
{
 "program": "TEST46",
 "pre_oos_freeze_sha256": "e0724e207aea45c16416207379a540e4e44550434eeaefb4440911732dd334ce",
 "written_before_TEST46_new_oos": true,
 "TEST46_NEW_OOS_START": "2026-09-28",
 "challenger": "NONE",
 "if_NONE": "no TEST46 promotion test is run; shadow clues may be monitored descriptively only",
 "evaluation_gate": {
  "min_sessions": ">= 120 completed RTH sessions on/after TEST46_NEW_OOS_START (TEST44 rule unchanged)",
  "data": "canonical ES/MNQ per TEST44_OOS_DATA_PROTOCOL; the 2026-05-28..2026-09-27 quarantine is never evaluated for TEST46"
 },
 "absolute_pass (C43 + candidate)": {
  "net_pnl": "> 0",
  "max_dd": "<= $15,000",
  "worst_day": ">= -$3,000",
  "remove_top3_avg": "> 0",
  "best_day": "<= 35% of net",
  "SLIP4_net": "> 0",
  "margin": "no breach"
 },
 "promotion_over_C43": {
  "net": ">= 1.10 x C43",
  "ret_dd": ">= C43",
  "matched_beta_excess": ">= C43",
  "session_matched_excess": ">= C43",
  "overnight_lock": "no unacceptable locked exposure (TEST45 governor)"
 },
 "prohibited_after_opening": [
  "any parameter / feature / threshold / model change",
  "switching to a shadow clue"
 ],
 "live_authorization": "NO"
}
```

