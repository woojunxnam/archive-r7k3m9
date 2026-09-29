"""Phase-0 FQ accounting audit: conservation invariants + negative controls."""
import os, sys
import numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from mesgrid.data import bars_from_frame
from mesgrid.engine import Engine, ExecConfig, LaneSpec, Order
from mesgrid.features import compute_features
from mesgrid.factory import FactoryStrategy
from mesgrid.strategies import ScriptedStrategy
from mesgrid.audit import reconcile
from test_factory import rand_df

R1 = dict(rec_activation="always", rec_anchor="low60", rec_spacing="float", rec_step=5.0, rec_tp=3.0)
FQ = {
    "FQ_12_20": dict(R1, core_cap=12, rec_cap=20, recovery=dict(h=12, rec_tp=2.0, rec_step=10.0, layer_x=5.0)),
    "FQ_16_16": dict(R1, core_cap=16, rec_cap=16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=5.0)),
    "FQ_16_16_add": dict(R1, core_cap=16, rec_cap=16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=5.0),
                         add_trigger="armed", reversal="ll_fail"),
}


def with_roll(df):
    df = df.copy()
    k = len(df) // 2
    df["contract"] = ["ESH4"] * k + ["ESM4"] * (len(df) - k)
    df["cum_adjustment"] = [0.0] * k + [-55.0] * (len(df) - k)
    return df


@pytest.mark.parametrize("name", list(FQ))
@pytest.mark.parametrize("seed,drift", [(1, -0.2), (2, 0.0), (3, 0.1), (4, -0.4)])
def test_fq_conservation_and_reconciliation(name, seed, drift):
    df = with_roll(rand_df(days=8, seed=seed, drift=drift))
    b = bars_from_frame(df, False)
    e = Engine(b, FactoryStrategy(compute_features(b, b.v), **FQ[name]), ExecConfig(), audit=True).run()
    r = reconcile(e)
    assert r["audit_bar_checks"] > 0
    assert r["all_ok"], r
    # lane sum == total at every bar (state frame, all bars incl. ETH)
    st = e.state
    lanes = [c for c in st.columns if c.startswith("qty_")]
    assert (st[lanes].sum(axis=1) == st.qty).all()


def test_negative_control_silent_slot_release_is_caught():
    """A strategy that deletes an underwater recycle tranche (the feared 're-centering' bug) must fail the audit."""
    df = rand_df(days=3, seed=5, drift=-0.3)
    b = bars_from_frame(df, False)

    def script(ctx, i):
        rec = ctx.lane("rec")
        if i == 5:
            return [Order("market_buy", "rec")]
        if i == 50 and rec.tranches:
            t = rec.tranches[0]
            rec.tranches.remove(t)      # illegal: free the slot without an exit
        return []
    with pytest.raises(AssertionError):
        Engine(b, ScriptedStrategy([LaneSpec("rec", 4, "individual", 50.0)], script), ExecConfig(), audit=True).run()


def test_negative_control_basis_reset_is_caught():
    df = rand_df(days=3, seed=6, drift=-0.3)
    b = bars_from_frame(df, False)

    def script(ctx, i):
        rec = ctx.lane("rec")
        if i == 5:
            return [Order("market_buy", "rec")]
        if i == 50 and rec.tranches:
            rec.tranches[0].entry_px -= 20.0   # illegal: lower cost basis without realizing P&L
        return []
    with pytest.raises(AssertionError):
        Engine(b, ScriptedStrategy([LaneSpec("rec", 4, "individual", 50.0)], script), ExecConfig(), audit=True).run()


RUN3 = {
    "limit_close": dict(FQ["FQ_16_16"], rec_entry_mode="limit_close"),
    "rec_last": dict(FQ["FQ_16_16"], rec_exit="last", rec_exit_x=3.0),
    "rec_last2": dict(FQ["FQ_16_16"], rec_exit="last2", rec_exit_x=3.0),
    "harvest_rec": dict(FQ["FQ_16_16"], harvest="rec_prof", harvest_x=3.0),
    "harvest_all": dict(FQ["FQ_16_16"], harvest="all_prof", harvest_x=3.0),
    "harvest_partial": dict(FQ["FQ_16_16"], harvest="partial_high", harvest_x=3.0, max_total=12, core_cap=6, rec_cap=6),
    "dd_all": dict(FQ["FQ_16_16"], acct_dd=dict(thr=300.0, mode="all")),
    "dd_core_harvest": dict(FQ["FQ_16_16"], acct_dd=dict(thr=300.0, mode="core_harvest")),
    "dd_progressive": dict(FQ["FQ_16_16"], acct_dd=dict(thr=300.0, mode="progressive")),
    "cooldown": dict(FQ["FQ_16_16"], rec_cooldown_bars=3),
}


@pytest.mark.parametrize("name", list(RUN3))
def test_run3_modules_conserve_and_causal(name):
    df = with_roll(rand_df(days=8, seed=11, drift=-0.2))
    b = bars_from_frame(df, False)
    F = compute_features(b, b.v)
    e = Engine(b, FactoryStrategy(F, **RUN3[name]), ExecConfig(), audit=True).run()
    assert reconcile(e)["all_ok"]
    cut = 2000
    bp = bars_from_frame(df.iloc[:cut], False)
    ep = Engine(bp, FactoryStrategy(compute_features(bp, bp.v), **RUN3[name]), ExecConfig()).run()
    ff = e.fills_df[e.fills_df.idx < cut - 1].reset_index(drop=True)
    pf = ep.fills_df[ep.fills_df.idx < cut - 1].reset_index(drop=True) if len(ep.fills_df) else ep.fills_df
    if len(ff) or len(pf):
        pd.testing.assert_frame_equal(ff[["idx", "side", "lane", "px"]], pf[["idx", "side", "lane", "px"]])


def test_dd_all_pause_blocks_buys():
    df = rand_df(days=6, seed=12, drift=-0.4)
    b = bars_from_frame(df, False)
    e = Engine(b, FactoryStrategy(compute_features(b, b.v), **dict(FQ["FQ_16_16"], acct_dd=dict(thr=500.0, mode="all"))), ExecConfig()).run()
    st = e.state
    dd = st.equity.cummax() - st.equity
    buys = e.fills_df[e.fills_df.side == "BUY"]
    # every buy was decided at a bar close where DD (at close) was below threshold or had resumed below 80%
    for idx in buys.idx:
        assert dd.iloc[idx - 1] < 500.0 + 1e-6
