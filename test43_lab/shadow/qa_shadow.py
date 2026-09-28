"""Track A QA on research data only (<= 2026-05-27): (1) reproduction of the frozen historical T61-R1C / C43 daily; (2) causality / prefix
invariance: a run whose data END is 2025-12-31 must give identical rows for 2025-10-01 .. 2025-12-30 as the run with END 2026-05-27;
(3) forward-fold code path (FINAL_ALL genomes appended after the last outer fold) smoke test (trade counts only); (4) fail-closed test."""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.abspath(os.path.join(HERE, ".."))
QA = os.path.join(LAB, "out", "forward_shadow_qa")
sys.path.insert(0, os.path.join(LAB, "src"))


def run(end, rs, tag):
    out = os.path.join(QA, tag)
    if not os.path.exists(os.path.join(out, "daily_report.csv")):
        subprocess.run([sys.executable, os.path.join(HERE, "forward_shadow.py"), "replay", "--end", end, "--report-start", rs, "--out", out], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def main():
    import t45_common as C45
    res = {}
    full = run("2026-05-27", "2025-10-01", "replay_full")
    R = pd.read_csv(os.path.join(full, "daily_report.csv"), parse_dates=["date"])
    z = np.load(os.path.join(LAB, "out/test61r1/T61R1C_daily.npz")); sess = pd.DatetimeIndex(C45.build_panel()["sessions"])
    for name, ref in (("T61-R1C", pd.Series(z["r1c"], index=sess)), ("C43-CORE", C45.champion_daily().pnl)):
        x = R[R.portfolio == name].set_index("date").daily_pnl
        res[f"reproduction_maxabs_{name}"] = float((x - ref.reindex(x.index)).abs().max())
    pre = run("2025-12-31", "2025-10-01", "replay_prefix_2025-12-31")
    Q = pd.read_csv(os.path.join(pre, "daily_report.csv"), parse_dates=["date"])
    cut = pd.Timestamp("2025-12-30")
    a = R[R.date <= cut].set_index(["date", "portfolio"]).sort_index(); b = Q[Q.date <= cut].set_index(["date", "portfolio"]).sort_index()
    num = [c for c in a.columns if c in b.columns and a[c].dtype.kind in "fi"]
    diff = (a[num] - b[num]).abs().max()
    res["prefix_rows_compared"] = int(len(b)); res["prefix_max_abs_diff_by_col"] = {k: float(v) for k, v in diff.items() if v > 1e-6}
    for nm in ("C43-CORE", "T55", "T61-R1C"):
        la = pd.read_csv(os.path.join(full, f"session_log_{nm}.csv.gz"), parse_dates=["session"]); lb = pd.read_csv(os.path.join(pre, f"session_log_{nm}.csv.gz"), parse_dates=["session"])
        la, lb = la[la.session <= cut].reset_index(drop=True), lb[lb.session <= cut].reset_index(drop=True)
        cols = [c for c in ("final_target_MES", "final_target_MNQ", "clamped_TEST53", "virtual_TEST53", "order_delta_MNQ", "C43_gov_level") if c in la]
        res[f"prefix_minute_mismatch_{nm}"] = int((la[cols].fillna(-9).values != lb[cols].fillna(-9).values).any(axis=1).sum())
    res["PREFIX_INVARIANT"] = bool(not res["prefix_max_abs_diff_by_col"] and all(v == 0 for k, v in res.items() if k.startswith("prefix_minute")))
    res["REPRODUCES_FROZEN_HISTORY"] = bool(max(v for k, v in res.items() if k.startswith("reproduction")) < 1e-6)
    # forward-fold code path: FINAL_ALL genomes appended exactly as shadow_engine does for END > 2026-05-27 (smoke: trade counts only)
    code = ("import sys,os;sys.path.insert(0,'src');import t45_common as C45,numpy as np;"
            "C45.OUTER[-1]=(C45.OUTER[-1][0],C45.OUTER[-1][1],'2025-12-31');C45.OUTER.append(('FINAL_ALL_TO_2026-05-27','2026-01-01','2026-05-27'));"
            "import t47_engine as E;from t53_run import module_trades;es,nq=E.setup();TR=module_trades(nq,nq.pn.sess);"
            "s0=int(np.searchsorted(nq.pn.sess.values,np.datetime64('2026-01-01')));print(TR[TR.s>=s0].groupby('mod').size().to_dict())")
    res["forward_fold_code_path_trades_by_module"] = subprocess.run([sys.executable, "-c", code], cwd=LAB, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    # fail-closed: tamper a copy of the package and verify it refuses
    tmp = os.path.join(QA, "_tamper"); shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(os.path.join(LAB, "frozen", "t61_r1c"), os.path.join(tmp, "frozen", "t61_r1c"))
    open(os.path.join(tmp, "frozen", "t61_r1c", "src", "t53_run.py"), "a").write("\n# tamper\n")
    r = subprocess.run([sys.executable, os.path.join(tmp, "frozen", "t61_r1c", "verify_frozen.py")], capture_output=True, text=True)
    res["FAIL_CLOSED_ON_TAMPER"] = bool(r.returncode == 2 and "FAILED" in r.stdout); shutil.rmtree(tmp)
    json.dump(res, open(os.path.join(QA, "FORWARD_SHADOW_QA.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
