"""RUN-4 final aggregation: AB_PORTFOLIO_RESULTS.csv, PARETO_AB.csv, WEEKLY_ANALYSIS.csv, EXECUTION_STRESS.csv,
BOOTSTRAP_SUMMARY.csv. Block bootstrap on WEEKLY P&L (13-week blocks, 5000 draws) keeps time dependence.
ES-signal / MES-economics proxy backtest (in-sample; NOT OOS)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import run4_lib as L
from run4_analyze import pareto, load

ROOT = L.ROOT
SER = os.path.join(L.OUT, "series")
AB_AXES = [("wk_mean", "max"), ("max_dd", "max"), ("wk_worst", "max"), ("corr_weekly", "min"), ("dd_overlap_B_uw_given_A_uw", "min"),
           ("peak_contracts", "min"), ("peak_notional", "min"), ("pnl_per_contract_day", "max")]


def weekly_stats(dp, name):
    wk = dp.resample("W-FRI").sum()
    neg = (wk < 0).astype(int).values
    best = cur = 0
    for v in neg:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return dict(name=name, weeks=len(wk), wk_mean=wk.mean(), wk_median=wk.median(), wk_p10=wk.quantile(.1), wk_p25=wk.quantile(.25),
                wk_p75=wk.quantile(.75), wk_p90=wk.quantile(.9), wk_pos=(wk > 0).mean(), wk_ge1k=(wk >= 1000).mean(),
                wk_ge2k=(wk >= 2000).mean(), wk_ge3k=(wk >= 3000).mean(), wk_ge4k=(wk >= 4000).mean(), wk_le_m2k=(wk <= -2000).mean(),
                wk_le_m4k=(wk <= -4000).mean(), wk_worst=wk.min(), wk_worst_4w=wk.rolling(4).sum().min(), wk_longest_losing=best,
                weeks_to_4k_gap=4000 - wk.mean())


def block_bootstrap(w, name, B=5000, blk=13, seed=20260930):
    rng = np.random.default_rng(seed)
    w = np.asarray(w, float)
    n = len(w)
    rows = []
    for H in (52, n):
        ann, mdd, streak, rec = [], [], [], []
        for _ in range(B):
            idx = []
            while len(idx) < H:
                s0 = rng.integers(0, n - blk)
                idx.extend(range(s0, s0 + blk))
            x = w[np.array(idx[:H])]
            cum = np.cumsum(x)
            peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
            ddv = cum - peak
            mdd.append(ddv.min())
            ann.append(x.sum() * 52 / H)
            neg = (x < 0).astype(int); cur = bst = 0
            for v in neg:
                cur = cur + 1 if v else 0; bst = max(bst, cur)
            streak.append(bst)
            # recovery time: longest run of weeks below the running peak
            uw = ddv < 0; cur = bst = 0
            for v in uw:
                cur = cur + 1 if v else 0; bst = max(bst, cur)
            rec.append(bst)
        ann, mdd, streak, rec = map(np.asarray, (ann, mdd, streak, rec))
        rows.append(dict(name=name, horizon_weeks=H, ann_pnl_p05=np.percentile(ann, 5), ann_pnl_p50=np.percentile(ann, 50),
                         ann_pnl_p95=np.percentile(ann, 95), p_ann_loss=float((ann < 0).mean()), wk_mean_p50=np.percentile(ann, 50) / 52,
                         maxdd_p50=np.percentile(mdd, 50), maxdd_p05=np.percentile(mdd, 5), maxdd_p01=np.percentile(mdd, 1),
                         losing_streak_p50=np.percentile(streak, 50), losing_streak_p95=np.percentile(streak, 95),
                         underwater_weeks_p50=np.percentile(rec, 50), underwater_weeks_p95=np.percentile(rec, 95)))
    return rows


def main(finals):
    """finals: dict name -> ("A", config_id) | ("B", params dict) | ("AB", config_id)"""
    import run4_b_lib as BL
    if not BL.G:
        BL.init_b()
        import run4_b
        run4_b._variant_events()
    wrows, brows = [], []
    for name, (kind, ref) in finals.items():
        if kind == "A":
            d = pd.read_parquet(os.path.join(SER, f"{ref}_daily.parquet"))
            eq = d.equity; eq.index = pd.to_datetime(eq.index)
            dp = eq.diff().fillna(eq.iloc[0] - 150000.0)
        elif kind == "AB":
            dp = pd.read_parquet(os.path.join(SER, f"{ref}_portfolio_daily.parquet")).pnl
            dp.index = pd.to_datetime(dp.index)
        else:
            sig, _ = BL.signal_array(ref["events"], ref.get("cluster_min"))
            T = BL.trade_frame(BL.simulate(sig, ref, dict(slippage_ticks=1, penetration_ticks=1, commission_per_side=0.62), size=ref.get("size", 1)),
                               dict(commission_per_side=0.62, slippage_ticks=1), size=ref.get("size", 1))
            dp = T.groupby("day").net.sum()
            dp.index = pd.to_datetime(dp.index.astype(str))
            alld = pd.to_datetime(pd.Series(BL.G["days"]).astype(str))
            dp = dp.reindex(alld, fill_value=0.0)
        wrows.append(weekly_stats(dp, name))
        brows += block_bootstrap(dp.resample("W-FRI").sum().values, name)
    pd.DataFrame(wrows).to_csv(os.path.join(ROOT, "WEEKLY_ANALYSIS.csv"), index=False)
    pd.DataFrame(brows).to_csv(os.path.join(ROOT, "BOOTSTRAP_SUMMARY.csv"), index=False)
    # execution stress (A S5 + B S5)
    A = load("A"); B = load("B")
    rows = []
    if len(A):
        s5 = A[A.stage == "S5"]
        base = A.set_index("config_id")
        for _, r in s5.iterrows():
            p = base.loc[r.parent] if r.parent in base.index else None
            rows.append(dict(sleeve="A", config_id=r.config_id, parent=r.parent, note=r.note, exec=r["exec"], total_mtm=r.total_mtm,
                             base_total_mtm=p.total_mtm if p is not None else np.nan, max_mtm_dd=r.max_mtm_dd,
                             base_max_mtm_dd=p.max_mtm_dd if p is not None else np.nan, fs2022_min_equity=r.fs2022_min_equity,
                             base_fs2022_min_equity=p.fs2022_min_equity if p is not None else np.nan,
                             no_entry_fresh2022=r.fs2022_no_entry_days))
    if len(B):
        s5 = B[B.stage == "S5"]
        for _, r in s5.iterrows():
            rows.append(dict(sleeve="B", config_id=r.config_id, parent=r.parent, note=r.note, exec=r["exec"], net_pnl=r.net_pnl,
                             ev_net=r.ev_net, max_dd_daily=r.max_dd_daily, years_pos=r.years_pos, trades=r.trades))
    pd.DataFrame(rows).to_csv(os.path.join(ROOT, "EXECUTION_STRESS.csv"), index=False)
    AB = load("AB")
    if len(AB):
        AB["pareto"] = pareto(AB, AB_AXES)
        AB.drop(columns=["params"]).to_csv(os.path.join(ROOT, "AB_PORTFOLIO_RESULTS.csv"), index=False)
        AB[AB.pareto].drop(columns=["params"]).sort_values("wk_mean", ascending=False).to_csv(os.path.join(ROOT, "PARETO_AB.csv"), index=False)
    print(pd.DataFrame(wrows).round(2).to_string(index=False))
    print(pd.DataFrame(brows).round(1).to_string(index=False))


if __name__ == "__main__":
    main(json.load(open(sys.argv[1])))
