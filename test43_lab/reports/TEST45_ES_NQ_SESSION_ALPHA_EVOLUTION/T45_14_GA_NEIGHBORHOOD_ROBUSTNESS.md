# T45_14 GA neighbourhood robustness

Perturbations: each active continuous gene at -20/-10/+10/+20% (+/-0.05 near 0), plus adjacent discrete times. PASS requires every perturbation to keep avg > 0 and >= 50% of base, and MaxDD <= 1.5 x base.

Outer-fold selections (on their own training window):

|    | fold       | plateau_pass   |   share_ok |
|---:|:-----------|:---------------|-----------:|
|  0 | O1_2021    | False          |      0.800 |
|  1 | O2_2022    | True           |      1.000 |
|  2 | O3_2023    | False          |      0.714 |
|  3 | O4_2024    | False          |      0.880 |
|  4 | O5_2025_26 | False          |      0.885 |

Final GA genome plateau pass: False

|    | perturbation    |    avg |   max_dd |
|---:|:----------------|-------:|---------:|
|  0 | BASE            | 46.553 | 3720.700 |
|  1 | m_gap_lo -20%   | 46.553 | 3720.700 |
|  2 | m_gap_lo -10%   | 46.553 | 3720.700 |
|  3 | m_gap_lo +10%   | 46.553 | 3720.700 |
|  4 | m_gap_lo +20%   | 46.553 | 3720.700 |
|  5 | m_flush_lo -20% | 46.553 | 3720.700 |
|  6 | m_flush_lo -10% | 46.553 | 3720.700 |
|  7 | m_flush_lo +10% | 46.553 | 3720.700 |
|  8 | m_flush_lo +20% | 46.553 | 3720.700 |
|  9 | m_reclaim -20%  | 46.553 | 3720.700 |
| 10 | m_reclaim -10%  | 46.553 | 3720.700 |
| 11 | m_reclaim +10%  | 46.304 | 3720.700 |
| 12 | m_reclaim +20%  | 46.329 | 3720.700 |
| 13 | m_vol_max -20%  | 45.819 | 3839.800 |
| 14 | m_vol_max -10%  | 45.961 | 3720.700 |
| 15 | m_vol_max +10%  | 46.980 | 3720.700 |
| 16 | m_vol_max +20%  | 47.470 | 3720.700 |
| 17 | m_dd_max -20%   | 45.611 | 3930.940 |
| 18 | m_dd_max -10%   | 45.980 | 3930.940 |
| 19 | m_dd_max +10%   | 46.553 | 3720.700 |
| 20 | m_dd_max +20%   | 46.553 | 3720.700 |
| 21 | c_thr -20%      | 46.553 | 3720.700 |
| 22 | c_thr -10%      | 46.553 | 3720.700 |
| 23 | c_thr +10%      | 46.553 | 3720.700 |
| 24 | c_thr +20%      | 46.553 | 3720.700 |
| 25 | m_w 30          | 47.175 | 3720.700 |
| 26 | m_w 90          | 44.561 | 3959.120 |
| 27 | m_exit 14:00    | 44.681 | 4333.420 |
| 28 | m_exit 15:45    | 45.683 | 4214.560 |
| 29 | c_time 15:30    | 44.687 | 4788.180 |
| 30 | c_time 16:00    | 39.200 | 4133.020 |
| 31 | o_w 15          | 45.191 | 3664.200 |
| 32 | o_w 60          | 43.491 | 6201.660 |

Answer: GENETIC_PARAMETER_PLATEAU_PASS = NO. Only 1 of 5 fold selections is a plateau; the final genome has cliff-like genes.

