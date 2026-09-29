"""RUN-3 Phase 1: explicit roll reconciliation."""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIN = json.load(open(os.path.join(ROOT, "results", "FINALISTS.json")))
W = {"2020": ("2020-02-01", "2020-08-31"), "2022_23": ("2022-01-01", "2023-12-31"), "2025": ("2025-02-01", "2025-07-31")}


def job(a):
    name, slip = a
    b = load_canonical(); F = compute_features(b, b.v)
    e = Engine(b, FactoryStrategy(F, **FIN[name]), ExecConfig(roll_slippage_ticks=slip)).run()
    led = e.roll_ledger_df
    net = float(e.state.equity.iloc[-1] - 150000)
    row = dict(candidate=name, roll_slip_ticks=slip, net_roll_aware_pnl=net, roll_commission=e.roll_commission,
               roll_slippage=e.roll_slippage, roll_cost_total=e.roll_cost,
               gross_before_roll_costs=net + e.roll_cost, roll_events_total=int(len(set(led.roll_idx))) if len(led) else 0,
               contracts_rolled=int(led.qty.sum()) if len(led) else 0,
               avg_cost_per_contract=e.roll_cost / max(led.qty.sum(), 1) if len(led) else 0.0)
    for k, (s, t) in W.items():
        lw = led[(pd.DatetimeIndex(led.dt) >= s) & (pd.DatetimeIndex(led.dt) <= t)] if len(led) else led
        row[f"{k}_rolls"] = int(lw.roll_idx.nunique()) if len(lw) else 0
        row[f"{k}_contracts"] = int(lw.qty.sum()) if len(lw) else 0
        row[f"{k}_roll_cost"] = float(lw.cost.sum()) if len(lw) else 0.0
    return row


if __name__ == "__main__":
    jobs = [(n, s) for n in ("BASE", "FQ_12_20", "FQ_16_16", "FQ_16_16_add") for s in (1.0, 2.0)]
    with Pool(4) as p:
        rows = p.map(job, jobs)
    df = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "results", "RUN3_P1_ROLL"), exist_ok=True)
    df.to_csv(os.path.join(ROOT, "results", "RUN3_P1_ROLL", "roll_reconciliation.csv"), index=False)
    pd.set_option("display.width", 250)
    print(df.round(2).T.to_string())
