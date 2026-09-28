"""TEST70 BOX GEOMETRY ATLAS (preregistered 455ffc57): 44 causal geometries x {MNQ, ES}; bottom-touch events, economic labels, matched-long excess,
horizons, zones, top-hold study, direction / transition / width / velocity / time-of-day tables, failure map.  No strategy optimisation."""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, os.path.dirname(__file__))
import box_common as B  # noqa: E402
from box_prereg import GEOMETRIES, ZONES  # noqa: E402

OUT = os.path.join(B.BOX, "TEST70"); LZ, UZ = ZONES["LOWER_ZONE_base"], ZONES["UPPER_ZONE_base"]
HZ = {"h15": 15, "h30": 30, "h60": 60, "h120": 120, "h1600": "J16", "h1615": "J15", "hNEXTOPEN": "NXT"}


@njit(cache=True)
def zone_first(C, bs, birth, death, lo, hi, edges):
    nz = edges.shape[0] - 1; out = np.full((bs.shape[0], nz), -1, np.int64)
    for b in range(bs.shape[0]):
        w = hi[b] - lo[b]; s = bs[b]
        for j in range(birth[b], death[b]):
            p = (C[s, j] - lo[b]) / w
            for z in range(nz):
                if out[b, z] < 0 and p >= edges[z] and (p < edges[z + 1] or (z == nz - 1 and p <= edges[z + 1])):
                    out[b, z] = j
    return out


@njit(cache=True)
def breaks(C, bs, birth, death, lo, hi, J15_):
    """first up / down break (close beyond the box during its life) and whether it is TRUE (no close back inside within 30 min)."""
    out = np.full((bs.shape[0], 4), -1, np.int64)   # j_up, true_up, j_dn, true_dn
    for b in range(bs.shape[0]):
        s = bs[b]
        for j in range(birth[b], death[b]):
            if out[b, 0] < 0 and C[s, j] > hi[b]:
                out[b, 0] = j; t = 1
                for k in range(j + 1, min(j + 31, J15_ + 1)):
                    if C[s, k] <= hi[b]:
                        t = 0; break
                out[b, 1] = t
            if out[b, 2] < 0 and C[s, j] < lo[b]:
                out[b, 2] = j; t = 1
                for k in range(j + 1, min(j + 31, J15_ + 1)):
                    if C[s, k] >= lo[b]:
                        t = 0; break
                out[b, 3] = t
    return out


def seg_of(j):
    for k, (a, b) in B.SEGS.items():
        if a <= j < b:
            return k
    return "S5_1515_1615"


def events_for(I, geo, spec):
    Bx = B.build(I, geo, spec)
    if not len(Bx):
        return Bx, pd.DataFrame()
    Bx = B.annotate(Bx, I)
    a = lambda c, t=np.int64: Bx[c].values.astype(t)
    ev = B.bottom_events(I.C, I.H, I.L, I.FP, I.FPb, a("s"), a("birth"), a("death"), a("lo", float), a("hi", float), LZ, UZ, B.J15, B.J16)
    ok = ~np.isnan(ev[:, 0])
    D = Bx[ok].copy().reset_index().rename(columns={"index": "box"})
    e = ev[ok]
    for i, c in enumerate(["j_touch", "j_in", "px_in", "j_xdec", "reason", "j_x", "px_x", "mid_before_break", "top_before_break", "t_mid", "t_top", "mfe_w", "mae_w",
                           "j_topdec", "px_topfill", "j_topfill"]):
        D[c] = e[:, i]
    s = D.s.values.astype(np.int64); ji = D.j_in.values.astype(np.int64); jx = D.j_x.values.astype(np.int64)
    D["gross"] = (D.px_x - D.px_in) * I.pv; D["net"] = D.gross - 2 * I.cs; D["net4"] = D.gross - 2 * I.cs4
    ctl = B.matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, s, ji, jx, np.zeros(len(D), np.int64), I.pv, I.cs)
    D["ctl"] = ctl; D["excess"] = D.net - ctl; D["excess4"] = D.net4 - ctl
    for h, v in HZ.items():
        if v == "NXT":
            xo = I.nxt_open[s]; kind = np.ones(len(D), np.int64); jj = np.full(len(D), B.J15, np.int64)
        else:
            jj = np.minimum(ji + v, B.J15) if isinstance(v, int) else np.full(len(D), B.J16 if v == "J16" else B.J15, np.int64)
            jj = np.maximum(jj, ji); xo = I.FPb[s, jj]; kind = np.zeros(len(D), np.int64)
        n_ = (xo - D.px_in.values) * I.pv - 2 * I.cs
        c_ = B.matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, s, ji, jj, kind, I.pv, I.cs)
        D[f"{h}_net"] = n_; D[f"{h}_x"] = n_ - c_
    D["date"] = I.sess[s]; D["fold"] = B.fold_of(D.date); D["seg"] = [seg_of(j) for j in D.j_touch.astype(int)]
    D["age_at_touch"] = D.j_touch - D.birth; D["life"] = D.death - D.birth
    return Bx, D


def summarize(I, geo, spec, Bx, D):
    nd = int(I.full.sum()); r = {"instrument": I.name, "geometry": geo, "family": spec["family"], "boxes": len(Bx), "boxes_per_day": len(Bx) / nd}
    if not len(D):
        return {**r, "events": 0, "eligible": False}
    fs = {nm: int(((I.sess >= a) & (I.sess <= b)).sum()) for nm, a, b in B.FOLDS}
    fx = {nm: float(D.excess[D.fold == nm].sum() / fs[nm]) for nm in fs}; fn = {nm: int((D.fold == nm).sum()) for nm in fs}
    life_h = float((Bx.death - Bx.birth).sum() / 60)
    r.update({"events": len(D), "events_per_day": len(D) / nd, "median_w_atr": float(Bx.w_atr.median()), "median_life_min": float((Bx.death - Bx.birth).median()),
              "net_per_event": float(D.net.mean()), "excess_per_event": float(D.excess.mean()), "net_day": float(D.net.sum() / nd),
              "excess_day": float(D.excess.sum() / nd), "excess4_day": float(D.excess4.sum() / nd), "net4_day": float(D.net4.sum() / nd),
              "top_before_break": float(D.top_before_break.mean()), "mid_before_break": float(D.mid_before_break.mean()),
              "p_break": float((D.reason == 2).mean()), "p_eod": float((D.reason == 3).mean()), "mfe_w": float(D.mfe_w.mean()), "mae_w": float(D.mae_w.mean()),
              "usd_per_completed_cycle": float(D.net[D.reason == 1].mean()) if (D.reason == 1).any() else np.nan,
              "usd_per_bottom_touch": float(D.net.mean()), "usd_per_contract_side": float(D.net.sum() / (2 * len(D))),
              "usd_per_active_box_hour": float(D.net.sum() / max(life_h, 1e-9)), "friction_over_gross": float(2 * I.cs * len(D) / max(abs(D.gross.sum()), 1e-9)),
              **{f"fx_{k}": v for k, v in fx.items()}, **{f"n_{k}": v for k, v in fn.items()},
              "folds_excess_pos": int(sum(v > 0 for v in fx.values())), "score_fold_median_excess_day": float(np.median(list(fx.values()))),
              **{f"{h}_x_per_event": float(D[f"{h}_x"].mean()) for h in HZ}})
    r["eligible"] = bool(r["folds_excess_pos"] >= 4 and r["events"] >= 300 and min(fn.values()) >= 40 and r["excess4_day"] > 0)
    return r


def main():
    Is = B.load()
    edges = np.array([z[0] for z in ZONES["study_zones"]] + [1.0])
    atlas, horiz, zones, dirs, trans, wdyn, vel, segs, fails, tops, geoms = [], [], [], [], [], [], [], [], [], [], []
    for inst, I in Is.items():
        nd = int(I.full.sum())
        for geo, spec in GEOMETRIES.items():
            Bx, D = events_for(I, geo, spec)
            r = summarize(I, geo, spec, Bx, D); atlas.append(r)
            geoms.append({"geometry": geo, "instrument": inst, **spec, "boxes": len(Bx), "events": len(D)})
            print(inst, geo, len(Bx), len(D), round(r.get("excess_day", np.nan), 2), r.get("folds_excess_pos"), flush=True)
            if not len(D):
                continue
            key = {"instrument": inst, "geometry": geo}
            for h in HZ:
                horiz.append({**key, "horizon": h, "net_per_event": float(D[f"{h}_net"].mean()), "excess_per_event": float(D[f"{h}_x"].mean()),
                              "folds_x_pos": int(sum(D[D.fold == nm][f"{h}_x"].mean() > 0 for nm, _, _ in B.FOLDS))})
            # zones
            a = lambda c, t=np.int64: Bx[c].values.astype(t)
            zf = zone_first(I.C, a("s"), a("birth"), a("death"), a("lo", float), a("hi", float), edges)
            for z in range(zf.shape[1]):
                m = (zf[:, z] >= 0) & (zf[:, z] + 1 < B.J15)
                if m.sum() < 30:
                    continue
                s = Bx.s.values[m].astype(np.int64); ji = zf[m, z] + 1
                for h, hv in (("h30", 30), ("h1615", None)):
                    jj = np.minimum(ji + hv, B.J15) if hv else np.full(len(ji), B.J15, np.int64)
                    n_ = (I.FPb[s, jj] - I.FP[s, ji]) * I.pv - 2 * I.cs
                    c_ = B.matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, s, ji, jj, np.zeros(len(ji), np.int64), I.pv, I.cs)
                    zones.append({**key, "zone": f"{edges[z]:.2f}-{edges[z + 1]:.2f}", "horizon": h, "n": int(m.sum()), "net": float(np.nanmean(n_)), "excess": float(np.nanmean(n_ - c_)), "ctl_nan": int(np.isnan(c_).sum())})
            # direction / transitions / width / velocity / segment
            for col, lst in (("dir", dirs), ("width_dyn", wdyn), ("seg", segs)):
                for v, g in D.groupby(col):
                    lst.append({**key, col: v, "n": len(g), "net_per_event": float(g.net.mean()), "excess_per_event": float(g.excess.mean()),
                                "excess_day": float(g.excess.sum() / nd), "folds_x_pos": int(sum(g[g.fold == nm].excess.mean() > 0 for nm, _, _ in B.FOLDS))})
            for (pdv, dv), g in D.groupby(["prev_dir", "dir"]):
                trans.append({**key, "transition": f"{pdv}->{dv}", "n": len(g), "net_per_event": float(g.net.mean()), "excess_per_event": float(g.excess.mean())})
            vq = pd.qcut(D.velocity, 3, labels=["V_LOW", "V_MID", "V_HIGH"], duplicates="drop") if D.velocity.notna().sum() > 60 else None
            if vq is not None:
                for v, g in D.groupby(vq, observed=True):
                    vel.append({**key, "velocity_tercile": str(v), "n": len(g), "excess_per_event": float(g.excess.mean()), "net_per_event": float(g.net.mean())})
            # top study: exit now vs hold (incremental, raw and matched; no extra costs for holding)
            T = D[D.reason == 1].dropna(subset=["j_topfill"])
            if len(T) >= 30:
                s = T.s.values.astype(np.int64); jt = T.j_topfill.values.astype(np.int64); px = T.px_topfill.values
                for h, hv in HZ.items():
                    if hv == "NXT":
                        xo = I.nxt_open[s]; jj = np.full(len(T), B.J15, np.int64); kind = np.ones(len(T), np.int64)
                    else:
                        jj = np.minimum(jt + hv, B.J15) if isinstance(hv, int) else np.full(len(T), B.J16 if hv == "J16" else B.J15, np.int64)
                        jj = np.maximum(jj, jt); xo = I.FPb[s, jj]; kind = np.zeros(len(T), np.int64)
                    raw = (xo - px) * I.pv
                    c_ = B.matched(I.FP, I.FPb, I.nxt_open, I.gidx, I.gptr, I.gpos, s, jt, jj, kind, I.pv, 0.0)
                    tops.append({**key, "hold": h, "n": len(T), "hold_incr_raw": float(np.nanmean(raw)), "hold_incr_excess": float(np.nanmean(raw - c_))})
            # failure map (labels only) - causal differences at the touch
            bk = breaks(I.C, a("s"), a("birth"), a("death"), a("lo", float), a("hi", float), B.J15)
            Dx = D.assign(outcome=np.where(D.top_before_break == 1, "BOX_BOTTOM_SUCCESS", "BOX_BOTTOM_FAILURE"))
            for o, g in Dx.groupby("outcome"):
                fails.append({**key, "label": o, "n": len(g), "w_atr": float(g.w_atr.mean()), "age_at_touch": float(g.age_at_touch.mean()),
                              "rising_share": float((g.dir == "RISING").mean()), "falling_share": float((g.dir == "FALLING").mean()),
                              "expanding_share": float((g.width_dyn == "EXPANDING").mean()), "velocity": float(g.velocity.mean())})
            for lab, cj, ct in (("UP_BREAK", 0, 1), ("DOWN_BREAK", 2, 3)):
                m = bk[:, cj] >= 0
                for tv, nm in ((1, "TRUE_"), (0, "FALSE_")):
                    mm = m & (bk[:, ct] == tv)
                    fails.append({**key, "label": nm + lab, "n": int(mm.sum()), "w_atr": float(Bx.w_atr[mm].mean()) if mm.any() else np.nan,
                                  "age_at_touch": float((bk[mm, cj] - Bx.birth.values[mm]).mean()) if mm.any() else np.nan,
                                  "rising_share": float((Bx.dir[mm] == "RISING").mean()) if mm.any() else np.nan,
                                  "falling_share": float((Bx.dir[mm] == "FALLING").mean()) if mm.any() else np.nan,
                                  "expanding_share": float((Bx.width_dyn[mm] == "EXPANDING").mean()) if mm.any() else np.nan, "velocity": float(Bx.velocity[mm].mean()) if mm.any() else np.nan})
            D.drop(columns=["date"]).to_parquet(os.path.join(OUT, f"events_{inst}_{geo}.parquet"))
    A = pd.DataFrame(atlas)
    for nm, df in (("BOX_GEOMETRY_ATLAS", A), ("ATLAS_HORIZONS", pd.DataFrame(horiz)), ("ATLAS_ZONES", pd.DataFrame(zones)), ("ATLAS_DIRECTION", pd.DataFrame(dirs)),
                   ("ATLAS_WIDTH_DYNAMICS", pd.DataFrame(wdyn)), ("ATLAS_VELOCITY", pd.DataFrame(vel)), ("ATLAS_TIME_SEGMENTS", pd.DataFrame(segs)),
                   ("ATLAS_FAILURE_MAP", pd.DataFrame(fails)), ("ATLAS_TOP_HOLD_STUDY", pd.DataFrame(tops))):
        df.to_csv(os.path.join(OUT, f"{nm}.csv"), index=False)
    T = pd.DataFrame(trans); T.to_csv(os.path.join(B.BOX, "BOX_TRANSITION_MATRIX.csv"), index=False)
    pd.DataFrame(geoms).to_csv(os.path.join(B.BOX, "BOX_GEOMETRY_REGISTRY.csv"), index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
    cols = ["instrument", "geometry", "events", "events_per_day", "median_w_atr", "net_per_event", "excess_per_event", "net_day", "excess_day", "excess4_day",
            "top_before_break", "p_break", "folds_excess_pos", "score_fold_median_excess_day", "eligible"]
    print(A[cols].sort_values(["instrument", "score_fold_median_excess_day"], ascending=[True, False]).round(3).to_string())


if __name__ == "__main__":
    main()
