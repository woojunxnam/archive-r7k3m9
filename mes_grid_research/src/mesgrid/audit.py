"""End-of-run economic reconciliation (Phase-0 FQ audit). Returns a dict of identities and their errors."""
import numpy as np


def reconcile(e) -> dict:
    pv = e.cfg.point_value
    tr = e.trades_df
    b = e.bars
    last = len(b) - 1
    open_tr = [t for ln in e.lanes.values() for t in ln.tranches]
    closed_px_pnl = float(((tr.exit_px - tr.entry_px) * tr.qty).sum() * pv) if len(tr) else 0.0
    closed_gross = float(tr.gross.sum()) if len(tr) else 0.0
    slip_open = sum((t.entry_px - t.entry_ideal) * t.qty for t in open_tr) * pv
    unreal_open = sum((b.c[last] - t.entry_px) * t.qty for t in open_tr) * pv
    fl = e.fills_df
    n_buy = int((fl.side == "BUY").sum()) if len(fl) else 0
    n_sell = int((fl.side == "SELL").sum()) if len(fl) else 0
    out = dict(
        opened=len(e._opened_ids), closed=len(e._closed_ids), open_now=len(open_tr),
        conservation_ok=(e._opened_ids == e._closed_ids | {t.id for t in open_tr}) and not (e._closed_ids & {t.id for t in open_tr}),
        fills_buy=n_buy, fills_sell=n_sell,
        fills_match=(n_buy == len(e._opened_ids) and n_sell == len(e._closed_ids) == len(tr)),
        # realized = explicit closes at fill prices - all commissions - roll costs
        err_realized_vs_ledger=float(e.realized_net - (closed_px_pnl - e.commission - e.roll_cost)),
        # gross(ideal) - slippage(closed) - commission - roll = realized
        err_realized_vs_gross=float(e.realized_net - (closed_gross - (e.slippage - slip_open) - e.commission - e.roll_cost)),
        err_unrealized_end=float(e.state.unrealized.iloc[-1] - unreal_open),
        err_equity_end=float(e.state.equity.iloc[-1] - (e.cfg.initial_capital + e.realized_net + unreal_open)),
        err_trade_net_sum=float(tr.net.sum() - (closed_px_pnl - 2 * e.cfg.commission_per_side * tr.qty.sum())) if len(tr) else 0.0,
        open_qty_end=int(sum(t.qty for t in open_tr)), state_qty_end=int(e.state.qty.iloc[-1]),
        realized_net=float(e.realized_net), closed_px_pnl=closed_px_pnl, closed_gross=closed_gross,
        commission=float(e.commission), slippage=float(e.slippage), slippage_open=float(slip_open),
        roll_cost=float(e.roll_cost), unrealized_end=float(unreal_open), audit_bar_checks=e.audit_checks,
        max_roll_ledger_error=float(e.max_ledger_error),
    )
    out["all_ok"] = bool(out["conservation_ok"] and out["fills_match"] and out["open_qty_end"] == out["state_qty_end"]
                         and all(abs(out[k]) < 1e-4 for k in out if k.startswith("err_")) and out["max_roll_ledger_error"] < 1e-6)
    return out
