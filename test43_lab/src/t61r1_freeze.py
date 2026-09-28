"""T61-R1 corrected freeze (supersedes the first t61r1_validate.py freeze, whose cap-enforcement QA was tautological).
Implementation rule vs live promotion gate are separated; nominated architecture fixed by TEST61 prereg semantics = X2_B_INT."""
import datetime
import glob
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import prog_common as P  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test61r1"); FZ = os.path.join(H.HX, "freeze_r1")

if __name__ == "__main__":
    for f in ("CORRECTED_PRE_OOS_FREEZE.json", "CORRECTED_OOS_RULES.json", "CORRECTED_FREEZE.sha256"):
        p = os.path.join(FZ, f)
        if os.path.exists(p):
            shutil.move(p, os.path.join(FZ, "SUPERSEDED_v1_" + f))
    X2 = pd.read_csv(f"{OUT}/C43_X2_THREE_WAY.csv").set_index("variant")
    CMP = pd.read_csv(f"{OUT}/T61R1_COMPARISON_TABLE.csv")
    why = json.load(open(f"{OUT}/C43_X2_WHY.json"))
    lanes = pd.read_csv(f"{OUT}/T61R1_LANES.csv").iloc[0]
    r1a = CMP[CMP.portfolio.str.startswith("T61-R1A")].iloc[0]; r1b = CMP[CMP.portfolio.str.startswith("T61-R1B")].iloc[0]
    now = datetime.datetime.now(datetime.timezone.utc); oos = first_rth_after(now)
    impl = {"C43-CORE": "frozen TEST43-P SECONDARY_2 / CHAMPION_CONTROL_V1 engine, unchanged",
            "T55 (GROWTH SHADOW)": "C43x1 + TEST53 residual; TEST53 admitted only while total MNQ <= 3 (entry rule as frozen in TEST55)",
            "T61-R1B (PROVISIONAL HIGH-GROWTH FORWARD CANDIDATE)": {
                "C43_leg": "X2_B_INT: the frozen C43 engine takes its integer decision on the 1x float target; the order is exactly 2 x that integer; every $ "
                           "governor threshold (env DD tiers, day stop) is doubled; $150k account; original margin logic (never binding: peak util 0.12)",
                "TEST53_leg": "M1-M4 frozen per-fold genomes, 1 MNQ per lot, ensemble cap 2, ensemble day governor -1000 (unchanged)",
                "IMPLEMENTATION_RULE": "GLOBAL TOTAL MNQ TARGET <= 6 at every RTH execution minute: C43 has priority; if C43 raises its MNQ so that C43 + open TEST53 "
                                       "lots > 6, the excess TEST53 lots (latest first) are closed at the next 1m open; new TEST53 lots only while total < 6",
                "MES": "2 x C43 MES (peak 6)", "no_retuning": True}}
    gates = {"common": ">= 250 full RTH OOS sessions; incremental avg/day vs C43-CORE > 0; matched-beta excess of the TEST53 leg > 0; no margin breach; "
                       "IMPLEMENTATION_RULE respected every session (a total > 6 lasting beyond one 1m fill lag = breach); no retuning",
             "GROWTH_STYLE": "forward MaxDD <= 30,000 and worst day >= -6,000",
             "CORE_STYLE (report)": "forward MaxDD <= 15,000, worst day >= -3,000, forward ret/DD >= C43-CORE forward ret/DD",
             "LIVE_PROMOTION_THRESHOLD": "forward MaxDD <= 20,000 AND worst day >= -5,000 AND common gate AND the X2 governor assumption re-approved by the user "
                                         "(the historical growth exists only with doubled $ governor thresholds: X2_A same-governor = 53.9 $/day ~ C43)"}
    rules = {"FINAL_GROWTH_PROGRAM_OOS_START": oos, "rule": "first full RTH session strictly after the corrected freeze; 2026-09-28 excluded (freeze after its RTH open)",
             "freeze_timestamp_utc": now.isoformat(timespec="seconds"), "IMPLEMENTATION_RULES": impl, "FORWARD_PROMOTION_GATES": gates,
             "labels": {"C43-CORE": "VALIDATED_CHAMPION", "T55": "GROWTH_SHADOW", "T61-R1B": "PROVISIONAL_FORWARD_GROWTH_CANDIDATE", "T61-R1A": "diagnostic only",
                        "T61_ORIGINAL_APPROXIMATION": "historical evidence only", "T61_HISTORICAL_SELECTION_CLEAN": "NO"},
             "excluded": "2026-05-28 .. OOS_START-1 never used", "NEW_OOS_OPENED": "NO", "live_authorization": "NO"}
    rp = os.path.join(FZ, "CORRECTED_OOS_RULES.json"); json.dump(rules, open(rp, "w"), indent=1)
    spec_p = os.path.join(FZ, "T61R1B_IMPLEMENTATION_SPEC.json"); json.dump(impl, open(spec_p, "w"), indent=1)
    srcs = [os.path.join(C45.SRC, f) for f in ("t61r1_validate.py", "t61r1_x2audit.py", "t61r1_freeze.py", "t53_run.py", "hx_common.py")]
    ev = sorted(p for p in glob.glob(os.path.join(OUT, "*")) if os.path.isfile(p) and not p.endswith(".log"))
    freeze = {"freeze_timestamp_utc": rules["freeze_timestamp_utc"], "nominated": "T61-R1B", "why_x2_versions_differ": why["why"], "parity_proof": why["proof"],
              "T61_R1B": {k: (float(r1b[k]) if isinstance(r1b[k], (int, float, np.floating, np.integer)) else r1b[k]) for k in
                          ("avg_day", "avg_day_2021", "max_dd", "worst_day", "ret_dd", "SLIP4_avg_day", "SLIP4_max_dd", "peak_MES", "peak_MNQ", "peak_margin_pct",
                           "cap_minutes_over6", "cap_over6_only_1min_lag", "forced_TEST53_reductions")},
              "growth_lane_with_plateau": {"GROWTH": bool(lanes.GROWTH), "plateau_totals": lanes.plateau_totals},
              "implementation_spec_sha256": P.sha(spec_p), "source_sha256": {os.path.basename(p): P.sha(p) for p in srcs},
              "evidence_sha256": {os.path.relpath(p, C45.ROOT): P.sha(p) for p in ev}, "superseded": "SUPERSEDED_v1_* (tautological cap QA)",
              "prior_growth_freeze": open(os.path.join(H.HX, "freeze", "FINAL_GROWTH_PROGRAM_FREEZE.sha256")).read(), "live_authorization": "NO"}
    fp = os.path.join(FZ, "CORRECTED_PRE_OOS_FREEZE.json"); json.dump(freeze, open(fp, "w"), indent=1, default=str)
    hf, hr = P.sha(fp), P.sha(rp)
    open(os.path.join(FZ, "CORRECTED_FREEZE.sha256"), "w").write(f"{hf}  CORRECTED_PRE_OOS_FREEZE.json\n{hr}  CORRECTED_OOS_RULES.json\n")
    files = sorted(glob.glob(os.path.join(FZ, "*")) + ev + srcs)
    HI = pd.DataFrame({"file": [os.path.relpath(p, C45.ROOT) for p in files], "sha256": [P.sha(p) for p in files]})
    HI.to_csv(os.path.join(FZ, "T61R1_HASH_INDEX.csv"), index=False)
    st = {"C43_X2_SIMPLE_APPROX_AVG_DAY": round(X2.loc["SIMPLE_2X_DAILY_APPROX", "avg_day"], 2), "C43_X2_A_SAME_GOV_AVG_DAY": round(X2.loc["X2_A_INT", "avg_day"], 2),
          "C43_X2_B_SCALED_GOV_AVG_DAY": round(X2.loc["X2_B_INT", "avg_day"], 2), "X2_A_CORR_TO_SIMPLE_2X": round(X2.loc["X2_A_INT", "corr_to_simple_2x"], 3),
          "X2_B_CORR_TO_SIMPLE_2X": round(X2.loc["X2_B_INT", "corr_to_simple_2x"], 3), "X2_A_MAXDD": round(X2.loc["X2_A_INT", "max_dd"]),
          "X2_B_MAXDD": round(X2.loc["X2_B_INT", "max_dd"]), "X2_A_WORST_DAY": round(X2.loc["X2_A_INT", "worst_day"]), "X2_B_WORST_DAY": round(X2.loc["X2_B_INT", "worst_day"]),
          "FLOAT_DIAGNOSTICS": {"X2_A_FLOAT_avg_day": round(X2.loc["X2_A_FLOAT", "avg_day"], 2), "X2_B_FLOAT_avg_day": round(X2.loc["X2_B_FLOAT", "avg_day"], 2)},
          "OLD_T61_PEAK_MNQ": 8, "GLOBAL_CAP6_IMPLEMENTATION_PASS": bool(r1b.cap_over6_only_1min_lag and r1a.cap_over6_only_1min_lag),
          "T61_R1A_AVG_DAY": round(r1a.avg_day, 2), "T61_R1A_MAXDD": round(r1a.max_dd), "T61_R1A_WORST_DAY": round(r1a.worst_day), "T61_R1A_RET_DD": round(r1a.ret_dd, 4),
          "T61_R1B_AVG_DAY": round(r1b.avg_day, 2), "T61_R1B_MAXDD": round(r1b.max_dd), "T61_R1B_WORST_DAY": round(r1b.worst_day), "T61_R1B_RET_DD": round(r1b.ret_dd, 4),
          "T61_R1B_SLIP4_AVG_DAY": round(r1b.SLIP4_avg_day, 2), "FULL_PORTFOLIO_SLIP4_PASS": bool(r1b.SLIP4_avg_day > 0 and r1b.SLIP4_max_dd <= 30000 and r1b.SLIP4_worst >= -6000),
          "FINAL_PROVISIONAL_GROWTH_CANDIDATE": "T61-R1B (C43 X2_B_INT + TEST53 residual + GLOBAL MNQ TARGET <= 6)",
          "CORRECTED_PRE_OOS_FREEZE_SHA256": hf, "CORRECTED_OOS_RULES_SHA256": hr, "FINAL_GROWTH_PROGRAM_OOS_START": oos, "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(st, open(f"{OUT}/T61R1_FINAL_STATUS.json", "w"), indent=1)
    H.md("T61R1_CORRECTED_FREEZE.md", "T61-R1 corrected freeze", ["```json\n" + json.dumps(st, indent=1) + "\n```", "C43 x2 three-way:", X2.T, "Comparison:", CMP.T,
                                                                 "Why:", "```json\n" + json.dumps(why, indent=1) + "\n```"])
    print(json.dumps(st, indent=1))
