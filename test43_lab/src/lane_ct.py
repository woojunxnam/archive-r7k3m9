"""GA-CT lane (TEST49): continuation grammar (preregistered genes)."""
import numpy as np

import t45_common as C45
import t47_engine as E
import t49_engine as T

NAME = "GA-CT"
TIMES = ["09:45", "10:00", "10:15", "10:30", "11:00", "11:30", "12:30", "13:30", "14:30", "15:00"]
SPACE = [("inst", "cat", ["ES", "MNQ"]), ("t0", "cat", TIMES), ("span", "cat", [0, 3, 6, 12, 24]), ("k_ret", "num", (0.0, 1.0)),
         ("eff_min", "num", (0.0, 0.8)), ("above_min", "num", (0.0, 0.9)), ("pos_min", "num", (0.0, 0.9)), ("volt_max", "cat", [0.5, 0.8, 1.0]),
         ("bull", "cat", [0, 1]), ("exit", "cat", ["X1600", "X1615", "NEXTOPEN", "NEXT1000"])]


def init():
    import prog_ga as PG
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    base = PG.base_tables(mks, ["X1600", "X1615"])
    for k, mk in mks.items():
        for r in ("NEXTOPEN", "NEXT1000"):
            base[(k, r)] = T.overnight_base(mk, r)
    return {"mks": mks, "sess": es.pn.sess, "base": base, "st": {k: T.State(m) for k, m in mks.items()}}


def run(g, ctx, slip=1.0):
    mk = ctx["mks"][g["inst"]]; st = ctx["st"][g["inst"]]
    b0 = (C45.g(g["t0"]) + 1) // 5 - 1; b1 = min(b0 + g["span"], 74)
    cond = (st.ret >= g["k_ret"]) & (st.eff >= g["eff_min"]) & (np.nan_to_num(st.above) >= g["above_min"]) & (st.pos >= g["pos_min"])
    if g["volt_max"] < 1.0:
        cond &= (mk.volt <= g["volt_max"])[:, None]
    if g["bull"]:
        cond &= mk.bull[:, None]
    b = T.first_trigger(st, cond, b0, b1)
    ej = np.where(b >= 0, 5 * (b + 1), -1); ej = np.where(ej <= E.J_LAST_ENTRY, ej, -1)
    d, s, j, pnl, so = T.trades(mk, ej, g["exit"], slip)
    return d, s, j, pnl, g["exit"]


def complexity(g):
    return int(1 + (g["k_ret"] > 0.05) + (g["eff_min"] > 0.05) + (g["above_min"] > 0.05) + (g["pos_min"] > 0.05) + (g["volt_max"] < 1) + g["bull"] + (g["span"] > 0))


def cluster(g):
    fam = "OPEN" if g["t0"] <= "10:30" else ("MID" if g["t0"] <= "13:30" else "LATE")
    return f"{g['inst']}|{fam}|{'ON' if g['exit'].startswith('NEXT') else 'RTH'}"
