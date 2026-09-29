"""RUN-3 addendum A-I, X-AE: Bottom event study. Output BOTTOM_EVENT_STUDY.csv (+ parquet caches for reuse).
Entry proxy = next-bar open (ES price as MES proxy). Gross points (no costs); round-trip cost ~0.75pt MES-equivalent
(1 tick slip each side + $1.24 commission) is noted separately. Same-bar target/stop ambiguity = loss."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.events import forward_outcomes, event_features, PAIRS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache"); os.makedirs(CACHE, exist_ok=True)
SPLITS = {"s1_2019_21": (2019, 2021), "s2_2022": (2022, 2022), "s3_2023_24": (2023, 2024), "s4_2025_26": (2025, 2026)}


def roll_any(x, n):
    return pd.Series(x.astype(float)).rolling(n, min_periods=1).max().values > 0


def build_events(X):
    E = {}
    E["ALL_BARS (baseline)"] = np.ones(len(X), bool)
    for t in (-1.0, -1.5, -2.0, -3.0):
        E[f"LOC vwap_dev<= {t}ATR"] = X.vwap_dev_atr.values <= t
    for t in (-1.5, -2.0, -2.5):
        E[f"LOC vwap_z<= {t}"] = X.vwap_z.values <= t
    for t in (-2.0, -3.0, -4.0):
        E[f"LOC sess_dd<= {t}ATR"] = X.sess_dd_atr.values <= t
    E["LOC near_sess_low"] = X.near_sess_low.values
    E["LOC prev_close_dd<=-2ATR"] = X.prev_close_dd_atr.values <= -2
    E["LOC below_prev_day_low"] = X.below_pdl.values
    E["LOC within0.5ATR_of_pdl"] = np.abs(X.dist_pdl_atr.values) <= 0.5
    E["LOC below_prev_week_low"] = X.below_pwl.values
    for N in ("15", "30", "60", "120", "1d", "5d"):
        for q in (0.05, 0.10, 0.20, 0.25, 0.33):
            E[f"LOC rpos{N}<= {q}"] = X[f"rpos{N}"].values <= q
    for k in (2, 3, 4, 5):
        E[f"EXH consec_down>={k}"] = X.consec_down.values >= k
    for nm in ("big_bear", "atr_spike", "rvol_spike", "decel", "shrinking_bodies", "growing_lower_wicks", "failed_new_low",
               "newlow_weak_close", "newlow_reclaim", "rex_contract"):
        E[f"EXH {nm}"] = X[nm].values.astype(bool)
    E["EXH dist_ema20<=-1.5ATR"] = X.dist_ema20_atr.values <= -1.5
    E["EXH sess_dd<=-3ATR (large intraday DD)"] = X.sess_dd_atr.values <= -3
    for nm in ("close_upper25", "close_upper33", "long_lower_wick", "bull_engulf", "outside_rev", "inside_after_sell",
               "prev_high_reclaim", "two_bar_hc", "two_bar_rev", "ll_higher_close", "ll_close_gt_pc", "micro_double_bottom",
               "sweep_reclaim30", "sweep_reclaim_sess", "sweep_reclaim_pdl"):
        E[f"REV {nm}"] = X[nm].values.astype(bool)
    E["REV wick/body>=2"] = X.wick_body_ratio.values >= 2
    for N in ("15", "30", "60", "120"):
        E[f"REV newlow{N} (raw)"] = X[f"newlow{N}"].values.astype(bool)
    # context splits of a reference setup
    ref = X.vwap_dev_atr.values <= -1.5
    for tod in sorted(X.tod.unique()):
        E[f"TOD {tod} | vwap_dev<=-1.5"] = ref & (X.tod.values == tod)
        E[f"TOD {tod} | all"] = X.tod.values == tod
    for vr in ("LOW", "NORMAL", "HIGH", "EXTREME"):
        E[f"VOL {vr} | vwap_dev<=-1.5"] = ref & (X.volreg.values == vr)
    E["CTX downtrend_persist | vwap_dev<=-1.5"] = ref & X.down_trend_persist.values
    E["CTX not_persist | vwap_dev<=-1.5"] = ref & ~X.down_trend_persist.values
    E["CTX slope60<-3ATR | vwap_dev<=-1.5"] = ref & (X.slope60_atr.values < -3)
    E["CTX slope60>=0 | vwap_dev<=-1.5 (trend-up pullback)"] = ref & (X.slope60_atr.values >= 0)
    E["CTX gap<-0.5dATR day | vwap_dev<=-1.5"] = ref & (X.gap_atr.values < -0.5)
    # two-stage: setup within last 10 bars + confirmation now
    setups = {"vwapdev-1.5": X.vwap_dev_atr.values <= -1.5, "rpos60<=0.1": X.rpos60.values <= 0.1,
              "sessdd-3": X.sess_dd_atr.values <= -3, "flush": X.big_bear.values.astype(bool) | X.atr_spike.values.astype(bool)}
    confs = {"prev_high_reclaim": X.prev_high_reclaim.values.astype(bool), "two_bar_hc": X.two_bar_hc.values.astype(bool),
             "failed_new_low": X.failed_new_low.values.astype(bool), "two_bar_rev": X.two_bar_rev.values.astype(bool)}
    for sn, sv in setups.items():
        rec = roll_any(sv, 10)
        E[f"2STG cheap-only {sn}"] = sv
        for cn, cv in confs.items():
            E[f"2STG {sn} -> {cn}"] = rec & cv
    for cn, cv in confs.items():
        E[f"2STG confirmation-only {cn}"] = cv
    # three-stage: flush (last 20) + stabilization (no new low last 5) + reclaim
    flush = roll_any(X.slope30_atr.values <= -2.0, 20)
    l5new = roll_any(X.newlow15.values.astype(bool), 5)
    E["3STG flush->stable5->reclaim"] = flush & ~l5new & X.prev_high_reclaim.values.astype(bool)
    E["3STG flush->stable5->reclaim & vwapdev<=-1"] = E["3STG flush->stable5->reclaim"] & (X.vwap_dev_atr.values <= -1)
    # confluence (only modules with individual value are combined in the analysis stage; listed here for audit)
    E["CONF rpos60<=0.1 & vwapdev<=-1 & near_pdl"] = (X.rpos60.values <= 0.1) & (X.vwap_dev_atr.values <= -1) & (np.abs(X.dist_pdl_atr.values) <= 1)
    return E


def second_entry(X, b, W):
    l, h, c = b.l[W], b.h[W], b.c[W]
    a15 = np.maximum(X_a15, 0.25)
    lo_prior = pd.Series(l).shift(6).rolling(25, min_periods=10).min().values
    lo_recent = pd.Series(l).rolling(6, min_periods=3).min().values
    hi30 = pd.Series(h).rolling(30, min_periods=10).max().values
    return (lo_recent > lo_prior) & (lo_recent < lo_prior + 0.5 * a15) & (hi30 - lo_prior >= a15) & X.prev_high_reclaim.values.astype(bool)


def agg(mask, O, name, delay=0):
    m = mask & O.tradeable.values
    if delay:
        m = np.concatenate([np.zeros(delay, bool), m[:-delay]])   # same-day check implicit via outcome NaNs
    sub = O[m]
    r = dict(event=name, delay=delay, n=int(m.sum()), per_day=m.sum() / float(O.day_n.iloc[0]))
    for U, D in PAIRS:
        r[f"p_{U}_before_{D}"] = sub[f"win_{U}_{D}"].mean()
    for k in (5, 15, 30, 60, 120):
        r[f"ret{k}"] = sub[f"ret{k}"].mean()
    r.update(mfe15=sub.mfe15.mean(), mae15=sub.mae15.mean(), mfe60=sub.mfe60.mean(), mae60=sub.mae60.mean(),
             t_reb2_5_med=sub["t_reb2.5"].median(), t_mfe60_med=sub.t_mfe60.median(), p_newlow30=sub.newlow30.mean(),
             persist60=(sub.ret60 / sub.mfe60.replace(0, np.nan)).median())
    for sk, (y0, y1) in SPLITS.items():
        ss = sub[(sub.year >= y0) & (sub.year <= y1)]
        r[f"{sk}_n"] = len(ss)
        r[f"{sk}_p3"] = ss["win_3.0_3.0"].mean()
        r[f"{sk}_ret30"] = ss.ret30.mean()
    return r


if __name__ == "__main__":
    t0 = time.time()
    b = load_canonical(); F = compute_features(b, b.v)
    pO = os.path.join(CACHE, "fwd_outcomes.parquet"); pX = os.path.join(CACHE, "event_features.parquet")
    if os.path.exists(pO):
        O = pd.read_parquet(pO)
    else:
        O = forward_outcomes(b); O.to_parquet(pO)
    X = event_features(b, F); X.to_parquet(pX)
    W = X.idx.values
    X_a15 = F["atr15"][W]
    O["day_n"] = 0
    O.day_n = len(np.unique(b.day[b.tradeable]))
    print("outcomes/features ready", round(time.time() - t0), "s", flush=True)
    E = build_events(X)
    E["AB second_entry_long"] = second_entry(X, b, W)
    E["AB first_flush_buy (compare)"] = X.big_bear.values.astype(bool) & (X.vwap_dev_atr.values <= -1)
    rows = [agg(v, O, k) for k, v in E.items()]
    # delay robustness for a pre-listed set
    for k in ("2STG vwapdev-1.5 -> prev_high_reclaim", "3STG flush->stable5->reclaim", "REV sweep_reclaim30", "LOC vwap_dev<= -2.0ATR",
              "AB second_entry_long", "EXH failed_new_low", "EXH newlow_reclaim"):
        for d in (1, 2, 3):
            rows.append(agg(E[k], O, k, delay=d))
    df = pd.DataFrame(rows)
    base = df.iloc[0]
    for col in [c for c in df.columns if c.startswith("p_") or c.endswith("_p3")]:
        df[f"lift_{col}"] = df[col] - (base[col])
    split_lifts = df[[f"lift_{s}_p3" for s in SPLITS]]
    df["stable_all_splits"] = (split_lifts > 0).all(axis=1)
    df["min_split_lift_p3"] = split_lifts.min(axis=1)
    df.to_csv(os.path.join(ROOT, "BOTTOM_EVENT_STUDY.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    cols = ["event", "delay", "n", "per_day", "p_3.0_before_3.0", "p_5.0_before_10.0", "p_10.0_before_5.0", "ret30", "mae15", "mfe15",
            "p_newlow30", "min_split_lift_p3", "stable_all_splits"]
    print(df[cols].round(3).to_string(index=False))
    print("total", round(time.time() - t0), "s")
