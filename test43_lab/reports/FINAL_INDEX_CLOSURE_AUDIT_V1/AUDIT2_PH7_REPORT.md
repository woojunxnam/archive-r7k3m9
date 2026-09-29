# AUDIT 2 — PH7 fresh-recovery eligibility correction — results (prereg bc400e5)

Original signal n 31 -> corrected 31; removed by < 30 min: 0 (same structural reason as Audit 1).  Results identical to PH7:
A FRESH_SIGNAL_RECOVERY +20.38 $/add (SLIP4 +16.66, n 31); B MATCHED_GENERIC_UNDERWATER +10.83; **A - B = +9.56 $/add [-12.4, +32.6]**, 3/5 folds,
3/4 instruments, 3/6 years; C FIRST_GENERIC_UNDERWATER (control) +8.33 [-6.8, +23.0], SLIP4 +4.27 (n 519).

**PH7_CORRECTED_RECOVERY_SPECIFICITY = GENERIC_AVERAGING** -> no exit research; recovery / DCA alpha research CLOSED.

```json
{
 "original_signal_n": 31,
 "corrected_signal_n": 31,
 "removed_lt_30min": 0,
 "generic_control_pool_n": 10901,
 "match_levels": {
  "0": 29,
  "1": 2
 },
 "SIGNAL_ADD": {
  "n": 31,
  "mean": 20.38096774193532,
  "ci_lo": -6.762096774193557,
  "ci_hi": 46.570907258064324,
  "folds_pos": 4,
  "inst_pos": 4,
  "years_pos": 4,
  "years": 6,
  "slip4_mean": 16.655161290322418
 },
 "MATCHED_GENERIC": {
  "n": 31,
  "mean": 10.82545411525024,
  "ci_lo": -6.182565528613396,
  "ci_hi": 29.425955886669662,
  "folds_pos": 4,
  "inst_pos": 3,
  "years_pos": 5,
  "years": 6,
  "slip4_mean": 7.099647663637335
 },
 "SIGNAL_MINUS_MATCHED": {
  "n": 31,
  "mean": 9.555513626685084,
  "ci_lo": -12.378913897962613,
  "ci_hi": 32.61902932905684,
  "folds_pos": 3,
  "inst_pos": 3,
  "years_pos": 3,
  "years": 6,
  "slip4_mean": 9.555513626685084
 },
 "FIRST_GENERIC": {
  "n": 519,
  "mean": 8.331772639691689,
  "ci_lo": -6.7538916243701586,
  "ci_hi": 23.038879119255157,
  "folds_pos": 4,
  "inst_pos": 3,
  "years_pos": 4,
  "years": 6,
  "slip4_mean": 4.273969171483597
 },
 "PH7_CORRECTED_RECOVERY_SPECIFICITY": "GENERIC_AVERAGING"
}
```
