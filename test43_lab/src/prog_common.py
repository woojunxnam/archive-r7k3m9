"""Autonomous ES/NQ long-alpha program (TEST48+): shared layer.
* Research data <= 2026-05-27 only (canonical ES / MNQ 1m, hash-verified).  No newer data is ever loaded.
* DISCOVERY region for hypothesis generation (gap map, opportunity labels, feature information): 2019-07-01 .. 2020-12-31 ONLY,
  i.e. the region that is training data in every nested outer fold; the outer folds 2021 .. 2026-05-27 stay blind to
  hypothesis generation.
* Master registries live in out/program/ (machine-readable CSV)."""
import datetime
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

ROOT = C45.ROOT
PROG = os.path.join(ROOT, "out", "program"); os.makedirs(PROG, exist_ok=True)
REPP = os.path.join(ROOT, "reports", "AUTONOMOUS_PROGRAM"); os.makedirs(REPP, exist_ok=True)
END = pd.Timestamp("2026-05-27")
DISC = (pd.Timestamp("2019-07-01"), pd.Timestamp("2020-12-31"))
SPAN21 = pd.Timestamp("2021-01-01")
REG = {k: os.path.join(PROG, f"{k}.csv") for k in ("AUTONOMOUS_TEST_REGISTRY", "REJECTED_FAMILY_REGISTRY", "SHADOW_CLUE_REGISTRY",
                                                  "SURVIVOR_LIBRARY", "ALPHA_GAP_MAP", "PORTFOLIO_CANDIDATE_FRONTIER", "RESEARCH_BUDGET_LOG")}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def reg_load(name):
    p = REG[name]
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def reg_append(name, rows, key=None):
    df = reg_load(name)
    new = pd.DataFrame(rows)
    df = pd.concat([df, new], ignore_index=True)
    if key:
        df = df.drop_duplicates(key, keep="last")
    df.to_csv(REG[name], index=False)
    return df


def prereg(test, spec):
    """write + hash a preregistration BEFORE any economics of the test are computed."""
    d = os.path.join(ROOT, "out", test.lower()); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{test}_PREREGISTRATION.json")
    spec = {"test": test, "written_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z", "research_data_end": "2026-05-27", **spec}
    json.dump(spec, open(p, "w"), indent=1, default=str)
    h = sha(p); open(p + ".sha256", "w").write(h + "\n")
    return h


def md(path, title, blocks, rep=REPP):
    os.makedirs(rep, exist_ok=True)
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b))
        lines.append("")
    open(os.path.join(rep, path), "w").write("\n".join(lines) + "\n")


# ------------------------------------------------------------------------------------------ C43 intraday state
def c43_positions(sess):
    """C43 (CHAMPION_CONTROL_V1) position per session x 1m RTH grid (ES, MNQ), from the frozen TEST44 reproduction
    (3m union timeline).  Research label / context only (the portfolio position is known causally to the live engine)."""
    cache = os.path.join(PROG, "c43_pos_grid.npz")
    if os.path.exists(cache):
        z = np.load(cache)
        return z["ES"], z["MNQ"]
    from t43 import portfolio as PF
    T = PF.timeline(END)
    pos = np.load(os.path.join(ROOT, "out", "t44", "pos_CHAMPION_CONTROL_V1.npy"))
    df = pd.DataFrame({"t": T.index.values, "pES": pos[:, 0], "pMNQ": pos[:, 1], "sd": pd.to_datetime(T.sd.values)})
    out = {k: np.full((len(sess), C45.NG), np.nan) for k in ("ES", "MNQ")}
    si = pd.Index(sess)
    df["mod"] = df.t.dt.hour * 60 + df.t.dt.minute
    df = df[(df["mod"] >= 9 * 60 + 27) & (df["mod"] <= 16 * 60 + 15)]
    df["s"] = si.get_indexer(df.sd)
    df = df[df.s >= 0]
    for _, g in df.groupby("s"):
        s = int(g.s.iloc[0])
        m = g["mod"].values
        for k, col in (("ES", "pES"), ("MNQ", "pMNQ")):
            # grid minute j (bar end-stamp M0+j) lies in 3m bar starting at floor((M0+j-1)/3)*3; position after that bar
            mins = C45.M0 + np.arange(C45.NG) - 1
            idx = np.searchsorted(m, mins, side="right") - 1
            v = g[col].values[np.clip(idx, 0, len(g) - 1)].astype(float)
            v[idx < 0] = np.nan
            out[k][s] = v
    np.savez_compressed(cache, **out)
    return out["ES"], out["MNQ"]


# ------------------------------------------------------------------------------------------ standard module evaluation
def risk(x):
    x = np.asarray(x, float)
    eq = np.r_[0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    return {"avg_day": float(x.mean()), "total": float(x.sum()), "max_dd": mdd, "worst_day": float(x.min()),
            "ret_dd": float(x.mean() / mdd) if mdd > 0 else np.nan}


def evaluate_module(name, d, exc, sess, champ, extra=None):
    """d = daily $ of the module (integer contracts, costs incl.), exc = daily matched-long excess $.
    Standard program gate (fixed for the whole program, written before TEST48 economics):
      G1 >= 4/5 outer folds positive AND median outer > 0      G2 matched-long excess/day > 0 (2021+)
      G3 remove-top3 > 0 and remove-top5 >= 0 (report)          G4 C43+module: MaxDD <= 15k, worst >= -3k, ret/DD >= C43 ret/DD
      G5 parameter plateau PASS (supplied)                      G6 recurrence PASS (GA/ML only, supplied)
      G7 >= $3/day incremental 2021+ AND |corr C43| <= 0.5     G8 >= 150 active days 2021+, no year > 40% of positive P&L
      G9 4-tick slippage stress still positive (supplied)"""
    extra = dict(extra or {})
    m = sess >= SPAN21
    x = d[m]; ch = champ[m]; xe = exc[m]
    fold = {}
    for nm, a, b in C45.OUTER:
        mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b))
        fold[nm] = float(d[mm].mean())
    act = x[x != 0]; top = np.sort(act)[::-1]
    yr_all = pd.Series(d, index=sess).groupby(sess.year).sum()
    yr = yr_all[yr_all.index >= 2021]
    rc, rch = risk(ch + x), risk(ch)
    o = {"module": name, **{f"fold_{k}": v for k, v in fold.items()}, "folds_pos": int(sum(v > 0 for v in fold.values())),
         "fold_median": float(np.median(list(fold.values()))), "fold_worst": float(min(fold.values())), **{f"y{k}": v for k, v in yr_all.items()},
         "pre2023_avg": float(d[(sess < pd.Timestamp("2023-01-01")) & (sess >= DISC[0])].mean()), "from2023_avg": float(d[sess >= pd.Timestamp("2023-01-01")].mean()),
         **{f"standalone_{k}": v for k, v in risk(x).items()}, "matched_excess_day": float(xe.mean()),
         "active_days": int((x != 0).sum()), "remove_top3": float(act.sum() - top[:3].sum()) if len(top) >= 3 else np.nan,
         "remove_top5": float(act.sum() - top[:5].sum()) if len(top) >= 5 else np.nan,
         **{f"comb_{k}": v for k, v in rc.items()}, "C43_ret_dd": rch["ret_dd"], "incr_avg_day": rc["avg_day"] - rch["avg_day"],
         "corr_C43": float(np.corrcoef(ch, x)[0, 1]) if x.std() > 0 else np.nan,
         "loss_day_jaccard": float(((ch < 0) & (x < 0)).sum() / max(((ch < 0) | (x < 0)).sum(), 1)),
         "bottom_tail_overlap": float((x[np.argsort(ch)[:20]] < 0).mean()),
         "max_year_share": float(yr.clip(lower=0).max() / max(yr.clip(lower=0).sum(), 1e-9)),
         "roll6m_min": float(pd.Series(x).rolling(126).mean().min()), "roll12m_min": float(pd.Series(x).rolling(252).mean().min()),
         "roll12m_pos_share": float((pd.Series(x).rolling(252).mean().dropna() > 0).mean())}
    o["G1"] = o["folds_pos"] >= 4 and o["fold_median"] > 0
    o["G2"] = o["matched_excess_day"] > 0
    o["G3"] = bool(o["remove_top3"] > 0)
    o["G4"] = rc["max_dd"] <= 15000 and rc["worst_day"] >= -3000 and rc["ret_dd"] >= rch["ret_dd"]
    o["G5"] = bool(extra.pop("plateau_pass", True))
    o["G6"] = bool(extra.pop("recurrence_pass", True))
    o["G7"] = o["incr_avg_day"] >= 3 and (abs(o["corr_C43"]) <= 0.5 if o["corr_C43"] == o["corr_C43"] else False)
    o["G8"] = o["active_days"] >= 150 and o["max_year_share"] <= 0.40
    o["G9"] = bool(extra.pop("stress4_pos", True))
    o["PASS"] = all(o[f"G{i}"] for i in range(1, 10))
    o.update(extra)
    return o


def budget(test, hypotheses=0, ml_configs=0, genomes=0, finalists=0, note=""):
    reg_append("RESEARCH_BUDGET_LOG", [{"test": test, "hypotheses": hypotheses, "ml_configs": ml_configs, "valid_genomes": genomes,
                                        "finalists": finalists, "note": note, "utc": datetime.datetime.utcnow().isoformat(timespec="seconds")}])
