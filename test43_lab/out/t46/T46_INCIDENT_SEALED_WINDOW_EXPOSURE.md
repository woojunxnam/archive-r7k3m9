# TEST46 incident: exposure to sealed new-OOS window (2026-05-28+) via a legacy ledger

- When: TEST46 Phase 0 (authority recovery), before any TEST46 model, rule, feature or selection existed.
- What: Google Drive file `SCREEN_1Y_LC03_NQ_T07-11_2025-2026.csv` (id 1SlgqGnNTHiX0uKnwWjJfNGijPprLqyCK) was read in full
  to test whether CSV ledgers can be read as text. The file is a TradingView export of the frozen LC03 (NQ-NOON) strategy
  and contains 26 trades, 8 of which fall on 2026-05-28 .. 2026-08-27 (inside the sealed window). Their dates, entry/exit
  prices and P&L were displayed to the research agent.
- Not done: the content was NOT saved, parsed, summarised further, or used in any computation. No market data after
  2026-05-27 was loaded into the lab. Nothing in this repository contains those rows.
- Frozen authorities are unaffected: TEST44 (3401331f.../2f74e2ca...) and TEST45 (185d1ef9.../76941f63...) were frozen and
  pushed BEFORE this exposure.
- Consequence for TEST46: every legacy FULL_HISTORY / SCREEN ledger on Drive was exported ~2026-09-15 and very likely
  contains post-2026-05-27 trades. Reading any of them whole (the Drive connector returns full files) re-exposes the sealed
  window. TEST46 Phase 0 ledger parity therefore cannot proceed without a user decision.
- Status: TEST46 paused at Phase 0. NEW_OOS_DATA_ACQUIRED (lab data) = NO; sealed-window legacy-ledger rows VIEWED = YES (8 LC03 trades).
