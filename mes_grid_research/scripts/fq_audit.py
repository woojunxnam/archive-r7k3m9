"""RUN-3 Phase 0: full-data FQ audit (per-bar invariants + reconciliation + forensic ledgers)."""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from mesgrid.data import load_canonical
from mesgrid.features import compute_features
from mesgrid.engine import Engine, ExecConfig
from mesgrid.factory import FactoryStrategy
from mesgrid.audit import reconcile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "RUN3_P0_AUDIT")
FIN = json.load(open(os.path.join(ROOT, "results", "FINALISTS.json")))
WINDOWS = {"w2022_worst": ("2022-08-15", "2022-10-31"), "w2025": ("2025-02-01", "2025-06-30")}


def job(name):
    b = load_canonical(); F = compute_features(b, b.v)
    e = Engine(b, FactoryStrategy(F, **FIN[name]), ExecConfig(), audit=True).run()
    r = reconcile(e)
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    tr, fl, st = e.trades_df, e.fills_df, e.state
    fl["month"] = pd.DatetimeIndex(fl.dt).to_period("M").astype(str)
    hf = fl.groupby("month").size().idxmax()
    wins = dict(WINDOWS, w_highfreq=(hf + "-01", str((pd.Period(hf) + 1).start_time.date())))
    for k, (s, t) in wins.items():
        m = (pd.DatetimeIndex(fl.dt) >= s) & (pd.DatetimeIndex(fl.dt) < t)
        fl[m].to_csv(os.path.join(d, f"fills_{k}.csv"), index=False)
        mt = (pd.DatetimeIndex(tr.exit_dt) >= s) & (pd.DatetimeIndex(tr.exit_dt) < t)
        tr[mt].to_csv(os.path.join(d, f"closed_trades_{k}.csv"), index=False)
        ms = (pd.DatetimeIndex(st.dt) >= s) & (pd.DatetimeIndex(st.dt) < t) & st.tradeable.values
        cols = ["dt", "qty"] + [c for c in st.columns if c.startswith("qty_")] + ["realized_net", "unrealized", "equity", "c"]
        st.loc[ms, cols].iloc[::15].to_csv(os.path.join(d, f"inventory_15m_{k}.csv"), index=False)
    # recycle lane occupancy forensics
    q = st.qty_rec.values[b.tradeable]
    rt = tr[tr.lane == "rec"]
    hold = (pd.to_datetime(rt.exit_dt) - pd.to_datetime(rt.entry_dt)).dt.total_seconds() / 60
    rbuy = fl[(fl.lane == "rec") & (fl.side == "BUY")]
    # recycle entries per recovery/normal regime and the distribution of open recycle count
    occ = pd.Series(q).value_counts().sort_index()
    open_rec_end = [dict(id=t.id, entry=t.entry_px, dt=str(t.entry_dt)) for t in e.lanes["rec"].tranches]
    rec_stats = dict(cap=e.lanes["rec"].spec.capacity, max_open=int(q.max()), mean_open=float(q.mean()),
                     p99_open=float(np.percentile(q, 99)), share_full=float((q >= e.lanes["rec"].spec.capacity).mean()),
                     occupancy_dist={int(k): float(v / len(q)) for k, v in occ.items()},
                     rec_trades=int(len(rt)), rec_win_rate=float((rt.net > 0).mean()), rec_losses=int((rt.net < 0).sum()),
                     hold_min_median=float(hold.median()), hold_min_p90=float(hold.quantile(.9)), hold_days_max=float(hold.max() / 1440),
                     rec_exit_reasons=rt.reason.value_counts().to_dict(), rec_buys=int(len(rbuy)),
                     open_rec_at_end=open_rec_end,
                     longest_rec_trade=rt.assign(h=hold).nlargest(5, "h")[["entry_dt", "exit_dt", "entry_px", "exit_px", "net"]].astype(str).to_dict("records"))
    out = dict(name=name, reconcile=r, rec_stats=rec_stats, high_freq_month=hf)
    json.dump(out, open(os.path.join(d, "audit.json"), "w"), indent=1, default=str)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    with Pool(3) as p:
        res = p.map(job, ["FQ_12_20", "FQ_16_16", "FQ_16_16_add"])
    for r in res:
        print(r["name"], "ALL_OK=", r["reconcile"]["all_ok"], {k: v for k, v in r["reconcile"].items() if k.startswith("err_") or k in ("opened", "closed", "open_now", "audit_bar_checks")})
        s = r["rec_stats"]; print("   rec:", {k: s[k] for k in ("cap", "max_open", "mean_open", "p99_open", "share_full", "rec_trades", "rec_win_rate", "rec_losses", "hold_min_median", "hold_min_p90", "hold_days_max", "rec_exit_reasons")}, "hf month", r["high_freq_month"])
