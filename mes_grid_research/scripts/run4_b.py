"""RUN-4 Sleeve B stages. Usage: python scripts/run4_b.py <stage>
S1: every event definition x 5 coarse exits (broad screen). Later stages are generated from S1 results.
All results: ES-signal / MES-economics proxy backtest (in-sample, NOT OOS)."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import run4_lib as L
import run4_b_lib as BL

INF = float("inf")
S1_EXITS = {"tp2_t5": dict(tp=2.0, tmax=5), "tp3_t15": dict(tp=3.0, tmax=15), "tp5_t30": dict(tp=5.0, tmax=30),
            "tp7.5_t60": dict(tp=7.5, tmax=60), "t60": dict(tmax=60)}
EX = dict(slippage_ticks=1, penetration_ticks=1, commission_per_side=0.62)


def E(family, params, parent=None, note="", stage="S1", exec_kw=None):
    return L.make_entry("B", family, params, exec_kw=exec_kw or EX, parent=parent, kind="fastsim", stage=stage, fresh=(), note=note)


def run_seq(entries, tag):
    done = L.done_ids()
    todo = [e for e in entries if e["config_id"] not in done or not os.path.exists(L.result_path(e))]
    print(f"[{tag}] {len(entries)} configs, {len(todo)} to run", flush=True)
    t0 = time.time()
    for k, e in enumerate(todo):
        cid, st, err = L._worker_wrap((BL.job_b, e))
        if st == "FAILED":
            print("FAILED", cid, err[:300], flush=True)
        if (k + 1) % 100 == 0:
            print(f"[{tag}] {k + 1}/{len(todo)} {time.time() - t0:.0f}s", flush=True)


def s1():
    J = []
    for name, m in BL.G["meta"].items():
        for xn, xp in S1_EXITS.items():
            J.append(E(f"B-{m['family']}", dict(events=[name], **xp), note=f"{name} {xn}"))
    return J


EOD = 10**9


def load_b(stage=None):
    d = L.collect("B")
    if not len(d):
        return d
    d["pp"] = d.params.apply(json.loads)
    d["ev_name"] = d.pp.apply(lambda p: "+".join(p["events"]))
    return d if stage is None else d[d.stage == stage]


def s2():
    """exit / execution research for the strongest S1 events (auto-selected from S1 results): 20 events by best gross
    EV/trade across S1 exits (>= 300 trades), plus 6 high-turnover events (>= 5 trades/day) by best gross EV."""
    d = load_b("S1")
    g = d[d.trades >= 300].groupby("ev_name").ev_gross.max().sort_values(ascending=False)
    top = list(g.index[:20])
    ht = d[(d.tpd_mean >= 5)].groupby("ev_name").ev_gross.max().sort_values(ascending=False)
    top_ht = [e for e in ht.index if e not in top][:6]
    ex = {"t30": dict(tmax=30), "t90": dict(tmax=90), "t120": dict(tmax=120), "t240": dict(tmax=240), "tEOD": dict(tmax=EOD),
          "tp5_t60": dict(tp=5.0, tmax=60), "tp7.5_t120": dict(tp=7.5, tmax=120), "tp10_t120": dict(tp=10.0, tmax=120),
          "tp10_EOD": dict(tp=10.0, tmax=EOD), "tp15_EOD": dict(tp=15.0, tmax=EOD),
          "trail3_EOD": dict(trail=3.0, tmax=EOD), "trail5_EOD": dict(trail=5.0, tmax=EOD), "trail8_EOD": dict(trail=8.0, tmax=EOD),
          "STOP5_t60": dict(stop=5.0, tmax=60), "STOP8_EOD": dict(stop=8.0, tmax=EOD),
          "lmt0.5x5_t60": dict(lim_off=0.5, ttl=5, tmax=60), "lmt1x10_t60": dict(lim_off=1.0, ttl=10, tmax=60),
          "lmt0.5x5_tp7.5_t120": dict(lim_off=0.5, ttl=5, tp=7.5, tmax=120), "lmt1x10_tEOD": dict(lim_off=1.0, ttl=10, tmax=EOD)}
    ex_ht = {"tp1.5_t3": dict(tp=1.5, tmax=3), "tp2_t10": dict(tp=2.0, tmax=10), "tp2.5_t10": dict(tp=2.5, tmax=10),
             "tp4_t30": dict(tp=4.0, tmax=30), "t10": dict(tmax=10), "lmt0.5x3_tp2_t10": dict(lim_off=0.5, ttl=3, tp=2.0, tmax=10),
             "lmt1x5_tp3_t15": dict(lim_off=1.0, ttl=5, tp=3.0, tmax=15), "lmt0x1_tp2_t10": dict(lim_off=0.0, ttl=1, tp=2.0, tmax=10)}
    J = []
    for evn in top:
        fam = BL.G["meta"][evn]["family"]
        for xn, xp in ex.items():
            J.append(E(f"B-{fam}", dict(events=[evn], **xp), note=f"S2 {evn} {xn}", stage="S2"))
    for evn in top_ht:
        fam = BL.G["meta"][evn]["family"]
        for xn, xp in ex_ht.items():
            J.append(E(f"B-{fam}", dict(events=[evn], **xp), note=f"S2-HT {evn} {xn}", stage="S2"))
        for cd in (1, 2, 3, 5):
            J.append(E(f"B-{fam}", dict(events=[evn], tp=2.0, tmax=10, cooldown=cd), note=f"S2-HT {evn} tp2_t10 cooldown{cd}", stage="S2"))
    return J


def _variant_events():
    """B7 first-impulse and B4 opening-range events with perturbed parameters (local robustness, +/-10-20%).
    Deterministic; names encode parameters."""
    from mesgrid.features import compute_features
    from mesgrid.mtf import add_basic_features, mtf_bars, prior_min, to_1m
    from mesgrid.momentum import _second_leg, _orb_states
    b = BL.G["b"]
    n = len(b)
    ok = BL.G["nxt"] & ~BL.G["nil"] & b.tradeable
    new = {}
    for k in (2, 3, 5):
        m = add_basic_features(mtf_bars(b, k))
        for Lb in (8, 10, 12):
            ll = prior_min(m["l"], Lb, m["nb"])
            for km in (4.0, 4.5, 5.0, 5.5, 6.0):
                first, second = _second_leg(m["h"], m["l"], m["c"], m["newday"], ll, m["atr"], km, 0.3)
                new[f"B7v_tf{k}_L{Lb}_k{km}_first"] = to_1m(m, first, n)
    m1 = add_basic_features(mtf_bars(b, 1))
    for orn in (10, 12, 15, 18, 20):
        brk, rt, fdr = _orb_states(m1["h"], m1["l"], m1["c"], m1["nb"], m1["newday"], orn, 0.5)
        new[f"B4v_or{orn}_break"] = to_1m(m1, brk, n)
        new[f"B4v_or{orn}_pullback"] = to_1m(m1, rt, n)
    for k2, v in new.items():
        BL.G["ev"][k2] = np.flatnonzero(v & ok)
        BL.G["meta"][k2] = dict(family=k2[:2], variant=True)


def _null_events(evname, seeds=20):
    """random entries preserving the event's per-year count and 15-minute time-of-day distribution."""
    b = BL.G["b"]
    ok = BL.G["nxt"] & ~BL.G["nil"] & b.tradeable
    cand = np.flatnonzero(ok)
    key = (BL.G["years"][cand] * 100 + (b.minute[cand] - 571) // 15)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    ev = BL.G["ev"][evname]
    ek = BL.G["years"][ev] * 100 + (b.minute[ev] - 571) // 15
    names = []
    for s in range(1, seeds + 1):
        rng = np.random.default_rng(10_000 + s)
        lo = np.searchsorted(ks, ek, "left"); hi = np.searchsorted(ks, ek, "right")
        pick = cand[order[lo + (rng.random(len(ek)) * (hi - lo)).astype(np.int64)]]
        nm = f"NULL_{evname}_s{s}"
        BL.G["ev"][nm] = np.unique(pick)
        BL.G["meta"][nm] = dict(family="NULL", base=evname, seed=s)
        names.append(nm)
    return names


def s3():
    """local robustness (event params +/-, exits +/-) for the B survivors + random-timing nulls."""
    _variant_events()
    J = []
    exits = {f"tp{tp}_t{t}": dict(tp=tp, tmax=t) for tp in (6.0, 7.5, 9.0, 10.0, 12.0) for t in (90, 120, 150)}
    for nm in [k for k in BL.G["ev"] if k.startswith("B7v_")]:
        for xn in ("tp7.5_t120", "tp10.0_t120"):
            J.append(E("B-B7", dict(events=[nm], **exits[xn]), note=f"S3 {nm} {xn}", stage="S3"))
    for xn, xp in exits.items():
        J.append(E("B-B7", dict(events=["B7_tf3_k5.0_first"], **xp), note=f"S3 exit grid {xn}", stage="S3"))
        J.append(E("B-B7", dict(events=["B7_tf3_k5.0_first"], lim_off=0.5, ttl=5, **xp), note=f"S3 exit grid lmt {xn}", stage="S3"))
    for nm in [k for k in BL.G["ev"] if k.startswith("B4v_")]:
        for xp in (dict(tp=15.0, tmax=EOD), dict(tp=10.0, tmax=EOD), dict(tp=10.0, tmax=240)):
            J.append(E("B-B4", dict(events=[nm], **xp), note=f"S3 {nm}", stage="S3"))
    for evn, xp in (("B7_tf3_k5.0_first", dict(tp=7.5, tmax=120)), ("B4_or15_break", dict(tp=15.0, tmax=EOD)),
                    ("B4_or15_pullback", dict(tp=10.0, tmax=EOD)), ("B1_tf10_body1.2", dict(tmax=60))):
        for nm in _null_events(evn):
            J.append(E("B-NULL", dict(events=[nm], **xp), parent=evn, note=f"S3 NULL for {evn}", stage="S3"))
    return J


B_FINALISTS = {
    "B7F": dict(events=["B7_tf3_k5.0_first"], lim_off=0.5, ttl=5, tp=9.0, tmax=120),
    "B4F": dict(events=["B4v_or18_pullback"], tp=10.0, tmax=EOD),
    "B1F": dict(events=["B1_tf10_body1.2"], tmax=60),
    "B4O": dict(events=["B4_or15_break"], tp=15.0, tmax=EOD),
}
UNION = ["B7_tf3_k5.0_first", "B1_tf10_body1.2", "B4_or15_break", "B4v_or18_pullback", "B9_tf5_vwap_deep", "B2_tf3_N4_rngexp"]


def s4():
    """B finalists: clustering / union combos (trade-count question), cooldown, execution stress (1-4 ticks, higher
    commission, 2-tick penetration, no same-bar TP on the entry bar)."""
    _variant_events()
    J = []
    for w in (0, 1, 2, 3):
        for xn, xp in (("tp9_t120", dict(tp=9.0, tmax=120)), ("t60", dict(tmax=60))):
            J.append(E("B-UNION", dict(events=UNION, cluster_min=w, **xp), note=f"S4 union6 cluster{w}m {xn}", stage="S4"))
    allev = [k for k in BL.G["meta"] if not k.startswith(("B7v", "B4v", "NULL"))]
    for w in (1, 3):
        J.append(E("B-UNION", dict(events=allev, cluster_min=w, tp=2.0, tmax=5), note=f"S4 union-ALL-167 cluster{w}m tp2_t5", stage="S4"))
        J.append(E("B-UNION", dict(events=allev, cluster_min=w, tmax=60), note=f"S4 union-ALL-167 cluster{w}m t60", stage="S4"))
    for fn, p in B_FINALISTS.items():
        for slip in (1, 2, 3, 4):
            for comm in (0.62, 0.775, 0.93):
                ex = dict(EX, slippage_ticks=slip, commission_per_side=comm)
                J.append(E("B-STRESS", dict(p), exec_kw=ex, parent=fn, note=f"S5 {fn} slip{slip} comm{comm}", stage="S5"))
        J.append(E("B-STRESS", dict(p), exec_kw=dict(EX, penetration_ticks=2), parent=fn, note=f"S5 {fn} pen2", stage="S5"))
        J.append(E("B-STRESS", dict(p, strict=True), parent=fn, note=f"S5 {fn} strict entry-bar TP", stage="S5"))
        J.append(E("B-STRESS", dict(p, strict=True), exec_kw=dict(EX, slippage_ticks=2, penetration_ticks=2, commission_per_side=0.93),
                   parent=fn, note=f"S5 {fn} all-stress", stage="S5"))
        for cd in (1, 2, 3, 5):
            J.append(E("B-COOL", dict(p, cooldown=cd), parent=fn, note=f"S4 {fn} cooldown{cd}", stage="S4"))
    return J


STAGES = {"s1": s1, "s2": s2, "s3": s3, "s4": s4}

if __name__ == "__main__":
    st = sys.argv[1]
    BL.init_b()
    J = STAGES[st]()
    ids = [e["config_id"] for e in J]
    assert len(ids) == len(set(ids))
    print(st, len(J), "configs,", L.register(J), "new", flush=True)
    run_seq(J, f"B-{st}")
    print("DONE", st, flush=True)
