"""RUN-4 step 2: verify engine before new research. Reproduce BASE, C32_mkt, C14_mkt, C14_lmt (RUN-3 finalists)
against RUN3_FINAL/summary.csv and run the per-bar audit + economic reconciliation on C32_mkt."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
import run3_lib as rl
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy
from mesgrid.audit import reconcile

ROOT = rl.ROOT
OUT = os.path.join(ROOT, "results", "RUN4_OVERNIGHT", "verify")
os.makedirs(OUT, exist_ok=True)
FIN = json.load(open(os.path.join(ROOT, "results", "RUN3_FINALISTS.json")))
REF = pd.read_csv(os.path.join(ROOT, "results", "RUN3_FINAL", "summary.csv")).set_index("name")
rl.init()
rows = []
for name in ("BASE", "C32_mkt", "C14_mkt", "C14_lmt"):
    t0 = time.time()
    audit = name in ("C32_mkt", "C14_lmt")
    e = Engine(rl._B, FactoryStrategy(rl._F, **FIN[name]), ExecConfig(), audit=audit).run()
    s = rl.summarize(e)
    r = dict(name=name, runtime_s=time.time() - t0)
    for k in ("total_mtm", "max_mtm_dd", "min_equity", "realized", "unreal_end", "open_qty_end", "fills_total", "cost"):
        r[k] = s[k]; r[k + "_ref"] = REF.loc[name, k]; r[k + "_diff"] = s[k] - REF.loc[name, k]
    if audit:
        rec = reconcile(e)
        r.update({"audit_" + k: v for k, v in rec.items() if not isinstance(v, (list, dict))})
    rows.append(r)
    print(name, round(r["runtime_s"]), "s", {k: round(r[k + "_diff"], 6) for k in ("total_mtm", "max_mtm_dd", "min_equity", "fills_total")}, flush=True)
    del e
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "reproduction.csv"), index=False)
ok = bool((df[[c for c in df.columns if c.endswith("_diff")]].abs() < 1e-6).all().all()) and bool(df.get("audit_all_ok", pd.Series([True])).dropna().all())
json.dump(dict(all_reproduced=ok), open(os.path.join(OUT, "verify.json"), "w"))
print("ALL_REPRODUCED", ok)
