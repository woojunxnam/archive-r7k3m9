"""GA-EXPOSURE lane (TEST57): Beta-Carrier-V2 exposure grammar; custom fitness (increment over C43, timing value, tail + margin constraints)."""
import numpy as np

import t45_common as C45
import t47_engine as E
import hx_common as H
import hx_carrier as X

NAME = "GA-EXPOSURE"
TIERS = [0, 1, 2, 3, 5, 8, 12]
FM = [(10, 30), (20, 50), (30, 100)]
SPACE = [("fm", "cat", [0, 1, 2]), ("dd_bear", "num", (2.0, 8.0)), ("vol_crash", "cat", [0.8, 0.9, 0.95, 1.01]),
         ("t0", "cat", list(range(7))), ("t1", "cat", list(range(7))), ("t2", "cat", list(range(7))), ("t3", "cat", list(range(7))),
         ("vt", "cat", [0, 1]), ("gov", "cat", [0, 1, 2]), ("intraday", "cat", [0, 1]), ("r_nq", "cat", [0.0, 0.5, 1.0]), ("state_inst", "cat", ["ES", "MNQ"])]
GOV = [None, (8000, 16000), (15000, 30000)]


def init():
    es, nq = E.setup(); mks = {"ES": es, "MNQ": nq}
    bk = H.Book(mks)
    per = {k: np.nan_to_num(np.r_[np.nan, np.diff(m.pn.se)] * m.pv) for k, m in mks.items()}
    champ = C45.champion_daily().pnl.reindex(es.pn.sess).fillna(0.0).values
    return {"mks": mks, "bk": bk, "sess": es.pn.sess, "per": per, "champ": champ, "cache": {}}


def run_carrier(g, ctx, slip=1.0):
    tiers = sorted([TIERS[g["t0"]], TIERS[g["t1"]], TIERS[g["t2"]], TIERS[g["t3"]]])
    f, m = FM[g["fm"]]
    return X.carrier(ctx["mks"], ctx["bk"], tiers, r_nq=g["r_nq"], vol_target=bool(g["vt"]), dd_gov=GOV[g["gov"]], margin_cap=0.40,
                     intraday_only=bool(g["intraday"]), slip=slip, state_p={"f": f, "m": m, "s": max(100, 2 * m), "dd_bear": g["dd_bear"],
                                                                              "vol_crash": g["vol_crash"]}, state_inst=g["state_inst"])


def timing(ctx, r, s0, s1):
    qE, qN = r["qE"][s0:s1], r["qN"][s0:s1]
    beta = qE.mean() * ctx["per"]["ES"][s0:s1].mean() + qN.mean() * ctx["per"]["MNQ"][s0:s1].mean()
    return float(r["gross"][s0:s1].mean() - beta)


def complexity(g):
    return int(1 + g["vt"] + (g["gov"] > 0) + g["intraday"] + (g["vol_crash"] < 1.0) + len(set([g["t0"], g["t1"], g["t2"], g["t3"]])))


def cluster(g):
    tiers = sorted([TIERS[g["t0"]], TIERS[g["t1"]], TIERS[g["t2"]], TIERS[g["t3"]]])
    return f"{'ID' if g['intraday'] else 'ON'}|max{tiers[-1]}|min{tiers[0]}|vt{g['vt']}|gov{g['gov']}"


def run(g, ctx, slip=1.0):
    r = run_carrier(g, ctx, slip)
    return r["daily"], np.zeros(0, int), np.zeros(0, int), np.zeros(0), "X1615"


def fitness(g, ctx, win):
    r = run_carrier(g, ctx)
    s0, s1 = win
    x = r["daily"][s0:s1]
    tot = ctx["champ"][s0:s1] + x
    chunks = np.array_split(np.arange(len(x)), 4)
    fa = np.array([x[c].mean() for c in chunks])
    eq = np.r_[0.0, np.cumsum(tot)]; mdd = float((np.maximum.accumulate(eq) - eq).max())
    tv = timing(ctx, r, s0, s1)
    cx = complexity(g)
    obj = np.array([-np.median(fa), -fa.min(), mdd, -tv, cx], float)
    worst = float(tot.min()); pm = float(r["on_margin"][s0:s1].max() / H.NLV)
    active = float((r["units"][s0:s1] > 0).mean())
    cv = max(0.0, (-6000 - worst) / 6000) + max(0.0, pm - 0.40) + max(0.0, 0.05 - active)
    return obj, cv, {"median_inner": float(np.median(fa)), "worst_inner": float(fa.min()), "train_avg": float(x.mean()), "train_mdd": mdd,
                     "train_excess_day": tv, "train_trades": int((r["units"][s0:s1] > 0).sum()), "corr": 0.0, "complexity": cx}


def outer_eval(g, ctx, s0, s1):
    r = run_carrier(g, ctx)
    x = r["daily"][s0:s1]
    tot = ctx["champ"][s0:s1] + x
    eq = np.r_[0.0, np.cumsum(tot)]
    return {"outer_avg": float(x.mean()), "outer_total": float(x.sum()), "outer_trades": int((r["units"][s0:s1] > 0).sum()),
            "outer_mdd": float((np.maximum.accumulate(eq) - eq).max()), "outer_excess_day": timing(ctx, r, s0, s1),
            "outer_corr_C43": float(np.corrcoef(ctx["champ"][s0:s1], x)[0, 1]) if x.std() > 0 else np.nan, "outer_worst_comb": float(tot.min())}
