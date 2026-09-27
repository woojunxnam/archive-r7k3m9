# M00 Status

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


Status: TEST43-M COMPLETE (DEV discovery + one-time VAL confirmation). HOLDOUT_OPENED = NO. PORTFOLIO_MEMBERSHIP_CHANGED = NO.
LIVE_AUTHORIZATION = NO. TEST43M_PROMOTE_TO_FINALIST = NO.

Execution architecture note: the +1 bar test is renamed **TIMING_BRITTLENESS_STRESS** (it is a stress on decision-to-fill
timing, not expected latency). Production path = local engine -> local data -> state -> IBKR; TradingView/webhook is
validation/sentinel only. The live engine must log bar-close, decision, submit, IBKR ack and fill timestamps and slippage.
Research fill convention unchanged (completed-bar signal, next-bar-open fill).

Reports: M01..M18 in this folder. Machine-readable tables: `out/m/tables/*.csv`. Code: `src/t43/ranges.py`,
`src/t43/analog.py`, `src/t43/mstats.py`, `src/m_build.py`, `src/m_info.py`, `src/m_analog.py`, `src/m_analog_eval.py`,
`src/m_fractal.py`, `src/m_overlay.py`, `src/m_redadd.py`, `src/m_val_info.py`, `tests/test_ranges.py`.

Next (V6 track, unchanged): reduce finalist count, write + freeze holdout acceptance rules, freeze finalists, open holdout once.

