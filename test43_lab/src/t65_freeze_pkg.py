"""TEST65+ step 0: immutable T61-R1C_ATOMIC_CAP6 production/shadow package (frozen/t61_r1c/).
Copies the full import closure of the T61-R1C construction, every configuration artifact it reads, the corrected freeze v3 files and the
historical evidence; canonical data are referenced by sha256.  Writes T61_R1C_MANIFEST.json, T61_R1C_MANIFEST.sha256, T61_R1C_HASH_INDEX.csv.
Refuses to overwrite an existing package (permanent freeze)."""
import ast
import datetime
import json
import os
import shutil
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402

LAB = os.path.abspath(C45.ROOT); PKG = os.path.join(LAB, "frozen", "t61_r1c")
ENTRY = ["t61r1c_atomic.py"]


def closure(entry):
    src = os.path.join(LAB, "src"); seen = set(); st = list(entry)
    while st:
        f = st.pop()
        if f in seen or not os.path.exists(os.path.join(src, f)):
            continue
        seen.add(f)
        for n in ast.walk(ast.parse(open(os.path.join(src, f)).read())):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                ([n.module] + [n.module + "." + a.name for a in n.names]) if isinstance(n, ast.ImportFrom) and n.module else []
            st += [m.replace(".", "/") + ".py" for m in mods]
    pkg = {os.path.join("t43", f) for f in os.listdir(os.path.join(src, "t43")) if f.endswith(".py")}   # whole t43 package (relative imports)
    return sorted(seen | pkg)


ARTIFACTS = {  # lab-relative path -> role
    "out/p/freeze/TEST43P_FINAL_PORTFOLIOS.json": "C43 SECONDARY_2 members / contract weights / risk envelope",
    "out/test48/ga/GA-AC_selected.csv": "TEST53 M1 per-fold genomes (forward: FINAL_ALL_TO_2026-05-27 rank 0)",
    "out/test49/ga/GA-CT_selected.csv": "TEST53 M2 per-fold genomes (forward: FINAL_ALL_TO_2026-05-27 rank 0)",
    "out/test50/ga/GA-VX_selected.csv": "TEST53 M3 per-fold genomes (forward: FINAL_ALL_TO_2026-05-27 rank 0)",
    "out/v6/shortlist.json": "C43 sleeve candidate definitions (frozen V6 parameters)",
    "out/HIGH_EXPOSURE_PROGRAM/hx_gate_spec.json": "hx lane gate spec",
    "out/t45/baseline/champion_session_state.csv": "t45_feat baseline state table (imported, not used by T61 decisions)",
    "out/t44/daily_CHAMPION_CONTROL_V1.csv": "C43-CORE historical daily (reference)",
    "out/test53/TEST53_PREREGISTRATION.json": "TEST53 ensemble semantics (cap 2, governor -1000)",
    "out/test55/T55_results.csv": "T55 historical evidence",
    "out/HIGH_EXPOSURE_PROGRAM/freeze_r1/CORRECTED_PRE_OOS_FREEZE.json": "corrected freeze v3",
    "out/HIGH_EXPOSURE_PROGRAM/freeze_r1/CORRECTED_OOS_RULES.json": "corrected OOS rules v3 (OOS start 2026-09-29)",
    "out/HIGH_EXPOSURE_PROGRAM/freeze_r1/CORRECTED_FREEZE.sha256": "freeze v3 hashes",
    "out/HIGH_EXPOSURE_PROGRAM/freeze_r1/T61R1C_IMPLEMENTATION_SPEC.json": "T61-R1C implementation spec",
    "out/HIGH_EXPOSURE_PROGRAM/freeze_r1/T61R1_HASH_INDEX.csv": "freeze v3 hash index",
    "out/test61r1/T61R1C_daily.npz": "historical T61-R1C daily (reproduction target)",
    "out/test61r1/T61R1C_FINAL_STATUS.json": "historical T61-R1C metrics",
    "out/test61r1/T61R1C_vs_R1B.csv": "historical R1C vs R1B",
    "out/test61r1/T61R1C_LANE.csv": "historical GROWTH lane",
}

EXECUTION_SPEC = {
    "name": "T61-R1C_ATOMIC_CAP6",
    "status": "PERMANENTLY FROZEN; T61 historical tuning CLOSED",
    "steps_per_causal_decision_timestamp": [
        "1 C43 1x float target (frozen TEST43-P SECONDARY_2 / CHAMPION_CONTROL_V1 sleeves, 3m union timeline incl. overnight)",
        "2 X2_B_INT: integer decision taken on the 1x target (deadband 0.6) then multiplied by 2",
        "3 C43 $ governor thresholds doubled (env DD tiers dd1/dd2 = 2 x env_dd x {0.6, 0.85}; day stop 2 x 0.8 x |worst|); marginU 0.5; INIT 150k",
        "4 TEST53 virtual target: M1 GA-AC, M2 GA-CT, M3 GA-VX, M4 opening drive; 1 MNQ/lot; ensemble cap 2; ensemble day governor -1000",
        "5 C43 priority: allowed_TEST53 = max(0, 6 - C43_MNQ_target)",
        "6 clamp TEST53 (latest lots first) to allowed_TEST53",
        "7 ONE aggregate MNQ target = C43_MNQ_target + clamped TEST53 (never > 6), single net order at the next legal 1m open",
        "8 MES target = 2 x C43 1x MES integer decision (peak 6)"],
    "entry_exit_overnight": "exactly as frozen in the TEST53 / C43 engines (M2 holds to next 09:31 open; C43 overnight per sleeves)",
    "code_entrypoint": "frozen/t61_r1c/src/t61r1c_atomic.py (historical) ; shadow/forward_shadow.py (forward, imports the byte-identical live copies)",
    "forward_conventions": {
        "TEST53_forward_genomes": "fold FINAL_ALL_TO_2026-05-27, sel_rank 0 (program convention; used for every session after 2026-05-27)",
        "state": "continuous: the frozen kernels run over all available history so indicator / $ governor state is the same object as in the backtest; "
                 "sessions before the OOS start are warm-up only and are never written, reported or looked at",
        "OOS_START": "2026-09-29", "gap_2026-05-28_to_2026-09-28": "never used for research or tuning; warm-up only inside the forward runner"},
}


def main():
    if os.path.exists(os.path.join(PKG, "T61_R1C_MANIFEST.json")):
        raise SystemExit("frozen/t61_r1c already exists - permanent freeze, refusing to overwrite")
    os.makedirs(PKG, exist_ok=True)
    rows = []
    for f in closure(ENTRY):
        live = os.path.join("src", f); dst = os.path.join(PKG, "src", f); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(LAB, live), dst)
        rows.append({"kind": "source", "frozen_path": os.path.join("src", f), "live_path": live, "sha256": P.sha(dst), "role": "T61-R1C import closure"})
    for rel, role in ARTIFACTS.items():
        dst = os.path.join(PKG, "artifacts", rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(LAB, rel), dst)
        rows.append({"kind": "artifact", "frozen_path": os.path.join("artifacts", rel), "live_path": rel, "sha256": P.sha(dst), "role": role})
    for inst, (rel, h) in C45.DATA.items():
        rows.append({"kind": "reference_only", "frozen_path": "", "live_path": rel, "sha256": h, "role": f"canonical 1m {inst} (research data <= 2026-05-27)"})
    vf = os.path.join(PKG, "verify_frozen.py")
    rows.append({"kind": "guard", "frozen_path": "verify_frozen.py", "live_path": "", "sha256": P.sha(vf), "role": "fail-closed verifier"})
    HI = pd.DataFrame(rows)
    HI.to_csv(os.path.join(PKG, "T61_R1C_HASH_INDEX.csv"), index=False)
    st = json.load(open(os.path.join(LAB, "out/test61r1/T61R1C_FINAL_STATUS.json")))
    man = {"package": "T61-R1C_ATOMIC_CAP6 production / shadow package", "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "T61_R1C_FROZEN": "YES", "frozen_elements": ["C43 rules", "X2_B semantics + doubled C43 $ governor thresholds", "TEST53 M1-M4 + day governor + ensemble cap",
                                                          "atomic netting + GLOBAL MNQ CAP 6", "MES scaling", "entry / exit / overnight logic"],
           "execution_spec": EXECUTION_SPEC, "historical_metrics": st["T61_R1C"],
           "corrected_freeze_sha256": st["CORRECTED_PRE_OOS_FREEZE_SHA256"], "corrected_rules_sha256": st["CORRECTED_OOS_RULES_SHA256"],
           "T61_FORWARD_OOS_START": "2026-09-29",
           "forward_promotion": {"common": ">= 250 OOS sessions; T61 incremental vs C43 > 0; TEST53 matched excess > 0; no margin breach; MNQ <= 6; no retuning",
                                 "LIVE_reference": "MaxDD <= 20,000 and worst day >= -5,000 AND user approval of the doubled C43 $ governor thresholds",
                                 "auto_promotion": "NO"},
           "hash_index_sha256": P.sha(os.path.join(PKG, "T61_R1C_HASH_INDEX.csv")), "n_files": len(HI),
           "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO"}
    mp = os.path.join(PKG, "T61_R1C_MANIFEST.json"); json.dump(man, open(mp, "w"), indent=1)
    open(os.path.join(PKG, "T61_R1C_MANIFEST.sha256"), "w").write(f"{P.sha(mp)}  T61_R1C_MANIFEST.json\n")
    sys.path.insert(0, PKG); import verify_frozen  # noqa: E402
    verify_frozen.verify(check_data=True)
    print(HI.kind.value_counts().to_dict(), P.sha(mp))


if __name__ == "__main__":
    main()
