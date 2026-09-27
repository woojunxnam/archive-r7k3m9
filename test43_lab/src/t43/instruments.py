"""Instrument profiles (external constraints; never optimised).

IBKR initial-margin references are the values supplied by the user for 2026-09-27
(to be re-verified before final Pine freeze).  For historical simulation the margin
is scaled with the contract's RAW price relative to the reference price level, i.e. a
constant fraction of notional (margin requirements broadly track notional/vol).
"""
PROFILES = {
    "MES": dict(symbol="MES", data="ES", point_value=5.0, tick=0.25, tick_value=1.25,
                commission_side=0.62, ibkr_intraday=2502.605, ibkr_overnight=3575.15,
                ref_price=7800.0),
    "MNQ": dict(symbol="MNQ", data="MNQ", point_value=2.0, tick=0.25, tick_value=0.50,
                commission_side=0.62, ibkr_intraday=4833.22, ibkr_overnight=6904.59,
                ref_price=None),  # filled from data (raw close on the last canonical session)
}


def margin_frac(profile, kind="overnight"):
    ref = profile["ibkr_" + kind]
    return ref / (profile["ref_price"] * profile["point_value"])
