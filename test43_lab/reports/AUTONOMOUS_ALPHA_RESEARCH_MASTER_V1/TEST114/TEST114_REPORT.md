# TEST114 academic intraday close momentum (GHLZ) — results (prereg ac38e48)

```json
{
 "TEST114_CLASSIFICATION": "REJECT (sign-reversed in 2019-2026 index futures; not a duplicate - worse than the TEST49-style control)",
 "G1_R1": "xN -0.0082 ATR [-0.0177,+0.0012]; negative in 4/4 instruments, 2/8 years positive",
 "G2_R1_R12": "xN -0.0033 (REJECT)",
 "G1_R1_X1615_TIMING_SENSITIVITY": "xN -0.0067 (REJECT)",
 "TB_OPEN_CONTROL": "~0 (REJECT)",
 "DUPLICATION_TEST": "within return-since-open > 0 sessions, r1 > 0 minus r1 <= 0 = -0.0181 ATR [-0.0334,-0.0025] -> r1 carries information but with the OPPOSITE sign (last-half-hour reversal after a positive first half hour); not RESEARCH_DUPLICATE",
 "LONG_ONLY_NOTE": "the reversal is a short-side signal; outside this long-only program (recorded, not pursued)",
 "DISTINCT_NEW_DEFINITIONS": 4,
 "LEDGER_ROWS": 4,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant         | horizon   |    n |    mean |   net_mean |   cost_atr |      xN |   ci_lo |   ci_hi |   years_pos |   inst_pos |   x2021 |   x2022 |    x_ES |    x_NQ |   x_RTY |    x_YM | class   |
|---:|:----------------|:----------|-----:|--------:|-----------:|-----------:|--------:|--------:|--------:|------------:|-----------:|--------:|--------:|--------:|--------:|--------:|--------:|:--------|
|  0 | G1_R1           | R16       | 3769 | -0.0142 |    -0.0251 |     0.0109 | -0.0082 | -0.0177 |  0.0012 |           2 |          0 | -0.0082 | -0.0172 | -0.0073 | -0.0083 | -0.0071 | -0.0102 | REJECT  |
|  1 | G2_R1_R12       | R16       | 2039 | -0.0098 |    -0.0206 |     0.0108 | -0.0033 | -0.0140 |  0.0071 |           2 |          1 | -0.0075 | -0.0035 |  0.0005 | -0.0056 | -0.0014 | -0.0067 | REJECT  |
|  2 | G1_R1_X1615     | R1615     | 3769 | -0.0074 |    -0.0183 |     0.0109 | -0.0067 | -0.0162 |  0.0035 |           2 |          0 | -0.0051 | -0.0197 | -0.0057 | -0.0091 | -0.0063 | -0.0055 | REJECT  |
|  3 | TB_OPEN_CONTROL | R16       | 3693 | -0.0064 |    -0.0172 |     0.0108 | -0.0008 | -0.0092 |  0.0081 |           3 |          1 | -0.0022 |  0.0164 | -0.0010 | -0.0013 | -0.0027 |  0.0015 | REJECT  |

## Duplication test

```json
{
 "within_TB_true_r1pos_minus_r1neg": -0.01812712679039181,
 "ci_lo": -0.03336610744946639,
 "ci_hi": -0.002512340427905056,
 "n_r1pos": 2284,
 "n_r1neg": 1409,
 "G1_xN": -0.008211120431222149,
 "TB_xN": -0.0008467603526018939,
 "RESEARCH_DUPLICATE": false
}
```

Per-instrument rows: out/index_alpha_master_v1/t114/.

Interpretation: the Gao-Han-Li-Zhou intraday momentum effect does not hold for ES/NQ/YM/RTY futures in 2019-07..2026-05; a positive first half-hour return (from the prior close) is followed by a weaker, not stronger, last half hour. Family closed.

