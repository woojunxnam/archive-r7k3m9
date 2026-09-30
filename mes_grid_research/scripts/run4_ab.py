"""RUN-4 Stage 6: Sleeve A + Sleeve B portfolio under a GLOBAL ES contract budget.

A = FactoryStrategy engine run (series saved: per-bar qty, daily equity, fresh-2022 daily equity).
B = single-position momentum trades (fastsim.sim_single_sized, validated vs engine) with size in contracts.
Budget: static partition cap_A + size_B <= G (exact: total contracts can never exceed G); inventory interaction
variants change B's size by A's inventory at the decision bar (causal). All daily P&L is MTM (A) + closed intraday
trades (B is flat overnight). ES-signal / MES-economics proxy backtest (in-sample, NOT OOS)."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
import run4_lib as L
import run4_b_lib as BL
from mesgrid import fastsim as fs

SER = os.path.join(L.OUT, "series")
CAP0 = 150_000.0


def a_series(a_id):
    d = pd.read_parquet(os.path.join(SER, f"{a_id}_daily.parquet"))
    q = np.load(os.path.join(SER, f"{a_id}_qty.npy")).astype(np.int64)
    fr = os.path.join(SER, f"{a_id}_fresh2022_daily.parquet")
    f22 = pd.read_parquet(fr) if os.path.exists(fr) else None
    return d, q, f22


def b_trades(p, size_arr, ex=None):
    ex = ex or dict(slippage_ticks=1, penetration_ticks=1, commission_per_side=0.62)
    b = BL.G["b"]
    sig, _ = BL.signal_array(p["events"], p.get("cluster_min"))
    r = fs.sim_single_sized(sig, b.o, b.h, b.l, b.c, b.tradeable, BL.G["nxt"], BL.G["nil"], BL.G["dtm"],
                            float(p.get("tp", np.inf)), int(p.get("tmax", 10**9)), float(p.get("stop", np.inf)),
                            float(p.get("trail", np.inf)), int(p.get("cooldown", 0)), float(ex["slippage_ticks"]),
                            float(ex["penetration_ticks"]), size_arr, float(p.get("lim_off", -1.0)), int(p.get("ttl", 1)))
    e_i, x_i, e_p, x_p, rs, q = r
    net = (x_p - e_p) * 5.0 * q - 2 * ex["commission_per_side"] * q
    return pd.DataFrame(dict(e=e_i, x=x_i, q=q, net=net, day=b.day[x_i]))


def weekly_block(dp):
    wk = dp.resample("W-FRI").sum()
    neg = (wk < 0).astype(int).values
    best = cur = 0
    for v in neg:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return wk, dict(wk_mean=wk.mean(), wk_median=wk.median(), wk_p10=wk.quantile(.1), wk_p25=wk.quantile(.25), wk_p75=wk.quantile(.75),
                    wk_p90=wk.quantile(.9), wk_pos=(wk > 0).mean(), wk_ge1k=(wk >= 1000).mean(), wk_ge2k=(wk >= 2000).mean(),
                    wk_ge3k=(wk >= 3000).mean(), wk_ge4k=(wk >= 4000).mean(), wk_le_m2k=(wk <= -2000).mean(),
                    wk_le_m4k=(wk <= -4000).mean(), wk_worst=wk.min(), wk_worst_4w=wk.rolling(4).sum().min(), wk_longest_losing=best)


def evaluate(spec):
    b = BL.G["b"]
    n = len(b)
    days = pd.to_datetime(pd.Series(BL.G["days"]).astype(str))
    G = spec["G"]
    # ---- A
    if spec.get("a_id"):
        ad, qA, f22 = a_series(spec["a_id"])
        eqA = ad.equity.copy()
        eqA.index = pd.to_datetime(eqA.index)
        dA = eqA.diff().fillna(eqA.iloc[0] - CAP0)
    else:
        qA = np.zeros(n, np.int64); f22 = None
        dA = pd.Series(0.0, index=days)
    # ---- B (possibly several independent single-position books)
    qB = np.zeros(n, np.int64)
    bday = []
    for bs in spec.get("b", []):
        size = int(bs["size"])
        if size <= 0:
            continue
        sz = np.full(n, size, np.int64)
        rule = bs.get("rule")
        if rule == "half_when_A_high":
            thr = bs["thr"]
            sz = np.where(qA >= thr, max(size // 2, 1), size)
        elif rule == "skip_when_A_high":
            sz = np.where(qA >= bs["thr"], 0, size)
        T = b_trades(bs["params"], sz)
        for e_, x_, q_ in zip(T.e.values, T.x.values, T.q.values):
            qB[e_:x_ + 1] += q_
        bday.append(T.groupby("day").net.sum())
    if bday:
        dB = pd.concat(bday, axis=1).sum(axis=1)
        dB.index = pd.to_datetime(dB.index.astype(str))
    else:
        dB = pd.Series(0.0, index=days[:1])
    idx = dA.index.union(dB.index)
    dA = dA.reindex(idx, fill_value=0.0)
    dB = dB.reindex(idx, fill_value=0.0)
    dP = dA + dB
    eq = CAP0 + dP.cumsum()
    dd = eq - eq.cummax()
    tot = qA + qB
    raw = b.c - b.adj
    r = dict(G=G, peak_contracts=int(tot.max()), peak_A=int(qA.max()), peak_B=int(qB.max()), budget_violation=bool(tot.max() > G),
             peak_notional=float((tot * np.abs(raw) * 5.0).max()),
             total_pnl=float(dP.sum()), pnl_A=float(dA.sum()), pnl_B=float(dB.sum()), max_dd=float(dd.min()), min_equity=float(eq.min()),
             underwater_days_max=float(_longest_uw(eq)))
    wk, ws = weekly_block(dP)
    r.update({k: float(v) for k, v in ws.items()})
    wA = dA.resample("W-FRI").sum(); wB = dB.resample("W-FRI").sum()
    act = (dB != 0)
    r["corr_daily"] = float(dA[act | (dA != 0)].corr(dB[act | (dA != 0)])) if dB.abs().sum() > 0 and dA.abs().sum() > 0 else np.nan
    r["corr_weekly"] = float(wA.corr(wB)) if wB.abs().sum() > 0 and wA.abs().sum() > 0 else np.nan
    if dB.abs().sum() > 0 and dA.abs().sum() > 0:
        eA = dA.cumsum(); eB = dB.cumsum()
        uwA = eA < eA.cummax(); uwB = eB < eB.cummax()
        r["dd_overlap_B_uw_given_A_uw"] = float(uwB[uwA].mean())
        r["dd_overlap_A_uw_given_B_uw"] = float(uwA[uwB].mean())
        r["dd_series_corr"] = float((eA - eA.cummax()).corr(eB - eB.cummax()))
        qa = dA.quantile(0.10); qb = dB[dB != 0].quantile(0.10)
        r["B_on_A_worst10pct_days"] = float(dB[dA <= qa].mean())
        r["A_on_B_worst10pct_days"] = float(dA[(dB != 0) & (dB <= qb)].mean())
        wa10 = wA.nsmallest(10).index; wb10 = wB.nsmallest(10).index
        r["B_in_A_worst10w"] = float(wB.reindex(wa10).sum()); r["A_worst10w"] = float(wA.reindex(wa10).sum())
        r["A_in_B_worst10w"] = float(wA.reindex(wb10).sum()); r["B_worst10w"] = float(wB.reindex(wb10).sum())
    cdays = float(((tot[:-1]) * np.diff(b.dt).astype("int64") / 86400e9).sum())
    r["pnl_per_contract_day"] = r["total_pnl"] / max(cdays, 1e-9)
    years = (idx[-1] - idx[0]).days / 365.25
    r["annual_pnl_over_maxdd"] = (r["total_pnl"] / years) / max(-r["max_dd"], 1.0)
    srt = dP.sort_values(ascending=False)
    r.update(top1_day_share=float(srt.iloc[0] / r["total_pnl"]) if r["total_pnl"] > 0 else np.nan,
             top10_day_share=float(srt.iloc[:10].sum() / r["total_pnl"]) if r["total_pnl"] > 0 else np.nan,
             pnl_ex_best10d=float(r["total_pnl"] - srt.iloc[:10].sum()))
    # fresh start 2022-01: A fresh run equity + B P&L from 2022 (B is flat overnight -> exact)
    if f22 is not None:
        eA22 = f22.equity.copy(); eA22.index = pd.to_datetime(eA22.index)
        dA22 = eA22.diff().fillna(eA22.iloc[0] - CAP0)
    else:
        dA22 = pd.Series(0.0, index=idx[idx >= "2022-01-01"])
    dB22 = dB[dB.index >= "2022-01-01"]
    i22 = dA22.index.union(dB22.index)
    e22 = CAP0 + (dA22.reindex(i22, fill_value=0) + dB22.reindex(i22, fill_value=0)).cumsum()
    r["fresh2022_min_equity"] = float(e22.min())
    r["fresh2022_max_dd"] = float((e22 - e22.cummax()).min())
    yr = dP.groupby(dP.index.year).sum()
    for y in range(2019, 2027):
        r[f"y{y}_pnl"] = float(yr.get(y, 0.0))
    return r, dP


def _longest_uw(eq):
    peak = eq.cummax()
    uw = eq < peak
    best = cur = 0
    start = None
    for t, u in zip(eq.index, uw.values):
        if u:
            start = t if start is None else start
            cur = (t - start).days
            best = max(best, cur)
        else:
            start = None
    return best


def job_ab(e):
    t0 = time.time()
    r, dP = evaluate(e["params"])
    if (e.get("extra") or {}).get("save"):
        dP.to_frame("pnl").to_parquet(os.path.join(SER, f"{e['config_id']}_portfolio_daily.parquet"))
    r["runtime_s"] = time.time() - t0
    return {k: (float(v) if isinstance(v, (np.floating,)) else int(v) if isinstance(v, (np.integer,)) else v) for k, v in r.items()}
