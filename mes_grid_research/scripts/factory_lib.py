"""Research-factory runner: run FactoryStrategy configs in parallel, save metrics + one summary row each."""
import json, os, sys, time, subprocess
from dataclasses import replace
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy
from mesgrid import metrics, ENGINE_VERSION, EXEC_SPEC_VERSION, ROLL_MODEL_VERSION, DATASET_SHA256
from mesgrid.stress import window_report, top_drawdowns

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDOWS = {"w20": ("2020-02-01", "2020-08-31"), "w2223": ("2022-01-01", "2023-12-31"), "w25": ("2025-02-01", "2025-07-31")}
PERIODS = {"p1921": ("2019-05-01", "2021-12-31"), "p22": ("2022-01-01", "2022-12-31"), "p23p": ("2023-01-01", "2026-12-31")}
_B = _F = None


def git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        return None


def init(start=None, end=None):
    global _B, _F
    _B = load_canonical(start=start, end=end)
    _F = compute_features(_B, _B.v)


def _episodes(dt, mask):
    from mesgrid.metrics import episodes
    ep = episodes(dt, mask, top=1)
    return ep[0][0] if ep else 0.0


def summarize(e, m, cfg):
    st = e.state
    b = e.bars
    dt = st.dt.values
    q = st.qty.values
    tr = e.trades_df
    L = m["lanes"]
    cap = cfg.get("cap_total") or 32
    row = dict(realized=m["realized_net"], unreal_end=m["unrealized_end"], total_mtm=m["total_mtm_pnl"],
               open_qty_end=m["open_qty_end"], max_mtm_dd=m["max_mtm_dd"], max_dd_trough=m["max_mtm_dd_trough"][:10],
               worst_cycle=(m["worst_cycle_mtm"] or (0,))[0], min_equity=m["min_equity"],
               underwater_days=m["longest_mtm_underwater_days"], pf=m["profit_factor"], trades=m["trades"],
               trades_day=m["trades_per_day"], cost=m["total_cost"], roll_cost=m["roll_cost"],
               inv_avg=m["inv_avg_rth"], inv_p95=m["inv_p95_rth"], inv_max=m["inv_max"],
               share16=m["inv_share_rth_ge"][16], share_gt24=float((q[b.tradeable] > 24).mean()),
               share32=m["inv_share_rth_ge"][32],
               lock32_days=m["longest_max_lock"][0][0] if m["longest_max_lock"] else 0.0,
               gt24_days=m["longest_gt24"][0][0] if m["longest_gt24"] else 0.0,
               sat_days=_episodes(dt, q >= cap),
               peak_notional=m["peak_notional"], avg_notional=m["avg_notional_rth"],
               min_excess_2500=m["margin_stress"][2500]["min_excess_liquidity"],
               ret_over_dd=m["total_mtm_pnl"] / max(-m["max_mtm_dd"], 1.0),
               ret_per_avg_notional=m["total_mtm_pnl"] / max(m["avg_notional_rth"], 1.0))
    for ln in ("rec", "emerg"):
        d = L.get(ln)
        if d:
            lt = tr[tr.lane == ln] if len(tr) else tr
            lq = st[f"qty_{ln}"].values[b.tradeable]
            row.update({f"{ln}_trades_day": d.get("trades_per_day", 0.0), f"{ln}_pnl": d.get("pnl_net", 0.0),
                        f"{ln}_loss_realized": float(lt.net[lt.net < 0].sum()) if len(lt) else 0.0,
                        f"{ln}_rotations": int((lt.reason == "rotate").sum()) if len(lt) else 0,
                        f"{ln}_full_share": d["full_share_rth"], f"{ln}_zero_free_days": d["longest_full"][0][0] if d["longest_full"] else 0.0,
                        f"{ln}_free_avg": float((d["capacity"] - lq).mean()), f"{ln}_max": int(lq.max())})
    if len(tr):
        lt = tr[tr.lane == "core"]
        row["core_trades_day"] = len(lt) / max(m["trading_days"], 1)
    # periods (MTM change inside period, path from full run)
    dts = pd.DatetimeIndex(dt)
    eq = st.equity.values
    for k, (s, t) in PERIODS.items():
        msk = (dts >= s) & (dts <= t)
        if msk.any():
            i0 = np.argmax(msk); i1 = len(msk) - 1 - np.argmax(msk[::-1])
            base = eq[i0 - 1] if i0 > 0 else e.cfg.initial_capital
            row[f"{k}_mtm"] = float(eq[i1] - base)
            seg = eq[i0:i1 + 1]
            row[f"{k}_dd"] = float((seg - np.maximum.accumulate(np.concatenate([[base], seg]))[1:]).min())
    yr = pd.Series(eq, index=dts.year).groupby(level=0).last()
    ych = yr.diff().fillna(yr.iloc[0] - e.cfg.initial_capital)
    row["worst_year_mtm"] = float(ych.min()); row["pos_years"] = int((ych > 0).sum()); row["n_years"] = int(len(ych))
    for k, (s, t) in WINDOWS.items():
        if not ((dts >= s) & (dts <= t)).any():
            continue
        w = window_report(e, s, t)
        row[f"{k}_dd"] = w["mtm_dd_from_prior_peak"]
        row[f"{k}_lock"] = (w["longest_max_lock_in_window"] or (0,))[0]
        row[f"{k}_share32"] = w["share_rth_at_max"]
        row[f"{k}_trades"] = w["sells"]
        row[f"{k}_rec_trades"] = w["lanes"].get("rec", {}).get("trades", 0)
        msk = (dts >= s) & (dts <= t)
        row[f"{k}_gt24_days"] = _episodes(dt[msk], q[msk] > 24)
    return row


def run_one(args):
    exp, name, family, module, control, cfg, exec_kw, save_trades = args
    t0 = time.time()
    ex = ExecConfig(**exec_kw)
    strat = FactoryStrategy(_F, **cfg)
    e = Engine(_B, strat, ex).run()
    m = metrics.compute(e, name)
    row = dict(exp=exp, name=name, family=family, module=module, control=control,
               cfg=json.dumps(cfg, default=str, sort_keys=True), exec=json.dumps(exec_kw, sort_keys=True))
    row.update(summarize(e, m, cfg))
    row["runtime_s"] = time.time() - t0
    d = os.path.join(ROOT, "results", exp, name)
    os.makedirs(d, exist_ok=True)
    m["lineage"] = dict(exp=exp, name=name, dataset_sha256=DATASET_SHA256, engine_version=ENGINE_VERSION,
                        exec_spec=EXEC_SPEC_VERSION, roll_model=ROLL_MODEL_VERSION, git=git_hash(), cfg=cfg,
                        exec_cfg=ex.__dict__, date_range=[str(_B.dt[0]), str(_B.dt[-1])])
    m.pop("open_inventory", None)
    json.dump(dict(metrics=m, summary=row, top10_dd=top_drawdowns(e, 10)), open(os.path.join(d, "metrics.json"), "w"),
              indent=1, default=str)
    if save_trades and len(e.trades_df):
        e.trades_df.to_csv(os.path.join(d, "trades.csv.gz"), index=False)
    return row


def run_batch(exp, jobs, procs=4, start=None, end=None, out_name="summary.csv"):
    """jobs: list of (name, family, module, control, cfg, exec_kw, save_trades)"""
    os.makedirs(os.path.join(ROOT, "results", exp), exist_ok=True)
    args = [(exp,) + tuple(j) for j in jobs]
    rows = []
    with Pool(procs, initializer=init, initargs=(start, end)) as p:
        for k, r in enumerate(p.imap_unordered(run_one, args)):
            rows.append(r)
            if (k + 1) % 10 == 0:
                print(f"[{exp}] {k + 1}/{len(args)} done", flush=True)
                pd.DataFrame(rows).to_csv(os.path.join(ROOT, "results", exp, out_name + ".partial"), index=False)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(ROOT, "results", exp, out_name), index=False)
    return df
