"""FactoryStrategy: one modular long-only inventory strategy whose DEFAULT config reproduces Baseline A.

Every research module is switched by config keys (see DEFAULTS). Decisions use only bars <= i and causal
features (features.py). Orders are for bar i+1 (engine enforces). Lanes:
  core  - averaging lane, basket escape (+ optional layer exits)
  rec   - recycle lane, individual TP (+ optional rolling replacement)
  emerg - emergency reserve lane, individual TP, usable only under an explicit condition
"""
from __future__ import annotations

import math

import numpy as np

from .engine import LaneSpec, Order, Strategy, ceil_tick, floor_tick

NS_DAY = 86400 * 10**9

DEFAULTS = dict(
    max_total=32,
    # ---- architecture
    core_cap=32, rec_cap=0, emerg_cap=0,
    dyn_alloc=None,            # None | "vol" | "dd" | "age": shrink effective core cap
    # ---- core exit
    basket_tp=25.0, basket_tp_mode="pts", basket_atr_k=0.4,   # "pts" | "datr"
    layer_exit=None,           # None|"last"|"last2"|"last4"|"all_ind"|"newest_prof"|"deepest_prof"|"partial"
    layer_x=5.0, layer_min_qty=1,
    scale_out=None,            # None | (x1, x2, x3) basket scale-out 25/25/50 at avg+x
    reclaim_exit=None,         # None | "vwap" | "prev_close": sell whole core at market when reclaimed & avg+min in profit
    reclaim_min=5.0,
    # ---- core add spacing
    spacing="fixed", grid=5.0,
    convex_a=0.1, tiers=((8, 5.0), (16, 10.0), (24, 20.0), (32, 40.0)),
    atr_k=1.0, pct=0.001, dd_D=25000.0, age_A=10.0, volpct_k=1.0,
    add_ref=None,              # None(auto) | "last_fill" | "lowest"
    # ---- core add trigger
    add_trigger="close",       # "close" | "limit" | "armed"
    reversal="bull_hc",        # for armed: bull_hc|prev_high|two_bar|ll_fail|wick|upper_q|rex
    cooldown_bars=1, cooldown_min=0,
    # ---- initial entry
    init="immediate",          # immediate|vwap|range|bb|keltner|sess_dd|prev_dd
    init_k=0.5, init_x=10.0, init_pct=0.2,
    # ---- recycle lane
    rec_activation="core_full",  # always|core_full|state
    rec_anchor="runhigh",        # runhigh|low30|low60|vwap|range|swing
    rec_spacing="ladder",        # ladder|float
    rec_step=5.0, rec_tp=3.0, rec_tp_mode="pts",   # pts|atr|inv|age|vol
    rec_tp_atr_k=0.3, rec_vwap_k=1.0,
    rec_roll=None,               # None | "pts" | "atr" | "newlow" | "reversal"
    rec_roll_x=20.0, rec_roll_select="highest",   # highest|oldest
    # ---- emergency lane
    emerg_step=20.0, emerg_tp=10.0, emerg_access="others_full",   # others_full|critical
    # ---- freefall governor
    gov=None, gov_x=None, gov_action="core",   # gov: atr_spike|atr_pct|vwap_dev|lower_lows|mom15|mom30|mom60|range_exp|rvol
    # ---- state machine / recovery
    state=None,                  # None | dict(t=(8,16,24), dd=None, age=None, mult=(1,1.5,3,inf), rec_tp=None,
                                 #   recovery_exit=None, rec_exit_x=5.0, recovery_until=12)
    recovery=None,               # None | dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=None, confirm="vwap")
    # ---- exposure caps (apply to all new buys)
    cap_total=None, eq_cap_Q=None, dd_cap_X=None, vol_cap=False, notional_L=None,
    # ---- time of day
    skip_first=0, lunch_core_off=False, core_cutoff=None, late_rec_tp=None,
    # ---- ETH context (labelled)
    eth=None,                    # None | "gapdown_init" | "openloc_init" | "onret_pause" | "below_onlow_adds"
    eth_k=0.5,
    # ---- RUN-3 modules (all OFF by default)
    rec_entry_mode="market",     # market | limit_close (resting limit at signal-bar close, 1 bar)
    rec_exit="tp",               # tp | last | last2   (last/last2: LIFO layer exit on recycle lane)
    rec_exit_x=3.0,
    harvest=None,                # None | rec_prof | all_prof | partial_high
    harvest_x=3.0,
    acct_dd=None,                # None | dict(thr=$, mode=all|core|core_harvest|progressive, resume=0.8)
    rec_filter=None,             # None | name of boolean feature array in F (smart recycle entry)
    rec_cooldown_bars=0,         # bars after a recycle exit before a new recycle entry
    core_filter=None,            # None | name of boolean feature array in F (core entry/add gate)
    # ---- RUN-4 Sleeve A modules (all OFF by default; defaults reproduce RUN-3 exactly)
    shadow=False,                # record recycle signals blocked by full slots/budget (no behaviour change)
    rec_anchor_feat=None,        # rec_anchor="feat": boolean array name in F (NULL-C random timing)
    dead_days=5.0,               # recycle tranche age (calendar days) at which it counts as DEAD
    dead_dist_datr=None,         # optional: also DEAD if entry - close >= x * daily ATR
    harvest_cond=None,           # None | dict(trig=free|dead|inv|always, k=, x=, q=, policy=, hx=, be=, core=False)
    salvage=None,                # None | dict(trig=free|always, k=0, rebound=pts|atr|pivot|mid30|vwap|rollhigh, rb=,
                                 #             select=oldest|highest|closest_be, max_per_day=1)
    cap_sm=None,                 # None | dict(min_free=K, deep_mult=None, deep_off=None, ttl=30, harvest=None, hx=1.0,
                                 #             harvest_at=1, salvage=None|dict, salvage_at=0)
    rec_soft=None,               # None | dict(feat=, cuts=(..), offs=(..), unit=pts|atr, skip_top=False, ttl=30)
    core_mode="grid",            # grid (default) | static: buy core_cap contracts at the first bars, never sell (rolled)
)


def _reversal(kind, F, b, i):
    o, h, l, c = b.o[i], b.h[i], b.l[i], b.c[i]
    if kind == "bull_hc":
        return c > o and c > F["prev_c"][i]
    if kind == "prev_high":
        return c > F["prev_high"][i]
    if kind == "two_bar":
        return F["prev_c"][i] < F["prev_open"][i] and c > o and c > F["prev_open"][i]
    if kind == "ll_fail":
        return F["prev_low"][i] < F["prev_low2"][i] and l >= F["prev_low"][i] and c > F["prev_c"][i]
    if kind == "wick":
        rng = h - l
        return rng > 0 and (min(o, c) - l) >= 0.5 * rng and c >= o
    if kind == "upper_q":
        rng = h - l
        return rng > 0 and c >= l + 0.75 * rng
    if kind == "rex":
        return F["range1"][i - 1] > 2 * F["range1_avg20"][i - 1] and F["range1"][i] < F["range1"][i - 1] and c > o
    raise ValueError(kind)


class FactoryStrategy(Strategy):
    def __init__(self, F: dict, **cfg):
        unknown = set(cfg) - set(DEFAULTS)
        assert not unknown, f"unknown config keys {unknown}"
        self.cfg = dict(DEFAULTS, **cfg)
        k = self.cfg
        self.F = F
        self.max_total = k["max_total"]
        if k["core_mode"] == "static":
            self.lanes = [LaneSpec("core", min(k["core_cap"], self.max_total), "none", 1e9)]
        else:
            self.lanes = [LaneSpec("core", min(k["core_cap"], self.max_total), "basket", k["basket_tp"])]
        if k["rec_cap"]:
            self.lanes.append(LaneSpec("rec", k["rec_cap"], "individual" if k["rec_exit"] == "tp" else "none", k["rec_tp"]))
        if k["emerg_cap"]:
            self.lanes.append(LaneSpec("emerg", k["emerg_cap"], "individual", k["emerg_tp"]))
        self.params = {kk: v for kk, v in self.cfg.items() if DEFAULTS.get(kk) != v}
        self.params["strategy"] = "FactoryStrategy"
        self._hi = None
        self._armed = None
        self._last_core_add_i = -10**9
        self._last_core_add_dt = None
        self._scaled = 0
        self._state = "NORMAL"
        self._recovering = False
        self._day_eth_ok = None
        self._basket_tp_cur = k["basket_tp"]
        self._dd_paused = False
        self._last_rec_exit_i = -10**9
        self._pend = None            # pending (re-issued) deep recycle limit: dict(px, tp, exp, day)
        self.shadow_log = []         # (i, tp, n_dead, n_rec, n_free) for blocked recycle signals
        self._salv_day = None
        self._salv_n = 0
        self.n_salvage = 0
        self.n_cond_harvest = 0

    # ------------------------------------------------------------------ helpers
    def _age_days(self, ctx, i):
        s = ctx.cycle_start_idx
        if s is None:
            return 0.0
        return float((ctx.bars.dt[i] - ctx.bars.dt[s]).astype("int64")) / NS_DAY

    def _update_state(self, ctx, i):
        st = self.cfg["state"]
        q = ctx.total_qty
        if not st:
            return
        t1, t2, t3 = st.get("t", (8, 16, 24))
        crit = q >= t3
        if st.get("dd") is not None and ctx.unrealized(i) <= -st["dd"]:
            crit = True
        if st.get("age") is not None and self._age_days(ctx, i) >= st["age"] and q >= t1:
            crit = True
        if crit:
            self._state = "CRITICAL"
            if st.get("recovery_exit") is not None:
                self._recovering = True
            return
        if self._recovering and q >= st.get("recovery_until", 12):
            self._state = "RECOVERY"
            return
        self._recovering = False
        self._state = "NORMAL" if q < t1 else ("ELEVATED" if q < t2 else "HIGH")

    def _state_mult(self):
        st = self.cfg["state"]
        if not st:
            return 1.0
        m = st.get("mult", (1.0, 1.5, 3.0, math.inf))
        return {"NORMAL": m[0], "ELEVATED": m[1], "HIGH": m[2], "CRITICAL": m[3], "RECOVERY": m[3]}[self._state]

    def _in_recovery_mode(self, ctx, i):
        r = self.cfg["recovery"]
        if not r:
            return False
        if ctx.total_qty >= r.get("h", 24):
            self._rec_mode = True
        elif ctx.total_qty < r.get("exit", 12):
            self._rec_mode = False
        return getattr(self, "_rec_mode", False)

    def _core_step(self, ctx, i, n):
        """spacing for the next core add when core holds n contracts"""
        k, F = self.cfg, self.F
        sp = k["spacing"]
        if sp == "fixed":
            s = k["grid"]
        elif sp == "convex":
            s = k["grid"] * (1 + k["convex_a"] * max(n - 1, 0))
        elif sp == "tiers":
            s = math.inf
            for upto, step in k["tiers"]:
                if n < upto:
                    s = step
                    break
        elif sp == "atr":
            s = k["atr_k"] * F["atr15"][i]
        elif sp == "pct":
            s = k["pct"] * (ctx.bars.c[i] - ctx.bars.adj[i])       # raw price level
        elif sp == "dd":
            s = k["grid"] * (1 + max(-ctx.unrealized(i), 0) / k["dd_D"])
        elif sp == "age":
            s = k["grid"] * (1 + self._age_days(ctx, i) / k["age_A"])
        elif sp == "volpct":
            s = k["grid"] * (1 + k["volpct_k"] * 2 * max(F["datr_pct"][i] - 0.5, 0) * 2)
        else:
            raise ValueError(sp)
        return max(s * self._state_mult(), 0.25)

    def _core_cap_eff(self, ctx, i):
        k = self.cfg
        cap = self.lanes[0].capacity
        d = k["dyn_alloc"]
        if d == "vol":
            cap = min(cap, 20 if self.F["datr_pct"][i] > 0.8 else cap)
        elif d == "dd":
            u = -ctx.unrealized(i)
            cap = min(cap, cap - int(u // 25000) * 4) if u > 0 else cap
        elif d == "age":
            a = self._age_days(ctx, i)
            cap = min(cap, cap - int(a // 10) * 4)
        return max(cap, 0)

    def _total_cap_eff(self, ctx, i):
        k, F, b = self.cfg, self.F, ctx.bars
        cap = self.max_total
        if k["cap_total"]:
            cap = min(cap, k["cap_total"])
        eq = None
        if k["eq_cap_Q"]:
            eq = ctx.equity(i)
            cap = min(cap, max(int(eq // k["eq_cap_Q"]), 0))
        if k["dd_cap_X"]:
            eq = eq if eq is not None else ctx.equity(i)
            dd = max(ctx.peak_equity - eq, 0)
            cap = min(cap, self.max_total - int(dd // k["dd_cap_X"]) * 4)
        if k["vol_cap"]:
            p = F["datr_pct"][i]
            cap = min(cap, 32 if p < 0.7 else (24 if p < 0.9 else 16))
        if k["notional_L"]:
            eq = eq if eq is not None else ctx.equity(i)
            raw = b.c[i] - b.adj[i]
            cap = min(cap, max(int(k["notional_L"] * max(eq, 0) / (raw * 5.0)), 0))
        return max(cap, 0)

    def _governed(self, i):
        k, F, b = self.cfg, self.F, None
        g = k["gov"]
        if not g:
            return False
        x = k["gov_x"]
        a15 = F["atr15"][i]
        if g == "atr_spike":
            return F["atr15_rel"][i] > (x or 1.5)
        if g == "atr_pct":
            return F["datr_pct"][i] > (x or 0.85)
        if g == "vwap_dev":
            return (self._c - F["vwap"][i]) / a15 < -(x or 2.0)
        if g == "lower_lows":
            return bool(F["lower_lows"][i])
        if g in ("mom15", "mom30", "mom60"):
            return F[g][i] / a15 < -(x or 1.5)
        if g == "range_exp":
            return F["range30"][i] / a15 > (x or 3.0)
        if g == "rvol":
            return F["rvol_ratio"][i] > (x or 2.0)
        raise ValueError(g)

    def _init_ok(self, ctx, i):
        k, F, c = self.cfg, self.F, self._c
        m = k["init"]
        a15 = F["atr15"][i]
        if k["eth"] == "gapdown_init" and not (F["gap"][i] < -k["eth_k"] * a15):
            return False
        if k["eth"] == "openloc_init" and not (F["eth_open_loc"][i] < 0.5):
            return False
        if m == "immediate":
            return True
        if m == "vwap":
            return c <= F["vwap"][i] - k["init_k"] * a15
        if m == "range":
            return F["rangepos120"][i] <= k["init_pct"]
        if m == "bb":
            return c <= F["bb_lower"][i]
        if m == "keltner":
            return c <= F["kelt_lower"][i]
        if m == "sess_dd":
            return c <= F["sess_high"][i] - k["init_x"]
        if m == "prev_dd":
            return c <= F["prev_close"][i] - k["init_x"]
        raise ValueError(m)

    def _rec_tp(self, ctx, i):
        k, F = self.cfg, self.F
        m = k["rec_tp_mode"]
        tp = k["rec_tp"]
        if m == "atr":
            tp = max(k["rec_tp_atr_k"] * F["atr15"][i], 1.0)
        elif m == "inv":
            q = ctx.total_qty + 1
            tp = 5.0 if q <= 8 else (4.0 if q <= 16 else (3.0 if q <= 24 else 2.5))
        elif m == "age":
            a = self._age_days(ctx, i)
            tp = k["rec_tp"] if a < 5 else (k["rec_tp"] * 0.75 if a < 20 else k["rec_tp"] * 0.5)
        elif m == "vol":
            tp = k["rec_tp"] * min(max(F["datr"][i] / 60.0, 0.5), 2.0)
        st = k["state"]
        if st and st.get("rec_tp") and self._state in st["rec_tp"]:
            tp = st["rec_tp"][self._state]
        r = k["recovery"]
        if r and getattr(self, "_rec_mode", False):
            tp = r.get("rec_tp", tp)
        if k["late_rec_tp"] is not None and ctx.bars.minute[i] >= 15 * 60:
            tp = k["late_rec_tp"]
        return max(ceil_tick(tp), 0.25)

    # ------------------------------------------------------------------ hooks
    def observe(self, ctx, i):
        k = self.cfg
        self._c = ctx.bars.c[i]
        for f in ctx.fills_this_bar:
            if f["side"] == "SELL" and f["lane"] == "rec":
                self._last_rec_exit_i = i
            elif f["side"] == "BUY" and f["tag"] == "rec_pend":
                self._pend = None
            tg = f.get("tag") or ""
            if tg.startswith("SO1"):
                self._scaled = max(self._scaled, 1)
            elif tg.startswith("SO2"):
                self._scaled = max(self._scaled, 2)
        self._update_state(ctx, i)
        if k["rec_cap"]:
            rec = ctx.lane("rec")
            if rec.qty == 0 and self._rec_active(ctx):
                self._hi = self._c if self._hi is None else max(self._hi, self._c)
            else:
                self._hi = None

    def _rec_active(self, ctx):
        a = self.cfg["rec_activation"]
        if a == "always":
            return True
        if a == "core_full":
            return ctx.lane("core").qty >= getattr(self, "_core_cap_now", self.lanes[0].capacity)
        if a == "state":
            return self._state != "NORMAL"
        raise ValueError(a)

    def on_bar_close(self, ctx, i):
        k, F, b = self.cfg, self.F, ctx.bars
        c = self._c = b.c[i]
        out = []
        core = ctx.lane("core")
        minute = b.minute[i]
        total_cap = self._total_cap_eff(ctx, i)
        buys_budget = total_cap - ctx.total_qty
        # time of day gating for new buys (decision at close of bar i -> fill at i+1 open = minute i)
        tod_ok = minute - 571 + 1 >= k["skip_first"]
        core_tod_ok = tod_ok
        if k["lunch_core_off"] and 11 * 60 + 30 <= minute < 13 * 60 + 30:
            core_tod_ok = False
        if k["core_cutoff"] is not None and minute >= k["core_cutoff"]:
            core_tod_ok = False
        governed = self._governed(i)
        in_rec_mode = self._in_recovery_mode(ctx, i)
        a15 = F["atr15"][i]

        self._core_cap_now = self._core_cap_eff(ctx, i)
        dd_mode = None
        if k["acct_dd"]:
            ad = k["acct_dd"]
            dd = max(ctx.peak_equity - ctx.equity(i), 0.0)
            if dd >= ad["thr"]:
                self._dd_paused = True
            elif dd < ad.get("resume", 0.8) * ad["thr"]:
                self._dd_paused = False
            if ad["mode"] == "progressive":
                self._core_cap_now = min(self._core_cap_now, int(self.lanes[0].capacity * max(0.0, 1 - dd / ad["thr"]) + 0.5)) if dd > 0 else self._core_cap_now
            elif self._dd_paused:
                dd_mode = ad["mode"]
        if dd_mode == "all":
            buys_budget = 0
        if k["basket_tp_mode"] == "datr":
            core.spec.tp_pts = max(ceil_tick(k["basket_atr_k"] * F["datr"][i]), 5.0)
        if k["core_mode"] == "static":
            # passive long core: fill to core_cap one contract per bar, never exit (roll-accounted by the engine)
            if core.qty < self.lanes[0].capacity and buys_budget > 0:
                out.append(Order("market_buy", "core", 1, tag="static"))
                buys_budget -= 1
            if k["rec_cap"] and buys_budget > 0 and tod_ok:
                out += self._rec_orders(ctx, i, a15, False)
            if k["shadow"] and k["rec_cap"] and tod_ok:
                rec_l = ctx.lane("rec")
                if (rec_l.free <= 0 or buys_budget <= 0) and self._rec_signal(ctx, i, a15, False):
                    nd = sum(1 for t in rec_l.tranches if self._is_dead(ctx, i, t))
                    self.shadow_log.append((i, self._rec_tp(ctx, i), nd, rec_l.qty, rec_l.free))
            if k["rec_cap"] and (k["harvest_cond"] or k["salvage"] or k["cap_sm"]):
                out = self._r4_exit_orders(ctx, i, out, a15) + out
            return self._fit(ctx, out, total_cap)
        # ================= CORE EXITS (strategy-managed, in addition to basket escape)
        if core.qty:
            out += self._core_exit_orders(ctx, i, core, in_rec_mode)
        out += self._harvest_orders(ctx, i, out, dd_mode)
        if k["rec_cap"] and (k["harvest_cond"] or k["salvage"] or k["cap_sm"]):
            out += self._r4_exit_orders(ctx, i, out, a15)

        # ================= CORE ENTRY / ADD
        core_allowed = core_tod_ok and buys_budget > 0 and not (governed and k["gov_action"] in ("core", "all"))
        if self._state == "CRITICAL" and self._state_mult() == math.inf:
            core_allowed = False
        if dd_mode in ("core", "core_harvest"):
            core_allowed = False
        if k["core_filter"] is not None and not bool(F[k["core_filter"]][i]):
            core_allowed = False
        if in_rec_mode:
            core_allowed = False
            conf = k["recovery"].get("confirm")
            if conf == "vwap" and c > F["vwap"][i]:
                core_allowed = core_tod_ok and buys_budget > 0
        if k["eth"] == "onret_pause" and F["eth_on_ret"][i] < -k["eth_k"] * F["datr"][i]:
            core_allowed = False
        if k["eth"] == "below_onlow_adds" and core.qty and not (c < F["eth_on_low"][i]):
            core_allowed = False
        sold_core = sum(1 for od in out if od.lane == "core" and od.kind == "market_sell")
        if core_allowed and core.qty == 0 and sold_core == 0:
            if self._init_ok(ctx, i):
                out.append(Order("market_buy", "core", 1, tag="init"))
                buys_budget -= 1
                self._scaled = 0
        elif core_allowed and core.qty > 0 and core.qty < self._core_cap_now and core.free > 0:
            ref_mode = k["add_ref"] or ("lowest" if k["layer_exit"] else "last_fill")
            ref = core.last_entry_px if ref_mode == "last_fill" else min(t.entry_px for t in core.tranches)
            step = self._core_step(ctx, i, core.qty)
            level = ref - step
            cool_ok = (i - self._last_core_add_i) >= k["cooldown_bars"]
            if k["cooldown_min"] and self._last_core_add_dt is not None:
                cool_ok = cool_ok and (b.dt[i] - self._last_core_add_dt) >= np.timedelta64(int(k["cooldown_min"]), "m")
            if cool_ok and math.isfinite(level):
                trig = k["add_trigger"]
                if trig == "close":
                    if c <= level:
                        out.append(Order("market_buy", "core", 1, tag="add")); buys_budget -= 1
                        self._mark_add(b, i)
                elif trig == "limit":
                    lv = floor_tick(level)
                    if c > lv:
                        out.append(Order("limit_buy", "core", 1, price=lv, tag="add_lmt")); buys_budget -= 1
                    else:
                        out.append(Order("market_buy", "core", 1, tag="add")); buys_budget -= 1
                    self._mark_add(b, i, soft=True)
                elif trig == "armed":
                    if b.l[i] <= level:
                        self._armed = level if self._armed is None else min(self._armed, level)
                    if self._armed is not None:
                        if c > self._armed + step:
                            self._armed = None
                        elif _reversal(k["reversal"], F, b, i):
                            out.append(Order("market_buy", "core", 1, tag="add_rev")); buys_budget -= 1
                            self._armed = None
                            self._mark_add(b, i)
        if core.qty == 0:
            self._armed = None

        # ================= RECYCLE
        if k["shadow"] and k["rec_cap"] and tod_ok and not (governed and k["gov_action"] == "all") and self._rec_active(ctx):
            rec_l = ctx.lane("rec")
            if (rec_l.free <= 0 or buys_budget <= 0) and self._rec_signal(ctx, i, a15, in_rec_mode):
                nd = sum(1 for t in rec_l.tranches if self._is_dead(ctx, i, t))
                self.shadow_log.append((i, self._rec_tp(ctx, i), nd, rec_l.qty, rec_l.free))
        if k["rec_cap"] and buys_budget > 0 and tod_ok and not (governed and k["gov_action"] == "all"):
            out += self._rec_orders(ctx, i, a15, in_rec_mode)
        elif k["rec_cap"] and k["rec_roll"]:
            out += self._rec_roll_orders(ctx, i, a15, in_rec_mode)   # rotations are inventory-neutral

        # ================= EMERGENCY
        if k["emerg_cap"] and tod_ok:
            out += self._emerg_orders(ctx, i)

        # final capacity guard
        return self._fit(ctx, out, total_cap)

    def _mark_add(self, b, i, soft=False):
        self._last_core_add_i = i
        self._last_core_add_dt = b.dt[i]

    def _fit(self, ctx, out, total_cap):
        sells = [o for o in out if o.kind in ("market_sell", "limit_sell")]
        buys = [o for o in out if o.kind in ("market_buy", "limit_buy")]
        msell = {}
        for o in sells:
            if o.kind == "market_sell":
                msell[o.lane] = msell.get(o.lane, 0) + 1
        keep = []
        tot = ctx.total_qty - sum(msell.values())
        lane_add = {}
        for o in buys:
            ln = ctx.lane(o.lane)
            la = lane_add.get(o.lane, 0)
            if la + o.qty > ln.free + msell.get(o.lane, 0):
                continue
            is_rot = o.tag == "rot_buy"
            if not is_rot and tot + o.qty > min(total_cap, ctx.max_total):
                continue
            if tot + o.qty > ctx.max_total:
                continue
            keep.append(o)
            tot += o.qty
            lane_add[o.lane] = la + o.qty
        return sells + keep

    def _core_exit_orders(self, ctx, i, core, in_rec_mode):
        k, F, b = self.cfg, self.F, ctx.bars
        c = b.c[i]
        out = []
        tr = sorted(core.tranches, key=lambda t: t.entry_idx)
        mode = k["layer_exit"]
        x = k["layer_x"]
        st = k["state"]
        if st and st.get("recovery_exit") is not None and self._state in ("RECOVERY", "CRITICAL"):
            mode, x = st["recovery_exit"], st.get("rec_exit_x", 5.0)
        r = k["recovery"]
        if r and in_rec_mode and r.get("layer_x"):
            mode, x = "all_ind", r["layer_x"]
        if mode and len(tr) >= k["layer_min_qty"]:
            if mode == "last":
                t = tr[-1]
                out.append(Order("limit_sell", "core", tranche_id=t.id, price=ceil_tick(t.entry_px + x), tag="L_last"))
            elif mode in ("last2", "last4"):
                m = 2 if mode == "last2" else 4
                grp = tr[-m:]
                px = ceil_tick(sum(t.entry_px for t in grp) / len(grp) + x)
                out += [Order("limit_sell", "core", tranche_id=t.id, price=px, tag=f"L_{mode}") for t in grp]
            elif mode == "all_ind":
                out += [Order("limit_sell", "core", tranche_id=t.id, price=ceil_tick(t.entry_px + x), tag="L_ind") for t in tr]
            elif mode in ("newest_prof", "deepest_prof", "partial"):
                prof = [t for t in tr if c - t.entry_px >= x]
                if prof:
                    if mode == "newest_prof":
                        sel = [prof[-1]]
                    elif mode == "deepest_prof":
                        sel = [min(prof, key=lambda t: t.entry_px)]
                    else:
                        sel = prof[: max(len(prof) // 2, 1)]
                    out += [Order("market_sell", "core", tranche_id=t.id, tag=f"L_{mode}") for t in sel]
        if k["scale_out"] and core.qty >= 4:
            avg = core.avg
            x1, x2, x3 = k["scale_out"]
            n = core.qty
            # 25% at +x1, next 25% at +x2 (the basket escape at +x3 handles the rest)
            if self._scaled == 0:
                grp = sorted(tr, key=lambda t: -t.entry_px)[: max(n // 4, 1)]
                out += [Order("limit_sell", "core", tranche_id=t.id, price=ceil_tick(avg + x1), tag="SO1") for t in grp]
            elif self._scaled == 1:
                grp = sorted(tr, key=lambda t: -t.entry_px)[: max(n // 3, 1)]
                out += [Order("limit_sell", "core", tranche_id=t.id, price=ceil_tick(avg + x2), tag="SO2") for t in grp]
        if k["reclaim_exit"] and core.avg is not None and c >= core.avg + k["reclaim_min"]:
            lvl = F["vwap"][i] if k["reclaim_exit"] == "vwap" else F["prev_close"][i]
            if np.isfinite(lvl) and c > lvl and F["prev_c"][i] <= lvl:
                out += [Order("market_sell", "core", tranche_id=t.id, tag="reclaim") for t in tr]
        # de-duplicate: one order per tranche (market beats limit)
        seen, ded = set(), []
        for o in sorted(out, key=lambda o: o.kind != "market_sell"):
            if o.tranche_id in seen:
                continue
            seen.add(o.tranche_id)
            ded.append(o)
        return ded

    def _rec_step_now(self, ctx, in_rec_mode):
        k = self.cfg
        step = k["rec_step"]
        r = k["recovery"]
        if r and in_rec_mode:
            step = r.get("rec_step", step)
        st = k["state"]
        if st and st.get("rec_step_mult"):
            step *= st["rec_step_mult"].get(self._state, 1.0)
        cs = k["cap_sm"]
        if cs and cs.get("deep_mult") and ctx.lane("rec").free < cs["min_free"]:
            step *= cs["deep_mult"]
        return step

    def _space_ok(self, ctx, px, step):
        opens = [t.entry_px for t in ctx.lane("rec").tranches]
        if not opens:
            return True, False
        if self.cfg["rec_spacing"] == "ladder":
            return px <= min(opens) - step, True
        return all(abs(px - e) >= step for e in opens), True

    def _rec_signal(self, ctx, i, a15, in_rec_mode):
        """True if a recycle entry would be placed at bar i given a free slot (spacing, filter, cooldown, anchor)."""
        k, F, b = self.cfg, self.F, ctx.bars
        space_ok, has_open = self._space_ok(ctx, b.c[i], self._rec_step_now(ctx, in_rec_mode))
        if k["rec_filter"] is not None and not bool(F[k["rec_filter"]][i]):
            space_ok = False
        if (i - self._last_rec_exit_i) <= k["rec_cooldown_bars"] and k["rec_cooldown_bars"] > 0:
            space_ok = False
        return bool(space_ok and self._rec_anchor_ok(ctx, i, a15, has_open))

    def _entry_offset(self, ctx, i, a15):
        """RUN-4 price improvement: 0 = normal entry, >0 = resting limit this many points below close, None = skip."""
        k, F = self.cfg, self.F
        off = 0.0
        cs = k["cap_sm"]
        if cs and cs.get("deep_off") and ctx.lane("rec").free < cs["min_free"]:
            off = max(off, float(cs["deep_off"]))
        rs = k["rec_soft"]
        if rs:
            sc = F[rs["feat"]][i]
            bin_ = 0 if not np.isfinite(sc) else int(np.searchsorted(np.asarray(rs["cuts"]), sc, side="right"))
            if rs.get("skip_top") and bin_ == len(rs["cuts"]):
                return None
            o = float(rs["offs"][bin_]) * (a15 if rs.get("unit", "pts") == "atr" else 1.0)
            off = max(off, o)
        return off

    def _rec_orders(self, ctx, i, a15, in_rec_mode):
        k, F, b = self.cfg, self.F, ctx.bars
        rec = ctx.lane("rec")
        c = b.c[i]
        out = []
        if not self._rec_active(ctx):
            return out
        if rec.free > 0:
            if self._pend is not None:
                p = self._pend
                if i > p["exp"] or b.day[i] != p["day"]:
                    self._pend = None
                else:
                    ok, _ = self._space_ok(ctx, p["px"], self._rec_step_now(ctx, in_rec_mode))
                    if ok:
                        out.append(Order("limit_buy", "rec", 1, price=p["px"], tp_pts=p["tp"], tag="rec_pend"))
                        return out
                    self._pend = None
            if self._rec_signal(ctx, i, a15, in_rec_mode):
                off = self._entry_offset(ctx, i, a15) if (k["cap_sm"] or k["rec_soft"]) else 0.0
                if off is None:
                    return out
                tp = self._rec_tp(ctx, i)
                if off > 0:
                    px = floor_tick(c - off)
                    ttl = (k["rec_soft"] or {}).get("ttl") or (k["cap_sm"] or {}).get("ttl", 30)
                    self._pend = dict(px=px, tp=tp, exp=i + int(ttl), day=b.day[i])
                    out.append(Order("limit_buy", "rec", 1, price=px, tp_pts=tp, tag="rec_pend"))
                elif k["rec_entry_mode"] == "limit_close":
                    out.append(Order("limit_buy", "rec", 1, price=floor_tick(c), tp_pts=tp, tag="rec_lmt"))
                else:
                    out.append(Order("market_buy", "rec", 1, tp_pts=tp, tag="rec"))
        elif k["rec_roll"]:
            out += self._rec_roll_orders(ctx, i, a15, in_rec_mode)
        return out

    # ------------------------------------------------------------------ RUN-4 capacity management
    def _is_dead(self, ctx, i, t):
        k = self.cfg
        b = ctx.bars
        if float((b.dt[i] - t.entry_dt).astype("int64")) / NS_DAY >= k["dead_days"]:
            return True
        x = k["dead_dist_datr"]
        return bool(x) and (t.entry_px - b.c[i]) >= x * self.F["datr"][i]

    def _harvest_select(self, ctx, i, policy, hx, be, include_core, taken):
        c = ctx.bars.c[i]
        lanes = ["rec"] + (["core"] if include_core else [])
        tr = [(n, t) for n in lanes for t in ctx.lane(n).tranches if t.id not in taken]
        if policy == "prof_be":
            return [(n, t) for n, t in tr if c - t.entry_px >= -be]
        prof = [(n, t) for n, t in tr if c - t.entry_px >= hx]
        if not prof:
            return []
        if policy == "newest_prof":
            return [max(prof, key=lambda nt: nt[1].entry_idx)]
        if policy == "most_prof":
            return [max(prof, key=lambda nt: c - nt[1].entry_px)]
        if policy == "all_prof":
            return prof
        if policy == "partial":
            srt = sorted(prof, key=lambda nt: -(c - nt[1].entry_px))
            return srt[: (len(srt) + 1) // 2]
        raise ValueError(policy)

    def _rebound_ok(self, sv, i, a15):
        F, b = self.F, self._bars
        c = b.c[i]
        lo = F["low60"][i]
        if not np.isfinite(lo):
            return False
        m = sv["rebound"]
        rb = sv.get("rb", 0.0)
        if m == "pts":
            return c - lo >= rb
        if m == "atr":
            return c - lo >= rb * a15
        if m == "pivot":
            return c > F["prev_high"][i] and F["prev_low"][i] <= lo + 0.25 and c - lo >= 0.5 * a15
        if m == "mid30":
            mid = 0.5 * (F["high30"][i] + F["low30"][i])
            return c > mid and F["prev_c"][i] <= mid and c - lo >= 0.5 * a15
        if m == "vwap":
            vw = F["vwap"][i]
            return c >= vw - 0.25 * a15 and lo <= vw - 1.0 * a15
        if m == "rollhigh":
            return c > F["r4_high5p"][i] and c - lo >= 0.5 * a15
        raise ValueError(m)

    def _salvage_orders(self, ctx, i, sv, taken, a15):
        b = ctx.bars
        rec = ctx.lane("rec")
        if self._salv_day != b.day[i]:
            self._salv_day, self._salv_n = b.day[i], 0
        if self._salv_n >= sv.get("max_per_day", 1):
            return []
        dead = [t for t in rec.tranches if t.id not in taken and self._is_dead(ctx, i, t)]
        if not dead or not self._rebound_ok(sv, i, a15):
            return []
        sel = sv.get("select", "oldest")
        c = b.c[i]
        if sel == "oldest":
            t = min(dead, key=lambda t: t.entry_idx)
        elif sel == "highest":
            t = max(dead, key=lambda t: t.entry_px)
        elif sel == "closest_be":
            t = max(dead, key=lambda t: c - t.entry_px)
        else:
            raise ValueError(sel)
        self._salv_n += 1
        self.n_salvage += 1
        return [Order("market_sell", "rec", tranche_id=t.id, tag="salvage")]

    def _r4_exit_orders(self, ctx, i, existing, a15):
        k = self.cfg
        self._bars = ctx.bars
        rec = ctx.lane("rec")
        out = []
        taken = {o.tranche_id for o in existing if o.tranche_id is not None}
        hc = k["harvest_cond"]
        pol = None
        if hc:
            trig = hc.get("trig", "free")
            if trig == "free":
                fire = rec.free <= hc.get("k", 1)
            elif trig == "dead":
                nd = sum(1 for t in rec.tranches if self._is_dead(ctx, i, t))
                fire = nd >= hc.get("x", 0.5) * rec.spec.capacity
            elif trig == "inv":
                fire = ctx.total_qty >= hc.get("q", 0.75 * ctx.max_total)
            elif trig == "always":
                fire = True
            else:
                raise ValueError(trig)
            if fire:
                pol = (hc["policy"], hc.get("hx", 1.0), hc.get("be", 1.0), hc.get("core", False))
        cs = k["cap_sm"]
        if cs and cs.get("harvest") and rec.free <= cs.get("harvest_at", 1) and pol is None:
            pol = (cs["harvest"], cs.get("hx", 1.0), cs.get("be", 1.0), False)
        if pol is not None:
            sel = self._harvest_select(ctx, i, pol[0], pol[1], pol[2], pol[3], taken)
            for n, t in sel:
                out.append(Order("market_sell", n, tranche_id=t.id, tag="H_cond"))
                taken.add(t.id)
            self.n_cond_harvest += len(sel)
        sv = None
        if k["salvage"]:
            s0 = k["salvage"]
            if s0.get("trig", "free") == "always" or rec.free <= s0.get("k", 0):
                sv = s0
        if cs and cs.get("salvage") and rec.free <= cs.get("salvage_at", 0) and sv is None:
            sv = cs["salvage"]
        if sv is not None:
            out += self._salvage_orders(ctx, i, sv, taken, a15)
        return out

    def _harvest_orders(self, ctx, i, existing, dd_mode):
        k, b = self.cfg, ctx.bars
        c = b.c[i]
        out = []
        taken = {o.tranche_id for o in existing if o.tranche_id is not None}
        # recycle LIFO layer exits (Phase 4 B/C)
        if k["rec_cap"] and k["rec_exit"] in ("last", "last2"):
            rec = ctx.lane("rec")
            tr = sorted(rec.tranches, key=lambda t: t.entry_idx)
            if tr:
                grp = tr[-1:] if k["rec_exit"] == "last" else tr[-2:]
                px = ceil_tick(sum(t.entry_px for t in grp) / len(grp) + k["rec_exit_x"])
                out += [Order("limit_sell", "rec", tranche_id=t.id, price=px, tag=f"R_{k['rec_exit']}") for t in grp if t.id not in taken]
        mode = k["harvest"]
        if dd_mode == "core_harvest":
            mode = "all_prof"
        if not mode:
            return out
        x = k["harvest_x"]
        lanes = ["rec"] if mode == "rec_prof" else [n for n in ctx.lanes]
        prof = [(n, t) for n in lanes for t in ctx.lane(n).tranches if c - t.entry_px >= x and t.id not in taken]
        if mode == "partial_high":
            if ctx.total_qty < 0.75 * ctx.max_total:
                return out
            prof = sorted(prof, key=lambda nt: nt[1].entry_px)[: max(len(prof) // 2, 1)] if prof else []
        out += [Order("market_sell", n, tranche_id=t.id, tag=f"H_{mode}") for n, t in prof]
        return out

    def _rec_anchor_ok(self, ctx, i, a15, has_open):
        k, F, b = self.cfg, self.F, ctx.bars
        c = b.c[i]
        an = k["rec_anchor"]
        if an == "none":           # NULL-B: dumb floating recycle, no timing condition
            return True
        if an == "feat":           # NULL-C: externally supplied (e.g. random, time-of-day matched) signal
            return bool(F[k["rec_anchor_feat"]][i])
        if an == "runhigh":
            if has_open:
                return True        # ladder/float spacing already enforced
            return self._hi is not None and c <= self._hi - k["rec_step"]
        if an in ("low30", "low60"):
            lowp = F[an][i - 1] if i > 0 else np.nan
            return np.isfinite(lowp) and b.l[i] <= lowp and c >= b.l[i] + 0.25 * a15
        if an == "vwap":
            return c <= F["vwap"][i] - k["rec_vwap_k"] * a15
        if an == "range":
            return F["rangepos120"][i] <= 0.15
        if an == "swing":
            return c <= F["high30"][i] - k["rec_step"] and c > F["prev_high"][i]
        raise ValueError(an)

    def _rec_roll_orders(self, ctx, i, a15, in_rec_mode):
        k, F, b = self.cfg, self.F, ctx.bars
        rec = ctx.lane("rec")
        if rec.free > 0 or not rec.tranches:
            return []
        c = b.c[i]
        lo = min(t.entry_px for t in rec.tranches)
        m = k["rec_roll"]
        x = k["rec_roll_x"]
        if m == "pts":
            trig = c <= lo - x
        elif m == "atr":
            trig = c <= lo - x * a15
        elif m == "newlow":
            trig = c <= lo - k["rec_step"] and np.isfinite(F["low60"][i - 1]) and b.l[i] < F["low60"][i - 1]
        elif m == "reversal":
            trig = c <= lo - x and c > F["prev_high"][i]
        else:
            raise ValueError(m)
        if not trig:
            return []
        if k["rec_roll_select"] == "oldest":
            sel = min(rec.tranches, key=lambda t: t.entry_idx)
        else:   # highest cost == worst distance-to-market for a long
            sel = max(rec.tranches, key=lambda t: t.entry_px)
        return [Order("market_sell", "rec", tranche_id=sel.id, tag="rotate"),
                Order("market_buy", "rec", 1, tp_pts=self._rec_tp(ctx, i), tag="rot_buy")]

    def _emerg_orders(self, ctx, i):
        k, b = self.cfg, ctx.bars
        em = ctx.lane("emerg")
        if em.free <= 0:
            return []
        acc = k["emerg_access"]
        others_full = all(ln.free <= 0 for nm, ln in ctx.lanes.items() if nm != "emerg")
        if acc == "others_full":
            ok = others_full
        elif acc == "critical":
            ok = self._state == "CRITICAL" or others_full
        else:
            raise ValueError(acc)
        if not ok:
            return []
        allp = [t.entry_px for ln in ctx.lanes.values() for t in ln.tranches]
        ref = min(allp) if allp else b.c[i]
        eopen = [t.entry_px for t in em.tranches]
        if eopen:
            ref = min(min(eopen), ref)
        if b.c[i] <= ref - k["emerg_step"]:
            return [Order("market_buy", "emerg", 1, tp_pts=k["emerg_tp"], tag="emerg")]
        return []
