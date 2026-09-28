"""TEST68 - MNQ secondary session-high breakout (>= 60 min after the previous high, after 10:30), ML meta-labeled (TEST65 clue AUC 0.61 5/5)."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402

SPEC = {
    "question": "Is the first secondary MNQ session-high break (>= 60 min after the previous high, 10:30-16:00) a detectable continuation that adds to T61-R1C once meta-labeled?",
    "mechanism": "late re-acceptance of higher prices after a >= 1h consolidation below the session high (stops above the high + trend-follower re-entry); "
                 "TEST65 clean-forward AUC 0.61 in 5/5 folds on these triggers; T61 is under-exposed at many of them",
    "difference_from_rejected": "not a compression-box breakout (no range/rvol quietness condition), not trend-state-to-close thresholds: a single structural "
                                "event (second high) with an out-of-sample meta-label; entry at the next 1m open after the break (no 15m wait)",
    "primary_E68ML": {"triggers": "TEST65 NQ_SECONDARY_BREAKOUT event rows (features at the break minute)", "model": "L2 logistic (C=1), 14 TEST65 features, label = fwd to 16:15 >= 0.3 ATR_d",
                      "walk_forward": "train on triggers before each outer fold (>= 2019-07-01), score the fold", "trade": "p >= 70th pct of training p",
                      "exit": "16:15", "size": "1 MNQ, T61 priority cut at the same fill", "span": "2021+ (nested outer only)"},
    "plateau_neighbours": ["p >= 60th pct", "p >= 80th pct", "exit 16:00", "label threshold 0.2 ATR_d"],
    "report_only": "unfiltered trigger (all breaks)",
    "gate": "TEST65+ incremental gate",
    "budget": {"hypotheses": 6, "ml_configs": 4},
}


def signals(EV, q=0.7, thr=0.3, exit_j=None):
    import t65_run as R
    exit_j = E.J1615 if exit_j is None else exit_j
    d = EV[EV.cat == "NQ_SECONDARY_BREAKOUT"].dropna(subset=R.FEATS).reset_index(drop=True)
    y = (d.fwd >= thr).astype(int).values; rows = []
    for nm, a, b in C45.OUTER[:5]:
        tr = (d.date < pd.Timestamp(a)).values; te = ((d.date >= pd.Timestamp(a)) & (d.date <= pd.Timestamp(b))).values
        sc = StandardScaler().fit(d.loc[tr, R.FEATS]); m = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(d.loc[tr, R.FEATS]), y[tr])
        t = np.quantile(m.predict_proba(sc.transform(d.loc[tr, R.FEATS]))[:, 1], q)
        p = m.predict_proba(sc.transform(d.loc[te, R.FEATS]))[:, 1]
        for i, pp in zip(np.where(te)[0], p):
            if pp >= t and d.j[i] < exit_j:
                rows.append((int(d.s[i]), int(d.j[i]), int(d.s[i]), exit_j))
    return pd.DataFrame(rows, columns=["s", "j_in", "s_out", "j_out"])


def main():
    import t65_mod as M
    env = M.Env()
    EV = pd.read_parquet(os.path.join(C45.ROOT, "out", "test65", "T65_event_labels.parquet"))
    neigh = [signals(EV, q=0.6), signals(EV, q=0.8), signals(EV, exit_j=E.J1600), signals(EV, thr=0.2)]
    rows = []
    o, d = M.evaluate(env, "E68ML_SECONDARY_BREAKOUT", signals(EV), plateau=neigh, from21=True); rows.append(o)
    allb = EV[(EV.cat == "NQ_SECONDARY_BREAKOUT") & (EV.date >= K.S21)]
    o2, d2 = M.evaluate(env, "E68r_ALL_BREAKS", pd.DataFrame({"s": allb.s, "j_in": allb.j, "s_out": allb.s, "j_out": E.J1615}), from21=True); rows.append(o2)
    R = pd.DataFrame(rows); out = os.path.join(C45.ROOT, "out", "test68")
    R.to_csv(os.path.join(out, "T68_results.csv"), index=False); np.savez_compressed(os.path.join(out, "T68_daily.npz"), E68=d, allb=d2)
    pd.set_option("display.width", 250); print(R.T.to_string())
    K.reg_append("T61_INCREMENTAL_PORTFOLIO_FRONTIER", [{"test": "TEST68", "module": r.module, "incr_avg_day": r.incr_avg_day, "comb_avg_day": r.comb_avg_day, "comb_maxdd": r.comb_maxdd,
                                                        "comb_worst": r.comb_worst, "comb_ret_dd": r.comb_ret_dd, "corr_to_t61": r.corr_to_t61, "PASS": r.PASS} for r in R.itertuples()], key="module")
    K.md("TEST68_SECONDARY_BREAKOUT.md", "TEST68 - MNQ secondary session-high breakout (ML meta-label) vs T61-R1C", [R.T])


if __name__ == "__main__":
    if sys.argv[1:] == ["prereg"]:
        print(K.prereg("TEST68", SPEC))
    else:
        main()
