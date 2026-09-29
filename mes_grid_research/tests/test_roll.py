"""ROLL-1.0 accounting gate tests."""
import os, sys
import numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mesgrid.data import bars_from_frame
from mesgrid.engine import Engine, ExecConfig, LaneSpec, Order
from mesgrid.strategies import ScriptedStrategy, BasketGrid
from mesgrid import metrics

PV = 5.0


def two_contract_bars(raw_old=5000.0, raw_new=5060.0, move_after=0.0):
    """Old contract (adj 0 -> anchor) then new contract trading +60 raw (contango). Raw price flat in each.
    Forward additive adjustment: cum_new = cum_old - spread."""
    rows = []
    for t, px, k, adj in [("2024-03-08 09:31", raw_old, "ESH4", 0.0), ("2024-03-08 09:32", raw_old, "ESH4", 0.0),
                          ("2024-03-08 09:33", raw_old, "ESH4", 0.0), ("2024-03-11 17:00", raw_old, "ESH4", 0.0),
                          ("2024-03-11 18:01", raw_new, "ESM4", -(raw_new - raw_old)),
                          ("2024-03-12 09:31", raw_new + move_after, "ESM4", -(raw_new - raw_old)),
                          ("2024-03-12 09:32", raw_new + move_after, "ESM4", -(raw_new - raw_old)),
                          ("2024-03-12 09:33", raw_new + move_after, "ESM4", -(raw_new - raw_old))]:
        a = px + adj
        rows.append(dict(dt=pd.Timestamp(t), o=a, h=a, l=a, c=a, contract=k, cum_adjustment=adj))
    return bars_from_frame(pd.DataFrame(rows), holiday_filter=False)


def hold(bars, cfg, n=2, lane=LaneSpec("core", 32, "none")):
    return Engine(bars, ScriptedStrategy([lane], {0: [Order("market_buy", lane.name)] * n}), cfg).run()


def test_no_artificial_pnl_from_contango_roll():
    b = two_contract_bars()
    e = hold(b, ExecConfig(slippage_ticks=0, commission_per_side=0, roll_slippage_ticks=0))
    st = e.state
    # raw price jumps +60 at roll, but economic MTM must be exactly 0
    assert st.raw_c.iloc[-1] - st.raw_c.iloc[0] == 60
    assert np.allclose(st.equity.values, 150_000)
    assert e.roll_cost == 0


@pytest.mark.parametrize("mode", ["basis_adjust", "close_reopen"])
def test_roll_preserves_identity_and_basis(mode):
    b = two_contract_bars(move_after=10)
    e = hold(b, ExecConfig(roll_mode=mode))
    assert len(e.roll_ledger) == 2
    led = e.roll_ledger_df
    ids = {t.id for t in e.lanes["core"].tranches}
    assert set(led.tranche) == ids                      # logical identity preserved
    assert (led.old_contract == "ESH4").all() and (led.new_contract == "ESM4").all()
    assert (led.spread == 60).all()
    for t in e.lanes["core"].tranches:
        assert t.contract == 1 and t.rolls == 1
        if mode == "basis_adjust":
            assert t.raw_basis == pytest.approx(5000.25 + 60)   # entry + spread
        else:
            assert t.raw_basis == pytest.approx(5060.0)         # reopened at old close + spread
            assert t.roll_realized == pytest.approx((5000 - 5000.25) * PV)
    # adjusted basis + current cum_adjustment == raw basis (basis_adjust) -> economic equivalence
    st = e.state
    last = st.iloc[-1]
    assert last.unrealized == pytest.approx(2 * (10 - 0.25) * PV)


def test_roll_modes_equal_equity_different_split():
    b = two_contract_bars(move_after=-30)
    a = hold(b, ExecConfig(roll_mode="basis_adjust"))
    c = hold(b, ExecConfig(roll_mode="close_reopen"))
    assert np.allclose(a.state.equity.values, c.state.equity.values)
    la, lc = a.state.iloc[-1], c.state.iloc[-1]
    assert la.realized_broker == pytest.approx(la.realized_net)       # basis_adjust: nothing realized at roll
    assert lc.realized_broker - lc.realized_net == pytest.approx(2 * (5000 - 5000.25) * PV)
    assert lc.realized_broker + lc.unrealized_broker == pytest.approx(la.realized_net + la.unrealized)


def test_roll_costs_configurable():
    b = two_contract_bars()
    e1 = hold(b, ExecConfig(), n=3)
    assert e1.roll_cost == pytest.approx(3 * (2 * 0.62 + 0.25 * 5))
    e2 = hold(b, ExecConfig(roll_slippage_ticks=2.0, commission_per_side=1.0), n=3)
    assert e2.roll_cost == pytest.approx(3 * (2 * 1.0 + 2 * 0.25 * 5))
    assert e2.roll_commission == pytest.approx(6.0) and e2.roll_slippage == pytest.approx(7.5)
    e3 = hold(b, ExecConfig(roll_cost_per_contract=0.0), n=3)
    assert e3.roll_cost == 0


def test_exit_after_roll_ledger_invariant_and_target():
    # basket entered in old contract, TP reached only in new contract; raw target = raw basis avg + tp
    rows = []
    for t, raw, k, adj in [("2024-03-08 09:31", 5000, "ESH4", 0.0), ("2024-03-08 09:32", 5000, "ESH4", 0.0),
                           ("2024-03-08 09:33", 5000, "ESH4", 0.0), ("2024-03-11 18:01", 5060, "ESM4", -60.0),
                           ("2024-03-12 09:31", 5070, "ESM4", -60.0), ("2024-03-12 09:32", 5086, "ESM4", -60.0)]:
        a = raw + adj
        rows.append(dict(dt=pd.Timestamp(t), o=a, h=a + (0.5 if raw == 5086 else 0), l=a, c=a, contract=k, cum_adjustment=adj))
    b = bars_from_frame(pd.DataFrame(rows), holiday_filter=False)
    for mode in ("basis_adjust", "close_reopen"):
        e = Engine(b, ScriptedStrategy([LaneSpec("core", 32, "basket", 25.0)], {0: [Order("market_buy", "core")]}),
                   ExecConfig(roll_mode=mode)).run()
        tr = e.trades_df.iloc[0]
        assert tr.rolls == 1
        # adjusted target = 5000.25 + 25 = 5025.25 adj (= 5085.25 raw in ESM4); bar opens 5026 -> gap fill O - tick
        assert tr.exit_px == 5025.75 and tr.raw_exit == 5085.75 and tr.reason == "basket_tp_gap"
        assert e.max_ledger_error < 1e-6
        assert tr.net == pytest.approx(25.5 * PV - 2 * 0.62)


def test_naive_raw_continuous_creates_phantom_profit():
    """Documenting the failure mode ROLL-1.0 prevents: running on the unadjusted raw series books the spread."""
    b = two_contract_bars()
    rawb = bars_from_frame(pd.DataFrame(dict(dt=b.dt, o=b.o - b.adj, h=b.h - b.adj, l=b.l - b.adj, c=b.c - b.adj)),
                           holiday_filter=False)
    e = hold(rawb, ExecConfig(slippage_ticks=0, commission_per_side=0))
    assert e.state.unrealized.iloc[-1] == pytest.approx(2 * 60 * PV)   # phantom +$600
    good = hold(b, ExecConfig(slippage_ticks=0, commission_per_side=0, roll_slippage_ticks=0))
    assert good.state.unrealized.iloc[-1] == pytest.approx(0)


def test_rolling_replacement_same_bar_capacity():
    rows = [("2024-01-10 09:31", 100), ("2024-01-10 09:32", 100), ("2024-01-10 09:33", 90), ("2024-01-10 09:34", 90)]
    b = bars_from_frame(pd.DataFrame([dict(dt=pd.Timestamp(t), o=p, h=p, l=p, c=p) for t, p in rows]), holiday_filter=False)

    def script(ctx, i):
        ln = ctx.lane("rec")
        if i == 0:
            return [Order("market_buy", "rec")]
        if i == 1:
            t = ln.tranches[0]
            return [Order("market_sell", "rec", tranche_id=t.id, tag="rotate"), Order("market_buy", "rec", tag="rot_buy")]
        return []
    e = Engine(b, ScriptedStrategy([LaneSpec("rec", 1, "individual", 3.0)], script, max_total=1), ExecConfig()).run()
    assert e.state.qty.max() == 1 and len(e.trades_df) == 1
    assert e.trades_df.iloc[0].reason == "rotate"
    assert e.trades_df.iloc[0].net == pytest.approx((89.75 - 100.25) * PV - 2 * 0.62)
    assert e.lanes["rec"].tranches[0].entry_px == 90.25
