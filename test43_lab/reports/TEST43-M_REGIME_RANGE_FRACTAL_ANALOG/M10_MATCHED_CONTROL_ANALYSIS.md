# M10 Matched-control analysis

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


Control = same instrument, era (year), regime tier, vol tercile, 30-min clock bucket, broad range-position quintile.
Deltas: future return, MFE, MAE, first passage (+0.5 before -0.5 ATR, conditional on resolution).

## Mechanism stability across the four intraday scales (non-NONE rows)
| inst | ev | metric | n_pass_pos | n_pass_neg | sign_agree_of_4 | strong_opposite | t_by_hz | verdict |
|---|---|---|---|---|---|---|---|---|
| MNQ | DB_FAILED_ACCEPT | d_ret60 | 1 | 0 | 3 | 0 | 120m:-0.1; 15m:2.4; 30m:3.2; 60m:0.5 | SINGLE_HORIZON |
| MNQ5 | DB_ACCEPT | d_ret60 | 2 | 0 | 4 | 0 | 120m:0.7; 15m:2.6; 30m:2.5; 60m:1.4 | STABLE_POS |
| MNQ5 | DB_BREAK | d_ret60 | 1 | 0 | 4 | 0 | 120m:0.3; 15m:2.6; 30m:2.0; 60m:1.6 | SINGLE_HORIZON |
| MNQ5 | L_FAILED_RECLAIM | d_fp05 | 1 | 0 | 4 | 0 | 120m:0.4; 15m:1.4; 30m:0.7; 60m:2.3 | SINGLE_HORIZON |
| MNQ5 | L_RETEST | d_ret60 | 1 | 0 | 4 | 0 | 120m:0.8; 15m:1.4; 30m:1.2; 60m:2.8 | SINGLE_HORIZON |
| MNQ5 | L_SWEEP | d_ret60 | 3 | 0 | 3 | 0 | 120m:-0.0; 15m:2.7; 30m:2.6; 60m:2.3 | STABLE_POS |
| MNQ5 | UB_REENTRY | d_ret60 | 0 | 1 | 3 | 0 | 120m:-0.6; 15m:-0.8; 30m:0.1; 60m:-2.5 | SINGLE_HORIZON |
| MNQ5 | UB_RESUMED | d_ret60 | 0 | 1 | 3 | 0 | 120m:-3.3; 15m:0.8; 30m:-0.3; 60m:-0.8 | SINGLE_HORIZON |
| MNQ5 | U_FAILED_RECLAIM | d_fp05 | 1 | 0 | 2 | 0 | 120m:0.5; 15m:-1.3; 30m:2.7; 60m:-0.5 | SINGLE_HORIZON |
| MNQ5 | U_FAILED_RETEST | d_ret60 | 0 | 1 | 3 | 0 | 120m:-0.7; 15m:0.2; 30m:-1.4; 60m:-2.6 | SINGLE_HORIZON |

Placebo-calibrated critical |t|: ES 2.80, MNQ 2.65, 5m 2.19. After calibration the share
of informative rows equals the false-positive rate. Nothing adds information beyond regime + volatility + clock +
location controls: not sweep progression, breakout progression, nested alignment, or analog similarity.

