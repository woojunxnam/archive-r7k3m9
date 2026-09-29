# TEST103 complex pullback / second entry — results (prereg b9d9db6)

```json
{
 "TEST103_CLASSIFICATION": "REJECT by ESP-1 (0/12 EVENT_CLUE); second-entry forms = WEAK_RESEARCH_CLUE_ONLY (best of program so far)",
 "P1_H2_TWO_LEG": "WEAK_RESEARCH_CLUE_ONLY at 60m / 120m / 16:15 (xF +0.0075 / +0.0100 / +0.0127; all CIs include 0; 5-6/8 years; 3/4 instruments)",
 "P2_FAILED_FIRST_SECOND_RESUMPTION": "WEAK_RESEARCH_CLUE_ONLY at 60m / 120m (xF +0.0141 [-0.0019,+0.0300], +0.0226 [-0.0009,+0.0462]); 16:15 xF +0.0334 [-0.0001,+0.0650] but only 4/8 positive years -> REJECT at 16:15; n = 713 (small)",
 "P3_EMA21_SECOND_TOUCH": "REJECT",
 "P1_H1_FIRST_ENTRY_COMPARATOR": "~0 at every horizon",
 "SECOND_MINUS_FIRST_RAW": "P1_H2 +0.004..+0.016, P2 +0.011..+0.037 ATR over the first entry (60m..16:15)",
 "P4": "NOT_RUN_BY_RULE (no TEST99 EVENT_CLUE)",
 "P5": "NOT_RUN_BY_RULE (no EVENT_CLUE in P1-P3)",
 "STRATEGY_PHASE_OPENED": "NO (requires STRONG_CLUE)",
 "MULTIPLE_TESTING": "12 primary tests, ~0.3 chance CI passes expected; none passed",
 "DISTINCT_NEW_DEFINITIONS": 4,
 "LEDGER_ROWS": 80,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant          | horizon   |    n |    mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:-----------------|:----------|-----:|--------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | P1_H2            | h12       | 1920 |  0.0036 |     0.0109 |  0.0075 | -0.0042 |  0.0186 |           5 |          3 |    0.0045 |  0.0140 |  0.0010 |  0.0005 | True          | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  1 | P1_H2            | h24       | 1777 |  0.0048 |     0.0109 |  0.0100 | -0.0048 |  0.0264 |           6 |          3 |    0.0055 |  0.0158 |  0.0008 | -0.0008 | True          | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  2 | P1_H2            | h1615     | 1920 |  0.0160 |     0.0109 |  0.0127 | -0.0106 |  0.0371 |           6 |          3 |    0.0082 |  0.0338 |  0.0091 |  0.0104 | True          | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  3 | P2_FAILED_FIRST  | h12       |  713 |  0.0108 |     0.0109 |  0.0141 | -0.0019 |  0.0300 |           6 |          3 |    0.0061 |  0.0264 |  0.0093 |  0.0075 | True          | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  4 | P2_FAILED_FIRST  | h24       |  660 |  0.0182 |     0.0109 |  0.0226 | -0.0009 |  0.0462 |           6 |          3 |    0.0113 |  0.0111 |  0.0139 |  0.0117 | False         | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  5 | P2_FAILED_FIRST  | h1615     |  713 |  0.0373 |     0.0109 |  0.0334 | -0.0001 |  0.0650 |           4 |          3 |    0.0295 |  0.0939 |  0.0308 |  0.0314 | False         | 0.98/0.02/0.00 | REJECT                  |
|  6 | P3_EMA21_SECOND  | h12       | 3843 | -0.0004 |     0.0109 |  0.0000 | -0.0083 |  0.0083 |           6 |          3 |   -0.0004 |  0.0013 | -0.0022 | -0.0036 | False         | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  7 | P3_EMA21_SECOND  | h24       | 3544 | -0.0027 |     0.0109 | -0.0024 | -0.0162 |  0.0107 |           4 |          1 |   -0.0017 |  0.0006 | -0.0056 | -0.0082 | False         | 0.97/0.03/0.00 | REJECT                  |
|  8 | P3_EMA21_SECOND  | h1615     | 3843 |  0.0012 |     0.0109 | -0.0047 | -0.0260 |  0.0171 |           3 |          1 |   -0.0050 | -0.0065 | -0.0040 | -0.0047 | False         | 0.98/0.02/0.00 | REJECT                  |
|  9 | P1_H1_COMPARATOR | h12       | 3462 | -0.0000 |     0.0109 |  0.0013 | -0.0075 |  0.0102 |           5 |          4 |    0.0018 |  0.0138 | -0.0032 | -0.0044 | False         | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 10 | P1_H1_COMPARATOR | h24       | 3303 | -0.0022 |     0.0109 |  0.0001 | -0.0128 |  0.0131 |           5 |          2 |    0.0018 |  0.0179 | -0.0058 | -0.0094 | False         | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 11 | P1_H1_COMPARATOR | h1615     | 3462 |  0.0001 |     0.0109 | -0.0043 | -0.0275 |  0.0172 |           4 |          0 |   -0.0034 |  0.0173 | -0.0073 | -0.0069 | False         | 0.97/0.03/0.00 | REJECT                  |

## Second entry vs first entry (raw pooled means, same contexts)

|    | second          | horizon   |   second_mean |   first_mean |   second_minus_first |
|---:|:----------------|:----------|--------------:|-------------:|---------------------:|
|  0 | P1_H2           | h6        |       -0.0023 |      -0.0003 |              -0.0020 |
|  1 | P1_H2           | h12       |        0.0036 |      -0.0000 |               0.0036 |
|  2 | P1_H2           | h24       |        0.0048 |      -0.0022 |               0.0070 |
|  3 | P1_H2           | h1615     |        0.0160 |       0.0001 |               0.0159 |
|  4 | P2_FAILED_FIRST | h6        |        0.0029 |      -0.0003 |               0.0032 |
|  5 | P2_FAILED_FIRST | h12       |        0.0108 |      -0.0000 |               0.0109 |
|  6 | P2_FAILED_FIRST | h24       |        0.0182 |      -0.0022 |               0.0204 |
|  7 | P2_FAILED_FIRST | h1615     |        0.0373 |       0.0001 |               0.0373 |

Per-instrument rows: out/index_alpha_master_v1/t103/.

Interpretation: inside a fresh-breakout context, entries that come after a trapped first attempt (failed first resumption, or a two-leg high-2) beat the first entry and the context null at every horizon, whereas the first entry itself carries nothing; but the effect does not clear the date-clustered CI (n small) and so remains a WEAK_RESEARCH_CLUE_ONLY under the preregistered ESP-1 rule. No strategy phase is opened; recorded for TEST104/105 (failure-state) and for the final synthesis as a forward clue only.

