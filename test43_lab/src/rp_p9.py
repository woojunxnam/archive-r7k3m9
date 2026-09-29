"""P9 relaxed research frontier: exhaustive integrated portfolio enumeration (prereg 215d01f)."""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import rp_econ as EC  # noqa: E402
import rp_state as R  # noqa: E402
from rp_p6 import add_control, control_tables  # noqa: E402
from rp_p7 import CAND, CAP, MARGIN, MICRO, prep  # noqa: E402

OUT = os.path.join(R.OUT, "p9"); os.makedirs(OUT, exist_ok=True)
MG = {"C1_R1_TRAPPED_UNION": "D_WINNER_PYRAMID", "C2_P2_FAILED_FIRST": "D_WINNER_PYRAMID", "C7_L1_SWH60": "C_FRESH_RECOVERY"}


def module_orders(cand, mgmt, Tctl):
    """list of orders: base units (+ add units tied to their base) with prices, times and control $."""
    T = prep(pd.read_parquet(os.path.join(R.OUT, "p6", f"ARM_{cand}_{CAND[cand]}.parquet"))).reset_index(drop=True)
    T = add_control(T, "h1615", Tctl) if "ctl_usd" not in T else T
    rows = []
    for k, r in enumerate(T.itertuples(index=False)):
        rows.append(dict(mod=cand, key=f"{cand}#{k}", parent=None, date=int(r.date), inst=r.inst, j_in=int(r.j_in), j_out=int(r.j_out), px_in=r.px_in, px_out=r.px_out,
                         pv=r.pv, cs=r.cs, cs4=r.cs4, ctl=r.ctl_usd, year=int(r.year)))
    if mgmt:
        Mg = pd.read_parquet(os.path.join(R.OUT, "p8", f"MGMT_{cand}.parquet")).reset_index(drop=True); arm = MG[cand]
        assert len(Mg) == len(T)
        for k, (r, g) in enumerate(zip(T.itertuples(index=False), Mg.itertuples(index=False))):
            ja = getattr(g, f"{arm}_ja", np.nan)
            if ja == ja:
                rows.append(dict(mod=cand, key=f"{cand}#{k}+", parent=f"{cand}#{k}", date=int(r.date), inst=r.inst, j_in=int(ja), j_out=int(r.j_out),
                                 px_in=getattr(g, f"{arm}_pa"), px_out=r.px_out, pv=r.pv, cs=r.cs, cs4=r.cs4, ctl=np.nan, year=int(r.year)))
    return rows


def allocate(orders, lots):
    c = EC.ctx(); n = len(c["sess"]); G = c["occ"]["MNQ"].shape[1]
    main_occ = {"MNQ": c["occ"]["MNQ"], "MES": c["occ"]["ES"]}; co = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}
    orders = sorted(orders, key=lambda o: (o["date"], o["j_in"], o["parent"] is not None)); filled = set()
    d = {m: np.zeros(n) for m in set(o["mod"] for o in orders)}; d4 = {m: np.zeros(n) for m in d}; dadd = np.zeros(n); dctl = np.zeros(n)
    for o in orders:
        if o["parent"] is not None and o["parent"] not in filled:
            continue
        si = c["pos"].get(o["date"], -1)
        if si < 0:
            continue
        L = lots[o["mod"]]; mi = MICRO[o["inst"]]; ji, jo = o["j_in"], o["j_out"]
        base = main_occ[mi][si, ji:jo + 1] if mi in main_occ else 0
        if np.max(base + co[mi][si, ji:jo + 1]) + L > CAP[mi]:
            continue
        co[mi][si, ji:jo + 1] += L; filled.add(o["key"])
        pnl = L * ((o["px_out"] - o["px_in"]) * o["pv"] - 2 * o["cs"]); d[o["mod"]][si] += pnl; d4[o["mod"]][si] += L * ((o["px_out"] - o["px_in"]) * o["pv"] - 2 * o["cs4"])
        if o["parent"] is not None:
            dadd[si] += pnl
        elif o["ctl"] == o["ctl"]:
            dctl[si] += L * o["ctl"]
    return d, d4, dadd, dctl, co


def stats(dm, dc, d4c, dadd, dctl, co, mods, main_occ):
    c = EC.ctx(); w = c["win"]; yrs = c["sess"][w].year; mw = dm[w]; x = dc[w]; tot = mw + x; rm = EC.risk(mw); rt = EC.risk(tot)
    top = np.sort(tot)[::-1]; b5 = mw <= np.percentile(mw, 5)
    o = {"avg_day": rt["avg_day"], "incr": rt["avg_day"] - rm["avg_day"], "slip4_avg_day": float((mw + d4c[w]).mean()), "max_dd": rt["max_dd"], "worst_day": rt["worst_day"],
         "ret_dd": rt["ret_dd"], "sharpe_daily": float(tot.mean() / tot.std()), "corr_main_cand": float(np.corrcoef(x, mw)[0, 1]) if x.std() > 0 else 0.0,
         "loss_jaccard": float(((x < 0) & (mw < 0)).sum() / max(((x < 0) | (mw < 0)).sum(), 1)), "bottom5_cand_mean": float(x[b5].mean()),
         "active_overlap": float(((x != 0) & (mw != 0)).mean()), "y2022": float(tot[yrs == 2022].sum()), "y2022_cand": float(x[yrs == 2022].sum()),
         "y2022_mb_excess": float((x - dctl[w])[yrs == 2022].sum()), "remove_top3": float(tot.sum() - top[:3].sum()), "add_units_avg_day": float(dadd[w].mean()),
         "peak_MNQ": int((main_occ["MNQ"] + co["MNQ"]).max()), "peak_MES": int((main_occ["ES"] + co["MES"]).max()), "peak_MYM": int(co["MYM"].max()), "peak_M2K": int(co["M2K"].max()),
         "cand_margin_peak_approx": int(max((sum(MARGIN[k] * co[k][s].max() for k in co)) for s in range(co["MES"].shape[0]))),
         "per10k_dd": rt["avg_day"] / rt["max_dd"] * 1e4, **{f"year_{y}": float(tot[yrs == y].sum()) for y in sorted(set(yrs))}}
    o["risk_normalized_increment"] = o["per10k_dd"] - rm["avg_day"] / rm["max_dd"] * 1e4
    o["route_A"] = bool(o["incr"] >= 5 and rt["ret_dd"] >= rm["ret_dd"] and rt["max_dd"] <= 1.10 * rm["max_dd"] and rt["worst_day"] >= -5000 and o["slip4_avg_day"] > rm["avg_day"])
    o["route_B"] = bool(o["incr"] >= 1.5 and abs(o["corr_main_cand"]) <= 0.35 and rt["ret_dd"] >= 1.02 * rm["ret_dd"] and rt["max_dd"] <= 1.03 * rm["max_dd"] and rt["worst_day"] >= rm["worst_day"] - 250)
    b5m = mw[b5].mean(); b5t = tot[b5].mean()
    o["route_C"] = bool(o["incr"] >= -0.5 and (rt["max_dd"] <= 0.95 * rm["max_dd"] or b5t >= b5m + 0.05 * abs(b5m)) and rt["ret_dd"] > rm["ret_dd"] and rt["worst_day"] >= rm["worst_day"] - 250)
    return o


def main():
    c = EC.ctx(); Tctl = control_tables(); OR = {}
    for cand in ("C1_R1_TRAPPED_UNION", "C2_P2_FAILED_FIRST", "C7_L1_SWH60"):
        OR[(cand, False)] = module_orders(cand, False, Tctl); OR[(cand, True)] = module_orders(cand, True, Tctl)
    trapped = [None] + [(m, g, L) for m in ("C1_R1_TRAPPED_UNION", "C2_P2_FAILED_FIRST") for g in (False, True) for L in (1, 2)]
    c7 = [None] + [("C7_L1_SWH60", g, L) for g in (False, True) for L in (1, 2)]
    res = []; mw = c["main"]; mods_d = {}
    for t, s7 in itertools.product(trapped, c7):
        sel = [x for x in (t, s7) if x]; orders = []; lots = {}
        for m, g, L in sel:
            orders += OR[(m, g)]; lots[m] = L
        name = " + ".join(f"{m.split('_')[0]}{'+MGMT' if g else ''}x{L}" for m, g, L in sel) or "MAIN_ONLY"
        if orders:
            d, d4, dadd, dctl, co = allocate(orders, lots); dc = sum(d.values()); d4c = sum(d4.values())
        else:
            n = len(c["sess"]); G = c["occ"]["MNQ"].shape[1]; d = {}; dc = d4c = dadd = dctl = np.zeros(n); co = {k: np.zeros((n, G), np.int32) for k in MICRO.values()}
        o = {"portfolio": name, "n_modules": len(sel), **stats(mw, dc, d4c, dadd, dctl, co, sel, c["occ"])}
        if len(d) == 2:
            a, b = [v[c["win"]] for v in d.values()]; o["pair_corr"] = float(np.corrcoef(a, b)[0, 1])
        res.append(o); mods_d[name] = dc
        print(name, round(o["avg_day"], 2), round(o["incr"], 2), round(o["max_dd"]), round(o["ret_dd"], 5), o["route_A"], o["route_B"], o["route_C"], flush=True)
    Rr = pd.DataFrame(res); Rr.to_csv(os.path.join(OUT, "P9_PORTFOLIOS.csv"), index=False)
    np.savez_compressed(os.path.join(OUT, "P9_DAILY.npz"), **{k.replace(" ", ""): v for k, v in mods_d.items()})
    main_r = Rr[Rr.portfolio == "MAIN_ONLY"].iloc[0]; mdd = main_r.max_dd
    A = Rr[(Rr.max_dd <= 1.10 * mdd) & (Rr.worst_day >= -5000)].sort_values("avg_day").iloc[-1]; B = Rr.sort_values("ret_dd").iloc[-1]
    Cc = Rr[Rr.incr > 0].sort_values("max_dd").iloc[0]; Dd = Rr[Rr.worst_day >= -5000].sort_values("avg_day").iloc[-1]
    par = [r.portfolio for r in Rr.itertuples() if not any((q.avg_day >= r.avg_day) and (q.ret_dd >= r.ret_dd) and (q.max_dd <= r.max_dd) and (q.worst_day >= r.worst_day)
                                                          and ((q.avg_day > r.avg_day) or (q.ret_dd > r.ret_dd) or (q.max_dd < r.max_dd) or (q.worst_day > r.worst_day)) for q in Rr.itertuples())]
    fr = {"FRONTIER_A": A.portfolio, "FRONTIER_B": B.portfolio, "FRONTIER_C": Cc.portfolio, "FRONTIER_D": Dd.portfolio, "PARETO": par, "N_PORTFOLIOS": len(Rr)}
    json.dump(fr, open(os.path.join(OUT, "P9_FRONTIERS.json"), "w"), indent=1); print(json.dumps(fr, indent=1))


if __name__ == "__main__":
    main()
