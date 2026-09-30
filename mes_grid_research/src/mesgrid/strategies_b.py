"""Engine reference implementation of the Sleeve B single-position momentum trade (used to validate fastsim.sim_single
fill-by-fill, and for full-accounting re-runs of finalists). Market entry at next open after a signal; individual TP
limit; close-based time / stop / trail exits as market orders at the next open; forced exit at the open of the last
tradeable bar of the day; cooldown in bars after an exit."""
import numpy as np

from .engine import LaneSpec, Order, Strategy


class MomentumStrategy(Strategy):
    def __init__(self, sig, nil, dtm, tp=np.inf, tmax=10**9, stop=np.inf, trail=np.inf, cooldown=0, size=1, lim_off=-1.0, ttl=1):
        self.sig, self.nil, self.dtm = sig, nil, dtm
        self.tp, self.tmax, self.stop, self.trail, self.cool, self.size = tp, tmax, stop, trail, cooldown, size
        self.lanes = [LaneSpec("mom", size, "individual" if np.isfinite(tp) else "none", tp if np.isfinite(tp) else 1e9)]
        self.max_total = size
        self._cool_until = -1
        self._maxc = -np.inf
        self._ei = None
        self.lim_off, self.ttl = lim_off, ttl
        self._lim = None      # (price, expiry bar)

    def observe(self, ctx, i):
        for f in ctx.fills_this_bar:
            if f["side"] == "SELL":
                self._cool_until = i + self.cool
                self._ei = None
            else:
                self._ei = i
                self._maxc = -np.inf
                self._lim = None

    def on_bar_close(self, ctx, i):
        ln = ctx.lane("mom")
        c = ctx.bars.c[i]
        if ln.qty:
            t = ln.tranches[0]
            self._maxc = max(self._maxc, c)
            held = self.dtm[i] - self.dtm[t.entry_idx] + 1
            if self.nil[i] or held >= self.tmax or c <= t.entry_px - self.stop or c <= self._maxc - self.trail:
                return [Order("market_sell", "mom", tranche_id=t.id, tag="x")]
            return []
        tpp = self.tp if np.isfinite(self.tp) else None
        if self._lim is not None and self._lim[1] >= i + 1 and not self.nil[i]:
            return [Order("limit_buy", "mom", self.size, price=self._lim[0], tp_pts=tpp, tag="mom_lmt")]
        self._lim = None
        if self.sig[i] and i >= self._cool_until and not self.nil[i]:
            if self.lim_off >= 0:
                from .engine import floor_tick
                self._lim = (floor_tick(c - self.lim_off), i + self.ttl)
                return [Order("limit_buy", "mom", self.size, price=self._lim[0], tp_pts=tpp, tag="mom_lmt")]
            return [Order("market_buy", "mom", self.size, tp_pts=tpp, tag="mom")]
        return []
