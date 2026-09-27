# M13 Incremental exposure test (V6 finalist + TEST43-M modifier)

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


**Gate status:** no mechanism survived the information gate, so none was eligible for translation into exposure. The
overlay below is a DIAGNOSTIC on the strongest frozen candidates to show the incremental effect explicitly. The V6
candidates are untouched (base results reproduce the shortlist exactly; modifier hook `xm` in `t43/v6a.py` is a no-op at 1).
Modifier: target x {1.25, 1.5} on positive state (optional +2 contracts cap headroom, never in risk cut / DD tier),
x {0.75, 0.5} on negative state; hold 20 bars (60m) with no re-trigger while active (event), or to next decision point
(analog, HIGH/MED confidence). 10 V6A controls (ES_r2_G_AGG_0 is a v6x kernel; not overlay-compatible).

| inst | mech | variants | n_improve | median_d_avg | median_d_dd | median_d_excess | median_fills_ratio | margin_breaches |
|---|---|---|---|---|---|---|---|---|
| ES | O1_ES_LSWEEP30_UP | 20 | 0 | -8.654 | 4655.145 | -13.481 | 2.933 | 0 |
| ES | O2_ES_UPPERFAIL_DOWN | 10 | 1 | -1.84 | 67.925 | -0.517 | 1.157 | 0 |
| ES | O4_ES_ANALOG_A1 | 50 | 0 | -5.925 | 567.36 | -4.972 | 1.891 | 0 |
| MNQ | O1_MNQ_LSWEEP30_UP | 20 | 2 | -4.043 | 658.9 | -5.731 | 1.377 | 0 |
| MNQ | O3_MNQ_DOWNFAIL_LSWEEP_UP | 20 | 2 | -4.005 | 658.9 | -5.713 | 1.378 | 0 |
| MNQ | O4_MNQ_ANALOG_A1 | 50 | 12 | 0.0 | 0.0 | 0.0 | 1.056 | 0 |

Improvement = higher DEV avg/day AND DD not worse AND higher matched-beta excess. Most variants reduce net P&L and
multiply turnover 1.1-13x; the few improving cells are single candidates (+$1-4/day) with no pattern across candidates.
Full table: `M13_incremental_exposure_DEV.csv`.

