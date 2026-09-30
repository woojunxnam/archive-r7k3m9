"""RUN-4 Sleeve A modules: conservation, causality (truncation), shadow book is observational only."""
import os, sys
import numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from mesgrid.data import bars_from_frame
from mesgrid.engine import Engine, ExecConfig
from mesgrid.features import compute_features
from mesgrid.factory import FactoryStrategy
from mesgrid.audit import reconcile
from mesgrid import slotmetrics as sm
from test_factory import rand_df
from test_audit import with_roll, FQ

BASEQ = dict(FQ["FQ_16_16_add"], core_cap=6, rec_cap=6, max_total=12, recovery=dict(h=6, rec_tp=2.0, rec_step=10.0, layer_x=5.0),
             rec_entry_mode="limit_close", dead_days=0.02)
SV = dict(trig="free", k=0, rebound="pts", rb=3.0, select="closest_be", max_per_day=3)


def extras(b, F):
    W = np.flatnonzero(b.in_window)
    hp = pd.Series(b.h[W]).shift(1).rolling(5, min_periods=3).max().values
    a = np.full(len(b), np.nan); a[W] = hp
    rnd = np.zeros(len(b), bool); rnd[W] = np.random.default_rng(7).random(len(W)) < 0.05
    sc = np.full(len(b), np.nan); sc[W] = np.random.default_rng(8).random(len(W))   # independent streams: prefix-stable
    return {"r4_high5p": a, "rnd_s1": rnd, "trap_test": sc}


MODS = {
    "shadow": dict(BASEQ, shadow=True),
    "harv_free_newest": dict(BASEQ, harvest_cond=dict(trig="free", k=1, policy="newest_prof", hx=1.0)),
    "harv_dead_all": dict(BASEQ, harvest_cond=dict(trig="dead", x=0.3, policy="all_prof", hx=1.0)),
    "harv_inv_probe": dict(BASEQ, harvest_cond=dict(trig="inv", q=8, policy="prof_be", be=1.0)),
    "harv_partial_core": dict(BASEQ, harvest_cond=dict(trig="free", k=2, policy="partial", hx=1.0, core=True)),
    "salv_pts": dict(BASEQ, salvage=SV),
    "salv_vwap_oldest": dict(BASEQ, salvage=dict(SV, rebound="vwap", select="oldest")),
    "salv_rollhigh_highest": dict(BASEQ, salvage=dict(SV, rebound="rollhigh", select="highest")),
    "salv_mid30": dict(BASEQ, salvage=dict(SV, rebound="mid30")),
    "salv_pivot_always": dict(BASEQ, salvage=dict(SV, rebound="pivot", trig="always")),
    "csm_deep_mult": dict(BASEQ, cap_sm=dict(min_free=3, deep_mult=2.0)),
    "csm_full": dict(BASEQ, cap_sm=dict(min_free=3, deep_off=2.0, ttl=20, harvest="newest_prof", hx=1.0, salvage=SV)),
    "soft": dict(BASEQ, rec_soft=dict(feat="trap_test", cuts=(0.3, 0.6, 0.9), offs=(0, 1, 2, 3), ttl=15, skip_top=True)),
    "soft_atr": dict(BASEQ, rec_soft=dict(feat="trap_test", cuts=(0.5,), offs=(0, 0.25), unit="atr", ttl=10)),
    "null_none": dict(BASEQ, rec_anchor="none"),
    "null_feat": dict(BASEQ, rec_anchor="feat", rec_anchor_feat="rnd_s1"),
    "static_core_rec": dict(BASEQ, core_mode="static", recovery=None),
    "static_core_only": dict(BASEQ, core_mode="static", recovery=None, rec_cap=0, max_total=6),
    "static_core_csm": dict(BASEQ, core_mode="static", recovery=None, cap_sm=dict(min_free=2, deep_mult=2.0, harvest="newest_prof", hx=1.0, salvage=SV)),
}


def _run(df, cfg, audit=False):
    b = bars_from_frame(df, False)
    F = compute_features(b, b.v)
    F.update(extras(b, F))
    s = FactoryStrategy(F, **cfg)
    return Engine(b, s, ExecConfig(), audit=audit).run(), s, F


@pytest.mark.parametrize("name", list(MODS))
def test_run4_modules_conserve_and_causal(name):
    df = with_roll(rand_df(days=8, seed=21, drift=-0.25))
    e, s, F = _run(df, MODS[name], audit=True)
    assert reconcile(e)["all_ok"]
    cut = 2000
    ep, _, _ = _run(df.iloc[:cut], MODS[name])
    ff = e.fills_df[e.fills_df.idx < cut - 1].reset_index(drop=True)
    pf = ep.fills_df[ep.fills_df.idx < cut - 1].reset_index(drop=True) if len(ep.fills_df) else ep.fills_df
    if len(ff) or len(pf):
        pd.testing.assert_frame_equal(ff[["idx", "side", "lane", "px", "tag"]], pf[["idx", "side", "lane", "px", "tag"]])


def test_modules_actually_fire():
    df = with_roll(rand_df(days=8, seed=21, drift=-0.25))
    _, s, _ = _run(df, MODS["salv_pivot_always"])
    assert s.n_salvage > 0
    _, s, _ = _run(df, MODS["harv_free_newest"])
    assert s.n_cond_harvest > 0
    e, _, _ = _run(df, MODS["soft"])
    assert (e.fills_df.tag == "rec_pend").any()


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_shadow_is_observational(seed):
    df = with_roll(rand_df(days=8, seed=seed, drift=-0.3))
    e0, _, _ = _run(df, BASEQ)
    e1, s1, _ = _run(df, dict(BASEQ, shadow=True))
    pd.testing.assert_frame_equal(e0.fills_df, e1.fills_df)
    assert len(s1.shadow_log) > 0
    bi = sm.BarIndex(e1.bars)
    m = sm.shadow_metrics(e1, s1, bi, True)
    assert m["shadow_signals"] == len(s1.shadow_log)
    assert m["shadow_trades"] >= 1


def test_slot_metrics_consistency():
    df = with_roll(rand_df(days=8, seed=4, drift=-0.3))
    e, s, F = _run(df, dict(BASEQ, shadow=True))
    bi = sm.BarIndex(e.bars)
    m = sm.slot_metrics(e, bi, F)
    cap = e.lanes["rec"].spec.capacity
    tot = m["slots_free_avg"] + m["slots_fresh_avg"] + m["slots_stalled_avg"] + m["slots_dead_avg"]
    assert abs(tot - cap) < 1e-9
    # time-average occupancy equals the average of the state's recycle quantity over tradeable bars (before-exit convention)
    q = e.state.qty_rec.values[e.bars.tradeable]
    assert abs(m["rec_occ_avg"] - q.mean()) < 0.05 * cap
    d = sm.nulld_decomposition(e)
    assert abs(d["nulld_passive_pnl"] + d["timing_pnl"] - d["mtm_px_pnl"]) < 1e-6
