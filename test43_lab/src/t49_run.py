"""TEST49 simple continuation grid, exactly as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
import t49_engine as T  # noqa: E402
from t47_02_n3 import tstat  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test49"); os.makedirs(OUT, exist_ok=True)


def matched(mk, s, j, pnl, rule, key):
    if rule in ("NEXTOPEN", "NEXT1000"):
        M = T.overnight_base(mk, rule)
    else:
        M = E.Baseline(mk).table(rule)[0]
    df = pd.DataFrame(M); df["key"] = key
    G = df.groupby("key").mean()
    base = G.values[G.index.get_indexer(key[s]), j]
    return pnl - base


def main():
    es, nq = E.setup()
    sess = es.pn.sess
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    rows = []
    variants = [("T1_OPENING_DRIVE", {"t": "10:00", "k": 0.25}), ("T1_OPENING_DRIVE", {"t": "10:00", "k": 0.5}), ("T1_OPENING_DRIVE", {"t": "10:30", "k": 0.25}),
                ("T1_OPENING_DRIVE", {"t": "10:30", "k": 0.5}), ("T2_TREND_DAY", {}), ("T3_LATE_STRENGTH", {"t": "14:30"}), ("T3_LATE_STRENGTH", {"t": "15:00"}),
                ("T5_BREAKOUT_RETENTION", {})]
    for mk in (es, nq):
        st = T.State(mk)
        key = mk.year * 100 + mk.vt * 10 + mk.bull.astype(int)
        for fam, p in variants:
            b = T.family_entries(st, fam, **p)
            ej = np.where(b >= 0, 5 * (b + 1), -1); ej = np.where(ej <= E.J_LAST_ENTRY, ej, -1)
            for rule in ("X1600", "X1615", "NEXTOPEN", "NEXT1000"):
                d, s, j, pnl, so = T.trades(mk, ej, rule)
                exc = matched(mk, s, j, pnl, rule, key)
                xd = np.zeros(mk.n); np.add.at(xd, so, exc)
                d4 = T.trades(mk, ej, rule, slip=4.0)[0]
                nm = f"{mk.inst}|{fam}|{p}|{rule}"
                o = P.evaluate_module(nm, d, xd, sess, champ, {"stress4_pos": bool(d4[sess >= P.SPAN21].sum() > 0), "plateau_pass": False})
                m21 = sess[s] >= P.SPAN21
                o.update({"inst": mk.inst, "family": fam, "variant": str(p), "exit": rule, "trades_2021": int(m21.sum()), "avg_trade": float(np.mean(pnl)),
                          "excess_trade": float(np.mean(exc)), "t_excess": tstat(exc), "t_excess_2021": tstat(exc[m21])})
                rows.append(o)
        # T4 close-strength carry (decision 16:14 -> fill 16:15 -> next open / next 10:00), plus the unconditional-carry control
        cs, ret, pos = T.close_strength(st)
        for nm_, sel in (("T4_CLOSE_STRENGTH_CARRY", cs), ("CONTROL_UNCONDITIONAL_CARRY", st.valid.copy())):
            ej = np.where(sel, E.J1615, -1)
            for rule in ("NEXTOPEN", "NEXT1000"):
                d, s, j, pnl, so = T.trades(mk, ej, rule)
                exc = matched(mk, s, j, pnl, rule, key)
                xd = np.zeros(mk.n); np.add.at(xd, so, exc)
                d4 = T.trades(mk, ej, rule, slip=4.0)[0]
                o = P.evaluate_module(f"{mk.inst}|{nm_}|{rule}", d, xd, sess, champ, {"stress4_pos": bool(d4[sess >= P.SPAN21].sum() > 0), "plateau_pass": False})
                m21 = sess[s] >= P.SPAN21
                o.update({"inst": mk.inst, "family": nm_, "variant": "", "exit": rule, "trades_2021": int(m21.sum()), "avg_trade": float(np.mean(pnl)),
                          "excess_trade": float(np.mean(exc)), "t_excess": tstat(exc), "t_excess_2021": tstat(exc[m21])})
                rows.append(o)
        print(mk.inst, "done", flush=True)
    R = pd.DataFrame(rows)
    thr = np.where(R.family == "T5_BREAKOUT_RETENTION", 3.5, 3.0)
    R["finalist"] = (R.t_excess >= thr) & R.PASS
    R.to_csv(f"{OUT}/T49_grid.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    cols = ["inst", "family", "variant", "exit", "trades_2021", "avg_trade", "excess_trade", "t_excess", "t_excess_2021", "standalone_avg_day", "matched_excess_day",
            "folds_pos", "fold_median", "corr_C43", "comb_worst_day", "G4", "G8", "PASS"]
    print(R[cols].round(2).to_string())
    print("finalists", int(R.finalist.sum()), "PASS", int(R.PASS.sum()))
    P.budget("TEST49", hypotheses=len(R), finalists=int(R.finalist.sum()), note="simple continuation grid")


if __name__ == "__main__":
    main()
