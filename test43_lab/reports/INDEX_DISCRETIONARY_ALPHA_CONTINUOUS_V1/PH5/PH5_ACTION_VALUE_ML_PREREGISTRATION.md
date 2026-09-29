# PH5 ACTION-VALUE DATASETS + RESPONSE-SPEED MANAGEMENT + DISCRETIONARY-EMULATOR ML — preregistration (alone)

All targets are INCREMENTAL net dollars caused by an action (1 micro; SKIP / NO_ADD / HOLD baselines = 0 incremental).
Features (<= 50): the frozen P1 CORE features (rp_bank FEATS, 28) + instrument one-hots (4) + atlas state at the decision bar (up_room,
down_room, no_res, conf_sup_15, sup_type, sup_touch, sup_age; 7) + for checkpoint tasks the causal trade state (current return, MFE so far,
MAE so far, new-high-since-entry flag, bars elapsed, bars remaining, retention above the structural level; 7) -> <= 46.
ACTION DATASETS
- ENTRY (TAKE vs SKIP): every PH3 trigger event; value = net $ at the frozen 16:15 exit.
- HOLD vs EXIT_NOW (response speed): C2 trades (all C2 events 2019-2026) at checkpoints 10 / 20 / 30 min after entry (completed bars b+2 / b+4 / b+6);
  hold value = (16:15 exit price - FP at the next legal open after the checkpoint) x point value (exit costs cancel).
- ADD1 vs NO_ADD: C2 winner checkpoints and underwater checkpoints (PH1 checkpoint machinery, >= 30 min left); value = hypothetical ADD1 net $.
- EXIT architecture: per C2 trade the five frozen exits of PH4; value = $ of the chosen exit minus $ of X1615.
DETERMINISTIC RESPONSE-SPEED RULE (frozen): EXIT_IF_NOT_WORKING at checkpoint t in {10, 20, 30} = exit when the current return <= 0; incremental
value = - hold value on those checkpoints.  Response curves: hold value by causal quintile of current return at each checkpoint (coherence rule).
ML (nested outer folds; hyperparameters on the inner-validation year; scaling / imputation on training only):
- MODEL E (entry): populations D2, D3, D7, D8, C2; models RIDGE (T1 net $, take top 50% of training-score quantile), LOGIT (T2 net $ > 0, top 50%),
  HGB (T1, top 50%) -> 15 configs.
- MODEL H (hold): C2 checkpoints at 10 / 20 / 30 min; RIDGE / LOGIT / HGB; policy EXIT when predicted hold value < 0 (Ridge / HGB) or
  P(hold > 0) < 0.5 (Logit) -> 9 configs.
- MODEL A (add): C2 winner checkpoints and C2 underwater checkpoints, RIDGE only first eligible checkpoint per trade where predicted add value > 0
  (policy ADD1) plus LOGIT and HGB -> 6 configs.
- MODEL X (exit architecture): RIDGE per exit (5 outputs) on C2 trades; choose the exit with the highest predicted $ -> 3 configs (RIDGE / HGB /
  ElasticNet).  Total 33 ML configs (<= 96).
Evaluation: STITCHED_HISTORICAL_OUTER_OOS incremental $/day vs the default action (take-all / always hold / never add / X1615), SLIP4 where
costs change, folds positive, n.  A policy has ACTION_VALUE if incremental avg/day > 0, SLIP4 > 0 where applicable, >= 3/5 folds positive.
