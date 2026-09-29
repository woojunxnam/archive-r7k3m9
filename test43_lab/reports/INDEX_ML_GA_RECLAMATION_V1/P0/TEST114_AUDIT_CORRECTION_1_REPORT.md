# TEST114_AUDIT_CORRECTION_1 — results (prereg 132379e)

```json
{
 "TEST114_CLOCK_CORRECTION_STATUS": "CORRECTED (exit FP[389] = 15:59 price -> C[389] = 16:00 close; 16:15 sensitivity FP[404] -> C[404]); entry / references were already correct",
 "G1_R1_CORRECTED": "xN -0.0074 ATR [-0.0176,+0.0029] (was -0.0082); 0/4 instruments positive; 2/8 years",
 "G2_R1_R12_CORRECTED": "xN -0.0015 (REJECT)",
 "G1_R1_X1615_CORRECTED": "xN -0.0067 (REJECT)",
 "DUPLICATION_TEST_CORRECTED": "r1>0 minus r1<=0 within TB sessions -0.0161 [-0.0328,-0.0006] (reversal persists)",
 "GHLZ_REPLICATION": "CLOSED (sign remains negative after the exact-clock correction; not materially changed)",
 "CORRECTED_RESULT_REPLACES_OLD": "YES (no averaging)"
}
```

| variant         | horizon   |    n |    mean |   net_mean |   cost_atr |      xN |   ci_lo |   ci_hi |   years_pos |   inst_pos |   x2021 |   x2022 |    x_ES |    x_NQ |   x_RTY |    x_YM | class   |
|:----------------|:----------|-----:|--------:|-----------:|-----------:|--------:|--------:|--------:|------------:|-----------:|--------:|--------:|--------:|--------:|--------:|--------:|:--------|
| G1_R1           | R16       | 3769 | -0.0122 |    -0.0231 |     0.0109 | -0.0074 | -0.0176 |  0.0029 |           2 |          0 | -0.0061 | -0.0131 | -0.0053 | -0.0072 | -0.0075 | -0.0097 | REJECT  |
| G2_R1_R12       | R16       | 2039 | -0.0068 |    -0.0176 |     0.0108 | -0.0015 | -0.0126 |  0.0092 |           5 |          1 | -0.0059 |  0.0061 |  0.004  | -0.0071 | -0.0005 | -0.0019 | REJECT  |
| G1_R1_X1615     | R1615     | 3769 | -0.009  |    -0.0199 |     0.0109 | -0.0067 | -0.0165 |  0.0036 |           1 |          0 | -0.0059 | -0.0196 | -0.006  | -0.0094 | -0.0056 | -0.0058 | REJECT  |
| TB_OPEN_CONTROL | R16       | 3693 | -0.0049 |    -0.0157 |     0.0108 | -0.0005 | -0.0093 |  0.0086 |           5 |          1 | -0.0022 |  0.0209 | -0.0002 | -0.0027 | -0.0022 |  0.003  | REJECT  |
