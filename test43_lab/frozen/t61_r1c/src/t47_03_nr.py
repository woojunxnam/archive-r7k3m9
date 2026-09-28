"""TEST47 NR inventory recycle + exits + NASSI overnight + portability + recurrence (T47_19 .. T47_28).
Entry signals = predeclared control C2 (T1 default N3) with E1, and C4 (C2 + NB).  Every NR variant is compared with R0 on
the SAME signal set; incremental = variant - R0 (daily $, costs included for every extra side)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_common as C  # noqa: E402
import t47_engine as E  # noqa: E402
from t47_02_n3 import START, cfg, tstat  # noqa: E402

OUT = os.path.join(C.T47, "nr"); os.makedirs(OUT, exist_ok=True)
SPAN21 = pd.Timestamp("2021-01-01")


class LotBase:
    """matched ordinary long for each lot: same (year, vol tercile, HTF trend) sessions, same entry and exit grid minute."""

    def __init__(self, mk):
        self.mk = mk
        key = mk.year * 100 + mk.vt * 10 + mk.bull.astype(int)
        self.key = key
        self.groups = {k: np.where(key == k)[0] for k in np.unique(key)}

    def __call__(self, lots, slip=1.0):
        mk = self.mk; cs = C45.cost_side(mk.k, slip)
        out = np.full(len(lots), np.nan)
        for i, (s, ji, jo, et) in enumerate(lots[["s", "j_in", "j_out", "exit_type"]].values):
            idx = self.groups[self.key[int(s)]]
            if et == 2:
                idx = idx[idx + 1 < mk.n]
                x = (mk.FP[idx + 1, 0] - mk.FP[idx, int(ji)]) * mk.pv - 2 * cs
            else:
                x = (mk.FPb[idx, int(jo)] - mk.FP[idx, int(ji)]) * mk.pv - 2 * cs
            out[i] = np.nanmean(x)
        return out


def dly(mk, lots, col="pnl"):
    x = np.zeros(mk.n)
    np.add.at(x, lots.acct_s.values.astype(int), lots[col].values)
    return x


def risk(x):
    eq = np.r_[0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    q = np.sort(x)[:max(1, int(0.05 * len(x)))]
    uw = eq - np.maximum.accumulate(eq)
    return {"avg_day": float(x.mean()), "total": float(x.sum()), "max_dd": mdd, "worst_day": float(x.min()),
            "ret_dd": float(x.mean() / mdd) if mdd > 0 else np.nan, "cvar5_day": float(q.mean()), "days_underwater%": float((uw < 0).mean())}


def summarize(mk, lots, camps, lb, name, r0_daily=None, slip=1.0):
    sess = mk.pn.sess; m = sess >= SPAN21
    lots = lots.copy()
    lots["excess"] = lots.pnl - lb(lots, slip)
    d = dly(mk, lots); dx = dly(mk, lots, "excess")
    cp = lots.groupby("camp").pnl.sum()
    top = np.sort(cp.values)[::-1]
    o = {"config": name, "campaigns": len(camps), "lots": len(lots), "max_inventory": int(lots.groupby("camp").size().max()) if len(lots) else 0,
         "adds": int((lots.type > 0).sum()), "trims": int((lots.exit_type == 1).sum()), "overnight_lots": int((lots.exit_type == 2).sum()),
         "avg_campaign": float(cp.mean()), "worst_campaign": float(cp.min()) if len(cp) else np.nan,
         "remove_top3_campaigns": float(cp.sum() - top[:3].sum()), "excess_lot": float(lots.excess.mean()),
         "t_excess": tstat(lots.excess, lots.s), "excess_day_2021": float(dx[m].mean()),
         **{f"{k}_2021": v for k, v in risk(d[m]).items()},
         "pnl_INIT": float(lots[lots.type == 0].pnl.sum()), "pnl_SECOND": float(lots[lots.type == 1].pnl.sum()),
         "pnl_REBUILD": float(lots[lots.type == 2].pnl.sum()), "pnl_TRIM_exits": float(lots[lots.exit_type == 1].pnl.sum()),
         "extra_cost": float(2 * C45.cost_side(mk.k, slip) * (lots.type > 0).sum())}
    fold = []
    for nm, a, b in C45.OUTER:
        mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b))
        fold.append(d[mm].mean())
    o["folds_pos"] = int(sum(v > 0 for v in fold)); o["fold_median"] = float(np.median(fold))
    if r0_daily is not None:
        inc = d - r0_daily
        o.update({f"incr_{k}": v for k, v in risk(inc[m]).items() if k in ("avg_day", "total", "max_dd", "worst_day")})
        o["incr_t"] = tstat(inc[m][inc[m] != 0]) if (inc[m] != 0).sum() > 5 else np.nan
        o["delta_ret_dd"] = o["ret_dd_2021"] - risk(r0_daily[m])["ret_dd"]
        o["delta_worst_day"] = o["worst_day_2021"] - risk(r0_daily[m])["worst_day"]
        o["delta_max_dd"] = o["max_dd_2021"] - risk(r0_daily[m])["max_dd"]
        o["extra_sides"] = int(2 * (lots.type > 0).sum())
        o["cost_per_extra_cycle"] = float(2 * C45.cost_side(mk.k, slip))
    return o, d


def main():
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    rows, acct, exits, ovn, port, rec = [], [], [], [], [], []
    for k, mk in mks.items():
        lb = LotBase(mk)
        ev, cnt, legm = E.run_detect(mk, cfg())
        ev = ev[mk.pn.sess[ev.s.values] >= START]
        # ---------------- T47_19..24 recycle ladder
        for entry in ("E1", "NB"):
            for ex in ("X60", "REC50", "X1615"):
                base = dict(entry=entry, exit=ex)
                L0, C0 = E.run_campaign(mk, ev, legm, **base)
                o0, d0 = summarize(mk, L0, C0, lb, "R0 one lot", None)
                rows.append({"inst": k, "entry": entry, "exit": ex, **o0})
                variants = {"NR-A confirmed second buy": dict(add="confirmed"),
                            "NR-B blind DCA (-2u5) [diagnostic]": dict(add="blind"),
                            "NR-C confirmed + trim": dict(add="confirmed", trim=True),
                            "NR-D full recycle": dict(add="confirmed", trim=True, rebuild=True),
                            "NR-B+trim blind recycle [diagnostic]": dict(add="blind", trim=True, rebuild=True),
                            "CAP3 stress (report only)": None}
                for nm, v in variants.items():
                    if v is None:
                        continue
                    L, Cm = E.run_campaign(mk, ev, legm, **base, **v)
                    o, d = summarize(mk, L, Cm, lb, nm, d0)
                    rows.append({"inst": k, "entry": entry, "exit": ex, **o})
                    if ex == "REC50" and entry == "E1":
                        L = L.assign(inst=k, variant=nm); acct.append(L)
                print(k, entry, ex, "done", flush=True)
        # ---------------- T47_25 exit response (1 lot, E1 and NB)
        from t47_02_n3 import pnl_summary
        bl = E.Baseline(mk)
        for entry in ("E1", "NB"):
            for ex in ("X30", "X60", "X120", "X1600", "X1615", "REC50", "TWAP", "OPEN", "REF"):
                T = E.trades(mk, ev, entry, ex)
                exits.append({"inst": k, "entry": entry, **pnl_summary(mk, T, bl, ex, ex)})
        # ---------------- T47_26 NASSI overnight: unresolved campaigns at 16:15 (REC50 exit, R0)
        L, Cm = E.run_campaign(mk, ev, legm, exit="REC50")
        un = Cm[Cm.unresolved == 1]
        s_un = un.s.values[un.s.values + 1 < mk.n]
        on = (mk.FP[s_un + 1, 0] - mk.FPb[s_un, E.J1615]) * mk.pv - 2 * C45.cost_side(mk.k)
        allon = (mk.FP[1:, 0] - mk.FPb[:-1, E.J1615]) * mk.pv - 2 * C45.cost_side(mk.k)
        key = lb.key[:-1]
        mo = pd.Series(allon).groupby(key).mean()
        base_on = mo.reindex(lb.key[s_un]).values
        exc = on - base_on
        ovn.append({"inst": k, "unresolved_campaigns": len(s_un), "share_of_campaigns": len(un) / max(len(Cm), 1),
                    "avg_overnight_$": float(np.nanmean(on)), "matched_ordinary_overnight_$": float(np.nanmean(base_on)),
                    "conditional_excess_$": float(np.nanmean(exc)), "t": tstat(exc), "worst_overnight_$": float(np.nanmin(on)),
                    "years_excess_pos": int((pd.Series(exc).groupby(mk.year[s_un]).mean() > 0).sum()), "years": int(len(np.unique(mk.year[s_un])))})
        Lh, Ch = E.run_campaign(mk, ev, legm, exit="REC50", overnight=True)
        oh, dh = summarize(mk, Lh, Ch, lb, "R0 REC50 + unresolved overnight hold", dly(mk, L))
        ovn[-1].update({f"hold_{kk}": v for kk, v in oh.items() if kk.startswith("incr_") or kk in ("delta_worst_day", "delta_max_dd")})
        # ---------------- T47_28 multiyear recurrence of path structure (event level, +60m matched excess)
        from t47_02_n3 import Fwd, event_table
        fw = Fwd(mk)
        for nt in (2, 3, 4):
            e_, _, _ = E.run_detect(mk, cfg(ntick=nt)); e_ = e_[mk.pn.sess[e_.s.values] >= START]
            T = event_table(mk, fw, e_)
            T["x"] = T["+60m"] - T["+60m_base"]
            T["decel"] = T.leg3 <= T.leg2 if nt >= 3 else T.leg2 <= T.leg1
            T["size_t"] = pd.qcut(T.cum, 3, labels=["small", "mid", "large"])
            for yv, g in T.groupby("year"):
                rec.append({"inst": k, "ntick": nt, "year": yv, "events": len(g), "excess60": g.x.mean(),
                            "decel_minus_accel": g[g.decel].x.mean() - g[~g.decel].x.mean(),
                            "best_size_tercile": g.groupby("size_t", observed=True).x.mean().idxmax()})
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T47_19_23_recycle.csv", index=False)
    A = pd.concat(acct); A.to_parquet(f"{OUT}/T47_24_lot_ledger.parquet")
    X = pd.DataFrame(exits); X.to_csv(f"{OUT}/T47_25_exit_response.csv", index=False)
    O = pd.DataFrame(ovn); O.to_csv(f"{OUT}/T47_26_overnight.csv", index=False)
    RC = pd.DataFrame(rec); RC.to_csv(f"{OUT}/T47_28_recurrence.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(R[["inst", "entry", "exit", "config", "campaigns", "adds", "trims", "avg_day_2021", "excess_day_2021", "incr_avg_day", "incr_t",
             "delta_ret_dd", "delta_worst_day", "worst_campaign", "remove_top3_campaigns", "folds_pos"]].round(2).to_string())
    print(X[["inst", "entry", "config", "trades", "avg_trade", "excess_trade", "t_excess", "folds_pos"]].round(2).to_string())
    print(O.round(2).T.to_string())
    print(RC.pivot_table(index=["inst", "ntick"], columns="year", values="excess60").round(3).to_string())
    print(RC.pivot_table(index=["inst", "ntick"], columns="year", values="decel_minus_accel").round(3).to_string())


if __name__ == "__main__":
    main()
