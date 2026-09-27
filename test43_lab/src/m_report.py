"""Generate TEST43-M report family M00..M18 (markdown) from out/m/tables.  Usage: python m_report.py"""
import glob
import hashlib
import os

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
TAB = f"{ROOT}/out/m/tables"
REP = f"{ROOT}/reports/TEST43-M_REGIME_RANGE_FRACTAL_ANALOG"


def md(df, nd=3, maxrows=60):
    df = df.head(maxrows).copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].round(nd)
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def rd(name):
    return pd.read_csv(f"{TAB}/{name}")


def write(fn, title, body):
    os.makedirs(REP, exist_ok=True)
    open(f"{REP}/{fn}.md", "w").write(f"# {title}\n\nTEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. "
                                     f"HOLDOUT_OPENED = NO.\n\n{body}\n")


def main():
    mech = {t: rd(f"M04_M05_mechanism_info__{t}.csv") for t in ("ES", "MNQ", "ES5_MNQ5")}
    val = rd("M16_VAL_information_confirmation.csv")
    valo = rd("M16_VAL_overlay.csv") if os.path.exists(f"{TAB}/M16_VAL_overlay.csv") else None
    flags = FLAGS(val, valo)

    # ---------------- M01
    z = pd.concat([rd(f"M01_zone_information__{t}.csv") for t in ("ES", "MNQ")])
    zp = z.pivot_table(index=["inst", "zone"], columns="hz", values="t_d_ret60").round(1).reset_index()
    write("M01_RANGE_DEFINITION_AND_QA", "M01 Range definition and QA", f"""
## Definition (mechanical, causal)
* Trailing windows 15/30/60/120m (5/10/20/40 bars at 3m; 3/6/12/24 at 5m). Metrics per completed bar: overlap ratio
  (mean consecutive-bar overlap / union), directional efficiency |net|/path, width/(bar-ATR14*sqrt(H)), realised-vol
  contraction (sd of H-window changes / sd over 4H), close dispersion, touches of both 25% edges.
* **Qualified balance** = efficiency <= 33rd pct AND overlap >= median AND >=2 touches of each edge. **Compression** =
  qualified AND width <= 33rd pct AND vol-contraction <= median. Percentiles are *causal*: computed per session from the
  previous 60 sessions only (same RTH/ON side). Broad buckets only; no threshold was tuned.
* A qualified window is **frozen** at the bar it qualifies (boundaries never move; unit-tested). Re-freeze only while
  price is inside and no state machine is busy; NEW_BALANCE after an accepted expansion; expiry after 4H bars.
* Session-anchored frozen ranges: prior RTH (known at session open), 2D, 5D, opening range 15/30/60 (frozen at OR close).
* Qualified share of bars ~16-17% for every horizon (ES and MNQ), compression ~6-8%.

## QA
* `tests/test_ranges.py`: prefix invariance of every feature/state/event, frozen boundaries constant per range id,
  outcomes from NEXT bar open — pass.
* Real-data prefix invariance: the VAL build (data to 2025-09-30) reproduces every DEV feature column (105) and all
  917,621 (ES) / 921,631 (MNQ) DEV events exactly (`M08_prefix_invariance_real_data.csv`).
* Bugs found and fixed during the lab (all before any VAL use): (1) prior-RTH / 2D ranges expired at 04:00 (fixed to
  whole session); (2) first-passage counted unresolved windows as failures (volatility artefact; now NaN);
  (3) **session-equal-weighted means leak the future** (1/count weighting depends on the session's later path; BELOW-range
  bars +0.047 ATR session-weighted vs -0.003 ATR occurrence-weighted). All statistics now use occurrence weighting with
  session-clustered robust SE (`t43/mstats.py`).

## Location zones (Part 2) — matched-control t of the 60m return (control: year, tier, vol tercile, clock; no position)
{md(zp)}

Zones carry no directional information (all |t| < 2.6 except isolated cells; placebo-calibrated critical value ~2.6-2.8).
The hypothesis "MID = low information / BOUNDARY = high information" is **not supported**: the boundaries are not more
informative than the middle; no zone is informative. RANGE_MID_IS_LOW_INFORMATION_ZONE = NO for both instruments.
""")

    # ---------------- M02
    bal = pd.concat([rd(f"M02_balance_state_info__{t}.csv") for t in ("ES", "MNQ")])
    b2 = bal[bal.state.isin(["QUALIFIED_BALANCE", "COMPRESSION", "SM_ACCEPTED_EXPANSION", "SM_BREAKOUT_ATTEMPT"])]
    tr = pd.concat([rd(f"M02_event_transitions__{t}.csv") for t in ("ES", "MNQ")])
    trp = tr[tr.hz.isin(["15m", "30m", "60m", "120m", "PRTH"])].pivot_table(index=["inst", "from", "to"], columns="hz", values="p").round(3).reset_index()
    write("M02_RANGE_STATE_TRANSITIONS", "M02 Range state transitions and balance-state information", f"""
## Balance / compression vs matched control (60m forward return and forward 60m range, ATR units)
{md(b2[["inst", "hz", "state", "n_bars", "mean_d_ret60", "t_d_ret60", "mean_d_frange60", "t_d_frange60", "F1_t_d_frange60", "F2_t_d_frange60", "F3_t_d_frange60"]])}

**Reading.** Qualified balance / compression predicts a *smaller* next-60m range than the matched control (t -4 to -8
at 30-120m, all folds negative, both instruments): balance persists; it does not forecast expansion. It carries **no
directional** information (|t| < 2.2). RANGE_BALANCE_STATE_HAS_INFORMATION = YES (volatility / range only, not direction).
Controls match the daily vol regime, not intraday local volatility, so part of this is ordinary intraday vol clustering.

## Event transition probabilities (structural; nearly identical for ES and MNQ)
{md(trp, maxrows=80)}
Full per-bar state transition matrix: `M02_state_transition_matrix__*.csv`.
""")

    # ---------------- M03
    ne = pd.concat([rd(f"M03_nested_alignment__{t}.csv") for t in ("ES", "MNQ")])
    a = ne[ne.scope == "ALL_RTH_BARS"][["inst", "align", "n", "mean_d_ret60", "t_d_ret60", "pos60ctl_mean_d_ret60", "pos60ctl_t_d_ret60", "F1_t_d_ret60", "F2_t_d_ret60", "F3_t_d_ret60"]]
    e = ne[(ne.scope == "EVENT") & (ne.t_diff.abs() >= 2)][["inst", "hz", "ev", "align", "n", "mean_d_ret60", "diff_vs_other_align", "t_diff"]]
    write("M03_NESTED_RANGE_ANALYSIS", "M03 Nested range alignment", f"""
Positions recorded simultaneously: trailing 15/30/60/120m, RTH-so-far, prior RTH, 5D. Classes (descriptive, not tuned):
MULTI_LOW (>=4 of 7 positions <= 0.25, none >= 0.75), MULTI_HIGH (mirror), MID_CLUSTER (>=4 in 0.35-0.65), MIXED.

## Descriptive map (all RTH bars)
{md(a)}

## Events whose effect differs by alignment (|t_diff| >= 2 of {int((ne.scope == 'EVENT').sum())} event x alignment rows)
{md(e)}

Only 8 of ~450 event x alignment cells reach |t| >= 2 (chance ~ 5%). The one recurring pattern (UB_ACCEPT with
MULTI_HIGH at 120m / OR60, both instruments) was frozen as candidate C3 and **failed VAL** (M16).
NESTED_RANGE_ALIGNMENT_ADDS_VALUE_ES = {flags['NESTED_RANGE_ALIGNMENT_ADDS_VALUE_ES']}, _MNQ = {flags['NESTED_RANGE_ALIGNMENT_ADDS_VALUE_MNQ']}.
""")

    # ---------------- M04 / M05
    def mt(names):
        rows = []
        for t in ("ES", "MNQ"):
            x = mech[t]; x = x[x.ev.isin(names)]
            rows.append(x[["inst", "hz", "ev", "n", "n_sess", "n_campaign", "mean_d_ret60", "t_d_ret60", "mean_d_mae60", "t_d_mae60", "F1_t_d_ret60", "F2_t_d_ret60", "F3_t_d_ret60", "placebo_t_max_abs", "label_ret60"]])
        return pd.concat(rows)
    sw = ["L_SWEEP", "L_RECLAIM", "L_RETEST_HOLD", "L_RESUMPTION", "L_FAILED_RECLAIM", "U_SWEEP", "U_RECLAIM", "U_RETEST_HOLD", "U_FAILED_RECLAIM"]
    br = ["UB_BREAK", "UB_ACCEPT", "UB_RETEST_HOLD", "UB_RESUMED", "UB_FAILED_ACCEPT", "UB_REENTRY", "DB_ACCEPT", "DB_FAILED_ACCEPT", "DB_REENTRY"]
    tc = {t: mech[t].t_crit_placebo95.iloc[0] for t in mech}
    stat = f"""Statistic: occurrence-weighted mean of (event outcome - matched-control cell mean), session-clustered robust t.
Control cell = instrument x year x regime tier x vol tercile x 30-min clock bucket x broad (quintile) range position of the
same horizon. Critical |t| from a **timing placebo** (same events shifted 40-400 bars, 5 draws per row):
ES {tc['ES']:.2f}, MNQ {tc['MNQ']:.2f}, 5m {tc['ES5_MNQ5']:.2f}. Share of rows with |t| >= critical: ES
{(mech['ES'].t_d_ret60.abs() >= tc['ES']).mean():.1%}, MNQ {(mech['MNQ'].t_d_ret60.abs() >= tc['MNQ']).mean():.1%} (chance level).
Stability across horizons: `M10_mechanism_stability__*.csv` — no mechanism is stable across >= 2 horizons."""
    write("M04_SWEEP_RECLAIM_RETEST", "M04 Sweep -> reclaim -> retest -> resumption", f"""{stat}

{md(mt(sw)[lambda d: d.hz.isin(['15m', '30m', '60m', '120m', 'PRTH', 'OR30'])], maxrows=120)}

**Reading.** The progression SWEEP -> RECLAIM -> RETEST_HOLD -> RESUMPTION adds nothing beyond the control; later states
are not better than earlier ones. The only consistent (sub-critical) sign is a small positive 60m drift after a raw
lower-boundary sweep (L_SWEEP, +0.002..0.004 ATR ~ $1-2 per contract, below round-trip friction); frozen as C1/C2 and it
**failed VAL**. Reduction on upper sweeps/reclaims loses money (M14).
SWEEP_RECLAIM_RETEST_HAS_INFORMATION_ES = {flags['SWEEP_RECLAIM_RETEST_HAS_INFORMATION_ES']}, _MNQ = {flags['SWEEP_RECLAIM_RETEST_HAS_INFORMATION_MNQ']}.
""")
    write("M05_BREAK_ACCEPTANCE_RETEST", "M05 Break -> acceptance -> retest -> resumption", f"""{stat}

Acceptance = max(2, H/5) consecutive completed closes outside the frozen range; retest requires a prior departure > 10%
of width and a later revisit within 10% of the boundary; hold = close stays outside.

{md(mt(br)[lambda d: d.hz.isin(['15m', '30m', '60m', '120m', 'PRTH', '2D', '5D', 'OR30'])], maxrows=150)}

**Reading.** Breakouts, acceptances, retest-holds and resumptions carry no continuation information after matched
controls at any scale. Isolated cells (MNQ 2D/PRTH UB_BREAK +0.010..0.012 ATR, t 2.7-3.4 before the estimator fix;
t < critical after) do not survive the placebo-calibrated gate. Upside failures (ES 5D UB_FAILED_ACCEPT, ES OR15
U_RETEST_HOLD) were frozen (C4a/b) and failed VAL.
BREAK_RETEST_HAS_INFORMATION_ES = {flags['BREAK_RETEST_HAS_INFORMATION_ES']}, _MNQ = {flags['BREAK_RETEST_HAS_INFORMATION_MNQ']}.
""")

    # ---------------- M06
    de = pd.concat([rd(f"M06_destinations__{t}.csv") for t in ("ES", "MNQ")])
    d1 = de[de.ev.isin(["L_RECLAIM", "L_RETEST_HOLD", "U_RECLAIM", "U_RETEST_HOLD"]) & de.hz.isin(["15m", "30m", "60m", "120m", "PRTH", "OR30"])]
    d2 = de[de.ev.isin(["UB_ACCEPT", "UB_RETEST_HOLD", "DB_ACCEPT"]) & de.hz.isin(["15m", "30m", "60m", "120m", "PRTH", "OR30"])]
    write("M06_DESTINATION_ANALYSIS", "M06 Destination analysis", f"""
Invalidation: sweep extreme (sweep/reclaim) or range midpoint (breakouts). Window 4H bars (20..80). Descriptive only; no TP ladder.

## Sweep / reclaim: midpoint and opposite boundary before invalidation
{md(d1[["inst", "hz", "ev", "n", "P_mid_before_inval", "P_opp_before_inval", "med_bars_to_mid", "med_bars_to_opp", "mean_MAE_before_mid_atr", "mean_MFE_after_mid_atr"]], maxrows=60)}

## Break / acceptance: range-width units vs ATR units; does width carry destination information beyond ATR?
`excess_vs_ATRonly_1.0R` = P(hit +1.0 range width) minus the probability predicted by an ATR-only excursion curve at the
same distance; `partial_spearman` = rank correlation of excursion with width after removing local (bar-ATR) volatility.
{md(d2[["inst", "hz", "ev", "n", "P_hit_0.5R", "P_hit_1.0R", "P_hit_2.0R", "P_hit_0.5ATR", "P_hit_1.0ATR", "w_atr_median", "excess_vs_ATRonly_1.0R", "t_excess_1.0R", "spearman_mfe_width", "partial_spearman_mfe_width_given_localvol"]], maxrows=60)}

**Reading.** Excursions scale with width (Spearman 0.2-0.35) but mostly because width proxies local volatility; measured
moves in range units are not hit more often than an ATR-only model predicts (excess ~0 or negative at 30m+; positive
only for ES 15m). Midpoint is reached ~40-70% before invalidation at intraday scales, the opposite boundary ~25-50%.
RANGE_WIDTH_PREDICTS_DESTINATION_ES = NO (only 15m, not across scales), _MNQ = NO.
""")

    # ---------------- M07 / M08 / M09
    write("M07_ANALOG_MODEL_SPEC", "M07 Analog model specification", """
* Decision points: RTH bars closing on the quarter hour 10:00-16:00 (25/session). ~35.8k DEV points per instrument.
* Representations: SHAPE_ATR (close path at 6 evenly spaced points, (P_t - P_start)/ATR20_daily) and SHAPE_RANGE
  ((P_t - low_W)/(high_W - low_W)); windows 15/30/60/120m only.
* STATE families (standardised with warm-up-only constants; each family total weight 1): RANGE (60m qualified-range
  position or trailing position, RTH position, prior-RTH position), REGIME (tier, trend20/100), VOL (ATR20 pct, width,
  efficiency), NESTED (low/high alignment counts, 5D position), VWAP (z), CLOCK (time of day).
* Context hierarchy: same regime tier and same volatility tercile enforced by a large distance penalty, then Euclidean
  distance. Modes compared: SHAPE_ONLY (no context), SHAPE_PLUS_STATE (hierarchy + shape + all state), STATE_ONLY
  (hierarchy + state), RANDOM_IN_CONTEXT control (random neighbours inside the same context cell).
* k = 25/50/100/200 (all reported), at most 2 neighbours per library session; independent campaigns = distinct sessions.
* Library for a query in block starting at session s: points from sessions <= s-2 (1-session embargo), frozen per
  20-session block; warm-up 250 sessions (predictions start ~2020-05); library < 500 points -> NO_MATCH.
* Confidence HIGH/MED/LOW/NO_MATCH from median neighbour distance vs causal quantiles of previous blocks, neighbour
  agreement |mean|/(sd/sqrt(indep)), independent-campaign count. Targets: 30/60/120m return, 60m MFE/MAE, first passage.
* No DTW, no deep learning, no one-neighbour forecast.
""")
    meta = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{TAB}/M08_analog_library_meta__*.csv"))], keys=None)
    pi = rd("M08_prefix_invariance_real_data.csv")
    write("M08_ANALOG_CAUSAL_QA", "M08 Analog causal QA", f"""
* Library strictly before the query block in every block of every run: {bool(pd.concat([pd.read_csv(f) for f in glob.glob(f'{TAB}/M08_analog_library_meta__*.csv')]).strictly_before.all())}
  (`M08_analog_library_meta__*.csv`, {len(glob.glob(f'{TAB}/M08_analog_library_meta__*.csv'))} runs).
* Dependence control: mean raw neighbours = k, mean independent sessions ~0.95k (k=50) (see M09 tables).
* Real-data prefix invariance of the range/state features used by the analog:
{md(pi[["inst", "dev_bars", "feature_cols_checked", "feature_cols_mismatch", "dev_events", "val_build_dev_events", "events_identical"]])}
* **Rejected metric (look-ahead artefact):** a within-session (session-demeaned) IC produced 0.18 for STATE_ONLY;
  diagnosed as leakage (session mean uses the rest of the session; raw pos_rth alone scores -0.30). Removed. Likewise the
  session-paired tercile spread. Only pooled, control-residual IC is used.
* Standardisation constants from the first 250 sessions only; outcome labels are never features.
""")
    an = pd.concat([rd(f"M09_analog_eval__{t}_DEV.csv") for t in ("ES", "MNQ", "ES5", "MNQ5")])
    an2 = an[~an.config.str.startswith("ABL")][["inst", "config", "k", "n", "IC_pooled", "IC_pooled_t", "F1_IC_pooled", "F2_IC_pooled", "F3_IC_pooled", "top_minus_bottom_resid_atr"]]
    raw = pd.concat([rd(f"M09_analog_info__{t}_DEV.csv") for t in ("ES", "MNQ")])
    write("M09_ANALOG_OUTCOME_DISTRIBUTIONS", "M09 Analog information and outcome distributions", f"""
IC = Spearman(predicted 60m return, realised 60m return minus matched-control cell mean); t from monthly ICs.

{md(an2, nd=4, maxrows=80)}

## Risk information (predicted vs realised 60m MAE, control-residual)
{md(raw[raw.k.isin([100]) & ~raw.config.str.startswith('ABL')][["inst", "config", "k", "IC_raw", "IC_resid", "IC_mae60", "IC_mae60_resid", "IC_mfe60_resid", "mean_indep_campaigns"]], nd=3)}

**Reading.** No analog configuration has a positive, significant, fold-stable residual IC. SHAPE_ONLY ~0 (|t| < 1.9);
STATE_ONLY and SHAPE_PLUS_STATE are *negative* and no better than the RANDOM_IN_CONTEXT control (past-context means
do not forecast). Shape analogs do predict 60m MAE (IC ~0.13) but a plain local-volatility ratio does better (0.197) and
the partial correlation of the analog given local vol is -0.004: no value beyond ATR. Outcome-distribution quantiles by
prediction tercile: `M09_analog_info__*` / `analog_preds.parquet`.
""")

    # ---------------- M10
    ms = pd.concat([rd(f"M10_mechanism_stability__{t}.csv") for t in ("ES", "MNQ", "ES5_MNQ5")])
    write("M10_MATCHED_CONTROL_ANALYSIS", "M10 Matched-control analysis", f"""
Control = same instrument, era (year), regime tier, vol tercile, 30-min clock bucket, broad range-position quintile.
Deltas: future return, MFE, MAE, first passage (+0.5 before -0.5 ATR, conditional on resolution).

## Mechanism stability across the four intraday scales (non-NONE rows)
{md(ms[ms.verdict != 'NONE'], maxrows=80)}

Placebo-calibrated critical |t|: ES {tc['ES']:.2f}, MNQ {tc['MNQ']:.2f}, 5m {tc['ES5_MNQ5']:.2f}. After calibration the share
of informative rows equals the false-positive rate. Nothing adds information beyond regime + volatility + clock +
location controls: not sweep progression, breakout progression, nested alignment, or analog similarity.
""")

    # ---------------- M11
    fr = rd("M11_timeframe_fractal_transfer.csv"); ords = rd("M11_transition_ordering_stability.csv")
    write("M11_TIMEFRAME_FRACTAL_TRANSFER", "M11 Timeframe / fractal transfer", f"""
## Transition ordering across scales (Spearman of transition probabilities vs 3m/60m)
{md(ords)}

## Outcome effects across 15/30/60/120m and 3m vs 5m bars
{md(fr[["inst", "ev", "3m_sign_agree_of_4", "5m_sign_agree_of_4", "3m_n_sig_tcrit", "5m_n_sig_tcrit", "t_corr_3m_vs_5m", "same_sign_3m_5m_of_4", "FRACTAL_TRANSFER"]], maxrows=60)}

**Reading.** The *structure* is scale-invariant (transition ordering rank-correlation 0.69-1.0; ES and MNQ nearly
identical) — consistent with recurrent scale-normalised state mechanics. The *outcome information* is absent at every
scale, so there is nothing to transfer. MNQ L_SWEEP is the only mechanism with same-sign effects on both bar resolutions
(5m: 3 horizons above the 5m critical value; 3m: none) and it failed VAL.
FRACTAL_EFFECT_TRANSFERS_ACROSS_TIMEFRAMES_ES = NO, _MNQ = NO.
""")

    # ---------------- M12
    ab = an[an.config.str.startswith("ABL") | an.config.isin(["SHAPE_ONLY_ATR_60m", "STATE_ONLY"])]
    write("M12_ANALOG_FEATURE_ABLATION", "M12 Analog feature ablation", f"""
Base = SHAPE_ATR 60m path; one family added at a time (and the regime/vol hierarchy alone).
{md(ab[["inst", "config", "k", "IC_pooled", "IC_pooled_t", "F1_IC_pooled", "F2_IC_pooled", "F3_IC_pooled"]], nd=4, maxrows=80)}

No family adds measurable, stable value. +RANGE is the only one mildly positive on all four datasets (IC 0.010-0.019,
t 1.1-2.3); frozen as A1 and it failed VAL. +HIERARCHY / +REGIME / +VOL are negative. Complexity did not earn its place.
""")

    # ---------------- M13 / M14
    ov = rd("M13_incremental_exposure_DEV.csv"); ov = ov[ov.spec != "BASE"].copy()
    ov["mech"] = ov.spec.str.split("|").str[0]
    ov["improves"] = (ov.d_DEV_avg_daily > 0) & (ov.d_DEV_max_dd <= 0) & (ov.d_DEV_excess_vs_mb > 0)
    g = ov.groupby(["inst", "mech"]).agg(variants=("id", "size"), n_improve=("improves", "sum"),
                                        median_d_avg=("d_DEV_avg_daily", "median"), median_d_dd=("d_DEV_max_dd", "median"),
                                        median_d_excess=("d_DEV_excess_vs_mb", "median"), median_fills_ratio=("fills_ratio", "median"),
                                        margin_breaches=("margin_breach", "sum")).reset_index()
    write("M13_INCREMENTAL_EXPOSURE_TEST", "M13 Incremental exposure test (V6 finalist + TEST43-M modifier)", f"""
**Gate status:** no mechanism survived the information gate, so none was eligible for translation into exposure. The
overlay below is a DIAGNOSTIC on the strongest frozen candidates to show the incremental effect explicitly. The V6
candidates are untouched (base results reproduce the shortlist exactly; modifier hook `xm` in `t43/v6a.py` is a no-op at 1).
Modifier: target x {{1.25, 1.5}} on positive state (optional +2 contracts cap headroom, never in risk cut / DD tier),
x {{0.75, 0.5}} on negative state; hold 20 bars (60m) with no re-trigger while active (event), or to next decision point
(analog, HIGH/MED confidence). 10 V6A controls (ES_r2_G_AGG_0 is a v6x kernel; not overlay-compatible).

{md(g)}

Improvement = higher DEV avg/day AND DD not worse AND higher matched-beta excess. Most variants reduce net P&L and
multiply turnover 1.1-13x; the few improving cells are single candidates (+$1-4/day) with no pattern across candidates.
Full table: `M13_incremental_exposure_DEV.csv`.
""")
    red = rd("M14_reduction_avoided_vs_forgone.csv"); add = rd("M14b_add_now_vs_wait.csv")
    write("M14_REDUCTION_AVOIDED_VS_FORGONE", "M14 Reduction: avoided adverse vs forgone favourable (and add-now vs wait)", f"""
Reduction = cut the live V6 position (reference controls ES_robust_A_MOD_1 / MNQ_robust_A_MOD_2) by ~half at the state bar;
the reduced contracts are marked as if held. Net benefit = -(P&L of reduced contracts) - round-trip friction. USD, DEV.

{md(red[red.hz.isin(['30m', '60m', 'PRTH', 'OR30'])][["inst", "hz", "ev", "n", "mean_reduced_qty", "avoided_adverse_60m", "forgone_favourable_60m", "net_benefit_30m", "net_benefit_60m", "net_benefit_120m", "F1_net_benefit_60m", "F2_net_benefit_60m", "F3_net_benefit_60m"]], nd=0, maxrows=90)}

Avoided adverse ~= forgone favourable for every state; after friction almost every reduction state has negative net
benefit. The exception (ES PRTH UB_FAILED_ACCEPT, +$7.1k over DEV, positive in all folds, n=206) is too thin to act on.

## Add now vs wait for confirmation vs no add (1 contract, exit at +120m, USD after friction)
{md(add[add.hz.isin(['30m', '60m', 'PRTH', 'OR30'])][["inst", "hz", "event", "confirmation", "n", "wait_fill_rate", "NOW_pnl_usd", "NOW_t", "WAIT_pnl_usd_per_signal", "NOW_mae_usd", "WAIT_mae_usd", "F1_NOW_pnl_usd", "F2_NOW_pnl_usd", "F3_NOW_pnl_usd"]], nd=2, maxrows=90)}

No add state beats NO ADD reliably; waiting for confirmation lowers MAE but not expected P&L.
""")

    # ---------------- M15
    write("M15_DEV_INTERNAL_ROBUSTNESS", "M15 DEV internal robustness", f"""
Chronological folds F1 (<=2020), F2 (2021-22), F3 (2023-24), PRE23 vs 2023+ for every row (M04/M05/M01/M03 tables).
Horizon stability (15/30/60/120m), k stability (25/50/100/200), bar-resolution stability (3m vs 5m), timing placebo.

* Mechanism rows: ES {len(mech['ES'])}, MNQ {len(mech['MNQ'])}, 5m {len(mech['ES5_MNQ5'])}. PASS after placebo calibration: ES
  {int(mech['ES'].label_ret60.str.startswith('PASS').sum())}, MNQ {int(mech['MNQ'].label_ret60.str.startswith('PASS').sum())} (return); all isolated to one horizon -> UNSTABLE.
* Analog: no configuration positive at >=2 of 4 k with t >= 2; fold signs flip.
* Balance -> lower future range: stable in all folds (volatility information only).
""")

    # ---------------- M16
    vo = ""
    if valo is not None:
        vo = md(valo[["id", "spec", "VAL_avg_daily", "d_VAL_avg_daily", "d_VAL_max_dd", "d_VAL_excess_vs_mb", "d_DEV_avg_daily", "fills"]], nd=2, maxrows=80)
    write("M16_VAL_CONFIRMATION", "M16 VAL confirmation (one time, frozen, no retune)", f"""
Frozen file `out/m/frozen/TEST43M_FROZEN_MECHANISMS.json` (sha256 {open(f'{ROOT}/out/m/frozen/TEST43M_FROZEN_MECHANISMS.sha256').read().split()[0]}),
hash-checked before evaluation. VAL features built causally on data to 2025-09-30; DEV prefix reproduced exactly.
Pass rule (pre-registered): same sign as DEV and |t| >= 1.65.

## Information level
{md(val, nd=4)}

## Overlay level (pre-registered size up 1.25 / down 0.75, hold 20 bars, no headroom) — V6 baseline vs V6 + TEST43-M
{vo}

**Overlay reading.** O1 (up x1.25 for 60m after a 30m lower-range sweep) raised VAL P&L for most candidates
(ES +$5..41/day, MNQ -41..+22/day) while the *same frozen spec lost money on DEV* for the same candidates (d_DEV_avg_daily
column) and usually raised VAL drawdown and turnover. The information-level test of the same event failed VAL (C1/C2).
VAL (2025-01..09, sharp April sell-off and V-rebound) rewards any add-on-weakness exposure; this is regime/beta
exposure, not a validated mechanism. Under the governance (DEV gate failed; no rescue) it is not promoted.

Result: {int(val.VAL_PASS.sum())} of {len(val)} frozen candidates pass VAL at the information level (only C6, the
volatility-state effect of compression, for both instruments; every directional candidate fails). Per governance
nothing is rescued or retuned; TEST43-M is discarded and the V6 candidates remain intact.
""")

    # ---------------- M17
    fl = "\n".join(f"{k} = {v}" for k, v in flags.items())
    write("M17_FINAL_MECHANISM_REVIEW", "M17 Final mechanism review", f"""
## Answers
```
{fl}
```
## Summary
1. Balance vs expansion can be identified mechanically and causally; balance predicts continued low range, not direction.
2. Sweep/reclaim/retest and break/acceptance/retest are well-defined, scale-invariant state machines whose transition
   probabilities are almost identical for ES and MNQ and across 15m-120m and 3m/5m bars — but after matched controls and a
   placebo-calibrated threshold they carry no forward-return, MFE/MAE or first-passage information.
3. Nested alignment, range location zones (including the MID hypothesis) and range-width destinations add nothing beyond
   regime + vol + clock + location controls (width only proxies local volatility).
4. Historical analogs (kNN, strictly walk-forward, deduplicated) have no positive residual information in any mode;
   shape analogs predict risk (MAE) only as well as a local volatility ratio.
5. As exposure modifiers on untouched V6 candidates they mostly lower P&L and raise turnover; reductions avoid as much
   adverse as they forgo favourable movement and lose the friction.
6. Three methodological traps were found and corrected (session-equal weighting look-ahead, within-session demeaning
   look-ahead, unresolved first-passage volatility artefact) — each alone would have produced a false "edge".
7. Keep V6 finalists unchanged. The TEST43-M modules stay in the repo as diagnostics (and as a volatility-state input
   candidate for a future risk-governor study, not a trading signal).
""")

    # ---------------- M00, M18
    write("M00_STATUS", "M00 Status", f"""
Status: TEST43-M COMPLETE (DEV discovery + one-time VAL confirmation). HOLDOUT_OPENED = NO. PORTFOLIO_MEMBERSHIP_CHANGED = NO.
LIVE_AUTHORIZATION = NO. TEST43M_PROMOTE_TO_FINALIST = {flags['TEST43M_PROMOTE_TO_FINALIST']}.

Execution architecture note: the +1 bar test is renamed **TIMING_BRITTLENESS_STRESS** (it is a stress on decision-to-fill
timing, not expected latency). Production path = local engine -> local data -> state -> IBKR; TradingView/webhook is
validation/sentinel only. The live engine must log bar-close, decision, submit, IBKR ack and fill timestamps and slippage.
Research fill convention unchanged (completed-bar signal, next-bar-open fill).

Reports: M01..M18 in this folder. Machine-readable tables: `out/m/tables/*.csv`. Code: `src/t43/ranges.py`,
`src/t43/analog.py`, `src/t43/mstats.py`, `src/m_build.py`, `src/m_info.py`, `src/m_analog.py`, `src/m_analog_eval.py`,
`src/m_fractal.py`, `src/m_overlay.py`, `src/m_redadd.py`, `src/m_val_info.py`, `tests/test_ranges.py`.

Next (V6 track, unchanged): reduce finalist count, write + freeze holdout acceptance rules, freeze finalists, open holdout once.
""")
    lines = []
    for f in sorted(glob.glob(f"{TAB}/*.csv")) + sorted(glob.glob(f"{ROOT}/out/m/frozen/*")) + sorted(glob.glob(f"{REP}/M0*.md")) + sorted(glob.glob(f"{REP}/M1[0-7]*.md")):
        lines.append({"file": os.path.relpath(f, ROOT), "bytes": os.path.getsize(f), "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()})
    h = pd.DataFrame(lines)
    h.to_csv(f"{TAB}/../M18_HASH_INDEX.csv", index=False)
    write("M18_HASH_INDEX", "M18 Hash index", md(h, maxrows=500))
    print("reports written", len(glob.glob(f"{REP}/*.md")))


def FLAGS(val, valo):
    def vp(ids, inst):
        x = val[val.id.isin(ids) & (val.inst == inst)]
        return bool(len(x)) and bool(x.VAL_PASS.all())
    f = {}
    f["RANGE_BALANCE_STATE_HAS_INFORMATION"] = "YES (volatility/range only; NO directional information)"
    for i in ("ES", "MNQ"):
        f[f"SWEEP_RECLAIM_RETEST_HAS_INFORMATION_{i}"] = "NO"
    for i in ("ES", "MNQ"):
        f[f"BREAK_RETEST_HAS_INFORMATION_{i}"] = "NO"
    for i in ("ES", "MNQ"):
        f[f"NESTED_RANGE_ALIGNMENT_ADDS_VALUE_{i}"] = "YES" if vp(["C3"], i) else "NO"
    for i in ("ES", "MNQ"):
        f[f"RANGE_MID_IS_LOW_INFORMATION_ZONE_{i}"] = "NO (no zone is informative; boundaries are not more informative)"
    for i in ("ES", "MNQ"):
        f[f"RANGE_WIDTH_PREDICTS_DESTINATION_{i}"] = "NO"
    for m in ("SHAPE_ONLY_ANALOG_ADDS_VALUE", "STATE_ONLY_ANALOG_ADDS_VALUE", "SHAPE_PLUS_STATE_ADDS_VALUE"):
        for i in ("ES", "MNQ"):
            f[f"{m}_{i}"] = "NO"
    for i in ("ES", "MNQ"):
        f[f"FRACTAL_EFFECT_TRANSFERS_ACROSS_TIMEFRAMES_{i}"] = "NO (structure is scale-invariant; outcome information absent)"
    for i in ("ES", "MNQ"):
        imp = dd = ex = "NO"
        if valo is not None:
            x = valo[(valo.inst == i) & (valo.spec != "BASE")]
            if len(x):
                imp = "YES" if (x.d_VAL_avg_daily > 0).mean() > 0.75 else "NO"
                dd = "YES" if (x.d_VAL_max_dd < 0).mean() > 0.75 else "NO"
                ex = "YES" if (x.d_VAL_excess_vs_mb > 0).mean() > 0.75 else "NO"
        f[f"TEST43M_IMPROVES_V6_{i}"] = imp if imp == "NO" else imp + " (but gate failed)"
        f[f"TEST43M_REDUCES_DD_{i}"] = dd
        f[f"TEST43M_INCREASES_MATCHED_BETA_EXCESS_{i}"] = ex
    for i in ("ES", "MNQ"):
        x = val[val.inst == i]
        f[f"TEST43M_SURVIVES_VAL_{i}"] = "NO" if not x.VAL_PASS.any() else f"PARTIAL ({int(x.VAL_PASS.sum())}/{len(x)} frozen candidates; gate failed on DEV)"
    f["TEST43M_PROMOTE_TO_FINALIST"] = "NO"
    f["HOLDOUT_OPENED"] = "NO"
    f["PORTFOLIO_MEMBERSHIP_CHANGED"] = "NO"
    f["LIVE_AUTHORIZATION"] = "NO"
    return f


if __name__ == "__main__":
    main()
