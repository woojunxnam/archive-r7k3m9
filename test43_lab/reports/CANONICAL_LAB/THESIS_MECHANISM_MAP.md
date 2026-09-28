# Thesis mechanism map — Livermore / Hougaard as economic priors (TEST96+)

Written with the TEST96 preregistration, before any Generation-1 economics. [SOURCE] = trader's stated idea; [MECH] = the market mechanism that
would have to exist for it to pay; [OURS] = our systematic interpretation; [DONE] = already covered by MAIN or already rejected.

## Root theses and the mechanisms behind them

| Root idea | [MECH] why it could pay | Observable state transition | Status in our program |
|---|---|---|---|
| Market proves direction before entry (Livermore pivotal point; Hougaard "buy strength") | informed / trend-following flow arrives in waves; the first wave reveals the imbalance, later waves continue it | balanced -> directional | intraday session-high breakouts: T68 (in MAIN basket), generic momentum atlas [DONE / rejected as beta] |
| Line of least resistance / break from congestion | stops and resting orders cluster above a long congestion; the break forces liquidity-takers | multi-session compression -> break | intraday compression-expansion = T53-M3 [DONE]; **multi-session congestion (G4) new** |
| Natural reaction inside a trend, continuation after reaction | profit-taking in a trend is absorbed by participants who missed the first leg | directional -> reaction -> resumption | TEST95 literal Market Key failed (too slow); **intraday reaction-resumption (G1) and day-2 reaction-resumption (G2) new forms** |
| Old resistance becomes support; acceptance | a level that repels, once crossed and held, re-prices the auction (acceptance) | resistance -> tested -> accepted support | TEST84 profile work (value acceptance) [partly DONE]; **PDH retest acceptance (G3) new** |
| Strong movement follows through; strong -> stronger | momentum acceleration = second wave larger than first (more participants join) | strong -> stronger | single strong bar / impulse families [DONE: momentum atlas rejected]; **second-impulse-stronger (G5) new** |
| Broad participation confirms a move | index-wide buying (futures basket / program flow) vs idiosyncratic sector flow | one index leads -> broad confirmation | **G6 new (needs NQ / YM / RTY data now available)** |
| Sit tight; big trends last longer than expected | trend persistence at multi-day horizons | trend -> trend continues | T53-M2 next-open hold [DONE]; overnight only after intraday value |
| Add only when confirmed; cut losers | positive skew via conditional sizing | winner -> confirmation -> add | TEST94 PRESS1 failed [DONE]; revisit only on a new positive base |
| Calendar / structural flows | month-end / turn-of-month pension and index flows | calendar state | T67 (in MAIN basket) [DONE] -> portability D7 |

## Generation-1 selection logic
Every Gen-1 mechanism is a TRANSITION (not a static "strong market" state, which prior tests reduced to beta), is not a threshold variant of a
MAIN member or a rejected family, and has a family-specific null that isolates the transition from the static state:

| Gen-1 | Transition | Family-specific null (isolates the transition) |
|---|---|---|
| G1 | trend -> reaction -> resumption (intraday) | same trend state, no reaction, first qualifying minute |
| G2 | trend day -> next-day reaction -> resumption | trend-day-only entry (matched A) + momentum-null B |
| G3 | resistance -> retest -> accepted support | plain first PDH break |
| G4 | multi-session congestion -> break | 20-session-high break without congestion |
| G5 | strong -> stronger | first impulse only |
| G6 | one index leads -> broad confirmation | leader break without confirmation; T68 raw |

Instruments: ES->MES, NQ->MNQ, YM->MYM, RTY->M2K.  Primary exit 16:15; 30/60/120m, 16:00 and next-open reported (overnight judged only if the
intraday entry has value).  Next generations will be derived from Gen-1 failure analysis, never by varying Gen-1 thresholds.
