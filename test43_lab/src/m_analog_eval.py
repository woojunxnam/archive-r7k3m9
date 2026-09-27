"""NOTE: a within-session (session-demeaned) IC was tried and REJECTED as a look-ahead artefact: demeaning by the
session mean uses the rest of that session (even raw pos_rth scores -0.30).  Only pooled, control-residual IC is used.

Re-evaluate saved analog predictions (k=50/100): pooled and WITHIN-SESSION information, monthly t, folds,
versus the random-in-context control.  Usage: python m_analog_eval.py INST [END]"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
FOLDS = {"F1": ("2019-01-01", "2020-12-31"), "F2": ("2021-01-01", "2022-12-31"), "F3": ("2023-01-01", "2024-12-31"),
         "VAL": ("2025-01-01", "2025-09-30")}


def mt(x):
    x = x.dropna()
    return (x.mean(), x.mean() / (x.std() / np.sqrt(len(x))), len(x)) if len(x) > 5 else (np.nan, np.nan, len(x))


def ev(P, col, use_conf=True, start=None):
    p = P[f"{col}|pred"].values; d = P.d_ret60.values
    m = ~np.isnan(p) & ~np.isnan(d)
    if use_conf:
        m &= P[f"{col}|conf"].values != "NO_MATCH"
    if start is not None:
        m &= P.sd.values >= np.datetime64(start)
    x = pd.DataFrame({"sd": P.sd.values[m], "p": p[m], "d": d[m]})
    x["mon"] = pd.to_datetime(x.sd).dt.to_period("M")
    r = {"n": len(x)}
    r["IC_pooled"] = spearmanr(x.p, x.d)[0]
    mp = x.groupby("mon").apply(lambda g: spearmanr(g.p, g.d)[0] if len(g) > 30 else np.nan)
    r["IC_pooled_mean"], r["IC_pooled_t"], r["n_months"] = mt(mp)
    for f, (a, b) in FOLDS.items():
        g = x[(x.sd >= np.datetime64(a)) & (x.sd <= np.datetime64(b))]
        if len(g) > 300:
            r[f"{f}_IC_pooled"] = spearmanr(g.p, g.d)[0]
    # economic scale: top-minus-bottom tercile of predictions, mean residual 60m return (ATR units)
    q = pd.qcut(x.p.rank(method="first"), 3, labels=False)
    r["top_minus_bottom_resid_atr"] = x.d[q == 2].mean() - x.d[q == 0].mean()
    if f"{col}|conf" in P:
        for c in ("HIGH", "MED"):
            mm = x.index[(P[f"{col}|conf"].values[m] == c)]
            g = x.loc[mm]
            if len(g) > 30:
                r[f"{c}_n"] = len(g); r[f"{c}_signed_resid"] = float((np.sign(g.p) * g.d).mean())
    return r


def main(inst, end="DEV"):
    P = pd.read_parquet(f"{OUT}/{inst}_{end}/analog_preds.parquet")
    cols = sorted({c.rsplit("|", 1)[0] for c in P.columns if c.endswith("|pred")})
    rows = []
    for col in cols:
        rnd = col.startswith("RANDOM")
        r = {"inst": inst, "end": end, "config": col.split("|")[0], "k": col.split("|")[1]}
        r.update(ev(P, col, use_conf=not rnd, start="2025-01-01" if end == "VAL" else None))
        rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/tables/M09_analog_eval__{inst}_{end}.csv", index=False)
    pd.set_option("display.width", 250)
    print(df[["config", "k", "n", "IC_pooled", "IC_pooled_t", "F1_IC_pooled", "F2_IC_pooled", "F3_IC_pooled",
              "top_minus_bottom_resid_atr"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "DEV")
