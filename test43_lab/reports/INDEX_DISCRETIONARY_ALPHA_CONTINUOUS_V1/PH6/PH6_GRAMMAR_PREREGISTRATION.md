# PH6 STRUCTURAL DISCRETIONARY GRAMMAR SEARCH (EXHAUSTIVE) — preregistration (alone)

Data: PH4 exit dataset (PH3 triggers, frozen exits, base / SLIP4 $), PH2 atlas state at the event bar.  Structural genes only:
TRIGGER (10): C2 (= D1B u D1B_P), D1, D2, D3, D7, D8, LN1 (support reclaim), LN2 (sweep reclaim), LN3 (resistance break), TOUCH (support touch-hold).
CONTEXT: HTF direction {any, up50 = 1} x vol {any, vt in {0, 1}, vt = 2} x TOD {any, b < 30 (before 12:00), b >= 30}.
CONFLUENCE: {any, conf_sup_15 >= 2}.  ROOM: {any, upside room in the causal top tercile or no known resistance} (tercile edges from events of sessions
strictly before the month, pooled, >= 50 prior events).  EXIT: {X60, X120, X1615, XRES, XSTRUCT}.
10 x 2 x 3 x 3 x 2 x 2 x 5 = 3,600 genomes (<= 6,000; <= 10,000 -> exhaustive, no GA).  Management is NOT a grammar gene (PH7 handles it).
Nested per outer fold (reclamation P5 rules): fitness on train-inner = mean yearly avg/day - 0.5 x sd(yearly) - 0.5 $/day per restricted gene
- 5 x max(0, corr(train daily, Main) - 0.35); >= 100 train-inner trades; top 20 -> best inner-validation avg/day (>= 20 trades, > 0; ties -> fewer
restricted genes); else the fold abstains.  Stitched outer metrics; TIER B; GA_STABILITY = share of Hamming-1 neighbours with training fitness > 0
(>= 0.5 required) else GRAMMAR_OVERFIT_CLUE_ONLY.  Also stored: every genome's fixed stitched outer daily series (3,600 x days) for the
full-selection DSR / PBO / Reality Check in PH9.  Simplicity rule: a selected genome within 90% of a more complex one is preferred.
