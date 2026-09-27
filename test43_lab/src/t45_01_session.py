"""TEST45 timestamp QA (addendum 9), Phase 1 session-return decomposition, Phase 2 close-to-open premium controls,
Phase 19 / addendum 8 overnight lock risk.  Descriptive only - nothing is optimised here."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_sim as S  # noqa: E402

OUT = os.path.join(C.T45, "session"); os.makedirs(OUT, exist_ok=True)
YEARS = ["Y2019", "Y2020", "Y2021", "Y2022", "Y2023", "Y2024", "Y2025", "Y2026_TO_0527", "FORMER_HOLDOUT_USED"]


def ts_qa():
    rows = []
    sem = {"09:29": "pre-open Globex bar [09:28,09:29) - NOT RTH, never used", "09:30": "bar [09:29,09:30): last pre-open bar, never used",
           "09:31": "bar [09:30,09:31): o = RTH_OPEN (first RTH trade); decisions using the open print happen at 09:31, fill o(09:32)",
           "15:59": "bar [15:58,15:59)", "16:00": "bar [15:59,16:00): c = CASH_REFERENCE_CLOSE (16:00:00)",
           "16:01": "bar [16:00,16:01): first post-cash-close bar (still executable)",
           "16:14": "bar [16:13,16:14): LAST bar a decision may use (decision time 16:14)",
           "16:15": "bar [16:14,16:15): o = LAST CAUSAL EXECUTION fill (LOCK_REF); its h/l/c are NOT used by any decision",
           "16:16": "bar [16:15,16:16): after LAST_ALLOWED_EXECUTION -> LOCKED; never used (absent before 2021-06 halt change)"}
    for inst in C.INSTS:
        d = C.load1m(inst)
        mod = d.dt.dt.hour * 60 + d.dt.dt.minute
        ns = d.session_date.nunique()
        for hhmm, txt in sem.items():
            h, m = map(int, hhmm.split(":"))
            x = d[mod == h * 60 + m]
            rows.append({"inst": inst, "bar_end_stamp": hhmm, "covers": f"[{h:02d}:{m - 1:02d},{hhmm})" if m else hhmm,
                         "sessions_with_bar": x.session_date.nunique(), "sessions_total": ns, "share": x.session_date.nunique() / ns,
                         "role": txt})
        odd = d[(mod >= 571) & (mod <= 975) & (d.cal_date != d.session_date)].session_date.unique()
        rows.append({"inst": inst, "bar_end_stamp": "QA", "covers": "RTH-window bars whose cal_date != session_date",
                     "sessions_with_bar": len(odd), "sessions_total": ns, "share": len(odd) / ns, "role": ", ".join(str(pd.Timestamp(s).date()) for s in odd[:10])})
    return pd.DataFrame(rows)


def seg_defs(pn):
    Cf = pn.Cf; g = C.g
    px = lambda t: Cf[:, g(t)]
    nxt = lambda x: np.r_[x[1:], np.nan]
    return {
        "GAP_CASH prev 16:00 -> 09:30 open": (pn.p_cash, pn.open, None),
        "GAP_LOCK prev 16:15 fill -> 09:30 open": (pn.p_lock, pn.open, None),
        "09:30 -> 10:00": (pn.open, px("10:00"), (0, g("10:00"))),
        "09:30 -> 10:30": (pn.open, px("10:30"), (0, g("10:30"))),
        "09:30 -> 11:00": (pn.open, px("11:00"), (0, g("11:00"))),
        "11:00 -> 14:30": (px("11:00"), px("14:30"), (g("11:00") + 1, g("14:30"))),
        "14:30 -> 15:00": (px("14:30"), px("15:00"), (g("14:30") + 1, g("15:00"))),
        "15:00 -> 15:30": (px("15:00"), px("15:30"), (g("15:00") + 1, g("15:30"))),
        "15:30 -> 15:45": (px("15:30"), px("15:45"), (g("15:30") + 1, g("15:45"))),
        "15:45 -> 16:00 (cash close)": (px("15:45"), pn.cash_close, (g("15:45") + 1, g("16:00"))),
        "A 15:00 -> 16:00": (px("15:00"), pn.cash_close, (g("15:00") + 1, g("16:00"))),
        "B 16:00 -> 16:15 lock fill": (pn.cash_close, pn.lock, (g("16:01"), g("16:14"))),
        "RTH 09:30 -> 16:00": (pn.open, pn.cash_close, (0, g("16:00"))),
        "C LOCKED 16:15 -> next 09:30 (actual overnight inventory return)": (pn.lock, nxt(pn.open), None),
        "16:00 -> next 09:30 (comparison only; includes executable 16:00-16:15)": (pn.cash_close, nxt(pn.open), None),
    }


def seg_stats(r, atr, pv, mfe=None, mae=None):
    ok = ~np.isnan(r) & ~np.isnan(atr)
    x = r[ok]; z = (r / atr)[ok]
    o = {"n": int(ok.sum()), "mean_pts": x.mean(), "median_pts": np.median(x), "pos_share": (x > 0).mean(), "std_pts": x.std(),
         "t_stat": x.mean() / x.std() * np.sqrt(len(x)), "norm_mean(mean/std)": x.mean() / x.std(), "mean_atr": z.mean(),
         "mean_$1c": x.mean() * pv, "p1_$1c": np.percentile(x, 1) * pv, "worst_$1c": x.min() * pv, "best_$1c": x.max() * pv}
    if mfe is not None:
        o["MFE_mean_atr"] = np.nanmean((mfe / atr)[ok]); o["MAE_mean_atr"] = np.nanmean((mae / atr)[ok])
    return o


def decomposition(P):
    rows, yrows = [], []
    pns = {i: C.Panel(P, i) for i in C.INSTS}
    sess = pns["ES"].sess
    Z = {}
    for inst, pn in pns.items():
        pv = C.PV[pn.k]
        for name, (a, b, win) in seg_defs(pn).items():
            r = b - a
            mfe = mae = None
            if win is not None:
                H = np.nanmax(pn.H[:, win[0]:win[1] + 1], 1); L = np.nanmin(pn.L[:, win[0]:win[1] + 1], 1)
                mfe, mae = H - a, L - a
            rows.append({"inst": inst, "segment": name, **seg_stats(r, pn.atr, pv, mfe, mae)})
            Z[(inst, name)] = r / pn.atr
            for y in YEARS:
                m = C.mask_period(sess, y)
                yrows.append({"inst": inst, "segment": name, "period": y, "mean_atr": np.nanmean((r / pn.atr)[m]),
                              "mean_$1c": np.nanmean(r[m]) * pv, "pos_share": np.nanmean((r[m] > 0)[~np.isnan(r[m])]), "n": int((~np.isnan(r[m])).sum())})
    for name in seg_defs(pns["ES"]):
        dz = Z[("ES", name)] - Z[("MNQ", name)]
        ok = ~np.isnan(dz)
        rows.append({"inst": "ES-NQ (ATR units)", "segment": name, "n": int(ok.sum()), "mean_atr": dz[ok].mean(),
                     "t_stat": dz[ok].mean() / dz[ok].std() * np.sqrt(ok.sum()), "pos_share": (dz[ok] > 0).mean()})
    return pd.DataFrame(rows), pd.DataFrame(yrows)


DEC_TIMES = ["14:30", "15:00", "15:15", "15:30", "15:45", "16:00", "16:14"]


def carry_controls(P, sims, bench):
    rows, per = [], []
    for t in DEC_TIMES:
        res = {}
        for sm in sims:
            ej, eq = S.events(sm.n)
            ej[:, 0] = C.OPEN_BAR; eq[:, 0] = 0                     # pre-planned exit at the next RTH open print
            ej[:, 1] = C.g(t) + 1; eq[:, 1] = 1                      # decision at t, fill at open of bar t+1
            res[sm.k] = sm.run(ej, eq)
            m = S.metrics({sm.k: res[sm.k]}, bench)
            rows.append({"control": f"+1 {C.INSTS[sm.k]} decide {t} -> hold -> exit next open", "inst": C.INSTS[sm.k], "decision": t, **m})
        m = S.metrics(res, bench)
        rows.append({"control": f"+1 MES +1 MNQ decide {t}", "inst": "BOTH", "decision": t, **m})
        if t in ("15:45", "16:14"):
            for p in S.period_table(res, bench):
                per.append({"control": f"+1/+1 decide {t}", **p})
    return pd.DataFrame(rows), pd.DataFrame(per)


def lock_risk(P, sims):
    rows = []
    L = {}
    for sm in sims:
        pn = sm.pn
        lock = sm.FP[:, C.LOCK_FILL_BAR]; op_next = np.r_[sm.FP[1:, C.OPEN_BAR], np.nan]
        cash = pn.cash_close
        L[sm.k] = {"16:15->09:30": (op_next - lock) * sm.pv, "16:00->09:30 (comparison)": (op_next - cash) * sm.pv}
    # overnight mark-to-market excursion (REPORT ONLY; path never used by a strategy): min price between lock and next open
    for inst, sm in zip(C.INSTS, sims):
        d = C.load1m(inst)
        mod = (d.dt.dt.hour * 60 + d.dt.dt.minute).values
        sd = d.session_date.values
        si = pd.Index(sm.pn.sess).get_indexer(sd)
        # bars after 16:15 of session s and before 09:31 of session s+1
        tail = (mod > 975) & (mod <= 1020)
        head = (mod >= 1081) | (mod < 571)
        key = np.where(tail, si, np.where(head, si - 1, -9))
        ok = key >= 0
        lows = pd.Series(d.l.values[ok]).groupby(key[ok]).min().reindex(range(sm.n)).values
        L[sm.k]["MTM worst excursion 16:15->09:30 (report only)"] = (lows - sm.FP[:, C.LOCK_FILL_BAR]) * sm.pv
    combos = {"1 MES": (1, 0), "2 MES": (2, 0), "1 MNQ": (0, 1), "2 MNQ": (0, 2), "1 MES + 1 MNQ": (1, 1), "2 MES + 1 MNQ": (2, 1),
              "1 MES + 2 MNQ": (1, 2), "2 MES + 2 MNQ": (2, 2)}
    sess = sims[0].pn.sess
    for kind in L[0]:
        for name, (a, b) in combos.items():
            x = a * np.nan_to_num(L[0][kind], nan=np.nan) + b * L[1][kind]
            x = x[~np.isnan(x)]
            rows.append({"interval": kind, "position": name, "n": len(x), "mean": x.mean(), "median": np.median(x),
                         "p5": np.percentile(x, 5), "p1": np.percentile(x, 1), "p0.5": np.percentile(x, 0.5), "worst": x.min(),
                         "worst_as_%_capital": 100 * x.min() / C.CAPITAL})
    # overnight margin (IBKR overnight reference scaled by raw notional) at the lock
    mg = []
    for sm, k in zip(sims, (0, 1)):
        prof = C.PROF[C.INSTS[k]]
        frac = C.instruments.margin_frac(prof, "overnight")
        raw = sm.FP[:, C.LOCK_FILL_BAR] - pd.Series(C.load1m(C.INSTS[k]).groupby("session_date").cum_adjustment.last()).reindex(sess).values
        mg.append(frac * raw * sm.pv)
    for name, (a, b) in combos.items():
        x = a * mg[0] + b * mg[1]
        rows.append({"interval": "overnight margin at lock ($, IBKR ref scaled by raw notional)", "position": name, "n": int((~np.isnan(x)).sum()),
                     "mean": np.nanmean(x), "median": np.nanmedian(x), "worst": np.nanmax(x), "worst_as_%_capital": 100 * np.nanmax(x) / C.CAPITAL})
    worst = []
    for k, inst in enumerate(C.INSTS):
        x = L[k]["16:15->09:30"]; o = np.argsort(np.nan_to_num(x, nan=1e9))[:10]
        for i in o:
            worst.append({"inst": inst, "lock_session": str(sess[i].date()), "locked_return_$1c": x[i],
                          "atr_units": x[i] / sims[k].pv / sims[k].pn.atr[i]})
    return pd.DataFrame(rows), pd.DataFrame(worst), L


def main():
    P = C.build_panel()
    sims = [S.Sim(P, i) for i in C.INSTS]
    bench = S.Bench(sims)
    qa = ts_qa(); qa.to_csv(f"{OUT}/T45_timestamp_qa.csv", index=False)
    dec, dy = decomposition(P); dec.to_csv(f"{OUT}/T45_01_segments.csv", index=False); dy.to_csv(f"{OUT}/T45_01_segments_by_year.csv", index=False)
    cc, cp = carry_controls(P, sims, bench); cc.to_csv(f"{OUT}/T45_02_carry_controls.csv", index=False); cp.to_csv(f"{OUT}/T45_02_carry_by_period.csv", index=False)
    lr, lw, L = lock_risk(P, sims); lr.to_csv(f"{OUT}/T45_17_lock_risk.csv", index=False); lw.to_csv(f"{OUT}/T45_17_worst_locks.csv", index=False)
    np.savez(f"{OUT}/lock_returns.npz", ES=L[0]["16:15->09:30"], MNQ=L[1]["16:15->09:30"])
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(qa[["inst", "bar_end_stamp", "share"]])
    print(dec[["inst", "segment", "n", "mean_$1c", "t_stat", "pos_share", "mean_atr"]].to_string())
    print(cc[["control", "avg", "total", "max_dd", "worst", "matched_beta_excess", "session_matched_beta_excess", "cost", "incr_avg", "corr_champion"]].to_string())
    print(lr.to_string())


if __name__ == "__main__":
    main()
