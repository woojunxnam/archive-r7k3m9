# T46_25 GA-A specification

{
 "unique_genomes_total": 206678,
 "per_fold": {
  "FINAL_ALL_TO_2026-05-27": 35442,
  "O1_2021": 35515,
  "O2_2022": 35552,
  "O3_2023": 35482,
  "O4_2024": 35509,
  "O5_2025_26": 35561
 },
 "POP": 120,
 "GENS": 50,
 "SEEDS": [
  11,
  22
 ],
 "ISLANDS": 3
}

|    | gene      | type   | domain                 |
|---:|:----------|:-------|:-----------------------|
|  0 | fam       | cat    | [1, 2, 3, 4, 5, 6, 7]  |
|  1 | inst      | cat    | ['ES', 'MNQ']          |
|  2 | D         | num    | (0.0, 2.0)             |
|  3 | delta     | num    | (0.0, 0.5)             |
|  4 | k         | int    | (0, 6)                 |
|  5 | N         | int    | (3, 24)                |
|  6 | rho       | num    | (-0.2, 0.5)            |
|  7 | e0        | int    | (1, 24)                |
|  8 | span      | int    | (6, 70)                |
|  9 | veto5     | opt    | (1.0, 6.0)             |
| 10 | vetogap   | opt    | (0.5, 3.0)             |
| 11 | need_bull | cat    | [0, 1]                 |
| 12 | band      | num    | (1.0, 3.0)             |
| 13 | relx      | num    | (0.2, 1.5)             |
| 14 | exit_mode | cat    | [0, 1, 2]              |
| 15 | hold      | cat    | [30, 60, 120, 180]     |
| 16 | stop      | cat    | [-1.0, 0.0, 0.25, 0.5] |

GA-B/C/D (INDEX6 exit, pyramid, overnight evolution) were NOT run: seed parity failed and the TEST46 rule forbids evolving unverified seeds.

