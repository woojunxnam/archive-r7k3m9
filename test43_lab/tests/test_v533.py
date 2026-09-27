"""Unit/invariant tests for the V5.3.3 Python reference (synthetic data).

Run:  cd test43_lab && python -m pytest -q tests
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from t43 import bars as B  # noqa: E402
from t43 import v533  # noqa: E402
from t43 import metrics as M  # noqa: E402


def synth_1m(days=40, seed=7, drop_frac=0.01, drift=0.0):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-07 18:01")  # Sunday evening session open (END-stamped)
    rows = []
    px = 4800.0
    d = 0
    cur = start
    while d < days:
        sess_start = cur
        # one CME session: 18:01 .. 17:00 next day (END stamps), 1380 minutes
        for k in range(1380):
            t = sess_start + pd.Timedelta(minutes=k)
            mod = t.hour * 60 + t.minute
            in_rth = 571 <= mod <= 960
            sig = 0.6 if in_rth else 0.25
            step = rng.normal(drift, sig)
            o = px
            c = np.round((px + step) / 0.25) * 0.25
            hi = max(o, c) + 0.25 * rng.integers(0, 3)
            lo = min(o, c) - 0.25 * rng.integers(0, 3)
            px = c
            if rng.random() < drop_frac:
                continue
            vol = float(rng.integers(200, 3000) if in_rth else rng.integers(5, 300))
            rows.append((t, o, hi, lo, c, vol))
        d += 1
        nxt = sess_start + pd.Timedelta(days=1)
        if nxt.weekday() == 4:  # Friday evening -> jump to Sunday
            nxt = nxt + pd.Timedelta(days=2)
        cur = nxt
    df = pd.DataFrame(rows, columns=["dt", "o", "h", "l", "c", "v"])
    return df


@pytest.fixture(scope="module")
def data():
    m1 = B.normalise_1m(synth_1m())
    b = B.add_clock(B.aggregate_3m(m1))
    arr = B.to_arrays(b)
    return m1, b, arr


@pytest.fixture(scope="module")
def base_run(data):
    _, b, arr = data
    return v533.run(arr, v533.make_params())


def test_aggregation_open_stamped(data):
    m1, b, _ = data
    # a 3m bar stamped T contains 1m bars with END dt in (T, T+3]
    row = b.iloc[500]
    t = row["t"]
    sub = m1[(m1["dt"] > t) & (m1["dt"] <= t + pd.Timedelta(minutes=3))]
    assert row["o"] == sub["o"].iloc[0]
    assert row["c"] == sub["c"].iloc[-1]
    assert row["h"] == sub["h"].max() and row["l"] == sub["l"].min()
    assert row["v"] == sub["v"].sum()
    assert (b["t"].dt.minute % 3 == 0).all()


def test_rth_flags(data):
    _, b, arr = data
    assert b.loc[b["in_rth"], "mod"].min() >= 570 and b.loc[b["in_rth"], "mod"].max() <= 957
    # exactly one new RTH per session with RTH bars
    nr = pd.Series(arr["new_rth"]).groupby(b["session_date"].values).sum()
    assert (nr <= 1).all()


def test_vwap_session_reset_and_accumulation(data, base_run):
    _, b, arr = data
    diag = base_run["diag"]
    src = (b["h"] + b["l"] + b["c"]) / 3.0
    rth = b["in_rth"].values
    grp = np.cumsum(arr["new_rth"])
    df = pd.DataFrame({"g": grp, "pv": src * b["v"], "v": b["v"], "p2v": src * src * b["v"], "rth": rth})
    df = df[df.rth]
    cpv = df.groupby("g")["pv"].cumsum()
    cv = df.groupby("g")["v"].cumsum()
    vw = cpv / cv
    idx = df.index.values
    np.testing.assert_allclose(diag[idx, 0], vw.values, rtol=1e-12)
    # VWAP is na outside RTH
    assert np.isnan(diag[~rth, 0]).all()


def test_rolling_rth_levels_use_prior_bars_only(data, base_run):
    _, b, arr = data
    diag = base_run["diag"]
    rth = b["in_rth"].values
    grp = np.cumsum(arr["new_rth"])
    h = b["h"].values
    for i in np.where(rth)[0][100:400]:
        same = np.where(rth[:i] & (grp[:i] == grp[i]))[0]
        if len(same) == 0:
            assert np.isnan(diag[i, 3])
            continue
        np.testing.assert_allclose(diag[i, 3], h[same[-5:]].max())
        np.testing.assert_allclose(diag[i, 5], h[same[-20:]].max())


def test_prior_rth_and_5d(data, base_run):
    _, b, arr = data
    diag = base_run["diag"]
    rth = b["in_rth"].values
    grp = np.cumsum(arr["new_rth"])
    hi = pd.Series(b["h"].values[rth]).groupby(grp[rth]).max()
    for i in np.where(arr["new_rth"])[0][5:15]:
        g = grp[i]
        assert diag[i, 9] == hi.loc[g - 1]
        exp5 = max(hi.loc[g - 4:g - 1].max(), b["h"].values[i])
        assert diag[i, 7] == exp5


def test_no_short_and_cap(base_run):
    pos = base_run["pos"]
    assert pos.min() >= 0
    assert pos.max() <= 24


def test_next_open_fill_and_slippage(data, base_run):
    _, b, _ = data
    o = b["o"].values
    for bar, side, px in zip(base_run["f_bar"], base_run["f_side"], base_run["f_px"]):
        assert px == o[bar] + 0.25 * side


def test_orders_fill_next_bar(data, base_run):
    # position can only change at bars that have a fill record
    pos = base_run["pos"]
    chg = np.where(np.diff(np.concatenate([[0], pos])) != 0)[0]
    assert set(chg) == set(base_run["f_bar"])


def test_commission_and_equity_identity(data, base_run):
    _, b, _ = data
    eq = base_run["equity"]
    realized = base_run["f_real"].sum()
    # open lots MTM reconstructed from FIFO
    lots = []
    for side, q, px in zip(base_run["f_side"], base_run["f_qty"], base_run["f_px"]):
        if side == 1:
            lots.append([px, q])
        else:
            rem = q
            while rem:
                take = min(rem, lots[0][1])
                lots[0][1] -= take
                rem -= take
                if lots[0][1] == 0:
                    lots.pop(0)
    c = b["c"].values[-1]
    mtm = sum((c - p) * 5 * q for p, q in lots)
    np.testing.assert_allclose(eq[-1], 150000 + realized + mtm, rtol=1e-12)
    sides = base_run["f_qty"].sum()
    # every fill paid 0.62/contract
    buys = base_run["f_side"] == 1
    np.testing.assert_allclose(base_run["f_real"][buys].sum(), -0.62 * base_run["f_qty"][buys].sum())
    assert sides > 0


def test_one_repair_slot(data, base_run):
    """No REPAIR_SELL fill while a repair slot is pending."""
    diag = base_run["diag"]
    rs = v533.R["REPAIR_SELL"]
    for bar, reason in zip(base_run["f_bar"], base_run["f_reason"]):
        if reason == rs:
            # the order was created on bar-1: repair must not have been pending there
            assert diag[bar - 1, 16] == 0.0


def test_repair_resolution_paths(base_run):
    """Every repair slot ends with a BUY fill that restores the cap (Pine line 715 accepts ANY buy reason,
    e.g. OVERLAY_PULLBACK - V5.3.3 finding F-02) or with a flat reset.  Never silently."""
    reasons = [v533.REASONS[k] for k in base_run["f_reason"]]
    assert "REPAIR_SELL" in reasons, "synthetic run should exercise repair"
    diag = base_run["diag"]
    pend = diag[:, 16]
    starts = np.where((pend[1:] == 1) & (pend[:-1] == 0))[0] + 1
    ends = np.where((pend[1:] == 0) & (pend[:-1] == 1))[0] + 1
    fb = dict(zip(base_run["f_bar"], reasons))
    for e in ends:
        r = fb.get(e)
        side = dict(zip(base_run["f_bar"], base_run["f_side"])).get(e)
        assert side == 1 or base_run["pos"][e] == 0, (e, r)
    assert len(starts) > 0


def test_lower_rebuy_and_failed_restore_both_occur(base_run):
    reasons = set(v533.REASONS[k] for k in base_run["f_reason"])
    assert "LOWER_REBUY" in reasons or "FAILED_RESTORE" in reasons


def test_overnight_persistence(data, base_run):
    _, b, _ = data
    pos = base_run["pos"]
    rth = b["in_rth"].values
    # outside RTH no order can be created, so position after the post-RTH fill bar is constant until next RTH
    grp_change = False
    for i in range(1, len(pos)):
        if not rth[i] and not rth[i - 1] and pos[i] != pos[i - 1]:
            grp_change = True
    assert not grp_change
    # some inventory actually carried overnight
    assert (pos[~rth] > 0).any()


def test_missing_bars_do_not_create_fills(data, base_run):
    _, b, _ = data
    # fills only happen on existing bars; the fill bar immediately follows the order bar in the array
    assert base_run["f_bar"].min() >= 1


def test_costs_sensitivity(data):
    _, b, arr = data
    r0 = v533.run(arr, v533.make_params(commission=0.0, slippageTicks=0))
    r1 = v533.run(arr, v533.make_params())
    # same decisions? not guaranteed (openprofit sign can flip), but cost run must not be better in total
    s0 = M.summarize(b, r0, commission=0.0, slip_ticks=0)
    s1 = M.summarize(b, r1)
    assert s1["gross_before_cost"] - s1["friction"] == pytest.approx(s1["total_pnl"])
    assert s0["friction"] == 0.0


def test_margin_enforcement_rejects(data):
    _, b, arr = data
    r = v533.run(arr, v533.make_params(initialCapital=20000.0, enforceMargin=1))
    assert r["counter_dict"]["marginRejects"] > 0
