"""Full data audit of canonical ES 1m parquet. Read-only. Writes results/data_audit.json."""
import hashlib, json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "canonical", "canonical_1m_ES.parquet")
EXPECT = dict(bytes=38881868, sha256="2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116",
              rows=2486058, first="2019-05-05 18:01:00", last="2026-05-27 17:00:00")

def main():
    out = {}
    b = open(PATH, "rb").read()
    out["bytes"] = len(b); out["sha256"] = hashlib.sha256(b).hexdigest()
    df = pd.read_parquet(PATH)
    out["rows"] = len(df); out["columns"] = {c: str(t) for c, t in df.dtypes.items()}
    out["first"] = str(df.dt.iloc[0]); out["last"] = str(df.dt.iloc[-1])
    out["checks"] = {k: out[k] == v for k, v in EXPECT.items()}
    out["n_duplicate_dt"] = int(df.dt.duplicated().sum())
    out["monotonic_increasing"] = bool(df.dt.is_monotonic_increasing)
    out["nulls"] = {c: int(v) for c, v in df.isna().sum().items()}
    # OHLC sanity
    bad_h = (df.h < df[["o", "c"]].max(axis=1)).sum(); bad_l = (df.l > df[["o", "c"]].min(axis=1)).sum()
    out["ohlc_violations"] = {"high_below_oc": int(bad_h), "low_above_oc": int(bad_l),
                              "high_below_low": int((df.h < df.l).sum())}
    out["off_tick_grid"] = {c: int((np.abs((df[c] * 4) - np.round(df[c] * 4)) > 1e-9).sum()) for c in "ohlc"}
    out["volume"] = {"zero": int((df.v == 0).sum()), "negative": int((df.v < 0).sum())}
    out["seconds_nonzero"] = int((df.dt.dt.second != 0).sum())
    # sessions: 18:00 prev day -> 17:00; session_date column
    t = df.dt.dt.hour * 60 + df.dt.dt.minute
    out["bars_in_17_to_18_break"] = int(((t > 17 * 60) & (t <= 18 * 60)).sum())
    first_bar = df.groupby("session_date").dt.first().dt.strftime("%H:%M").value_counts().head(10).to_dict()
    last_bar = df.groupby("session_date").dt.last().dt.strftime("%H:%M").value_counts().head(10).to_dict()
    out["session_first_bar_time_counts"] = first_bar; out["session_last_bar_time_counts"] = last_bar
    out["n_sessions"] = int(df.session_date.nunique())
    # gaps inside sessions
    d = df.dt.diff().dt.total_seconds().div(60)
    same = df.session_date.eq(df.session_date.shift())
    gaps = d[same & (d > 1)]
    out["intra_session_gaps"] = {"count": int(len(gaps)), "missing_minutes": int((gaps - 1).sum()),
                                 "max_gap_min": float(gaps.max()) if len(gaps) else 0,
                                 "gap_len_counts": {str(k): int(v) for k, v in gaps.value_counts().head(10).items()}}
    # RTH coverage (bar END 09:31..16:15 = 405 bars) per session on weekdays
    rth = (t >= 9 * 60 + 31) & (t <= 16 * 60 + 15) & (df.dt.dt.normalize() == df.session_date)
    rc = df[rth].groupby("session_date").size()
    out["rth_bars_per_session"] = {"sessions_with_rth": int(len(rc)), "full_405": int((rc == 405).sum()),
                                   "lt_405": int((rc < 405).sum()), "min": int(rc.min()),
                                   "short_sessions_examples": {str(k.date()): int(v) for k, v in rc[rc < 405].sort_values().head(40).items()}}
    # 09:31 bar volume vs 09:30 bar volume — DST alignment check: RTH open volume spike must be at 09:31 bar end all year
    df["_t"] = t
    m = df[df._t.isin([9 * 60 + 30, 9 * 60 + 31, 9 * 60 + 32, 8 * 60 + 31, 10 * 60 + 31])]
    piv = m.pivot_table(index="session_date", columns="_t", values="v")
    piv["is_dst"] = pd.DatetimeIndex(piv.index).tz_localize("America/New_York").map(lambda x: bool(x.dst()))
    ratio = (piv[9 * 60 + 31] / piv[9 * 60 + 30])
    out["dst_open_spike_check"] = {"median_v0931_over_v0930_DST": float(ratio[piv.is_dst].median()),
                                   "median_v0931_over_v0930_STD": float(ratio[~piv.is_dst].median()),
                                   "share_sessions_spike_gt3x": float((ratio > 3).mean())}
    # DST transition days
    trans = []
    for y in range(2019, 2027):
        for dd in pd.date_range(f"{y}-03-01", f"{y}-11-30"):
            a = pd.Timestamp(dd).tz_localize("America/New_York").dst(); bb = (pd.Timestamp(dd) + pd.Timedelta(days=1)).tz_localize("America/New_York").dst()
            if a != bb: trans.append(str((dd + pd.Timedelta(days=1)).date()))
    out["dst_transition_dates"] = trans
    # 2am local on transition Sundays: check no duplicate/hole issues in naive ET (market closed Sunday before 18:00 anyway)
    # rolls
    roll_idx = np.where(df.contract.values[1:] != df.contract.values[:-1])[0] + 1
    rolls = []
    for i in roll_idx:
        prev, cur = df.iloc[i - 1], df.iloc[i]
        rolls.append({"from": prev.contract, "to": cur.contract, "last_dt_old": str(prev["dt"]), "first_dt_new": str(cur["dt"]),
                      "adj_step": float(cur.cum_adjustment - prev.cum_adjustment),
                      "adj_close_to_open_jump": float(cur.o - prev.c),
                      "raw_close_to_open_jump": float((cur.o - cur.cum_adjustment) - (prev.c - prev.cum_adjustment))})
    out["rolls"] = rolls
    out["cum_adjustment_constant_within_contract"] = bool((df.groupby("contract").cum_adjustment.nunique() == 1).all())
    # suspicious jumps (adjusted)
    same_sess = same
    j = (df.o - df.c.shift())[same_sess].abs()
    rng = (df.h - df.l)
    out["jumps"] = {"open_vs_prev_close_gt10pt_intrasession": int((j > 10).sum()),
                    "top_open_gaps": {str(df.dt[k]): float(v) for k, v in j.nlargest(10).items()},
                    "bar_range_gt30pt": int((rng > 30).sum()),
                    "top_bar_ranges": {str(df.dt[k]): float(v) for k, v in rng.nlargest(10).items()}}
    # raw price reconstruction
    raw_c = df.c - df.cum_adjustment
    out["raw_price_range"] = {"min": float(raw_c.min()), "max": float(raw_c.max()),
                              "first": float(raw_c.iloc[0]), "last": float(raw_c.iloc[-1])}
    out["adj_price_range"] = {"min": float(df.c.min()), "max": float(df.c.max())}
    out["roll_adjacent_rows"] = int(df.roll_adjacent.sum())
    out["session_date_vs_plus6h_mismatch"] = int((df.session_date != df.session_date_plus6h).sum())
    # weekend / holiday: sessions per year
    out["sessions_per_year"] = {str(k): int(v) for k, v in pd.Series(df.session_date.unique()).dt.year.value_counts().sort_index().items()}
    json.dump(out, open(os.path.join(ROOT, "results", "data_audit.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str)[:12000])

if __name__ == "__main__":
    main()
