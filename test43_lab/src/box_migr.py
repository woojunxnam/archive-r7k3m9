"""Stateful migrating box machine (TEST72 / TEST73).  Per session, decisions at 1m closes; a box used at close j was built from bars < its birth.
UP1 ladder shift (new lo = old hi, new hi = old hi + w) / UP2 rebuild from the next completed obs-minute window / UP3 ladder shift then replaced by the
fresh window.  DOWN1 shift lower one width / DOWN2 fresh completed window / DOWN3 fresh window + 5 completed bars inside before tradable.
Never repaints: every box is fixed at birth; LO/HI[s, j] = box in force for the decision at close j."""
import numpy as np
from numba import njit


@njit(cache=True)
def machine(C, H, L, obs, ub, db, up_mode, dn_mode, stable_n, J15_, mig_delay=0):
    n, NGx = C.shape
    LO = np.full((n, NGx), np.nan); HI = np.full((n, NGx), np.nan); ID = np.full((n, NGx), -1, np.int64)
    DIR = np.full((n, NGx), 2, np.int64); TRD = np.zeros((n, NGx), np.int64)
    bid = 0
    for s in range(n):
        have = False; lo = 0.0; hi = 0.0; ps = 0; tf = 0; d = 2; pmid = np.nan; pw = np.nan; fromdown = False
        for j in range(J15_ + 1):
            if ps >= 0 and j == ps + obs:
                wl = 1e18; wh = -1e18
                for k in range(ps, j):
                    if L[s, k] < wl:
                        wl = L[s, k]
                    if H[s, k] > wh:
                        wh = H[s, k]
                if wh > wl:
                    if have or pmid == pmid:
                        x = ((wl + wh) / 2 - pmid) / pw
                        d = 1 if x > 0.25 else (-1 if x < -0.25 else 0)
                    lo = wl; hi = wh; have = True; bid += 1; tf = j + stable_n if (dn_mode == 3 and fromdown) else j; fromdown = False
                ps = -1
            if not have:
                continue
            LO[s, j] = lo; HI[s, j] = hi; ID[s, j] = bid; DIR[s, j] = d; TRD[s, j] = 1 if j >= tf else 0
            w = hi - lo; c = C[s, j]
            if c > hi + ub * w:
                pmid = (lo + hi) / 2; pw = w
                fromdown = False
                if up_mode == 2:
                    have = False; ps = j + 1 + mig_delay
                else:
                    lo = hi; hi = hi + w; bid += 1; d = 1; tf = j + 1 + mig_delay
                    if up_mode == 3:
                        ps = j + 1 + mig_delay
            elif c < lo - db * w:
                pmid = (lo + hi) / 2; pw = w
                if dn_mode == 1:
                    hi = lo; lo = lo - w; bid += 1; d = -1; tf = j + 1 + mig_delay; ps = -1
                else:
                    have = False; ps = j + 1 + mig_delay; fromdown = True
    return LO, HI, ID, DIR, TRD


@njit(cache=True)
def trade(C, FP, FPb, LO, HI, ID, DIR, TRD, LZ, UZ, buf, exit_mode, dir_req, cycles, delay, miss, J15_):
    """exit_mode 0 RANGE (top of entry box / break below entry box), 1 HOLD (entry-box break or 16:15), 2 TRAIL (close below the CURRENT box
    lower - buf*w, last known box if rebuilding, or 16:15).  dir_req: 9 = any box, 1 = RISING only.  cycles = max entries per box id."""
    n, NGx = C.shape
    out = np.full((n * 40, 8), np.nan); m = 0
    for s in range(n):
        j = 0; last_id = -1; cnt = 0; lastlo = np.nan; lastw = np.nan
        while j < J15_:
            b = ID[s, j]
            if b < 0 or TRD[s, j] == 0 or (dir_req != 9 and DIR[s, j] != dir_req):
                j += 1; continue
            if b != last_id:
                last_id = b; cnt = 0
            lo = LO[s, j]; hi = HI[s, j]; w = hi - lo; c = C[s, j]
            if cnt >= cycles or not (c >= lo and c <= lo + LZ * w) or miss[s, j] == 1:
                j += 1; continue
            ji = j + 1 + delay
            if ji >= J15_:
                break
            px = FP[s, ji]; reason = 3; jx = J15_
            for k in range(ji, J15_):
                ck = C[s, k]
                if exit_mode == 0 and ck >= lo + UZ * w:
                    reason = 1; jx = k + 1; break
                if exit_mode <= 1 and ck < lo - buf * w:
                    reason = 2; jx = k + 1; break
                if exit_mode == 2:
                    if lastlo != lastlo:
                        lastlo = lo; lastw = w
                    if ID[s, k] >= b and LO[s, k] > lastlo:          # ratchet up only (structural trailing lower boundary)
                        lastlo = LO[s, k]; lastw = HI[s, k] - LO[s, k]
                    if ck < lastlo - buf * lastw:
                        reason = 2; jx = k + 1; break
            if jx > J15_:
                jx = J15_
            out[m, 0] = s; out[m, 1] = ji; out[m, 2] = jx; out[m, 3] = px; out[m, 4] = FPb[s, jx]; out[m, 5] = reason
            out[m, 6] = b; out[m, 7] = cnt; m += 1; cnt += 1; j = jx
            lastlo = np.nan
            if reason == 2 and exit_mode == 0:
                last_id = b; cnt = cycles
    return out[:m]
