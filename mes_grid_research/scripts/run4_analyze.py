"""RUN-4 aggregation: SLEEVE_A_RESULTS.csv, SLEEVE_B_RESULTS.csv, PARETO_A.csv, PARETO_B.csv, MODULE_LEADERBOARD.csv
(RUN-4 section), unique-config counts. No composite score: Pareto = non-dominated sets on the requested axes."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import run4_lib as L

ROOT = L.ROOT


def pareto(df, axes):
    """axes: list of (col, 'max'|'min'); returns boolean mask of non-dominated rows (NaN rows excluded)."""
    X = np.column_stack([df[c].values * (1 if s == "max" else -1) for c, s in axes]).astype(float)
    ok = np.isfinite(X).all(1)
    nd = np.zeros(len(df), bool)
    idx = np.flatnonzero(ok)
    for i in idx:
        dom = (X[idx] >= X[i]).all(1) & (X[idx] > X[i]).any(1)
        nd[i] = not dom.any()
    return nd


def load(sleeve):
    d = L.collect(sleeve)
    if not len(d):
        return d
    m = json.load(open(L.MANIFEST))["configs"]
    d["note"] = d.config_id.map(lambda c: m.get(c, {}).get("note", ""))
    d["stage"] = d.config_id.map(lambda c: m.get(c, {}).get("stage", ""))
    d["parent"] = d.config_id.map(lambda c: m.get(c, {}).get("parent"))
    d["hash_core"] = d.config_id.map(lambda c: L.cfg_hash(dict(p=m[c]["params"], x=m[c]["exec"])) if c in m else c)
    return d


A_AXES8 = [("total_mtm", "max"), ("max_mtm_dd", "max"), ("worst_fresh_min_equity", "max"), ("fs2022_no_entry_days", "min"),
           ("rec_trades_day", "max"), ("active_slot_frac", "max"), ("dead_slot_frac", "min"), ("pnl_per_contract_day", "max")]
A_AXES4 = [("total_mtm", "max"), ("max_mtm_dd", "max"), ("worst_fresh_min_equity", "max"), ("fs2022_no_entry_days", "min")]
B_AXES = [("net_pnl", "max"), ("max_dd_daily", "max"), ("tpd_mean", "max"), ("ev_net", "max"), ("pnl_per_contract_hour", "max"),
          ("slip_plus1_ev_net", "max"), ("years_pos", "max")]


def main():
    A = load("A")
    B = load("B")
    out = {}
    if len(A):
        A["contract_cap"] = A["contract_cap"].astype(int)
        A["pareto8"] = pareto(A, A_AXES8)
        A["pareto4"] = pareto(A, A_AXES4)
        # deltas vs parent control
        base = A.set_index("config_id")
        for c in ("total_mtm", "max_mtm_dd", "worst_fresh_min_equity", "fs2022_no_entry_days", "rec_trades_day", "dead_slot_frac", "active_slot_frac"):
            A[f"d_{c}"] = [r[c] - base.loc[r.parent, c] if isinstance(r.parent, str) and r.parent in base.index else np.nan for _, r in A.iterrows()]
        A.drop(columns=["params"]).to_csv(os.path.join(ROOT, "SLEEVE_A_RESULTS.csv"), index=False)
        A[A.pareto8 | A.pareto4].drop(columns=["params"]).sort_values("total_mtm", ascending=False).to_csv(os.path.join(ROOT, "PARETO_A.csv"), index=False)
        fam = A.groupby("family").agg(n=("config_id", "size"), best_mtm=("total_mtm", "max"), med_d_mtm=("d_total_mtm", "median"),
                                     med_d_dd=("d_max_mtm_dd", "median"), med_d_fresh=("d_worst_fresh_min_equity", "median"),
                                     med_d_noentry=("d_fs2022_no_entry_days", "median"), med_d_rectpd=("d_rec_trades_day", "median"),
                                     share_pareto8=("pareto8", "mean"))
        out["A_family"] = fam
    if len(B):
        B["pareto"] = pareto(B, B_AXES)
        B.drop(columns=["params"]).to_csv(os.path.join(ROOT, "SLEEVE_B_RESULTS.csv"), index=False)
        B[B.pareto].drop(columns=["params"]).sort_values("net_pnl", ascending=False).to_csv(os.path.join(ROOT, "PARETO_B.csv"), index=False)
        out["B_family"] = B.groupby("family").agg(n=("config_id", "size"), pos=("net_pnl", lambda x: int((x > 0).sum())),
                                                  med_ev=("ev_net", "median"), best_ev=("ev_net", "max"))
    counts = dict(A=len(A), B=len(B), A_unique=int(A.hash_core.nunique()) if len(A) else 0, B_unique=int(B.hash_core.nunique()) if len(B) else 0)
    AB = load("AB")
    counts["AB"] = len(AB)
    json.dump(counts, open(os.path.join(L.OUT, "counts.json"), "w"))
    for k, v in out.items():
        print(k); print(v.round(2).to_string())
    print(counts)


if __name__ == "__main__":
    main()
