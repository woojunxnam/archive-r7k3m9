# T44_22 New OOS acceptance rules

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

SHA256 `2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236`

```json
{
 "program": "TEST44",
 "written_before_new_oos_data": true,
 "pre_oos_freeze_sha256": "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4",
 "new_oos_window": {
  "start": "2026-05-28",
  "end": "open-ended; first evaluation after >= 120 RTH sessions, then quarterly"
 },
 "evaluated": [
  "CHAMPION_CONTROL_V1",
  "SIMPLE_INTEGER_CHALLENGER",
  "RIDGE_CHALLENGER",
  "XGBOOST_CHALLENGER"
 ],
 "integrity (before any result)": [
  "canonical OOS data hash-recorded before parsing; DEV/VAL/2026-05-27 prefix reproduces frozen daily P&L exactly",
  "code SHA256 equal to the pre-OOS freeze",
  "meta refits follow the frozen procedure only"
 ],
 "absolute_pass (each candidate, MODERATE envelope)": {
  "net_pnl": "> 0 after costs",
  "margin": "no breach; peak <= 0.5 equity",
  "max_dd": "<= $15,000",
  "worst_day": ">= -$3,000",
  "remove_top3_avg": "> 0",
  "best_day": "<= 35% of net P&L"
 },
 "promotion_over_CHAMPION (challenger must pass absolute AND all of)": {
  "ret_dd": ">= 1.25 x champion OOS return/MaxDD",
  "matched_beta_excess": ">= champion OOS matched-beta excess per day",
  "session_matched_beta_excess": ">= champion OOS session-matched-beta excess per day",
  "net_pnl": ">= 0.8 x champion OOS net P&L (no tiny-return 'win' by shrinking exposure)",
  "cost_robust": "SLIP4 net P&L > 0"
 },
 "XGB_vs_RIDGE": "XGB may be promoted only if it also beats RIDGE by >= 1.25x on OOS return/MaxDD and on net P&L",
 "reported_only": [
  "avg/day",
  "median/day",
  "remove-top-1/3/5",
  "friction",
  "contract sides",
  "turnover",
  "average/peak margin",
  "average RTH/ON contracts per symbol",
  "rolling 3m",
  "TIMING_BRITTLENESS_STRESS",
  "integer attribution per sleeve"
 ],
 "prohibited_after_opening": [
  "any parameter/feature/threshold/cap/governor change",
  "membership or model rescue",
  "re-labelling the same OOS window"
 ],
 "live_authorization": "NO (a pass only qualifies for paper/live readiness review)"
}
```
