"""T61-R1C_ATOMIC_CAP6: execution-layer correction only (no economic change).  At every causal decision timestamp the C43 (X2_B_INT) target and the
TEST53 virtual target are combined: TEST53 is clamped to max(0, 6 - C43 target) and ONE aggregate MNQ target is sent as a net order at the same fill
(no separate C43 add followed by a TEST53 cut one minute later).  Compared with T61-R1B; frozen GROWTH gate; corrected freeze v3."""
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
import t47_engine as E  # noqa: E402
import t44_common as TC  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402
from t43 import portfolio as PF  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402
from t53_run import matched_excess, module_trades  # noqa: E402
from t61r1_validate import grid_positions, metrics, simulate_hard  # noqa: E402
from t61r1_x2audit import run_mult  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test61r1"); FZ = os.path.join(H.HX, "freeze_r1")


def main():
    TC.setup()
    fin = json.load(open(os.path.join(C45.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")))
    Pp = fin["portfolios"]["SECONDARY_2"]; w = {c: m["contract_weight"] for c, m in Pp["members"].items()}
    bk3 = PF.Book(TC.END, TC.ELIG)
    gov1 = PD.gov_for(Pp["risk_envelope"]); gov2 = dict(gov1); gov2["env_dd"] *= 2; gov2["day_stop"] *= 2
    rB = run_mult(bk3, w, gov2, 2); rB4 = run_mult(bk3, w, gov2, 2, slip_ticks=4.0)          # X2_B_INT (C43 leg, exact)
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = nq.pn.sess; full = sess >= H.START
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    A = lambda s_: s_.reindex(sess).fillna(0.0).values
    cx, cx4 = A(rB["daily"]), A(rB4["daily"]); c1 = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE2, pM2 = grid_positions(bk3.T, rB["pos"], sess)
    pM2n = np.nan_to_num(pM2, nan=6.0)
    hard = np.maximum(0, 6 - pM2n).astype(int)
    TR = module_trades(nq, sess)
    res = {}
    for nm, at in (("T61-R1B", False), ("T61-R1C_ATOMIC_CAP6", True)):
        d, L, cnt, nev = simulate_hard(nq, TR, -1000.0, hard, hard, atomic=at)
        d4, _, _, _ = simulate_hard(nq, TR, -1000.0, hard, hard, slip=4.0, atomic=at)
        t = sum(d.values()); t[:s21] = 0; cnt[:s21] = 0; t4 = sum(d4.values()); t4[:s21] = 0
        res[nm] = dict(t=t, t4=t4, L=L, cnt=cnt, nev=nev)
    rows = []; ndays = full.sum()
    for nm, r in res.items():
        tot = np.nan_to_num(pM2) + r["cnt"]
        tgt = np.nan_to_num(pM2) + np.minimum(r["cnt"], hard)        # aggregate target after the clamp
        o = metrics(nm, cx + r["t"], sess, np.nan_to_num(pE2), tot, bk, np.sum(rB["sides"]) / ndays + 2 * len(r["L"][r["L"].s_in >= s21]) / ndays, cx4 + r["t4"])
        o.update({"avg_day_2021": float((cx + r["t"])[sess >= H.SPAN21].mean()), "peak_MNQ_target": int(np.nanmax(tgt[full])), "peak_actual_MNQ": int(np.nanmax(tot[full])),
                  "minutes_actual_gt6": int((tot[full] > 6).sum()), "netting_or_cap_events": int(r["nev"]),
                  "netting_cost_saving_if_netted_$": float(r["nev"] * 2 * C45.cost_side(nq.k))})
        exr = matched_excess(nq, r["L"]); exr[:s21] = 0
        o["matched_excess_TEST53_day"] = float(exr[s21:].mean())
        rows.append(o)
    R = pd.DataFrame(rows)
    rc = res["T61-R1C_ATOMIC_CAP6"]
    # frozen GROWTH gate on R1C (base C43-CORE): plateau governor +-10/20%, full SLIP4
    pl = []
    for g in (-800.0, -900.0, -1100.0, -1200.0):
        d, _, _, _ = simulate_hard(nq, TR, g, hard, hard, atomic=True); t = sum(d.values()); t[:s21] = 0
        pl.append(float((cx + t - c1)[s21:].sum()))
    base_tot = float((cx + rc["t"] - c1)[s21:].sum())
    rr = R.iloc[1]
    lane = H.lane_eval("T61-R1C_ATOMIC_CAP6", cx + rc["t"], c1, sess, rr["overnight_peak_margin_pct"] / 100 * H.NLV, rr["peak_margin_pct"] / 100 * H.NLV,
                       float(rr["matched_excess_TEST53_day"]), {"plateau_pass": bool(all(v > 0 and v >= 0.6 * base_tot for v in pl)),
                                                                 "stress4_pos": bool((cx4 + rc["t4"] - c1)[s21:].sum() > 0)})
    lane["plateau_totals"] = str([round(v) for v in pl])
    diff = (cx + rc["t"]) - (cx + res["T61-R1B"]["t"])
    cmpd = {"pnl_diff_total_R1C_minus_R1B": float(diff[full].sum()), "pnl_diff_days_nonzero": int((np.abs(diff[full]) > 1e-6).sum()),
            "pnl_diff_max_abs_day": float(np.abs(diff[full]).max())}
    R.to_csv(f"{OUT}/T61R1C_vs_R1B.csv", index=False); pd.DataFrame([lane]).to_csv(f"{OUT}/T61R1C_LANE.csv", index=False)
    np.savez_compressed(f"{OUT}/T61R1C_daily.npz", r1c=cx + rc["t"], r1c_slip4=cx4 + rc["t4"], r1b=cx + res["T61-R1B"]["t"])
    growth = bool(lane["GROWTH"]) and rr["peak_actual_MNQ"] <= 6
    # ---------------------------------------------------------------- corrected freeze v3
    for f in ("CORRECTED_PRE_OOS_FREEZE.json", "CORRECTED_OOS_RULES.json", "CORRECTED_FREEZE.sha256", "T61R1B_IMPLEMENTATION_SPEC.json"):
        p = os.path.join(FZ, f)
        if os.path.exists(p):
            shutil.move(p, os.path.join(FZ, "SUPERSEDED_v2_" + f))
    now = datetime.datetime.now(datetime.timezone.utc); oos = first_rth_after(now)
    final = "T61-R1C_ATOMIC_CAP6" if growth else "NONE (T61-R1B historical evidence only; T55 growth shadow)"
    impl = {"C43-CORE": "frozen C43 engine unchanged", "T55 (GROWTH SHADOW)": "C43x1 + TEST53 residual (TEST53 admitted only while total MNQ <= 3)",
            "T61-R1C_ATOMIC_CAP6 (PROVISIONAL FORWARD GROWTH IMPLEMENTATION)" if growth else "T61-R1C (not adopted)": {
                "C43_leg": "X2_B_INT: 1x integer decision x2; C43 $ governor thresholds x2; $150k account; original margin logic",
                "TEST53_leg": "M1-M4 frozen per-fold genomes, 1 MNQ/lot, ensemble cap 2, ensemble day governor -1000",
                "EXECUTION": "at every causal decision timestamp: C43 virtual target -> TEST53 virtual target -> allowed_TEST53 = max(0, 6 - C43 target) -> "
                             "TEST53 clamped (latest lots first) -> ONE aggregate broker MNQ target -> single NET order at the next legal fill",
                "IMPLEMENTATION_RULE": "BROKER_TARGET_MNQ <= 6 and BROKER_POSITION_MNQ <= 6 at all times (except broker partial-fill anomalies)",
                "MES": "2 x C43 MES (peak 6)", "no_retuning": True}}
    gates = {"common": ">= 250 full RTH OOS sessions; incremental avg/day vs C43-CORE > 0; matched-beta excess of the TEST53 leg > 0; no margin breach; "
                       "BROKER_POSITION_MNQ <= 6 every session; no retuning",
             "GROWTH_STYLE": "forward MaxDD <= 30,000 and worst day >= -6,000",
             "CORE_STYLE (report)": "forward MaxDD <= 15,000, worst day >= -3,000, forward ret/DD >= C43-CORE forward ret/DD",
             "LIVE_PROMOTION_THRESHOLD": "forward MaxDD <= 20,000 AND worst day >= -5,000 AND common gate AND user re-approval of the doubled C43 $ governor "
                                         "thresholds (same-governor X2_A = 53.9 $/day ~ C43)"}
    rules = {"FINAL_GROWTH_PROGRAM_OOS_START": oos, "rule": "first full RTH session strictly after this freeze; 2026-09-28 excluded", "freeze_timestamp_utc": now.isoformat(timespec="seconds"),
             "IMPLEMENTATION_RULES": impl, "FORWARD_PROMOTION_GATES": gates,
             "labels": {"C43-CORE": "VALIDATED_CHAMPION", "T55": "GROWTH_SHADOW", "T61-R1C": "PROVISIONAL_FORWARD_GROWTH_IMPLEMENTATION" if growth else "NOT_ADOPTED",
                        "T61-R1B": "historical evidence (superseded execution)", "T61_HISTORICAL_SELECTION_CLEAN": "NO", "T61_HISTORICAL_TUNING": "STOPPED"},
             "excluded": "2026-05-28 .. OOS_START-1 never used", "NEW_OOS_OPENED": "NO", "live_authorization": "NO"}
    rp = os.path.join(FZ, "CORRECTED_OOS_RULES.json"); json.dump(rules, open(rp, "w"), indent=1)
    sp = os.path.join(FZ, "T61R1C_IMPLEMENTATION_SPEC.json"); json.dump(impl, open(sp, "w"), indent=1)
    srcs = [os.path.join(C45.SRC, f) for f in ("t61r1c_atomic.py", "t61r1_validate.py", "t61r1_x2audit.py", "t53_run.py", "hx_common.py")]
    ev = sorted(p for p in glob.glob(os.path.join(OUT, "*")) if os.path.isfile(p) and not p.endswith(".log"))
    freeze = {"freeze_timestamp_utc": rules["freeze_timestamp_utc"], "final_provisional_growth": final,
              "R1C_vs_R1B": R.to_dict("records"), "R1C_lane": {k: (v if not isinstance(v, (np.floating, np.integer, np.bool_)) else v.item()) for k, v in lane.items()},
              "pnl_diff": cmpd, "implementation_spec_sha256": P.sha(sp), "source_sha256": {os.path.basename(p): P.sha(p) for p in srcs},
              "evidence_sha256": {os.path.relpath(p, C45.ROOT): P.sha(p) for p in ev}, "superseded": ["SUPERSEDED_v1_*", "SUPERSEDED_v2_*"], "live_authorization": "NO"}
    fp = os.path.join(FZ, "CORRECTED_PRE_OOS_FREEZE.json"); json.dump(freeze, open(fp, "w"), indent=1, default=str)
    hf, hr = P.sha(fp), P.sha(rp)
    open(os.path.join(FZ, "CORRECTED_FREEZE.sha256"), "w").write(f"{hf}  CORRECTED_PRE_OOS_FREEZE.json\n{hr}  CORRECTED_OOS_RULES.json\n")
    files = sorted(set(glob.glob(os.path.join(FZ, "*"))) - {os.path.join(FZ, "T61R1_HASH_INDEX.csv")}) + ev + srcs
    pd.DataFrame({"file": [os.path.relpath(p, C45.ROOT) for p in files], "sha256": [P.sha(p) for p in files]}).to_csv(os.path.join(FZ, "T61R1_HASH_INDEX.csv"), index=False)
    b, c = R.iloc[0], R.iloc[1]
    st = {k: v for k, v in {
        "T61_R1B": {"avg_day": round(b.avg_day, 2), "max_dd": round(b.max_dd), "worst_day": round(b.worst_day), "ret_dd": round(b.ret_dd, 4), "SLIP4_avg_day": round(b.SLIP4_avg_day, 2),
                    "peak_MNQ_target": int(b.peak_MNQ_target), "peak_actual_MNQ": int(b.peak_actual_MNQ), "cap_events": int(b.netting_or_cap_events)},
        "T61_R1C": {"avg_day": round(c.avg_day, 2), "avg_day_2021": round(c.avg_day_2021, 2), "max_dd": round(c.max_dd), "worst_day": round(c.worst_day), "ret_dd": round(c.ret_dd, 4),
                    "SLIP4_avg_day": round(c.SLIP4_avg_day, 2), "SLIP4_max_dd": round(c.SLIP4_max_dd), "peak_MNQ_target": int(c.peak_MNQ_target), "peak_actual_MNQ": int(c.peak_actual_MNQ),
                    "netting_events": int(c.netting_or_cap_events), "GROWTH_lane": bool(lane["GROWTH"]), "CORE_lane": bool(lane["CORE"]), "plateau": lane["plateau_totals"]},
        "PNL_DIFF_R1C_MINUS_R1B": cmpd, "FINAL_PROVISIONAL_GROWTH_IMPLEMENTATION": final,
        "CORRECTED_PRE_OOS_FREEZE_SHA256": hf, "CORRECTED_OOS_RULES_SHA256": hr, "FINAL_GROWTH_PROGRAM_OOS_START": oos, "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}.items()}
    json.dump(st, open(f"{OUT}/T61R1C_FINAL_STATUS.json", "w"), indent=1)
    H.md("T61R1C_ATOMIC_CAP6.md", "T61-R1C atomic net-target execution correction", ["```json\n" + json.dumps(st, indent=1) + "\n```", R.T, pd.DataFrame([lane]).T])
    pd.set_option("display.width", 250); print(R.round(3).T.to_string()); print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
