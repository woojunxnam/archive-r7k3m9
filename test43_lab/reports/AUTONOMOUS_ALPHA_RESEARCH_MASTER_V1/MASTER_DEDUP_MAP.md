# MASTER_DEDUP_MAP (AUTONOMOUS_ALPHA_RESEARCH_MASTER_PROGRAM_V1)

Sources read: reports/AUTONOMOUS_PROGRAM (TEST45-54), HIGH_EXPOSURE_PROGRAM (TEST55-61, T61-R1C), TEST65_PLUS (TEST65-69),
ADAPTIVE_BOX_LAB (TEST70-78+), AUCTION_PROFILE_LAB (TEST84-94), TEST49_CONTINUATION, TEST96_PLUS (incl. TEST95 literals / Track A-D),
TEST97_PLUS (+ AUDIT_CORRECTION_1), TEST98_PLUS (+ AUDIT_CORRECTION_1), MAIN authorities (T61-R1C manifest, FIXED_CLUE_BASKET_V1).
Rule: a closed family may NOT be reopened by renaming thresholds / windows.  Any new family overlapping a closed one must state a
NOVELTY_DELTA (what information / state / mechanism is new) in its preregistration; otherwise it is NOT_RUN_BY_DUPLICATION.

## A. Closed families (status at program start)
| family | source tests | status | nearest new-program families | required NOVELTY_DELTA |
|---|---|---|---|---|
| gap-down / opening-flush rebound | TEST45, TEST46 B1-B6 | CLOSED, no survivor | none (long-weakness) | n/a - not reopened |
| overnight carry (generic) | TEST45, TEST49, TEST59 | CLOSED (beta) | TEST111 survivor-only overnight | only as extension of a validated intraday survivor |
| PDL / 5-day-low / OR-low rebound | TEST46 B, TEST47 | CLOSED | TEST104 L3 SFP on NEW level types | level types not previously tested (PWL, causal 60m swing low, 2h extreme); failure-reclaim state not generic touch |
| VWAP lower-band / reclaim; HTF-bull + VWAP pullback | TEST46, TEST48, TEST97 W3_V3 | CLOSED | TEST100 V1-V3 | trend-side ACCEPTANCE state (time/share above VWAP, walk) not reclaim-from-below or band touch |
| range-exhaustion reversal | TEST46/47 | CLOSED | TEST108 (as VETO only), TEST116 | used only as a continuation veto; TEST116 needs NOVELTY_DELTA_VS_TEST46_47 |
| NASSI serial-leg exhaustion | TEST47 | CLOSED | none | n/a |
| blind DCA | TEST47, TEST97 H | CLOSED (control only) | TEST110 BLIND_DCA control | control arm only; never a candidate |
| ARM -> CONFIRM delayed entry | TEST48 | CLOSED | TEST103 P2 | second-resumption after a FAILED first attempt (a structural failure state), not generic delay |
| TEST49 continuation rules (opening drive, trend day, late strength, close-strength carry, ORB retention) | TEST49 | CLOSED | TEST114 academic close momentum, TEST106 ACD | TEST114 must be compared with TEST49 late-strength / opening-drive-to-close; if equivalent -> RESEARCH_DUPLICATE |
| generic compression -> expansion | TEST50 | CLOSED | TEST108 range budget | range budget as consumption of expected daily range, not compression state |
| C43 sizing meta; TEST52-54 ensembles | TEST51-54 | CLOSED | none | n/a |
| direct C43 / TEST53 portability | TEST96 D | CLOSED | none | n/a |
| boxes / Darvas / box migration / trend ladder / nested boxes / upper-state | TEST70-78 | CLOSED | TEST104 L1 (break-retest-hold) | L1 on external reference levels (PDH, PWH, ORH, 60m swing) with retest-hold state; boxes built from own range excluded |
| volume / auction profile (POC, VAH, HVN/LVN, PG12) | TEST84-94 | CLOSED (PG12 is basket member) | none; no profile levels anywhere | n/a |
| generic 5/15/60 alignment | TEST74, TEST95 | CLOSED | TEST99 HTF events | HTF bar-STRUCTURE events (strong bar, 2h breakout, two-bar) vs magnitude-matched null, not direction alignment |
| press ladders / press-winner | PRESS_BASKET_LAB, TEST94 | CLOSED | TEST110 WINNER_PYRAMID | only on a validated positive base, max 2 units |
| TEST95 Tom/Livermore literals; TEST96 A2 generations | TEST95/96 | CLOSED/SATURATED | TEST115 | ADX/DMI/stage STRENGTH beyond direction, null matched on simple HTF direction |
| Q2 breadth expansion; Q4 neighbours | TEST96 | STRONG FORWARD CLUE ONLY / closed | TEST113 | mechanism-specific synchrony only, conditional on a clue |
| TEST97 strong-bar / FT2 / first-pullback / recovery; W3_V1 vol breakout; Crabel NR x ORB | TEST97 (+CORR1) | CLOSED; W3_V1 k=.2/.3 16:15 = CORRECTED_HISTORICAL_CLUE | TEST99 HTF1 (strong bar on HTF), TEST103, TEST106 | TEST99 HTF1 on 15/30/60m with 5m-aggregation parity; TEST103 = two-leg/second-entry STRUCTURE after a failed first attempt, not first pullback |
| TEST98 path quality / open acceptance | TEST98 (+CORR1) | CLOSED/SATURATED; open acceptance WEAK_RESEARCH_CLUE_ONLY | TEST100 V1 | VWAP acceptance as a STATE (entry at state onset), not a pre-breakout path feature of the N=12 breakout |

## B. New-program family novelty statements (preregistered)
- TEST99 HTF momentum: new = 15/30/60m bar structure; null matched on cumulative displacement / range / TOD at the same TF.
- TEST100 VWAP trend-side: acceptance/walk/first-hold as state onsets; overlaps TEST98 PQ5 (feature) and TEST46/48 (reclaim) -> delta: onset event, trend side only.
- TEST101 event-anchored VWAP: anchor = causal event; delta vs TEST100: anchored vs session VWAP comparison.
- TEST102 Saty ATR phase / ribbon: continuous phase state; delta vs TEST49 trend-day: EMA/ATR-normalised phase, no daily-direction rule.
- TEST103 complex pullback: two-leg / failed-first structure; delta vs TEST48/TEST97 W3_V3 as in A.
- TEST104 level factory: external reference levels (no profile); delta vs boxes/PDL rebound as in A.
- TEST106 ACD: A/C levels from OR +/- fraction of recent daily range with time acceptance; must be compared with plain ORB (TEST49 ORB retention); equivalent -> RESEARCH_DUPLICATE.
- TEST108 range budget: consumption ratio veto on continuation clues only.
- TEST109 ICT: FVG vs matched no-FVG displacement (<= 12 definitions).
- TEST114: Gao-Han-Li-Zhou first-30m -> last-30m; compared with TEST49.
- TEST115: trend strength / stage beyond direction.
- TEST116: DeMark-style temporal count; NOT_RUN_BY_DUPLICATION unless NOVELTY_DELTA_VS_TEST46_47 holds (count of consecutive closes vs close[t-4] is time-based, not magnitude-based exhaustion).
