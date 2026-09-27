"""ROBUST2 objective: return robustness is secondary, risk robustness is primary (DEV-only; VAL never used)."""
import numpy as np

ENV = {"CONSERVATIVE": (10000, 2000), "MODERATE": (15000, 3000), "AGGRESSIVE": (20000, 5000), "EXPLORATORY": (1e12, 1e12)}


def score2(o, env, n_modules=0):
    L, W = ENV[env]
    avg = o.get("DEV_avg_daily"); ex5 = o.get("DEV_avg_ex_top5")
    if avg is None or ex5 is None:
        return -1e6, False
    dd = o.get("DEV_max_dd", 1e9); wd = -o.get("DEV_worst_day", -1e9)
    pen = 0.0
    if dd > L: pen += 200 + 400 * (dd / L - 1)
    if wd > W: pen += 200 + 400 * (wd / W - 1)
    if o.get("margin_breach") or o.get("min_equity", 1) <= 0: pen += 2000
    folds_avg = [o.get(f"F{k}_avg_daily") for k in (1, 2, 3)]
    folds_dd = [o.get(f"F{k}_max_dd") for k in (1, 2, 3)]
    folds_wd = [o.get(f"F{k}_worst_day") for k in (1, 2, 3)]
    s = 0.5 * avg + 0.5 * ex5
    if all(v is not None for v in folds_avg):
        s += 0.1 * min(folds_avg)                                   # consistency: secondary
        s -= 10.0 * max(0.0, max(folds_dd) / L - 0.75)               # fold drawdown containment
        s -= 10.0 * max(0.0, -min(folds_wd) / W - 0.8)               # fold worst-day containment
    days = o.get("DEV_days") or 1
    s -= 0.05 * (o.get("friction", 0.0) / days)                    # turnover preference (friction already in P&L)
    s -= 0.5 * n_modules                                            # simplicity
    return s - pen, pen == 0
