# RESERVE_R1 trapped-seller failure union (reserve) — results (prereg 1ce475c)

```json
{
 "RESERVE_R1_CLASSIFICATION": "REJECT by ESP-1 (WEAK_RESEARCH_CLUE_ONLY at all 3 primary horizons; SELECTION_EXPOSED)",
 "R1_UNION": "n 4,552 events; xF 60m +0.0070 [-0.0023,+0.0165], 120m +0.0119 [-0.0006,+0.0247] (gross 0.0107 < cost 0.0109), 16:15 +0.0138 [-0.0092,+0.0366]; 6-7/8 years; 3-4/4 instruments",
 "CONSTITUENTS_ON_UNION_EVENTS": "P2 strongest (16:15 +0.050, n 459), L2 steady (+0.009..+0.012, n 3,376), A3 ~0 / negative (n 717)",
 "POOLING_RESOLVES_CLUE": "NO",
 "SELECTION_EXPOSED": "YES",
 "STRATEGY_PHASE_OPENED": "NO",
 "DISTINCT_NEW_DEFINITIONS": 1,
 "LEDGER_ROWS": 20,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant          | horizon   |    n |   mean |   cost_atr |     xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |     xA |      xC | adjacent_ok   | class                   |
|---:|:-----------------|:----------|-----:|-------:|-----------:|-------:|--------:|--------:|------------:|-----------:|----------:|--------:|-------:|--------:|:--------------|:------------------------|
|  0 | R1_TRAPPED_UNION | h12       | 4316 | 0.0038 |     0.0109 | 0.0070 | -0.0023 |  0.0165 |           6 |          3 |    0.0057 | -0.0081 | 0.0032 | -0.0013 | True          | WEAK_RESEARCH_CLUE_ONLY |
|  1 | R1_TRAPPED_UNION | h24       | 4047 | 0.0107 |     0.0109 | 0.0119 | -0.0006 |  0.0247 |           6 |          4 |    0.0097 | -0.0050 | 0.0089 |  0.0017 | True          | WEAK_RESEARCH_CLUE_ONLY |
|  2 | R1_TRAPPED_UNION | h1615     | 4316 | 0.0172 |     0.0109 | 0.0138 | -0.0092 |  0.0366 |           7 |          4 |    0.0136 |  0.0109 | 0.0131 |  0.0079 | True          | WEAK_RESEARCH_CLUE_ONLY |

## Constituent excess on the union events

|    | horizon   |   P2_n |   L2_n |   A3_n |   P2_xF |   L2_xF |   A3_xF |
|---:|:----------|-------:|-------:|-------:|--------:|--------:|--------:|
|  0 | h6        |    459 |   3376 |    717 |  0.0097 |  0.0059 | -0.0100 |
|  1 | h12       |    459 |   3376 |    717 |  0.0152 |  0.0085 | -0.0054 |
|  2 | h24       |    459 |   3376 |    717 |  0.0249 |  0.0113 |  0.0066 |
|  3 | h1615     |    459 |   3376 |    717 |  0.0503 |  0.0121 | -0.0015 |

Per-instrument rows: out/index_alpha_master_v1/r1/.

Interpretation: pooling the trapped-seller failure structures (4.5k events) keeps the positive sign at every horizon but does not clear the date-clustered CI, and the 120-minute gross edge is below the micro round-trip cost. The mechanism is a persistent weak clue, not an exploitable edge at this sample size. Reserve families R2/R3 are not opened: no remaining mechanism has preregistered evidence, and the best point estimates in the program (~0.01-0.03 ATR_d gross) are at or below micro costs.

