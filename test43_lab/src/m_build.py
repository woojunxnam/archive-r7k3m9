"""TEST43-M dataset builder: per-bar range metrics/states/positions/outcomes/control cells + event table.

Usage: python m_build.py INST [END]      INST in ES, MNQ, ES5, MNQ5; END = DEV (default) or VAL
DEV discovery loads bars truncated at DEV_END, so no VAL/holdout bar can enter any feature or outcome.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import lab, ranges as R, v6lab  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
HS3 = np.array([5, 10, 20, 40, 80])      # forward horizons in bars (3m: 15/30/60/120/240m)


def bars_per_min(inst):
    return 5 if inst.endswith("5") else 3


def build(inst, end_name="DEV"):
    end = lab.DEV_END if end_name == "DEV" else lab.VAL_END
    b, f = v6lab.load(inst, end)
    bm = bars_per_min(inst)
    o = b.o.values; h = b.h.values; l = b.l.values; c = b.c.values
    n = len(c)
    atrD = np.nan_to_num(f["d_ATR20"], nan=0.0)
    atr14 = f["atr14"]
    sess = f["sess"]; in_rth = f["in_rth"]; mod = f["mod"]
    hs = np.array([max(1, int(round(x * 3 / bm))) for x in HS3])
    df = pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "mod": mod, "rth": in_rth, "c": c,
                       "atrD": atrD, "tier": f["d_TIER"], "trend20": f["d_TREND20"], "trend100": f["d_TREND100"],
                       "atr_pct": f["d_ATR20_pct"], "vwap_z": f["vwap_z"], "pos_rth": f["pos_rth"],
                       "pos_prior": f["pos_prior"], "pos_5d": f["pos_5d"]})
    ret, mfe, mae, fp05, fp10, rthc, on, nxo = R.outcomes(o, h, l, c, atrD, sess, in_rth, hs)
    for k, m in enumerate([15, 30, 60, 120, 240]):
        df[f"ret{m}"] = ret[:, k]; df[f"mfe{m}"] = mfe[:, k]; df[f"mae{m}"] = mae[:, k]
    df["fp05"] = fp05; df["fp10"] = fp10; df["ret_rthc"] = rthc; df["ret_on"] = on; df["ret_nxo"] = nxo
    df["frange60"] = df["mfe60"] - df["mae60"]
    # control-cell keys (instrument implicit; era=year; trend/vol regime; clock bucket)
    df["year"] = pd.DatetimeIndex(df.sd).year
    df["volT"] = np.where(np.isnan(df.atr_pct), 1, np.minimum((df.atr_pct.fillna(0.5) * 3).astype(int), 2))
    rth_b = (mod - 570) // 30
    hr = (mod // 60)
    on_b = np.where(hr >= 18, 20, np.where(hr < 4, 21, 22))
    df["clock"] = np.where(in_rth, rth_b, on_b)
    # ---- intraday horizons: qualified balance windows (causal percentiles of previous 60 sessions)
    events = []
    thr_cache = {}
    for name, H3 in R.HORIZONS.items():
        H = max(2, int(round(H3 * 3 / bm)))
        hi, lo, eff, ovl, rvr, cdisp, tl, th, wn = R.window_metrics(h, l, c, atr14, H)
        q_eff = R.causal_quantiles(eff, sess, in_rth, [1 / 3])
        q_ovl = R.causal_quantiles(ovl, sess, in_rth, [0.5])
        q_wn = R.causal_quantiles(wn, sess, in_rth, [1 / 3])
        q_rv = R.causal_quantiles(rvr, sess, in_rth, [0.5])
        thr_cache[name] = (q_eff, q_ovl, q_wn)
        qual = (eff <= q_eff[:, 0]) & (ovl >= q_ovl[:, 0]) & (tl >= 2) & (th >= 2)
        comp = qual & (wn <= q_wn[:, 0]) & (rvr <= q_rv[:, 0])
        w = hi - lo
        df[f"eff_{name}"] = eff; df[f"ovl_{name}"] = ovl; df[f"rvr_{name}"] = rvr; df[f"cdisp_{name}"] = cdisp
        df[f"wn_{name}"] = wn; df[f"qual_{name}"] = qual; df[f"comp_{name}"] = comp
        df[f"tpos_{name}"] = np.where(w > 0, (c - lo) / np.where(w > 0, w, 1), 0.5)   # trailing raw position
        df[f"effq_{name}"] = np.select([eff <= q_eff[:, 0]], [0], 1)
        res = R.state_machine(o, h, l, c, atrD, hi, lo, qual, comp, H, sess, 4 * H)
        act, RL, RH, st, rid = res[:5]
        df[f"act_{name}"] = act; df[f"state_{name}"] = st; df[f"rid_{name}"] = rid
        rw = RH - RL
        df[f"rpos_{name}"] = np.where(act & (rw > 0), (c - RL) / np.where(rw > 0, rw, 1), np.nan)
        df[f"rw_atr_{name}"] = np.where(act, rw / np.where(atrD > 0, atrD, np.nan), np.nan)
        events.append(_events(name, H, res[5:], df))
    # ---- session-anchored frozen ranges: prior RTH, 2D, 5D, opening ranges
    for name, (hi, lo, qual, H) in _session_ranges(b, f, bm).items():
        z = np.zeros(n, bool)
        age = 10 ** 7 if name == "5D" else (1400 // bm if name in ("PRTH", "2D") else 600 // bm)   # PRTH/2D: whole session
        res = R.state_machine(o, h, l, c, atrD, hi, lo, qual, z, H, sess, age)
        act, RL, RH, st, rid = res[:5]
        rw = RH - RL
        df[f"act_{name}"] = act; df[f"state_{name}"] = st; df[f"rid_{name}"] = rid
        df[f"rpos_{name}"] = np.where(act & (rw > 0), (c - RL) / np.where(rw > 0, rw, 1), np.nan)
        events.append(_events(name, H, res[5:], df))
    ev = pd.concat(events, ignore_index=True)
    # nested alignment at every bar (trailing 15/30/60/120m + RTH + prior RTH + 5D)
    P = np.column_stack([df[f"tpos_{k}"].values for k in R.HORIZONS] + [df.pos_rth.values, df.pos_prior.values,
                                                                          df.pos_5d.values])
    low = (P <= 0.25).sum(1); high = (P >= 0.75).sum(1); mid = ((P >= 0.35) & (P <= 0.65)).sum(1)
    df["n_low"] = low; df["n_high"] = high
    df["align"] = np.select([(low >= 4) & (high == 0), (high >= 4) & (low == 0), mid >= 4],
                            ["MULTI_LOW", "MULTI_HIGH", "MID_CLUSTER"], "MIXED")
    df["pbin60"] = np.clip((df["tpos_60m"].values * 5).astype(int), 0, 4)
    for k in R.HORIZONS:
        df[f"pbin_{k}"] = np.clip((df[f"tpos_{k}"].values * 5).astype(int), 0, 4)
    ev = ev.join(df[["align", "n_low", "n_high"]], on="bar")
    os.makedirs(f"{OUT}/{inst}_{end_name}", exist_ok=True)
    df.to_parquet(f"{OUT}/{inst}_{end_name}/bars.parquet")
    ev.to_parquet(f"{OUT}/{inst}_{end_name}/events.parquet")
    print(inst, end_name, "bars", n, "events", len(ev), "sessions", df.sd.nunique(), "last", df.sd.max())
    return df, ev


def _events(name, H, e, df):
    bar, code, rid, rl, rh, x, age = e
    ev = pd.DataFrame({"hz": name, "H": H, "bar": bar, "code": code, "ev": np.array(R.EV)[code], "rid": rid, "rL": rl,
                       "rH": rh, "x": x, "age": age})
    return ev


def _session_ranges(b, f, bm):
    """Frozen session ranges known at a causal time: prior RTH (from first bar of session), 2D (prior two RTH),
    5D (prior five RTH), opening range 15/30/60 (frozen at OR completion bar close)."""
    n = len(b)
    out = {}
    sd = b.session_date.values; mod = f["mod"]; rth = f["in_rth"]
    first = np.r_[True, sd[1:] != sd[:-1]]
    ph = f["d_RH"]; pl = f["d_RL"]
    q = first & ~np.isnan(ph)
    out["PRTH"] = (ph, pl, q, 40 * 3 // bm)
    s = pd.DataFrame({"sd": sd, "RH": ph, "RL": pl}).groupby("sd").first()
    h2 = s.RH.rolling(2).max(); l2 = s.RL.rolling(2).min()
    h5 = s.RH.rolling(5).max(); l5 = s.RL.rolling(5).min()
    idx = pd.Index(s.index).get_indexer(sd)
    out["2D"] = (h2.values[idx], l2.values[idx], first & ~np.isnan(h2.values[idx]), 40 * 3 // bm)
    out["5D"] = (h5.values[idx], l5.values[idx], first & ~np.isnan(h5.values[idx]), 40 * 3 // bm)
    h = b.h.values; l = b.l.values
    for m in (15, 30, 60):
        hi = np.full(n, np.nan); lo = np.full(n, np.nan); qual = np.zeros(n, bool)
        end_mod = 570 + m - bm       # bar opening at end_mod closes at 09:30+m
        dfo = pd.DataFrame({"sd": sd, "h": h, "l": l, "in": rth & (mod >= 570) & (mod <= end_mod)})
        g = dfo[dfo["in"]].groupby("sd").agg(H=("h", "max"), L=("l", "min"))
        comp_bar = np.where(rth & (mod == end_mod))[0]
        for i in comp_bar:
            d = sd[i]
            if d in g.index:
                hi[i] = g.at[d, "H"]; lo[i] = g.at[d, "L"]; qual[i] = True
        out[f"OR{m}"] = (hi, lo, qual, max(2, m // bm))
    return out


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "DEV")
