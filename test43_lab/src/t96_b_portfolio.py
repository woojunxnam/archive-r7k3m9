"""TEST96 Track B portfolio tests B0-B5 (prereg ad9240b7) - RESEARCH_ONLY_APPROX members (no member passes the frozen parity rule).
Member trades -> 1m grid (fill minute = bar open time - 09:30), capacity vs MAIN occupancy (MNQ <= 6, MES <= 8; breaching entries skipped),
daily $ at exit session.  Engine prices already include 1 tick slippage; commission 0.62 / side; SLIP4 adds 3 ticks / side."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
import t65_common as K  # noqa: E402
import t96_common as W  # noqa: E402

PV = {"MES": 5.0, "MNQ": 2.0}; TICKV = {"MES": 1.25, "MNQ": 0.5}; CAP = {"MES": 8, "MNQ": 6}


def load_members():
    M = {}
    for nm, path, inst in (("LC02", "out/t46/engine_trades_LC02.parquet", "MES"), ("LC03", "out/t96/engine_trades_LC03_NQ.parquet", "MNQ"),
                           ("LC05", "out/t96/engine_trades_LC05_NQ.parquet", "MNQ")):
        e = pd.read_parquet(os.path.join(B.LAB, path))
        M[nm] = (pd.DataFrame({"entry_time": pd.to_datetime(e.entry_time), "entry_px": e.entry_px, "exit_time": pd.to_datetime(e.exit_time) + pd.Timedelta(minutes=5),
                               "exit_px": e.exit_px}), inst)
    p = os.path.join(W.OUT, "TS22_T2207_REPLAY.csv")
    if os.path.exists(p):
        e = pd.read_csv(p, parse_dates=["entry_time", "exit_time"]); M["TS22"] = (e[["entry_time", "entry_px", "exit_time", "exit_px"]], "MNQ_NET")
    p = os.path.join(W.OUT, "T20_V1_ENGINE_LEGS.csv")
    if os.path.exists(p):
        e = pd.read_csv(p, parse_dates=["entry_time", "exit_time"]); e["exit_time"] = e.exit_time + pd.Timedelta(minutes=5)   # exits fill at bar close
        lg = e[e.direction.astype(str).str.upper() == "LONG"]
        M["TEST20_L2_ONLY"] = (lg[lg.leg_index == 2][["entry_time", "entry_px", "exit_time", "exit_px"]], "MNQ_T20")
        M["T20_V1"] = (lg[["entry_time", "entry_px", "exit_time", "exit_px"]], "MNQ_T20")
    return M


def to_daily(I, T, inst, occ, slip4=False):
    """-> daily $, occupancy add, trades kept."""
    kind = inst; inst = "MNQ" if inst.startswith("MNQ") else inst
    si = pd.Index(I.sess); d = np.zeros(I.n); add = np.zeros((I.n, occ.shape[1]), int); kept = 0
    for r in T.itertuples(index=False):
        s = si.get_indexer([r.entry_time.normalize()])[0]; sx = si.get_indexer([r.exit_time.normalize()])[0]
        if s < 0 or sx < 0 or not I.full[s]:
            continue
        ji = (r.entry_time.hour * 60 + r.entry_time.minute) - 570; jx = (r.exit_time.hour * 60 + r.exit_time.minute) - 570
        ji = int(np.clip(ji, 0, occ.shape[1] - 1)); jx = int(np.clip(jx, ji + 1, occ.shape[1])) if sx == s else occ.shape[1]
        if (occ[s, ji:jx] + add[s, ji:jx] + 1 > CAP[inst]).any():
            continue
        add[s, ji:jx] += 1; kept += 1
        # engine / port prices include 1 tick; the T20 port and TS22 port are converted the same way by their exporters
        extra = 3 * TICKV[inst] if slip4 else 0.0
        slip_in_px = kind != "MNQ_NET"                 # TS22 port prices are raw fills (no slippage) -> charge the tick here
        d[sx] += (r.exit_px - r.entry_px) * PV[inst] - 2 * (0.62 + extra + (0 if slip_in_px else TICKV[inst]))
    return d, add, kept


def main():
    ctx = W.main_ctx(); I = ctx["Is"]["MNQ"]; main = ctx["main"]; full = I.full; s21 = np.asarray(I.sess >= K.S21)
    occ = {"MNQ": ctx["occ"]["MNQ"].copy(), "MES": ctx["occ"]["ES"].copy()}
    M = load_members(); daily = {}; info = {}
    for nm, (T, inst) in M.items():
        base = "MNQ" if inst.startswith("MNQ") else inst
        d, add, kept = to_daily(I, T, inst, occ[base]); d4, _, _ = to_daily(I, T, inst, occ[base], slip4=True)
        daily[nm] = d; info[nm] = {"inst": base, "trades_kept": kept, "trades_in": len(T), "avg_day": float(d[full].mean()), "avg_day_2021": float(d[s21].mean()),
                                   "slip4_day": float(d4[full].mean()), "corr_to_main": float(np.corrcoef(d[full], main[full])[0, 1]) if d[full].std() > 0 else np.nan,
                                   "max_dd": B.risk(d[full])["max_dd"]}
    idx = [k for k in ("LC02", "LC03", "LC05", "TS22") if k in daily]
    INDEX = sum((daily[k] for k in idx), np.zeros(I.n))
    cands = {"B0_MAIN": np.zeros(I.n), "B1_MAIN+INDEX_APPROX": INDEX}
    if "TEST20_L2_ONLY" in daily:
        cands.update({"B2_MAIN+L2_ONLY": daily["TEST20_L2_ONLY"], "B3_MAIN+INDEX_APPROX+L2_ONLY": INDEX + daily["TEST20_L2_ONLY"],
                      "B4_MAIN+T20_V1": daily["T20_V1"], "B5_MAIN+INDEX_APPROX+T20_V1": INDEX + daily["T20_V1"]})
    rows = []; rm = B.risk(main[full])
    for nm, add in cands.items():
        x = main + add; r = B.risk(x[full]); r21 = B.risk(x[s21]); am = full & (add != 0)
        rows.append({"candidate": nm, "avg_day": r["avg_day"], "incr_avg_day": float(add[full].mean()), "incr_avg_day_2021": float(add[s21].mean()), "max_dd": r["max_dd"],
                     "worst_day": r["worst_day"], "ret_dd": r["ret_dd"], "ret_dd_2021": r21["ret_dd"],
                     "corr_add_to_main": float(np.corrcoef(add[full], main[full])[0, 1]) if add[full].std() > 0 else np.nan,
                     "loss_jaccard": float(((add < 0) & (main < 0) & am).sum() / max(((add < 0) | (main < 0))[am].sum(), 1)) if am.any() else np.nan,
                     "PORTFOLIO_PASS_IF_EXACT": bool(add[full].mean() >= 10 and add[s21].mean() >= 10 and r["ret_dd"] >= rm["ret_dd"] and r["max_dd"] <= 1.1 * rm["max_dd"]
                                                     and r["worst_day"] >= -5000) if nm != "B0_MAIN" else None})
    R = pd.DataFrame(rows); Mi = pd.DataFrame(info).T
    W.save("T96_B_PORTFOLIOS.json", {"members": info, "index_members_available": idx, "table": R.to_dict("records"),
                                     "note": "RESEARCH_ONLY_APPROX / SELECTION-BIASED; no authorization (no member RECOVERED_EXACT)"})
    W.md("T96_B_PORTFOLIOS.md", "TEST96 Track B - B0-B5 (RESEARCH_ONLY_APPROX, prereg ad9240b7)",
         ["All members are RESEARCH_ONLY_APPROX (none passes the frozen parity rule) -> results cannot authorize; SELECTION-BIASED.", Mi, R])
    pd.set_option("display.width", 250); print(Mi.to_string()); print(R.to_string())


if __name__ == "__main__":
    main()
