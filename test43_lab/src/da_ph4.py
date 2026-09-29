"""PH4 exit dataset for all PH3 triggers + C2 strategy economics with nested frozen-exit choice (prereg 415e00b)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import da_atlas as AT  # noqa: E402
import da_ph3 as D3  # noqa: E402
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402

OUT = os.path.join(R.OUT, "ph4"); os.makedirs(OUT, exist_ok=True); NB = P.NB; J15 = 404
EXITS = ["X60", "X120", "X1615", "XRES", "XSTRUCT"]
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K"}; CAP = {"MES": 8, "MNQ": 6, "MYM": 4, "M2K": 4}


def exits_for(m, T, F, lvl):
    I = m.I; out = {k: np.full(len(T), np.nan) for k in EXITS}; jo = {k: np.full(len(T), -1) for k in EXITS}
    for k, (s, b) in enumerate(zip(T.s.values, T.b.values)):
        ji = 5 * b + 5
        for nm, h in (("X60", 12), ("X120", 24)):
            j = 5 * (b + 1 + h)
            if j <= J15:
                out[nm][k] = I.FP[s, j]; jo[nm][k] = j
        out["X1615"][k] = I.FP[s, J15]; jo["X1615"][k] = J15
        rs = F["res"][s, b]; xj = J15
        if rs == rs:
            hit = np.where(I.C[s, ji:J15] >= rs)[0]
            if len(hit):
                xj = min(ji + hit[0] + 1, J15)
        out["XRES"][k] = I.FP[s, xj]; jo["XRES"][k] = xj
        L = lvl[k]; xj = J15
        if L == L:
            below = m.c[s, b + 1:NB] < L
            for q in range(len(below) - 1):
                if below[q] and below[q + 1]:
                    xj = min(5 * (b + 1 + q + 1) + 5, J15); break
        out["XSTRUCT"][k] = I.FP[s, xj]; jo["XSTRUCT"][k] = xj
    return out, jo


def capacity_daily(Tr, delay=False, missed=False, slip4=False):
    c = EC.ctx(); occ = {"MNQ": c["occ"]["MNQ"], "MES": c["occ"]["ES"]}; n = len(c["sess"]); G = occ["MNQ"].shape[1]
    co = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}; d = np.zeros(n); k_ = 0; nt = 0
    for r in Tr.sort_values(["date", "j_in"]).itertuples(index=False):
        k_ += 1
        if missed and k_ % 5 == 0:
            continue
        si = c["pos"].get(int(r.date), -1)
        if si < 0:
            continue
        ji = r.j_in + (5 if delay else 0); jo = int(r.j_out)
        if ji >= jo:
            continue
        mi = MICRO[r.inst]; base = occ[mi][si, ji:jo + 1] if mi in occ else 0
        if np.max(base + co[mi][si, ji:jo + 1]) + 1 > CAP[mi]:
            continue
        co[mi][si, ji:jo + 1] += 1; nt += 1
        pin = r.px_in_d1 if delay else r.px_in; d[si] += (r.px_out - pin) * r.pv - 2 * (r.cs4 if slip4 else r.cs)
    return d, nt, co


def main():
    M = P.markets(); T = pd.read_parquet(os.path.join(R.OUT, "ph3", "PH3_EVENTS.parquet")); allx = []
    for i in P.INSTS:
        m = M[i]; Lv, F = AT.build(m); band = 0.25 * m.atr5; D3.AUXB.clear()
        ev, aux = D3.sup_machines(m, F["sup"], band); rl = F["res"].copy(); rl[F["res_type"] == AT.RES.index("ORH")] = np.nan; bk = D3.brk_machines(m, rl, band)
        chk = {"D1": ev["D1"], "D2": ev["D2"], "LN1": ev["LN1"], "LN2": ev["LN2"], "D3": bk["D3"], "D7": bk["D7"], "LN3": bk["LN3"]}
        Ti = T[T.inst == i].copy()
        for k, mk in chk.items():                    # parity with PH3
            assert int((mk & m.valid & (m.bidx <= 67)).sum()) == int((Ti["def"] == k).sum()), (i, k)
        pl12 = pd.Series(m.l.ravel()).rolling(13).min().shift(1).values.reshape(m.n, NB)
        lvl = []
        for r in Ti.itertuples(index=False):
            if r._0 in ("D1", "D2", "LN1", "LN2"):
                lvl.append(aux[(r._0, r.s, r.b)][0])
            elif r._0 in ("D3", "D7", "LN3"):
                lvl.append(D3.AUXB[(r._0, r.s, r.b)])
            elif r._0 in ("D1B", "D1B_P", "D8", "D8_P", "TOUCH"):
                lvl.append(pl12[r.s, r.b])
            else:
                lvl.append(np.nan)
        px, jo = exits_for(m, Ti, F, np.array(lvl, float))
        Ti["j_in"] = 5 * Ti.b.values + 5; Ti["px_in"] = Ti.entry.values; Ti["px_in_d1"] = m.I.FP[Ti.s.values, np.minimum(5 * Ti.b.values + 10, J15)]; Ti["struct_level"] = lvl
        for k in EXITS:
            Ti[f"px_{k}"] = px[k]; Ti[f"jo_{k}"] = jo[k]; Ti[f"usd_{k}"] = (px[k] - Ti.px_in) * Ti.pv - 2 * Ti.cs; Ti[f"usd4_{k}"] = (px[k] - Ti.px_in) * Ti.pv - 2 * Ti.cs4
        allx.append(Ti); print(i, "exits done", flush=True)
    X = pd.concat(allx, ignore_index=True); X.to_parquet(os.path.join(OUT, "PH4_EXIT_DATASET.parquet"))
    # ---------- C2 strategy (D1B u D1B_P) ----------
    C2 = X[X["def"].isin(["D1B", "D1B_P"])].copy(); res = {}
    summ = C2.groupby("def").size().to_dict(); fx = []
    for k in EXITS:
        z = C2[C2.year >= 2021]; fx.append({"exit": k, "n": len(z), "usd": z[f"usd_{k}"].mean(), "usd4": z[f"usd4_{k}"].mean()})
    picks = {}; tests = []
    for f, ye in EC.TRAIN_END.items():
        a, b = EC.FOLDS[f]; tr = C2[C2.year <= ye]; te = C2[(C2.year >= a) & (C2.year <= b)].copy()
        best = max(EXITS, key=lambda k: tr[f"usd_{k}"].mean()); picks[f] = best
        te["px_out"] = te[f"px_{best}"]; te["j_out"] = te[f"jo_{best}"]; tests.append(te)
    Tn = pd.concat(tests); c = EC.ctx(); w = c["win"]; yrs = c["sess"][w].year; mw = c["main"][w]; rm = EC.risk(mw)
    out = {}
    for tag, kw in (("base", {}), ("slip4", {"slip4": True}), ("delay1", {"delay": True}), ("missed20", {"missed": True})):
        d, nt, co = capacity_daily(Tn, **kw); out[tag] = (d[w], nt, co)
    dw = out["base"][0]; r_ = EC.risk(dw); rc = EC.risk(mw + dw); top = np.sort(dw)[::-1]
    fold = {k: float(dw[(yrs >= a) & (yrs <= b)].mean()) for k, (a, b) in EC.FOLDS.items()}; corr = float(np.corrcoef(dw, mw)[0, 1])
    o = {"exit_picks": picks, "trades": out["base"][1], "avg_day": r_["avg_day"], "slip4_avg_day": float(out["slip4"][0].mean()), "delay1_avg_day": float(out["delay1"][0].mean()),
         "missed20_avg_day": float(out["missed20"][0].mean()), "remove_top3": float(dw.sum() - top[:3].sum()), "folds": fold, "folds_pos": int(sum(v > 0 for v in fold.values())),
         "y2022": float(dw[yrs == 2022].sum()), "max_dd": r_["max_dd"], "worst_day": r_["worst_day"], "corr_main": corr, "incr": rc["avg_day"] - rm["avg_day"],
         "comb_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"], "comb_max_dd": rc["max_dd"], "comb_worst": rc["worst_day"]}
    o["STRESS_PASS"] = bool(o["avg_day"] > 0 and o["slip4_avg_day"] > 0 and o["delay1_avg_day"] > 0 and o["missed20_avg_day"] > 0 and o["remove_top3"] > 0 and o["folds_pos"] >= 3)
    o["ROUTE_B"] = bool(o["STRESS_PASS"] and o["incr"] >= 1.5 and abs(corr) <= 0.35 and rc["ret_dd"] >= 1.02 * rm["ret_dd"] and rc["max_dd"] <= 1.03 * rm["max_dd"] and rc["worst_day"] >= rm["worst_day"] - 250)
    o["ROUTE_A"] = bool(o["STRESS_PASS"] and o["incr"] >= 5 and rc["ret_dd"] >= rm["ret_dd"] and rc["max_dd"] <= 1.10 * rm["max_dd"] and rc["worst_day"] >= -5000)
    z = C2[C2.year >= 2021]; dd = (z.usd_XSTRUCT - z.usd_X1615).values; lo, hi = P.boot(dd, z.date.values)
    o["XSTRUCT_minus_X1615_per_trade"] = {"mean": float(dd.mean()), "ci_lo": lo, "ci_hi": hi, "n": len(dd)}
    o["fixed_exit_table"] = fx; o["composition"] = summ
    np.save(os.path.join(OUT, "C2_NESTED_EXIT_DAILY.npy"), out["base"][0]); Tn.to_parquet(os.path.join(OUT, "C2_NESTED_EXIT_TRADES.parquet"))
    json.dump(o, open(os.path.join(OUT, "PH4_C2_STRATEGY.json"), "w"), indent=1, default=float); print(json.dumps(o, indent=1, default=float))
    # exit table for every trigger (stitched window, per trade)
    tab = X[X.year >= 2021].groupby("def")[[f"usd_{k}" for k in EXITS] + [f"usd4_{k}" for k in EXITS]].mean(); tab["n"] = X[X.year >= 2021].groupby("def").size()
    tab.to_csv(os.path.join(OUT, "PH4_EXIT_TABLE.csv")); print(tab.round(2).to_string())


if __name__ == "__main__":
    main()
