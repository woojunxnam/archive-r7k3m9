"""HIGH-EXPOSURE PROGRAM close-out: TEST57 stitched gate, TEST60 offline-bandit diagnostic, CORE/GROWTH/AGGRESSIVE frontier (report-only
composition grid of FROZEN components), $150k envelope maxima, margin-only ceiling, V5.3.3 comparison, $600/day frontier, registries,
freeze + OOS rules, final status.  No component is re-tuned here; the grid is a reporting frontier, not a selection."""
import datetime
import glob
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import hx_carrier as X  # noqa: E402
import prog_common as P  # noqa: E402
import prog_ga as PG  # noqa: E402
import t47_engine as E  # noqa: E402
from t47_06_final import first_rth_after  # noqa: E402
from t53_run import module_trades, simulate  # noqa: E402

FZ = os.path.join(H.HX, "freeze"); os.makedirs(FZ, exist_ok=True)


def main():
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = es.pn.sess; full = sess >= H.START; m21 = sess >= H.SPAN21
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess); pMn = np.nan_to_num(pM, nan=3.0)
    # ---------------- TEST57 stitched outer (GA-EXPOSURE)
    PG._init("lane_hx"); ctx = PG._ctx
    S = pd.read_csv(os.path.join(C45.ROOT, "out/test57/ga/GA-EXPOSURE_selected.csv"))
    st = np.zeros(len(sess)); tv = []; cl = []
    for name, a, b in C45.OUTER:
        r = S[(S.fold == name) & (S.sel_rank == 0)]
        s0 = int(np.searchsorted(sess.values, np.datetime64(a))); s1 = int(np.searchsorted(sess.values, np.datetime64(b), side="right"))
        if not len(r) or not isinstance(r.iloc[0].get("genome"), str):
            cl.append("NONE"); continue
        g = json.loads(r.iloc[0].genome); cl.append(ctx["L"].cluster(g))
        rr = ctx["L"].run_carrier(g, ctx); st[s0:s1] = rr["daily"][s0:s1]; tv.append(ctx["L"].timing(ctx, rr, s0, s1))
    g57 = H.lane_eval("C43 + GA-EXPOSURE stitched", champ + st, champ, sess, 0.40 * H.NLV, 0.40 * H.NLV, float(np.mean(tv)) if tv else 0.0,
                      {"plateau_pass": False, "stress4_pos": False})
    g57["fold_clusters"] = " ; ".join(cl)
    # ---------------- TEST60 offline bandit diagnostic (actions {1,3,5} units; linear reward -> sign policy)
    R60 = pd.read_csv(os.path.join(C45.ROOT, "out/test60/T60_results.csv"))
    bandit = {"condition_met": bool(((R60.policy == "ML-B_ADD") & (R60.years_pos >= 4)).any()),
              "note": "reward is linear in exposure, so the contextual bandit's greedy action is always the max or min tier by the sign of the predicted "
                      "return: it reduces to ML-B/ML-C sign policies already evaluated (best RIDGE ML-B timing +7.5 $/day, rank-IC 0.025, 2/6 years carry it)",
              "result": "NO robust state-dependent marginal exposure value"}
    # ---------------- frozen components (daily $)
    TR = module_trades(nq, sess)

    def t53(k):
        T = 3 + 2 * (k - 1)
        ca = np.minimum(2, np.floor(np.maximum(0, T - pMn) / k)).astype(int)
        daily, L, cnt = simulate(nq, TR, 2, -1000.0, cap_arr=ca)
        tot = k * sum(daily.values()); tot[:s21] = 0
        return tot, k * cnt
    comp_t53 = {k: t53(k) for k in (0, 1, 2, 3, 5) if k > 0}
    comp_t53[0] = (np.zeros(len(sess)), np.zeros_like(comp_t53[1][1]))
    beta = {u: X.carrier(mks, bk, [u] * 4) for u in (0, 2, 3, 5, 8, 12)}
    rows = []
    lock = E.J1615 - 1
    for kc, k53, bu in itertools.product((1, 2), (0, 1, 2, 3, 5), (0, 2, 3, 5, 8, 12)):
        d = kc * champ + comp_t53[k53][0] + beta[bu]["daily"]
        qN_on = kc * np.nan_to_num(pM[:, lock]) + comp_t53[k53][1][:, lock] + beta[bu]["qN"]
        qE_on = kc * np.nan_to_num(pE[:, lock]) + beta[bu]["qE"]
        mo = (qE_on * bk.m_on["ES"] + qN_on * bk.m_on["MNQ"])[full]
        r = P.risk(d[full])
        rows.append({"C43_scale": kc, "TEST53_lots": k53, "beta_units": bu, "avg_day_full": r["avg_day"], "avg_day_2021": float(d[m21].mean()),
                     "max_dd": r["max_dd"], "worst_day": r["worst_day"], "ret_dd": r["ret_dd"], "peak_on_margin_frac": float(mo.max() / H.NLV),
                     "avg_on_margin_frac": float(mo.mean() / H.NLV), "peak_MES": int(qE_on[full].max()), "peak_MNQ_lock": int(qN_on[full].max()),
                     "beta_timing_day": float(X.decompose(mks, bk, beta[bu], sess, full)["TIMING_VALUE_day"]) if bu else 0.0,
                     "CORE_env": r["max_dd"] <= 15000 and r["worst_day"] >= -3000, "GROWTH_env": r["max_dd"] <= 30000 and r["worst_day"] >= -6000,
                     "AGGR_env": r["max_dd"] <= 50000 and r["worst_day"] >= -10000, "margin_ok_70": bool(mo.max() <= 0.70 * H.NLV)})
    F = pd.DataFrame(rows)
    F["label"] = "C43x" + F.C43_scale.astype(str) + " + T53x" + F.TEST53_lots.astype(str) + " + BETA" + F.beta_units.astype(str)
    F.to_csv(f"{H.HX}/CORE_GROWTH_AGGRESSIVE_FRONTIER.csv", index=False)
    F.to_csv(f"{H.HX}/ADAPTIVE_EXPOSURE_FRONTIER.csv", index=False)
    # pareto (avg_day_full, max_dd, worst_day)
    par = []
    for i, r in F.iterrows():
        dom = ((F.avg_day_full >= r.avg_day_full) & (F.max_dd <= r.max_dd) & (F.worst_day >= r.worst_day) &
               ((F.avg_day_full > r.avg_day_full) | (F.max_dd < r.max_dd) | (F.worst_day > r.worst_day))).any()
        par.append(not dom)
    F["pareto"] = par
    env_max = {}
    for env in ("CORE_env", "GROWTH_env", "AGGR_env"):
        f = F[F[env] & F.margin_ok_70]
        b = f.sort_values("avg_day_full", ascending=False).iloc[0]
        env_max[env] = {"label": b.label, "avg_day_full": round(b.avg_day_full, 2), "avg_day_2021": round(b.avg_day_2021, 2), "max_dd": round(b.max_dd), "worst_day": round(b.worst_day)}
    # margin-only ceiling: max constant beta at 70% overnight margin (MNQ-only and ES-only)
    per = {k: np.nan_to_num(np.r_[np.nan, np.diff(m.pn.se)] * m.pv) for k, m in mks.items()}
    ceil = {}
    for k in ("ES", "MNQ"):
        q = int(np.floor(0.70 * H.NLV / bk.m_on[k][full].max()))
        q = min(q, 24)
        d = q * per[k] - 0.0
        r = P.risk(d[full])
        ceil[k] = {"contracts": q, "avg_day_full": round(r["avg_day"], 2), "max_dd": round(r["max_dd"]), "worst_day": round(r["worst_day"])}
    # V5.3.3 reference (repo out/02_BASELINE_PERIODS.csv, MES full history)
    v = pd.read_csv(os.path.join(C45.ROOT, "out/02_BASELINE_PERIODS.csv")).set_index("period")
    v533 = {"avg_day": round(v.loc["FULL", "avg_daily"], 2), "max_dd": round(v.loc["FULL", "max_dd"]), "worst_day": round(v.loc["FULL", "worst_day"]),
            "avg_MES": round(v.loc["FULL", "avg_mes"], 1), "max_MES": int(v.loc["FULL", "max_mes"]), "pre2023_avg": round(v.loc["PRE_2023", "avg_daily"], 2),
            "from2023_avg": round(v.loc["2023+", "avg_daily"], 2), "timing": "tactical timing minus friction NEGATIVE (TEST43 decomposition); return = long beta"}
    # ---------------- comparison table
    t55 = pd.read_csv(os.path.join(C45.ROOT, "out/test55/T55_results.csv")); g55 = t55[t55.candidate.str.contains("PRIMARY")].iloc[0]
    t61 = pd.read_csv(os.path.join(C45.ROOT, "out/test61/T61_results.csv")); g61 = t61.iloc[0]
    # predeclared TEST61 selection rule: higher full-history avg/day among GROWTH-passing {TEST55, TEST61}
    gr = g61 if (bool(g61.GROWTH) and g61.avg_day_full > g55.avg_day_full) else g55
    GROWTH_ID = "C43-GROWTH-T61 (C43x2 + TEST53 residual, total MNQ<=6)" if gr is g61 else "C43-GROWTH-T55"
    const_equiv = F[(F.C43_scale == 1) & (F.TEST53_lots == 0)]
    cmp_rows = [{"portfolio": "C43-CORE", "avg_day": P.risk(champ[full])["avg_day"], "max_dd": P.risk(champ[full])["max_dd"], "worst_day": P.risk(champ[full])["worst_day"],
                 "peak_on_margin": 0.123, "timing_value_day": "C43 alpha (validated)"},
                {"portfolio": "C43-GROWTH-T55 (C43 + TEST53 residual total MNQ<=3)", "avg_day": g55.avg_day_full, "max_dd": g55.max_dd, "worst_day": g55.worst_day,
                 "peak_on_margin": g55.peak_on_margin_frac, "timing_value_day": g55.timing_value_day},
                {"portfolio": GROWTH_ID, "avg_day": gr.avg_day_full, "max_dd": gr.max_dd, "worst_day": gr.worst_day,
                 "peak_on_margin": gr.peak_on_margin_frac, "timing_value_day": gr.timing_value_day},
                {"portfolio": "V5.3.3 (MES full history, reference)", "avg_day": v533["avg_day"], "max_dd": v533["max_dd"], "worst_day": v533["worst_day"], "peak_on_margin": np.nan,
                 "timing_value_day": "negative"},
                {"portfolio": "constant matched long 3 units (beta)", "avg_day": float(beta[3]["daily"][full].mean()), "max_dd": P.risk(beta[3]["daily"][full])["max_dd"],
                 "worst_day": P.risk(beta[3]["daily"][full])["worst_day"], "peak_on_margin": float(beta[3]["on_margin"][full].max() / H.NLV), "timing_value_day": 0.0}]
    CMP = pd.DataFrame(cmp_rows); CMP.to_csv(f"{H.HX}/V533_COMPARISON.csv", index=False)
    # beta/alpha decomposition for the frozen portfolios
    dec = []
    for nm, qE, qN, d in (("C43-CORE", st_pos := None, None, champ),):
        pass
    c43d = pd.read_csv(os.path.join(C45.ROOT, "out/t44/daily_CHAMPION_CONTROL_V1.csv"), index_col=0, parse_dates=True).reindex(sess)
    b43 = (c43d.pES.fillna(0).values[full].mean() * per["ES"][full].mean() + c43d.pMNQ.fillna(0).values[full].mean() * per["MNQ"][full].mean())
    t53d = comp_t53[1][0]; cnt1 = comp_t53[1][1]
    b53 = cnt1[:, ::5].mean(1)[m21].mean() * per["MNQ"][m21].mean()
    DEC = pd.DataFrame([{"portfolio": "C43-CORE", "net_day": champ[full].mean(), "PASSIVE_BETA_day": b43, "ALPHA_TIMING_day": champ[full].mean() - b43},
                        {"portfolio": "TEST53 residual increment (2021+)", "net_day": t53d[m21].mean(), "PASSIVE_BETA_day": b53, "ALPHA_TIMING_day": t53d[m21].mean() - b53},
                        {"portfolio": "BETA carrier CONST 3", **{k: X.decompose(mks, bk, beta[3], sess, full)[k2] for k, k2 in (("net_day", "net_day"), ("PASSIVE_BETA_day", "PASSIVE_BETA_day"), ("ALPHA_TIMING_day", "TIMING_VALUE_day"))}}])
    DEC.to_csv(f"{H.HX}/BETA_ALPHA_DECOMPOSITION.csv", index=False)
    # ---------------- $600 frontier for the growth portfolio
    g_avg = gr.avg_day_full; g_dd = gr.max_dd
    scale600 = 600 / g_avg
    fr600 = pd.DataFrame([{"target_day": t, "growth_scale": t / g_avg, "est_max_dd": g_dd * t / g_avg, "capital_same_pct_dd": H.NLV * t / g_avg} for t in (100, 150, 200, 300, 400, 600)])
    fr600.to_csv(f"{H.HX}/USD600_FRONTIER.csv", index=False)
    # ---------------- registries (HX folder copies + program registries)
    P.reg_append("AUTONOMOUS_TEST_REGISTRY", [
        {"test": "TEST57", "hypothesis": "GA-EXPOSURE nested over Beta-Carrier-V2 grammar", "prereg_hash": open(os.path.join(C45.ROOT, "out/test57/TEST57_PREREGISTRATION.json.sha256")).read()[:16],
         "result": f"FAIL (outer folds {g57['folds_pos']}/5, timing value {np.mean(tv):.1f} $/day; 2022 -59 $/day; selections = MNQ beta 5 units)", "survivor_count": 0,
         "best_clue": "none: GA rediscovers constant MNQ beta", "next_test_reason": "TEST58/59/60 then synthesis"},
        {"test": "TEST58", "hypothesis": "TEST53 lot-size ladder k=1,2,3,5 in residual architecture", "prereg_hash": open(os.path.join(C45.ROOT, "out/test58/TEST58_PREREGISTRATION.json.sha256")).read()[:16],
         "result": "k=2 FAIL GROWTH on the preregistered k-neighbour plateau (linear scaling makes k=1 < 60% of k=2 by construction); ret/DD 0.0074->0.0053->0.0041->0.0030",
         "survivor_count": 0, "best_clue": "marginal value per extra TEST53 lot ~ +21 $/day, +7-9k MaxDD, -1.3k worst day (linear, no diminishing returns)", "next_test_reason": "overnight value (TEST59)"},
        {"test": "TEST59", "hypothesis": "hold/overnight value of validated inventory", "prereg_hash": open(os.path.join(C45.ROOT, "out/test59/TEST59_PREREGISTRATION.json.sha256")).read()[:16],
         "result": "M2 overnight hold > 16:15 exit (TEST55 kept); beta carrier: overnight >> intraday-only in return, worst day barely improves", "survivor_count": 0,
         "best_clue": "MNQ locked-gap worst -2005/contract, ES -1170", "next_test_reason": "marginal exposure ML (TEST60)"},
        {"test": "TEST60", "hypothesis": "marginal-exposure ML (add / reduce carrier units)", "prereg_hash": open(os.path.join(C45.ROOT, "out/test60/TEST60_PREREGISTRATION.json.sha256")).read()[:16],
         "result": "NO (rank-IC <= 0.025; best Ridge add +7.5 $/day timing carried by 2 years; offline bandit reduces to the same sign policy)", "survivor_count": 0,
         "best_clue": "best up-days cluster in high-vol drawdowns (gap map V2) -> state de-risking loses rebounds", "next_test_reason": "STOP: exposure timing saturated"}], key="test")
    P.reg_append("REJECTED_FAMILY_REGISTRY", [
        {"family": "ga_exposure_policy_beta_carrier", "mechanism": "nested GA over state thresholds/tier maps/vol-target/governor/overnight", "test": "TEST57",
         "reason_rejected": "outer timing negative, 2022 loss, selects constant MNQ beta", "sample_size": "90k genomes", "outer_fold_result": f"{g57['folds_pos']}/5",
         "retest_forbidden": "YES", "reopen_requires": "new causal information not in daily OHLC state"},
        {"family": "marginal_exposure_ml_daily", "mechanism": "ML value of +/- beta units at the open", "test": "TEST60", "reason_rejected": "rank-IC <= 0.025",
         "sample_size": "~1300 days", "outer_fold_result": "<= 4/6 yrs, concentrated", "retest_forbidden": "YES", "reopen_requires": "-"}], key="family")
    P.reg_append("SHADOW_CLUE_REGISTRY", [
        {"clue_id": "HX_RISK_NOT_MARGIN", "source_test": "T55 capacity audit", "mechanism": "C43 uses <=12% overnight margin; binding constraint = worst-day gap tail",
         "why_interesting": "~-2k worst day per MES-eq unit of overnight beta; margin allows ~10x more", "why_not_promotable": "fact, not alpha",
         "future_prereg_test": "tail hedging is outside the long-only ES/NQ axis"},
        {"clue_id": "HX_T53_LINEAR_SCALING", "source_test": "TEST58", "mechanism": "TEST53 lots scale linearly", "why_interesting": "k=2: +42.6 $/day incr, MaxDD 16.3k, worst -3.7k",
         "why_not_promotable": "preregistered plateau (k-neighbours) fails by construction", "future_prereg_test": "forward OOS of TEST55 first; a lot-multiplier test only with a ret/DD-stability plateau declared in advance"}], key="clue_id")
    for src, dst in (("AUTONOMOUS_TEST_REGISTRY", "RESEARCH_REGISTRY.csv"), ("SHADOW_CLUE_REGISTRY", "CLUE_REGISTRY.csv"), ("REJECTED_FAMILY_REGISTRY", "REJECT_REGISTRY.csv")):
        P.reg_load(src).to_csv(os.path.join(H.HX, dst), index=False)
    B = P.reg_load("RESEARCH_BUDGET_LOG")
    hxb = B[B.test.isin([f"TEST{i}" for i in range(55, 61)])]
    budget = {"TOTAL_HYPOTHESES": int(B.hypotheses.sum()), "TOTAL_ML_CONFIGS": int(B.ml_configs.sum()), "TOTAL_GA_GENOMES": int(B.valid_genomes.sum()),
              "HX_PROGRAM_HYPOTHESES": int(hxb.hypotheses.sum()), "HX_PROGRAM_GENOMES": int(hxb.valid_genomes.sum()), "HX_PROGRAM_ML_CONFIGS": int(hxb.ml_configs.sum())}
    # ---------------- freeze
    now = datetime.datetime.now(datetime.timezone.utc); oos = first_rth_after(now)
    files = sorted(glob.glob(os.path.join(C45.SRC, "hx_*.py")) + glob.glob(os.path.join(C45.SRC, "t5[5-9]_*.py")) + glob.glob(os.path.join(C45.SRC, "t6[01]_*.py"))
                   + glob.glob(os.path.join(C45.SRC, "lane_hx.py")) + glob.glob(os.path.join(C45.SRC, "t53_run.py")) + glob.glob(os.path.join(C45.SRC, "prog_ga.py"))
                   + glob.glob(os.path.join(C45.ROOT, "out", "test5[5-9]", "*PREREG*")) + glob.glob(os.path.join(C45.ROOT, "out", "test6[01]", "*PREREG*"))
                   + [os.path.join(H.HX, "hx_gate_spec.json"), os.path.join(H.HX, "hx_gate_spec.json.sha256")])
    evid = sorted(p for p in glob.glob(os.path.join(H.HX, "*")) if os.path.isfile(p))
    freeze = {"program": "TEST55+ HIGH-EXPOSURE ES/NQ LONG PROGRAM", "freeze_timestamp_utc": now.isoformat(timespec="seconds"), "research_data_end": "2026-05-27",
              "FINAL_CORE_PORTFOLIO": "C43-CORE (unchanged)",
              "FINAL_GROWTH_PORTFOLIO": {"id": GROWTH_ID, "definition": "C43 x2 integer contracts (priority) + TEST53 ensemble (M1-M4 frozen per-fold genomes, 1 MNQ/lot, "
                                                                          "ensemble cap 2, day governor -1000) filling residual MNQ capacity so that total MNQ at entry <= 6",
                                         "prereg": "TEST61 cbd4c6e8 (selection rule predeclared)", "alternate_growth": "C43-GROWTH-T55 (C43x1 + TEST53 residual, total <= 3; TEST55 0a5ec770)"},
              "FINAL_AGGRESSIVE_RESEARCH_PORTFOLIO": {"id": "C43 + TEST53 x3 residual (report-only)", "note": "AGGRESSIVE lane is research-only; never promoted"},
              "gate_spec_sha256": open(os.path.join(H.HX, "hx_gate_spec.json.sha256")).read().strip(), "budget": budget,
              "source_sha256": {os.path.relpath(p, C45.ROOT): P.sha(p) for p in files if os.path.isfile(p)},
              "evidence_sha256": {os.path.relpath(p, C45.ROOT): P.sha(p) for p in evid},
              "prior_program_freeze_sha256": open(os.path.join(P.PROG, "freeze", "FINAL_PROGRAM_FREEZE.sha256")).read(),
              "live_authorization": "NO", "portfolio_membership_changed": "NO"}
    fp = os.path.join(FZ, "FINAL_GROWTH_PROGRAM_PRE_OOS_FREEZE.json"); json.dump(freeze, open(fp, "w"), indent=1, default=str)
    rules = {"FINAL_GROWTH_PROGRAM_OOS_START": oos, "rule": "first full RTH session strictly after the freeze timestamp", "freeze_timestamp_utc": freeze["freeze_timestamp_utc"],
             "evaluate": {"C43-CORE": "monitor", "FINAL_GROWTH": "forward shadow: promote to live consideration only after >= 250 full RTH OOS sessions with incremental "
                          "avg/day > 0 vs C43, combined MaxDD <= 15k, worst day >= -3k, total MNQ at entry <= 3, no margin breach, and matched excess > 0",
                          "AGGRESSIVE": "report only, never promoted from this program", "ALTERNATE_GROWTH_T55": "forward shadow (report)"},
             "no_retuning": True, "excluded": "2026-05-28 .. OOS_START-1 never used", "live_authorization": "NO"}
    rp = os.path.join(FZ, "FINAL_GROWTH_PROGRAM_OOS_RULES.json"); json.dump(rules, open(rp, "w"), indent=1)
    hf, hr = P.sha(fp), P.sha(rp)
    open(os.path.join(FZ, "FINAL_GROWTH_PROGRAM_FREEZE.sha256"), "w").write(f"{hf}  {os.path.basename(fp)}\n{hr}  {os.path.basename(rp)}\n")
    c43r = P.risk(champ[full])
    aud = pd.read_csv(os.path.join(H.HX, "CAPACITY_AUDIT.csv"))
    om = aud[(aud.portfolio == "C43-CORE") & aud.metric.str.startswith("overnight")].iloc[0]
    status = {"C43_CORE_AVG_DAY": round(c43r["avg_day"], 2), "C43_CORE_MAXDD": round(c43r["max_dd"]), "C43_CORE_WORST_DAY": round(c43r["worst_day"]),
              "C43_GROWTH_AVG_DAY": round(g55.avg_day_full, 2), "C43_GROWTH_AVG_DAY_2021": round(g55.avg_day_2021, 2), "C43_GROWTH_MAXDD": round(g55.max_dd),
              "C43_GROWTH_WORST_DAY": round(g55.worst_day), "C43_GROWTH_FORWARD_STATUS": "FORWARD_SHADOW (TEST55 GROWTH-lane PASS; unopened OOS); superseded as FINAL_GROWTH by TEST61 per predeclared rule",
              "C43_CURRENT_PEAK_MES": 3, "C43_CURRENT_PEAK_MNQ": 3, "C43_PEAK_MARGIN_USAGE": round(float(om["max"]), 3), "C43_AVG_MARGIN_USAGE": round(float(om["mean"]), 3),
              "ACCOUNT_IS_MARGIN_CONSTRAINED": "NO", "ACCOUNT_IS_RISK_CONSTRAINED": "YES",
              **{f"{t}_RESULT": r for t, r in zip(P.reg_load("AUTONOMOUS_TEST_REGISTRY").test, P.reg_load("AUTONOMOUS_TEST_REGISTRY").result) if t >= "TEST55"},
              "BEST_ADAPTIVE_EXPOSURE_POLICY": "NONE (every state/ML/GA exposure policy had timing value <= 0 or failed nested folds)",
              "BEST_AVG_MES": 1.5, "BEST_MAX_MES": 6, "BEST_AVG_MNQ": round(2 * float(aud[(aud.portfolio == 'C43-CORE') & (aud.metric.str.startswith('MNQ'))]['mean'].iloc[0]) + 0.6, 2),
              "BEST_MAX_MNQ": int(g61.get("peak_total_MNQ", 8)), "BEST_MARGIN_UTILIZATION": round(float(gr.peak_on_margin_frac), 3),
              "BEST_BETA_CARRIER_AVG_DAY": round(float(beta[3]["daily"][full].mean()), 2), "BEST_BETA_CARRIER_MAXDD": round(P.risk(beta[3]["daily"][full])["max_dd"]),
              "BEST_BETA_CARRIER_TIMING_VALUE": "<= 0 (constant carriers ~0 by construction; every adaptive carrier negative)",
              "BEST_BETA_CARRIER_MATCHED_BETA_EXCESS": 0, "BEST_GROWTH_PORTFOLIO_COMPONENTS": GROWTH_ID,
              "BEST_GROWTH_PORTFOLIO_AVG_DAY": round(gr.avg_day_full, 2), "BEST_GROWTH_PORTFOLIO_MAXDD": round(gr.max_dd), "BEST_GROWTH_PORTFOLIO_WORST_DAY": round(gr.worst_day),
              "BEST_GROWTH_PORTFOLIO_RET_DD": round(gr.ret_dd, 4), "INCREMENT_VS_C43": round(gr.incr_avg_day_2021, 2),
              "MAX_$150K_AVG_DAY_CORE_ENVELOPE": env_max["CORE_env"], "MAX_$150K_AVG_DAY_GROWTH_ENVELOPE": env_max["GROWTH_env"],
              "MAX_$150K_AVG_DAY_AGGRESSIVE_ENVELOPE": env_max["AGGR_env"], "MAX_$150K_AVG_DAY_MARGIN_ONLY": ceil,
              "24_MES_CAP_EVER_SELECTED": "NO", "24_MNQ_CAP_EVER_SELECTED": "NO",
              "WHY_HIGH_EXPOSURE_IS_OR_IS_NOT_USEFUL": "Margin is not binding (C43 <=12% NLV). The binding constraint is the locked-overnight / crash-day tail "
                                                      "(~-2k worst day per MES-eq unit of beta). Extra exposure only adds beta; no state, ML or GA policy produced positive "
                                                      "timing value, because the best up-days cluster inside high-vol drawdowns. High exposure raises return linearly and "
                                                      "tail/DD linearly: useful only as a capital/risk-tolerance choice, not as alpha.",
              "V533_AVG_DAY": v533["avg_day"], "V533_MAXDD": v533["max_dd"], "V533_TIMING_VALUE": "NEGATIVE",
              "BEST_POLICY_VS_V533": f"C43-GROWTH {gr.avg_day_full:.1f} $/day at MaxDD {gr.max_dd:.0f} vs V5.3.3 {v533['avg_day']} $/day at MaxDD {v533['max_dd']}",
              "$600_DAY_POSSIBLE_WITH_$150K_CORE": "NO", "$600_DAY_POSSIBLE_WITH_$150K_GROWTH": "NO", "$600_DAY_POSSIBLE_WITH_$150K_AGGRESSIVE": "NO",
              "ESTIMATED_CAPITAL_FOR_$600_AT_BEST_NEW_POLICY": round(H.NLV * scale600, -3), "BUDGET": budget, "OFFLINE_BANDIT": bandit,
              "FINAL_CORE_PORTFOLIO": "C43-CORE", "FINAL_GROWTH_PORTFOLIO": GROWTH_ID, "FINAL_AGGRESSIVE_RESEARCH_PORTFOLIO": "C43 + TEST53 x3 residual (report-only)",
              "FINAL_GROWTH_PROGRAM_PRE_OOS_FREEZE_SHA256": hf, "FINAL_GROWTH_PROGRAM_OOS_RULES_SHA256": hr, "FINAL_GROWTH_PROGRAM_OOS_START": oos,
              "NEW_OOS_OPENED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(status, open(os.path.join(H.HX, "FINAL_HIGH_EXPOSURE_STATUS.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    H.md("HX_00_FINAL_REPORT.md", "TEST55+ high-exposure program - final report",
         ["```json\n" + json.dumps(status, indent=1, default=str) + "\n```", "Pareto frontier (report-only composition of frozen components):",
          F[F.pareto].sort_values("avg_day_full"), "V5.3.3 comparison:", CMP, "Beta/alpha decomposition:", DEC, "$600 frontier (growth portfolio scaling):", fr600,
          "TEST57 stitched:", pd.DataFrame([g57]).T])
    print(json.dumps(status, indent=1, default=str))
    print(F[F.pareto].sort_values("avg_day_full")[["label", "avg_day_full", "avg_day_2021", "max_dd", "worst_day", "ret_dd", "peak_on_margin_frac", "CORE_env", "GROWTH_env", "AGGR_env"]].round(3).to_string())
    print(DEC.round(2)); print(CMP)


if __name__ == "__main__":
    main()
