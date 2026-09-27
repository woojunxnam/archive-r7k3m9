"""TEST45 causal session features.  A feature 'at decision grid index j' uses ONLY bars end-stamped <= grid j of the current
session plus completed prior-session RTH state (never an overnight bar).  Price features are in units of the previous
session's RTH ATR14."""
import numpy as np
import pandas as pd

import t45_common as C


def rolling_std_diff(Cf, j):
    x = np.diff(Cf[:, : j + 1], axis=1)
    return np.nanstd(x, axis=1) * np.sqrt(max(j, 1))


def late(pn, j):
    """features for a late-RTH decision at grid index j (bars <= j)."""
    a = pn.atr
    Cf = pn.Cf
    c = Cf[:, j]
    lag = lambda k: Cf[:, max(j - k, 0)]
    rng = pn.runhigh[:, j] - pn.runlow[:, j]
    f = {"rth_ret": (c - pn.open) / a, "day_ret": (c - pn.p_cash) / a, "dist_vwap": (c - pn.vwap[:, j]) / a,
         "range_pos": np.where(rng > 0, (c - pn.runlow[:, j]) / rng, 0.5), "mom15": (c - lag(15)) / a, "mom30": (c - lag(30)) / a,
         "mom60": (c - lag(60)) / a, "dd_from_high": (c - pn.runhigh[:, j]) / a, "rec_from_low": (c - pn.runlow[:, j]) / a,
         "accel": ((c - lag(30)) - (lag(30) - lag(60))) / a, "rth_range": rng / a, "rvol": rolling_std_diff(Cf, j) / a,
         "gap_lock": pn.gap_lock / a, "prior_ret": pn.p_ret / a, "prior_range": pn.p_range / a, "trend20": pn.p_trend20 / a,
         "vol_pct": pn.vol_pct}
    return f


def morning(pn, w):
    """features for a morning decision after an observation window of w minutes (w=0: decision at 09:31 using the open
    print only).  Decision grid index = max(w-1, 0); fill at grid index max(w, 1)."""
    a = pn.atr
    f = {"gap_lock_atr": pn.gap_lock / a, "gap_cash_atr": pn.gap_cash / a, "gap_lock_range": pn.gap_lock / pn.p_range,
         "gap_lock_sigma": pn.gap_lock / pn.gap_sigma, "gap_lock_pct": 100 * pn.gap_lock / pn.p_lock,
         "gap_cash_range": pn.gap_cash / pn.p_range, "gap_cash_sigma": pn.gap_cash / pn.gap_sigma, "gap_cash_pct": 100 * pn.gap_cash / pn.p_cash,
         "prior_ret": pn.p_ret / a, "prior_range": pn.p_range / a, "trend20": pn.p_trend20 / a, "vol_pct": pn.vol_pct}
    if w > 0:
        j = w - 1
        c = pn.Cf[:, j]; lo = pn.runlow[:, j]; hi = pn.runhigh[:, j]
        rng = hi - lo
        f.update({"ret_w": (c - pn.open) / a, "selloff_w": (lo - pn.open) / a, "recovery_w": (c - lo) / a,
                  "reclaim_frac": np.where(pn.open - lo > 0, (c - lo) / (pn.open - lo), 1.0),
                  "range_pos_w": np.where(rng > 0, (c - lo) / rng, 0.5), "disp_total": (lo - pn.p_lock) / a,
                  "dist_vwap_w": (c - pn.vwap[:, j]) / a})
    else:
        f.update({"ret_w": np.zeros(pn.n), "selloff_w": np.zeros(pn.n), "recovery_w": np.zeros(pn.n), "reclaim_frac": np.ones(pn.n),
                  "range_pos_w": np.full(pn.n, 0.5), "disp_total": pn.gap_lock / a, "dist_vwap_w": np.zeros(pn.n)})
    return f


def decision_fill(w):
    return max(w, 1)          # grid index of the fill bar: decision at bar end 09:30+w -> fill open of bar 09:31+w


def fwd(pn, FP, j_fill, j_exit):
    """return (points) of a long filled at FP[:, j_fill] and closed at the close of bar j_exit (descriptive)."""
    return pn.Cf[:, j_exit] - FP[:, j_fill]


def champion_state(sess):
    import os
    st = pd.read_csv(os.path.join(C.T45, "baseline", "champion_session_state.csv"), index_col=0, parse_dates=True).reindex(sess)
    ch = C.champion_daily().pnl.reindex(sess).fillna(0.0)
    eq = ch.cumsum()
    dd = (eq.cummax() - eq)
    st["champ_dd_prev"] = dd.shift(1).fillna(0.0).values             # champion drawdown through the PREVIOUS session
    return st.fillna(0.0)
