"""P&L decomposition: gross MTM = beta(avg pos) + timing; net = gross - friction - roll."""
import numpy as np
PV = 5.0

def decompose(b, res, start_mask=None, pv=PV):
    c = b["c"].values
    pos = res["pos"].astype(float)
    o = b["o"].values
    # position held over (open_i -> close_i) is pos_i (after open fill); over (close_{i-1} -> open_i) is pos_{i-1}
    dp_gap = np.diff(np.concatenate([[o[0]], o])) * 0  # placeholder
    prev_c = np.concatenate([[o[0]], c[:-1]])
    pos_prev = np.concatenate([[0.0], pos[:-1]])
    mtm = (pos_prev * (o - prev_c) + pos * (c - o)) * pv
    dp = (c - prev_c) * pv
    m = np.ones(len(c), bool) if start_mask is None else start_mask
    avg = pos[m].mean()
    gross = mtm[m].sum()
    beta = avg * dp[m].sum()
    return {"avg_pos": avg, "gross_mtm": gross, "beta_at_avg_pos": beta, "timing": gross - beta}
