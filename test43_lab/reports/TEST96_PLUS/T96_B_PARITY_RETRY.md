# TEST96 Track B - parity retry on canonical NQ (TEST46 rule unchanged)

|    | seed    |   ledger_entries_window |   engine_entries_window |   matched |   ledger_recall |   engine_precision |   price_within_1tick_share |   median_abs_price_diff | PARITY   |
|---:|:--------|------------------------:|------------------------:|----------:|----------------:|-------------------:|---------------------------:|------------------------:|:---------|
|  0 | LC03_NQ |                     198 |                     198 |       198 |           1.000 |              1.000 |                      0.934 |                   0.000 | BLOCKED  |
|  1 | LC05_NQ |                     602 |                     609 |       562 |           0.934 |              0.923 |                      0.950 |                   0.000 | BLOCKED  |


## Diagnostic (NOT a status change)
LC03 on canonical NQ: 198 / 198 ledger entries reproduced at the same timestamp (recall 1.000, precision 1.000).  Price parity under the frozen
TEST46 convention (quarterly median offset) = 0.934 < 0.95 -> **BLOCKED under the frozen rule**.  All 14 mismatches sit in quarters that contain a
contract roll: with a per-contract (roll-period) offset, 202 / 202 matched entries are within 1 tick (1.000).  The gap is a price-reference
convention artefact of the parity rule, not a strategy discrepancy.  Changing the convention after seeing the result would be a post-hoc
amendment, so LC03 stays BLOCKED / RESEARCH_ONLY_APPROX; adopting a per-contract offset convention is a user decision (it would make LC03
RECOVERED_EXACT without touching any threshold).
LC05 on canonical NQ: recall 0.934 / precision 0.923 (was 0.673 / 0.691 on MNQ) -> BLOCKED (remaining gap = TradingView NQ1! volume vs canonical
volume in the RVOL / VWAP filters; not fixable without changing economic inputs).
LC02: ES data unchanged -> BLOCKED (precision 0.978).
