"""TEST56 sparse state ladder / Beta-Carrier-V2 simple controls, as preregistered."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import hx_common as H  # noqa: E402
import hx_carrier as X  # noqa: E402
import prog_common as P  # noqa: E402
import t47_engine as E  # noqa: E402
from t53_run import module_trades, simulate  # noqa: E402

OUT = os.path.join(C45.ROOT, "out", "test56"); os.makedirs(OUT, exist_ok=True)


def growth_base(nq, sess, pM):
    p = os.path.join(C45.ROOT, "out", "test55", "T55_primary_daily.npz")
    if os.path.exists(p):
        z = np.load(p); return z["d"], z["cnt"]
    s21 = int(np.searchsorted(sess.values, np.datetime64("2021-01-01")))
    TR = module_trades(nq, sess)
    ca = np.maximum(0, 3 - np.nan_to_num(pM, nan=3.0)).astype(int)
    daily, L, cnt = simulate(nq, TR, 2, -1000.0, cap_arr=ca)
    tot = sum(daily.values()); tot[:s21] = 0; cnt[:s21] = 0
    np.savez_compressed(p, d=tot, cnt=cnt)
    return tot, cnt


def combo_margin(bk, pE, pM, extraN, res):
    lock = E.J1615 - 1
    qE = np.nan_to_num(pE[:, lock]) + res["qE"]; qN = np.nan_to_num(pM[:, lock]) + extraN[:, lock] + res["qN"]
    on = qE * bk.m_on["ES"] + qN * bk.m_on["MNQ"]
    qEi = np.nan_to_num(pE).max(1) + res["qE"]; qNi = (np.nan_to_num(pM) + extraN).max(1) + res["qN"]
    inn = qEi * bk.m_in["ES"] + qNi * bk.m_in["MNQ"]
    m = bk.sess >= H.START
    return float(on[m].max()), float(inn[m].max())


def main():
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}; bk = H.Book(mks)
    sess = es.pn.sess; full = sess >= H.START
    champ = C45.champion_daily().pnl.reindex(sess).fillna(0.0).values
    pE, pM = P.c43_positions(sess)
    g55, cnt55 = growth_base(nq, sess, pM)
    zero = np.zeros_like(cnt55)
    cands = []
    for u in (2, 3, 5, 8):
        cands.append((f"CONST_{u}", dict(tier_map=[u] * 4)))
    maps = {"L1": [0, 2, 5, 8], "L2_CONSERVATIVE": [0, 1, 3, 5], "L3_AGGRESSIVE": [1, 3, 8, 12], "L4_VERY_AGGRESSIVE": [2, 5, 12, 18]}
    for nm, mp in maps.items():
        for vt in (False, True):
            for gv in (None, (10000, 20000)):
                cands.append((f"{nm}|vt{int(vt)}|gov{int(gv is not None)}", dict(tier_map=mp, vol_target=vt, dd_gov=gv)))
    rows = []; keep = {}
    for nm, kw in cands:
        r = X.carrier(mks, bk, **kw)
        r4 = X.carrier(mks, bk, slip=4.0, **kw)
        dec = X.decompose(mks, bk, r, sess, full)
        keep[nm] = r["daily"]
        for base_nm, base_d, extraN in (("standalone", np.zeros(len(sess)), zero), ("C43-CORE", champ, zero), ("C43-GROWTH(T55)", champ + g55, cnt55)):
            mo, mi = combo_margin(bk, pE if base_nm != "standalone" else np.zeros_like(pE), pM if base_nm != "standalone" else np.zeros_like(pM),
                                  extraN if base_nm != "standalone" else zero, r)
            o = H.lane_eval(f"{base_nm} + {nm}", base_d + r["daily"], base_d, sess, mo, mi, dec["TIMING_VALUE_day"],
                            {"stress4_pos": bool((r4["daily"][sess >= H.SPAN21]).sum() > 0), "plateau_pass": False})
            o.update({"carrier": nm, "base": base_nm, **dec})
            rows.append(o)
        print(nm, round(dec["net_day"], 2), round(dec["TIMING_VALUE_day"], 2), flush=True)
    R = pd.DataFrame(rows)
    # plateau for every non-CONST candidate that passes GROWTH or CORE (ex-plateau) on a C43 base
    def pl_test(nm, kw, base_d):
        base_tot = float(X.carrier(mks, bk, **kw)["daily"][sess >= H.SPAN21].sum())
        vals = []
        for f in (0.8, 1.2):
            k2 = dict(kw); k2["tier_map"] = list(X.snap(np.array(kw["tier_map"]) * f)); vals.append(X.carrier(mks, bk, **k2)["daily"])
        for sp in ({"dd_bear": 4.0}, {"dd_bear": 6.0}, {"f": 15, "m": 40}, {"f": 25, "m": 60}):
            vals.append(X.carrier(mks, bk, state_p=sp, **kw)["daily"])
        tots = [float(v[sess >= H.SPAN21].sum()) for v in vals]
        return bool(all(t > 0 and t >= 0.6 * base_tot for t in tots)), tots
    ck = dict(cands)
    for i, r_ in R.iterrows():
        if r_.carrier.startswith("CONST") or r_.base == "standalone":
            continue
        pre = all(r_[c] for c in ("c1", "c2", "c3", "c5", "c6", "c7"))
        if pre:
            ok, tots = pl_test(r_.carrier, ck[r_.carrier], None)
            R.at[i, "c4"] = ok; R.at[i, "plateau_totals"] = str([round(t) for t in tots])
            full_ = R.loc[i]
            cm = all(full_[c] for c in ("c1", "c2", "c3", "c4", "c5", "c6", "c7"))
            c43rd = P.risk(champ[full])["ret_dd"]
            R.at[i, "CORE"] = cm and full_.max_dd <= 15000 and full_.worst_day >= -3000 and full_.ret_dd >= c43rd
            R.at[i, "GROWTH"] = cm and full_.max_dd <= 30000 and full_.worst_day >= -6000 and full_.incr_avg_day_2021 >= 20 and full_.ret_dd >= 0.6 * full_.base_ret_dd
            R.at[i, "AGGRESSIVE_REPORT"] = cm and full_.max_dd <= 50000 and full_.worst_day >= -10000
    R.to_csv(f"{OUT}/T56_results.csv", index=False)
    np.savez_compressed(f"{OUT}/T56_carrier_daily.npz", **{k.replace("|", "__"): v for k, v in keep.items()})
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
    cols = ["base", "carrier", "net_day", "PASSIVE_BETA_day", "TIMING_VALUE_day", "FRICTION_day", "avg_units", "avg_ES", "avg_MNQ", "max_ES", "max_MNQ",
            "avg_day_2021", "incr_avg_day_2021", "max_dd", "worst_day", "ret_dd", "folds_pos", "peak_on_margin_frac", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "CORE", "GROWTH", "AGGRESSIVE_REPORT"]
    print(R[cols].round(3).to_string())
    P.budget("TEST56", hypotheses=len(cands), finalists=int(R.GROWTH.sum() + R.CORE.sum()), note="state ladder carrier controls")


if __name__ == "__main__":
    main()
