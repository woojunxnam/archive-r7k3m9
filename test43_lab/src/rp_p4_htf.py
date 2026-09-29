"""P4 event-conditioned HTF regime (prereg ebfe9b0)."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(__file__))
import rp_state as R, mp_engine as P

OUT = os.path.join(R.OUT, "p4"); os.makedirs(OUT, exist_ok=True)


def causal_q(D, x, q):
    per = pd.to_datetime(D.date, unit="D").dt.to_period("M").values; out = np.full(len(D), -1); order = np.argsort(D.date.values, kind="stable")
    d0 = D.date.min()
    for mo in np.unique(per):
        rows = np.where(per == mo)[0]; start = D.date.values[rows].min()
        prior = x[(D.date.values < start)]; prior = prior[~np.isnan(prior)]
        if start - d0 < 170 or len(prior) < 50:     # ~120 sessions warm-up
            continue
        e = np.percentile(prior, np.linspace(0, 100, q + 1)[1:-1]); out[rows] = np.where(np.isnan(x[rows]), -1, np.digitize(np.nan_to_num(x[rows]), e))
    return out


def main():
    E = pd.read_parquet(os.path.join(R.OUT, "bank", "CANDIDATE_EVENTS.parquet")); rows, cur = [], []
    for cand in ("C1_R1_TRAPPED_UNION", "C2_P2_FAILED_FIRST", "C5_HTF1_30m"):
        D = E[(E.candidate == cand) & E.net_h1615.notna()].reset_index(drop=True); y = D.net_h1615.values
        tod3 = np.digitize(D.b.values, [12, 54]); dt = causal_q(D, D.disp6.values.astype(float), 3); up = D.up50.fillna(-1).values.astype(int)
        nul = np.full(len(D), np.nan)
        for cell in ([D.year.values, D.vt.values, tod3, dt, up], [D.vt.values, tod3, dt, up], [tod3, dt, up]):
            key = pd.Series(list(zip(*cell))).astype(str).values; ok = dt >= 0
            g = pd.DataFrame({"k": key[ok], "y": y[ok]}).groupby("k").y.agg(["sum", "count"])
            s = g["sum"].reindex(key).values; c = g["count"].reindex(key).values
            loo = (s - y) / (c - 1); good = ok & (c - 1 >= 10) & np.isnan(nul); nul[good] = loo[good]
        x = y - nul
        for f in ("adx14", "stage_slope", "tsmom1", "tsmom12"):
            b = causal_q(D, D[f].values.astype(float), 5); m = (b >= 0) & ~np.isnan(x)
            bm = [float(x[m & (b == k)].mean()) if (m & (b == k)).any() else np.nan for k in range(5)]
            for k in range(5):
                cur.append({"population": cand, "feature": f, "bin": k, "n": int((m & (b == k)).sum()), "x": bm[k]})
            okb = [k for k in range(5) if bm[k] == bm[k]]; rho = float(spearmanr(okb, [bm[k] for k in okb])[0]) if len(okb) >= 3 else np.nan
            sel = m & ((b == 0) | (b == 4)); lo, hi = P.boot_diff(x[sel], (b[sel] == 4), D.date.values[sel]); dd = bm[4] - bm[0]
            ys = [np.sign(np.nanmean(x[m & (b == 4) & (D.year.values == yy)]) - np.nanmean(x[m & (b == 0) & (D.year.values == yy)])) for yy in np.unique(D.year)]
            ins = [np.sign(np.nanmean(x[m & (b == 4) & (D.inst.values == ii)]) - np.nanmean(x[m & (b == 0) & (D.inst.values == ii)])) for ii in ("ES", "NQ", "YM", "RTY")]
            coh = abs(rho) >= 0.9 and (lo > 0 or hi < 0) and sum(s_ == np.sign(dd) for s_ in ys) >= 5 and sum(s_ == np.sign(dd) for s_ in ins) >= 3
            rows.append({"population": cand, "feature": f, "n": int(m.sum()), "spearman": rho, "top_minus_bottom": dd, "ci_lo": lo, "ci_hi": hi,
                         "years_same_sign": int(sum(s_ == np.sign(dd) for s_ in ys)), "inst_same_sign": int(sum(s_ == np.sign(dd) for s_ in ins)),
                         "COHERENT": bool(coh), "VALUE": bool(coh and np.nanmax(bm) > 0), "bins": str([round(v, 4) for v in bm])})
    Rr = pd.DataFrame(rows); Rr.to_csv(os.path.join(OUT, "P4_COHERENCE.csv"), index=False); pd.DataFrame(cur).to_csv(os.path.join(OUT, "P4_CURVES.csv"), index=False)
    pd.set_option("display.width", 250); print(Rr.round(4).to_string())


if __name__ == "__main__":
    main()
