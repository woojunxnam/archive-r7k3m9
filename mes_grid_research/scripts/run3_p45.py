"""RUN-3 Phase 4 (layer exits), Phase 5 (tail-risk), addendum J/L/N/S/T/X/AA (smart recycle) — single-module changes on frozen FQ."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from run3_lib import FQ, run_batch


def extra(b, F):
    from mesgrid.events import event_features
    X = event_features(b, F)
    W = X.idx.values
    n = len(b)

    def full(arr):
        a = np.zeros(n, bool); a[W] = np.asarray(arr, bool); return a
    comp = pd.DataFrame({
        "LOC": (X.rpos60 <= 0.05) | (X.rpos120 <= 0.05) | (X.vwap_dev_atr <= -1.5),
        "EXH": X.newlow_weak_close.astype(bool) | (X.consec_down >= 4),
        "REV": X.bull_engulf.astype(bool) | X.sweep_reclaim_sess.astype(bool),
        "TOD": X.tod.isin(["1000_1130", "1130_1330"]),
        "CTX": ~X.down_trend_persist.astype(bool)})
    sc = 100 * comp.mean(axis=1)
    return {"f_bs50": full(sc >= 50), "f_bs70": full(sc >= 70), "f_rpos1d_30": full(X.rpos1d <= 0.3),
            "f_rpos5d_50": full(X.rpos5d <= 0.5), "f_below_pdl": full(X.below_pdl.astype(bool)),
            "f_not_late": full(X.tod != "1500_1615"), "f_not_persist": full(~X.down_trend_persist.astype(bool)),
            "f_bull_engulf": full(X.bull_engulf.astype(bool)), "f_rpos60_05": full(X.rpos60 <= 0.05),
            "f_deep_or_multi": full((X.rpos1d <= 0.3) | X.below_pdl.astype(bool)),
            "f_core_deep": full((X.rpos5d <= 0.3) & (X.vwap_dev_atr <= -1.0)),
            "f_no_gapdown_shock": full(~((X.gap_atr < -0.5) & (X.sess_dd_atr > -99) & (b.minute[W] < 600)))}


CANDS = {"C32": FQ(16, 16, True), "C14": FQ(8, 6, True), "C10": FQ(5, 5, False)}


def jobs():
    J = []
    # ---- Phase 4: layer-exit forensics (C32, C14)
    for cn in ("C32", "C14"):
        base = CANDS[cn]
        J.append((f"P4_{cn}_A_tp", base, {}, True, None))
        J.append((f"P4_{cn}_B_last3", dict(base, rec_exit="last", rec_exit_x=3.0), {}, True, None))
        J.append((f"P4_{cn}_C_last2x3", dict(base, rec_exit="last2", rec_exit_x=3.0), {}, True, None))
        J.append((f"P4_{cn}_D_recprof3", dict(base, harvest="rec_prof", harvest_x=3.0), {}, True, None))
        J.append((f"P4_{cn}_E_allprof3", dict(base, harvest="all_prof", harvest_x=3.0), {}, True, None))
        J.append((f"P4_{cn}_E_allprof5", dict(base, harvest="all_prof", harvest_x=5.0), {}, True, None))
        J.append((f"P4_{cn}_F_partial3", dict(base, harvest="partial_high", harvest_x=3.0), {}, True, None))
    # ---- Phase 5: tail-risk policies (C32, C14, C10)
    for cn in ("C32", "C14", "C10"):
        base = CANDS[cn]
        for thr in (15000.0, 30000.0, 45000.0):
            for mode in ("all", "core", "core_harvest", "progressive"):
                J.append((f"P5_{cn}_{mode}_{int(thr/1000)}k", dict(base, acct_dd=dict(thr=thr, mode=mode)), {}, True, None))
        for Q in (7500.0, 10000.0, 12500.0):
            J.append((f"P5_{cn}_eqcap{int(Q)}", dict(base, eq_cap_Q=Q), {}, True, None))
    # ---- Smart recycle entry (J), cooldown (L), dynamic exit (N), inventory/DD state (S/T), core separation (AF)
    for cn in ("C32", "C14"):
        base = CANDS[cn]
        for f in ("f_bs50", "f_bs70", "f_rpos1d_30", "f_rpos5d_50", "f_below_pdl", "f_not_late", "f_not_persist", "f_bull_engulf",
                  "f_rpos60_05", "f_deep_or_multi"):
            J.append((f"J_{cn}_{f}", dict(base, rec_filter=f), {}, True, None))
        for cb in (1, 2, 3, 5):
            J.append((f"L_{cn}_cool{cb}", dict(base, rec_cooldown_bars=cb), {}, True, None))
        J.append((f"N_{cn}_tp_inv", dict(base, rec_tp_mode="inv"), {}, True, None))
        J.append((f"N_{cn}_tp_vol", dict(base, rec_tp_mode="vol"), {}, True, None))
        J.append((f"N_{cn}_tp_atr0.3", dict(base, rec_tp_mode="atr", rec_tp_atr_k=0.3), {}, True, None))
        J.append((f"N_{cn}_late_tp2", dict(base, late_rec_tp=2.0), {}, True, None))
        J.append((f"AF_{cn}_core_deep", dict(base, core_filter="f_core_deep"), {}, True, None))
        J.append((f"Y_{cn}_no_gapdown_core", dict(base, core_filter="f_no_gapdown_shock"), {}, True, None))
        J.append((f"AA_{cn}_gov_mom30", dict(base, gov="mom30", gov_x=1.5, gov_action="core"), {}, True, None))
        J.append((f"Z_{cn}_volcap", dict(base, vol_cap=True), {}, True, None))
    return J


if __name__ == "__main__":
    js = jobs(); print(len(js))
    run_batch("RUN3_P45", js, extra_feature_fn=extra)
