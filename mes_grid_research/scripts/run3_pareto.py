"""RUN-3 Phase 7 compact Pareto (no composite score). Non-dominated on (total MTM up, worst fresh min equity up,
longest no-entry down) at base execution; other metrics shown alongside. ES-signal / MES-economics proxy backtest."""
import json, os
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(os.path.join(ROOT, "results", "RUN3_FINAL", "summary.csv")).set_index("name")
base = [n for n in d.index if "__" not in n]
rows = []
for n in base:
    s = d.loc[n]; s2 = d.loc[f"{n}__slip2"]; s3 = d.loc[f"{n}__slip3"]
    cfg = json.loads(s.cfg)
    fresh_ne = max(s[f"fs{y}_no_entry_days"] for y in ("2020", "2022", "2025"))
    rows.append({"Candidate": n, "Max contracts": int(s.contract_cap),
                 "Split core/rec": f"{cfg.get('core_cap', 32)}/{cfg.get('rec_cap', 0)}" if "rec_cap" in cfg else "32/0",
                 "Total MTM": s.total_mtm, "Max DD": s.max_mtm_dd, "Min equity": s.min_equity,
                 "Worst fresh min equity": s.worst_fresh_min_equity, "Longest no-entry (full)": s.no_entry_days,
                 "Longest no-entry (fresh)": fresh_ne, "Longest underwater": s.underwater_days,
                 "Trades/day": s.trades_day, "Activity %": 100 * s.active_share,
                 "Recycle P&L": s.get("rec_pnl", np.nan), "Rec trades/day": s.get("rec_trades_day", np.nan),
                 "Total costs": s.cost, "Peak notional": s.peak_notional, "Wk mean": s.wk_mean,
                 "2t P&L": s2.total_mtm, "2t DD": s2.max_mtm_dd, "2t worst fresh": s2.worst_fresh_min_equity,
                 "3t P&L": s3.total_mtm, "3t DD": s3.max_mtm_dd, "3t worst fresh": s3.worst_fresh_min_equity,
                 "Unseen-data status": "NOT DONE (no post-2026-05-27 ES / MES); YM same-period cross-market only" if n in ("BASE", "C32_mkt", "C14_mkt", "C10_mkt") else "NOT DONE"})
P = pd.DataFrame(rows)
x = P[["Total MTM", "Worst fresh min equity"]].values; ne = P["Longest no-entry (fresh)"].values
dom = np.zeros(len(P), bool)
for i in range(len(P)):
    for j in range(len(P)):
        if i != j and x[j, 0] >= x[i, 0] and x[j, 1] >= x[i, 1] and ne[j] <= ne[i] and (x[j, 0] > x[i, 0] or x[j, 1] > x[i, 1] or ne[j] < ne[i]):
            dom[i] = True
P["Pareto (MTM, fresh depth, no-entry)"] = ~dom
P["Tier worst fresh"] = pd.cut(P["Worst fresh min equity"], [-1e9, 75e3, 90e3, 105e3, 120e3, 1e9], labels=["<75k", "75-90k", "90-105k", "105-120k", ">=120k"])
P.to_csv(os.path.join(ROOT, "PARETO_RUN3.csv"), index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print(P.drop(columns=["Unseen-data status"]).round(1).to_string(index=False))
