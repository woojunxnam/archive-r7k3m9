"""TEST67 - ES-specific structural-flow alpha: turn-of-month (TOM) long MES, as an additive module to T61-R1C."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402

SPEC = {
    "question": "Does an ES-specific calendar-flow mechanism (turn-of-month: month-end / new-month cash inflows into S&P 500 index funds, "
                "pension rebalancing, 401k contributions) add independent return to T61-R1C when traded as a 2-MES module?",
    "why_ES_specific": "flows are benchmarked to the S&P 500 (ES), not ported from an MNQ rule; information = calendar (not price state), so it is "
                       "neither C43 exposure timing nor an unconditional overnight carry (holds only across the TOM window)",
    "primary_E67_TOM": {"entry": "09:31 open fill (grid j=0) of the LAST trading session of the month (td=-1)", "exit": "16:15 close fill of the 3rd trading "
                        "session of the new month (td=+3)", "hold": "overnight across the window, close-to-close MTM", "size": "2 MES (ATR$ ~ 1 MNQ lot); total MES <= 8",
                        "no filters": True},
    "plateau_neighbours": ["entry td=-2", "entry td=+1 (first session)", "exit td=+2", "exit td=+4"],
    "report_only": ["intraday-only TOM (each TOM session 09:31 -> 16:15)", "MNQ version (1 MNQ, T61 priority)"],
    "gate": "TEST65+ incremental gate (TEST65 prereg): all items incl. matched-beta excess (same year x vol tercile x bull, same holding length), SLIP4, "
            "+1 bar delay, plateau, regime / year share, folds, risk",
    "budget": {"hypotheses": 5},
    "prior_risk": "well-known anomaly (possible decay post-publication); 2020 crash overlap; multi-day holds raise worst-day tail",
}


def tom_signals(sess, td_in=-1, td_out=3, j_in=0, j_out=None):
    j_out = E.J1615 if j_out is None else j_out
    m = sess.to_period("M"); n = len(sess)
    first = np.r_[True, m[1:] != m[:-1]]
    firsts = np.where(first)[0]; rows = []
    for f in firsts[1:]:
        si = f + td_in if td_in < 0 else f + td_in - 1
        so = f + td_out - 1
        if si < 0 or so >= n or sess[si] < K.START:
            continue
        rows.append((si, j_in, so, j_out))
    return pd.DataFrame(rows, columns=["s", "j_in", "s_out", "j_out"])


def main():
    import t65_mod as M
    env = M.Env(); X = env.X; sess = X.sess
    neigh = [tom_signals(sess, td_in=-2), tom_signals(sess, td_in=1), tom_signals(sess, td_out=2), tom_signals(sess, td_out=4)]
    rows = []; daily = {}
    o, d, L = M.evaluate_multi(env, "E67_TOM_MES2", tom_signals(sess), "ES", 2, neigh); rows.append(o); daily["E67"] = d
    # report-only
    intr = pd.concat([tom_signals(sess, td_in=k, td_out=k if k > 0 else 0) for k in (-1,)] + [], ignore_index=True)
    intr = []
    base = tom_signals(sess)
    for r in base.itertuples(index=False):
        for s in range(r.s, r.s_out + 1):
            intr.append((s, 0, s, E.J1615))
    o2, d2, _ = M.evaluate_multi(env, "E67r_TOM_INTRADAY_ONLY_MES2", pd.DataFrame(intr, columns=["s", "j_in", "s_out", "j_out"]), "ES", 2); rows.append(o2)
    o3, d3, _ = M.evaluate_multi(env, "E67r_TOM_MNQ1", base, "MNQ", 1); rows.append(o3)
    R = pd.DataFrame(rows); out = os.path.join(C45.ROOT, "out", "test67")
    R.to_csv(os.path.join(out, "T67_results.csv"), index=False); np.savez_compressed(os.path.join(out, "T67_daily.npz"), E67=d, intraday=d2, mnq=d3)
    yr = pd.Series(d[env.full], index=sess[env.full]).groupby(sess[env.full].year).sum()
    pd.set_option("display.width", 250); print(R.T.to_string()); print(yr.round(0).to_dict())
    K.reg_append("T61_INCREMENTAL_PORTFOLIO_FRONTIER", [{"test": "TEST67", "module": r.module, "incr_avg_day": r.incr_avg_day, "comb_avg_day": r.comb_avg_day, "comb_maxdd": r.comb_maxdd,
                                                        "comb_worst": r.comb_worst, "comb_ret_dd": r.comb_ret_dd, "corr_to_t61": r.corr_to_t61, "PASS": r.PASS} for r in R.itertuples()], key="module")
    K.md("TEST67_ES_TURN_OF_MONTH.md", "TEST67 - ES turn-of-month flow module vs T61-R1C", [R.T, "year $:", str(yr.round(0).to_dict())])


if __name__ == "__main__":
    if sys.argv[1:] == ["prereg"]:
        print(K.prereg("TEST67", SPEC))
    else:
        main()
