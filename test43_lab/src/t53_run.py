"""TEST53 capped shadow ensemble: one shared MNQ target (cap 2), shared day-loss governor, exactly as preregistered."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
import t48_engine as A  # noqa: E402
import t49_engine as T49  # noqa: E402
import t50_engine as V  # noqa: E402
import lane_vx  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test53"); os.makedirs(OUT, exist_ok=True)
FOLDS = C45.OUTER
J10 = C45.g("10:00")


def fold_ranges(sess):
    out = {}
    for name, a, b in FOLDS:
        out[name] = (int(np.searchsorted(sess.values, np.datetime64(a))), int(np.searchsorted(sess.values, np.datetime64(b), side="right")))
    return out


def exit_plan(rule, s, j, n):
    """planned exit (session, grid index)."""
    if rule in ("X30", "X60", "X120"):
        return s, min(j + int(rule[1:]), E.J1615)
    if rule == "X1600":
        return s, E.J1600
    if rule == "X1615":
        return s, E.J1615
    if rule == "NEXTOPEN":
        return (s + 1, 0) if s + 1 < n else (s, E.J1615)
    if rule == "NEXT1000":
        return (s + 1, J10) if s + 1 < n else (s, E.J1615)
    raise ValueError(rule)


def module_trades(nq, sess, check_inst=True):
    fr = fold_ranges(sess)
    rows = []
    # M1 GA-AC
    S = pd.read_csv(os.path.join(C45.ROOT, "out/test48/ga/GA-AC_selected.csv"))
    for name, (s0, s1) in fr.items():
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        if not len(r) or not isinstance(r.iloc[0].get("genome"), str):
            continue
        g = json.loads(r.iloc[0].genome)
        assert g["inst"] == "MNQ" or not check_inst
        ab = A.ArmBook(nq, xm=g["xm"])
        arm = ab.arms[g["setup"]].copy()
        if g["bull"]:
            arm[~nq.bull] = -1
        if g["volt_max"] < 1.0:
            arm[nq.volt > g["volt_max"]] = -1
        ent = A.entries(ab, g["setup"], g["conf"], W=g["W"], expx=g["expx"], arm=arm)
        for s in range(s0, s1):
            if ent[s] >= 0 and 5 * (ent[s] + 1) <= E.J_LAST_ENTRY:
                j = 5 * (ent[s] + 1); so, jo = exit_plan(g["exit"], s, j, nq.n)
                rows.append(("M1", s, j, so, jo, np.nan))
    # M2 GA-CT
    S = pd.read_csv(os.path.join(C45.ROOT, "out/test49/ga/GA-CT_selected.csv"))
    st = T49.State(nq)
    for name, (s0, s1) in fr.items():
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        g = json.loads(r.iloc[0].genome)
        assert g["inst"] == "MNQ" or not check_inst
        b0 = (C45.g(g["t0"]) + 1) // 5 - 1; b1 = min(b0 + g["span"], 74)
        cond = (st.ret >= g["k_ret"]) & (st.eff >= g["eff_min"]) & (np.nan_to_num(st.above) >= g["above_min"]) & (st.pos >= g["pos_min"])
        if g["volt_max"] < 1.0:
            cond &= (nq.volt <= g["volt_max"])[:, None]
        if g["bull"]:
            cond &= nq.bull[:, None]
        b = T49.first_trigger(st, cond, b0, b1)
        for s in range(s0, s1):
            if b[s] >= 0 and 5 * (b[s] + 1) <= E.J_LAST_ENTRY:
                j = 5 * (b[s] + 1); so, jo = exit_plan(g["exit"], s, j, nq.n)
                rows.append(("M2", s, j, so, jo, np.nan))
    # M3 GA-VX
    S = pd.read_csv(os.path.join(C45.ROOT, "out/test50/ga/GA-VX_selected.csv"))
    for name, (s0, s1) in fr.items():
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        g = json.loads(r.iloc[0].genome)
        assert g["inst"] == "MNQ" or not check_inst
        mask = np.ones(nq.n, bool)
        if g["bull"]:
            mask &= nq.bull
        if g["volt_max"] < 1.0:
            mask &= nq.volt <= g["volt_max"]
        valid = (nq.pn.sess >= pd.Timestamp("2019-07-01")) & (nq.atr > 0) & mask
        bmin = (C45.g(g["t_start"]) + 1) // 5 - 1
        ent, blo, bhi = V.scan(nq.o, nq.h, nq.l, nq.c, nq.u5, valid, V.KTYPES[g["ktype"]], float(lane_vx.KBASE[g["ktype"]] * g["kthr"]), int(g["L"]),
                               V.XTYPES[g["xtype"]], float(g["xsize"]), int(g["W"]), bmin, (C45.g("14:30") + 1) // 5 - 1, (C45.g("15:00") + 1) // 5 - 1)
        for s in range(s0, s1):
            if ent[s] >= 0 and 5 * (ent[s] + 1) <= 5 * 72:
                j = 5 * (ent[s] + 1); so, jo = exit_plan(g["exit"], s, j, nq.n)
                stp = blo[s] - g["buf"] * nq.u5[s] if g["stop"] else np.nan
                rows.append(("M3", s, j, so, jo, stp))
    # M4 opening drive
    b = T49.family_entries(st, "T1_OPENING_DRIVE", t="10:00", k=0.25)
    s21 = fr["O1_2021"][0]
    for s in range(s21, nq.n):
        if b[s] >= 0:
            j = 5 * (b[s] + 1); rows.append(("M4", s, j, s, E.J1615, np.nan))
    return pd.DataFrame(rows, columns=["mod", "s", "j", "s_out", "j_out", "stop"]).sort_values(["s", "j", "mod"]).reset_index(drop=True)


def simulate(nq, TR, cap=2, gov=-1000.0, slip=1.0, delay=0, miss=0.0, seed=5, cap_arr=None):
    """shared-target simulation; returns daily $ by module, trade ledger with actual exits."""
    n = nq.n; pv = nq.pv; cs = C45.cost_side(nq.k, slip)
    FP, FPb, L1, Cf = nq.FP, nq.FPb, nq.pn.L, nq.pn.Cf
    rng = np.random.default_rng(seed)
    by_s = {s: g for s, g in TR.groupby("s")}
    open_pos = []                                  # dicts: mod, s_in, j_in, px, s_out, j_out, stop
    daily = {m: np.zeros(n) for m in ("M1", "M2", "M3", "M4")}
    led = []
    count = np.zeros((n, C45.NG), np.int8)

    def close(p, s, j, px, why):
        if np.isnan(px):                                   # data gap: next valid print of the session (never earlier)
            row = FPb[s, j:]; ok = np.where(~np.isnan(row))[0]
            px = row[ok[0]] if len(ok) else np.nanmax(np.where(np.isnan(Cf[s]), -np.inf, Cf[s]))
            if not np.isfinite(px):
                px = p["px"]
        pnl = (px - p["px"]) * pv - 2 * cs
        daily[p["mod"]][s] += pnl
        led.append({**p, "s_x": s, "j_x": j, "px_x": px, "pnl": pnl, "why": why})

    for s in range(n):
        todays = by_s.get(s)
        ent = [] if todays is None else list(todays.itertuples(index=False))
        ei = 0; blocked = False; realized = 0.0
        for j in range(C45.NG):
            # scheduled exits (incl. overnight exits at the open / 10:00)
            keep = []
            for p in open_pos:
                if p["s_out"] == s and p["j_out"] == j:
                    px = FP[s, j] if j == 0 else FPb[s, j]
                    if np.isnan(px):
                        px = FPb[s, min(j + 1, C45.NG - 1)]
                    close(p, s, j, px, "planned"); realized += led[-1]["pnl"]
                elif p["s_in"] == s and not np.isnan(p["stop"]) and j > p["j_in"] and not np.isnan(L1[s, j]) and L1[s, j] <= p["stop"]:
                    op = FP[s, j]
                    px = min(p["stop"], op) if not np.isnan(op) else p["stop"]
                    close(p, s, j, px, "stop"); realized += led[-1]["pnl"]
                else:
                    keep.append(p)
            open_pos = keep
            # entries
            while ei < len(ent) and ent[ei].j + delay <= j:
                e = ent[ei]; ei += 1
                capj = cap if cap_arr is None else min(cap, cap_arr[s, j])
                if e.j + delay != j or blocked or len(open_pos) >= capj or (miss > 0 and rng.random() < miss):
                    continue
                px = FP[s, j]
                if np.isnan(px):
                    continue
                open_pos.append({"mod": e.mod, "s_in": s, "j_in": j, "px": px, "s_out": e.s_out, "j_out": e.j_out, "stop": e.stop})
            count[s, j] = len(open_pos)
            # governor (intraday only, RTH minutes before the lock)
            if not blocked and j < E.J1615 and open_pos:
                c = Cf[s, j]
                if not np.isnan(c):
                    unreal = sum((c - p["px"]) * pv for p in open_pos)
                    if realized + unreal <= gov:
                        blocked = True
                        jj = min(j + 1, E.J1615)
                        for p in open_pos:
                            close(p, s, jj, FPb[s, jj], "governor"); realized += led[-1]["pnl"]
                        open_pos = []
            if not blocked and j < E.J1615 and False:
                pass
        # end of session: positions whose planned exit is today at 16:15 were closed in the loop; stale same-day positions -> close at 16:15
        keep = []
        for p in open_pos:
            if p["s_out"] > s:
                keep.append(p)
            else:
                close(p, s, E.J1615, FPb[s, E.J1615], "eod")
        open_pos = keep
    return daily, pd.DataFrame(led), count


def matched_excess(nq, L):
    key = nq.year * 100 + nq.vt * 10 + nq.bull.astype(int)
    groups = {k: np.where(key == k)[0] for k in np.unique(key)}
    cs = C45.cost_side(nq.k)
    x = np.zeros(nq.n)
    for r in L.itertuples(index=False):
        idx = groups[key[r.s_in]]
        idx = idx[idx + (r.s_x - r.s_in) < nq.n]
        out = nq.FP[idx + 1, r.j_x] if (r.s_x > r.s_in and r.j_x == 0) else nq.FPb[idx + (r.s_x - r.s_in), r.j_x]
        base = np.nanmean((out - nq.FP[idx, r.j_in]) * nq.pv) - 2 * cs
        x[r.s_x] += r.pnl - base
    return x


def main():
    es, nq = E.setup()
    sess = nq.pn.sess
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    TR = module_trades(nq, sess)
    TR.to_csv(f"{OUT}/T53_module_signals.csv", index=False)
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))

    def run(cap=2, gov=-1000.0, **kw):
        daily, L, cnt = simulate(nq, TR, cap, gov, **kw)
        tot = sum(daily.values()); tot[:s21] = 0
        return tot, daily, L, cnt

    tot, daily, L, cnt = run()
    L.to_csv(f"{OUT}/T53_ledger.csv", index=False)
    exc = matched_excess(nq, L); exc[:s21] = 0
    # plateau
    pl = []
    for cap in (1, 2):
        for gv in (-800.0, -900.0, -1000.0, -1100.0, -1200.0):
            t, _, _, _ = run(cap, gv)
            pl.append({"cap": cap, "gov": gv, "total_2021": float(t[s21:].sum()), "avg_day": float(t[s21:].mean())})
    PL = pd.DataFrame(pl)
    base_total = float(tot[s21:].sum())
    plateau = bool((PL.total_2021 > 0).all() and (PL.total_2021 >= 0.6 * base_total).all())
    # stress
    st = []
    for nm, kw in (("base", {}), ("+5min entry delay", {"delay": 5}), ("4-tick slippage", {"slip": 4.0}), ("20% missed entries", {"miss": 0.2})):
        t, _, _, _ = run(**kw); st.append({"stress": nm, "avg_day": float(t[s21:].mean()), "total_2021": float(t[s21:].sum())})
    ST = pd.DataFrame(st)
    rec = sum(daily[m][s21:].sum() > 0 for m in daily)
    row = P.evaluate_module("TEST53 capped ensemble (cap2, gov -1000)", tot, exc, sess, champ,
                            {"plateau_pass": plateau, "recurrence_pass": rec >= 3, "stress4_pos": bool(ST[ST.stress == "4-tick slippage"].total_2021.iloc[0] > 0)})
    pE, pM = P.c43_positions(sess)
    tot_mnq = np.nan_to_num(pM) + cnt
    row.update({"peak_ensemble_MNQ": int(cnt.max()), "peak_total_MNQ_incl_C43": int(tot_mnq[s21:].max()),
                "share_minutes_total_MNQ_gt2": float((tot_mnq[s21:] > 2).mean()), "governor_days": int((L.why == "governor").groupby(L.s_x).any().sum()),
                "skipped_by_cap": int(len(TR[TR.s >= s21]) - len(L[L.s_in >= s21])), "modules_positive": int(rec)})
    G = pd.DataFrame([row]); G.to_csv(f"{OUT}/T53_gate.csv", index=False)
    attr = pd.DataFrame({m: {"total_2021": float(d[s21:].sum()), "avg_day": float(d[s21:].mean()), "trades": int((L["mod"] == m).sum())} for m, d in daily.items()}).T
    attr.to_csv(f"{OUT}/T53_attribution.csv"); PL.to_csv(f"{OUT}/T53_plateau.csv", index=False); ST.to_csv(f"{OUT}/T53_stress.csv", index=False)
    yr = pd.Series(tot[s21:], index=sess[s21:]).groupby(sess[s21:].year).agg(["sum", "mean"])
    yr.to_csv(f"{OUT}/T53_years.csv")
    np.save(f"{OUT}/T53_daily.npy", np.stack([tot, exc]))
    pd.set_option("display.width", 250)
    for k in ["folds_pos", "fold_median", "fold_worst", "standalone_avg_day", "standalone_max_dd", "standalone_worst_day", "matched_excess_day", "corr_C43",
              "comb_avg_day", "comb_max_dd", "comb_worst_day", "comb_ret_dd", "C43_ret_dd", "incr_avg_day", "active_days", "max_year_share", "remove_top3", "remove_top5",
              "roll6m_min", "roll12m_min", "roll12m_pos_share", "peak_ensemble_MNQ", "peak_total_MNQ_incl_C43", "share_minutes_total_MNQ_gt2", "governor_days",
              "skipped_by_cap", "modules_positive"] + [f"G{i}" for i in range(1, 10)] + ["PASS"]:
        print(k, round(row[k], 4) if isinstance(row[k], float) else row[k])
    print(attr.round(2)); print(PL.round(1)); print(ST.round(2)); print(yr.round(1))
    P.budget("TEST53", hypotheses=1, finalists=int(row["PASS"]), note="capped ensemble")


if __name__ == "__main__":
    main()
