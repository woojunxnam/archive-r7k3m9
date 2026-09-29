"""TradingView parity diagnostics for Baseline A.
Variants: price basis (adjusted vs unadjusted raw continuous) x fill model x start date."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from dataclasses import replace
from mesgrid.data import load_canonical, Bars
from mesgrid.engine import Engine, ExecConfig
from mesgrid.strategies import BasketGrid
from mesgrid import metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def to_raw(b: Bars) -> Bars:
    a = b.adj
    return replace(b, o=b.o - a, h=b.h - a, l=b.l - a, c=b.c - a, adj=np.zeros_like(a))

def slice_bars(b: Bars, start):
    k = np.searchsorted(b.dt, np.datetime64(pd.Timestamp(start)))
    return replace(b, **{f: getattr(b, f)[k:] for f in ("dt", "o", "h", "l", "c", "adj", "contract", "day", "minute", "in_window", "tradeable")})

def lock_2025(m):
    for d, s, e, _ in m["longest_max_lock"]:
        if s.startswith("2025"):
            return f"{s[:10]}→{e[:10]} ({d:.0f}d)"
    return "none(top5)"

CONS = ExecConfig()
TVL = ExecConfig(penetration_ticks=0, allow_same_bar_tp_after_intrabar_buy=True, roll_cost_per_contract=0.0)
rows = []
full = load_canonical()
raw = to_raw(full)
for basis, B in (("adjusted", full), ("unadjusted", raw)):
    for start in ("2019-05-05", "2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"):
        for fm, cfg in (("conservative", CONS if basis == "adjusted" else replace(CONS, roll_cost_per_contract=0.0)), ("tv_like", TVL)):
            if fm == "tv_like" and start not in ("2019-05-05", "2023-01-01"):
                continue
            bb = slice_bars(B, start) if start != "2019-05-05" else B
            e = Engine(bb, BasketGrid(32, 5.0, 25.0), cfg).run()
            m = metrics.compute(e)
            c = e.cycles_df
            locks = [x for x in m["longest_max_lock"]]
            rows.append(dict(basis=basis, start=start, fill=fm, cycles=len(c), entries=m["entries"],
                             realized=round(m["realized_net"]), unreal_end=round(m["unrealized_end"]),
                             open_end=m["open_qty_end"], worst_cycle=round(m["worst_cycle_mtm"][0]),
                             max_mtm_dd=round(m["max_mtm_dd"]), lock2025=lock_2025(m),
                             longest_lock=f"{locks[0][1][:10]}→{locks[0][2][:10]} ({locks[0][0]:.0f}d)" if locks else "",
                             profitable_cycles=float((c.realized > 0).mean()) if len(c) else None))
            print(rows[-1], flush=True)
df = pd.DataFrame(rows)
os.makedirs(os.path.join(ROOT, "results", "PARITY_001"), exist_ok=True)
df.to_csv(os.path.join(ROOT, "results", "PARITY_001", "parity_matrix.csv"), index=False)
print(df.to_string())
