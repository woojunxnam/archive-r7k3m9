"""RUN-3 W: failed-recycle diagnostics on C32 (FQA_32_16_16)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from run3_lib import FQ
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = load_canonical(); F = compute_features(b, b.v)
e = Engine(b, FactoryStrategy(F, **FQ(16, 16, True)), ExecConfig()).run()
tr = e.trades_df[e.trades_df.lane == "rec"].copy()
op = pd.DataFrame([dict(entry_idx=t.entry_idx, entry_px=t.entry_px, exit_idx=len(b) - 1, net=np.nan) for t in e.lanes["rec"].tranches])
R = pd.concat([tr[["entry_idx", "entry_px", "exit_idx", "net"]], op], ignore_index=True)
hold_days = (b.dt[R.exit_idx.values] - b.dt[R.entry_idx.values]) / np.timedelta64(1, "D")
# MAE during holding (ES proxy)
lows = b.l
mae = np.array([R.entry_px.iloc[k] - lows[R.entry_idx.iloc[k]:R.exit_idx.iloc[k] + 1].min() for k in range(len(R))])
R["hold_days"] = hold_days; R["mae"] = mae
R["failed"] = (R.hold_days > 1) | R.net.isna()
X = pd.read_parquet(os.path.join(ROOT, "data", "cache", "event_features.parquet")).set_index("idx")
dec = R.entry_idx.values - 1
feat = X.reindex(dec)
cols = ["vwap_dev_atr", "rpos60", "rpos1d", "rpos5d", "sess_dd_atr", "consec_down", "dist_ema20_atr", "slope30_atr", "slope60_atr",
        "eff_ratio30", "datr_pct", "gap_atr", "wick_body_ratio", "close_upper25", "newlow_weak_close", "down_trend_persist", "below_pdl"]
feat = feat[cols].astype(float)
feat["failed"] = R.failed.values
feat["tod"] = X.reindex(dec).tod.values
feat["volreg"] = X.reindex(dec).volreg.values
out = feat.groupby("failed")[cols].median().T
out.columns = ["ok_median", "failed_median"]
out["ok_mean"] = feat[~feat.failed][cols].mean(); out["failed_mean"] = feat[feat.failed][cols].mean()
tod = feat.groupby("tod").failed.mean(); vol = feat.groupby("volreg").failed.mean()
os.makedirs(os.path.join(ROOT, "results", "RUN3_BOTTOM"), exist_ok=True)
out.to_csv(os.path.join(ROOT, "results", "RUN3_BOTTOM", "failed_recycle_features.csv"))
R.to_csv(os.path.join(ROOT, "results", "RUN3_BOTTOM", "recycle_entries_mae_mfe.csv.gz"), index=False)
print("rec entries", len(R), "failed", int(R.failed.sum()), f"({R.failed.mean():.2%})", "mean MAE ok/failed",
      R[~R.failed].mae.mean().round(2), R[R.failed].mae.mean().round(2))
print("MAE quantiles (ok):", R[~R.failed].mae.quantile([.5, .9, .99]).round(2).to_dict())
print(out.round(3).to_string()); print("fail rate by TOD", tod.round(3).to_dict()); print("fail rate by vol", vol.round(3).to_dict())
print("fail rate by year", R.groupby(pd.DatetimeIndex(b.dt[R.entry_idx.values]).year).failed.mean().round(3).to_dict())
