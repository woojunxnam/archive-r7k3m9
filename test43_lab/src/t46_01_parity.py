"""TEST46 Phase 0: INDEX6 baseline parity (local engine vs sanitized legacy ledgers <= 2026-05-27).
PREDECLARED parity rule (written before any comparison was run):
  window = sessions 2019-09-03 .. 2026-05-27 (canonical data start 2019-05-06 + indicator warm-up);
  PARITY_PASS  iff  >= 98% of ledger entries in the window are reproduced at the same entry date+time AND >= 98% of engine
                    entries exist in the ledger AND >= 95% of matched entries have |raw entry price - ledger price| <= 1 tick;
  otherwise PARITY_BLOCKED (seed may still be used as a ledger-driven HISTORICAL research object, never evolved/promoted).
AMENDMENT v1.1 (made after the first parity run, BEFORE any Lane-A economics; changes only coverage and price convention,
never a strategy rule): (a) "source coverage" = sessions where the canonical data has all 81 RTH 5m bars complete (n1==5)
in BOTH ES and MNQ - sessions with canonical data gaps are excluded from both sides; (b) TradingView ledgers use a
back-adjusted continuous series anchored at the latest contract, so price parity = |(ledger - engine) - quarterly median
offset| <= 1 tick."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import t46_common as C, t46_seeds as S

W0 = pd.Timestamp("2019-09-03")


def covered_dates():
    ok = None
    for inst in ("ES", "MNQ"):
        b = C.bars5(inst)
        g = b.groupby("date").agg(n=("n1", "size"), full=("n1", lambda x: bool((x == 5).all())))
        s = set(g[(g.n == 81) & g.full].index)
        ok = s if ok is None else ok & s
    return ok


COV = None


def compare(name, led, eng):
    global COV
    COV = COV or covered_dates()
    L = led[(led.entry_time >= W0) & (led.entry_time.dt.normalize() <= C.END) & led.entry_time.dt.normalize().isin(COV)]
    E = eng[(eng.entry_time >= W0) & pd.to_datetime(eng.entry_time).dt.normalize().isin(COV)]
    lk = set(L.entry_time); ek = set(pd.to_datetime(E.entry_time))
    both = lk & ek
    mL = L[L.entry_time.isin(both)].set_index("entry_time"); mE = E.assign(entry_time=pd.to_datetime(E.entry_time)).set_index("entry_time").loc[sorted(both)]
    off = (mL.entry_px.reindex(mE.index) - mE.entry_px)
    qmed = off.groupby(off.index.to_period("Q")).transform("median")
    pdiff = (off - qmed).abs()
    o = {"seed": name, "ledger_entries_window": len(L), "engine_entries_window": len(E), "matched": len(both),
         "ledger_recall": len(both) / max(len(L), 1), "engine_precision": len(both) / max(len(E), 1),
         "price_within_1tick_share": float((pdiff <= 0.25 + 1e-9).mean()) if len(pdiff) else np.nan,
         "median_abs_price_diff": float(pdiff.median()) if len(pdiff) else np.nan}
    o["PARITY"] = "PASS" if (o["ledger_recall"] >= 0.98 and o["engine_precision"] >= 0.98 and o["price_within_1tick_share"] >= 0.95) else "BLOCKED"
    return o


def main():
    os.makedirs(C.T46, exist_ok=True)
    rows = []
    es, nq = C.bars5("ES"), C.bars5("MNQ")
    for name, b, fn in (("LC02", es, lambda b: S.lc02(b)), ("LC03", nq, lambda b: S.t07(b, "T07-11")), ("LC05", nq, lambda b: S.t07(b, "T07-01"))):
        sig, atr = fn(b)
        eng = S.simulate_shell(b, sig, atr)
        eng.to_parquet(f"{C.T46}/engine_trades_{name}.parquet")
        led = C.load_ledger(name)
        rows.append(compare(name, led, eng))
        print(rows[-1], flush=True)
    json.dump(rows, open(f"{C.T46}/T46_01_parity.json", "w"), indent=1)


if __name__ == "__main__":
    main()
