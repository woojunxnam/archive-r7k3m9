"""ALPHA_GAP_MAP_V1 + causal opportunity labelling (DISCOVERY region 2019-07-01 .. 2020-12-31 only).
Decision times every 15 min 09:45..15:45 (decision on bars end-stamped <= t, fill at the open of the next 1m bar).
Forward labels (research labels ONLY): +15/+30/+60/+120m, to 16:00, to 16:15, next 09:30 open (ATRd units, minus the
same-time/same-instrument discovery mean = drift-free excess).  Labels: HIGH_QUALITY_LONG (to-16:00 excess top quintile and
MAE <= 0.5 ATR), POOR_LONG (bottom quintile), HOLD_WORTH_MORE (to16:00 - +60m > 0.25 ATR), SECOND_CONTRACT_WORTH_MORE
(HQ while C43 holds exactly 1), NO_TRADE otherwise.  C43 intraday position = frozen TEST44 reproduction."""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402

OUT = os.path.join(P.PROG, "gapmap"); os.makedirs(OUT, exist_ok=True)
TIMES = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (0, 15, 30, 45) if (h, m) >= (9, 45) and (h, m) <= (15, 45)]
H = {"f15": 15, "f30": 30, "f60": 60, "f120": 120}


def features(mk, s, j, rel=None):
    """causal state at grid j (bars end-stamped <= M0+j)."""
    pn = mk.pn; a = mk.atr[s]; u = mk.u5[s]
    c = pn.Cf[s, j]; o = mk.open[s]
    H1 = pn.H[s, :j + 1]; L1 = pn.L[s, :j + 1]; Cc = pn.Cf[s, :j + 1]
    hi = np.nanmax(H1); lo = np.nanmin(L1)
    c5 = Cc[4::5] if j >= 4 else Cc[-1:]
    path = np.nansum(np.abs(np.diff(np.r_[o, c5])))
    tw = np.nanmean(c5)
    above = np.nanmean(c5 > np.r_[np.nan, np.nancumsum(c5)[:-1] / np.arange(1, len(c5))][: len(c5)]) if len(c5) > 1 else 0.5
    r = lambda k: (c - Cc[max(0, j - k)]) / a
    rng60 = (np.nanmax(H1[max(0, j - 60):]) - np.nanmin(L1[max(0, j - 60):])) / u
    rv30 = np.nanstd(np.diff(Cc[max(0, j - 30):])) * np.sqrt(5) / u if j > 5 else np.nan
    rv_day = np.nanstd(np.diff(Cc)) * np.sqrt(5) / u if j > 10 else np.nan
    od = (pn.Cf[s, min(j, C45.g("10:00"))] - o) / a
    return {"x_ret_open": (c - o) / a, "x_ret15": r(15), "x_ret30": r(30), "x_ret60": r(60), "x_eff": abs(c - o) / path if path > 0 else 0,
            "x_twap_dist": (c - tw) / u, "x_above_twap_share": above, "x_range_used": (hi - lo) / a, "x_pos_in_range": (c - lo) / (hi - lo) if hi > lo else 0.5,
            "x_from_high": (hi - c) / a, "x_from_low": (c - lo) / a, "x_bars_since_high": j - int(np.nanargmax(H1)), "x_bars_since_low": j - int(np.nanargmin(L1)),
            "x_rng60": rng60, "x_rv30": rv30, "x_rv_ratio": rv30 / rv_day if rv_day and rv_day > 0 else np.nan, "x_open_drive": od,
            "x_gap": mk.gap[s], "x_ret5d": mk.ret5[s], "x_bull": float(mk.bull[s]), "x_volt": mk.volt[s], "x_prev_ret": pn.p_ret[s] / a if a > 0 else np.nan,
            "x_rel": rel if rel is not None else np.nan}


def main():
    es, nq = E.setup()
    sess = es.pn.sess
    pE, pM = P.c43_positions(sess)
    disc = np.where((sess >= P.DISC[0]) & (sess <= P.DISC[1]))[0]
    rows = []
    for mk, pos in ((es, pE), (nq, pM)):
        other = nq if mk is es else es
        for s in disc:
            a = mk.atr[s]
            if not (a > 0) or not mk.pn.full[s]:
                continue
            for t in TIMES:
                j = C45.g(t); jf = j + 1
                px = mk.FP[s, jf]
                if np.isnan(px):
                    continue
                r = {"inst": mk.inst, "s": s, "date": sess[s], "time": t, "c43_pos": pos[s, j], "c43_pos_other": (pM if mk is es else pE)[s, j]}
                for k, h in H.items():
                    r[k] = (mk.FPb[s, min(jf + h, E.J1615)] - px) / a
                r["f1600"] = (mk.FPb[s, C45.g("16:00")] - px) / a; r["f1615"] = (mk.FPb[s, E.J1615] - px) / a
                r["fnext"] = (mk.FP[s + 1, 0] - px) / a if s + 1 < mk.n else np.nan
                r["mae1600"] = (px - np.nanmin(mk.pn.L[s, jf:C45.g("16:00") + 1])) / a
                ro = (mk.pn.Cf[s, j] - mk.open[s]) / a - (other.pn.Cf[s, j] - other.open[s]) / other.atr[s]
                r.update(features(mk, s, j, ro))
                rows.append(r)
    D = pd.DataFrame(rows)
    for k in list(H) + ["f1600", "f1615", "fnext"]:
        D[k + "_x"] = D[k] - D.groupby(["inst", "time"])[k].transform("mean")
    q = D.groupby("inst").f1600_x
    hi, lo = q.transform(lambda x: x.quantile(0.8)), q.transform(lambda x: x.quantile(0.2))
    D["HQ"] = (D.f1600_x >= hi) & (D.mae1600 <= 0.5)
    D["POOR"] = D.f1600_x <= lo
    D["HOLD_MORE"] = (D.f1600 - D.f60) > 0.25
    D["SECOND_MORE"] = D.HQ & (D.c43_pos == 1)
    D["label"] = np.select([D.HQ, D.POOR], ["HIGH_QUALITY_LONG", "POOR_LONG"], "NO_TRADE")
    D.to_parquet(f"{OUT}/opportunity_labels_discovery.parquet")
    # ---------------- gap map
    D["flat"] = D.c43_pos == 0
    G = D.groupby(["inst", "time"]).agg(n=("HQ", "size"), hq_share=("HQ", "mean"), poor_share=("POOR", "mean"), c43_flat_share=("flat", "mean"),
                                        hq_uncaptured=("HQ", lambda x: (x & D.loc[x.index, "flat"]).mean()),
                                        hold_more_share=("HOLD_MORE", "mean"), second_more=("SECOND_MORE", "mean"),
                                        f1600_x_when_flat=("f1600_x", lambda x: x[D.loc[x.index, "flat"]].mean()),
                                        f1600_x_when_long=("f1600_x", lambda x: x[~D.loc[x.index, "flat"]].mean())).reset_index()
    G.to_csv(f"{OUT}/ALPHA_GAP_MAP_V1_by_time.csv", index=False)
    # ---------------- causal-state information (Spearman IC vs drift-free excess)
    fx = [c for c in D.columns if c.startswith("x_")]
    ic = []
    for inst in ("ES", "MNQ"):
        for sub, m in (("all", np.ones(len(D), bool)), ("C43_flat", D.flat.values), ("C43_long", ~D.flat.values)):
            d = D[(D.inst == inst).values & m]
            for tgt in ("f60_x", "f1600_x", "fnext_x"):
                for f in fx:
                    ok = d[f].notna() & d[tgt].notna()
                    if ok.sum() < 200:
                        continue
                    ic.append({"inst": inst, "subset": sub, "target": tgt, "feature": f, "IC": spearmanr(d.loc[ok, f], d.loc[ok, tgt]).statistic, "n": int(ok.sum())})
    IC = pd.DataFrame(ic); IC.to_csv(f"{OUT}/state_information_IC.csv", index=False)
    # time-bucketed IC for the strongest features (AM / midday / PM)
    D["tb"] = pd.cut(D.time.str[:2].astype(int) + D.time.str[3:].astype(int) / 60, [9, 11, 13.5, 16], labels=["AM", "MID", "PM"])
    tb = []
    for (inst, b), d in D.groupby(["inst", "tb"], observed=True):
        for f in fx:
            ok = d[f].notna()
            tb.append({"inst": inst, "bucket": b, "feature": f, "IC_f1600": spearmanr(d.loc[ok, f], d.loc[ok, "f1600_x"]).statistic,
                       "IC_f60": spearmanr(d.loc[ok, f], d.loc[ok, "f60_x"]).statistic})
    TB = pd.DataFrame(tb); TB.to_csv(f"{OUT}/state_information_by_bucket.csv", index=False)
    # registry (summary rows)
    summ = G.groupby("inst").agg(hq_share=("hq_share", "mean"), hq_uncaptured=("hq_uncaptured", "mean"), c43_flat_share=("c43_flat_share", "mean"),
                                 hold_more_share=("hold_more_share", "mean"), second_more=("second_more", "mean")).reset_index()
    P.reg_append("ALPHA_GAP_MAP", [{"version": "V1", "region": "discovery 2019-07..2020-12", **r} for r in summ.to_dict("records")])
    pd.set_option("display.width", 250)
    print(G.round(3).to_string())
    top = IC[IC.subset == "all"].assign(a=lambda x: x.IC.abs()).sort_values("a", ascending=False).groupby(["inst", "target"]).head(8)
    print(top.round(3).to_string())
    print(IC[(IC.subset == "C43_flat") & (IC.target == "f1600_x")].assign(a=lambda x: x.IC.abs()).sort_values("a", ascending=False).head(12).round(3).to_string())
    print(TB.assign(a=lambda x: x.IC_f1600.abs()).sort_values("a", ascending=False).head(20).round(3).to_string())


if __name__ == "__main__":
    main()
