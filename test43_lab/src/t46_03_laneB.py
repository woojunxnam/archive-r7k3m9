"""TEST46 Lane B analysis (T46_11..T46_21): event forward returns, first passage, matched long baselines, multi-window
recurrence, grammar ablation (is FAILURE+RECLAIM informative beyond displacement?), relative-exhaustion ablation and
simple deterministic controls.  Default parameters are the PREDECLARED simple controls in t46_rebound.DEFAULTS."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t45_sim as S45  # noqa: E402
import t46_common as C  # noqa: E402
import t46_rebound as R  # noqa: E402

OUT = os.path.join(C.T46, "laneB"); os.makedirs(OUT, exist_ok=True)
HOR = {"+15m": 15, "+30m": 30, "+60m": 60, "+120m": 120, "to 16:00": "16:00", "to 16:15": "16:15"}
WINDOWS = [("W2019_20", "2019-01-01", "2020-12-31"), ("W2020_21", "2020-01-01", "2021-12-31"), ("W2021_22", "2021-01-01", "2022-12-31"),
           ("W2022_23", "2022-01-01", "2023-12-31"), ("W2023_24", "2023-01-01", "2024-12-31"), ("W2024_25", "2024-01-01", "2025-12-31"),
           ("W2025_26", "2025-01-01", "2026-05-27")]
MIN_RULES = {"min_events": 150, "min_years_with_10_events": 5, "max_single_year_share_of_pnl": 0.40, "remove_top3_positive": True,
             "note": "predeclared before any Lane-B result (T46_33 minimum-sample rule)"}


def setup():
    P = C45.build_panel()
    es, nq = R.Market(P, "ES"), R.Market(P, "MNQ")
    R.attach_fills(es, S45.Sim(P, "ES")); R.attach_fills(nq, S45.Sim(P, "MNQ"))
    return P, es, nq, R.rel_array(nq, es)


def fwd(mk, s, j):
    """forward $ (1 contract, gross) and ATR-unit returns from fill j."""
    FP = mk.FPb; px = mk.FP[s, j]; a = mk.atr[s]
    out = {}
    for lab, h in HOR.items():
        jx = np.minimum(j + h, C45.g("16:15")) if isinstance(h, int) else np.full(len(j), C45.g(h))
        out[lab] = (FP[s, jx] - px) / a
    return out, px


def first_passage(mk, s, j, jend):
    res = {}
    for th in (0.25, 0.5, 1.0):
        r = np.full(len(s), np.nan)
        for i in range(len(s)):
            a = mk.atr[s[i]]; px = mk.FP[s[i], j[i]]
            H = mk.pn.H[s[i], j[i]:jend]; L = mk.pn.L[s[i], j[i]:jend]
            up = np.where(H >= px + th * a)[0]; dn = np.where(L <= px - th * a)[0]
            u = up[0] if len(up) else 10 ** 9; d = dn[0] if len(dn) else 10 ** 9
            if u < d:
                r[i] = 1.0
            elif d < u:
                r[i] = 0.0
            # same minute or neither -> unresolved (NaN), never counted as a loss
        res[f"P(+{th} before -{th} ATR)"] = np.nanmean(r); res[f"unresolved_{th}"] = float(np.mean(np.isnan(r)))
    return res


def baseline(mk, j_all, key_year, key_vol, key_bull):
    """matched unconditional long: mean forward ATR return over ALL sessions with the same fill minute, year, vol tercile
    and HTF state (computed lazily per unique key)."""
    sess_year = mk.pn.sess.year.values
    vt = np.digitize(mk.volt, [1 / 3, 2 / 3])
    cache = {}

    def get(j, y, v, b):
        kk = (j, y, v, b)
        if kk not in cache:
            m = (sess_year == y) & (vt == v) & (mk.bull == b)
            ss = np.where(m)[0]
            if len(ss) < 5:
                m = (sess_year == y); ss = np.where(m)[0]
            o, _ = fwd(mk, ss, np.full(len(ss), j))
            cache[kk] = {k: np.nanmean(v_) for k, v_ in o.items()}
        return cache[kk]
    return get, vt


def event_table(mk, fam, p, rel, tag):
    ev, brk = R.run_detect(mk, fam, p, rel)
    s = np.where(ev >= 0)[0]
    j = 5 * (ev[s] + 1)
    ok = (j < C45.NG) & ~np.isnan(mk.FP[s, np.minimum(j, C45.NG - 1)])
    s, j = s[ok], j[ok]
    o, px = fwd(mk, s, j)
    get, vt = baseline(mk, None, None, None, None)
    yrs = mk.pn.sess.year.values[s]
    bl = {k: np.array([get(int(jj), int(yy), int(vv), bool(bb))[k] for jj, yy, vv, bb in zip(j, yrs, vt[s], mk.bull[s])]) for k in HOR}
    E = pd.DataFrame({"s": s, "date": mk.pn.sess[s], "year": yrs, "j": j, **{f"{k}_atr": o[k] for k in HOR},
                      **{f"{k}_excess_atr": o[k] - bl[k] for k in HOR}})
    H = mk.pn.H; L = mk.pn.L
    e1600 = C45.g("16:00")
    E["MFE_atr"] = [(np.nanmax(H[ss, jj:e1600]) - mk.FP[ss, jj]) / mk.atr[ss] if jj < e1600 else np.nan for ss, jj in zip(s, j)]
    E["MAE_atr"] = [(np.nanmin(L[ss, jj:e1600]) - mk.FP[ss, jj]) / mk.atr[ss] if jj < e1600 else np.nan for ss, jj in zip(s, j)]
    fp = first_passage(mk, s, j, e1600)
    return E, fp, ev, brk


def summarize(E, fp, fam, inst, tag):
    o = {"family": R.FAMS[fam], "inst": inst, "variant": tag, "events": len(E), "years": int(E.year.nunique()) if len(E) else 0}
    for k in HOR:
        x = E[f"{k}_atr"].values; ex = E[f"{k}_excess_atr"].values
        o[f"{k}_raw_atr"] = np.nanmean(x) if len(x) else np.nan
        o[f"{k}_excess_atr"] = np.nanmean(ex) if len(ex) else np.nan
        o[f"{k}_excess_t"] = np.nanmean(ex) / np.nanstd(ex) * np.sqrt(np.sum(~np.isnan(ex))) if len(ex) > 2 else np.nan
    o["MFE_atr"] = E.MFE_atr.mean() if len(E) else np.nan; o["MAE_atr"] = E.MAE_atr.mean() if len(E) else np.nan
    o.update(fp)
    return o


def daily_metrics(pnl, mk, champ):
    x = pnl
    eq = np.cumsum(x); mdd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    tr = x[x != 0]
    top = np.sort(tr)[::-1]
    comb = champ + x
    ce = np.cumsum(comb); cmdd = float((np.maximum.accumulate(np.r_[0, ce]) - np.r_[0, ce]).max())
    ch_e = np.cumsum(champ); ch_mdd = float((np.maximum.accumulate(np.r_[0, ch_e]) - np.r_[0, ch_e]).max())
    yrs = mk.pn.sess.year.values
    ys = pd.Series(x).groupby(yrs).sum()
    return {"trades": int(len(tr)), "total": float(x.sum()), "avg_day": float(x.mean()), "avg_trade": float(tr.mean()) if len(tr) else np.nan,
            "PF": float(tr[tr > 0].sum() / max(-tr[tr < 0].sum(), 1e-9)) if len(tr) else np.nan, "max_dd": mdd,
            "worst_day": float(x.min()), "remove_top3_total": float(x.sum() - top[:3].sum()) if len(top) >= 3 else np.nan,
            "remove_top5_total": float(x.sum() - top[:5].sum()) if len(top) >= 5 else np.nan,
            "max_year_share": float(ys.max() / x.sum()) if x.sum() > 0 else np.nan,
            "years_with_10_trades": int((pd.Series(x != 0).groupby(yrs).sum() >= 10).sum()),
            "corr_C43": float(np.corrcoef(champ, x)[0, 1]) if x.std() > 0 else np.nan,
            "comb_avg": float(comb.mean()), "comb_max_dd": cmdd, "C43_avg": float(champ.mean()), "C43_max_dd": ch_mdd,
            "comb_ret_dd": float(comb.mean() / cmdd), "C43_ret_dd": float(champ.mean() / ch_mdd),
            "loss_day_jaccard_C43": float(((x < 0) & (champ < 0)).sum() / max(((x < 0) | (champ < 0)).sum(), 1))}


def main():
    P, es, nq, rel = setup()
    champ = C45.champion_daily().pnl.reindex(es.pn.sess).fillna(0.0).values
    rows, recur, ctrl, abl, events_all = [], [], [], [], []
    for fam in range(1, 8):
        for mk in (es, nq):
            if fam == 7 and mk is es:
                continue
            p = dict(R.DEFAULTS[fam])
            variants = {"DEFAULT (full grammar)": p,
                        "ABLATION no failure (k=0)": dict(p, k=0),
                        "ABLATION no reclaim (rho=-99: entry at first bar after break)": dict(p, rho=-99.0, k=0),
                        "ABLATION no displacement (D=0)": dict(p, D=0.0),
                        "ABLATION no regime veto": dict(p, veto5=99.0, vetogap=99.0)}
            if fam == 7:
                variants["ABLATION B6 without ES information (relx=-99)"] = dict(p, relx=-99.0)
            for tag, pp in variants.items():
                E, fp, ev, brk = event_table(mk, fam, pp, rel if fam == 7 else None, tag)
                if len(E) == 0:
                    continue
                o = summarize(E, fp, fam, mk.inst, tag)
                (rows if tag.startswith("DEFAULT") else abl).append(o)
                if tag.startswith("DEFAULT"):
                    E["family"] = R.FAMS[fam]; E["inst"] = mk.inst; events_all.append(E)
                    for wn, a, b in WINDOWS:
                        m = (E.date >= a) & (E.date <= b)
                        x = E.loc[m, "to 16:00_excess_atr"]
                        recur.append({"family": R.FAMS[fam], "inst": mk.inst, "window": wn, "events": int(m.sum()),
                                      "excess_to1600_atr": x.mean() if len(x) else np.nan})
                    for exit_mode, hold, stop, en in ((1, 0, -1.0, "exit 16:00, no stop"), (0, 120, -1.0, "exit +120m, no stop"),
                                                      (1, 0, 0.25, "exit 16:00, stop break-low-0.25ATR")):
                        pnl, ji, jo = R.run_trades(mk, ev, brk, exit_mode, hold, stop)
                        pnl4, _, _ = R.run_trades(mk, ev, brk, exit_mode, hold, stop, slip=4.0)
                        dm = daily_metrics(pnl, mk, champ)
                        ctrl.append({"family": R.FAMS[fam], "inst": mk.inst, "exit": en, **dm, "SLIP4_total": float(pnl4.sum()),
                                     "minimum_sample_rule_pass": bool(dm["trades"] >= MIN_RULES["min_events"] and dm["years_with_10_trades"] >= 5
                                                                      and (dm["max_year_share"] <= 0.40 if dm["total"] > 0 else False)
                                                                      and (dm["remove_top3_total"] or -1) > 0)})
    S = pd.DataFrame(rows); A = pd.DataFrame(abl); RC = pd.DataFrame(recur); CT = pd.DataFrame(ctrl)
    S.to_csv(f"{OUT}/T46_18_event_forward_default.csv", index=False); A.to_csv(f"{OUT}/T46_11_grammar_ablation.csv", index=False)
    RC.to_csv(f"{OUT}/T46_20_multiyear_recurrence.csv", index=False); CT.to_csv(f"{OUT}/T46_21_simple_controls.csv", index=False)
    pd.concat(events_all, ignore_index=True).to_parquet(f"{OUT}/events_default.parquet")
    json.dump(MIN_RULES, open(f"{OUT}/T46_minimum_sample_rules.json", "w"), indent=1)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 40)
    cols = ["family", "inst", "variant", "events", "+60m_excess_atr", "to 16:00_raw_atr", "to 16:00_excess_atr", "to 16:00_excess_t",
            "P(+0.5 before -0.5 ATR)", "unresolved_0.5", "MFE_atr", "MAE_atr"]
    print(S[cols].round(3).to_string()); print(A[cols].round(3).to_string())
    print(RC.pivot_table(index=["family", "inst"], columns="window", values="excess_to1600_atr").round(3).to_string())
    print(CT[["family", "inst", "exit", "trades", "total", "avg_trade", "PF", "max_dd", "remove_top3_total", "max_year_share", "corr_C43",
              "comb_ret_dd", "C43_ret_dd", "SLIP4_total", "minimum_sample_rule_pass"]].round(3).to_string())


if __name__ == "__main__":
    main()
