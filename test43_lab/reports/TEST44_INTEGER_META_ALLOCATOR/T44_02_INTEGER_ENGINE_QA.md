# T44_02 Integer engine QA

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.


* `src/t43/intport.py`: integer MES/MNQ targets only (REQUEST / TRACK / RESIDUAL modes), one shared $150k account, DD tiers on a
  $ATR budget, time-based rearm (20 sessions; the TEST43 recovery-only rearm locked integer portfolios in reduced mode 88% of the time),
  day-loss cut, margin with the overnight fraction when the next bar is not RTH, next-bar-open execution, 1 tick, $0.62/side, roll cost.
* QA: a single sleeve requested at its own integer desired position with governor off reproduces the standalone sleeve exactly
  (ES_robust_A_MOD_1 $117,831.63; MNQ_robust_C_CON_0 $75,666.50 on 2019-05..2026-05).
* Frozen TEST43 portfolios reproduced on the extended data: CHAMPION_CONTROL_V1 former-holdout net +$9,690.71, D0 -$7,164.29 (exact).
* Bars rebuilt from the hash-verified canonical files and truncated at 2026-05-27 (hard assertion in `t44_common.py`).
