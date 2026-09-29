"""P0B common engine audit (prereg 8293ba9)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import rp_state as R  # noqa: E402
import t104_levels as T4  # noqa: E402

OUT = os.path.join(R.OUT, "p0b"); os.makedirs(OUT, exist_ok=True)


def main():
    M = P.markets(); res = {}
    m = M["NQ"]; x = (m.c - m.vwap) / m.a[:, None]; pop = m.valid.copy()
    b_full = P.causal_bins(m, pop, x, 5)
    cut = np.asarray(m.I.sess <= pd.Timestamp("2024-12-31")); x2 = x.copy(); x2[~cut] = np.nan; p2 = pop.copy(); p2[~cut] = False
    b_cut = P.causal_bins(m, p2, x2, 5); res["1_causal_bins_prefix_mismatch"] = int((b_full[cut] != b_cut[cut]).sum())
    # 2 null membership: pool excludes events
    ev = (m.c > m.prevhi[12]) & m.valid; r = m.R["h12"]; nl, lv = P.cell_null(m, ev, pop, "h12", [b_full])
    pool = pop & ~ev & m.valid & ~np.isnan(r) & (b_full >= 0); res["2_pool_event_overlap"] = int((pool & ev).sum())
    res["2_null_on_nonevent_bars"] = int((~np.isnan(nl) & ~ev).sum()); res["2_fallback_shares"] = [float(np.mean(lv[ev & ~np.isnan(nl)] == i)) for i in range(3)]
    # 3 date key identical across instruments
    ds = {i: pd.Series(M[i].date[:, 0], index=M[i].I.sess) for i in P.INSTS}
    res["3_date_key_mismatch"] = int(sum((ds[i] != ds["ES"].reindex(ds[i].index)).sum() for i in P.INSTS))
    # 4 cost
    res["4_cost_maxdiff"] = float(max(np.nanmax(np.abs(M[i].cost - 2 * M[i].I.cs / (M[i].I.pv * M[i].a))) for i in P.INSTS))
    res["5_s21_mismatch"] = int(sum(((M[i].year >= 2021) != M[i].s21).sum() for i in P.INSTS))
    h24 = m.R["h24"]; fin = ~np.isnan(h24) & m.full[:, None]; res["6_h24_max_decision_bar"] = int(m.bidx[fin].max()); res["6_h12_finite_share_b_le_67"] = float(np.mean(~np.isnan(m.R["h12"][m.valid & (m.bidx <= 67)])))
    I = m.I; res["7_entry_mismatch"] = int(np.nansum(np.abs(m.entry[:, :80] - I.FP[:, 5 * np.arange(1, 81)]) > 0))
    ex = np.full(h24.shape, np.nan); jj = 5 * (np.arange(81) + 25); ok = jj <= P.E.J15; ex[:, ok] = I.FP[:, jj[ok]]
    res["8_h24_maxdiff"] = float(np.nanmax(np.abs(h24 - (ex - m.entry) / m.a[:, None])))
    Hd, Ld = np.nanmax(I.H, 1), np.nanmin(I.L, 1); Cc = I.C[:, P.E.J15]; pc = np.r_[np.nan, Cc[:-1]]
    tr = np.nanmax(np.stack([Hd - Ld, np.abs(Hd - pc), np.abs(Ld - pc)]), 0)
    a14 = pd.Series(tr).rolling(14).mean().shift(1).values; a14c = pd.Series(tr).rolling(14).mean().values; rg = pd.Series(Hd - Ld).rolling(14).mean().shift(1).values
    okk = ~np.isnan(a14) & (m.a > 0)
    res["9_atr_corr_prior_TR14"] = float(np.corrcoef(a14[okk], m.a[okk])[0, 1]); res["9_atr_corr_prior_range14"] = float(np.corrcoef(rg[okk & ~np.isnan(rg)], m.a[okk & ~np.isnan(rg)])[0, 1])
    o2 = okk & ~np.isnan(a14c); res["9_atr_corr_INCLUDING_current_TR14"] = float(np.corrcoef(a14c[o2], m.a[o2])[0, 1])
    res["9_atr_uses_current_session"] = bool(res["9_atr_corr_INCLUDING_current_TR14"] > max(res["9_atr_corr_prior_TR14"], res["9_atr_corr_prior_range14"]) + 1e-6)
    res["10_nan_ohlc_in_full_sessions"] = int(sum(np.isnan(M[i].c[M[i].full]).sum() for i in P.INSTS)); res["10_nan_bars_by_bar_index_top"] = pd.Series(np.where(np.isnan(M["ES"].c) & M["ES"].full[:, None])[1]).value_counts().head(5).to_dict(); res["10_events_on_nan_bars"] = int(sum(((M[i].c > M[i].prevhi[12]) & M[i].valid & np.isnan(M[i].c)).sum() for i in P.INSTS))
    # 11 SWH60/SWL60 same-bar usage
    aff = {}
    for i in P.INSTS:
        mm = M[i]; Lv = T4.levels(mm); ev4, _ = T4.detect(mm, Lv)
        for nm, key in (("SWH60", "L1_SWH60"), ("SWL60", "L2_SWL60")):
            L = Lv[nm]; chg = np.concatenate([np.zeros((mm.n, 1), bool), L[:, 1:] != L[:, :-1]], 1) & ~np.isnan(L)
            # break / breakdown bar at which the level changed on the same bar
            c, pc_ = mm.c, np.concatenate([np.full((mm.n, 1), np.nan), mm.c[:, :-1]], 1); pL = np.concatenate([np.full((mm.n, 1), np.nan), L[:, :-1]], 1)
            cross = ((c > L) & (pc_ <= pL)) if nm == "SWH60" else ((c < L) & (pc_ >= pL))
            aff[f"{i}_{key}_cross_on_level_change_bar"] = int((cross & chg & (mm.bidx <= 60)).sum()); aff[f"{i}_{key}_events"] = int(ev4[key].sum())
        orh = np.full((mm.n, 81), np.nan); orh[:, 5:] = np.max(mm.h[:, :6], 1)[:, None]
        aff[f"{i}_ORH_cross_at_b5"] = int(((mm.c[:, 5] > orh[:, 5]) & (mm.c[:, 4] <= orh[:, 4])).sum())
    res["11_detector_notes"] = aff
    fails = [k for k in ("1_causal_bins_prefix_mismatch", "2_pool_event_overlap", "2_null_on_nonevent_bars", "3_date_key_mismatch", "5_s21_mismatch", "7_entry_mismatch") if res[k] != 0]
    if res["4_cost_maxdiff"] > 1e-12: fails.append("4")
    if res["6_h24_max_decision_bar"] > 55: fails.append("6")
    if res["8_h24_maxdiff"] > 1e-12: fails.append("8")
    if res["9_atr_uses_current_session"]: fails.append("9")
    res["SHARED_BUG_FAILS"] = fails; res["P0B_VERDICT"] = "PASS" if not fails else "FAIL"
    json.dump(res, open(os.path.join(OUT, "P0B_AUDIT.json"), "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
