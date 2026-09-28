"""TEST56 preregistration: SPARSE STATE EXPOSURE LADDER / BETA-CARRIER-V2 simple controls (daily open rebalance, low turnover)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402

SPEC = {
    "question": "Does a causal daily regime state (BEAR/NEUTRAL/BULL/STRONG_BULL) mapped to a sparse MES-equivalent exposure ladder add TIMING value over a "
                "constant long with the same average exposure, and does it produce a GROWTH-quality portfolio on top of C43 / C43-GROWTH?",
    "rationale": "Index drift is a deliberate structural prior (beta, not alpha).  Trend/volatility state may improve the beta harvest by holding less in hostile "
                 "regimes (2020 crash, 2022 bear) and more in calm persistent uptrends; V5.3.3 failed because inventory was high and constant and it churned.",
    "difference": "Not V5.3.3: one rebalance per session at the open, no intraday recycling, tiers from a sparse ladder, hard margin cap, optional DD governor.",
    "disclosure": "During engine validation (before this file) the full-sample result of map L1 = (0,2,5,8), no vol-target, no governor, was printed "
                  "(net 40.7 $/day, timing value -6.7 $/day). L1 is kept unchanged as predeclared; nothing below was altered after that print.",
    "state_definition": "hx_carrier.daily_state defaults: SMA 20/50/100 of RTH cash closes through the previous session; BULL = close>SMA50 & SMA20>SMA50; "
                        "STRONG_BULL = BULL & SMA100<SMA50 & close>SMA20 & 60d drawdown <= 1.5 ATRd & ATR20 pct <= 0.6; BEAR = (close<SMA50 & (SMA20<SMA50 or "
                        "drawdown >= 5 ATRd)) or (ATR pct >= 0.9 & 5d return < 0); state instrument = ES (applied to both)",
    "ladder": "units snapped to {0,1,2,3,5,8,12,18,24} MES-equivalent; split r_nq = 0.5 of units in MNQ (MNQ contracts = units x ATR$MES/ATR$MNQ); per-symbol <= 24",
    "maps": {"L1": [0, 2, 5, 8], "L2_CONSERVATIVE": [0, 1, 3, 5], "L3_AGGRESSIVE": [1, 3, 8, 12], "L4_VERY_AGGRESSIVE (report)": [2, 5, 12, 18]},
    "variants": {"vol_target": [False, True], "dd_governor": [None, [10000, 20000]]},
    "controls": {"CONST_units": [2, 3, 5, 8], "note": "matched passive long, same split"},
    "margin_cap": 0.40, "decision_clock": "session open only (09:31 fill); rebalance only when the target changes",
    "bases": ["standalone", "C43-CORE + carrier", "C43-GROWTH (TEST55 total<=3) + carrier"],
    "gate": "hx_gate_spec.json lanes; plateau = tier map x0.8/x1.2 (snapped), dd_bear +-20%, SMA (15,40)/(25,60) adjacent -> all positive incremental >= 60%",
    "falsification": "timing value <= 0 for all maps AND no candidate passes GROWTH/CORE",
}

if __name__ == "__main__":
    print(P.prereg("TEST56", SPEC))
