# PH6 structural grammar search (exhaustive) — results (prereg f85f648)

3,600 genomes enumerated; nested per outer fold.  **GRAMMAR_FAIL**: stitched 0.89 $/day, SLIP4 -3.58, remove-top3 negative, stability 0.27; fold picks jump between TOUCH / LN2 / C2 (no stable grammar).

Selection-exposed diagnostic (NOT a result): the best FIXED genomes on the stitched window are the high-frequency location-null triggers held to 16:15 (LN2 sweep-reclaim all-day 32.4 $/day, high-vol 42.7) — thousands of trades whose per-trade SLIP4 is negative (PH4: LN2 X1615 SLIP4 -2.00 $/trade); this is generic intraday long exposure, not a mechanism.  All 3,600 genome series are stored (not committed) for the PH9 full-selection diagnostics.

```json
{
 "n_genomes": 3600,
 "picks": {
  "O1": [
   "TOUCH",
   "any",
   "any",
   "any",
   "any",
   "room",
   "XSTRUCT"
  ],
  "O2": [
   "LN2",
   "any",
   "high",
   "am",
   "conf2",
   "any",
   "X120"
  ],
  "O3": [
   "LN2",
   "any",
   "high",
   "am",
   "conf2",
   "any",
   "X120"
  ],
  "O4": [
   "C2",
   "any",
   "any",
   "any",
   "any",
   "any",
   "XSTRUCT"
  ],
  "O5": [
   "C2",
   "any",
   "any",
   "any",
   "any",
   "any",
   "X1615"
  ]
 },
 "stability": 0.27,
 "class": "GRAMMAR_FAIL",
 "avg_day": 0.8926838235293775,
 "trades": 1455,
 "usd_per_trade": 0.8343986254295199,
 "slip4_avg_day": -3.5775367647059175,
 "y2022": 2789.1800000000044,
 "folds_pos": 3,
 "worst_fold": -17.855019762846034,
 "fold_O1": -17.855019762846034,
 "fold_O2": 11.112270916334678,
 "fold_O3": -0.6913147410358568,
 "fold_O4": 5.8528571428571246,
 "fold_O5": 4.648130311614731,
 "max_dd": 7333.36000000002,
 "worst_day": -1989.3800000000015,
 "remove_top3": -4241.490000000045,
 "corr_main": 0.19347024190747436,
 "coverage": 0.021448788254024412,
 "main_avg_day": 151.77951632758104,
 "main_max_dd": 13936.302365192969,
 "main_worst": -4666.439999999971,
 "main_ret_dd": 0.01089094598770062,
 "comb_avg_day": 152.67220015111042,
 "comb_max_dd": 17479.29000000009,
 "comb_worst": -4727.67999999997,
 "comb_ret_dd": 0.008734462335204099,
 "tier_b": false,
 "top10_fixed_genomes_selection_exposed": [
  [
   [
    "LN2",
    "any",
    "high",
    "any",
    "any",
    "any",
    "X1615"
   ],
   42.72
  ],
  [
   [
    "LN2",
    "any",
    "any",
    "any",
    "conf2",
    "any",
    "X1615"
   ],
   33.14
  ],
  [
   [
    "LN2",
    "any",
    "any",
    "any",
    "any",
    "any",
    "X1615"
   ],
   32.41
  ],
  [
   [
    "LN2",
    "any",
    "high",
    "any",
    "conf2",
    "any",
    "X1615"
   ],
   31.33
  ],
  [
   [
    "LN2",
    "any",
    "high",
    "am",
    "any",
    "any",
    "X1615"
   ],
   29.9
  ],
  [
   [
    "LN2",
    "any",
    "any",
    "am",
    "conf2",
    "any",
    "X1615"
   ],
   27.39
  ],
  [
   [
    "LN1",
    "any",
    "any",
    "any",
    "any",
    "any",
    "X1615"
   ],
   26.66
  ],
  [
   [
    "LN2",
    "any",
    "any",
    "am",
    "conf2",
    "room",
    "X1615"
   ],
   23.31
  ],
  [
   [
    "LN1",
    "any",
    "high",
    "any",
    "any",
    "any",
    "X1615"
   ],
   23.18
  ],
  [
   [
    "LN2",
    "any",
    "high",
    "am",
    "conf2",
    "any",
    "X1615"
   ],
   22.67
  ]
 ]
}
```
