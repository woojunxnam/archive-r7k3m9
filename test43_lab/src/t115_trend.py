"""TEST115 HTF trend-strength / stage factory (prereg 28b77c2)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import master_state as S  # noqa: E402

OUT = os.path.join(S.OUT, "t115"); os.makedirs(OUT, exist_ok=True)


def wilder(x, n=14):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False).mean().values


def feats(m):
    I = m.I; H = np.nanmax(I.H, 1); L = np.nanmin(I.L, 1); C = I.FP[:, P.E.J15]
    pc = np.r_[np.nan, C[:-1]]; up = np.r_[np.nan, np.diff(H)]; dn = np.r_[np.nan, -np.diff(L)]
    pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.nanmax(np.stack([H - L, np.abs(H - pc), np.abs(L - pc)]), 0); atr = wilder(np.nan_to_num(tr))
    pdi = 100 * wilder(pdm) / atr; mdi = 100 * wilder(mdm) / atr; dx = 100 * np.abs(pdi - mdi) / np.maximum(pdi + mdi, 1e-9); adx = wilder(dx)
    s = pd.Series(C); sma150 = s.rolling(150).mean(); sma50 = s.rolling(50).mean(); r = s.pct_change()
    f = pd.DataFrame({"T1_ADX": np.where(pdi > mdi, adx, np.nan), "T2_STAGE_SLOPE": np.where(C > sma150, (sma150 - sma150.shift(20)) / m.a, np.nan),
                      "T3_TSMOM_12M": (s / s.shift(252) - 1) / (r.rolling(252).std() * np.sqrt(252)),
                      "T4_TSMOM_1M": (s / s.shift(21) - 1) / (r.rolling(63).std() * np.sqrt(21)), "UP50": (C > sma50).astype(int)})
    return f.shift(1)          # known before session d


def main():
    M = P.markets(); recs = []
    for i in P.INSTS:
        m = M[i]; I = m.I; f = feats(m); ent = I.FP[:, 0]
        d = pd.DataFrame({"inst": i, "sidx": np.arange(m.n), "date": np.asarray(I.sess.values, "datetime64[D]").astype(np.int64), "year": I.year, "vt": I.vt,
                          "R1615": (I.FP[:, P.E.J15] - ent) / m.a, "R1600": (I.FP[:, P.E.J16] - ent) / m.a, "cost": m.cost, "ok": m.full & (m.a > 0)})
        d = pd.concat([d, f.reset_index(drop=True)], axis=1); d = d[d.ok & d.UP50.notna()]
        per = pd.DatetimeIndex(I.sess).to_period("M")[d.sidx.values]
        for k in ("T1_ADX", "T2_STAGE_SLOPE", "T3_TSMOM_12M", "T4_TSMOM_1M"):
            q = np.full(len(d), -1); x = d[k].values; si = d.sidx.values
            for mo in pd.unique(per):
                rows = np.where(per == mo)[0]; s0 = si[rows[0]]
                if s0 < 120:
                    continue
                v = x[si < s0]; v = v[~np.isnan(v)]
                if len(v) < 50:
                    continue
                e = np.percentile(v, [20, 40, 60, 80]); q[rows] = np.where(np.isnan(x[rows]), -1, np.digitize(np.nan_to_num(x[rows]), e))
            d[f"q_{k}"] = q
        for h in ("R1615", "R1600"):
            d[f"N{h}"] = d.groupby(["year", "vt", "UP50"])[h].transform("mean")
        recs.append(d)
    D = pd.concat(recs, ignore_index=True); coh, cur = [], []
    for k in ("T1_ADX", "T2_STAGE_SLOPE", "T3_TSMOM_12M", "T4_TSMOM_1M"):
        for h in ("R1615", "R1600"):
            e = D[(D[f"q_{k}"] >= 0) & D[h].notna() & D[f"N{h}"].notna()]; x = (e[h] - e[f"N{h}"]).values; b = e[f"q_{k}"].values
            bm = [float(x[b == j].mean()) for j in range(5)]; raw = [float(e[h].values[b == j].mean()) for j in range(5)]
            for j in range(5):
                cur.append({"feature": k, "horizon": h, "bin": j, "n": int((b == j).sum()), "xN": bm[j], "raw_mean": raw[j]})
            rho = float(spearmanr(range(5), bm)[0]); sel = (b == 0) | (b == 4); lo, hi = P.boot_diff(x[sel], (b[sel] == 4), e.date.values[sel]); dd = bm[4] - bm[0]
            ys = [np.sign(x[(e.year.values == y) & (b == 4)].mean() - x[(e.year.values == y) & (b == 0)].mean()) for y in np.unique(e.year)]
            ins = [np.sign(x[(e.inst.values == y) & (b == 4)].mean() - x[(e.inst.values == y) & (b == 0)].mean()) for y in P.INSTS]
            c = abs(rho) >= 0.9 and (lo > 0 or hi < 0) and sum(s == np.sign(dd) for s in ys) >= 5 and sum(s == np.sign(dd) for s in ins) >= 3
            bb = int(np.argmax(bm)); val = c and bm[bb] > 0 and raw[bb] > e.cost.mean()
            coh.append({"feature": k, "horizon": h, "spearman": rho, "top_minus_bottom": dd, "ci_lo": lo, "ci_hi": hi, "years_same_sign": int(sum(s == np.sign(dd) for s in ys)),
                        "inst_same_sign": int(sum(s == np.sign(dd) for s in ins)), "COHERENT": bool(c), "STRENGTH_ADDS_VALUE": bool(val), "bins": str([round(v, 4) for v in bm])})
    Cc = pd.DataFrame(coh); Cu = pd.DataFrame(cur); Cc.to_csv(os.path.join(OUT, "TEST115_COHERENCE.csv"), index=False); Cu.to_csv(os.path.join(OUT, "TEST115_CURVES.csv"), index=False)
    pd.set_option("display.width", 250); print(Cc.round(4).to_string())
    json.dump({"ledger_rows": len(Cu), "definitions_new": 4, "value": Cc.STRENGTH_ADDS_VALUE.tolist()}, open(os.path.join(OUT, "T115_META.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
