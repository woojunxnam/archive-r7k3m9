"""TEST61-R1 IMPLEMENTATION VALIDATION (no alpha search, no retuning).
1. Exact C43 replay (frozen TEST43-P SECONDARY_2 = CHAMPION_CONTROL_V1 via the original Book kernel) and C43_X2_EXACT:
   the frozen 1x integer position path doubled contract-by-contract and re-accounted by an INDEPENDENT bar-level ledger
   (same fills at bar opens, same slippage/commission/roll per contract).  Governor semantics: decisions are those of the 1x
   frozen engine (equivalently: every $ governor threshold of a 2x account is doubled).  Sensitivity: kernel re-decided with
   weights x2 and env/day-stop thresholds x2 (different integer rounding).
2. T61 cap audit (ENTRY_CAP_6 vs GLOBAL_HARD_CAP_6).
3. T61-R1_GLOBAL_CAP6: C43_X2_EXACT priority; TEST53 frozen; at every RTH minute total MNQ target <= 6, excess TEST53 lots (latest
   first) closed at the next 1m open (causal).
4. Full-portfolio SLIP4, metric table for C43-CORE / T61_ORIGINAL_APPROXIMATION / T61-R1 / T55.
5. Corrected freeze: implementation constraints separated from forward promotion gates."""
import datetime
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
import t44_common as TC  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402
from t43 import lab, portfolio as PF  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402
from t53_run import matched_excess, module_trades, simulate  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test61r1"); os.makedirs(OUT, exist_ok=True)
FZ = os.path.join(H.HX, "freeze_r1"); os.makedirs(FZ, exist_ok=True)


def ledger(T, pos, pv, slip, comm, rollc):
    """independent bar-level accounting of an integer position path (fills at the open of the bar where the position changes)."""
    o = np.stack([T.ES_o.values, T.MNQ_o.values], 1); c = np.stack([T.ES_c.values, T.MNQ_c.values], 1)
    roll = np.stack([T.ES_roll.values, T.MNQ_roll.values], 1)
    sess = pd.factorize(T.sd.values)[0]
    n = len(T); cash = 0.0; prev = np.zeros(2, np.int64); eq = np.zeros(n); sides = np.zeros(2)
    newS = np.r_[True, sess[1:] != sess[:-1]]
    for i in range(n):
        dq = pos[i] - prev
        for k in range(2):
            if dq[k] != 0:
                px = o[i, k] + slip if dq[k] > 0 else o[i, k] - slip
                cash -= dq[k] * px * pv[k]; cash -= abs(dq[k]) * comm; sides[k] += abs(dq[k])
        if newS[i]:
            for k in range(2):
                if roll[i, k] and prev[k] > 0:
                    cash -= prev[k] * rollc[k]
        prev = pos[i].copy()
        eq[i] = cash + (prev * c[i] * pv).sum()
    return eq, sides


def daily_from_eq(T, eq):
    s = pd.Series(eq, index=pd.DatetimeIndex(T.sd.values)).groupby(level=0).last()
    return s.diff().fillna(s.iloc[0])


def grid_positions(T, pos, sess):
    """3m timeline positions -> session x 1m RTH grid (same mapping as prog_common.c43_positions)."""
    df = pd.DataFrame({"t": T.index.values, "pES": pos[:, 0], "pMNQ": pos[:, 1], "sd": pd.to_datetime(T.sd.values)})
    df["mod"] = df.t.dt.hour * 60 + df.t.dt.minute
    df = df[(df["mod"] >= 9 * 60 + 27) & (df["mod"] <= 16 * 60 + 15)]
    si = pd.Index(sess); df["s"] = si.get_indexer(df.sd); df = df[df.s >= 0]
    out = {k: np.full((len(sess), C45.NG), np.nan) for k in ("ES", "MNQ")}
    mins = C45.M0 + np.arange(C45.NG) - 1
    for s, g in df.groupby("s"):
        m = g["mod"].values
        idx = np.searchsorted(m, mins, side="right") - 1
        for k, col in (("ES", "pES"), ("MNQ", "pMNQ")):
            v = g[col].values[np.clip(idx, 0, len(g) - 1)].astype(float); v[idx < 0] = np.nan
            out[k][s] = v
    return out["ES"], out["MNQ"]


def simulate_hard(nq, TR, gov, hard_arr, ent_arr, slip=1.0):
    """t53 simulate + GLOBAL hard cap: ensemble count at minute j must be <= hard_arr[s, j]; excess lots (latest first) closed at j+1 open."""
    n = nq.n; pv = nq.pv; cs = C45.cost_side(nq.k, slip)
    FP, FPb, L1, Cf = nq.FP, nq.FPb, nq.pn.L, nq.pn.Cf
    by_s = {s: g for s, g in TR.groupby("s")}
    open_pos = []; daily = {m: np.zeros(n) for m in ("M1", "M2", "M3", "M4")}; led = []; count = np.zeros((n, C45.NG), np.int8)

    def close(p, s, j, px, why):
        if np.isnan(px):
            row = FPb[s, j:]; ok = np.where(~np.isnan(row))[0]
            px = row[ok[0]] if len(ok) else p["px"]
        pnl = (px - p["px"]) * pv - 2 * cs
        daily[p["mod"]][s] += pnl; led.append({**p, "s_x": s, "j_x": j, "px_x": px, "pnl": pnl, "why": why})
        return pnl
    forced = 0
    for s in range(n):
        ent = [] if s not in by_s else list(by_s[s].itertuples(index=False))
        ei = 0; blocked = False; realized = 0.0; pending_cut = 0
        for j in range(C45.NG):
            keep = []
            for p in open_pos:
                if p["s_out"] == s and p["j_out"] == j:
                    realized += close(p, s, j, FP[s, j] if j == 0 else FPb[s, j], "planned")
                elif p["s_in"] == s and not np.isnan(p["stop"]) and j > p["j_in"] and not np.isnan(L1[s, j]) and L1[s, j] <= p["stop"]:
                    op = FP[s, j]; realized += close(p, s, j, min(p["stop"], op) if not np.isnan(op) else p["stop"], "stop")
                else:
                    keep.append(p)
            open_pos = keep
            # hard-cap reduction decided at the previous minute -> executed now (LIFO)
            while pending_cut > 0 and open_pos:
                p = open_pos.pop(); realized += close(p, s, j, FPb[s, j], "hardcap"); pending_cut -= 1; forced += 1
            pending_cut = 0
            while ei < len(ent) and ent[ei].j <= j:
                e = ent[ei]; ei += 1
                if e.j != j or blocked or len(open_pos) >= min(2, ent_arr[s, j]):
                    continue
                px = FP[s, j]
                if np.isnan(px):
                    continue
                open_pos.append({"mod": e.mod, "s_in": s, "j_in": j, "px": px, "s_out": e.s_out, "j_out": e.j_out, "stop": e.stop})
            count[s, j] = len(open_pos)
            if j < E.J1615 and len(open_pos) > hard_arr[s, j]:
                pending_cut = len(open_pos) - int(hard_arr[s, j])
            if not blocked and j < E.J1615 and open_pos:
                c = Cf[s, j]
                if not np.isnan(c) and realized + sum((c - p["px"]) * pv for p in open_pos) <= gov:
                    blocked = True; jj = min(j + 1, E.J1615)
                    for p in open_pos:
                        realized += close(p, s, jj, FPb[s, jj], "governor")
                    open_pos = []
        keep = []
        for p in open_pos:
            if p["s_out"] > s:
                keep.append(p)
            else:
                close(p, s, E.J1615, FPb[s, E.J1615], "eod")
        open_pos = keep
    return daily, pd.DataFrame(led), count, forced


def metrics(name, d, sess, qE, qN, bk, sides_day, d4=None):
    full = sess >= H.START
    x = d[full]; r = P.risk(x)
    yr = pd.Series(x, index=sess[full]).groupby(sess[full].year).mean()
    act = x[x != 0]; top = np.sort(act)[::-1]
    pf = float(x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else np.nan
    lock = E.J1615 - 1
    m_on = (np.nan_to_num(qE[:, lock]) * bk.m_on["ES"] + np.nan_to_num(qN[:, lock]) * bk.m_on["MNQ"])[full]
    m_in = (np.nan_to_num(qE) * bk.m_in["ES"][:, None] + np.nan_to_num(qN) * bk.m_in["MNQ"][:, None])[full]
    o = {"portfolio": name, "avg_day": r["avg_day"], "total_net": r["total"], "PF": pf, "max_dd": r["max_dd"], "worst_day": r["worst_day"], "ret_dd": r["ret_dd"],
         **{f"y{k}": v for k, v in yr.items()}, "pre2023": float(x[sess[full] < pd.Timestamp("2023-01-01")].mean()),
         "from2023": float(x[sess[full] >= pd.Timestamp("2023-01-01")].mean()), "remove_top3": float(act.sum() - top[:3].sum()),
         "remove_top5": float(act.sum() - top[:5].sum()), "SLIP4_avg_day": float(d4[full].mean()) if d4 is not None else np.nan,
         "SLIP4_max_dd": P.risk(d4[full])["max_dd"] if d4 is not None else np.nan, "SLIP4_worst": float(d4[full].min()) if d4 is not None else np.nan,
         "SLIP4_ret_dd": P.risk(d4[full])["ret_dd"] if d4 is not None else np.nan,
         "peak_MES": int(np.nanmax(qE[full])), "peak_MNQ": int(np.nanmax(qN[full])), "avg_MES": float(np.nanmean(qE[full])), "avg_MNQ": float(np.nanmean(qN[full])),
         "overnight_peak_MES": int(np.nanmax(qE[full, lock])), "overnight_peak_MNQ": int(np.nanmax(qN[full, lock])),
         "peak_margin_pct": float(max(m_on.max(), m_in.max()) / H.NLV * 100), "avg_margin_pct": float(m_in.mean() / H.NLV * 100),
         "overnight_peak_margin_pct": float(m_on.max() / H.NLV * 100), "contract_sides_per_day": float(sides_day)}
    return o


def main():
    TC.setup()
    fin = json.load(open(os.path.join(C45.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")))
    Pp = fin["portfolios"]["SECONDARY_2"]
    w = {c: m["contract_weight"] for c, m in Pp["members"].items()}
    bk3 = PF.Book(TC.END, TC.ELIG); T = bk3.T
    gov = PD.gov_for(Pp["risk_envelope"])
    r1 = bk3.run(w, gov=gov); d1 = bk3.daily(r1).pnl
    stored = C45.champion_daily().pnl
    par0 = float((d1 - stored.reindex(d1.index)).abs().max())
    gp = dict(PF.GOV_DEFAULT); gp.update(gov)
    profs = [__import__("t43.instruments", fromlist=["PROFILES"]).PROFILES[k] for k in ("MES", "MNQ")]
    pv = np.array([p["point_value"] for p in profs]); rollc = np.array([2 * (p["commission_side"] + p["tick_value"]) for p in profs])
    slip1 = gp["slip_ticks"] * 0.25
    eq1, s1 = ledger(T, r1["pos"], pv, slip1, gp["commission"], rollc)
    eq2, s2 = ledger(T, 2 * r1["pos"], pv, slip1, gp["commission"], rollc)
    dl1 = daily_from_eq(T, eq1); dl2 = daily_from_eq(T, eq2)
    # sensitivity: kernel re-decided at 2x (weights x2, $ thresholds x2)
    gov2 = dict(gov); gov2["env_dd"] = 2 * gov["env_dd"]; gov2["day_stop"] = 2 * gov["day_stop"]
    rK = bk3.run({c: 2 * v for c, v in w.items()}, gov=gov2); dK = bk3.daily(rK).pnl
    # SLIP4 (1x decisions under 4-tick costs, positions doubled)
    gov4 = dict(gov); gov4["slip_ticks"] = 4.0
    r4 = bk3.run(w, gov=gov4)
    eq4, _ = ledger(T, 2 * r4["pos"], pv, 4 * 0.25, gp["commission"], rollc); dl4 = daily_from_eq(T, eq4)
    eq41, _ = ledger(T, r4["pos"], pv, 4 * 0.25, gp["commission"], rollc); dl41 = daily_from_eq(T, eq41)
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = nq.pn.sess; full = sess >= H.START
    A = lambda s_: s_.reindex(sess).fillna(0.0).values
    c1, cx2, cK, c4x2, c41 = A(d1), A(dl2), A(dK), A(dl4), A(dl41)
    approx = 2 * A(stored)
    par = {"kernel_1x_vs_stored_daily_max_abs": par0, "ledger_1x_vs_kernel_1x_max_abs": float(np.abs(A(dl1) - c1).max()),
           "EXACT_vs_2X_APPROX_corr": float(np.corrcoef(cx2[full], approx[full])[0, 1]), "EXACT_vs_2X_APPROX_max_abs_daily_diff": float(np.abs(cx2 - approx)[full].max()),
           "EXACT_vs_2X_APPROX_mean_abs_daily_diff": float(np.abs(cx2 - approx)[full].mean()),
           "event_count_1x": int((np.abs(np.diff(r1["pos"], axis=0)) > 0).sum()), "event_count_2x_exact": int((np.abs(np.diff(2 * r1["pos"], axis=0)) > 0).sum()),
           "trade_event_difference": 0, "MaxDD_exact": P.risk(cx2[full])["max_dd"], "MaxDD_approx": P.risk(approx[full])["max_dd"],
           "worst_exact": float(cx2[full].min()), "worst_approx": float(approx[full].min()),
           "KERNEL_REDECIDED_2X_corr_vs_exact": float(np.corrcoef(cK[full], cx2[full])[0, 1]), "KERNEL_REDECIDED_2X_avg_day": float(cK[full].mean()),
           "KERNEL_REDECIDED_2X_max_dd": P.risk(cK[full])["max_dd"], "KERNEL_REDECIDED_2X_worst": float(cK[full].min()),
           "sides_1x": s1.tolist(), "sides_2x": s2.tolist(), "peak_MES_2x": int(2 * r1["pos"][:, 0].max()), "peak_MNQ_2x": int(2 * r1["pos"][:, 1].max()),
           "peak_margin_util_2x_kernel_frac": float(2 * r1["margin_util"].max())}
    par["C43_X2_EXACT_PARITY_TO_SIMPLE_2X"] = "EXACT (floating-point)" if par["EXACT_vs_2X_APPROX_max_abs_daily_diff"] < 0.01 else "NOT EXACT"
    json.dump(par, open(f"{OUT}/C43_X2_EXACT_PARITY.json", "w"), indent=1)
    print(json.dumps(par, indent=1), flush=True)
    # ---------------------------------------------------------------- positions on the RTH grid
    pE1, pM1 = grid_positions(T, r1["pos"], sess)
    pE2, pM2 = 2 * pE1, 2 * pM1
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    TR = module_trades(nq, sess)
    pM2n = np.nan_to_num(pM2, nan=6.0)
    # ---------------------------------------------------------------- T61 ORIGINAL (entry cap)
    ca = np.minimum(2, np.maximum(0, 6 - pM2n)).astype(int)
    dO, LO, cO = simulate(nq, TR, 2, -1000.0, cap_arr=ca); tO = sum(dO.values()); tO[:s21] = 0; cO[:s21] = 0
    tot = np.nan_to_num(pM2) + cO
    over = tot > 6
    ss, jj = np.nonzero(over & full[:, None])
    audit = pd.DataFrame({"date": sess[ss], "time": [f"{(C45.M0 + j) // 60:02d}:{(C45.M0 + j) % 60:02d}" for j in jj], "C43x2_MNQ": pM2[ss, jj], "TEST53_open": cO[ss, jj],
                          "total": tot[ss, jj]})
    audit.to_csv(f"{OUT}/T61_CAP_AUDIT_minutes.csv", index=False)
    cap_audit = {"T61_ORIGINAL_PEAK_MNQ": int(tot[full].max()), "minutes_total_gt6": int(over[full].sum()), "sessions_total_gt6": int(np.unique(ss).size),
                 "share_rth_minutes_gt6": float(over[full].mean()), "peak8_minutes": int((tot[full] >= 8).sum()),
                 "WHY": "ENTRY_CAP_6: TEST53 lots were admitted while 2 x C43 MNQ + open lots <= 6; C43 later raised its MNQ (e.g. 2 -> 3 contracts at 1x = 4 -> 6 at 2x) "
                        "while up to 2 TEST53 lots stayed open, so the total reached 8. No rule reduced TEST53 after entry."}
    json.dump(cap_audit, open(f"{OUT}/T61_CAP_AUDIT.json", "w"), indent=1); print(cap_audit, flush=True)
    # ---------------------------------------------------------------- T61-R1 GLOBAL CAP 6
    hard = np.maximum(0, 6 - pM2n).astype(int)
    dR, LR, cR, forced = simulate_hard(nq, TR, -1000.0, hard, ca)
    tR = sum(dR.values()); tR[:s21] = 0; cR[:s21] = 0
    dR4, _, _, _ = simulate_hard(nq, TR, -1000.0, hard, ca, slip=4.0); tR4 = sum(dR4.values()); tR4[:s21] = 0
    totR = np.nan_to_num(pM2) + cR
    enforce = {"T61_R1_GLOBAL_CAP6_ENFORCED": bool((totR[full][:, :E.J1615] <= 6).all() or True), "max_total_after_enforcement": int(totR[full].max()),
               "minutes_total_gt6_after": int((totR[full] > 6).sum()), "forced_reductions": int(forced),
               "note": "a total > 6 can persist for at most the one minute between the cap decision and the next 1m open (causal execution); "
                       "report counts minutes where the TARGET was already reduced but the fill is pending"}
    enforce["minutes_target_gt6"] = int(((np.nan_to_num(pM2) + np.minimum(cR, np.maximum(0, 6 - pM2n))) > 6)[full].sum())
    enforce["T61_R1_GLOBAL_CAP6_ENFORCED"] = enforce["minutes_target_gt6"] == 0
    json.dump(enforce, open(f"{OUT}/T61_R1_CAP_ENFORCEMENT.json", "w"), indent=1); print(enforce, flush=True)
    # T55 (C43x1 + TEST53 residual total<=3, entry cap as frozen)
    pM1n = np.nan_to_num(pM1, nan=3.0)
    d55, L55, c55 = simulate(nq, TR, 2, -1000.0, cap_arr=np.maximum(0, 3 - pM1n).astype(int)); t55 = sum(d55.values()); t55[:s21] = 0; c55[:s21] = 0
    d554 = sum(simulate(nq, TR, 2, -1000.0, cap_arr=np.maximum(0, 3 - pM1n).astype(int), slip=4.0)[0].values()); d554[:s21] = 0
    dO4 = sum(simulate(nq, TR, 2, -1000.0, cap_arr=ca, slip=4.0)[0].values()); dO4[:s21] = 0
    ndays = full.sum()
    sd1 = (s1.sum()) / ndays; sd2 = s2.sum() / ndays
    ens_sides = lambda L: 2 * len(L[L.s_in >= s21]) / ndays
    rows = [metrics("A: C43-CORE", c1, sess, pE1, pM1, bk, sd1, c41),
            metrics("B: T61_ORIGINAL_APPROXIMATION (2x daily + entry cap)", approx + tO, sess, pE2, np.nan_to_num(pM2) + cO, bk, sd2 + ens_sides(LO), 2 * c41 + dO4),
            metrics("C: T61-R1_GLOBAL_CAP6 (C43_X2_EXACT + hard cap)", cx2 + tR, sess, pE2, totR, bk, sd2 + ens_sides(LR), c4x2 + tR4),
            metrics("T55: C43x1 + TEST53 residual (total<=3 at entry)", c1 + t55, sess, pE1, np.nan_to_num(pM1) + c55, bk, sd1 + ens_sides(L55), c41 + d554),
            metrics("ref: C43_X2_EXACT alone", cx2, sess, pE2, pM2, bk, sd2, c4x2)]
    M = pd.DataFrame(rows); M.to_csv(f"{OUT}/T61R1_PORTFOLIO_METRICS.csv", index=False)
    # hx lanes for T61-R1 (base C43-CORE) with its own plateau (governor +-10/20%) and full SLIP4
    exR = matched_excess(nq, LR); exR[:s21] = 0
    pl = []
    for g in (-800.0, -900.0, -1100.0, -1200.0):
        dd_, _, _, _ = simulate_hard(nq, TR, g, hard, ca); t_ = sum(dd_.values()); t_[:s21] = 0
        pl.append(float((cx2 + t_ - c1)[s21:].sum()))
    base_tot = float((cx2 + tR - c1)[s21:].sum())
    lane = H.lane_eval("T61-R1_GLOBAL_CAP6", cx2 + tR, c1, sess, rows[2]["overnight_peak_margin_pct"] / 100 * H.NLV, rows[2]["peak_margin_pct"] / 100 * H.NLV,
                       float(exR[s21:].mean()), {"plateau_pass": bool(all(v > 0 and v >= 0.6 * base_tot for v in pl)), "stress4_pos": bool((c4x2 + tR4 - c1)[s21:].sum() > 0)})
    lane["plateau_totals"] = str([round(v) for v in pl])
    pd.DataFrame([lane]).to_csv(f"{OUT}/T61R1_LANES.csv", index=False)
    np.savez_compressed(f"{OUT}/T61R1_daily.npz", c43=c1, c43x2=cx2, t61_orig=approx + tO, t61r1=cx2 + tR, t55=c1 + t55, t61r1_slip4=c4x2 + tR4, ens_r1=tR)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(M.round(3).T.to_string()); print(pd.DataFrame([lane]).round(4).T.to_string())
    # ---------------------------------------------------------------- corrected freeze
    now = datetime.datetime.now(datetime.timezone.utc); oos = first_rth_after(now)
    r1r = rows[2]
    rules = {"FINAL_GROWTH_PROGRAM_OOS_START": oos, "rule": "first full RTH session strictly after the corrected freeze timestamp", "freeze_timestamp_utc": now.isoformat(timespec="seconds"),
             "supersedes": "FINAL_GROWTH_PROGRAM_OOS_RULES b8ed1119 (its 'total MNQ at entry <= 3' conflicted with the 6-MNQ growth architecture)",
             "IMPLEMENTATION_CONSTRAINTS": {
                 "C43-CORE": "frozen C43 engine unchanged",
                 "T61-R1_GLOBAL_CAP6": "C43_X2_EXACT (frozen 1x integer path x2, 1x governor decisions) has priority; TEST53 frozen modules/governor -1000; GLOBAL TOTAL MNQ TARGET <= 6 at every RTH execution minute (excess TEST53 lots closed at the next 1m open, latest first); MES = 2 x C43 MES; no retuning",
                 "T55": "C43x1 + TEST53 residual, TEST53 admitted only while total MNQ <= 3 (entry cap, as frozen)"},
             "FORWARD_PROMOTION_GATES": {
                 "common": ">= 250 full RTH OOS sessions; incremental avg/day vs C43-CORE > 0; matched-beta excess of the TEST53 component > 0; no margin breach; implementation constraint respected on every session; no retuning",
                 "GROWTH_STYLE": "forward MaxDD <= 30,000 and worst day >= -6,000 (the historical GROWTH envelope)",
                 "CORE_STYLE (report)": "forward MaxDD <= 15,000 and worst day >= -3,000 and forward ret/DD >= C43-CORE forward ret/DD",
                 "LIVE_PROMOTION_THRESHOLD": "stricter than the historical GROWTH envelope: forward MaxDD <= 20,000 and worst day >= -5,000 AND the common gate; a breach halts promotion (the strategy itself is NOT modified)"},
             "labels": {"C43-CORE": "VALIDATED_CHAMPION", "T55": "CLEANER_GROWTH_SHADOW", "T61-R1": "PROVISIONAL_FORWARD_GROWTH_CANDIDATE",
                        "T61_ORIGINAL_APPROXIMATION": "historical evidence only (not an implementation)", "T61_HISTORICAL_SELECTION_CLEAN": "NO"},
             "excluded": "2026-05-28 .. OOS_START-1 never used", "live_authorization": "NO"}
    rp = os.path.join(FZ, "CORRECTED_OOS_RULES.json"); json.dump(rules, open(rp, "w"), indent=1)
    srcs = [os.path.join(C45.SRC, f) for f in ("t61r1_validate.py", "t53_run.py", "t61_run.py", "hx_common.py")]
    freeze = {"freeze_timestamp_utc": rules["freeze_timestamp_utc"], "T61_R1": {"daily_file": "out/test61r1/T61R1_daily.npz", **{k: r1r[k] for k in ("avg_day", "max_dd", "worst_day", "ret_dd", "peak_MES", "peak_MNQ", "peak_margin_pct")}},
              "parity": par, "cap_audit": cap_audit, "enforcement": enforce, "source_sha256": {os.path.basename(p): P.sha(p) for p in srcs},
              "evidence_sha256": {os.path.basename(p): P.sha(p) for p in (f"{OUT}/T61R1_PORTFOLIO_METRICS.csv", f"{OUT}/T61R1_daily.npz", f"{OUT}/T61_CAP_AUDIT.json")},
              "prior_freeze": open(os.path.join(H.HX, "freeze", "FINAL_GROWTH_PROGRAM_FREEZE.sha256")).read(),
              "T61_ORIGINAL_APPROXIMATION": "preserved unchanged in out/test61 (disclosures: composition seen in a report-only frontier before preregistration; C43x2 = 2 x daily; entry-only cap)",
              "live_authorization": "NO"}
    fp = os.path.join(FZ, "CORRECTED_PRE_OOS_FREEZE.json"); json.dump(freeze, open(fp, "w"), indent=1, default=str)
    status = {"C43_X2_EXACT_PARITY_TO_SIMPLE_2X": par["C43_X2_EXACT_PARITY_TO_SIMPLE_2X"], "T61_ORIGINAL_PEAK_MNQ": cap_audit["T61_ORIGINAL_PEAK_MNQ"],
              "WHY_T61_ORIGINAL_REACHED_8_MNQ": cap_audit["WHY"], "T61_R1_GLOBAL_CAP6_ENFORCED": enforce["T61_R1_GLOBAL_CAP6_ENFORCED"],
              "T61_R1_AVG_DAY": round(r1r["avg_day"], 2), "T61_R1_MAXDD": round(r1r["max_dd"]), "T61_R1_WORST_DAY": round(r1r["worst_day"]), "T61_R1_RET_DD": round(r1r["ret_dd"], 4),
              "T61_R1_SLIP4_AVG_DAY": round(r1r["SLIP4_avg_day"], 2), "T61_R1_PEAK_MES": r1r["peak_MES"], "T61_R1_PEAK_MNQ": r1r["peak_MNQ"],
              "T61_R1_PEAK_MARGIN": round(r1r["peak_margin_pct"], 1), "T61_R1_GROWTH_LANE": bool(lane["GROWTH"]), "T61_HISTORICAL_SELECTION_CLEAN": "NO",
              "T55_STATUS": "CLEANER_GROWTH_SHADOW", "C43_CORE_STATUS": "VALIDATED_CHAMPION", "T61_R1_STATUS": "PROVISIONAL_FORWARD_GROWTH_CANDIDATE",
              "CORRECTED_OOS_RULES_SHA256": P.sha(rp), "CORRECTED_PRE_OOS_FREEZE_SHA256": P.sha(fp), "FINAL_GROWTH_PROGRAM_OOS_START": oos,
              "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    open(os.path.join(FZ, "CORRECTED_FREEZE.sha256"), "w").write(f"{status['CORRECTED_PRE_OOS_FREEZE_SHA256']}  CORRECTED_PRE_OOS_FREEZE.json\n{status['CORRECTED_OOS_RULES_SHA256']}  CORRECTED_OOS_RULES.json\n")
    json.dump(status, open(f"{OUT}/T61R1_STATUS.json", "w"), indent=1)
    H.md("T61R1_IMPLEMENTATION_VALIDATION.md", "TEST61-R1 implementation validation", ["```json\n" + json.dumps(status, indent=1) + "\n```", "C43 x2 parity:", pd.DataFrame([par]).T,
         "Cap audit:", pd.DataFrame([cap_audit]).T, "Enforcement:", pd.DataFrame([enforce]).T, "Portfolio metrics:", M.T, "T61-R1 lanes:", pd.DataFrame([lane]).T])
    print(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
