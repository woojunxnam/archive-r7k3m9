"""Deterministic event-driven 1m backtester for long-only multi-lane MES inventory.

Execution rules follow EXECUTION_SPEC.md (EXEC-1.1). Key points:
- strategy decides on completed bar t; orders live only on bar t+1 (same trading day);
- market orders fill at open +slippage; limit orders need 1-tick penetration;
- a tranche bought by an intrabar limit cannot exit on the same bar;
- a lane with an intrabar limit buy does not evaluate its basket TP on that bar.

Roll accounting (ROLL-1.0, EXECUTION_SPEC §8): prices are the canonical forward-additive adjusted
series. Every tranche also carries a raw per-contract ledger. At each contract change the tranche keeps
its logical id; its raw basis is either shifted by the calendar spread ("basis_adjust") or the old leg is
closed at the old contract's last price and reopened in the new contract at old+spread ("close_reopen").
Both are economically identical to adjusted-price P&L; only the realized/unrealized split differs.
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
    slippage_ticks: float = 1
    penetration_ticks: float = 1
    allow_same_bar_tp_after_intrabar_buy: bool = False
    # roll: per contract = roll_commission_sides * commission + roll_slippage_ticks * tick * pv
    roll_commission_sides: int = 2
    roll_slippage_ticks: float = 1.0
    roll_cost_per_contract: Optional[float] = None   # explicit override (e.g. 0 for TV-like)
    roll_mode: str = "basis_adjust"                   # "basis_adjust" | "close_reopen" (reporting split only)
    initial_capital: float = 150_000.0
    spec_version: str = EXEC_SPEC_VERSION

    def roll_cost(self) -> float:
        if self.roll_cost_per_contract is not None:
            return self.roll_cost_per_contract
        return self.roll_commission_sides * self.commission_per_side + self.roll_slippage_ticks * TICK * self.point_value


@dataclass
class LaneSpec:
    name: str
    capacity: int
    exit_mode: str = "basket"          # "basket" | "individual" | "none" (strategy-managed)
    tp_pts: float = 25.0


@dataclass
class Order:
    kind: str                           # "market_buy" | "limit_buy" | "market_sell" | "limit_sell"
    lane: str
    qty: int = 1
    price: Optional[float] = None       # limit price
    tp_pts: Optional[float] = None      # per-tranche TP override (individual mode)
    tranche_id: Optional[int] = None    # for sells
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
    raw_basis: float = 0.0              # cost basis in the CURRENT contract's raw price
    contract: int = 0
    rolls: int = 0
    roll_realized: float = 0.0          # close_reopen: realized leg P&L booked at rolls (price only)


class LaneState:
    def __init__(self, spec: LaneSpec):
        self.spec = spec
        self.tranches: list[Tranche] = []
        self.last_entry_px: Optional[float] = None
        self.last_exit_px: Optional[float] = None
        self.cycle_id = 0
        self.cycle_start_idx: Optional[int] = None
        self._qty = 0
        self._sum = 0.0

    def _add(self, t):
        self.tranches.append(t)
        self._qty += t.qty
        self._sum += t.entry_px * t.qty

    def _remove(self, t):
        self.tranches.remove(t)
        self._qty -= t.qty
        self._sum -= t.entry_px * t.qty
        if self._qty == 0:
            self._sum = 0.0

    @property
    def qty(self) -> int:
        return self._qty

    @property
    def avg(self) -> Optional[float]:
        return None if self._qty == 0 else self._sum / self._qty

    @property
    def free(self) -> int:
        return self.spec.capacity - self._qty

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

    @property
    def cycle_start_idx(self):
        return self._e.cycle_start_idx if self._e.total_qty() else None

    def sum_px(self) -> float:
        return sum(ln._sum for ln in self._e.lanes.values())

    def unrealized(self, i) -> float:
        return (self.bars.c[i] * self.total_qty - self.sum_px()) * self._e.cfg.point_value

    def equity(self, i) -> float:
        return self._e.cfg.initial_capital + self._e.realized_net + self.unrealized(i)

    @property
    def peak_equity(self) -> float:
        return self._e.peak_equity


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
        for sp in strategy.lanes:
            assert sp.capacity <= self.max_total, "lane capacity exceeds max_total"
        self._total = 0
        self.next_tid = 1
        self.cycle_id = 0
        self.cycle_start_idx = None
        self.realized_net = 0.0
        self.realized_gross = 0.0
        self.commission = 0.0
        self.slippage = 0.0
        self.roll_cost = 0.0
        self.roll_commission = 0.0
        self.roll_slippage = 0.0
        self.trades: list[dict] = []
        self.fills: list[dict] = []
        self.cycles: list[dict] = []
        self.lane_cycles: list[dict] = []
        self.roll_events: list[tuple[int, float]] = []
        self.roll_ledger: list[dict] = []
        self.ambiguous_bars = 0
        self.bar_fills: list[dict] = []
        self.cancelled_capacity = 0
        self.peak_equity = self.cfg.initial_capital
        self.max_ledger_error = 0.0

    # ------------------------------------------------------------------ helpers
    def total_qty(self) -> int:
        return self._total

    def _commission(self, qty):
        c = qty * self.cfg.commission_per_side
        self.commission += c
        return c

    def _open_tranche(self, lane: LaneState, qty, px, ideal, i, at_open, tp_pts, tag):
        b = self.bars
        if self._total == 0:
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
                    self.cycle_id, lane.cycle_id, raw_basis=px - b.adj[i], contract=int(b.contract[i]))
        self.next_tid += 1
        lane._add(t)
        self._total += qty
        lane.last_entry_px = px
        c = self._commission(qty)
        self.realized_net -= c
        self.slippage += (px - ideal) * qty * self.cfg.point_value
        self._cycle_stats["entries"] += 1
        self._cycle_stats["max_qty"] = max(self._cycle_stats["max_qty"], self._total)
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
        lane._remove(t)
        self._total -= t.qty
        c = self._commission(t.qty)
        pnl_px = (px - t.entry_px) * t.qty * pv
        gross = (ideal - t.entry_ideal) * t.qty * pv
        self.realized_net += pnl_px - c
        self.realized_gross += gross
        self.slippage += (ideal - px) * t.qty * pv
        lane.last_exit_px = px
        # roll-ledger invariant: raw exit leg + booked roll legs == adjusted-price P&L
        assert int(b.contract[i]) == t.contract, "tranche contract out of sync with bar contract"
        raw_leg = (px - b.adj[i] - t.raw_basis) * t.qty * pv
        err = abs(raw_leg + t.roll_realized - pnl_px)
        self.max_ledger_error = max(self.max_ledger_error, err)
        net = pnl_px - c - t.qty * self.cfg.commission_per_side  # include entry commission in trade net
        self.trades.append(dict(tranche=t.id, lane=t.lane, qty=t.qty, entry_idx=t.entry_idx, exit_idx=i,
                                entry_dt=t.entry_dt, exit_dt=b.dt[i], entry_px=t.entry_px, exit_px=px,
                                gross=gross, net=net, reason=reason, tag=t.tag, cycle=t.cycle_id,
                                lane_cycle=t.lane_cycle_id, rolls=t.rolls, raw_exit=px - b.adj[i],
                                raw_basis_final=t.raw_basis, roll_realized=t.roll_realized))
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
        if self._total == 0:
            self.cycles.append(dict(cycle=self.cycle_id, start_idx=self.cycle_start_idx, end_idx=i,
                                    start_dt=b.dt[self.cycle_start_idx], end_dt=b.dt[i], **self._cycle_stats))

    def _roll(self, r):
        """Contract change at bar r (first bar of new contract). Old contract last bar = r-1."""
        b = self.bars
        cfg = self.cfg
        pv = cfg.point_value
        q = self._total
        if not q:
            return
        old_c, new_c = int(b.contract[r - 1]), int(b.contract[r])
        old_exit_raw = b.c[r - 1] - b.adj[r - 1]
        spread = b.adj[r - 1] - b.adj[r]          # new-contract raw price minus old at roll
        new_entry_raw = old_exit_raw + spread
        cost_pc = cfg.roll_cost()
        com_pc = cfg.roll_commission_sides * cfg.commission_per_side
        for ln in self.lanes.values():
            for t in ln.tranches:
                assert t.contract == old_c, "tranche not in rolling contract"
                leg = (old_exit_raw - t.raw_basis) * t.qty * pv
                old_basis = t.raw_basis
                if cfg.roll_mode == "close_reopen":
                    t.roll_realized += leg
                    t.raw_basis = new_entry_raw
                else:
                    t.raw_basis += spread
                t.contract = new_c
                t.rolls += 1
                self.roll_ledger.append(dict(roll_idx=r, dt=b.dt[r], tranche=t.id, lane=t.lane, qty=t.qty,
                                             old_contract=b.contract_names[old_c], new_contract=b.contract_names[new_c],
                                             old_exit_raw=old_exit_raw, spread=spread, old_basis_raw=old_basis, new_basis_raw=t.raw_basis,
                                             leg_pnl=leg, cost=cost_pc * t.qty))
        cost = q * cost_pc
        self.roll_cost += cost
        self.roll_commission += q * com_pc
        self.roll_slippage += cost - q * com_pc
        self.realized_net -= cost
        self.roll_events.append((int(r), cost))

    def _validate(self, orders):
        buy_q, sell_q = {}, {}
        for od in orders:
            if od.kind in ("market_buy", "limit_buy"):
                assert od.qty > 0
                if od.kind == "limit_buy":
                    assert od.price is not None and abs(od.price / TICK - round(od.price / TICK)) < 1e-9, "limit off tick"
                buy_q[od.lane] = buy_q.get(od.lane, 0) + od.qty
            elif od.kind == "market_sell":
                sell_q[od.lane] = sell_q.get(od.lane, 0) + 1
            elif od.kind == "limit_sell":
                assert od.price is not None and abs(od.price / TICK - round(od.price / TICK)) < 1e-9, "limit off tick"
        tot = 0
        for lnm, q in buy_q.items():
            # market sells at the same open release capacity first (rolling replacement)
            assert q <= self.lanes[lnm].free + sell_q.get(lnm, 0), f"orders exceed free capacity in lane {lnm}"
            tot += q
        assert self._total + tot - sum(sell_q.values()) <= self.max_total, "orders exceed max_total"

    # ------------------------------------------------------------------ main loop
    def run(self):
        b = self.bars
        cfg = self.cfg
        tick = TICK
        slip = cfg.slippage_ticks * tick
        pen = cfg.penetration_ticks * tick
        pv = cfg.point_value
        n = len(b)
        ctx = Context(self)
        self.s.on_start(ctx)

        trade_idx = np.flatnonzero(b.tradeable)
        lane_names = list(self.lanes)
        snap_idx, snap_qty, snap_sum, snap_real, snap_raw, snap_rollreal = [], [], [], [], [], []
        snap_lane = {ln: [] for ln in lane_names}
        roll_idx = np.flatnonzero(np.diff(b.contract) != 0) + 1
        rp = 0
        pending: list[Order] = []
        pending_for = -1
        c_arr, h_arr, l_arr, o_arr = b.c, b.h, b.l, b.o

        for i in trade_idx:
            while rp < len(roll_idx) and roll_idx[rp] <= i:
                self._roll(int(roll_idx[rp]))
                rp += 1
            self.bar_fills = []
            orders = pending if pending_for == i else []
            pending = []
            O, H, L = o_arr[i], h_arr[i], l_arr[i]
            intrabar_lanes = set()
            intrabar_tids = set()

            # 1) existing lane TP orders: gap-through at open
            self._exits_at_open(i, O, pen)
            # 1b) strategy limit sells gap-through at open
            for od in orders:
                if od.kind == "limit_sell":
                    ln = self.lanes[od.lane]
                    t = self._find(ln, od.tranche_id)
                    if t is not None and O >= od.price + tick:
                        self._close_tranche(ln, t, max(od.price, O - slip), O, i, (od.tag or "lsell") + "_gap")
            # 2) market sells at open
            for od in orders:
                if od.kind == "market_sell":
                    ln = self.lanes[od.lane]
                    t = self._find(ln, od.tranche_id)
                    if t is not None:
                        self._close_tranche(ln, t, O - slip, O, i, od.tag or "market_sell")
            # 3) market buys at open
            for od in orders:
                if od.kind == "market_buy":
                    ln = self.lanes[od.lane]
                    if od.qty > ln.free or self._total + od.qty > self.max_total:
                        self.cancelled_capacity += 1
                        continue
                    self._open_tranche(ln, od.qty, O + slip, O, i, True, od.tp_pts, od.tag)
            # 4) limit buys: gap-through at open, else intrabar
            for od in orders:
                if od.kind != "limit_buy":
                    continue
                ln = self.lanes[od.lane]
                if od.qty > ln.free or self._total + od.qty > self.max_total:
                    self.cancelled_capacity += 1
                    continue
                Lp = od.price
                if O <= Lp - tick:
                    self._open_tranche(ln, od.qty, min(Lp, O + slip), O, i, True, od.tp_pts, od.tag)
                elif L <= Lp - pen:
                    t = self._open_tranche(ln, od.qty, Lp, Lp, i, False, od.tp_pts, od.tag)
                    intrabar_lanes.add(od.lane)
                    intrabar_tids.add(t.id)
            # 5) intrabar exits: lane TPs
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
            # 5b) strategy limit sells intrabar (only pre-existing tranches can be targeted)
            for od in orders:
                if od.kind == "limit_sell":
                    ln = self.lanes[od.lane]
                    t = self._find(ln, od.tranche_id)
                    if t is not None and H >= od.price + pen:
                        self._close_tranche(ln, t, od.price, od.price, i, od.tag or "lsell")
            # 6) cycle MTM stats + snapshot
            q = self._total
            sm = 0.0
            rawsum = 0.0
            rollreal = 0.0
            if q:
                for ln in self.lanes.values():
                    sm += ln._sum
                    for t in ln.tranches:
                        rawsum += t.raw_basis * t.qty
                        rollreal += t.roll_realized
                u_c = (c_arr[i] * q - sm) * pv
                u_l = (L * q - sm) * pv
                cs = self._cycle_stats
                if u_c < cs["worst_mtm"]:
                    cs["worst_mtm"] = u_c
                if u_l < cs["worst_mtm_low"]:
                    cs["worst_mtm_low"] = u_l
                eq = cfg.initial_capital + self.realized_net + u_c
            else:
                eq = cfg.initial_capital + self.realized_net
            if eq > self.peak_equity:
                self.peak_equity = eq
            snap_idx.append(i)
            snap_qty.append(q)
            snap_sum.append(sm)
            snap_real.append(self.realized_net)
            snap_raw.append(rawsum)
            snap_rollreal.append(rollreal)
            for lnm in lane_names:
                snap_lane[lnm].append(self.lanes[lnm]._qty)
            # 7) strategy decision for next bar
            self.s.observe(ctx, i)
            j = i + 1
            if j < n and b.tradeable[j] and b.day[j] == b.day[i]:
                pending = self.s.on_bar_close(ctx, i) or []
                pending_for = j
                if pending:
                    self._validate(pending)
        # rolls after the last tradeable bar
        while rp < len(roll_idx):
            self._roll(int(roll_idx[rp]))
            rp += 1

        self._finalize(snap_idx, snap_qty, snap_sum, snap_real, snap_lane, snap_raw, snap_rollreal)
        return self

    @staticmethod
    def _find(ln, tid):
        for t in ln.tranches:
            if t.id == tid:
                return t
        return None

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

    # ------------------------------------------------------------------ outputs
    def _finalize(self, snap_idx, snap_qty, snap_sum, snap_real, snap_lane, snap_raw, snap_rollreal):
        b = self.bars
        n = len(b)
        cfg = self.cfg
        idx = np.asarray(snap_idx, dtype=np.int64)

        def ffill(vals, init=0.0):
            arr = np.full(n, np.nan)
            if len(idx):
                arr[idx] = vals
            return pd.Series(arr).ffill().fillna(init).values

        qty = ffill(snap_qty).astype(np.int64)
        sm = ffill(snap_sum)
        real = ffill(snap_real)
        rawsum = ffill(snap_raw)
        rollreal = ffill(snap_rollreal)
        # roll costs/ledger changes are booked at the next tradeable bar in the loop; move them to the roll bar
        roll_adj = np.zeros(n)
        raw_adj = np.zeros(n)
        rr_adj = np.zeros(n)
        led = pd.DataFrame(self.roll_ledger)
        for ridx, cost in self.roll_events:
            k = np.searchsorted(idx, ridx)
            nxt = idx[k] if k < len(idx) else n
            roll_adj[ridx:nxt] -= cost
            if len(led):
                g = led[led.roll_idx == ridx]
                raw_adj[ridx:nxt] += ((g.new_basis_raw - g.old_basis_raw) * g.qty).sum()
                if cfg.roll_mode == "close_reopen":
                    rr_adj[ridx:nxt] += g.leg_pnl.sum()
        real = real + roll_adj
        rawsum = rawsum + raw_adj
        rollreal = rollreal + rr_adj
        pv = cfg.point_value
        unreal = (qty * b.c - sm) * pv
        unreal_low = (qty * b.l - sm) * pv
        equity = cfg.initial_capital + real + unreal
        raw_c = b.c - b.adj
        self.state = pd.DataFrame({
            "dt": b.dt, "qty": qty, "sum_px": sm, "realized_net": real, "unrealized": unreal,
            "unrealized_low": unreal_low, "equity": equity, "equity_low": cfg.initial_capital + real + unreal_low,
            "c": b.c, "raw_c": raw_c, "tradeable": b.tradeable,
            "raw_basis_sum": rawsum,
            # broker view (close_reopen): realized includes roll legs of still-open tranches
            "realized_broker": real + rollreal, "unrealized_broker": unreal - rollreal,
        })
        for lnm, vals in snap_lane.items():
            self.state[f"qty_{lnm}"] = ffill(vals).astype(np.int64)
        self.trades_df = pd.DataFrame(self.trades)
        self.fills_df = pd.DataFrame(self.fills)
        self.cycles_df = pd.DataFrame(self.cycles)
        self.lane_cycles_df = pd.DataFrame(self.lane_cycles)
        self.roll_ledger_df = led
        last = n - 1
        open_rows = []
        for ln in self.lanes.values():
            for t in ln.tranches:
                open_rows.append(dict(tranche=t.id, lane=t.lane, qty=t.qty, entry_dt=t.entry_dt, entry_px=t.entry_px,
                                      mark=b.c[last], unrealized=(b.c[last] - t.entry_px) * t.qty * pv,
                                      cycle=t.cycle_id, contract=b.contract_names[t.contract], rolls=t.rolls,
                                      raw_basis=t.raw_basis, raw_mark=raw_c[last], roll_realized=t.roll_realized))
        self.open_df = pd.DataFrame(open_rows)
        if self._total and self.cycle_start_idx is not None:
            self.open_cycle = dict(cycle=self.cycle_id, start_idx=self.cycle_start_idx,
                                   start_dt=b.dt[self.cycle_start_idx], **self._cycle_stats)
        else:
            self.open_cycle = None
        self.meta = dict(engine_version=ENGINE_VERSION, exec_spec=cfg.spec_version,
                         ambiguous_bars=self.ambiguous_bars, cancelled_capacity=self.cancelled_capacity,
                         max_ledger_error=self.max_ledger_error, roll_mode=cfg.roll_mode)
