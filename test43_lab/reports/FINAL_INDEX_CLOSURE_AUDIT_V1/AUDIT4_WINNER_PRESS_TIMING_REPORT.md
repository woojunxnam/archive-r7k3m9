# AUDIT 4 — C2 winner press vs same-base frontload — results (prereg dacb1cb)

## 4A pure trade-level timing (no capacity)
Frontload ADD1 EV **+15.65 $/opportunity** (all 590); winner ADD1 EV +15.90 $/add when added (545 opportunities have a winner checkpoint),
+14.69 $/opportunity.  **WINNER - FRONTLOAD = -0.96 $/opportunity [-6.36, +6.93]**,
SLIP4 -0.69; -0.42 $/day; folds positive 1/5; years 2/6; instruments 2/4.
Delaying the second unit does NOT improve its dollar value.  It does halve the tail: C2-module worst trade / day -1633 (winner press) vs
-3265 (frontload); module MaxDD 6179 vs 6221; basket MAE p95 649 vs 675.

## 4B Main-capacity integration
| variant | base filled / skipped | 2nd filled / blocked | cand $/day capped | uncapped | lost to capacity | Main+ avg/day | MaxDD | worst | ret/DD | peak MNQ/MES/MYM/M2K |
|---|---|---|---|---|---|---|---|---|---|---|
| A_C2x1 | 570 / 20 | 0 / 0 | 4.96 | 6.79 | 1.83 | 156.74 | 13980 | -4728 | 0.01121 | 6/8/1/1 |
| B1_C2x2_FRONT_SEPARATE | 570 / 20 | 552 / 18 | 8.76 | 13.58 | 4.82 | 160.54 | 14464 | -4789 | 0.01110 | 6/8/2/2 |
| B2_C2x2_ALL_OR_NONE | 552 / 38 | 0 / 0 | 7.60 | 13.58 | 5.99 | 159.38 | 14464 | -4789 | 0.01102 | 6/8/2/2 |
| C_C2_WINNER_ADD1 | 570 / 20 | 508 / 18 | 8.88 | 13.16 | 4.29 | 160.65 | 14105 | -4792 | 0.01139 | 6/8/2/2 |

Decomposition: TOTAL (C - B1, capped) +0.11 $/day = PURE TIMING -0.42 + CAPACITY EFFECT +0.53
(the delayed unit is blocked less often / costs less capacity P&L: lost to capacity 4.29 vs 4.82 $/day).  Combined ret/DD C - B1 = +0.00029.
Note: the earlier PH9 'C2x2' used an all-or-none lot-2 order (B2), which loses 1.2 $/day more to capacity than a separately filled frontload (B1);
against the fair B1 comparator the winner press is only +0.11 $/day better.

**C2_WINNER_PRESS_TIMING_CLASS = CAPACITY_TIMING_VALUE** (pure timing <= 0; the small dollar edge comes from capacity), with a real RISK benefit
(worst trade/day halved, ret/DD 0.01139 vs 0.01110).  This is MANAGEMENT / EXPOSURE TIMING, not entry alpha.  ADD3 not opened.

```json
{
 "4A_PURE_TIMING": {
  "per_trade": {
   "n": 590,
   "mean": -0.964322033898324,
   "ci_lo": -6.363186725897273,
   "ci_hi": 6.933396643855833,
   "folds_pos": 1,
   "inst_pos": 2,
   "years_pos": 2,
   "years": 6,
   "slip4_mean": -0.689745762711883
  },
  "T_day": -0.41834558823530216,
  "T_slip4_day": -0.29922794117647866,
  "T_folds": {
   "O1": -1.4695652173914229,
   "O2": -2.2602390438246953,
   "O3": -1.5590438247011782,
   "O4": -2.401111111111094,
   "O5": 3.8713031161473337
  },
  "T_folds_pos": 1,
  "n_base": 590,
  "n_with_winner_checkpoint": 545,
  "front_add_ev": 15.654067796610175,
  "winner_add_ev_all_opportunities": 14.689745762711853,
  "winner_add_ev_when_added": 15.902660550458704,
  "module_front": {
   "avg_day": 13.582205882352948,
   "max_dd": 6220.819999999947,
   "worst_day": -3265.48,
   "ret_dd": 0.002183346549547015,
   "worst_trade": -3265.48,
   "mae_p95": 674.9749999999998
  },
  "module_winner": {
   "avg_day": 13.163860294117644,
   "max_dd": 6179.119999999983,
   "worst_day": -1632.74,
   "ret_dd": 0.0021303778360215824,
   "worst_trade": -1632.74,
   "mae_p95": 649.4375
  }
 },
 "4B_CAPACITY": {
  "A_C2x1": {
   "counts": {
    "base_filled": 570,
    "base_skipped": 20,
    "second_filled": 0,
    "second_blocked": 0,
    "second_no_parent": 0
   },
   "capped_cand_day": 4.962647058823532,
   "uncapped_cand_day": 6.791102941176474,
   "pnl_lost_to_capacity_day": 1.8284558823529418,
   "avg_day": 156.74216338640454,
   "incr": 4.9626470588235065,
   "slip4_avg_day": 155.01826632758102,
   "max_dd": 13979.562365192993,
   "worst_day": -4727.67999999997,
   "ret_dd": 0.01121223678479871,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 1,
   "peak_M2K": 1,
   "route_A": false,
   "route_B": true
  },
  "B1_C2x2_FRONT_SEPARATE": {
   "counts": {
    "base_filled": 570,
    "base_skipped": 20,
    "second_filled": 552,
    "second_blocked": 18,
    "second_no_parent": 20
   },
   "capped_cand_day": 8.760455882352947,
   "uncapped_cand_day": 13.582205882352948,
   "pnl_lost_to_capacity_day": 4.8217500000000015,
   "avg_day": 160.53997220993398,
   "incr": 8.760455882352943,
   "slip4_avg_day": 157.13188397463986,
   "max_dd": 14463.759999999933,
   "worst_day": -4788.919999999968,
   "ret_dd": 0.01109946322463417,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 2,
   "peak_M2K": 2,
   "route_A": true,
   "route_B": false
  },
  "B2_C2x2_ALL_OR_NONE": {
   "counts": {
    "base_filled": 552,
    "base_skipped": 38,
    "second_filled": 0,
    "second_blocked": 0,
    "second_no_parent": 0
   },
   "capped_cand_day": 7.595617647058831,
   "uncapped_cand_day": 13.582205882352948,
   "pnl_lost_to_capacity_day": 5.986588235294117,
   "avg_day": 159.37513397463985,
   "incr": 7.595617647058816,
   "slip4_avg_day": 156.0067516216987,
   "max_dd": 14463.759999999933,
   "worst_day": -4788.919999999968,
   "ret_dd": 0.011018928271392819,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 2,
   "peak_M2K": 2,
   "route_A": true,
   "route_B": false
  },
  "C_C2_WINNER_ADD1": {
   "counts": {
    "base_filled": 570,
    "base_skipped": 20,
    "second_filled": 508,
    "second_blocked": 18,
    "second_no_parent": 19
   },
   "capped_cand_day": 8.87538970588235,
   "uncapped_cand_day": 13.163860294117644,
   "pnl_lost_to_capacity_day": 4.288470588235294,
   "avg_day": 160.6549060334634,
   "incr": 8.875389705882355,
   "slip4_avg_day": 157.36372956287514,
   "max_dd": 14105.269999999935,
   "worst_day": -4791.919999999968,
   "ret_dd": 0.011389707962588744,
   "peak_MNQ": 6,
   "peak_MES": 8,
   "peak_MYM": 2,
   "peak_M2K": 2,
   "route_A": true,
   "route_B": true
  }
 },
 "DECOMPOSITION": {
  "TOTAL_WINNER_MINUS_FRONTLOAD_capped_day": 0.11493382352940351,
  "PURE_TIMING_uncapped_day": -0.41834558823530443,
  "CAPACITY_EFFECT_day": 0.533279411764708,
  "check_T_4A": -0.41834558823530216,
  "additive": "YES (definitionally; interaction absorbed in CAPACITY_EFFECT)",
  "ret_dd_C_minus_B1": 0.00029024473795457445
 },
 "C_minus_A_capped_day": 3.912742647058818,
 "C2_WINNER_PRESS_TIMING_CLASS": "CAPACITY_TIMING_VALUE"
}
```
