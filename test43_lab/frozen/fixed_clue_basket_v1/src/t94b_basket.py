"""TEST94B LANE B - FIXED SHADOW-CLUE BASKET (preregistered da885810): members frozen before economics, run exactly once, joint capacity with T61."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402
import t45_common as C45  # noqa: E402
import t65_common as K  # noqa: E402

OUT = os.path.join(B.LAB, "out", "PRESS_BASKET_LAB", "LANE_B_BASKET"); os.makedirs(OUT, exist_ok=True)


def member_trades():
    """frozen generators -> list of (member, inst, lots, s, j_in(fill), j_out(fill))."""
    import t65_mod as M
    import t66_run as T66
    import t67_run as T67
    import t68_run as T68
    import t86_run as T86
    import t91_ml as T91
    from sklearn.ensemble import HistGradientBoostingRegressor
    env = M.Env(); X = env.X; rows = []
    for r in T66.ml_signals(X).itertuples(index=False):
        rows.append(("T66_ML_OPENING", "MNQ", 1, int(r.s), int(r.j_in), int(r.j_out)))
    EV = pd.read_parquet(os.path.join(C45.ROOT, "out", "test65", "T65_event_labels.parquet"))
    ab = EV[(EV.cat == "NQ_SECONDARY_BREAKOUT") & (EV.date >= K.S21)]
    for r in ab.itertuples(index=False):
        rows.append(("T68_RAW_BREAKS", "MNQ", 1, int(r.s), int(r.j), B.J15))
    base = T67.tom_signals(X.sess)
    for r in base.itertuples(index=False):
        for s in range(r.s, r.s_out + 1):
            rows.append(("T67_TOM_INTRADAY", "ES", 2, int(s), 0, B.J15))
    # PG12 ML: exactly the TEST91 primary (HGB, preset, walk-forward, predicted net > 0)
    Is = B.load(); I = Is["MNQ"]; BK = A.buckets(I); c = T86.CAND["PG12_DOWN_STACK"]; h = c["horizon"]
    E, P1, F = T86.events(I, Is["ES"], "PG12_DOWN_STACK", c["base_proxy"])
    E = A.label(I, E.copy(), BK); E["date"] = I.sess[E.s.values]; E = E.dropna(subset=[f"{h}_net"]).reset_index(drop=True)
    Xf = T91.feats(I, E, P1, F); y = E[f"{h}_net"].values; pred = np.full(len(E), np.nan)
    for nm, a_, b_ in B.FOLDS:
        tr = (E.date < a_).values; te = ((E.date >= a_) & (E.date <= b_)).values
        m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=25, random_state=5).fit(Xf[tr], y[tr]); pred[te] = m.predict(Xf[te])
    jx16 = C45.g("16:00")
    for r, p in zip(E.itertuples(index=False), pred):
        if p == p and p > 0:
            rows.append(("PG12_ML", "MNQ", 1, int(r.s), int(r.j) + 1, jx16))
    return pd.DataFrame(rows, columns=["member", "inst", "lots", "s", "j_in", "j_out"]), env


def joint(trades, Is, TN, TE, slip=1.0):
    """minute-level joint allocation with T61 priority: MNQ T61 + basket <= 6 (skip at entry, cut latest at the same fill), MES T61 + basket <= 8."""
    daily = {m: np.zeros(Is["MNQ"].n) for m in trades.member.unique()}; led = []; cnt = np.zeros((Is["MNQ"].n, A.NG, 2))
    by_s = {s: g.sort_values("j_in") for s, g in trades.groupby("s")}
    for s, g in by_s.items():
        opn = []; ents = list(g.itertuples(index=False)); ei = 0
        for j in range(A.NG):
            keep = []
            for p in opn:
                if p["j_out"] == j:
                    I = Is[p["inst"]]; px = I.FPb[s, j]; pnl = p["lots"] * ((px - p["px"]) * I.pv - 2 * C45.cost_side(I.k, slip))
                    daily[p["member"]][s] += pnl; led.append({**p, "s": s, "j_x": j, "pnl": pnl})
                else:
                    keep.append(p)
            opn = keep
            nmnq = sum(p["lots"] for p in opn if p["inst"] == "MNQ")
            while opn and TN[s, j] + nmnq > 6 and any(p["inst"] == "MNQ" for p in opn):
                k = max(i for i, p in enumerate(opn) if p["inst"] == "MNQ"); p = opn.pop(k); I = Is["MNQ"]; px = I.FPb[s, j]
                pnl = p["lots"] * ((px - p["px"]) * I.pv - 2 * C45.cost_side(I.k, slip)); daily[p["member"]][s] += pnl; led.append({**p, "s": s, "j_x": j, "pnl": pnl, "cut": 1})
                nmnq -= p["lots"]
            while ei < len(ents) and ents[ei].j_in <= j:
                e = ents[ei]; ei += 1
                if e.j_in != j or e.j_out <= j or any(p["member"] == e.member for p in opn):
                    continue
                I = Is[e.inst]
                if e.inst == "MNQ" and TN[s, j] + nmnq + e.lots > 6:
                    continue
                if e.inst == "ES" and TE[s, j] + sum(p["lots"] for p in opn if p["inst"] == "ES") + e.lots > 8:
                    continue
                px = I.FP[s, j]
                if px != px:
                    continue
                opn.append({"member": e.member, "inst": e.inst, "lots": e.lots, "j_in": j, "j_out": e.j_out, "px": px})
                if e.inst == "MNQ":
                    nmnq += e.lots
            for p in opn:
                cnt[s, j, 0 if p["inst"] == "ES" else 1] += p["lots"]
    return daily, pd.DataFrame(led), cnt


def main():
    trades, env = member_trades()
    Is = B.load(); X = env.X; sess = X.sess; full = np.asarray(sess >= K.START); s21 = np.asarray(sess >= K.S21)
    daily, L, cnt = joint(trades, Is, X.qN.astype(int), X.qE.astype(int))
    d4 = sum(joint(trades, Is, X.qN.astype(int), X.qE.astype(int), slip=4.0)[0].values())
    d = sum(daily.values()); t61 = X.t61
    ex = np.zeros(X.n)
    for inst in ("MNQ", "ES"):
        Li = L[L.inst == inst]
        if len(Li):
            I = Is[inst]
            c = B.matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, Li.s.values.astype(np.int64), Li.j_in.values.astype(np.int64), Li.j_x.values.astype(np.int64),
                          np.zeros(len(Li), np.int64), I.pv, I.cs) * Li.lots.values
            np.add.at(ex, Li.s.values, Li.pnl.values - np.nan_to_num(c))
    qE = X.qE + cnt[..., 0]; qN = X.qN + cnt[..., 1]
    mi = (qE * env.bk.m_in["ES"][:, None] + qN * env.bk.m_in["MNQ"][:, None])[full].max()
    mi61 = (X.qE * env.bk.m_in["ES"][:, None] + X.qN * env.bk.m_in["MNQ"][:, None])[full].max()
    gate = K.incremental_gate("FIXED_CLUE_BASKET", d, t61, sess, {"matched_excess_day": float(ex[full].mean()), "slip4_incr_avg_day": float(d4[full].mean()),
                                                                   "plateau_pass": True, "delay1_incr_avg_day": 1.0, "peak_total_MNQ": int(qN[full].max()),
                                                                   "peak_total_MES": int(qE[full].max()), "peak_margin_pct": float(mi / 150000 * 100)})
    am = full & (d != 0); lossj = float(((d < 0) & (t61 < 0) & am).sum() / max(((d < 0) | (t61 < 0))[am].sum(), 1))
    per = {m: {"avg_day": float(v[full].mean()), "avg_day_2021": float(v[s21].mean()), "trades": int((L.member == m).sum()),
               "corr_to_t61": float(np.corrcoef(v[full], t61[full])[0, 1]) if v[full].std() > 0 else 0.0} for m, v in daily.items()}
    cm = pd.DataFrame({m: v[s21] for m, v in daily.items()}).corr().round(3)
    rc, rb = B.risk((t61 + d)[full]), B.risk(t61[full]); rc21, rb21 = B.risk((t61 + d)[s21]), B.risk(t61[s21])
    o = {"FIXED_CLUE_BASKET_MEMBERS": list(daily), "basket_avg_day": float(d[full].mean()), "basket_avg_day_2021": float(d[s21].mean()), "basket_maxdd": B.risk(d[full])["max_dd"],
         "basket_worst": float(d[full].min()), "basket_folds_pos": gate["folds_pos"], "basket_corr_to_t61": gate["corr_to_t61"], "loss_day_jaccard": lossj,
         "t61_plus_avg_day": rc["avg_day"], "t61_plus_incr_day": float(d[full].mean()), "t61_plus_incr_day_2021": float(d[s21].mean()), "t61_plus_maxdd": rc["max_dd"],
         "t61_plus_worst": rc["worst_day"], "t61_plus_ret_dd": rc["ret_dd"], "t61_ret_dd": rb["ret_dd"], "t61_plus_ret_dd_2021": rc21["ret_dd"], "t61_ret_dd_2021": rb21["ret_dd"],
         "peak_margin_pct_t61_plus": float(mi / 150000 * 100), "peak_margin_pct_t61": float(mi61 / 150000 * 100), "t61_plus_slip4_incr_day": float(d4[full].mean()),
         "matched_excess_day": float(ex[full].mean()), "turnover_sides_per_day": float(2 * L.lots.sum() / full.sum()), "priority_cuts": int(L.get("cut", pd.Series(dtype=float)).fillna(0).sum()),
         "gate_items": {k: v for k, v in gate.items() if k.startswith("g_")}, "per_member": per}
    o["MEANINGFUL_INCREMENT"] = bool(o["t61_plus_incr_day"] >= 10 and o["t61_plus_incr_day_2021"] >= 10 and rc["ret_dd"] >= rb["ret_dd"])
    items = {k: v for k, v in gate.items() if k in ("g_folds", "g_slip4", "g_top5", "g_regime", "g_corr", "g_caps", "g_risk", "g_incr_pos", "g_excess")}
    o["FIXED_CLUE_BASKET_PASS"] = bool(all(items.values()) and o["MEANINGFUL_INCREMENT"])
    import json
    json.dump(o, open(os.path.join(OUT, "BASKET_RESULT.json"), "w"), indent=1, default=str); cm.to_csv(os.path.join(OUT, "BASKET_MEMBER_CORR_2021.csv"))
    L.to_csv(os.path.join(OUT, "BASKET_LEDGER.csv"), index=False); np.savez_compressed(os.path.join(OUT, "BASKET_daily.npz"), basket=d, **daily)
    print(json.dumps(o, indent=1, default=str)); print(cm)


if __name__ == "__main__":
    main()
