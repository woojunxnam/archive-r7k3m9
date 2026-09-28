"""TEST65+ additive-alpha program shared layer.  Research data <= 2026-05-27 ONLY.  The baseline is the permanently frozen T61-R1C
(frozen/t61_r1c, verified fail-closed on import); every module is judged standalone AND as T61-R1C + module (incremental).
New code only - no frozen file is modified."""
import datetime
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402
import prog_common as P  # noqa: E402

LAB = os.path.abspath(C45.ROOT)
sys.path.insert(0, os.path.join(LAB, "frozen", "t61_r1c"))
import verify_frozen  # noqa: E402

verify_frozen.verify(check_live=True, quiet=True)                         # fail closed if T61-R1C was touched

OUT = os.path.join(LAB, "out", "TEST65_PLUS"); os.makedirs(OUT, exist_ok=True)
REP = os.path.join(LAB, "reports", "TEST65_PLUS"); os.makedirs(REP, exist_ok=True)
T61H = os.path.join(LAB, "out", "test65", "t61_hist")
START = pd.Timestamp("2019-07-01"); S21 = pd.Timestamp("2021-01-01"); END = pd.Timestamp("2026-05-27")
REG = {k: os.path.join(OUT, f"{k}.csv") for k in ("TEST65_PLUS_RESEARCH_REGISTRY", "TEST65_PLUS_REJECT_REGISTRY", "TEST65_PLUS_CLUE_REGISTRY",
                                                  "TEST65_PLUS_SURVIVOR_LIBRARY", "T61_INCREMENTAL_PORTFOLIO_FRONTIER")}
T61_REF = {"avg_day": 125.08, "max_dd": 12607.0, "worst_day": -4347.0, "ret_dd": 0.0099}
MNQ_CAP = 6; MES_CAP_TOTAL = 8; MODULE_MES_MAX = 2


def reg_append(name, rows, key=None):
    p = REG[name]
    df = pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    if key:
        df = df.drop_duplicates(key, keep="last")
    df.to_csv(p, index=False)


def prereg(test, spec):
    return P.prereg(test, {"program": "TEST65+ ADDITIVE ALPHA (baseline = frozen T61-R1C)", **spec})


def t61_daily():
    """frozen T61-R1C / C43 / T55 daily $ over the research history (from the fail-closed shadow replay)."""
    R = pd.read_csv(os.path.join(T61H, "daily_report.csv"), parse_dates=["date"])
    return {k: g.set_index("date") for k, g in R.groupby("portfolio")}


def t61_minutes(cols=("final_target_MES", "final_target_MNQ", "clamped_TEST53")):
    """session x 405 grid arrays of the frozen T61-R1C broker-model targets."""
    cache = os.path.join(OUT, "t61_minutes.npz")
    if os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        return pd.DatetimeIndex(z["sess"]), {c: z[c] for c in cols}
    L = pd.read_csv(os.path.join(T61H, "session_log_T61-R1C.csv.gz"), usecols=["session", *cols], parse_dates=["session"])
    sess = pd.DatetimeIndex(L.session.unique())
    out = {c: L[c].values.reshape(len(sess), C45.NG) for c in cols}
    np.savez_compressed(cache, sess=sess.values, **out)
    return sess, out


def risk(x):
    return P.risk(np.asarray(x, float))


def incremental_gate(name, d_mod, d_t61, sess, extra=None):
    """preregistered TEST65+ portfolio incremental gate: T61-R1C vs T61-R1C + module (daily $ arrays aligned to sess)."""
    extra = dict(extra or {})
    full = np.asarray(sess >= START); m21 = np.asarray(sess >= S21)
    comb = d_t61 + d_mod
    rc, rb = risk(comb[full]), risk(d_t61[full])
    inc = d_mod
    folds = {}
    for nm, a, b in C45.OUTER[:5]:
        mm = np.asarray((sess >= pd.Timestamp(a)) & (sess <= pd.Timestamp(min(pd.Timestamp(b), END))))
        folds[nm] = float(inc[mm].mean())
    act = inc[full & (inc != 0)]; top = np.sort(act)[::-1]
    yr = pd.Series(inc[full], index=sess[full]).groupby(sess[full].year).sum()
    pos_tot = yr[yr > 0].sum()
    lo = d_t61 < np.percentile(d_t61[full], 10)
    o = {"module": name, "standalone_avg_day": float(inc[full].mean()), "standalone_maxdd": risk(inc[full])["max_dd"], "standalone_worst": float(inc[full].min()),
         "incr_avg_day": float(inc[full].mean()), "incr_avg_day_2021": float(inc[m21].mean()),
         "comb_avg_day": rc["avg_day"], "comb_maxdd": rc["max_dd"], "comb_worst": rc["worst_day"], "comb_ret_dd": rc["ret_dd"],
         "t61_ret_dd": rb["ret_dd"], "corr_to_t61": float(np.corrcoef(inc[full], d_t61[full])[0, 1]) if inc[full].std() > 0 else 0.0,
         "loss_overlap": float(((inc < 0) & (d_t61 < 0))[full].sum() / max(1, (inc < 0)[full].sum())),
         "tail_overlap_mod_on_t61_worst10pct": float(inc[full & lo].mean()) if (full & lo).any() else 0.0,
         **{f"fold_{k}": v for k, v in folds.items()}, "folds_pos": int(sum(v > 0 for v in folds.values())),
         "remove_top3": float(act.sum() - top[:3].sum()), "remove_top5": float(act.sum() - top[:5].sum()),
         "pre2023": float(inc[full & np.asarray(sess < "2023-01-01")].mean()), "from2023": float(inc[full & np.asarray(sess >= "2023-01-01")].mean()),
         "max_year_share": float(yr.max() / pos_tot) if pos_tot > 0 else 1.0, "active_days": int((inc[full] != 0).sum())}
    o.update(extra)
    chk = {"g_incr_pos": o["incr_avg_day"] > 0 and o["incr_avg_day_2021"] > 0,
           "g_folds": o["folds_pos"] >= 4,
           "g_risk": o["comb_maxdd"] <= 20000 and o["comb_worst"] >= -5000,
           "g_retdd": o["comb_ret_dd"] >= o["t61_ret_dd"],
           "g_corr": o["corr_to_t61"] <= 0.5,
           "g_excess": extra.get("matched_excess_day", 0.0) > 0,
           "g_slip4": extra.get("slip4_incr_avg_day", -1.0) > 0,
           "g_top5": o["remove_top5"] > 0,
           "g_regime": o["pre2023"] > 0 and o["from2023"] > 0 and o["max_year_share"] <= 0.5,
           "g_plateau": bool(extra.get("plateau_pass", False)),
           "g_delay": extra.get("delay1_incr_avg_day", -1.0) > 0,
           "g_caps": extra.get("peak_total_MNQ", 0) <= MNQ_CAP and extra.get("peak_total_MES", 0) <= MES_CAP_TOTAL and extra.get("peak_margin_pct", 0) <= 50}
    o.update(chk); o["PASS"] = bool(all(chk.values()))
    return o


def md(name, title, blocks):
    lines = [f"# {title}", ""]
    for b in blocks:
        lines.append(b.to_markdown(floatfmt=".3f") if isinstance(b, pd.DataFrame) else str(b)); lines.append("")
    open(os.path.join(REP, name), "w").write("\n".join(lines) + "\n")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def jdump(obj, path):
    json.dump(obj, open(path, "w"), indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
