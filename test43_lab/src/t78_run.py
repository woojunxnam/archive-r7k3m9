"""TEST78 UPPER-STATE EVENT ATLAS (preregistered 1dda59d7): upper-zone touch / acceptance / break / old-top retest / rising-sequence events on 4
causal box geometries x {MNQ, ES}; net forward P&L at 8 horizons; MATCHED_LONG and MOMENTUM_NULL controls; direction / velocity / width conditioning."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
from box_prereg import GEOMETRIES  # noqa: E402

OUT = os.path.join(B.BOX, "TEST78"); os.makedirs(OUT, exist_ok=True)
GEOS = ["C_PRIORCLOSE_K0.75", "H_BAL6", "A_OBS30_LIFE60", "F_QMAD_W60"]
EVT = ["A1_TOUCH", "A2_CLOSE", "A3_TWO_CLOSES", "BRK0", "BRK10", "BRK20", "Z70", "U4_RETEST"]
HZ = {"h5": 5, "h15": 15, "h30": 30, "h60": 60, "h120": 120, "h1600": "J16", "h1615": "J15", "hNEXTOPEN": "NXT"}
RB_EDGES = np.array([-0.5, -0.2, 0.0, 0.2, 0.5])


@njit(cache=True)
def upper_events(C, H, L, bs, birth, death, lo, hi, uz, J15_, J16_):
    """decision minute j per event type (-1 none); causal: box built from bars < birth, events at closes j in [birth, death)."""
    out = np.full((bs.shape[0], 8), -1, np.int64)
    for b in range(bs.shape[0]):
        s = bs[b]; w = hi[b] - lo[b]; up = lo[b] + uz * w; prev_up = False; jb = -1
        for j in range(birth[b], death[b]):
            if j + 1 >= J15_:
                break
            c = C[s, j]; p = (c - lo[b]) / w
            if out[b, 6] < 0 and p >= 0.70 and p < 0.85:
                out[b, 6] = j
            if out[b, 0] < 0 and H[s, j] >= up:
                out[b, 0] = j
            if c >= up:
                if out[b, 1] < 0:
                    out[b, 1] = j
                if prev_up and out[b, 2] < 0:
                    out[b, 2] = j
                prev_up = True
            else:
                prev_up = False
            if out[b, 3] < 0 and c > hi[b]:
                out[b, 3] = j
            if out[b, 4] < 0 and c > hi[b] + 0.10 * w:
                out[b, 4] = j; jb = j
            if out[b, 5] < 0 and c > hi[b] + 0.20 * w:
                out[b, 5] = j
        # U4 old-top retest after BRK10 (may run past the box's death: the old top is a structural level fixed at the break)
        if jb >= 0:
            pulled = False
            for k in range(jb + 1, J16_):
                if C[s, k] < hi[b] - 0.25 * w:
                    break
                if not pulled and L[s, k] <= hi[b] + 0.10 * w:
                    pulled = True
                    if C[s, k] >= hi[b] and k + 1 < J15_:
                        out[b, 7] = k; break
                    continue
                if pulled and C[s, k] >= hi[b] and k + 1 < J15_:
                    out[b, 7] = k; break
    return out


@njit(cache=True)
def mom_null(FP, FPb, nxt, gidx, gptr, gpos_s, RB, s_arr, jin, jx, kind, pv, cs):
    """generic-momentum control: matched group AND same session-return bucket at the decision minute (jin-1); no box information."""
    m = s_arr.shape[0]; out = np.full(m, np.nan); nn = np.zeros(m, np.int64)
    for e in range(m):
        g = gpos_s[s_arr[e]]; a, b = gptr[g], gptr[g + 1]; bk = RB[s_arr[e], jin[e] - 1]
        tot = 0.0; cnt = 0
        for q in range(a, b):
            ss = gidx[q]
            if RB[ss, jin[e] - 1] != bk:
                continue
            xo = nxt[ss] if kind[e] == 1 else FPb[ss, jx[e]]
            xi = FP[ss, jin[e]]
            if xo != xo or xi != xi:
                continue
            tot += (xo - xi) * pv - 2 * cs; cnt += 1
        if cnt > 0:
            out[e] = tot / cnt; nn[e] = cnt
    return out, nn


def vel_class(v):
    return np.where(np.isnan(v), "NONE", np.where(v < -0.05, "NEGATIVE", np.where(v <= 0.05, "NEAR_ZERO", np.where(v <= 0.25, "POSITIVE", "STRONG"))))


def box_frame(I, geo, dir_thr=0.25):
    Bx = B.build(I, geo, GEOMETRIES[geo]).sort_values(["s", "birth"]).reset_index(drop=True)
    # rebuild prev pointers after sort (build returns prev as row index into its own order; sort by (s, birth) is its native order)
    Bx = B.annotate(Bx, I)
    if dir_thr != 0.25:
        mid = (Bx.lo + Bx.hi).values / 2; w = (Bx.hi - Bx.lo).values; pv = Bx.prev.values
        x = np.where(pv >= 0, (mid - mid[np.maximum(pv, 0)]) / w[np.maximum(pv, 0)], np.nan)
        Bx["dir"] = np.where(pv < 0, "NONE", np.where(x > dir_thr, "RISING", np.where(x < -dir_thr, "FALLING", "FLAT")))
        Bx["prev_dir"] = np.where(pv >= 0, Bx.dir.values[np.maximum(pv, 0)], "NONE")
    # velocity per hour: (mid - mid 2 boxes back) / ATR / elapsed hours
    mid = (Bx.lo + Bx.hi).values / 2; pv = Bx.prev.values; q = pv.copy()
    q2 = np.where(q >= 0, pv[np.maximum(q, 0)], -1); qq = np.where(q2 >= 0, q2, q)
    el = np.where(qq >= 0, (Bx.birth.values - Bx.birth.values[np.maximum(qq, 0)]) / 60.0, np.nan)
    v = np.where((qq >= 0) & (el > 0), (mid - mid[np.maximum(qq, 0)]) / I.atr[Bx.s.values] / el, np.nan)
    Bx["vel_h"] = v; Bx["vel_class"] = vel_class(v)
    return Bx


def event_table(I, Bx, uz=0.85):
    a = lambda c, t=np.int64: Bx[c].values.astype(t)
    ev = upper_events(I.C, I.H, I.L, a("s"), a("birth"), a("death"), a("lo", float), a("hi", float), uz, B.J15, B.J16)
    rows = []
    for k, nm in enumerate(EVT):
        m = ev[:, k] >= 0
        if m.any():
            rows.append(pd.DataFrame({"box": np.where(m)[0], "event": nm, "j": ev[m, k]}))
    E = pd.concat(rows, ignore_index=True)
    E = E.join(Bx[["s", "lo", "hi", "dir", "prev_dir", "width_dyn", "vel_class", "w_atr"]], on="box")
    ext = []
    for nm, base, cond in (("A4_RISING", "A2_CLOSE", lambda d: d.dir == "RISING"), ("SEQ2", "A2_CLOSE", lambda d: (d.dir == "RISING") & (d.prev_dir == "RISING"))):
        x = E[(E.event == base)]; ext.append(x[cond(x)].assign(event=nm))
    return pd.concat([E] + ext, ignore_index=True)


def price_labels(I, E, RB):
    s = E.s.values.astype(np.int64); ji = E.j.values.astype(np.int64) + 1; px = I.FP[s, ji]
    E["px_in"] = px
    for h, v in HZ.items():
        if v == "NXT":
            xo = I.nxt_open[s]; jj = np.full(len(E), B.J15, np.int64); kind = np.ones(len(E), np.int64)
        else:
            jj = np.minimum(ji + v, B.J15) if isinstance(v, int) else np.full(len(E), B.J16 if v == "J16" else B.J15, np.int64)
            jj = np.maximum(jj, ji); xo = I.FPb[s, jj]; kind = np.zeros(len(E), np.int64)
        gross = (xo - px) * I.pv
        E[f"{h}_net"] = gross - 2 * I.cs; E[f"{h}_net4"] = gross - 2 * I.cs4
        c1 = B.matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, s, ji, jj, kind, I.pv, I.cs)
        c2, nn = mom_null(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, RB, s, ji, jj, kind, I.pv, I.cs)
        E[f"{h}_mx"] = E[f"{h}_net"] - c1; E[f"{h}_mom"] = E[f"{h}_net"] - c2
        if h == "h1615":
            E["mom_n_ctl"] = nn
    return E


def ret_bucket(I):
    r = (I.C - I.FP[:, :1]) / I.atr[:, None]
    return np.digitize(r, RB_EDGES).astype(np.int64)


def summarize(E, I, keys):
    nd = int(I.full.sum()); rows = []
    for k, g in E.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        for h in HZ:
            fm = {nm: g[(g.date >= a) & (g.date <= b)][f"{h}_mom"].mean() for nm, a, b in B.FOLDS}
            fn = {nm: int(((g.date >= a) & (g.date <= b)).sum()) for nm, a, b in B.FOLDS}
            rows.append({**dict(zip(keys, k)), "horizon": h, "n": len(g), "per_day": len(g) / nd, "net_per_event": g[f"{h}_net"].mean(), "net4_per_event": g[f"{h}_net4"].mean(),
                         "matched_x_per_event": g[f"{h}_mx"].mean(), "momentum_x_per_event": g[f"{h}_mom"].mean(), "momentum_x_day": g[f"{h}_mom"].sum() / nd,
                         "folds_mom_pos": int(sum(v > 0 for v in fm.values() if v == v)), "fold_median_mom": float(np.nanmedian(list(fm.values()))),
                         "min_fold_n": min(fn.values()), **{f"mom_{nm}": v for nm, v in fm.items()}})
    return pd.DataFrame(rows)


def main():
    Is = B.load(); allE = []
    for inst, I in Is.items():
        RB = ret_bucket(I)
        for geo in GEOS:
            Bx = box_frame(I, geo); E = event_table(I, Bx); E = price_labels(I, E, RB)
            E["instrument"] = inst; E["geometry"] = geo; E["date"] = I.sess[E.s.values]; allE.append(E)
            print(inst, geo, len(Bx), E.groupby("event").size().to_dict(), flush=True)
    E = pd.concat(allE, ignore_index=True)
    E.drop(columns=["date"]).to_parquet(os.path.join(OUT, "T78_events.parquet"))
    I0 = Is["MNQ"]
    P = summarize(E, I0, ["instrument", "event"])
    P["qualifies"] = (P.net_per_event > 0) & (P.net4_per_event > 0) & (P.momentum_x_per_event > 0) & (P.folds_mom_pos >= 4) & (P.matched_x_per_event > 0) & (P.n >= 300)
    G = summarize(E, I0, ["instrument", "event", "geometry"])
    CD = pd.concat([summarize(E[E.event.isin(["A2_CLOSE", "BRK10", "A1_TOUCH"])], I0, ["instrument", "event", c]).assign(cond=c) for c in ("dir", "vel_class", "width_dyn")], ignore_index=True)
    P.to_csv(os.path.join(OUT, "T78_POOLED.csv"), index=False); G.to_csv(os.path.join(OUT, "T78_BY_GEOMETRY.csv"), index=False); CD.to_csv(os.path.join(OUT, "T78_CONDITIONING.csv"), index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)
    cols = ["instrument", "event", "horizon", "n", "net_per_event", "net4_per_event", "matched_x_per_event", "momentum_x_per_event", "folds_mom_pos", "fold_median_mom", "qualifies"]
    print(P[P.horizon.isin(["h5", "h30", "h60", "h1600", "h1615", "hNEXTOPEN"])][cols].round(2).to_string())
    print("QUALIFYING:", P[P.qualifies][["instrument", "event", "horizon"]].values.tolist())
    print(CD[CD.horizon.isin(["h60", "h1615"])][["instrument", "event", "cond", "dir", "vel_class", "width_dyn", "horizon", "n", "net_per_event", "momentum_x_per_event", "folds_mom_pos"]].round(2).to_string())


if __name__ == "__main__":
    main()
