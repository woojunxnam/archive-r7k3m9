# AUDIT 3 — NR1 / NR3 strictly historical causal null (preregistration, alone)

Signals and raw realized economics unchanged (PH10 8547410 definitions).  Only the null changes.
NR1 (NR1_L5, NR1_L20; 12 half-hour slots; signal = prior-L same-slot mean > 0): for each event (instrument, date, slot) the null is the mean slot
return over ALL sessions strictly BEFORE the event date in cell instrument x vt x slot; if < 20 prior observations -> fallback instrument x slot ->
slot (all instruments, dates strictly before).  NR3 (pre-holiday RTH open -> 16:15): null = mean over PRIOR NON-pre-holiday sessions of the same
instrument x vt; fallback instrument; min 20.
Report per definition: n, raw gross return, raw net $ / day, SLIP4, causal-null excess with date-clustered CI (2,000, seed 7), years, instruments,
folds (stitched outer years), comparison to the PH10 (within-year) null.  Classes: *_CAUSAL_REJECT (excess <= 0), *_CAUSAL_CLUE (excess > 0 but the
exploration gate fails), *_CAUSAL_ECONOMIC_CANDIDATE (gate: excess > 0, >= 5/8 years, >= 3/4 instruments, gross >= 0.9 x cost AND raw stitched Tier B)
-> one standard stress run only.  No new thresholds, no ML.
