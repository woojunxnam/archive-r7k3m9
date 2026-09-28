# TEST97 Wave 1 - failure / clue analysis (written before Wave 2 economics)

Scale: all returns in ATR_d units; round-trip micro cost = 0.005 (MNQ) .. 0.015 (MES) ATR_d, pooled ~0.011.  43 pooled variants + 35 response-curve
bins (~425 ledger rows) were tested; ~2-4 nominal CI passes are expected by chance, so only coherent (monotone, multi-instrument) structures count.

| Question | Wave-1 answer |
|---|---|
| Q1 strong 5m bull bar predicts follow-through beyond size / drift? | Weak: canonical STRONG +0.005 xA / +0.009 xB at 60 min (CI includes 0; gross 0.006 < cost). body_pct / close-position curves are flat-to-mildly-monotone; range/ATR5 peaks at 1.25-1.5 and turns NEGATIVE above 3 (exhaustion). STRONG_BAR_HAS_ALPHA = NO (tradeable) |
| Q2 rolling-high breakout adds information? | Monotone in window N: xA 0.005 (N=2) -> 0.011 (N=60), xB 0.008 -> 0.015; driven by NQ / ES; CI still includes 0 |
| Q3 compression improves a burst? | NO: low- vs high-compression bursts matched on burst size alternate sign across size quintiles |
| Q4 follow-through adds timing value? | Confirmation carries INFORMATION (confirmed minus unconfirmed at the same minute: +0.013 ATR / 60 min pooled; ES, NQ, YM positive), graded by confirmation strength (B 0.015 < D 0.015/0.038@16:15 < F 0.040 gross). But it does NOT add timing value vs the (unknowable) original entry, which already contains the confirmation bar |
| Q6 shallow pullback -> second leg | 25-38% depth: +0.08 ATR at 30 min (n = 35); deeper pullbacks ~0 -> clue, tiny sample |
| Q7 fresh second signal after failure | NO (weaker than the first signal) |
| Q10 exhaustion | range > 3 x ATR5 and body >= 0.9 with large range turn negative; VWAP / EMA distance: monotone up to 1 ATR, too few events beyond |
| Q12 HTF alignment | above-VWAP / above-open aligned breakouts beat non-aligned by ~+0.02 ATR at 60 min (small non-aligned n) |
| M07 microchannel | monotone in length k = 2 / 3 / 4: 0.008 / 0.013 / 0.026 gross, 7 / 8 years positive at k = 2 |
| M08 ORB | small positive, CI includes 0; not better than the late-session high break |

**Common thread (clue):** information grows with PERSISTENCE (multi-bar follow-through, longer microchannels, longer breakout windows), not with the
strength of one bar.  Untested alternative explanation: persistence = larger multi-bar DISPLACEMENT, i.e. magnitude, which the 1-bar null B does not
control.  Wave 2 must therefore use a MULTI-BAR magnitude null (same k-bar cumulative displacement decile, time bucket, year).
