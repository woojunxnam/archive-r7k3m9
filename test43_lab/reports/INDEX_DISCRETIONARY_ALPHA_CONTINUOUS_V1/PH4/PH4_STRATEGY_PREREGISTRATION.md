# PH4 STRATEGY ECONOMICS + FROZEN EXIT SET — preregistration (alone)

Exit dataset (ALL PH3 trigger definitions, used later by PH5 / PH6): for every event, 1 micro, entry FP[5b+5]; five frozen exits:
X60 (engine h12), X120 (h24), X1615 (engine 16:15), XRES = exit at the next legal open after the first completed 1m bar whose close >= the
nearest known resistance R* at the event bar (else 16:15; no known resistance -> 16:15), XSTRUCT = exit at the next legal open after the second
consecutive completed 5m close below the event's structural level (D1 / D2: the frozen failed level L; D3 / D7 / LN3: the broken level; C2 / D1B /
D8 / TOUCH / LN1 / LN2: the lowest low of the 12 bars before the event) — not an optimised stop; else 16:15.  Base-cost and SLIP4 dollars stored.
Strategy phase (only for ECONOMIC_RESEARCH_CANDIDATE populations of PH3): D1B is a C2 derivative without location value, so the strategy
population is the frozen C2 population (D1B u D1B_P = C2_P2_FAILED_FIRST).  Per outer fold the exit with the best TRAINING-window mean net
$/trade is chosen (nested) and applied to the test year; all five fixed-exit series are also reported (selection-exposed).
Stresses (stitched window, capacity with Main priority as in the reclamation P7): base, SLIP4, +1 bar delay, missed 20%, remove-top3, folds,
2022, peaks, margin, turnover.  STRUCTURAL-EXIT QUESTION: XSTRUCT vs X1615 on identical entries (paired difference per trade, date-clustered CI).
Routes A / B / C vs Main as before.  C2 is not retuned: only the frozen exit set is compared.
