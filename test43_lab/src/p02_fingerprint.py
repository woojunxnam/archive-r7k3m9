"""TEST43-P Phases 1-3: behavioural fingerprints (DEV), pairwise redundancy, behavioural clustering.
Standalone sleeve runs are stored for the portfolio simulator (runs cover DEV+VAL; everything reported here is DEV).
Usage: python p02_fingerprint.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments, lab, sleeves as S, v6lab  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out", "p")
DEV_END = lab.DEV_END
ALL = S.ELIGIBLE + S.SHADOW


def regimes(inst):
    b, f = v6lab.load(inst)
    g = pd.DataFrame({"sd": b.session_date.values, "tier": f["d_TIER"], "atrp": f["d_ATR20_pct"],
                      "tr100": f["d_TREND100"]}).groupby("sd").first()
    g["vol"] = np.where(g.atrp >= 2 / 3, "HIVOL", np.where(g.atrp <= 1 / 3, "LOVOL", "MIDVOL"))
    g["trend"] = np.where(g.tr100 == 1, "TREND", "RANGE_NEUTRAL")
    g["tierlab"] = np.array(["BEAR", "NEUTRAL", "BULL", "BULL"])[g.tier.clip(0, 3).astype(int)]
    return g


def roll_stats(pnl, n):
    r = pnl.rolling(n).sum().dropna()
    return (float((r > 0).mean()), float(r.min())) if len(r) else (np.nan, np.nan)


def fingerprint(cid, c, b, res, d, reg):
    inst = c["inst"]; prof = instruments.PROFILES[v6lab.PROF[inst]]; pv = prof["point_value"]
    dd = d[d.index <= DEV_END]
    st = lab.period_stats(dd)
    mb = v6lab.matched_beta(inst, d, "DEV")
    n = len(dd)
    r = {"id": cid, "inst": inst, "arch": c["arch"], "role": "ELIGIBLE" if cid in S.ELIGIBLE else "SHADOW",
         "days": n, "total": dd.pnl.sum(), "avg_daily": st["avg_daily"], "median_day": dd.pnl.median(),
         "pos_day_share": float((dd.pnl > 0).mean()), "max_dd": st["max_dd"], "worst_day": st["worst_day"],
         "mb_total": mb["mb_avg"] * n, "mb_avg": mb["mb_avg"], "excess_vs_mb": st["avg_daily"] - mb["mb_avg"],
         "ret_dd": st["avg_daily"] / st["max_dd"] if st["max_dd"] > 0 else np.nan}
    m = (b.session_date <= DEV_END).values
    pos = res["pos"][m].astype(float); rth = b.in_rth.values[m]
    r["avg_contracts"] = pos.mean(); r["avg_on_contracts"] = pos[~rth].mean(); r["max_contracts"] = pos.max()
    fb = res["f_bar"]; fq = np.abs(res["f_qty"]); fm = fb < m.sum()
    r["fills_per_day"] = fm.sum() / n
    r["friction_per_day"] = fq[fm].sum() * (prof["commission_side"] + prof["tick_value"]) / n
    ps = dd.pnl.sort_values(ascending=False)
    for k in (1, 3, 5):
        r[f"avg_ex_top{k}"] = (dd.pnl.sum() - ps.iloc[:k].sum()) / n
    for w, k in (("3m", 63), ("6m", 126), ("12m", 252)):
        r[f"roll{w}_pos_share"], r[f"roll{w}_min"] = roll_stats(dd.pnl, k)
    for lab_, (s_, e_) in (("PRE23", ("1900", "2022-12-31")), ("P23", ("2023-01-01", "2024-12-31")),
                          ("Y2020", ("2020-01-01", "2020-12-31")), ("Y2022", ("2022-01-01", "2022-12-31"))):
        x = dd[(dd.index >= s_) & (dd.index <= e_)]
        stx = lab.period_stats(x)
        r[f"{lab_}_total"] = x.pnl.sum(); r[f"{lab_}_avg"] = stx["avg_daily"]; r[f"{lab_}_max_dd"] = stx["max_dd"]
        r[f"{lab_}_worst"] = stx["worst_day"]
        per = {"PRE23": "PRE23", "P23": None, "Y2020": "Y2020", "Y2022": "Y2022"}[lab_]
        if per:
            r[f"{lab_}_mb_avg"] = v6lab.matched_beta(inst, d, per)["mb_avg"]
            r[f"{lab_}_excess"] = stx["avg_daily"] - r[f"{lab_}_mb_avg"]
    j = dd.join(reg, how="left")
    for col, vals in (("vol", ("HIVOL", "LOVOL")), ("trend", ("TREND", "RANGE_NEUTRAL")), ("tierlab", ("BEAR", "NEUTRAL", "BULL"))):
        for v in vals:
            x = j[j[col] == v].pnl
            r[f"{v}_avg"] = x.mean(); r[f"{v}_days"] = len(x)
    c_ = b.c.values; o_ = b.o.values; p_ = res["pos"].astype(float)
    prev_c = np.r_[o_[0], c_[:-1]]; pp = np.r_[0.0, p_[:-1]]
    mtm = (pp * (o_ - prev_c) + p_ * (c_ - o_)) * pv
    mod = b["mod"].values; rt = b.in_rth.values
    r["gross_rth_morning"] = mtm[m & rt & (mod < 660)].sum(); r["gross_rth_midday"] = mtm[m & rt & (mod >= 660) & (mod < 840)].sum()
    r["gross_rth_late"] = mtm[m & rt & (mod >= 840)].sum(); r["gross_overnight"] = mtm[m & ~rt].sum()
    return r


def jacc(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else np.nan


def main():
    os.makedirs(OUT, exist_ok=True)
    C = S.candidates()
    regs = {i: regimes(i) for i in ("ES", "MNQ")}
    fps, daily, bar_pos, on_daily, marg = [], {}, {}, {}, {}
    for cid in ALL:
        c = C[cid]
        b, res, d = S.run_sleeve(c)
        fps.append(fingerprint(cid, c, b, res, d, regs[c["inst"]]))
        daily[cid] = d.pnl
        s = pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "rth": b.in_rth.values,
                          "pos": res["pos"].astype(float), "desired": S.desired(res)})
        s.to_parquet(f"{OUT}/sleeve_{cid}.parquet")
        bar_pos[cid] = s.set_index("t").pos
        on_daily[cid] = s[~s.rth].groupby("sd").pos.mean()
        prof = instruments.PROFILES[v6lab.PROF[c["inst"]]]
        raw = (b.c - b.cum_adjustment.astype(float)).values
        fr = np.where(b.in_rth.values, instruments.margin_frac(prof, "intraday"), instruments.margin_frac(prof, "overnight"))
        util = res["pos"] * raw * prof["point_value"] * fr / np.maximum(res["equity"], 1.0)
        marg[cid] = pd.Series(util, index=b.session_date.values).groupby(level=0).max()
        print(cid, "done", flush=True)
    fp = pd.DataFrame(fps)
    fp.to_csv(f"{OUT}/p03_fingerprint_DEV.csv", index=False)
    D = pd.DataFrame(daily).fillna(0.0)
    D.to_csv(f"{OUT}/p03_daily_pnl_all_candidates_DV.csv")   # aligned by session_date (DEV+VAL; VAL not used before freeze)
    Dd = D[D.index <= DEV_END]
    # ---------------- Phase 2: redundancy (DEV)
    W = Dd.resample("W").sum() if isinstance(Dd.index, pd.DatetimeIndex) else Dd
    P = pd.DataFrame(bar_pos); P = P[P.index <= pd.Timestamp(DEV_END) + pd.Timedelta(days=1)]
    P30 = P.iloc[::10]                                # 30-min sample of actual positions
    ON = pd.DataFrame(on_daily).loc[:DEV_END]
    MG = pd.DataFrame(marg).loc[:DEV_END]
    sig = Dd.std()
    under = {}
    for cid in ALL:
        eq = Dd[cid].cumsum(); ddv = eq.cummax() - eq
        under[cid] = ddv > 0.25 * ddv.max()
    y20 = (Dd.index.year == 2020); y22 = (Dd.index.year == 2022)
    hv = regs["ES"].reindex(Dd.index).vol.values == "HIVOL"
    rows = []
    for i, a in enumerate(ALL):
        for bb in ALL[i + 1:]:
            r = {"A": a, "B": bb, "daily_corr": Dd[a].corr(Dd[bb]), "weekly_corr": W[a].corr(W[bb]),
                 "position_corr": P30[a].corr(P30[bb]), "overnight_exposure_corr": ON[a].corr(ON[bb]),
                 "dd_overlap": jacc(under[a].values, under[bb].values),
                 "worst20_overlap": jacc(Dd[a].rank(method="first") <= 20, Dd[bb].rank(method="first") <= 20),
                 "loss2020_overlap": jacc((Dd[a] < 0).values & y20, (Dd[bb] < 0).values & y20),
                 "loss2022_overlap": jacc((Dd[a] < 0).values & y22, (Dd[bb] < 0).values & y22),
                 "hivol_loss_overlap": jacc((Dd[a] < 0).values & hv, (Dd[bb] < 0).values & hv),
                 "margin_corr": MG[a].corr(MG[bb])}
            # incremental: A alone vs A + B at equal daily-vol risk
            for x, y, tag in ((a, bb, "B_to_A"), (bb, a, "A_to_B")):
                base = Dd[x] / sig[x]; comb = (Dd[x] / sig[x] + Dd[y] / sig[y]) / 2
                def m_(s):
                    eq = s.cumsum(); mdd = (eq.cummax() - eq).max()
                    return s.mean(), mdd, s.min(), s.mean() / mdd if mdd > 0 else np.nan
                b0 = m_(base); b1 = m_(comb)
                r[f"incr_{tag}_d_avg"] = b1[0] - b0[0]; r[f"incr_{tag}_d_maxdd"] = b1[1] - b0[1]
                r[f"incr_{tag}_d_worst"] = b1[2] - b0[2]; r[f"incr_{tag}_retdd_ratio"] = b1[3] / b0[3]
            rows.append(r)
    red = pd.DataFrame(rows)
    red.to_csv(f"{OUT}/p04_pairwise_redundancy_DEV.csv", index=False)
    # ---------------- Phase 3: behavioural clustering (actual behaviour)
    E = S.ELIGIBLE
    sim = pd.DataFrame(np.eye(len(E)), index=E, columns=E)
    for _, r in red.iterrows():
        if r.A in E and r.B in E:
            s_ = 0.5 * r.daily_corr + 0.25 * r.position_corr + 0.25 * r.dd_overlap
            sim.loc[r.A, r.B] = sim.loc[r.B, r.A] = s_
    dist = (1 - sim).clip(lower=0)
    Z = linkage(squareform(dist.values, checks=False), "average")
    out = []
    for thr in (0.4, 0.5, 0.6):
        lab_ = fcluster(Z, t=thr, criterion="distance")
        out.append(pd.DataFrame({"id": E, "cut_distance": thr, "cluster": lab_}))
    cl = pd.concat(out)
    cl.to_csv(f"{OUT}/p05_clusters_DEV.csv", index=False)
    sim.to_csv(f"{OUT}/p05_similarity_matrix_DEV.csv")
    pd.set_option("display.width", 250)
    print(fp[["id", "avg_daily", "max_dd", "worst_day", "excess_vs_mb", "ret_dd", "Y2020_avg", "Y2022_avg", "Y2022_max_dd",
              "Y2022_excess", "avg_contracts", "fills_per_day", "friction_per_day"]].round(2).to_string(index=False))
    print(sim.round(2).to_string())
    print(cl.pivot(index="id", columns="cut_distance", values="cluster"))


if __name__ == "__main__":
    main()
