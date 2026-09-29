"""RUN-3 Phase 6 (substitute): frozen FQ candidates run ONCE on YM (never used in discovery).
Cross-MARKET robustness only; SAME calendar period as ES -> NOT temporal out-of-sample, NOT MES validation.
Pre-registered transform: price_es_equiv = round_to_0.25(YM_price / k), k = median(YM raw close)/median(ES raw close)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
import run3_lib as rl
from mesgrid.data import bars_from_frame, load_canonical
from mesgrid.features import compute_features
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy

ROOT = rl.ROOT
FZ = json.load(open(os.path.join(ROOT, "FROZEN_CANDIDATES.json")))
ym = pd.read_parquet(os.path.join(ROOT, "data", "external", "canonical_1m_YM.parquet"),
                     columns=["dt", "o", "h", "l", "c", "v", "cum_adjustment", "contract"])
es = pd.read_parquet(os.path.join(ROOT, "data", "canonical", "canonical_1m_ES.parquet"), columns=["c", "cum_adjustment"])
k = float(np.median(ym.c - ym.cum_adjustment) / np.median(es.c - es.cum_adjustment))
q = lambda x: np.round(x / k * 4) / 4  # noqa: E731
for col in ("o", "h", "l", "c", "cum_adjustment"):
    ym[col] = q(ym[col])
b = bars_from_frame(ym)
F = compute_features(b, b.v)
rl._B, rl._F = b, F
rows = []
cands = {n: v["cfg"] for n, v in FZ["candidates"].items()}
cands["BASE (reference)"] = {}
for n, cfg in cands.items():
    r = rl.run_cfg((n, cfg, {}, True, None))
    r["market"] = "YM (ES-equivalent points, k=%.4f)" % k
    rows.append(r)
    print(n, "done", flush=True)
df = pd.DataFrame(rows)
os.makedirs(os.path.join(ROOT, "results", "RUN3_P6_YM"), exist_ok=True)
df.to_csv(os.path.join(ROOT, "results", "RUN3_P6_YM", "summary.csv"), index=False)
print("k =", k)
c = ["name", "total_mtm", "max_mtm_dd", "min_equity", "worst_fresh_min_equity", "fs2022_min_equity", "no_entry_days", "active_share",
     "trades_day", "rec_pnl", "wk_mean", "underwater_days"]
print(df[c].round(1).to_string(index=False))
