"""FACTORY_S4: selected interactions. Each combo lists its component single-module names for attribution."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from factory_lib import run_batch
from stage1 import R1, A24, A16, A16AL, S_BASIC, INF

T3 = ((8, 5.0), (16, 10.0), (24, 20.0))
GOV = dict(gov="atr_spike", gov_x=1.5, gov_action="core")
AGE = dict(t=(1, 33, 33), age=15.0, mult=(1, 1, 1, INF), recovery_exit="all_ind", rec_exit_x=5.0, recovery_until=1)
S6 = dict(S_BASIC, recovery_exit="all_ind", rec_exit_x=5.0)
S6AGE = dict(S6, age=15.0)
ADD = dict(add_trigger="armed", reversal="ll_fail")
FLOAT16 = dict(A16AL, rec_anchor="low60", rec_spacing="float")
QC24 = dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=5.0, confirm="vwap"))
Q16 = dict(A16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=5.0))


def combos():
    c = [
        ("X_gov+age", "M_atr_spike1.5_core|J_age15_recovery", dict(GOV, state=AGE)),
        ("X_gov+S6", "M_atr_spike1.5_core|I_S6_recovexit", dict(GOV, state=S6)),
        ("X_S6+age", "I_S6_recovexit|J_age15_recovery", dict(state=S6AGE)),
        ("X_cap20+add", "N_cap20|L_armed_ll_fail", dict(ADD, cap_total=20)),
        ("X_cap24+gov", "N_cap24|M_atr_spike1.5_core", dict(GOV, cap_total=24)),
        ("X_cap24+age", "N_cap24|J_age15_recovery", dict(cap_total=24, state=AGE)),
        ("X_cap20+gov", "N_cap20|M_atr_spike1.5_core", dict(GOV, cap_total=20)),
        ("X_tiers+float", "C_tiersT3|D_16_16al_low60_float", dict(core_cap=24, rec_cap=8, spacing="tiers", tiers=T3,
                                                                 **dict(R1, rec_activation="always", rec_anchor="low60", rec_spacing="float"))),
        ("X_tiers+add", "C_tiersT3|L_armed_ll_fail", dict(ADD, spacing="tiers", tiers=T3)),
        ("X_S1+gov", "I_S1|M_atr_spike1.5_core", dict(GOV, state=S_BASIC)),
        ("X_Q16+gov", "Q_16_16_rec_layer|M_atr_spike1.5_core", dict(Q16, **GOV)),
        ("X_QC24+gov", "Q_24_8_rec_confirm|M_atr_spike1.5_core", dict(QC24, **GOV)),
        ("X_Q16+add", "Q_16_16_rec_layer|L_armed_ll_fail", dict(Q16, **ADD)),
        ("X_float+Q", "D_16_16al_low60_float|Q_16_16_rec_layer", dict(FLOAT16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=5.0))),
        ("X_float+gov", "D_16_16al_low60_float|M_atr_spike1.5_core", dict(FLOAT16, **GOV)),
        ("X_atr+float", "C_atr1.5|D_16_16al_low60_float", dict(FLOAT16, spacing="atr", atr_k=1.5)),
        ("X_S6+add", "I_S6_recovexit|L_armed_ll_fail", dict(ADD, state=S6)),
        ("X_convex+roll", "C_convex0.2|B_16_16_newlow0_hi", dict(A16, spacing="convex", convex_a=0.2, rec_roll="newlow", rec_roll_x=0.0)),
        ("X_reserve+roll", "H_res8_E_step80|B_16_16_newlow0_hi", dict(core_cap=20, rec_cap=4, emerg_cap=8, emerg_step=80.0, emerg_tp=20.0,
                                                                      rec_roll="newlow", rec_roll_x=0.0, **R1)),
        ("X_float+invtp", "D_16_16al_low60_float|E_rec_tp_inv", dict(FLOAT16, rec_tp_mode="inv")),
        ("X_fixed10+add", "C_fixed10.0|L_armed_ll_fail", dict(ADD, grid=10.0)),
        ("X_S1+convex", "I_S1|C_convex0.1", dict(state=S_BASIC, spacing="convex", convex_a=0.1)),
        # small 3/4-way stacks (components already measured singly and in pairs above)
        ("X3_cap24+gov+age", "N_cap24|M_atr_spike1.5_core|J_age15_recovery", dict(GOV, cap_total=24, state=AGE)),
        ("X3_S6age+gov+add", "I_S6_recovexit|J_age15_recovery|M_atr_spike1.5_core|L_armed_ll_fail", dict(GOV, **ADD, state=S6AGE)),
        ("X3_QC24+gov+age", "Q_24_8_rec_confirm|M_atr_spike1.5_core|J_age15_recovery", dict(QC24, **GOV, state=AGE)),
        ("X3_cap20+gov+age+add", "N_cap20|M_atr_spike1.5_core|J_age15_recovery|L_armed_ll_fail", dict(GOV, **ADD, cap_total=20, state=AGE)),
        ("X3_Q16+gov+age", "Q_16_16_rec_layer|M_atr_spike1.5_core|J_age15_recovery", dict(Q16, **GOV, state=AGE)),
        ("X3_S6age+gov", "I_S6_recovexit|J_age15_recovery|M_atr_spike1.5_core", dict(GOV, state=S6AGE)),
    ]
    return [(n, "X", comp, "BASE", cfg, {}, True) for n, comp, cfg in c]


if __name__ == "__main__":
    js = combos()
    print(len(js), "interaction configs")
    run_batch(sys.argv[1] if len(sys.argv) > 1 else "FACTORY_S4", js, procs=4)
