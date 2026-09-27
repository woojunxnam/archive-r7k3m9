"""Finalist robustness: parameter neighbours (plateau), cost stress, entry delay, margin stress, remove-top days,
rolling windows, vol/trend regimes, time-of-day attribution.  DEV+VAL only (holdout excluded).
Usage: python robustness.py FINALISTS.json OUTDIR
FINALISTS.json: [{"id":..., "inst":..., "arch":..., "params":{...}}, ...]
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import decomp, instruments, lab, v6lab  # noqa: E402
import optimize_v6_G as G  # noqa: E402

PER = ("DEV", "VAL", "DV", "F1", "F2", "F3", "PRE23", "P23", "Y2020", "Y2022")
_setup = {}


def run(inst, arch, p):
    if arch in ("B", "G"):
        if inst not in _setup:
            _setup[inst] = G.setup(inst, lab.VAL_END)
        b, a = _setup[inst]
        o, res, d = G.evaluate_v6x(inst, b, a, p, PER, lab.VAL_END)
    else:
        o, res, d = v6lab.evaluate(inst, p, periods=PER, keep=True, mb=True)
        b, _ = v6lab.load(inst)
    return o, res, d, b


NUMERIC_SKIP = {"pointValue", "commission", "rollCost", "rollCostPerContract", "mIntraFrac", "mOnFrac", "tickSize",
                "disableMask", "onMode", "overnightMode", "coreTierMode", "tacticalMode", "coreBuildMode", "dipOn", "redOn",
                "dipNeedRev", "decayMode", "profitRefMode", "buyStartMod", "buyEndMod", "lastBarMod", "delayBars", "marginU",
                "slipTicks", "slippageTicks"}


def neighbours(p):
    out = []
    for k, v in p.items():
        if k in NUMERIC_SKIP or not isinstance(v, (int, float)) or v == 0:
            continue
        for f in (0.8, 0.9, 1.1, 1.2):
            q = dict(p)
            if isinstance(v, int) and not isinstance(v, bool):
                nv = int(round(v * f))
                if nv == v:
                    nv = v + (1 if f > 1 else -1)
                q[k] = max(nv, 0)
            else:
                q[k] = v * f
            out.append((f"{k}x{f}", q))
    return out


def main(fin_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    fins = json.load(open(fin_path))
    allrows = []
    for fin in fins:
        inst, arch, p = fin["inst"], fin["arch"], fin["params"]
        pv = instruments.PROFILES[G.PROF[inst]]["point_value"]
        slipk = "slippageTicks" if arch in ("B", "G") else "slipTicks"
        commk = "commission"
        base, res, d, b = run(inst, arch, p)
        rows = [{"id": fin["id"], "test": "BASE", **base}]
        for lab_, q in [("SLIP2", {**p, slipk: 2}), ("SLIP4", {**p, slipk: 4}), ("COMM1.00", {**p, commk: 1.00}),
                        ("COMM0.61", {**p, commk: 0.61})]:
            o, *_ = run(inst, arch, q); rows.append({"id": fin["id"], "test": lab_, **o})
        if arch not in ("B", "G"):
            o, *_ = run(inst, arch, {**p, "delayBars": 1}); rows.append({"id": fin["id"], "test": "DELAY+1", **o})
            mi = instruments.margin_frac(instruments.PROFILES[G.PROF[inst]], "intraday")
            mo = instruments.margin_frac(instruments.PROFILES[G.PROF[inst]], "overnight")
            o, *_ = run(inst, arch, {**p, "mIntraFrac": mi * 1.5, "mOnFrac": mo * 1.5}); rows.append({"id": fin["id"], "test": "MARGINx1.5", **o})
            o, *_ = run(inst, arch, {**p, "mOnFrac": mo * 2.0}); rows.append({"id": fin["id"], "test": "ON_MARGINx2", **o})
        nb = neighbours(p)
        for name, q in nb:
            o, *_ = run(inst, arch, q); rows.append({"id": fin["id"], "test": "NB_" + name, **o})
        df = pd.DataFrame(rows)
        nbd = df[df.test.str.startswith("NB_")]
        summ = {"id": fin["id"], "inst": inst, "arch": arch, "n_neighbours": len(nbd),
                "base_DEV": base["DEV_avg_daily"], "nb_DEV_median": nbd.DEV_avg_daily.median(), "nb_DEV_p10": nbd.DEV_avg_daily.quantile(0.1),
                "base_VAL": base["VAL_avg_daily"], "nb_VAL_median": nbd.VAL_avg_daily.median(), "nb_VAL_p10": nbd.VAL_avg_daily.quantile(0.1),
                "nb_DEVdd_p90": nbd.DEV_max_dd.quantile(0.9), "nb_share_DEV_ge_80pct": float((nbd.DEV_avg_daily >= 0.8 * base["DEV_avg_daily"]).mean())}
        # remove-top days, rolling windows, regimes, time of day
        dv = d[d.index <= lab.VAL_END]
        pn = dv.pnl.sort_values(ascending=False)
        for k in (1, 3, 5):
            summ[f"DV_avg_ex_top{k}"] = float((dv.pnl.sum() - pn.iloc[:k].sum()) / len(dv))
        for w, n in (("3m", 63), ("6m", 126), ("12m", 252)):
            roll = dv.pnl.rolling(n).sum().dropna()
            summ[f"roll{w}_pos_share"] = float((roll > 0).mean()); summ[f"roll{w}_min"] = float(roll.min())
        f = v6lab.load(inst)[1]
        atrp = pd.Series(f["d_ATR20_pct"], index=b.index).groupby(b.session_date.values).first()
        trend = pd.Series(f["d_TREND100"], index=b.index).groupby(b.session_date.values).first()
        dd_ = dv.join(atrp.rename("atrp")).join(trend.rename("tr"))
        summ["hi_vol_avg"] = float(dd_[dd_.atrp >= 0.66].pnl.mean()); summ["lo_vol_avg"] = float(dd_[dd_.atrp <= 0.33].pnl.mean())
        summ["trend_avg"] = float(dd_[dd_.tr == 1].pnl.mean()); summ["range_avg"] = float(dd_[dd_.tr == 0].pnl.mean())
        c = b.c.values; o_ = b.o.values; pos = res["pos"].astype(float)
        prev_c = np.concatenate([[o_[0]], c[:-1]]); pp = np.concatenate([[0.0], pos[:-1]])
        mtm = (pp * (o_ - prev_c) + pos * (c - o_)) * pv
        mod = b["mod"].values; rth = b.in_rth.values
        m = (b.session_date <= lab.VAL_END).values
        summ["tod_morning_0930_1100"] = float(mtm[m & rth & (mod < 660)].sum())
        summ["tod_midday_1100_1400"] = float(mtm[m & rth & (mod >= 660) & (mod < 840)].sum())
        summ["tod_late_1400_1600"] = float(mtm[m & rth & (mod >= 840)].sum())
        summ["overnight_gross"] = float(mtm[m & ~rth].sum())
        for r in rows[1:]:
            if not r["test"].startswith("NB_"):
                summ[f"{r['test']}_DV_avg"] = r["DV_avg_daily"]; summ[f"{r['test']}_DV_dd"] = r["DV_max_dd"]
                summ[f"{r['test']}_breach"] = r.get("margin_breach")
        allrows.append(summ)
        df.to_csv(f"{outdir}/rob_{fin['id']}.csv", index=False)
        print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in summ.items()}))
    pd.DataFrame(allrows).to_csv(f"{outdir}/ROBUSTNESS_SUMMARY.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
