"""TEST43-P holdout acceptance evaluator — implements EXACTLY TEST43P_HOLDOUT_ACCEPTANCE_RULES.json
(sha256 62e5faf2...).  Pass conditions (ALL must hold, at the portfolio's frozen envelope):
  total net P&L > 0; no margin breach; peak margin utilisation <= 0.5 of equity; MaxDD <= envelope DD;
  worst day >= envelope floor; average daily P&L after removing the 3 best days > 0; best day <= 35% of total net P&L.
Report only: matched-beta excess, SLIP4, TIMING_BRITTLENESS_STRESS, SESSION_MATCHED_BETA.
"""
import numpy as np
import pandas as pd

from t43 import instruments, lab, v6lab

ENV = {"CONSERVATIVE": (10000.0, -2000.0), "MODERATE": (15000.0, -3000.0), "AGGRESSIVE": (20000.0, -5000.0)}
SMB_DOC = ("per instrument: passive long of size = portfolio average RTH contracts during RTH bars and portfolio average "
           "overnight contracts during non-RTH bars (same period), marked on adjusted prices; net = gross - size-change "
           "commission+1 tick - roll cost. Report only.")


def evaluate(d, env, mb_avg=None, stress=None, report_only=None):
    """d: portfolio daily table for the evaluation window (columns pnl, mu_max)."""
    dd_lim, floor = ENV[env]
    pnl = d.pnl.astype(float)
    total = float(pnl.sum()); n = len(pnl)
    eq = np.r_[0.0, pnl.cumsum().values]          # window starts at the account level on entry (peak includes the start)
    mdd = float((np.maximum.accumulate(eq) - eq).max()) if n else 0.0
    worst = float(pnl.min()) if n else np.nan
    top = pnl.sort_values(ascending=False)
    ex3 = float((total - top.iloc[:3].sum()) / n) if n else np.nan
    best = float(top.iloc[0]) if n else np.nan
    peak_mu = float(d.mu_max.max()) if n else np.nan
    c = {"net_pnl_positive": total > 0,
         "no_margin_breach": bool(peak_mu <= 1.0),
         "peak_margin_util_le_0.5": bool(peak_mu <= 0.5),
         "max_dd_within_envelope": mdd <= dd_lim,
         "worst_day_within_envelope": worst >= floor,
         "remove_top3_avg_positive": ex3 > 0,
         "best_day_le_35pct_of_total": bool(total > 0 and best <= 0.35 * total)}
    out = {"envelope": env, "sessions": n, "total_net_pnl": total, "avg_daily": total / n if n else np.nan, "max_dd": mdd,
           "worst_day": worst, "avg_ex_top3": ex3, "best_day": best, "best_day_share": best / total if total else np.nan,
           "peak_margin_util": peak_mu, "conditions": c, "PASS": bool(all(c.values())),
           "report_only": {"matched_beta_avg": mb_avg, "matched_beta_excess": (total / n - mb_avg) if (mb_avg is not None and n) else None,
                           "stress": stress, **(report_only or {})}}
    return out


def session_matched_beta(T, pos, d, start, end):
    sd = pd.DatetimeIndex(T.sd.values)
    m = np.ones(len(T), bool)
    if start is not None:
        m &= sd >= pd.Timestamp(start)
    if end is not None:
        m &= sd <= pd.Timestamp(end)
    res = {"portfolio_net_pnl": float(d.pnl[(d.index >= (pd.Timestamp(start) if start is not None else d.index.min())) & (d.index <= pd.Timestamp(end))].sum())}
    net_total = 0.0; gross_total = 0.0
    for k, inst in enumerate(("ES", "MNQ")):
        prof = instruments.PROFILES[v6lab.PROF[inst]]; pv = prof["point_value"]
        rth = T[f"{inst}_rth"].values; c = T[f"{inst}_c"].values; valid = T[f"{inst}_valid"].values
        p = pos[:, k].astype(float)
        aR = float(p[m & rth].mean()) if (m & rth).any() else 0.0
        aO = float(p[m & ~rth].mean()) if (m & ~rth).any() else 0.0
        pp = np.where(rth, aR, aO)
        dc = np.r_[0.0, np.diff(c)]
        gross = float((pp * dc * pv)[m & valid].sum())
        chg = np.abs(np.diff(np.r_[pp[0], pp]))
        cost = float((chg * (prof["commission_side"] + prof["tick_value"]))[m].sum())
        rollm = T[f"{inst}_roll"].values & np.r_[True, T.sd.values[1:] != T.sd.values[:-1]]
        cost += float((pp * 2 * (prof["commission_side"] + prof["tick_value"]))[m & rollm].sum())
        res[f"{inst}_avg_rth_contracts"] = aR; res[f"{inst}_avg_on_contracts"] = aO
        res[f"{inst}_passive_gross"] = gross; res[f"{inst}_passive_net"] = gross - cost
        net_total += gross - cost; gross_total += gross
    ns = len(np.unique(sd[m]))
    res["sessions"] = ns
    res["session_matched_net_pnl"] = net_total; res["session_matched_gross_pnl"] = gross_total
    res["excess_vs_session_matched_total"] = res["portfolio_net_pnl"] - net_total
    res["excess_vs_session_matched_per_day"] = res["excess_vs_session_matched_total"] / ns if ns else np.nan
    return res


def self_test():
    """Synthetic cases: one passing window and one targeted failure per rule."""
    idx = pd.date_range("2030-01-01", periods=100, freq="B")
    base = pd.DataFrame({"pnl": np.r_[np.full(50, 120.0), np.full(50, -20.0)], "mu_max": 0.2}, index=idx)
    cases = []
    def add(name, d, env, expect, key=None):
        r = evaluate(d, env)
        ok = (r["PASS"] == expect) and (key is None or r["conditions"][key] is False)
        cases.append({"case": name, "expected_pass": expect, "got_pass": r["PASS"], "failed_condition_checked": key, "pass": bool(ok)})
    add("baseline_pass", base, "MODERATE", True)
    x = base.copy(); x["pnl"] = -np.abs(x.pnl); add("negative_total", x, "MODERATE", False, "net_pnl_positive")
    x = base.copy(); x.loc[x.index[10], "mu_max"] = 1.2; add("margin_breach", x, "MODERATE", False, "no_margin_breach")
    x = base.copy(); x.loc[x.index[10], "mu_max"] = 0.6; add("margin_util_above_0.5", x, "MODERATE", False, "peak_margin_util_le_0.5")
    x = base.copy(); x.loc[x.index[60:], "pnl"] = -400.0; x.loc[x.index[:50], "pnl"] = 400.0; add("maxdd_breach_MOD", x, "MODERATE", False, "max_dd_within_envelope")
    x = base.copy(); x.loc[x.index[20], "pnl"] = -2500.0; add("worst_day_CONS", x, "CONSERVATIVE", False, "worst_day_within_envelope")
    add("worst_day_same_ok_MOD", x, "MODERATE", True)
    x = base.copy(); x["pnl"] = -10.0; x.loc[x.index[:3], "pnl"] = 800.0; add("top3_dependence", x, "MODERATE", False, "remove_top3_avg_positive")
    x = base.copy(); x.loc[x.index[5], "pnl"] = 4000.0; add("single_day_concentration", x, "MODERATE", False, "best_day_le_35pct_of_total")
    return cases
