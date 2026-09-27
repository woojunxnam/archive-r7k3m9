"""Generate TEST43-P report family P00..P23 (markdown) from out/p.  Usage: python p_report.py"""
import glob
import hashlib
import json
import os

import numpy as np
import pandas as pd

from m_report import md

ROOT = os.path.join(os.path.dirname(__file__), "..")
O = f"{ROOT}/out/p"
REP = f"{ROOT}/reports/TEST43-P_MULTI_STRATEGY_REGIME_ENSEMBLE"
HDR = "TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO."


def w(fn, title, body):
    os.makedirs(REP, exist_ok=True)
    open(f"{REP}/{fn}.md", "w").write(f"# {title}\n\n{HDR}\n\n{body}\n")


def main():
    g = pd.read_csv(f"{O}/p01_g_portability.csv")
    fp = pd.read_csv(f"{O}/p03_fingerprint_DEV.csv")
    red = pd.read_csv(f"{O}/p04_pairwise_redundancy_DEV.csv")
    cl = pd.read_csv(f"{O}/p05_clusters_DEV.csv")
    sim = pd.read_csv(f"{O}/p05_similarity_matrix_DEV.csv", index_col=0)
    rn = pd.read_csv(f"{O}/p06_risk_normalisation_DEV.csv")
    stab = pd.read_csv(f"{O}/p06_sleeve_stability_and_risk_units_DEV.csv")
    fr = pd.read_csv(f"{O}/p07_p12_portfolios_frontiers_DEV.csv")
    rm = pd.read_csv(f"{O}/p09_regime_matrix_DEV.csv")
    comp = pd.read_csv(f"{O}/p10_complementarity_DEV.csv")
    cnt = pd.read_csv(f"{O}/p11_candidate_count_frontier_DEV.csv")
    loo = pd.read_csv(f"{O}/p13_leave_one_out_DEV.csv")
    rob = pd.read_csv(f"{O}/p15_portfolio_robustness_DEV.csv")
    V = pd.read_csv(f"{O}/p18_val_confirmation.csv")
    sel = json.load(open(f"{O}/p20_selection.json"))
    fin = json.load(open(f"{O}/freeze/TEST43P_FINAL_PORTFOLIOS.json"))
    rules = json.load(open(f"{O}/freeze/TEST43P_HOLDOUT_ACCEPTANCE_RULES.json"))
    shas = {k: open(f"{O}/freeze/{k}.sha256").read().split()[0] for k in
            ("TEST43P_PRE_VAL_FREEZE", "TEST43P_HOLDOUT_ACCEPTANCE_RULES", "TEST43P_FINAL_PORTFOLIOS")}
    c5 = cl[cl.cut_distance == 0.5].set_index("id").cluster
    # within / between cluster similarity and daily correlation
    wi, bt = [], []
    for _, r in red.iterrows():
        if r.A in c5 and r.B in c5:
            (wi if c5[r.A] == c5[r.B] else bt).append(r.daily_corr)
    # adds-value definition: DEV ret/DD at MODERATE vs the best single sleeve (count frontier k=1), and VAL pass
    k1 = cnt[cnt.n_candidates == 1].iloc[0]
    def adds(name):
        x = V[(V.portfolio == name) & (V.risk_env == "MODERATE")]
        if not len(x):
            return "NO"
        x = x.iloc[0]
        return "YES" if (x.DEV_ret_dd > k1.DEV_ret_dd * 1.05 and x.VAL_PASS) else "NO"
    p2m = V[(V.portfolio == "P2_STATIC_DIVERSIFIED") & (V.risk_env == "MODERATE")].iloc[0]
    p3m = V[V.portfolio.str.startswith("P3") & (V.risk_env == "MODERATE")]
    p3_adds = "NO" if not ((p3m.VAL_avg > p2m.VAL_avg) & (p3m.VAL_ret_dd > p2m.VAL_ret_dd)).any() else "YES"
    sat = int(cnt.loc[cnt.DEV_ret_dd.idxmax(), "n_candidates"])
    modV = V[V.risk_env == "MODERATE"]
    best20 = modV.loc[modV.Y2020_avg.idxmax(), "portfolio"]; best22 = modV.loc[modV.Y2022_avg.idxmax(), "portfolio"]
    status = {
        "G_WALLCLOCK_FIX_PASS": "YES (exact fill-for-fill 3m reproduction; 3m-specific bar counts / clock anchors converted)",
        "G_3M_REGRESSION_PASS": "YES (1011 fills, identical positions/equity)",
        "G_5M_PASS": "NO (DEV MaxDD $20.5k > $20k AGGRESSIVE envelope; return 90% retained)",
        "G_TRANSFER_PASS": "NO (MNQ 3m: DEV MaxDD $23.4k envelope breach, VAL excess -$40.6/day)",
        "CANDIDATES_ANALYZED": f"{len(fp)} ({len(fp[fp.role == 'ELIGIBLE'])} eligible + {len(fp[fp.role == 'SHADOW'])} shadow)",
        "BEHAVIORAL_CLUSTERS": f"{c5.nunique()} (MNQ-A growth, MNQ-C defensive, ES all four)",
        "FULL_UNIVERSE_ADDS_VALUE": adds("P0_FULL_UNIVERSE_EQUAL_RISK"),
        "CLUSTER_EQUAL_RISK_ADDS_VALUE": adds("P1_CLUSTER_EQUAL_RISK"),
        "STATIC_DIVERSIFIED_ADDS_VALUE": adds("P2_STATIC_DIVERSIFIED") + " (P2); P2B 4-sleeve: " + adds("P2B_STATIC_4SLEEVE"),
        "REGIME_ADAPTIVE_ADDS_VALUE": "NO (DEV mixed; VAL MODERATE below P2 static)",
        "REGIME_ADAPTIVE_BEATS_STATIC_AFTER_COST": p3_adds + " at MODERATE (VAL SLIP4: P3_25 %.1f / P3_50 %.1f vs P2 %.1f $/day); AGGRESSIVE P3 higher on VAL but not a selected envelope" % (
            p3m[p3m.portfolio == "P3_REGIME_ADAPTIVE_25"].SLIP4_VAL_avg.iloc[0], p3m[p3m.portfolio == "P3_REGIME_ADAPTIVE_50"].SLIP4_VAL_avg.iloc[0], p2m.SLIP4_VAL_avg),
        "DIVERSIFICATION_SATURATION_COUNT": f"{sat} (3 clusters; 5+ adds no ret/DD)",
        "BEST_2020_PORTFOLIO": f"{best20} (MODERATE, DEV-period 2020)",
        "BEST_2022_PORTFOLIO": f"{best22} (MODERATE, 2022)",
        "PRIMARY_PORTFOLIO": sel["PRIMARY"], "SECONDARY_PORTFOLIO_1": sel["SECONDARY_1"], "SECONDARY_PORTFOLIO_2": sel["SECONDARY_2"],
        "PRE_VAL_FREEZE_SHA256": shas["TEST43P_PRE_VAL_FREEZE"], "FINAL_FREEZE_SHA256": shas["TEST43P_FINAL_PORTFOLIOS"],
        "HOLDOUT_RULES_SHA256": shas["TEST43P_HOLDOUT_ACCEPTANCE_RULES"],
        "HOLDOUT_OPENED": "NO", "PORTFOLIO_MEMBERSHIP_CHANGED": "NO", "LIVE_AUTHORIZATION": "NO"}
    json.dump(status, open(f"{O}/P00_final_status.json", "w"), indent=1)
    stat_txt = "\n".join(f"{k} = {v}" for k, v in status.items())
    selrows = V[(V.portfolio + "|" + V.risk_env).isin(sel.values())]

    w("P00_STATUS", "P00 Status", f"""Run complete up to the final freeze. Holdout NOT loaded.

```
{stat_txt}
```

Authority: GitHub branch `claude/test43-mes-optimization-lab-olvn9b` (full tables in `test43_lab/out/p`, freeze files in
`test43_lab/out/p/freeze`). V6_09 authority is `test43_lab/reports/V6/V6_09_ROBUSTNESS_5M_TRANSFER.md` (Drive copy blocked by
connector write policy; not a research blocker). TEST43-M not rerun; no TEST43-M directional signal is used.

## Selected portfolios (DEV and VAL)
{md(selrows[["portfolio", "risk_env", "members", "DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_excess_vs_mb", "VAL_avg", "VAL_total", "VAL_max_dd", "VAL_worst", "VAL_excess_vs_mb", "SLIP4_VAL_avg", "TIMING_BRITTLENESS_STRESS_VAL_avg"]], 1)}

Next step (not in this run): open the holdout once under `TEST43P_HOLDOUT_ACCEPTANCE_RULES.json`.""")

    w("P01_G_WALLCLOCK_PORTABILITY", "P01 ES_r2_G_AGG_0 wall-clock portability", f"""
## Audit of v6x intraday quantities
| quantity | class | treatment |
|---|---|---|
| microDBLookback, strengthBuildBars, addCooldownBars, oppositeSideCooldownBars, antiStallBars, targetDecayBars, repairLookback, repairLifeBars, coreRotationAgeBars, rfLookback | A: time (bars of 3m) | converted: bars_new = round(bars_3m * 3 / barMinutes), never rounded to 0 when live (G: targetDecayBars 88 = 264 min -> 53 bars at 5m; oppositeSideCooldownBars 8 = 24 min -> 5 bars) |
| rolling 15/30/60m RTH highs/lows (hard-coded 5/10/20 bars) | A: time | now round(15/30/60 / barMinutes) bars (ring buffer 64) |
| trim decision bar (hard-coded 16:09 bar = close 16:12) | A: clock | first bar whose close >= 16:12 |
| buy window end (bar open <= 15:54), late-session repair restore (15:48+), last-RTH trim (bar open >= 15:57) | A: clock | expressed on bar CLOSE time (identical on 3m) |
| regimeLen, ddRearmLen, tier EMAs/SMAs, 5-day range | B: completed RTH sessions | NOT converted |
| ATR14, RSI2, W%R2, 2-bar patterns, next-bar-open fill | C: bar-native indicator / execution semantics | not converted (same as Pine on the chart timeframe); documented limitation |

New parameters appended (defaults = native 3m): barMinutes, refMinutes, fillDelayBars (TIMING_BRITTLENESS_STRESS only).
The frozen G parameters are untouched.

## Results (DEV+VAL; frozen parameters)
{md(g[["test", "DV_total", "DEV_avg_daily", "DEV_max_dd", "DEV_worst_day", "DEV_excess_vs_mb", "VAL_avg_daily", "VAL_max_dd", "VAL_excess_vs_mb", "Y2022_avg_daily", "Y2022_max_dd", "fills", "friction", "avg_pos", "avg_on_pos", "peak_margin_util", "margin_breach", "DEV_env", "VAL_env"]], 1)}

**Regression:** the wall-clock kernel reproduces the frozen 3m run fill-for-fill (1011 fills, identical positions and
equity). **Gate:** 5m keeps 90% of DEV return and positive matched-beta excess but DEV MaxDD $20.5k exceeds the $20k
AGGRESSIVE envelope; ATR$-scaled MNQ transfer breaches the envelope ($23.4k) and has negative VAL excess at 3m.
Cost / timing / margin stresses pass. Same standard as the V6A downgrades (ES F-AGG, MNQ E-AGG) -> G is a SHADOW /
CONTROL sleeve, not capital-eligible. Not retuned.
""")

    w("P02_CANDIDATE_UNIVERSE", "P02 Candidate universe", f"""
Eligible (8): {', '.join(fp[fp.role == 'ELIGIBLE'].id)}.
Shadow controls (3): ES_robust_F_AGG_0 (cost + neighbourhood DD), MNQ_arch_E_AGG_0 (neighbourhood DD), ES_r2_G_AGG_0 (P01).
Candidate hashes / parameters: `freeze/TEST43P_PRE_VAL_FREEZE.json` -> candidates.

## 2022 verification (canonical frozen replay; all user-quoted figures reproduced)
{md(fp[["id", "role", "Y2022_avg", "Y2022_max_dd", "Y2022_worst", "Y2022_mb_avg", "Y2022_excess", "Y2020_avg", "Y2020_max_dd"]], 1)}
""")

    w("P03_BEHAVIORAL_FINGERPRINT", "P03 Behavioural fingerprint (DEV)", f"""
{md(fp[["id", "role", "total", "avg_daily", "median_day", "pos_day_share", "max_dd", "worst_day", "mb_total", "excess_vs_mb", "ret_dd", "avg_contracts", "avg_on_contracts", "max_contracts", "fills_per_day", "friction_per_day"]], 2)}

## Concentration, rolling windows, eras
{md(fp[["id", "avg_ex_top1", "avg_ex_top3", "avg_ex_top5", "roll3m_pos_share", "roll3m_min", "roll6m_pos_share", "roll6m_min", "roll12m_pos_share", "roll12m_min", "PRE23_avg", "P23_avg", "Y2020_avg", "Y2022_avg"]], 2)}

## Regimes and time of day (gross MTM $)
{md(fp[["id", "HIVOL_avg", "LOVOL_avg", "TREND_avg", "RANGE_NEUTRAL_avg", "BEAR_avg", "NEUTRAL_avg", "BULL_avg", "gross_rth_morning", "gross_rth_midday", "gross_rth_late", "gross_overnight"]], 1)}

Daily series for all candidates aligned by session_date: `out/p/p03_daily_pnl_all_candidates_DV.csv`.
""")

    w("P04_CORRELATION_AND_DD_OVERLAP", "P04 Correlation and drawdown overlap (DEV)", f"""
{md(red[["A", "B", "daily_corr", "weekly_corr", "position_corr", "overnight_exposure_corr", "dd_overlap", "worst20_overlap", "loss2020_overlap", "loss2022_overlap", "hivol_loss_overlap", "margin_corr"]], 2, 80)}

## Incremental effect of adding B to A (equal daily-vol risk)
{md(red[["A", "B", "incr_B_to_A_d_avg", "incr_B_to_A_d_maxdd", "incr_B_to_A_d_worst", "incr_B_to_A_retdd_ratio"]], 3, 80)}
(units: standardised daily P&L; retdd_ratio > 1 = the pair has better return/DD than A alone)
""")

    w("P05_BEHAVIORAL_CLUSTERS", "P05 Behavioural clusters", f"""
Similarity = 0.5 x daily P&L corr + 0.25 x 30-min actual-position corr + 0.25 x drawdown-overlap (Jaccard); average
linkage on 1 - similarity. Cut 0.5 used (cuts 0.4 / 0.6 shown for sensitivity).

{md(sim.round(2).reset_index().rename(columns={'index': 'id'}), 2)}

{md(cl.pivot(index='id', columns='cut_distance', values='cluster').reset_index(), 0)}

Clusters (cut 0.5): 1 = MNQ_arch_A_AGG_0 + MNQ_robust_A_MOD_2 (MNQ growth), 2 = MNQ_r2_C_MOD_1 + MNQ_robust_C_CON_0
(MNQ defensive), 3 = all four ES candidates (A/F/A/C behave as one ES long-exposure cluster).
Mean within-cluster daily corr {np.mean(wi):.2f}; mean between-cluster daily corr {np.mean(bt):.2f}.
Names do not define clusters: ES A, F and C are one behavioural cluster.
""")

    w("P06_RISK_NORMALISATION", "P06 Common risk unit", f"""
Primary risk unit = sleeve standalone DEV daily P&L standard deviation. Sleeve contract weight w = budget x L / sigma;
instrument target = sum of weighted desired contracts; integer rounding only at the net execution layer.

{md(rn, 2)}

## Sleeve stability (P2 representative rule) and cost robustness
{md(stab, 2)}
""")

    def ptab(name):
        x = fr[fr.portfolio == name]
        return md(x[["risk_env", "L", "DEV_avg", "DEV_total", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "DEV_excess_vs_mb", "DEV_mu_avg", "DEV_mu_peak", "DEV_mu_on_avg", "DEV_mu_on_peak", "DEV_atr_avg", "DEV_atr_peak", "fills_per_day", "env"]], 3)
    w("P07_FULL_UNIVERSE", "P07 P0 full universe, equal risk", ptab("P0_FULL_UNIVERSE_EQUAL_RISK") +
      f"\n\nAt MODERATE P0 does not beat the best single sleeve on DEV return/DD (P0 {fr[(fr.portfolio=='P0_FULL_UNIVERSE_EQUAL_RISK')&(fr.risk_env=='MODERATE')].DEV_ret_dd.iloc[0]:.4f} vs {k1.DEV_ret_dd:.4f}): half the universe is one ES cluster, so equal weight across names overweights ES. FULL_UNIVERSE_ADDS_VALUE = {status['FULL_UNIVERSE_ADDS_VALUE']}.")
    w("P08_CLUSTER_EQUAL_RISK", "P08 P1 cluster equal risk", ptab("P1_CLUSTER_EQUAL_RISK") +
      "\n\nBest CONSERVATIVE drawdown on DEV ($4.8k) - selected as the defensive SECONDARY_2. At MODERATE its DEV ret/DD is not above the best single sleeve.")
    w("P09_STATIC_DIVERSIFIED", "P09 P2 static diversified (and P2B)", ptab("P2_STATIC_DIVERSIFIED") + "\n\n## P2B (4 sleeves: count-frontier saturation point)\n" +
      md(V[V.portfolio == "P2B_STATIC_4SLEEVE"][["risk_env", "members", "L", "DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "DEV_excess_vs_mb"]], 3) +
      "\n\nP2 = one representative per cluster (max min-fold matched-beta excess): MNQ_robust_A_MOD_2, MNQ_robust_C_CON_0, ES_robust_A_MOD_1. P2B adds MNQ_arch_A_AGG_0 (second member of the MNQ growth cluster) and has the best DEV return/DD.")
    tl = pd.read_csv(f"{O}/p10_regime_tilt_alpha0.5_DEV.csv", index_col=0)
    w("P10_REGIME_ADAPTIVE", "P10 P3 regime adaptive (limited tilt on P2)", f"""
Tilt: 0% (= P2), 25%, 50%. Cells = trend tier (BEAR/NEUTRAL/BULL, lagged) x HIVOL; expanding strictly-prior estimates,
t-statistic shrinkage, no tilt before 250 sessions or with < 20 cell sessions; total risk renormalised. No TEST43-M signal.

{ptab("P3_REGIME_ADAPTIVE_25")}

{ptab("P3_REGIME_ADAPTIVE_50")}

## Regime performance matrix (DEV, shrunk toward unconditional, k = 60 sessions)
{md(rm, 2, 80)}

## Complementarity (rank within regime, 1 = best)
{md(comp, 1)}

Tilt multiplier range realised (alpha 0.5): min {tl.min().min():.2f}, max {tl.max().max():.2f}.
All sleeves earn most in BULL cells; defensive roles are relative (MNQ C-CON has the smallest BEAR losses in 2022) rather
than regime-specific positive alpha. P3 improves DEV MODERATE MaxDD slightly but does not beat P2 on VAL after cost.
REGIME_ADAPTIVE_BEATS_STATIC_AFTER_COST = {status['REGIME_ADAPTIVE_BEATS_STATIC_AFTER_COST']}.
""")
    w("P11_CANDIDATE_COUNT_FRONTIER", "P11 How many strategies is enough?", md(cnt[["n_candidates", "members", "effective_clusters", "L", "DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "DEV_excess_vs_mb", "Y2020_avg", "Y2022_avg", "DEV_mu_peak"]], 3) +
      f"\n\nDeterministic round-robin across clusters (best-first). Diversification saturates at {sat} sleeves (3 clusters): 5-6 give similar ret/DD, 7-8 (adding more ES cluster members) degrade it. DIVERSIFICATION_SATURATION_COUNT = {sat}.")
    st = fr[fr.risk_env == "MODERATE"][["portfolio", "Y2020_total", "Y2020_avg", "Y2020_max_dd", "Y2020_worst", "Y2020_mb_avg", "Y2020_excess_vs_mb", "Y2022_total", "Y2022_avg", "Y2022_max_dd", "Y2022_worst", "Y2022_mb_avg", "Y2022_excess_vs_mb"]]
    w("P12_2020_2022_STRESS", "P12 2020 / 2022 stress (MODERATE, DEV)", md(st, 1) + "\n\nAll envelopes: `p07_p12_portfolios_frontiers_DEV.csv`. No weight was chosen for either year (P2 rule uses min fold excess over F1/F2/F3).\n" +
      f"BEST_2020_PORTFOLIO = {best20}; BEST_2022_PORTFOLIO = {best22}. P2 and the P3 tilts are the MODERATE portfolios clearly positive in 2022 (+$10.7..+14.0/day); P0 and P1 lose in 2022 (more ES / MNQ-growth weight); P2B is about flat (+$1.3/day) with the strongest 2020.")
    w("P13_LEAVE_ONE_OUT", "P13 Leave-one-out (MODERATE, same L)", md(loo, 1, 60) +
      "\n\nIn P2 removing MNQ_robust_A_MOD_2 raises MaxDD (+$1.5k) and cuts return; removing MNQ_robust_C_CON_0 cuts return and 2022 (-$29.9/day); ES_robust_A_MOD_1 adds little average return but supports 2022 (-$15.2/day without it) and the worst day. In P0/P1 several ES members are removable without loss (duplicates of one cluster).")
    sel_d = {}
    for k, v in sel.items():
        fn_ = f"{O}/daily_{v.replace('|', '_')}_DV.csv"
        if os.path.exists(fn_):
            d = pd.read_csv(fn_, index_col=0, parse_dates=True)
            sel_d[k] = {"portfolio": v, "avg_margin_util": d.mu_avg.mean(), "peak_margin_util": d.mu_max.max(),
                        "avg_on_margin_util": d.mu_on_avg.mean(), "peak_on_margin_util": d.mu_on_max.max(),
                        "avg_atr_$": d.atr_avg.mean(), "peak_atr_$": d.atr_max.max(), "avg_MES": d.pES.mean(), "avg_MNQ": d.pMNQ.mean(),
                        "max_total_contracts": d.max_pos.max()}
    w("P14_SHARED_MARGIN_AND_RISK", "P14 Shared account, margin and risk", f"""
One $150,000 account; shared equity, drawdown, margin (raw price x IBKR fraction), governor (portfolio DD tiers, day loss
cut, gross $ATR and instrument-share caps available), net integer target per instrument, next-bar-open fills.
Validation: single-sleeve portfolios reproduce the standalone sleeve P&L exactly (ES_robust_A_MOD_1 $93,596; MNQ_robust_A_MOD_2 $159,115 on DEV).

## Selected portfolios (DEV+VAL)
{md(pd.DataFrame(sel_d).T.reset_index().rename(columns={'index': 'role'}), 3)}

Margin is never binding (peak utilisation well below the 0.5 cap), so the 1.5x intraday / 2x overnight margin stresses
leave P&L unchanged; the binding constraint in calibration is the worst-day floor.
""")
    w("P15_PORTFOLIO_ROBUSTNESS", "P15 Portfolio robustness (MODERATE, DEV)", md(rob[rob.test != "SIMULTANEOUS_LOSS"][["portfolio", "test", "DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_avg_ex_top1", "DEV_avg_ex_top3", "DEV_avg_ex_top5", "PRE23_avg", "P23_avg", "DEV_roll3m_min", "DEV_roll6m_min", "DEV_roll12m_min", "DEV_worst20_sessions_sum", "margin_breach"]], 1, 60) +
      "\n\n## Simultaneous-strategy-loss diagnostics\n" + md(rob[rob.test == "SIMULTANEOUS_LOSS"].dropna(axis=1, how="all"), 2))
    w("P16_STRATEGY_HEALTH_MONITOR_SPEC", "P16 Strategy health monitor (production specification)", """
All viable sleeves (including shadows and zero-weight sleeves) keep computing their virtual desired exposure and virtual
ledger in production. States: NORMAL / WATCH / REDUCED / DISABLED. Thresholds are fixed a priori from each sleeve's own DEV
distribution (percentiles), NOT optimised on this backtest.

| input | WATCH | REDUCED (sleeve budget x0.5) | DISABLED (budget 0, still computed) |
|---|---|---|---|
| rolling 3m virtual P&L | < DEV 10th pct of rolling 3m | < DEV 5th pct | < DEV minimum |
| rolling 6m / 12m virtual P&L | < DEV 10th pct | < DEV 5th pct | 12m < DEV minimum |
| rolling 6m matched-beta excess | < 0 | < DEV 5th pct | < DEV minimum for 2 consecutive months |
| current virtual DD | > DEV 75th pct of DD | > DEV 95th pct | > 1.25 x DEV MaxDD |
| fill rate / rejected orders (live vs virtual) | < 98% | < 95% | < 90% |
| friction per day | > 1.5 x DEV | > 2 x DEV | > 3 x DEV |
| average exposure vs virtual | deviation > 10% | > 20% | > 35% |

Transitions: evaluated after each completed session; recovery one state per 20 sessions once all inputs are back inside
the WATCH band. A DISABLED sleeve's budget is NOT redistributed automatically (portfolio simply holds less risk); any
redistribution is a new frozen decision. Every state change is logged with the inputs. This is a monitoring spec only; it
was not applied to the historical results in this report.
""")
    pre = json.load(open(f"{O}/freeze/TEST43P_PRE_VAL_FREEZE.json"))
    w("P17_PRE_VAL_FREEZE", "P17 Pre-VAL freeze", f"""
File `out/p/freeze/TEST43P_PRE_VAL_FREEZE.json`, SHA256 `{shas['TEST43P_PRE_VAL_FREEZE']}`, committed (21f0b33) before
any VAL portfolio outcome was computed; VAL script hash-checks it before running.

Frozen: eligibility, shadow list, candidate hashes/params, clusters, risk unit and sigma, portfolio budgets (P0, P1, P2,
P2B), regime-tilt logic (alphas 0.25/0.5), L per envelope, governor, envelopes, costs, margin, VAL pass rule, final
selection rule.

## Frozen risk scales
{md(pd.Series(pre['risk_scale_L']).rename('L').reset_index().rename(columns={'index': 'portfolio|envelope'}), 1)}
""")
    w("P18_VAL_CONFIRMATION", "P18 VAL confirmation (one time, frozen)", md(V[["portfolio", "risk_env", "DEV_avg", "DEV_max_dd", "DEV_ret_dd", "VAL_avg", "VAL_total", "VAL_max_dd", "VAL_worst", "VAL_excess_vs_mb", "VAL_ret_dd", "SLIP4_VAL_avg", "SLIP4_VAL_max_dd", "TIMING_BRITTLENESS_STRESS_VAL_avg", "VAL_env", "VAL_PASS"]], 2) +
      "\n\nDEV values in this DEV+VAL run are identical to the DEV-only run (causality check). All 18 frozen variants pass VAL. P3 does not beat P2 at MODERATE after cost -> not eligible for PRIMARY (no rescue). P0 is not better than simpler portfolios.\n\nNote: VAL (2025-01..09) is short (188 sessions) and bullish after the April sell-off; VAL numbers are confirmation, not a ranking tool.")
    V2 = V.copy(); V2["key"] = V2.portfolio + "|" + V2.risk_env
    pareto = []
    for _, r in V2.iterrows():
        dom = ((V2.DEV_avg >= r.DEV_avg) & (V2.DEV_max_dd <= r.DEV_max_dd) & ((V2.DEV_avg > r.DEV_avg) | (V2.DEV_max_dd < r.DEV_max_dd))).any()
        pareto.append(not dom)
    V2["DEV_pareto"] = pareto
    w("P19_PARETO_FRONTIER", "P19 Pareto frontier (DEV avg/day vs DEV MaxDD)", md(V2.sort_values("DEV_max_dd")[["key", "DEV_avg", "DEV_max_dd", "DEV_ret_dd", "VAL_avg", "VAL_max_dd", "DEV_pareto"]], 2))
    w("P20_FINAL_PORTFOLIO_SELECTION", "P20 Final portfolio selection", f"""
Pre-registered rule (frozen before VAL): {json.dumps(pre['final_selection_rule'], indent=1)}

Result: PRIMARY = {sel['PRIMARY']}; SECONDARY_1 = {sel['SECONDARY_1']}; SECONDARY_2 = {sel['SECONDARY_2']}.

{md(selrows[["portfolio", "risk_env", "members", "DEV_avg", "DEV_max_dd", "DEV_worst", "DEV_ret_dd", "Y2020_avg", "Y2022_avg", "VAL_avg", "VAL_max_dd", "VAL_worst", "VAL_excess_vs_mb"]], 2)}

Contract weights (desired contracts per sleeve contract) are in `TEST43P_FINAL_PORTFOLIOS.json`.
""")
    w("P21_HOLDOUT_ACCEPTANCE_RULES", "P21 Holdout acceptance rules (frozen, not applied)", f"SHA256 `{shas['TEST43P_HOLDOUT_ACCEPTANCE_RULES']}`\n\n```json\n{json.dumps(rules, indent=1)}\n```")
    w("P22_FINAL_FREEZE_MANIFEST", "P22 Final freeze manifest", f"""
`out/p/freeze/TEST43P_FINAL_PORTFOLIOS.json` SHA256 `{shas['TEST43P_FINAL_PORTFOLIOS']}` (references pre-VAL freeze
{shas['TEST43P_PRE_VAL_FREEZE'][:12]}... and holdout rules {shas['TEST43P_HOLDOUT_ACCEPTANCE_RULES'][:12]}...).
Contains exact portfolio names, membership, candidate hashes and parameters, clusters, budgets, contract weights, risk
normalisation, regime rules (none selected), governor, cost and margin assumptions, execution architecture, code hashes.

{md(pd.DataFrame([{'role': r, 'portfolio': p['portfolio'], 'envelope': p['risk_envelope'], 'L': p['risk_scale_L'], **{f'w[{c}]': round(m['contract_weight'], 4) for c, m in p['members'].items()}} for r, p in fin['portfolios'].items()]), 4)}
""")
    lines = []
    files = sorted(glob.glob(f"{O}/*.csv")) + sorted(glob.glob(f"{O}/*.json")) + sorted(glob.glob(f"{O}/freeze/*")) + sorted(glob.glob(f"{REP}/P[0-2]*.md"))
    for f in files:
        if "P23_HASH_INDEX" in f:
            continue
        lines.append({"file": os.path.relpath(f, ROOT), "bytes": os.path.getsize(f), "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()})
    h = pd.DataFrame(lines); h.to_csv(f"{O}/P23_HASH_INDEX.csv", index=False)
    w("P23_HASH_INDEX", "P23 Hash index", md(h, 0, 1000))
    print(stat_txt)


if __name__ == "__main__":
    main()
