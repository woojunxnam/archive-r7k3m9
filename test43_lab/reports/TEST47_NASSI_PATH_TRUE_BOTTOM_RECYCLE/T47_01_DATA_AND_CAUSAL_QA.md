# T47_01 Data and causal QA

Research data <= 2026-05-27 only. $ are 1 MES / 1 MNQ contract, costs included (commission 0.62 + 1 tick per side).

|    | inst   |   sessions | first      | last       | last_le_cutoff   |   full_81bar_sessions |   u5_median_pts |   atrd_median_pts | canonical_sha256                                                 | volume_used_by_signals   |
|---:|:-------|-----------:|:-----------|:-----------|:-----------------|----------------------:|----------------:|------------------:|:-----------------------------------------------------------------|:-------------------------|
|  0 | ES     |       1780 | 2019-05-06 | 2026-05-27 | True             |                  1769 |           5.077 |            55.938 | 2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116 | NO                       |
|  1 | MNQ    |       1780 | 2019-05-06 | 2026-05-27 | True             |                  1770 |          23.396 |           252.473 | 66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2 | NO                       |

Causal perturbation test: every bar from bar b0 onward replaced by noise; events decided before b0 must be identical.

|    | inst   |   perturb_from_bar |   events_before | identical   |
|---:|:-------|-------------------:|----------------:|:------------|
|  0 | ES     |                 20 |             438 | True        |
|  1 | ES     |                 40 |             718 | True        |
|  2 | ES     |                 60 |             958 | True        |
|  3 | MNQ    |                 20 |             485 | True        |
|  4 | MNQ    |                 40 |             788 | True        |
|  5 | MNQ    |                 60 |            1000 | True        |

No TEST47 signal uses volume (the MNQ-for-NQ volume substitution never arises). 15m bars are completed 5m triplets; no developing value is used.

