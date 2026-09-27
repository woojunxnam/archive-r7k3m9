# T44_12 Ridge meta allocator specification

TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO.


Sample (sleeve, session); target = session P&L of 1 contract held while the sleeve is ON minus ON-share x passive 1-contract P&L, in daily-ATR
units, clipped +-3. Features (session t-1 information only; no calendar): {"A": ["inten_last", "inten_mean", "on_share_prev", "on_last", "is_MNQ", "cl1", "cl2", "cl3"], "B": ["tier", "atr_pct", "trend20", "trend100"], "C": ["y_roll20", "y_roll60", "y_sd60", "y_dd120"], "D": ["acct_dd", "acct_mu", "acct_ret20"]}. Standardised, Ridge alpha 10.0.
Expanding walk-forward: first fit after 500 sessions, refit every 63 sessions, 1-session purge. Scores map to integer
demand by GATE_POS (keep if score > 0), TOP_HALF (keep sleeves at/above the session median score) or DROP_BOTTOM_Q; never fractional, never extra leverage.
Stacking leakage: meta labels are the frozen sleeves' realised outcomes; no sleeve is refit. The sleeves were optimised on 2019-2024, so the
2021-2024 part of the meta span is in-sample for the BASE strategies (disclosed); 2025-2026 is out of sample for both.
Final fit for OOS: `out/t44/freeze/ridge_final.json` sha256 a8c3a62ea9b15233...
