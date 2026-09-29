# TEST100 VWAP trend-side state — results (prereg b69e62e)

```json
{
 "TEST100_CLASSIFICATION": "REJECT (0/18 EVENT_CLUE; V1_K3 / V2_K6 60m WEAK_RESEARCH_CLUE_ONLY)",
 "V1_ACCEPTANCE": "WEAK_RESEARCH_CLUE_ONLY at 60m (K3 xF +0.0049 [-0.005,+0.015]); 16:15 <= 0 (K3)",
 "V2_WALK": "K6 weak (all CIs include 0); K12 REJECT (negative) - not coherent across K",
 "V3_FIRST_HOLD": "REJECT (negative excess at every primary horizon, both K)",
 "VWAP_TREND_SIDE_ADDS_ALPHA": "NO",
 "DISTINCT_NEW_DEFINITIONS": 6,
 "LEDGER_ROWS": 120,
 "ML_CONFIGS": 0,
 "GA_GENOMES": 0,
 "STRATEGY_PHASE_OPENED": "NO",
 "NEW_OOS_OPENED": "NO",
 "LIVE_AUTHORIZATION": "NO",
 "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"
}
```

## Classification (pooled, family null; excess in ATR_d units)

|    | variant   | horizon   |    n |   mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:----------|:----------|-----:|-------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | V1_K3     | h12       | 6118 | 0.0072 |     0.0109 |  0.0049 | -0.0052 |  0.0146 |           5 |          4 |    0.0023 | -0.0040 |  0.0070 | -0.0013 | False         | 0.95/0.05/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  1 | V1_K3     | h24       | 6011 | 0.0088 |     0.0109 |  0.0026 | -0.0117 |  0.0164 |           6 |          2 |    0.0004 |  0.0073 |  0.0045 | -0.0058 | False         | 0.95/0.05/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  2 | V1_K3     | h1615     | 6118 | 0.0134 |     0.0109 | -0.0013 | -0.0244 |  0.0221 |           5 |          2 |   -0.0047 | -0.0088 |  0.0031 | -0.0024 | False         | 0.95/0.05/0.00 | REJECT                  |
|  3 | V1_K6     | h12       | 5524 | 0.0028 |     0.0109 |  0.0006 | -0.0082 |  0.0099 |           5 |          2 |    0.0008 |  0.0038 |  0.0035 | -0.0042 | True          | 0.95/0.04/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  4 | V1_K6     | h24       | 5337 | 0.0067 |     0.0109 |  0.0010 | -0.0128 |  0.0145 |           4 |          2 |    0.0010 |  0.0040 |  0.0044 | -0.0050 | True          | 0.95/0.05/0.00 | REJECT                  |
|  5 | V1_K6     | h1615     | 5524 | 0.0164 |     0.0109 |  0.0033 | -0.0180 |  0.0250 |           5 |          3 |    0.0021 |  0.0101 |  0.0080 |  0.0051 | False         | 0.96/0.04/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  6 | V2_K6     | h12       | 5078 | 0.0051 |     0.0109 |  0.0027 | -0.0058 |  0.0110 |           6 |          3 |    0.0050 | -0.0068 |  0.0038 |  0.0006 | False         | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  7 | V2_K6     | h24       | 4847 | 0.0074 |     0.0109 |  0.0022 | -0.0107 |  0.0149 |           5 |          3 |    0.0038 | -0.0129 |  0.0044 | -0.0008 | False         | 0.96/0.04/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  8 | V2_K6     | h1615     | 5078 | 0.0155 |     0.0109 |  0.0036 | -0.0185 |  0.0234 |           4 |          3 |    0.0051 | -0.0059 |  0.0060 |  0.0072 | False         | 0.97/0.03/0.00 | REJECT                  |
|  9 | V2_K12    | h12       | 4284 | 0.0052 |     0.0109 | -0.0006 | -0.0096 |  0.0080 |           3 |          2 |    0.0001 | -0.0111 |  0.0033 |  0.0013 | False         | 0.99/0.01/0.00 | REJECT                  |
| 10 | V2_K12    | h24       | 3949 | 0.0076 |     0.0109 | -0.0011 | -0.0144 |  0.0111 |           3 |          2 |    0.0021 | -0.0193 |  0.0063 |  0.0014 | False         | 0.99/0.01/0.00 | REJECT                  |
| 11 | V2_K12    | h1615     | 4284 | 0.0117 |     0.0109 | -0.0021 | -0.0228 |  0.0167 |           3 |          1 |   -0.0004 | -0.0131 |  0.0043 |  0.0049 | False         | 1.00/0.00/0.00 | REJECT                  |
| 12 | V3_K3     | h12       | 5536 | 0.0017 |     0.0109 | -0.0018 | -0.0109 |  0.0075 |           3 |          1 |   -0.0028 |  0.0072 |  0.0015 | -0.0048 | True          | 0.97/0.03/0.00 | REJECT                  |
| 13 | V3_K3     | h24       | 5359 | 0.0049 |     0.0109 | -0.0021 | -0.0154 |  0.0118 |           3 |          0 |   -0.0021 |  0.0120 |  0.0013 | -0.0072 | False         | 0.96/0.03/0.00 | REJECT                  |
| 14 | V3_K3     | h1615     | 5536 | 0.0118 |     0.0109 | -0.0032 | -0.0263 |  0.0190 |           4 |          2 |   -0.0062 |  0.0064 |  0.0032 | -0.0008 | True          | 0.97/0.03/0.00 | REJECT                  |
| 15 | V3_K6     | h12       | 4494 | 0.0007 |     0.0109 | -0.0037 | -0.0124 |  0.0050 |           3 |          1 |   -0.0044 |  0.0160 | -0.0011 | -0.0036 | False         | 0.96/0.03/0.00 | REJECT                  |
| 16 | V3_K6     | h24       | 4200 | 0.0053 |     0.0109 | -0.0007 | -0.0140 |  0.0125 |           3 |          3 |   -0.0015 |  0.0180 |  0.0028 | -0.0023 | True          | 0.96/0.03/0.01 | REJECT                  |
| 17 | V3_K6     | h1615     | 4494 | 0.0119 |     0.0109 | -0.0019 | -0.0247 |  0.0195 |           4 |          1 |   -0.0031 |  0.0194 |  0.0030 |  0.0040 | True          | 0.97/0.03/0.00 | REJECT                  |

Per-instrument rows: out/index_alpha_master_v1/t100/.

Interpretation: once price is held on the trend side of VWAP at the same distance and session move, the onset of acceptance / walk adds nothing measurable, and the first VWAP hold from above is slightly worse than simply being above VWAP. VWAP trend-side state family SATURATED.

