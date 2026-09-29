import os, sys
import numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mesgrid.data import bars_from_frame
from mesgrid.engine import Engine, ExecConfig
from mesgrid.strategies import BasketGrid
from mesgrid.features import compute_features
from mesgrid.factory import FactoryStrategy


def rand_df(days=6, seed=1, drift=-0.03):
    rng = np.random.default_rng(seed)
    rows, px = [], 4000.0
    for d in range(days):
        day = pd.Timestamp("2024-01-08") + pd.Timedelta(days=d)
        # a few ETH bars then full RTH window
        for t in ["08:00", "09:00", "09:30"]:
            rows.append(dict(dt=pd.Timestamp(f"{day.date()} {t}"), o=px, h=px + 1, l=px - 1, c=px, v=100))
        t0 = pd.Timestamp(f"{day.date()} 09:31")
        for k in range(405):
            o = px
            c = round((px + rng.normal(drift, 2)) * 4) / 4
            h = max(o, c) + 0.25 * rng.integers(0, 6)
            l = min(o, c) - 0.25 * rng.integers(0, 6)
            rows.append(dict(dt=t0 + pd.Timedelta(minutes=k), o=o, h=h, l=l, c=c, v=int(rng.integers(50, 500))))
            px = c
    return pd.DataFrame(rows)


def run(df, **cfg):
    b = bars_from_frame(df, False)
    F = compute_features(b, b.v)
    return Engine(b, FactoryStrategy(F, **cfg), ExecConfig()).run()


def test_default_factory_equals_baseline():
    df = rand_df()
    b = bars_from_frame(df, False)
    a = Engine(b, BasketGrid(32, 5, 25), ExecConfig()).run()
    f = run(df)
    pd.testing.assert_frame_equal(a.fills_df, f.fills_df)


def test_features_are_causal():
    df = rand_df(seed=4)
    full = compute_features(bars_from_frame(df, False), df.v.values)
    for cut in (500, 1300, 2000):
        part = compute_features(bars_from_frame(df.iloc[:cut], False), df.v.values[:cut])
        for k in full:
            a, b_ = full[k][:cut], part[k]
            if a.dtype == bool:
                assert (a == b_).all(), k
            else:
                assert np.allclose(a, b_, equal_nan=True), k


CONFIGS = [
    dict(core_cap=24, rec_cap=8, rec_roll="pts", rec_roll_x=10),
    dict(core_cap=20, rec_cap=4, emerg_cap=8, emerg_step=10),
    dict(spacing="convex", convex_a=0.2),
    dict(spacing="atr", atr_k=0.75, add_trigger="armed", reversal="prev_high"),
    dict(layer_exit="last2", layer_x=5),
    dict(layer_exit="newest_prof", layer_x=3),
    dict(scale_out=(5, 10, 15), basket_tp=15),
    dict(state=dict(t=(4, 8, 12), mult=(1, 2, 4, float("inf")), recovery_exit="all_ind", rec_exit_x=3), core_cap=24, rec_cap=8, rec_activation="state"),
    dict(gov="mom30", gov_x=1.0, init="vwap", init_k=0.25),
    dict(cap_total=12, notional_L=40, dd_cap_X=500),
    dict(core_cap=16, rec_cap=16, rec_activation="always", rec_anchor="low30", rec_spacing="float", rec_tp_mode="inv"),
    dict(recovery=dict(h=10, rec_tp=2.0, rec_step=10, layer_x=4, confirm="vwap"), core_cap=24, rec_cap=8),
    dict(basket_tp_mode="datr", basket_atr_k=0.2, reclaim_exit="vwap"),
    dict(skip_first=15, lunch_core_off=True, core_cutoff=15 * 60, eth="openloc_init"),
]


@pytest.mark.parametrize("cfg", CONFIGS)
def test_factory_modules_run_causal_and_capped(cfg):
    df = rand_df(seed=7, drift=-0.08)
    full = run(df, **cfg)
    cap = min(cfg.get("cap_total") or 32, 32)
    assert full.state.qty.max() <= 32
    assert full.max_ledger_error < 1e-6
    part = run(df.iloc[:1700], **cfg)
    if len(part.fills_df) == 0:
        assert len(full.fills_df) == 0 or (full.fills_df.idx >= 1699).all()
        return
    ff = full.fills_df[full.fills_df.idx < 1699].reset_index(drop=True)
    pf = part.fills_df[part.fills_df.idx < 1699].reset_index(drop=True)
    pd.testing.assert_frame_equal(ff[["idx", "side", "lane", "px"]], pf[["idx", "side", "lane", "px"]])


def test_rolling_recycle_inventory_neutral():
    df = rand_df(seed=9, drift=-0.15)
    e = run(df, core_cap=8, rec_cap=4, rec_activation="always", rec_roll="pts", rec_roll_x=5)
    rot = e.trades_df[e.trades_df.reason == "rotate"]
    assert len(rot) > 0
    assert e.state.qty_rec.max() <= 4


def test_emergency_lane_only_when_others_full():
    df = rand_df(seed=9, drift=-0.15)
    e = run(df, core_cap=4, rec_cap=2, rec_activation="always", emerg_cap=2, emerg_step=5, emerg_tp=3)
    em = e.fills_df[(e.fills_df.lane == "emerg") & (e.fills_df.side == "BUY")]
    assert len(em) > 0
    st = e.state
    for idx in em.idx:
        assert st.qty_core.iloc[idx - 1] == 4 and st.qty_rec.iloc[idx - 1] == 2
