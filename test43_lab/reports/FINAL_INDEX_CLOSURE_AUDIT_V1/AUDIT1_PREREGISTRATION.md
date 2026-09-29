# AUDIT 1 — PH1 winner-add eligibility correction (preregistration, alone)

Defect: PH1 (da_ph1.py) built generic winner checkpoints with MG.checkpoints(T, min_left=30) but fresh-signal rows with min_left=0, so signal
adds with < 30 min of legal holding left had no possible matched control.  Correction: signal rows are taken from the SAME min_left=30 checkpoint
set (a signal whose first-independent-event checkpoint has < 30 min left is REMOVED — not replaced by a later checkpoint).  Frozen: C2 take-all
population (590 trades), independent-event set {C3, C5, C6, C7, C8}, first-event rule, winner definition (close > entry at the decision close),
next-open ADD1, 16:15 exit, matching cells (instrument x vt x TOD tercile x causal terciles of elapsed / unrealised P&L / remaining), fallbacks,
min 10, costs, bootstrap (2,000, seed 7).  Classification = the original PH1 rule (SIGNAL_SPECIFIC_WINNER_ADD / GENERIC_WINNER_PRESS / NO_ADD_VALUE).
Output: original n, corrected n, removed-by-<30-min n, generic control n, match fallback counts, fresh EV / SLIP4, matched EV, signal-minus-matched
with CI, folds, years, instruments -> PH1_CORRECTED_WINNER_SPECIFICITY.
