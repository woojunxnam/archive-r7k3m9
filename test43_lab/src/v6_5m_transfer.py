"""V6 finalist checks: 5m timeframe robustness (no re-optimisation) and ES<->MNQ transfer. DEV+VAL only."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments, lab, v6lab  # noqa: E402

PER = ("DEV", "VAL", "DV", "F2")
SL = json.load(open("../out/v6/shortlist.json"))


def atr_dollar(inst):
    b, f = v6lab.load(inst)
    pv = instruments.PROFILES[v6lab.PROF[inst]]["point_value"]
    m = (b.session_date <= lab.DEV_END).values
    return float(np.nanmedian(f["d_ATR20"][m]) * pv)


def scale_caps(p, ratio):
    q = dict(p)
    for k in ("capRTH", "capON"):
        if k in q:
            q[k] = max(1, int(round(q[k] * ratio)))
    return q


rows = []
ratio_es_to_mnq = atr_dollar("ES") / atr_dollar("MNQ")
print("ATR$ ES", atr_dollar("ES"), "MNQ", atr_dollar("MNQ"), "ratio ES->MNQ caps x", round(ratio_es_to_mnq, 3))
for c in SL:
    if c["arch"] in ("B", "G"):
        rows.append({"id": c["id"], "test": "5m/transfer", "note": "v6x lane: bar-count internals are 3m-specific; not transferable without re-spec"})
        continue
    p = c["params"]
    base = v6lab.evaluate(c["inst"], p, periods=PER, mb=True)
    rows.append({"id": c["id"], "test": "BASE_3m", **{k: base[k] for k in base if k.startswith(PER) or k in ("fills",)}})
    q = dict(p); q["lastBarMod"] = 955
    for k in ("cooldownBars", "dipMaxBars"):
        if k in q:
            q[k] = int(round(q[k] * 3 / 5))
    o = v6lab.evaluate(c["inst"] + "5", q, periods=PER, mb=True)
    rows.append({"id": c["id"], "test": "TF_5m", **{k: o[k] for k in o if k.startswith(PER) or k in ("fills",)}})
    other = "MNQ" if c["inst"] == "ES" else "ES"
    r = ratio_es_to_mnq if c["inst"] == "ES" else 1 / ratio_es_to_mnq
    o = v6lab.evaluate(other, scale_caps(p, r), periods=PER, mb=True)
    rows.append({"id": c["id"], "test": f"TRANSFER_TO_{other}", **{k: o[k] for k in o if k.startswith(PER) or k in ("fills",)}})
df = pd.DataFrame(rows)
df.to_csv("../out/v6/tf5m_transfer.csv", index=False)
pd.set_option("display.width", 250)
print(df[["id", "test", "DEV_avg_daily", "DEV_excess_vs_mb", "DEV_max_dd", "VAL_avg_daily", "VAL_excess_vs_mb", "VAL_max_dd", "F2_avg_daily", "DV_avg_mes", "fills"]].round(1).to_string())
