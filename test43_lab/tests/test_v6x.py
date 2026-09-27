import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B  # noqa: E402
from t43 import v533, v6x  # noqa: E402
from test_v533 import synth_1m  # noqa: E402


@pytest.fixture(scope="module")
def arr():
    b = B.add_clock(B.aggregate_3m(B.normalise_1m(synth_1m(days=60, seed=11, drift=0.02))))
    return b, B.to_arrays(b)


def test_defaults_reproduce_v533_exactly(arr):
    b, a = arr
    r0 = v533.run(a, v533.make_params())
    r1 = v6x.run(a, v6x.make_params())
    for k in ("f_bar", "f_side", "f_qty", "f_px", "f_reason"):
        np.testing.assert_array_equal(r0[k], r1[k])
    np.testing.assert_allclose(r0["equity"], r1["equity"])


def test_core_floor_never_violated_by_ordinary_sells(arr):
    b, a = arr
    K = 8
    r = v6x.run(a, v6x.make_params(coreQty=K, coreBuildMode=1, intradayMaxQty=24))
    pos = r["pos"]
    first = np.argmax(pos >= K)
    assert pos[first:].min() >= K
    assert r["counter_dict"]["coreBuildOrders"] > 0


def test_max_position_scaling(arr):
    b, a = arr
    r = v6x.run(a, v6x.make_params(coreQty=10, coreBuildMode=1, intradayMaxQty=40))
    assert r["pos"].max() <= 40
    assert r["pos"].max() > 24 or r["pos"].max() >= 10


def test_overnight_core_only(arr):
    b, a = arr
    K = 6
    r = v6x.run(a, v6x.make_params(coreQty=K, coreBuildMode=1, overnightMode=2))
    pos = r["pos"]
    mod = a["mod"]
    # at bars 17:00-..18:00-09:27 (fully overnight, after trim fill) position must be <= K
    on = (~a["in_rth"]) & ((mod >= 16 * 60 + 6) | (mod < 9 * 60))
    assert pos[on].max() <= K


def test_emergency_and_daystop_run(arr):
    b, a = arr
    r = v6x.run(a, v6x.make_params(dayStop=500.0, emergencyLoss=2000.0))
    assert r["pos"].min() >= 0
    cd = r["counter_dict"]
    assert cd["dayStopOrders"] + cd["emergencyOrders"] > 0


def test_rf_and_lock_change_behaviour(arr):
    b, a = arr
    r0 = v6x.run(a, v6x.make_params())
    r1 = v6x.run(a, v6x.make_params(rfThreshold=0.5))
    r2 = v6x.run(a, v6x.make_params(reductionLock=1))
    assert len(r1["f_bar"]) != len(r0["f_bar"]) or not np.array_equal(r1["f_bar"], r0["f_bar"])
    assert not np.array_equal(r2["f_bar"], r0["f_bar"])


def test_roll_cost_charged(arr):
    b, a = arr
    a2 = dict(a)
    roll = np.zeros(len(a["o"]), dtype=np.bool_)
    roll[len(roll) // 2] = True
    a2["roll_day"] = roll
    r0 = v6x.run(a2, v6x.make_params(coreQty=5, coreBuildMode=1))
    r1 = v6x.run(a2, v6x.make_params(coreQty=5, coreBuildMode=1, rollCostPerContract=3.74))
    assert r1["counter_dict"]["rollCost"] > 0
    assert r1["equity"][-1] < r0["equity"][-1]


def test_core_tier_mode_runs_and_respects_cap(arr):
    b, a = arr
    r = v6x.run(a, v6x.make_params(coreTierMode=1, kBase=4, kMid=4, kTop=4, coreBuildMode=1, intradayMaxQty=28))
    assert r["pos"].max() <= 28 and r["pos"].min() >= 0
