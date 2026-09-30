"""RUN-4 Stage 6 driver. Usage:
  python scripts/run4_port.py series <mechanism.json>   # A-SERIES: chosen A mechanism at caps 6..24 (series saved)
  python scripts/run4_port.py ab <mechanism.json>       # A+B portfolios under global budgets G
mechanism.json: {"name": ..., "params": {FactoryStrategy kwargs WITHOUT core_cap/rec_cap/max_total/recovery.h},
                 "b": {"B7F": {...}, "B4F": {...}}}
ES-signal / MES-economics proxy backtest (in-sample, NOT OOS)."""
import os, sys, json, copy
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import run4_lib as L

SPLITS = {6: (3, 3), 8: (4, 4), 10: (5, 5), 12: (6, 6), 14: (8, 6), 16: (8, 8), 20: (10, 10), 24: (12, 12)}


def a_params(mech, cap):
    from run4_a_lib import FQ
    cc, rc = SPLITS[cap]
    extra = copy.deepcopy(mech["params"])
    return FQ(cc, rc, **extra)


def series_entries(mech, caps=tuple(SPLITS), with_bpause=False):
    J = []
    for cap in caps:
        p = a_params(mech, cap)
        J.append(L.make_entry("A", "A-SERIES", p, stage="S6", fresh=("2022-01-01",), extra={"save": True},
                              note=f"SERIES {mech['name']} cap{cap}"))
        if with_bpause and cap in (8, 12):
            q = dict(p, core_filter="bmom_ok30")
            J.append(L.make_entry("A", "A-SERIES", q, stage="S6", fresh=("2022-01-01",), extra={"save": True},
                                  note=f"SERIES {mech['name']} cap{cap} + core pause 30m after strong B momentum"))
    return J


def ab_entries(mech, sid):
    """sid: cap -> A-SERIES config_id (and ('pause', cap) -> id)."""
    J = []
    caps = sorted(c for c in sid if isinstance(c, int))
    B = mech["b"]
    books = {"B7F": [("B7F", 1.0)], "B7F+B4F": [("B7F", 0.5), ("B4F", 0.5)]}
    for G in (10, 12, 14, 16, 20, 24):
        for wA in (1.0, 0.75, 0.6, 0.5, 0.4, 0.25, 0.0):
            capA = max([c for c in caps if c <= wA * G + 1e-9], default=0) if wA > 0 else 0
            sizeB = G - capA
            for bk, parts in books.items():
                if wA == 1.0 and bk != "B7F":
                    continue
                bl = []
                for nm, frac in parts:
                    s = int(round(sizeB * frac))
                    if s > 0:
                        bl.append(dict(name=nm, params=B[nm], size=s))
                spec = dict(G=G, a_id=sid.get(capA) if capA else None, capA=capA, b=bl, alloc=f"{int(wA*100)}/{int(100-wA*100)}", book=bk)
                J.append(L.make_entry("AB", "AB-FIXED", spec, kind="portfolio", stage="S6", fresh=(),
                                      note=f"G{G} A{capA} B{sizeB} alloc {spec['alloc']} {bk}"))
    # risk-budget allocation: B size chosen so that B's standalone DD share ~ target (per-contract DD of B7F ~ $930)
    ddB1 = mech.get("ddB_per_contract", 930.0)
    ddA = mech.get("ddA_by_cap", {})
    for G in (12, 16, 20, 24):
        for share in (0.25, 0.5):
            best = None
            for capA in caps:
                if capA >= G or str(capA) not in ddA:
                    continue
                sB = G - capA
                shareB = sB * ddB1 / (sB * ddB1 + ddA[str(capA)])
                if best is None or abs(shareB - share) < best[0]:
                    best = (abs(shareB - share), capA, sB, shareB)
            if best:
                _, capA, sB, shB = best
                spec = dict(G=G, a_id=sid[capA], capA=capA, b=[dict(name="B7F", params=B["B7F"], size=sB)], alloc=f"riskB{int(share*100)}",
                            book="B7F", realized_risk_share_B=round(shB, 3))
                J.append(L.make_entry("AB", "AB-RISK", spec, kind="portfolio", stage="S6", fresh=(),
                                      note=f"G{G} risk-budget B~{int(share*100)}% -> A{capA} B{sB}"))
    # inventory interaction variants (G=16)
    for capA in (8, 12):
        if capA not in sid:
            continue
        sB = 16 - capA
        for rule in ("half_when_A_high", "skip_when_A_high"):
            spec = dict(G=16, a_id=sid[capA], capA=capA, b=[dict(name="B7F", params=B["B7F"], size=sB, rule=rule, thr=int(0.75 * capA))],
                        alloc=f"{capA}/{sB}", book="B7F", interaction=rule)
            J.append(L.make_entry("AB", "AB-INTER", spec, kind="portfolio", stage="S6", fresh=(), note=f"G16 A{capA} B{sB} {rule}"))
        if ("pause", capA) in sid:
            spec = dict(G=16, a_id=sid[("pause", capA)], capA=capA, b=[dict(name="B7F", params=B["B7F"], size=sB)], alloc=f"{capA}/{sB}",
                        book="B7F", interaction="A core pause 30m after strong B momentum")
            J.append(L.make_entry("AB", "AB-INTER", spec, kind="portfolio", stage="S6", fresh=(), note=f"G16 A{capA}(pause) B{sB}"))
    return J


if __name__ == "__main__":
    mode, mf = sys.argv[1], sys.argv[2]
    mech = json.load(open(mf))
    if mode == "series":
        from run4_a_lib import job_engine, init_a
        J = series_entries(mech, with_bpause=True)
        print(len(J), "series configs,", L.register(J), "new", flush=True)
        L.run_entries(J, job_engine, init_fn=init_a, nmax=3, start_workers=3, tag="A-SERIES", log=lambda m: print(m, flush=True))
        print("DONE series", flush=True)
    else:
        import run4_b_lib as BL
        from run4_ab import job_ab
        import run4_b
        BL.init_b()
        run4_b._variant_events()          # B4v_* / B7v_* variant events used by B finalists
        m = json.load(open(L.MANIFEST))["configs"]
        sid = {}
        for cid, e in m.items():
            if e["family"] == "A-SERIES" and e["note"].startswith(f"SERIES {mech['name']} cap"):
                cap = int(e["note"].split("cap")[1].split()[0])
                if "pause" in e["note"]:
                    sid[("pause", cap)] = cid
                else:
                    sid[cap] = cid
        J = ab_entries(mech, sid)
        seen, JJ = set(), []
        for e in J:
            if e["config_id"] not in seen:
                seen.add(e["config_id"]); JJ.append(e)
        print(len(JJ), "portfolio configs,", L.register(JJ), "new", flush=True)
        done = L.done_ids()
        for k, e in enumerate(JJ):
            if e["config_id"] in done:
                continue
            e2 = dict(e, extra={"save": True})
            cid, st, err = L._worker_wrap((job_ab, e2))
            if st == "FAILED":
                print("FAILED", cid, err[:400], flush=True)
        print("DONE ab", flush=True)
