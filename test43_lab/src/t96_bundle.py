"""TEST96 Track D fixed synthesis P0-P3 (prereg 492152fd bundle rule): bundle = Stage-A mechanisms passing STANDALONE or DIVERSIFIER gate;
lots = max(1, round(median $ATR(MES) / median $ATR(micro))) on sessions < 2021-01-01.  Defined before portfolio P&L is opened."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import box_common as B, t65_common as K, t96_common as W
import t96_port as P


def lots_rule(Is, inst):
    pre = np.asarray(Is["ES"].sess < pd.Timestamp("2021-01-01")) & Is["ES"].full
    es = np.nanmedian(Is["ES"].atr[pre] * Is["ES"].pv); mi = np.nanmedian(Is[inst].atr[pre] * Is[inst].pv)
    return max(1, int(round(es / mi))), float(es), float(mi)


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]; main = ctx["main"]; full = Is["ES"].full; s21 = np.asarray(Is["ES"].sess >= K.S21)
    R = pd.read_csv(os.path.join(W.OUT, "PORT_STAGE_A.csv"))
    z = np.load(os.path.join(W.OUT, "PORT_STAGE_A_daily.npz"))
    out = {"bundle_rule": "Stage-A STANDALONE_PASS or DIVERSIFIER_PASS; lots by $ATR ratio pre-2021"}
    bund = {}
    for inst in ("YM", "RTY"):
        mem = R[(R.instrument == inst) & (R.STANDALONE_PASS | R.DIVERSIFIER_PASS)].module.tolist()
        L, es, mi = lots_rule(Is, inst)
        d = sum((L * z[m] for m in mem), np.zeros(len(main)))
        bund[inst] = d
        out[f"FIXED_{inst}_TRANSFER_BUNDLE"] = {"members": mem, "lots_each": L, "median_$ATR_MES_pre2021": es, f"median_$ATR_{inst}_micro_pre2021": mi}
    rows = []
    for name, add in (("P0_CURRENT_MAIN", 0), ("P1_MAIN+YM", bund["YM"]), ("P2_MAIN+RTY", bund["RTY"]), ("P3_MAIN+YM+RTY", bund["YM"] + bund["RTY"])):
        x = main + add; r = B.risk(x[full]); r21 = B.risk(x[s21])
        a = add if not np.isscalar(add) else np.zeros(len(main))
        rows.append({"portfolio": name, "avg_day": r["avg_day"], "incr_avg_day": float(a[full].mean()), "incr_avg_day_2021": float(a[s21].mean()),
                     "max_dd": r["max_dd"], "worst_day": r["worst_day"], "ret_dd": r["ret_dd"], "ret_dd_2021": r21["ret_dd"],
                     "corr_add_to_main": float(np.corrcoef(a[full], main[full])[0, 1]) if a[full].std() > 0 else np.nan})
    T = pd.DataFrame(rows); print(T.to_string()); print(json.dumps(out, indent=1))
    b = T.set_index("portfolio"); m0 = b.loc["P0_CURRENT_MAIN"]
    for p in ("P1_MAIN+YM", "P2_MAIN+RTY", "P3_MAIN+YM+RTY"):
        r = b.loc[p]
        out[p + "_PASS_PORTFOLIO"] = bool(r.incr_avg_day >= 10 and r.incr_avg_day_2021 >= 10 and r.ret_dd >= m0.ret_dd and r.max_dd <= 1.10 * m0.max_dd and r.worst_day >= -5000)
        out[p + "_PASS_DIVERSIFIER"] = bool(r.incr_avg_day >= 3 and r.ret_dd >= 1.05 * m0.ret_dd and r.max_dd <= 1.05 * m0.max_dd and r.worst_day >= -5000
                                            and abs(r.corr_add_to_main) <= 0.30)
    W.save("T96_D_PORTFOLIOS.json", {**out, "table": T.to_dict("records")})
    W.md("T96_D_PORTFOLIOS.md", "TEST96 Track D fixed synthesis P0-P3", [T, "```json\n" + json.dumps(out, indent=1) + "\n```"])
    print(json.dumps({k: v for k, v in out.items() if "PASS" in k}, indent=1))


if __name__ == "__main__":
    main()
