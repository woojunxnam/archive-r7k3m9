"""Forward-shadow compute engine (runs INSIDE a workspace built by forward_shadow.py; never imported by research code).

The workspace holds a byte-identical copy of frozen/t61_r1c/src (so C45.ROOT = workspace), the frozen artifacts, and the canonical 1m files
for this run.  Harness-level settings only (no rule change): the data end date, the canonical-file hashes recorded by the orchestrator and,
for sessions after 2026-05-27, the TEST53 forward genome fold FINAL_ALL_TO_2026-05-27 (rank 0).

Outputs (only sessions >= REPORT_START are ever written):
  session_log_<PORTFOLIO>.csv.gz : one row per RTH execution minute (bar ts, decision ts, virtual / clamped targets, broker-model position,
                                  order delta, expected / model fill, slippage, commission, margin, equity, drawdown, governor state, contributions)
  daily_report.csv               : one row per session x {C43-CORE, T55, T61-R1C}
"""
import json
import os
import sys

import numpy as np
import pandas as pd

WS = os.environ["SHADOW_WS"]
sys.path.insert(0, os.path.join(WS, "src"))
import t45_common as C45  # noqa: E402
import t44_common as TC  # noqa: E402
import prog_common as P  # noqa: E402

CFG = json.load(open(os.path.join(WS, "run_config.json")))
END = pd.Timestamp(CFG["data_end"]); REPORT_START = pd.Timestamp(CFG["report_start"])
# ---- harness settings (module globals read at call time)
for m in (C45, TC, P):
    m.END = END
for inst in ("ES", "MNQ"):
    C45.DATA[inst] = (C45.DATA[inst][0], CFG["data_sha256"][inst]); TC.DATA[inst] = C45.DATA[inst]
C45.OUTER[-1] = (C45.OUTER[-1][0], C45.OUTER[-1][1], str(min(END, pd.Timestamp("2026-05-27")).date()))
if END > pd.Timestamp("2026-05-27"):
    C45.OUTER.append(("FINAL_ALL_TO_2026-05-27", "2026-05-28", str(END.date())))

import hx_common as H  # noqa: E402
import t47_engine as E  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402
from t43 import instruments, lab, portfolio as PF, sleeves as S, v6lab  # noqa: E402
from t53_run import matched_excess, module_trades, simulate  # noqa: E402
from t61r1_validate import grid_positions, ledger, simulate_hard  # noqa: E402
from t61r1_x2audit import kernel_mult  # noqa: E402

CAP_TOTAL = 6; T55_TOTAL = 3; ENS_GOV = -1000.0


def build_sleeves():
    os.makedirs(f"{TC.T44}/sleeves", exist_ok=True)
    C = S.candidates()
    for cid in TC.ELIG:
        b, res, d = S.run_sleeve(C[cid], end=TC.END)
        assert b.session_date.max() <= TC.END
        pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "rth": b.in_rth.values, "pos": res["pos"].astype(float),
                      "desired": S.desired(res)}).to_parquet(f"{TC.T44}/sleeves/sleeve_{cid}.parquet")


def run_c43(bk, w, gov, mult):
    """frozen kernel_mult (X2 audit copy of the C43 kernel, mult=1 == C43-CORE) returning the full equity path as well."""
    gp = dict(PF.GOV_DEFAULT); gp.update(gov)
    T = bk.T; n = len(T); D = np.zeros((n, 2))
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
    # governor state replay (same rules as the kernel, evaluated on its own equity path): level 0/1/2 and day-cut flag per 3m bar
    dd1, dd2, ds = gp["dd1_frac"] * env, gp["dd2_frac"] * env, gp.get("day_stop", 0.0)
    lev = np.zeros(n, np.int8); cut = np.zeros(n, bool); hwm = lab.INIT; level = 0; ss = lab.INIT; dc = False; prev = lab.INIT
    sc = bk.sess_codes
    for i in range(n):
        e = eq[i]
        if i == 0 or sc[i] != sc[i - 1]:
            ss = prev; dc = False
            if level > 0 and hwm - e < 0.5 * dd1:
                level = 0; hwm = max(hwm, e)
        if level == 0 and e > hwm:
            hwm = e
        if dd2 > 0 and hwm - e >= dd2:
            level = max(level, 2)
        elif dd1 > 0 and hwm - e >= dd1:
            level = max(level, 1)
        if ds > 0 and e - ss <= -ds:
            dc = True
        lev[i] = level; cut[i] = dc; prev = e
    return {"pos": pos, "eq": eq, "daily": s.diff().fillna(s.iloc[0] - lab.INIT), "sides": sides, "level": lev, "daycut": cut, "pv": pv, "rollc": rollc,
            "slip": gp["slip_ticks"] * 0.25, "comm": gp["commission"]}


def leg_daily(T, pos, r, k):
    """per-instrument C43 leg daily $ (independent ledger with the other instrument zeroed)."""
    p = pos.copy(); p[:, 1 - k] = 0
    eq, _ = ledger(T, p, r["pv"], r["slip"], r["comm"], r["rollc"])
    s = pd.Series(eq, index=pd.DatetimeIndex(T.sd.values)).groupby(level=0).last()
    return s.diff().fillna(s.iloc[0])


def grid_map(T, arr, sess):
    """any 3m timeline array -> session x 1m RTH grid (same mapping as grid_positions)."""
    a = np.stack([arr, arr], 1).astype(float)
    return grid_positions(T, a, sess)[0]


def mod_counts(L, n, which=None):
    """per-module open lots per session x minute from a ledger (open at j_in, closed at j_x on s_x)."""
    out = {m: np.zeros((n, C45.NG), np.int16) for m in ("M1", "M2", "M3", "M4")}
    for r in L.itertuples(index=False):
        for s in range(r.s_in, r.s_x + 1):
            j0 = r.j_in if s == r.s_in else 0
            j1 = r.j_x if s == r.s_x else C45.NG
            out[r.mod][s, j0:j1] += 1
    return out


def main():
    TC.setup()
    build_sleeves()
    fin = json.load(open(os.path.join(C45.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")))
    Pp = fin["portfolios"]["SECONDARY_2"]; w = {c: m["contract_weight"] for c, m in Pp["members"].items()}
    bk3 = PF.Book(TC.END, TC.ELIG); T = bk3.T
    gov1 = PD.gov_for(Pp["risk_envelope"]); gov2 = dict(gov1); gov2["env_dd"] *= 2; gov2["day_stop"] *= 2
    r1 = run_c43(bk3, w, gov1, 1)              # C43-CORE
    r2 = run_c43(bk3, w, gov2, 2)              # X2_B_INT (T61 C43 leg)
    es, nq = E.setup(); bk = H.Book({"ES": es, "MNQ": nq})
    sess = nq.pn.sess; n = nq.n
    rep = np.asarray(sess >= REPORT_START)
    assert rep.any(), "no session at/after REPORT_START in the data"
    A = lambda x: x.reindex(sess).fillna(0.0).values
    pE1, pM1 = grid_positions(T, r1["pos"], sess); pE2, pM2 = grid_positions(T, r2["pos"], sess)
    eq1g, eq2g = grid_map(T, r1["eq"], sess), grid_map(T, r2["eq"], sess)
    lv1, lv2 = grid_map(T, r1["level"], sess), grid_map(T, r2["level"], sess)
    dc1, dc2 = grid_map(T, r1["daycut"], sess), grid_map(T, r2["daycut"], sess)
    TR = module_trades(nq, sess)
    # ---- TEST53 legs
    hard61 = np.maximum(0, CAP_TOTAL - np.nan_to_num(pM2, nan=float(CAP_TOTAL))).astype(int)
    d61, L61, cnt61, nev61 = simulate_hard(nq, TR, ENS_GOV, hard61, hard61, atomic=True)
    free = np.full((n, C45.NG), 2, int)
    dvir, Lvir, cntvir, _ = simulate_hard(nq, TR, ENS_GOV, free, free, atomic=True)          # TEST53 virtual (unclamped, standalone)
    cap55 = np.maximum(0, T55_TOTAL - np.nan_to_num(pM1, nan=float(T55_TOTAL))).astype(int)
    d55, L55, cnt55 = simulate(nq, TR, 2, ENS_GOV, cap_arr=cap55)
    ex61, ex55 = matched_excess(nq, L61), matched_excess(nq, L55)
    c1, c2 = A(r1["daily"]), A(r2["daily"])
    legs = {"C43x1_MES": A(leg_daily(T, r1["pos"], r1, 0)), "C43x1_MNQ": A(leg_daily(T, r1["pos"], r1, 1)),
            "C43x2_MES": A(leg_daily(T, r2["pos"], r2, 0)), "C43x2_MNQ": A(leg_daily(T, r2["pos"], r2, 1))}
    books = {"C43-CORE": dict(daily=c1, qE=pE1, qN=pM1, t53=None, L=None, cnt=None, eqg=eq1g, lev=lv1, dc=dc1, c43=r1, legs=("C43x1_MES", "C43x1_MNQ")),
             "T55": dict(daily=c1 + sum(d55.values()), qE=pE1, qN=np.nan_to_num(pM1) + cnt55, t53=d55, L=L55, cnt=cnt55, eqg=eq1g, lev=lv1, dc=dc1, c43=r1,
                         legs=("C43x1_MES", "C43x1_MNQ"), ex=ex55, c43N=pM1),
             "T61-R1C": dict(daily=c2 + sum(d61.values()), qE=pE2, qN=np.nan_to_num(pM2) + cnt61, t53=d61, L=L61, cnt=cnt61, eqg=eq2g, lev=lv2, dc=dc2, c43=r2,
                             legs=("C43x2_MES", "C43x2_MNQ"), ex=ex61, c43N=pM2)}
    out = CFG["out_dir"]; os.makedirs(out, exist_ok=True)
    tickN, tickE = C45.TICKV[C45.INSTS.index("MNQ")] / nq.pv, C45.TICKV[C45.INSTS.index("ES")] / es.pv
    idx = np.where(rep)[0]
    rows = []
    for name, b in books.items():
        qE = np.nan_to_num(b["qE"]); qN = np.nan_to_num(b["qN"])
        t53 = np.zeros((n, C45.NG)) if b["cnt"] is None else b["cnt"].astype(float)
        c43N = np.nan_to_num(b.get("c43N", b["qN"]))
        mc = mod_counts(b["L"], n) if b["L"] is not None else None
        # session-level account path: C43 kernel equity + TEST53 realised/MTM
        logs = []
        for s in idx:
            dN = np.diff(np.r_[qN[s - 1, E.J1615] if s > 0 else 0, qN[s]]); dE = np.diff(np.r_[qE[s - 1, E.J1615] if s > 0 else 0, qE[s]])
            m_in = qE[s] * bk.m_in["ES"][s] + qN[s] * bk.m_in["MNQ"][s]
            df = pd.DataFrame({
                "session": sess[s].date(), "bar_ts_end": [f"{(C45.M0 + j) // 60:02d}:{(C45.M0 + j) % 60:02d}" for j in range(C45.NG)],
                "decision_ts": [f"{(C45.M0 + j - 1) // 60:02d}:{(C45.M0 + j - 1) % 60:02d}" for j in range(C45.NG)],
                "virtual_C43_MES": b["qE"][s], "virtual_C43_MNQ": b.get("c43N", b["qN"])[s],
                "virtual_TEST53": cntvir[s] if name != "C43-CORE" else 0, "clamped_TEST53": t53[s],
                **({f"TEST53_{m}": mc[m][s] for m in mc} if mc else {}),
                "final_target_MES": qE[s], "final_target_MNQ": qN[s], "broker_model_MES": qE[s], "broker_model_MNQ": qN[s],
                "order_delta_MES": dE, "order_delta_MNQ": dN,
                "expected_fill_MNQ": nq.FPb[s], "model_fill_MNQ": nq.FPb[s] + np.sign(dN) * tickN, "expected_fill_MES": es.FPb[s],
                "model_fill_MES": es.FPb[s] + np.sign(dE) * tickE, "slippage_ticks_model": (np.abs(dN) + np.abs(dE)) > 0,
                "commission": (np.abs(dN) + np.abs(dE)) * C45.COMM, "intraday_margin": m_in, "margin_pct_NLV": m_in / H.NLV * 100,
                "C43_kernel_equity": b["eqg"][s], "C43_gov_level": b["lev"][s], "C43_day_cut": b["dc"][s],
                "TEST53_governor_blocked": 0, "broker_fill_MNQ": np.nan, "broker_fill_MES": np.nan})
            if b["L"] is not None:
                g = b["L"][(b["L"].s_x == s) & (b["L"].why == "governor")]
                if len(g):
                    df.loc[int(g.j_x.min()):, "TEST53_governor_blocked"] = 1
            logs.append(df)
        L = pd.concat(logs, ignore_index=True)
        L.to_csv(os.path.join(out, f"session_log_{name}.csv.gz"), index=False, compression="gzip")
    cum = {k: 0.0 for k in books}; peak = {k: 0.0 for k in books}
    for s in idx:
        for name, b in books.items():
            d = float(b["daily"][s]); cum[name] += d; peak[name] = max(peak[name], cum[name])
            qE = np.nan_to_num(b["qE"][s]); qN = np.nan_to_num(b["qN"][s])
            lock = E.J1615 - 1
            t53d = 0.0 if b["t53"] is None else float(sum(v[s] for v in b["t53"].values()))
            Ls = b["L"][b["L"].s_x == s] if b["L"] is not None else None
            q0E = np.nan_to_num(b["qE"][s - 1, E.J1615]) if s > 0 else 0.0; q0N = np.nan_to_num(b["qN"][s - 1, E.J1615]) if s > 0 else 0.0
            sE = float(np.abs(np.diff(np.r_[q0E, qE])).sum()); sN = float(np.abs(np.diff(np.r_[q0N, qN])).sum()); sides = sE + sN
            # worst intraday MTM: C43 kernel equity path relative to its session start (+ TEST53 realised at close; report proxy)
            e = b["eqg"][s]; e0 = b["eqg"][s - 1][~np.isnan(b["eqg"][s - 1])][-1] if s > 0 and np.isfinite(b["eqg"][s - 1]).any() else np.nan
            rows.append({"date": sess[s].date(), "portfolio": name, "daily_pnl": d, "cum_pnl": cum[name], "drawdown": cum[name] - peak[name],
                         "C43_leg_pnl": float(c1[s] if b["c43"] is r1 else c2[s]), "C43_MES_leg": float(legs[b["legs"][0]][s]), "C43_MNQ_leg": float(legs[b["legs"][1]][s]),
                         "TEST53_pnl": t53d, **({f"TEST53_{m}": float(v[s]) for m, v in b["t53"].items()} if b["t53"] else {}),
                         "incremental_vs_C43": d - float(c1[s]), "TEST53_matched_excess": float(b["ex"][s]) if "ex" in b else 0.0,
                         "peak_MES": float(qE.max()), "peak_MNQ": float(qN.max()), "overnight_MES": float(qE[lock]), "overnight_MNQ": float(qN[lock]),
                         "peak_intraday_margin_pct": float((qE * bk.m_in["ES"][s] + qN * bk.m_in["MNQ"][s]).max() / H.NLV * 100),
                         "overnight_margin_pct": float((qE[lock] * bk.m_on["ES"][s] + qN[lock] * bk.m_on["MNQ"][s]) / H.NLV * 100),
                         "worst_intraday_C43_MTM": float(np.nanmin(e) - e0) if np.isfinite(e0) else np.nan,
                         "contract_sides_model": sides, "costs_model": sE * C45.cost_side(es.k) + sN * C45.cost_side(nq.k), "TEST53_trades_closed": int(len(Ls)) if Ls is not None else 0,
                         "implementation_violations": int((qN > CAP_TOTAL).sum()) if name == "T61-R1C" else 0})
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(out, "daily_report.csv"), index=False)
    json.dump({"sessions_reported": int(rep.sum()), "first": str(sess[idx[0]].date()), "last": str(sess[idx[-1]].date()), "netting_events_T61": int(nev61),
               "data_end": str(END.date()), "report_start": str(REPORT_START.date())}, open(os.path.join(out, "run_summary.json"), "w"), indent=1)
    print("shadow engine done", len(R))


if __name__ == "__main__":
    main()
