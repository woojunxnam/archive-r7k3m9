import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B  # noqa: E402
from t43 import bench, features, v6a  # noqa: E402
from test_v533 import synth_1m  # noqa: E402


@pytest.fixture(scope="module")
def data():
    df = synth_1m(days=90, seed=5, drift=0.01)
    df["cum_adjustment"] = 0.0
    df["roll_adjacent"] = False
    b = B.add_clock(B.aggregate_3m(B.normalise_1m(df)))
    f = features.build(b, 5.0)
    return b, f


def test_feature_prefix_invariance(data):
    b, f = data
    cut = len(b) * 2 // 3
    f2 = features.build(b.iloc[:cut].reset_index(drop=True), 5.0)
    for k in ("vwap_z", "pos_rth", "pos_5d", "d_ATR20", "d_TIER", "d_EMA20", "rsi2", "gap_atr", "vwap_slope", "ret60m_atr"):
        a1 = np.asarray(f[k][:cut], float); a2 = np.asarray(f2[k], float)
        np.testing.assert_allclose(a1, a2, equal_nan=True, err_msg=k)


def test_constant_exposure_matches_benchmark(data):
    b, f = data
    N = 3
    prm = v6a.make_params(capRTH=N, capON=N, marginU=100.0, onMode=4, rollCost=0.0)
    r = v6a.run(b, f, prm)
    first = np.argmax(r["pos"] > 0)
    assert (r["pos"][first:] == N).all()
    # after entry, bar-to-bar equity changes equal N contracts of price change
    de = np.diff(r["equity"][first:])
    dc = np.diff(b.c.values[first:]) * 5 * N
    np.testing.assert_allclose(de, dc, atol=1e-6)


def test_caps_no_short_and_next_open(data):
    b, f = data
    prm = v6a.make_params(capRTH=6, capON=2, marginU=100.0, onMode=4, dipOn=1, dipBoost=0.5, fNeut=0.5, fMed=0.5,
                          fStrong=0.5, fBear=0.5, dipZ=0.5)
    r = v6a.run(b, f, prm)
    assert r["pos"].min() >= 0 and r["pos"].max() <= 6
    o = b.o.values
    for bar, q, px in zip(r["f_bar"], r["f_qty"], r["f_px"]):
        assert px == o[bar] + 0.25 * np.sign(q)
    # overnight (bars fully outside RTH after the trim fill) never above capON
    mod = b["mod"].values; rth = b.in_rth.values
    deep_on = (~rth) & ((mod >= 16 * 60 + 6) | (mod < 9 * 60))
    assert r["pos"][deep_on].max() <= 2


def test_O0_flat_overnight(data):
    b, f = data
    r = v6a.run(b, f, v6a.make_params(capRTH=3, capON=3, marginU=100.0, onMode=0))
    mod = b["mod"].values; rth = b.in_rth.values
    deep_on = (~rth) & ((mod >= 16 * 60 + 6) | (mod < 9 * 60))
    assert r["pos"][deep_on].max() == 0
    assert r["pos"].max() == 3


def test_margin_cap(data):
    b, f = data
    # margin fraction 10% of notional (4800*5=24000 -> 2400/contract); 50% of 150k -> ~31 contracts
    r = v6a.run(b, f, v6a.make_params(capRTH=100, capON=100, marginU=0.5, mIntraFrac=0.1, mOnFrac=0.1, onMode=4))
    notional = b.c.values * 5
    assert (r["pos"] * notional * 0.1 <= 0.5 * r["equity"] + 5000).all()


def test_dd_governor_cuts(data):
    b, f = data
    r0 = v6a.run(b, f, v6a.make_params(capRTH=10, capON=10, marginU=100.0, onMode=4))
    r1 = v6a.run(b, f, v6a.make_params(capRTH=10, capON=10, marginU=100.0, onMode=4, dd1=500.0, ddM1=0.0,
                                       ddRearmTier=9))
    assert r1["pos"].sum() < r0["pos"].sum()
    assert (np.asarray(r1["f_reason"]) == 4).any()


def test_daystop(data):
    b, f = data
    r = v6a.run(b, f, v6a.make_params(capRTH=10, capON=10, marginU=100.0, onMode=4, dayStop=300.0))
    assert (np.asarray(r["f_reason"]) == 5).any()
    assert r["pos"].min() >= 0
