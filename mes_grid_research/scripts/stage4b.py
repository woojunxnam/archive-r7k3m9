"""FACTORY_S4b: capacity-maintenance combos. Motivation (recorded before running): all DD-reducing modules in
S1-S4 stop entering for ~750 days in 2022-23; only always-active floating/rolling recycle keeps trading.
Test floating recycle (near-market, always active) + one core-side risk module at a time, then a few stacks."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from factory_lib import run_batch
from stage1 import R1, S_BASIC, INF

T3 = ((8, 5.0), (16, 10.0), (24, 20.0))
GOV = dict(gov="atr_spike", gov_x=1.5, gov_action="core")


def FL(cc, rc, anchor="low60", **kw):
    d = dict(R1, core_cap=cc, rec_cap=rc, rec_activation="always", rec_anchor=anchor, rec_spacing="float")
    d.update(kw)
    return d


def REC(h, lx=5.0):
    return dict(recovery=dict(h=h, rec_tp=2.0, rec_step=10.0, layer_x=lx))


def combos():
    c = []
    for cc, rc in ((12, 12), (12, 20), (16, 16), (20, 12), (24, 8)):
        c.append((f"Y_fl{cc}_{rc}_Q", "D_float|Q_recovery", FL(cc, rc, **REC(cc))))
    for an in ("low30", "vwap"):
        c.append((f"Y_fl16_16_{an}_Q", "D_float_anchor|Q_recovery", FL(16, 16, an, **REC(16))))
    c.append(("Y_fl16_16_Q_gov", "D_float|Q_recovery|M_gov", FL(16, 16, **REC(16), **GOV)))
    c.append(("Y_fl16_16_tiers", "D_float|C_tiers", FL(16, 16, spacing="tiers", tiers=((8, 5.0), (16, 10.0)))))
    c.append(("Y_fl16_16_S1", "D_float|I_S1", FL(16, 16, state=dict(t=(8, 12, 16), mult=(1.0, 1.5, 3.0, INF)))))
    c.append(("Y_fl16_16_cap24", "D_float|N_cap24", FL(16, 16, cap_total=24)))
    c.append(("Y_fl16_16_cap24_Q", "D_float|N_cap24|Q_recovery", FL(16, 16, cap_total=24, **REC(16))))
    c.append(("Y_fl16_16_cap24_Q_gov", "D_float|N_cap24|Q_recovery|M_gov", FL(16, 16, cap_total=24, **REC(16), **GOV)))
    c.append(("Y_fl16_16_Q_add", "D_float|Q_recovery|L_armed", FL(16, 16, **REC(16), add_trigger="armed", reversal="ll_fail")))
    c.append(("Y_fl16_16_Q_invtp", "D_float|Q_recovery|E_inv_tp", FL(16, 16, **REC(16), rec_tp_mode="inv")))
    c.append(("Y_fl16_16_Q_tp4", "D_float|Q_recovery|E_tp4", FL(16, 16, **REC(16), rec_tp=4.0)))
    c.append(("Y_fl16_16_Q_step7.5", "D_float|Q_recovery|rec_step", FL(16, 16, **REC(16), rec_step=7.5)))
    c.append(("Y_fl16_16_Q_roll", "D_float|Q_recovery|B_roll", FL(16, 16, **REC(16), rec_roll="newlow", rec_roll_x=0.0)))
    c.append(("Y_fl12_12_E8_Q", "D_float|H_emerg|Q_recovery", FL(12, 12, emerg_cap=8, emerg_step=80.0, emerg_tp=20.0, **REC(12))))
    return [(n, "Y", comp, "BASE", cfg, {}, True) for n, comp, cfg in c]


if __name__ == "__main__":
    js = combos()
    print(len(js))
    run_batch(sys.argv[1] if len(sys.argv) > 1 else "FACTORY_S4b", js, procs=4)
