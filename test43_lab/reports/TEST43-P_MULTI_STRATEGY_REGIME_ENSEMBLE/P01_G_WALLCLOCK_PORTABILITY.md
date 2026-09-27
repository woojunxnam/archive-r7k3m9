# P01 ES_r2_G_AGG_0 wall-clock portability

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


## Audit of v6x intraday quantities
| quantity | class | treatment |
|---|---|---|
| microDBLookback, strengthBuildBars, addCooldownBars, oppositeSideCooldownBars, antiStallBars, targetDecayBars, repairLookback, repairLifeBars, coreRotationAgeBars, rfLookback | A: time (bars of 3m) | converted: bars_new = round(bars_3m * 3 / barMinutes), never rounded to 0 when live (G: targetDecayBars 88 = 264 min -> 53 bars at 5m; oppositeSideCooldownBars 8 = 24 min -> 5 bars) |
| rolling 15/30/60m RTH highs/lows (hard-coded 5/10/20 bars) | A: time | now round(15/30/60 / barMinutes) bars (ring buffer 64) |
| trim decision bar (hard-coded 16:09 bar = close 16:12) | A: clock | first bar whose close >= 16:12 |
| buy window end (bar open <= 15:54), late-session repair restore (15:48+), last-RTH trim (bar open >= 15:57) | A: clock | expressed on bar CLOSE time (identical on 3m) |
| regimeLen, ddRearmLen, tier EMAs/SMAs, 5-day range | B: completed RTH sessions | NOT converted |
| ATR14, RSI2, W%R2, 2-bar patterns, next-bar-open fill | C: bar-native indicator / execution semantics | not converted (same as Pine on the chart timeframe); documented limitation |

New parameters appended (defaults = native 3m): barMinutes, refMinutes, fillDelayBars (TIMING_BRITTLENESS_STRESS only).
The frozen G parameters are untouched.

## Results (DEV+VAL; frozen parameters)
| test | DV_total | DEV_avg_daily | DEV_max_dd | DEV_worst_day | DEV_excess_vs_mb | VAL_avg_daily | VAL_max_dd | VAL_excess_vs_mb | Y2022_avg_daily | Y2022_max_dd | fills | friction | avg_pos | avg_on_pos | peak_margin_util | margin_breach | DEV_env | VAL_env |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OLD_3M_FROZEN_KERNEL | 157263.7 | 92.5 | 14099.5 | -4922.4 | 39.0 | 134.2 | 7400.6 | 44.1 | 3.2 | 14099.5 | 1011 | 6814.3 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| WALLCLOCK_3M | 157263.7 | 92.5 | 14099.5 | -4922.4 | 39.0 | 134.2 | 7400.6 | 44.1 | 3.2 | 14099.5 | 1011 | 6814.3 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| WALLCLOCK_ES_5M | 146583.4 | 82.9 | 20532.3 | -4384.3 | 29.4 | 150.1 | 8229.4 | 59.9 | -21.5 | 14347.0 | 993 | 6717.0 | 5.9 | 5.8 | 0.1 | False | EXPLORATORY | AGGRESSIVE |
| NAIVE_ES_5M_NO_CONVERSION(ref) | 145943.2 | 82.7 | 18601.4 | -4384.3 | 29.0 | 148.8 | 8229.4 | 58.7 | -19.7 | 14347.0 | 988 | 6660.9 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| TRANSFER_MNQ_3M | 118601.1 | 76.8 | 23431.7 | -5137.4 | 22.4 | 48.3 | 10310.8 | -40.6 | -45.1 | 19664.4 | 1081 | 3073.3 | 3.3 | 3.3 | 0.1 | False | EXPLORATORY | AGGRESSIVE |
| TRANSFER_MNQ_5M | 139273.0 | 79.4 | 25340.8 | -4561.8 | 24.8 | 138.4 | 9072.5 | 47.1 | -47.2 | 17844.6 | 1033 | 2938.9 | 3.4 | 3.3 | 0.1 | False | EXPLORATORY | AGGRESSIVE |
| SLIP2 | 152771.2 | 90.0 | 14217.0 | -4957.4 | 36.4 | 129.8 | 7528.1 | 39.7 | 1.0 | 14217.0 | 1011 | 11369.3 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| SLIP4 | 144098.7 | 85.0 | 14452.0 | -5027.4 | 31.5 | 121.4 | 7783.1 | 31.3 | -3.6 | 14452.0 | 1011 | 20479.3 | 5.9 | 5.8 | 0.1 | False | EXPLORATORY | AGGRESSIVE |
| COMM1.00 | 155941.4 | 91.8 | 14135.2 | -4933.0 | 38.2 | 132.8 | 7439.4 | 42.8 | 2.5 | 14135.2 | 1011 | 8199.0 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| TIMING_BRITTLENESS_STRESS | 159342.4 | 96.3 | 13633.3 | -4661.1 | 42.7 | 116.4 | 7729.4 | 30.4 | -4.2 | 13633.3 | 1059 | 6821.8 | 5.9 | 5.7 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| MARGINx1.5_INTRADAY | 157263.7 | 92.5 | 14099.5 | -4922.4 | 39.0 | 134.2 | 7400.6 | 44.1 | 3.2 | 14099.5 | 1011 | 6814.3 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |
| ON_MARGINx2 | 157263.7 | 92.5 | 14099.5 | -4922.4 | 39.0 | 134.2 | 7400.6 | 44.1 | 3.2 | 14099.5 | 1011 | 6814.3 | 5.9 | 5.8 | 0.2 | False | AGGRESSIVE | AGGRESSIVE |
| ES_5M_SLIP4 | 133199.6 | 75.2 | 22489.8 | -4448.0 | 21.7 | 137.5 | 8611.9 | 47.4 | -28.4 | 14722.0 | 993 | 20187.0 | 5.9 | 5.8 | 0.1 | False | EXPLORATORY | AGGRESSIVE |
| ES_5M_TIMING_BRITTLENESS_STRESS | 152716.9 | 83.8 | 19051.6 | -4909.9 | 30.3 | 176.4 | 8475.2 | 86.2 | -33.1 | 15540.8 | 1011 | 6627.3 | 5.9 | 5.8 | 0.1 | False | AGGRESSIVE | AGGRESSIVE |

**Regression:** the wall-clock kernel reproduces the frozen 3m run fill-for-fill (1011 fills, identical positions and
equity). **Gate:** 5m keeps 90% of DEV return and positive matched-beta excess but DEV MaxDD $20.5k exceeds the $20k
AGGRESSIVE envelope; ATR$-scaled MNQ transfer breaches the envelope ($23.4k) and has negative VAL excess at 3m.
Cost / timing / margin stresses pass. Same standard as the V6A downgrades (ES F-AGG, MNQ E-AGG) -> G is a SHADOW /
CONTROL sleeve, not capital-eligible. Not retuned.

