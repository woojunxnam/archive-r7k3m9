# TEST101 event-anchored VWAP — results (prereg 53bc874)

```json
{
 "TEST101_CLASSIFICATION": "REJECT (0/18 EVENT_CLUE; AV_OR30 WEAK_RESEARCH_CLUE_ONLY at all 3 primary horizons)",
 "AV_OR30": "WEAK_RESEARCH_CLUE_ONLY: xF +0.0089 (60m, CI [-0.0010,+0.0189]), +0.0086 (120m), +0.0129 (16:15); 6/8 years, 4/4 instruments, 2021+ stronger; adjacency FAILS (AV_BRK12 / AV_PDH not consistent)",
 "AV_BRK12": "REJECT",
 "AV_PDH": "REJECT (60m weak only)",
 "AVWAP_VS_SESSION_VWAP": "AVWAP hold > session-VWAP hold on raw mean in 12/12 anchor x horizon cells (+0.005..+0.011 ATR); session-VWAP hold after an upside anchor is NEGATIVE vs F101 (deeper pullback confound: the SV hold occurs later / deeper)",
 "EVENT_ANCHORED_VWAP_ADDS_ALPHA": "NO (not an EVENT_CLUE)",
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

|    | variant   | horizon   |    n |    mean |   cost_atr |      xF |   xF_lo |   xF_hi |   years_pos |   inst_pos |   xF_2021 |   x2022 |      xA |      xC | adjacent_ok   | fallback       | class                   |
|---:|:----------|:----------|-----:|--------:|-----------:|--------:|--------:|--------:|------------:|-----------:|----------:|--------:|--------:|--------:|:--------------|:---------------|:------------------------|
|  0 | AV_BRK12  | h12       | 6058 | -0.0005 |     0.0109 | -0.0004 | -0.0090 |  0.0080 |           2 |          2 |    0.0021 | -0.0039 | -0.0020 | -0.0060 | False         | 0.90/0.10/0.00 | REJECT                  |
|  1 | AV_BRK12  | h24       | 5857 | -0.0013 |     0.0109 | -0.0027 | -0.0149 |  0.0089 |           4 |          1 |    0.0008 |  0.0033 | -0.0043 | -0.0103 | True          | 0.89/0.11/0.00 | REJECT                  |
|  2 | AV_BRK12  | h1615     | 6058 |  0.0052 |     0.0109 | -0.0048 | -0.0255 |  0.0171 |           4 |          1 |   -0.0020 |  0.0108 | -0.0032 | -0.0037 | True          | 0.90/0.10/0.00 | REJECT                  |
|  3 | SV_BRK12  | h12       | 4751 | -0.0071 |     0.0108 | -0.0089 | -0.0174 | -0.0005 |           2 |          0 |   -0.0079 | -0.0053 | -0.0080 | -0.0118 | True          | 0.94/0.05/0.00 | REJECT                  |
|  4 | SV_BRK12  | h24       | 4382 | -0.0061 |     0.0108 | -0.0114 | -0.0240 |  0.0014 |           2 |          0 |   -0.0125 | -0.0023 | -0.0077 | -0.0144 | True          | 0.94/0.06/0.00 | REJECT                  |
|  5 | SV_BRK12  | h1615     | 4751 | -0.0027 |     0.0108 | -0.0161 | -0.0368 |  0.0049 |           2 |          0 |   -0.0182 |  0.0018 | -0.0094 | -0.0112 | True          | 0.95/0.05/0.00 | REJECT                  |
|  6 | AV_PDH    | h12       | 3114 |  0.0027 |     0.0109 |  0.0044 | -0.0091 |  0.0183 |           5 |          3 |    0.0071 |  0.0026 | -0.0007 | -0.0097 | True          | 0.88/0.11/0.00 | WEAK_RESEARCH_CLUE_ONLY |
|  7 | AV_PDH    | h24       | 3022 | -0.0045 |     0.0109 | -0.0039 | -0.0219 |  0.0139 |           4 |          1 |   -0.0029 | -0.0071 | -0.0110 | -0.0254 | True          | 0.87/0.12/0.00 | REJECT                  |
|  8 | AV_PDH    | h1615     | 3114 | -0.0057 |     0.0109 | -0.0100 | -0.0386 |  0.0187 |           4 |          0 |   -0.0101 | -0.0002 | -0.0232 | -0.0265 | False         | 0.88/0.11/0.00 | REJECT                  |
|  9 | SV_PDH    | h12       | 2583 | -0.0023 |     0.0110 |  0.0006 | -0.0142 |  0.0158 |           3 |          2 |    0.0024 | -0.0052 | -0.0053 | -0.0147 | False         | 0.90/0.10/0.00 | REJECT                  |
| 10 | SV_PDH    | h24       | 2496 | -0.0106 |     0.0110 | -0.0076 | -0.0280 |  0.0112 |           2 |          1 |   -0.0074 | -0.0184 | -0.0164 | -0.0324 | True          | 0.89/0.11/0.00 | REJECT                  |
| 11 | SV_PDH    | h1615     | 2583 | -0.0143 |     0.0110 | -0.0168 | -0.0496 |  0.0148 |           3 |          0 |   -0.0185 | -0.0314 | -0.0308 | -0.0352 | True          | 0.90/0.10/0.00 | REJECT                  |
| 12 | AV_OR30   | h12       | 4016 |  0.0054 |     0.0107 |  0.0089 | -0.0010 |  0.0189 |           6 |          4 |    0.0145 |  0.0063 |  0.0049 |  0.0007 | False         | 0.75/0.23/0.02 | WEAK_RESEARCH_CLUE_ONLY |
| 13 | AV_OR30   | h24       | 3884 |  0.0066 |     0.0107 |  0.0086 | -0.0059 |  0.0233 |           6 |          4 |    0.0156 |  0.0049 |  0.0040 | -0.0019 | False         | 0.73/0.25/0.02 | WEAK_RESEARCH_CLUE_ONLY |
| 14 | AV_OR30   | h1615     | 4016 |  0.0139 |     0.0107 |  0.0129 | -0.0126 |  0.0363 |           6 |          4 |    0.0194 |  0.0103 |  0.0047 |  0.0042 | False         | 0.75/0.23/0.02 | WEAK_RESEARCH_CLUE_ONLY |
| 15 | SV_OR30   | h12       | 2858 | -0.0059 |     0.0106 | -0.0115 | -0.0239 |  0.0007 |           2 |          1 |   -0.0096 |  0.0009 | -0.0063 | -0.0102 | True          | 0.91/0.09/0.00 | REJECT                  |
| 16 | SV_OR30   | h24       | 2652 | -0.0021 |     0.0106 | -0.0159 | -0.0332 |  0.0013 |           2 |          0 |   -0.0169 |  0.0056 | -0.0036 | -0.0098 | True          | 0.90/0.09/0.00 | REJECT                  |
| 17 | SV_OR30   | h1615     | 2858 |  0.0040 |     0.0106 | -0.0217 | -0.0491 |  0.0033 |           1 |          0 |   -0.0190 |  0.0077 | -0.0029 | -0.0035 | True          | 0.92/0.08/0.00 | REJECT                  |

## AVWAP vs session VWAP (same anchor, same hold rule)

|    | anchor   | horizon   |   AV_mean |   SV_mean |   AV_minus_SV_raw |   AV_xF |   SV_xF |
|---:|:---------|:----------|----------:|----------:|------------------:|--------:|--------:|
|  0 | BRK12    | h6        |    0.0023 |   -0.0032 |            0.0055 |  0.0022 | -0.0022 |
|  1 | BRK12    | h12       |   -0.0005 |   -0.0071 |            0.0065 | -0.0004 | -0.0089 |
|  2 | BRK12    | h24       |   -0.0013 |   -0.0061 |            0.0048 | -0.0027 | -0.0114 |
|  3 | BRK12    | h1615     |    0.0052 |   -0.0027 |            0.0079 | -0.0048 | -0.0161 |
|  4 | PDH      | h6        |    0.0044 |   -0.0030 |            0.0074 |  0.0047 | -0.0010 |
|  5 | PDH      | h12       |    0.0027 |   -0.0023 |            0.0050 |  0.0044 |  0.0006 |
|  6 | PDH      | h24       |   -0.0045 |   -0.0106 |            0.0061 | -0.0039 | -0.0076 |
|  7 | PDH      | h1615     |   -0.0057 |   -0.0143 |            0.0085 | -0.0100 | -0.0168 |
|  8 | OR30     | h6        |    0.0031 |   -0.0037 |            0.0068 |  0.0076 | -0.0058 |
|  9 | OR30     | h12       |    0.0054 |   -0.0059 |            0.0112 |  0.0089 | -0.0115 |
| 10 | OR30     | h24       |    0.0066 |   -0.0021 |            0.0087 |  0.0086 | -0.0159 |
| 11 | OR30     | h1615     |    0.0139 |    0.0040 |            0.0100 |  0.0129 | -0.0217 |

Per-instrument rows: out/index_alpha_master_v1/t101/.

Interpretation: an anchored-VWAP hold after an opening-range upside resolution is the best-looking cell of the family (positive at every horizon, all instruments) but does not clear the date-clustered CI and does not replicate on the other anchors. Session-VWAP holds after an upside anchor are negative. Family SATURATED; AV_OR30 is recorded as a weak clue only (not reopened by neighbour search).

