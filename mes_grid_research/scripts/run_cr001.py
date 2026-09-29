"""CR_001: Core/Recycle architecture screen (R1 profit-only), pre-registered in EXPERIMENT_REGISTRY.
Control 32/0 vs {24/8, 20/12, 16/16} x rec_tp {2.5,3,4,5} x activation {always, core_full}; rec_step=5."""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.engine import Engine, ExecConfig
from mesgrid.strategies import CoreRecycle
from mesgrid import metrics, ENGINE_VERSION, EXEC_SPEC_VERSION, DATASET_SHA256
from mesgrid.stress import window_report, top_drawdowns, REGRESSION_WINDOW

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = sys.argv[1] if len(sys.argv) > 1 else "CR_001"
OUT = os.path.join(ROOT, "results", EXP)
_B = None

def init():
    global _B
    _B = load_canonical()

def summarize(name, e, m, w25, w22):
    L = m["lanes"]
    rec = L.get("rec", {})
    lock = m["longest_max_lock"][0] if m["longest_max_lock"] else (0, "", "", "")
    core_full = L["core"]["longest_full"][0] if L["core"]["longest_full"] else (0, "", "", "")
    return dict(config=name, realized=m["realized_net"], unreal_end=m["unrealized_end"], total_mtm=m["total_mtm_pnl"],
                max_mtm_dd=m["max_mtm_dd"], max_dd_peak=m["max_mtm_dd_peak"][:10], worst_cycle=m["worst_cycle_mtm"][0],
                min_equity=m["min_equity"], pf=m["profit_factor"], trades=m["trades"], trades_day=m["trades_per_day"],
                cost=m["total_cost"], inv_avg=m["inv_avg_rth"], share32=m["inv_share_rth_ge"][32], share24=m["inv_share_rth_ge"][24],
                lock32_days=lock[0], lock32_span=f"{lock[1][:10]}→{lock[2][:10]}", core_full_days=core_full[0],
                core_full_share=L["core"]["full_share_rth"], rec_trades_day=rec.get("trades_per_day", 0),
                rec_pnl=rec.get("pnl_net", 0), rec_win=rec.get("win_rate"), rec_full_share=rec.get("full_share_rth"),
                rec_longest_full=(rec.get("longest_full") or [(0,)])[0][0], rec_hold_med_min=rec.get("median_hold_min"),
                w25_share32=w25["share_rth_at_max"], w25_trades=w25["sells"], w25_rec_trades=w25["lanes"].get("rec", {}).get("trades", 0),
                w25_dd=w25["mtm_dd_from_prior_peak"], w25_lock=(w25["longest_max_lock_in_window"] or (0,))[0],
                w22_share32=w22["share_rth_at_max"], w22_trades=w22["sells"], w22_rec_trades=w22["lanes"].get("rec", {}).get("trades", 0),
                w22_dd=w22["mtm_dd_from_prior_peak"], open_qty_end=m["open_qty_end"], margin_excess_2500=m["margin_stress"][2500]["min_excess_liquidity"])

def job(args):
    name, kw = args
    strat = CoreRecycle(**kw)
    e = Engine(_B, strat, ExecConfig()).run()
    m = metrics.compute(e, name)
    w25 = window_report(e, *REGRESSION_WINDOW)
    w22 = window_report(e, "2022-01-01", "2023-12-31")
    m["lineage"] = dict(exp_id=EXP, config=name, dataset_sha256=DATASET_SHA256, engine_version=ENGINE_VERSION,
                        exec_spec=EXEC_SPEC_VERSION, params=strat.params, exec_cfg=ExecConfig().__dict__)
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    json.dump(dict(metrics=m, regression_2025=w25, window_2022_23=w22, top10_dd=top_drawdowns(e, 10)),
              open(os.path.join(d, "metrics.json"), "w"), indent=1, default=str)
    e.trades_df.to_csv(os.path.join(d, "trades.csv.gz"), index=False)
    return summarize(name, e, m, w25, w22)

def configs():
    yield "C32_0", dict(core_cap=32, rec_cap=0)
    for cc, rc in ((24, 8), (20, 12), (16, 16)):
        for tp in (2.5, 3.0, 4.0, 5.0):
            for act in ("always", "core_full"):
                yield f"C{cc}_{rc}_tp{tp}_{act}", dict(core_cap=cc, rec_cap=rc, rec_tp=tp, activation=act, rec_step=5.0)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    with Pool(4, initializer=init) as p:
        rows = p.map(job, list(configs()))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
    print(df.round(3).to_string())
