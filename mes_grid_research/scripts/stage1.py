"""FACTORY_S1: broad mechanism screen. Every config = control + ONE module change (attribution preserved).
Full period 2019-05..2026-05, EXEC-1.1 conservative, ROLL-1.0. Pre-registered list; do not edit after running."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from factory_lib import run_batch

INF = float("inf")
R1 = dict(rec_activation="core_full", rec_anchor="runhigh", rec_spacing="ladder", rec_step=5.0, rec_tp=3.0)
A24 = dict(core_cap=24, rec_cap=8, **R1)
A16 = dict(core_cap=16, rec_cap=16, **R1)
A16AL = dict(core_cap=16, rec_cap=16, **dict(R1, rec_activation="always"))
A20 = dict(core_cap=20, rec_cap=12, **R1)
S_BASIC = dict(t=(8, 16, 24), mult=(1.0, 1.5, 3.0, INF))


def J(name, fam, mod, ctrl, cfg, exec_kw=None, trades=False):
    return (name, fam, mod, ctrl, cfg, exec_kw or {}, trades)


def jobs():
    out = [J("BASE", "CTRL", "control", "BASE", {}, trades=True)]
    # ---- A architecture
    for cc, rc in ((28, 4), (24, 8), (20, 12), (16, 16)):
        out.append(J(f"A_{cc}_{rc}_cf", "A", "lanes_fixed_corefull", "BASE", dict(core_cap=cc, rec_cap=rc, **R1)))
        out.append(J(f"A_{cc}_{rc}_al", "A", "lanes_fixed_always", "BASE", dict(core_cap=cc, rec_cap=rc, **dict(R1, rec_activation="always"))))
    for cc, rc, ec in ((20, 4, 8), (16, 8, 8), (20, 8, 4), (24, 4, 4), (12, 12, 8)):
        out.append(J(f"A3_{cc}_{rc}_{ec}E", "A", "three_layer", "BASE",
                     dict(core_cap=cc, rec_cap=rc, emerg_cap=ec, emerg_step=20.0, emerg_tp=10.0, **R1)))
    for d in ("vol", "dd", "age"):
        out.append(J(f"A_dyn_{d}", "A", "dynamic_alloc", "BASE", dict(core_cap=28, rec_cap=12, dyn_alloc=d, **R1)))
    # ---- B rolling recycle (CR_002)
    for trig, xs in (("pts", (10, 20, 40)), ("atr", (1.0, 2.0, 4.0)), ("newlow", (0,)), ("reversal", (10,))):
        for x in xs:
            out.append(J(f"B_24_8_{trig}{x}_hi", "B", f"roll_{trig}", "A_24_8_cf", dict(A24, rec_roll=trig, rec_roll_x=float(x))))
    for trig, x in (("pts", 20), ("atr", 2.0), ("newlow", 0)):
        out.append(J(f"B_24_8_{trig}{x}_old", "B", "roll_select_oldest", "A_24_8_cf",
                     dict(A24, rec_roll=trig, rec_roll_x=float(x), rec_roll_select="oldest")))
    for trig, x in (("pts", 20), ("atr", 2.0), ("newlow", 0), ("pts", 40)):
        out.append(J(f"B_16_16_{trig}{x}_hi", "B", f"roll_{trig}", "A_16_16_cf", dict(A16, rec_roll=trig, rec_roll_x=float(x))))
    for trig, x in (("pts", 20), ("atr", 2.0)):
        out.append(J(f"B_16_16al_{trig}{x}_hi", "B", f"roll_{trig}", "A_16_16_al", dict(A16AL, rec_roll=trig, rec_roll_x=float(x))))
    out.append(J("B_20_12_pts20_hi", "B", "roll_pts", "A_20_12_cf", dict(A20, rec_roll="pts", rec_roll_x=20.0)))
    # ---- C slower core accumulation
    for g in (7.5, 10.0, 15.0):
        out.append(J(f"C_fixed{g}", "C", "spacing_fixed", "BASE", dict(grid=g)))
    for a in (0.05, 0.1, 0.2):
        out.append(J(f"C_convex{a}", "C", "spacing_convex", "BASE", dict(spacing="convex", convex_a=a)))
    tiers = {"T1": ((8, 5.0), (16, 7.5), (24, 10.0), (32, 15.0)), "T2": ((8, 5.0), (16, 10.0), (24, 20.0), (32, 40.0)),
             "T3": ((8, 5.0), (16, 10.0), (24, 20.0))}
    for k, t in tiers.items():
        out.append(J(f"C_tiers{k}", "C", "spacing_tiers", "BASE", dict(spacing="tiers", tiers=t)))
    out.append(J("C_tiersT3_E8", "C", "spacing_tiers_emerg", "BASE",
                 dict(spacing="tiers", tiers=tiers["T3"], core_cap=24, emerg_cap=8, emerg_step=40.0, emerg_tp=15.0)))
    for k_ in (0.5, 0.75, 1.0, 1.5):
        out.append(J(f"C_atr{k_}", "C", "spacing_atr15", "BASE", dict(spacing="atr", atr_k=k_)))
    for p in (0.001, 0.0015, 0.002, 0.003):
        out.append(J(f"C_pct{p}", "C", "spacing_pct", "BASE", dict(spacing="pct", pct=p)))
    for D in (10000.0, 25000.0, 50000.0):
        out.append(J(f"C_dd{int(D)}", "C", "spacing_dd", "BASE", dict(spacing="dd", dd_D=D)))
    for k_ in (1.0, 2.0):
        out.append(J(f"C_volpct{k_}", "C", "spacing_volpct", "BASE", dict(spacing="volpct", volpct_k=k_)))
    for A in (3.0, 10.0, 30.0):
        out.append(J(f"C_age{A}", "C", "spacing_age", "BASE", dict(spacing="age", age_A=A)))
    # ---- D floating / dynamic recycle
    for an in ("runhigh", "low30", "low60", "vwap", "range", "swing"):
        for sp in ("ladder", "float"):
            if an == "runhigh" and sp == "ladder":
                continue
            out.append(J(f"D_24_8_{an}_{sp}", "D", f"rec_anchor_{an}_{sp}", "A_24_8_cf", dict(A24, rec_anchor=an, rec_spacing=sp)))
    for an in ("runhigh", "low60", "vwap"):
        out.append(J(f"D_16_16al_{an}_float", "D", f"rec_anchor_{an}_float", "A_16_16_al", dict(A16AL, rec_anchor=an, rec_spacing="float")))
    # ---- E recycle TP
    for tp in (2.0, 2.5, 4.0, 5.0, 7.5):
        out.append(J(f"E_24_8_tp{tp}", "E", "rec_tp_pts", "A_24_8_cf", dict(A24, rec_tp=tp)))
    for k_ in (0.2, 0.4):
        out.append(J(f"E_24_8_tpatr{k_}", "E", "rec_tp_atr", "A_24_8_cf", dict(A24, rec_tp_mode="atr", rec_tp_atr_k=k_)))
    for md in ("inv", "age", "vol"):
        out.append(J(f"E_24_8_tp_{md}", "E", f"rec_tp_{md}", "A_24_8_cf", dict(A24, rec_tp_mode=md)))
    out.append(J("E_16_16_tp_inv", "E", "rec_tp_inv", "A_16_16_cf", dict(A16, rec_tp_mode="inv")))
    out.append(J("E_16_16_tp2.0", "E", "rec_tp_pts", "A_16_16_cf", dict(A16, rec_tp=2.0)))
    # ---- F last-buy / layer exits
    for md, xs in (("last", (3, 5, 10)), ("last2", (5, 10)), ("last4", (5, 10)), ("all_ind", (5, 10, 15)),
                   ("newest_prof", (5, 10)), ("deepest_prof", (5, 10)), ("partial", (10,))):
        for x in xs:
            out.append(J(f"F_{md}{x}", "F", f"layer_{md}", "BASE", dict(layer_exit=md, layer_x=float(x))))
    # ---- G basket / hybrid exits
    for bt in (5.0, 10.0, 15.0, 20.0, 30.0):
        out.append(J(f"G_basket{bt}", "G", "basket_pts", "BASE", dict(basket_tp=bt)))
    for k_ in (0.25, 0.4, 0.6):
        out.append(J(f"G_basketdatr{k_}", "G", "basket_datr", "BASE", dict(basket_tp_mode="datr", basket_atr_k=k_)))
    out.append(J("G_scale_10_20_30", "G", "scale_out", "BASE", dict(scale_out=(10.0, 20.0, 30.0), basket_tp=30.0)))
    out.append(J("G_scale_5_15_25", "G", "scale_out", "BASE", dict(scale_out=(5.0, 15.0, 25.0))))
    out.append(J("G_reclaim_vwap", "G", "reclaim_exit", "BASE", dict(reclaim_exit="vwap", reclaim_min=5.0)))
    out.append(J("G_reclaim_prevclose", "G", "reclaim_exit", "BASE", dict(reclaim_exit="prev_close", reclaim_min=5.0)))
    out.append(J("G_invpartial16", "G", "inventory_partial_exit", "BASE", dict(layer_exit="newest_prof", layer_x=5.0, layer_min_qty=16)))
    # ---- H capacity management
    out.append(J("H_res4_E", "H", "reserve_emergency", "BASE", dict(core_cap=28, emerg_cap=4, emerg_step=20.0, emerg_tp=10.0)))
    out.append(J("H_res8_E", "H", "reserve_emergency", "BASE", dict(core_cap=24, emerg_cap=8, emerg_step=20.0, emerg_tp=10.0)))
    out.append(J("H_res8_E_step40", "H", "reserve_emergency", "BASE", dict(core_cap=24, emerg_cap=8, emerg_step=40.0, emerg_tp=15.0)))
    out.append(J("H_res8_E_step80", "H", "reserve_emergency", "BASE", dict(core_cap=24, emerg_cap=8, emerg_step=80.0, emerg_tp=20.0)))
    for d in ("vol", "dd", "age"):
        out.append(J(f"H_dyncap_{d}", "H", "dynamic_core_cap", "BASE", dict(dyn_alloc=d)))
    # ---- I state machine
    out.append(J("I_S1", "I", "state_inv", "BASE", dict(state=S_BASIC)))
    out.append(J("I_S2", "I", "state_inv_strong", "BASE", dict(state=dict(t=(8, 16, 24), mult=(1.0, 2.0, 4.0, INF)))))
    out.append(J("I_S3_dd", "I", "state_inv_dd", "BASE", dict(state=dict(S_BASIC, dd=50000.0))))
    out.append(J("I_S4_age", "I", "state_inv_age", "BASE", dict(state=dict(S_BASIC, age=20.0))))
    out.append(J("I_S5_rec", "I", "state_rec", "BASE", dict(core_cap=24, rec_cap=8, **dict(R1, rec_activation="state"),
                                                           state=dict(S_BASIC, rec_tp={"ELEVATED": 4.0, "HIGH": 3.0, "CRITICAL": 2.5}))))
    out.append(J("I_S6_recovexit", "I", "state_recovery_exit", "BASE", dict(state=dict(S_BASIC, recovery_exit="all_ind", rec_exit_x=5.0))))
    out.append(J("I_S7_rec_emerg", "I", "state_rec_emerg", "BASE",
                 dict(core_cap=20, rec_cap=8, emerg_cap=4, emerg_access="critical", **dict(R1, rec_activation="state"),
                      state=dict(S_BASIC, rec_tp={"ELEVATED": 4.0, "HIGH": 3.0, "CRITICAL": 2.5}))))
    # ---- J cycle age
    for A in (10.0, 20.0):
        out.append(J(f"J_age_coreoff{int(A)}", "J", "age_core_off", "BASE", dict(state=dict(t=(1, 33, 33), age=A, mult=(1, 1, 1, INF)))))
    out.append(J("J_age15_recovery", "J", "age_recovery", "BASE",
                 dict(state=dict(t=(1, 33, 33), age=15.0, mult=(1, 1, 1, INF), recovery_exit="all_ind", rec_exit_x=5.0, recovery_until=1))))
    # ---- K initial entry
    for k_ in (0.0, 0.25, 0.5, 1.0):
        out.append(J(f"K_vwap{k_}", "K", "init_vwap", "BASE", dict(init="vwap", init_k=k_)))
    for p in (0.1, 0.2, 0.3):
        out.append(J(f"K_range{p}", "K", "init_range", "BASE", dict(init="range", init_pct=p)))
    out.append(J("K_bb", "K", "init_bb", "BASE", dict(init="bb")))
    out.append(J("K_keltner", "K", "init_keltner", "BASE", dict(init="keltner")))
    for x in (10.0, 20.0):
        out.append(J(f"K_sessdd{int(x)}", "K", "init_sess_dd", "BASE", dict(init="sess_dd", init_x=x)))
        out.append(J(f"K_prevdd{int(x)}", "K", "init_prev_dd", "BASE", dict(init="prev_dd", init_x=x)))
    # ---- L add / reversal logic
    out.append(J("L_limit", "L", "add_limit_touch", "BASE", dict(add_trigger="limit")))
    for rv in ("bull_hc", "prev_high", "two_bar", "ll_fail", "wick", "upper_q", "rex"):
        out.append(J(f"L_armed_{rv}", "L", "add_armed_reversal", "BASE", dict(add_trigger="armed", reversal=rv)))
    for cb in (2, 3):
        out.append(J(f"L_cool{cb}bars", "L", "add_cooldown_bars", "BASE", dict(cooldown_bars=cb)))
    for cm in (15, 30):
        out.append(J(f"L_cool{cm}min", "L", "add_cooldown_time", "BASE", dict(cooldown_min=cm)))
    # ---- M freefall governor
    for g, x in (("atr_spike", 1.5), ("atr_spike", 2.0), ("atr_pct", 0.8), ("atr_pct", 0.9), ("vwap_dev", 2.0), ("vwap_dev", 3.0),
                 ("lower_lows", None), ("mom15", 1.5), ("mom30", 1.5), ("mom60", 2.0), ("range_exp", 3.0), ("rvol", 2.0)):
        out.append(J(f"M_{g}{x or ''}_core", "M", f"gov_{g}", "BASE", dict(gov=g, gov_x=x, gov_action="core")))
    for g, x in (("atr_spike", 1.5), ("vwap_dev", 2.0), ("mom30", 1.5), ("lower_lows", None)):
        out.append(J(f"M_{g}{x or ''}_all", "M", f"gov_{g}_all", "BASE", dict(gov=g, gov_x=x, gov_action="all")))
    for g, x in (("vwap_dev", 2.0), ("mom30", 1.5)):
        out.append(J(f"M_24_8_{g}{x}_coreonly", "M", f"gov_{g}_rec_continues", "A_24_8_cf", dict(A24, gov=g, gov_x=x, gov_action="core")))
    # ---- N exposure control
    for cap in (16, 20, 24, 28):
        out.append(J(f"N_cap{cap}", "N", "cap_fixed", "BASE", dict(cap_total=cap)))
    for Q in (5000.0, 7500.0):
        out.append(J(f"N_eqcap{int(Q)}", "N", "cap_equity", "BASE", dict(eq_cap_Q=Q)))
    for X in (25000.0, 50000.0):
        out.append(J(f"N_ddcap{int(X)}", "N", "cap_dd", "BASE", dict(dd_cap_X=X)))
    out.append(J("N_volcap", "N", "cap_vol", "BASE", dict(vol_cap=True)))
    for Lv in (3.0, 5.0):
        out.append(J(f"N_notional{Lv}", "N", "cap_notional_equity", "BASE", dict(notional_L=Lv)))
    # ---- O time of day
    for sf in (5, 15, 30):
        out.append(J(f"O_skip{sf}", "O", "skip_first", "BASE", dict(skip_first=sf)))
    out.append(J("O_lunch_core_off", "O", "lunch_core_off", "BASE", dict(lunch_core_off=True)))
    out.append(J("O_core_cutoff1500", "O", "core_cutoff", "BASE", dict(core_cutoff=15 * 60)))
    out.append(J("O_24_8_late_tp2", "O", "late_rec_tp", "A_24_8_cf", dict(A24, late_rec_tp=2.0)))
    # ---- P ETH context (labelled)
    out.append(J("P_eth_gapdown_init", "P", "eth_gapdown_init", "BASE", dict(eth="gapdown_init", eth_k=0.5)))
    out.append(J("P_eth_openloc_init", "P", "eth_openloc_init", "BASE", dict(eth="openloc_init")))
    out.append(J("P_eth_onret_pause", "P", "eth_onret_pause", "BASE", dict(eth="onret_pause", eth_k=0.25)))
    out.append(J("P_eth_below_onlow_adds", "P", "eth_below_onlow_adds", "BASE", dict(eth="below_onlow_adds")))
    # ---- Q recovery mode
    out.append(J("Q_24_8_rec", "Q", "recovery_core_off", "A_24_8_cf", dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0))))
    out.append(J("Q_24_8_rec_layer", "Q", "recovery_layer_exit", "A_24_8_cf", dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=5.0))))
    out.append(J("Q_24_8_rec_confirm", "Q", "recovery_confirm_vwap", "A_24_8_cf",
                 dict(A24, recovery=dict(h=24, rec_tp=2.0, rec_step=10.0, layer_x=5.0, confirm="vwap"))))
    out.append(J("Q_16_16_rec_layer", "Q", "recovery_layer_exit", "A_16_16_cf", dict(A16, recovery=dict(h=16, rec_tp=2.0, rec_step=10.0, layer_x=5.0))))
    # ---- R roll model
    out.append(J("R_roll2x", "R", "roll_slippage_2x", "BASE", {}, dict(roll_slippage_ticks=2.0)))
    out.append(J("R_close_reopen", "R", "roll_close_reopen_reporting", "BASE", {}, dict(roll_mode="close_reopen")))
    names = [j[0] for j in out]
    assert len(names) == len(set(names))
    return out


if __name__ == "__main__":
    js = jobs()
    print(len(js), "configs")
    if "--count" in sys.argv:
        sys.exit(0)
    df = run_batch(sys.argv[1] if len(sys.argv) > 1 else "FACTORY_S1", js, procs=4)
    print(df[["name", "total_mtm", "max_mtm_dd", "lock32_days", "share32", "trades_day"]].to_string())
