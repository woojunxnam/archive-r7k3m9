"""TEST43-M information study (DEV only): range states, zones, nested alignment, sweep/break machines,
destinations, matched controls, fold/horizon stability, timing placebo, timeframe transfer.

Usage: python m_info.py            (reads out/m/{ES,MNQ,ES5,MNQ5}_DEV, writes out/m/tables/*.csv)
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import ranges as R  # noqa: E402
from t43.mstats import cr_mean_t  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
TAB = f"{OUT}/tables"
OUTC = ["ret30", "ret60", "ret120", "mfe60", "mae60", "mfe120", "mae120", "fp05", "fp10", "frange60", "ret_rthc"]
INTRA = list(R.HORIZONS)
SESSR = ["PRTH", "2D", "5D", "OR15", "OR30", "OR60"]
MECH = ["L_SWEEP", "L_RECLAIM", "L_RETEST", "L_RETEST_HOLD", "L_RESUMPTION", "L_FAILED_RECLAIM", "L_FAILED_RETEST",
        "L_RANGE_REENTRY", "U_SWEEP", "U_RECLAIM", "U_RETEST", "U_RETEST_HOLD", "U_RESUMPTION", "U_FAILED_RECLAIM",
        "U_FAILED_RETEST", "UB_BREAK", "UB_ACCEPT", "UB_RETEST_HOLD", "UB_RESUMED", "UB_FAILED_ACCEPT", "UB_REENTRY",
        "DB_BREAK", "DB_ACCEPT", "DB_RETEST_HOLD", "DB_RESUMED", "DB_FAILED_ACCEPT", "DB_REENTRY"]
FOLDS = {"F1": ("1900", "2020-12-31"), "F2": ("2021-01-01", "2022-12-31"), "F3": ("2023-01-01", "2024-12-31"),
         "PRE23": ("1900", "2022-12-31"), "P23": ("2023-01-01", "2024-12-31")}
RNG = np.random.default_rng(20260927)


def ctl_keys(hz):
    return ["year", "tier", "volT", "clock", f"pbin_{hz}" if hz in INTRA else "pbin60"]


def cell_means(df, keys, cols=OUTC):
    return df.groupby(keys)[cols].mean()


def attach_control(x, df, keys, prefix="c_", cols=OUTC):
    cm = cell_means(df, keys, cols)
    j = x.join(cm.add_prefix(prefix), on=keys)
    for k in cols:
        j["d_" + k] = j[k] - j[prefix + k]
    return j


def cl_t(x, col, by="sd"):
    """Occurrence-weighted mean with session-clustered robust t (see t43.mstats for why not session means)."""
    return cr_mean_t(x[col].values, x[by].values)


def fold_block(x, col):
    out = {}
    for f, (a, b) in FOLDS.items():
        s = x[(x.sd >= pd.Timestamp(a)) & (x.sd <= pd.Timestamp(b))]
        m, t, n = cl_t(s, col)
        out[f"{f}_{col}"] = m; out[f"{f}_t_{col}"] = t; out[f"{f}_nsess"] = n
    return out


def row_label(r, col="d_ret60", thr=2.0):
    t = r.get(f"t_{col}"); m = r.get(f"mean_{col}")
    if t is None or np.isnan(t) or abs(t) < thr:
        return "NO_INFO"
    s = np.sign(m)
    if np.sign(r.get(f"PRE23_{col}", 0)) != s or np.sign(r.get(f"P23_{col}", 0)) != s:
        return "UNSTABLE_ERA"
    for f in ("F1", "F2", "F3"):
        tf = r.get(f"{f}_t_{col}")
        if tf is not None and not np.isnan(tf) and np.sign(tf) != s and abs(tf) >= 1.5:
            return "UNSTABLE_FOLD_REVERSAL"
    return "PASS_POS" if s > 0 else "PASS_NEG"


def summarise(x, keys_extra):
    r = dict(keys_extra)
    r["n"] = len(x); r["n_sess"] = x.sd.nunique(); r["n_campaign"] = x.drop_duplicates(["rid"]).shape[0] if "rid" in x else np.nan
    for k in ("ret60", "ret120", "mfe60", "mae60"):
        v = x[k].dropna()
        if len(v):
            r[f"{k}_mean"] = v.mean(); r[f"{k}_med"] = v.median()
            for q in (10, 25, 75, 90):
                r[f"{k}_p{q}"] = v.quantile(q / 100)
    for col in ("d_ret30", "d_ret60", "d_ret120", "d_mfe60", "d_mae60", "d_mfe120", "d_mae120", "d_fp05", "d_fp10",
                "d_frange60", "d_ret_rthc"):
        m, t, _ = cl_t(x, col)
        r[f"mean_{col}"] = m; r[f"t_{col}"] = t
    r.update(fold_block(x, "d_ret60")); r.update(fold_block(x, "d_fp05"))
    r["label_ret60"] = row_label(r, "d_ret60"); r["label_fp05"] = row_label(r, "d_fp05")
    return r


def load(inst):
    df = pd.read_parquet(f"{OUT}/{inst}_DEV/bars.parquet")
    ev = pd.read_parquet(f"{OUT}/{inst}_DEV/events.parquet")
    return df, ev


def event_table(inst, df, ev):
    base = df[["sd", "year", "tier", "volT", "clock", "pbin60", "c", "atrD", "rth"] + [f"pbin_{k}" for k in INTRA] + OUTC]
    ev = ev[ev.ev.isin(MECH)].join(base, on="bar")
    parts = []
    for hz, g in ev.groupby("hz"):
        parts.append(attach_control(g, df, ctl_keys(hz)))
    return pd.concat(parts)


def placebo(x, df, hz, reps=3):
    """Timing placebo: same events shifted by a random 40..400 bars (same count), matched-control deltas."""
    ts = []
    for _ in range(reps):
        sh = RNG.integers(40, 400, len(x)) * RNG.choice([-1, 1], len(x))
        bars = np.clip(x.bar.values + sh, 0, len(df) - 1)
        y = df.iloc[bars][["sd", "year", "tier", "volT", "clock", "pbin60"] + [f"pbin_{k}" for k in INTRA] + OUTC].copy()
        y = attach_control(y, df, ctl_keys(hz))
        ts.append(cl_t(y, "d_ret60")[1])
    return ts


def info_mechanisms(inst, et, df):
    rows = []
    for (hz, e), g in et.groupby(["hz", "ev"]):
        if len(g) < 30:
            continue
        r = summarise(g, {"inst": inst, "hz": hz, "ev": e})
        pt = placebo(g, df, hz, reps=5) if len(g) >= 100 else [np.nan]
        r["placebo_t_max_abs"] = np.nanmax(np.abs(pt))
        r["placebo_ts"] = ";".join(f"{t:.3f}" for t in pt)
        rows.append(r)
    out = pd.DataFrame(rows)
    # empirical null from the timing placebo (dependence-aware critical value)
    null = np.abs(np.array([float(v) for s in out.placebo_ts.dropna() for v in s.split(";") if v != "nan"]))
    tcrit = max(2.0, float(np.quantile(null, 0.95))) if len(null) > 50 else 2.0
    out["t_crit_placebo95"] = tcrit
    out["label_ret60"] = [row_label(r, "d_ret60", tcrit) for r in out.to_dict("records")]
    out["label_fp05"] = [row_label(r, "d_fp05", tcrit) for r in out.to_dict("records")]
    return out


def mech_stability(tab):
    """Mechanism-level stability across the four intraday horizons."""
    out = []
    for (inst, e), g in tab[tab.hz.isin(INTRA)].groupby(["inst", "ev"]):
        for col in ("d_ret60", "d_fp05"):
            lab = g[f"label_{col[2:]}"]
            npos = int((lab == "PASS_POS").sum()); nneg = int((lab == "PASS_NEG").sum())
            signs = np.sign(g[f"mean_{col}"]).values
            same = max((signs > 0).sum(), (signs < 0).sum())
            strong_opp = ((np.sign(g[f"mean_{col}"]) != np.sign(np.nanmedian(g[f"mean_{col}"]))) & (g[f"t_{col}"].abs() >= 2)).sum()
            verdict = "STABLE_POS" if npos >= 2 and nneg == 0 and strong_opp == 0 else \
                "STABLE_NEG" if nneg >= 2 and npos == 0 and strong_opp == 0 else \
                "SINGLE_HORIZON" if npos + nneg == 1 else "NONE" if npos + nneg == 0 else "CONFLICT"
            out.append({"inst": inst, "ev": e, "metric": col, "n_pass_pos": npos, "n_pass_neg": nneg,
                        "sign_agree_of_4": int(same), "strong_opposite": int(strong_opp),
                        "t_by_hz": "; ".join(f"{h}:{t:.1f}" for h, t in zip(g.hz, g[f"t_{col}"])), "verdict": verdict})
    return pd.DataFrame(out)


def zones(inst, df):
    """Part 2: location zones inside frozen qualified ranges (control WITHOUT position)."""
    rows = []
    edges = [-np.inf, 0, 0.2, 0.4, 0.6, 0.8, 1.0, np.inf]
    names = ["BELOW", "LOWER_EDGE", "LOWER_HALF", "MID", "UPPER_HALF", "UPPER_EDGE", "ABOVE"]
    keys = ["year", "tier", "volT", "clock"]
    base = attach_control(df[["sd"] + keys + OUTC].copy(), df, keys)
    for hz in INTRA + ["PRTH", "5D", "OR30"]:
        rp = df[f"rpos_{hz}"]
        m = rp.notna() & df.rth
        z = pd.cut(rp[m], edges, labels=names, right=False)
        x = base[m].assign(zone=z.values)
        for zn, g in x.groupby("zone", observed=True):
            r = {"inst": inst, "hz": hz, "zone": zn, "n_bars": len(g), "n_sess": g.sd.nunique()}
            for col in ("d_ret60", "d_fp05", "d_frange60", "d_mfe60", "d_mae60"):
                mm, t, _ = cl_t(g, col)
                r[f"mean_{col}"] = mm; r[f"t_{col}"] = t
            r["sd_ret60"] = g.ret60.std()
            r.update(fold_block(g, "d_ret60"))
            rows.append(r)
    return pd.DataFrame(rows)


def balance_state(inst, df):
    """Q1: does qualified balance / compression carry information? control matched incl. position bucket."""
    rows = []
    for hz in INTRA:
        keys = ctl_keys(hz)
        x = attach_control(df[["sd"] + keys + OUTC + [f"qual_{hz}", f"comp_{hz}", f"state_{hz}"]].copy(), df, keys)
        x = x[df.rth.values]
        for lab_, m in (("QUALIFIED_BALANCE", x[f"qual_{hz}"]), ("COMPRESSION", x[f"comp_{hz}"]),
                        ("NOT_QUALIFIED", ~x[f"qual_{hz}"])):
            g = x[m.values]
            r = {"inst": inst, "hz": hz, "state": lab_, "n_bars": len(g)}
            for col in ("d_ret60", "d_frange60", "d_mfe60", "d_mae60", "d_fp05"):
                mm, t, _ = cl_t(g, col)
                r[f"mean_{col}"] = mm; r[f"t_{col}"] = t
            r.update(fold_block(g, "d_frange60")); r.update(fold_block(g, "d_ret60"))
            rows.append(r)
        for sc, g in x.groupby(f"state_{hz}"):
            r = {"inst": inst, "hz": hz, "state": "SM_" + R.STATES[int(sc)], "n_bars": len(g)}
            for col in ("d_ret60", "d_frange60", "d_mfe60", "d_mae60", "d_fp05"):
                mm, t, _ = cl_t(g, col)
                r[f"mean_{col}"] = mm; r[f"t_{col}"] = t
            r.update(fold_block(g, "d_frange60")); r.update(fold_block(g, "d_ret60"))
            rows.append(r)
    return pd.DataFrame(rows)


def transitions(inst, df, ev):
    rows = []
    chains = [("L_SWEEP", "L_RECLAIM"), ("L_RECLAIM", "L_RETEST"), ("L_RETEST", "L_RETEST_HOLD"),
              ("L_RETEST_HOLD", "L_RESUMPTION"), ("L_SWEEP", "L_FAILED_RECLAIM"),
              ("U_SWEEP", "U_RECLAIM"), ("U_RECLAIM", "U_RETEST"), ("U_RETEST", "U_RETEST_HOLD"),
              ("U_RETEST_HOLD", "U_RESUMPTION"),
              ("UB_BREAK", "UB_ACCEPT"), ("UB_BREAK", "UB_FAILED_ACCEPT"), ("UB_ACCEPT", "UB_RETEST_HOLD"),
              ("UB_ACCEPT", "UB_REENTRY"), ("UB_RETEST_HOLD", "UB_RESUMED"),
              ("DB_BREAK", "DB_ACCEPT"), ("DB_BREAK", "DB_FAILED_ACCEPT"), ("DB_ACCEPT", "DB_RETEST_HOLD"),
              ("DB_ACCEPT", "DB_REENTRY"), ("DB_RETEST_HOLD", "DB_RESUMED")]
    cnt = ev.groupby(["hz", "ev"]).size()
    for hz in ev.hz.unique():
        for a, b in chains:
            na = cnt.get((hz, a), 0); nb = cnt.get((hz, b), 0)
            rows.append({"inst": inst, "hz": hz, "from": a, "to": b, "n_from": int(na), "n_to": int(nb),
                         "p": nb / na if na else np.nan})
    # per-bar state transition matrix (changes only)
    mats = []
    for hz in INTRA + ["PRTH"]:
        s = df[f"state_{hz}"].values
        ch = np.where(s[1:] != s[:-1])[0]
        m = pd.crosstab(pd.Series(np.array(R.STATES)[s[ch]], name="from"), pd.Series(np.array(R.STATES)[s[ch + 1]], name="to"),
                        normalize="index")
        m = m.stack().rename("p").reset_index(); m["inst"] = inst; m["hz"] = hz
        mats.append(m)
    return pd.DataFrame(rows), pd.concat(mats)


def nested(inst, df, et):
    """Part 3: descriptive alignment map (all RTH bars) + conditional event effects by alignment."""
    rows = []
    keys0 = ["year", "tier", "volT", "clock"]
    x = attach_control(df[["sd"] + keys0 + ["pbin60", "align"] + OUTC].copy(), df, keys0)
    x2 = attach_control(df[["sd"] + keys0 + ["pbin60", "align"] + OUTC].copy(), df, keys0 + ["pbin60"], prefix="c2_")
    for al in ("MULTI_LOW", "MULTI_HIGH", "MID_CLUSTER", "MIXED"):
        m = (x["align"] == al) & df.rth.values
        r = {"inst": inst, "scope": "ALL_RTH_BARS", "hz": "-", "ev": "-", "align": al, "n": int(m.sum())}
        for col in ("d_ret60", "d_fp05", "d_mfe60", "d_mae60"):
            mm, t, _ = cl_t(x[m], col); r[f"mean_{col}"] = mm; r[f"t_{col}"] = t
            mm, t, _ = cl_t(x2[m], col); r[f"pos60ctl_mean_{col}"] = mm; r[f"pos60ctl_t_{col}"] = t
        r.update(fold_block(x2[m], "d_ret60"))
        rows.append(r)
    for (hz, e), g in et[et.ev.isin(["L_RECLAIM", "L_RETEST_HOLD", "L_RESUMPTION", "UB_ACCEPT", "UB_RETEST_HOLD",
                                      "U_RECLAIM", "U_RETEST_HOLD", "DB_ACCEPT"])].groupby(["hz", "ev"]):
        for al, gg in g.groupby("align"):
            if len(gg) < 30:
                continue
            r = {"inst": inst, "scope": "EVENT", "hz": hz, "ev": e, "align": al, "n": len(gg)}
            for col in ("d_ret60", "d_fp05", "d_mfe60", "d_mae60"):
                mm, t, _ = cl_t(gg, col); r[f"mean_{col}"] = mm; r[f"t_{col}"] = t
            r.update(fold_block(gg, "d_ret60"))
            # difference vs the same event in other alignment classes
            rest = g[g["align"] != al]
            ma, ta, _ = cr_mean_t(gg.d_ret60.values, gg.sd.values); mb, tb, _ = cr_mean_t(rest.d_ret60.values, rest.sd.values)
            se = np.sqrt((ma / ta) ** 2 + (mb / tb) ** 2) if ta and tb and not np.isnan(ta) and not np.isnan(tb) else np.nan
            r["diff_vs_other_align"] = ma - mb; r["t_diff"] = (ma - mb) / se if se else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


def destination(inst, df, ev, bars_o, bars_h, bars_l):
    rows = []
    atrD = df.atrD.values
    spec = {"L_RECLAIM": 1, "L_RETEST_HOLD": 1, "U_RECLAIM": -1, "U_RETEST_HOLD": -1, "UB_ACCEPT": 1,
            "UB_RETEST_HOLD": 1, "DB_ACCEPT": -1, "DB_RETEST_HOLD": -1}
    evs = []
    for (hz, e), g in ev[ev.ev.isin(spec)].groupby(["hz", "ev"]):
        d = spec[e]
        w = (g.rH - g.rL).values; mid = (g.rH + g.rL).values / 2
        if e.startswith("L_") or e.startswith("U_"):
            inval = g.x.values; opp = g.rH.values if d > 0 else g.rL.values
        else:
            inval = mid; opp = (g.rH + w).values if d > 0 else (g.rL - w).values
        H = int(g.H.iloc[0]); Hmax = int(min(max(4 * H, 20), 80))
        res = R.destinations(bars_o, bars_h, bars_l, atrD, g.bar.values.astype(np.int64), np.full(len(g), d, np.int64),
                             inval.astype(float), mid.astype(float), opp.astype(float), w.astype(float), Hmax)
        hit_mid, t_mid, hit_opp, t_opp, mae_pre, mfe_post, mfe_all, hitR, hitA = res
        x = g.assign(hit_mid=hit_mid, t_mid=t_mid, hit_opp=hit_opp, t_opp=t_opp, mae_pre=mae_pre, mfe_post=mfe_post,
                     mfe_all=mfe_all, w_atr=w / atrD[g.bar.values], sd=df.sd.values[g.bar.values],
                     loc_vol=df[f"wn_{hz}"].values[g.bar.values] if f"wn_{hz}" in df else np.nan, Hmax=Hmax)
        for k, mlt in enumerate((0.5, 1.0, 1.5, 2.0)):
            x[f"hitR{mlt}"] = hitR[:, k]; x[f"hitA{mlt}"] = hitA[:, k]
        x = x[x.hit_mid.notna() & (x.w_atr > 0)]
        if len(x) < 50:
            continue
        # ATR-only survival curve from pooled events of this (hz, ev): predicted P(MFE >= m * width)
        mf = np.sort(x.mfe_all.values)
        surv = lambda d_: 1 - np.searchsorted(mf, d_, side="left") / len(mf)  # noqa: E731
        r = {"inst": inst, "hz": hz, "ev": e, "n": len(x), "n_sess": x.sd.nunique(), "Hmax_bars": Hmax,
             "P_mid_before_inval": x.hit_mid.mean(), "P_opp_before_inval": x.hit_opp.mean(),
             "med_bars_to_mid": x.t_mid.median(), "med_bars_to_opp": x.t_opp.median(),
             "mean_MAE_before_mid_atr": x.mae_pre.mean(), "mean_MFE_after_mid_atr": x.mfe_post.mean(),
             "w_atr_median": x.w_atr.median()}
        for mlt in (0.5, 1.0, 1.5, 2.0):
            r[f"P_hit_{mlt}R"] = x[f"hitR{mlt}"].mean(); r[f"P_hit_{mlt}ATR"] = x[f"hitA{mlt}"].mean()
            pred = surv(mlt * x.w_atr.values)
            ex = x[f"hitR{mlt}"].values - pred
            mu_, t_, _ = cr_mean_t(ex, x.sd.values)
            r[f"excess_vs_ATRonly_{mlt}R"] = mu_; r[f"t_excess_{mlt}R"] = t_
        # rank correlation between width and progress; partial on local vol (width in local-ATR units is wn)
        rk = x[["mfe_all", "w_atr"]].rank()
        r["spearman_mfe_width"] = rk.corr().iloc[0, 1]
        if x.loc_vol.notna().sum() > 50:
            lv = (x.w_atr / x.loc_vol).rank()   # local-vol proxy (ATR-units per local-vol unit)
            a = rk.mfe_all - np.polyval(np.polyfit(lv, rk.mfe_all, 1), lv)
            bb = rk.w_atr - np.polyval(np.polyfit(lv, rk.w_atr, 1), lv)
            r["partial_spearman_mfe_width_given_localvol"] = np.corrcoef(a, bb)[0, 1]
        for f, (a0, b0) in FOLDS.items():
            s = x[(x.sd >= pd.Timestamp(a0)) & (x.sd <= pd.Timestamp(b0))]
            if len(s) > 30:
                r[f"{f}_excess_1.0R"] = float(np.mean(s["hitR1.0"].values - surv(s.w_atr.values)))
                r[f"{f}_spearman"] = s[["mfe_all", "w_atr"]].rank().corr().iloc[0, 1]
        rows.append(r)
        evs.append(x.assign(inst=inst))
    return pd.DataFrame(rows), (pd.concat(evs) if evs else pd.DataFrame())


def main():
    from t43 import lab, v6lab
    os.makedirs(TAB, exist_ok=True)
    acc = {k: [] for k in ("mech", "z", "bal", "tr", "mat", "nest", "dest")}
    for inst in sys.argv[1:] or ("ES", "MNQ", "ES5", "MNQ5"):
        df, ev = load(inst)
        b, _ = v6lab.load(inst, lab.DEV_END)
        assert len(b) == len(df)
        print(inst, "loaded", len(df), len(ev), flush=True)
        et = event_table(inst, df, ev)
        et.to_parquet(f"{OUT}/{inst}_DEV/events_ctl.parquet")
        acc["mech"].append(info_mechanisms(inst, et, df)); print(inst, "mech done", flush=True)
        tr, mat = transitions(inst, df, ev); acc["tr"].append(tr); acc["mat"].append(mat)
        acc["bal"].append(balance_state(inst, df)); print(inst, "balance done", flush=True)
        d, dx = destination(inst, df, ev, b.o.values, b.h.values, b.l.values); acc["dest"].append(d)
        dx.to_parquet(f"{OUT}/{inst}_DEV/destination_events.parquet")
        if not inst.endswith("5"):
            acc["z"].append(zones(inst, df))
            acc["nest"].append(nested(inst, df, et))
        print(inst, "done", flush=True)
    tag = "_".join(sys.argv[1:]) or "ALL"
    names = {"mech": "M04_M05_mechanism_info", "z": "M01_zone_information", "bal": "M02_balance_state_info",
             "tr": "M02_event_transitions", "mat": "M02_state_transition_matrix", "nest": "M03_nested_alignment",
             "dest": "M06_destinations"}
    for k, v in acc.items():
        if v:
            pd.concat(v).to_csv(f"{TAB}/{names[k]}__{tag}.csv", index=False)
    ms = mech_stability(pd.concat(acc["mech"]))
    ms.to_csv(f"{TAB}/M10_mechanism_stability__{tag}.csv", index=False)


if __name__ == "__main__":
    main()
