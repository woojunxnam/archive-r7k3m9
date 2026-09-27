"""TEST43-P FINAL PRE-HOLDOUT INTEGRITY CHECK (audit only; no research, no change to any frozen object).

HOLDOUT outcomes are never computed: every simulation path truncates at VAL_END (2025-09-30) before features,
sleeves or the portfolio are built.  Usage: python p08_preflight.py
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, instruments, lab, portfolio as PF, sleeves as S, v6lab  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402
import p07_acceptance as ACC  # noqa: E402

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(SRC, "..")
REPO = os.path.abspath(os.path.join(ROOT, ".."))
FZ = os.path.join(ROOT, "out", "p", "freeze")
EXPECT = {"TEST43P_PRE_VAL_FREEZE.json": "18d3507d7978f98b8000b51a0ab4a375f80f7226d27b6a7b4403781b77a7d817",
          "TEST43P_FINAL_PORTFOLIOS.json": "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7",
          "TEST43P_HOLDOUT_ACCEPTANCE_RULES.json": "62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0"}
DATA = {"ES": ("data/canonical_1m_ES.parquet", "2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116"),
        "MNQ": ("data/canonical_1m_MNQ.parquet", "66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2")}
STORED_3M = {"ES": os.path.join(ROOT, "out", "p123", "ES_3m_bars.parquet"), "MNQ": os.path.join(ROOT, "out", "mnq", "MNQ_3m_bars.parquet")}
SELECTED = {"PRIMARY": "P2B_STATIC_4SLEEVE|MODERATE", "SECONDARY_1": "P2_STATIC_DIVERSIFIED|MODERATE",
            "SECONDARY_2": "P1_CLUSTER_EQUAL_RISK|CONSERVATIVE"}


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def git_blob(path_in_repo, rev):
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path_in_repo}"], capture_output=True, check=True).stdout


def main():
    R = {"checks": {}}
    chk = R["checks"]
    # ---------------------------------------------------------------- 1 frozen files: sha + byte-for-byte vs commits
    f1 = {}
    for fn, exp in EXPECT.items():
        p = os.path.join(FZ, fn)
        loc = open(p, "rb").read()
        side = open(p.replace(".json", ".sha256")).read().split()[0]
        head = git_blob(f"test43_lab/out/p/freeze/{fn}", "HEAD")
        created = "21f0b33" if "PRE_VAL" in fn else "1b54501"
        orig = git_blob(f"test43_lab/out/p/freeze/{fn}", created)
        f1[fn] = {"sha256": hashlib.sha256(loc).hexdigest(), "expected": exp, "sidecar": side,
                  "bytes": len(loc), "byte_equal_HEAD": loc == head, "byte_equal_creation_commit_" + created: loc == orig}
        f1[fn]["pass"] = f1[fn]["sha256"] == exp == side and loc == head and loc == orig
    chk["1_freeze_files"] = f1
    FREEZE_OK = all(v["pass"] for v in f1.values())
    pre = json.load(open(os.path.join(FZ, "TEST43P_PRE_VAL_FREEZE.json")))
    fin = json.load(open(os.path.join(FZ, "TEST43P_FINAL_PORTFOLIOS.json")))
    rules = json.load(open(os.path.join(FZ, "TEST43P_HOLDOUT_ACCEPTANCE_RULES.json")))
    FREEZE_OK &= fin["pre_val_freeze_sha256"] == EXPECT["TEST43P_PRE_VAL_FREEZE.json"] and \
        fin["holdout_rules_sha256"] == EXPECT["TEST43P_HOLDOUT_ACCEPTANCE_RULES.json"]
    FREEZE_OK &= fin["selection"] == SELECTED and rules["evaluated_portfolios"] == SELECTED
    # ---------------------------------------------------------------- 2 candidate parameter hashes
    C = S.candidates()
    c2 = {}
    for cid, meta in pre["candidates"].items():
        now = S.cand_hash(C[cid])
        c2[cid] = {"frozen": meta["sha256"], "recomputed_from_shortlist": now, "params_equal": C[cid]["params"] == meta["params"],
                   "pass": now == meta["sha256"] and C[cid]["params"] == meta["params"]}
    for role, p in fin["portfolios"].items():
        for cid, m in p["members"].items():
            c2[cid]["final_manifest_hash_equal"] = m["candidate_sha256"] == c2[cid]["frozen"] and m["params"] == C[cid]["params"]
            c2[cid]["pass"] &= c2[cid]["final_manifest_hash_equal"]
    chk["2_candidate_hashes"] = c2
    CAND_OK = all(v["pass"] for v in c2.values())
    # ---------------------------------------------------------------- 3 code hashes
    c3 = {}
    for f, h in fin["code"].items():
        now = sha_file(os.path.join(SRC, f))
        c3[f] = {"frozen": h, "now": now, "pass": now == h}
    for f, h in pre["code"].items():
        c3.setdefault(f, {})["pre_val_frozen"] = h
    # supporting modules not listed in the manifest: must be unchanged since the pre-VAL freeze commit
    for f in ("t43/v6lab.py", "t43/features.py", "t43/lab.py", "t43/instruments.py", "t43/bars.py", "t43/v533.py", "t43/metrics.py", "t43/bench.py"):
        same = open(os.path.join(SRC, f), "rb").read() == git_blob(f"test43_lab/src/{f}", "21f0b33")
        c3[f] = {"now": sha_file(os.path.join(SRC, f)), "unchanged_since_pre_val_freeze_commit": same, "pass": same}
    chk["3_code_hashes"] = c3
    CODE_OK = all(v.get("pass", True) for v in c3.values()) and CAND_OK
    # ---------------------------------------------------------------- 4 canonical data (hash BEFORE parsing)
    c4 = {}
    for inst, (rel, exp) in DATA.items():
        h = sha_file(os.path.join(ROOT, rel))
        c4[inst] = {"file": rel, "sha256": h, "expected": exp, "pass": h == exp}
    chk["4_data_hashes"] = c4
    DATA_OK = all(v["pass"] for v in c4.values())
    # ---------------------------------------------------------------- 6 holdout window
    c6 = {"lab_HOLDOUT_split_start": str(lab.SPLITS["HOLDOUT"][0].date()), "VAL_END": str(lab.VAL_END.date()),
          "rules_window": rules["holdout_window"], "pre_freeze_data": pre["data"]}
    c6["pass"] = c6["lab_HOLDOUT_split_start"] == "2025-10-01" and rules["holdout_window"] == ["2025-10-01", "2026-05-27"] \
        and pre["data"]["HOLDOUT"] == "closed" and pre["data"]["VAL"][1] == "2025-09-30"
    chk["6_holdout_window"] = c6
    # ---------------------------------------------------------------- 7 rebuild from canonical files and reproduce DEV / VAL
    tmp = tempfile.mkdtemp(prefix="t43p_preflight_")
    c7 = {"bars": {}}
    rebuilt = {}
    for inst, (rel, _) in DATA.items():
        m1 = B.normalise_1m(pd.read_parquet(os.path.join(ROOT, rel)))
        b = B.add_clock(B.aggregate_3m(m1))
        if "cum_adjustment" in b.columns:
            b["raw_o"] = b["o"] - b["cum_adjustment"].astype(float)
        b = b[b.session_date <= lab.VAL_END].reset_index(drop=True)          # HOLDOUT rows dropped here, before any use
        st = pd.read_parquet(STORED_3M[inst]); st = st[st.session_date <= lab.VAL_END].reset_index(drop=True)
        cols = [c for c in st.columns if c in b.columns]
        eq = len(b) == len(st) and all(b[c].equals(st[c]) or np.allclose(b[c].astype(float), st[c].astype(float), equal_nan=True)
                                       if b[c].dtype.kind in "fiub" else b[c].astype(str).equals(st[c].astype(str)) for c in cols)
        c7["bars"][inst] = {"rows_DV": len(b), "stored_rows_DV": len(st), "columns_compared": len(cols), "identical": bool(eq),
                            "max_session_date_used": str(b.session_date.max().date())}
        path = os.path.join(tmp, f"{inst}_3m_bars_rebuilt_DV.parquet")
        b.to_parquet(path); rebuilt[inst] = path
    # point every loader at the rebuilt (already truncated) bars and a scratch sleeve directory
    v6lab.BARS["ES"] = rebuilt["ES"]; v6lab.BARS["MNQ"] = rebuilt["MNQ"]; v6lab._S.clear(); v6lab._C1.clear()
    S.PATHS3["ES"] = rebuilt["ES"]; S.PATHS3["MNQ"] = rebuilt["MNQ"]
    PF.PDIR = tmp; PD.OUT = tmp
    daily = {}
    for cid in S.ELIGIBLE + S.SHADOW:
        b, res, d = S.run_sleeve(C[cid])
        pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "rth": b.in_rth.values, "pos": res["pos"].astype(float),
                      "desired": S.desired(res)}).to_parquet(os.path.join(tmp, f"sleeve_{cid}.parquet"))
        daily[cid] = d.pnl
    Dnew = pd.DataFrame(daily).fillna(0.0)
    Dold = pd.read_csv(os.path.join(ROOT, "out", "p", "p03_daily_pnl_all_candidates_DV.csv"), index_col=0, parse_dates=True)
    c7["sleeve_daily_max_abs_diff"] = float((Dnew[Dold.columns] - Dold).abs().max().max())
    Dnew.to_csv(os.path.join(tmp, "p03_daily_pnl_all_candidates_DV.csv"))
    sig = pd.Series(pre["risk_normalisation"]["sigma_daily_dev"])
    bk = PF.Book(lab.VAL_END, S.ELIGIBLE)
    c7["timeline_max_session"] = str(pd.Timestamp(bk.T.sd.max()).date())
    port = {}
    base = pre["portfolios"]["P2_STATIC_DIVERSIFIED"]
    tilts = {a: PD.regime_tilt(bk, list(base), base, a, PD.load_daily())[0] for a in pre["regime_tilt"]["alphas"]}
    defs = [(n, b_, None) for n, b_ in pre["portfolios"].items()] + [(f"P3_REGIME_ADAPTIVE_{int(a * 100)}", base, a) for a in pre["regime_tilt"]["alphas"]]
    diffs = {}
    runs = {}
    for name, bud, a in defs:
        for env in PD.ENV:
            L = pre["risk_scale_L"][f"{name}|{env}"]
            o, d, r = PD.run_port(bk, bud, sig, L, env, tilt=tilts.get(a), end=lab.VAL_END, pers=("VAL", "DEV"))
            old = pd.read_csv(os.path.join(ROOT, "out", "p", f"daily_{name}_{env}_DV.csv"), index_col=0, parse_dates=True)
            dd_ = (d.pnl - old.pnl.reindex(d.index)).abs()
            diffs[f"{name}|{env}"] = {"DEV_max_abs_diff": float(dd_[dd_.index <= lab.DEV_END].max()),
                                      "VAL_max_abs_diff": float(dd_[dd_.index > lab.DEV_END].max()),
                                      "DEV_total": float(d.pnl[d.index <= lab.DEV_END].sum()), "VAL_total": float(d.pnl[d.index > lab.DEV_END].sum()),
                                      "n_sessions": len(d), "same_session_index": bool(d.index.equals(old.index))}
            runs[f"{name}|{env}"] = (bud, L, env, r, d, a)
    c7["portfolios"] = diffs
    DEV_OK = c7["sleeve_daily_max_abs_diff"] < 1e-6 and all(v["DEV_max_abs_diff"] < 1e-6 and v["same_session_index"] for v in diffs.values()) \
        and all(v["identical"] for v in c7["bars"].values())
    VAL_OK = all(v["VAL_max_abs_diff"] < 1e-6 for v in diffs.values()) and DEV_OK
    chk["7_reproduction"] = c7
    # ---------------------------------------------------------------- 5 holdout untouched
    outs = []
    for f in glob.glob(os.path.join(ROOT, "out", "p", "*.csv")):
        try:
            x = pd.read_csv(f, index_col=0, nrows=None)
            ix = pd.to_datetime(x.index, errors="coerce")
            if ix.notna().mean() > 0.9:
                outs.append((os.path.basename(f), str(ix.max().date())))
        except Exception:  # noqa: BLE001
            pass
    sl = [(os.path.basename(f), str(pd.read_parquet(f, columns=["sd"]).sd.max().date())) for f in glob.glob(os.path.join(ROOT, "out", "p", "sleeve_*.parquet"))]
    grep = subprocess.run(["grep", "-n", "HOLDOUT\\|end=None\\|VAL_END\\|DEV_END", *[os.path.join(SRC, f) for f in
                           ("t43/sleeves.py", "t43/portfolio.py", "p02_fingerprint.py", "p03_portfolio_dev.py", "p04_pre_val_freeze.py",
                            "p05_val_confirm.py", "p06_final_freeze.py")]], capture_output=True, text=True).stdout
    c5 = {"dated_outputs_max_date": dict(outs), "sleeve_files_max_session": dict(sl),
          "loader_truncation": "v6lab.load(inst, end=VAL_END) and sleeves.run_sleeve(end=VAL_END) truncate at session_date <= 2025-09-30 "
                               "immediately after reading the bar file, before features/sleeves/portfolio; no TEST43-P call uses end=None",
          "code_references": grep.strip().splitlines()}
    c5["pass"] = all(v <= "2025-09-30" for v in dict(outs).values()) and all(v <= "2025-09-30" for v in dict(sl).values()) and "end=None" not in grep
    chk["5_holdout_untouched"] = c5
    # ---------------------------------------------------------------- 8/9 simulator structure
    c8 = {}
    bud, L, env, r, d, _ = runs[SELECTED["PRIMARY"]]
    w = PD.weights(bud, sig, L)
    Dman = np.zeros_like(r["D"])
    for cid, wt in w.items():
        k = PF.INSTS.index(bk.inst[cid]); Dman[:, k] += wt * bk.des[cid]
    c8["net_target_equals_sum_of_weighted_sleeves"] = bool(np.allclose(Dman, r["D"]))
    c8["contract_weights_equal_final_manifest"] = bool(all(abs(w[c] - m["contract_weight"]) < 1e-9 for c, m in fin["portfolios"]["PRIMARY"]["members"].items()))
    c8["positions_integer_per_instrument"] = bool(r["pos"].dtype.kind == "i" and r["pos"].shape[1] == 2)
    c8["order_streams"] = "exactly one net order stream per instrument (kernel pend[k]); fills counted per instrument: " + str(r["fills"].tolist())
    c8["sleeves_never_trade"] = "sleeves are standalone virtual ledgers whose only output is desired exposure; the portfolio kernel is the only object that creates fills"
    single = bk.run({"ES_robust_A_MOD_1": 1.0}, gov=dict(marginU=100, deadband=0.01))
    dsingle = bk.daily(single).pnl
    c8["single_sleeve_reproduces_standalone"] = bool(abs(dsingle[dsingle.index <= lab.DEV_END].sum() - Dnew["ES_robust_A_MOD_1"][Dnew.index <= lab.DEV_END].sum()) < 1e-6)
    c8["shared_account"] = "one equity/HWM/governor/margin state across both instruments (kernel scalars eq, hwm, level)"
    c8["pass"] = c8["net_target_equals_sum_of_weighted_sleeves"] and c8["contract_weights_equal_final_manifest"] and c8["single_sleeve_reproduces_standalone"]
    chk["8_9_simulator"] = c8
    # ---------------------------------------------------------------- 10 costs / margins / account
    profs = {i: instruments.PROFILES[v6lab.PROF[i]] for i in PF.INSTS}
    c10 = {"commission_side": PF.GOV_DEFAULT["commission"], "slip_ticks": PF.GOV_DEFAULT["slip_ticks"],
           "roll_cost": {"MES": 2 * (profs["ES"]["commission_side"] + profs["ES"]["tick_value"]),
                         "MNQ": 2 * (profs["MNQ"]["commission_side"] + profs["MNQ"]["tick_value"])},
           "margin": {"MES": [instruments.margin_frac(profs["ES"], "intraday"), instruments.margin_frac(profs["ES"], "overnight")],
                      "MNQ": [instruments.margin_frac(profs["MNQ"], "intraday"), instruments.margin_frac(profs["MNQ"], "overnight")]},
           "marginU": PF.GOV_DEFAULT["marginU"], "initial_capital": lab.INIT}
    c10["pass"] = (c10["commission_side"] == fin["costs"]["commission_side"] and c10["slip_ticks"] == fin["costs"]["slippage_ticks"]
                   and abs(c10["roll_cost"]["MES"] - fin["costs"]["roll_cost"]["MES"]) < 1e-9 and abs(c10["roll_cost"]["MNQ"] - fin["costs"]["roll_cost"]["MNQ"]) < 1e-9
                   and c10["margin"]["MES"] == [fin["margin"]["MES"]["intraday_frac"], fin["margin"]["MES"]["overnight_frac"]]
                   and c10["margin"]["MNQ"] == [fin["margin"]["MNQ"]["intraday_frac"], fin["margin"]["MNQ"]["overnight_frac"]]
                   and c10["marginU"] == 0.5 and lab.INIT == 150000.0
                   and all(p["governor"]["marginU"] == 0.5 and p["governor"]["commission"] == 0.62 for p in fin["portfolios"].values()))
    chk["10_costs_margin_account"] = c10
    # ---------------------------------------------------------------- 11 acceptance evaluator (tested on synthetic + DEV/VAL; never holdout)
    tests = ACC.self_test()
    demo = {}
    for role, key in SELECTED.items():
        bud, L, env, r, d, a = runs[key]
        v = d[d.index > lab.DEV_END]
        demo[role] = ACC.evaluate(v, env, report_only={"note": "applied to VAL only as an evaluator dry run"})
    c11 = {"self_tests": tests, "dry_run_on_VAL_not_a_decision": demo, "rules_text": rules["per_portfolio_acceptance (each evaluated at its frozen envelope; ALL must hold)"]}
    c11["pass"] = all(t["pass"] for t in tests)
    chk["11_acceptance_evaluator"] = c11
    ACC_OK = c11["pass"]
    # ---------------------------------------------------------------- 12 SESSION_MATCHED_BETA (report only)
    smb = {}
    for role, key in SELECTED.items():
        bud, L, env, r, d, a = runs[key]
        for per, (s_, e_) in (("DEV", (None, lab.DEV_END)), ("VAL", (lab.DEV_END + pd.Timedelta(days=1), lab.VAL_END))):
            smb[f"{role}|{per}"] = ACC.session_matched_beta(bk.T, r["pos"], d, s_, e_)
    c12 = {"definition": ACC.SMB_DOC, "results_DEV_VAL": smb, "pass_fail_role": "REPORT ONLY (not a pass condition; not used for any selection)"}
    SMB_OK = all(np.isfinite(v["portfolio_net_pnl"]) and np.isfinite(v["session_matched_net_pnl"]) for v in smb.values())
    chk["12_session_matched_beta"] = c12
    status = {"FREEZE_HASHES_PASS": FREEZE_OK, "CODE_HASHES_PASS": CODE_OK, "DATA_HASHES_PASS": DATA_OK,
              "DEV_REPRODUCTION_PASS": DEV_OK, "VAL_REPRODUCTION_PASS": VAL_OK,
              "HOLDOUT_UNTOUCHED_CONFIRMED": c5["pass"] and c6["pass"], "ACCEPTANCE_EVALUATOR_PASS": ACC_OK,
              "SESSION_MATCHED_BETA_READY": SMB_OK}
    status["READY_TO_OPEN_HOLDOUT"] = all(status.values()) and c8["pass"] and c10["pass"]
    status = {k: ("YES" if v else "NO") for k, v in status.items()}
    status["HOLDOUT_OPENED"] = "NO"
    R["status"] = status
    R["frozen_hashes"] = EXPECT; R["selected"] = SELECTED
    out = os.path.join(FZ, "TEST43P_FINAL_PREFLIGHT.json")
    json.dump(R, open(out, "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    print(json.dumps(status, indent=1))
    return R


if __name__ == "__main__":
    main()
