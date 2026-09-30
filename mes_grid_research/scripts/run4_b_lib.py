"""RUN-4 Sleeve B job: single-position long momentum strategy via fastsim.sim_single (validated fill-by-fill against
the engine, tests/test_run4_b.py). ES-signal / MES-economics proxy backtest, EXEC-1.1 conservative (in-sample)."""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid import fastsim as fs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = {}


def init_b(load_events=True):
    b = load_canonical()
    nxt, last_td, nil, dtm = fs.day_structure(b)
    G.update(b=b, nxt=nxt, nil=nil, dtm=dtm)
    G["days"] = np.unique(b.day[b.tradeable])
    G["years"] = (b.day // 10000).astype(np.int64)
    if load_events:
        z = np.load(os.path.join(ROOT, "data", "cache", "r4_b_events.npz"))
        G["ev"] = {k: z[k] for k in z.files}
        G["meta"] = json.load(open(os.path.join(ROOT, "data", "cache", "r4_b_events_meta.json")))
    G["cap_inf"] = np.full(len(b), 10**6, np.int64)


def signal_array(names, cluster_min=None):
    b = G["b"]
    idx = np.unique(np.concatenate([G["ev"][n] for n in names]))
    n_raw = int(sum(len(G["ev"][n]) for n in names))
    n_dup = n_raw - len(idx)                     # same-bar duplicates across families
    if cluster_min is not None and len(idx):
        dtm, day = G["dtm"], b.day
        keep = np.zeros(len(idx), bool)
        last_t, last_d = -10**12, -1
        for q, s in enumerate(idx):
            if day[s] != last_d or dtm[s] - last_t > cluster_min:
                keep[q] = True
                last_t, last_d = dtm[s], day[s]
        n_clustered = int((~keep).sum())
        idx = idx[keep]
    else:
        n_clustered = 0
    sig = np.zeros(len(b), bool)
    sig[idx] = True
    return sig, dict(n_signals_raw=n_raw, n_same_bar_dup=n_dup, n_clustered_away=n_clustered, n_signals=len(idx))


def simulate(sig, p, ex, cap=None, size=1):
    b = G["b"]
    return fs.sim_single(sig, b.o, b.h, b.l, b.c, b.tradeable, G["nxt"], G["nil"], G["dtm"],
                         float(p.get("tp", np.inf)), int(p.get("tmax", 10**9)), float(p.get("stop", np.inf)),
                         float(p.get("trail", np.inf)), int(p.get("cooldown", 0)), float(ex.get("slippage_ticks", 1)),
                         float(ex.get("penetration_ticks", 1)), bool(p.get("strict", False)),
                         G["cap_inf"] if cap is None else cap, int(size), float(p.get("lim_off", -1.0)), int(p.get("ttl", 1)))


def trade_frame(res, ex, size=1):
    b = G["b"]
    e_i, x_i, e_p, x_p, rs, ns, ni, nc = res
    comm = float(ex.get("commission_per_side", 0.62))
    slip = float(ex.get("slippage_ticks", 1)) * 0.25
    net = (x_p - e_p) * 5.0 * size - 2 * comm * size
    exit_slip = np.where(np.isin(rs, [3, 4, 5, 6, 9]), slip, np.where(rs == 1, np.minimum(slip, np.maximum(b.o[x_i] - x_p, 0)), 0.0))
    slip_cost = (slip + exit_slip) * 5.0 * size
    gross = net + 2 * comm * size + slip_cost
    hold = G["dtm"][x_i] - G["dtm"][e_i] + 1
    return pd.DataFrame(dict(e=e_i, x=x_i, ep=e_p, xp=x_p, reason=rs, net=net, gross=gross, cost=net * 0 + 2 * comm * size + slip_cost,
                             hold=hold, day=b.day[x_i], year=G["years"][x_i]))


def bucket(tpd):
    return "LOW" if tpd < 5 else "MEDIUM" if tpd < 10 else "HIGH" if tpd < 20 else "VERY_HIGH" if tpd < 30 else "ULTRA"


def metrics(T, sig_info, ns, ni, ncap, size=1, prefix=""):
    days = G["days"]
    nd = len(days)
    r = dict(sig_info)
    r.update(n_sig_decision=int(ns), n_ignored_overlap=int(ni), n_cap_block=int(ncap))
    n = len(T)
    r["trades"] = n
    if n == 0:
        r.update(tpd_mean=0.0, net_pnl=0.0, ev_net=np.nan)
        return {prefix + k: v for k, v in r.items()}
    per_day = T.groupby("day").size().reindex(days, fill_value=0)
    dp = T.groupby("day").net.sum().reindex(days, fill_value=0.0)
    eq = dp.cumsum()
    dd = (eq - np.maximum.accumulate(np.concatenate([[0.0], eq.values]))[1:])
    tr_eq = T.net.cumsum().values
    tr_dd = (tr_eq - np.maximum.accumulate(np.concatenate([[0.0], tr_eq]))[1:]).min()
    dts = pd.to_datetime(days.astype(str))
    wk = pd.Series(dp.values, index=dts).resample("W-FRI").sum()
    srt = dp.sort_values(ascending=False)
    tot = float(T.net.sum())
    q99 = T.net.quantile(0.99)
    r.update(signal_to_fill=n / max(ns, 1), tpd_mean=n / nd, tpd_median=float(per_day.median()), tpd_p10=float(per_day.quantile(.1)),
             tpd_p90=float(per_day.quantile(.9)), freq_bucket=bucket(n / nd), active_day_share=float((per_day > 0).mean()),
             net_pnl=tot, gross_pnl=float(T.gross.sum()), cost_total=float(T.cost.sum()), ev_net=tot / n, ev_gross=float(T.gross.mean()),
             cost_per_trade=float(T.cost.mean()), cost_share_of_gross=float(T.cost.sum() / T.gross.sum()) if T.gross.sum() > 0 else np.nan,
             win_rate=float((T.net > 0).mean()), hold_mean=float(T.hold.mean()), hold_median=float(T.hold.median()),
             pnl_per_contract_hour=tot / max(float(T.hold.sum()) / 60.0 * size, 1e-9), max_dd_daily=float(dd.min()), max_dd_trade=float(tr_dd),
             wk_mean=float(wk.mean()), wk_median=float(wk.median()), wk_p10=float(wk.quantile(.1)), wk_p25=float(wk.quantile(.25)),
             wk_p75=float(wk.quantile(.75)), wk_p90=float(wk.quantile(.9)), wk_pos=float((wk > 0).mean()), wk_worst=float(wk.min()),
             wk_worst_4w=float(wk.rolling(4).sum().min()), top1pct_trades_share=float(T.net[T.net >= q99].sum() / tot) if tot > 0 else np.nan,
             top5_day_share=float(srt.iloc[:5].sum() / tot) if tot > 0 else np.nan, top10_day_share=float(srt.iloc[:10].sum() / tot) if tot > 0 else np.nan,
             pnl_ex_best5d=float(tot - srt.iloc[:5].sum()), pnl_ex_best10d=float(tot - srt.iloc[:10].sum()),
             reason_tp_share=float(np.isin(T.reason, [1, 2]).mean()))
    yr = T.groupby("year").net.agg(["sum", "size"])
    for y in range(2019, 2027):
        r[f"y{y}_pnl"] = float(yr["sum"].get(y, 0.0)); r[f"y{y}_n"] = int(yr["size"].get(y, 0))
    r["years_pos"] = int(sum(r[f"y{y}_pnl"] > 0 for y in range(2019, 2027)))
    r["s19_21_pnl"] = sum(r[f"y{y}_pnl"] for y in (2019, 2020, 2021)); r["s22_pnl"] = r["y2022_pnl"]
    r["s23p_pnl"] = sum(r[f"y{y}_pnl"] for y in (2023, 2024, 2025, 2026))
    r["s19_21_ev"] = r["s19_21_pnl"] / max(sum(r[f"y{y}_n"] for y in (2019, 2020, 2021)), 1)
    r["s22_ev"] = r["s22_pnl"] / max(r["y2022_n"], 1)
    r["s23p_ev"] = r["s23p_pnl"] / max(sum(r[f"y{y}_n"] for y in (2023, 2024, 2025, 2026)), 1)
    return {prefix + k: v for k, v in r.items()}


def job_b(e):
    t0 = time.time()
    p = e["params"]
    ex = e["exec"]
    sig, info = signal_array(p["events"], p.get("cluster_min"))
    res = simulate(sig, p, ex)
    T = trade_frame(res, ex)
    r = metrics(T, info, res[5], res[6], res[7])
    # execution sensitivity (always reported): 2-tick slippage
    if not ex.get("no_sens"):
        ex2 = dict(ex, slippage_ticks=float(ex.get("slippage_ticks", 1)) + 1)
        r2 = simulate(sig, p, ex2)
        T2 = trade_frame(r2, ex2)
        r["slip_plus1_ev_net"] = float(T2.net.mean()) if len(T2) else np.nan
        r["slip_plus1_net_pnl"] = float(T2.net.sum()) if len(T2) else 0.0
    r["runtime_s"] = time.time() - t0
    return {k: (float(v) if isinstance(v, (np.floating,)) else int(v) if isinstance(v, (np.integer,)) else v) for k, v in r.items()}
