"""PH3 evaluation: magnitude-null excess, location / pattern comparisons, D4-D6 response curves, gate (prereg 33f1203)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import da_state as R  # noqa: E402
import mp_engine as P  # noqa: E402

OUT = os.path.join(R.OUT, "ph3"); HZ = ["h6", "h12", "h24", "h1615"]
CMP = {"D1": ("LN1", "D1P"), "D2": ("LN2", "D2P"), "D3": ("LN3", "D3P"), "D7": ("LN3", "D7P"), "D1B": ("TOUCH", "D1B_P"), "D8": ("TOUCH", "D8_P")}


def stats(d):
    o = {"n": len(d), "cost_atr": float(d.cost.mean())}
    for h in HZ:
        x = d[f"x_{h}"].values; r = d[f"R_{h}"].values; ok = ~np.isnan(x)
        lo, hi = P.boot(x[ok], d.date.values[ok]) if ok.sum() >= 20 else (np.nan, np.nan)
        yy = pd.Series(x[ok]).groupby(d.year.values[ok]).mean(); ii = pd.Series(x[ok]).groupby(d.inst.values[ok]).mean()
        usd = r * d.atr.values * d.pv.values
        o.update({f"{h}_R": float(np.nanmean(r)), f"{h}_x": float(np.nanmean(x)), f"{h}_lo": lo, f"{h}_hi": hi, f"{h}_years": int((yy > 0).sum()), f"{h}_inst": int((ii > 0).sum()),
                  f"{h}_ppos": float(np.nanmean(r[ok] > 0)) if ok.any() else np.nan, f"{h}_gross_usd": float(np.nanmean(usd)), f"{h}_net_usd": float(np.nanmean(usd - 2 * d.cs.values)),
                  f"{h}_slip4_usd": float(np.nanmean(usd - 2 * d.cs4.values)), f"{h}_x2022": float(yy.get(2022, np.nan))})
    o.update({"mfe60": float(d.mfe60.mean()), "mae60": float(d.mae60.mean()), "t_mfe": float(d.t_mfe.mean())})
    return o


def gate(o):
    pos = [h for h in HZ if o[f"{h}_x"] > 0]
    ok = len(pos) >= 2 and max(o[f"{h}_years"] for h in pos) >= 5 and max(o[f"{h}_inst"] for h in pos) >= 3 and max(o[f"{h}_R"] for h in ("h12", "h24", "h1615")) >= 0.9 * o["cost_atr"]
    return bool(ok), pos


def cmpdiff(T, a, b, h):
    d = T[T["def"].isin([a, b])]; x = d[f"x_{h}"].values; g = (d["def"] == a).values; ok = ~np.isnan(x)
    lo, hi = P.boot_diff(x[ok], g[ok], d.date.values[ok]); return float(np.nanmean(x[g]) - np.nanmean(x[~g])), lo, hi


def causal_q(D, x, q=5):
    per = pd.to_datetime(D.date, unit="D").dt.to_period("M").values; out = np.full(len(D), -1); d0 = D.date.min()
    for mo in np.unique(per):
        rows = np.where(per == mo)[0]; st = D.date.values[rows].min(); pr = x[D.date.values < st]; pr = pr[~np.isnan(pr)]
        if st - d0 < 170 or len(pr) < 50:
            continue
        e = np.unique(np.percentile(pr, np.linspace(0, 100, q + 1)[1:-1])); out[rows] = np.where(np.isnan(x[rows]), -1, np.digitize(np.nan_to_num(x[rows]), e))
    return out


def curve(D, feat, name):
    rows = []
    for h in ("h12", "h24", "h1615"):
        x = D[f"x_{h}"].values; b = causal_q(D, D[feat].values.astype(float)); m = (b >= 0) & ~np.isnan(x); K = int(b.max()) + 1 if (b >= 0).any() else 0
        if K < 3:
            rows.append({"curve": name, "feature": feat, "horizon": h, "COHERENT": False, "note": "too few bins"}); continue
        bm = [float(x[m & (b == k)].mean()) if (m & (b == k)).any() else np.nan for k in range(K)]
        okb = [k for k in range(K) if bm[k] == bm[k]]; rho = float(spearmanr(okb, [bm[k] for k in okb])[0])
        sel = m & ((b == 0) | (b == K - 1)); lo, hi = P.boot_diff(x[sel], (b[sel] == K - 1), D.date.values[sel]); dd = bm[K - 1] - bm[0]
        ys = [np.sign(np.nanmean(x[m & (b == K - 1) & (D.year.values == y)]) - np.nanmean(x[m & (b == 0) & (D.year.values == y)])) for y in np.unique(D.year)]
        ins = [np.sign(np.nanmean(x[m & (b == K - 1) & (D.inst.values == y)]) - np.nanmean(x[m & (b == 0) & (D.inst.values == y)])) for y in ("ES", "NQ", "YM", "RTY")]
        coh = abs(rho) >= 0.9 and (lo > 0 or hi < 0) and sum(s == np.sign(dd) for s in ys) >= 5 and sum(s == np.sign(dd) for s in ins) >= 3
        rows.append({"curve": name, "feature": feat, "horizon": h, "n": int(m.sum()), "bins": str([round(v, 4) for v in bm]), "spearman": rho, "top_minus_bottom": dd, "ci_lo": lo, "ci_hi": hi,
                     "years_same": int(sum(s == np.sign(dd) for s in ys)), "inst_same": int(sum(s == np.sign(dd) for s in ins)), "COHERENT": bool(coh)})
    return rows


def main():
    T = pd.read_parquet(os.path.join(OUT, "PH3_EVENTS.parquet")); res = {}; cm = []
    for dname, d in T.groupby("def"):
        res[dname] = stats(d)
        for h in HZ:
            o = res[dname]; R.append("EVENT_LEDGER.csv", {"phase": "PH3", "mechanism": dname, "null": "MAGNITUDE", "horizon": h, "n": o["n"], "mean": round(o[f"{h}_R"], 5), "excess": round(o[f"{h}_x"], 5),
                                                          "ci_lo": round(o[f"{h}_lo"], 5), "ci_hi": round(o[f"{h}_hi"], 5), "years_pos": o[f"{h}_years"], "inst_pos": o[f"{h}_inst"]})
    for ev, (ln, pn) in CMP.items():
        g, pos = gate(res[ev]); res[ev]["GATE"] = g; res[ev]["pos_horizons"] = pos
        for h in HZ:
            dl, l1, h1 = cmpdiff(T, ev, ln, h); dp, l2, h2 = cmpdiff(T, ev, pn, h)
            cm.append({"event": ev, "horizon": h, "vs_location_null": dl, "loc_lo": l1, "loc_hi": h1, "vs_pattern_null": dp, "pat_lo": l2, "pat_hi": h2})
        c = pd.DataFrame(cm); c = c[c.event == ev]
        res[ev]["PATTERN_VALUE"] = bool((c.vs_location_null > 0).sum() >= 3); res[ev]["LOCATION_VALUE"] = bool((c.vs_pattern_null > 0).sum() >= 3)
        res[ev]["CLASS"] = "ECONOMIC_RESEARCH_CANDIDATE" if g else "REJECT"
        R.append("MECHANISM_REGISTRY.csv", {"mechanism": ev, "phase": "PH3", "definition": "see PH3 prereg", "n_events": res[ev]["n"], "status": res[ev]["CLASS"],
                                            "value_type": ("LOCATION+" if res[ev]["LOCATION_VALUE"] else "") + ("PATTERN" if res[ev]["PATTERN_VALUE"] else ""), "note": f"pos horizons {pos}"})
    C = pd.DataFrame(cm)
    curves = []
    sup = T[T["def"].isin(["D1", "D2", "D1B"])]
    for r in (15, 10, 20):
        curves += curve(sup, f"ev_conf_{r}", f"D4_CONFLUENCE_r{r}")
    for nm, pop in (("D5_ROOM_SUPPORT_EVENTS", T[T["def"].isin(["D1", "D2", "D1B", "D8"])]), ("D5_ROOM_BREAKOUT_EVENTS", T[T["def"].isin(["D3", "D7"])]), ("D5_ROOM_C2_ALL", T[T["def"].isin(["D1B", "D1B_P"])])):
        pop = pop.copy(); pop["room_f"] = np.where(pop.no_res.values > 0, 5.0, pop.up_room.values); curves += curve(pop, "room_f", nm)
    d12 = T[T["def"].isin(["D1", "D2"])]
    for k in ("disp6", "bars_since_high", "bear_frac6", "consec_bear", "range_contract", "lower_wick", "cpos_chg3", "sup_touch"):
        curves += curve(d12, f"ap_{k}", f"D6_APPROACH_{k}")
    CV = pd.DataFrame(curves)
    C.to_csv(os.path.join(OUT, "PH3_NULL_COMPARISONS.csv"), index=False); CV.to_csv(os.path.join(OUT, "PH3_CURVES.csv"), index=False)
    pd.DataFrame(res).T.to_csv(os.path.join(OUT, "PH3_STATS.csv")); json.dump({k: {kk: v[kk] for kk in ("n", "CLASS", "LOCATION_VALUE", "PATTERN_VALUE", "pos_horizons")} for k, v in res.items() if "CLASS" in v},
                                                                                open(os.path.join(OUT, "PH3_GATES.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    cols = ["n", "cost_atr"] + [f"{h}_{s}" for h in HZ for s in ("R", "x", "lo", "years", "inst")]
    print(pd.DataFrame(res).T[cols].astype(float).round(4).to_string()); print(C.round(4).to_string()); print(CV[["curve", "horizon", "bins", "spearman", "ci_lo", "ci_hi", "COHERENT"]].to_string())
    print(json.dumps({k: {kk: v.get(kk) for kk in ("CLASS", "LOCATION_VALUE", "PATTERN_VALUE")} for k, v in res.items() if "CLASS" in v}))


if __name__ == "__main__":
    main()
