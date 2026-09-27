"""TEST43-M Part 7/8/15/16: walk-forward kNN analog information study (DEV only).

Usage: python m_analog.py INST [END]   (INST: ES, MNQ, ES5, MNQ5; END: DEV default, VAL for the one-time confirmation)
Writes out/m/{INST}_{END}/analog_preds.parquet and out/m/tables/M09_analog_info__{INST}_{END}.csv
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from t43 import analog as A  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
WIN = {"15m": 15, "30m": 30, "60m": 60, "120m": 120}
FOLDS = {"F1": ("2019-01-01", "2020-12-31"), "F2": ("2021-01-01", "2022-12-31"), "F3": ("2023-01-01", "2024-12-31"),
         "VAL": ("2025-01-01", "2025-09-30")}
ALLF = list(A.FAMILIES)


def configs():
    cf = []
    for w in WIN:
        for norm in ("ATR", "RANGE"):
            cf.append(dict(name=f"SHAPE_ONLY_{norm}_{w}", shape=(w, norm), fams=[], ctx=False))
    for w in WIN:
        cf.append(dict(name=f"SHAPE_PLUS_STATE_ATR_{w}", shape=(w, "ATR"), fams=ALLF, ctx=True))
    cf.append(dict(name="SHAPE_PLUS_STATE_RANGE_60m", shape=("60m", "RANGE"), fams=ALLF, ctx=True))
    cf.append(dict(name="STATE_ONLY", shape=None, fams=ALLF, ctx=True))
    cf.append(dict(name="RANDOM_IN_CONTEXT_CTL", shape=None, fams=ALLF, ctx=True, random=True))
    for fam in ALLF:   # Part 15: base shape + one family at a time
        cf.append(dict(name=f"ABL_SHAPE_ATR_60m+{fam}", shape=("60m", "ATR"), fams=[fam], ctx=False))
    cf.append(dict(name="ABL_SHAPE_ATR_60m+HIERARCHY", shape=("60m", "ATR"), fams=[], ctx=True))
    return cf


_G = {}


def _setup(inst, end):
    df = pd.read_parquet(f"{OUT}/{inst}_{end}/bars.parquet")
    bm = 5 if inst.endswith("5") else 3
    idx = A.decision_points(df, bm)
    # need enough history for the longest window
    idx = idx[idx >= 200]
    sd = df.sd.values[idx]
    su = np.unique(df.sd.values)
    sess_idx = np.searchsorted(su, sd)
    keys = ["year", "tier", "volT", "clock", "pbin60"]
    cm = df.groupby(keys)[["ret60", "mae60", "mfe60"]].mean().add_prefix("c_")
    cj = df[keys].join(cm, on=keys)
    ctl = cj["c_ret60"].values
    Y = df[A.TARGETS].values[idx].astype(float)
    ctx = np.stack([df.tier.values[idx], df.volT.values[idx]], 1).astype(int)
    _G.update(df=df, bm=bm, idx=idx, sess_idx=sess_idx, Y=Y, ctx=ctx, d_ret60=Y[:, 1] - ctl[idx], d_mae60=Y[:, 4] - cj["c_mae60"].values[idx],
              d_mfe60=Y[:, 3] - cj["c_mfe60"].values[idx],
              sd=sd, inst=inst, end=end)


def _features(cfg):
    df, idx, bm = _G["df"], _G["idx"], _G["bm"]
    mats = []
    if cfg["shape"]:
        w, norm = cfg["shape"]
        Wb = WIN[w] // bm
        c = df.c.values; atrD = df.atrD.values
        if norm == "RANGE":
            s = pd.Series(c)
            lo = s.rolling(Wb + 1).min().values; hi = s.rolling(Wb + 1).max().values
            M = A.shape_matrix(c, (lo, hi), atrD, idx, Wb, "RANGE")
        else:
            M = A.shape_matrix(c, None, np.where(atrD > 0, atrD, np.nan), idx, Wb, "ATR")
        mats.append(("SHAPE", M))
    fam_cols = A.state_matrix(df, idx, cfg["fams"])
    for fam in cfg["fams"]:
        mats.append((fam, np.stack([v for f_, k, v in fam_cols if f_ == fam], 1)))
    warm = _G["sess_idx"] < A.WARMUP
    if not mats:
        return np.zeros((len(idx), 1), np.float32)
    return A.standardise(mats, warm)


def run_cfg(cfg):
    X = _features(cfg)
    res, meta = A.knn_walkforward(X, _G["sess_idx"], _G["Y"], ctx=_G["ctx"] if cfg["ctx"] else None,
                                  random_ctl=cfg.get("random", False))
    out = {}
    for k, o in res.items():
        conf = A.confidence(o["pred"][:, 1], o["sd"], o["dist"], o["indep"], k, _G["sess_idx"])
        out[k] = dict(pred=o["pred"], conf=conf, indep=o["indep"], nraw=o["nraw"], dist=o["dist"], pup=o["pup"])
    return cfg["name"], out, meta


def evaluate(name, k, o):
    sd = pd.to_datetime(_G["sd"]); y = _G["Y"][:, 1]; dr = _G["d_ret60"]
    p = o["pred"][:, 1]
    m = ~np.isnan(p) & ~np.isnan(y) & (o["conf"] != "NO_MATCH")
    r = {"inst": _G["inst"], "config": name, "k": k, "n_pred": int(m.sum()),
         "coverage": float(m.sum() / max(1, (~np.isnan(p)).sum())),
         "mean_nraw": float(o["nraw"][m].mean()) if m.any() else np.nan,
         "mean_indep_campaigns": float(o["indep"][m].mean()) if m.any() else np.nan}
    if m.sum() < 500:
        return r
    r["IC_raw"] = spearmanr(p[m], y[m])[0]
    r["IC_resid"] = spearmanr(p[m], dr[m])[0]
    mon = pd.DataFrame({"m": sd[m].to_period("M"), "p": p[m], "d": dr[m], "y": y[m]})
    mic = mon.groupby("m").apply(lambda g: spearmanr(g.p, g.d)[0] if len(g) > 30 else np.nan).dropna()
    r["IC_resid_monthly_mean"] = mic.mean(); r["IC_resid_monthly_t"] = mic.mean() / (mic.std() / np.sqrt(len(mic)))
    r["n_months"] = len(mic)
    for f, (a, b) in FOLDS.items():
        mm = m & (sd >= a) & (sd <= b)
        if mm.sum() > 300:
            r[f"{f}_IC_resid"] = spearmanr(p[mm], dr[mm])[0]
    q = pd.qcut(pd.Series(p[m]).rank(method="first"), 3, labels=[0, 1, 2]).values
    ses = pd.DataFrame({"s": sd[m], "q": q, "d": dr[m], "y": y[m]})
    top = ses[ses.q == 2].groupby("s").d.mean(); bot = ses[ses.q == 0].groupby("s").d.mean()
    j = pd.concat([top, bot], axis=1, keys=["t", "b"]).dropna()
    diff = j.t - j.b
    r["tercile_spread_resid"] = diff.mean(); r["tercile_spread_t"] = diff.mean() / (diff.std() / np.sqrt(len(diff)))
    r["top_tercile_resid"] = ses[ses.q == 2].d.mean(); r["bottom_tercile_resid"] = ses[ses.q == 0].d.mean()
    for c in ("HIGH", "MED", "LOW"):
        cm = m & (o["conf"] == c)
        r[f"share_{c}"] = cm.sum() / m.sum()
        if cm.sum() > 50:
            pos = cm & (p > 0); neg = cm & (p < 0)
            r[f"{c}_pos_resid"] = dr[pos].mean() if pos.sum() else np.nan
            r[f"{c}_neg_resid"] = dr[neg].mean() if neg.sum() else np.nan
            r[f"{c}_n_pos"] = int(pos.sum()); r[f"{c}_n_neg"] = int(neg.sum())
    # risk information: predicted MAE vs realised MAE
    mae_p = o["pred"][:, 4]; mae_y = _G["Y"][:, 4]
    mm = m & ~np.isnan(mae_y)
    r["IC_mae60"] = spearmanr(mae_p[mm], mae_y[mm])[0]
    mfe_p = o["pred"][:, 3]; mfe_y = _G["Y"][:, 3]
    r["IC_mfe60"] = spearmanr(mfe_p[mm], mfe_y[mm])[0]
    r["IC_mae60_resid"] = spearmanr(mae_p[mm], _G["d_mae60"][mm])[0]
    r["IC_mfe60_resid"] = spearmanr(mfe_p[mm], _G["d_mfe60"][mm])[0]
    return r


def main(inst, end="DEV"):
    _setup(inst, end)
    cf = configs()
    rows, preds, metas = [], {}, []
    with ProcessPoolExecutor(4, initializer=_setup, initargs=(inst, end)) as ex:
        for name, out, meta in ex.map(run_cfg, cf):
            for k, o in out.items():
                rows.append(evaluate(name, k, o))
                if k in (50, 100):
                    preds[f"{name}|k{k}|pred"] = o["pred"][:, 1]
                    preds[f"{name}|k{k}|conf"] = o["conf"]
                    preds[f"{name}|k{k}|mae"] = o["pred"][:, 4]
                    preds[f"{name}|k{k}|indep"] = o["indep"]
            meta["config"] = name; metas.append(meta)
            print(name, "done", flush=True)
    P = pd.DataFrame(preds)
    P.insert(0, "bar", _G["idx"]); P.insert(1, "sd", _G["sd"]); P["ret60"] = _G["Y"][:, 1]; P["d_ret60"] = _G["d_ret60"]
    P.to_parquet(f"{OUT}/{inst}_{end}/analog_preds.parquet")
    os.makedirs(f"{OUT}/tables", exist_ok=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/tables/M09_analog_info__{inst}_{end}.csv", index=False)
    M = pd.concat(metas)
    su = np.unique(_G["df"].sd.values)
    M["block_first_date"] = su[M.block_first_sess.values]; M["lib_last_date"] = su[M.lib_last_sess.values]
    M["strictly_before"] = M.lib_last_date < M.block_first_date
    M.to_csv(f"{OUT}/tables/M08_analog_library_meta__{inst}_{end}.csv", index=False)
    print("causal library check: all strictly before =", bool(M.strictly_before.all()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "DEV")
