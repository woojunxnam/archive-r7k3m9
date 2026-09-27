# P15 Portfolio robustness (MODERATE, DEV)

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.

| portfolio | test | DEV_avg | DEV_max_dd | DEV_worst | DEV_avg_ex_top1 | DEV_avg_ex_top3 | DEV_avg_ex_top5 | PRE23_avg | P23_avg | DEV_roll3m_min | DEV_roll6m_min | DEV_roll12m_min | DEV_worst20_sessions_sum | margin_breach |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P0_FULL_UNIVERSE_EQUAL_RISK | BASE | 66.4 | 9968.5 | -2610.3 | 64.0 | 59.7 | 55.9 | 58.2 | 81.4 | -7503.5 | -8575.4 | -9009.8 | -7553.9 | False |
| P0_FULL_UNIVERSE_EQUAL_RISK | SLIP2 | 65.6 | 9941.5 | -2613.3 | 63.2 | 58.9 | 55.1 | 57.4 | 80.5 | -7520.3 | -8547.1 | -9016.3 | -7561.7 | False |
| P0_FULL_UNIVERSE_EQUAL_RISK | SLIP4 | 63.9 | 9938.8 | -2619.3 | 61.5 | 57.2 | 53.4 | 55.8 | 78.8 | -7553.8 | -8541.9 | -9080.5 | -7577.2 | False |
| P0_FULL_UNIVERSE_EQUAL_RISK | COMM1.00 | 66.0 | 9929.5 | -2611.5 | 63.6 | 59.3 | 55.5 | 57.9 | 80.9 | -7510.0 | -8536.0 | -8988.2 | -7559.2 | False |
| P0_FULL_UNIVERSE_EQUAL_RISK | TIMING_BRITTLENESS_STRESS | 63.4 | 9978.8 | -2784.1 | 61.0 | 56.7 | 53.0 | 59.5 | 70.4 | -7597.5 | -8548.1 | -9021.5 | -7383.9 | False |
| P0_FULL_UNIVERSE_EQUAL_RISK | MARGINx1.5_INTRADAY | 66.4 | 9968.5 | -2610.3 | 64.0 | 59.7 | 55.9 | 58.2 | 81.4 | -7503.5 | -8575.4 | -9009.8 | -7553.9 | False |
| P0_FULL_UNIVERSE_EQUAL_RISK | ON_MARGINx2 | 66.4 | 9968.5 | -2610.3 | 64.0 | 59.7 | 55.9 | 58.2 | 81.4 | -7503.5 | -8575.4 | -9009.8 | -7553.9 | False |
| P1_CLUSTER_EQUAL_RISK | BASE | 62.9 | 9410.5 | -2651.5 | 60.7 | 56.6 | 52.7 | 55.8 | 75.9 | -6743.8 | -8549.9 | -8887.4 | -8234.4 | False |
| P1_CLUSTER_EQUAL_RISK | SLIP2 | 62.9 | 9441.0 | -2654.2 | 60.7 | 56.6 | 52.8 | 56.3 | 75.2 | -6760.6 | -8558.9 | -8898.9 | -8242.2 | False |
| P1_CLUSTER_EQUAL_RISK | SLIP4 | 59.7 | 9851.5 | -2659.7 | 57.5 | 53.4 | 49.6 | 54.4 | 69.6 | -6853.1 | -8926.4 | -9271.4 | -8704.5 | False |
| P1_CLUSTER_EQUAL_RISK | COMM1.00 | 62.2 | 9426.8 | -2653.0 | 59.9 | 55.8 | 52.0 | 54.9 | 75.5 | -6757.2 | -8553.2 | -8891.5 | -8239.7 | False |
| P1_CLUSTER_EQUAL_RISK | TIMING_BRITTLENESS_STRESS | 62.1 | 9916.3 | -2750.8 | 60.0 | 55.9 | 52.1 | 57.9 | 70.0 | -6826.0 | -8945.7 | -9308.2 | -8079.2 | False |
| P1_CLUSTER_EQUAL_RISK | MARGINx1.5_INTRADAY | 62.9 | 9410.5 | -2651.5 | 60.7 | 56.6 | 52.7 | 55.8 | 75.9 | -6743.8 | -8549.9 | -8887.4 | -8234.4 | False |
| P1_CLUSTER_EQUAL_RISK | ON_MARGINx2 | 62.9 | 9410.5 | -2651.5 | 60.7 | 56.6 | 52.7 | 55.8 | 75.9 | -6743.8 | -8549.9 | -8887.4 | -8234.4 | False |
| P2_STATIC_DIVERSIFIED | BASE | 70.1 | 8795.9 | -2655.1 | 66.3 | 60.5 | 55.1 | 62.1 | 84.7 | -7279.9 | -7836.6 | -5829.1 | -6321.1 | False |
| P2_STATIC_DIVERSIFIED | SLIP2 | 68.5 | 9190.4 | -2657.4 | 64.7 | 59.0 | 53.6 | 60.6 | 83.1 | -7420.6 | -8250.8 | -5942.1 | -6582.6 | False |
| P2_STATIC_DIVERSIFIED | SLIP4 | 61.8 | 9218.2 | -2661.9 | 58.0 | 52.2 | 46.9 | 58.3 | 68.2 | -7617.0 | -8396.2 | -6168.1 | -6325.1 | False |
| P2_STATIC_DIVERSIFIED | COMM1.00 | 69.4 | 8780.2 | -2656.2 | 65.6 | 59.8 | 54.5 | 61.6 | 83.9 | -7342.9 | -7928.5 | -5880.7 | -6232.5 | False |
| P2_STATIC_DIVERSIFIED | TIMING_BRITTLENESS_STRESS | 78.7 | 8022.2 | -2657.9 | 75.0 | 69.2 | 64.0 | 78.1 | 79.9 | -7660.4 | -6536.6 | -5796.8 | -6445.8 | False |
| P2_STATIC_DIVERSIFIED | MARGINx1.5_INTRADAY | 70.1 | 8795.9 | -2655.1 | 66.3 | 60.5 | 55.1 | 62.1 | 84.7 | -7279.9 | -7836.6 | -5829.1 | -6321.1 | False |
| P2_STATIC_DIVERSIFIED | ON_MARGINx2 | 70.1 | 8795.9 | -2655.1 | 66.3 | 60.5 | 55.1 | 62.1 | 84.7 | -7279.9 | -7836.6 | -5829.1 | -6321.1 | False |
| P3_REGIME_ADAPTIVE_25 | BASE | 71.0 | 7699.6 | -2655.1 | 67.6 | 62.7 | 57.9 | 66.8 | 78.7 | -6933.8 | -6307.6 | -5362.9 | -6430.8 | False |
| P3_REGIME_ADAPTIVE_25 | SLIP2 | 69.5 | 7754.1 | -2657.4 | 66.2 | 61.2 | 56.5 | 65.4 | 77.1 | -7076.6 | -6355.6 | -5470.9 | -6489.3 | False |
| P3_REGIME_ADAPTIVE_25 | SLIP4 | 59.5 | 9376.2 | -2661.9 | 56.1 | 51.2 | 46.4 | 51.6 | 73.9 | -7362.1 | -8612.3 | -5686.9 | -5894.5 | False |
| P3_REGIME_ADAPTIVE_25 | COMM1.00 | 70.2 | 7720.5 | -2656.2 | 66.9 | 61.9 | 57.2 | 66.1 | 77.8 | -6998.4 | -6324.7 | -5410.7 | -6454.8 | False |
| P3_REGIME_ADAPTIVE_25 | TIMING_BRITTLENESS_STRESS | 71.4 | 7657.8 | -2657.9 | 68.1 | 63.1 | 58.4 | 70.0 | 74.1 | -7279.3 | -6287.4 | -5547.6 | -5982.0 | False |
| P3_REGIME_ADAPTIVE_25 | MARGINx1.5_INTRADAY | 71.0 | 7699.6 | -2655.1 | 67.6 | 62.7 | 57.9 | 66.8 | 78.7 | -6933.8 | -6307.6 | -5362.9 | -6430.8 | False |
| P3_REGIME_ADAPTIVE_25 | ON_MARGINx2 | 71.0 | 7699.6 | -2655.1 | 67.6 | 62.7 | 57.9 | 66.8 | 78.7 | -6933.8 | -6307.6 | -5362.9 | -6430.8 | False |
| P3_REGIME_ADAPTIVE_50 | BASE | 71.8 | 8150.5 | -2655.1 | 68.4 | 63.5 | 58.7 | 64.7 | 84.8 | -6882.7 | -7468.0 | -5118.4 | -6309.4 | False |
| P3_REGIME_ADAPTIVE_50 | SLIP2 | 70.3 | 8206.0 | -2657.4 | 67.0 | 62.0 | 57.3 | 63.3 | 83.2 | -7035.5 | -7523.5 | -5207.9 | -6373.9 | False |
| P3_REGIME_ADAPTIVE_50 | SLIP4 | 59.5 | 8708.1 | -2661.9 | 56.2 | 51.3 | 46.5 | 48.3 | 80.1 | -7341.0 | -8378.7 | -5386.9 | -6337.1 | False |
| P3_REGIME_ADAPTIVE_50 | COMM1.00 | 71.0 | 8171.0 | -2656.2 | 67.7 | 62.7 | 58.0 | 64.0 | 84.0 | -6954.9 | -7488.5 | -5154.5 | -6334.5 | False |
| P3_REGIME_ADAPTIVE_50 | TIMING_BRITTLENESS_STRESS | 72.2 | 8164.2 | -2657.9 | 68.9 | 63.9 | 59.2 | 67.7 | 80.4 | -7111.7 | -7481.7 | -5303.4 | -6021.8 | False |
| P3_REGIME_ADAPTIVE_50 | MARGINx1.5_INTRADAY | 71.8 | 8150.5 | -2655.1 | 68.4 | 63.5 | 58.7 | 64.7 | 84.8 | -6882.7 | -7468.0 | -5118.4 | -6309.4 | False |
| P3_REGIME_ADAPTIVE_50 | ON_MARGINx2 | 71.8 | 8150.5 | -2655.1 | 68.4 | 63.5 | 58.7 | 64.7 | 84.8 | -6882.7 | -7468.0 | -5118.4 | -6309.4 | False |

## Simultaneous-strategy-loss diagnostics
| portfolio | test | days_all_sleeves_lose | days_majority_lose | portfolio_avg_on_all_lose_days | portfolio_worst_on_all_lose_days | share_of_portfolio_loss_from_all_lose_days |
|---|---|---|---|---|---|---|
| P0_FULL_UNIVERSE_EQUAL_RISK | SIMULTANEOUS_LOSS | 118.0 | 496.0 | -712.11 | -2610.35 | 0.32 |
| P1_CLUSTER_EQUAL_RISK | SIMULTANEOUS_LOSS | 118.0 | 496.0 | -780.4 | -2651.48 | 0.34 |
| P2_STATIC_DIVERSIFIED | SIMULTANEOUS_LOSS | 133.0 | 420.0 | -906.74 | -2655.11 | 0.41 |
| P3_REGIME_ADAPTIVE_25 | SIMULTANEOUS_LOSS | 133.0 | 420.0 | -908.14 | -2655.11 | 0.42 |
| P3_REGIME_ADAPTIVE_50 | SIMULTANEOUS_LOSS | 133.0 | 420.0 | -903.9 | -2655.11 | 0.42 |
