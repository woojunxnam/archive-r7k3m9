# CANONICAL_SOURCE_AUDIT (TEST95+ Track A)

Three layers are kept separate everywhere in the code and reports:
**[SOURCE]** = rule stated in a primary / authoritative source; **[FORMAL]** = our systematic formalization of that rule
(thresholds, bar sizes, clocks are OURS, not the trader's); **[HYP]** = our own new hypothesis.

## Sources consulted
- Jesse Livermore, *How to Trade in Stocks* (1940), full text PDF (buysidedigest.com mirror), chapters "The Pivotal Point",
  "Money in the Hand", "Explanatory Rules" 1-8 (text extracted locally).
- Tom Hougaard: tradertom.com "Breakout Strategy for the DAX and Dow Open"; *Trading Manual* (tradertom.com PDF, 72 pp);
  *Best Loser Wins* (Harriman House, 2022) - publisher description only (book text not accessed).
- Secondary / formalization references (NOT authority): MQL5 article "Jesse Livermore's Pivotal Point System" (author's
  thresholds explicitly the author's), TradingView "School Run" community scripts (third-party interpretations).

## Livermore
| Principle | [SOURCE] (1940) | [FORMAL] (ours) |
|---|---|---|
| Market Key columns | Six columns: Secondary Rally, Natural Rally, Upward Trend, Downward Trend, Natural Reaction, Secondary Reaction (Rules 1-3) | causal state machine, one update per completed bar |
| Swing threshold | a reaction / rally of "approximately six points" (stocks > ~$30; Key Price 12 points) starts a Natural Reaction / Rally (Rules 4, 6) | R = k x ATR_d, k = 2.0 (neighbours 1.5 / 2.5); daily highs feed rising columns, daily lows falling columns |
| Pivotal Points | last Upward/Downward-Trend price becomes a Pivotal Point when a Natural Reaction/Rally begins; extreme of the reaction/rally becomes the next Pivotal Point (Rule 6 note) | stored causally at the bar the column change is recorded |
| Resumption / confirmation | "if the movement is going to be resumed ... it will carry through its previous Pivotal Point - by three points" (Rule 8a); Natural Rally price >= 3 points above black-lined rally pivot -> Upward Trend (Rule 5a) | C = R/2 (the source ratio 3/6) |
| Trend over | "sells three points or more below the last Pivotal Point ... Upward Trend is over" (Rule 8b) | exit when low <= reaction pivot - C, or state -> Downward Trend |
| Primary pivot buy | example: fails to pierce the low Pivotal Point -> "buy as soon as it rallies 3 points from the low"; confirmation later by exceeding the high pivot by 3 points | L2 entries |
| Enter only when proved | "real money ... in commitments ... showing a profit right from the start"; wait until a new high confirms ("makes a new high ... you have been justified") | entry only on pivot break; adds only while in profit |
| Staged accumulation | cotton plan "accumulation of 100,000 bales after the Pivotal Point had been passed"; wheat: bought more "as soon as it pierced the next Pivotal Point" | L5: probe at primary pivot, one add per confirmed continuation pivot |
| No averaging down | "avoid averaging down" (Money in the Hand) | hard constraint |
| Sit tight | "As long as a stock is acting right ... do not be in a hurry to take a profit"; big money in sitting through minor reactions | L4 state-based exit vs fixed holds |
| Line of least resistance / Market Key | concepts of *Reminiscences* / the 1940 book; operationalized in the book only through the six-column rules | = the state machine |

## Hougaard
| Principle | [SOURCE] | [FORMAL] (ours) |
|---|---|---|
| Opening breakout (canonical) | Dow: mark high / low of the 59 pre-market minutes 13:30-14:29 GMT (= 08:30-09:29 ET), buy stop at the high, sell stop at the low, cancel the other when one fills; risk 9 points, target 6 points, "I always go for more" (tradertom.com) | T2: long side only (program is long-only): buy stop at the pre-market high from 09:30; stop 0.06 ATR_d, target 0.04 ATR_d (the 9 / 6 Dow points scaled by a ~150-pt Dow ATR of that era) = T2A; runner version T2B (breakeven after +target, trail, 16:15) |
| Higher timeframe | trade with the long-term trend and fade the short-term counter-trend; a 5-min trend change is not a 60-min trend change; trend change = lower high + lower low + trade below that low (Trading Manual pp. 5-6, 53-54) | T1: HTF = 60-min swing structure permits; LTF = 5-min execution |
| Patterns | engulfing bar setup in trend direction (Manual p. ~30) | P_ENGULF (5m); pullback-resumption (fade the short-term counter move) P_RESUME; breakout of the session high P_BREAK [FORMAL of 'trade with trend'] |
| Trade management | move stop to breakeven when the market runs; trail "progressively in the direction of the trend"; aim for a runner, not a monetary target | stop = pattern-bar low; BE at +1R; trail to the prior completed 5m low; 16:15 flat |
| Add to winners / cut losers | *Best Loser Wins* theme (cut losers fast, press winners) - exact add rules NOT available in the accessed sources | T3 = [HYP]/[FORMAL]: add only while in profit, trend valid, and the stop of all units can be raised to lock existing open risk |
| Trend -> Pattern -> Execution | phrase appears in program brief; the accessed Hougaard texts express it as HTF trend -> candle pattern -> execution/management | ordering enforced: HTF permission is a gate, never a score term |

## Attribution rule
No threshold in our code is attributed to Livermore or Hougaard: 6/3-point ratios, 59-minute window and 9/6-point risk / target
are source facts; every ATR scaling, bar size and clock is our formalization.
