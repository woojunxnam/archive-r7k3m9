"""FACTORY_S5 (temporal/regime robustness) and FACTORY_S6 (execution/cost stress) for finalists.
Finalists are read from results/FINALISTS.json: {name: cfg}."""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import factory_lib as fl
from factory_lib import ROOT, run_batch
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy
from mesgrid import metrics
from mesgrid.stress import top_drawdowns

EXEC_VARIANTS = {
    "base": {},
    "slip2": dict(slippage_ticks=2),
    "slip4": dict(slippage_ticks=4),
    "comm+25": dict(commission_per_side=0.62 * 1.25),
    "comm+50": dict(commission_per_side=0.62 * 1.5),
    "pen2": dict(penetration_ticks=2),
    "roll2x": dict(roll_slippage_ticks=2.0),
    "neutral": dict(penetration_ticks=0),
    "tv_like": dict(penetration_ticks=0, allow_same_bar_tp_after_intrabar_buy=True, slippage_ticks=0),
    "stress_all": dict(slippage_ticks=2, commission_per_side=0.62 * 1.5, penetration_ticks=2, roll_slippage_ticks=2.0),
}


def finalists():
    return json.load(open(os.path.join(ROOT, "results", "FINALISTS.json")))


def temporal_job(args):
    name, cfg = args
    e = Engine(fl._B, FactoryStrategy(fl._F, **cfg), ExecConfig()).run()
    st = e.state
    day = pd.DatetimeIndex(st.dt).normalize()
    daily = st.groupby(day).agg(equity=("equity", "last"), qty=("qty", "max"), realized=("realized_net", "last"),
                                unrealized=("unrealized", "last"))
    d = os.path.join(ROOT, "results", "FACTORY_S5", name)
    os.makedirs(d, exist_ok=True)
    daily.to_csv(os.path.join(d, "daily.csv"))
    eq = daily.equity
    y = eq.groupby(eq.index.year).last()
    ych = y.diff().fillna(y.iloc[0] - 150000.0)
    r12 = (eq - eq.shift(252)).dropna()
    # rolling 12m max drawdown (on daily closes)
    dd12 = []
    vals = eq.values
    for k in range(252, len(vals), 21):
        seg = vals[k - 252:k]
        dd12.append((seg - np.maximum.accumulate(seg)).min())
    row = dict(name=name, **{f"y{k}": float(v) for k, v in ych.items()},
               pos_years=int((ych > 0).sum()), worst_year=float(ych.min()),
               roll12_min=float(r12.min()), roll12_share_pos=float((r12 > 0).mean()),
               roll12_worst_dd=float(min(dd12)), roll12_median_dd=float(np.median(dd12)))
    td = top_drawdowns(e, 10)
    json.dump(dict(top10_dd=td, annual=ych.to_dict()), open(os.path.join(d, "temporal.json"), "w"), indent=1, default=str)
    row["top10_dd_sum"] = float(sum(x["depth"] for x in td))
    row["top10_worst_days_underwater"] = int(max(x["days_underwater"] for x in td))
    return row


def fresh_job(args):
    name, cfg, start = args
    b = fl._BF[start]
    F = fl._FF[start]
    e = Engine(b, FactoryStrategy(F, **cfg), ExecConfig()).run()
    m = metrics.compute(e)
    lk = m["longest_max_lock"][0][0] if m["longest_max_lock"] else 0.0
    return dict(name=name, start=start, total_mtm=m["total_mtm_pnl"], realized=m["realized_net"], unreal_end=m["unrealized_end"],
                open_qty_end=m["open_qty_end"], max_mtm_dd=m["max_mtm_dd"], min_equity=m["min_equity"], lock32=lk,
                gt24=m["longest_gt24"][0][0] if m["longest_gt24"] else 0.0, trades_day=m["trades_per_day"])


def init_fresh(starts):
    fl.init()
    from mesgrid.data import load_canonical
    from mesgrid.features import compute_features
    fl._BF, fl._FF = {}, {}
    for s in starts:
        b = load_canonical(start=s)
        fl._BF[s] = b
        fl._FF[s] = compute_features(b, b.v)


if __name__ == "__main__":
    what = sys.argv[1]
    fin = finalists()
    if what == "s5":
        starts = ["2022-01-01", "2023-01-01", "2025-01-01"]
        with Pool(4, initializer=init_fresh, initargs=(starts,)) as p:
            rows = p.map(temporal_job, list(fin.items()))
            fr = p.map(fresh_job, [(n, c, s) for n, c in fin.items() for s in starts])
        pd.DataFrame(rows).to_csv(os.path.join(ROOT, "results", "FACTORY_S5", "temporal.csv"), index=False)
        pd.DataFrame(fr).to_csv(os.path.join(ROOT, "results", "FACTORY_S5", "fresh_starts.csv"), index=False)
        print(pd.DataFrame(rows).round(0).to_string()); print(pd.DataFrame(fr).round(0).to_string())
    elif what == "s6":
        jobs = [(f"{n}__{v}", "S6", n, n, c, ex, False) for n, c in fin.items() for v, ex in EXEC_VARIANTS.items()]
        run_batch("FACTORY_S6", jobs, procs=4)
