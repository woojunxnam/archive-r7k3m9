"""TEST43-P FINAL HOLDOUT — ONE SHOT.  Frozen objects only; integrity checks run BEFORE any holdout economics.
Usage: python p09_holdout.py"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import instruments, lab, portfolio as PF, sleeves as S, v6lab  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402
import p07_acceptance as ACC  # noqa: E402

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(SRC, "..")
REPO = os.path.abspath(os.path.join(ROOT, ".."))
FZ = os.path.join(ROOT, "out", "p", "freeze")
HO = os.path.join(ROOT, "out", "p", "holdout")
H0, H1 = pd.Timestamp("2025-10-01"), pd.Timestamp("2026-05-27")
EXPECT = {"TEST43P_PRE_VAL_FREEZE.json": "18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817",
          "TEST43P_FINAL_PORTFOLIOS.json": "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7",
          "TEST43P_HOLDOUT_ACCEPTANCE_RULES.json": "62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0"}
DATA = {"ES": ("data/canonical_1m_ES.parquet", "2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116"),
        "MNQ": ("data/canonical_1m_MNQ.parquet", "66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2")}
SELECTED = {"PRIMARY": "P2B_STATIC_4SLEEVE|MODERATE", "SECONDARY_1": "P2_STATIC_DIVERSIFIED|MODERATE",
            "SECONDARY_2": "P1_CLUSTER_EQUAL_RISK|CONSERVATIVE"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def blob(path, rev):
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"], capture_output=True, check=True).stdout


def integrity():
    ok = {}
    for fn, e in EXPECT.items():
        p = os.path.join(FZ, fn)
        ok[f"freeze:{fn}"] = sha(p) == e and open(p, "rb").read() == blob(f"test43_lab/out/p/freeze/{fn}", "33359fd")
    fin = json.load(open(os.path.join(FZ, "TEST43P_FINAL_PORTFOLIOS.json")))
    pre = json.load(open(os.path.join(FZ, "TEST43P_PRE_VAL_FREEZE.json")))
    rules = json.load(open(os.path.join(FZ, "TEST43P_HOLDOUT_ACCEPTANCE_RULES.json")))
    ok["selection"] = fin["selection"] == SELECTED and rules["evaluated_portfolios"] == SELECTED
    ok["window"] = rules["holdout_window"] == ["2025-10-01", "2026-05-27"]
    for f, h in fin["code"].items():
        ok[f"code:{f}"] = sha(os.path.join(SRC, f)) == h
    for f in ("t43/v6lab.py", "t43/features.py", "t43/lab.py", "t43/instruments.py", "t43/bars.py", "t43/v533.py",
              "t43/metrics.py", "t43/bench.py", "p07_acceptance.py", "p08_preflight.py"):
        ok[f"code:{f}"] = open(os.path.join(SRC, f), "rb").read() == blob(f"test43_lab/src/{f}", "33359fd")
    C = S.candidates()
    for cid, m in pre["candidates"].items():
        ok[f"cand:{cid}"] = S.cand_hash(C[cid]) == m["sha256"] and C[cid]["params"] == m["params"]
    for inst, (rel, e) in DATA.items():
        ok[f"data:{inst}"] = sha(os.path.join(ROOT, rel)) == e
    return ok, fin, pre, rules


def main():
    os.makedirs(HO, exist_ok=True)
    ok, fin, pre, rules = integrity()
    if not all(ok.values()):
        json.dump({"ABORTED": True, "failed": [k for k, v in ok.items() if not v]}, open(os.path.join(HO, "ABORT.json"), "w"), indent=1)
        print("INTEGRITY FAILED - STOP", [k for k, v in ok.items() if not v]); sys.exit(1)
    print("integrity checks passed:", len(ok))
    END = H1
    # rebuild 3m bars from the hash-verified canonical 1m files (same pipeline as V1) and point every loader at them
    from t43 import bars as B
    for inst, (rel, _) in DATA.items():
        m1 = B.normalise_1m(pd.read_parquet(os.path.join(ROOT, rel)))
        bb = B.add_clock(B.aggregate_3m(m1))
        if "cum_adjustment" in bb.columns:
            bb["raw_o"] = bb["o"] - bb["cum_adjustment"].astype(float)
        bb = bb[bb.session_date <= H1].reset_index(drop=True)
        pth = os.path.join(HO, f"{inst}_3m_bars_from_canonical.parquet"); bb.to_parquet(pth)
        v6lab.BARS[inst] = pth; S.PATHS3[inst] = pth
    v6lab._S.clear(); v6lab._C1.clear()
    C = S.candidates()
    need = sorted({c for p in fin["portfolios"].values() for c in p["members"]})
    PF.PDIR = HO
    sleeve_daily = {}
    for cid in need:
        b, res, d = S.run_sleeve(C[cid], end=END)
        pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "rth": b.in_rth.values, "pos": res["pos"].astype(float),
                      "desired": S.desired(res)}).to_parquet(os.path.join(HO, f"sleeve_{cid}.parquet"))
        sleeve_daily[cid] = d.pnl
    bk = PF.Book(END, need)
    last = pd.Timestamp(bk.T.sd.max())
    # ---- QA before economics: DEV/VAL prefix of the full run must reproduce the frozen daily P&L
    qa = {}
    runs = {}
    for role, key in SELECTED.items():
        name, env = key.split("|")
        P = fin["portfolios"][role]
        w = {c: m["contract_weight"] for c, m in P["members"].items()}
        runs[role] = {}
        for tag, ex in (("BASE", {}), ("SLIP4", {"slip_ticks": 4}), ("TIMING_BRITTLENESS_STRESS", {"delay": 1})):
            r = bk.run(w, gov=PD.gov_for(env, ex))
            runs[role][tag] = (r, bk.daily(r))
        dv = runs[role]["BASE"][1]; dv = dv[dv.index <= lab.VAL_END]
        old = pd.read_csv(os.path.join(ROOT, "out", "p", f"daily_{name}_{env}_DV.csv"), index_col=0, parse_dates=True)
        qa[role] = float((dv.pnl - old.pnl.reindex(dv.index)).abs().max())
    if not all(v < 1e-6 for v in qa.values()) or last != H1:
        print("PREFIX QA FAILED - STOP", qa, last); sys.exit(1)
    print("prefix QA passed (DEV+VAL reproduced):", qa, "data last session", last.date())
    # ---- holdout economics
    T = bk.T; sdT = pd.DatetimeIndex(T.sd.values); hm = (sdT >= H0) & (sdT <= H1)
    profs = [instruments.PROFILES[v6lab.PROF[i]] for i in PF.INSTS]
    c1 = {i: v6lab.const1_daily(i, END).pnl for i in PF.INSTS}
    out = {"status": {}, "portfolios": {}}
    daily_all, monthly_all, attr_all, stress_all = [], [], [], []
    for role, key in SELECTED.items():
        name, env = key.split("|")
        P = fin["portfolios"][role]
        r, d = runs[role]["BASE"]
        h = d[(d.index >= H0) & (d.index <= H1)].copy()
        pos = r["pos"]
        # friction and gross inside the window
        dpos = np.abs(np.diff(np.r_[[pos[0]], pos], axis=0))
        fr_k = [float((dpos[hm, k] * (profs[k]["commission_side"] + profs[k]["tick_value"])).sum()) for k in range(2)]
        sides_k = [float(dpos[hm, k].sum()) for k in range(2)]
        newS = np.r_[True, T.sd.values[1:] != T.sd.values[:-1]]
        roll_k = [float((pos[:, k] * 2 * (profs[k]["commission_side"] + profs[k]["tick_value"]))[hm & newS & T[f"{PF.INSTS[k]}_roll"].values].sum()) for k in range(2)]
        net = float(h.pnl.sum()); friction = sum(fr_k); gross = net + friction + sum(roll_k)
        mb = float((h.pES.mean() * c1["ES"].reindex(h.index).fillna(0) + h.pMNQ.mean() * c1["MNQ"].reindex(h.index).fillna(0)).mean())
        smb = ACC.session_matched_beta(T, pos, d, H0, H1)
        stress = {}
        for tag in ("SLIP4", "TIMING_BRITTLENESS_STRESS"):
            ds = runs[role][tag][1]; ds = ds[(ds.index >= H0) & (ds.index <= H1)]
            eq = np.r_[0.0, ds.pnl.cumsum().values]
            stress[tag] = {"net_pnl": float(ds.pnl.sum()), "avg_day": float(ds.pnl.mean()), "max_dd": float((np.maximum.accumulate(eq) - eq).max()),
                           "worst_day": float(ds.pnl.min())}
            stress_all.append({"role": role, "portfolio": key, "test": tag, **stress[tag]})
        ev = ACC.evaluate(h, env, mb_avg=mb, stress=stress)
        n = len(h); top = h.pnl.sort_values(ascending=False)
        rth = T.rth.values
        rep = {"portfolio": key, "members": list(P["members"]), "sessions": n, "gross_pnl": gross, "net_pnl": net,
               "friction_commission_slippage": friction, "roll_cost": sum(roll_k), "contract_sides_MES": sides_k[0], "contract_sides_MNQ": sides_k[1],
               "avg_day": net / n, "median_day": float(h.pnl.median()), "max_dd": ev["max_dd"], "worst_day": ev["worst_day"],
               "best_day": ev["best_day"], "best_day_share": ev["best_day_share"], "return_dd": (net / n) / ev["max_dd"] if ev["max_dd"] > 0 else None,
               "avg_ex_top1": float((net - top.iloc[:1].sum()) / n), "avg_ex_top3": float((net - top.iloc[:3].sum()) / n),
               "avg_ex_top5": float((net - top.iloc[:5].sum()) / n), "positive_day_share": float((h.pnl > 0).mean()),
               "matched_beta_avg_day": mb, "matched_beta_excess_per_day": net / n - mb,
               "session_matched_beta": smb, "session_matched_beta_excess_per_day": smb["excess_vs_session_matched_per_day"],
               "avg_contracts_MES": float(pos[hm, 0].mean()), "avg_contracts_MNQ": float(pos[hm, 1].mean()),
               "avg_rth_MES": float(pos[hm & rth, 0].mean()), "avg_on_MES": float(pos[hm & ~rth, 0].mean()),
               "avg_rth_MNQ": float(pos[hm & rth, 1].mean()), "avg_on_MNQ": float(pos[hm & ~rth, 1].mean()),
               "max_contracts_MES": int(pos[hm, 0].max()), "max_contracts_MNQ": int(pos[hm, 1].max()),
               "peak_margin_util": float(h.mu_max.max()), "peak_overnight_margin_util": float(h.mu_on_max.max()),
               "stress": stress, "acceptance": ev}
        out["portfolios"][role] = rep
        hd = h[["pnl", "eq_end", "pES", "pMNQ", "mu_max", "mu_on_max", "atr_max"]].copy(); hd.insert(0, "role", role); hd.insert(1, "portfolio", key)
        daily_all.append(hd)
        # monthly + rolling 3m
        eq = np.r_[0.0, h.pnl.cumsum().values]; ddser = pd.Series((np.maximum.accumulate(eq) - eq)[1:], index=h.index)
        for mth, g in h.groupby(h.index.to_period("M")):
            e2 = np.r_[0.0, g.pnl.cumsum().values]
            monthly_all.append({"role": role, "portfolio": key, "month": str(mth), "sessions": len(g), "net_pnl": float(g.pnl.sum()),
                                "avg_day": float(g.pnl.mean()), "intra_month_max_dd": float((np.maximum.accumulate(e2) - e2).max()),
                                "window_dd_at_month_end": float(ddser.loc[g.index[-1]]), "positive_day_share": float((g.pnl > 0).mean())})
        roll = h.pnl.rolling(63).sum().dropna()
        rep["rolling_3m"] = {"n_windows": len(roll), "min": float(roll.min()) if len(roll) else None, "max": float(roll.max()) if len(roll) else None,
                             "positive_share": float((roll > 0).mean()) if len(roll) else None}
        # sleeve attribution (virtual weighted desire; realised position allocated pro rata to desire within instrument)
        wts = {c: m["contract_weight"] for c, m in P["members"].items()}
        D = r["D"]
        for cid, wt in wts.items():
            k = PF.INSTS.index(bk.inst[cid]); inst = PF.INSTS[k]; pv = profs[k]["point_value"]
            wd = wt * bk.des[cid]
            held = np.r_[0.0, wd[:-1]]                                        # desire decided at i-1 is held during bar i
            dc = np.r_[0.0, np.diff(T[f"{inst}_c"].values)]
            share = np.where(D[:, k] > 1e-12, wd / np.where(D[:, k] > 1e-12, D[:, k], 1), 0.0)
            realised = pos[:, k] * np.r_[0.0, share[:-1]]
            gross_virtual = float((held * dc * pv)[hm].sum())
            gross_realised = float((realised * dc * pv)[hm].sum())
            dsh = np.abs(np.diff(np.r_[wd[0], wd]))
            tot = np.zeros(len(T))
            for c2, w2 in wts.items():
                if bk.inst[c2] == inst:
                    tot += np.abs(np.diff(np.r_[w2 * bk.des[c2][0], w2 * bk.des[c2]]))
            fsh = float((dsh[hm]).sum() / tot[hm].sum()) if tot[hm].sum() > 0 else 0.0
            sd_ = sleeve_daily[cid]; sd_ = sd_[(sd_.index >= H0) & (sd_.index <= H1)]
            attr_all.append({"role": role, "portfolio": key, "sleeve": cid, "inst": inst, "contract_weight": wt,
                             "risk_budget": P["members"][cid]["risk_budget"],
                             "avg_weighted_desired_contracts": float(wd[hm].mean()), "avg_realised_contracts_allocated": float(realised[hm].mean()),
                             "gross_contribution_virtual": gross_virtual, "gross_contribution_realised": gross_realised,
                             "friction_allocated": fsh * fr_k[k], "net_contribution_realised_approx": gross_realised - fsh * fr_k[k] - fsh * roll_k[k],
                             "standalone_virtual_ledger_holdout_pnl": float(sd_.sum()),
                             "standalone_virtual_ledger_holdout_pnl_x_weight": float(sd_.sum() * wt)})
    for role, rep in out["portfolios"].items():
        out["status"][f"{role}_HOLDOUT_PASS"] = "YES" if rep["acceptance"]["PASS"] else "NO"
    pr = out["portfolios"]["PRIMARY"]
    if pr["acceptance"]["PASS"]:
        final = "PRIMARY = HOLDOUT_PASS / CANDIDATE_FOR_PAPER_LIVE_READINESS_REVIEW"
    elif any(out["portfolios"][r]["acceptance"]["PASS"] for r in ("SECONDARY_1", "SECONDARY_2")):
        final = "PRIMARY = HOLDOUT_FAIL; SECONDARY PASS REPORTED ONLY (no automatic promotion)"
    else:
        final = "TEST43-P = HOLDOUT_REJECTED"
    out["status"].update({"HOLDOUT_OPENED": "YES", "HOLDOUT_WINDOW": "2025-10-01 through 2026-05-27",
                          "PRIMARY_NET_PNL": pr["net_pnl"], "PRIMARY_AVG_DAY": pr["avg_day"], "PRIMARY_MAX_DD": pr["max_dd"],
                          "PRIMARY_WORST_DAY": pr["worst_day"], "PRIMARY_REMOVE_TOP3_AVG": pr["avg_ex_top3"],
                          "PRIMARY_BEST_DAY_CONCENTRATION": pr["best_day_share"], "PRIMARY_MATCHED_BETA_EXCESS": pr["matched_beta_excess_per_day"],
                          "PRIMARY_SESSION_MATCHED_BETA_EXCESS": pr["session_matched_beta_excess_per_day"],
                          "FINAL_TEST43P_STATUS": final, "LIVE_AUTHORIZATION": "NO"})
    out["integrity"] = {"checks_passed": len(ok), "prefix_qa_max_abs_diff": qa, "data_last_session": str(last.date())}
    json.dump(out, open(os.path.join(HO, "TEST43P_HOLDOUT_FINAL.json"), "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    pd.concat(daily_all).to_csv(os.path.join(HO, "TEST43P_HOLDOUT_DAILY.csv"))
    pd.DataFrame(monthly_all).to_csv(os.path.join(HO, "TEST43P_HOLDOUT_MONTHLY.csv"), index=False)
    pd.DataFrame(attr_all).to_csv(os.path.join(HO, "TEST43P_HOLDOUT_SLEEVE_ATTRIBUTION.csv"), index=False)
    pd.DataFrame(stress_all).to_csv(os.path.join(HO, "TEST43P_HOLDOUT_STRESS.csv"), index=False)
    print(json.dumps(out["status"], indent=1, default=str))


if __name__ == "__main__":
    main()
