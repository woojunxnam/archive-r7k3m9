"""RUN-4 Sleeve A batches (FQ / mean-reversion / floating recycle). Usage: python scripts/run4_a.py <wave> [nmax]
Every config: full history 2019-05..2026-05 + fresh start 2022-01 (stage S1); survivors get all fresh starts later.
All results are ES-signal / MES-economics proxy backtests (in-sample; NOT OOS)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run4_lib as L
from run4_a_lib import FQ, job_engine, init_a

STRUCT = {12: [(6, 6), (4, 8), (8, 4)], 14: [(8, 6), (6, 8), (4, 10)], 16: [(8, 8), (6, 10), (10, 6)],
          18: [(8, 10), (10, 8), (6, 12)], 20: [(10, 10), (8, 12), (6, 14)], 24: [(12, 12), (8, 16), (10, 14)]}
HSTRUCT = [(8, 6), (8, 8), (10, 10)]
SV0 = dict(trig="free", k=0, select="closest_be", max_per_day=1)
REB = {"pts5": dict(rebound="pts", rb=5.0), "pts10": dict(rebound="pts", rb=10.0), "pts15": dict(rebound="pts", rb=15.0),
       "atr0.5": dict(rebound="atr", rb=0.5), "atr1": dict(rebound="atr", rb=1.0), "pivot": dict(rebound="pivot"),
       "mid30": dict(rebound="mid30"), "vwap": dict(rebound="vwap"), "rollhigh": dict(rebound="rollhigh")}


def E(family, params, parent=None, note="", **kw):
    return L.make_entry("A", family, params, parent=parent, note=note, **kw)


def wave1():
    J = []
    ctrl = {}
    # ---- A-STRUCT: caps x splits x entry (control grid; also the core/recycle separation baseline)
    for T, splits in STRUCT.items():
        for cc, rc in splits:
            for ent in ("lmt", "mkt"):
                p = FQ(cc, rc, lmt=(ent == "lmt"))
                e = E("A-STRUCT", p, note=f"cap{T} core{cc}/rec{rc} {ent}")
                J.append(e)
                ctrl[(cc, rc, ent)] = e["config_id"]
    for ent in ("lmt", "mkt"):
        e = E("A-STRUCT", FQ(16, 16, lmt=(ent == "lmt")), note=f"cap32 core16/rec16 {ent} (RUN-3 C32)")
        J.append(e); ctrl[(16, 16, ent)] = e["config_id"]
    # ---- A-SEP: core/recycle separation (wider/slower core)
    for cc, rc in [(6, 8), (6, 10), (8, 8), (4, 10), (8, 12)]:
        for grid in (5.0, 10.0, 20.0):
            for cool in (0, 120, 1440):
                if grid == 5.0 and cool == 0:
                    continue
                p = FQ(cc, rc, grid=grid, cooldown_min=cool)
                J.append(E("A-SEP", p, parent=ctrl.get((cc, rc, "lmt")), note=f"core{cc}/rec{rc} grid{grid} cool{cool}m"))
    # ---- A-HARV: conditional harvesting when capacity is scarce (recycle only; core harvest separately labelled)
    trigs = {"free3": dict(trig="free", k=3), "free2": dict(trig="free", k=2), "free1": dict(trig="free", k=1),
             "free0": dict(trig="free", k=0), "invhigh": dict(trig="inv", q=None), "dead50": dict(trig="dead", x=0.5)}
    for cc, rc in HSTRUCT:
        par = ctrl[(cc, rc, "lmt")]
        for tn, tg in trigs.items():
            for pol in ("newest_prof", "all_prof", "most_prof", "prof_be", "partial"):
                hc = dict(tg, policy=pol, hx=1.0, be=1.0)
                if tn == "invhigh":
                    hc["q"] = int(round(0.75 * (cc + rc)))
                J.append(E("A-HARV", FQ(cc, rc, harvest_cond=hc), parent=par, note=f"{tn} {pol} +1"))
        for tn in ("free1", "free2"):
            for pol in ("newest_prof", "all_prof"):
                J.append(E("A-HARV", FQ(cc, rc, harvest_cond=dict(trigs[tn], policy=pol, hx=2.0)), parent=par, note=f"{tn} {pol} +2"))
        for tn in ("free1", "invhigh"):
            hc = dict(trigs[tn], policy="all_prof", hx=1.0, core=True)
            if tn == "invhigh":
                hc["q"] = int(round(0.75 * (cc + rc)))
            J.append(E("A-HARV-CORE", FQ(cc, rc, harvest_cond=hc), parent=par, note=f"CORE-INCLUDED {tn} all_prof +1 (labelled)"))
    # ---- A-SALV: rebound salvage of DEAD recycle only after a rebound (never at lows)
    for cc, rc in HSTRUCT:
        par = ctrl[(cc, rc, "lmt")]
        for dd in (5.0, 20.0):
            for rn, rb in REB.items():
                J.append(E("A-SALV", FQ(cc, rc, dead_days=dd, salvage=dict(SV0, **rb)), parent=par, note=f"dead{dd:g}d {rn} closest_be"))
            for rn in ("pts10", "atr0.5", "vwap"):
                for sel in ("oldest", "highest"):
                    J.append(E("A-SALV", FQ(cc, rc, dead_days=dd, salvage=dict(SV0, select=sel, **REB[rn])), parent=par,
                               note=f"dead{dd:g}d {rn} {sel}"))
    for trig in (dict(trig="free", k=1), dict(trig="always")):
        for rn in ("pts10", "atr0.5"):
            J.append(E("A-SALV", FQ(8, 8, dead_days=5.0, salvage=dict(SV0, **trig, **REB[rn])), parent=ctrl[(8, 8, "lmt")],
                       note=f"dead5d {rn} closest_be trig={trig}"))
    # ---- A-CSM: capacity state machine (progressive responses, no immediate loss liquidation)
    sv = dict(SV0, **REB["pts10"])
    for cc, rc in HSTRUCT:
        par = ctrl[(cc, rc, "lmt")]
        for K in (1, 2, 3, 4):
            resp = {"R1_deep": dict(min_free=K, deep_mult=2.0),
                    "R2_deeplimit": dict(min_free=K, deep_off=2.0, ttl=30),
                    "R3_deep_harv": dict(min_free=K, deep_mult=2.0, harvest="newest_prof", hx=1.0, harvest_at=1),
                    "R4_deep_harv_salv": dict(min_free=K, deep_mult=2.0, harvest="newest_prof", hx=1.0, harvest_at=1, salvage=sv, salvage_at=0)}
            for rn, cs in resp.items():
                J.append(E("A-CSM", FQ(cc, rc, cap_sm=cs), parent=par, note=f"minfree{K} {rn}"))
        J.append(E("A-CSM", FQ(cc, rc, cap_sm=dict(min_free=1, harvest="newest_prof", hx=1.0, harvest_at=1, salvage=sv, salvage_at=0)),
                   parent=par, note="R5_harv_salv"))
    # ---- NULLS
    for c in (6, 8, 10, 12, 14, 16, 20, 24, 32):
        p = dict(core_cap=c, max_total=c, add_trigger="armed", reversal="ll_fail")
        J.append(E("A-NULL-A", p, note=f"NULL-A core only cap{c} (armed add, basket +25, grid 5)"))
    for cc, rc in [(8, 6), (8, 8), (10, 10), (16, 16)]:
        J.append(E("A-NULL-B", FQ(cc, rc, rec_anchor="none"), parent=ctrl[(cc, rc, "lmt")], note="NULL-B dumb floating recycle step5"))
    for cc, rc in [(8, 8), (16, 16)]:
        J.append(E("A-NULL-B", FQ(cc, rc, rec_anchor="none", rec_step=10.0), parent=ctrl[(cc, rc, "lmt")], note="NULL-B dumb floating recycle step10"))
    for s in range(1, 21):
        J.append(E("A-NULL-C", FQ(8, 8, rec_anchor="feat", rec_anchor_feat=f"rnd_s{s}"), parent=ctrl[(8, 8, "lmt")],
                   note=f"NULL-C random TOD-matched recycle timing seed {s}"))
    for s in range(1, 11):
        J.append(E("A-NULL-C", FQ(16, 16, rec_anchor="feat", rec_anchor_feat=f"rnd_s{s}"), parent=ctrl[(16, 16, "lmt")],
                   note=f"NULL-C random TOD-matched recycle timing seed {s}"))
    return J


def wave2():
    """A-SOFT: trap-risk dependent PRICE IMPROVEMENT (soft filter, not binary). Scores = causal walk-forward logistic
    percentiles (run4_trap.py); NaN before a prior-fold model exists -> normal entry. hold_20d score = negative control
    (anti-predictive out of sample)."""
    J = []
    base = {}
    for cc, rc in HSTRUCT:
        base[(cc, rc)] = L.make_entry("A", "A-STRUCT", FQ(cc, rc))["config_id"]
    offs = {"pts_0_.5_1_2": dict(offs=(0, 0.5, 1, 2), unit="pts"), "pts_0_1_2_3": dict(offs=(0, 1, 2, 3), unit="pts"),
            "pts_0_1_3_5": dict(offs=(0, 1, 3, 5), unit="pts"), "atr_0_.1_.25_.5": dict(offs=(0, 0.1, 0.25, 0.5), unit="atr")}
    for feat in ("trap_lr_hold_5d", "trap_lr_mae_2atr"):
        for on, od in offs.items():
            for skip in (False, True):
                for cc, rc in HSTRUCT:
                    rs = dict(feat=feat, cuts=(0.5, 0.8, 0.95), ttl=30, skip_top=skip, **od)
                    J.append(E("A-SOFT", FQ(cc, rc, rec_soft=rs), parent=base[(cc, rc)], note=f"{feat} {on} skip_top={skip}"))
    for on in ("pts_0_1_2_3", "pts_0_1_3_5"):
        rs = dict(feat="trap_lr_hold_20d", cuts=(0.5, 0.8, 0.95), ttl=30, skip_top=False, **offs[on])
        J.append(E("A-SOFT", FQ(8, 8, rec_soft=rs), parent=base[(8, 8)], note=f"NEGATIVE CONTROL trap_lr_hold_20d {on}"))
    # uniform price improvement (no score) as the score-free control
    for off in (0.5, 1.0, 2.0):
        for cc, rc in HSTRUCT:
            rs = dict(feat="trap_lr_hold_5d", cuts=(), offs=(off,), unit="pts", ttl=30)
            J.append(E("A-SOFT", FQ(cc, rc, rec_soft=rs), parent=base[(cc, rc)], note=f"UNIFORM limit offset {off} (score-free control)"))
    return J


def wave1b():
    """A-STATIC: core/recycle separation taken to its limit (motivated by NULL-D: exposure-matched passive long had
    ~FQ P&L with smaller DD). Core = passive static long (fill to q, never sell, rolled); recycle = FQ floating recycle
    (low60 anchor, limit entry, TP +3), no recovery mode. Nulls: static core alone (= passive long)."""
    J = []
    R = dict(rec_activation="always", rec_anchor="low60", rec_spacing="float", rec_step=5.0, rec_tp=3.0,
             rec_entry_mode="limit_close", shadow=True, core_mode="static")
    for q in (2, 4, 6, 8, 10, 12):
        J.append(E("A-STATIC-NULL", dict(core_mode="static", core_cap=q, max_total=q), note=f"passive static core {q} only"))
    for q in (4, 6, 8):
        for r in (6, 8, 10, 12, 16):
            if q + r > 24:
                continue
            J.append(E("A-STATIC", dict(R, core_cap=q, rec_cap=r, max_total=q + r), note=f"static core {q} + recycle {r}"))
    sv = dict(SV0, **REB["pts10"])
    for q, r in ((4, 10), (6, 8), (6, 10), (8, 8)):
        J.append(E("A-STATIC", dict(R, core_cap=q, rec_cap=r, max_total=q + r,
                                    cap_sm=dict(min_free=4, deep_mult=2.0, harvest="newest_prof", hx=1.0, harvest_at=1, salvage=sv, salvage_at=0)),
                   note=f"static core {q} + recycle {r} + CSM R4 minfree4"))
    for r in (8, 12, 16):
        J.append(E("A-STATIC", dict(R, core_cap=0, rec_cap=r, max_total=r), note=f"recycle only {r} (no core)"))
    return J


def _load_results():
    import pandas as pd
    d = L.collect("A")
    m = json.load(open(L.MANIFEST))["configs"]
    d["note"] = d.config_id.map(lambda c: m[c]["note"])
    d["pp"] = d.config_id.map(lambda c: m[c]["params"])
    d["parent"] = d.config_id.map(lambda c: m[c].get("parent"))
    d["stage"] = d.config_id.map(lambda c: m[c].get("stage"))
    return d


def select_survivors(d, n_max=16):
    """Stage-2 mechanism survivors (auto): recycle activity kept (fresh-2022 no-entry <= 30 d), P&L >= 70% of the
    parent control, ranked by worst fresh min equity; plus 4-axis Pareto members. Controls/nulls excluded."""
    import numpy as np
    from run4_analyze import pareto, A_AXES4
    base = d.set_index("config_id")
    cand = d[~d.family.isin(["A-STRUCT", "A-NULL-A", "A-NULL-B", "A-NULL-C", "A-SERIES"]) & (d.stage == "S1")].copy()
    cand["par_mtm"] = cand.parent.map(lambda p: base.loc[p, "total_mtm"] if isinstance(p, str) and p in base.index else np.nan)
    ok = cand[(cand.fs2022_no_entry_days <= 30) & (cand.total_mtm >= 0.7 * cand.par_mtm)]
    top = ok.sort_values("worst_fresh_min_equity", ascending=False).head(n_max)
    cand["p4"] = pareto(cand, A_AXES4)
    extra = cand[cand.p4 & ~cand.config_id.isin(top.config_id)].sort_values("worst_fresh_min_equity", ascending=False).head(6)
    return list(top.config_id) + list(extra.config_id)


def _perturb(p):
    """local neighbours (+/-20% numeric, +/-1 integer) of the RUN-4 module parameters of a config."""
    import copy
    out = []
    for key in ("cap_sm", "salvage", "harvest_cond", "rec_soft"):
        if not p.get(key):
            continue
        blk = p[key]
        for fld, val in list(blk.items()):
            if isinstance(val, bool) or fld in ("trig", "policy", "select", "rebound", "unit", "feat", "harvest"):
                continue
            if isinstance(val, dict):          # nested salvage inside cap_sm
                for f2, v2 in val.items():
                    if isinstance(v2, (int, float)) and not isinstance(v2, bool) and f2 in ("rb",):
                        for mlt in (0.8, 1.2):
                            q = copy.deepcopy(p); q[key][fld][f2] = round(v2 * mlt, 3); out.append((f"{key}.{fld}.{f2}x{mlt}", q))
                continue
            if isinstance(val, int) and fld in ("min_free", "k", "harvest_at", "salvage_at", "max_per_day", "ttl"):
                for dv in (-1, 1):
                    if val + dv >= 0:
                        q = copy.deepcopy(p); q[key][fld] = val + dv; out.append((f"{key}.{fld}{dv:+d}", q))
            elif isinstance(val, (int, float)) and fld in ("deep_mult", "deep_off", "rb", "hx", "be", "x"):
                for mlt in (0.8, 1.2):
                    q = copy.deepcopy(p); q[key][fld] = round(val * mlt, 3); out.append((f"{key}.{fld}x{mlt}", q))
    if p.get("salvage") or (p.get("cap_sm") or {}).get("salvage"):
        for mlt in (0.8, 1.2):
            q = copy.deepcopy(p); q["dead_days"] = round(p.get("dead_days", 5.0) * mlt, 3); out.append((f"dead_days x{mlt}", q))
    return out


def wave3():
    """Stage 2 (all fresh starts) + Stage 3 (local robustness) + Stage 5 (execution stress) for auto-selected survivors."""
    d = _load_results()
    surv = select_survivors(d)
    base = d.set_index("config_id")
    J = []
    for cid in surv:
        p = base.loc[cid, "pp"]
        fam = base.loc[cid, "family"]
        note = base.loc[cid, "note"]
        J.append(L.make_entry("A", fam, p, parent=cid, stage="S2", fresh=("2020-02-01", "2022-01-01", "2025-02-01"),
                              note=f"S2 all-fresh {note}"))
        for tag, q in _perturb(p):
            J.append(L.make_entry("A", fam, q, parent=cid, stage="S3", note=f"S3 {tag} of [{note}]"))
        for tag, ex in (("slip2", dict(slippage_ticks=2)), ("slip3", dict(slippage_ticks=3)), ("comm+50%", dict(commission_per_side=0.93)),
                        ("pen2", dict(penetration_ticks=2))):
            J.append(L.make_entry("A", fam, p, exec_kw=ex, parent=cid, stage="S5", note=f"S5 {tag} [{note}]"))
    # controls with all fresh starts + stress for comparison
    for cc, rc in [(8, 6), (8, 8), (10, 10), (16, 16), (6, 14)]:
        p = FQ(cc, rc)
        cid = L.make_entry("A", "A-STRUCT", p)["config_id"]
        J.append(L.make_entry("A", "A-STRUCT", p, parent=cid, stage="S2", fresh=("2020-02-01", "2022-01-01", "2025-02-01"),
                              note=f"S2 all-fresh control core{cc}/rec{rc} lmt"))
        for tag, ex in (("slip2", dict(slippage_ticks=2)), ("slip3", dict(slippage_ticks=3))):
            J.append(L.make_entry("A", "A-STRUCT", p, exec_kw=ex, parent=cid, stage="S5", note=f"S5 {tag} control core{cc}/rec{rc}"))
    seen, JJ = set(), []
    for e in J:
        if e["config_id"] not in seen:
            seen.add(e["config_id"]); JJ.append(e)
    return JJ


WAVES = {"wave1": wave1, "wave1b": wave1b, "wave2": wave2, "wave3": wave3}

if __name__ == "__main__":
    wave = sys.argv[1]
    nmax = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    J = WAVES[wave]()
    ids = [e["config_id"] for e in J]
    assert len(ids) == len(set(ids)), "duplicate configs"
    n_new = L.register(J)
    print(f"{wave}: {len(J)} configs ({n_new} newly registered)", flush=True)
    L.run_entries(J, job_engine, init_fn=init_a, nmax=nmax, start_workers=2, tag=f"A-{wave}",
                  log=lambda m: print(m, flush=True))
    print("DONE", wave, flush=True)
