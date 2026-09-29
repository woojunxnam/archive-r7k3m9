# PH1 C2 WINNER-ADD SPECIFICITY AUDIT + MANAGEMENT OVERFIT RE-AUDIT — preregistration (alone)

Base population: the frozen C2_P2_FAILED_FIRST take-all stitched outer trades used in INDEX_ML_GA_RECLAMATION_V1 P8 (590 trades,
2021-01-01..2026-05-27, 1 micro, entry FP[5b+5], exit engine 16:15 coordinate, pre-capacity).  No C2 retuning.
Checkpoints: every completed 5m bar k of the trade with 5k+4 >= entry minute and 5(k+1)+5 <= exit minute - 30 (>= 30 min of legal holding left).
A checkpoint is a WINNER checkpoint if close[k] > UNIT1 entry (the P8 profit rule).  Hypothetical ADD1 = entry at FP[5k+5] -> frozen C2 exit.
Arms: A NO_ADD; B GENERIC_WINNER_ADD = ADD1 at the FIRST winner checkpoint of each trade; C FRESH_SIGNAL_WINNER_ADD = the frozen P8 definition
(first independent bank event {C3, C5, C6, C7, C8} after entry and before exit, taken only if close at its decision bar > UNIT1 entry).
MATCHED CONTROL for each C add: generic winner checkpoints (all winner checkpoints of all C2 trades that are NOT independent-event bars) in the
same cell instrument x vt x TOD tercile (b < 30 / 30-53 / >= 54) x elapsed-bars tercile x unrealised-PnL/ATR_d tercile x remaining-bars tercile;
tercile edges CAUSAL (from checkpoints of sessions strictly before the month; >= 50 prior checkpoints else pooled-history edges are unavailable
and the event is matched at the next fallback level).  Minimum 10 control checkpoints; fallback (1) drop vt, (2) drop instrument.  The control
value is the cell mean of ADD1 return in ATR_d units, converted with the signal trade's ATR_d x point value minus the same costs.
PRIMARY: mean over C adds of (signal ADD1 $ - matched generic ADD1 $); base cost and SLIP4; date-clustered 95% CI (2,000 reps, seed 7);
positive years; instruments; outer folds O1-O5; n.  Also the unmatched generic arm B EV (and its SLIP4, folds).
Classification (frozen):
- SIGNAL_SPECIFIC_WINNER_ADD: matched excess > 0 AND (CI lower > 0 OR (>= 4/5 folds AND >= 3/4 instruments positive)) AND signal ADD1 SLIP4 EV > 0.
- GENERIC_WINNER_PRESS: not signal-specific AND arm B EV > 0, SLIP4 EV > 0, >= 3/5 folds positive.
- NO_ADD_VALUE otherwise.
C2 freeze: C2_SIGNAL_WINNER_ADD / C2_GENERIC_WINNER_PRESS / C2_BASE_ONLY (neither) / C2_REJECTED_MANAGEMENT_BUT_BASE_SURVIVES (if add arms negative).
MANAGEMENT OVERFIT RE-AUDIT (FINAL_SELECTION_OVERFIT_DIAGNOSTIC): joint matrix of stitched daily INCREMENT series over the whole reclamation
chain that exists on disk: 64 ML configs + 8 take-alls + 2 references + 3 GA stitched series + P8 management baskets (3 bases x 4 arms) +
45 P9 portfolio increments (portfolio minus Main).  DSR of the selected series (P9 FRONTIER_B increment) with N = matrix size + 2,592 GA genomes
(genome series not stored: conservative N, V from the matrix); PBO (CSCV, 16 blocks) and White Reality Check (stationary bootstrap) on the
matrix.  Stated limitation: genome-level series and per-fold hyperparameter paths are not in the matrix.
