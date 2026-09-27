# T45_12 Genetic algorithm specification

Island-model NSGA-II (own implementation: constrained non-dominated sort + crowding): 2 seeds x 3 islands x pop 120 x 50 generations. Ring migration of 4 after generation 25.

Unique genomes evaluated: **174,140** (per fold: {'FINAL_ALL_TO_2026-05-27': 31244, 'O1_2021': 29947, 'O2_2022': 30024, 'O3_2023': 30752, 'O4_2024': 30307, 'O5_2025_26': 31405}), within the 250k limit.

Nested chronological validation: for outer blocks 2021, 2022, 2023, 2024 and 2025-01..2026-05-27, evolution sees ONLY sessions before the block. A final run on all data uses the identical procedure.

Objectives (minimised): -median inner-fold $/day, -worst inner-fold $/day, training MaxDD, -session-matched-beta excess, complexity. Constraints: >=30 active sessions, sides/day <= 4, |corr Champion| <= 0.6. Whole-history P&L is NOT an objective.

Predeclared selection per outer fold: feasible rank-0 members with worst inner fold > 0; maximise median_inner / max(MaxDD, 1000); tie-break lower complexity.

Genome space (overlay only, V6 never evolved):

|    | gene       | type   | domain                                                                                           |
|---:|:-----------|:-------|:-------------------------------------------------------------------------------------------------|
|  0 | inst       | cat    | ['ES', 'MNQ', 'BOTH']                                                                            |
|  1 | m_on       | cat    | [0, 1]                                                                                           |
|  2 | m_gap_kind | cat    | ['lock', 'cash']                                                                                 |
|  3 | m_gap_norm | cat    | ['atr', 'range', 'sigma', 'pct']                                                                 |
|  4 | m_gap_hi   | opt    | (-2.5, 0.25)                                                                                     |
|  5 | m_gap_lo   | opt    | (-5.0, -0.75)                                                                                    |
|  6 | m_w        | cat    | [0, 5, 15, 30, 60, 90]                                                                           |
|  7 | m_flush_hi | opt    | (-1.2, 0.0)                                                                                      |
|  8 | m_flush_lo | opt    | (-3.0, -0.4)                                                                                     |
|  9 | m_reclaim  | opt    | (0.05, 1.0)                                                                                      |
| 10 | m_exit     | cat    | ['10:30', '11:00', '12:00', '13:00', '14:00', '15:00', '15:45', '16:00', 'CARRY']                |
| 11 | m_q        | cat    | [1, 2]                                                                                           |
| 12 | m_vol_max  | opt    | (0.3, 0.99)                                                                                      |
| 13 | m_trend    | cat    | [-1, 0, 1]                                                                                       |
| 14 | m_rel      | cat    | [-1, 0, 1]                                                                                       |
| 15 | m_v6       | cat    | [-1, 0, 1]                                                                                       |
| 16 | m_dd_max   | opt    | (500.0, 5000.0)                                                                                  |
| 17 | c_on       | cat    | [0, 1]                                                                                           |
| 18 | c_time     | cat    | ['14:30', '15:00', '15:15', '15:30', '15:45', '16:00', '16:14']                                  |
| 19 | c_base     | cat    | [0, 1]                                                                                           |
| 20 | c_feat     | cat    | ['none', 'rth_ret', 'day_ret', 'dist_vwap', 'range_pos', 'mom15', 'mom60', 'accel', 'champ_pos'] |
| 21 | c_dir      | cat    | [-1, 1]                                                                                          |
| 22 | c_thr      | num    | (-1.5, 1.5)                                                                                      |
| 23 | c_boost    | cat    | [1, 2]                                                                                           |
| 24 | c_vol_max  | opt    | (0.3, 0.99)                                                                                      |
| 25 | o_rule     | cat    | ['EXIT_OPEN', 'KEEP_ADVERSE', 'EXIT_AFTER', 'KEEP_UNTIL']                                        |
| 26 | o_thr      | num    | (-2.0, 0.0)                                                                                      |
| 27 | o_until    | cat    | ['10:30', '11:00', '12:00', '15:00', '16:00']                                                    |
| 28 | o_w        | cat    | [1, 5, 15, 30, 60]                                                                               |

Frozen lock governor: {'LOCK_K': 2.5, 'LOCK_BUDGET': 4000.0}. QMAX 2 per symbol.

