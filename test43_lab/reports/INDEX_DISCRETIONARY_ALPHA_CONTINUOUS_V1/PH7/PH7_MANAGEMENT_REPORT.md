# PH7 management with matched controls — results (prereg 9e7fe2e)

- FRESH_SIGNAL_RECOVERY (C2): ADD1 +20.38 $/add but n = 31 only; matched underwater control +10.83; signal minus matched +9.56 [-12.4, +32.6] -> NO_SIGNAL_VALUE (generic averaging); blind first-underwater ADD1 control +8.33 $/add (SLIP4 +4.27) — averaging down inside C2 is itself mildly positive (control only, never a candidate). Recovery exits not run (n < 100).
- WINNER PRESS: first-winner ADD1 +15.90 $/add [2.3, 30.5], SLIP4 +11.79, 4/5 folds, n 545; matched ANY-checkpoint ADD1 +10.35 [6.9, 13.6] -> adding to C2 at any stage is positive (the C2 base itself keeps drifting up), winner state adds +6.79 [-6.4, +20.6] -> STATE_SPECIFIC_WINNER_PRESS by the point rule (unresolved).
- Tails: worst basket day = worst single-unit day (-1,633); 2022 basket +9,666 vs unit +5,117.
- ADD2 ELIGIBLE by program sec. 41 (EV > 0, SLIP4 > 0, 4/5 folds, n 545 >= 150, matched state excess > 0, tails OK) -> PH7B ADD2 preregistered separately.

```json
{
 "A_FRESH_SIGNAL_RECOVERY": {
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
 "A_MATCHED_UNDERWATER_CONTROL": {
  "n": 31,
  "mean": 10.82545411525024,
  "ci_lo": -6.182565528613396,
  "ci_hi": 29.425955886669662,
  "folds_pos": 4,
  "inst_pos": 3,
  "years_pos": 5,
  "years": 6
 },
 "A_SIGNAL_MINUS_MATCHED": {
  "n": 31,
  "mean": 9.555513626685084,
  "ci_lo": -12.378913897962613,
  "ci_hi": 32.61902932905684,
  "folds_pos": 3,
  "inst_pos": 3,
  "years_pos": 3,
  "years": 6
 },
 "A_BLIND_FIRST_UNDERWATER_CONTROL": {
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
 "B_FIRST_WINNER_ADD": {
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
 "B_MATCHED_ANY_CHECKPOINT": {
  "n": 535,
  "mean": 10.35250743604145,
  "ci_lo": 6.9250886347452,
  "ci_hi": 13.6386228404961,
  "folds_pos": 5,
  "inst_pos": 3,
  "years_pos": 6,
  "years": 6
 },
 "B_WINNER_MINUS_MATCHED": {
  "n": 535,
  "mean": 6.793941162089388,
  "ci_lo": -6.359056770910808,
  "ci_hi": 20.60345550238099,
  "folds_pos": 4,
  "inst_pos": 2,
  "years_pos": 4,
  "years": 6
 },
 "C_TAILS": {
  "worst_unit1": -1632.74,
  "worst_basket": -1632.74,
  "basket_2022": 9665.819999999992,
  "unit1_2022": 5116.569999999994
 },
 "RECOVERY_CLASS": "NO_SIGNAL_VALUE (generic averaging)",
 "WINNER_PRESS_CLASS": "STATE_SPECIFIC_WINNER_PRESS",
 "ADD2_ELIGIBLE": true
}
```
