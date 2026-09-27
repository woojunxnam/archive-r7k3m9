# P16 Strategy health monitor (production specification)

TEST43-P — MULTI-STRATEGY REGIME ENSEMBLE / PORTFOLIO ALLOCATOR. HOLDOUT_OPENED = NO.


All viable sleeves (including shadows and zero-weight sleeves) keep computing their virtual desired exposure and virtual
ledger in production. States: NORMAL / WATCH / REDUCED / DISABLED. Thresholds are fixed a priori from each sleeve's own DEV
distribution (percentiles), NOT optimised on this backtest.

| input | WATCH | REDUCED (sleeve budget x0.5) | DISABLED (budget 0, still computed) |
|---|---|---|---|
| rolling 3m virtual P&L | < DEV 10th pct of rolling 3m | < DEV 5th pct | < DEV minimum |
| rolling 6m / 12m virtual P&L | < DEV 10th pct | < DEV 5th pct | 12m < DEV minimum |
| rolling 6m matched-beta excess | < 0 | < DEV 5th pct | < DEV minimum for 2 consecutive months |
| current virtual DD | > DEV 75th pct of DD | > DEV 95th pct | > 1.25 x DEV MaxDD |
| fill rate / rejected orders (live vs virtual) | < 98% | < 95% | < 90% |
| friction per day | > 1.5 x DEV | > 2 x DEV | > 3 x DEV |
| average exposure vs virtual | deviation > 10% | > 20% | > 35% |

Transitions: evaluated after each completed session; recovery one state per 20 sessions once all inputs are back inside
the WATCH band. A DISABLED sleeve's budget is NOT redistributed automatically (portfolio simply holds less risk); any
redistribution is a new frozen decision. Every state change is logged with the inputs. This is a monitoring spec only; it
was not applied to the historical results in this report.

