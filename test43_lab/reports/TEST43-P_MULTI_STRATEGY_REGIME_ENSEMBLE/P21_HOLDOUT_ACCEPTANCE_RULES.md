# P21 Holdout acceptance rules (frozen, not applied)

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.

SHA256 `62e5faf2e59702158470b8cf45a1f65ce4d1425229e0317bbd7e634e92e124d0`

```json
{
 "program": "TEST43-P",
 "written_before_holdout": true,
 "holdout_opened": false,
 "holdout_window": [
  "2025-10-01",
  "2026-05-27"
 ],
 "evaluated_portfolios": {
  "PRIMARY": "P2B_STATIC_4SLEEVE|MODERATE",
  "SECONDARY_1": "P2_STATIC_DIVERSIFIED|MODERATE",
  "SECONDARY_2": "P1_CLUSTER_EQUAL_RISK|CONSERVATIVE"
 },
 "data_and_implementation_QA (all required before reading results)": [
  "canonical ES and MNQ 1m files pass exact SHA256 validation BEFORE parsing (ES 2b4f41b1..., MNQ 66204b12...)",
  "rebuilt DEV+VAL outputs from the full file reproduce the frozen DEV/VAL portfolio daily P&L exactly (prefix invariance)",
  "code SHA256 equal to TEST43P_FINAL_PORTFOLIOS.json 'code' section",
  "no missing RTH sessions beyond the exchange calendar; roll dates as in canonical roll map"
 ],
 "per_portfolio_acceptance (each evaluated at its frozen envelope; ALL must hold)": {
  "net_pnl": "HOLDOUT total net P&L > 0 after commission, 1-tick slippage and roll cost",
  "margin": "no intraday or overnight margin breach (IBKR fractions frozen); peak margin utilisation <= 0.5 of equity",
  "max_drawdown": "HOLDOUT MaxDD <= envelope DD (CONSERVATIVE $10k, MODERATE $15k, AGGRESSIVE $20k)",
  "worst_day": "HOLDOUT worst day >= envelope floor (CONSERVATIVE -$2k, MODERATE -$3k, AGGRESSIVE -$5k)",
  "remove_top3": "HOLDOUT average daily P&L after removing the 3 best days > 0",
  "single_day_concentration": "best single day <= 35% of HOLDOUT total net P&L",
  "matched_beta": "matched-beta excess (same average MES/MNQ exposure, constant long) is REPORTED; not a pass condition",
  "stress_report": "SLIP4 and TIMING_BRITTLENESS_STRESS reported; not pass conditions"
 },
 "decision": {
  "PRIMARY passes": "candidate for paper/live readiness review (still LIVE_AUTHORIZATION = NO)",
  "PRIMARY fails, a SECONDARY passes": "report; no automatic promotion of the secondary without a new review",
  "all fail": "TEST43-P portfolios rejected; no rescue"
 },
 "prohibited_after_holdout": [
  "parameter changes",
  "portfolio membership rescue",
  "weight / risk-budget rescue",
  "regime-rule rescue",
  "envelope or L re-calibration",
  "cost/margin assumption changes",
  "re-running the holdout with modified code"
 ],
 "one_shot": "the holdout is opened once; results are final"
}
```
