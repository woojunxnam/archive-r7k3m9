"""TEST46 Lane A (RESEARCH-ONLY: every seed is PARITY_BLOCKED, see T46_01): ledger-driven study of the frozen INDEX6 entries.
Entries = sanitized ledger entry timestamps (<= 2026-05-27) inside canonical coverage (>= 2019-06-03); every outcome is
re-measured on canonical 1m data in micro economics (MES $5/pt, MNQ $2/pt; commission 0.62/side + 1 tick/side; roll cost
if carried into a switch session).  Nothing here can become a TEST46 challenger (no live-engine parity)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t45_sim as S45  # noqa: E402
import t46_common as C  # noqa: E402

OUT = os.path.join(C.T46, "laneA"); os.makedirs(OUT, exist_ok=True)
SEEDS = {"LC02 ES-VOR": ("LC02", "ES"), "LC03 NQ-NOON": ("LC03", "MNQ"), "LC05 NQ-PDH": ("LC05", "MNQ"),
         "T30-L1 NQ-COMP(base, W01 filter unrecoverable)": ("T30_W01", "MNQ")}
W0 = pd.Timestamp("2019-06-03")
g = C45.g


def load(P):
    sims = {i: S45.Sim(P, i) for i in ("ES", "MNQ")}
    return sims


def map_entries(led, sim):
    sess = sim.pn.sess
    d = led[led.entry_time >= W0].copy()
    d["date"] = d.entry_time.dt.normalize()
    d["s"] = sess.get_indexer(d.date)
    m = d.entry_time.dt.hour * 60 + d.entry_time.dt.minute
    d["j"] = (m + 1 - C45.M0).astype(int)                           # 5m bar open T -> 1m bar end-stamped T+1
    d["ex_m"] = d.exit_time.dt.hour * 60 + d.exit_time.dt.minute
    d["jx"] = (d.ex_m + 6 - C45.M0).clip(upper=C45.NG - 1).astype(int)   # exit at 5m bar close = open of 1m bar T+6
    d = d[(d.s >= 0) & (d.j >= 0) & (d.j < C45.NG)]
    d = d[d.exit_time.dt.normalize() == d.date]                       # intraday original trades only
    return d.reset_index(drop=True)


def horizon_prices(sim, s, j):
    FP, n = sim.FP, sim.n
    out = {}
    for lab, mins in (("30m", 30), ("60m", 60), ("90m", 90), ("120m", 120), ("180m", 180)):
        jj = np.minimum(j + mins, g("16:15"))
        out[lab] = FP[s, jj]
    out["16:00"] = FP[s, g("16:00")]
    out["16:15"] = FP[s, g("16:15")]
    nx = np.minimum(s + 1, n - 1)
    ok = s + 1 < n
    out["next 09:30"] = np.where(ok, FP[nx, 0], np.nan)
    out["next 10:00"] = np.where(ok, FP[nx, g("10:00")], np.nan)
    out["next 16:00"] = np.where(ok, FP[nx, g("16:00")], np.nan)
    return out


def main():
    P = C45.build_panel()
    sims = load(P)
    rows, curves, overnight, pyr, trades_all = [], [], [], [], []
    base_cache = {}
    for label, (led_name, inst) in SEEDS.items():
        sim = sims[inst]; pn = sim.pn; pv = sim.pv; k = sim.k
        cs = C45.cost_side(k)
        led = C.load_ledger(led_name)
        d = map_entries(led, sim)
        s, j = d.s.values, d.j.values
        ep = sim.FP[s, j]
        ok = ~np.isnan(ep)
        d, s, j, ep = d[ok].reset_index(drop=True), s[ok], j[ok], ep[ok]
        atr = pn.atr[s]
        # E0 original frozen shell reproduced on canonical data: exit at the ledger exit bar (TIME/RTH) or at the stop level
        stop = ep - np.round(2.0 * atr * 0 + np.abs(d.entry_px.values - d.exit_px.values) * 0, 2)     # placeholder (not used)
        xprice = sim.FPb[s, d.jx.values]
        is_sl = d.exit_reason.astype(str).str.contains("SL|STOP").values
        # stop distance: frozen 2x ATR14 of the SIGNAL-timeframe bars is not reproducible exactly -> use the ledger's own
        # adverse distance (entry - exit) for stopped trades, translated to canonical prices
        led_dist = (d.entry_px.values - d.exit_px.values)
        xprice = np.where(is_sl, ep - led_dist, xprice)
        e0 = (xprice - ep) * pv - 2 * cs
        H = horizon_prices(sim, s, j)
        rolln = np.r_[pn.roll_in[1:], False][s]
        # matched long baselines: same instrument, same entry minute (+/- 15m bucket), same horizon, same calendar year,
        # all sessions (unconditional long over the identical clock interval)
        yrs = pn.sess.year.values
        rets = {}
        for lab, px in H.items():
            gross = (px - ep) * pv
            over = lab.startswith("next")
            cost = 2 * cs + (2 * cs * rolln if over else 0)
            net = gross - cost
            key = (inst, lab)
            # baseline per (year, entry 15m bucket): mean over all sessions of the same interval return
            bl = np.full(len(s), np.nan)
            for yy in np.unique(yrs[s]):
                for bk in np.unique(j[yrs[s] == yy] // 15):
                    sel = (yrs[s] == yy) & (j // 15 == bk)
                    jj0 = bk * 15 + 7
                    allm = yrs == yy
                    p0 = sim.FP[allm, min(jj0, C45.NG - 1)]
                    hp = horizon_prices(sim, np.where(allm)[0], np.full(allm.sum(), jj0))[lab]
                    bl[sel] = np.nanmean((hp - p0) * pv) - cost if np.isscalar(cost) else np.nanmean((hp - p0) * pv) - 2 * cs
            rets[lab] = (net, bl)
            curves.append({"seed": label, "horizon": lab, "n": int(np.sum(~np.isnan(net))), "avg_net_$": np.nanmean(net),
                           "PF": np.nansum(net[net > 0]) / max(-np.nansum(net[net < 0]), 1e-9), "win%": np.nanmean(net > 0),
                           "matched_baseline_$": np.nanmean(bl), "excess_$": np.nanmean(net - bl),
                           "excess_t": np.nanmean(net - bl) / np.nanstd(net - bl) * np.sqrt(np.sum(~np.isnan(net - bl)))})
        # E-family summary (per trade)
        E = {"E0 original shell": e0, "E1 hold 120m no stop": rets["120m"][0], "E2 hold to 16:00": rets["16:00"][0],
             "E3 hold to 16:15 lock": rets["16:15"][0], "E4 overnight -> next 09:30": rets["next 09:30"][0],
             "E5 overnight -> next 10:00": rets["next 10:00"][0], "E6 overnight -> next 16:00": rets["next 16:00"][0]}
        dates = pn.sess[s]
        for nm, v in E.items():
            x = np.nan_to_num(v)
            daily = pd.Series(x).groupby(dates).sum()
            eq = daily.cumsum(); mdd = float((eq.cummax() - eq).max())
            rows.append({"seed": label, "exit": nm, "trades": int(len(x)), "net": float(x.sum()), "avg_trade": float(x.mean()),
                         "PF": float(x[x > 0].sum() / max(-x[x < 0].sum(), 1e-9)), "maxdd_tradeseq": mdd, "worst_trade": float(x.min()),
                         "incr_vs_E0_total": float(x.sum() - np.nan_to_num(e0).sum()),
                         "pre2023_avg": float(x[dates < "2023-01-01"].mean()), "2023+_avg": float(x[dates >= "2023-01-01"].mean()),
                         "Y2022_avg": float(x[(dates >= "2022-01-01") & (dates < "2023-01-01")].mean())})
        # strategy-specific overnight: incremental value of carrying from the 16:15 lock to next open, for trades of this seed,
        # vs matched control = unconditional lock->open carry on NON-signal sessions of the same year and vol tercile
        carry = (H["next 09:30"] - H["16:15"]) * pv - (2 * cs * rolln)
        allcarry = (np.r_[sim.FP[1:, 0], np.nan] - sim.FP[:, g("16:15")]) * pv
        volt = pd.Series(pn.vol_pct).fillna(0.5).values
        sig_days = np.zeros(sim.n, bool); sig_days[s] = True
        ctrl = np.full(len(s), np.nan)
        for i_, (yy, vv) in enumerate(zip(yrs[s], volt[s])):
            msk = (yrs == yy) & ~sig_days & (np.abs(volt - vv) <= 0.15)
            ctrl[i_] = np.nanmean(allcarry[msk])
        overnight.append({"seed": label, "n": int(np.sum(~np.isnan(carry))), "raw_carry_avg_$": np.nanmean(carry),
                          "matched_control_carry_$": np.nanmean(ctrl), "strategy_conditioned_excess_$": np.nanmean(carry - ctrl),
                          "excess_t": np.nanmean(carry - ctrl) / np.nanstd(carry - ctrl) * np.sqrt(np.sum(~np.isnan(carry - ctrl))),
                          "pre2023_excess": np.nanmean((carry - ctrl)[dates < "2023-01-01"]), "2023+_excess": np.nanmean((carry - ctrl)[dates >= "2023-01-01"])})
        # pyramids: second contract, measured as INCREMENTAL P&L of the add (fill -> original E0 exit), per rule
        jx = d.jx.values
        vw = pn.vwap
        adds = {"P2 winner (+0.25 ATRd & close>VWAP, within 60m)": [], "P3 reclaim (dip >=0.25 ATRd then close>=entry)": [],
                "DCA blind (-0.25 ATRd)": []}
        for t_ in range(len(s)):
            ss, j0, j1 = s[t_], j[t_], min(jx[t_], C45.NG - 1)
            if j1 <= j0 + 1:
                continue
            a = atr[t_]
            cl = pn.Cf[ss, j0:j1]; lo = np.fmin.accumulate(np.nan_to_num(pn.L[ss, j0:j1], nan=np.inf))
            win = np.where((cl - ep[t_] >= 0.25 * a) & (cl > vw[ss, j0:j1]) & (np.arange(len(cl)) <= 60))[0]
            dip = lo <= ep[t_] - 0.25 * a
            rec = np.where(dip & (cl >= ep[t_]))[0]
            dca = np.where(cl <= ep[t_] - 0.25 * a)[0]
            for nm, idx in zip(adds, (win, rec, dca)):
                if len(idx) and j0 + idx[0] + 1 < j1:
                    fj = j0 + idx[0] + 1
                    px_in = sim.FP[ss, fj]
                    px_out = xprice[t_]
                    if np.isnan(px_in):
                        continue
                    if is_sl[t_] and px_out > px_in:
                        px_out = px_in                                   # conservative: a stopped trade never exits above the add
                    adds[nm].append(((px_out - px_in) * pv - 2 * cs, dates[t_]))
        # P1 independent confirmation: another INDEX seed on the same instrument/day (computed later across seeds)
        for nm, v in adds.items():
            x = np.array([a_ for a_, _ in v]) if v else np.array([])
            pyr.append({"seed": label, "rule": nm, "adds": len(x), "add_avg_$": x.mean() if len(x) else np.nan,
                        "add_total_$": x.sum() if len(x) else 0.0, "add_win%": (x > 0).mean() if len(x) else np.nan,
                        "t": x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan})
        trades_all.append(pd.DataFrame({"seed": label, "inst": inst, "date": dates, "j": j, "jx": jx, "e0": e0,
                                        **{f"H_{k_}": (H[k_] - ep) * pv - 2 * cs for k_ in H}}))
    T = pd.concat(trades_all, ignore_index=True)
    # P1: second seed on the same instrument & day, entry after the first seed's entry, while the first is still open
    p1 = []
    for inst in ("MNQ",):
        X = T[T.inst == inst].sort_values(["date", "j"])
        for dt, grp in X.groupby("date"):
            if grp.seed.nunique() < 2:
                continue
            first = grp.iloc[0]
            for _, r in grp.iloc[1:].iterrows():
                if r.seed != first.seed and r.j < first.jx:
                    p1.append(r.e0)
    p1 = np.array(p1)
    pyr.append({"seed": "NQ seeds (LC03/LC05/T30-L1)", "rule": "P1 independent confirmation (2nd distinct seed while 1st open)",
                "adds": len(p1), "add_avg_$": p1.mean() if len(p1) else np.nan, "add_total_$": p1.sum(), "add_win%": (p1 > 0).mean() if len(p1) else np.nan,
                "t": p1.mean() / p1.std() * np.sqrt(len(p1)) if len(p1) > 2 else np.nan})
    R = pd.DataFrame(rows); CU = pd.DataFrame(curves); ON = pd.DataFrame(overnight); PY = pd.DataFrame(pyr)
    R.to_csv(f"{OUT}/T46_05_hold_extension.csv", index=False); CU.to_csv(f"{OUT}/T46_04_exit_response.csv", index=False)
    ON.to_csv(f"{OUT}/T46_06_strategy_overnight.csv", index=False); PY.to_csv(f"{OUT}/T46_07_10_pyramids.csv", index=False)
    T.to_parquet(f"{OUT}/laneA_trades.parquet")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(R.round(2).to_string()); print(CU.round(2).to_string()); print(ON.round(2).to_string()); print(PY.round(2).to_string())


if __name__ == "__main__":
    main()
