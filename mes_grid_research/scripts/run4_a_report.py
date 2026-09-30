"""RUN-4 Sleeve A report tables (printed + saved to results/RUN4_OVERNIGHT/a_tables/):
 1. module families vs parent control (median / best deltas)
 2. activity-with-fewer-contracts frontier (by total cap: best fresh equity with fresh no-entry <= 30 d)
 3. dead-slot economics (shadow slot value, salvage cost, dead fraction)
 4. true-alpha / null decomposition (NULL-A core-only exposure-matched, NULL-B dumb recycle, NULL-C random timing, NULL-D passive)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import run4_lib as L
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from run4_analyze import load

OUTD = os.path.join(L.OUT, "a_tables")
os.makedirs(OUTD, exist_ok=True)
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 60)


def _daily_close():
    from mesgrid.data import load_canonical
    b = load_canonical()
    s = pd.Series(b.c, index=pd.DatetimeIndex(b.dt).normalize()).groupby(level=0).last()
    return s


def _roll_days():
    from mesgrid.data import load_canonical
    b = load_canonical()
    r = np.flatnonzero(np.diff(b.contract) != 0) + 1
    return pd.Series(1.0, index=pd.DatetimeIndex(b.dt[r]).normalize()).groupby(level=0).sum()


def main():
    A = load("A")
    A = A[A.stage.isin(["S1", "S2"]) | A.family.isin(["A-NULL-A", "A-NULL-B", "A-NULL-C"])].copy()
    A["cap"] = A.contract_cap.astype(int)
    base = A.set_index("config_id")
    s1 = A[A.stage == "S1"]
    # ---------------- 1. families vs control
    rows = []
    for fam, g in s1.groupby("family"):
        g = g[g.parent.isin(base.index)] if fam not in ("A-STRUCT", "A-NULL-A") else g
        if fam in ("A-STRUCT", "A-NULL-A"):
            rows.append(dict(family=fam, n=len(g)))
            continue
        par = base.loc[g.parent]
        d = pd.DataFrame({"d_mtm": g.total_mtm.values - par.total_mtm.values, "d_dd": g.max_mtm_dd.values - par.max_mtm_dd.values,
                          "d_fresh22": g.fs2022_min_equity.values - par.fs2022_min_equity.values,
                          "d_noentry": g.fs2022_no_entry_days.values - par.fs2022_no_entry_days.values,
                          "d_rectpd": g.rec_trades_day.values - par.rec_trades_day.values,
                          "d_dead": g.dead_slot_frac.values - par.dead_slot_frac.values})
        act = (g.fs2022_no_entry_days.values <= 30)
        rows.append(dict(family=fam, n=len(g), med_d_mtm=d.d_mtm.median(), med_d_dd=d.d_dd.median(), med_d_fresh22=d.d_fresh22.median(),
                         med_d_noentry=d.d_noentry.median(), med_d_rectpd=d.d_rectpd.median(), med_d_dead=d.d_dead.median(),
                         share_active=act.mean(), share_fresh_up_and_active=float(((d.d_fresh22 > 0).values & act).mean()),
                         best_fresh22=g.fs2022_min_equity.max()))
    fam = pd.DataFrame(rows)
    fam.to_csv(os.path.join(OUTD, "families_vs_control.csv"), index=False)
    print("== families vs parent control (S1)"); print(fam.round(2).to_string(index=False))
    # ---------------- 2. activity frontier by cap
    act = s1[(s1.fs2022_no_entry_days <= 30) & ~s1.family.str.startswith("A-NULL")]
    fr = []
    for cap, g in s1[~s1.family.str.startswith("A-NULL")].groupby("cap"):
        ga = g[g.fs2022_no_entry_days <= 30]
        ctrl = g[g.family == "A-STRUCT"]
        fr.append(dict(cap=cap, n=len(g), n_active=len(ga),
                       ctrl_best_fresh22=ctrl.fs2022_min_equity.max() if len(ctrl) else np.nan,
                       ctrl_min_noentry=ctrl.fs2022_no_entry_days.min() if len(ctrl) else np.nan,
                       active_best_fresh22=ga.fs2022_min_equity.max() if len(ga) else np.nan,
                       active_best_note=ga.sort_values("fs2022_min_equity").note.iloc[-1] if len(ga) else "",
                       active_best_mtm=ga.sort_values("fs2022_min_equity").total_mtm.iloc[-1] if len(ga) else np.nan,
                       active_best_rectpd=ga.sort_values("fs2022_min_equity").rec_trades_day.iloc[-1] if len(ga) else np.nan))
    fr = pd.DataFrame(fr)
    fr.to_csv(os.path.join(OUTD, "activity_frontier_by_cap.csv"), index=False)
    print("== activity frontier (fresh-2022 no-entry <= 30 d) by total cap"); print(fr.round(1).to_string(index=False))
    # ---------------- 3. dead-slot economics
    cols = ["family", "note", "cap", "rec_cap", "dead_slot_frac", "slots_dead_avg", "dead20_slot_frac", "dist_dead_slot_frac", "active_slot_frac",
            "blocked_share", "shadow_signals", "shadow_trades", "shadow_pnl", "shadow_pnl_per_blocked_day", "shadow_pnl_per_year",
            "rec_pnl_per_slot_day", "rec_trades_per_active_slot_day", "rec_age_med_d", "rec_age_p90_d", "rec_age_p99_d", "rec_age_max_d"]
    ctrl = s1[s1.family == "A-STRUCT"][[c for c in cols if c in s1.columns]]
    ctrl.to_csv(os.path.join(OUTD, "dead_slot_economics_controls.csv"), index=False)
    print("== dead-slot economics (controls)"); print(ctrl.sort_values(["cap", "rec_cap"]).round(3).to_string(index=False))
    sv = s1[s1.family.isin(["A-SALV", "A-CSM"])]
    keep = [c for c in ["family", "note", "cap", "n_salvage", "salvage_n", "salvage_realized", "total_mtm", "max_mtm_dd", "fs2022_min_equity",
                        "fs2022_no_entry_days", "rec_trades_day", "dead_slot_frac"] if c in sv.columns]
    sv[keep].to_csv(os.path.join(OUTD, "salvage_economics.csv"), index=False)
    # ---------------- 4. nulls / true alpha
    nd = s1[["family", "note", "cap", "total_mtm", "nulld_passive_pnl", "nulld_passive_net", "timing_pnl", "exec_residual_pnl", "costs_total",
             "q_mean", "mtm_core", "mtm_rec", "rec_pnl", "max_mtm_dd", "fs2022_min_equity"]].copy() if "nulld_passive_pnl" in s1.columns else pd.DataFrame()
    if len(nd):
        nd["alpha_vs_passive"] = nd.total_mtm - nd.nulld_passive_net
        # passive constant-inventory long (NULL-D) path risk: daily adjusted closes x mean inventory, rolls charged
        pxd = _daily_close()
        rolls_per_day = _roll_days()
        dds, mins, f22 = [], [], []
        for q in nd.q_mean.values:
            pnl = q * pxd.diff().fillna(0.0) * 5.0 - q * rolls_per_day.reindex(pxd.index, fill_value=0) * 2.49
            eq = 150000 + pnl.cumsum()
            dds.append(float((eq - eq.cummax()).min())); mins.append(float(eq.min()))
            p22 = pnl[pnl.index >= "2022-01-01"]; e22 = 150000 + p22.cumsum(); f22.append(float(e22.min()))
        nd["passive_max_dd"] = dds; nd["passive_min_equity"] = mins; nd["passive_fresh22_min_equity"] = f22
        nd.to_csv(os.path.join(OUTD, "nulld_decomposition.csv"), index=False)
        print("== NULL-D (controls)"); print(nd[nd.family == "A-STRUCT"].sort_values("cap")[["note", "total_mtm", "nulld_passive_net", "alpha_vs_passive", "timing_pnl", "exec_residual_pnl", "costs_total", "q_mean", "max_mtm_dd", "passive_max_dd", "fs2022_min_equity", "passive_fresh22_min_equity"]].round(0).to_string(index=False))
    nc = s1[s1.family == "A-NULL-C"]
    if len(nc):
        out = []
        for par, g in nc.groupby("parent"):
            p = base.loc[par]
            for c in ("total_mtm", "rec_pnl", "timing_pnl", "max_mtm_dd", "fs2022_min_equity", "rec_trades_day", "fs2022_no_entry_days"):
                out.append(dict(parent_note=p.note, metric=c, fq=p[c], null_mean=g[c].mean(), null_p05=g[c].quantile(.05), null_p95=g[c].quantile(.95),
                                frac_null_ge_fq=float((g[c] >= p[c]).mean()), n=len(g)))
        out = pd.DataFrame(out)
        out.to_csv(os.path.join(OUTD, "nullc_random_timing.csv"), index=False)
        print("== NULL-C random recycle timing"); print(out.round(2).to_string(index=False))
    nb = s1[s1.family == "A-NULL-B"]
    if len(nb):
        cmp_ = []
        for _, r in nb.iterrows():
            p = base.loc[r.parent]
            cmp_.append(dict(note=r.note, parent=p.note, mtm=r.total_mtm, fq_mtm=p.total_mtm, rec_pnl=r.rec_pnl, fq_rec_pnl=p.rec_pnl,
                             dd=r.max_mtm_dd, fq_dd=p.max_mtm_dd, fresh22=r.fs2022_min_equity, fq_fresh22=p.fs2022_min_equity,
                             rectpd=r.rec_trades_day, fq_rectpd=p.rec_trades_day))
        cmp_ = pd.DataFrame(cmp_); cmp_.to_csv(os.path.join(OUTD, "nullb_dumb_recycle.csv"), index=False)
        print("== NULL-B dumb recycle"); print(cmp_.round(0).to_string(index=False))
    na = s1[s1.family == "A-NULL-A"]
    if len(na):
        ctl = s1[s1.family == "A-STRUCT"]
        rows = []
        for _, r in ctl.iterrows():
            j = (na.q_mean - r.q_mean).abs().idxmin()
            m = na.loc[j]
            rows.append(dict(fq=r.note, fq_qmean=r.q_mean, fq_mtm=r.total_mtm, fq_dd=r.max_mtm_dd, fq_fresh22=r.fs2022_min_equity,
                             core_only=m.note, co_qmean=m.q_mean, co_mtm=m.total_mtm, co_dd=m.max_mtm_dd, co_fresh22=m.fs2022_min_equity))
        rows = pd.DataFrame(rows); rows.to_csv(os.path.join(OUTD, "nulla_core_only_matched.csv"), index=False)
        print("== NULL-A exposure-matched core-only"); print(rows.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
