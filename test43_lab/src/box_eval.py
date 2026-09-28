"""Standalone evaluation of a box trading configuration (TEST71+): economics, matched excess, folds, friction, stress, plateau, gate."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402

_BX = {}


def boxes(I, geo, spec, builder=None):
    key = (I.name, geo)
    if key not in _BX:
        Bx = (builder or B.build)(I, geo, spec)
        _BX[key] = Bx.sort_values(["s", "birth"]).reset_index(drop=True) if len(Bx) else Bx
    return _BX[key]


def run(I, Bx, LZ=0.15, UZ=0.85, buf=0.0, cycles=1, delay=0, miss_e=0.0, miss_x=0.0, mode=0, seed=5):
    rng = np.random.default_rng(seed); n = len(Bx)
    me = (rng.random(n) < miss_e).astype(np.int64); mx = (rng.random(n) < miss_x).astype(np.int64)
    a = lambda c, t=np.int64: Bx[c].values.astype(t)
    return B.sim_boxes(I.C, I.FP, I.FPb, a("s"), a("birth"), a("death"), a("lo", float), a("hi", float), LZ, UZ, buf, cycles, delay, me, mx, B.J15, mode)


def evaluate(I, Bx, name, params, plateau=()):
    """params: kwargs for run(); plateau: list of (label, Bx_neighbour, params_neighbour)."""
    full = I.full; nd = int(full.sum()); sess = I.sess
    D, d = B.ledger_eval(I, run(I, Bx, **params))
    o = {"config": name, "instrument": I.name, **{k: v for k, v in params.items()}}
    if not len(D):
        return {**o, "trades": 0, "PASS": False}, D, d
    r = B.risk(d[full]); x = np.zeros(I.n); np.add.at(x, D.s.values, D.excess.values)
    folds = {}
    for nm, a_, b_ in B.FOLDS:
        mm = np.asarray((sess >= a_) & (sess <= b_)); tm = mm[D.s.values]
        folds[f"fold_net_{nm}"] = float(d[mm].mean()); folds[f"fold_x_{nm}"] = float(x[mm].mean()); folds[f"fold_n_{nm}"] = int(tm.sum())
    act = d[full & (d != 0)]; top = np.sort(act)[::-1]
    life_h = float((Bx.death - Bx.birth).sum() / 60)
    d4 = B.ledger_eval(I, run(I, Bx, **params), cs=I.cs4)[1]
    dl = B.ledger_eval(I, run(I, Bx, **{**params, "delay": params.get("delay", 0) + 1}))[1]
    dme = B.ledger_eval(I, run(I, Bx, **{**params, "miss_e": 0.2}))[1]
    dmx = B.ledger_eval(I, run(I, Bx, **{**params, "miss_x": 0.2}))[1] if params.get("mode", 0) == 0 else d
    o.update({"trades": len(D), "trades_per_day": len(D) / nd, "contract_sides_per_day": 2 * len(D) / nd, "cycles_per_day": float((D.reason == 1).sum() / nd),
              "gross_day": float(D.gross.sum() / nd), "commission_day": 2 * 0.62 * len(D) / nd, "slippage_day": 2 * (I.cs - 0.62) * len(D) / nd,
              "friction_over_gross": float(2 * I.cs * len(D) / max(abs(D.gross.sum()), 1e-9)),
              "avg_day": r["avg_day"], "max_dd": r["max_dd"], "worst_day": r["worst_day"], "ret_dd": r["ret_dd"], "excess_day": float(x[full].mean()),
              "win_rate": float((D.net > 0).mean()), "p_top": float((D.reason == 1).mean()), "p_break": float((D.reason == 2).mean()),
              "usd_per_completed_cycle": float(D.net[D.reason == 1].mean()) if (D.reason == 1).any() else np.nan, "usd_per_bottom_touch": float(D.net.mean()),
              "usd_per_contract_side": float(D.net.sum() / (2 * len(D))), "usd_per_active_box_hour": float(D.net.sum() / max(life_h, 1e-9)),
              **folds, "folds_net_pos": int(sum(folds[f"fold_net_{nm}"] > 0 for nm, _, _ in B.FOLDS)),
              "folds_x_pos": int(sum(folds[f"fold_x_{nm}"] > 0 for nm, _, _ in B.FOLDS)), "min_fold_n": int(min(folds[f"fold_n_{nm}"] for nm, _, _ in B.FOLDS)),
              "remove_top3": float(act.sum() - top[:3].sum()), "slip4_day": float(d4[full].mean()), "delay1_day": float(dl[full].mean()),
              "miss20_entry_day": float(dme[full].mean()), "miss20_exit_day": float(dmx[full].mean()),
              "pre2023_day": float(d[full & np.asarray(sess < "2023-01-01")].mean()), "from2023_day": float(d[full & np.asarray(sess >= "2023-01-01")].mean())})
    base = float(d[full].sum()); pl = []
    for lab, Bn, pn in plateau:
        Dn, dn = B.ledger_eval(I, run(I, Bn, **pn))
        pl.append((lab, float(dn[full].sum()), float(Dn.excess.sum()) if len(Dn) else 0.0))
    o["plateau"] = str([(l_, round(t_), round(x_)) for l_, t_, x_ in pl])
    o["plateau_pass"] = bool(len(pl) > 0 and all(t_ > 0 and t_ >= 0.6 * base for _, t_, _ in pl) and np.mean([x_ > 0 for _, _, x_ in pl]) >= 0.75)
    g = {"g_excess": o["excess_day"] > 0, "g_folds": o["folds_net_pos"] >= 4, "g_top3": o["remove_top3"] > 0, "g_slip4": o["slip4_day"] > 0,
         "g_plateau": o["plateau_pass"], "g_delay": o["delay1_day"] > 0, "g_miss": o["miss20_entry_day"] > 0 and o["miss20_exit_day"] > 0,
         "g_sample": o["trades"] >= 300 and o["min_fold_n"] >= 40}
    o.update(g); o["PASS"] = bool(all(g.values()))
    return o, D, d


def evaluate_fn(I, name, runner, params, plateau=(), mode=0, extra_boxes_hours=None):
    """generic: runner(params, cs_override=None) -> ledger array (s, j_in, j_x, px_in, px_x, reason, box, cycle)."""
    full = I.full; nd = int(full.sum()); sess = I.sess
    D, d = B.ledger_eval(I, runner(params))
    o = {"config": name, "instrument": I.name, **params}
    if not len(D):
        return {**o, "trades": 0, "PASS": False}, D, d
    r = B.risk(d[full]); x = np.zeros(I.n); np.add.at(x, D.s.values, D.excess.values)
    folds = {}
    for nm, a_, b_ in B.FOLDS:
        mm = np.asarray((sess >= a_) & (sess <= b_)); tm = mm[D.s.values]
        folds[f"fold_net_{nm}"] = float(d[mm].mean()); folds[f"fold_x_{nm}"] = float(x[mm].mean()); folds[f"fold_n_{nm}"] = int(tm.sum())
    act = d[full & (d != 0)]; top = np.sort(act)[::-1]
    d4 = B.ledger_eval(I, runner(params), cs=I.cs4)[1]
    dl = B.ledger_eval(I, runner({**params, "delay": params.get("delay", 0) + 1}))[1]
    dm = B.ledger_eval(I, runner({**params, "miss": 0.2}))[1]
    dmig = B.ledger_eval(I, runner({**params, "mig_delay": 1}))[1] if "mig_delay" in params else d
    o.update({"trades": len(D), "trades_per_day": len(D) / nd, "contract_sides_per_day": 2 * len(D) / nd, "cycles_per_day": float((D.reason == 1).sum() / nd),
              "gross_day": float(D.gross.sum() / nd), "commission_day": 2 * 0.62 * len(D) / nd, "slippage_day": 2 * (I.cs - 0.62) * len(D) / nd,
              "friction_over_gross": float(2 * I.cs * len(D) / max(abs(D.gross.sum()), 1e-9)), "avg_day": r["avg_day"], "max_dd": r["max_dd"],
              "worst_day": r["worst_day"], "ret_dd": r["ret_dd"], "excess_day": float(x[full].mean()), "win_rate": float((D.net > 0).mean()),
              "p_top": float((D.reason == 1).mean()), "p_break": float((D.reason == 2).mean()), "p_eod": float((D.reason == 3).mean()),
              "usd_per_trade": float(D.net.mean()), "usd_per_contract_side": float(D.net.sum() / (2 * len(D))), "avg_hold_min": float((D.j_x - D.j_in).mean()),
              **folds, "folds_net_pos": int(sum(folds[f"fold_net_{nm}"] > 0 for nm, _, _ in B.FOLDS)),
              "folds_x_pos": int(sum(folds[f"fold_x_{nm}"] > 0 for nm, _, _ in B.FOLDS)), "min_fold_n": int(min(folds[f"fold_n_{nm}"] for nm, _, _ in B.FOLDS)),
              "remove_top3": float(act.sum() - top[:3].sum()), "slip4_day": float(d4[full].mean()), "delay1_day": float(dl[full].mean()),
              "miss20_entry_day": float(dm[full].mean()), "mig_delay1_day": float(dmig[full].mean()),
              "pre2023_day": float(d[full & np.asarray(sess < "2023-01-01")].mean()), "from2023_day": float(d[full & np.asarray(sess >= "2023-01-01")].mean())})
    base = float(d[full].sum()); pl = []
    for lab, pn in plateau:
        Dn, dn = B.ledger_eval(I, runner(pn)); pl.append((lab, float(dn[full].sum()), float(Dn.excess.sum()) if len(Dn) else 0.0))
    o["plateau"] = str([(l_, round(t_), round(x_)) for l_, t_, x_ in pl])
    o["plateau_pass"] = bool(len(pl) > 0 and all(t_ > 0 and t_ >= 0.6 * base for _, t_, _ in pl) and np.mean([x_ > 0 for _, _, x_ in pl]) >= 0.75)
    g = {"g_excess": o["excess_day"] > 0, "g_folds": o["folds_net_pos"] >= 4, "g_top3": o["remove_top3"] > 0, "g_slip4": o["slip4_day"] > 0,
         "g_plateau": o["plateau_pass"], "g_delay": o["delay1_day"] > 0 and o["mig_delay1_day"] > 0, "g_miss": o["miss20_entry_day"] > 0,
         "g_sample": o["trades"] >= 300 and o["min_fold_n"] >= 40}
    o.update(g); o["PASS"] = bool(all(g.values()))
    return o, D, d
