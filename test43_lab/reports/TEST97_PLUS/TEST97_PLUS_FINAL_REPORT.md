# TEST97+ momentum burst / breakout / trend-following factory - final

```json
{
 "TEST97_STATUS": "CLOSED - no portfolio survivor; momentum-burst thesis universe NOT declared exhausted",
 "PREREG": {
  "WAVE1": "d6fb544b139415ab40fdedeb10f7e932746eeb7712e8f2cd408f9348d510ea5e",
  "WAVE2": "9136fe6c164c793a9163ee6322577520d9ab9271f9644db1e2336c7f17d2a06c",
  "PHASE3": "985955dfe2cc72cc08068af7de40dfaab94308e2adaf907dcec37a6438d2f6d4",
  "WAVE3": "0e027b595b2a1bf3238021af8085569178ed84ae0c37c00f53dbea008ff55d0a"
 },
 "RESEARCH_DATA_END": "2026-05-27",
 "CURRENT_MAIN": "T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO",
 "T66_FROZEN_REPRODUCTION": "PASS",
 "T66_ROBUSTNESS": "FRAGILE",
 "WAVE1_FAMILIES_TESTED": 10,
 "WAVE1_EVENT_VARIANTS": 43,
 "WAVE1_RESPONSE_CURVE_BINS": 35,
 "WAVE1_SURVIVING_MECHANISMS": "3 nominal EVENT_EDGE (M04_F, M04_D, M05 shallow n=35); none tradeable alone",
 "WAVE2": "persistence ladder = magnitude (0 vs multi-bar null); FT2 (breakout + STRONG follow-through) keeps EVENT_EDGE vs 2-bar magnitude null (+0.037 ATR/60m, CI>0, 6/8 yrs), graded by follow-through strength",
 "WAVE3": "volatility breakout inverted-U (peak k=0.3, fails CI); daily NR/inside-day adds little to ORB; first pullback worse than chase",
 "BEST_PORTABLE_MECHANISM": "FT2 event (ES, NQ, RTY positive; YM negative at 60 min) - event level only",
 "BEST_NQ_SPECIFIC_MECHANISM": "none (NQ carries the largest excess in M02 / M04 but no NQ-only survivor; NQ has the lowest cost in ATR units, 0.005)",
 "BEST_ES_SPECIFIC_MECHANISM": "FT2_X1615_ES (5/5 folds, SLIP4 +0.64, delay +1.32 $/day @1 MES) - fails sample (135) and plateau",
 "BEST_YM_SPECIFIC_MECHANISM": "none",
 "BEST_RTY_SPECIFIC_MECHANISM": "none",
 "STRONG_BAR_HAS_ALPHA": "NO (single bar ~ magnitude; range > 3 ATR5 turns negative)",
 "BREAKOUT_ADDS_ALPHA": "WEAK / monotone in window N (2 -> 60 bars) but CI includes 0; scale family, not separate mechanisms",
 "COMPRESSION_ADDS_ALPHA": "NO (intraday, burst-size matched) ; daily NR / inside-day: small, inconsistent",
 "FOLLOW_THROUGH_ADDS_TIMING_VALUE": "INFORMATION YES (+0.013 ATR/60m confirmed vs unconfirmed at the same minute; FT2 strongest) / TIMING VALUE vs original entry NO",
 "FIRST_PULLBACK_ADDS_VALUE": "NO (worse than chase)",
 "SECOND_LEG_EFFECT": "only very shallow pullbacks (<38.2%), n = 35-68 -> clue, not established",
 "FRESH_SECOND_SIGNAL_ADDS_VALUE": "NO (second signal after failure weaker than the first)",
 "RECOVERY_STACK_ADDS_VALUE": "NO (ADD1 EV negative in ES / NQ / YM / RTY on FT2 events)",
 "WINNER_PYRAMID_ADDS_VALUE": "MIXED / NO (ADD1 +13.6 ES, +16.2 NQ, negative YM / RTY; ADD2+ <= 0 mostly)",
 "EXHAUSTION_THRESHOLD_STRUCTURE_FOUND": "PARTIAL (bar range > 3 x ATR5 and body >= .9 with large range negative; vol-breakout inverted-U peak k = 0.3)",
 "HTF_ALIGNMENT_ADDS_VALUE": "PARTIAL (above VWAP / open aligned +0.02 ATR at 60 min vs small non-aligned set; 60m-trend alignment none)",
 "TOD_SPECIALIZATION_FOUND": "NO robust (persistence strongest 09:30-11:00, noisy)",
 "OVERNIGHT_INCREMENTAL_ALPHA": "NOT OPENED (no intraday strategy survivor)",
 "ML_RUN": "NO (no base event >= 600 with edge)",
 "GA_RUN": "NO",
 "BEST_NEW_CANDIDATE": "FT2_X1615_4INDEX (virtual, 1 micro each) - FAILS plateau (close-pos 0.9 neighbour 11% of base)",
 "MAIN_PLUS_NEW_CANDIDATE_AVG_DAY": 146.65409087048258,
 "MAIN_PLUS_NEW_CANDIDATE_MAXDD": 13136.030000000144,
 "MAIN_PLUS_NEW_CANDIDATE_WORST_DAY": -4666.439999999971,
 "MAIN_PLUS_NEW_CANDIDATE_RET_DD": 0.0111642627849114,
 "MAIN_RET_DD": 0.0102758294430884,
 "NEW_CANDIDATE_INCREMENT_AVG_DAY": 3.447024698449166,
 "PORTFOLIO_SURVIVOR": "NO",
 "TOTAL_TEST97_VARIANTS": 570,
 "TOTAL_TEST97_ML_CONFIGS": 0,
 "TOTAL_TEST97_GA_GENOMES": 0,
 "binding_constraint": "60-min conditional excess of the best events (0.01-0.04 ATR_d) is of the same order as round-trip micro cost (0.005-0.015 ATR_d)",
 "NEXT_RESEARCH": [
  "FT2 as a preregistered forward-shadow observation (no authorization)",
  "longer-horizon (session / multi-day) versions of follow-through information where cost is small relative to move",
  "NQ-cost-advantaged event execution (lowest ATR cost) with a preregistered NQ-only branch",
  "cross-index FT2 synchrony (follow-through in several indices at once) - distinct from closed Q2"
 ],
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO"
}
```

Detail: T97_W1_*.md, T97_W1_FAILURE_CLUE_ANALYSIS.md, T97_W2_EVENTS.md, T97_P3_FT2_STRATEGY.md, T97_W3_EVENTS.md; ledger out/t97/TEST97_RESEARCH_LEDGER.csv

