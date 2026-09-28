"""ALPHA_GAP_MAP_V2: under/over-exposure events of C43-CORE and C43-GROWTH (TEST55 architecture) at the daily-open decision.
Research labels only; feature contrasts computed on the DISCOVERY region (2019-07..2020-12) to keep outer folds blind; event catalogues
cover the full history for description."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t60_run import feats  # noqa: E402

if __name__ == "__main__":
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = es.pn.sess
    pE, pM = P.c43_positions(sess)
    z = np.load(os.path.join(C45.ROOT, "out/test55/T55_primary_daily.npz")); cnt = z["cnt"]
    ratio = bk.atr_d["MNQ"] / bk.atr_d["ES"]
    uC = np.nan_to_num(pE[:, 1]) + np.nan_to_num(pM[:, 1]) * ratio                      # MES-eq units at 09:32
    uG = uC + cnt[:, 60:].mean(1) * ratio                                                  # growth: + avg intraday ensemble MNQ
    fwd = 0.5 * (es.FPb[:, E.J1615] - es.FP[:, 0]) * es.pv + 0.5 * (nq.FPb[:, E.J1615] - nq.FP[:, 0]) * nq.pv / ratio   # per MES-eq unit RTH
    D = pd.DataFrame({"date": sess, "units_C43": uC, "units_GROWTH": uG, "fwd_rth_per_unit": fwd})
    F = pd.concat([feats(es, "es"), feats(nq, "nq")], axis=1)
    D = pd.concat([D, F.reset_index(drop=True)], axis=1)
    D = D[sess >= H.START].reset_index(drop=True)
    hi, lo = D.fwd_rth_per_unit.quantile(0.9), D.fwd_rth_per_unit.quantile(0.1)
    D["UNDEREXPOSURE"] = (D.fwd_rth_per_unit >= hi) & (D.units_GROWTH <= D.units_GROWTH.quantile(0.25))
    D["OVEREXPOSURE"] = (D.fwd_rth_per_unit <= lo) & (D.units_GROWTH >= D.units_GROWTH.quantile(0.75))
    D[D.UNDEREXPOSURE].to_parquet(f"{H.HX}/UNDEREXPOSURE_EVENTS.parquet"); D[D.OVEREXPOSURE].to_parquet(f"{H.HX}/OVEREXPOSURE_EVENTS.parquet")
    disc = D[D.date <= P.DISC[1]]
    fc = [c for c in F.columns]
    con = pd.DataFrame({"under_mean": disc[disc.UNDEREXPOSURE][fc].mean(), "over_mean": disc[disc.OVEREXPOSURE][fc].mean(), "all_mean": disc[fc].mean(),
                        "all_std": disc[fc].std()})
    con["under_z"] = (con.under_mean - con.all_mean) / con.all_std; con["over_z"] = (con.over_mean - con.all_mean) / con.all_std
    con.to_csv(f"{H.HX}/ALPHA_GAP_MAP_V2_state_contrast_discovery.csv")
    summ = D.groupby(D.date.dt.year).agg(days=("date", "size"), under=("UNDEREXPOSURE", "sum"), over=("OVEREXPOSURE", "sum"),
                                         avg_units_C43=("units_C43", "mean"), avg_units_G=("units_GROWTH", "mean"))
    summ.to_csv(f"{H.HX}/ALPHA_GAP_MAP_V2.csv")
    print(summ); print(con.sort_values("under_z").round(2).to_string())
