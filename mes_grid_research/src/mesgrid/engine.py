"""Deterministic event-driven 1m backtester for long-only multi-lane MES inventory.

Execution rules follow EXECUTION_SPEC.md (EXEC-1.0). Key points:
- strategy decides on completed bar t; orders live only on bar t+1 (same trading day);
- market orders fill at open +slippage; limit orders need 1-tick penetration;
- a tranche bought by an intrabar limit cannot exit on the same bar;
- a lane with an intrabar limit buy does not evaluate its basket TP on that bar.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from . import ENGINE_VERSION, EXEC_SPEC_VERSION
from .data import Bars

TICK = 0.25


def ceil_tick(x: float) -> float:
    return math.ceil(round(x / TICK, 9)) * TICK


def floor_tick(x: float) -> float:
    return math.floor(round(x / TICK, 9)) * TICK


@dataclass
class ExecConfig:
    point_value: float = 5.0
    commission_per_side: float = 0.62
    slippage_ticks: int = 1
    penetration_ticks: int = 1
    allow_same_bar_tp_after_intrabar_buy: bool = False
    roll_cost_per_contract: float = 2 * 0.62 + 1.25
    initial_capital: float = 150_000.0
    spec_version: str = EXEC_SPEC_VERSION


@dataclass
class LaneSpec:
    name: str
    capacity: int
    exit_mode: str = "basket"          # "basket" | "individual" | "none"
    tp_pts: float = 25.0


@dataclass
class Order:
    kind: str                           # "market_buy" | "limit_buy" | "market_sell"
    lane: str
    qty: int = 1
    price: Optional[float] = None       # limit price
    tp_pts: Optional[float] = None      # per-tranche TP override (individual mode)
    tranche_id: Optional[int] = None    # for market_sell
    tag: str = ""


@dataclass
class Tranche:
    id: int
    lane: str
    qty: int
    entry_px: float
    entry_ideal: float
    entry_idx: int
    entry_dt: np.datetime64
    filled_at_open: bool
    tp_px: Optional[float]
    tag: str
    cycle_id: int
    lane_cycle_id: int


class LaneState:
    def __init__(self, spec: LaneSpec):
        self.spec = spec
        self.tranches: list[Tranche] = []
        self.last_entry_px: Optional[float] = None
        self.last_exit_px: Optional[float] = None
        self.cycle_id = 0
        self.cycle_start_idx: Optional[int] = None

    @property
    def qty(self) -> int:
        return sum(t.qty for t in self.tranches)

    @property
    def avg(self) -> Optional[float]:
        q = self.qty
        if q == 0:
            return None
        return sum(t.entry_px * t.qty for t in self.tranches) / q

    @property
    def free(self) -> int:
        return self.spec.capacity - self.qty

    def basket_target(self) -> Optional[float]:
        a = self.avg
        return None if a is None else ceil_tick(a + self.spec.tp_pts)


class Context:
    """Read-only view handed to strategies."""

    def __init__(self, engine: "Engine"):
        self._e = engine
        self.bars = engine.bars

    def lane(self, name: str) -> LaneState:
        return self._e.lanes[name]

    @property
    def lanes(self):
        return self._e.lanes

    @property
    def total_qty(self) -> int:
        return self._e.total_qty()

    @property
    def max_total(self) -> int:
        return self._e.max_total

    @property
    def fills_this_bar(self):
        return self._e.bar_fills


class Strategy:
    lanes: list[LaneSpec] = []
    max_total: int = 32

    def on_start(self, ctx: Context):
        pass

    def on_bar_close(self, ctx: Context, i: int) -> list[Order]:
        return []

    def observe(self, ctx: Context, i: int):
        """Called after every tradeable bar (incl. the last of the day) before on_bar_close.
        For state updates only; cannot place orders."""
        pass


class Engine:
    def __init__(self, bars: Bars, strategy: Strategy, cfg: ExecConfig | None = None):
        self.bars = bars
        self.s = strategy
        self.cfg = cfg or ExecConfig()
        self.lanes = {sp.name: LaneState(sp) for sp in strategy.lanes}
        self.max_total = strategy.max_total
        assert sum(sp.capacity for sp in strategy.lanes) <= self.max_total, "lane capacities exceed max_total"
        self.next_tid = 1
        self.cycle_id = 0
        self.cycle_start_idx = None
        self.realized_net = 0.0
        self.realized_gross = 0.0
        self.commission = 0.0
        self.slippage = 0.0
        self.roll_cost = 0.0
        self.trades: list[dict] = []
        self.fills: list[dict] = []
        self.cycles: list[dict] = []
        self.lane_cycles: list[dict] = []
        self.roll_events: list[tuple[int, float]] = []
        self.ambiguous_bars = 0
        self.bar_fills: list[dict] = []
        self.cancelled_capacity = 0

    # ------------------------------------------------------------------ helpers
    def total_qty(self) -> int:
        return sum(ls.qty for ls in self.lanes.values())

    def _commission(self, qty):
        c = qty * self.cfg.commission_per_side
        self.commission += c
        return c

    def _open_tranche(self, lane: LaneState, qty, px, ideal, i, at_open, tp_pts, tag):
        b = self.bars
        if self.total_qty() == 0:
            self.cycle_id += 1
            self.cycle_start_idx = i
            self._cycle_stats = dict(entries=0, max_qty=0, worst_mtm=0.0, worst_mtm_low=0.0, realized=0.0)
        if lane.qty == 0:
            lane.cycle_id += 1
            lane.cycle_start_idx = i
            lane._cstats = dict(entries=0, max_qty=0, realized=0.0)
        tp_px = None
        if lane.spec.exit_mode == "individual":
            tp_px = ceil_tick(px + (tp_pts if tp_pts is not None else lane.spec.tp_pts))
        t = Tranche(self.next_tid, lane.spec.name, qty, px, ideal, i, b.dt[i], at_open, tp_px, tag,
                    self.cycle_id, lane.cycle_id)
        self.next_tid += 1
        lane.tranches.append(t)
        lane.last_entry_px = px
        c = self._commission(qty)
        self.realized_net -= c
        self.slippage += (px - ideal) * qty * self.cfg.point_value
        self._cycle_stats["entries"] += 1
        self._cycle_stats["max_qty"] = max(self._cycle_stats["max_qty"], self.total_qty())
        lane._cstats["entries"] += 1
        lane._cstats["max_qty"] = max(lane._cstats["max_qty"], lane.qty)
        f = dict(idx=i, dt=b.dt[i], side="BUY", lane=lane.spec.name, tranche=t.id, qty=qty, px=px,
                 ideal=ideal, at_open=at_open, tag=tag)
        self.fills.append(f)
        self.bar_fills.append(f)
        return t

    def _close_tranche(self, lane: LaneState, t: Tranche, px, ideal, i, reason):
        b = self.bars
        pv = self.cfg.point_value
        lane.tranches.remove(t)
        c = self._commission(t.qty)
        pnl_px = (px - t.entry_px) * t.qty * pv
        gross = (ideal - t.entry_ideal) * t.qty * pv
        self.realized_net += pnl_px - c
        self.realized_gross += gross
        self.slippage += (ideal - px) * t.qty * pv
        lane.last_exit_px = px
        net = pnl_px - c - t.qty * self.cfg.commission_per_side  # include entry commission in trade net
        self.trades.append(dict(tranche=t.id, lane=t.lane, qty=t.qty, entry_idx=t.entry_idx, exit_idx=i,
                                entry_dt=t.entry_dt, exit_dt=b.dt[i], entry_px=t.entry_px, exit_px=px,
                                gross=gross, net=net, reason=reason, tag=t.tag, cycle=t.cycle_id,
                                lane_cycle=t.lane_cycle_id))
        f = dict(idx=i, dt=b.dt[i], side="SELL", lane=lane.spec.name, tranche=t.id, qty=t.qty, px=px,
                 ideal=ideal, at_open=None, tag=reason)
        self.fills.append(f)
        self.bar_fills.append(f)
        self._cycle_stats["realized"] += net
        lane._cstats["realized"] += net
        if lane.qty == 0:
            self.lane_cycles.append(dict(lane=lane.spec.name, lane_cycle=lane.cycle_id,
                                         start_idx=lane.cycle_start_idx, end_idx=i,
                                         start_dt=b.dt[lane.cycle_start_idx], end_dt=b.dt[i], **lane._cstats))
        if self.total_qty() == 0:
            self.cycles.append(dict(cycle=self.cycle_id, start_idx=self.cycle_start_idx, end_idx=i,
                                    start_dt=b.dt[self.cycle_start_idx], end_dt=b.dt[i], **self._cycle_stats))

    # ------------------------------------------------------------------ main loop
    def run(self):
        b = self.bars
        cfg = self.cfg
        tick = TICK
        slip = cfg.slippage_ticks * tick
        pen = cfg.penetration_ticks * tick
        n = len(b)
        ctx = Context(self)
        self.s.on_start(ctx)

        trade_idx = np.flatnonzero(b.tradeable)
        # state snapshots at tradeable bars (and roll bars): qty, sum(px*qty), realized, per-lane qty
        lane_names = list(self.lanes)
        snap_idx = []
        snap_qty = []
        snap_sum = []
        snap_real = []
        snap_lane = {ln: [] for ln in lane_names}
        roll_idx = np.flatnonzero(np.diff(b.contract) != 0) + 1
        rp = 0
        pending: list[Order] = []
        pending_for = -1

        for i in trade_idx:
            # roll costs for rolls that happened since last processed bar
            while rp < len(roll_idx) and roll_idx[rp] <= i:
                q = self.total_qty()
                if q:
                    cost = q * cfg.roll_cost_per_contract
                    self.roll_cost += cost
                    self.realized_net -= cost
                    self.roll_events.append((int(roll_idx[rp]), cost))
                rp += 1
            self.bar_fills = []
            orders = pending if pending_for == i else []
            pending = []
            O, H, L = b.o[i], b.h[i], b.l[i]
            intrabar_lanes = set()
            intrabar_tids = set()

            # 1) existing TP orders: gap-through at open (state before this bar's entries)
            self._exits_at_open(i, O, pen)
            # 2) market sells at open
            for od in orders:
                if od.kind == "market_sell":
                    ln = self.lanes[od.lane]
                    t = next((x for x in ln.tranches if x.id == od.tranche_id), None)
                    if t is not None:
                        self._close_tranche(ln, t, O - slip, O, i, od.tag or "market_sell")
            # 3) market buys at open
            for od in orders:
                if od.kind == "market_buy":
                    ln = self.lanes[od.lane]
                    if od.qty > ln.free or self.total_qty() + od.qty > self.max_total:
                        self.cancelled_capacity += 1
                        continue
                    self._open_tranche(ln, od.qty, O + slip, O, i, True, od.tp_pts, od.tag)
            # 4) limit buys: gap-through at open, else intrabar
            for od in orders:
                if od.kind != "limit_buy":
                    continue
                ln = self.lanes[od.lane]
                if od.qty > ln.free or self.total_qty() + od.qty > self.max_total:
                    self.cancelled_capacity += 1
                    continue
                Lp = od.price
                if O <= Lp - tick:
                    px = min(Lp, O + slip)
                    self._open_tranche(ln, od.qty, px, O, i, True, od.tp_pts, od.tag)
                elif L <= Lp - pen:
                    t = self._open_tranche(ln, od.qty, Lp, Lp, i, False, od.tp_pts, od.tag)
                    intrabar_lanes.add(od.lane)
                    intrabar_tids.add(t.id)
            # 5) intrabar exits
            for ln in self.lanes.values():
                if not ln.tranches:
                    continue
                mode = ln.spec.exit_mode
                if mode == "individual":
                    for t in list(ln.tranches):
                        if t.id in intrabar_tids and not cfg.allow_same_bar_tp_after_intrabar_buy:
                            continue
                        if H >= t.tp_px + pen:
                            self._close_tranche(ln, t, t.tp_px, t.tp_px, i, "tp")
                elif mode == "basket":
                    T = ln.basket_target()
                    if H >= T + pen:
                        if ln.spec.name in intrabar_lanes and not cfg.allow_same_bar_tp_after_intrabar_buy:
                            self.ambiguous_bars += 1
                            continue
                        for t in list(ln.tranches):
                            self._close_tranche(ln, t, T, T, i, "basket_tp")
            # 6) cycle MTM stats
            q = self.total_qty()
            if q:
                sm = sum(t.entry_px * t.qty for ln in self.lanes.values() for t in ln.tranches)
                u_c = (b.c[i] * q - sm) * cfg.point_value
                u_l = (L * q - sm) * cfg.point_value
                cs = self._cycle_stats
                if u_c < cs["worst_mtm"]:
                    cs["worst_mtm"] = u_c
                if u_l < cs["worst_mtm_low"]:
                    cs["worst_mtm_low"] = u_l
            else:
                sm = 0.0
            snap_idx.append(i)
            snap_qty.append(q)
            snap_sum.append(sm)
            snap_real.append(self.realized_net)
            for lnm in lane_names:
                snap_lane[lnm].append(self.lanes[lnm].qty)
            # 7) strategy decision for next bar
            self.s.observe(ctx, i)
            j = i + 1
            if j < n and b.tradeable[j] and b.day[j] == b.day[i]:
                pending = self.s.on_bar_close(ctx, i) or []
                pending_for = j
                self._validate(pending)

        self._finalize(snap_idx, snap_qty, snap_sum, snap_real, snap_lane)
        return self

    def _exits_at_open(self, i, O, pen):
        tick = TICK
        slip = self.cfg.slippage_ticks * tick
        for ln in self.lanes.values():
            if not ln.tranches:
                continue
            if ln.spec.exit_mode == "individual":
                for t in list(ln.tranches):
                    if O >= t.tp_px + tick:
                        self._close_tranche(ln, t, max(t.tp_px, O - slip), O, i, "tp_gap")
            elif ln.spec.exit_mode == "basket":
                T = ln.basket_target()
                if O >= T + tick:
                    px = max(T, O - slip)
                    for t in list(ln.tranches):
                        self._close_tranche(ln, t, px, O, i, "basket_tp_gap")

    def _validate(self, orders):
        buy_q = {}
        for od in orders:
            if od.kind in ("market_buy", "limit_buy"):
                assert od.qty > 0
                if od.kind == "limit_buy":
                    assert od.price is not None and abs(od.price / TICK - round(od.price / TICK)) < 1e-9, "limit off tick"
                buy_q[od.lane] = buy_q.get(od.lane, 0) + od.qty
        tot = 0
        for lnm, q in buy_q.items():
            assert q <= self.lanes[lnm].free, f"orders exceed free capacity in lane {lnm}"
            tot += q
        assert self.total_qty() + tot <= self.max_total, "orders exceed max_total"

    # ------------------------------------------------------------------ outputs
    def _finalize(self, snap_idx, snap_qty, snap_sum, snap_real, snap_lane):
        b = self.bars
        n = len(b)
        cfg = self.cfg
        idx = np.asarray(snap_idx, dtype=np.int64)

        def ffill(vals, init=0.0):
            arr = np.full(n, np.nan)
            arr[idx] = vals
            s = pd.Series(arr).ffill().fillna(init)
            return s.values

        qty = ffill(snap_qty).astype(np.int64)
        sm = ffill(snap_sum)
        real = ffill(snap_real)
        # roll costs recorded at roll bar; snapshot realized already includes them from next tradeable bar,
        # so shift the cost to the actual roll bar for the MTM curve.
        roll_adj = np.zeros(n)
        for ridx, cost in self.roll_events:
            nxt = idx[np.searchsorted(idx, ridx)] if np.searchsorted(idx, ridx) < len(idx) else n
            roll_adj[ridx:nxt] -= cost
        real = real + roll_adj
        pv = cfg.point_value
        unreal = (qty * b.c - sm) * pv
        unreal_low = (qty * b.l - sm) * pv
        equity = cfg.initial_capital + real + unreal
        self.state = pd.DataFrame({
            "dt": b.dt, "qty": qty, "sum_px": sm, "realized_net": real, "unrealized": unreal,
            "unrealized_low": unreal_low, "equity": equity, "equity_low": cfg.initial_capital + real + unreal_low,
            "c": b.c, "raw_c": b.c - b.adj, "tradeable": b.tradeable,
        })
        for lnm, vals in snap_lane.items():
            self.state[f"qty_{lnm}"] = ffill(vals).astype(np.int64)
        self.trades_df = pd.DataFrame(self.trades)
        self.fills_df = pd.DataFrame(self.fills)
        self.cycles_df = pd.DataFrame(self.cycles)
        self.lane_cycles_df = pd.DataFrame(self.lane_cycles)
        # open inventory at end
        last = n - 1
        open_rows = []
        for ln in self.lanes.values():
            for t in ln.tranches:
                open_rows.append(dict(tranche=t.id, lane=t.lane, qty=t.qty, entry_dt=t.entry_dt, entry_px=t.entry_px,
                                      mark=b.c[last], unrealized=(b.c[last] - t.entry_px) * t.qty * pv,
                                      cycle=t.cycle_id))
        self.open_df = pd.DataFrame(open_rows)
        if self.total_qty() and self.cycle_start_idx is not None:
            self.open_cycle = dict(cycle=self.cycle_id, start_idx=self.cycle_start_idx,
                                   start_dt=b.dt[self.cycle_start_idx], **self._cycle_stats)
        else:
            self.open_cycle = None
        self.meta = dict(engine_version=ENGINE_VERSION, exec_spec=cfg.spec_version,
                         ambiguous_bars=self.ambiguous_bars, cancelled_capacity=self.cancelled_capacity)
