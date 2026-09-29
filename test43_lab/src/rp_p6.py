"""P6 consensus, matched-beta control, overfit diagnostics (prereg 2d5d88d)."""
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import mp_engine as P  # noqa: E402
import rp_econ as EC  # noqa: E402
import rp_ga as GA  # noqa: E402
import rp_ml as ML  # noqa: E402
import rp_state as R  # noqa: E402

OUT = os.path.join(R.OUT, "p6"); os.makedirs(OUT, exist_ok=True)
CANDS = ML.CANDS; GAF = ["C1_R1_TRAPPED_UNION", "C4_L2_FAMILY", "C7_L1_SWH60"]


def control_tables():
    M = P.markets(); T = {}
    for i in P.INSTS:
        m = M[i]; tod3 = np.digitize(m.bidx, [12, 54]); v = m.valid & (m.bidx <= 67)
        for h in ("h12", "h24", "h1615"):
            r = m.R[h]; ok = v & ~np.isnan(r)
            T[(i, h)] = pd.DataFrame({"y": m.year[ok], "vt": m.vt[ok], "t": tod3[ok], "r": r[ok]}).groupby(["y", "vt", "t"]).r.mean()
    return T


def add_control(D, h, T):
    tod3 = np.digitize(D.b.values, [12, 54]); ctl = np.empty(len(D))
    hs = D["hz"].values if "hz" in D else np.full(len(D), h)
    for k, (i, y, vt, t, hh) in enumerate(zip(D.inst.values, D.year.values, D.vt.values, tod3, hs)):
        ctl[k] = T[(i, hh)].get((y, vt, t), np.nan)
    D = D.copy(); D["ctl_usd"] = ctl * D.atr.values * D.pv.values - 2 * D.cs.values; return D


def ga_trades(E, cand, picks):
    gname, gvals = GA.spaces()[cand]; D = E[E.candidate == cand].reset_index(drop=True); Mk = GA.masks(D, gname, gvals); rows = []
    parse = lambda s: tuple(x.strip("' ") for x in s.strip("()").split(",") if x.strip("' ")) if gname == "group" else s
    for f, g in picks.items():
        if g is None:
            continue
        a, b = EC.FOLDS[f]; g0 = parse(g[0]); vt = g[2] if g[2] == "any" else int(g[2])
        m = Mk[("g", g0)] & Mk[("t", g[1])] & Mk[("v", vt)] & Mk[("w", g[3])] & (D.year.values >= a) & (D.year.values <= b) & D[f"usd_{g[4]}"].notna().values
        d = D[m].copy(); d["usd"] = d[f"usd_{g[4]}"]; d["usd4"] = d[f"usd4_{g[4]}"]; d["hz"] = g[4]; d["fold"] = f; rows.append(d)
    return pd.concat(rows), Mk, D, parse


def arm_d(E, cand, picks):
    """ML (K1 ridge top50) inside the GA-selected population, nested."""
    gname, gvals = GA.spaces()[cand]; D = E[E.candidate == cand].reset_index(drop=True); Mk = GA.masks(D, gname, gvals); X = ML.design(D); out = []
    parse = lambda s: tuple(x.strip("' ") for x in s.strip("()").split(",") if x.strip("' ")) if gname == "group" else s
    for f, ye in EC.TRAIN_END.items():
        g = picks[f]
        if g is None:
            continue
        a, b = EC.FOLDS[f]; vt = g[2] if g[2] == "any" else int(g[2]); h = g[4]
        m = Mk[("g", parse(g[0]))] & Mk[("t", g[1])] & Mk[("v", vt)] & Mk[("w", g[3])] & D[f"usd_{h}"].notna().values
        Dm = D[m].copy(); Dm["usd"] = Dm[f"usd_{h}"]; Dm["usd4"] = Dm[f"usd4_{h}"]; Dm["hz"] = h
        tr = Dm[Dm.year <= ye]; te = Dm[(Dm.year >= a) & (Dm.year <= b)]
        if len(tr) < 100 or not len(te):
            continue
        s, _, _ = ML.run_config("RIDGE", "T1", 0.5, tr, te, X); out.append(te[s])
    return pd.concat(out) if out else None


def series(T):
    c = EC.ctx(); return EC.daily(T.date.values, T.usd.values)[c["win"]]


def dsr(x, trials):
    sr = x.mean() / x.std(); srs = np.array([t.mean() / t.std() for t in trials if t.std() > 0]); N = len(trials); V = srs.var(ddof=1)
    g = 0.5772156649; sr0 = np.sqrt(V) * ((1 - g) * norm.ppf(1 - 1 / N) + g * norm.ppf(1 - 1 / (N * np.e)))
    Tn = len(x); den = np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2)
    return float(norm.cdf((sr - sr0) * np.sqrt(Tn - 1) / den)), float(sr), float(sr0)


def pbo(Mx, S=16):
    T = Mx.shape[1]; blocks = np.array_split(np.arange(T), S); lam = []
    for comb in itertools.combinations(range(S), S // 2):
        ins = np.concatenate([blocks[k] for k in comb]); oos = np.concatenate([blocks[k] for k in range(S) if k not in comb])
        sr_i = Mx[:, ins].mean(1) / (Mx[:, ins].std(1) + 1e-12); sr_o = Mx[:, oos].mean(1) / (Mx[:, oos].std(1) + 1e-12)
        best = np.argmax(sr_i); rk = (sr_o < sr_o[best]).sum() + 0.5 * ((sr_o == sr_o[best]).sum() - 1); w = (rk + 1) / (len(sr_o) + 1)
        lam.append(np.log(w / (1 - w)))
    return float(np.mean(np.array(lam) <= 0))


def reality_check(Mx, reps=2000, blk=10, seed=7):
    rng = np.random.default_rng(seed); T = Mx.shape[1]; stat = np.sqrt(T) * Mx.mean(1).max(); mu = Mx.mean(1, keepdims=True); cnt = 0
    for _ in range(reps):
        idx = np.empty(T, int); t = rng.integers(T)
        for k in range(T):
            idx[k] = t; t = rng.integers(T) if rng.random() < 1 / blk else (t + 1) % T
        cnt += np.sqrt(T) * (Mx[:, idx] - mu).mean(1).max() >= stat
    return float(cnt / reps)


def main():
    E = pd.read_parquet(os.path.join(R.OUT, "bank", "CANDIDATE_EVENTS.parquet")); T = control_tables(); G = pd.read_csv(os.path.join(R.OUT, "ga", "P5_GA_RESULTS.csv")).set_index("family")
    rows, diag = [], []
    for cand in CANDS + ["REF_A2_ACD", "REF_ORB15"]:
        D = E[(E.candidate == cand) & E.usd_h1615.notna()].copy(); D["usd"] = D.usd_h1615; D["usd4"] = D.usd4_h1615; D["hz"] = "h1615"; npop = int((D.year >= 2021).sum())
        arms = {"A_TAKE_ALL": D[D.year >= 2021]}
        if not cand.startswith("REF"):
            arms["B_ML_NESTED"] = pd.read_parquet(os.path.join(R.OUT, "ml", f"NESTED_TRADES_{cand}.parquet")).assign(hz="h1615")
        if cand in GAF:
            picks = {k: (v if v else None) for k, v in json.loads(G.loc[cand, "picks"]).items()}
            arms["C_GA"] = ga_trades(E, cand, picks)[0]; dd = arm_d(E, cand, picks)
            if dd is not None:
                arms["D_ML_IN_GA"] = dd
        res = {}
        for a, Tr in arms.items():
            Tr = add_control(Tr, "h1615", T); m = EC.metrics(Tr.date.values, Tr.usd.values, Tr.usd4.values, npop)
            ex = EC.metrics(Tr.date.values, (Tr.usd - Tr.ctl_usd).fillna(0).values, (Tr.usd4 - Tr.ctl_usd).fillna(0).values, npop)
            res[a] = {"family": cand, "arm": a, **m, "tier_b": EC.tier_b(m), "mb_excess_avg_day": ex["avg_day"], "mb_excess_2022": ex["y2022"], "mb_excess_folds_pos": ex["folds_pos"]}
            rows.append(res[a]); Tr.to_parquet(os.path.join(OUT, f"ARM_{cand}_{a}.parquet"))
        order = [a for a in ("A_TAKE_ALL", "C_GA", "B_ML_NESTED", "D_ML_IN_GA") if a in res and res[a]["tier_b"]]
        choice = None
        for a in order:
            if choice is None or res[choice]["avg_day"] < 0.9 * res[a]["avg_day"]:
                choice = a
        if choice:
            r = res[choice]; lab = "CONSENSUS_CANDIDATE" if r["mb_excess_avg_day"] > 0 else "BETA_CARRIER"
        else:
            lab = "NO_TIER_B_ARM"
        # overfit diagnostics (trial set = take-all + K1..K8)
        if not cand.startswith("REF"):
            trials = [series(arms["A_TAKE_ALL"])] + [series(pd.read_parquet(os.path.join(R.OUT, "ml", f"TRADES_{cand}_{k}.parquet"))) for k in ML.CONF]
            Mx = np.vstack(trials); ng = int(G.loc[cand, "n_genomes"]) if cand in GAF else 0
            try:
                x = series(add_control(arms[choice], "h1615", T)) if choice else trials[0]
                d_, sr, sr0 = dsr(x, trials + [np.zeros(1)] * 0) if True else (np.nan, np.nan, np.nan)
                N = len(trials) + ng
                srs = np.array([t.mean() / t.std() for t in trials]); V = srs.var(ddof=1); g = 0.5772156649
                sr0 = np.sqrt(V) * ((1 - g) * norm.ppf(1 - 1 / N) + g * norm.ppf(1 - 1 / (N * np.e)))
                den = np.sqrt(1 - skew(x) * sr + (kurtosis(x, fisher=False) - 1) / 4 * sr ** 2); d_ = float(norm.cdf((sr - sr0) * np.sqrt(len(x) - 1) / den))
                pb = pbo(Mx); rc = reality_check(Mx); stt = "COMPUTED"
            except Exception as e:  # noqa: BLE001
                d_ = pb = rc = np.nan; stt = f"OVERFIT_DIAGNOSTIC_NOT_COMPUTED ({e})"
            diag.append({"family": cand, "trials": len(trials) + ng, "chosen_arm": choice, "daily_sharpe": sr, "sr0": sr0, "dsr": d_, "pbo": pb, "reality_check_p": rc, "status": stt, "label": lab})
            R.append("OVERFIT_DIAGNOSTICS.csv", {"family": cand, "trials": len(trials) + ng, "dsr": round(d_, 4), "pbo": round(pb, 4), "reality_check_p": round(rc, 4), "status": stt})
        rows.append({"family": cand, "arm": "CONSENSUS", "choice": choice, "label": lab})
        print(cand, choice, lab, {a: (round(v["avg_day"], 2), round(v["mb_excess_avg_day"], 2), v["tier_b"]) for a, v in res.items()}, flush=True)
    Rr = pd.DataFrame(rows); Rr.to_csv(os.path.join(OUT, "P6_CONSENSUS.csv"), index=False); pd.DataFrame(diag).to_csv(os.path.join(OUT, "P6_OVERFIT.csv"), index=False)
    pd.set_option("display.width", 250); print(pd.DataFrame(diag).round(4).to_string())


if __name__ == "__main__":
    main()
