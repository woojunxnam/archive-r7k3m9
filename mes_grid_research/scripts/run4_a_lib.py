"""RUN-4 Sleeve A engine job: FactoryStrategy full history (+ fresh starts) with RUN-4 metrics.
ES-signal / MES-economics proxy backtest, EXEC-1.1 conservative, ROLL-1.0."""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
import run3_lib as rl
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy
from mesgrid import slotmetrics as sm

ROOT = rl.ROOT
TRAP_CACHE = os.path.join(ROOT, "data", "cache", "r4_trap_scores.npz")
BI = None
SAVE_DIR = os.path.join(ROOT, "results", "RUN4_OVERNIGHT", "series")


def FQ(cc, rc, add=True, lmt=True, **kw):
    """Frozen FQ mechanism (RUN-2/3) with RUN-4 defaults: armed add, limit_close recycle entry, shadow book on."""
    d = rl.FQ(cc, rc, add, **kw)
    if lmt and "rec_entry_mode" not in kw:
        d["rec_entry_mode"] = "limit_close"
    d.setdefault("shadow", True)
    return d


def anchor_rate_by_tod(b, F):
    """rate of the FQ recycle anchor (low60 touch + 0.25 ATR bounce) per 30-minute time-of-day bucket (RTH)."""
    W = np.flatnonzero(b.in_window)
    lo_prev = np.concatenate([[np.nan], F["low60"][W][:-1]])
    a15 = F["atr15"][W]
    l, c = b.l[W], b.c[W]
    anc = (l <= lo_prev) & (c >= l + 0.25 * a15)
    bucket = (b.minute[W] - 571) // 30
    rate = pd.Series(anc.astype(float)).groupby(bucket).mean()
    return rate, W, bucket


def r4_extras(b, F, n_rnd=20):
    out = {}
    W = np.flatnonzero(b.in_window)
    h = b.h[W]
    hp = pd.Series(h).shift(1).rolling(5, min_periods=3).max().values
    a = np.full(len(b), np.nan); a[W] = hp
    out["r4_high5p"] = a
    rate, W, bucket = anchor_rate_by_tod(b, F)
    p = rate.reindex(bucket).values
    for s in range(1, n_rnd + 1):
        rng = np.random.default_rng(1000 + s)
        m = np.zeros(len(b), bool)
        m[W] = rng.random(len(W)) < p
        out[f"rnd_s{s}"] = m
    bev = os.path.join(ROOT, "data", "cache", "r4_b_events.npz")
    if os.path.exists(bev):
        # A/B interaction feature: False within 30 RTH minutes after a strong B momentum event (B7 first impulse or
        # opening-range break); core averaging can be paused while it is False (known at the event bar's close)
        z = np.load(bev)
        flag = np.zeros(len(b), bool)
        for k in ("B7_tf3_k5.0_first", "B4_or15_break"):
            if k in z.files:
                flag[z[k]] = True
        f = flag[W].astype(float)
        recent = pd.Series(f).rolling(30, min_periods=1).max().values > 0
        ok = np.ones(len(b), bool)
        ok[W] = ~recent
        out["bmom_ok30"] = ok
    if os.path.exists(TRAP_CACHE):
        z = np.load(TRAP_CACHE)
        for k in z.files:
            out[k] = z[k]
    return out


def init_a():
    global BI
    rl.init(r4_extras)
    BI = sm.BarIndex(rl._B)


def _clean(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, (np.integer,)):
            v = int(v)
        elif isinstance(v, (np.floating,)):
            v = float(v)
        elif isinstance(v, (np.bool_,)):
            v = bool(v)
        out[k] = v
    return out


FRESH_KEYS = ("total_mtm", "max_mtm_dd", "min_equity", "no_entry_days", "underwater_days", "trades_day", "max_inv",
              "active_share", "open_qty_end", "unreal_end", "realized")


def job_engine(e):
    t0 = time.time()
    cfg = dict(e["params"])
    ex = ExecConfig(**e["exec"])
    strat = FactoryStrategy(rl._F, **cfg)
    eng = Engine(rl._B, strat, ex).run()
    r = rl.summarize(eng)
    r.update(sm.slot_metrics(eng, BI, rl._F))
    r.update(sm.capital_metrics(eng, r))
    r.update(sm.turnover_metrics(eng))
    r.update(sm.nulld_decomposition(eng))
    if cfg.get("shadow") and cfg.get("rec_cap"):
        r.update(sm.shadow_metrics(eng, strat, BI, cfg.get("rec_entry_mode") == "limit_close"))
    r["n_salvage"] = strat.n_salvage
    r["n_cond_harvest"] = strat.n_cond_harvest
    tr = eng.trades_df
    if len(tr):
        for tag in ("salvage", "H_cond"):
            t = tr[tr.reason == tag]
            r[f"{tag}_n"] = int(len(t)); r[f"{tag}_realized"] = float(t.net.sum())
            r[f"{tag}_avg"] = float(t.net.mean()) if len(t) else np.nan
        rt = tr[tr.lane == "rec"]
        r["rec_realized_losses_sum"] = float(rt.net[rt.net < 0].sum())
        # recycle P&L split: TP exits vs other exits
        r["rec_tp_exit_pnl"] = float(rt.net[rt.reason.isin(["tp", "tp_gap"])].sum())
    # temporal robustness: calendar-year MTM P&L and rolling 12-month windows (daily equity)
    st_ = eng.state
    deq = pd.Series(st_.equity.values, index=pd.DatetimeIndex(st_.dt).normalize()).groupby(level=0).last()
    dpl = deq.diff().fillna(deq.iloc[0] - 150000.0)
    yr = dpl.groupby(dpl.index.year).sum()
    for y in range(2019, 2027):
        r[f"y{y}_mtm"] = float(yr.get(y, 0.0))
    r["years_pos_mtm"] = int((yr > 0).sum())
    m12 = deq.rolling("365D").apply(lambda x: x[-1] - x[0], raw=True)
    r["roll12m_worst_pnl"] = float(m12[m12.index >= m12.index[0] + pd.Timedelta(days=365)].min())
    r["roll12m_pos_share"] = float((m12[m12.index >= m12.index[0] + pd.Timedelta(days=365)] > 0).mean())
    r["p19_21_mtm"] = float(sum(r[f"y{y}_mtm"] for y in (2019, 2020, 2021)))
    r["p22_mtm"] = r["y2022_mtm"]
    r["p23p_mtm"] = float(sum(r[f"y{y}_mtm"] for y in (2023, 2024, 2025, 2026)))
    ex_extra = e.get("extra") or {}
    if ex_extra.get("save"):
        os.makedirs(SAVE_DIR, exist_ok=True)
        st = eng.state
        day = pd.DatetimeIndex(st.dt).normalize()
        st.groupby(day).agg(equity=("equity", "last"), qty=("qty", "max"), realized=("realized_net", "last"),
                            unreal=("unrealized", "last")).to_parquet(os.path.join(SAVE_DIR, f"{e['config_id']}_daily.parquet"))
        np.save(os.path.join(SAVE_DIR, f"{e['config_id']}_qty.npy"), st.qty.values.astype(np.int16))
        np.save(os.path.join(SAVE_DIR, f"{e['config_id']}_equity.npy"), st.equity.values.astype(np.float64))
        eng.trades_df.to_parquet(os.path.join(SAVE_DIR, f"{e['config_id']}_trades.parquet"))
    del eng, strat
    worst = np.inf
    for s in e.get("fresh") or []:
        b, F = rl.slice_from(s)
        ef = Engine(b, FactoryStrategy(F, **cfg), ex).run()
        fr = rl.summarize(ef)
        if ex_extra.get("save"):
            stf = ef.state
            dayf = pd.DatetimeIndex(stf.dt).normalize()
            stf.groupby(dayf).agg(equity=("equity", "last"), qty=("qty", "max")).to_parquet(
                os.path.join(SAVE_DIR, f"{e['config_id']}_fresh{s[:4]}_daily.parquet"))
        pre = f"fs{s[:4]}_"
        for k in FRESH_KEYS:
            r[pre + k] = fr[k]
        worst = min(worst, fr["min_equity"])
        del ef
    r["worst_fresh_min_equity"] = worst if np.isfinite(worst) else np.nan
    r["runtime_s"] = time.time() - t0
    return _clean(r)
