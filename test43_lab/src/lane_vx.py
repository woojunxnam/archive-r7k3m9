"""GA-VX lane (TEST50): compression -> upside expansion grammar (preregistered genes)."""
import numpy as np

import t47_engine as E
import t49_engine as T49
import t50_engine as V

NAME = "GA-VX"
SPACE = [("inst", "cat", ["ES", "MNQ"]), ("ktype", "cat", ["K1_RANGE", "K2_RVOL", "K3_CONTRACTION"]), ("kthr", "num", (0.5, 1.5)),
         ("L", "cat", [6, 12, 24]), ("xtype", "cat", ["X1_BOX_BREAK", "X2_EXP_BAR", "X3_HL_BREAK", "X4_BREAK_RETEST"]), ("xsize", "num", (0.5, 2.0)),
         ("W", "cat", [6, 12, 24]), ("stop", "cat", [0, 1]), ("buf", "num", (0.0, 1.5)), ("exit", "cat", ["X120", "X1600", "X1615", "NEXTOPEN"]),
         ("t_start", "cat", ["10:00", "10:30", "11:30", "13:00"]), ("bull", "cat", [0, 1]), ("volt_max", "cat", [0.5, 0.8, 1.0])]
KBASE = {"K1_RANGE": 4.0, "K2_RVOL": 0.6, "K3_CONTRACTION": 0.35}      # kthr gene is a multiplier of these base values


def init():
    import prog_ga as PG
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    base = PG.base_tables(mks, ["X120", "X1600", "X1615"])
    for k, mk in mks.items():
        base[(k, "NEXTOPEN")] = T49.overnight_base(mk, "NEXTOPEN")
    return {"mks": mks, "sess": es.pn.sess, "base": base}


def run(g, ctx, slip=1.0):
    mk = ctx["mks"][g["inst"]]
    mask = np.ones(mk.n, bool)
    if g["bull"]:
        mask &= mk.bull
    if g["volt_max"] < 1.0:
        mask &= mk.volt <= g["volt_max"]
    thr = KBASE[g["ktype"]] * g["kthr"]
    L = g["L"] if g["ktype"] != "K3_CONTRACTION" else g["L"]
    d, s, j, pnl, off = V.run(mk, g["ktype"], thr, L, g["xtype"], g["xsize"], g["W"], bool(g["stop"]), g["buf"], g["exit"], slip, g["t_start"], mask)
    return d, s, j, pnl, g["exit"]


def complexity(g):
    return int(1 + g["stop"] + g["bull"] + (g["volt_max"] < 1) + (g["xtype"] == "X4_BREAK_RETEST") + (abs(g["kthr"] - 1) > 0.25))


def cluster(g):
    return f"{g['inst']}|{g['ktype']}|{g['xtype']}|{'ON' if g['exit'] == 'NEXTOPEN' else 'RTH'}"
