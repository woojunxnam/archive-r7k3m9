"""TEST43-M Part 12 (reduction: avoided adverse vs forgone favourable) and Part 13 (add now vs wait vs no add).
DEV only.  Usage: python m_redadd.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments, lab, v6a, v6lab  # noqa: E402
from t43.mstats import cr_mean_t  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "m")
TAB = f"{OUT}/tables"
SL = {c["id"]: c for c in json.load(open(os.path.join(os.path.dirname(__file__), "..", "out", "v6", "shortlist.json")))}
REF = {"ES": "ES_robust_A_MOD_1", "MNQ": "MNQ_robust_A_MOD_2"}   # representative untouched V6A controls
FOLDS = {"F1": ("1900", "2020-12-31"), "F2": ("2021-01-01", "2022-12-31"), "F3": ("2023-01-01", "2024-12-31")}
RED_EVENTS = ["U_SWEEP", "U_RECLAIM", "U_RETEST_HOLD", "U_RESUMPTION", "UB_FAILED_ACCEPT", "UB_REENTRY",
              "DB_BREAK", "DB_ACCEPT", "L_FAILED_RECLAIM", "L_FAILED_RETEST"]
ADD_PAIRS = [("L_SWEEP", "L_RECLAIM"), ("L_RECLAIM", "L_RETEST_HOLD"), ("L_RETEST_HOLD", "L_RESUMPTION"),
             ("UB_BREAK", "UB_ACCEPT"), ("UB_ACCEPT", "UB_RETEST_HOLD"), ("DB_ACCEPT", "DB_REENTRY"),
             ("L_FAILED_RECLAIM", "L_RECLAIM")]


@njit(cache=True)
def path_stats(o, h, l, c, entry_bar, exit_bar):
    """Per trade (1 contract long): entry at o[entry_bar], exit at c[exit_bar]; MFE/MAE (points) and bars to recover."""
    m = len(entry_bar)
    pnl = np.full(m, np.nan); mfe = np.full(m, np.nan); mae = np.full(m, np.nan); rec = np.full(m, np.nan)
    for k in range(m):
        a = entry_bar[k]; b = exit_bar[k]
        if a < 0 or b < a or b >= len(c):
            continue
        e = o[a]; mx = 0.0; mn = 0.0; below = -1; r = -1
        for j in range(a, b + 1):
            mx = max(mx, h[j] - e); mn = min(mn, l[j] - e)
            if below < 0 and l[j] < e:
                below = j
            if below >= 0 and r < 0 and c[j] >= e and j > below:
                r = j - below
        pnl[k] = c[b] - e; mfe[k] = mx; mae[k] = mn
        if below >= 0:
            rec[k] = r if r >= 0 else np.nan
        else:
            rec[k] = 0.0
    return pnl, mfe, mae, rec


def reduction(inst, df, ev, pos, pv, fric1):
    rows = []
    x = ev[ev.ev.isin(RED_EVENTS) & df.rth.values[ev.bar.values]].copy()
    x = x.join(df[["sd", "atrD", "ret30", "ret60", "ret120", "mfe30", "mae30", "mfe60", "mae60", "mfe120", "mae120"]],
               on="bar")
    x["p"] = pos[x.bar.values]
    x["r"] = x.p - np.floor(x.p * 0.5 + 0.5)          # reduce by ~half of the live V6 position
    x = x[x.r > 0]
    for (hz, e), g in x.groupby(["hz", "ev"]):
        if len(g) < 30:
            continue
        r = {"inst": inst, "ref": REF[inst], "hz": hz, "ev": e, "n": len(g), "n_sess": g.sd.nunique(),
             "mean_reduced_qty": g.r.mean()}
        for hname, hh in (("30m", "30"), ("60m", "60"), ("120m", "120")):
            usd = g.r * pv * g.atrD
            avoided = (usd * np.maximum(0, -g[f"mae{hh}"])).sum()
            forgone = (usd * np.maximum(0, g[f"mfe{hh}"])).sum()
            held = (usd * g[f"ret{hh}"]).sum()
            fr = (2 * g.r * fric1).sum()
            r[f"avoided_adverse_{hname}"] = avoided; r[f"forgone_favourable_{hname}"] = forgone
            r[f"net_benefit_{hname}"] = -held - fr
            r[f"share_helped_{hname}"] = float((g[f"ret{hh}"] < 0).mean())
            for f, (a, b) in FOLDS.items():
                s = g[(g.sd >= pd.Timestamp(a)) & (g.sd <= pd.Timestamp(b))]
                r[f"{f}_net_benefit_{hname}"] = float((-(s.r * pv * s.atrD * s[f"ret{hh}"]) - 2 * s.r * fric1).sum())
        rows.append(r)
    return pd.DataFrame(rows)


def add_model(inst, df, ev, b, pv, fric1):
    rows = []
    o = b.o.values; h = b.h.values; l = b.l.values; c = b.c.values
    n = len(c)
    rth = df.rth.values
    for hz in ev.hz.unique():
        e_h = ev[ev.hz == hz]
        for first, conf in ADD_PAIRS:
            A = e_h[(e_h.ev == first) & rth[e_h.bar.values]]
            C = e_h[e_h.ev == conf]
            if len(A) < 30:
                continue
            cmap = C.groupby("rid").bar.apply(np.array).to_dict()
            ent_now = A.bar.values + 1
            ex = np.minimum(A.bar.values + 40, n - 1)
            ent_wait = np.full(len(A), -1)
            for k, (rid, bb, xx) in enumerate(zip(A.rid.values, A.bar.values, ex)):
                cb = cmap.get(rid)
                if cb is not None:
                    later = cb[(cb > bb) & (cb < xx)]
                    if len(later):
                        ent_wait[k] = later[0] + 1
            ok = ex < n - 1
            pn, mfn, man, rcn = path_stats(o, h, l, c, ent_now[ok], ex[ok])
            pw, mfw, maw, rcw = path_stats(o, h, l, c, np.where(ent_wait[ok] <= ex[ok], ent_wait[ok], -1), ex[ok])
            sd = df.sd.values[A.bar.values[ok]]
            r = {"inst": inst, "hz": hz, "event": first, "confirmation": conf, "n": int(ok.sum()),
                 "wait_fill_rate": float(np.mean(~np.isnan(pw)))}
            r["NOW_pnl_usd"] = np.nanmean(pn) * pv - 2 * fric1
            r["NOW_mfe_usd"] = np.nanmean(mfn) * pv; r["NOW_mae_usd"] = np.nanmean(man) * pv
            r["NOW_recovery_bars_med"] = np.nanmedian(rcn); r["NOW_never_recovered"] = float(np.mean(np.isnan(rcn)))
            wf = ~np.isnan(pw)
            r["WAIT_pnl_usd_per_signal"] = (np.nansum(pw) * pv - 2 * fric1 * wf.sum()) / len(pw)
            r["WAIT_pnl_usd_per_fill"] = np.nanmean(pw) * pv - 2 * fric1 if wf.any() else np.nan
            r["WAIT_mfe_usd"] = np.nanmean(mfw) * pv; r["WAIT_mae_usd"] = np.nanmean(maw) * pv
            r["WAIT_recovery_bars_med"] = np.nanmedian(rcw)
            r["NO_ADD_pnl_usd"] = 0.0
            # session-clustered t for NOW pnl
            r["NOW_t"] = cr_mean_t(pn * pv - 2 * fric1, sd)[1]
            # unconditional drift benchmark: same clock, random bars (matched control on 120m outcome)
            r["NOW_minus_ctl_ret120_atr"] = float(np.nanmean(df.ret120.values[A.bar.values[ok]] -
                                                          df["c_ret120"].values[A.bar.values[ok]])) if "c_ret120" in df else np.nan
            for f, (a, b_) in FOLDS.items():
                mm = (sd >= np.datetime64(a)) & (sd <= np.datetime64(b_))
                r[f"{f}_NOW_pnl_usd"] = np.nanmean(pn[mm]) * pv - 2 * fric1 if mm.sum() > 10 else np.nan
                r[f"{f}_WAIT_pnl_usd_per_signal"] = (np.nansum(pw[mm]) * pv - 2 * fric1 * (~np.isnan(pw[mm])).sum()) / max(1, mm.sum())
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    red, add = [], []
    for inst in ("ES", "MNQ"):
        b, f = v6lab.load(inst, lab.DEV_END)
        df = pd.read_parquet(f"{OUT}/{inst}_DEV/bars.parquet")
        keys = ["year", "tier", "volT", "clock", "pbin60"]
        cm = df.groupby(keys)["ret120"].mean().rename("c_ret120")
        df = df.join(cm, on=keys)
        ev = pd.read_parquet(f"{OUT}/{inst}_DEV/events.parquet")
        ev = ev[ev.hz.isin(["15m", "30m", "60m", "120m", "PRTH", "OR30"])]
        prof = instruments.PROFILES[v6lab.PROF[inst]]
        pv = prof["point_value"]; fric1 = prof["commission_side"] + prof["tick_value"]
        cand = SL[REF[inst]]
        p = v6lab.inst_params(inst); p.update(cand["params"])
        r = v6a.run(b, f, v6a.make_params(**p))
        red.append(reduction(inst, df, ev, r["pos"], pv, fric1))
        add.append(add_model(inst, df, ev, b, pv, fric1))
        print(inst, "done", flush=True)
    pd.concat(red).to_csv(f"{TAB}/M14_reduction_avoided_vs_forgone.csv", index=False)
    pd.concat(add).to_csv(f"{TAB}/M14b_add_now_vs_wait.csv", index=False)


if __name__ == "__main__":
    main()
