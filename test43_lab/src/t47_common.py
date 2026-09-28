"""TEST47 shared layer (NASSI path / true-bottom / inventory-recycle).  Research data <= 2026-05-27 ONLY: canonical ES / MNQ
1m (hash-verified by t45_common.load1m); no legacy ledger, no TEST46 post-cutoff artefact is read.  Signal market = ES / NQ
price (MNQ canonical prints = NQ price; NO volume is used by any TEST47 signal, so the MNQ-volume substitution issue never
arises); execution = MES / MNQ.  All decisions on completed 5m bars (fill = open of the next 1m bar) or completed 1m bars.

PREDECLARED (written and hashed before any TEST47 economic result): every threshold, grid, control, gate and minimum-sample
rule is in SPEC below and is dumped to out/t47/T47_02_predeclared_spec.json by t47_01_spec.py."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

ROOT = C45.ROOT
T47 = os.path.join(ROOT, "out", "t47")
REP = os.path.join(ROOT, "reports", "TEST47_NASSI_PATH_TRUE_BOTTOM_RECYCLE")
END = pd.Timestamp("2026-05-27")
os.makedirs(T47, exist_ok=True)

SPEC = {
    "unit": "u5 = mean 5m RTH bar range (h-l) over the previous 10 sessions (causal, constant within a session)",
    "leg_defs": {
        "T1": "close-to-close drop c[b-1]-c[b] >= x*u5",
        "T2": "bear body o-c >= x*u5 and close location (c-l)/(h-l) <= 0.35",
        "T3": "lower close AND lower low vs b-1, c[b-1]-c[b] >= x*u5, close location <= 0.50 (no excessive immediate recovery)",
        "T4": "cumulative: reference close (running high close in IDLE, last-leg close afterwards) minus c[b] >= x*u5 -> one leg",
    },
    "x_default": {"T1": 0.75, "T2": 0.75, "T3": 0.5, "T4": 1.5},
    "x_neighbourhood": [0.8, 0.9, 1.0, 1.1, 1.2],
    "nassi_r1": "T1-T3: in IDLE the first bearish bar after a bullish bar does not start the count (source rule 1)",
    "meaningful_up_bar": "c[b]-c[b-1] >= 0.5*u5",
    "neutral_bar": "neither a leg nor a meaningful up-bar",
    "sideways_modes": {"KEEP": "no effect", "DECAY": "every N neutral bars -> count-1", "RESET": "N neutral bars -> count 0"},
    "sideways_grid": {"KEEP": [0], "DECAY": [3, 6], "RESET": [3, 6]},
    "sideways_default": ["RESET", 6],
    "upbar_modes": {"KEEP": "no effect", "DECAY": "count-1", "RESET": "count 0"},
    "upbar_frac_grid": [0.5, 1.0],
    "upbar_default": ["RESET", 1.0],
    "hard_reset": "close >= pre-sequence reference close -> reset; sequence older than max_dur bars -> reset",
    "max_dur_bars": 24,
    "ntick_frontier": [2, 3, 4], "ntick_default": 3,
    "trigger_window_5m_bars": [1, 72],
    "entries": {"E1": "fill at open of first 1m bar after the leg-N 5m close",
                "E2": "source rule 4: first 1m bar of the next 5m bar closes >= its open -> fill next 1m open; else no entry for this event",
                "E3": "first bullish 5m bar (c>o) within 6 bars; fill after its close",
                "E4": "1m grammar within 30 min: new 1m low below leg-N low, then >=2 1m bars without a new low, then a 1m close above the high of the low bar",
                "E5": "5m close above the high of the leg-N bar within 6 bars"},
    "entry_default": "E1",
    "prior_rally": "rally30 = (c[s0-1] - min low of the 6 bars before the first leg) / u5 ; LARGE if >= 4.0",
    "prior_rally_variants": ["NONE", "NEED4", "NOTRADE", "CONFIRM15"],
    "true_bottom_NB": "within 6 bars after leg N: a bar k with (no new low more than 0.25*u5 below the sequence low) AND c[k] >= c[k-1] AND "
                      "(lower-wick ratio >= 0.33 OR c>o); fill after bar k",
    "deceleration": "last leg <= previous leg (ratio <= 1.0)",
    "crash_veto": {"accel": "last leg >= 2.0 x previous leg", "cum": "cumulative displacement >= 10 u5",
                   "gap": "opening gap <= -1.5 ATRd", "ret5": "5-session return <= -3 ATRd", "vol": "ATR20 percentile >= 0.90"},
    "15m": "completed synthetic 15m bars (5m triplets); 15m legs by T1 with x=0.75*u5*sqrt(3); CONFIRM15 = last completed 15m bar bullish",
    "exits": {"X30": "+30m", "X60": "+60m", "X120": "+120m", "X1600": "16:00", "X1615": "16:15",
              "REC50": "5m close >= leg-N close + 0.5 x (reference - leg-N close), else 16:15",
              "TWAP": "5m close >= session TWAP (volume-free), else 16:15", "OPEN": "5m close >= RTH open, else 16:15",
              "REF": "5m close >= pre-sequence reference close, else 16:15"},
    "exit_primary": "X60",
    "recycle": {"cap": 2, "R0": "one entry one contract", "NR_A": "second buy after a NEW complete meaningful leg below lot-1 entry + NB bar; never same bar",
                "NR_B": "blind DCA: 5m close <= lot-1 entry - 2.0*u5 -> add one (diagnostic only)",
                "NR_C": "trim: q=2 and 5m close >= lot-2 entry + 1.0*u5 -> sell 1",
                "NR_D": "NR_A + NR_C + rebuild to 2 on the next validated lower bottom (<= 2 rebuilds / campaign), <= 2 campaigns / session",
                "final_exit": "campaign exit rule = primary exit measured from the FIRST entry (X60) unless stated; 16:15 at latest (intraday)"},
    "overnight": "only campaigns unresolved at 16:15 (REC50 target not reached): hold 16:15 fill -> next 09:31 open vs matched ordinary overnight long",
    "costs": {"base": "commission 0.62 + 1 tick slippage per side", "stress": "4 ticks per side"},
    "min_sample": {"min_trades_2020_2026": 150, "min_years_with_10": 5, "max_single_year_pnl_share": 0.40, "remove_top3_positive": True,
                   "folds_positive_min": 4},
    "matched_null": "same instrument, same fill minute, same calendar year, same ATR20-percentile tercile, same HTF (20d) trend state, same exit",
    "path_order_null": "all (session, 5m bar) windows with the SAME duration d and cumulative drop within the same 0.5-u5 bin, same hour bucket and vol tercile, "
                       "where the leg state machine did NOT reach N legs; excess = event fwd - mean(control fwd)",
    "shuffle": "bars of each W=12 window permuted (20 perms); detector re-run on the synthetic path; E[fwd|real trigger] vs E[fwd|shuffled trigger]",
    "outer_folds": [f[0] for f in C45.OUTER], "stress_year": "2020 (reported, inside the training region of O1)",
    "gate": {"G1": ">= 4/5 outer folds with positive incremental $/day and median outer > 0",
             "G2": "matched-long excess > 0 over 2021-2026-05-27",
             "G3": "remove-top3 campaigns total > 0",
             "G4": "C43+candidate: MaxDD <= 15000, worst day >= -3000, return/DD >= C43 (or standalone excess >= $5/day with G4a,b)",
             "G5": "parameter plateau PASS (all +-10/20% neighbours positive total, >= 60% of base)",
             "G6": "rule recurrence PASS for GA/GP (same semantic cluster selected in >= 3 of 5 outer folds)",
             "G7": "economic contribution >= $5/day incremental over 2021-2026",
             "G8": "min_sample rules", "G9": "beats the simplest same-family control (C1) on outer-fold total"},
}


def u5(mk):
    """mean 5m bar range over the previous 10 sessions (causal)."""
    r = np.nanmean(mk.h - mk.l, axis=1)
    return pd.Series(r).rolling(10, min_periods=5).mean().shift(1).values


def md(path, title, blocks):
    os.makedirs(REP, exist_ok=True)
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b))
        lines.append("")
    open(os.path.join(REP, path), "w").write("\n".join(lines) + "\n")
