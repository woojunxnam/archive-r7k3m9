"""Generate TEST44 reports T44_00..T44_23 (markdown) + session-matched-beta table.  Usage: python t44_report.py"""
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from m_report import md  # noqa: E402
import t44_alloc as A  # noqa: E402
import t44_common as TC  # noqa: E402
import t44_04_meta as MM  # noqa: E402
import p07_acceptance as ACC  # noqa: E402
from t44_03_priority_loo import parse  # noqa: E402

O = TC.T44
REP = os.path.join(TC.ROOT, "reports", "TEST44_INTEGER_META_ALLOCATOR")
HDR = "TEST44 — DISCRETE CONTRACT + META ALLOCATOR LAB. Data through 2026-05-27 only. NEW_OOS_OPENED = NO."


def w(fn, title, body):
    os.makedirs(REP, exist_ok=True)
    open(f"{REP}/{fn}.md", "w").write(f"# {title}\n\n{HDR}\n\n{body}\n")


def main():
    fz = json.load(open(f"{O}/freeze/TEST44_PRE_OOS_FREEZE.json"))
    rules = json.load(open(f"{O}/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.json"))
    pre_sha = open(f"{O}/freeze/TEST44_PRE_OOS_FREEZE.sha256").read().split()[0]
    rules_sha = open(f"{O}/freeze/TEST44_NEW_OOS_ACCEPTANCE_RULES.sha256").read().split()[0]
    ch = fz["challengers"]
    grid = pd.read_csv(f"{O}/t44_deterministic_grid.csv"); grid["maxc"] = grid.caps.str.split("/").str[0].astype(int)
    bench = pd.read_csv(f"{O}/t44_benchmarks.csv")
    pri = pd.read_csv(f"{O}/t44_priority_rules.csv"); loo = pd.read_csv(f"{O}/t44_integer_loo.csv")
    att = pd.read_csv(f"{O}/t44_integer_attribution.csv"); fr = pd.read_csv(f"{O}/t44_contract_frontier.csv")
    info = pd.read_csv(f"{O}/t44_meta_information.csv"); perf = pd.read_csv(f"{O}/t44_meta_performance.csv")
    F = pd.read_csv(f"{O}/t44_final_comparison.csv"); S = pd.read_csv(f"{O}/t44_final_stress.csv")
    FA = pd.read_csv(f"{O}/t44_final_integer_attribution.csv"); FAIL = pd.read_csv(f"{O}/t44_test43_failure_attribution.csv")
    ho = pd.read_csv(os.path.join(TC.ROOT, "out", "p", "holdout", "TEST43P_HOLDOUT_SLEEVE_ATTRIBUTION.csv"))
    blocks = json.load(open(f"{O}/t44_meta_walkforward_blocks.json"))
    # ---- session-matched beta for the final set (report only)
    E = A.Engine()
    P, sess, six = MM.panel(E)
    allf = sum(MM.FAM.values(), [])
    fsets = {"E_ALL": allf, "A_ONLY": MM.FAM["A"], **{f"E_minus_{k}": [f for f in allf if f not in v] for k, v in MM.FAM.items()}}
    smb = []
    for role, spec in ch.items():
        mode, rq, rk, cap = parse(spec["alloc_cfg"])
        sc = None
        if spec.get("model"):
            pred, _ = MM.walk_forward(P, spec["model"], fsets[spec["features"]]); sc = MM.score_arrays(E, P, pred, six, spec["usage"])
        REQ, X, dem = E.requests(**rq, score=sc)
        r = E.run(mode, REQ, X, E.priority("LOW_DD", dem), caps=(cap, cap), **rk)
        d = E.daily(r)
        for per in ("ALL", "ML_OOS_SPAN", "F4_2025_2026", "FORMER_HOLDOUT"):
            s, e = TC.PERIODS[per]
            x = ACC.session_matched_beta(E.T, r["pos"], d, s, e)
            smb.append({"candidate": role, "period": per, "portfolio_net": x["portfolio_net_pnl"], "session_matched_net": x["session_matched_net_pnl"],
                        "excess_per_day": x["excess_vs_session_matched_per_day"]})
    champ_pos = None
    pd.DataFrame(smb).to_csv(f"{O}/t44_session_matched_beta.csv", index=False)
    SMB = pd.DataFrame(smb)
    # ---- answers
    k1 = F.set_index("candidate")
    d0 = bench.set_index("config").loc["D0_CURRENT_TEST43"]
    best_fam = grid[grid.feasible].sort_values("ALL_ret_dd", ascending=False).groupby("family").head(1).set_index("family")
    anyfam = grid.sort_values("ALL_ret_dd", ascending=False).groupby("family").head(1).set_index("family")
    status = {
        "FRACTIONAL_ROUNDING_WAS_MATERIAL_FAILURE_SOURCE": "YES for the former holdout (integer gross -$22.4k vs virtual fractional; PRIMARY -$6.7k realised vs +$15.7k desired), but NOT a persistent historical bias (gap 2019-2024 within +-$1.8k)",
        "ONE_CONTRACT_BEATS_TEST43_ALLOCATOR": "NO on full-history return/DD (best D1 %.4f vs D0 %.4f); YES only inside the former-holdout window" % (anyfam.loc["D1_ONE_CONTRACT", "ALL_ret_dd"], d0.ALL_ret_dd),
        "ONE_TWO_CONTRACT_BEATS_TEST43_ALLOCATOR": "NO on full-history return/DD (best D2 %.4f); YES only inside the former-holdout window" % anyfam.loc["D2_TWO_CONTRACT", "ALL_ret_dd"],
        "CLUSTER_SLOT_ADDS_VALUE": "MARGINAL (best feasible D3 %.4f vs D1 %.4f at max 1; lower DD, not better at max 2+)" % (best_fam.loc["D3_CLUSTER_SLOT", "ALL_ret_dd"], best_fam.loc["D1_ONE_CONTRACT", "ALL_ret_dd"]),
        "INTEGER_TRACKING_ADDS_VALUE": "YES among integer allocators (D4 best at every contract cap; best feasible %.4f)" % best_fam.loc["D4_INTEGER_TRACKING", "ALL_ret_dd"],
        "RESIDUAL_ALLOCATOR_ADDS_VALUE": "NO (best feasible %.4f with 2-5x turnover; error diffusion re-creates the chop it was meant to avoid)" % best_fam.loc["RESIDUAL", "ALL_ret_dd"],
        "BEST_PRACTICAL_MAX_CONTRACTS": "2 (highest return inside the MODERATE envelope with every fold positive; 1 has similar return/DD; 3-4 breach the envelope)",
        "RIDGE_ADDS_VALUE_OVER_SIMPLE_INTEGER": "YES on risk efficiency (ML span ret/DD %.4f vs %.4f, MaxDD $%.0f vs $%.0f, excess %.1f vs %.1f/day) but LOWER absolute P&L (%.1f vs %.1f/day)" % (
            k1.loc["RIDGE_CHALLENGER", "ML_OOS_SPAN_ret_dd"], k1.loc["SIMPLE_INTEGER_CHALLENGER", "ML_OOS_SPAN_ret_dd"], k1.loc["RIDGE_CHALLENGER", "ML_OOS_SPAN_max_dd"],
            k1.loc["SIMPLE_INTEGER_CHALLENGER", "ML_OOS_SPAN_max_dd"], k1.loc["RIDGE_CHALLENGER", "ML_OOS_SPAN_excess_vs_mb"], k1.loc["SIMPLE_INTEGER_CHALLENGER", "ML_OOS_SPAN_excess_vs_mb"],
            k1.loc["RIDGE_CHALLENGER", "ML_OOS_SPAN_avg"], k1.loc["SIMPLE_INTEGER_CHALLENGER", "ML_OOS_SPAN_avg"]),
        "XGBOOST_ADDS_VALUE_OVER_SIMPLE_INTEGER": "WEAK YES on ret/DD (%.4f vs %.4f) with much lower P&L (%.1f vs %.1f/day) and lower matched-beta excess" % (
            k1.loc["XGBOOST_CHALLENGER", "ML_OOS_SPAN_ret_dd"], k1.loc["SIMPLE_INTEGER_CHALLENGER", "ML_OOS_SPAN_ret_dd"], k1.loc["XGBOOST_CHALLENGER", "ML_OOS_SPAN_avg"], k1.loc["SIMPLE_INTEGER_CHALLENGER", "ML_OOS_SPAN_avg"]),
        "XGBOOST_ADDS_VALUE_OVER_RIDGE": "NO (ret/DD %.4f vs %.4f; excess %.1f vs %.1f)" % (k1.loc["XGBOOST_CHALLENGER", "ML_OOS_SPAN_ret_dd"], k1.loc["RIDGE_CHALLENGER", "ML_OOS_SPAN_ret_dd"],
                                                                                          k1.loc["XGBOOST_CHALLENGER", "ML_OOS_SPAN_excess_vs_mb"], k1.loc["RIDGE_CHALLENGER", "ML_OOS_SPAN_excess_vs_mb"]),
        "XGBOOST_COMPLEXITY_JUSTIFIED": "NO",
        "CHAMPION_CONTROL_V1": "P1_CLUSTER_EQUAL_RISK|CONSERVATIVE",
        "SIMPLE_INTEGER_CHALLENGER": ch["SIMPLE_INTEGER_CHALLENGER"]["alloc_cfg"],
        "RIDGE_CHALLENGER": f"RIDGE|{ch['RIDGE_CHALLENGER']['features']}|{ch['RIDGE_CHALLENGER']['usage']}|{ch['RIDGE_CHALLENGER']['alloc_cfg']}",
        "XGBOOST_CHALLENGER": f"{ch['XGBOOST_CHALLENGER']['model']}|{ch['XGBOOST_CHALLENGER']['features']}|{ch['XGBOOST_CHALLENGER']['usage']}|{ch['XGBOOST_CHALLENGER']['alloc_cfg']}",
        "PRE_OOS_FREEZE_SHA256": pre_sha, "NEW_OOS_RULES_SHA256": rules_sha,
        "NEW_OOS_DATA_ACQUIRED": "NO", "NEW_OOS_OPENED": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(status, open(f"{O}/T44_00_final_status.json", "w"), indent=1)
    st = "\n".join(f"{k} = {v}" for k, v in status.items())
    cmp_cols = ["candidate", "ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd", "ALL_excess_vs_mb", "ML_OOS_SPAN_avg", "ML_OOS_SPAN_max_dd", "ML_OOS_SPAN_ret_dd",
                "ML_OOS_SPAN_excess_vs_mb", "F4_2025_2026_avg", "F4_2025_2026_max_dd", "Y2020_avg", "Y2022_avg", "FORMER_HOLDOUT_avg"]
    w("T44_00_STATUS", "T44_00 Status", f"""Research complete; pre-OOS freeze and new-OOS rules written and hashed. No data after 2026-05-27 was acquired or inspected.

```
{st}
```

## Final comparison (all candidates on identical costs, margin, $150k account, MODERATE governor; CHAMPION frozen as TEST43)
{md(F[cmp_cols], 3)}

Reading: no TEST44 allocator beats CHAMPION_CONTROL_V1 on absolute P&L or matched-beta excess. The Ridge challenger has the best risk
efficiency on the ML walk-forward span (ret/DD 0.013 vs champion 0.009) at far lower exposure. The walk-forward span is NOT fully clean:
the frozen sleeves were optimised on 2019-2024, and ~100 meta variants were compared on the same span (selection optimism). F4
(2025-01..2026-05, sleeves out of sample) is the cleanest block. The new OOS (from 2026-05-28) decides; promotion requires the frozen
thresholds in T44_22.""")
    w("T44_01_TEST43_FAILURE_ATTRIBUTION", "T44_01 TEST43 failure attribution", f"""
## D0 (TEST43 PRIMARY): fractional virtual desire vs realised integer position, gross $
{md(FAIL, 0)}

## TEST43 holdout sleeve attribution (from the one-shot holdout)
{md(ho[ho.role == 'PRIMARY'][['sleeve', 'contract_weight', 'avg_weighted_desired_contracts', 'avg_realised_contracts_allocated', 'gross_contribution_virtual', 'gross_contribution_realised', 'standalone_virtual_ledger_holdout_pnl']], 2)}

The quantisation gap was small and two-sided in 2019-2024 (+$1.8k, +$0.4k, +$0.3k) and -$22.4k in the former holdout: rounding at
fractional desires (~0.2-0.9 contracts per instrument) turned a +$15.7k desired P&L into -$6.7k. It is an episodic, path-dependent
distortion rather than a persistent bias, which is why DEV/VAL could not reveal it.""")
    w("T44_02_INTEGER_ENGINE_QA", "T44_02 Integer engine QA", """
* `src/t43/intport.py`: integer MES/MNQ targets only (REQUEST / TRACK / RESIDUAL modes), one shared $150k account, DD tiers on a
  $ATR budget, time-based rearm (20 sessions; the TEST43 recovery-only rearm locked integer portfolios in reduced mode 88% of the time),
  day-loss cut, margin with the overnight fraction when the next bar is not RTH, next-bar-open execution, 1 tick, $0.62/side, roll cost.
* QA: a single sleeve requested at its own integer desired position with governor off reproduces the standalone sleeve exactly
  (ES_robust_A_MOD_1 $117,831.63; MNQ_robust_C_CON_0 $75,666.50 on 2019-05..2026-05).
* Frozen TEST43 portfolios reproduced on the extended data: CHAMPION_CONTROL_V1 former-holdout net +$9,690.71, D0 -$7,164.29 (exact).
* Bars rebuilt from the hash-verified canonical files and truncated at 2026-05-27 (hard assertion in `t44_common.py`).""")
    meta = json.load(open(f"{O}/sleeve_meta.json"))
    w("T44_03_0_1_2_CONTRACT_MAPPING", "T44_03 0/1/2 contract mapping", f"""
intensity = frozen V6 desired target / the sleeve's maximum desired target on DEV (<= 2024-12-31). OFF = desired 0 or intensity below an
off-band (0 / 0.1 / 0.2, broad); NORMAL = 1 contract; STRONG = 2 contracts when intensity >= theta (0.33 / 0.50 / 0.67).
The off-band was needed: ES sleeves are active ~100% of the time and express bear/neutral regimes only through smaller targets.

{md(pd.DataFrame(meta).T.reset_index().rename(columns={'index': 'sleeve'})[['sleeve', 'inst', 'max_desired_DEV', 'mean_desired_when_active_DEV', 'active_share_DEV']], 3)}""")
    gcols = ["config", "ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd", "ALL_excess_vs_mb", "Y2020_avg", "Y2022_avg", "FORMER_HOLDOUT_avg", "fills_per_day", "avg_MES", "avg_MNQ", "feasible"]
    for fn, fam, title in (("T44_04_ONE_CONTRACT_BASELINE", "D1_ONE_CONTRACT", "D1 one contract"), ("T44_05_TWO_CONTRACT_BASELINE", "D2_TWO_CONTRACT", "D2 one/two contracts"),
                           ("T44_06_CLUSTER_SLOT_ALLOCATOR", "D3_CLUSTER_SLOT", "D3 cluster slots"), ("T44_07_INTEGER_TRACKING_ALLOCATOR", "D4_INTEGER_TRACKING", "D4 integer tracking"),
                           ("T44_08_RESIDUAL_ALLOCATOR", "RESIDUAL", "Residual / error accumulator")):
        g = grid[grid.family == fam].sort_values("ALL_ret_dd", ascending=False)
        w(fn, f"{fn[:6]} {title}", f"Feasible = ALL MaxDD <= $15k, worst day >= -$3k, peak margin <= 0.5, every fold F1..F4 positive.\n\n{md(g[gcols], 3, 40)}\n\nBenchmarks: {md(bench[['config', 'ALL_avg', 'ALL_max_dd', 'ALL_worst', 'ALL_ret_dd', 'ALL_excess_vs_mb', 'Y2020_avg', 'Y2022_avg', 'FORMER_HOLDOUT_avg']], 3)}")
    w("T44_09_PRIORITY_ALLOCATOR", "T44_09 Priority allocation", md(pri[["config", "budget_frac", "priority", "ALL_avg", "ALL_max_dd", "ALL_worst", "ALL_ret_dd", "Y2022_avg", "FORMER_HOLDOUT_avg", "note"]], 3, 80) +
      "\n\nPriority only matters when the shared $ATR budget binds; a binding budget (75% / 50% of caps) costs more return than any priority rule recovers, and no rule dominates across allocators. D4 TRACK resolves scarcity inside its constrained search. Simple priority does NOT solve the quantisation problem.")
    w("T44_10_CONTRACT_COUNT_FRONTIER", "T44_10 Contract-count frontier (MAX_1..MAX_4)", md(fr, 3) + "\n\nMAX_1 and MAX_2 are the only caps with envelope-feasible allocators; MAX_2 gives the highest feasible return, MAX_1 marginally the best ret/DD. MAX_3/4 add return but breach the MODERATE envelope.")
    w("T44_11_LEAVE_ONE_OUT", "T44_11 Integer leave-one-out", md(loo, 2, 40) + "\n\nUnder integer execution several fractional-era diversifiers are redundant (removing ES_r2_A_CON_1 / ES_robust_C_CON_4 changes little); the MNQ A family and ES_robust_A_MOD_1 / ES_r2_F_MOD_2 carry the return; MNQ_robust_C_CON_0 lowers drawdown.")
    w("T44_12_RIDGE_SPEC", "T44_12 Ridge meta allocator specification", f"""
Sample (sleeve, session); target = session P&L of 1 contract held while the sleeve is ON minus ON-share x passive 1-contract P&L, in daily-ATR
units, clipped +-3. Features (session t-1 information only; no calendar): {json.dumps(MM.FAM)}. Standardised, Ridge alpha {MM.RIDGE_ALPHA}.
Expanding walk-forward: first fit after {MM.FIRST_TRAIN} sessions, refit every {MM.BLOCK} sessions, {MM.PURGE}-session purge. Scores map to integer
demand by GATE_POS (keep if score > 0), TOP_HALF (keep sleeves at/above the session median score) or DROP_BOTTOM_Q; never fractional, never extra leverage.
Stacking leakage: meta labels are the frozen sleeves' realised outcomes; no sleeve is refit. The sleeves were optimised on 2019-2024, so the
2021-2024 part of the meta span is in-sample for the BASE strategies (disclosed); 2025-2026 is out of sample for both.
Final fit for OOS: `{fz['meta_models']['final_fits']['RIDGE_CHALLENGER']['file']}` sha256 {fz['meta_models']['final_fits']['RIDGE_CHALLENGER']['sha256'][:16]}...""")
    icols = ["model", "features", "n", "IC_pooled", "IC_monthly_mean", "IC_monthly_t", "share_positive_scores", "top3_minus_bottom3_y_atr", "gated_mean_y", "kept_mean_y"]
    pcols = ["model", "features", "usage", "allocator", "ML_OOS_SPAN_avg", "ML_OOS_SPAN_max_dd", "ML_OOS_SPAN_ret_dd", "ML_OOS_SPAN_excess_vs_mb", "F2_2021_2022_avg", "F3_2023_2024_avg", "F4_2025_2026_avg", "Y2022_avg", "FORMER_HOLDOUT_avg", "SLIP4_ML_OOS_SPAN_avg", "fills_per_day"]
    w("T44_13_RIDGE_WALKFORWARD", "T44_13 Ridge walk-forward", f"## Information (out-of-sample scores)\n{md(info[info.model == 'RIDGE'][icols], 4)}\n\n## Allocation\n{md(perf[perf.model.isin(['RIDGE', 'NONE(simple integer)'])][pcols], 3, 60)}\n\nBlocks: {len(blocks.get('RIDGE|E_ALL', []))} refits.")
    w("T44_14_XGB_SPEC", "T44_14 XGBoost specification", f"Presets (predeclared, no search): {json.dumps(MM.XGB_PRESETS)}. Early stopping on the last 20% (chronological) of each training window. Same target/features/walk-forward/usages as Ridge.\nFinal fit: `{fz['meta_models']['final_fits']['XGBOOST_CHALLENGER']['file']}` sha256 {fz['meta_models']['final_fits']['XGBOOST_CHALLENGER']['sha256'][:16]}...")
    w("T44_15_XGB_WALKFORWARD", "T44_15 XGBoost walk-forward", f"## Information\n{md(info[info.model.str.startswith('XGB')][icols], 4)}\n\n## Allocation\n{md(perf[perf.model.str.startswith('XGB')][pcols], 3, 80)}")
    ab = info[info.model.isin(["RIDGE", "XGB_REGULARIZED"])][icols]
    w("T44_16_FEATURE_ABLATION", "T44_16 Feature-family ablation", md(ab, 4) + "\n\nFamily A (frozen sleeve state) carries the information: removing A kills IC for both models. For XGB removing B, C or D each raises IC; for Ridge removing C or D raises IC and removing B lowers it slightly (0.038 -> 0.033). The A-only models match or beat the full models. Complexity did not earn its place.")
    w("T44_17_MODEL_COMPARISON", "T44_17 Model comparison", f"{md(F[cmp_cols], 3)}\n\n## Session-matched beta (report only)\n{md(SMB, 2)}\n\n## Stress\n{md(S[['candidate', 'test', 'ALL_avg', 'ALL_max_dd', 'ALL_worst', 'ML_OOS_SPAN_avg', 'peak_margin']], 2, 40)}\n\n## Rolling / folds\n{md(F[['candidate'] + [c for c in F.columns if 'roll' in c and c.startswith(('ALL', 'ML_OOS'))]], 3)}")
    w("T44_18_2020_2022_STRESS", "T44_18 2020 / 2022 stress", md(F[["candidate"] + [c for c in F.columns if c.startswith(("Y2020", "Y2022"))]], 2) + "\n\nMeta challengers are identical to their base integer allocator before the first walk-forward block (2021-05), so their 2020 equals the base allocator's.")
    w("T44_19_FORMER_HOLDOUT_DIAGNOSTIC", "T44_19 Former TEST43 holdout window (now historical)", md(F[["candidate"] + [c for c in F.columns if c.startswith("FORMER_HOLDOUT")]], 2) + "\n\nNo allocator was tuned for this window; it is one historical block among many (fold F4).")
    w("T44_20_FINAL_CHALLENGERS", "T44_20 Final challengers", f"Selection rules (applied mechanically): simple = max full-history ret/DD among envelope-feasible deterministic allocators (ties -> fewer contracts); Ridge / XGB = max ML-span ret/DD with F2, F3, F4 > 0, positive matched-beta excess and ML-span MaxDD <= $15k (ties -> fewer features).\n\n```json\n{json.dumps(ch, indent=1)}\n```\n\n## Integer attribution (requested vs received, denial reasons)\n{md(FA, 3, 60)}\n\n## Deterministic attribution\n{md(att, 3, 40)}")
    w("T44_21_PRE_OOS_FREEZE", "T44_21 Pre-OOS freeze", f"`out/t44/freeze/TEST44_PRE_OOS_FREEZE.json` SHA256 `{pre_sha}`\n\n```json\n{json.dumps({k: v for k, v in fz.items() if k not in ('sleeves', 'code_sha256')}, indent=1, default=str)[:12000]}\n```")
    w("T44_22_NEW_OOS_ACCEPTANCE_RULES", "T44_22 New OOS acceptance rules", f"SHA256 `{rules_sha}`\n\n```json\n{json.dumps(rules, indent=1)}\n```")
    rows = []
    for f in sorted(glob.glob(f"{O}/*.csv")) + sorted(glob.glob(f"{O}/*.json")) + sorted(glob.glob(f"{O}/freeze/*")) + sorted(glob.glob(f"{REP}/T44_[0-2]*.md")):
        if "T44_23" in f:
            continue
        rows.append({"file": os.path.relpath(f, TC.ROOT), "bytes": os.path.getsize(f), "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()})
    h = pd.DataFrame(rows); h.to_csv(f"{O}/T44_23_HASH_INDEX.csv", index=False)
    w("T44_23_HASH_INDEX", "T44_23 Hash index", md(h, 0, 1000))
    print(st)
    print(SMB.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
