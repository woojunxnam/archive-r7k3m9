"""TEST50 simple compression -> expansion grid + nulls, exactly as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
import t49_engine as T49  # noqa: E402
import t50_engine as V  # noqa: E402
from t47_02_n3 import tstat  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test50"); os.makedirs(OUT, exist_ok=True)


def main():
    es, nq = E.setup()
    sess = es.pn.sess
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    comps = [("K1_RANGE", 3.0), ("K1_RANGE", 4.0), ("K1_RANGE", 5.0), ("K2_RVOL", 0.5), ("K2_RVOL", 0.7), ("K3_CONTRACTION", 0.35)]
    xs = ["X1_BOX_BREAK", "X2_EXP_BAR", "X3_HL_BREAK", "X4_BREAK_RETEST"]
    rows = []
    for mk in (es, nq):
        key = mk.year * 100 + mk.vt * 10 + mk.bull.astype(int)
        tabs = {}
        for rule in ("X120", "X1600", "X1615", "NEXTOPEN"):
            M = T49.overnight_base(mk, rule) if rule == "NEXTOPEN" else E.Baseline(mk).table(rule)[0]
            df = pd.DataFrame(M); df["key"] = key
            tabs[rule] = df.groupby("key").mean()
        cfgs = [(k, t, x) for k, t in comps for x in xs] + [("NONE", 0.0, "X2_EXP_BAR"), ("NONE", 0.0, "X3_HL_BREAK")] + [(k, t, "COMP_ONLY") for k, t in comps]
        for kt, kv, xt in cfgs:
            for stop in (True, False):
                for rule in ("X120", "X1600", "X1615", "NEXTOPEN"):
                    d, s, j, pnl, off = V.run(mk, kt, kv, 12, xt, stop_on=stop, rule=rule)
                    Gt = tabs[rule]
                    exc = pnl - Gt.values[Gt.index.get_indexer(key[s]), j]
                    xd = np.zeros(mk.n); np.add.at(xd, s + off, exc)
                    d4 = V.run(mk, kt, kv, 12, xt, stop_on=stop, rule=rule, slip=4.0)[0]
                    nm = f"{mk.inst}|{kt}{kv}|{xt}|stop{int(stop)}|{rule}"
                    o = P.evaluate_module(nm, d, xd, sess, champ, {"stress4_pos": bool(d4[sess >= P.SPAN21].sum() > 0), "plateau_pass": False})
                    m21 = sess[s] >= P.SPAN21
                    o.update({"inst": mk.inst, "comp": f"{kt}{kv}", "exp": xt, "stop": stop, "exit": rule, "trades_2021": int(m21.sum()),
                              "avg_trade": float(np.mean(pnl)) if len(pnl) else np.nan, "excess_trade": float(np.mean(exc)) if len(exc) else np.nan,
                              "t_excess": tstat(exc) if len(exc) > 5 else np.nan, "t_excess_2021": tstat(exc[m21]) if m21.sum() > 5 else np.nan})
                    rows.append(o)
        print(mk.inst, "done", flush=True)
    R = pd.DataFrame(rows)
    thr = np.where(R.inst == "MNQ", 3.5, 3.0)
    R["finalist"] = (R.t_excess >= thr) & R.PASS
    R.to_csv(f"{OUT}/T50_grid.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 500)
    cols = ["inst", "comp", "exp", "stop", "exit", "trades_2021", "avg_trade", "excess_trade", "t_excess", "standalone_avg_day", "matched_excess_day",
            "folds_pos", "fold_median", "corr_C43", "comb_worst_day", "PASS"]
    prim = R[(R.exit == "X1600") & (R.stop)]
    print(prim[cols].round(2).to_string())
    print(R.sort_values("t_excess", ascending=False)[cols].head(25).round(2).to_string())
    # compression-information test: best compression version vs no-compression null (same expansion, X1600, stop)
    print(R[(R.exit == "X1600") & (R.stop)].groupby(["inst", "exp"])[["matched_excess_day", "t_excess"]].agg(["max", "mean"]).round(2))
    print("finalists", int(R.finalist.sum()), "PASS", int(R.PASS.sum()))
    P.budget("TEST50", hypotheses=len(R), finalists=int(R.finalist.sum()), note="simple compression->expansion grid")


if __name__ == "__main__":
    main()
