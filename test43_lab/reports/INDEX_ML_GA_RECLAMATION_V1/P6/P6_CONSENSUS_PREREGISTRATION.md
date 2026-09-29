# P6 ML + GA CONSENSUS, MATCHED-BETA CONTROL, OVERFIT DIAGNOSTICS — preregistration (alone)

Arms per family (all on STITCHED_HISTORICAL_OUTER_OOS, 1 micro per event):
A TAKE_ALL (deterministic frozen population, frozen 16:15 exit); B ML NESTED_SELECTED (P3); C GA stitched (P5; C1, C4, C7 only);
D ML inside the GA-selected population (C1, C4, C7): in each fold the P5 genome restricts BOTH training and test events, then K1
RIDGE_T1_TOP50 (fixed, simplest ML) is fitted exactly as in P3 on that restricted training set; fold abstains when the GA fold abstained.
E (GA on ML score buckets): NOT RUN (declared).
Complexity order A < C < B < D.  Consensus choice per family: among arms passing TIER B, the simplest one, unless a more complex Tier-B arm's
avg/day exceeds the simpler one's by more than 1/0.9 (simpler < 90% of complex), in which case the more complex arm is chosen.
MATCHED-BETA CONTROL (mandatory): for every trade, control $ = mean 16:15 (or the arm's exit horizon) long return, in ATR units, over ALL valid
5m decision bars of the same instrument x calendar year x vt x tod3 (engine arrays), converted to micro dollars minus base cost.  Report
matched-beta excess avg/day (total and 2022).  An arm with matched-beta excess avg/day <= 0 is labelled BETA_CARRIER (exposure, category E),
never alpha; it may still be carried to P9 only under the label EXPOSURE / RISK route, not ALPHA.
CONSENSUS_CANDIDATE = consensus arm passing TIER B with matched-beta excess > 0.
OVERFIT DIAGNOSTICS per family (consensus arm), trial set = TAKE_ALL + K1..K8 stitched daily series (+ GA genome count in N):
- Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014): N = 9 + genomes of that family, V = variance of daily Sharpe across the 9 series,
  skew / kurtosis of the chosen series, T = stitched days.
- PBO by CSCV (Bailey et al.): 16 contiguous blocks of the 9-series matrix, all C(16,8) splits, PBO = share of splits where the in-sample best
  series ranks below the median out of sample.
- White Reality Check: stationary bootstrap (mean block 10 days, 2,000 reps, seed 7) of the max mean over the 9 series vs a zero benchmark; p-value.
If any cannot be computed (degenerate matrix), OVERFIT_DIAGNOSTIC_NOT_COMPUTED with the reason.
