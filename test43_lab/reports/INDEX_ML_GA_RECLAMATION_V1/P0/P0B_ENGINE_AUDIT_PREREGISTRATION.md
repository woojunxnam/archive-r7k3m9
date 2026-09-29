# P0B COMMON ENGINE AUDIT — preregistration (alone)

Scope: mp_engine.py (ESP-1 engine), t97_engine.Mkt arrays it reuses, and the per-test detectors reused by the candidate bank (t99, t101, t103,
t104, t106, t109, r1).  Checks (automated; PASS/FAIL recorded):
1 causal_bins prefix invariance: bins for sessions <= 2024-12-31 recomputed with all later data masked must be identical (0 mismatches).
2 family-null membership: the null pool never contains a bar of the tested event set (0 overlaps); target bars only receive a null from their
  own cell / fallback level; fallback shares reported.
3 date clustering: the cluster key of a session is identical across ES / NQ / YM / RTY.
4 cost: cost_atr = 2 x cost_per_side / (point value x ATR_d) matches an independent recomputation (max abs diff < 1e-12).
5 2021+ mask = calendar year >= 2021.
6 BMAX / horizon eligibility: h24 is finite only for decision bars with 5(b+1+24) <= J15 (b <= 55); h12 finite for all b <= 67.
7 entry coordinate: entry[s, b] = FP[s, 5b + 5] (open of the minute after the completed bar).  8 h24 = (FP[s, 5(b+25)] - entry) / ATR_d.
9 ATR_d causality: ATR_d[s] uses only sessions < s (recompute ATR14 of prior RTH ranges; correlation / exact match reported).
10 chained sessions: rolling windows chain across sessions BY DESIGN (documented); count of NaN OHLC inside RTH grids reported.
11 known detector notes: t104 SWH60 / SWL60 levels confirmed at the completion of 5m bar b are usable at decision b (causal; prereg wording said
  "next bar") — the number of affected events is counted; ORH / ORL defined at bar 5 cannot produce a cross at b = 5 (verified).
12 contemporaneous nulls: family / A nulls pool bars from the whole calendar-year cell (a contemporaneous matched COMPARATOR, not a predictor);
  documented, not a leak, because nulls never enter any trading rule or ML feature in this program.
Rule: a FAIL in 1-9 that affects outputs = shared bug -> all contaminated TEST99-115 results invalidated, correction preregistered, affected results
rerun (never averaged).  Detector-specific notes (11) are corrected only if an event would change under the preregistered wording.
