# M01 Range definition and QA

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


## Definition (mechanical, causal)
* Trailing windows 15/30/60/120m (5/10/20/40 bars at 3m; 3/6/12/24 at 5m). Metrics per completed bar: overlap ratio
  (mean consecutive-bar overlap / union), directional efficiency |net|/path, width/(bar-ATR14*sqrt(H)), realised-vol
  contraction (sd of H-window changes / sd over 4H), close dispersion, touches of both 25% edges.
* **Qualified balance** = efficiency <= 33rd pct AND overlap >= median AND >=2 touches of each edge. **Compression** =
  qualified AND width <= 33rd pct AND vol-contraction <= median. Percentiles are *causal*: computed per session from the
  previous 60 sessions only (same RTH/ON side). Broad buckets only; no threshold was tuned.
* A qualified window is **frozen** at the bar it qualifies (boundaries never move; unit-tested). Re-freeze only while
  price is inside and no state machine is busy; NEW_BALANCE after an accepted expansion; expiry after 4H bars.
* Session-anchored frozen ranges: prior RTH (known at session open), 2D, 5D, opening range 15/30/60 (frozen at OR close).
* Qualified share of bars ~16-17% for every horizon (ES and MNQ), compression ~6-8%.

## QA
* `tests/test_ranges.py`: prefix invariance of every feature/state/event, frozen boundaries constant per range id,
  outcomes from NEXT bar open — pass.
* Real-data prefix invariance: the VAL build (data to 2025-09-30) reproduces every DEV feature column (105) and all
  917,621 (ES) / 921,631 (MNQ) DEV events exactly (`M08_prefix_invariance_real_data.csv`).
* Bugs found and fixed during the lab (all before any VAL use): (1) prior-RTH / 2D ranges expired at 04:00 (fixed to
  whole session); (2) first-passage counted unresolved windows as failures (volatility artefact; now NaN);
  (3) **session-equal-weighted means leak the future** (1/count weighting depends on the session's later path; BELOW-range
  bars +0.047 ATR session-weighted vs -0.003 ATR occurrence-weighted). All statistics now use occurrence weighting with
  session-clustered robust SE (`t43/mstats.py`).

## Location zones (Part 2) — matched-control t of the 60m return (control: year, tier, vol tercile, clock; no position)
| inst | zone | 120m | 15m | 30m | 5D | 60m | OR30 | PRTH |
|---|---|---|---|---|---|---|---|---|
| ES | ABOVE | 1.4 | 1.1 | 1.1 | -0.3 | 0.5 | 1.1 | 0.6 |
| ES | BELOW | -1.1 | -1.1 | -0.6 | 0.7 | -0.7 | -0.9 | 0.7 |
| ES | LOWER_EDGE | 2.4 | 1.1 | 1.0 | -2.5 | 1.8 | -0.7 | -2.5 |
| ES | LOWER_HALF | 0.4 | -0.8 | 0.9 | -0.2 | -0.5 | -1.0 | -1.8 |
| ES | MID | 0.1 | 0.6 | 0.4 | 1.3 | 0.2 | -0.4 | 0.9 |
| ES | UPPER_EDGE | 0.4 | 0.7 | -0.4 | 0.0 | 1.6 | 0.3 | -0.8 |
| ES | UPPER_HALF | -0.3 | 0.0 | 0.1 | 0.9 | 1.1 | 0.3 | 1.0 |
| MNQ | ABOVE | 0.4 | 0.7 | 1.2 | 0.4 | 2.1 | 1.8 | 1.0 |
| MNQ | BELOW | -1.5 | -0.5 | -0.9 | 0.4 | -1.7 | -1.9 | -0.5 |
| MNQ | LOWER_EDGE | 0.1 | 0.8 | 1.1 | -0.2 | 0.6 | -0.7 | -0.3 |
| MNQ | LOWER_HALF | -0.1 | -0.1 | 0.2 | -1.0 | 0.8 | -0.9 | -1.8 |
| MNQ | MID | 1.1 | 1.6 | 0.6 | -0.1 | 1.4 | -0.4 | 0.9 |
| MNQ | UPPER_EDGE | 0.3 | -0.4 | -0.1 | 1.2 | -0.0 | 1.0 | 0.3 |
| MNQ | UPPER_HALF | 2.0 | -0.1 | 1.1 | -0.7 | -0.0 | 1.2 | 0.6 |

Zones carry no directional information (all |t| < 2.6 except isolated cells; placebo-calibrated critical value ~2.6-2.8).
The hypothesis "MID = low information / BOUNDARY = high information" is **not supported**: the boundaries are not more
informative than the middle; no zone is informative. RANGE_MID_IS_LOW_INFORMATION_ZONE = NO for both instruments.

