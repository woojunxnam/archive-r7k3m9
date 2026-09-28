# T47_47 New-OOS acceptance rules

sha256 = 55bd409506ed676e9f78c851de59bea6ffed42cac73b732b86a8530ba37e172d

```json
{
 "test": "TEST47",
 "TEST47_NEW_OOS_START": "2026-09-28",
 "rule_for_start": "first full RTH session strictly after the freeze timestamp",
 "freeze_timestamp_utc": "2026-09-28T03:24:50+00:00",
 "challenger": "NONE",
 "if_challenger_NONE": "No TEST47 strategy is evaluated on the new OOS. The window may only be used to (a) re-confirm the NO-EDGE finding for the frozen C2 / C4 / C6 controls exactly as frozen (report-only, no promotion path), (b) monitor C43. No re-tuning, no new NASSI variant may be selected on it; any new idea is a NEW HYPOTHESIS requiring its own freeze.",
 "report_only_monitors": [
  "C2 [ES]",
  "C2 [MNQ]",
  "C4 [ES]",
  "C4 [MNQ]",
  "C6 [ES]",
  "C6 [MNQ]"
 ],
 "excluded_intervals": {
  "2026-05-28..(TEST47_NEW_OOS_START - 1)": "never used for TEST47 research, selection or validation (TEST46 LC03 exposure window)"
 },
 "minimum_evaluation": ">= 120 full RTH sessions before any conclusion",
 "live_authorization": "NO",
 "portfolio_membership_changed": "NO"
}
```

