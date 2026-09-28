"""TEST96 Track D4: C43 mechanism portability audit + Stage-A transfer (prereg 492152fd).
C43 = CHAMPION_CONTROL_V1 = TEST43-P P1_CLUSTER_EQUAL_RISK|CONSERVATIVE over 8 frozen V6 allocator sleeves (arch A / C / F).
Audit: mechanism logic (daily trend tier -> target exposure, buy-time window, overnight carry rule, VWAP-z dip / red trims, drawdown / day-stop
governors) is dimensionless EXCEPT dollar constants (dd1, dd2, dd3, dayStop, volBudget, volBudgetON) and contract caps (capRTH, capON).
Stage A: sleeve params unchanged except dollar constants x k and caps / k (rounded, >= 1), k = median $ATR(target micro) / median $ATR(source micro),
sessions < 2021-01-01; tick / point value / costs of MYM / M2K; margin = MES fraction of notional (assumption: YM / RTY micro margins are a similar
fraction of notional).  The C43 portfolio layer (cluster equal-risk scaling + governor) is NOT replicated: C43_MECH_<X> = sum of the 8 transferred
sleeves at their own sizing, reported per sleeve too.  Named C43_MECH_YM / C43_MECH_RTY (never C43)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
import t65_common as K  # noqa: E402
import t96_common as W  # noqa: E402
import t96_data as X  # noqa: E402
from t43 import bars as TB, features, sleeves as S, v6a, lab  # noqa: E402

DOLLAR = ("dd1", "dd2", "dd3", "dayStop", "volBudget", "volBudgetON")
CAPS = ("capRTH", "capON")
PROFX = {"YM": dict(pv=0.5, tick=1.0), "RTY": dict(pv=5.0, tick=0.1)}


def bars3(inst):
    p = os.path.join(W.OUT, f"{inst}_3m_bars.parquet")
    if os.path.exists(p):
        return pd.read_parquet(p)
    m1 = TB.normalise_1m(C45.load1m(inst)); b = TB.add_clock(TB.aggregate_3m(m1)); b = b[b.session_date <= C45.END].reset_index(drop=True)
    b.to_parquet(p); return b


def run(b, f, inst, prm):
    pr = {"pointValue": PROFX[inst]["pv"], "tickSize": PROFX[inst]["tick"], "commission": 0.62, "rollCost": 2 * (0.62 + 0.5), "mIntraFrac": 0.0642, "mOnFrac": 0.0917}
    pr.update(prm)
    res = v6a.run(b, f, v6a.make_params(**pr)); return lab.daily(b, res), res


def main():
    ctx = W.main_ctx(); Is = ctx["Is"]; main_d = ctx["main"]; cand = S.candidates(); pre = np.asarray(Is["ES"].sess < pd.Timestamp("2021-01-01")) & Is["ES"].full
    usd = {k: float(np.nanmedian(Is[k].atr[pre] * Is[k].pv)) for k in ("ES", "MNQ", "YM", "RTY")}
    rows = []; tot = {}
    for inst in ("YM", "RTY"):
        b = bars3(inst); f = features.build(b, PROFX[inst]["pv"]); I = Is[inst]; si = pd.Index(I.sess)
        const = np.zeros(I.n)                                        # constant 1-micro long RTH-open -> 16:15 (exposure-matched beta proxy)
        const[I.full] = np.nan_to_num((I.FPb[:, B.J15] - I.FP[:, 0]) * I.pv)[I.full]
        on = np.r_[0, (I.FP[1:, 0] - I.FPb[:-1, B.J15]) * I.pv]; const_on = np.where(I.full, np.nan_to_num(on), 0)
        tot[inst] = np.zeros(I.n)
        for cid in S.ELIGIBLE:
            c = cand[cid]; src = c["inst"]; k = usd[inst] / usd[src]; prm = dict(c["params"])
            for key in DOLLAR:
                if key in prm:
                    prm[key] = prm[key] * k
            for key in CAPS:
                if key in prm:
                    prm[key] = max(1, int(round(prm[key] / k)))
            d, res = run(b, f, inst, prm)
            d.index = pd.to_datetime(d.index); dd = d.pnl.reindex(I.sess).fillna(0).values.copy(); dd[~I.full] = 0; tot[inst] += dd
            ap = d.avg_pos.reindex(I.sess).fillna(0).values; ep = d.end_pos.reindex(I.sess).shift(1).fillna(0).values
            beta = ap * const + ep * const_on                               # exposure-matched long (RTH avg position + carried overnight position)
            r = B.risk(dd[I.full]); fd = {nm: float(dd[np.asarray((I.sess >= a_) & (I.sess <= b_))].mean()) for nm, a_, b_ in B.FOLDS}
            rows.append({"sleeve": f"C43_MECH_{inst}:{cid}", "k_$ATR": k, "avg_day": r["avg_day"], "avg_day_2021": float(dd[np.asarray(I.sess >= K.S21)].mean()),
                         "excess_vs_exposure_matched_long_day": float((dd - beta)[I.full].mean()), "max_dd": r["max_dd"], "worst": r["worst_day"],
                         "folds_pos": int(sum(v > 0 for v in fd.values())), "avg_pos": float(ap[I.full].mean()), "corr_to_main": float(np.corrcoef(dd[I.full], main_d[I.full])[0, 1])})
        x = tot[inst]; r = B.risk(x[I.full]); rc, rm = B.risk((main_d + x)[I.full]), B.risk(main_d[I.full])
        fd = {nm: float(x[np.asarray((I.sess >= a_) & (I.sess <= b_))].mean()) for nm, a_, b_ in B.FOLDS}
        act = x[I.full & (x != 0)]; top = np.sort(act)[::-1]
        rows.append({"sleeve": f"C43_MECH_{inst} (sum of 8)", "avg_day": r["avg_day"], "avg_day_2021": float(x[np.asarray(I.sess >= K.S21)].mean()),
                     "excess_vs_exposure_matched_long_day": float(sum(rr["excess_vs_exposure_matched_long_day"] for rr in rows if rr["sleeve"].startswith(f"C43_MECH_{inst}:"))),
                     "max_dd": r["max_dd"], "worst": r["worst_day"], "folds_pos": int(sum(v > 0 for v in fd.values())), "remove_top3": float(act.sum() - top[:3].sum()),
                     "corr_to_main": float(np.corrcoef(x[I.full], main_d[I.full])[0, 1]), "main_plus_ret_dd": rc["ret_dd"], "main_ret_dd": rm["ret_dd"],
                     "main_plus_maxdd": rc["max_dd"], "main_maxdd": rm["max_dd"]})
    R = pd.DataFrame(rows); R.to_csv(os.path.join(W.OUT, "PORT_C43.csv"), index=False); np.savez_compressed(os.path.join(W.OUT, "PORT_C43_daily.npz"), **tot)
    audit = ("Structural audit: C43 sleeves are regime-tiered long-exposure allocators on 3m bars (daily trend tier -> target fraction of a contract cap, "
             "buy window, overnight carry, VWAP-z trims, DD / day-stop governors).  Mechanism logic is portable; ES/NQ-specific constants = dollar "
             "governor levels and contract caps (normalised by $ATR ratio).  PASS rule for C43_PORTABLE: sum-of-sleeves net > 0, excess vs "
             "exposure-matched long > 0, >= 4/5 folds, remove-top3 > 0.")
    W.md("T96_D4_C43_PORTABILITY.md", "TEST96 D4 - C43 mechanism portability (Stage A normalised)", [audit, R])
    pd.set_option("display.width", 250); print(R.to_string())


if __name__ == "__main__":
    main()


REFERENCE_NOTE = """Reference (same excess measure on the ORIGINAL ES / MNQ sleeves, data <= 2026-05-27): excess vs exposure-matched long per sleeve
MNQ_arch_A_AGG_0 -36.0, MNQ_robust_A_MOD_2 -3.8, MNQ_r2_C_MOD_1 +1.6, MNQ_robust_C_CON_0 +4.5, ES_robust_A_MOD_1 +0.3, ES_r2_F_MOD_2 +1.7,
ES_r2_A_CON_1 +4.0, ES_robust_C_CON_4 -2.2 $/day -> C43's value at source is predominantly managed long exposure (beta + governors), not a
timing edge; its portable 'mechanism' is therefore mostly beta, which on YM / RTY adds correlated drawdown."""
