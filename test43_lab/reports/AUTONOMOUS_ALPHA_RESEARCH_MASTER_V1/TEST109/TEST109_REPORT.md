# TEST109 ICT falsification mini-lane — results (prereg a05fae4)

```json
{
 "TEST109_CLASSIFICATION": "REJECT (0/18 EVENT_CLUE): FVG adds nothing beyond matched displacement",
 "FVG_VS_MATCHED_NO_FVG": "FVG_DISP 5m xF +0.0036 (60m, CI [-0.0014,+0.0086]); 15m ~0 -> a gap adds no information beyond the same 3-bar displacement",
 "FVG_RETRACE": "5m WEAK (+0.003..+0.004), 15m REJECT",
 "CHOCH": "15m WEAK at all 3 horizons (+0.007..+0.013, CIs include 0), 5m WEAK at 60m only; adjacency fails",
 "FVG_AFTER_LEVEL_FAILURE": "NOT_RUN_BY_RULE",
 "ICT_ADDS_ALPHA": "NO",
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

|    | variant         | horizon   |     n |   mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:----------------|:----------|------:|-------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | FVG_DISP_5m     | h12       | 46642 | 0.0056 |     0.0108 |  0.0036 | -0.0014 |  0.0086 |           5 |          4 |    0.0041 | -0.0065 |  0.0044 |  0.0030 | False         | 0.95/0.05/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  1 | FVG_DISP_5m     | h24       | 38469 | 0.0074 |     0.0108 |  0.0010 | -0.0082 |  0.0102 |           4 |          2 |    0.0008 | -0.0108 |  0.0039 |  0.0013 | True          | 0.95/0.04/0.01 | REJECT                  |
|  2 | FVG_DISP_5m     | h1615     | 46642 | 0.0121 |     0.0108 |  0.0051 | -0.0117 |  0.0210 |           4 |          4 |    0.0036 | -0.0024 |  0.0055 |  0.0069 | False         | 0.98/0.02/0.00 | REJECT                  |
|  3 | FVG_DISP_15m    | h12       | 15001 | 0.0046 |     0.0109 |  0.0002 | -0.0062 |  0.0068 |           5 |          2 |    0.0005 | -0.0043 |  0.0029 | -0.0000 | True          | 0.75/0.25/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  4 | FVG_DISP_15m    | h24       | 12005 | 0.0070 |     0.0109 |  0.0016 | -0.0099 |  0.0131 |           4 |          3 |    0.0016 | -0.0136 |  0.0024 | -0.0001 | True          | 0.85/0.15/0.00 | REJECT                  |
|  5 | FVG_DISP_15m    | h1615     | 15001 | 0.0058 |     0.0109 |  0.0015 | -0.0167 |  0.0190 |           4 |          3 |    0.0040 |  0.0030 | -0.0008 | -0.0010 | True          | 0.84/0.16/0.00 | REJECT                  |
|  6 | FVG_RETRACE_5m  | h12       | 24690 | 0.0053 |     0.0108 |  0.0032 | -0.0015 |  0.0082 |           5 |          4 |    0.0045 |  0.0065 |  0.0038 |  0.0020 | True          | 0.99/0.01/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  7 | FVG_RETRACE_5m  | h24       | 20163 | 0.0056 |     0.0108 |  0.0009 | -0.0080 |  0.0101 |           5 |          2 |    0.0038 |  0.0062 |  0.0019 | -0.0007 | False         | 0.98/0.02/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  8 | FVG_RETRACE_5m  | h1615     | 24690 | 0.0115 |     0.0108 |  0.0043 | -0.0128 |  0.0209 |           5 |          4 |    0.0048 |  0.0164 |  0.0058 |  0.0060 | False         | 1.00/0.00/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  9 | FVG_RETRACE_15m | h12       |  6578 | 0.0064 |     0.0108 |  0.0027 | -0.0042 |  0.0097 |           5 |          3 |    0.0030 |  0.0058 |  0.0050 |  0.0028 | True          | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 10 | FVG_RETRACE_15m | h24       |  5088 | 0.0024 |     0.0108 | -0.0026 | -0.0147 |  0.0091 |           3 |          1 |   -0.0002 | -0.0022 | -0.0012 | -0.0033 | False         | 0.99/0.01/0.00 | REJECT                  |
| 11 | FVG_RETRACE_15m | h1615     |  6578 | 0.0048 |     0.0108 | -0.0029 | -0.0215 |  0.0149 |           4 |          1 |   -0.0037 |  0.0017 | -0.0008 | -0.0005 | False         | 0.98/0.02/0.00 | REJECT                  |
| 12 | CHOCH_5m        | h12       |  4961 | 0.0050 |     0.0108 |  0.0040 | -0.0042 |  0.0121 |           5 |          3 |    0.0036 | -0.0058 |  0.0033 |  0.0008 | True          | 1.00/0.00/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 13 | CHOCH_5m        | h24       |  4614 | 0.0044 |     0.0108 |  0.0014 | -0.0110 |  0.0147 |           4 |          3 |    0.0043 | -0.0088 |  0.0005 | -0.0033 | True          | 0.99/0.01/0.00 | REJECT                  |
| 14 | CHOCH_5m        | h1615     |  4961 | 0.0072 |     0.0108 | -0.0010 | -0.0216 |  0.0191 |           3 |          1 |   -0.0009 | -0.0208 |  0.0021 | -0.0005 | False         | 1.00/0.00/0.00 | REJECT                  |
| 15 | CHOCH_15m       | h12       |  3244 | 0.0104 |     0.0108 |  0.0098 | -0.0013 |  0.0207 |           6 |          4 |    0.0127 |  0.0207 |  0.0050 |  0.0032 | False         | 0.95/0.05/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 16 | CHOCH_15m       | h24       |  2677 | 0.0092 |     0.0108 |  0.0072 | -0.0085 |  0.0233 |           5 |          3 |    0.0105 |  0.0168 |  0.0000 | -0.0028 | False         | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |
| 17 | CHOCH_15m       | h1615     |  3244 | 0.0141 |     0.0108 |  0.0132 | -0.0118 |  0.0367 |           7 |          4 |    0.0100 |  0.0290 |  0.0030 |  0.0034 | False         | 0.97/0.03/0.00 | WEAK_RESEARCH_CLUE_ONLY |

Per-instrument rows: out/index_alpha_master_v1/t109/.

Interpretation: ICT fair value gaps are falsified as an information source once the displacement that creates them is matched; change-of-character is a weak, unresolved restatement of a swing-high breakout. Lane closed.

