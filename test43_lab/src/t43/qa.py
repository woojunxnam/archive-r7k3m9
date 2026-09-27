"""Phase 1 data QA for canonical 1m futures parquet (no canonical history is altered)."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_qa(path: str, out_prefix: str) -> dict:
    import pyarrow.parquet as pq
    meta = pq.ParquetFile(path)
    raw = pd.read_parquet(path)
    rep: dict = {"file": path, "sha256": sha256(path), "rows": int(len(raw)),
                 "schema": {f.name: str(f.type) for f in meta.schema_arrow},
                 "columns": list(raw.columns)}
    cols = {c.lower(): c for c in raw.columns}
    dtc = cols.get("dt") or cols.get("timestamp") or cols.get("ts")
    dt = pd.to_datetime(raw[dtc])
    rep["dt_tz"] = str(dt.dt.tz)
    rep["first_dt"] = str(dt.min())
    rep["last_dt"] = str(dt.max())
    rep["out_of_order_rows"] = int((dt.diff() < pd.Timedelta(0)).sum())
    rep["duplicate_dt"] = int(dt.duplicated().sum())
    o, h, l, c = (raw[cols[k]].astype(float) for k in ("o", "h", "l", "c"))
    v = raw[cols["v"]].astype(float)
    bad = (h < l) | (o > h) | (o < l) | (c > h) | (c < l)
    rep["bad_ohlc_rows"] = int(bad.sum())
    rep["nonpositive_price_rows"] = int(((o <= 0) | (h <= 0) | (l <= 0) | (c <= 0)).sum())
    rep["nan_price_rows"] = int((o.isna() | h.isna() | l.isna() | c.isna()).sum())
    rep["zero_volume_rows"] = int((v == 0).sum())
    rep["negative_volume_rows"] = int((v < 0).sum())
    rep["nan_volume_rows"] = int(v.isna().sum())
    ticks = ((c / 0.25) - np.round(c / 0.25)).abs()
    rep["off_tick_close_rows"] = int((ticks > 1e-6).sum())
    # minute-of-day histogram (END stamps)
    mod = dt.dt.hour * 60 + dt.dt.minute
    rep["hour17_rows"] = int((dt.dt.hour == 17).sum())
    rep["rows_17_01_to_18_00"] = int(((mod > 17 * 60) & (mod <= 18 * 60)).sum())
    # session date: END stamps after 18:00 belong to next session
    sd = dt.dt.normalize().where(mod <= 18 * 60, dt.dt.normalize() + pd.Timedelta(days=1))
    # END stamp 18:00 exactly belongs to prior window only if maintenance break absent; treat >18:00 as next
    sd = dt.dt.normalize().where(mod <= 17 * 60, dt.dt.normalize() + pd.Timedelta(days=1))
    df = pd.DataFrame({"sd": sd, "mod": mod, "c": c, "v": v})
    rth = (mod > 570) & (mod <= 960)
    df["rth"] = rth
    per = df.groupby("sd").agg(rows=("c", "size"), rth_rows=("rth", "sum"), vol=("v", "sum"))
    per["weekday"] = pd.to_datetime(per.index).weekday
    rep["sessions"] = int(len(per))
    rep["sessions_with_rth"] = int((per["rth_rows"] > 0).sum())
    rep["median_rows_per_session"] = float(per["rows"].median())
    rep["median_rth_rows"] = float(per.loc[per.rth_rows > 0, "rth_rows"].median())
    rep["full_rth_sessions_390"] = int((per["rth_rows"] == 390).sum())
    rep["partial_rth_sessions_lt_380"] = int(((per["rth_rows"] > 0) & (per["rth_rows"] < 380)).sum())
    rep["short_rth_sessions_le_225"] = int(((per["rth_rows"] > 0) & (per["rth_rows"] <= 225)).sum())
    rep["missing_rth_minutes_total"] = int((390 - per.loc[per.rth_rows > 0, "rth_rows"]).clip(lower=0).sum())
    # gaps within RTH
    rdt = dt[rth.values]
    gaps = rdt.diff().dt.total_seconds().div(60)
    same = sd[rth.values].diff().dt.days.eq(0)
    rep["rth_intra_session_gaps_gt1m"] = int(((gaps > 1) & same).sum())
    rep["rth_intra_session_gaps_gt5m"] = int(((gaps > 5) & same).sum())
    # DST sanity: RTH open volume spike should stay at 09:31 END stamp across DST
    first_rth = df[rth].groupby("sd")["mod"].min()
    rep["rth_first_minute_mode"] = int(first_rth.mode().iloc[0]) if len(first_rth) else None
    rep["rth_first_minute_not_0931"] = int((first_rth != 571).sum())
    # volume spike check around 09:30 by month (DST shift would move the spike by 60m)
    vm = df.assign(m=pd.to_datetime(df["sd"]).dt.to_period("M")).groupby(["m", "mod"])["v"].mean().reset_index()
    spike = vm[(vm["mod"] >= 500) & (vm["mod"] <= 640)].loc[lambda x: x.groupby("m")["v"].idxmax()]
    rep["volume_spike_minute_by_month_unique"] = sorted(set(int(x) for x in spike["mod"]))
    # roll behaviour
    if "contract" in cols:
        ctr = raw[cols["contract"]]
        chg = ctr.ne(ctr.shift())
        rep["contracts"] = int(ctr.nunique())
        rep["contract_switches"] = int(chg.sum() - 1)
        sw = pd.DataFrame({"dt": dt[chg.values], "contract": ctr[chg.values]})
        rep["contract_switch_list"] = [f"{a} {b}" for a, b in zip(sw["dt"].astype(str), sw["contract"])]
    if "cum_adjustment" in cols:
        ca = raw[cols["cum_adjustment"]].astype(float)
        rep["cum_adjustment_unique"] = int(ca.nunique())
        rep["cum_adjustment_first_last"] = [float(ca.iloc[0]), float(ca.iloc[-1])]
    if "roll_adjacent" in cols:
        rep["roll_adjacent_rows"] = int(raw[cols["roll_adjacent"]].astype(bool).sum())
        rep["roll_adjacent_sessions"] = int(sd[raw[cols["roll_adjacent"]].astype(bool).values].nunique())
    # big 1m moves (possible anomalies)
    ret = c.diff().abs()
    same_s = sd.diff().dt.days.eq(0)
    big = ret[same_s] > 40
    rep["abs_1m_close_change_gt_40pts"] = int(big.sum())
    rep["abs_1m_close_change_top5"] = [
        (str(dt.iloc[i]), float(ret.iloc[i])) for i in ret[same_s].nlargest(5).index]
    per.to_csv(out_prefix + "_sessions.csv")
    with open(out_prefix + ".json", "w") as f:
        json.dump(rep, f, indent=1, default=str)
    return rep
