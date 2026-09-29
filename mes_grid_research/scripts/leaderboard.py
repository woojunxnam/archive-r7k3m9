"""Build MODULE_LEADERBOARD.csv from factory summaries: every config vs its own control and vs BASE.
Verdicts are mechanism labels (no composite score)."""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(exps):
    dfs = []
    for e in exps:
        p = os.path.join(ROOT, "results", e, "summary.csv")
        if os.path.exists(p):
            dfs.append(pd.read_csv(p))
    return pd.concat(dfs, ignore_index=True)


def verdict(r):
    rg, lg, sg = r.dd_gain_vs_base, r.lock_gain_vs_base, r.share32_gain_vs_base
    eff = r.ret_over_dd / r.base_ret_over_dd if r.base_ret_over_dd else np.nan
    risk = rg >= 0.15 or lg >= 0.25
    if rg <= -0.05 and lg <= 0.05:
        return "HARMFUL_RISK"
    if risk and eff >= 1.0 and r.total_mtm > 0:
        return "STRONG_RISK+EFF"
    if risk and r.total_mtm > 0:
        return "RISK_IMPROVES_LOWER_EFF"
    if r.total_mtm > r.base_total * 1.05 and rg < 0.05:
        return "PROFIT_VIA_EXPOSURE"
    if abs(rg) < 0.05 and abs(lg) < 0.1:
        return "NEUTRAL"
    return "MIXED"


def build(df):
    base = df[df.name == "BASE"].iloc[0]
    by = df.set_index("name")
    rows = []
    for _, r in df.iterrows():
        c = by.loc[r.control] if r.control in by.index else base
        lock = r.sat_days if r.family == "N" else r.lock32_days
        d = dict(module=r.module, family=r.family, name=r.name, control=r.control,
                 total_mtm=r.total_mtm, realized=r.realized, unreal_end=r.unreal_end, open_qty_end=r.open_qty_end,
                 max_mtm_dd=r.max_mtm_dd, lock_days=lock, lock32_days=r.lock32_days, share32=r.share32,
                 share_gt24=r.share_gt24, trades_day=r.trades_day, underwater_days=r.underwater_days, cost=r.cost,
                 ret_over_dd=r.ret_over_dd, min_equity=r.min_equity,
                 d_pnl_vs_ctrl=r.total_mtm - c.total_mtm, d_dd_vs_ctrl=r.max_mtm_dd - c.max_mtm_dd,
                 d_lock_vs_ctrl=lock - c.lock32_days, d_share32_vs_ctrl=r.share32 - c.share32,
                 d_trades_day_vs_ctrl=r.trades_day - c.trades_day, d_underwater_vs_ctrl=r.underwater_days - c.underwater_days,
                 d_cost_vs_ctrl=r.cost - c.cost,
                 dd_gain_vs_base=(r.max_mtm_dd - base.max_mtm_dd) / abs(base.max_mtm_dd),
                 lock_gain_vs_base=(base.lock32_days - lock) / base.lock32_days,
                 share32_gain_vs_base=base.share32 - r.share32,
                 base_ret_over_dd=base.ret_over_dd, base_total=base.total_mtm,
                 periods_pos=int(sum(r.get(k, 0) > 0 for k in ("p1921_mtm", "p22_mtm", "p23p_mtm"))),
                 p22_mtm=r.get("p22_mtm"), worst_year=r.get("worst_year_mtm"),
                 w2223_dd=r.get("w2223_dd"), w2223_lock=r.get("w2223_lock"), w25_dd=r.get("w25_dd"), w25_lock=r.get("w25_lock"),
                 w20_dd=r.get("w20_dd"))
        rows.append(d)
    lb = pd.DataFrame(rows)
    lb["verdict"] = lb.apply(verdict, axis=1)
    return lb


if __name__ == "__main__":
    exps = sys.argv[1:] or ["FACTORY_S1"]
    df = load(exps)
    lb = build(df)
    lb.to_csv(os.path.join(ROOT, "MODULE_LEADERBOARD.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    cols = ["name", "total_mtm", "max_mtm_dd", "lock_days", "share32", "trades_day", "underwater_days", "ret_over_dd", "min_equity", "verdict"]
    print(lb.sort_values("max_mtm_dd", ascending=False)[cols].round(2).to_string())
