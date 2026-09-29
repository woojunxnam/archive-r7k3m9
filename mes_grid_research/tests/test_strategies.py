import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mesgrid.data import bars_from_frame
from mesgrid.engine import Engine, ExecConfig
from mesgrid.strategies import BasketGrid, CoreRecycle


def rand_bars(n=1500, seed=3, days=4):
    rng = np.random.default_rng(seed)
    rows, px = [], 1000.0
    per = n // days
    for d in range(days):
        t0 = pd.Timestamp("2024-01-08 09:31") + pd.Timedelta(days=d)
        for k in range(min(per, 405)):
            o = px
            c = round((px + rng.normal(-0.05, 2)) * 4) / 4
            h = max(o, c) + 0.25 * rng.integers(0, 6)
            l = min(o, c) - 0.25 * rng.integers(0, 6)
            rows.append(dict(dt=t0 + pd.Timedelta(minutes=k), o=o, h=h, l=l, c=c))
            px = c
    return pd.DataFrame(rows)


def test_core_recycle_32_0_equals_baseline():
    df = rand_bars()
    a = Engine(bars_from_frame(df, False), BasketGrid(32, 5, 10), ExecConfig()).run()
    b = Engine(bars_from_frame(df, False), CoreRecycle(32, 0, 5, 10), ExecConfig()).run()
    pd.testing.assert_frame_equal(a.fills_df, b.fills_df)
    assert a.realized_net == b.realized_net


def test_core_recycle_respects_caps_and_no_lookahead():
    df = rand_bars(seed=11)
    mk = lambda d: Engine(bars_from_frame(d, False), CoreRecycle(6, 3, 5, 10, 4, 3), ExecConfig(), ).run()  # noqa
    full = mk(df)
    assert full.state.qty_core.max() <= 6 and full.state.qty_rec.max() <= 3
    assert full.state.qty.max() <= 32
    assert (full.fills_df.lane == "rec").any()
    for cut in (300, 700, 1100):
        part = mk(df.iloc[:cut])
        ff = full.fills_df[full.fills_df.idx < cut - 1].reset_index(drop=True)
        pf = part.fills_df[part.fills_df.idx < cut - 1].reset_index(drop=True)
        pd.testing.assert_frame_equal(ff[["idx", "side", "lane", "px"]], pf[["idx", "side", "lane", "px"]])


def test_recycle_core_full_activation_only_trades_when_core_full():
    df = rand_bars(seed=5)
    e = Engine(bars_from_frame(df, False), CoreRecycle(4, 4, 5, 10, 4, 3, activation="core_full"), ExecConfig()).run()
    st = e.state
    rb = e.fills_df[(e.fills_df.lane == "rec") & (e.fills_df.side == "BUY")]
    assert len(rb) > 0
    for idx in rb.idx:
        # decision made at close of idx-1 -> core must have been full then
        assert st.qty_core.iloc[idx - 1] == 4
