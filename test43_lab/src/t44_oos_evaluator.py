"""TEST44 NEW-OOS EVALUATOR — PREPARED, NOT RUN on OOS data.

Evaluates exactly four frozen candidates (CHAMPION_CONTROL_V1, SIMPLE_INTEGER_CHALLENGER, RIDGE_CHALLENGER,
XGBOOST_CHALLENGER) under TEST44_NEW_OOS_ACCEPTANCE_RULES.json (unchanged).  Fails closed on any integrity failure and
before 120 completed RTH sessions exist from 2026-05-28.

Real OOS use (future, separate authorised command only):
    python t44_oos_evaluator.py --oos-es ES_FULL.parquet --oos-mnq MNQ_FULL.parquet --confirm-open-new-oos
Mechanics dry run on already-USED historical data (no OOS data; pseudo window 2025-10-01..2026-05-27):
    python t44_oos_evaluator.py --dry-run-historical
Report-only additions: FROZEN_MODEL_PREFIX (OOS sessions 1-63) / ONLINE_REFIT_CONTINUATION (64+), champion legacy
CONSERVATIVE envelope, session-matched beta, integer sleeve attribution.  No strategy/model/allocation logic is changed.
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t44_common as TC  # noqa: E402

SRC = TC.SRC
FZ44 = os.path.join(TC.T44, "freeze")
PROT = os.path.join(TC.T44, "oos_protocol")
EXPECT = {"pre_oos_freeze": ("TEST44_PRE_OOS_FREEZE.json", "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4"),
          "new_oos_rules": ("TEST44_NEW_OOS_ACCEPTANCE_RULES.json", "2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236")}
CHAMPION_FINAL = os.path.join(TC.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")
CHAMPION_SHA = "3269dc94f5972854ac99ae1c7a45a6cc44b00987b46b279ddb2e16b13dc66fe7"
OOS_START = pd.Timestamp("2026-05-28")
HIST_END = pd.Timestamp("2026-05-27")
MIN_SESSIONS = 120
PREFIX_SESSIONS = 63
CANDIDATES = ("CHAMPION_CONTROL_V1", "SIMPLE_INTEGER_CHALLENGER", "RIDGE_CHALLENGER", "XGBOOST_CHALLENGER")
OUTPUT_SCHEMA = {
    "per_candidate": ["net_pnl", "avg_day", "median_day", "max_dd", "worst_day", "best_day", "avg_ex_top1", "avg_ex_top3", "avg_ex_top5",
                      "positive_day_share", "matched_beta_excess_per_day", "session_matched_beta_excess_per_day", "SLIP4", "TIMING_BRITTLENESS_STRESS",
                      "contract_sides_MES", "contract_sides_MNQ", "friction", "avg_MES", "avg_MNQ", "avg_rth_MES", "avg_on_MES", "avg_rth_MNQ",
                      "avg_on_MNQ", "peak_margin_util", "integer_sleeve_attribution", "absolute_pass (frozen MODERATE rules)",
                      "FROZEN_MODEL_PREFIX (OOS sessions 1-63) metrics", "ONLINE_REFIT_CONTINUATION (OOS sessions 64+) metrics"],
    "champion_only_report": "ORIGINAL_CHAMPION_CONSERVATIVE (MaxDD <= $10k, worst >= -$2k) - report only, not a TEST44 pass condition",
    "promotion": "each challenger vs CHAMPION per frozen rules; XGB vs RIDGE per frozen rule",
    "integrity": "all checks with values; FAIL CLOSED before any economics"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


class Closed(Exception):
    pass


def fail(msg, rep):
    rep["FAILED_CLOSED"] = msg
    raise Closed(msg)


# ----------------------------------------------------------------------------------------------- integrity
def static_integrity(rep):
    chk = {}
    for k, (fn, e) in EXPECT.items():
        chk[k] = sha(os.path.join(FZ44, fn)) == e
    fz = json.load(open(os.path.join(FZ44, EXPECT["pre_oos_freeze"][0])))
    for f, h in fz["code_sha256"].items():
        chk[f"code:{f}"] = sha(os.path.join(SRC, f)) == h
    for role, v in fz["meta_models"]["final_fits"].items():
        chk[f"model:{role}"] = sha(os.path.join(TC.ROOT, v["file"])) == v["sha256"]
    chk["champion_final_portfolios"] = sha(CHAMPION_FINAL) == CHAMPION_SHA
    ph = dict(l.split()[::-1] for l in open(os.path.join(PROT, "TEST44_OOS_DATA_PROTOCOL.sha256")).read().strip().splitlines())
    chk["oos_data_protocol_json"] = sha(os.path.join(PROT, "TEST44_OOS_DATA_PROTOCOL.json")) == ph["TEST44_OOS_DATA_PROTOCOL.json"]
    from t43 import sleeves as S
    C = S.candidates()
    for c, m in fz["sleeves"].items():
        chk[f"sleeve:{c}"] = S.cand_hash(C[c]) == m["sha256"] and C[c]["params"] == m["params"]
    for inst, (rel, h) in TC.DATA.items():
        chk[f"frozen_canonical:{inst}"] = sha(os.path.join(TC.ROOT, rel)) == h
    rep["static_integrity"] = chk
    if not all(chk.values()):
        fail("static integrity: " + ", ".join(k for k, v in chk.items() if not v), rep)
    return fz


def validate_delivery(paths, start, rep, dry):
    """Protocol validators on the delivered full-history files (hash recorded BEFORE parsing)."""
    out = {}
    lim = {"ES": 34.5, "MNQ": 53.0}
    for inst, p in paths.items():
        v = {"sha256_before_parse": sha(p), "bytes": os.path.getsize(p)}
        frozen = pd.read_parquet(os.path.join(TC.ROOT, TC.DATA[inst][0]))
        d = pd.read_parquet(p)
        v["schema_identical"] = list(d.columns) == list(frozen.columns) and all(str(d[c].dtype) == str(frozen[c].dtype) for c in frozen.columns)
        pre = d[d.session_date <= HIST_END].reset_index(drop=True)
        v["prefix_identical_to_frozen"] = len(pre) == len(frozen) and all(pre[c].equals(frozen[c]) for c in frozen.columns)
        new = d[d.session_date > HIST_END] if not dry else d[d.session_date >= start]
        mod = d.dt.dt.hour * 60 + d.dt.dt.minute
        v["monotonic_no_dup_whole_minutes"] = bool(d.dt.is_monotonic_increasing and not d.dt.duplicated().any() and (d.dt.dt.second == 0).all())
        v["no_maintenance_hour_bars"] = int(((mod > 1020) & (mod <= 1080)).sum()) == 0
        v["volume_positive"] = bool((d.v > 0).all())
        v["plus6h_and_cal_date"] = bool((d.session_date_plus6h == (d.dt + pd.Timedelta(hours=6)).dt.normalize()).all() and (d.cal_date == d.dt.dt.normalize()).all())
        v["cum_adj_constant_per_contract"] = bool((d.groupby("contract").cum_adjustment.nunique() == 1).all())
        sw = np.where(d.contract.values[1:] != d.contract.values[:-1])[0]
        v["switch_at_18:01"] = bool((d.dt.iloc[sw + 1].dt.strftime("%H:%M") == "18:01").all())
        ra = np.array(sorted(d[d.roll_adjacent].session_date.unique()), dtype="datetime64[ns]")
        v["roll_adjacent_equals_switch_sessions"] = bool(np.array_equal(ra, np.array(sorted(d.session_date.values[sw + 1]), dtype="datetime64[ns]")))
        v["switch_gap_within_2x_hist_max"] = bool((np.abs(d.o.values[sw + 1] - d.c.values[sw]) <= lim[inst]).all())
        v["ohlc_sane"] = bool(((d.l <= d[["o", "c"]].min(1)) & (d.h >= d[["o", "c"]].max(1)) & (d.l > 0)).all())
        v["new_rows_after_hist_end"] = int(len(new))
        out[inst] = v
    rep["delivery_validation"] = out
    bad = [f"{i}:{k}" for i, v in out.items() for k, x in v.items() if isinstance(x, bool) and not x]
    if bad:
        fail("delivery validation: " + ", ".join(bad), rep)


def completed_rth_sessions(start, end):
    from t43 import v6lab
    ok = None
    for inst in ("ES", "MNQ"):
        b, _ = v6lab.load(inst, end)
        s = set(b[(b.session_date >= start) & b.in_rth & (b["mod"] == 957)].session_date)
        ok = s if ok is None else ok & s
    return sorted(ok)


# ----------------------------------------------------------------------------------------------- engine plumbing
def point_loaders(paths, end, work):
    from t43 import bars as B, portfolio as PF, sleeves as S, v6lab
    os.makedirs(f"{work}/bars", exist_ok=True); os.makedirs(f"{work}/sleeves", exist_ok=True)
    for inst, p in paths.items():
        m1 = B.normalise_1m(pd.read_parquet(p))
        bb = B.add_clock(B.aggregate_3m(m1))
        if "cum_adjustment" in bb.columns:
            bb["raw_o"] = bb["o"] - bb["cum_adjustment"].astype(float)
        bb = bb[bb.session_date <= end].reset_index(drop=True)
        bp = f"{work}/bars/{inst}_3m.parquet"; bb.to_parquet(bp)
        v6lab.BARS[inst] = bp; S.PATHS3[inst] = bp
    v6lab._S.clear(); v6lab._C1.clear()
    PF.PDIR = f"{work}/sleeves"
    TC.END = end
    TC.setup = lambda rebuild=False: True          # loaders already point at the validated rebuild


def reference_bars_equal(paths, rep):
    """3m bars rebuilt from the delivered files equal the bars rebuilt from the frozen canonical files (<= 2026-05-27)."""
    from t43 import bars as B
    res = {}
    for inst, p in paths.items():
        a = B.add_clock(B.aggregate_3m(B.normalise_1m(pd.read_parquet(p))))
        b = B.add_clock(B.aggregate_3m(B.normalise_1m(pd.read_parquet(os.path.join(TC.ROOT, TC.DATA[inst][0])))))
        a = a[a.session_date <= HIST_END].reset_index(drop=True); b = b[b.session_date <= HIST_END].reset_index(drop=True)
        res[inst] = bool(len(a) == len(b) and all(a[c].equals(b[c]) for c in b.columns))
    rep["rebuilt_3m_prefix_identical"] = res
    if not all(res.values()):
        fail("3m prefix mismatch", rep)


def meta_scores(E, P, six, spec, s0, final_fit, dry):
    import t44_04_meta as MM
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    allf = sum(MM.FAM.values(), [])
    fsets = {"E_ALL": allf, "A_ONLY": MM.FAM["A"], **{f"E_minus_{k}": [f for f in allf if f not in v] for k, v in MM.FAM.items()}}
    feats = fsets[spec["features"]]
    hist, _ = MM.walk_forward(P, spec["model"], feats)
    pred = hist.where(P.sess_ix < s0)                              # frozen historical walk-forward, cut at the OOS start
    nS = int(P.sess_ix.max()) + 1

    def fit(train_end):
        tr = P[P.sess_ix < train_end - MM.PURGE].dropna(subset=feats + ["y"])
        X_ = tr[feats].values; y_ = np.clip(tr.y.values, -3, 3)
        if spec["model"] == "RIDGE":
            sc = StandardScaler().fit(X_); m = Ridge(alpha=MM.RIDGE_ALPHA).fit(sc.transform(X_), y_)
            return lambda Z: m.predict(sc.transform(Z))
        o = np.argsort(tr.sess_ix.values, kind="stable"); cut = int(len(tr) * 0.8)
        m = xgb.XGBRegressor(objective="reg:squarederror", random_state=7, n_jobs=4, early_stopping_rounds=40, **MM.XGB_PRESETS[spec["model"]])
        m.fit(X_[o[:cut]], y_[o[:cut]], eval_set=[(X_[o[cut:]], y_[o[cut:]])], verbose=False)
        return lambda Z: m.predict(Z)
    for b0 in range(s0, nS, MM.BLOCK):
        if b0 == s0 and not dry:
            f = final_fit                                             # frozen final fit (hash-verified)
        else:
            f = fit(b0)                                               # frozen procedure: expanding refit, 1-session purge
        te = P[(P.sess_ix >= b0) & (P.sess_ix < b0 + MM.BLOCK)].dropna(subset=feats)
        if len(te):
            pred.loc[te.index] = f(te[feats].values)
    return MM.score_arrays(E, P, pred, six, spec["usage"])


def load_final_fit(fz, role):
    info = fz["meta_models"]["final_fits"][role]
    p = os.path.join(TC.ROOT, info["file"])
    if role == "RIDGE_CHALLENGER":
        m = json.load(open(p))
        mean, scale, coef, b = np.array(m["scaler_mean"]), np.array(m["scaler_scale"]), np.array(m["coef"]), m["intercept"]
        return lambda Z: ((Z - mean) / scale) @ coef + b
    import xgboost as xgb
    m = xgb.XGBRegressor(); m.load_model(p)
    return lambda Z: m.predict(Z)


# ----------------------------------------------------------------------------------------------- metrics
def window_metrics(d, pos, T, mask_bars, c1, pv, tick, env="MODERATE"):
    import p07_acceptance as ACC
    x = d
    n = len(x)
    if n == 0:
        return {}
    mb = float((x.pES.mean() * c1["ES"].reindex(x.index).fillna(0) + x.pMNQ.mean() * c1["MNQ"].reindex(x.index).fillna(0)).mean())
    ev = ACC.evaluate(x, env, mb_avg=mb)
    top = x.pnl.sort_values(ascending=False)
    dpos = np.abs(np.diff(np.r_[[pos[0]], pos], axis=0))
    rth = T.rth.values
    o = {"sessions": n, "net_pnl": ev["total_net_pnl"], "avg_day": ev["avg_daily"], "median_day": float(x.pnl.median()), "max_dd": ev["max_dd"],
         "worst_day": ev["worst_day"], "best_day": ev["best_day"], "avg_ex_top1": float((x.pnl.sum() - top.iloc[:1].sum()) / n),
         "avg_ex_top3": ev["avg_ex_top3"], "avg_ex_top5": float((x.pnl.sum() - top.iloc[:5].sum()) / n),
         "positive_day_share": float((x.pnl > 0).mean()), "matched_beta_avg_day": mb, "matched_beta_excess_per_day": ev["avg_daily"] - mb,
         "return_dd": ev["avg_daily"] / ev["max_dd"] if ev["max_dd"] > 0 else None,
         "contract_sides_MES": float(dpos[mask_bars, 0].sum()), "contract_sides_MNQ": float(dpos[mask_bars, 1].sum()),
         "friction": float((dpos[mask_bars] * (0.62 + tick)).sum()),
         "avg_MES": float(pos[mask_bars, 0].mean()), "avg_MNQ": float(pos[mask_bars, 1].mean()),
         "avg_rth_MES": float(pos[mask_bars & rth, 0].mean()), "avg_on_MES": float(pos[mask_bars & ~rth, 0].mean()),
         "avg_rth_MNQ": float(pos[mask_bars & rth, 1].mean()), "avg_on_MNQ": float(pos[mask_bars & ~rth, 1].mean()),
         "peak_margin_util": float(x.mu_max.max()), "absolute_pass": ev["PASS"], "absolute_conditions": ev["conditions"]}
    return o


def attribution_window(E, r, dem, mask):
    FP = pd.read_csv(os.path.join(TC.ROOT, "out", "p", "p03_fingerprint_DEV.csv")).set_index("id")
    pos = r["pos"]; rows = []
    INSTS = ("ES", "MNQ")
    for k in range(2):
        members = sorted([c for c in dem if INSTS.index(E.inst[c]) == k], key=lambda c: FP.loc[c, "max_dd"])
        left = pos[:, k].astype(float).copy()
        dc = np.r_[0.0, np.diff(E.arr["c"][:, k])] * E.pv[k]
        for c in members:
            got = np.minimum(dem[c], left); left = left - got
            held = np.r_[0.0, got[:-1]]; den = dem[c] - got
            rows.append({"sleeve": c, "inst": INSTS[k], "avg_requested": float(dem[c][mask].mean()), "avg_received": float(got[mask].mean()),
                         "denied_share": float(den[mask].sum() / max(dem[c][mask].sum(), 1)),
                         "denied_by_governor_cut_share": float(((den > 0) & (r["cut"][:, k] > 0))[mask].mean()),
                         "gross_contribution": float((held * dc)[mask].sum())})
    return rows


# ----------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos-es"); ap.add_argument("--oos-mnq")
    ap.add_argument("--confirm-open-new-oos", action="store_true")
    ap.add_argument("--dry-run-historical", action="store_true")
    a = ap.parse_args(argv)
    dry = a.dry_run_historical
    rep = {"mode": "DRY_RUN_HISTORICAL (mechanics only; former TEST43 holdout window, already USED; NOT an OOS result)" if dry else "NEW_OOS",
           "rules_sha256": EXPECT["new_oos_rules"][1], "pre_oos_freeze_sha256": EXPECT["pre_oos_freeze"][1]}
    if not dry and not (a.oos_es and a.oos_mnq and a.confirm_open_new_oos):
        print("REFUSED: new-OOS evaluation requires --oos-es, --oos-mnq and --confirm-open-new-oos (separate authorised command)."); return 2
    start = pd.Timestamp("2025-10-01") if dry else OOS_START
    work = os.path.join(TC.T44, "oos_eval", "dry_run_historical" if dry else "new_oos")
    os.makedirs(work, exist_ok=True)
    try:
        fz = static_integrity(rep)
        paths = ({i: os.path.join(TC.ROOT, TC.DATA[i][0]) for i in ("ES", "MNQ")} if dry else {"ES": a.oos_es, "MNQ": a.oos_mnq})
        validate_delivery(paths, start, rep, dry)
        reference_bars_equal(paths, rep)
        end = max(pd.read_parquet(p, columns=["session_date"]).session_date.max() for p in paths.values())
        if dry:
            end = HIST_END
        point_loaders(paths, end, work)
        sess_ok = completed_rth_sessions(start, end)
        rep["completed_RTH_sessions"] = len(sess_ok)
        if len(sess_ok) < MIN_SESSIONS:
            fail(f"only {len(sess_ok)} completed RTH sessions (< {MIN_SESSIONS}); evaluation prohibited", rep)
        # ---------------- candidates
        from t43 import portfolio as PF, sleeves as S
        import p03_portfolio_dev as PD
        import t44_alloc as A
        import t44_04_meta as MM
        from t44_03_priority_loo import parse
        import p07_acceptance as ACC
        C = S.candidates()
        for cid in TC.ELIG:
            b, res, dd = S.run_sleeve(C[cid], end=end)
            pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "rth": b.in_rth.values, "pos": res["pos"].astype(float),
                          "desired": S.desired(res)}).to_parquet(f"{work}/sleeves/sleeve_{cid}.parquet")
        E = A.Engine(end=end)
        P, sess, six = MM.panel(E)
        s0 = int(sess.get_indexer([sess[sess >= start][0]])[0])
        runs = {}
        fin = json.load(open(CHAMPION_FINAL))
        champ = fin["portfolios"]["SECONDARY_2"]
        w = {c: m["contract_weight"] for c, m in champ["members"].items()}
        for tag, ex in (("BASE", {}), ("SLIP4", {"slip_ticks": 4}), ("TIMING_BRITTLENESS_STRESS", {"delay": 1})):
            r = E.bk.run(w, gov=PD.gov_for(champ["risk_envelope"], ex))
            runs[("CHAMPION_CONTROL_V1", tag)] = (r, E.daily(r), None)
        for role in CANDIDATES[1:]:
            spec = fz["challengers"][role]
            mode, rq, rk, cap = parse(spec["alloc_cfg"])
            sc = None
            if spec.get("model"):
                ff = None if dry else load_final_fit(fz, role)
                sc = meta_scores(E, P, six, spec, s0, ff, dry)
            REQ, X, dem = E.requests(**rq, score=sc)
            pr = E.priority("LOW_DD", dem)
            for tag, ex in (("BASE", {}), ("SLIP4", {"slip_ticks": 4}), ("TIMING_BRITTLENESS_STRESS", {"delay": 1})):
                r = E.run(mode, REQ, X, pr, caps=(cap, cap), **rk, **ex)
                runs[(role, tag)] = (r, E.daily(r), dem)
        # ---------------- historical reproduction (fail closed)
        repro = {}
        ref = {"CHAMPION_CONTROL_V1": "daily_CHAMPION_CONTROL_V1.csv", "SIMPLE_INTEGER_CHALLENGER": "daily_FINAL_SIMPLE_INTEGER_CHALLENGER.csv",
               "RIDGE_CHALLENGER": "daily_FINAL_RIDGE_CHALLENGER.csv", "XGBOOST_CHALLENGER": "daily_FINAL_XGBOOST_CHALLENGER.csv"}
        cut = start - pd.Timedelta(days=1)
        for role in CANDIDATES:
            d = runs[(role, "BASE")][1]; old = pd.read_csv(os.path.join(TC.T44, ref[role]), index_col=0, parse_dates=True)
            x = d[d.index <= cut].pnl; y = old.pnl.reindex(x.index)
            repro[role] = float((x - y).abs().max())
        rep["historical_daily_pnl_reproduction_max_abs_diff"] = repro
        if not all(v < 1e-6 for v in repro.values()):
            fail("historical daily P&L does not reproduce the frozen values", rep)
        # ---------------- economics (only after every check passed)
        T = E.T; sdT = pd.DatetimeIndex(T.sd.values)
        oos_sess = sess[sess >= start]
        pre_s = set(oos_sess[:PREFIX_SESSIONS]); post_s = set(oos_sess[PREFIX_SESSIONS:])
        c1 = E.c1; tick = E.tick
        res = {}
        daily_out = []
        for role in CANDIDATES:
            r, d, dem = runs[(role, "BASE")]
            win = d[d.index >= start]
            assert win.index.min() >= start, "pre-OOS date leaked into the OOS result"
            m_all = np.asarray(sdT >= start)
            o = window_metrics(win, r["pos"], T, m_all, c1, E.pv, tick)
            smb = ACC.session_matched_beta(T, r["pos"], d, start, end)
            o["session_matched_beta_excess_per_day"] = smb["excess_vs_session_matched_per_day"]
            for tag in ("SLIP4", "TIMING_BRITTLENESS_STRESS"):
                ds = runs[(role, tag)][1]; ds = ds[ds.index >= start]
                eq = np.r_[0.0, ds.pnl.cumsum().values]
                o[tag] = {"net_pnl": float(ds.pnl.sum()), "avg_day": float(ds.pnl.mean()), "max_dd": float((np.maximum.accumulate(eq) - eq).max())}
            for lab_, ss in (("FROZEN_MODEL_PREFIX", pre_s), ("ONLINE_REFIT_CONTINUATION", post_s)):
                wd = win[win.index.isin(ss)]
                mb_ = np.asarray(pd.Series(sdT).isin(ss))
                o[lab_] = window_metrics(wd, r["pos"], T, mb_, c1, E.pv, tick) if len(wd) else {}
            if role == "CHAMPION_CONTROL_V1":
                o["ORIGINAL_CHAMPION_CONSERVATIVE (report only)"] = {"max_dd_le_10000": o["max_dd"] <= 10000, "worst_day_ge_-2000": o["worst_day"] >= -2000}
                o["integer_sleeve_attribution"] = "n/a (fractional-weight TEST43 implementation; see TEST43 holdout attribution method)"
            else:
                o["integer_sleeve_attribution"] = attribution_window(E, r, dem, m_all)
            res[role] = o
            dw = win.copy(); dw.insert(0, "candidate", role); daily_out.append(dw)
        ch = res["CHAMPION_CONTROL_V1"]
        promo = {}
        for role in CANDIDATES[1:]:
            x = res[role]
            promo[role] = {"absolute_pass": x["absolute_pass"],
                           "ret_dd_ge_1.25x_champion": (x["return_dd"] or -1e9) >= 1.25 * (ch["return_dd"] or 1e9),
                           "matched_beta_excess_ge_champion": x["matched_beta_excess_per_day"] >= ch["matched_beta_excess_per_day"],
                           "session_matched_beta_excess_ge_champion": x["session_matched_beta_excess_per_day"] >= ch["session_matched_beta_excess_per_day"],
                           "net_pnl_ge_0.8x_champion": x["net_pnl"] >= 0.8 * ch["net_pnl"], "SLIP4_positive": x["SLIP4"]["net_pnl"] > 0}
            promo[role]["PROMOTE_OVER_CHAMPION"] = all(promo[role].values())
        xg, rd = res["XGBOOST_CHALLENGER"], res["RIDGE_CHALLENGER"]
        promo["XGB_vs_RIDGE_rule"] = (xg["return_dd"] or -1e9) >= 1.25 * (rd["return_dd"] or 1e9) and xg["net_pnl"] >= 1.25 * rd["net_pnl"]
        promo["XGBOOST_CHALLENGER"]["PROMOTE_OVER_CHAMPION"] &= promo["XGB_vs_RIDGE_rule"]
        rep["results"] = res; rep["promotion"] = promo
        rep["oos_window"] = [str(start.date()), str(end.date())]
        pd.concat(daily_out).to_csv(f"{work}/TEST44_OOS_DAILY.csv")
    except Closed as e:
        print("FAILED CLOSED:", e)
    json.dump(rep, open(f"{work}/TEST44_OOS_RESULT.json", "w"), indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
    print(json.dumps({k: rep[k] for k in rep if k not in ("results", "static_integrity", "delivery_validation")}, indent=1, default=str)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
