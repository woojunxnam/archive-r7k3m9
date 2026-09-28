"""TEST46 final candidate gate (T46_36/T46_38).  Mechanical rule (TEST46 prompt section 66 + the TEST45 economic threshold,
fixed before the gate table was computed):
  G1 outer/walk-forward block median incremental $/day > 0 and >= 4 of 5 outer blocks (2021, 2022, 2023, 2024, 2025-26) > 0
  G2 positive matched-long excess over the evaluation span
  G3 C43 + candidate: MaxDD <= $15,000, worst day >= -$3,000, return/MaxDD >= C43
  G4 remove-top-3 incremental total > 0
  G5 economically meaningful: incremental >= $5/day and |corr with C43| <= 0.5
  G6 beats the simplest same-family control on total P&L over the same span
  G7 GA/GP: parameter plateau PASS and concept recurrence >= 3 of 5 folds;  ML: decision-threshold neighbourhood stable
  G8 live-engine parity PASS for any Lane-A seed it depends on (all INDEX6 seeds are PARITY_BLOCKED -> Lane A ineligible)
FINAL = the lowest complexity rung among passers (at most one); otherwise NONE."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t46_common as C  # noqa: E402
import t46_05_gaA as GA  # noqa: E402

OUT = os.path.join(C.T46, "final"); os.makedirs(OUT, exist_ok=True)
BLOCKS = [(n, a, b) for n, a, b in C45.OUTER]


def block_stats(pnl, sess):
    return {n: float(pnl[(sess >= np.datetime64(a)) & (sess <= np.datetime64(b))].mean()) for n, a, b in BLOCKS}


def comb(pnl, champ, m):
    x = champ[m] + pnl[m]; eq = np.r_[0, np.cumsum(x)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    ce = np.r_[0, np.cumsum(champ[m])]; cmdd = float((np.maximum.accumulate(ce) - ce).max())
    return {"comb_avg": float(x.mean()), "comb_mdd": mdd, "comb_worst": float(x.min()), "comb_ret_dd": float(x.mean() / mdd),
            "C43_avg": float(champ[m].mean()), "C43_mdd": cmdd, "C43_ret_dd": float(champ[m].mean() / cmdd),
            "corr": float(np.corrcoef(champ[m], pnl[m])[0, 1]) if pnl[m].std() > 0 else np.nan}


def main():
    GA._init()
    es = GA._ctx["es"]; sess = es.pn.sess.values; champ = GA._ctx["champ"]; n = len(sess)
    span = sess >= np.datetime64("2021-01-01")
    cands = {}
    # GA-A nested stitched
    S = pd.read_csv(os.path.join(C.T46, "gaA", "T46_26_gaA_selected.csv"))
    st = np.zeros(n); exc = np.zeros(n)
    for name, a, b in BLOCKS:
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        if not len(r):
            continue
        g = json.loads(r.iloc[0].genome)
        mk, ev, pnl = GA.run_genome(g)
        m = (sess >= np.datetime64(a)) & (sess <= np.datetime64(b))
        st[m] = pnl[m]
        s0 = int(np.argmax(m)); em, hold = g["exit_mode"], (g["hold"] if g["exit_mode"] == 0 else 0)
        bl = np.nanmean(GA._ctx["base"][(GA.fix(g)["inst"], em, hold)][:s0], axis=0)
        exc[m] = np.where(ev[m] >= 0, pnl[m] - np.nan_to_num(bl[np.clip(ev[m], 0, 80)]), 0)
    cands["GA-A nested (stitched outer folds)"] = (st, exc, "GA", "NONE (no simple same-family control: structural simple controls T46_21)")
    # ML-A (walk-forward) models: daily P&L of taken events
    E = pd.read_parquet(os.path.join(C.T46, "ml", "mlA_event_pool.parquet"))
    ML = pd.read_csv(os.path.join(C.T46, "ml", "T46_23_ml_walkforward.csv"))
    from t46_06_ml import wf, models
    Z = models(); feats = [c for c in E.columns if c.startswith("f_")]
    ctrl = np.zeros(n)
    for _, r in E[E.year >= 2021].iterrows():
        ctrl[int(r.s)] += r.pnl
    cands["ML-A simple control (take every broad event)"] = (ctrl, ctrl * 0, "DET", None)
    for mname in ("RIDGE", "ELASTIC_NET", "LOGISTIC", "EXTRA_TREES"):
        pred = wf(E, feats, mname, Z)
        pnl = np.zeros(n)
        for (_, r), p in zip(E.iterrows(), pred):
            if not np.isnan(p) and p > 0:
                pnl[int(r.s)] += r.pnl
        # threshold neighbourhood (G7 for ML): take p > q for q in +/- 0.25 std of predictions
        sd = np.nanstd(pred); neigh = []
        for q in (-0.25 * sd, -0.1 * sd, 0.1 * sd, 0.25 * sd):
            t = E[(~np.isnan(pred)) & (pred > q)]
            neigh.append(float(t.pnl.sum()))
        cands[f"ML-A {mname}"] = (pnl, pnl * 0, "ML", neigh)
    rows = []
    for nm, (pnl, exc, rung, extra) in cands.items():
        m = span
        bs = block_stats(pnl, sess)
        cb = comb(pnl, champ, m)
        tr = pnl[m][pnl[m] != 0]; top = np.sort(tr)[::-1]
        o = {"candidate": nm, "rung": rung, **{f"blk_{k}": v for k, v in bs.items()}, "blk_median": float(np.median(list(bs.values()))),
             "blk_pos": int(sum(v > 0 for v in bs.values())), "incr_avg": float(pnl[m].mean()), "total": float(pnl[m].sum()),
             "remove_top3": float(tr.sum() - top[:3].sum()) if len(top) >= 3 else np.nan, **cb}
        o["matched_excess_day"] = float(exc[m].mean()) if rung == "GA" else np.nan
        o["G1"] = o["blk_median"] > 0 and o["blk_pos"] >= 4
        o["G2"] = (o["matched_excess_day"] > 0) if rung == "GA" else bool(o["total"] > 0)      # ML/DET: excess approximated by net vs zero-beta (intraday, flat overnight)
        o["G3"] = o["comb_mdd"] <= 15000 and o["comb_worst"] >= -3000 and o["comb_ret_dd"] >= o["C43_ret_dd"]
        o["G4"] = (o["remove_top3"] or -1) > 0
        o["G5"] = o["incr_avg"] >= 5 and abs(o["corr"]) <= 0.5
        ctrl_total = float(ctrl[m].sum())
        o["G6"] = o["total"] > ctrl_total if nm != "ML-A simple control (take every broad event)" else True
        if rung == "ML":
            o["G7"] = bool(all(v > 0 for v in extra)); o["threshold_neighbourhood_totals"] = json.dumps([round(v) for v in extra])
        elif rung == "GA":
            o["G7"] = False; o["threshold_neighbourhood_totals"] = "outer generalisation failed; plateau not established"
        else:
            o["G7"] = True
        o["G8"] = True
        o["ELIGIBLE"] = all(o[f"G{i}"] for i in range(1, 9))
        rows.append(o)
    R = pd.DataFrame(rows)
    R.to_csv(f"{OUT}/T46_36_incremental_gate.csv", index=False)
    el = R[R.ELIGIBLE]
    final = el.sort_values("rung").iloc[0].candidate if len(el) else "NONE"
    json.dump({"FINAL_TEST46_CHALLENGER": final, "n_candidates": len(R), "n_eligible": int(R.ELIGIBLE.sum()),
               "lane_A": "all INDEX6 seeds PARITY_BLOCKED -> ineligible by G8 (research-only)",
               "gp": "not run: GA outer generalisation failed and tree ML did not beat linear ML (GP not justified)"},
              open(f"{OUT}/T46_38_final_selection.json", "w"), indent=1)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(R.round(3).to_string()); print("FINAL", final)


if __name__ == "__main__":
    main()
