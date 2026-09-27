"""TEST43-M Part 18: ONE-TIME VAL confirmation of the frozen DEV candidates (information level).
Reads out/m/frozen/TEST43M_FROZEN_MECHANISMS.json (hash-checked) and the VAL builds; no parameter is changed."""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import m_info as MI  # noqa: E402
from t43.mstats import cr_mean_t  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
FZ = f"{OUT}/frozen/TEST43M_FROZEN_MECHANISMS.json"
VAL0 = pd.Timestamp("2025-01-01")


def main():
    h = hashlib.sha256(open(FZ, "rb").read()).hexdigest()
    assert h == open(f"{OUT}/frozen/TEST43M_FROZEN_MECHANISMS.sha256").read().split()[0], "frozen file changed"
    fz = json.load(open(FZ))
    rows = []
    for inst in ("ES", "MNQ"):
        dev_mech = pd.read_csv(f"{OUT}/tables/M04_M05_mechanism_info__{inst}.csv")
        dev_nest = pd.read_csv(f"{OUT}/tables/M03_nested_alignment__{inst}.csv")
        dev_bal = pd.read_csv(f"{OUT}/tables/M02_balance_state_info__{inst}.csv")
        df = pd.read_parquet(f"{OUT}/{inst}_VAL/bars.parquet")
        ev = pd.read_parquet(f"{OUT}/{inst}_VAL/events.parquet")
        v = df.sd >= VAL0
        dfv = df[v]                                   # control cells from the VAL era only (same method as DEV)
        et = MI.event_table(inst, df, ev)
        et = et[et.sd >= VAL0]
        et = pd.concat([MI.attach_control(g.drop(columns=[c for c in g.columns if c.startswith(("c_", "d_"))]), dfv,
                                          MI.ctl_keys(hz)) for hz, g in et.groupby("hz")])
        for c in fz["information_candidates"]:
            if inst not in c["insts"]:
                continue
            r = {"id": c["id"], "inst": inst, "hz": c["hz"], "what": c.get("ev", c.get("state")), "metric": c["metric"],
                 "expected_sign": c["sign"]}
            if "state" in c:
                keys = MI.ctl_keys(c["hz"])
                x = MI.attach_control(dfv[["sd"] + keys + MI.OUTC + [f"comp_{c['hz']}"]].copy(), dfv, keys)
                x = x[dfv.rth.values & x[f"comp_{c['hz']}"].values]
                r["VAL_n"] = len(x); r["VAL_mean"], r["VAL_t"], _ = cr_mean_t(x.d_frange60.values, x.sd.values)
                d0 = dev_bal[(dev_bal.hz == c["hz"]) & (dev_bal.state == c["state"])].iloc[0]
                r["DEV_mean"], r["DEV_t"] = d0.mean_d_frange60, d0.t_d_frange60
            elif "align" in c:
                g = et[(et.hz == c["hz"]) & (et.ev == c["ev"])]
                a = g[g["align"] == c["align"]]; b = g[g["align"] != c["align"]]
                ma, ta, _ = cr_mean_t(a.d_ret60.values, a.sd.values); mb, tb, _ = cr_mean_t(b.d_ret60.values, b.sd.values)
                se = np.sqrt((ma / ta) ** 2 + (mb / tb) ** 2) if ta and tb and not np.isnan(ta * tb) else np.nan
                r["VAL_n"] = len(a); r["VAL_mean"] = ma - mb; r["VAL_t"] = (ma - mb) / se if se else np.nan
                d0 = dev_nest[(dev_nest.scope == "EVENT") & (dev_nest.hz == c["hz"]) & (dev_nest.ev == c["ev"]) &
                              (dev_nest["align"] == c["align"])].iloc[0]
                r["DEV_mean"], r["DEV_t"] = d0.diff_vs_other_align, d0.t_diff
            else:
                g = et[(et.hz == c["hz"]) & (et.ev == c["ev"])]
                r["VAL_n"] = len(g); r["VAL_mean"], r["VAL_t"], _ = cr_mean_t(g.d_ret60.values, g.sd.values)
                d0 = dev_mech[(dev_mech.hz == c["hz"]) & (dev_mech.ev == c["ev"])].iloc[0]
                r["DEV_mean"], r["DEV_t"] = d0.mean_d_ret60, d0.t_d_ret60
            r["VAL_same_sign"] = bool(np.sign(r["VAL_mean"]) == c["sign"]) if not np.isnan(r["VAL_mean"]) else False
            r["VAL_PASS"] = bool(r["VAL_same_sign"] and abs(r["VAL_t"]) >= 1.65)
            rows.append(r)
        ae = pd.read_csv(f"{OUT}/tables/M09_analog_eval__{inst}_VAL.csv")
        ad = pd.read_csv(f"{OUT}/tables/M09_analog_eval__{inst}_DEV.csv")
        for c in fz["analog_candidates"]:
            if inst not in c["insts"]:
                continue
            cfg, k = c["col"].split("|")
            rv = ae[(ae.config == cfg) & (ae.k == k)].iloc[0]; rd = ad[(ad.config == cfg) & (ad.k == k)].iloc[0]
            r = {"id": c["id"], "inst": inst, "hz": "-", "what": c["col"], "metric": "IC_pooled (resid)", "expected_sign": 1,
                 "VAL_n": rv.n, "VAL_mean": rv.IC_pooled, "VAL_t": rv.IC_pooled_t, "DEV_mean": rd.IC_pooled, "DEV_t": rd.IC_pooled_t}
            r["VAL_same_sign"] = bool(rv.IC_pooled > 0); r["VAL_PASS"] = bool(rv.IC_pooled > 0 and rv.IC_pooled_t >= 1.65)
            rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(f"{OUT}/tables/M16_VAL_information_confirmation.csv", index=False)
    pd.set_option("display.width", 220)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
