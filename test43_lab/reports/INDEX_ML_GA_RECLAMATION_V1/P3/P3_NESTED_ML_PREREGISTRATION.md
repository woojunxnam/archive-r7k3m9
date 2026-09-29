# P3 NESTED WALK-FORWARD ML — preregistration (alone)

Populations: CANDIDATE_BANK_V1 C1-C8 (all Tier A YES; frozen horizon 16:15 for all), events from CANDIDATE_EVENTS.parquet with a finite 16:15
target.  REF_A2 / REF_ORB15: take-all reference only (0 ML configs).  Trades: 1 micro per event (MES / MNQ / MYM / M2K), entry = frozen engine entry
(next legal open after the event bar), exit = engine 16:15 coordinate; base cost and SLIP4 as in the program prereg; overlapping events are all
counted (concurrency reported, capacity applied in P7).
Features: the 28 frozen CORE features + 4 instrument one-hots + constituent one-hots (C1: 7, C4: 5) -> <= 39 columns.  Median imputation and
standardisation fitted on the training window only.
Targets: ML-T1 = net micro dollars at 16:15 (regression); ML-T2 = 1{net dollars > 0} (classification).  ML-T3 ranking = selection of the top
fraction by model score, with the score cutoff = the (1 - fraction) quantile of the refit model's scores on its own training window.
ML-T4 barrier race: NOT RUN (declared).
Configs (8 per family, identical across families; 64 total <= 80):
 K1 RIDGE_T1_TOP50  K2 RIDGE_T1_TOP25  K3 ENET_T1_TOP50  K4 LOGIT_T2_TOP50  K5 LOGIT_T2_TOP25  K6 HGB_T1_TOP50  K7 HGB_T1_TOP25  K8 HGBCLS_T2_TOP50
Hyperparameter grids (inner-validation choice): Ridge alpha {1, 10, 100, 1000}; ElasticNet alpha {0.01, 0.1, 1} x l1_ratio 0.5 on y / sd(y_train);
Logistic C {0.01, 0.1, 1}; HGB (regressor / classifier) max_depth 3, learning_rate 0.05, min_samples_leaf 50, l2 1.0, max_iter {100, 200}.
Chronology: outer folds O1-O5 (program prereg); inner validation = last calendar year of the training window, train-inner = earlier years;
the hyperparameter maximising inner-validation selected net dollars is refit on the full training window and applied ONCE to the outer test year.
NESTED_SELECTED series: in every outer fold the config (K1-K8) with the highest inner-validation selected net dollars is chosen inside training
and applied to the test year -> this series is the one tested against TIER B.  The best-of-8 stitched config is reported as
SELECTION_EXPOSED_BEST_OF_8 only.  Take-all control reported for every family.
Metrics on STITCHED_HISTORICAL_OUTER_OOS (2021-01-01..2026-05-27, all full sessions as days): avg/day, $/trade, trades, SLIP4 avg/day, 2022,
folds positive (5), worst fold, MaxDD, worst day, remove-top3 (total after removing the 3 best days), corr Main (same days), coverage,
peak concurrent micros.  AUC / R2 diagnostic only.
TIER B (ML_ECONOMIC_CANDIDATE) on the NESTED_SELECTED series: avg/day > 0, SLIP4 > 0, >= 3/5 folds positive, remove-top3 > 0, worst fold
>= -2 x |avg/day|, >= 150 trades, coverage >= 10%.
