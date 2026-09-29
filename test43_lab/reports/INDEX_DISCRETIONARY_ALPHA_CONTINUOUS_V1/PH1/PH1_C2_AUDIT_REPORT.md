# PH1 C2 winner-add specificity audit — results (prereg 0702ab8)

**C2_WINNER_ADD_SPECIFICITY = GENERIC_WINNER_PRESS -> C2 frozen as C2_GENERIC_WINNER_PRESS.**

- Fresh-signal winner ADD1: +14.59 $/add (n 197, SLIP4 +10.45).
- Matched generic winner checkpoints (same instrument / vol / TOD / elapsed / unrealised P&L / remaining terciles): +30.08 $/add [CI 20.9, 39.5].
- Signal minus matched: **-13.26 $/add** [CI -31.5, +4.2], 1/5 folds, 1/6 years positive -> the independent bullish signal adds NO information (if anything it selects worse add points).
- Generic first winner checkpoint ADD1: +15.90 $/add [CI +2.3, +30.5], SLIP4 +11.79, 4/5 folds -> pressing a C2 winner is valuable in itself (GENERIC WINNER PRESS = position sizing on C2 winners, not signal alpha).

FINAL_SELECTION_OVERFIT_DIAGNOSTIC (whole reclamation chain, 130 stored series, N = 2,722 incl. GA genomes): selected C2+MGMTx1 increment DSR **0.27**, PBO **0.84**, White RC p **0.155** -> after accounting for the full search path, the C2 small-diversifier result is NOT distinguishable from selection luck (limitation: genome-level series not stored).

```json
{
 "n_trades": 590,
 "n_checkpoints": 24088,
 "n_winner_checkpoints": 13006,
 "n_signal_adds": 197,
 "match_levels": {
  "0": 169,
  "1": 19,
  "-1": 5,
  "2": 4
 },
 "C_FRESH_SIGNAL_WINNER_ADD": {
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
 "MATCHED_GENERIC_CONTROL": {
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
 "B_GENERIC_WINNER_ADD_FIRST": {
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
 "ALL_GENERIC_WINNER_CHECKPOINTS": {
  "n": 13006,
  "mean": 14.160834230355238,
  "ci_lo": 2.0911238389971363,
  "ci_hi": 27.00000089121825,
  "folds_pos": 3,
  "inst_pos": 3,
  "years_pos": 4,
  "years": 6,
  "slip4_mean": 9.994487928648333
 },
 "C2_WINNER_ADD_SPECIFICITY": "GENERIC_WINNER_PRESS",
 "C2_FREEZE": "C2_GENERIC_WINNER_PRESS",
 "FINAL_SELECTION_OVERFIT_DIAGNOSTIC": {
  "status": "COMPUTED_WITH_LIMITATION (genome-level series not stored; N includes 2,592 genomes, V from the stored matrix)",
  "matrix_series": 130,
  "N_trials": 2722,
  "selected": "P9_C2+MGMTx1",
  "daily_sharpe": 0.040752463648105156,
  "sr0": 0.056835856942066144,
  "DSR": 0.2650256740812048,
  "PBO": 0.8383061383061383,
  "reality_check_p": 0.155
 }
}
```
