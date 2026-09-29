# TEST106 Fisher ACD opening auction — results (prereg 7363e7c)

```json
{
 "TEST106_CLASSIFICATION": "A2 = STRONG_CLUE at 60m (event level) BUT RESEARCH_DUPLICATE of plain ORB; no strategy phase",
 "A2_A_UP_IMMEDIATE": "STRONG_CLUE at 60m: xF +0.0137 ATR [+0.0010,+0.0266], 6/8 years, 4/4 instruments, gross 0.0139 > cost 0.0108, xC > 0, 2021+ > 0, adjacent A1 consistent; 120m / 16:15 WEAK",
 "A1_A_UP_HELD": "WEAK at 60m / 120m; time acceptance does NOT improve on the immediate trigger (A1 < A2 at every horizon)",
 "A3_FAILED_A_DOWN": "WEAK at 120m / 16:15 (xF +0.017 / +0.019, CIs include 0; 2022 negative)",
 "A4_C_UP": "REJECT / WEAK (n 538)",
 "ORB_COMPARATOR": "WEAK (60m xF +0.0080 [-0.0036,+0.0188]; 16:15 +0.0182 [-0.0061,+0.0432])",
 "ACD_VS_ORB": "A2 minus ORB excess (date-clustered CI): 60m +0.0058 [-0.0019,+0.0134], 120m +0.0081 [-0.0006,+0.0173], 16:15 -0.0066 [-0.0174,+0.0041] -> not distinguishable from plain ORB at any horizon -> RESEARCH_DUPLICATE (ORB retention family closed in TEST49)",
 "SAME_SESSION_RAW_COMPARISON": "reported but INVALID for inference (conditioning on a later A-up / A-down trigger selects ORB outcomes)",
 "ECONOMIC_FEASIBILITY_NOTE": "even if opened: net 60m edge ~0.003 ATR_d per event (~$1-2/trade at 1 micro), ~130 events / instrument / year -> order of $1/day, far below the +$3 DIVERSIFIER / +$10 STANDARD gates",
 "STRATEGY_PHASE_OPENED": "NO (RESEARCH_DUPLICATE)",
 "MULTIPLE_TESTING": "15 primary tests, ~0.4 chance passes expected; 1 observed (A2 60m)",
 "DISTINCT_NEW_DEFINITIONS": 5,
 "LEDGER_ROWS": 100,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant           | horizon   |    n |    mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:------------------|:----------|-----:|--------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | A1_A_UP_HELD      | h12       | 2136 |  0.0099 |     0.0107 |  0.0089 | -0.0038 |  0.0214 |           6 |          3 |    0.0112 | -0.0062 |  0.0079 |  0.0045 | True          | 0.84/0.16/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  1 | A1_A_UP_HELD      | h24       | 2064 |  0.0141 |     0.0107 |  0.0065 | -0.0099 |  0.0248 |           5 |          3 |    0.0087 |  0.0158 |  0.0092 |  0.0055 | True          | 0.83/0.16/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  2 | A1_A_UP_HELD      | h1615     | 2136 |  0.0117 |     0.0107 | -0.0035 | -0.0336 |  0.0252 |           2 |          2 |   -0.0004 | -0.0038 | -0.0025 |  0.0011 | False         | 0.84/0.15/0.00 | REJECT                  |
|  3 | A2_A_UP_IMMEDIATE | h12       | 3551 |  0.0139 |     0.0108 |  0.0137 |  0.0010 |  0.0266 |           6 |          4 |    0.0198 |  0.0279 |  0.0124 |  0.0071 | True          | 0.85/0.15/0.00 | STRONG_CLUE             |
|  4 | A2_A_UP_IMMEDIATE | h24       | 3456 |  0.0181 |     0.0108 |  0.0098 | -0.0078 |  0.0268 |           6 |          3 |    0.0178 |  0.0329 |  0.0129 |  0.0064 | True          | 0.84/0.16/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  5 | A2_A_UP_IMMEDIATE | h1615     | 3551 |  0.0220 |     0.0108 |  0.0115 | -0.0145 |  0.0375 |           7 |          3 |    0.0214 |  0.0272 |  0.0101 |  0.0094 | False         | 0.85/0.15/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  6 | A3_FAILED_A_DOWN  | h12       | 1059 | -0.0038 |     0.0109 |  0.0006 | -0.0222 |  0.0208 |           5 |          1 |    0.0005 | -0.0274 | -0.0018 | -0.0098 | True          | 1.00/0.00/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  7 | A3_FAILED_A_DOWN  | h24       | 1033 |  0.0121 |     0.0109 |  0.0171 | -0.0096 |  0.0436 |           6 |          3 |    0.0111 | -0.0292 |  0.0140 |  0.0020 | False         | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  8 | A3_FAILED_A_DOWN  | h1615     | 1059 |  0.0184 |     0.0109 |  0.0187 | -0.0256 |  0.0621 |           5 |          4 |    0.0161 | -0.0410 |  0.0237 |  0.0074 | False         | 1.00/0.00/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  9 | A4_C_UP           | h12       |  505 |  0.0123 |     0.0104 |  0.0091 | -0.0198 |  0.0372 |           4 |          3 |    0.0191 |  0.0288 |  0.0110 |  0.0078 | False         | 0.98/0.02/0.00 | REJECT                  |
| 10 | A4_C_UP           | h24       |  444 |  0.0103 |     0.0104 |  0.0032 | -0.0474 |  0.0491 |           6 |          2 |    0.0234 |  0.0172 |  0.0101 |  0.0045 | True          | 0.92/0.08/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 11 | A4_C_UP           | h1615     |  505 |  0.0085 |     0.0104 |  0.0025 | -0.0595 |  0.0601 |           4 |          3 |    0.0209 | -0.0265 |  0.0041 |  0.0035 | True          | 0.98/0.02/0.00 | REJECT                  |
| 12 | ORB_COMPARATOR    | h12       | 4500 |  0.0101 |     0.0107 |  0.0080 | -0.0036 |  0.0188 |           7 |          4 |    0.0089 |  0.0097 |  0.0082 |  0.0004 | False         | 0.88/0.12/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 13 | ORB_COMPARATOR    | h24       | 4426 |  0.0143 |     0.0107 |  0.0017 | -0.0135 |  0.0158 |           4 |          3 |    0.0025 |  0.0277 |  0.0092 | -0.0016 | False         | 0.87/0.13/0.00 | REJECT                  |
| 14 | ORB_COMPARATOR    | h1615     | 4500 |  0.0215 |     0.0107 |  0.0182 | -0.0061 |  0.0432 |           6 |          4 |    0.0253 |  0.0343 |  0.0090 |  0.0032 | False         | 0.88/0.12/0.00 | WEAK_RESEARCH_CLUE_ONLY |

## A2 minus ORB F106 excess (date-clustered 95% CI, 2,000 reps)

|    | horizon   |   A2_xF |   ORB_xF |    diff |   ci_lo |   ci_hi |
|---:|:----------|--------:|---------:|--------:|--------:|--------:|
|  0 | h6        |  0.0083 |   0.0072 |  0.0011 | -0.0053 |  0.0075 |
|  1 | h12       |  0.0137 |   0.0080 |  0.0058 | -0.0019 |  0.0134 |
|  2 | h24       |  0.0098 |   0.0017 |  0.0081 | -0.0006 |  0.0173 |
|  3 | h1615     |  0.0115 |   0.0182 | -0.0066 | -0.0174 |  0.0041 |

## Same-session raw comparison (INVALID for inference; selection on a later trigger)

|    | acd               | horizon   |   n_sessions |   acd_mean |   orb_mean |   acd_minus_orb |
|---:|:------------------|:----------|-------------:|-----------:|-----------:|----------------:|
|  0 | A1_A_UP_HELD      | h6        |         2233 |     0.0063 |     0.0879 |         -0.0816 |
|  1 | A1_A_UP_HELD      | h12       |         2233 |     0.0099 |     0.1110 |         -0.1011 |
|  2 | A1_A_UP_HELD      | h24       |         2233 |     0.0136 |     0.1342 |         -0.1206 |
|  3 | A1_A_UP_HELD      | h1615     |         2233 |     0.0117 |     0.1472 |         -0.1354 |
|  4 | A2_A_UP_IMMEDIATE | h6        |         3722 |     0.0104 |     0.0453 |         -0.0349 |
|  5 | A2_A_UP_IMMEDIATE | h12       |         3722 |     0.0139 |     0.0619 |         -0.0480 |
|  6 | A2_A_UP_IMMEDIATE | h24       |         3722 |     0.0176 |     0.0790 |         -0.0614 |
|  7 | A2_A_UP_IMMEDIATE | h1615     |         3722 |     0.0220 |     0.0985 |         -0.0765 |
|  8 | A3_FAILED_A_DOWN  | h6        |          680 |     0.0416 |    -0.0471 |          0.0887 |
|  9 | A3_FAILED_A_DOWN  | h12       |          680 |     0.0773 |    -0.0668 |          0.1440 |
| 10 | A3_FAILED_A_DOWN  | h24       |          680 |     0.1280 |    -0.1006 |          0.2286 |
| 11 | A3_FAILED_A_DOWN  | h1615     |          680 |     0.1747 |    -0.1134 |          0.2881 |
| 12 | A4_C_UP           | h6        |          538 |     0.0049 |    -0.0006 |          0.0055 |
| 13 | A4_C_UP           | h12       |          538 |     0.0123 |     0.0185 |         -0.0063 |
| 14 | A4_C_UP           | h24       |          538 |     0.0091 |     0.0291 |         -0.0200 |
| 15 | A4_C_UP           | h1615     |          538 |     0.0085 |     0.0887 |         -0.0802 |

Per-instrument rows: out/index_alpha_master_v1/t106/.

Interpretation: the ACD A-up trigger is the only ESP-1 STRONG_CLUE of the program so far (60-minute horizon), but its excess over a plain close-confirmed ORB is not resolved at any horizon, the ORB family is closed, and the per-event net edge is ~0.3% of a daily ATR - an order of magnitude too small for any gate. Classified RESEARCH_DUPLICATE; no strategy phase. The failed-A-down (A3) direction agrees with the TEST104 L2 failed-breakdown clue.

