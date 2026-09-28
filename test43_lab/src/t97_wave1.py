"""TEST97 Wave 1 (prereg d6fb544b): M01-M10 event studies on ES / NQ / YM / RTY with null hierarchy, response curves, family-specific nulls,
timing attribution.  Outputs tables in out/t97 and reports/TEST97_PLUS; every variant is logged to the research ledger."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E  # noqa: E402

M = E.markets(); INSTS = E.INSTS
ALL = []; YRS = []; CURVES = []; NOTES = {}
KEYS = ["h1", "h3", "h6", "h12", "h1615"]


def shift(mask, k):
    """event at bar b+k derived from condition at b (within session)."""
    out = np.zeros_like(mask)
    if k > 0:
        out[:, k:] = mask[:, :-k]
    return out


def run(name, evs, fam, src, cls, nulls=("A",), family_null=None):
    rows, yrs = E.study(name, evs, nulls=nulls, family_null=family_null)
    P = rows[-1]; P["EDGE_h12_A"] = E.edge(P, "h12", "A"); P["EDGE_h6_A"] = E.edge(P, "h6", "A"); P["EDGE_h1615_A"] = E.edge(P, "h1615", "A")
    if "B" in nulls:
        P["EDGE_h12_B"] = E.edge(P, "h12", "B")
    for r in rows:
        r["family"] = fam
    ALL.extend(rows); YRS.extend(yrs); E.ledger(rows, fam, src, cls)
    return rows


def strong(m, bp=0.6, cp=0.8, ra=1.25):
    return m.bull & (m.body_pct >= bp) & (m.cpos >= cp) & (m.rng_atr5 >= ra)


def curve(fam, feat, edges, base, nulls=("A", "B")):
    """1D response: pooled excess per bin (bins [e_i, e_{i+1}))."""
    for lo, hi in zip(edges[:-1], edges[1:]):
        evs = {k: base(M[k]) & (getattr(M[k], feat) >= lo) & (getattr(M[k], feat) < hi) for k in INSTS}
        rows, _ = E.study(f"{fam}:{feat}[{lo},{hi})", evs, nulls=nulls, horizons=["h3", "h6", "h12", "h1615"])
        P = rows[-1]; E.ledger(rows, fam, "", "curve")
        CURVES.append({"family": fam, "feature": feat, "bin": f"[{lo},{hi})", "n": P["n_events"], **{f"{h}_mean": P[f"{h}_mean"] for h in ("h3", "h6", "h12", "h1615")},
                       **{f"{h}_x{nl}": P[f"{h}_x{nl}"] for h in ("h6", "h12", "h1615") for nl in nulls},
                       "h12_xA_lo": P["h12_xA_lo"], "h12_xA_hi": P["h12_xA_hi"], "cost_atr": P["cost_atr"],
                       **{f"{k}_h12_xA": r_["h12_xA"] for k, r_ in zip(INSTS, rows[:-1])}})


def main():
    # ---------------------------------------------------------------- M01 strong bull bar: response curves (null A and B)
    bull = lambda m: m.bull
    curve("M01", "body_pct", [0.5, 0.6, 0.7, 0.8, 0.9, 1.01], lambda m: m.bull & (m.cpos >= 0.7))
    curve("M01", "cpos", [0.7, 0.8, 0.9, 0.95, 1.01], lambda m: m.bull & (m.body_pct >= 0.5))
    curve("M01", "rng_atr5", [0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 99], lambda m: m.bull & (m.body_pct >= 0.5) & (m.cpos >= 0.7))
    for bp in (0.5, 0.7, 0.9):                                   # sparse 2D body x range
        curve("M01_2D_body>=%.1f" % bp, "rng_atr5", [0.75, 1.25, 2.0, 99], lambda m, bp=bp: m.bull & (m.body_pct >= bp) & (m.cpos >= 0.7))
    run("M01_STRONG_canonical", {k: strong(M[k]) for k in INSTS}, "M01", "Brooks strong bull bar [SOURCE principle / FORMAL thresholds]", "NEW_EVENT_STUDY",
        nulls=("A", "B"))
    # ---------------------------------------------------------------- M02 strong + rolling breakout (scale family) vs strong without breakout
    for N in (2, 4, 6, 8, 12, 20, 30, 60):
        run(f"M02_STRONG_BRK{N}", {k: strong(M[k]) & (M[k].c > M[k].prevhi[N]) for k in INSTS}, "M02", "Brooks / Donchian [FORMAL]", "PARTIALLY_COVERED",
            nulls=("A", "B"), family_null={k: strong(M[k]) & ~(M[k].c > M[k].prevhi[12]) for k in INSTS})
    run("M02_BRK12_ANY_BAR (basic momentum, no strength)", {k: (M[k].c > M[k].prevhi[12]) & ~strong(M[k]) for k in INSTS}, "M02", "control", "control", nulls=("A", "B"))
    # ---------------------------------------------------------------- M03 compression + surprise burst vs same-size burst without compression
    for k in INSTS:
        m = M[k]; w = (m.prevhi[12] - m.prevlo12) / m.a[:, None]
        pct = pd.DataFrame(w).rolling(60, min_periods=30).rank(pct=True).shift(1).values  # per bar index over prior 60 sessions
        m.comp_pct = pct
        m.burst = m.bull & (m.h - m.l >= 2 * m.medr20) & (m.cpos >= 0.8) & (m.c > m.prevhi[12])
        m.burst_dec = np.digitize(np.nan_to_num((m.h - m.l) / m.a[:, None]), np.nanpercentile(((m.h - m.l) / m.a[:, None])[m.burst & m.valid], [20, 40, 60, 80]))
    for lab, lo, hi in (("LOW_COMP", 0, 1 / 3), ("MID_COMP", 1 / 3, 2 / 3), ("HIGH_COMP", 2 / 3, 1.01)):
        run(f"M03_BURST_{lab}", {k: M[k].burst & (M[k].comp_pct >= lo) & (M[k].comp_pct < hi) for k in INSTS}, "M03", "Crabel / Hougaard surprise [FORMAL]",
            "PARTIALLY_COVERED", nulls=("A", "B"))
    # burst-size-matched compression value: per burst-size quintile, low-comp minus high-comp (pooled means)
    cv = []
    for q in range(5):
        lo_ = E.study(f"M03_q{q}_LOW", {k: M[k].burst & (M[k].burst_dec == q) & (M[k].comp_pct < 1 / 3) for k in INSTS}, horizons=["h6", "h12", "h1615"])[0][-1]
        hi_ = E.study(f"M03_q{q}_HIGH", {k: M[k].burst & (M[k].burst_dec == q) & (M[k].comp_pct >= 2 / 3) for k in INSTS}, horizons=["h6", "h12", "h1615"])[0][-1]
        cv.append({"burst_size_quintile": q, "n_low": lo_["n_events"], "n_high": hi_["n_events"], **{f"{h}_low_minus_high": lo_[f"{h}_mean"] - hi_[f"{h}_mean"] for h in ("h6", "h12", "h1615")},
                   **{f"{h}_xA_low": lo_[f"{h}_xA"] for h in ("h12",)}, **{f"{h}_xA_high": hi_[f"{h}_xA"] for h in ("h12",)}})
    NOTES["M03_compression_value_by_burst_size"] = cv
    # ---------------------------------------------------------------- M04 follow-through + timing attribution
    base = {k: strong(M[k]) & (M[k].c > M[k].prevhi[12]) for k in INSTS}
    conf = {"B_next_bull": lambda m: m.bull, "C_next_close_gt": lambda m: m.c > np.concatenate([m.c[:, :1], m.c[:, :-1]], 1),
            "E_next_HH_HL": lambda m: (m.h > np.concatenate([m.h[:, :1], m.h[:, :-1]], 1)) & (m.l > np.concatenate([m.l[:, :1], m.l[:, :-1]], 1)),
            "F_next_STRONG": lambda m: strong(m)}
    att = []
    for cname, fn in conf.items():
        ev_c = {k: shift(base[k], 1) & fn(M[k]) for k in INSTS}; ev_u = {k: shift(base[k], 1) & ~fn(M[k]) for k in INSTS}
        rc = run(f"M04_{cname}_confirmed", ev_c, "M04", "Brooks follow-through [FORMAL]", "NEW_EVENT_STUDY"); ru = E.study(f"M04_{cname}_unconfirmed", ev_u)[0]
        nxt = lambda a: np.concatenate([a[:, 1:], np.zeros((a.shape[0], 1), bool)], 1)
        orig = E.study(f"M04_{cname}_orig_entry_of_confirmed", {k: base[k] & nxt(fn(M[k])) for k in INSTS}, horizons=["h6", "h12"])[0]
        for rC, rU, rO in zip(rc, ru, orig):
            att.append({"confirm": cname, "instrument": rC["instrument"], "n_conf": rC["n_events"], "n_unconf": rU["n_events"],
                        "info_h6": rC["h6_mean"] - rU["h6_mean"], "info_h12": rC["h12_mean"] - rU["h12_mean"],
                        "conf_entry_h12": rC["h12_mean"], "orig_entry_same_events_h12 (exits 1 bar earlier)": rO["h12_mean"]})
    ev_d = {k: shift(base[k], 2) & M[k].bull & shift(M[k].bull, 1) for k in INSTS}; run("M04_D_two_bull_followthrough", ev_d, "M04", "Brooks", "NEW_EVENT_STUDY")
    NOTES["M04_attribution"] = att
    # ---------------------------------------------------------------- M05 impulse -> pullback -> second leg (depth response)
    sl = []
    for k in INSTS:
        m = M[k]; imp = base[k]; ev = np.zeros_like(imp); depth = np.full(imp.shape, np.nan); hold = np.zeros_like(imp)
        for s, b0 in zip(*np.where(imp & m.valid)):
            H0, L0 = m.h[s, b0], m.l[s, b0]; lo = np.inf
            for b in range(b0 + 1, min(b0 + 8, E.NB - 1)):
                if b == b0 + 1 and m.h[s, b] > H0:
                    break                                          # immediate continuation: no pullback
                if b >= b0 + 2 and m.c[s, b] > m.h[s, b - 1] and m.bull[s, b]:
                    ev[s, b] = True; depth[s, b] = (H0 - lo) / max(H0 - L0, 1e-9); break   # resumption (lo = pullback bars only)
                lo = min(lo, m.l[s, b])
                if m.h[s, b] > H0:
                    break                                          # new high without a clean resumption bar
        m.m05 = ev; m.m05_depth = depth
    for lo_, hi_ in ((0, .25), (.25, .382), (.382, .5), (.5, .618), (.618, .75), (.75, 9)):
        r = run(f"M05_SECOND_LEG_depth[{lo_},{hi_})", {k: M[k].m05 & (M[k].m05_depth >= lo_) & (M[k].m05_depth < hi_) for k in INSTS}, "M05",
                "Brooks / Raschke / Grimes second leg [FORMAL]", "PARTIALLY_COVERED")
    run("M05_SECOND_LEG_all", {k: M[k].m05 for k in INSTS}, "M05", "", "PARTIALLY_COVERED", family_null={k: base[k] for k in INSTS})
    # ---------------------------------------------------------------- M06 failed first -> fresh second signal
    for k in INSTS:
        m = M[k]; first = np.zeros_like(base[k]); second = np.zeros_like(base[k]); later_first_ok = np.zeros_like(base[k])
        for s in np.where(m.full)[0]:
            bs = np.where(base[k][s])[0]
            if not len(bs):
                continue
            b1 = bs[0]; first[s, b1] = True; lvl = m.prevhi[12][s, b1]
            fail = [b for b in range(b1 + 1, min(b1 + 7, E.NB)) if m.c[s, b] < lvl]
            if fail:
                nxt = [b for b in bs if b > fail[0]]
                if nxt:
                    second[s, nxt[0]] = True
        m.m06_first, m.m06_second = first, second
    run("M06_FIRST_SIGNAL", {k: M[k].m06_first for k in INSTS}, "M06", "OURS", "FRESH")
    run("M06_SECOND_AFTER_FAILURE", {k: M[k].m06_second for k in INSTS}, "M06", "OURS", "FRESH", family_null={k: M[k].m06_first for k in INSTS})
    # ---------------------------------------------------------------- M07 microchannel vs single bar (null B = magnitude)
    for kk in (2, 3, 4):
        evs = {}
        for k in INSTS:
            m = M[k]; prevc = np.concatenate([m.c[:, :1], m.c[:, :-1]], 1); prevl = np.concatenate([m.l[:, :1], m.l[:, :-1]], 1)
            ok = m.bull & (m.l > prevl) & (m.cpos >= 0.5) & (m.l >= prevc - 0.1 * m.atr5)
            run_ = ok.copy()
            for q in range(1, kk):
                run_ &= shift(ok, q)
            evs[k] = run_
        run(f"M07_MICROCHANNEL_{kk}", evs, "M07", "Brooks microchannel [FORMAL]", "FRESH", nulls=("A", "B"))
    # ---------------------------------------------------------------- M08 opening momentum (close-confirmed ORB) vs later session-high break
    for orb in (1, 2, 3, 6):
        evs = {}; evs_s = {}
        for k in INSTS:
            m = M[k]; orh = np.max(m.h[:, :orb], 1)[:, None]; brk = (m.c > orh) & (m.bidx >= orb) & (m.bidx < 18)
            first = brk & (np.cumsum(brk, 1) == 1); evs[k] = first; evs_s[k] = first & strong(m)
        run(f"M08_ORB{orb * 5}m", evs, "M08", "Crabel ORB [FORMAL, close-confirmed]", "PARTIALLY_COVERED")
        run(f"M08_ORB{orb * 5}m_STRONG", evs_s, "M08", "", "PARTIALLY_COVERED")
    evs = {}
    for k in INSTS:
        m = M[k]; sh = np.maximum.accumulate(m.h, 1); prev_sh = np.concatenate([np.full((m.n, 1), np.inf), sh[:, :-1]], 1)
        brk = (m.c > prev_sh) & (m.bidx >= 18); evs[k] = brk & (np.cumsum(brk, 1) == 1)
    run("M08_LATE_SESSION_HIGH_BREAK (comparison)", evs, "M08", "", "control")
    # ---------------------------------------------------------------- M09 HTF alignment on M02 N=12
    htf = []
    for nm, fn in (("above_VWAP", lambda m: m.c > m.vwap), ("above_open", lambda m: m.c > m.open0[:, None]), ("above_PDH", lambda m: m.c > m.pdh[:, None]),
                   ("last60m_up", lambda m: m.c > np.concatenate([np.full((m.n, 12), np.nan), m.c[:, :-12]], 1))):
        ra = run(f"M09_{nm}_ALIGNED", {k: base[k] & fn(M[k]) for k in INSTS}, "M09", "multi-timeframe [FORMAL]", "PARTIALLY_COVERED")[-1]
        rn = E.study(f"M09_{nm}_NOT", {k: base[k] & ~fn(M[k]) for k in INSTS})[0][-1]
        htf.append({"state": nm, "n_aligned": ra["n_events"], "n_not": rn["n_events"], **{f"{h}_aligned_minus_not_xA": ra[f"{h}_xA"] - rn[f"{h}_xA"] for h in ("h6", "h12", "h1615")}})
    NOTES["M09_incremental"] = htf
    # ---------------------------------------------------------------- M10 extension / exhaustion curves on STRONG
    for k in INSTS:
        m = M[k]; m.ext_vwap = (m.c - m.vwap) / m.a[:, None]; m.ext_ema = (m.c - m.ema20) / m.a[:, None]; m.ext_open = (m.c - m.open0[:, None]) / m.a[:, None]
    for f in ("ext_vwap", "ext_ema", "ext_open"):
        curve("M10", f, [-9, 0, 0.5, 1.0, 1.5, 2.0, 99], lambda m: strong(m), nulls=("A",))
    # ---------------------------------------------------------------- outputs
    R = pd.DataFrame(ALL); R.to_csv(os.path.join(E.OUT, "WAVE1_EVENTS.csv"), index=False)
    C = pd.DataFrame(CURVES); C.to_csv(os.path.join(E.OUT, "WAVE1_CURVES.csv"), index=False)
    Y = pd.DataFrame(YRS); Y.to_csv(os.path.join(E.OUT, "WAVE1_YEARS.csv"), index=False)
    json.dump(NOTES, open(os.path.join(E.OUT, "WAVE1_NOTES.json"), "w"), indent=1, default=float)
    P = R[R.instrument == "POOLED"]
    cols = ["variant", "n_events", "h1_mean", "h6_mean", "h12_mean", "h1615_mean", "h6_xA", "h12_xA", "h12_xA_lo", "h12_xA_hi", "h12_xA_years_pos", "h12_xB", "h1615_xA",
            "cost_atr", "newhigh60", "bar050", "EDGE_h6_A", "EDGE_h12_A", "EDGE_h1615_A", "EDGE_h12_B"]
    E.md("T97_W1_EVENTS_POOLED.md", "TEST97 Wave 1 - pooled event results (ATR_d units)", [P[[c for c in cols if c in P]]])
    ci = ["variant", "instrument", "n_events", "h6_mean", "h12_mean", "h12_xA", "h12_xB", "h1615_xA", "cost_atr", "mfe60", "mae60", "mae60_p95", "bar025", "bar050",
          "newhigh60", "underwater_1615"]
    E.md("T97_W1_EVENTS_BY_INSTRUMENT.md", "TEST97 Wave 1 - per instrument", [R[R.instrument != "POOLED"][[c for c in ci if c in R]]])
    E.md("T97_W1_RESPONSE_CURVES.md", "TEST97 Wave 1 - response curves (pooled)", [C])
    E.md("T97_W1_NOTES.md", "TEST97 Wave 1 - attribution notes", ["```json\n" + json.dumps(NOTES, indent=1, default=float) + "\n```"])
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(P[[c for c in cols if c in P]].to_string()); print(C[["family", "feature", "bin", "n", "h6_xA", "h12_xA", "h12_xB" if "h12_xB" in C else "h12_xA", "h1615_xA", "cost_atr"]].to_string())
    print(json.dumps(NOTES, indent=0, default=float)[:6000])


if __name__ == "__main__":
    main()
