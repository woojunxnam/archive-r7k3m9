"""Occurrence-weighted means with session-clustered (cluster-robust) standard errors.

Equal-weighting sessions (mean of per-session means) is NOT used: the number of occurrences in a session depends on
that session's future path, so 1/count weighting leaks future information (detected in TEST43-M: BELOW-range bars
+0.047 ATR session-weighted vs -0.003 ATR occurrence-weighted)."""
import numpy as np
import pandas as pd


def cr_mean_t(values, clusters, min_clusters=10):
    v = np.asarray(values, float); c = np.asarray(clusters)
    m = ~np.isnan(v)
    v = v[m]; c = c[m]
    n = len(v)
    if n == 0:
        return np.nan, np.nan, 0
    mu = v.mean()
    s = pd.Series(v - mu).groupby(c).sum()
    G = len(s)
    if G < min_clusters:
        return float(mu), np.nan, G
    var = (s.values ** 2).sum() / n ** 2 * G / (G - 1)
    return float(mu), float(mu / np.sqrt(var)) if var > 0 else np.nan, G
