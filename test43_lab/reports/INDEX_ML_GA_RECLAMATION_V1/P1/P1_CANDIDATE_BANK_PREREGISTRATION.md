# P1 CANDIDATE_BANK_V1 + FROZEN FEATURE DICTIONARY — preregistration (alone)

No economics are computed in P1 beyond copying already-committed MASTER statistics for the Tier-A check.
After the P1 result commit NO candidate may be added except through a separately preregistered NEW_CANDIDATE_MEMO.

## Members (exact frozen historical code; event parity vs the committed MASTER per-instrument event counts is REQUIRED — any mismatch
-> that candidate is IMPLEMENTATION_BLOCKED)
C1 R1_TRAPPED_UNION (RESERVE_R1, r1_trapped.py; constituent label = P2 / L2_<level> / A3)
C2 P2_FAILED_FIRST (TEST103)          C3 P1_H2 (TEST103)
C4 L2_FAILED_BREAKDOWN_FAMILY = L2_PDL + L2_PWL + L2_ORL + L2_SWL60 + L2_L2H (TEST104; level type = categorical feature; one population)
C5 HTF1_30m (TEST99)                  C6 AV_OR30 (TEST101)          C7 L1_SWH60 (TEST104)          C8 CHOCH_15m (TEST109, low priority)
REFERENCE ONLY: A2_A_UP_IMMEDIATE and ORB_COMPARATOR (TEST106) — duplicate control, never counted as an independent candidate.
Overlap note: C1 contains C2 and C4 events (first event per instrument-session) -> C1, C2 and C4 are the SAME mechanism exposure for portfolio
purposes (at most one of them may enter a frontier; no double counting).

## Frozen horizon per candidate (deterministic rule applied to committed MASTER pooled statistics): among the primary horizons 60 min (h12),
120 min (h24), 16:15 (h1615) with pooled family-null excess xF > 0, the one with the highest pooled gross mean.  (For C4 the pooled L2 statistics
are the event-weighted averages of the five L2 rows.)

## Tier-A check (program section 6) from committed MASTER statistics at the frozen horizon: n >= 500 (or grouped), xF > 0, >= 5/8 positive
years or repeated related evidence, >= 3/4 instruments or documented structure, gross mean >= 0.9 x round-trip cost.

## CORE_FEATURE_SET (<= 40 columns; all known at the completion of the decision bar b; scaling fitted on training data only)
identity: inst_ES/NQ/YM/RTY (4), constituent one-hot (family-specific, <= 7), tod = b / 80.
geometry (5m bar b, ATR_d units unless stated): disp1, rng_atr5 (range / ATR5), body_pct, cpos, disp6 = (c_b - c_{b-6}) / ATR_d,
  disp12, rng12 = (max h - min l over the last 12 chained bars) / ATR_d.
session: sess_ret = (c - open) / ATR_d, sess_range = (high_so_far - low_so_far) / ATR_d, dist_hi = (high_so_far - c) / ATR_d,
  dist_lo = (c - low_so_far) / ATR_d, or_pos = (c - ORL30) / (ORH30 - ORL30) for b >= 6 else missing, gap = (open - prior close) / ATR_d,
  bars_since_low = (b - bar of the session low so far) / 80.
VWAP: vwap_dist = (c - VWAP) / ATR_d, vwap_slope6 = (VWAP_b - VWAP_{b-6}) / ATR_d, share_above_vwap12 (last min(12, b+1) closes).
HTF (daily, prior sessions only): up50 (close > SMA50), adx14, di_up (+DI > -DI), stage_slope = (SMA150_t - SMA150_{t-20}) / ATR_d,
  tsmom12, tsmom1 (TEST115 definitions), prev_ret = prior-day close-to-close / ATR_d.
volatility: vt (engine tercile), atr_ratio = mean range 5d / 60d, atr5_rel = ATR5 / ATR_d.
Missing values imputed with the training-window median (fit on training only).  No cross-index features.
Tags (SOURCE / DEFINITION / AVAILABLE_AT / NORMALIZATION / FAMILY_RELEVANCE) are written to FEATURE_DICTIONARY.csv.

## Targets stored per event: net ATR return at h12 / h24 / h1615 (gross minus micro round-trip cost), net micro dollars (base cost) and SLIP4
dollars at each horizon, entry FP[5b+5], exit FP at the horizon (engine coordinates), date, year, instrument, session, decision bar.
