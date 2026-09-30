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
    ex_extra = e.get("extra") or {}
    if ex_extra.get("save"):
        os.makedirs(SAVE_DIR, exist_ok=True)
        st = eng.state
        day = pd.DatetimeIndex(st.dt).normalize()
        st.groupby(day).agg(equity=("equity", "last"), qty=("qty", "max"), realized=("realized_net", "last"),
                            unreal=("unrealized", "last")).to_parquet(os.path.join(SAVE_DIR, f"{e['config_id']}_daily.parquet"))
        np.save(os.path.join(SAVE_DIR, f"{e['config_id']}_qty.npy"), st.qty.values.astype(np.int16))
        eng.trades_df.to_parquet(os.path.join(SAVE_DIR, f"{e['config_id']}_trades.parquet"))
    del eng, strat
    worst = np.inf
    for s in e.get("fresh") or []:
        b, F = rl.slice_from(s)
        ef = Engine(b, FactoryStrategy(F, **cfg), ex).run()
        fr = rl.summarize(ef)
        pre = f"fs{s[:4]}_"
        for k in FRESH_KEYS:
            r[pre + k] = fr[k]
        worst = min(worst, fr["min_equity"])
        del ef
    r["worst_fresh_min_equity"] = worst if np.isfinite(worst) else np.nan
    r["runtime_s"] = time.time() - t0
    return _clean(r)
