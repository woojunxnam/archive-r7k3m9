"""RUN-4 Sleeve B: MTF causality, event causality (truncation), fastsim == engine fill-by-fill."""
import os, sys
import numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from mesgrid.data import bars_from_frame
from mesgrid.engine import Engine, ExecConfig
from mesgrid.features import compute_features
from mesgrid.mtf import mtf_bars
from mesgrid.momentum import build_events
from mesgrid import fastsim as fs
from mesgrid.strategies_b import MomentumStrategy
from test_factory import rand_df


def _bars(days=6, seed=3, drift=0.05, drop=0):
    df = rand_df(days=days, seed=seed, drift=drift)
    if drop:
        rng = np.random.default_rng(seed)
        df = df.drop(index=rng.choice(df.index[50:-50], drop, replace=False)).reset_index(drop=True)
    return df


@pytest.mark.parametrize("k", [1, 2, 3, 5, 10, 15, 30, 60])
@pytest.mark.parametrize("drop", [0, 40])
def test_mtf_aggregation_and_completion(k, drop):
    b = bars_from_frame(_bars(drop=drop), False)
    m = mtf_bars(b, k)
    W = np.flatnonzero(b.in_window)
    for j in range(len(m["c"])):
        f, la = m["first"][j], m["last"][j]
        seg = np.arange(f, la + 1)
        seg = seg[b.in_window[seg]]
        assert m["h"][j] == b.h[seg].max() and m["l"][j] == b.l[seg].min()
        assert m["o"][j] == b.o[f] and m["c"][j] == b.c[la]
        cp = m["comp"][j]
        if cp >= 0:
            assert cp >= la                                      # never known before its last 1m bar
            assert b.day[cp] == m["day"][j]
            if cp > la:                                          # delayed completion: final clock minute missing
                assert b.minute[la] < 571 + k * m["bucket"][j] + k - 1
            # no 1m bar at or before comp belongs to a LATER part of this bucket
            assert b.minute[la] <= 571 + k * m["bucket"][j] + k - 1


@pytest.mark.parametrize("seed", [1, 2])
def test_events_are_causal_under_truncation(seed):
    df = _bars(days=8, seed=seed, drop=30)
    b = bars_from_frame(df, False)
    ev, meta, _ = build_events(b, compute_features(b, b.v))
    cut = 5 * 1380
    bp = bars_from_frame(df.iloc[:cut], False)
    evp, _, _ = build_events(bp, compute_features(bp, bp.v))
    for name in ev:
        a = ev[name][ev[name] < cut - 2]
        p = evp[name][evp[name] < cut - 2]
        assert np.array_equal(a, p), name


PARITY = [dict(tp=2.0, tmax=10), dict(tp=3.0, tmax=30), dict(tp=np.inf, tmax=15), dict(tp=5.0, tmax=10**9),
          dict(tp=2.0, tmax=10, cooldown=3), dict(tp=np.inf, tmax=60, trail=2.0), dict(tp=4.0, tmax=30, stop=3.0),
          dict(tp=1.0, tmax=5, cooldown=1), dict(tp=3.0, tmax=30, lim_off=0.0, ttl=1), dict(tp=3.0, tmax=30, lim_off=1.0, ttl=5),
          dict(tp=np.inf, tmax=60, lim_off=2.0, ttl=10, cooldown=2), dict(tp=2.0, tmax=10, lim_off=0.5, ttl=3, trail=3.0)]


@pytest.mark.parametrize("p", PARITY)
@pytest.mark.parametrize("slip", [1, 3])
def test_fastsim_equals_engine(p, slip):
    df = _bars(days=10, seed=7, drop=25)
    b = bars_from_frame(df, False)
    rng = np.random.default_rng(1)
    sig = np.zeros(len(b), bool)
    sig[np.flatnonzero(b.in_window)] = rng.random(b.in_window.sum()) < 0.03
    nxt, last_td, nil, dtm = fs.day_structure(b)
    kw = dict(tp=np.inf, tmax=10**9, stop=np.inf, trail=np.inf, cooldown=0, lim_off=-1.0, ttl=1)
    kw.update(p)
    cap = np.full(len(b), 10, np.int64)
    e_i, x_i, e_p, x_p, rs, ns, ni, nc = fs.sim_single(sig, b.o, b.h, b.l, b.c, b.tradeable, nxt, nil, dtm, kw["tp"], kw["tmax"],
                                                       kw["stop"], kw["trail"], kw["cooldown"], slip, 1, False, cap, 1,
                                                       kw["lim_off"], kw["ttl"])
    ex = ExecConfig(slippage_ticks=slip)
    e = Engine(b, MomentumStrategy(sig, nil, dtm, **kw), ex).run()
    tr = e.trades_df
    assert len(tr) == len(e_i) > 5
    assert np.array_equal(tr.entry_idx.values, e_i) and np.array_equal(tr.exit_idx.values, x_i)
    assert np.allclose(tr.entry_px.values, e_p) and np.allclose(tr.exit_px.values, x_p)
    net = (x_p - e_p) * 5 - 2 * 0.62
    assert np.allclose(tr.net.values, net)
    assert e.state.qty.iloc[-1] == 0


@pytest.mark.parametrize("p", PARITY[:6] + PARITY[8:10])
def test_sized_sim_matches_constant_size(p):
    df = _bars(days=10, seed=9, drop=25)
    b = bars_from_frame(df, False)
    rng = np.random.default_rng(2)
    sig = np.zeros(len(b), bool)
    sig[np.flatnonzero(b.in_window)] = rng.random(b.in_window.sum()) < 0.03
    nxt, last_td, nil, dtm = fs.day_structure(b)
    kw = dict(tp=np.inf, tmax=10**9, stop=np.inf, trail=np.inf, cooldown=0, lim_off=-1.0, ttl=1)
    kw.update(p)
    cap = np.full(len(b), 10, np.int64)
    a = fs.sim_single(sig, b.o, b.h, b.l, b.c, b.tradeable, nxt, nil, dtm, kw["tp"], kw["tmax"], kw["stop"], kw["trail"],
                      kw["cooldown"], 1, 1, False, cap, 3, kw["lim_off"], kw["ttl"])
    z = fs.sim_single_sized(sig, b.o, b.h, b.l, b.c, b.tradeable, nxt, nil, dtm, kw["tp"], kw["tmax"], kw["stop"], kw["trail"],
                            kw["cooldown"], 1, 1, np.full(len(b), 3, np.int64), kw["lim_off"], kw["ttl"])
    for u, v in zip(a[:5], z[:5]):
        assert np.array_equal(u, v)
    assert (z[5] == 3).all()
