"""RUN-4 Sleeve B event study (before any strategy conversion).
For every event (B1-B12, 167 definitions) and the all-bars baseline: count, events/day, forward returns, MFE/MAE,
P(+U before -D) with entry at next open + 1 tick and target fill needing 1-tick penetration (same-bar ambiguity =
LOSS), time to MFE / target, splits 2019-21 / 2022 / 2023+ and per year, cost-aware EV proxies.
Output: SLEEVE_B_EVENTS.parquet (+ csv copy) and data/cache/r4_b_events.npz (event index arrays).
ES-signal / MES-economics proxy (in-sample, not OOS)."""
import os, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.momentum import build_events
from mesgrid import fastsim as fs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = [(1.0, 1.0), (2.0, 2.0), (3.0, 2.0), (3.0, 3.0), (5.0, 3.0), (5.0, 5.0)]
HOR = np.array([1, 2, 3, 5, 10, 15, 30, 60], dtype=np.int64)
COMM_PT = 2 * 0.62 / 5.0          # round-trip commission in points
SLIP_PT = 0.25


def summarize(name, idx, b, nxt, dtm, years, meta):
    ups = np.array([u for u, d in PAIRS]); dns = np.array([d for u, d in PAIRS])
    wins, rets, mfe, mae, tm, tt = fs.bracket_outcomes(idx, b.o, b.h, b.l, b.c, nxt, dtm, ups, dns, HOR, 30, 2.0, 1, 1)
    ok = ~np.isnan(mfe)
    r = dict(event=name, **{k: (v if not isinstance(v, (list, tuple)) else str(v)) for k, v in meta.items()})
    r["n"] = int(ok.sum())
    nd = len(np.unique(b.day[b.tradeable]))
    r["per_day"] = r["n"] / nd
    yv = years[idx]
    for p, (u, d) in enumerate(PAIRS):
        w = wins[ok, p]
        pw = np.nanmean(w) if np.isfinite(w).any() else np.nan
        r[f"p_{u:g}_{d:g}"] = pw
        r[f"ev_{u:g}_{d:g}"] = pw * u - (1 - pw) * (d + SLIP_PT) - COMM_PT if np.isfinite(pw) else np.nan
        r[f"unres_{u:g}_{d:g}"] = float(np.mean(np.isnan(w))) if len(w) else np.nan
    for h, hh in enumerate(HOR):
        x = rets[ok, h]
        r[f"ret{hh}"] = np.nanmean(x)
        r[f"evt{hh}"] = np.nanmean(x) - 2 * SLIP_PT - COMM_PT      # time exit: market in and out
    r["mfe30"] = np.nanmean(mfe[ok]); r["mae30"] = np.nanmean(mae[ok])
    r["t_mfe_med"] = np.nanmedian(tm[ok]); r["t_target2_med"] = np.nanmedian(tt[ok]); r["p_target2"] = float(np.mean(np.isfinite(tt[ok])))
    for sk, (y0, y1) in {"s19_21": (2019, 2021), "s22": (2022, 2022), "s23p": (2023, 2026)}.items():
        m = ok & (yv >= y0) & (yv <= y1)
        r[f"{sk}_n"] = int(m.sum())
        r[f"{sk}_p2_2"] = np.nanmean(wins[m, 1]) if m.any() else np.nan
        r[f"{sk}_ret10"] = np.nanmean(rets[m, 4]) if m.any() else np.nan
    for y in range(2019, 2027):
        m = ok & (yv == y)
        r[f"y{y}_n"] = int(m.sum())
        r[f"y{y}_ret10"] = np.nanmean(rets[m, 4]) if m.any() else np.nan
        r[f"y{y}_p2_2"] = np.nanmean(wins[m, 1]) if m.any() else np.nan
    return r


if __name__ == "__main__":
    t0 = time.time()
    b = load_canonical()
    F = compute_features(b, b.v)
    ev, meta, M = build_events(b, F)
    nxt, last_td, nil, dtm = fs.day_structure(b)
    years = (b.day // 10000).astype(np.int64)
    # keep only events on bars whose next bar is tradeable in the same day and is not the last bar of the day
    ok_dec = nxt & ~nil & b.tradeable
    for k in list(ev):
        ev[k] = ev[k][ok_dec[ev[k]]]
    np.savez_compressed(os.path.join(ROOT, "data", "cache", "r4_b_events.npz"), **ev)
    json.dump(meta, open(os.path.join(ROOT, "data", "cache", "r4_b_events_meta.json"), "w"), default=str)
    rows = [summarize("BASELINE_all_bars", np.flatnonzero(ok_dec), b, nxt, dtm, years, dict(family="BASE"))]
    base = rows[0]
    for k in ev:
        rows.append(summarize(k, ev[k], b, nxt, dtm, years, meta[k]))
    df = pd.DataFrame(rows)
    for (u, d) in PAIRS:
        df[f"lift_p_{u:g}_{d:g}"] = df[f"p_{u:g}_{d:g}"] - base[f"p_{u:g}_{d:g}"]
    for hh in HOR:
        df[f"lift_ret{hh}"] = df[f"ret{hh}"] - base[f"ret{hh}"]
    yr_cols = [f"y{y}_ret10" for y in range(2019, 2027)]
    df["years_pos_ret10"] = (df[yr_cols] > 0).sum(axis=1)
    df["years_pos_lift_ret10"] = (df[yr_cols].values > np.array([base[c] for c in yr_cols])[None, :]).sum(axis=1)
    df["best_ev_bracket"] = df[[f"ev_{u:g}_{d:g}" for u, d in PAIRS]].max(axis=1)
    df["best_ev_time"] = df[[f"evt{h}" for h in HOR]].max(axis=1)
    df.to_parquet(os.path.join(ROOT, "SLEEVE_B_EVENTS.parquet"), index=False)
    df.to_csv(os.path.join(ROOT, "results", "RUN4_OVERNIGHT", "sleeve_b_events.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    cols = ["event", "n", "per_day", "p_1_1", "p_2_2", "p_3_2", "p_5_5", "ret5", "ret10", "ret30", "evt10", "ev_2_2", "ev_3_2",
            "best_ev_bracket", "best_ev_time", "years_pos_lift_ret10", "s19_21_ret10", "s22_ret10", "s23p_ret10"]
    print(df[cols].sort_values("best_ev_bracket", ascending=False).round(3).to_string(index=False))
    print("total", round(time.time() - t0), "s")
