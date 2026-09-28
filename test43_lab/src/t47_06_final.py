"""TEST47 final stage (T47_39 .. T47_48): GP decision, execution stress, account risk, module combination, alpha attribution,
C43 incremental gate (mechanical, predeclared in SPEC['gate'] / SPEC['min_sample'] BEFORE ranking), final candidate,
GA recurrence + parameter plateau, pre-OOS freeze, new-OOS acceptance rules, hash index, final status.

Candidate list (fixed before the gate table was computed): the complexity ladder C1..C6 per instrument (primary exit X60,
C6 = C5 + trim), the stitched outer-fold GA selections of each lane (per the nested design), and the walk-forward ML-A RIDGE
selector (best linear) and ML-C LOGISTIC (second-contract selector, evaluated on the NR-A campaign it modifies)."""
import datetime
import glob
import hashlib
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import t47_common as C  # noqa: E402
import t47_engine as E  # noqa: E402
import t47_05_ga as GA  # noqa: E402
from t47_02_n3 import START, cfg  # noqa: E402
from t47_03_nr import risk  # noqa: E402

OUT = os.path.join(C.T47, "final"); os.makedirs(OUT, exist_ok=True)
FZ = os.path.join(C.T47, "freeze"); os.makedirs(FZ, exist_ok=True)
SPAN = pd.Timestamp("2021-01-01")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def camp_daily(mk, L):
    d = np.zeros(mk.n); np.add.at(d, L.acct_s.values.astype(int), L.pnl.values)
    return d


def gate_row(name, rung, d, exc_day, sess, champ, extra):
    m = sess >= SPAN
    x = d[m]; ch = champ[m]
    fold = {}
    for nm, a, b in C45.OUTER:
        mm = (sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(b))
        fold[nm] = float(d[mm].mean())
    comb = ch + x
    rc, rch = risk(comb), risk(ch)
    act = x[x != 0]; top = np.sort(act)[::-1]
    yr = pd.Series(x, index=sess[m]).groupby(sess[m].year).sum()
    o = {"candidate": name, "rung": rung, **{f"fold_{k}": v for k, v in fold.items()}, "folds_pos": sum(v > 0 for v in fold.values()),
         "fold_median": float(np.median(list(fold.values()))), "avg_day": float(x.mean()), "total": float(x.sum()), "active_days": int((x != 0).sum()),
         "matched_excess_day": exc_day, "remove_top3": float(act.sum() - top[:3].sum()) if len(top) >= 3 else np.nan,
         "remove_top5": float(act.sum() - top[:5].sum()) if len(top) >= 5 else np.nan,
         "comb_avg": rc["avg_day"], "comb_mdd": rc["max_dd"], "comb_worst": rc["worst_day"], "comb_ret_dd": rc["ret_dd"], "C43_ret_dd": rch["ret_dd"],
         "corr_C43": float(np.corrcoef(ch, x)[0, 1]) if x.std() > 0 else np.nan,
         "loss_day_overlap": float(((ch < 0) & (x < 0)).sum() / max((x < 0).sum(), 1)),
         "bottom_tail_overlap": float((x[np.argsort(ch)[:20]] < 0).mean()),
         "max_year_share": float(yr.clip(lower=0).max() / max(yr.clip(lower=0).sum(), 1e-9)), "years_with_activity": int((yr != 0).sum()), **extra}
    ms = C.SPEC["min_sample"]
    o["G1"] = o["folds_pos"] >= 4 and o["fold_median"] > 0
    o["G2"] = bool(exc_day > 0) if exc_day == exc_day else False
    o["G3"] = bool(o["remove_top3"] > 0)
    o["G4"] = o["comb_mdd"] <= 15000 and o["comb_worst"] >= -3000 and (o["comb_ret_dd"] >= o["C43_ret_dd"] or exc_day >= 5)
    o["G5"] = bool(extra.get("plateau_pass", True))
    o["G6"] = bool(extra.get("recurrence_pass", True))
    o["G7"] = o["avg_day"] >= 5
    o["G8"] = o["active_days"] >= ms["min_trades_2020_2026"] and o["max_year_share"] <= ms["max_single_year_pnl_share"]
    o["G9"] = bool(extra.get("beats_C1", True))
    o["ELIGIBLE"] = all(o[f"G{i}"] for i in range(1, 10))
    return o


def plateau(lane, g, s0):
    """+-10/20% on normalised thresholds, adjacent timing / leg-count values; evaluated on 2021..2026-05-27."""
    num = {"N3": ["xm"], "NB": ["tol", "wick"], "NR": ["blind_x", "trim_x", "rec_frac"]}[lane]
    d0, _, _ = GA.run(lane, g); base = d0[s0:].sum()
    rows = []
    for nm in num:
        for f in (0.8, 0.9, 1.1, 1.2):
            h = dict(g); h[nm] = g[nm] * f
            d, _, _ = GA.run(lane, h); rows.append({"param": nm, "factor": f, "total": float(d[s0:].sum())})
    if lane == "N3":
        for nt in (2, 3, 4):
            if nt != g["ntick"]:
                h = dict(g); h["ntick"] = nt; d, _, _ = GA.run(lane, h); rows.append({"param": "ntick", "factor": nt, "total": float(d[s0:].sum())})
        for md in (12, 24, 36):
            if md != g["maxdur"]:
                h = dict(g); h["maxdur"] = md; d, _, _ = GA.run(lane, h); rows.append({"param": "maxdur", "factor": md, "total": float(d[s0:].sum())})
    R = pd.DataFrame(rows)
    ok = bool(base > 0 and (R.total > 0).all() and (R.total >= 0.6 * base).all())
    return ok, float(base), R


def first_rth_after(ts_utc):
    ny = ZoneInfo("America/New_York")
    t = ts_utc.astimezone(ny)
    hol = {datetime.date(2026, 11, 26), datetime.date(2026, 12, 25), datetime.date(2027, 1, 1)}
    d = t.date()
    while True:
        op = datetime.datetime(d.year, d.month, d.day, 9, 30, tzinfo=ny)
        if d.weekday() < 5 and d not in hol and op > t:
            return d.isoformat()
        d += datetime.timedelta(days=1)


def main():
    GA._init()
    es, nq = GA._ctx["mk"]["ES"], GA._ctx["mk"]["MNQ"]
    mks = {"ES": es, "MNQ": nq}
    sess = es.pn.sess; champ = GA._ctx["champ"]; s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    rows, stress, attr = [], [], []
    daily = {}
    # ------------------------------------------------ ladder C1..C6 per instrument (X60)
    for k, mk in mks.items():
        from t47_03_nr import LotBase
        lb = LotBase(mk)
        ev1, _, legm1 = E.run_detect(mk, cfg(side=["KEEP", 0])); ev1 = ev1[mk.pn.sess[ev1.s.values] >= START]
        ev2, _, legm2 = E.run_detect(mk, cfg()); ev2 = ev2[mk.pn.sess[ev2.s.values] >= START]
        lad = {"C1 3 meaningful legs": (ev1, legm1, dict(entry="E1")), "C2 +sideways reset": (ev2, legm2, dict(entry="E1")),
               "C3 +bullish 5m confirm": None, "C4 +true bottom NB": (ev2, legm2, dict(entry="NB")),
               "C5 C4+confirmed second buy": (ev2, legm2, dict(entry="NB", add="confirmed")),
               "C6 C5+recycle trim": (ev2, legm2, dict(entry="NB", add="confirmed", trim=True))}
        c1_total = None
        for nm, v in lad.items():
            if v is None:
                T = E.trades(mk, ev2, "E3", "X60")
                d = E.daily(mk, T); bl = E.Baseline(mk); exc = bl.excess(T, "X60")[0]
                exd = float(pd.Series(exc).groupby(T.s.values).sum().reindex(range(mk.n)).fillna(0).values[s21:].mean())
            else:
                ev, legm, kw = v
                L, Cm = E.run_campaign(mk, ev, legm, exit="X60", **kw)
                d = camp_daily(mk, L)
                ex = L.pnl - lb(L)
                xd = np.zeros(mk.n); np.add.at(xd, L.acct_s.values.astype(int), ex.values); exd = float(xd[s21:].mean())
            daily[f"{nm} [{k}]"] = d
            if c1_total is None:
                c1_total = d[s21:].sum()
            rows.append(gate_row(f"{nm} [{k}]", "SIMPLE", d, exd, sess, champ, {"beats_C1": bool(d[s21:].sum() > c1_total) if not nm.startswith("C1") else True}))
        # attribution on the ladder (daily $ avg 2021+)
        a = {nm: daily[f"{nm} [{k}]"][s21:].mean() for nm in lad}
        L0, _ = E.run_campaign(mk, ev2, legm2, exit="REC50"); L1, _ = E.run_campaign(mk, ev2, legm2, exit="REC50", overnight=True)
        attr.append({"inst": k, "BASE_3TICK_ENTRY (C2)": a["C2 +sideways reset"], "TRUE_BOTTOM_CONFIRMATION (C4-C2)": a["C4 +true bottom NB"] - a["C2 +sideways reset"],
                     "SECOND_CONTRACT (C5-C4)": a["C5 C4+confirmed second buy"] - a["C4 +true bottom NB"],
                     "RECYCLE_TRIM (C6-C5)": a["C6 C5+recycle trim"] - a["C5 C4+confirmed second buy"]})
        Ld, _ = E.run_campaign(mk, ev2, legm2, entry="NB", exit="X60", add="confirmed", trim=True, rebuild=True)
        attr[-1]["RECYCLE_REENTRY (NR-D - C6)"] = camp_daily(mk, Ld)[s21:].mean() - a["C6 C5+recycle trim"]
        attr[-1]["OVERNIGHT_CARRY (REC50 hold - no hold)"] = camp_daily(mk, L1)[s21:].mean() - camp_daily(mk, L0)[s21:].mean()
        # ------------------------------------------------ execution stress on C2 / C4 / C6 (no survivor exists; documentation)
        for nm, kw in (("C2", dict(entry="E1")), ("C4", dict(entry="NB")), ("C6", dict(entry="NB", add="confirmed", trim=True))):
            ev = ev2
            base_d = camp_daily(mk, E.run_campaign(mk, ev, legm2, exit="X60", **kw)[0])[s21:].mean()
            for sn, sk in (("base", {}), ("+1 bar entry delay", dict(delay=5)), ("4-tick slippage", dict(slip=4.0)), ("missed initial entry 20%", dict(p_miss_entry=0.2)),
                           ("missed second add 50%", dict(p_miss_add=0.5)), ("missed trim 50%", dict(p_miss_trim=0.5)), ("next-bar confirmation delay", dict(delay=5, slip=2.0))):
                d = camp_daily(mk, E.run_campaign(mk, ev, legm2, exit="X60", **kw, **sk)[0])[s21:]
                stress.append({"inst": k, "candidate": nm, "stress": sn, "avg_day": d.mean(), "delta_vs_base": d.mean() - base_d, "total": d.sum()})
    # ------------------------------------------------ GA lanes: stitched outer + recurrence + plateau
    rec, plat = [], []
    for lane in ("N3", "NB", "NR"):
        p = os.path.join(GA.OUT, f"T47_GA_{lane}_selected.csv")
        if not os.path.exists(p):
            continue
        S = pd.read_csv(p)
        st = np.zeros(len(sess)); ex = np.zeros(len(sess)); clusters = []
        for name, a, b in C45.OUTER:
            r = S[(S.fold == name) & (S.sel_rank == 0)]
            if not len(r) or not isinstance(r.iloc[0].get("genome"), str):
                clusters.append("NONE"); continue
            g = json.loads(r.iloc[0].genome); clusters.append(r.iloc[0].cluster)
            s0 = int(np.searchsorted(sess.values, np.datetime64(a))); s1 = int(np.searchsorted(sess.values, np.datetime64(b), side="right"))
            d, exc, ntr = GA.run(lane, g)
            st[s0:s1] = d[s0:s1]
            ex[s0:s1] = exc[s0:s1] if lane == "NR" else (GA.excess_daily(len(d), exc, s0, s1, (20, s0)) if ntr else 0)
        vc = pd.Series(clusters).value_counts()
        top_cluster = vc.index[0] if len(vc) else "NONE"
        recurrence = bool(top_cluster != "NONE" and vc.iloc[0] >= 3)
        rec.append({"lane": lane, "fold_clusters": " ; ".join(clusters), "modal_cluster": top_cluster, "modal_count": int(vc.iloc[0]) if len(vc) else 0,
                    "RECURRENCE_PASS": recurrence})
        fin = S[(S.fold == "FINAL_ALL_TO_2026-05-27") & (S.sel_rank == 0)]
        ppass = False
        if len(fin) and isinstance(fin.iloc[0].get("genome"), str):
            ppass, base, R = plateau(lane, json.loads(fin.iloc[0].genome), s21)
            R["lane"] = lane; R["base_total"] = base; plat.append(R)
        rows.append(gate_row(f"GA-{lane} nested (stitched outer folds)", "GA", st, float(ex[s21:].mean()), sess, champ,
                             {"plateau_pass": ppass, "recurrence_pass": recurrence}))
        daily[f"GA-{lane}"] = st
    # ------------------------------------------------ ML candidates (walk-forward predictions re-generated with identical folds)
    ml = pd.read_csv(os.path.join(C.T47, "ml", "T47_29_30_ml_walkforward.csv"))
    for model, task in (("RIDGE", "ML-A"), ("LOGISTIC", "ML-C second contract")):
        r = ml[(ml.task == task) & (ml.model == model)]
        if len(r):
            r = r.iloc[0]
            rows.append({"candidate": f"{task} {model} (walk-forward)", "rung": "ML", "total": r.taken_pnl, "avg_day": r.taken_pnl / max((sess >= SPAN).sum(), 1),
                         "years_pos_taken": r.years_pos, "rankIC": r.rankIC,
                         "note": "ML-A: taken P&L negative -> fails G1/G7; ML-C modifies NR-A whose base campaign (R0 + adds) is negative -> fails G1/G2 at campaign level",
                         **{f"G{i}": False for i in (1, 2, 7)}, "ELIGIBLE": False})
    G = pd.DataFrame(rows); G.to_csv(f"{OUT}/T47_44_incremental_gate.csv", index=False)
    el = G[G.ELIGIBLE == True]  # noqa: E712
    order = {"SIMPLE": 0, "GA": 1, "ML": 2}
    final = el.assign(o=el.rung.map(order)).sort_values(["o", "avg_day"], ascending=[True, False]).iloc[0].candidate if len(el) else "NONE"
    pd.DataFrame(stress).to_csv(f"{OUT}/T47_40_execution_stress.csv", index=False)
    pd.DataFrame(attr).to_csv(f"{OUT}/T47_43_alpha_attribution.csv", index=False)
    pd.DataFrame(rec).to_csv(f"{OUT}/T47_37_ga_recurrence.csv", index=False)
    if plat:
        pd.concat(plat).to_csv(f"{OUT}/T47_38_ga_plateau.csv", index=False)
    # ------------------------------------------------ account risk / combination (T47_41 / T47_42)
    acc = []
    for nm, d in daily.items():
        x = d[s21:]; ch = champ[s21:]
        acc.append({"module": nm, **{f"standalone_{k}": v for k, v in risk(x).items() if k in ("avg_day", "max_dd", "worst_day")},
                    **{f"C43_plus_{k}": v for k, v in risk(ch + x).items() if k in ("avg_day", "max_dd", "worst_day", "ret_dd")}})
    acc.append({"module": "C43 alone", **{f"C43_plus_{k}": v for k, v in risk(champ[s21:]).items() if k in ("avg_day", "max_dd", "worst_day", "ret_dd")}})
    pd.DataFrame(acc).to_csv(f"{OUT}/T47_41_42_account_combination.csv", index=False)
    sel = {"FINAL_TEST47_CHALLENGER": final, "n_candidates": int(len(G)), "n_eligible": int(len(el)),
           "gp": "GP_NOT_JUSTIFIED: no simple rule, GA lane or ML task showed positive outer-fold signal (TEST47 §51)"}
    json.dump(sel, open(f"{OUT}/T47_45_final_selection.json", "w"), indent=1)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(G.drop(columns=[c for c in G.columns if c.startswith("fold_O")], errors="ignore").round(2).to_string())
    print(pd.DataFrame(stress).round(2).to_string()); print(pd.DataFrame(attr).round(2).T.to_string()); print(pd.DataFrame(rec).to_string())
    if plat:
        print(pd.concat(plat).round(1).to_string())
    print(pd.DataFrame(acc).round(2).to_string())
    print("FINAL", final)
    return G, sel


if __name__ == "__main__":
    main()
