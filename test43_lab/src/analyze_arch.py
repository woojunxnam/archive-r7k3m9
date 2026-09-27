"""Summarise architecture-ablation lanes: DEV best, VAL of DEV-best, top-10 VAL median."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import v6lab  # noqa: E402

IN = sys.argv[1] if len(sys.argv) > 1 else "../out/v6/arch"
rows = []
for f in sorted(glob.glob(f"{IN}/*_*_*.csv")):
    d = pd.read_csv(f)
    if "feasible" not in d or d.empty:
        continue
    inst, arch, env = d.inst.iloc[0], d.arch.iloc[0], d.env.iloc[0]
    fe = d[d.feasible].sort_values("score", ascending=False)
    if fe.empty:
        rows.append({"inst": inst, "arch": arch, "env": env, "trials": len(d), "feasible": 0})
        continue
    top = fe.head(10)
    evals = [v6lab.evaluate(inst, json.loads(p)) for p in top.params]
    b = evals[0]
    fb = fe.sort_values("trial").score.cummax()
    rows.append({
        "inst": inst, "arch": arch, "env": env, "trials": len(d), "feasible": len(fe),
        "best_score": fe.score.iloc[0],
        "DEV_avg": b["DEV_avg_daily"], "DEV_ex5": b["DEV_avg_ex_top5"], "DEV_dd": b["DEV_max_dd"], "DEV_worst": b["DEV_worst_day"],
        "VAL_avg": b["VAL_avg_daily"], "VAL_dd": b["VAL_max_dd"], "VAL_worst": b["VAL_worst_day"], "VAL_env": b["VAL_env"],
        "PRE23_avg": b["PRE23_avg_daily"], "P23_avg": b["P23_avg_daily"], "Y2022": b["Y2022_total"],
        "avg_mes": b["DV_avg_mes"], "avg_on": b["DV_avg_on_mes"], "max_mes": b["DV_max_mes"], "fills": b["fills"],
        "friction": b["friction"], "margin_util": b["peak_margin_util"],
        "top10_VAL_median": float(np.median([e["VAL_avg_daily"] for e in evals])),
        "top10_DEV_median": float(np.median([e["DEV_avg_daily"] for e in evals])),
        "best_at_n-500": float(fb.iloc[max(0, len(fb) - 500)] if len(fb) > 500 else np.nan),
    })
out = pd.DataFrame(rows).sort_values(["inst", "env", "arch"])
out.to_csv(f"{IN}/SUMMARY.csv", index=False)
pd.set_option("display.width", 250)
print(out.round(1).to_string())
