# AUDIT 1 — PH1 winner-add eligibility correction — results (prereg e81e3fd)

Original signal n 197 -> corrected n 197; **removed by < 30 min remaining: 0**.  Reason: every independent bank event has decision bar b <= 67, so
its ADD1 fill (grid 5b+5 <= 340) always leaves >= 64 min before the 16:15 exit (grid 404); the min_left=0 construction was a latent code
inconsistency that affected no row.  Results are therefore identical to PH1:
fresh ADD1 +14.59 $/add (SLIP4 +10.45); matched generic +30.08; signal minus matched **-13.26 $/add [-31.5, +4.2]**, 1/5 folds, 1/4 instruments,
1/6 years; first generic winner ADD1 +15.90 [2.3, 30.5], SLIP4 +11.79, 4/5 folds.

**PH1_CORRECTED_WINNER_SPECIFICITY = GENERIC_WINNER_PRESS** -> signal-specific winner-add CLOSED permanently.

```json
{
 "original_signal_n": 197,
 "corrected_signal_n": 197,
 "removed_lt_30min": 0,
 "generic_control_pool_n": 12741,
 "match_levels": {
  "0": 169,
  "1": 19,
  "-1": 5,
  "2": 4
 },
 "SIGNAL_ADD": {
  "n": 197,
  "mean": 14.588680203045726,
  "ci_lo": -5.672143596974188,
  "ci_hi": 34.119274412519765,
  "folds_pos": 4,
  "inst_pos": 3,
  "years_pos": 5,
  "years": 6,
  "slip4_mean": 10.446548223350295
 },
 "MATCHED_GENERIC": {
  "n": 192,
  "mean": 30.08234013816937,
  "ci_lo": 20.94771541059076,
  "ci_hi": 39.545654837297164,
  "folds_pos": 5,
  "inst_pos": 3,
  "years_pos": 6,
  "years": 6,
  "slip4_mean": 25.91046513816937
 },
 "SIGNAL_MINUS_MATCHED": {
  "n": 192,
  "mean": -13.263746388169325,
  "ci_lo": -31.499877032818677,
  "ci_hi": 4.16961101633131,
  "folds_pos": 1,
  "inst_pos": 1,
  "years_pos": 1,
  "years": 6,
  "slip4_mean": -13.263746388169325
 },
 "FIRST_GENERIC": {
  "n": 545,
  "mean": 15.902660550458704,
  "ci_lo": 2.2868750803032105,
  "ci_hi": 30.52935208859159,
  "folds_pos": 4,
  "inst_pos": 3,
  "years_pos": 4,
  "years": 6,
  "slip4_mean": 11.787981651376136
 },
 "PH1_CORRECTED_WINNER_SPECIFICITY": "GENERIC_WINNER_PRESS"
}
```
