"""TEST45 Phases 11(recurrence), 16 (neighbourhood robustness), 18-26: GA/GP outer-fold generalisation, recurrence,
plateau, module combination with the Champion, scaling frontier, stress, complexity ladder, ablation, final candidate.

PREDECLARED FINAL-CANDIDATE RULE (written before the GA/GP results were inspected):
  a candidate overlay is ELIGIBLE only if ALL hold
   1. out-of-sample evidence: nested outer-fold (GA/GP) or fixed-rule block median $/day > 0 and >= 4 of 5 outer blocks > 0
   2. Champion+overlay return/MaxDD (full history <= 2026-05-27) >= Champion return/MaxDD
   3. incremental $/day >= +5 and |corr with Champion| <= 0.5
   4. Champion+overlay MaxDD <= $10,000 and worst day >= -$2,500 (inside the TEST44 MODERATE envelope with margin)
   5. beats the simplest control of the same family (unconditional carry / CONTROL_B) on outer-block median AND on combined ret/DD
   6. GA/GP only: parameter plateau PASS and concept recurrence in >= 3 of 5 outer folds
  among eligible: prefer the lowest rung of the complexity ladder whose combined ret/DD is within 10% of the best; else NONE."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_overlay as O  # noqa: E402
import t45_sim as S  # noqa: E402
import t45_05_ga as GA  # noqa: E402
import t45_06_gp as GP  # noqa: E402

OUT = os.path.join(C.T45, "final"); os.makedirs(OUT, exist_ok=True)
FOLDS = [f[0] for f in C.OUTER]


def outer_masks(bank):
    s = bank.sess.values
    return {n: (s >= np.datetime64(a)) & (s <= np.datetime64(b)) for n, a, b in C.OUTER}


def comb_stats(pnl, bank, mask=None):
    m = np.ones(bank.n, bool) if mask is None else mask
    ch = bank.bench.champ[m]; x = ch + pnl[m]
    a = C.dstats(ch); b = C.dstats(x)
    return {"champ_avg": a["avg"], "champ_mdd": a["max_dd"], "champ_ret_dd": a["ret_dd"], "comb_avg": b["avg"], "comb_mdd": b["max_dd"],
            "comb_ret_dd": b["ret_dd"], "comb_worst": b["worst"], "incr_avg": b["avg"] - a["avg"],
            "corr": float(np.corrcoef(ch, pnl[m])[0, 1]) if pnl[m].std() > 0 else 0.0}


# ------------------------------------------------------------------ concepts for recurrence
def concept(g):
    c = {"inst": g["inst"], "morning": int(g["m_on"]), "close": int(g["c_on"])}
    if g["m_on"]:
        gh = g["m_gap_hi"]
        c["m_gap_region"] = "none" if gh is None or not np.isfinite(gh) else ("<=-1.0" if gh <= -1.0 else "(-1.0,-0.5]" if gh <= -0.5 else "(-0.5,0]" if gh <= 0 else ">0")
        c["m_w"] = g["m_w"]
        fh = g["m_flush_hi"]
        c["m_flush_region"] = "none" if fh is None or not np.isfinite(fh) else ("<=-0.5" if fh <= -0.5 else "(-0.5,-0.2]" if fh <= -0.2 else "(-0.2,0]")
        c["m_exit"] = g["m_exit"]
        c["m_crash_guard"] = int(g["m_gap_lo"] is not None and np.isfinite(g["m_gap_lo"]))
    if g["c_on"]:
        c["c_time"] = g["c_time"]; c["c_base"] = g["c_base"]
        c["c_boost_feature"] = "none" if g["c_feat"] == "none" else f"{g['c_feat']}{'>' if g['c_dir'] > 0 else '<'}"
        c["c_vol_gate"] = int(g["c_vol_max"] is not None and g["c_vol_max"] < 1)
        c["o_rule"] = g["o_rule"]
    return c


def recurrence(FR):
    rows = []
    FR = FR.copy()
    genomes = [GA.row_to_genome(r) for _, r in FR.iterrows()]
    cons = pd.DataFrame([concept(g) for g in genomes])
    cons["fold"] = FR.fold.values; cons["run"] = FR.fold.values + "|" + FR.run_seed.astype(str) + "|" + FR.run_island.astype(str)
    runs = cons.run.unique()
    for col in [c for c in cons.columns if c not in ("fold", "run")]:
        for val, sub in cons.groupby(col):
            share_by_run = sub.groupby("run").size() / cons.groupby("run").size()
            present = share_by_run[share_by_run >= 0.25]
            folds = sorted(set(r.split("|")[0] for r in present.index))
            rows.append({"concept": col, "value": str(val), "runs_with>=25%_of_front": len(present), "runs_total": len(runs),
                         "outer_folds_present": len([f for f in folds if f in FOLDS]), "final_run_present": "FINAL_ALL_TO_2026-05-27" in folds,
                         "front_share_all": len(sub) / len(cons)})
    return pd.DataFrame(rows).sort_values(["concept", "runs_with>=25%_of_front"], ascending=[True, False])


# ------------------------------------------------------------------ plateau
def perturbations(g):
    out = []
    for nm, t, dom in GA.SPACE:
        v = g[nm]
        if t in ("num", "opt") and v is not None:
            if nm.startswith("m_") and not g["m_on"]:
                continue
            if (nm.startswith("c_") or nm.startswith("o_")) and not g["c_on"]:
                continue
            if nm == "c_thr" and g["c_feat"] == "none":
                continue
            if nm == "o_thr" and g["o_rule"] != "KEEP_ADVERSE":
                continue
            for f in (-0.2, -0.1, 0.1, 0.2):
                x = dict(g); x[nm] = v * (1 + f) if abs(v) > 0.05 else v + f * 0.25
                out.append((f"{nm} {f:+.0%}", x))
    for nm, lst in (("m_w", O.WINDOWS), ("m_exit", O.M_EXITS), ("c_time", O.C_TIMES), ("o_until", O.O_UNTIL), ("o_w", O.O_W)):
        if (nm.startswith("m_") and not g["m_on"]) or (not nm.startswith("m_") and not g["c_on"]):
            continue
        if nm == "o_until" and g["o_rule"] not in ("KEEP_ADVERSE", "KEEP_UNTIL"):
            continue
        if nm == "o_w" and g["o_rule"] != "EXIT_AFTER":
            continue
        i = lst.index(g[nm])
        for d in (-1, 1):
            if 0 <= i + d < len(lst) and lst[i + d] != "CARRY":
                x = dict(g); x[nm] = lst[i + d]; out.append((f"{nm} {lst[i + d]}", x))
    return out


def plateau(g, bank, mask):
    base = O.run(GA.decode(g), bank)
    bp = O.daily(base, bank.n)[mask]
    b = C.dstats(bp)
    rows = [{"perturbation": "BASE", "avg": b["avg"], "max_dd": b["max_dd"]}]
    for nm, x in perturbations(g):
        p = O.daily(O.run(GA.decode(x), bank), bank.n)[mask]
        s = C.dstats(p)
        rows.append({"perturbation": nm, "avg": s["avg"], "max_dd": s["max_dd"]})
    R = pd.DataFrame(rows)
    pert = R.iloc[1:]
    ok = (pert.avg > 0) & (pert.avg >= 0.5 * b["avg"]) & (pert.max_dd <= 1.5 * max(b["max_dd"], 1.0))
    return R, bool(len(pert) == 0 or ok.all()), float(ok.mean()) if len(pert) else 1.0


def main():
    P = C.build_panel()
    bank = O.Bank(P)
    om = outer_masks(bank)
    Fm, Fc = GP.gp_features(bank)
    res = {}
    # ---------------------------------------------------------------- GA / GP nested outer results
    GS = pd.read_csv(os.path.join(C.T45, "ga", "T45_13_ga_selected.csv"))
    PS = pd.read_csv(os.path.join(C.T45, "gp", "T45_15_gp_selected.csv"))
    ga0 = GS[(GS.sel_rank == 0) & GS.fold.isin(FOLDS)]
    gp0 = PS[(PS.sel_rank == 0) & PS.fold.isin(FOLDS)]
    outer_rows = []
    for nm, D in (("GA", ga0), *[(f"GP|{k}", gp0[gp0.kind == k]) for k in ("GP_MORNING", "GP_CLOSE")]):
        for _, r in D.iterrows():
            outer_rows.append({"method": nm, "fold": r.fold, "inner_median": r.inner_median, "outer_avg": r.outer_avg, "outer_max_dd": r.outer_max_dd,
                               "outer_smb_excess": r.outer_session_matched_beta_excess, "outer_mb_excess": r.outer_matched_beta_excess,
                               "outer_corr_champion": r.outer_corr_champion, "degradation": r.outer_avg - r.inner_median,
                               "genome_or_rule": r.genome if nm == "GA" else r.rule})
    OR = pd.DataFrame(outer_rows)
    # comparators on the same outer blocks
    det = pd.read_parquet(os.path.join(C.T45, "det", "T45_08_overlay_daily.parquet"))
    mld = pd.read_parquet(os.path.join(C.T45, "ml", "T45_10_model_daily.parquet"))
    comp = {}
    for col in det.columns:
        comp[f"DET|{col}"] = det[col].reindex(bank.sess).fillna(0).values
    for col in mld.columns:
        if col.endswith("POS1") and ("ALL_NO_REGIME" in col or "RIDGE" in col):
            comp[f"ML|{col}"] = mld[col].reindex(bank.sess).fillna(0).values
    crow = []
    for nm, p in comp.items():
        ba = {f: float(p[m].mean()) for f, m in om.items()}
        cs = comb_stats(p, bank)
        crow.append({"candidate": nm, **{f"outer_{f}": v for f, v in ba.items()}, "outer_median": float(np.median(list(ba.values()))),
                     "outer_min": float(np.min(list(ba.values()))), "outer_pos": int(np.sum(np.array(list(ba.values())) > 0)), **cs})
    CR = pd.DataFrame(crow)
    # nested GA/GP as a procedure: stitched outer-fold daily P&L (each block traded by the genome evolved without it)
    stitched = {}
    for nm, D in (("GA_NESTED_STITCHED", ga0), ("GP_MORNING_NESTED_STITCHED", gp0[gp0.kind == "GP_MORNING"]),
                  ("GP_CLOSE_NESTED_STITCHED", gp0[gp0.kind == "GP_CLOSE"])):
        p = np.zeros(bank.n)
        for _, r in D.iterrows():
            if nm.startswith("GA"):
                g = json.loads(r.genome); g = {k: (None if v is None else v) for k, v in g.items()}
                pp = O.daily(O.run(GA.decode(g), bank), bank.n)
            else:
                ind = json.loads(r.ind); ind["tree"] = eval(r.tree)  # noqa: S307
                ge, mt, ct = GP.to_overlay(ind, Fm, Fc)
                pp = O.daily(O.run(ge, bank, 1.0, mt, ct), bank.n)
            p[om[r.fold]] = pp[om[r.fold]]
        stitched[nm] = p
        span = np.any(np.stack(list(om.values())), 0)
        ba = {f: float(p[m].mean()) for f, m in om.items()}
        crow.append({"candidate": nm, **{f"outer_{f}": v for f, v in ba.items()}, "outer_median": float(np.median(list(ba.values()))),
                     "outer_min": float(np.min(list(ba.values()))), "outer_pos": int(np.sum(np.array(list(ba.values())) > 0)),
                     **comb_stats(p, bank, span)})
    CR = pd.DataFrame(crow)
    CR.to_csv(f"{OUT}/T45_outer_block_comparison.csv", index=False)
    OR.to_csv(f"{OUT}/T45_13_nested_outer_folds.csv", index=False)
    # ---------------------------------------------------------------- recurrence
    FR = pd.read_parquet(os.path.join(C.T45, "ga", "T45_13_ga_island_fronts.parquet"))
    REC = recurrence(FR); REC.to_csv(f"{OUT}/T45_13_ga_recurrence.csv", index=False)
    sel_con = pd.DataFrame([{**concept(GA.row_to_genome(pd.Series({f"g_{k}": v for k, v in json.loads(r.genome).items()}))), "fold": r.fold}
                            for _, r in GS[GS.sel_rank == 0].iterrows()])
    sel_con.to_csv(f"{OUT}/T45_13_ga_selected_concepts.csv", index=False)
    # behaviour clustering of selected GA genomes (full-history daily P&L correlation)
    beh = {}
    for _, r in GS[GS.sel_rank == 0].iterrows():
        g = json.loads(r.genome)
        beh[r.fold] = O.daily(O.run(GA.decode(g), bank), bank.n)
    BC = pd.DataFrame(beh).corr(); BC.to_csv(f"{OUT}/T45_13_ga_selected_behaviour_corr.csv")
    # ---------------------------------------------------------------- final GA / GP candidates: plateau + full metrics
    allm = np.ones(bank.n, bool); allm[:20] = False
    fin = {}
    gfin = GS[(GS.fold == "FINAL_ALL_TO_2026-05-27") & (GS.sel_rank == 0)]
    if len(gfin):
        g = json.loads(gfin.iloc[0].genome)
        PL, ok, share = plateau(g, bank, allm)
        PL.to_csv(f"{OUT}/T45_14_ga_final_plateau.csv", index=False)
        fin["GA_FINAL"] = {"genome": g, "plateau_pass": ok, "plateau_share_ok": share, "concept": concept(g)}
        # plateau of each outer-fold selection on its own training window
        prow = []
        for _, r in ga0.iterrows():
            gg = json.loads(r.genome)
            s1 = int(np.argmax(om[r.fold])); m = np.zeros(bank.n, bool); m[20:s1] = True
            _, okf, sh = plateau(gg, bank, m)
            prow.append({"fold": r.fold, "plateau_pass": okf, "share_ok": sh})
        pd.DataFrame(prow).to_csv(f"{OUT}/T45_14_ga_fold_plateau.csv", index=False)
        fin["GA_FOLD_PLATEAU_PASS_COUNT"] = int(sum(p["plateau_pass"] for p in prow))
    for kind in ("GP_MORNING", "GP_CLOSE"):
        x = PS[(PS.fold == "FINAL_ALL_TO_2026-05-27") & (PS.sel_rank == 0) & (PS.kind == kind)]
        if len(x):
            fin[f"{kind}_FINAL"] = {"rule": x.iloc[0].rule, "ind": x.iloc[0].ind, "tree": x.iloc[0].tree}
    # ---------------------------------------------------------------- candidate library for combination / scaling
    import t45_03_det as DET
    lib = {}
    for nm in ("CONTROL_A unconditional +1 locked 16:15->next open", "S1 = CONTROL_A (late-RTH unconditional carry, decide 15:45)",
               "CONTROL_B GAP_LOCK<=-0.5ATR +1 09:32->16:00", "S2 gap-down rebound + crash guard", "S3 opening-flush rebound + crash guard",
               "S4 gap+flush combined + crash guard", "S5b late boost (V6 champion long -> 2) [informed by T45_03]",
               "S6b S1 + open manager (keep if GAP_LOCK<=-0.75 until 12:00)", "S6c S1 + gap-down rebound (combined close-build + open)"):
        for inst in ("ES", "MNQ", "BOTH"):
            lib[f"DET|{nm.split(' ')[0]}|{inst}"] = ("genome", dict(DET.SPECS[nm], inst=inst))
    if "GA_FINAL" in fin:
        lib["GA|FINAL"] = ("genome", GA.decode(fin["GA_FINAL"]["genome"]))
    for kind in ("GP_MORNING", "GP_CLOSE"):
        if f"{kind}_FINAL" in fin:
            ind = json.loads(fin[f"{kind}_FINAL"]["ind"]); ind["tree"] = eval(fin[f"{kind}_FINAL"]["tree"])  # noqa: S307
            lib[f"GP|{kind}|FINAL"] = ("gp", ind)
    rows, per = [], []
    for nm, (kind, obj) in lib.items():
        for cap in (1, 2, 3):
            O.QMAX = cap
            if kind == "genome":
                ge = dict(obj)
                if cap == 3:
                    ge["m_q"] = 3 if ge["m_q"] == 2 else ge["m_q"]; ge["c_boost"] = 3 if ge["c_boost"] == 2 else ge["c_boost"]
                r1 = O.run(ge, bank); r4 = O.run(ge, bank, 4.0)
            else:
                ind = dict(obj)
                if cap == 3:
                    ind["m_q"] = 3 if ind.get("m_q") == 2 else ind.get("m_q"); ind["c_boost"] = 3 if ind.get("c_boost") == 2 else ind.get("c_boost")
                ge, mt, ct = GP.to_overlay(ind, Fm, Fc)
                r1 = O.run(ge, bank, 1.0, mt, ct); r4 = O.run(ge, bank, 4.0, mt, ct)
            p = O.daily(r1, bank.n)
            mt_ = S.metrics(r1, bank.bench, allm)
            cs = comb_stats(p, bank, allm)
            maxq = {C.INSTS[k]: int(max(r["q_end"].max(), r["q_rth"].max())) for k, r in r1.items()}
            locked_worst = sum(np.nanmin(np.where(r["q_end"] > 0, r["q_end"] * np.r_[np.diff(bank.sims[k].FP[:, 0]), np.nan] * 0 +
                                                   r["q_end"] * (np.r_[bank.sims[k].FP[1:, 0], np.nan] - bank.sims[k].FP[:, C.LOCK_FILL_BAR]) * C.PV[k], 0))
                               for k, r in r1.items())
            o = {"candidate": nm, "cap": cap, **{k: mt_[k] for k in ("avg", "total", "max_dd", "worst", "matched_beta_excess",
                                                                    "session_matched_beta_excess", "sides", "cost", "corr_champion",
                                                                    "worst20_champion_overlay_loss_share", "loss_day_overlap")},
                 **cs, "SLIP4_total": float(O.daily(r4, bank.n)[allm].sum()), "max_contracts": json.dumps(maxq), "worst_locked_night_$": float(locked_worst),
                 "avg_locked_contracts": float(sum(r["q_end"][allm].mean() for r in r1.values()))}
            ba = {f: float(p[m].mean()) for f, m in om.items()}
            o.update({f"outer_{f}": v for f, v in ba.items()}); o["outer_median"] = float(np.median(list(ba.values())))
            o["outer_pos"] = int(np.sum(np.array(list(ba.values())) > 0))
            for pp in ("Y2020", "Y2022", "FORMER_HOLDOUT_USED"):
                m = C.mask_period(bank.sess, pp)
                c2 = comb_stats(p, bank, m)
                o[f"{pp}_overlay_avg"] = float(p[m].mean()); o[f"{pp}_comb_avg"] = c2["comb_avg"]; o[f"{pp}_comb_mdd"] = c2["comb_mdd"]
                o[f"{pp}_champ_avg"] = c2["champ_avg"]; o[f"{pp}_champ_mdd"] = c2["champ_mdd"]
            rows.append(o)
            if cap == 2:
                for pp in C.PERIODS:
                    m = C.mask_period(bank.sess, pp)
                    per.append({"candidate": nm, "period": pp, "overlay_avg": float(p[m].mean()), **comb_stats(p, bank, m)})
            res[(nm, cap)] = p
    O.QMAX = 2
    L = pd.DataFrame(rows); L.to_csv(f"{OUT}/T45_19_20_combination_scaling.csv", index=False)
    pd.DataFrame(per).to_csv(f"{OUT}/T45_21_22_periods.csv", index=False)
    # ---------------------------------------------------------------- multi-module combinations (sum of daily P&L; integer cap checked)
    combos = {"Champion + gap rebound (S2 BOTH)": ["DET|S2|BOTH"], "Champion + opening flush (S3 BOTH)": ["DET|S3|BOTH"],
              "Champion + overnight carry (S1 BOTH)": ["DET|S1|BOTH"], "Champion + gap + flush (S2+S3 BOTH)": ["DET|S2|BOTH", "DET|S3|BOTH"],
              "Champion + carry + open manager (S6b BOTH)": ["DET|S6b|BOTH"], "Champion + carry + gap rebound (S6c BOTH)": ["DET|S6c|BOTH"]}
    if "GA|FINAL" in lib:
        combos["Champion + best GA overlay"] = ["GA|FINAL"]
    for kind in ("GP_MORNING", "GP_CLOSE"):
        if f"GP|{kind}|FINAL" in lib:
            combos[f"Champion + best {kind} overlay"] = [f"GP|{kind}|FINAL"]
    if "GP|GP_MORNING|FINAL" in lib and "GP|GP_CLOSE|FINAL" in lib:
        combos["Champion + GP morning + GP close (evolved combined)"] = ["GP|GP_MORNING|FINAL", "GP|GP_CLOSE|FINAL"]
    ml = mld[[c for c in mld.columns if c.startswith("A_CARRY|RIDGE|ALL_NO_REGIME|POS1")]]
    if ml.shape[1]:
        res[("ML|A_CARRY_RIDGE_POS1", 2)] = ml.iloc[:, 0].reindex(bank.sess).fillna(0).values
        combos["Champion + best ML overlay (carry Ridge POS1; walk-forward from 2021-05)"] = ["ML|A_CARRY_RIDGE_POS1"]
    crow = []
    for nm, parts in combos.items():
        p = sum(res[(x, 2)] for x in parts)
        cs = comb_stats(p, bank, allm)
        ba = {f: float(p[m].mean()) for f, m in om.items()}
        crow.append({"combination": nm, **cs, "outer_median": float(np.median(list(ba.values()))), "outer_pos": int(np.sum(np.array(list(ba.values())) > 0)),
                     **{f"outer_{f}": v for f, v in ba.items()},
                     **{f"{pp}_comb_avg": comb_stats(p, bank, C.mask_period(bank.sess, pp))["comb_avg"] for pp in ("Y2020", "Y2022", "FORMER_HOLDOUT_USED")}})
    crow.insert(0, {"combination": "Champion only", **comb_stats(np.zeros(bank.n), bank, allm)})
    CB = pd.DataFrame(crow); CB.to_csv(f"{OUT}/T45_19_module_combination.csv", index=False)
    json.dump(fin, open(f"{OUT}/T45_ga_gp_final.json", "w"), indent=1, default=str)
    print(OR.to_string()); print(CR.sort_values("outer_median").tail(25).to_string()); print(REC.head(60).to_string())
    print(L[L.cap == 2][["candidate", "avg", "max_dd", "comb_ret_dd", "champ_ret_dd", "incr_avg", "corr", "outer_median", "outer_pos", "comb_mdd", "comb_worst"]].to_string())
    print(CB.to_string()); print(json.dumps({k: v for k, v in fin.items() if k != "genome"}, default=str)[:2000])


if __name__ == "__main__":
    main()
