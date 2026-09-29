"""Engine unit tests (EXECUTION_SPEC EXEC-1.0). Synthetic bars; no dependency on the canonical file
except the optional real-data DST test."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mesgrid.data import bars_from_frame, CANONICAL_PATH  # noqa: E402
from mesgrid.engine import Engine, ExecConfig, LaneSpec, Order, ceil_tick  # noqa: E402
from mesgrid.strategies import BasketGrid, ScriptedStrategy  # noqa: E402
from mesgrid import metrics  # noqa: E402

PV = 5.0
COM = 0.62


def mk(rows, day="2024-01-10"):
    """rows: list of (hh:mm or full datetime str, o, h, l, c[, contract, adj])"""
    recs = []
    for r in rows:
        t = r[0]
        dt = pd.Timestamp(t) if len(t) > 5 else pd.Timestamp(f"{day} {t}")
        rec = dict(dt=dt, o=r[1], h=r[2], l=r[3], c=r[4])
        rec["contract"] = r[5] if len(r) > 5 else "ESH4"
        rec["cum_adjustment"] = r[6] if len(r) > 6 else 0.0
        recs.append(rec)
    return bars_from_frame(pd.DataFrame(recs), holiday_filter=False)


def flat_bars(n, start="09:31", px=100.0, day="2024-01-10"):
    t0 = pd.Timestamp(f"{day} {start}")
    return [((t0 + pd.Timedelta(minutes=k)).strftime("%Y-%m-%d %H:%M"), px, px, px, px) for k in range(n)]


def run(bars, lanes, script, max_total=32, **cfg):
    e = Engine(bars, ScriptedStrategy(lanes, script, max_total), ExecConfig(**cfg))
    return e.run()


IND = lambda cap=4, tp=3.0: LaneSpec("rec", cap, "individual", tp)  # noqa: E731
BSK = lambda cap=32, tp=25.0: LaneSpec("core", cap, "basket", tp)  # noqa: E731


# 1 single buy / single TP ------------------------------------------------------------
def test_single_buy_single_tp():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 101, 99.5, 100.5), ("09:33", 100.5, 103.5, 100.5, 103)]
    e = run(mk(rows), [IND()], {0: [Order("market_buy", "rec")]})
    assert len(e.trades_df) == 1
    t = e.trades_df.iloc[0]
    assert t.entry_px == 100.25 and t.exit_px == ceil_tick(100.25 + 3) == 103.25
    assert t.exit_idx == 2
    assert t.net == pytest.approx((103.25 - 100.25) * PV - 2 * COM)
    assert e.realized_net == pytest.approx(t.net)


# 2 multiple buys / basket average -----------------------------------------------------
def test_basket_average():
    rows = flat_bars(5)
    rows[1] = (rows[1][0], 100, 100, 100, 100)
    rows[2] = (rows[2][0], 90, 90, 90, 90)
    e = run(mk(rows), [BSK()], {0: [Order("market_buy", "core")], 1: [Order("market_buy", "core")]})
    ln = e.lanes["core"]
    assert ln.qty == 2
    assert ln.avg == pytest.approx((100.25 + 90.25) / 2)
    assert ln.basket_target() == ceil_tick(95.25 + 25) == 120.25


# 3 individual tranche exit -------------------------------------------------------------
def test_individual_tranche_exit_only_one():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 95, 95, 95, 95),
            ("09:34", 95, 98.5, 95, 98)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("market_buy", "rec")], 1: [Order("market_buy", "rec")]})
    # tranche1 @100.25 TP 103.25 (not reached), tranche2 @95.25 TP 98.25 -> needs H>=98.5: reached
    assert len(e.trades_df) == 1
    assert e.trades_df.iloc[0].entry_px == 95.25
    assert e.lanes["rec"].qty == 1 and e.lanes["rec"].tranches[0].entry_px == 100.25


# 4 basket exit --------------------------------------------------------------------------
def test_basket_exit_all_at_target():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 90, 90, 90, 90),
            ("09:34", 90, 120.25, 90, 120), ("09:35", 120, 120.5, 119, 120.5)]
    e = run(mk(rows), [BSK()], {0: [Order("market_buy", "core")], 1: [Order("market_buy", "core")]})
    # target 120.25: bar 09:34 high 120.25 < 120.5 -> no fill; bar 09:35 high 120.5 -> fill
    assert len(e.trades_df) == 2
    assert set(e.trades_df.exit_idx) == {4}
    assert (e.trades_df.exit_px == 120.25).all()
    assert e.lanes["core"].qty == 0
    assert len(e.cycles_df) == 1 and e.cycles_df.iloc[0].entries == 2


# 5 simultaneous open tranches (two lanes) -------------------------------------------------
def test_simultaneous_tranches_two_lanes():
    rows = flat_bars(4)
    e = run(mk(rows), [BSK(2), IND(2)], {0: [Order("market_buy", "core"), Order("market_buy", "rec"),
                                                  Order("market_buy", "rec")]}, max_total=4)
    assert e.lanes["core"].qty == 1 and e.lanes["rec"].qty == 2
    ids = [t.id for ln in e.lanes.values() for t in ln.tranches]
    assert len(set(ids)) == 3
    assert e.state.qty.iloc[-1] == 3


# 6 max contract enforcement ---------------------------------------------------------------
def test_max_contract_order_rejected():
    rows = flat_bars(4)
    with pytest.raises(AssertionError):
        run(mk(rows), [BSK(2)], {0: [Order("market_buy", "core", qty=3)]}, max_total=2)


def test_basketgrid_never_exceeds_max_in_crash():
    # steady fall 1pt/bar for a whole day -> grid adds every 5pt
    rows = []
    px = 1000.0
    t0 = pd.Timestamp("2024-01-10 09:31")
    for k in range(405):
        rows.append(((t0 + pd.Timedelta(minutes=k)).strftime("%Y-%m-%d %H:%M"), px, px, px - 1, px - 1))
        px -= 1
    e = Engine(mk(rows), BasketGrid(max_qty=8, grid_pts=5), ExecConfig()).run()
    assert e.state.qty.max() == 8
    assert (e.fills_df.side == "BUY").sum() == 8


# 7 session boundary ----------------------------------------------------------------------
def test_session_boundary_no_trades_outside_window():
    rows = [("09:30", 100, 100, 100, 100),  # ETH bar (open 09:29) - not tradeable
            ("09:31", 100, 100, 100, 100), ("16:14", 100, 100, 100, 100), ("16:15", 100, 100, 100, 100),
            ("16:16", 100, 200, 100, 200), ("16:17", 200, 200, 200, 200)]
    bars = mk(rows)
    assert list(bars.tradeable) == [False, True, True, True, False, False]
    calls = []

    def script(ctx, i):
        calls.append(i)
        return [Order("market_buy", "rec")] if i == 1 else []
    e = run(bars, [IND(4, 3.0)], script)
    # strategy called on 09:31 and 16:14 closes only (16:15 close has no same-day next tradeable bar)
    assert calls == [1, 2]
    # buy happened at bar 16:14 open? No: order from bar1 (09:31) targets bar index 2 (16:14) since data consecutive
    assert e.fills_df.iloc[0].idx == 2
    # TP 103.25 reached only at 16:16 (outside window) -> no exit
    assert len(e.trades_df) == 0
    assert e.lanes["rec"].qty == 1


def test_orders_expire_at_session_end():
    rows = [("2024-01-10 16:15", 100, 100, 100, 100), ("2024-01-11 09:31", 90, 90, 90, 90)]
    called = []
    e = run(mk(rows), [IND()], lambda ctx, i: called.append(i) or [Order("market_buy", "rec")])
    assert called == []          # 16:15 close -> next bar is next day -> no order generation
    assert len(e.fills_df) == 0


# 8 overnight carry ----------------------------------------------------------------------
def test_overnight_carry_and_mtm():
    rows = [("2024-01-10 09:31", 100, 100, 100, 100), ("2024-01-10 09:32", 100, 100, 100, 100),
            ("2024-01-10 16:15", 100, 100, 100, 100), ("2024-01-10 20:00", 90, 90, 80, 85),
            ("2024-01-11 09:31", 85, 86, 84, 86), ("2024-01-11 09:32", 86, 104, 86, 104)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("market_buy", "rec")]})
    st = e.state
    # overnight bar: MTM uses its close 85 -> unrealized = (85-100.25)*5
    assert st.unrealized.iloc[3] == pytest.approx((85 - 100.25) * PV)
    assert st.unrealized_low.iloc[3] == pytest.approx((80 - 100.25) * PV)
    assert st.qty.iloc[3] == 1
    # next day exits at TP 103.25
    assert len(e.trades_df) == 1 and e.trades_df.iloc[0].exit_idx == 5


# 9 next-bar-open market entry -------------------------------------------------------------
def test_market_entry_next_open_not_signal_close():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 105, 106, 104, 106)]
    e = run(mk(rows), [BSK()], {0: [Order("market_buy", "core")]})
    f = e.fills_df.iloc[0]
    assert f.idx == 1 and f.px == 105.25 and f.ideal == 105


# 10 limit fill requires penetration --------------------------------------------------------
def test_limit_buy_needs_one_tick_through():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 98, 99), ("09:33", 99, 99, 97.75, 98)]
    e = run(mk(rows), [IND()], {0: [Order("limit_buy", "rec", price=98.0)], 1: [Order("limit_buy", "rec", price=98.0)]})
    # bar 09:32 low == 98 -> no fill; bar 09:33 low 97.75 -> fill at 98
    assert len(e.fills_df) == 1
    f = e.fills_df.iloc[0]
    assert f.idx == 2 and f.px == 98.0 and not f.at_open


def test_limit_buy_gap_through_fills_at_open_with_slippage_cap():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 95, 96, 94, 95)]
    e = run(mk(rows), [IND()], {0: [Order("limit_buy", "rec", price=98.0)]})
    f = e.fills_df.iloc[0]
    assert f.px == 95.25 and f.at_open


def test_tp_needs_one_tick_through_and_gap_fill():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 100, 103.25, 100, 103),
            ("09:34", 110, 111, 109, 110)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("market_buy", "rec")]})
    # TP 103.25; bar 09:33 high == 103.25 -> no; bar 09:34 opens 110 >= TP+tick -> gap fill at max(TP, O - tick)
    t = e.trades_df.iloc[0]
    assert t.exit_idx == 3 and t.exit_px == 109.75 and t.reason == "tp_gap"


# 11 commission / 12 slippage -----------------------------------------------------------------
def test_commission_and_slippage_accounting():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 100, 110, 100, 110),
            ("09:34", 110, 110, 110, 110), ("09:35", 110, 110, 110, 110)]
    script = {0: [Order("market_buy", "rec"), Order("market_buy", "rec")], 2: []}
    e = run(mk(rows), [IND(4, 3.0)], script, commission_per_side=1.0, slippage_ticks=2)
    # 2 buys at 100.5 (2 ticks), TP 103.5, exit intrabar at 103.5 (no slippage on limit)
    assert e.commission == pytest.approx(4 * 1.0)
    assert e.slippage == pytest.approx(2 * 0.5 * PV)
    assert e.realized_net == pytest.approx(2 * (3.0 * PV) - 4.0)
    assert e.realized_gross == pytest.approx(2 * (103.5 - 100.0) * PV)
    assert e.realized_gross - e.slippage - e.commission == pytest.approx(e.realized_net)


# 13 same-bar ambiguity ------------------------------------------------------------------------
def test_intrabar_limit_buy_cannot_tp_same_bar():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 104, 97, 100), ("09:33", 100, 104, 100, 101)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("limit_buy", "rec", price=98.0)]})
    t = e.trades_df.iloc[0]
    assert t.entry_idx == 1 and t.exit_idx == 2  # not same bar


def test_intrabar_limit_buy_same_bar_tp_allowed_in_tv_like_mode():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 104, 97, 100), ("09:33", 100, 104, 100, 101)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("limit_buy", "rec", price=98.0)]},
            allow_same_bar_tp_after_intrabar_buy=True)
    assert e.trades_df.iloc[0].exit_idx == 1


def test_market_entry_at_open_may_tp_same_bar():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 104, 100, 103)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("market_buy", "rec")]})
    t = e.trades_df.iloc[0]
    assert t.entry_idx == 1 and t.exit_idx == 1 and t.exit_px == 103.25


def test_basket_tp_skipped_when_intrabar_add_in_same_lane():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100),
            ("09:33", 100, 126, 94, 100),  # add at 95 intrabar and old target 125.25 touched -> ambiguous
            ("09:34", 100, 121, 100, 120)]  # new avg 97.625 -> target 122.75 not reached
    e = run(mk(rows), [BSK()], {0: [Order("market_buy", "core")], 1: [Order("limit_buy", "core", price=95.0)]})
    assert e.ambiguous_bars == 1
    assert len(e.trades_df) == 0 and e.lanes["core"].qty == 2


# 14 recycle slot reopening ---------------------------------------------------------------------
def test_recycle_slot_reopens_next_bar():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 100, 104, 100, 103),
            ("09:34", 103, 103, 103, 103), ("09:35", 103, 103, 103, 103)]

    def script(ctx, i):
        ln = ctx.lane("rec")
        return [Order("market_buy", "rec")] if ln.free > 0 else []
    e = run(mk(rows), [IND(1, 3.0)], script, max_total=1)
    buys = e.fills_df[e.fills_df.side == "BUY"]
    # buy bar1, TP bar2 -> slot free at close of bar2 -> buy bar3 open
    assert list(buys.idx) == [1, 3]
    assert e.trades_df.iloc[0].exit_idx == 2


def test_slot_freed_intrabar_not_reused_same_bar():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 100, 104, 96, 103)]

    def script(ctx, i):
        ln = ctx.lane("rec")
        if i == 0:
            return [Order("market_buy", "rec")]
        if i == 1:
            assert ln.free == 0
            return []  # cannot place a limit buy while full (validator would reject)
        return []
    e = run(mk(rows), [IND(1, 3.0)], script, max_total=1)
    assert (e.fills_df.side == "BUY").sum() == 1


# 15 core/recycle capacity separation -------------------------------------------------------------
def test_lane_capacity_separation():
    rows = flat_bars(6)

    def script(ctx, i):
        core, rec = ctx.lane("core"), ctx.lane("rec")
        out = []
        if core.free:
            out.append(Order("market_buy", "core"))
        if rec.free:
            out.append(Order("market_buy", "rec"))
        return out
    e = run(mk(rows), [BSK(2), IND(1, 50.0)], script, max_total=3)
    assert e.lanes["core"].qty == 2 and e.lanes["rec"].qty == 1
    with pytest.raises(AssertionError):
        run(mk(rows), [BSK(2), IND(1, 50.0)], lambda ctx, i: [Order("market_buy", "rec")] * 2, max_total=3)


def test_overlapping_lane_capacities_total_still_enforced():
    # lanes may overlap (dynamic allocation) but the absolute ceiling is enforced
    with pytest.raises(AssertionError):
        run(mk(flat_bars(2)), [BSK(33), IND(4)], {}, max_total=32)
    rows = flat_bars(6)
    e = run(mk(rows), [BSK(3), IND(3)], lambda ctx, i: [Order("market_buy", "core")] if ctx.total_qty < 4 and ctx.lane("core").free else
            ([Order("market_buy", "rec")] if ctx.total_qty < 4 else []), max_total=4)
    assert e.state.qty.max() == 4
    with pytest.raises(AssertionError):
        run(mk(rows), [BSK(3), IND(3)], lambda ctx, i: [Order("market_buy", "core"), Order("market_buy", "core"), Order("market_buy", "rec")] * (ctx.total_qty < 4), max_total=4)


# 16 MTM equity -----------------------------------------------------------------------------------
def test_mtm_equity_identity():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 100, 104, 100, 103),
            ("09:34", 95, 96, 94, 95)]
    e = run(mk(rows), [IND(4, 3.0)], {0: [Order("market_buy", "rec"), Order("market_buy", "rec")],
                                       2: [Order("market_buy", "rec")]})
    st = e.state
    last = st.iloc[-1]
    open_px = sum(t.entry_px for t in e.lanes["rec"].tranches)
    assert last.unrealized == pytest.approx((95 * e.lanes["rec"].qty - open_px) * PV)
    assert last.equity == pytest.approx(150_000 + e.realized_net + last.unrealized)
    assert e.open_df.unrealized.sum() == pytest.approx(last.unrealized)


# 17 drawdown ---------------------------------------------------------------------------------------
def test_max_drawdown_function():
    eq = np.array([100, 120, 90, 130, 100, 140.])
    dd, p, t = metrics.max_drawdown(eq)
    assert dd == -30 and p == 1 and t == 2 or (dd == -30 and p == 3 and t == 4)
    assert metrics.max_drawdown(np.array([1, 2, 3.]))[0] == 0


# 18 no future-data leakage -----------------------------------------------------------------------------
def test_no_lookahead_truncation_invariance():
    rng = np.random.default_rng(7)
    t0 = pd.Timestamp("2024-01-10 09:31")
    px = 1000.0
    rows = []
    for k in range(400):
        o = px
        c = round((px + rng.normal(0, 2)) * 4) / 4
        h = max(o, c) + 0.25 * rng.integers(0, 6)
        l = min(o, c) - 0.25 * rng.integers(0, 6)
        rows.append(((t0 + pd.Timedelta(minutes=k)).strftime("%Y-%m-%d %H:%M"), o, h, l, c))
        px = c
    full = Engine(mk(rows), BasketGrid(8, 5, 3), ExecConfig()).run()
    for cut in (50, 150, 300):
        part = Engine(mk(rows[:cut]), BasketGrid(8, 5, 3), ExecConfig()).run()
        ff = full.fills_df[full.fills_df.idx < cut - 1].reset_index(drop=True)
        pf = part.fills_df[part.fills_df.idx < cut - 1].reset_index(drop=True)
        pd.testing.assert_frame_equal(ff[["idx", "side", "px", "tranche"]], pf[["idx", "side", "px", "tranche"]])


def test_strategy_sees_only_past_bars():
    rows = flat_bars(10)
    seen = []

    def script(ctx, i):
        seen.append(i)
        return []
    run(mk(rows), [IND()], script)
    assert seen == list(range(9))  # called at close of bars 0..8, never for the last bar


# 19 DST / session transition -------------------------------------------------------------------------
def test_dst_window_is_wall_clock():
    rows = [("2024-03-08 09:30", 1, 1, 1, 1), ("2024-03-08 09:31", 1, 1, 1, 1), ("2024-03-08 16:15", 1, 1, 1, 1),
            ("2024-03-11 09:30", 1, 1, 1, 1), ("2024-03-11 09:31", 1, 1, 1, 1), ("2024-03-11 16:15", 1, 1, 1, 1),
            ("2024-03-11 16:16", 1, 1, 1, 1)]
    b = mk(rows)
    assert list(b.tradeable) == [False, True, True, False, True, True, False]


@pytest.mark.skipif(not os.path.exists(CANONICAL_PATH), reason="canonical data not restored")
def test_real_data_first_window_bar_across_dst():
    df = pd.read_parquet(CANONICAL_PATH, columns=["dt"])
    for d in ["2025-03-07", "2025-03-10", "2025-10-31", "2025-11-03", "2024-03-08", "2024-03-11"]:
        x = df[(df.dt > f"{d} 09:00") & (df.dt <= f"{d} 16:30")]
        tm = x.dt.dt.strftime("%H:%M")
        assert "09:31" in set(tm) and "16:15" in set(tm)


# 20 end-of-data open inventory ---------------------------------------------------------------------------
def test_end_of_data_open_inventory_disclosed():
    rows = [("09:31", 100, 100, 100, 100), ("09:32", 100, 100, 100, 100), ("09:33", 90, 90, 90, 90)]
    e = run(mk(rows), [BSK()], {0: [Order("market_buy", "core")], 1: [Order("market_buy", "core")]})
    assert len(e.open_df) == 2 and len(e.trades_df) == 0
    m = metrics.compute(e)
    assert m["open_qty_end"] == 2
    assert m["unrealized_end"] == pytest.approx(((90 - 100.25) + (90 - 90.25)) * PV)
    assert m["total_mtm_pnl"] == pytest.approx(m["realized_net"] + m["unrealized_end"])
    assert m["open_cycle"] is not None


# extra: roll cost and holiday filter -----------------------------------------------------------------------
def test_roll_cost_charged_on_open_inventory():
    rows = [("2024-03-11 09:31", 100, 100, 100, 100, "ESH4", 0.0), ("2024-03-11 09:32", 100, 100, 100, 100, "ESH4", 0.0),
            ("2024-03-11 17:00", 100, 100, 100, 100, "ESH4", 0.0), ("2024-03-11 18:01", 100, 100, 100, 100, "ESM4", -60.0),
            ("2024-03-12 09:31", 100, 100, 100, 100, "ESM4", -60.0)]
    e = run(mk(rows), [BSK()], {0: [Order("market_buy", "core"), Order("market_buy", "core")]})
    assert e.roll_cost == pytest.approx(2 * (2 * 0.62 + 1.25))
    st = e.state
    # MTM curve reflects roll cost from the roll bar (idx 3)
    assert st.equity.iloc[3] == pytest.approx(st.equity.iloc[2] - e.roll_cost)
    # notional uses raw price = adj - cum_adjustment
    assert st.raw_c.iloc[4] == 160.0


def test_holiday_filter_blocks_trading():
    t0 = pd.Timestamp("2024-01-15 09:31")
    rows = [((t0 + pd.Timedelta(minutes=k)), 1, 1, 1, 1) for k in range(210)]  # ends 13:00 -> holiday
    df = pd.DataFrame([dict(dt=r[0], o=1, h=1, l=1, c=1) for r in rows])
    b = bars_from_frame(df, holiday_filter=True)
    assert b.tradeable.sum() == 0 and 20240115 in b.holiday_days
