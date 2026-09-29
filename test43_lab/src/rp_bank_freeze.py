"""P1 freeze: horizons, Tier-A, feature dictionary, CANDIDATE_BANK.csv (prereg f7eff97)."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import master_state as MS, rp_state as R, rp_bank as B

rd = lambda p: pd.read_csv(os.path.join(MS.OUT, p))
SRC = {"C1_R1_TRAPPED_UNION": ("r1/RESERVE_R1_EVENTS.csv", ["R1_TRAPPED_UNION"]), "C2_P2_FAILED_FIRST": ("t103/TEST103_EVENTS.csv", ["P2_FAILED_FIRST"]),
       "C3_P1_H2": ("t103/TEST103_EVENTS.csv", ["P1_H2"]), "C4_L2_FAMILY": ("t104/TEST104_EVENTS.csv", [f"L2_{x}" for x in ("PDL", "PWL", "ORL", "SWL60", "L2H")]),
       "C5_HTF1_30m": ("t99/T99_EVENTS.csv", ["T99_HTF1_30m"]), "C6_AV_OR30": ("t101/TEST101_EVENTS.csv", ["AV_OR30"]),
       "C7_L1_SWH60": ("t104/TEST104_EVENTS.csv", ["L1_SWH60"]), "C8_CHOCH_15m": ("t109/TEST109_EVENTS.csv", ["CHOCH_15m"])}
rows = []
for c, (p, vs) in SRC.items():
    D = rd(p); Pd = D[(D.instrument == "POOLED") & D.variant.isin(vs)]; I = D[(D.instrument != "POOLED") & D.variant.isin(vs)]
    best = None; hz = {}
    for h in ("h12", "h24", "h1615"):
        w = Pd[f"{h}_n"].values; f = lambda k: float(np.average(Pd[k].values, weights=w))
        instx = I.groupby("instrument").apply(lambda g: np.average(g[f"{h}_xF"], weights=g[f"{h}_n"]))
        hz[h] = {"n": int(w.sum()), "mean": f(f"{h}_mean"), "xF": f(f"{h}_xF"), "years_pos_min": int(Pd[f"{h}_years_pos"].min()), "years_pos_max": int(Pd[f"{h}_years_pos"].max()),
                 "inst_pos": int((instx > 0).sum()), "cost": float(np.average(Pd.cost_atr, weights=w))}
        if hz[h]["xF"] > 0 and (best is None or hz[h]["mean"] > hz[best]["mean"]):
            best = h
    z = hz[best]; rep = c in ("C1_R1_TRAPPED_UNION", "C4_L2_FAMILY", "C2_P2_FAILED_FIRST")      # repeated related evidence (trapped-seller mechanism, 3 tests)
    ta = z["n"] >= 500 and z["xF"] > 0 and (z["years_pos_max"] >= 5 or rep) and (z["inst_pos"] >= 3) and z["mean"] >= 0.9 * z["cost"]
    rows.append({"candidate": c, "source_test": p.split("/")[0], "definition": "+".join(vs), "frozen_horizon": best, "n_events": z["n"], "role": "",
                 "tier_a": "YES" if ta else "NO", "note": json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in z.items()})})
roles = {"C1_R1_TRAPPED_UNION": "ML reclamation (trapped-seller union)", "C2_P2_FAILED_FIRST": "family ML + strategy economics", "C3_P1_H2": "comparison / pullback module",
         "C4_L2_FAMILY": "level-failure family ML (level type categorical)", "C5_HTF1_30m": "market-condition ML", "C6_AV_OR30": "AVWAP ML", "C7_L1_SWH60": "level break-retest ML",
         "C8_CHOCH_15m": "low priority"}
for r in rows:
    r["role"] = roles[r["candidate"]]
bank = pd.DataFrame(rows); bank = pd.concat([bank, pd.DataFrame([{"candidate": "REF_A2_ACD", "source_test": "t106", "definition": "A2_A_UP_IMMEDIATE", "frozen_horizon": "h12", "n_events": 3722, "role": "reference / duplicate control", "tier_a": "REFERENCE_ONLY"},
                                                             {"candidate": "REF_ORB15", "source_test": "t106", "definition": "ORB_COMPARATOR", "frozen_horizon": "h12", "n_events": 4724, "role": "reference", "tier_a": "REFERENCE_ONLY"}])])
for r in bank.to_dict("records"):
    R.append("CANDIDATE_BANK.csv", r)
bank.to_csv(os.path.join(R.OUT, "bank", "CANDIDATE_BANK_V1.csv"), index=False)
FD = {"tod": ("engine", "b/80", "bar b close", "none", "all"), "disp1": ("engine", "(c_b-c_{b-1})/ATR_d", "b", "ATR_d", "all"), "rng_atr5": ("engine", "range_b/ATR5", "b", "ATR5", "all"),
      "body_pct": ("engine", "(c-o)/range", "b", "ratio", "all"), "cpos": ("engine", "(c-l)/range", "b", "ratio", "all"), "disp6": ("P1", "(c_b-c_{b-6})/ATR_d", "b", "ATR_d", "pullback/level"),
      "disp12": ("P1", "(c_b-c_{b-12})/ATR_d", "b", "ATR_d", "all"), "rng12": ("P1", "12-bar high-low / ATR_d", "b", "ATR_d", "all"), "sess_ret": ("P1", "(c-open)/ATR_d", "b", "ATR_d", "all"),
      "sess_range": ("P1", "(hi-lo so far)/ATR_d", "b", "ATR_d", "all"), "dist_hi": ("P1", "(hi so far-c)/ATR_d", "b", "ATR_d", "all"), "dist_lo": ("P1", "(c-lo so far)/ATR_d", "b", "ATR_d", "trapped/level"),
      "or_pos": ("P1", "(c-ORL30)/(ORH30-ORL30), b>=6", "b", "ratio", "OR"), "gap": ("P1", "(open-prior 16:00 close)/ATR_d", "09:30", "ATR_d", "all"),
      "bars_since_low": ("P1", "(b - bar of session low)/80", "b", "ratio", "trapped (reclaim speed proxy)"), "vwap_dist": ("TEST100", "(c-VWAP)/ATR_d", "b", "ATR_d", "all"),
      "vwap_slope6": ("TEST100", "(VWAP_b-VWAP_{b-6})/ATR_d", "b", "ATR_d", "all"), "share_above_vwap12": ("TEST98 PQ5", "share of last 12 closes > VWAP", "b", "ratio", "all"),
      "up50": ("TEST115", "prior close > SMA50", "prior session", "binary", "HTF"), "adx14": ("TEST115", "Wilder ADX14 daily", "prior session", "raw", "HTF"),
      "di_up": ("TEST115", "+DI>-DI", "prior session", "binary", "HTF"), "stage_slope": ("TEST115", "(SMA150-SMA150[-20])/ATR_d", "prior session", "ATR_d", "HTF"),
      "tsmom12": ("TEST115", "12m return / annualised vol", "prior session", "z", "HTF"), "tsmom1": ("TEST115", "1m return / vol", "prior session", "z", "HTF"),
      "prev_ret": ("P1", "prior close-to-close / ATR_d", "prior session", "ATR_d", "all"), "vt": ("engine", "causal vol tercile", "prior session", "ordinal", "all"),
      "atr_ratio": ("TEST112", "mean range 5d / 60d", "prior session", "ratio", "all"), "atr5_rel": ("engine", "ATR5/ATR_d", "b", "ratio", "all")}
fd = pd.DataFrame([{"feature": k, "SOURCE": v[0], "DEFINITION": v[1], "AVAILABLE_AT": v[2], "NORMALIZATION": v[3], "FAMILY_RELEVANCE": v[4]} for k, v in FD.items()])
fd = pd.concat([fd, pd.DataFrame([{"feature": f"inst_{i}", "SOURCE": "identity", "DEFINITION": "one-hot instrument", "AVAILABLE_AT": "static", "NORMALIZATION": "binary", "FAMILY_RELEVANCE": "all"} for i in ("ES", "NQ", "YM", "RTY")]
                               + [{"feature": "constituent_*", "SOURCE": "identity", "DEFINITION": "one-hot constituent / level type (C1, C4 only)", "AVAILABLE_AT": "event", "NORMALIZATION": "binary", "FAMILY_RELEVANCE": "C1, C4"}])])
assert set(FD) == set(B.FEATS)
fd.to_csv(os.path.join(R.REP, "P1", "FEATURE_DICTIONARY.csv"), index=False)
print(bank[["candidate", "frozen_horizon", "n_events", "tier_a", "note"]].to_string()); print(len(fd), "feature rows")
