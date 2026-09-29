"""MASTER program event-study engine (ESP-1): TEST97 5m engine + h24 horizon, causal family-null cells, clustered CIs, ESP-1 classification."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E  # noqa: E402
import master_state as S  # noqa: E402

INSTS = E.INSTS; NB = E.NB; BMAX = E.BMAX_COMMON; WARM = 120; REPS = 2000
HZ = ["h6", "h12", "h24", "h1615"]
LEDGER = os.path.join(S.OUT, "MASTER_RESEARCH_LEDGER.csv")


def markets():
    M = E.markets()
    for m in M.values():
        if "h24" not in m.R:
            I = m.I; ex = np.full((m.n, NB), np.nan); jj = 5 * (np.arange(NB) + 1 + 24); ok = jj <= E.J15
            ex[:, ok] = I.FP[:, jj[ok]]; m.R["h24"] = (ex - m.entry) / m.a[:, None]
            m.tod3 = np.digitize(m.bidx, [12, 54]); m.s21 = m.year >= 2021
    return M


def causal_bins(m, pop, x, q):
    """quantile bins; edges from pop bars in sessions strictly before the month (monthly expanding); warm-up / missing -> -1."""
    per = m.I.sess.to_period("M"); out = np.full(x.shape, -1)
    for mo in per.unique():
        rows = np.where(per == mo)[0]
        if rows[0] < WARM:
            continue
        v = x[:rows[0]][pop[:rows[0]]]; v = v[~np.isnan(v)]
        if len(v) < 50:
            continue
        edges = np.percentile(v, np.linspace(0, 100, q + 1)[1:-1]); sub = x[rows]
        out[rows] = np.where(np.isnan(sub), -1, np.digitize(np.nan_to_num(sub), edges))
    return out


def cell_null(m, ev, pop, key, bins, minn=10):
    """null value per bar = mean fwd return of NON-event pop bars in the same cell; cells = year x vt x tod3 x bins, fallback drop year, then vt."""
    r = m.R[key]; okb = np.all([b >= 0 for b in bins], 0) if bins else np.ones(r.shape, bool)
    z = 0
    for b in bins:
        z = z * 10 + b
    levels = [((m.year * 10 + m.vt) * 10 + m.tod3) * 10 ** 6 + z, (m.vt * 10 + m.tod3) * 10 ** 6 + z, m.tod3 * 10 ** 6 + z]
    pool = pop & ~ev & m.valid & ~np.isnan(r) & okb; tgt = ev & okb
    null = np.full(r.shape, np.nan); lev = np.full(r.shape, -1)
    for li, cell in enumerate(levels):
        s = pd.Series(r[pool]).groupby(cell[pool]).agg(["sum", "count"]); s = s[s["count"] >= minn]
        mv = (s["sum"] / s["count"]).reindex(cell[tgt]).values
        cur = null[tgt]; cl = lev[tgt]; g = np.isnan(cur) & ~np.isnan(mv); cur[g] = mv[g]; cl[g] = li; null[tgt] = cur; lev[tgt] = cl
    return null, lev


def boot(v, cl, reps=REPS, seed=7):
    ok = ~np.isnan(v); v, cl = v[ok], cl[ok]
    if len(v) < 20:
        return np.nan, np.nan
    u, inv = np.unique(cl, return_inverse=True); s = np.bincount(inv, v); c = np.bincount(inv)
    rng = np.random.default_rng(seed); out = np.empty(reps)
    for i in range(reps):
        k = rng.integers(0, len(u), len(u)); out[i] = s[k].sum() / c[k].sum()
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def evaluate(name, evs, nullf, horizons=HZ, primary=("h12", "h24", "h1615"), meta=None):
    """evs: {inst: mask}; nullf(m, inst, ev, key) -> (null, level).  Returns rows (per inst + POOLED) with ESP-1 fields."""
    M = markets(); rows = []; pool = {k: dict(x=[], cl=[], yr=[], r=[], xa=[], xc=[], lev=[], s21=[]) for k in horizons}
    for inst, ev0 in evs.items():
        m = M[inst]; ev = ev0 & m.valid & (m.bidx <= BMAX)
        o = {"variant": name, "instrument": inst, "n_events": int(ev.sum())}
        for key in horizons:
            r = m.R[key]; nl, lv = nullf(m, inst, ev, key); x = (r - nl)[ev]; rr = r[ev]
            xa = (r[ev] - m.null("A", key, ev)); xc = (r[ev] - m.null("C", key, ev))
            o[f"{key}_n"] = int((~np.isnan(rr)).sum()); o[f"{key}_mean"] = float(np.nanmean(rr)) if o[f"{key}_n"] else np.nan
            o[f"{key}_median"] = float(np.nanmedian(rr)) if o[f"{key}_n"] else np.nan; o[f"{key}_ppos"] = float(np.nanmean(rr[~np.isnan(rr)] > 0)) if o[f"{key}_n"] else np.nan
            o[f"{key}_xF"] = float(np.nanmean(x)); o[f"{key}_xA"] = float(np.nanmean(xa)); o[f"{key}_xC"] = float(np.nanmean(xc))
            d = pool[key]; d["x"].append(x); d["cl"].append(m.date[ev]); d["yr"].append(m.year[ev]); d["r"].append(rr); d["xa"].append(xa); d["xc"].append(xc)
            d["lev"].append(lv[ev]); d["s21"].append(m.s21[ev])
        o["cost_atr"] = float(np.nanmean(np.repeat(m.cost[:, None], NB, 1)[ev])) if ev.any() else np.nan
        for k in ("mfe60", "mae60", "t_mfe", "newhigh60", "bar050", "underwater_1615", "t_recover"):
            o[k] = float(np.nanmean(m.P[k][ev])) if ev.any() else np.nan
        rows.append(o)
    P = {"variant": name, "instrument": "POOLED", "n_events": sum(r["n_events"] for r in rows), "cost_atr": float(np.nanmean([r["cost_atr"] for r in rows]))}
    for key in horizons:
        d = {k: np.concatenate(v) for k, v in pool[key].items()}
        P[f"{key}_n"] = int((~np.isnan(d["x"])).sum()); P[f"{key}_mean"] = float(np.nanmean(d["r"])); P[f"{key}_xF"] = float(np.nanmean(d["x"]))
        P[f"{key}_xF_lo"], P[f"{key}_xF_hi"] = boot(d["x"], d["cl"])
        by = pd.Series(d["x"]).groupby(d["yr"]).mean(); P[f"{key}_years_pos"] = int((by > 0).sum()); P[f"{key}_years"] = int(by.notna().sum())
        P[f"{key}_x2022"] = float(by.get(2022, np.nan)); P[f"{key}_xF_2021"] = float(np.nanmean(d["x"][d["s21"]]))
        P[f"{key}_xA"] = float(np.nanmean(d["xa"])); P[f"{key}_xC"] = float(np.nanmean(d["xc"]))
        P[f"{key}_inst_pos"] = int(sum(r[f"{key}_xF"] > 0 for r in rows))
        lv = d["lev"][~np.isnan(d["x"])]; P[f"{key}_fallback"] = "/".join(f"{np.mean(lv == i):.2f}" for i in range(3))
        P[f"{key}_null_missing"] = float(np.mean(np.isnan(d["x"])))
    rows.append(P)
    for key in primary:
        P[f"{key}_class"] = classify(P, key)
    for r in rows:
        r.update(meta or {})
    return rows


def classify(P, key, adjacent_ok=None):
    ev = P.get(f"{key}_xF_lo", np.nan) > 0 and P[f"{key}_years_pos"] >= 5 and P[f"{key}_inst_pos"] >= 3 and P[f"{key}_mean"] > P["cost_atr"]
    if ev:
        strong = P[f"{key}_xC"] > 0 and P[f"{key}_xF_2021"] > 0 and (adjacent_ok is None or adjacent_ok)
        return "STRONG_CLUE" if (strong and adjacent_ok) else "EVENT_CLUE"
    if P[f"{key}_xF"] > 0 and P[f"{key}_years_pos"] >= 5:
        return "WEAK_RESEARCH_CLUE_ONLY"
    return "REJECT"


def ledger(rows, test, family, note=""):
    recs = []
    for r in rows:
        for key in HZ:
            if f"{key}_xF" in r:
                recs.append({"test": test, "family": family, "variant": r["variant"], "instrument": r["instrument"], "horizon": key, "n": r.get(f"{key}_n"),
                             "mean": r.get(f"{key}_mean"), "xF": r.get(f"{key}_xF"), "xF_lo": r.get(f"{key}_xF_lo", ""), "xA": r.get(f"{key}_xA"),
                             "xC": r.get(f"{key}_xC"), "class": r.get(f"{key}_class", ""), "note": note})
    df = pd.DataFrame(recs); df.to_csv(LEDGER, mode="a", header=not os.path.exists(LEDGER), index=False)
    return len(df)


def md(path, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".4f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(path, "w").write("\n".join(lines) + "\n")


def run_family(test, family, evsets, nullf, adj, primary=("h12", "h24", "h1615"), outdir=None, horizons=HZ):
    """evaluate every definition, classify with adjacency (same sign, >= 50% magnitude of an adjacent definition), write ledger + csvs."""
    R = []; pooled = {}
    for name, evs in evsets.items():
        rows = evaluate(name, evs, nullf, horizons=horizons, primary=primary, meta={"family": family}); R.extend(rows); pooled[name] = rows[-1]
        print(name, rows[-1]["n_events"], {k: round(rows[-1][f"{k}_xF"], 4) for k in horizons}, flush=True)
    fin = []
    for name, r in pooled.items():
        for key in primary:
            x = r[f"{key}_xF"]
            aok = any(np.sign(pooled[a][f"{key}_xF"]) == np.sign(x) and abs(pooled[a][f"{key}_xF"]) >= 0.5 * abs(x) for a in adj.get(name, []))
            fin.append({"variant": name, "horizon": key, "n": r[f"{key}_n"], "mean": r[f"{key}_mean"], "cost_atr": r["cost_atr"], "xF": x,
                        "xF_lo": r[f"{key}_xF_lo"], "xF_hi": r[f"{key}_xF_hi"], "years_pos": r[f"{key}_years_pos"], "inst_pos": r[f"{key}_inst_pos"],
                        "xF_2021": r[f"{key}_xF_2021"], "x2022": r[f"{key}_x2022"], "xA": r[f"{key}_xA"], "xC": r[f"{key}_xC"], "adjacent_ok": aok,
                        "fallback": r[f"{key}_fallback"], "class": classify(r, key, adjacent_ok=aok)})
    D = pd.DataFrame(R); F = pd.DataFrame(fin)
    if outdir:
        os.makedirs(outdir, exist_ok=True); D.to_csv(os.path.join(outdir, f"{test}_EVENTS.csv"), index=False); F.to_csv(os.path.join(outdir, f"{test}_CLASSIFICATION.csv"), index=False)
    n = ledger(R, test, family, "PHASE1")
    return D, F, n
