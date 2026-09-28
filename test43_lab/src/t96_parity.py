"""TEST96 Track B: INDEX parity retries with canonical full-contract NQ (unchanged TEST46 parity rule and engine; no rule change).
LC03 = T07-11 and LC05 = T07-01 on NQ bars (true NQ volume).  LC02 unchanged (ES data unchanged; stays BLOCKED)."""
import json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import t96_data as X
X.register()
import t46_common as C, t46_seeds as S, t46_01_parity as P
import t96_common as W


def covered_dates_nq():
    ok = None
    for inst in ("ES", "MNQ", "NQ"):
        b = C.bars5(inst)
        g = b.groupby("date").agg(n=("n1", "size"), full=("n1", lambda x: bool((x == 5).all())))
        s = set(g[(g.n == 81) & g.full].index)
        ok = s if ok is None else ok & s
    return ok


def main():
    P.COV = covered_dates_nq(); rows = []
    nq = C.bars5("NQ")
    for name, which in (("LC03", "T07-11"), ("LC05", "T07-01")):
        sig, atr = S.t07(nq, which); eng = S.simulate_shell(nq, sig, atr)
        eng.to_parquet(os.path.join(W.OUT, f"engine_trades_{name}_NQ.parquet"))
        o = P.compare(name + "_NQ", C.load_ledger(name), eng); rows.append(o); print(o, flush=True)
    W.save("T96_B_PARITY.json", rows)
    W.md("T96_B_PARITY_RETRY.md", "TEST96 Track B - parity retry on canonical NQ (TEST46 rule unchanged)", [pd.DataFrame(rows)])


if __name__ == "__main__":
    main()
