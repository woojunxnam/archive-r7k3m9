"""T61-R1 C43 x2 GOVERNOR AUDIT (implementation diagnostics; no retuning).
Variants (all on the $150k account, original margin logic):
  SIMPLE_2X_DAILY_APPROX : 2 x stored C43 daily P&L (the old T61 approximation)
  X2_A_INT  : integer C43 targets doubled (1x float target -> 1x integer decision -> x2), $ DD / day-stop thresholds UNCHANGED, decisions recomputed causally
  X2_B_INT  : integer C43 targets doubled, $ thresholds x2, recomputed  (== TEST61 preregistered semantics "integer contract doubling; governor
              thresholds scaled equally")
  X2_A_FLOAT: float desired targets doubled before integer rounding/deadband (Book.run weights x2), thresholds unchanged
  X2_B_FLOAT: float desired targets doubled, thresholds x2
T61-R1A / T61-R1B = X2_A_INT / X2_B_INT + TEST53 residual + GLOBAL total MNQ target <= 6 (TEST53 reduced at the next 1m open).
FLOAT variants are reported as diagnostics with the same global cap.  The nominated architecture is fixed by the TEST61 preregistration: X2_B_INT."""
import datetime
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
import t44_common as TC  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402
from t43 import instruments, lab, portfolio as PF, v6lab  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402
from t53_run import matched_excess, module_trades, simulate  # noqa: E402
from t61r1_validate import grid_positions, metrics, simulate_hard  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test61r1"); FZ = os.path.join(H.HX, "freeze_r1")


@njit(cache=True)
def kernel_mult(o, c, raw, valid, roll, atrD, rth, sessid, D, pv, fin, fon, rollc, INIT, marginU, dd1, dd2, m1, m2,
                dayStop, dayMult, atrCap, instShare, deadband, slip, comm, delay, mult):
    """identical to t43.portfolio.kernel except: the integer decision is taken on the 1x float target and the order is mult x that
    integer (integer contract multiplication); equity/margin/governor are evaluated on the multiplied book."""
    n, K = o.shape
    pos = np.zeros(K, np.int64); avg = np.zeros(K); realized = 0.0
    pend = np.zeros(K, np.int64); pendAt = np.full(K, -1, np.int64)
    pos_arr = np.zeros((n, K), np.int64); eq_arr = np.zeros(n); mu_arr = np.zeros(n)
    sides = np.zeros(K)
    hwm = INIT; level = 0; sessStart = INIT; dayCut = False; prev_eq = INIT
    for i in range(n):
        newSess = i == 0 or sessid[i] != sessid[i - 1]
        for k in range(K):
            if pend[k] != 0 and valid[i, k] and i - pendAt[k] >= 1 + delay:
                q = pend[k]
                px = o[i, k] + slip if q > 0 else o[i, k] - slip
                if q > 0:
                    avg[k] = (avg[k] * pos[k] + px * q) / (pos[k] + q)
                else:
                    realized += (px - avg[k]) * pv[k] * (-q)
                pos[k] += q
                realized -= abs(q) * comm
                sides[k] += abs(q)
                if pos[k] == 0:
                    avg[k] = 0.0
                pend[k] = 0; pendAt[k] = -1
        if newSess:
            for k in range(K):
                if roll[i, k] and pos[k] > 0:
                    realized -= pos[k] * rollc[k]
        eq = INIT + realized
        for k in range(K):
            if pos[k] > 0:
                eq += (c[i, k] - avg[k]) * pv[k] * pos[k]
        if newSess:
            sessStart = prev_eq; dayCut = False
            if level > 0 and hwm - eq < 0.5 * dd1:
                level = 0; hwm = max(hwm, eq)
        if level == 0 and eq > hwm:
            hwm = eq
        dd = hwm - eq
        if dd2 > 0 and dd >= dd2:
            level = max(level, 2)
        elif dd1 > 0 and dd >= dd1:
            level = max(level, 1)
        g = 1.0 if level == 0 else (m1 if level == 1 else m2)
        if dayStop > 0 and eq - sessStart <= -dayStop:
            dayCut = True
        if dayCut:
            g *= dayMult
        x = np.zeros(K); capped = False
        onSide = (not rth[i]) or (i + 1 < n and not rth[i + 1])
        for k in range(K):
            x[k] = max(D[i, k] * g, 0.0)
        if atrCap > 0:
            tot = 0.0
            for k in range(K):
                tot += mult * x[k] * pv[k] * atrD[i, k]
            if tot > atrCap:
                capped = True
                for k in range(K):
                    x[k] *= atrCap / tot
        req = 0.0
        for k in range(K):
            req += mult * x[k] * raw[i, k] * pv[k] * (fon[k] if onSide else fin[k])
        lim = marginU * max(eq, 0.0)
        if req > lim and req > 0:
            capped = True
            for k in range(K):
                x[k] *= lim / req
        for k in range(K):
            p1 = pos[k] // mult                    # 1x-equivalent current integer position
            tk = p1
            if abs(x[k] - p1) >= deadband or x[k] < p1 - 1e-9 and math.floor(x[k]) < p1:
                tk = int(math.floor(x[k] + 0.5))
            if tk > x[k] + 0.5:
                tk = int(math.floor(x[k] + 0.5))
            if capped and tk > x[k]:
                tk = int(math.floor(x[k]))
            if tk < 0:
                tk = 0
            if tk * mult != pos[k] and pend[k] == 0:
                pend[k] = tk * mult - pos[k]; pendAt[k] = i
        u = 0.0
        for k in range(K):
            u += pos[k] * raw[i, k] * pv[k] * (fon[k] if not rth[i] else fin[k])
        mu_arr[i] = u / max(eq, 1.0)
        for k in range(K):
            pos_arr[i, k] = pos[k]
        eq_arr[i] = eq; prev_eq = eq
    return pos_arr, eq_arr, mu_arr, sides


def run_mult(bk, w, gov, mult, slip_ticks=None):
    gp = dict(PF.GOV_DEFAULT); gp.update(gov)
    if slip_ticks is not None:
        gp["slip_ticks"] = slip_ticks
    T = bk.T; n = len(T)
    D = np.zeros((n, 2))
    for cid, wt in w.items():
        D[:, PF.INSTS.index(bk.inst[cid])] += wt * bk.des[cid]
    profs = [instruments.PROFILES[v6lab.PROF[i]] for i in PF.INSTS]
    pv = np.array([p["point_value"] for p in profs])
    fin = np.array([instruments.margin_frac(p, "intraday") for p in profs]) * gp["m_intra"]
    fon = np.array([instruments.margin_frac(p, "overnight") for p in profs]) * gp["m_on"]
    rollc = np.array([2 * (p["commission_side"] + p["tick_value"]) for p in profs])
    env = gp.get("env_dd", 0.0)
    st = lambda a, b: np.stack([T[a].values, T[b].values], 1)
    pos, eq, mu, sides = kernel_mult(st("ES_o", "MNQ_o"), st("ES_c", "MNQ_c"), st("ES_raw", "MNQ_raw"), st("ES_valid", "MNQ_valid"), st("ES_roll", "MNQ_roll"),
                                     st("ES_atrD", "MNQ_atrD"), T.rth.values, bk.sess_codes, D, pv, fin, fon, rollc, lab.INIT, gp["marginU"],
                                     gp["dd1_frac"] * env, gp["dd2_frac"] * env, gp["m1"], gp["m2"], gp.get("day_stop", 0.0), gp["day_mult"], gp["atr_cap"],
                                     gp["inst_share"], gp["deadband"], gp["slip_ticks"] * 0.25, gp["commission"], int(gp["delay"]), int(mult))
    s = pd.Series(eq, index=pd.DatetimeIndex(T.sd.values)).groupby(level=0).last()
    return {"pos": pos, "daily": s.diff().fillna(s.iloc[0] - lab.INIT), "mu": mu, "sides": sides}


def run_float(bk, w, gov, mult, slip_ticks=None):
    g = dict(gov)
    if slip_ticks is not None:
        g["slip_ticks"] = slip_ticks
    r = bk.run({c: mult * v for c, v in w.items()}, gov=g)
    d = bk.daily(r)
    return {"pos": r["pos"], "daily": d.pnl, "mu": r["margin_util"], "sides": r["sides"]}


def main():
    TC.setup()
    fin = json.load(open(os.path.join(C45.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")))
    Pp = fin["portfolios"]["SECONDARY_2"]; w = {c: m["contract_weight"] for c, m in Pp["members"].items()}
    bk3 = PF.Book(TC.END, TC.ELIG); T = bk3.T
    gov1 = PD.gov_for(Pp["risk_envelope"]); gov2 = dict(gov1); gov2["env_dd"] = 2 * gov1["env_dd"]; gov2["day_stop"] = 2 * gov1["day_stop"]
    base1 = run_mult(bk3, w, gov1, 1)
    stored = C45.champion_daily().pnl
    qa_kernel_copy = float((base1["daily"] - stored.reindex(base1["daily"].index)).abs().max())
    V = {"X2_A_INT": (run_mult, gov1), "X2_B_INT": (run_mult, gov2), "X2_A_FLOAT": (run_float, gov1), "X2_B_FLOAT": (run_float, gov2)}
    R = {k: f(bk3, w, g, 2) for k, (f, g) in V.items()}
    R4 = {k: f(bk3, w, g, 2, slip_ticks=4.0) for k, (f, g) in V.items()}
    r41 = run_mult(bk3, w, gov1, 1, slip_ticks=4.0)
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = nq.pn.sess; full = sess >= H.START
    A = lambda s_: s_.reindex(sess).fillna(0.0).values
    simple = 2 * A(stored); c1 = A(stored)
    rows = []; ndays = full.sum()
    ref_pos = 2 * base1["pos"]
    for k, r in R.items():
        d = A(r["daily"])
        yr = pd.Series(d[full], index=sess[full]).groupby(sess[full].year).mean()
        rows.append({"variant": k, "avg_day": float(d[full].mean()), "corr_to_simple_2x": float(np.corrcoef(d[full], simple[full])[0, 1]),
                     "mean_abs_daily_diff": float(np.abs(d - simple)[full].mean()), "max_abs_daily_diff": float(np.abs(d - simple)[full].max()),
                     "events": int((np.abs(np.diff(r["pos"], axis=0)) > 0).sum()), "events_simple": int((np.abs(np.diff(ref_pos, axis=0)) > 0).sum()),
                     "bars_position_differs_from_2x_path": float((r["pos"] != ref_pos).any(1).mean()), "max_dd": P.risk(d[full])["max_dd"], "worst_day": float(d[full].min()),
                     "ret_dd": P.risk(d[full])["ret_dd"], **{f"y{y}": v for y, v in yr.items()}, "peak_MES": int(r["pos"][:, 0].max()), "peak_MNQ": int(r["pos"][:, 1].max()),
                     "peak_margin_util": float(np.max(r["mu"])), "sides_per_day": float(np.sum(r["sides"]) / ndays),
                     "SLIP4_avg_day": float(A(R4[k]["daily"])[full].mean())})
    rows.insert(0, {"variant": "SIMPLE_2X_DAILY_APPROX", "avg_day": float(simple[full].mean()), "corr_to_simple_2x": 1.0, "mean_abs_daily_diff": 0.0, "max_abs_daily_diff": 0.0,
                    "events": int((np.abs(np.diff(ref_pos, axis=0)) > 0).sum()), "bars_position_differs_from_2x_path": 0.0, "max_dd": P.risk(simple[full])["max_dd"],
                    "worst_day": float(simple[full].min()), "ret_dd": P.risk(simple[full])["ret_dd"],
                    **{f"y{y}": v for y, v in pd.Series(simple[full], index=sess[full]).groupby(sess[full].year).mean().items()},
                    "peak_MES": int(ref_pos[:, 0].max()), "peak_MNQ": int(ref_pos[:, 1].max()), "peak_margin_util": float(2 * np.max(base1["mu"])),
                    "sides_per_day": float(2 * np.sum(base1["sides"]) / ndays), "SLIP4_avg_day": float(2 * A(r41["daily"])[full].mean())})
    X2 = pd.DataFrame(rows); X2.to_csv(f"{OUT}/C43_X2_THREE_WAY.csv", index=False)
    why = {"SIMPLE_2X_DAILY_APPROX": "2 x the 1x daily P&L; identical to doubling the 1x integer position path (P&L and per-contract costs are linear) - proven: X2_B_INT max |diff| below.",
           "X2_B_INT": "integer decisions from the 1x float target, orders doubled, $ thresholds doubled -> the equity path is exactly 2x the 1x path, so every governor "
                       "comparison (dd >= 2*dd1, day P&L <= -2*stop) has the same truth value as at 1x: decisions identical, P&L exactly 2x.",
           "X2_A_INT": "same integer doubling but $ thresholds unchanged: the 2x equity path hits the DD / day-stop tiers at HALF the relative drawdown, so the governor "
                       "de-risks earlier and more often (lower exposure after losses, different recovery path).",
           "X2_A_FLOAT / X2_B_FLOAT": "doubling the FLOAT desired target before integer rounding + 0.6-contract deadband changes rounding (e.g. 0.7 -> 1 at 1x = 2 at 2x, but "
                                      "1.4 -> 1 at 2x) and the hysteresis: a different, lower-exposure position path; not an integer doubling of C43."}
    proof = {"kernel_copy_1x_vs_stored_max_abs": qa_kernel_copy,
             "X2_B_INT_vs_SIMPLE_max_abs_daily_diff": float(X2.set_index("variant").loc["X2_B_INT", "max_abs_daily_diff"])}
    # ---------------------------------------------------------------- global cap 6 for each variant
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    TR = module_trades(nq, sess)
    pE1, pM1 = grid_positions(T, base1["pos"], sess)
    comp = []
    daily_store = {}

    def cap_qa(tot, cnt_over_minutes_ok):
        return cnt_over_minutes_ok

    for k in ("X2_A_INT", "X2_B_INT", "X2_A_FLOAT", "X2_B_FLOAT"):
        pE2, pM2 = grid_positions(T, R[k]["pos"], sess)
        pM2n = np.nan_to_num(pM2, nan=6.0)
        hard = np.maximum(0, 6 - pM2n).astype(int)
        dR, LR, cR, forced = simulate_hard(nq, TR, -1000.0, hard, hard)
        tR = sum(dR.values()); tR[:s21] = 0; cR[:s21] = 0
        dR4, _, _, _ = simulate_hard(nq, TR, -1000.0, hard, hard, slip=4.0); tR4 = sum(dR4.values()); tR4[:s21] = 0
        totR = np.nan_to_num(pM2) + cR
        # corrected cap QA: every minute with total > 6 must be followed by total <= 6 at the next minute (one-minute causal fill lag)
        ov = (totR > 6) & full[:, None]
        nxt_ok = np.zeros_like(ov)
        nxt_ok[:, :-1] = totR[:, 1:] <= 6
        lag_only = bool((~ov | nxt_ok).all())
        cx = A(R[k]["daily"]); c4 = A(R4[k]["daily"])
        name = {"X2_A_INT": "T61-R1A (X2_A_INT + GLOBAL CAP6)", "X2_B_INT": "T61-R1B (X2_B_INT + GLOBAL CAP6)  [NOMINATED]"}.get(k, f"diag: {k} + GLOBAL CAP6")
        o = metrics(name, cx + tR, sess, np.nan_to_num(pE2), totR, bk, np.sum(R[k]["sides"]) / ndays + 2 * len(LR[LR.s_in >= s21]) / ndays, c4 + tR4)
        o.update({"avg_day_2021": float((cx + tR)[sess >= H.SPAN21].mean()), "cap_minutes_over6": int(ov.sum()), "cap_over6_only_1min_lag": lag_only,
                  "forced_TEST53_reductions": int(forced), "peak_total_MNQ_target": int(np.nanmax(np.minimum(totR, np.maximum(6, pM2n))[full])),
                  "cost_per_day": float((np.sum(R[k]["sides"]) * 0 + (cx - c4)[full].mean() / 4 + (tR - tR4)[full].mean() / 3))})
        exR = matched_excess(nq, LR); exR[:s21] = 0
        lane = H.lane_eval(name, cx + tR, c1, sess, o["overnight_peak_margin_pct"] / 100 * H.NLV, o["peak_margin_pct"] / 100 * H.NLV, float(exR[s21:].mean()),
                           {"plateau_pass": True, "stress4_pos": bool((c4 + tR4 - c1)[s21:].sum() > 0)})
        o.update({"GROWTH_lane_ex_plateau": bool(lane["GROWTH"]), "CORE_lane": bool(lane["CORE"]), "folds_pos": lane["folds_pos"], "matched_excess_TEST53_day": float(exR[s21:].mean())})
        comp.append(o); daily_store[k] = cx + tR
    # reference rows
    z = np.load(f"{OUT}/T61R1_daily.npz")
    M0 = pd.read_csv(f"{OUT}/T61R1_PORTFOLIO_METRICS.csv")
    ref = M0[M0.portfolio.str.startswith(("A:", "B:", "T55"))].copy()
    ref["avg_day_2021"] = [float(z["c43"][sess >= H.SPAN21].mean()), float(z["t61_orig"][sess >= H.SPAN21].mean()), float(z["t55"][sess >= H.SPAN21].mean())]
    CMP = pd.concat([ref, pd.DataFrame(comp)], ignore_index=True)
    CMP.to_csv(f"{OUT}/T61R1_COMPARISON_TABLE.csv", index=False)
    # cap audit transitions for the OLD T61 (entry cap): first minute of each episode + C43 state before/after
    aud = pd.read_csv(f"{OUT}/T61_CAP_AUDIT_minutes.csv")
    aud["date"] = pd.to_datetime(aud.date)
    ep = aud.groupby("date").first().reset_index()
    pM2s = 2 * pM1
    trans = []
    for r_ in ep.itertuples():
        s = sess.get_loc(r_.date); hh, mm = map(int, r_.time.split(":")); j = hh * 60 + mm - C45.M0
        prev = pM2s[s, max(j - 1, 0)]
        trans.append({"date": r_.date.date(), "first_over_minute": r_.time, "C43x2_MNQ_before": prev, "C43x2_MNQ_after": r_.C43x2_MNQ, "TEST53_open_lots": r_.TEST53_open,
                      "total": r_.total, "minutes_over_in_session": int((aud.date == r_.date).sum())})
    TRn = pd.DataFrame(trans); TRn.to_csv(f"{OUT}/T61_CAP_AUDIT_TRANSITIONS.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(X2.round(3).T.to_string()); print(json.dumps(proof, indent=1)); print(CMP.round(3).T.to_string()); print(TRn.head(15).to_string()); print(len(TRn))
    json.dump({"why": why, "proof": proof}, open(f"{OUT}/C43_X2_WHY.json", "w"), indent=1)
    np.savez_compressed(f"{OUT}/T61R1_AB_daily.npz", **daily_store)
    return X2, CMP, TRn, why, proof


if __name__ == "__main__":
    main()
