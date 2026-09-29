"""AUDIT 5: D7 frozen practical carrier + affected portfolios (prereg bcee7ee)."""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_ph4 as P4  # noqa: E402
import da_ph9 as P9  # noqa: E402
import rp_econ as EC  # noqa: E402
from fa_audit4 import allocate  # noqa: E402
from rp_p6 import control_tables  # noqa: E402
from rp_p9 import module_orders, stats  # noqa: E402

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, "out", "final_index_closure_audit_v1")
DA = os.path.join(LAB, "out", "index_discretionary_alpha_continuous_v1")


def main():
    c = EC.ctx(); w = c["win"]; yrs = c["sess"][w].year; mw = c["main"][w]; rm = EC.risk(mw)
    X = pd.read_parquet(os.path.join(DA, "ph4", "PH4_EXIT_DATASET.parquet")); D7 = X[(X["def"] == "D7") & (X.year >= 2021) & X.px_X1615.notna()].copy()
    D7["px_out"] = D7.px_X1615; D7["j_out"] = D7.jo_X1615.astype(int)
    out = {}
    for tag, kw in (("base", {}), ("slip4", {"slip4": True}), ("delay1", {"delay": True}), ("missed20", {"missed": True})):
        d, nt, co = P4.capacity_daily(D7, **kw); out[tag] = (d[w], nt, co)
    dw = out["base"][0]; r_ = EC.risk(dw); rc = EC.risk(mw + dw); top = np.sort(dw)[::-1]; fold = {k: float(dw[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in EC.FOLDS.items()}
    corr = float(np.corrcoef(dw, mw)[0, 1]); b5 = mw <= np.percentile(mw, 5)
    st = {"signals": len(D7), "trades_after_capacity": out["base"][1], "avg_day": r_["avg_day"], "slip4": float(out["slip4"][0].mean()), "delay1": float(out["delay1"][0].mean()),
          "missed20": float(out["missed20"][0].mean()), "remove_top3": float(dw.sum() - top[:3].sum()), "folds": fold, "folds_pos": int(sum(v > 0 for v in fold.values())),
          "y2022": float(dw[yrs == 2022].sum()), "max_dd": r_["max_dd"], "worst_day": r_["worst_day"], "corr_main": corr, "turnover_trades_per_day": out["base"][1] / w.sum(),
          "loss_jaccard": float(((dw < 0) & (mw < 0)).sum() / max(((dw < 0) | (mw < 0)).sum(), 1)), "d7_mean_on_main_bottom5": float(dw[b5].mean()),
          "comb_avg_day": rc["avg_day"], "comb_max_dd": rc["max_dd"], "comb_worst": rc["worst_day"], "comb_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"], "main_max_dd": rm["max_dd"], "main_worst": rm["worst_day"],
          "peaks": {k: int(v.max()) for k, v in out["base"][2].items()}}
    st["incr"] = rc["avg_day"] - rm["avg_day"]
    st["STRESS_PASS"] = bool(st["avg_day"] > 0 and st["slip4"] > 0 and st["delay1"] > 0 and st["missed20"] > 0 and st["remove_top3"] > 0 and st["folds_pos"] >= 3)
    st["ROUTE_B"] = bool(st["STRESS_PASS"] and st["incr"] >= 1.5 and abs(corr) <= 0.35 and rc["ret_dd"] >= 1.02 * rm["ret_dd"] and rc["max_dd"] <= 1.03 * rm["max_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
    st["ROUTE_C"] = bool(st["incr"] >= -0.5 and (rc["max_dd"] <= 0.95 * rm["max_dd"] or (mw + dw)[b5].mean() >= mw[b5].mean() + 0.05 * abs(mw[b5].mean())) and rc["ret_dd"] > rm["ret_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
    st["D7_PRACTICAL_CARRIER_STATUS"] = "D7_PRACTICAL_CARRIER_PASS (BETA/STRUCTURE CARRIER)" if (st["ROUTE_B"] or st["ROUTE_C"]) else "D7_PRACTICAL_CARRIER_FAIL"
    print(json.dumps(st, default=float), flush=True)
    # affected portfolio comparisons
    Tctl = control_tables(); base = module_orders("C2_P2_FAILED_FIRST", False, Tctl); a1, _ = P9.add_orders()
    d7o = [dict(mod="D7", key=f"D7#{k}", parent=None, date=int(r.date), inst=r.inst, j_in=int(5 * r.b + 5), j_out=int(r.j_out), px_in=r.entry, px_out=r.px_out, pv=r.pv, cs=r.cs, cs4=r.cs4, ctl=np.nan, year=int(r.year))
           for k, r in enumerate(D7.itertuples(index=False))]
    pf = {}; incs = {}
    for (cn, co_), use in itertools.product({"none": [], "C2": base, "C2+W1": base + a1}.items(), (False, True)):
        ords = list(co_) + (d7o if use else []); name = "+".join([x for x in (cn if cn != "none" else "", "D7" if use else "") if x]) or "MAIN_ONLY"
        if not ords:
            continue
        dcap, d4cap, cc, cnt = allocate(ords, True); s_ = stats(c["main"], dcap, d4cap, np.zeros_like(dcap), np.zeros_like(dcap), cc, [], c["occ"])
        pf[name] = {k: s_[k] for k in ("avg_day", "incr", "slip4_avg_day", "max_dd", "worst_day", "ret_dd", "corr_main_cand", "route_A", "route_B", "route_C", "per10k_dd", "risk_normalized_increment", "peak_MNQ", "peak_MES", "peak_MYM", "peak_M2K", "cand_margin_peak_approx")}
        incs[name] = dcap[w]; print(name, json.dumps(pf[name], default=float), flush=True)
    np.savez_compressed(os.path.join(OUT, "AUDIT5_PORTFOLIO_INCREMENTS.npz"), **{k.replace("+", "_"): v for k, v in incs.items()}, D7_ALONE=dw)
    json.dump({"D7": st, "portfolios": pf}, open(os.path.join(OUT, "AUDIT5_D7.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
