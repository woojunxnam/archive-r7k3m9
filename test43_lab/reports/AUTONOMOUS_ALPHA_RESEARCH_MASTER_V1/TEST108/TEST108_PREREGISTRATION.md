# TEST108 RANGE BUDGET / EXHAUSTION AS A CONTINUATION VETO — preregistration

Committed ALONE before any TEST108 economics.  Master prereg 319a7f6, ESP-1 applies.  Attribution: SYSTEMATIC_FORMALIZATION (Crabel / Grimes
"average range" budget; ATR-consumption heuristics), Tier 2.  NOVELTY_DELTA vs TEST50 (compression -> expansion) and TEST46/47 (range-exhaustion
REVERSAL): the budget is used only as a VETO on continuation entries, never as a reversal entry.

(TEST107 response speed / time-to-MFE: NOT_RUN_BY_RULE — no survivor and no non-duplicate STRONG_CLUE; the only STRONG_CLUE (TEST106 A2) is a
RESEARCH_DUPLICATE of ORB with ~$1/day economics.)

Continuation bases (frozen, not re-tuned):
- BASE_BRK12: fresh N = 12 upside breakout (TEST98 base event), b <= 67.
- BASE_ORB15: first close above the 09:30-09:45 OR high (TEST106 ORB comparator), 3 <= b <= 60.
Budget features at the decision bar b (causal):
- RB1 consumed range = (session high so far - session low so far) / ATR_d.
- RB2 upside consumed = (close - session low so far) / ATR_d.
4 curve definitions (2 features x 2 bases).  Causal quintiles (edges from the base events in sessions strictly before the month; 120-session warm-up).
Null RBN (state null, deliberately NOT magnitude-matched because the budget is itself a magnitude): cell mean over all valid bars in year x vt x tod3.
Coherence rule (TEST102 / TEST98): |Spearman| >= 0.9, top-minus-bottom date-clustered CI excludes 0, same sign >= 5/8 years and >= 3/4 instruments.
VETO_HAS_VALUE iff COHERENT with a NEGATIVE slope AND the top-quintile excess < 0 at a primary horizon (60 / 120 min, 16:15); the improvement of the
base mean when the top quintile is vetoed is reported (and the fraction of events removed).  A veto never creates a standalone strategy.
