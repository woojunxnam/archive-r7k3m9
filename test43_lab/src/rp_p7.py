"""P7 strategy simulation / stress + routes (prereg 4d653cc)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_state as R  # noqa: E402

OUT = os.path.join(R.OUT, "p7"); os.makedirs(OUT, exist_ok=True)
CAND = {"C1_R1_TRAPPED_UNION": "A_TAKE_ALL", "C2_P2_FAILED_FIRST": "A_TAKE_ALL", "C4_L2_FAMILY": "C_GA", "C5_HTF1_30m": "A_TAKE_ALL", "C6_AV_OR30": "A_TAKE_ALL",
        "C7_L1_SWH60": "B_ML_NESTED"}
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K"}; CAP = {"MES": 8, "MNQ": 6, "MYM": 4, "M2K": 4}; MARGIN = {"MES": 1500, "MNQ": 2100, "MYM": 1000, "M2K": 800}
HB = {"h12": 12, "h24": 24}


def prep(T):
    M = P.markets(); T = T.copy(); T["hz"] = T["hz"].fillna("h1615") if "hz" in T else "h1615"
    T["j_in"] = 5 * T.b.values + 5; T["j_out"] = [404 if h == "h1615" else 5 * (b + 1 + HB[h]) for b, h in zip(T.b.values, T.hz.values)]
    T["px_in"] = T.entry.values; T["px_out"] = T.entry.values + T[[f"R_{h}" for h in ("h12", "h24", "h1615")]].values[np.arange(len(T)), [("h12", "h24", "h1615").index(h) for h in T.hz]] * T.atr.values
    T["px_in_d1"] = [M[i].I.FP[s, j + 5] for i, s, j in zip(T.inst, T.s, T.j_in)]
    return T.sort_values(["date", "j_in"]).reset_index(drop=True)


def main():
    c = EC.ctx(); win = c["win"]; mw = c["main"][win]; rm = EC.risk(mw); yrs = c["sess"][win].year
    res = []; D_out = {}
    for cand, arm in CAND.items():
        T = prep(pd.read_parquet(os.path.join(R.OUT, "p6", f"ARM_{cand}_{arm}.parquet")))
        out = {}
        for tag, kw in (("base", {}), ("slip4", {"slip4": True}), ("delay1", {"delay": 1}), ("missed20", {"missed": True})):
            # simulate and collect dates in the same order
            c_ = EC.ctx(); occ = {"MNQ": c_["occ"]["MNQ"].astype(np.int32).copy(), "MES": c_["occ"]["ES"].astype(np.int32).copy()}
            n = len(c_["sess"]); G = occ["MNQ"].shape[1]; co = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}
            d = np.zeros(n); k_ = 0; ntr = 0
            for r in T.itertuples(index=False):
                k_ += 1
                if kw.get("missed") and k_ % 5 == 0:
                    continue
                si = c_["pos"].get(int(r.date), -1)
                if si < 0:
                    continue
                ji = r.j_in + (5 if kw.get("delay") else 0); jo = r.j_out
                if ji >= jo:
                    continue
                mi = MICRO[r.inst]; base = occ[mi][si, ji:jo + 1] if mi in occ else 0
                if np.max(base + co[mi][si, ji:jo + 1]) + 1 > CAP[mi]:
                    continue
                co[mi][si, ji:jo + 1] += 1; ntr += 1
                pin = r.px_in_d1 if kw.get("delay") else r.px_in; cs = r.cs4 if kw.get("slip4") else r.cs
                d[si] += (r.px_out - pin) * r.pv - 2 * cs
            out[tag] = (d, ntr, co)
        d, ntr, co = out["base"]; dw = d[win]; r_ = EC.risk(dw); rc = EC.risk(mw + dw); top = np.sort(dw)[::-1]
        fold = {k: float(dw[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in EC.FOLDS.items()}
        occ_tot_N = (c["occ"]["MNQ"] + co["MNQ"]); occ_tot_E = (c["occ"]["ES"] + co["MES"])
        margin_peak = max(int(sum(MARGIN[k] * co[k][s].max(1) for k in co).max()) for s in [slice(None)])
        b5 = mw <= np.percentile(mw, 5); b5_main = mw[b5].mean(); b5_comb = (mw + dw)[b5].mean()
        corr = float(np.corrcoef(dw, mw)[0, 1])
        o = {"candidate": cand, "arm": arm, "trades_after_capacity": ntr, "trades_signal": len(T), "avg_day": r_["avg_day"], "slip4_avg_day": float(out["slip4"][0][win].mean()),
             "delay1_avg_day": float(out["delay1"][0][win].mean()), "missed20_avg_day": float(out["missed20"][0][win].mean()), "remove_top3": float(dw.sum() - top[:3].sum()),
             **{f"fold_{k}": v for k, v in fold.items()}, "folds_pos": int(sum(v > 0 for v in fold.values())), "y2022": float(dw[yrs == 2022].sum()),
             "max_dd": r_["max_dd"], "worst_day": r_["worst_day"], "corr_main": corr, "turnover_trades_per_day": ntr / win.sum(),
             **{f"peak_{k}": int(v.max()) for k, v in co.items()}, "peak_MNQ_total": int(occ_tot_N.max()), "peak_MES_total": int(occ_tot_E.max()), "margin_peak_approx": margin_peak,
             "main_avg_day": rm["avg_day"], "main_max_dd": rm["max_dd"], "main_worst": rm["worst_day"], "main_ret_dd": rm["ret_dd"],
             "comb_avg_day": rc["avg_day"], "comb_max_dd": rc["max_dd"], "comb_worst": rc["worst_day"], "comb_ret_dd": rc["ret_dd"], "bottom5_main": b5_main, "bottom5_comb": b5_comb}
        o["incr"] = o["comb_avg_day"] - o["main_avg_day"]
        o["STRESS_PASS"] = bool(o["avg_day"] > 0 and o["slip4_avg_day"] > 0 and o["delay1_avg_day"] > 0 and o["missed20_avg_day"] > 0 and o["remove_top3"] > 0 and o["folds_pos"] >= 3)
        o["ROUTE_A"] = bool(o["STRESS_PASS"] and o["incr"] >= 5 and rc["ret_dd"] >= rm["ret_dd"] and rc["max_dd"] <= 1.10 * rm["max_dd"] and rc["worst_day"] >= -5000)
        o["ROUTE_A_STRONG"] = bool(o["ROUTE_A"] and o["incr"] >= 10)
        o["ROUTE_B"] = bool(o["STRESS_PASS"] and o["incr"] >= 1.5 and abs(corr) <= 0.35 and rc["ret_dd"] >= 1.02 * rm["ret_dd"] and rc["max_dd"] <= 1.03 * rm["max_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
        o["ROUTE_C"] = bool(o["incr"] >= -0.5 and (rc["max_dd"] <= 0.95 * rm["max_dd"] or b5_comb >= b5_main + 0.05 * abs(b5_main)) and rc["ret_dd"] > rm["ret_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
        res.append(o); np.save(os.path.join(OUT, f"DAILY_{cand}.npy"), d); np.save(os.path.join(OUT, f"DAILY_SLIP4_{cand}.npy"), out["slip4"][0])
        np.savez_compressed(os.path.join(OUT, f"OCC_{cand}.npz"), **{k: v for k, v in co.items()})
        print(cand, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in o.items() if k in ("avg_day", "slip4_avg_day", "delay1_avg_day", "missed20_avg_day", "folds_pos", "incr", "comb_ret_dd", "comb_max_dd", "corr_main", "STRESS_PASS", "ROUTE_A", "ROUTE_B", "ROUTE_C", "peak_MNQ_total", "trades_after_capacity")}, flush=True)
    pd.DataFrame(res).to_csv(os.path.join(OUT, "P7_STRESS.csv"), index=False)


if __name__ == "__main__":
    main()
