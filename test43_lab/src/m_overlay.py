"""TEST43-M Parts 11-13: incremental exposure-modifier overlay on untouched V6A candidates, reduction
avoided-vs-forgone, add-now vs wait vs no-add.

Usage:
  python m_overlay.py DEV            grid of broad modifier sizes on DEV (+ F1/F2/F3), writes M13/M14/M15 tables
  python m_overlay.py VAL FROZEN.json  one-time VAL confirmation of frozen overlays (no retune)
The V6 candidate parameters are read from out/v6/shortlist.json and never modified.
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import features, instruments, lab, v6a, v6lab  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
TAB = f"{OUT}/tables"
SL = json.load(open(os.path.join(os.path.dirname(__file__), "..", "out", "v6", "shortlist.json")))
V6A = [c for c in SL if c["arch"] not in ("B", "G")]
PER_DEV = ("DEV", "F1", "F2", "F3", "PRE23")
PER_VAL = ("VAL", "DEV")


# ------------------------------------------------------------------------------------------ modifier arrays
def xm_from_events(n, ev, up, down, hold, up_mult, dn_mult, align_up=None, align_dn=None):
    """Event-triggered modifier: trigger at the event bar close, active for `hold` bars, no re-trigger while active
    (rearm only after expiry); an opposite trigger while active ends the modifier."""
    trig = []
    for (hz, e) in up:
        m = (ev.hz == hz) & (ev.ev == e)
        if align_up:
            m &= ev["align"].isin(align_up)
        trig += [(b, 1) for b in ev.bar[m].values]
    for (hz, e) in down:
        m = (ev.hz == hz) & (ev.ev == e)
        if align_dn:
            m &= ev["align"].isin(align_dn)
        trig += [(b, -1) for b in ev.bar[m].values]
    trig.sort()
    xm = np.ones(n)
    until = -1; side = 0
    for b, s in trig:
        if b <= until:
            if s != side:
                xm[b:until + 1] = 1.0; until = b; side = 0
            continue
        side = s; until = min(n - 1, b + hold - 1)
        xm[b:until + 1] = up_mult if s > 0 else dn_mult
    return xm


def xm_from_analog(n, P, col, conf_ok, up_mult, dn_mult, hold=5, min_abs=0.0):
    pred = P[f"{col}|pred"].values; conf = P[f"{col}|conf"].values; bars = P.bar.values
    xm = np.ones(n)
    for b, p, c in zip(bars, pred, conf):
        if c in conf_ok and not np.isnan(p) and abs(p) > min_abs:
            xm[b:min(n, b + hold)] = up_mult if p > 0 else dn_mult
    return xm


# ------------------------------------------------------------------------------------------ evaluation
_S = {}


def _load(inst, end_name):
    key = (inst, end_name)
    if key not in _S:
        end = lab.DEV_END if end_name == "DEV" else lab.VAL_END
        b, f = v6lab.load(inst, end)
        ev = pd.read_parquet(f"{OUT}/{inst}_{end_name}/events.parquet")
        pa = f"{OUT}/{inst}_{end_name}/analog_preds.parquet"
        P = pd.read_parquet(pa) if os.path.exists(pa) else None
        _S[key] = (b, f, ev, P, end)
    return _S[key]


def run_one(args):
    cand, spec, end_name, periods = args
    inst = cand["inst"]
    b, f, ev, P, end = _load(inst, end_name)
    n = len(b)
    if spec is None:
        xm = np.ones(n)
    elif spec["type"] == "event":
        xm = xm_from_events(n, ev, [tuple(x) for x in spec.get("up", [])], [tuple(x) for x in spec.get("down", [])],
                            spec["hold"], spec["up_mult"], spec["dn_mult"], spec.get("align_up"), spec.get("align_dn"))
    else:
        xm = xm_from_analog(n, P, spec["col"], set(spec["conf"]), spec["up_mult"], spec["dn_mult"], spec.get("hold", 5))
    f2 = dict(f); f2["xm"] = xm
    p = v6lab.inst_params(inst); p.update(cand["params"])
    if spec is not None:
        p["xHead"] = spec.get("xHead", 0)
    r = v6a.run(b, f2, v6a.make_params(**p))
    d = v6lab.daily(b, r)
    out = {"id": cand["id"], "inst": inst, "spec": spec["name"] if spec else "BASE", "xm_active_share": float((xm != 1).mean())}
    out.update(v6lab.period_block(inst, d, periods, end, mb=True))
    out["fills"] = int(len(r["f_qty"])); out["sides"] = float(np.abs(r["f_qty"]).sum())
    rawpx = (b.c - b.cum_adjustment.astype(float)).values
    fr = np.where(b.in_rth.values, p["mIntraFrac"], p["mOnFrac"])
    util = r["pos"] * rawpx * p["pointValue"] * fr / np.maximum(r["equity"], 1.0)
    out["peak_margin_util"] = float(util.max()); out["margin_breach"] = bool(util.max() > 1.0)
    return out


def grid_specs(frozen):
    """Broad modifier sizes for each surviving mechanism (no fine tuning)."""
    specs = []
    for mech in frozen["mechanisms"]:
        for um, dm in ((1.25, 1.0), (1.5, 1.0), (1.0, 0.75), (1.0, 0.5), (1.25, 0.75), (1.5, 0.5)):
            if mech["type"] == "event" and not mech.get("up") and um != 1.0:
                continue
            if mech["type"] == "event" and not mech.get("down") and dm != 1.0:
                continue
            if mech["type"] == "analog" and mech.get("side") == "down" and um != 1.0:
                continue
            if mech["type"] == "analog" and mech.get("side") == "up" and dm != 1.0:
                continue
            for xh in ((0, 2) if um > 1 else (0,)):
                s = dict(mech); s.update(up_mult=um, dn_mult=dm, xHead=xh,
                                         name=f"{mech['name']}|up{um}|dn{dm}|head{xh}")
                specs.append(s)
    return specs


def main_dev(frozen_path):
    frozen = json.load(open(frozen_path))
    specs = grid_specs(frozen)
    jobs = []
    for c in V6A:
        jobs.append((c, None, "DEV", PER_DEV))
        for s in specs:
            if s["inst"] == c["inst"]:
                jobs.append((c, s, "DEV", PER_DEV))
    with ProcessPoolExecutor(4) as ex:
        rows = list(ex.map(run_one, jobs, chunksize=4))
    df = pd.DataFrame(rows)
    base = df[df.spec == "BASE"].set_index("id")
    for k in ("DEV_avg_daily", "DEV_max_dd", "DEV_worst_day", "DEV_excess_vs_mb", "F1_avg_daily", "F2_avg_daily",
              "F3_avg_daily", "F2_max_dd", "fills"):
        df["d_" + k] = df[k] - df.id.map(base[k])
    df["fills_ratio"] = df.fills / df.id.map(base["fills"])
    df.to_csv(f"{TAB}/M13_incremental_exposure_DEV.csv", index=False)
    print(df[["id", "spec", "d_DEV_avg_daily", "d_DEV_max_dd", "d_DEV_excess_vs_mb", "d_F1_avg_daily", "d_F2_avg_daily",
              "d_F3_avg_daily", "fills_ratio", "DEV_env"]].round(2).to_string())


def main_val(frozen_path):
    frozen = json.load(open(frozen_path))
    jobs = []
    for c in V6A:
        jobs.append((c, None, "VAL", PER_VAL))
        for s in frozen["overlays"]:
            if s["inst"] == c["inst"] and (not s.get("ids") or c["id"] in s["ids"]):
                jobs.append((c, s, "VAL", PER_VAL))
    with ProcessPoolExecutor(4) as ex:
        rows = list(ex.map(run_one, jobs))
    df = pd.DataFrame(rows)
    base = df[df.spec == "BASE"].set_index("id")
    for k in ("VAL_avg_daily", "VAL_max_dd", "VAL_worst_day", "VAL_excess_vs_mb", "DEV_avg_daily", "DEV_max_dd", "fills"):
        df["d_" + k] = df[k] - df.id.map(base[k])
    df.to_csv(f"{TAB}/M16_VAL_overlay.csv", index=False)
    print(df[["id", "spec", "VAL_avg_daily", "d_VAL_avg_daily", "d_VAL_max_dd", "d_VAL_excess_vs_mb", "d_DEV_avg_daily",
              "fills"]].round(2).to_string())


if __name__ == "__main__":
    if sys.argv[1] == "DEV":
        main_dev(sys.argv[2])
    else:
        main_val(sys.argv[2])
