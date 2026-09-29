"""Run Baseline A (Basket +25, grid 5, max 32, immediate entry) on full canonical data."""
import json, os, sys, time, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.engine import Engine, ExecConfig
from mesgrid.strategies import BasketGrid
from mesgrid import metrics, ENGINE_VERSION, EXEC_SPEC_VERSION, DATASET_SHA256

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        return None

def run(exp_id, strat, cfg=None, bars=None, save=True):
    t0 = time.time()
    bars = bars or load_canonical()
    cfg = cfg or ExecConfig()
    e = Engine(bars, strat, cfg).run()
    m = metrics.compute(e, exp_id)
    m["runtime_s"] = time.time() - t0
    m["lineage"] = dict(exp_id=exp_id, dataset_sha256=DATASET_SHA256, engine_version=ENGINE_VERSION,
                        exec_spec=EXEC_SPEC_VERSION, git=git_hash(), params=getattr(strat, "params", {}),
                        exec_cfg=cfg.__dict__, date_range=[str(bars.dt[0]), str(bars.dt[-1])],
                        session="bar-end 09:31-16:15 ET, holidays excluded")
    if save:
        out = os.path.join(ROOT, "results", exp_id)
        os.makedirs(out, exist_ok=True)
        e.trades_df.to_csv(os.path.join(out, "trades.csv"), index=False)
        e.cycles_df.to_csv(os.path.join(out, "cycles.csv"), index=False)
        e.lane_cycles_df.to_csv(os.path.join(out, "lane_cycles.csv"), index=False)
        e.open_df.to_csv(os.path.join(out, "open_inventory.csv"), index=False)
        st = e.state
        day = pd.DatetimeIndex(st.dt).normalize()
        daily = st.groupby(day).agg(equity=("equity", "last"), equity_min_close=("equity", "min"),
                                    equity_min_low=("equity_low", "min"), realized=("realized_net", "last"),
                                    unrealized=("unrealized", "last"), qty_end=("qty", "last"), qty_max=("qty", "max"),
                                    raw_c=("raw_c", "last"))
        daily.to_csv(os.path.join(out, "daily_mtm.csv"))
        json.dump(m, open(os.path.join(out, "metrics.json"), "w"), indent=1, default=str)
    return e, m

if __name__ == "__main__":
    e, m = run("BASE_A_001", BasketGrid(32, 5.0, 25.0))
    print(json.dumps({k: v for k, v in m.items() if k not in ("open_inventory",)}, indent=1, default=str)[:9000])
