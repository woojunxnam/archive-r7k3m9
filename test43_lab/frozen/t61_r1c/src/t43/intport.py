"""TEST44 integer-aware portfolio engine.  Integer contracts ARE the model: no fractional target is ever executed.

Modes (per bar, decided at the bar close, executed at the next bar open):
  0 REQUEST   : integer MES/MNQ requests supplied (from 0/1/2 sleeve demands, cluster slots, ...)
  1 TRACK     : integer pair (q_ES, q_MNQ) in [0..cap] chosen by exhaustive search minimising
                risk-weighted tracking error to a desired float state + cluster-share imbalance + turnover penalty,
                subject to HARD constraints (caps, margin, $ATR budget x governor multiplier)
  2 RESIDUAL  : error-diffusion toward a desired float state; changes only at epochs of H bars, at most K changes
                per instrument per session, residual clipped (anti wind-up)
Shared-account governor (all modes): one $150k equity; DD tiers scale the $ATR budget (x m1 / x m2), day-loss cut,
margin (raw price x IBKR fraction; overnight fraction when the next bar is not RTH), per-symbol caps.  When the budget
binds, contracts are removed one at a time from the instrument with the LOWER priority (prio array, higher = keep).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit


@njit(cache=True)
def _atr_cost(q0, q1, pv, atr, i):
    return q0 * pv[0] * atr[i, 0] + q1 * pv[1] * atr[i, 1]


@njit(cache=True)
def _margin(q0, q1, raw, pv, fr, i):
    return q0 * raw[i, 0] * pv[0] * fr[0] + q1 * raw[i, 1] * pv[1] * fr[1]


@njit(cache=True)
def kernel(mode, o, c, raw, valid, roll, atrD, rth, sessid, REQ, X, XC, prio, caps, pv, fin, fon, rollc, INIT, marginU,
           dd1, dd2, m1, m2, dayStop, dayMult, slip, comm, delay, lam, mu, H, K, budget_frac, rearm):
    n = o.shape[0]
    pos = np.zeros(2, np.int64); avg = np.zeros(2); realized = 0.0
    pend = np.zeros(2, np.int64); pendAt = np.full(2, -1, np.int64)
    pos_arr = np.zeros((n, 2), np.int64); eq_arr = np.zeros(n); mu_arr = np.zeros(n); atr_arr = np.zeros(n)
    gov_arr = np.zeros(n); req_arr = np.zeros((n, 2), np.int64); cut_arr = np.zeros((n, 2), np.int64)
    sides = np.zeros(2); fills = np.zeros(2, np.int64)
    hwm = INIT; level = 0; sessStart = INIT; dayCut = False; prev_eq = INIT; since = 0
    resid = np.zeros(2); held = np.zeros(2, np.int64); nchg = np.zeros(2, np.int64); lastEpoch = -1
    fr = np.zeros(2)
    for i in range(n):
        newSess = i == 0 or sessid[i] != sessid[i - 1]
        for k in range(2):
            if pend[k] != 0 and valid[i, k] and i - pendAt[k] >= 1 + delay:
                q = pend[k]
                px = o[i, k] + slip if q > 0 else o[i, k] - slip
                if q > 0:
                    avg[k] = (avg[k] * pos[k] + px * q) / (pos[k] + q)
                else:
                    realized += (px - avg[k]) * pv[k] * (-q)
                pos[k] += q
                realized -= abs(q) * comm
                sides[k] += abs(q); fills[k] += 1
                if pos[k] == 0:
                    avg[k] = 0.0
                pend[k] = 0; pendAt[k] = -1
        if newSess:
            for k in range(2):
                if roll[i, k] and pos[k] > 0:
                    realized -= pos[k] * rollc[k]
            nchg[:] = 0
        eq = INIT + realized
        for k in range(2):
            if pos[k] > 0:
                eq += (c[i, k] - avg[k]) * pv[k] * pos[k]
        if newSess:
            sessStart = prev_eq; dayCut = False
            # time-based rearm: after `rearm` sessions at a reduced tier, restore and reset the high-water mark
            if level > 0:
                since += 1
                if since >= rearm or hwm - eq < 0.5 * dd1:
                    level = 0; hwm = max(eq, 0.0) if since >= rearm else max(hwm, eq); since = 0
        if level == 0 and eq > hwm:
            hwm = eq
        dd = hwm - eq
        if dd2 > 0 and dd >= dd2:
            if level < 2:
                since = 0
            level = max(level, 2)
        elif dd1 > 0 and dd >= dd1:
            if level < 1:
                since = 0
            level = max(level, 1)
        g = 1.0 if level == 0 else (m1 if level == 1 else m2)
        if dayStop > 0 and eq - sessStart <= -dayStop:
            dayCut = True
        if dayCut:
            g *= dayMult
        onSide = (not rth[i]) or (i + 1 < n and not rth[i + 1])
        for k in range(2):
            fr[k] = fon[k] if onSide else fin[k]
        budget = g * budget_frac * _atr_cost(caps[0], caps[1], pv, atrD, i)
        lim = marginU * max(eq, 0.0)
        q = np.zeros(2, np.int64)
        # ------------------------------------------------ requested integer targets
        if mode == 0:
            for k in range(2):
                q[k] = min(max(REQ[i, k], 0), caps[k])
        elif mode == 1:
            best = 1e300; b0 = pos[0]; b1 = pos[1]
            w1 = (pv[1] * atrD[i, 1]) / max(pv[0] * atrD[i, 0], 1e-9)
            xs = X[i, 0] + w1 * X[i, 1]
            for a in range(caps[0] + 1):
                for b in range(caps[1] + 1):
                    if _atr_cost(a, b, pv, atrD, i) > budget + 1e-9 or _margin(a, b, raw, pv, fr, i) > lim:
                        continue
                    err = (a - X[i, 0]) ** 2 + (w1 * (b - X[i, 1])) ** 2
                    tot = a + w1 * b
                    if xs > 1e-9 and tot > 1e-9:
                        err += mu * (a / tot - X[i, 0] / xs) ** 2
                    err += lam * (abs(a - pos[0]) + w1 * abs(b - pos[1]))
                    if err < best - 1e-12:
                        best = err; b0 = a; b1 = b
            q[0] = b0; q[1] = b1
        else:
            for k in range(2):
                resid[k] += X[i, k] - held[k]
                lim_r = H * caps[k]
                resid[k] = min(max(resid[k], -lim_r), lim_r)
            if lastEpoch < 0 or i - lastEpoch >= H:
                lastEpoch = i
                for k in range(2):
                    tgt = int(math.floor(X[i, k] + resid[k] / H + 0.5))
                    tgt = min(max(tgt, 0), caps[k])
                    if tgt != held[k] and nchg[k] < K:
                        held[k] = tgt; nchg[k] += 1
            for k in range(2):
                q[k] = held[k]
        for k in range(2):
            req_arr[i, k] = q[k]
        # ------------------------------------------------ hard governor (budget, margin): drop lowest-priority first
        guard = 0
        while (_atr_cost(q[0], q[1], pv, atrD, i) > budget + 1e-9 or _margin(q[0], q[1], raw, pv, fr, i) > lim) and guard < 100:
            guard += 1
            k = 0 if prio[i, 0] < prio[i, 1] else 1
            if q[k] == 0:
                k = 1 - k
            if q[k] == 0:
                break
            q[k] -= 1; cut_arr[i, k] += 1
        for k in range(2):
            if q[k] != pos[k] and pend[k] == 0:
                pend[k] = q[k] - pos[k]; pendAt[k] = i
        u = 0.0
        for k in range(2):
            u += pos[k] * raw[i, k] * pv[k] * (fon[k] if not rth[i] else fin[k])
        mu_arr[i] = u / max(eq, 1.0); atr_arr[i] = _atr_cost(pos[0], pos[1], pv, atrD, i); gov_arr[i] = g
        for k in range(2):
            pos_arr[i, k] = pos[k]
        eq_arr[i] = eq; prev_eq = eq
    return pos_arr, eq_arr, mu_arr, atr_arr, gov_arr, req_arr, cut_arr, sides, fills
