"""TEST43-M range module causality: every per-bar feature/state/event must be prefix-invariant."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from t43 import ranges as R  # noqa: E402


def _walk(n=6000, seed=3):
    rng = np.random.default_rng(seed)
    c = 4000 + np.cumsum(rng.normal(0, 1.0, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.uniform(0, 1, n)
    l = np.minimum(o, c) - rng.uniform(0, 1, n)
    sess = (np.arange(n) // 200).astype(np.int64)
    rth = (np.arange(n) % 200) >= 70
    atr14 = np.full(n, 1.5); atrD = np.full(n, 20.0)
    return o, h, l, c, sess, rth, atr14, atrD


def _features(o, h, l, c, sess, rth, atr14, atrD, H=10):
    hi, lo, eff, ovl, rvr, cdisp, tl, th, wn = R.window_metrics(h, l, c, atr14, H)
    q_eff = R.causal_quantiles(eff, sess, rth, [1 / 3], lookback=10, min_sessions=3)
    q_ovl = R.causal_quantiles(ovl, sess, rth, [0.5], lookback=10, min_sessions=3)
    qual = (eff <= q_eff[:, 0]) & (ovl >= q_ovl[:, 0]) & (tl >= 2) & (th >= 2)
    res = R.state_machine(o, h, l, c, atrD, hi, lo, qual, qual, H, sess, 4 * H)
    return (hi, lo, eff, ovl, wn, q_eff[:, 0], qual), res


def test_prefix_invariance():
    full = _walk()
    ff, fr = _features(*full)
    for cut in (1500, 3333, 5001):
        part = tuple(x[:cut] for x in full)
        pf, pr = _features(*part)
        for a, b in zip(ff, pf):
            np.testing.assert_array_equal(np.asarray(a)[:cut], np.asarray(b))
        for a, b in zip(fr[:5], pr[:5]):
            np.testing.assert_array_equal(np.asarray(a)[:cut], np.asarray(b))
        m = fr[5] < cut
        np.testing.assert_array_equal(fr[5][m], pr[5])
        np.testing.assert_array_equal(fr[6][m], pr[6])


def test_frozen_boundaries_do_not_move_within_range_id():
    full = _walk()
    _, (act, RL, RH, st, rid, *_e) = _features(*full)
    for r in np.unique(rid[rid >= 0]):
        m = rid == r
        assert np.nanmax(RL[m]) == np.nanmin(RL[m]) and np.nanmax(RH[m]) == np.nanmin(RH[m])


def test_outcomes_use_next_open():
    o, h, l, c, sess, rth, atr14, atrD = _walk(800)
    hs = np.array([5, 10])
    ret, mfe, mae, *_ = R.outcomes(o, h, l, c, atrD, sess, rth, hs)
    i = 100
    assert np.isclose(ret[i, 0], (c[i + 5] - o[i + 1]) / atrD[i])
    assert np.isclose(mfe[i, 1], (h[i + 1:i + 11].max() - o[i + 1]) / atrD[i])
    assert np.isnan(ret[len(c) - 3, 0])
