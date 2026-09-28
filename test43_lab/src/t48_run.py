"""TEST48 simple ARM -> CONFIRM grid (5 setups x 6 confirmations x 3 exits x 2 instruments), exactly as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
import t48_engine as A  # noqa: E402
from t47_02_n3 import tstat  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test48"); os.makedirs(OUT, exist_ok=True)


def main():
    es, nq = E.setup()
    sess = es.pn.sess
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    rows = []; daily = {}
    for mk in (es, nq):
        ab = A.ArmBook(mk); bl = E.Baseline(mk)
        for st in A.SETUPS:
            for cf in A.CONFS:
                ent = A.entries(ab, st, cf)
                for ex in ("X60", "X120", "X1600"):
                    d, s, j, pnl = A.trade_daily(mk, ent, ex)
                    T = pd.DataFrame({"s": s, "j": j, "pnl": pnl})
                    exc, _ = bl.excess(T, ex)
                    xd = np.zeros(mk.n); xd[s] = exc
                    d4 = A.trade_daily(mk, ent, ex, slip=4.0)[0]
                    name = f"{mk.inst}|{st}|{cf}|{ex}"
                    o = P.evaluate_module(name, d, xd, sess, champ, {"stress4_pos": bool(d4[sess >= P.SPAN21].sum() > 0), "plateau_pass": False})
                    m21 = sess[s] >= P.SPAN21
                    o.update({"inst": mk.inst, "setup": st, "conf": cf, "exit": ex, "trades": len(s), "trades_2021": int(m21.sum()),
                              "avg_trade": float(pnl.mean()) if len(pnl) else np.nan, "excess_trade": float(exc.mean()) if len(exc) else np.nan,
                              "t_excess": tstat(exc) if len(exc) > 5 else np.nan, "t_excess_2021": tstat(exc[m21]) if m21.sum() > 5 else np.nan})
                    rows.append(o); daily[name] = d
        print(mk.inst, "done", flush=True)
    R = pd.DataFrame(rows)
    # delayed - immediate (same setup, exit, instrument) on matched excess per trade and $/day
    imm = R[R.conf == "CF0_IMMEDIATE"].set_index(["inst", "setup", "exit"])
    R["delta_excess_day_vs_immediate"] = R.matched_excess_day - imm.matched_excess_day.reindex(pd.MultiIndex.from_frame(R[["inst", "setup", "exit"]])).values
    R["delta_avg_day_vs_immediate"] = R.standalone_avg_day - imm.standalone_avg_day.reindex(pd.MultiIndex.from_frame(R[["inst", "setup", "exit"]])).values
    R["finalist"] = (R.t_excess >= 3.0) & R.PASS
    R.to_csv(f"{OUT}/T48_grid.csv", index=False)
    np.savez_compressed(f"{OUT}/T48_grid_daily.npz", **{k.replace("|", "__"): v for k, v in daily.items()})
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 400)
    cols = ["inst", "setup", "conf", "exit", "trades_2021", "avg_trade", "excess_trade", "t_excess", "t_excess_2021", "matched_excess_day",
            "folds_pos", "fold_median", "delta_excess_day_vs_immediate", "corr_C43", "PASS"]
    print(R[R.exit == "X120"][cols].round(2).to_string())
    print(R.sort_values("t_excess", ascending=False)[cols].head(20).round(2).to_string())
    print("finalists", int(R.finalist.sum()), "PASS", int(R.PASS.sum()))
    print(R.groupby(["conf"])[["delta_excess_day_vs_immediate"]].agg(["mean", "median", lambda x: (x > 0).mean()]).round(3))
    P.budget("TEST48", hypotheses=180, finalists=int(R.finalist.sum()), note="simple ARM->CONFIRM grid")


if __name__ == "__main__":
    main()
