# AUDIT 3 — NR1 / NR3 strictly historical causal null — results (prereg 05a17c8)

| def | n | raw R (ATR) | causal-null excess [CI] | old within-year excess | years | inst | raw $/day | SLIP4 $/day | folds | class |
|---|---|---|---|---|---|---|---|---|---|---|
| NR1_L5 | 42,375 | -0.0003 | -0.0014 [-0.0041, +0.0012] | -0.0029 | 4/8 | 0/4 | -49.77 | -150.86 | 0/5 | NR1_CAUSAL_REJECT |
| NR1_L20 | 39,760 | -0.0022 | -0.0041 [-0.0068, -0.0014] | -0.0060 | 2/8 | 0/4 | -65.41 | -160.06 | 0/5 | NR1_CAUSAL_REJECT |
| NR3_PREHOLIDAY | 244 | +0.0506 | +0.0328 [-0.0783, +0.1435] | +0.0400 | 4/8 | 4/4 | +2.03 | +1.45 | 3/5 | NR3_CAUSAL_CLUE |

(NR3 n 244 vs 248 in PH10: 4 early events have < 20 prior control sessions and receive no causal null.)  NR1 fallback: 97% primary cell.
The causal null shrinks both excess estimates toward zero but changes no sign or class: NR1 stays rejected (reversal / cost-dominated);
NR3 stays a small-sample clue (raw 2.03 $/day, remove-top3 -767, not Tier B) — no stress run (not an economic candidate).

```json
{
 "NR1_L5": {
  "n": 42375,
  "R": -0.0002964898590465475,
  "x": -0.0014130816558518811,
  "ci_lo": -0.004141206071189251,
  "ci_hi": 0.0011940921433949057,
  "years_pos": 4,
  "years": 8,
  "inst_pos": 0,
  "cost_atr": 0.010960344616303679,
  "old_within_year_x": -0.0028694190993550435,
  "fallback": {
   "0": 41110,
   "1": 905,
   "2": 360
  },
  "econ": {
   "avg_day": -49.77328676470598,
   "slip4_avg_day": -150.85674264705895,
   "folds_pos": 0,
   "trades": 33208,
   "tier_b": false,
   "max_dd": 73169.02000000016
  },
  "class": "NR1_CAUSAL_REJECT"
 },
 "NR1_L20": {
  "n": 39760,
  "R": -0.002163391651279389,
  "x": -0.004052163326380802,
  "ci_lo": -0.00678096310736098,
  "ci_hi": -0.0014142305118315646,
  "years_pos": 2,
  "years": 8,
  "inst_pos": 0,
  "cost_atr": 0.011005205725487313,
  "old_within_year_x": -0.006043488083236849,
  "fallback": {
   "0": 38903,
   "1": 857
  },
  "econ": {
   "avg_day": -65.40643382352941,
   "slip4_avg_day": -160.06415441176472,
   "folds_pos": 0,
   "trades": 31150,
   "tier_b": false,
   "max_dd": 95686.73999999992
  },
  "class": "NR1_CAUSAL_REJECT"
 },
 "NR3_PREHOLIDAY": {
  "n": 244,
  "R": 0.05055984370982821,
  "x": 0.032754966173791776,
  "ci_lo": -0.07834546755951774,
  "ci_hi": 0.14351359656907714,
  "years_pos": 4,
  "years": 8,
  "inst_pos": 4,
  "cost_atr": 0.011495858288421866,
  "old_within_year_x": 0.03997871915490038,
  "fallback": {
   "0": 233,
   "1": 11,
   "-1": 4
  },
  "econ": {
   "avg_day": 2.0276985294117584,
   "slip4_avg_day": 1.445345588235288,
   "folds_pos": 3,
   "trades": 192,
   "tier_b": false,
   "max_dd": 2602.7100000000023,
   "remove_top3": -766.7000000000071,
   "worst_fold": -2.1232861189801655
  },
  "class": "NR3_CAUSAL_CLUE"
 }
}
```
