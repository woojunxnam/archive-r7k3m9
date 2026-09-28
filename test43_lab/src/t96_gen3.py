"""TEST96 Track A2 Generation 3 - FINAL (prereg 052c65b1): R1 ML TRADE/SKIP on the Q2 breadth-expansion base (economic target, nested chronological),
R2 Q2 overnight increment diagnostic, R3 daily breadth thrust."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t95_common as T  # noqa: E402
import t96_common as W  # noqa: E402
import t96_data as X  # noqa: E402
import t96_gen1 as G1  # noqa: E402
import t96_gen2 as G2  # noqa: E402

INSTS = G2.INSTS


def models():
    import lightgbm as lgb
    import xgboost as xgb
    from catboost import CatBoostRegressor
    sc = lambda m: make_pipeline(StandardScaler(), m)
    return {"Ridge": sc(Ridge(alpha=10.0)), "ElasticNet": sc(ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=5000)),
            "HistGB": HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=25, random_state=5),
            "RF": RandomForestRegressor(n_estimators=300, min_samples_leaf=20, random_state=5, n_jobs=-1),
            "ExtraTrees": ExtraTreesRegressor(n_estimators=300, min_samples_leaf=20, random_state=5, n_jobs=-1),
            "XGB": xgb.XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=5, verbosity=0),
            "LightGBM": lgb.LGBMRegressor(n_estimators=200, num_leaves=7, min_child_samples=25, learning_rate=0.05, random_state=5, verbose=-1),
            "CatBoost": CatBoostRegressor(iterations=300, depth=4, learning_rate=0.05, random_seed=5, verbose=0)}


def features(Is, inst, TR, br, u, rv):
    I = Is[inst]; mk = X.mkt(inst); rows = []
    for r in TR.itertuples(index=False):
        s, j = int(r.s), int(r.j) - 1
        rs = [(Is[k].C[s, j] - Is[k].FP[s, 0]) / Is[k].atr[s] for k in INSTS]; r30 = [(Is[k].C[s, j] - Is[k].C[s, j - 30]) / Is[k].atr[s] for k in INSTS]
        p = s - 1
        rows.append([j, br[s, j - 10], br[s, j - 20], *rs, *r30, float(np.std(r30)), rv[s, j], (I.FP[s, 0] - I.C[p, T.J15]) / I.atr[s],
                     (I.C[p, T.J15] - I.FP[p, 0]) / I.atr[p], mk.volt[s], float(mk.bull[s]), u[s, j]])
    return np.nan_to_num(np.array(rows, float))


def t61_u(Is):
    tsess, tm = K.t61_minutes(); ix = pd.Index(tsess).get_indexer(Is["ES"].sess)
    g = lambda q: np.where(ix[:, None] >= 0, q[np.clip(ix, 0, None)], 0.0)
    ratio = (Is["ES"].atr * Is["ES"].pv) / (Is["MNQ"].atr * Is["MNQ"].pv)
    return g(tm["final_target_MNQ"]) + g(tm["final_target_MES"]) * ratio[:, None]


def r1(ctx, Is):
    b2 = G2.q2(Is); cond = {k: G2.breadth_cond(Is[k]) for k in INSTS}; br = sum(cond[k].astype(int) for k in INSTS); u = t61_u(Is)
    res = []; daily = {}
    for inst in INSTS:
        I = Is[inst]; occ = ctx["occ"].get(inst); TR = b2[inst][0].reset_index(drop=True)
        D = W.simulate(I, TR, occ=occ)
        TR = TR.merge(D[["s", "j_in", "net"]].rename(columns={"j_in": "j"}), on=["s", "j"], how="inner").reset_index(drop=True)
        Xf = features(Is, inst, TR, br, u, A.rel_volume(I)); y = TR.net.values; dates = I.sess[TR.s.values]
        picks = {}
        for mname, m in models().items():
            keep = np.zeros(len(TR), bool); tested = np.zeros(len(TR), bool)
            for nm, a, b in B.FOLDS:
                tr = np.asarray(dates < a); te = np.asarray((dates >= a) & (dates <= b))
                if tr.sum() < 150 or te.sum() == 0:
                    continue
                import sklearn.base
                mm = sklearn.base.clone(m).fit(Xf[tr], y[tr]); keep[te] = mm.predict(Xf[te]) > 0; tested |= te
            picks[mname] = (keep, tested)
        keep, tested = picks["Ridge"]
        base_pt = float(y[tested].mean()); bk = A.buckets(I)
        sel = lambda k: TR[k][["s", "j", "s_out", "j_out"]]
        o, Dd, d = W.run_module(I, f"R1_ML_Q2_RIDGE_{inst}", sel(keep), bk, ctx["main"], occ=occ, plateau_TRs=[sel(picks["HistGB"][0]), sel(picks["ElasticNet"][0])],
                                extra={"base_usd_trade_same_folds": base_pt, "base_trades_same_folds": int(tested.sum()),
                                       **{f"alt_{k}_usd_trade": float(y[v[0]].mean()) if v[0].any() else np.nan for k, v in picks.items()},
                                       **{f"alt_{k}_n": int(v[0].sum()) for k, v in picks.items()}})
        o["beats_base_per_trade"] = bool(o["usd_per_trade"] > base_pt)
        res.append(o); daily[o["module"]] = d; print(o["module"], o["trades"], round(o["avg_day"], 2), round(o["usd_per_trade"], 1), round(base_pt, 1), o["STANDALONE_PASS"], flush=True)
    return res, daily


def r2(ctx, Is):
    b2 = G2.q2(Is); out = []
    for inst in INSTS:
        I = Is[inst]; TR = b2[inst][0]; s = TR.s.values; s = s[s + 1 < I.n]
        on = (I.FP[s + 1, 0] - I.FPb[s, T.J15]) * I.pv
        ctl = []
        for ss in s:
            g = I.gpos[ss]; grp = I.gidx[I.gptr[g]:I.gptr[g + 1]]; grp = grp[grp + 1 < I.n]
            ctl.append(np.nanmean((I.FP[grp + 1, 0] - I.FPb[grp, T.J15]) * I.pv))
        out.append({"instrument": inst, "n": len(s), "overnight_usd_trade": float(np.nanmean(on)), "matched_overnight_usd_trade": float(np.nanmean(ctl)),
                    "overnight_increment_usd_trade": float(np.nanmean(on - np.array(ctl)))})
    return pd.DataFrame(out)


def r3(ctx, Is, lb=3):
    Cd = {k: Is[k].C[:, T.J15] for k in INSTS}
    at = {k: pd.Series(Cd[k]).rolling(20, min_periods=20).max().values <= Cd[k] + 1e-9 for k in INSTS}
    cnt = sum(at[k].astype(int) for k in INSTS); n = len(cnt); rows, nul = [], []
    for s in range(lb, n - 1):
        if cnt[s] == 4 and cnt[s - lb] <= 1:
            rows.append((s + 1, 0, s + 1, T.J15))
        elif cnt[s] == 4 and cnt[s - lb] >= 3:
            nul.append((s + 1, 0, s + 1, T.J15))
    return G1.ev(rows), G1.ev(nul)


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]
    res, daily = r1(ctx, Is)
    TR, NUL = r3(ctx, Is); pls = [r3(ctx, Is, 2)[0], r3(ctx, Is, 5)[0]]
    for inst in INSTS:
        I = Is[inst]; occ = ctx["occ"].get(inst); nD = W.simulate(I, NUL, occ=occ)
        o, D, d = W.run_module(I, f"R3_DAILY_BREADTH_THRUST_{inst}", TR, A.buckets(I), ctx["main"], sample=(60, 8), occ=occ, plateau_TRs=pls,
                               extra={"ctl_family_null_usd_trade": float(nD.net.mean()) if len(nD) else np.nan, "ctl_family_null_n": len(nD), **G1.horizons(I, TR)})
        o["usd_trade_minus_null"] = o["usd_per_trade"] - o["ctl_family_null_usd_trade"]
        res.append(o); daily[o["module"]] = d; print(o["module"], o["trades"], round(o["avg_day"], 2), round(o["usd_trade_minus_null"], 1), o["STANDALONE_PASS"], flush=True)
    R = pd.DataFrame(res); R.to_csv(os.path.join(W.OUT, "GEN3_RESULTS.csv"), index=False); np.savez_compressed(os.path.join(W.OUT, "GEN3_daily.npz"), **daily)
    ON = r2(ctx, Is); ON.to_csv(os.path.join(W.OUT, "GEN3_R2_OVERNIGHT.csv"), index=False)
    cols = ["module", "trades", "avg_day", "avg_day_2021", "usd_per_trade", "base_usd_trade_same_folds", "beats_base_per_trade", "usd_trade_minus_null", "matched_A_day",
            "momentum_B_day", "folds_pos", "min_fold_n", "remove_top3", "slip4_day", "delay1_day", "plateau", "corr_to_main", "main_plus_ret_dd", "main_ret_dd",
            "STANDALONE_PASS", "PORTFOLIO_PASS", "DIVERSIFIER_PASS"]
    alt = ["module"] + [c for c in R.columns if c.startswith("alt_")]
    W.md("T96_A2_GEN3_RESULTS.md", "TEST96 Track A2 - Generation 3 (final; prereg 052c65b1)", [R[[c for c in cols if c in R]], "## R1 model alternatives (reported, not selected)",
                                                                                               R[[c for c in alt if c in R]], "## R2 Q2 overnight increment (diagnostic)", ON])
    pd.set_option("display.width", 260); print(R[[c for c in cols if c in R]].to_string()); print(ON.to_string()); print(R[[c for c in alt if c in R]].to_string())


if __name__ == "__main__":
    main()
