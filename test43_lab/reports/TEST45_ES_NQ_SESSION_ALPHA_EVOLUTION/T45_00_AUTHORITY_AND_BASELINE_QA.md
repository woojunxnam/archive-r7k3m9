# T45_00 Authority and baseline QA

Research data: canonical 1m ES/MNQ (hash-verified), session_date <= 2026-05-27 only. Nothing after 2026-05-27 was acquired or opened.

Authorities (sha256 verified, unchanged):

|                                                     | expected                                                         | actual                                                           | ok   |
|:----------------------------------------------------|:-----------------------------------------------------------------|:-----------------------------------------------------------------|:-----|
| out/t44/freeze/TEST44_PRE_OOS_FREEZE.json           | 3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4 | 3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4 | True |
| out/t44/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json | 2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236 | 2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236 | True |
| out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.json  | f50902babcbc848574984abb59c4e9cd435e2a3d20878a66955686b6429d7cc3 | f50902babcbc848574984abb59c4e9cd435e2a3d20878a66955686b6429d7cc3 | True |
| out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.md    | a7e846c4fdfbef214cbd46cb4dc08a661d3344b3b48328ea212f121628decdc3 | a7e846c4fdfbef214cbd46cb4dc08a661d3344b3b48328ea212f121628decdc3 | True |
| src/t44_oos_evaluator.py                            | dde908ea03ae93d31f827c21366f7a2088c8027ab711f86d64dbce37fafa3b29 | dde908ea03ae93d31f827c21366f7a2088c8027ab711f86d64dbce37fafa3b29 | True |
| out/p/freeze/TEST43P_FINAL_PORTFOLIOS.json          | 3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7 | 3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7 | True |
| out/p/freeze/TEST43P_HOLDOUT_ACCEPTANCE_RULES.json  | 62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0 | 62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0 | True |
| out/p/freeze/TEST43P_PRE_VAL_FREEZE.json            | 18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817 | 18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817 | True |
| data/canonical_1m_ES.parquet                        | 2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116 | 2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116 | True |
| data/canonical_1m_MNQ.parquet                       | 66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2 | 66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2 | True |

Frozen controls re-run through 2026-05-27 with the frozen TEST44 code. Daily P&L and positions reproduce the frozen outputs **exactly** (max abs diff 0.0):

|    | candidate                 |   daily_pnl_max_abs_diff |   ALL_total |   ALL_avg |   ALL_max_dd |   ALL_worst |   FH_total |   FH_avg |   FH_max_dd |   FH_worst |   peak_margin_util |
|---:|:--------------------------|-------------------------:|------------:|----------:|-------------:|------------:|-----------:|---------:|------------:|-----------:|-------------------:|
|  0 | CHAMPION_CONTROL_V1       |                    0.000 |   93609.780 |    52.590 |     6193.430 |   -1722.990 |   9690.710 |   58.732 |    6193.430 |  -1523.360 |              0.079 |
|  1 | SIMPLE_INTEGER_CHALLENGER |                    0.000 |   70346.730 |    39.521 |     8819.400 |   -2482.490 |  11218.250 |   67.989 |    8819.400 |  -2482.490 |              0.046 |
|  2 | RIDGE_CHALLENGER          |                    0.000 |   56185.070 |    31.565 |     5465.000 |   -1785.250 |   7398.020 |   44.836 |    1618.360 |  -1104.360 |              0.059 |
|  3 | XGBOOST_CHALLENGER        |                    0.000 |   42404.570 |    23.823 |     5169.710 |   -1785.250 |   7341.510 |   44.494 |    1956.180 |  -1557.500 |              0.053 |

CHAMPION_CONTROL_V1: full history $93,610 (52.59/day, MaxDD $6,193); former TEST43 holdout (USED data) $9,690.71 (58.73/day, MaxDD $6,193, worst $-1,523).

**Causality fix recorded:** the first pass used the Champion position of the 16:12 bar as a feature at decision times 14:30-16:00. That is look-ahead. It was found before selection. Every stage (T45_03, 08-26) was re-run with the Champion position in effect at the decision minute. All numbers here are post-fix.

