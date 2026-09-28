"""TEST69 - ES pre-FOMC announcement drift (scheduled FOMC statement days), additive module to T61-R1C."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t65_common as K  # noqa: E402
import t45_common as C45  # noqa: E402
import t47_engine as E  # noqa: E402

FOMC = ["2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
        "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
        "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
        "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
        "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29"]

SPEC = {
    "question": "Does the documented pre-FOMC announcement drift in the S&P 500 (ES-specific event information) add to T61-R1C as a 2-MES intraday module?",
    "mechanism": "risk-premium resolution / dealer positioning ahead of scheduled 14:00 ET statements (Lucca-Moench); event calendar is public and known in advance",
    "events": "scheduled FOMC statement days 2019-07..2026-05 (emergency 2020-03-03 / 2020-03-15 excluded); list hard-coded in t69_run.FOMC",
    "primary_E69": {"entry": "09:31 open fill (j=0) on the FOMC day", "exit": "fill at the open of the 13:55 minute (before the 14:00 statement)", "size": "2 MES",
                    "no filters": True},
    "plateau_neighbours": ["entry 10:00", "exit 13:30", "exit 13:58", "entry prior-session 15:00 (held overnight into the FOMC day)"],
    "report_only": ["MNQ 1 lot version", "post-statement 14:05 -> 16:15 (no hypothesis; diagnostic)"],
    "gate": "TEST65+ incremental gate",
    "budget": {"hypotheses": 5},
    "prior_risk": "only ~54 events (~7/yr); low $/day by construction; published anomaly with reported decay after 2016",
}


def sig(sess, j_in=0, exit_t="13:55", prev_day=False, j_prev=None):
    ix = pd.Index(sess).get_indexer(pd.DatetimeIndex(FOMC)); jo = C45.g(exit_t) + 1; rows = []
    for s in ix:
        if s < 0 or sess[s] < K.START:
            continue
        rows.append((s - 1, j_prev, s, jo) if prev_day else (s, j_in, s, jo))
    return pd.DataFrame(rows, columns=["s", "j_in", "s_out", "j_out"])


def main():
    import t65_mod as M
    env = M.Env(); sess = env.X.sess
    j10 = C45.g("10:00") + 1; j15 = C45.g("15:00") + 1
    neigh = [sig(sess, j_in=j10), sig(sess, exit_t="13:30"), sig(sess, exit_t="13:58"), sig(sess, prev_day=True, j_prev=j15)]
    rows = []
    o, d, L = M.evaluate_multi(env, "E69_PRE_FOMC_MES2", sig(sess), "ES", 2, neigh); rows.append(o)
    o2, d2, _ = M.evaluate_multi(env, "E69r_PRE_FOMC_MNQ1", sig(sess), "MNQ", 1); rows.append(o2)
    post = sig(sess); post["j_in"] = C45.g("14:05") + 1; post["j_out"] = E.J1615
    o3, d3, _ = M.evaluate_multi(env, "E69r_POST_STATEMENT_MES2", post, "ES", 2); rows.append(o3)
    R = pd.DataFrame(rows); out = os.path.join(C45.ROOT, "out", "test69")
    R.to_csv(os.path.join(out, "T69_results.csv"), index=False); np.savez_compressed(os.path.join(out, "T69_daily.npz"), E69=d, mnq=d2, post=d3)
    yr = pd.Series(d[env.full], index=sess[env.full]).groupby(sess[env.full].year).sum()
    pd.set_option("display.width", 250); print(R.T.to_string()); print(len(L), yr.round(0).to_dict())
    K.reg_append("T61_INCREMENTAL_PORTFOLIO_FRONTIER", [{"test": "TEST69", "module": r.module, "incr_avg_day": r.incr_avg_day, "comb_avg_day": r.comb_avg_day, "comb_maxdd": r.comb_maxdd,
                                                        "comb_worst": r.comb_worst, "comb_ret_dd": r.comb_ret_dd, "corr_to_t61": r.corr_to_t61, "PASS": r.PASS} for r in R.itertuples()], key="module")
    K.md("TEST69_PRE_FOMC.md", "TEST69 - ES pre-FOMC drift vs T61-R1C", [R.T, "year $: " + str(yr.round(0).to_dict())])


if __name__ == "__main__":
    if sys.argv[1:] == ["prereg"]:
        print(K.prereg("TEST69", SPEC))
    else:
        main()
