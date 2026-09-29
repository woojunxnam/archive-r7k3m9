"""ROLL_GATE_001: roll-aware accounting gate for Baseline A."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dataclasses import replace
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.engine import Engine, ExecConfig
from mesgrid.strategies import BasketGrid
from mesgrid import metrics
from mesgrid.stress import window_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "ROLL_GATE_001"); os.makedirs(OUT, exist_ok=True)
WINDOWS = {"2020": ("2020-02-01", "2020-08-31"), "2022_23": ("2022-01-01", "2023-12-31"), "2025": ("2025-02-01", "2025-07-31")}
B = load_canonical()
RAW = replace(B, o=B.o - B.adj, h=B.h - B.adj, l=B.l - B.adj, c=B.c - B.adj, adj=np.zeros_like(B.adj))

def win_stats(e, s, t):
    st = e.state; dt = pd.DatetimeIndex(st.dt)
    m = (dt >= s) & (dt <= t); w = st[m]
    k = int(np.argmin(w.unrealized.values)); row = w.iloc[k]
    q = row.qty
    led = e.roll_ledger_df
    lw = led[(pd.DatetimeIndex(led.dt) >= s) & (pd.DatetimeIndex(led.dt) <= t)] if len(led) else led
    after = st[dt > pd.Timestamp(row["dt"])]
    rec = after[after.equity >= st.equity[dt <= pd.Timestamp(row["dt"])].max()]
    wr = window_report(e, s, t)
    return dict(worst_unreal=float(row.unrealized), worst_dt=str(row["dt"])[:16], qty=int(q),
                basket_avg_adj=float(row.sum_px / q) if q else None,
                basket_avg_raw=float(row.raw_basis_sum / q) if q else None,
                raw_price=float(row.raw_c), adj_price=float(row.c),
                realized_broker_minus_logical=float(row.realized_broker - row.realized_net),
                rolls_with_inventory=int(lw.roll_idx.nunique()) if len(lw) else 0,
                roll_cost_in_window=float(lw.cost.sum()) if len(lw) else 0.0,
                roll_leg_pnl_in_window=float(lw.leg_pnl.sum()) if len(lw) else 0.0,
                recovery_dt=str(rec.dt.iloc[0])[:16] if len(rec) else "NOT RECOVERED",
                lock=wr["longest_max_lock_in_window"], window_mtm_dd=wr["mtm_dd_from_prior_peak"])

variants = {
    "V0_prev_BASE_A_001": None,  # from saved metrics
    "V1_roll_basis_adjust": (B, ExecConfig(roll_mode="basis_adjust")),
    "V2_roll_close_reopen": (B, ExecConfig(roll_mode="close_reopen")),
    "V3_roll_2x_slippage": (B, ExecConfig(roll_slippage_ticks=2.0)),
    "V4_naive_raw_no_roll": (RAW, ExecConfig(roll_cost_per_contract=0.0)),
}
rows, detail = [], {}
prev = json.load(open(os.path.join(ROOT, "results", "BASE_A_001", "metrics.json")))
for name, v in variants.items():
    if v is None:
        m = prev; ws = None
    else:
        e = Engine(v[0], BasketGrid(32, 5.0, 25.0), v[1]).run()
        m = metrics.compute(e, name)
        ws = {k: win_stats(e, *w) for k, w in WINDOWS.items()}
        detail[name] = dict(windows=ws, ledger_error=e.max_ledger_error, n_ledger=len(e.roll_ledger),
                            roll_commission=e.roll_commission, roll_slippage=e.roll_slippage,
                            end_realized_broker=float(e.state.realized_broker.iloc[-1]),
                            end_unrealized_broker=float(e.state.unrealized_broker.iloc[-1]))
        if name == "V2_roll_close_reopen":
            e.roll_ledger_df.to_csv(os.path.join(OUT, "roll_ledger_close_reopen.csv.gz"), index=False)
    lk = m["longest_max_lock"][0]
    rows.append(dict(variant=name, net_total_mtm=round(m["total_mtm_pnl"], 2), realized_logical=round(m["realized_net"], 2),
                     unrealized_end=round(m["unrealized_end"], 2),
                     realized_broker_end=round(detail.get(name, {}).get("end_realized_broker", np.nan), 2),
                     max_mtm_dd=round(m["max_mtm_dd"], 2), max_inv=m["inv_max"], longest_32_lock_days=round(lk[0], 2),
                     lock_span=f"{str(lk[1])[:10]}→{str(lk[2])[:10]}", roll_cost=round(m["roll_cost"], 2),
                     cycles=m["cycles_completed"], ledger_err=detail.get(name, {}).get("ledger_error")))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "comparison.csv"), index=False)
json.dump(detail, open(os.path.join(OUT, "detail.json"), "w"), indent=1, default=str)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(df.to_string())
for k in WINDOWS:
    print("\n==", k)
    print(pd.DataFrame({n: d["windows"][k] for n, d in detail.items()}).T.to_string())
