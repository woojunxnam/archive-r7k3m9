"""Strategies. Each decides only from bars[..i] and engine state at close of bar i."""
from __future__ import annotations

from .engine import LaneSpec, Order, Strategy


class ScriptedStrategy(Strategy):
    """Test helper: emits pre-scripted orders keyed by bar index."""

    def __init__(self, lanes, script, max_total=32):
        self.lanes = lanes
        self.max_total = max_total
        self.script = script  # {bar_index: [Order, ...]} or callable(ctx, i) -> orders

    def on_bar_close(self, ctx, i):
        if callable(self.script):
            return self.script(ctx, i)
        return list(self.script.get(i, []))


class BasketGrid(Strategy):
    """Baseline A: single core lane, immediate entry when flat, static grid add, basket TP.

    - flat -> market buy 1 at next open
    - holding and close <= last_fill - grid_pts and room -> market buy 1 at next open (max 1 add/bar)
    - exit: basket limit at avg + basket_tp_pts (engine, lane exit_mode='basket')
    """

    def __init__(self, max_qty=32, grid_pts=5.0, basket_tp_pts=25.0):
        self.max_total = max_qty
        self.grid = grid_pts
        self.lanes = [LaneSpec("core", max_qty, "basket", basket_tp_pts)]
        self.params = dict(strategy="BasketGrid", max_qty=max_qty, grid_pts=grid_pts, basket_tp_pts=basket_tp_pts)

    def on_bar_close(self, ctx, i):
        core = ctx.lane("core")
        if core.qty == 0:
            return [Order("market_buy", "core", 1, tag="init")]
        if core.free > 0 and ctx.bars.c[i] <= core.last_entry_px - self.grid:
            return [Order("market_buy", "core", 1, tag="add")]
        return []


class CoreRecycle(Strategy):
    """Core lane (Baseline-A logic, capacity core_cap) + Recycle lane (individual TP, capacity rec_cap).

    Recycle model R1 (profit-only):
      - active when `activation`=="always", or only while core is full ("core_full").
      - lane empty: buy (market, next open) when close <= running_high - rec_step, where running_high
        is the highest window-bar close since the lane became empty / was activated.
      - lane holding: add when close <= lowest open recycle entry - rec_step.
      - exit: individual limit TP at fill + rec_tp (engine). No loss realization.
      - rec_tp may be a callable(total_qty_after_fill) -> pts (model R4, inventory-aware TP).
    """

    def __init__(self, core_cap=24, rec_cap=8, core_grid=5.0, basket_tp=25.0, rec_step=5.0, rec_tp=3.0,
                 activation="always", max_total=32):
        assert core_cap + rec_cap <= max_total
        self.max_total = max_total
        self.core_grid, self.rec_step, self.rec_tp, self.activation = core_grid, rec_step, rec_tp, activation
        self.lanes = [LaneSpec("core", core_cap, "basket", basket_tp)]
        if rec_cap > 0:
            self.lanes.append(LaneSpec("rec", rec_cap, "individual", rec_tp if not callable(rec_tp) else 0.0))
        self.rec_cap = rec_cap
        self.params = dict(strategy="CoreRecycle", model="R1", core_cap=core_cap, rec_cap=rec_cap, core_grid=core_grid,
                           basket_tp=basket_tp, rec_step=rec_step,
                           rec_tp=rec_tp if not callable(rec_tp) else getattr(rec_tp, "label", "callable"),
                           activation=activation)
        self._hi = None

    def _active(self, ctx):
        if self.activation == "always":
            return True
        return ctx.lane("core").free == 0

    def observe(self, ctx, i):
        if self.rec_cap == 0:
            return
        rec = ctx.lane("rec")
        c = ctx.bars.c[i]
        if rec.qty == 0 and self._active(ctx):
            self._hi = c if self._hi is None else max(self._hi, c)
        else:
            self._hi = None

    def _tp_for_next(self, ctx):
        if callable(self.rec_tp):
            return float(self.rec_tp(ctx.total_qty + 1))
        return None

    def on_bar_close(self, ctx, i):
        out = []
        c = ctx.bars.c[i]
        core = ctx.lane("core")
        if core.qty == 0:
            out.append(Order("market_buy", "core", 1, tag="init"))
        elif core.free > 0 and c <= core.last_entry_px - self.core_grid:
            out.append(Order("market_buy", "core", 1, tag="add"))
        if self.rec_cap:
            rec = ctx.lane("rec")
            if rec.free > 0 and self._active(ctx):
                if rec.qty > 0:
                    ref = min(t.entry_px for t in rec.tranches)
                    if c <= ref - self.rec_step:
                        out.append(Order("market_buy", "rec", 1, tp_pts=self._tp_for_next(ctx), tag="rec_add"))
                elif self._hi is not None and c <= self._hi - self.rec_step:
                    out.append(Order("market_buy", "rec", 1, tp_pts=self._tp_for_next(ctx), tag="rec_init"))
        # never exceed total capacity
        free_total = ctx.max_total - ctx.total_qty
        return out[:max(free_total, 0)]
