"""Markdown tables for the RUN-4 report (results/RUN4_OVERNIGHT/report_tables.md)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import run4_lib as L
from run4_analyze import load

OUT = os.path.join(L.OUT, "report_tables.md")


def k(x):
    return "" if pd.isna(x) else f"{x/1000:,.1f}k"


def f1(x, d=1):
    return "" if pd.isna(x) else f"{x:,.{d}f}"


def md(df, cols, fmts):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join(fmts[c](r[c]) if c in fmts else str(r[c]) for c in cols) + " |")
    return head + "\n".join(rows) + "\n"


def main():
    A = load("A")
    B = load("B")
    AB = load("AB")
    out = []
    A["cap"] = A.contract_cap.astype(int)
    # ---- survivors S2 (all fresh) + S5 stress + S3 robustness
    s2 = A[A.stage == "S2"].copy()
    if len(s2):
        base = A.set_index("config_id")
        rows = []
        for _, r in s2.iterrows():
            par = r.parent
            st = A[(A.parent == par) & (A.stage == "S5")]
            rb = A[(A.parent == par) & (A.stage == "S3")]
            d = dict(note=r.note.replace("S2 all-fresh ", "")[:70], family=r.family, cap=r.cap, mtm=r.total_mtm, dd=r.max_mtm_dd,
                     fr20=r.get("fs2020_min_equity"), fr22=r.get("fs2022_min_equity"), fr25=r.get("fs2025_min_equity"),
                     worst=r.worst_fresh_min_equity, ne=r.get("fs2022_no_entry_days"), rtpd=r.rec_trades_day, qm=r.q_mean,
                     pcd=r.pnl_per_contract_day, uw=r.underwater_days, yp=r.get("years_pos_mtm"))
            s2t = st[st["exec"].str.contains('"slippage_ticks":2')]
            s3t = st[st["exec"].str.contains('"slippage_ticks":3')]
            d["mtm_2t"] = s2t.total_mtm.iloc[0] if len(s2t) else np.nan
            d["fr22_2t"] = s2t.fs2022_min_equity.iloc[0] if len(s2t) else np.nan
            d["mtm_3t"] = s3t.total_mtm.iloc[0] if len(s3t) else np.nan
            d["fr22_3t"] = s3t.fs2022_min_equity.iloc[0] if len(s3t) else np.nan
            if len(rb):
                d["rob_n"] = len(rb)
                d["rob_fr22_min"] = rb.fs2022_min_equity.min(); d["rob_fr22_max"] = rb.fs2022_min_equity.max()
                d["rob_mtm_min"] = rb.total_mtm.min(); d["rob_mtm_max"] = rb.total_mtm.max()
                d["rob_ne_max"] = rb.fs2022_no_entry_days.max()
            rows.append(d)
        S = pd.DataFrame(rows).sort_values(["family", "cap"])
        S.to_csv(os.path.join(L.OUT, "a_tables", "survivors_s2_s3_s5.csv"), index=False)
        cols = ["family", "note", "cap", "mtm", "dd", "fr20", "fr22", "fr25", "ne", "rtpd", "qm", "pcd", "mtm_2t", "fr22_2t", "fr22_3t",
                "rob_n", "rob_fr22_min", "rob_fr22_max", "rob_ne_max"]
        fm = {c: k for c in ("mtm", "dd", "fr20", "fr22", "fr25", "mtm_2t", "fr22_2t", "fr22_3t", "rob_fr22_min", "rob_fr22_max")}
        fm.update({"ne": f1, "rtpd": lambda x: f1(x, 2), "qm": f1, "pcd": lambda x: f1(x, 2), "rob_n": lambda x: "" if pd.isna(x) else str(int(x)),
                   "rob_ne_max": f1, "cap": lambda x: str(int(x))})
        out.append("## A survivors: all fresh starts (S2), 2/3-tick stress (S5), local robustness range (S3)\n" + md(S, cols, fm))
    # ---- AB best portfolios
    if len(AB):
        AB["mech"] = AB.config_id.map(lambda c: "")
        m = json.load(open(L.MANIFEST))["configs"]
        AB["spec"] = AB.config_id.map(lambda c: m[c]["params"])
        sid2mech = {}
        for cid, e in m.items():
            if e["family"] == "A-SERIES":
                sid2mech[cid] = e["note"].split()[1]
        AB["mech"] = AB.spec.map(lambda p: sid2mech.get(p.get("a_id"), "none"))
        AB["capA"] = AB.spec.map(lambda p: p.get("capA", 0))
        AB["sizeB"] = AB.spec.map(lambda p: sum(x["size"] for x in p.get("b", [])))
        AB["book"] = AB.spec.map(lambda p: p.get("book", ""))
        AB["inter"] = AB.spec.map(lambda p: p.get("interaction", p.get("b", [{}])[0].get("rule", "") if p.get("b") else ""))
        AB.to_csv(os.path.join(L.OUT, "a_tables", "ab_all.csv"), index=False)
        cols = ["mech", "G", "capA", "sizeB", "book", "inter", "total_pnl", "max_mtm_dd_bar", "min_equity_bar", "fresh2022_min_equity", "wk_mean",
                "wk_median", "wk_worst", "wk_worst_4w", "wk_ge1k", "wk_ge4k", "corr_weekly", "peak_contracts", "pnl_per_contract_day"]
        fm = {c: k for c in ("total_pnl", "max_mtm_dd_bar", "min_equity_bar", "fresh2022_min_equity", "wk_worst", "wk_worst_4w")}
        fm.update({"wk_mean": f1, "wk_median": f1, "wk_ge1k": lambda x: f"{x*100:.0f}%", "wk_ge4k": lambda x: f"{x*100:.0f}%",
                   "corr_weekly": lambda x: f1(x, 2), "pnl_per_contract_day": lambda x: f1(x, 2)})
        top = AB[AB.G == 16].sort_values("wk_mean", ascending=False)
        out.append("## A+B portfolios at G=16 (sorted by mean weekly P&L)\n" + md(top, cols, fm))
        for G in (10, 12, 14, 20, 24):
            t = AB[(AB.G == G)].sort_values("wk_mean", ascending=False).head(8)
            out.append(f"## A+B portfolios at G={G} (top 8 by mean weekly P&L)\n" + md(t, cols, fm))
    open(OUT, "w").write("\n".join(out))
    print("\n".join(out)[:20000])


if __name__ == "__main__":
    main()
