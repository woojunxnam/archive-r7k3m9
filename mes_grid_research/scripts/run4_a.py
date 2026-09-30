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


WAVES = {"wave1": wave1}

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
