"""TEST84 VOLUME DATA / PROFILE APPROXIMATION QA: volume coverage, zero / missing bars, rolls, abnormal days, time-of-day curve, yearly
normalisation; proxy agreement; PREFIX INVARIANCE of every profile feature (fail closed); builds the base profile feature cache."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import ap_common as A  # noqa: E402
import box_common as B  # noqa: E402

OUT = os.path.join(A.AP, "TEST84"); CACHE = os.path.join(A.AP, "cache"); os.makedirs(CACHE, exist_ok=True)
BASE = {"f_bin": 0.02, "pct": 0.70}


def features(I, proxy, f_bin=0.02, pct=0.70):
    p = os.path.join(CACHE, f"F_{I.name}_{proxy}_{f_bin}_{pct}.npz")
    if os.path.exists(p):
        z = np.load(p); return z["P1"], z["F"]
    P1, F = A.session_features(I.H, I.L, I.C, I.V.astype(float), I.atr, f_bin, A.PROXY[proxy], pct, A.J15)
    np.savez_compressed(p, P1=P1, F=F); return P1, F


def volume_qa(I, raw):
    full = I.full; V = I.V[full]; px = ~np.isnan(np.where(I.full[:, None], I.C, np.nan))[full]
    dv = V.sum(1); med = pd.Series(dv).rolling(20, min_periods=10).median().shift(1).values
    abn = (dv > 5 * med) | (dv < 0.2 * med)
    r = raw[(raw.session_date >= "2019-07-01") & (raw.session_date <= "2026-05-27")]
    rolls = r.groupby("session_date").contract.nunique(); roll_s = set(rolls[rolls > 1].index) | set(r[r.roll_adjacent.fillna(False).astype(bool)].session_date.unique())
    sess = I.sess[full]; is_roll = np.array([d in roll_s for d in sess])
    tod = V.reshape(len(V), A.NB5, 5).sum(2) if V.shape[1] >= 405 else None
    share = (tod / np.maximum(tod.sum(1, keepdims=True), 1)).mean(0)
    yr = pd.Series(dv, index=sess).groupby(sess.year).median()
    return {"instrument": I.name, "sessions": int(full.sum()), "rth_minutes": int(V.size), "zero_volume_share": float((V == 0).mean()),
            "missing_price_share": float(1 - px.mean()), "sessions_with_any_zero_bar_share": float((V == 0).any(1).mean()),
            "abnormal_volume_days": int(abn.sum()), "roll_sessions": int(is_roll.sum()),
            "roll_vs_nonroll_volume_ratio": float(np.median(dv[is_roll]) / np.median(dv[~is_roll])) if is_roll.any() else np.nan,
            "median_daily_rth_volume_by_year": {int(k): int(v) for k, v in yr.items()}, "open_5m_share": float(share[0]), "close_5m_share": float(share[-1]),
            "midday_min_5m_share": float(share.min()), "tod_curve": [round(float(x), 4) for x in share]}


def prefix_test(I, proxy, P1, F, rng, k=300):
    bad = 0; checked = 0
    ss = rng.choice(np.where(I.full)[0][1:], k)
    for s in ss:
        b = int(rng.integers(1, A.NB5 - 1)); j = 5 * b + 4
        H, L, C, V = (I.H[s - 1:s + 1].copy(), I.L[s - 1:s + 1].copy(), I.C[s - 1:s + 1].copy(), I.V[s - 1:s + 1].astype(float).copy())
        g = rng.normal(0, 50, H[1, j + 1:].shape)
        H[1, j + 1:] += 100 + g; L[1, j + 1:] -= 100 - g; C[1, j + 1:] += g; V[1, j + 1:] = rng.integers(1, 10 ** 6, V[1, j + 1:].shape)
        P1x, Fx = A.session_features(H, L, C, V, I.atr[s - 1:s + 1].copy(), BASE["f_bin"], A.PROXY[proxy], BASE["pct"], A.J15)
        a1, a2 = Fx[1, :b + 1], F[s, :b + 1]
        same = np.allclose(np.nan_to_num(a1, nan=-7), np.nan_to_num(a2, nan=-7)) and np.allclose(np.nan_to_num(P1x[1], nan=-7), np.nan_to_num(P1[s], nan=-7))
        bad += int(not same); checked += 1
    return checked, bad


def main():
    Is = B.load(); rows = []; pref = []; agree = []
    rng = np.random.default_rng(5)
    for inst, I in Is.items():
        raw = pd.read_parquet(os.path.join(B.LAB, "data", f"canonical_1m_{inst}.parquet"), columns=["session_date", "contract", "roll_adjacent"])
        raw["session_date"] = pd.to_datetime(raw.session_date)
        q = volume_qa(I, raw); q["signal_volume_source"] = "ES full contract" if inst == "ES" else "MNQ micro (PROXY for NQ; full NQ not in data set)"; rows.append(q)
        Fs = {}
        for px in A.PROXY:
            P1, F = features(I, px); Fs[px] = F
            c, bd = prefix_test(I, px, P1, F, rng); pref.append({"instrument": inst, "proxy": px, "checked": c, "mismatches": bd})
        a = I.atr[:, None]
        for f in ("P2_POC", "P4_POC", "P2_VAH", "P2_VAL"):
            k = A.FEAT[f]
            for p1, p2 in (("VP-A", "VP-B"), ("VP-A", "VP-C"), ("VP-B", "VP-C")):
                x, y = Fs[p1][..., k], Fs[p2][..., k]; m = ~np.isnan(x) & ~np.isnan(y)
                agree.append({"instrument": inst, "feature": f, "pair": f"{p1}/{p2}", "corr_of_30m_change": float(np.corrcoef((x[:, 6:] - x[:, :-6])[m[:, 6:] & m[:, :-6]],
                                                                                                                   (y[:, 6:] - y[:, :-6])[m[:, 6:] & m[:, :-6]])[0, 1]),
                              "median_abs_diff_ATR": float(np.nanmedian(np.abs(x - y) / a)), "same_bin_share": float(np.mean(np.abs(x - y)[m] < 1e-9))})
        print(inst, "done", flush=True)
    Q = pd.DataFrame(rows); PF = pd.DataFrame(pref); AG = pd.DataFrame(agree)
    Q.to_json(os.path.join(OUT, "TEST84_VOLUME_QA.json"), orient="records", indent=1); PF.to_csv(os.path.join(OUT, "TEST84_PREFIX_INVARIANCE.csv"), index=False)
    AG.to_csv(os.path.join(OUT, "TEST84_PROXY_AGREEMENT.csv"), index=False)
    ok = int(PF.mismatches.sum()) == 0
    print(Q.drop(columns=["tod_curve"]).T.to_string()); print(PF.to_string()); print(AG.round(3).to_string()); print("PREFIX_INVARIANT", ok)
    A.budget("TEST84", note="data / approximation QA (no hypotheses)")
    A.md("TEST84_VOLUME_PROFILE_QA.md", "TEST84 - volume data / profile approximation QA",
         ["1m OHLCV only: every profile is an APPROXIMATION (VP-A single price, VP-B uniform range, VP-C centre-weighted). NQ signal = MNQ volume proxy.",
          Q.drop(columns=["tod_curve"]).T, PF, AG.round(3), f"PREFIX_INVARIANT = {ok}"])
    if not ok:
        raise SystemExit("PREFIX INVARIANCE FAILED - fail closed")


if __name__ == "__main__":
    main()
