"""TEST96 C1: TS13-S01 (T13-07 YM) parity: frozen-Pine port vs sanitized TradingView ledger (TEST46 rule unchanged; per-contract offset diag)."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import t96_data as X; X.register()
import t46_common as C, t46_01_parity as P, t45_common as C45
import t96_common as W, t96_ts13 as T13


def main():
    b = C.bars5("YM"); g = b.groupby("date").agg(n=("n1", "size"), full=("n1", lambda x: bool((x == 5).all())))
    P.COV = set(g[(g.n == 81) & g.full].index)
    eng = T13.replay(T13.bars("YM")); eng["entry_time"] = pd.to_datetime(eng.entry_time)
    led = pd.read_csv(os.path.join(C.LEDGER_DIR, "TS13_S01_T1307_0e546_TO_20260527.csv"))
    ent = led[led.Type.str.startswith("Entry")].set_index("Trade number")
    L = pd.DataFrame({"entry_time": pd.to_datetime(ent["Date and time"]), "entry_px": ent["Price USD"].astype(float)}).reset_index(drop=True)
    o = P.compare("TS13_S01_YM", L, eng)
    m = L.merge(eng[["entry_time", "entry_px"]], on="entry_time", suffixes=("_l", "_e")); m = m[m.entry_time >= P.W0]
    ct = C45.load1m("YM")[["session_date", "contract"]].drop_duplicates("session_date")
    m = m.merge(ct, left_on=m.entry_time.dt.normalize(), right_on="session_date", how="left"); off = m.entry_px_l - m.entry_px_e
    o["DIAG_per_contract_offset_within_1tick"] = float(((off - off.groupby(m.contract).transform("median")).abs() <= 1.0 + 1e-9).mean())
    o["ledger_first_entry"] = str(L.entry_time.min().date()); o["engine_trades_total"] = len(eng)
    W.save("T96_C1_TS13_PARITY.json", o); print(o)


if __name__ == "__main__":
    main()
