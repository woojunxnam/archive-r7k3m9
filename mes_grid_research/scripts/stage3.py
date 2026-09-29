"""FACTORY_S3: local robustness (adjacent coarse / ~±10% / ~±20%) for Stage-2 survivors.
Survivor list and reasons are recorded in results/FACTORY_S3/stage2_candidates.csv."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
from factory_lib import run_batch, ROOT
from stage1 import R1, A24, A16, A16AL, S_BASIC, INF

T3 = ((8, 5.0), (16, 10.0), (24, 20.0))

CANDS = {  # name: (base cfg, reason)
    "N_cap16": (dict(cap_total=16), "exposure cap: DD -48%, best ret/DD 2.88"),
    "N_cap20": (dict(cap_total=20), "exposure cap: DD -36%, ret/DD 2.67"),
    "N_cap24": (dict(cap_total=24), "exposure cap: DD -23%"),
    "Q_16_16_rec_layer": (dict(A16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=5.0)), "recovery mode: DD -52%, min equity 88k"),
    "Q_24_8_rec_confirm": (dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=5.0, confirm="vwap")), "recovery+confirm: DD -44%, w2223 -76k"),
    "Q_24_8_rec_layer": (dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=5.0)), "recovery layer exit: DD -39%"),
    "I_S6_recovexit": (dict(state=dict(S_BASIC, recovery_exit="all_ind", rec_exit_x=5.0)), "state machine + recovery layer exit: DD -36%"),
    "C_tiersT3": (dict(spacing="tiers", tiers=T3), "tiered spacing + stop at 24 (== I_S2): DD -26%, no >24"),
    "I_S1": (dict(state=S_BASIC), "state machine inventory tiers: DD -25%"),
    "I_S5_rec": (dict(core_cap=24, rec_cap=8, **dict(R1, rec_activation="state"),
                      state=dict(S_BASIC, rec_tp={"ELEVATED": 4.0, "HIGH": 3.0, "CRITICAL": 2.5})), "state + recycle: DD -23%, trades 4.3/day"),
    "D_16_16al_low60_float": (dict(A16AL, rec_anchor="low60", rec_spacing="float"), "floating recycle near market: DD -18%, lock 59d, min eq 76k"),
    "C_atr1.5": (dict(spacing="atr", atr_k=1.5), "slow core ATR spacing: DD -21%, underwater 463d"),
    "C_fixed15.0": (dict(grid=15.0), "slow core fixed: DD -12%, underwater 463d"),
    "C_convex0.2": (dict(spacing="convex", convex_a=0.2), "slow core convex: DD -12%"),
    "C_volpct2.0": (dict(spacing="volpct", volpct_k=2.0), "vol-scaled spacing: min eq 49k, w2020 -134k"),
    "M_atr_spike1.5_core": (dict(gov="atr_spike", gov_x=1.5, gov_action="core"), "governor: 2020 DD -65k (vs -164k), min eq 108k"),
    "J_age15_recovery": (dict(state=dict(t=(1, 33, 33), age=15.0, mult=(1, 1, 1, INF), recovery_exit="all_ind", rec_exit_x=5.0, recovery_until=1)),
                         "cycle age recovery: 2022-23 DD -71k (vs -155k), lock 101d"),
    "L_armed_ll_fail": (dict(add_trigger="armed", reversal="ll_fail"), "smart add: +$51k P&L at equal DD"),
    "L_armed_bull_hc": (dict(add_trigger="armed", reversal="bull_hc"), "smart add: +$54k P&L at equal DD"),
    "P_eth_gapdown_init": (dict(eth="gapdown_init", eth_k=0.5), "ETH gap-down init: underwater 289d (suspected path luck)"),
    "C_tiersT3_E8": (dict(spacing="tiers", tiers=T3, core_cap=24, emerg_cap=8, emerg_step=40.0, emerg_tp=15.0), "tiers + emergency reserve"),
    "B_16_16_newlow0_hi": (dict(A16, rec_roll="newlow", rec_roll_x=0.0), "rolling recycle: 32-lock 4d, min eq 67k (economics worse)"),
}


def perturb():
    """(name, family, module, control, cfg)"""
    out = []
    def add(base, tag, cfg):
        out.append((f"{base}__{tag}", "S3", base, base, cfg, {}, False))
    for cap in (13, 14, 18, 19):
        add("N_cap16", f"cap{cap}", dict(cap_total=cap))
    for cap in (16, 18, 22, 24):
        add("N_cap20", f"cap{cap}", dict(cap_total=cap))
    for cap in (19, 22, 26, 29):
        add("N_cap24", f"cap{cap}", dict(cap_total=cap))
    for x in (4.0, 4.5, 5.5, 6.0):
        add("Q_16_16_rec_layer", f"lx{x}", dict(A16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=x)))
    for cc, rc in ((13, 16), (14, 16), (18, 14), (19, 13)):
        add("Q_16_16_rec_layer", f"core{cc}", dict(A16, core_cap=cc, rec_cap=rc, recovery=dict(h=cc, rec_tp=2.0, rec_step=10.0, layer_x=5.0)))
    for x in (4.0, 4.5, 5.5, 6.0):
        add("Q_24_8_rec_confirm", f"lx{x}", dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=x, confirm="vwap")))
    for h in (19, 22, 26):
        add("Q_24_8_rec_confirm", f"h{h}", dict(A24, core_cap=min(h, 24), recovery=dict(h=h, rec_tp=2.0, rec_step=10.0, layer_x=5.0, confirm="vwap")))
    for x in (4.0, 4.5, 5.5, 6.0):
        add("I_S6_recovexit", f"x{x}", dict(state=dict(S_BASIC, recovery_exit="all_ind", rec_exit_x=x)))
    for sc in (0.8, 0.9, 1.1, 1.2):
        add("I_S6_recovexit", f"t{sc}", dict(state=dict(S_BASIC, t=tuple(round(v * sc) for v in (8, 16, 24)), recovery_exit="all_ind", rec_exit_x=5.0)))
    for sc in (0.8, 0.9, 1.1, 1.2):
        add("C_tiersT3", f"step{sc}", dict(spacing="tiers", tiers=tuple((u, s * sc) for u, s in T3)))
    for top in (20, 22, 26, 28):
        add("C_tiersT3", f"top{top}", dict(spacing="tiers", tiers=((8, 5.0), (16, 10.0), (top, 20.0))))
    for sc in (0.8, 0.9, 1.1, 1.2):
        add("I_S1", f"mult{sc}", dict(state=dict(S_BASIC, mult=(1.0, 1.5 * sc, 3.0 * sc, INF))))
        add("I_S5_rec", f"t{sc}", dict(core_cap=24, rec_cap=8, **dict(R1, rec_activation="state"),
                                        state=dict(S_BASIC, t=tuple(round(v * sc) for v in (8, 16, 24)), rec_tp={"ELEVATED": 4.0, "HIGH": 3.0, "CRITICAL": 2.5})))
    for st in (4.0, 4.5, 5.5, 6.0):
        add("D_16_16al_low60_float", f"step{st}", dict(A16AL, rec_anchor="low60", rec_spacing="float", rec_step=st))
    for tp in (2.5, 3.5):
        add("D_16_16al_low60_float", f"tp{tp}", dict(A16AL, rec_anchor="low60", rec_spacing="float", rec_tp=tp))
    add("D_16_16al_low60_float", "low30", dict(A16AL, rec_anchor="low30", rec_spacing="float"))
    add("D_16_16al_low60_float", "20_12", dict(core_cap=20, rec_cap=12, **dict(R1, rec_activation="always", rec_anchor="low60", rec_spacing="float")))
    for k_ in (1.2, 1.35, 1.65, 1.8):
        add("C_atr1.5", f"k{k_}", dict(spacing="atr", atr_k=k_))
    for g in (12.0, 13.5, 16.5, 18.0):
        add("C_fixed15.0", f"g{g}", dict(grid=g))
    for a in (0.16, 0.18, 0.22, 0.24):
        add("C_convex0.2", f"a{a}", dict(spacing="convex", convex_a=a))
    for k_ in (1.6, 1.8, 2.2, 2.4):
        add("C_volpct2.0", f"k{k_}", dict(spacing="volpct", volpct_k=k_))
    for x in (1.2, 1.35, 1.65, 1.8):
        add("M_atr_spike1.5_core", f"x{x}", dict(gov="atr_spike", gov_x=x, gov_action="core"))
    for a in (12.0, 13.5, 16.5, 18.0):
        add("J_age15_recovery", f"age{a}", dict(state=dict(t=(1, 33, 33), age=a, mult=(1, 1, 1, INF), recovery_exit="all_ind", rec_exit_x=5.0, recovery_until=1)))
    for x in (4.0, 6.0):
        add("J_age15_recovery", f"x{x}", dict(state=dict(t=(1, 33, 33), age=15.0, mult=(1, 1, 1, INF), recovery_exit="all_ind", rec_exit_x=x, recovery_until=1)))
    for g in (4.0, 4.5, 5.5, 6.0):
        add("L_armed_ll_fail", f"g{g}", dict(add_trigger="armed", reversal="ll_fail", grid=g))
        add("L_armed_bull_hc", f"g{g}", dict(add_trigger="armed", reversal="bull_hc", grid=g))
    for k_ in (0.25, 0.4, 0.6, 0.75):
        add("P_eth_gapdown_init", f"k{k_}", dict(eth="gapdown_init", eth_k=k_))
    for es in (32.0, 36.0, 44.0, 48.0):
        add("C_tiersT3_E8", f"es{es}", dict(spacing="tiers", tiers=T3, core_cap=24, emerg_cap=8, emerg_step=es, emerg_tp=15.0))
    for st in (4.0, 6.0):
        add("B_16_16_newlow0_hi", f"step{st}", dict(A16, rec_roll="newlow", rec_roll_x=0.0, rec_step=st))
    return out


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "results", "FACTORY_S3"), exist_ok=True)
    pd.DataFrame([dict(name=k, cfg=str(v[0]), reason=v[1]) for k, v in CANDS.items()]).to_csv(
        os.path.join(ROOT, "results", "FACTORY_S3", "stage2_candidates.csv"), index=False)
    js = perturb()
    print(len(js), "robustness configs")
    run_batch(sys.argv[1] if len(sys.argv) > 1 else "FACTORY_S3", js, procs=4)
