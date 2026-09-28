"""TEST86 SIMPLE DETERMINISTIC PROFILE STRATEGIES on the TEST85-qualifying mechanisms (MNQ PG12_DOWN_STACK, MNQ PI_DIVERGE).
1 MNQ, one event per session, next-open fill, hold the qualifying RTH horizon; standalone gate + plateau + T61 incremental gate + +10 $/day."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t85_run as T85  # noqa: E402
from t84_run import features  # noqa: E402

OUT = os.path.join(A.AP, "TEST86"); os.makedirs(OUT, exist_ok=True)
CAND = {"PG12_DOWN_STACK": {"inst": "MNQ", "horizon": "h1600", "base_proxy": "VP-B"}, "PI_DIVERGE": {"inst": "MNQ", "horizon": "h60", "base_proxy": "VP-C"}}
SPEC = {"candidates": CAND, "excluded": {"ES PH_PRICE_NULL": "price-range null of the rejected generic-compression family; qualifies only at next open"},
        "note": "PG12_DOWN_STACK = long at 12:00 when the developing value area lies entirely below the prior RTH value area: flagged REBOUND-PROXIMATE "
                "(evaluated honestly; must beat the session-return momentum null, which it does at TEST85)",
        "base_proxy_rule": "qualifying proxy with the largest fold-median B at the chosen horizon; horizon = qualifying structural RTH horizon with the largest "
                           "fold-median B (next open excluded)",
        "entry_speed": {"IMMEDIATE": "next 1m open after the 5m decision", "ACCEPT1": "condition still true at the next 5m close, fill after it"},
        "plateau": {"value_area": [0.65, 0.75], "bin_f": [0.015, 0.03], "proxy": "other two proxies", "horizon": "adjacent structural horizons"},
        "gate": "program standalone gate + T61 incremental gate + minimum meaningful increment >= +10 $/day (2019-07+ and 2021+)", "budget": {"hypotheses": 2}}
HADJ = {"h60": ["h30", "h1600"], "h1600": ["h60", "h1615"]}


def events(I, other, name, proxy, f_bin=0.02, pct=0.70):
    g = T85.grid(I, other); P1, F = features(I, proxy, f_bin, pct)
    HV, LV = A.p1_nodes(I.H, I.L, I.C, I.V.astype(float), I.atr, f_bin, A.PROXY[proxy], A.J15, 16)
    E, _ = T85.profile_events(I, g, P1, F, HV, LV)
    E = E[(E.event == name) & I.full[E.s.values] & (E.j.values + 1 < A.J15)].reset_index(drop=True)
    return E, P1, F


def trade(I, E, horizon, delay=0, cs=None, miss=0.0, seed=5):
    cs = I.cs if cs is None else cs
    s = E.s.values.astype(int); ji = E.j.values.astype(int) + 1 + delay
    v = A.HZ[horizon]
    jx = np.full(len(E), A.J15) if v == ("abs", "16:15") else (np.full(len(E), min(A.C45.g(v[1]), A.J15)) if isinstance(v, tuple) else np.minimum(ji + v, A.J15))
    ok = ji < jx
    if miss > 0:
        ok &= np.random.default_rng(seed).random(len(E)) >= miss
    s, ji, jx = s[ok], ji[ok], jx[ok]
    net = (I.FPb[s, jx] - I.FP[s, ji]) * I.pv - 2 * cs
    d = np.zeros(I.n); np.add.at(d, s, net)
    L = pd.DataFrame({"s": s, "j_in": ji, "j_x": jx, "net": net})
    return d, L


def main():
    print(A.prereg("TEST86", SPEC))
    Is = B.load(); rows = []; dailies = {}
    t61 = K.t61_daily()["T61-R1C"].daily_pnl
    for name, c in CAND.items():
        I = Is[c["inst"]]; other = Is["ES" if c["inst"] == "MNQ" else "MNQ"]; BK = A.buckets(I); full = I.full; nd = int(full.sum())
        E, P1, F = events(I, other, name, c["base_proxy"])
        for speed in ("IMMEDIATE", "ACCEPT1"):
            Ex = E.copy()
            if speed == "ACCEPT1":
                Ex["j"] = Ex.j + 5
                Ex = Ex[Ex.j + 1 < A.J15]
                if name == "PG12_DOWN_STACK":
                    b = (Ex.j.values - 4) // 5
                    keep = F[Ex.s.values, b, A.FEAT["P2_VAH"]] < P1[Ex.s.values, 2]; Ex = Ex[keep]
                else:
                    keep = I.C[Ex.s.values, Ex.j.values] >= I.C[Ex.s.values, Ex.j.values - 5]; Ex = Ex[keep]
                Ex = Ex.reset_index(drop=True)
            d, L = trade(I, Ex, c["horizon"])
            Lb = A.label(I, Ex.assign(), BK)
            h = c["horizon"]
            xB = np.zeros(I.n); np.add.at(xB, Lb.s.values, np.nan_to_num(Lb[f"{h}_B"].values)); xA = np.zeros(I.n); np.add.at(xA, Lb.s.values, np.nan_to_num(Lb[f"{h}_A"].values))
            d4, _ = trade(I, Ex, h, cs=I.cs4); dl, _ = trade(I, Ex, h, delay=1); dm, _ = trade(I, Ex, h, miss=0.2)
            r = B.risk(d[full]); act = d[full & (d != 0)]; top = np.sort(act)[::-1]
            fd = {nm: float(d[np.asarray((I.sess >= a) & (I.sess <= b))].mean()) for nm, a, b in B.FOLDS}
            fnn = {nm: int(((I.sess[L.s.values] >= a) & (I.sess[L.s.values] <= b)).sum()) for nm, a, b in B.FOLDS}
            yr = pd.Series(d[full], index=I.sess[full]).groupby(I.sess[full].year).sum(); yshare = float(yr.max() / yr[yr > 0].sum()) if (yr > 0).any() else 1.0
            pl = []
            if speed == "IMMEDIATE":
                for lab, kw in ([(f"VA={p}", {"pct": p}) for p in SPEC["plateau"]["value_area"]] + [(f"bin={f}", {"f_bin": f}) for f in SPEC["plateau"]["bin_f"]]
                                + [(f"proxy={px}", {"proxy": px}) for px in A.PROXY if px != c["base_proxy"]]):
                    En, _, _ = events(I, other, name, kw.get("proxy", c["base_proxy"]), kw.get("f_bin", 0.02), kw.get("pct", 0.70))
                    pl.append((lab, float(trade(I, En, h)[0][full].sum())))
                for hh in HADJ[h]:
                    pl.append((f"hold={hh}", float(trade(I, E, hh)[0][full].sum())))
            base = float(d[full].sum())
            o = {"mechanism": name, "instrument": c["inst"], "proxy": c["base_proxy"], "horizon": h, "entry": speed, "trades": len(L), "trades_per_day": len(L) / nd,
                 "sides_per_day": 2 * len(L) / nd, "gross_day": float((L.net + 2 * I.cs).sum() / nd), "cost_day": float(2 * I.cs * len(L) / nd), "avg_day": r["avg_day"],
                 "usd_per_trade": float(L.net.mean()), "max_dd": r["max_dd"], "worst_day": r["worst_day"], "B_excess_day": float(xB[full].mean()), "A_excess_day": float(xA[full].mean()),
                 "slip4_day": float(d4[full].mean()), "delay1_day": float(dl[full].mean()), "miss20_day": float(dm[full].mean()), "remove_top3": float(act.sum() - top[:3].sum()),
                 **{f"fold_{k}": v for k, v in fd.items()}, "folds_pos": int(sum(v > 0 for v in fd.values())), "min_fold_n": min(fnn.values()), "max_year_share": yshare,
                 "plateau": str([(l_, round(t_)) for l_, t_ in pl]), "plateau_pass": bool(pl and all(t_ > 0 and t_ >= 0.6 * base for _, t_ in pl))}
            g_ = {"g_B": o["B_excess_day"] > 0, "g_A": o["A_excess_day"] > 0, "g_folds": o["folds_pos"] >= 4, "g_top3": o["remove_top3"] > 0, "g_slip4": o["slip4_day"] > 0,
                  "g_delay": o["delay1_day"] > 0, "g_miss": o["miss20_day"] > 0, "g_year": yshare <= 0.5, "g_plateau": o["plateau_pass"] if speed == "IMMEDIATE" else None,
                  "g_sample": o["trades"] >= 300 and o["min_fold_n"] >= 40}
            o.update(g_); o["STANDALONE_PASS"] = bool(all(v for v in g_.values() if v is not None) and speed == "IMMEDIATE")
            # T61 incremental (MNQ residual capacity: cut at the same fill if T61 MNQ + 1 > 6)
            tm = K.t61_minutes()[1]; ts = K.t61_minutes()[0]; ix = pd.Index(ts).get_indexer(I.sess)
            qN = np.where(ix[:, None] >= 0, tm["final_target_MNQ"][np.clip(ix, 0, None)], 0)
            dd = np.zeros(I.n)
            for rr in L.itertuples(index=False):
                if qN[rr.s, rr.j_in] + 1 > 6:
                    continue
                cut = np.where(qN[rr.s, rr.j_in:rr.j_x] + 1 > 6)[0]; jx = rr.j_in + int(cut[0]) if len(cut) else rr.j_x
                dd[rr.s] += (I.FPb[rr.s, jx] - I.FP[rr.s, rr.j_in]) * I.pv - 2 * I.cs
            t = t61.reindex(I.sess).fillna(0).values
            gi = K.incremental_gate(f"{name}_{speed}", dd, t, I.sess, {"matched_excess_day": o["B_excess_day"], "slip4_incr_avg_day": o["slip4_day"], "plateau_pass": o["plateau_pass"],
                                                                        "delay1_incr_avg_day": o["delay1_day"], "peak_total_MNQ": 6, "peak_total_MES": 6, "peak_margin_pct": 31})
            o.update({"t61_incr_day": gi["incr_avg_day"], "t61_incr_day_2021": gi["incr_avg_day_2021"], "t61_comb_avg_day": gi["comb_avg_day"], "t61_comb_maxdd": gi["comb_maxdd"],
                      "t61_comb_worst": gi["comb_worst"], "t61_comb_ret_dd": gi["comb_ret_dd"], "corr_to_t61": gi["corr_to_t61"],
                      "MEANINGFUL_INCREMENT": bool(gi["incr_avg_day"] >= 10 and gi["incr_avg_day_2021"] >= 10 and gi["comb_ret_dd"] >= gi["t61_ret_dd"])})
            o["SURVIVOR"] = bool(o["STANDALONE_PASS"] and gi["PASS"] and o["MEANINGFUL_INCREMENT"])
            rows.append(o); dailies[f"{name}_{speed}"] = d
            print(name, speed, round(o["avg_day"], 2), round(o["B_excess_day"], 2), o["folds_pos"], o["trades"], o["STANDALONE_PASS"], round(o["t61_incr_day"], 2), flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "TEST86_RESULTS.csv"), index=False); np.savez_compressed(os.path.join(OUT, "TEST86_daily.npz"), **dailies)
    pd.set_option("display.width", 250); print(R.T.to_string())
    A.reg_append("PROFILE_T61_FRONTIER", [{"test": "TEST86", "module": f"{r.mechanism}_{r.entry}", "incr_avg_day": r.t61_incr_day, "comb_avg_day": r.t61_comb_avg_day,
                                          "comb_maxdd": r.t61_comb_maxdd, "comb_worst": r.t61_comb_worst, "comb_ret_dd": r.t61_comb_ret_dd, "corr": r.corr_to_t61, "SURVIVOR": r.SURVIVOR}
                                         for r in R.itertuples()], key="module")
    A.budget("TEST86", hypotheses=2, note="2 qualifying profile mechanisms x 2 entry speeds (+ plateau)")
    A.md("TEST86_SIMPLE_PROFILE.md", "TEST86 - simple deterministic profile strategies", [str(SPEC), R.T])


if __name__ == "__main__":
    main()
