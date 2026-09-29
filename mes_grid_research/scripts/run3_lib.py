"""RUN-3 common runner: full history + fresh starts, capital / weekly / concentration metrics.
All results are "ES-signal / MES-economics proxy backtests" (ES OHLC as MES price proxy, $5/pt)."""
import json, os, sys, time
from dataclasses import replace
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy
from mesgrid import metrics, ENGINE_VERSION, EXEC_SPEC_VERSION, ROLL_MODEL_VERSION, DATASET_SHA256
from mesgrid.metrics import episodes, longest_underwater

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRESH = ("2020-02-01", "2022-01-01", "2025-02-01")
LABEL = "ES-signal / MES-economics proxy backtest"
R1 = dict(rec_activation="always", rec_anchor="low60", rec_spacing="float", rec_step=5.0, rec_tp=3.0)
ADD = dict(add_trigger="armed", reversal="ll_fail")
_B = _F = None
_EXTRA = None


def FQ(cc, rc, add=False, **kw):
    """Frozen FQ mechanism (RUN-2 discovery): always-active floating recycle (low60) + recovery mode.
    recovery trigger h = core cap on TOTAL inventory; exit threshold 12 (literal RUN-2 value)."""
    d = dict(R1, core_cap=cc, rec_cap=rc, max_total=cc + rc, recovery=dict(h=cc, rec_tp=2.0, rec_step=10.0, layer_x=5.0))
    if add:
        d.update(ADD)
    d.update(kw)
    return d


def init(extra_feature_fn=None):
    global _B, _F
    _B = load_canonical()
    _F = compute_features(_B, _B.v)
    if extra_feature_fn:
        _F.update(extra_feature_fn(_B, _F))


def slice_from(start):
    k = int(np.searchsorted(_B.dt, np.datetime64(pd.Timestamp(start))))
    fields = ("dt", "o", "h", "l", "c", "adj", "contract", "day", "minute", "in_window", "tradeable", "v")
    b = replace(_B, **{f: getattr(_B, f)[k:] for f in fields})
    F = {kk: v[k:] for kk, v in _F.items()}
    return b, F


def weekly_stats(st, cap=150000.0):
    day = pd.DatetimeIndex(st.dt).normalize()
    daily = pd.Series(st.equity.values, index=day).groupby(level=0).last()
    dpnl = daily.diff().fillna(daily.iloc[0] - cap)
    wk = daily.resample("W-FRI").last().dropna()
    w = wk.diff().fillna(wk.iloc[0] - cap)
    r4 = w.rolling(4).sum()
    neg = (w < 0).astype(int).values
    streak = best = 0
    for x in neg:
        streak = streak + 1 if x else 0
        best = max(best, streak)
    tot = dpnl.sum()
    srt = dpnl.sort_values(ascending=False)
    out = dict(wk_mean=w.mean(), wk_median=w.median(), wk_p10=w.quantile(.1), wk_p25=w.quantile(.25), wk_best=w.max(),
               wk_worst=w.min(), wk_pos=(w > 0).mean(), wk_ge1k=(w >= 1000).mean(), wk_ge2k=(w >= 2000).mean(),
               wk_ge3k=(w >= 3000).mean(), wk_ge4k=(w >= 4000).mean(), wk_le_m2k=(w <= -2000).mean(),
               wk_le_m4k=(w <= -4000).mean(), wk_worst_4w=r4.min(), wk_longest_losing=int(best), n_weeks=len(w),
               top1_day_share=srt.iloc[0] / tot if tot > 0 else np.nan, top5_day_share=srt.iloc[:5].sum() / tot if tot > 0 else np.nan,
               top10_day_share=srt.iloc[:10].sum() / tot if tot > 0 else np.nan,
               pnl_ex_best5=tot - srt.iloc[:5].sum(), pnl_ex_best10=tot - srt.iloc[:10].sum())
    yr = dpnl.groupby(dpnl.index.year).sum()
    for y in (2020, 2022, 2025):
        out[f"pnl_ex_{y}"] = tot - yr.get(y, 0.0)
    return {k: float(v) for k, v in out.items()}


def summarize(e, prefix=""):
    m = metrics.compute(e)
    st = e.state
    b = e.bars
    dt = st.dt.values
    tr = e.trades_df
    fl = e.fills_df
    q = st.qty.values
    en = np.sort(fl[fl.side == "BUY"].dt.values) if len(fl) else np.array([], dtype="datetime64[ns]")
    ge = np.diff(np.concatenate([en, [dt[-1]]])) / np.timedelta64(1, "D") if len(en) else np.array([np.nan])
    fday = pd.DatetimeIndex(fl.dt).normalize().unique() if len(fl) else []
    uw = longest_underwater(dt, st.equity.values)
    ntd = max(m["trading_days"], 1)
    r = dict(total_mtm=m["total_mtm_pnl"], realized=m["realized_net"], unreal_end=m["unrealized_end"], open_qty_end=m["open_qty_end"],
             max_mtm_dd=m["max_mtm_dd"], min_equity=m["min_equity"], min_equity_dt=m["min_equity_dt"][:10],
             max_inv=int(q.max()), underwater_days=uw[0], underwater_recovered=uw[3],
             no_entry_days=float(ge.max()), active_share=len(fday) / ntd, trades_day=m["trades_per_day"],
             fills_total=int(len(fl)), peak_notional=m["peak_notional"], avg_notional=m["avg_notional_rth"],
             cost=m["total_cost"], commission=m["commission"], slippage=m["slippage_cost"], roll_cost=m["roll_cost"],
             inv_avg=m["inv_avg_rth"])
    for ln in ("rec", "core", "emerg"):
        if ln in e.lanes and len(tr):
            lt = tr[tr.lane == ln]
            r[f"{ln}_pnl"] = float(lt.net.sum())
            r[f"{ln}_trades_day"] = len(lt) / ntd
            r[f"{ln}_winrate"] = float((lt.net > 0).mean()) if len(lt) else np.nan
            if ln in e.lanes:
                lq = st[f"qty_{ln}"].values[b.tradeable]
                r[f"{ln}_full_share"] = float((lq >= e.lanes[ln].spec.capacity).mean())
    r.update(weekly_stats(st))
    r["contract_cap"] = int(e.max_total)
    r["profit_per_avg_contract"] = r["total_mtm"] / max(r["inv_avg"], 1e-9)
    r["profit_per_peak_contract"] = r["total_mtm"] / max(r["max_inv"], 1)
    r["wk_mean_over_dd"] = r["wk_mean"] / max(-r["max_mtm_dd"], 1)
    r["wk_mean_over_avg_notional"] = r["wk_mean"] / max(r["avg_notional"], 1)
    return {prefix + k: v for k, v in r.items()}


def run_cfg(args):
    name, cfg, exec_kw, fresh, save = args
    t0 = time.time()
    ex = ExecConfig(**exec_kw)
    out = dict(name=name, cfg=json.dumps(cfg, sort_keys=True, default=str), exec=json.dumps(exec_kw, sort_keys=True), label=LABEL)
    e = Engine(_B, FactoryStrategy(_F, **cfg), ex).run()
    out.update(summarize(e))
    if save:
        d = os.path.join(ROOT, "results", save, name)
        os.makedirs(d, exist_ok=True)
        e.trades_df.to_csv(os.path.join(d, "trades.csv.gz"), index=False)
        st = e.state
        day = pd.DatetimeIndex(st.dt).normalize()
        st.groupby(day).agg(equity=("equity", "last"), qty=("qty", "max")).to_csv(os.path.join(d, "daily.csv"))
    del e
    if fresh:
        worst = np.inf
        for s in FRESH:
            b, F = slice_from(s)
            ef = Engine(b, FactoryStrategy(F, **cfg), ex).run()
            fr = summarize(ef, prefix=f"fs{s[:4]}_")
            out.update({k: v for k, v in fr.items() if not k.split("_", 1)[1].startswith(("wk_", "top", "pnl_ex", "profit_per", "rec_", "core_", "emerg_"))})
            worst = min(worst, fr[f"fs{s[:4]}_min_equity"])
            del ef
        out["worst_fresh_min_equity"] = worst
    out["lineage"] = json.dumps(dict(dataset=DATASET_SHA256[:12], engine=ENGINE_VERSION, exec=EXEC_SPEC_VERSION, roll=ROLL_MODEL_VERSION))
    out["runtime_s"] = time.time() - t0
    return out


def run_batch(exp, jobs, procs=4, extra_feature_fn=None):
    """jobs: list of (name, cfg, exec_kw, fresh:bool, save:str|None)"""
    d = os.path.join(ROOT, "results", exp)
    os.makedirs(d, exist_ok=True)
    rows = []
    with Pool(procs, initializer=init, initargs=(extra_feature_fn,)) as p:
        for k, r in enumerate(p.imap_unordered(run_cfg, jobs)):
            rows.append(r)
            if (k + 1) % 5 == 0:
                print(f"[{exp}] {k + 1}/{len(jobs)}", flush=True)
                pd.DataFrame(rows).to_csv(os.path.join(d, "summary.csv.partial"), index=False)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(d, "summary.csv"), index=False)
    return df
