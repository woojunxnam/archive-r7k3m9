# T44_14 XGBoost specification

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.

Presets (predeclared, no search): {"XGB_SHALLOW": {"max_depth": 2, "learning_rate": 0.03, "n_estimators": 400, "min_child_weight": 50, "reg_lambda": 10.0, "subsample": 1.0, "colsample_bytree": 1.0}, "XGB_REGULARIZED": {"max_depth": 3, "learning_rate": 0.03, "n_estimators": 400, "min_child_weight": 100, "reg_lambda": 30.0, "subsample": 0.7, "colsample_bytree": 0.7}, "XGB_VERY_REGULARIZED": {"max_depth": 1, "learning_rate": 0.02, "n_estimators": 200, "min_child_weight": 200, "reg_lambda": 50.0, "subsample": 0.7, "colsample_bytree": 0.7}}. Early stopping on the last 20% (chronological) of each training window. Same target/features/walk-forward/usages as Ridge.
Final fit: `out/t44/freeze/xgb_final.json` sha256 bfb02c2928d02529...
