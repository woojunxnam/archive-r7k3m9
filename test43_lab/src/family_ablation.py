"""Feature-family ablation by removal for V6A candidates (DEV+VAL only)."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import v6lab  # noqa: E402

PER = ("DEV", "VAL", "DV", "F2", "Y2022")
FAMILIES = {
    "REGIME_TIERS": dict(fBear=1.0, fNeut=1.0, fMed=1.0, fStrong=1.0),
    "TREND_MULT": dict(trendMult=1.0),
    "DD_GOVERNOR": dict(dd1=0.0, dd2=0.0, dd3=0.0),
    "SESSION_RISK_CUTS": dict(dayStop=0.0, gapK=0.0, shockK=0.0),
    "OVERNIGHT_MODE->FULL": dict(onMode=4),
    "OVERNIGHT_MODE->FLAT": dict(onMode=0),
    "VOL_TARGET": dict(volBudget=0.0, volBudgetON=0.0),
    "DIP_BOOST": dict(dipOn=0),
    "UPPER_REDUCTION": dict(redOn=0),
    "TURNOVER_SUPPRESSORS": dict(minDelta=1, cooldownBars=0),
    "BUY_WINDOW": dict(buyStartMod=570, buyEndMod=954),
}


def main(cands_json, out):
    cands = json.load(open(cands_json))
    rows = []
    for c in cands:
        base = v6lab.evaluate(c["inst"], c["params"], periods=PER, mb=True)
        rows.append({"id": c["id"], "family_removed": "NONE(BASE)", **base})
        for fam, over in FAMILIES.items():
            q = dict(c["params"]); q.update(over)
            if q == c["params"]:
                continue
            o = v6lab.evaluate(c["inst"], q, periods=PER, mb=True)
            rows.append({"id": c["id"], "family_removed": fam, **o})
    df = pd.DataFrame(rows)
    keys = ["DEV_avg_daily", "DEV_max_dd", "DEV_worst_day", "VAL_avg_daily", "VAL_max_dd", "DV_excess_vs_mb", "DV_avg_mes",
            "F2_max_dd", "Y2022_total", "friction", "fills"]
    for k in keys:
        df["d_" + k] = df[k] - df.groupby("id")[k].transform("first")
    df.to_csv(out, index=False)
    pd.set_option("display.width", 250)
    print(df[["id", "family_removed"] + ["d_" + k for k in keys]].round(1).to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
