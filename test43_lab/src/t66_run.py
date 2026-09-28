"""TEST66 - early opening-trend participation (TEST65 pick MISSED_OPENING_TREND).  Preregistration written first (python t66_run.py prereg)."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import t45_common as C45  # noqa: E402

SPEC = {
    "question": "Does an EARLY (09:35-09:45, no 15m wait) opening-trend MNQ entry, taken only while T61-R1C is under-exposed, add to T61-R1C?",
    "mechanism": "TEST65: T61 is under-exposed (u<3) in 290 strong opening-hour trends; clean-forward detectability AUC 0.58 at 09:35 (5/5 folds). "
                 "Opening order-flow imbalance persists for the first hour; C43 needs 3m bars + deadband and TEST53-M4 waits until 10:00.",
    "difference_from_rejected": "not a gap / flush / VWAP rebound, not a breakout of a compression box, not exposure timing of C43: a separate 1-lot MNQ module "
                                "gated by early directional efficiency and ES confirmation, exit at the end of the opening hour (distinct from M4: 10:00 -> 16:15)",
    "primary_rule_E66": {"decision": "bars ending 09:31..09:40 complete (grid j=10), fill at the 09:40-09:41 open", "ret_since_open_MNQ": ">= 0.15 ATR_d",
                         "path_efficiency_since_open": ">= 0.5", "ES_confirm": "ES ret since open > 0", "T61_u_at_decision": "< 3",
                         "exit": "10:30 (open of the minute after the 10:30 bar)", "size": "1 MNQ; skipped / cut at the same fill when T61 MNQ + 1 > 6"},
    "plateau_neighbours": ["j=5 (09:35)", "j=15 (09:45)", "k=0.10", "k=0.20", "eff=0.4", "eff=0.6", "exit 11:00", "exit entry+60m"],
    "ml_meta_labeler_E66ML": "one config: L2 logistic on the 14 TEST65 features at 09:35, label = TEST65 clean-forward strong W1 move, walk-forward outer folds "
                             "(train < fold), trade if p >= 70th pct of training p AND ret_since_open > 0 AND T61 u < 3; exit 10:30; 2021+ only (nested)",
    "gate": "TEST65+ incremental gate (TEST65 prereg) on each of E66 and E66ML separately; no post-hoc rescue",
    "budget": {"hypotheses": 10, "ml_configs": 1},
}


def rule(X, j=10, k=0.15, eff=0.5, exit_j=None, exit_rel=None):
    rows = []; jx0 = C45.g("10:30") + 1 if exit_j is None else exit_j
    for s in np.where(np.asarray(X.sess >= K.START))[0]:
        if np.isnan(X.atr["MNQ"][s]) or np.isnan(X.o0["MNQ"][s]):
            continue
        f = dict(zip(("r", "re", "_", "_", "_", "eff"), X.feats(s, j)[:6])); u = X.u[s, j - 1]
        if f["r"] >= k and f["eff"] >= eff and f["re"] > 0 and u < 3:
            rows.append((s, j, s, j + exit_rel if exit_rel else jx0))
    return pd.DataFrame(rows, columns=["s", "j_in", "s_out", "j_out"])


def ml_signals(X):
    import t65_run as R  # noqa: F401
    W = pd.read_parquet(os.path.join(C45.ROOT, "out", "test65", "T65_window_labels.parquet"))
    W = W[W.window == "W1_0930_1030"].dropna(subset=R.FEATS + ["fwd_strongN"]).reset_index(drop=True)
    s_of = pd.Index(X.sess).get_indexer(W.date); rows = []
    for nm, a, b in C45.OUTER[:5]:
        tr = (W.date < pd.Timestamp(a)).values; te = ((W.date >= pd.Timestamp(a)) & (W.date <= pd.Timestamp(b))).values
        sc = StandardScaler().fit(W.loc[tr, R.FEATS]); m = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(W.loc[tr, R.FEATS]), W.fwd_strongN[tr].astype(int))
        thr = np.quantile(m.predict_proba(sc.transform(W.loc[tr, R.FEATS]))[:, 1], 0.7)
        p = m.predict_proba(sc.transform(W.loc[te, R.FEATS]))[:, 1]
        for i, pp in zip(np.where(te)[0], p):
            if pp >= thr and W.ret_since_open_MNQ[i] > 0 and W.t61_exposure_u[i] < 3:
                rows.append((s_of[i], 5, s_of[i], C45.g("10:30") + 1))
    return pd.DataFrame(rows, columns=["s", "j_in", "s_out", "j_out"])


def main():
    import t65_mod as M
    env = M.Env(); X = env.X
    g11 = C45.g("11:00") + 1
    neigh = [rule(X, j=5), rule(X, j=15), rule(X, k=0.10), rule(X, k=0.20), rule(X, eff=0.4), rule(X, eff=0.6), rule(X, exit_j=g11), rule(X, exit_rel=60)]
    rows = []; daily = {}
    o, d = M.evaluate(env, "E66_EARLY_OPENING_TREND", rule(X), plateau=neigh); rows.append(o); daily["E66"] = d
    sml = ml_signals(X)
    o, d = M.evaluate(env, "E66ML_META_LABELER", sml, from21=True); rows.append(o); daily["E66ML"] = d
    R = pd.DataFrame(rows)
    out = os.path.join(C45.ROOT, "out", "test66"); R.to_csv(os.path.join(out, "T66_results.csv"), index=False)
    np.savez_compressed(os.path.join(out, "T66_daily.npz"), **daily)
    pd.set_option("display.width", 250); print(R.T.to_string())
    for _, r in R.iterrows():
        K.reg_append("T61_INCREMENTAL_PORTFOLIO_FRONTIER", [{"test": "TEST66", "module": r.module, "incr_avg_day": r.incr_avg_day, "comb_avg_day": r.comb_avg_day,
                                                            "comb_maxdd": r.comb_maxdd, "comb_worst": r.comb_worst, "comb_ret_dd": r.comb_ret_dd, "corr_to_t61": r.corr_to_t61,
                                                            "PASS": r.PASS}], key="module")
    K.md("TEST66_EARLY_OPENING_TREND.md", "TEST66 - early opening-trend participation vs T61-R1C", [R.T])
    return R


if __name__ == "__main__":
    if sys.argv[1:] == ["prereg"]:
        print(K.prereg("TEST66", SPEC))
    else:
        main()
