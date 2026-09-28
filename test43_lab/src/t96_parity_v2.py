"""PROPOSED PARITY_PRICE_SPACE_V2 (NOT APPLIED - user approval required before any governance status change).
Only the price-offset convention changes: TEST46 v1.1 used the quarterly median of (ledger - engine) entry-price offsets; V2 uses the median offset
per canonical CONTRACT period (contract label of the entry session in the canonical 1m file = deterministic roll calendar).  No P&L is used.
Recall / precision (>= 98%) and price (>= 95% within 1 tick) gates are unchanged; same method for every ledger-backed sleeve."""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t96_data as X  # noqa: E402
X.register()
import t45_common as C45  # noqa: E402
import t46_01_parity as P  # noqa: E402
import t46_common as C  # noqa: E402
import t96_common as W  # noqa: E402

TICK = {"ES": 0.25, "NQ": 0.25, "YM": 1.0}


def cov(insts):
    ok = None
    for i in insts:
        b = C.bars5(i); g = b.groupby("date").agg(n=("n1", "size"), full=("n1", lambda x: bool((x == 5).all())))
        s = set(g[(g.n == 81) & g.full].index); ok = s if ok is None else ok & s
    return ok


def ledger_entries(path):
    d = pd.read_csv(path); e = d[d.Type.str.startswith("Entry")]
    return pd.DataFrame({"entry_time": pd.to_datetime(e["Date and time"]), "entry_px": e["Price USD"].astype(float)}).reset_index(drop=True)


def evaluate(name, led, eng, inst, cover):
    P.COV = cover; base = P.compare(name, led, eng)                           # V1 (frozen) result, unchanged recall / precision
    L = led[(led.entry_time >= P.W0) & led.entry_time.dt.normalize().isin(cover)]
    E = eng.assign(entry_time=pd.to_datetime(eng.entry_time)); E = E[(E.entry_time >= P.W0) & E.entry_time.dt.normalize().isin(cover)]
    m = L.merge(E[["entry_time", "entry_px"]], on="entry_time", suffixes=("_l", "_e"))
    ct = C45.load1m(inst).groupby("session_date").contract.last()
    m["contract"] = ct.reindex(m.entry_time.dt.normalize()).values
    off = m.entry_px_l - m.entry_px_e; v2 = float(((off - off.groupby(m.contract).transform("median")).abs() <= TICK[inst] + 1e-9).mean())
    o = {"sleeve": name, "recall": base["ledger_recall"], "precision": base["engine_precision"], "price_share_V1_quarterly": base["price_within_1tick_share"],
         "price_share_V2_contract": v2, "PARITY_V1": base["PARITY"],
         "PARITY_V2_PROPOSED": "PASS" if (base["ledger_recall"] >= 0.98 and base["engine_precision"] >= 0.98 and v2 >= 0.95) else "BLOCKED"}
    return o


def main():
    rows = []
    es_cov, nq_cov, ym_cov = cov(("ES", "MNQ")), cov(("ES", "MNQ", "NQ")), cov(("YM",))
    rows.append(evaluate("LC02 (ES)", C.load_ledger("LC02")[["entry_time", "entry_px"]], pd.read_parquet(os.path.join(C45.ROOT, "out/t46/engine_trades_LC02.parquet")), "ES", es_cov))
    for nm in ("LC03", "LC05"):
        rows.append(evaluate(f"{nm} (NQ)", C.load_ledger(nm)[["entry_time", "entry_px"]], pd.read_parquet(os.path.join(W.OUT, f"engine_trades_{nm}_NQ.parquet")), "NQ", nq_cov))
    import t96_ts13 as T13
    rows.append(evaluate("TS13-S01 (YM)", ledger_entries(os.path.join(C.LEDGER_DIR, "TS13_S01_T1307_0e546_TO_20260527.csv")), T13.replay(T13.bars("YM")), "YM", ym_cov))
    p = os.path.join(W.OUT, "T20_V1_ENGINE_LEGS.csv")
    if os.path.exists(p):
        e = pd.read_csv(p, parse_dates=["entry_time"])
        # pyramided legs share timestamps: timestamp-level comparison on the first leg per timestamp (both sides, same rule)
        led = ledger_entries(os.path.join(C.LEDGER_DIR, "TEST20_V1_1_MARGINFIX_NQ_V1_45ce0_TO_20260527.csv")).drop_duplicates("entry_time")
        rows.append(evaluate("TEST20 V1 (NQ, timestamp level)", led, e[["entry_time", "entry_px"]].drop_duplicates("entry_time"), "NQ", nq_cov))
    R = pd.DataFrame(rows); W.save("PARITY_PRICE_SPACE_V2_PROPOSAL.json", R.to_dict("records"))
    note = ("PROPOSAL ONLY - NOT APPLIED.  Governance statuses remain as under the frozen TEST46 v1.1 convention until the user approves V2.  "
            "Offsets are defined from the canonical contract calendar only (no P&L).  LC05 stays BLOCKED regardless (signal recall / precision fail).")
    W.md("PARITY_PRICE_SPACE_V2_PROPOSAL.md", "PARITY_PRICE_SPACE_V2 - proposed contract-period price offsets (before / after)", [note, R])
    print(R.to_string())


if __name__ == "__main__":
    main()
