"""RUN-4 Sleeve A metrics computed from a finished Engine run (no behaviour change):

- recycle slot state model: time-weighted occupancy by tranche age (FRESH <1d, STALLED 1-5d, DEAD >=5d, plus
  DEAD>=10/20/40d and distance-DEAD: entry - close >= 1 daily ATR), active/dead slot fractions, ages, MAE
- recycle efficiency: trades per active-slot-day, P&L per rec-slot-day, P&L per rec contract-hour
- capital efficiency: P&L per contract-day / contract-hour (calendar), weekly P&L / avg and peak notional,
  annual P&L / |Max MTM DD|
- turnover: closed trades per trading day (mean/median/p10/p90), holding minutes, gross/net EV and cost per trade
- NULL-D decomposition of gross MTM: exposure-matched passive long (mean inventory x price change) + inventory
  timing (covariance of inventory with price changes) + execution residual; per lane
- shadow slot (opportunity cost of one more recycle slot) from FactoryStrategy.shadow_log
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import fastsim as fs

NS_DAY = 86400 * 10**9
DEAD_DAYS = (1, 2, 5, 10, 20, 40)


class BarIndex:
    """Per-bars cached helpers (block indices) shared across runs in a worker."""

    def __init__(self, b, pen_ticks=1):
        self.b = b
        self.B = 1024
        self.nxt, self.last_td, self.nil, self.dtm = fs.day_structure(b)
        self.g = fs.tp_trigger_array(b, pen_ticks)
        self.bmax_g = fs.block_max(self.g, self.B)
        self.lmin = fs.block_min(b.l, self.B)
        self.tidx = np.flatnonzero(b.tradeable)
        self.tdt = b.dt[self.tidx]
        self.n_trade_bars = len(self.tidx)
        self.n_days = len(np.unique(b.day[self.tidx]))


def _rec_tranches(e):
    b = e.bars
    n = len(b)
    tr = e.trades_df
    rows = []
    if len(tr):
        r = tr[tr.lane == "rec"]
        rows.append(pd.DataFrame(dict(entry_idx=r.entry_idx.values, exit_idx=r.exit_idx.values, entry_px=r.entry_px.values,
                                      net=r.net.values, closed=True, qty=r.qty.values)))
    op = [t for t in e.lanes["rec"].tranches] if "rec" in e.lanes else []
    if op:
        last = n - 1
        rows.append(pd.DataFrame(dict(entry_idx=[t.entry_idx for t in op], exit_idx=[last] * len(op),
                                      entry_px=[t.entry_px for t in op],
                                      net=[(b.c[last] - t.entry_px) * t.qty * e.cfg.point_value - t.qty * e.cfg.commission_per_side for t in op],
                                      closed=[False] * len(op), qty=[t.qty for t in op])))
    if not rows:
        return pd.DataFrame(columns=["entry_idx", "exit_idx", "entry_px", "net", "closed", "qty"])
    return pd.concat(rows, ignore_index=True)


def slot_metrics(e, bi: BarIndex, F) -> dict:
    b = e.bars
    out = {}
    if "rec" not in e.lanes:
        return out
    cap = e.lanes["rec"].spec.capacity
    R = _rec_tranches(e)
    if not len(R):
        return dict(rec_cap=cap, rec_tranches=0)
    ei = R.entry_idx.values.astype(np.int64)
    xi = R.exit_idx.values.astype(np.int64)
    ep = R.entry_px.values.astype(float)
    age_d = (b.dt[xi] - b.dt[ei]).astype("int64") / NS_DAY
    mae = fs.tranche_mae(ei, xi, ep, b.l, bi.lmin, bi.B)
    a15 = np.maximum(F["atr15"][ei], 0.25)
    pos_s = np.searchsorted(bi.tidx, ei)
    pos_e = np.searchsorted(bi.tidx, xi)          # bars [entry, exit) occupy the slot
    occ = np.maximum(pos_e - pos_s, 0)
    N = bi.n_trade_bars
    out.update(rec_cap=cap, rec_tranches=int(len(R)), rec_open_end=int((~R.closed).sum()),
               rec_age_med_d=float(np.median(age_d)), rec_age_p90_d=float(np.percentile(age_d, 90)),
               rec_age_p95_d=float(np.percentile(age_d, 95)), rec_age_p99_d=float(np.percentile(age_d, 99)),
               rec_age_max_d=float(age_d.max()), rec_mae_med=float(np.median(mae)), rec_mae_p90=float(np.percentile(mae, 90)),
               rec_mae_atr_p90=float(np.percentile(mae / a15, 90)),
               rec_occ_avg=float(occ.sum() / N))
    band = {}
    for D in DEAD_DAYS:
        thr = b.dt[ei] + np.timedelta64(int(D * 86400), "s")
        pos_t = np.searchsorted(bi.tdt, thr)
        band[D] = float(np.maximum(pos_e - np.maximum(pos_s, pos_t), 0).sum() / N)
    fresh = out["rec_occ_avg"] - band[1]
    free = cap - out["rec_occ_avg"]
    out.update(slots_free_avg=free, slots_fresh_avg=fresh, slots_stalled_avg=band[1] - band[5], slots_dead_avg=band[5],
               slots_dead10_avg=band[10], slots_dead20_avg=band[20], slots_dead40_avg=band[40],
               active_slot_frac=(free + fresh) / cap, dead_slot_frac=band[5] / cap, dead20_slot_frac=band[20] / cap,
               stalled_slot_frac=(band[1] - band[5]) / cap)
    dd = fs.dist_dead_bars(ei, xi, ep, b.c, F["datr"], b.tradeable, 1.0)
    out["dist_dead_slot_frac"] = float(dd.sum() / N / cap)
    days = bi.n_days
    act_slot_days = (free + fresh) * days
    closed = R[R.closed]
    rec_pnl = float(R.net.sum())
    hold_h = age_d * 24.0
    out.update(rec_trades_per_active_slot_day=len(closed) / max(act_slot_days, 1e-9),
               rec_pnl_per_slot_day=rec_pnl / (cap * days), rec_pnl_total_incl_open=rec_pnl,
               rec_pnl_per_contract_hour=rec_pnl / max(float((hold_h * R.qty.values).sum()), 1e-9),
               rec_losses_realized=int((closed.net < 0).sum()))
    return out


def capital_metrics(e, s: dict) -> dict:
    st = e.state
    dt = st.dt.values
    q = st.qty.values.astype(float)
    dtd = np.diff(dt).astype("int64") / NS_DAY
    cdays = float((q[:-1] * dtd).sum())
    years = float((dt[-1] - dt[0]).astype("int64") / NS_DAY / 365.25)
    tot = s["total_mtm"]
    raw = st.raw_c.values
    notional = q * np.abs(raw) * e.cfg.point_value
    out = dict(contract_days=cdays, pnl_per_contract_day=tot / max(cdays, 1e-9), pnl_per_contract_hour=tot / max(cdays * 24, 1e-9),
               wk_pnl_over_peak_notional=s.get("wk_mean", np.nan) / max(float(notional.max()), 1.0),
               annual_pnl_over_maxdd=(tot / max(years, 1e-9)) / max(-s["max_mtm_dd"], 1.0), years=years)
    return out


def turnover_metrics(e) -> dict:
    tr = e.trades_df
    b = e.bars
    if not len(tr):
        return dict(n_closed=0)
    days = pd.Index(np.unique(b.day[b.tradeable]))
    per_day = pd.Series(1, index=b.day[tr.exit_idx.values]).groupby(level=0).sum().reindex(days, fill_value=0)
    hold = (pd.to_datetime(tr.exit_dt) - pd.to_datetime(tr.entry_dt)).dt.total_seconds().values / 60
    n = len(tr)
    cost = float(e.commission + e.slippage)
    return dict(n_closed=n, tpd_mean=float(per_day.mean()), tpd_median=float(per_day.median()),
                tpd_p10=float(per_day.quantile(.1)), tpd_p90=float(per_day.quantile(.9)),
                hold_min_mean=float(hold.mean()), hold_min_median=float(np.median(hold)),
                ev_gross_per_trade=float(tr.gross.sum() / n), ev_net_per_trade=float(tr.net.sum() / n),
                cost_per_trade=cost / n)


def nulld_decomposition(e) -> dict:
    """Gross MTM decomposition (price terms only; costs reported separately):
    sum_t q_{t-1} dp_t = qbar * sum dp  (exposure-matched passive long, NULL-D)
                       + sum (q_{t-1} - qbar) dp_t   (inventory timing)
    execution residual = actual gross P&L - sum q dp (entry/exit prices inside bars vs closes)."""
    st = e.state
    pv = e.cfg.point_value
    c = st.c.values
    dp = np.diff(c)
    out = {}
    q = st.qty.values.astype(float)
    qb = q[:-1].mean()
    mtm = float((q[:-1] * dp).sum() * pv)
    passive = float(qb * dp.sum() * pv)
    out.update(q_mean=float(qb), nulld_passive_pnl=passive, timing_pnl=mtm - passive, mtm_px_pnl=mtm)
    # actual price P&L before costs = realized_net + commission + roll_cost + unrealized (fills already incl. slippage)
    actual = float(e.realized_net + e.commission + e.roll_cost + st.unrealized.iloc[-1])
    out["exec_residual_pnl"] = actual - mtm
    out["costs_total"] = float(e.commission + e.roll_cost + e.slippage)
    for ln in e.lanes:
        ql = st[f"qty_{ln}"].values.astype(float)
        out[f"mtm_{ln}"] = float((ql[:-1] * dp).sum() * pv)
        out[f"qmean_{ln}"] = float(ql[:-1].mean())
    # passive long with the same mean inventory also pays rolls
    out["nulld_passive_net"] = passive - qb * len(e.roll_events) * e.cfg.roll_cost()
    return out


def shadow_metrics(e, strat, bi: BarIndex, limit_mode: bool) -> dict:
    log = strat.shadow_log
    b = e.bars
    out = dict(shadow_signals=len(log))
    if not log:
        return out
    arr = np.asarray(log, dtype=float)
    si = arr[:, 0].astype(np.int64)
    tp = arr[:, 1]
    ndead = arr[:, 2]
    out["shadow_signals_with_dead"] = int((ndead >= 1).sum())
    se, sx, sep, sxp = fs.shadow_sim(si, tp, limit_mode, b.o, b.h, b.l, b.c, bi.g, bi.bmax_g, bi.B, b.tradeable, bi.nxt,
                                    e.cfg.slippage_ticks, e.cfg.penetration_ticks)
    pv = e.cfg.point_value
    cm = e.cfg.commission_per_side
    last = len(b) - 1
    closed = sx >= 0
    pnl = np.where(closed, (sxp - sep) * pv - 2 * cm, (b.c[last] - sep) * pv - cm)
    st = e.state
    rq = st.qty_rec.values[bi.tidx]
    tq = st.qty.values[bi.tidx]
    blocked = (rq >= e.lanes["rec"].spec.capacity) | (tq >= e.max_total)
    blocked_days = float(blocked.sum() / 405.0)
    years = float((b.dt[-1] - b.dt[0]).astype("int64") / NS_DAY / 365.25)
    out.update(shadow_trades=int(len(se)), shadow_closed=int(closed.sum()), shadow_pnl=float(pnl.sum()),
               shadow_pnl_realized=float(pnl[closed].sum()), shadow_open_end=int((~closed).sum()),
               shadow_trades_per_day=len(se) / max(bi.n_days, 1), shadow_pnl_per_year=float(pnl.sum()) / max(years, 1e-9),
               blocked_share=float(blocked.mean()), blocked_days=blocked_days,
               shadow_pnl_per_blocked_day=float(pnl.sum()) / max(blocked_days, 1e-9),
               shadow_hold_med_min=float(np.median((bi.dtm[np.where(closed, sx, last)] - bi.dtm[se]))) if len(se) else np.nan)
    return out
