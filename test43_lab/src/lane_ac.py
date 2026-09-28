"""GA-AC lane (TEST48): ARM -> CONFIRM grammar (preregistered genes)."""
import numpy as np

import t47_engine as E
import t48_engine as A

NAME = "GA-AC"
SPACE = [("inst", "cat", ["ES", "MNQ"]), ("setup", "cat", A.SETUPS), ("xm", "num", (0.5, 2.0)), ("conf", "cat", A.CONFS),
         ("W", "cat", [6, 12, 24]), ("expx", "num", (0.5, 2.0)), ("exit", "cat", ["X60", "X120", "X1600"]), ("bull", "cat", [0, 1]),
         ("volt_max", "cat", [0.5, 0.8, 1.0])]


def init():
    import prog_ga as PG
    es, nq = E.setup()
    mks = {"ES": es, "MNQ": nq}
    return {"mks": mks, "sess": es.pn.sess, "base": PG.base_tables(mks, ["X60", "X120", "X1600"]),
            "books": {(k, 1.0): A.ArmBook(m) for k, m in mks.items()}}


def run(g, ctx, slip=1.0):
    mk = ctx["mks"][g["inst"]]
    kb = (g["inst"], round(g["xm"], 2))
    if kb not in ctx["books"]:
        if len(ctx["books"]) > 400:
            ctx["books"] = {k: v for k, v in ctx["books"].items() if k[1] == 1.0}
        ctx["books"][kb] = A.ArmBook(mk, xm=g["xm"])
    ab = ctx["books"][kb]
    arm = ab.arms[g["setup"]].copy()
    if g["bull"]:
        arm[~mk.bull] = -1
    if g["volt_max"] < 1.0:
        arm[mk.volt > g["volt_max"]] = -1
    ent = A.entries(ab, g["setup"], g["conf"], W=g["W"], expx=g["expx"], arm=arm)
    d, s, j, pnl = A.trade_daily(mk, ent, g["exit"], slip)
    return d, s, j, pnl, g["exit"]


def complexity(g):
    return int(1 + (g["conf"] != "CF0_IMMEDIATE") + g["bull"] + (g["volt_max"] < 1.0) + (abs(g["xm"] - 1) > 0.25))


def cluster(g):
    return f"{g['inst']}|{g['setup']}|{g['conf']}|{g['exit']}"
