# P5 STRUCTURAL GA — EXHAUSTIVE ENUMERATION — preregistration (alone)

Eligibility: (A) NESTED ML Tier B: C1_R1_TRAPPED_UNION, C7_L1_SWH60; (B) strong repeated deterministic clue with sufficient sample and coherent
heterogeneity: C4_L2_FAMILY (15/15 positive level x horizon cells in TEST104, 5,722 events).  Others: not GA-eligible (recorded).
Every structural space fits the budget -> EXHAUSTIVE ENUMERATION (no stochastic GA).  All genomes logged.
Genes (broad structural buckets only):
- C1: constituent group subset of {P2, L2, A3} (7 non-empty) x TOD {any, <10:30, 10:30-14:00, >14:00} x vt {any, 0, 1, 2} x VWAP state
  {any, close > VWAP, close <= VWAP} x exit {60 min, 120 min, 16:15}  = 1,008 genomes.
- C4: level permission {all, PDL, PWL, ORL, SWL60, L2H} x TOD 4 x vt 4 x VWAP 3 x exit 3 = 864 genomes.
- C7: market permission {all, drop ES, drop NQ, drop YM, drop RTY} x TOD 4 x vt 4 x VWAP 3 x exit 3 = 720 genomes.
Total 2,592 (<= 1,250 per family, <= 8,000 global).
Nested per outer fold (O1-O5): using PAST data only.  Train-inner = training years except the last; inner validation = the last training year.
Fitness on train-inner (1 micro per event, base cost, daily $ over full sessions): mean of yearly avg/day - 0.5 x sd(yearly avg/day)
- 0.5 $/day per restricted gene (complexity) - 5 x max(0, corr(train-inner daily, Main) - 0.35) $/day; a genome needs >= 100 train-inner trades.
Selection: the 20 best by fitness -> the one with the highest inner-validation avg/day (>= 20 validation trades; ties -> fewer restricted genes);
if none is positive in validation the fold ABSTAINS (no trades).  The selected genome is evaluated ONCE on the outer test year.
Stitched outer metrics as in P3.  GA pass = TIER B on the stitched series AND GA_STABILITY >= 0.5, where GA_STABILITY = share of Hamming-1
neighbours (one gene changed) of each fold's selected genome whose training fitness is > 0 (averaged over folds); outer-test neighbour
positivity is reported as a diagnostic only.  A pass with stability < 0.5 = GA_OVERFIT_CLUE_ONLY.
