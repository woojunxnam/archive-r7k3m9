# PH10 NOVELTY RESERVE (3 families) — NOVELTY_MEMOs + preregistration (alone)

Opened automatically: PH9 found 0 new portfolio-additive modules (< 2).  Budget: <= 20 deterministic definitions per family, <= 40 ML configs and
<= 2,000 genomes in total (none planned).  Source note: citations below are from the author's existing knowledge of the published literature;
external access was not used to re-verify them in this session, and no trader rule beyond the cited published findings is claimed.
Dedup check against MASTER_DEDUP_MAP / reclamation / this program: none of the three root mechanisms (same-slot intraday periodicity, round-number
price levels, pre-holiday drift) was tested before (TEST67 turn-of-month and TEST69 pre-FOMC are different calendar mechanisms; the level atlas
contains no round-number levels).  One clue-rescue phase max per family.  Common rules: ESP-style magnitude / family nulls, date-clustered CIs,
stitched outer economics for any family passing the exploration gate, stresses, routes.

## NR1 INTRADAY PERIODICITY (Heston, Korajczyk & Sadka 2010, J. Finance: returns in a given half-hour tend to repeat in the same half-hour on prior days)
Mechanism: recurring institutional trading at fixed times.  Slots = 12 half-hours 10:00-16:00 (entry = FP at the slot start, exit = FP at the slot
end, both engine grid).  Signal for slot k on day d: mean slot-k return over the prior L trading days (L = 5, 20) > 0 -> long that slot.
Definitions: NR1_L5, NR1_L20 (2).  Family null: the same slot on all days (unconditional TOD-matched long) in year x vt cells; also slot-by-slot.
Gate as the program.  Cost note: a 30-min hold must beat ~0.011 ATR_d.
## NR2 ROUND-NUMBER CROSSINGS (Osler 2003, J. Finance: stop / take-profit orders cluster at round numbers; trends tend to accelerate after
round numbers are crossed)
Round levels fixed a priori per instrument: MAJOR = multiples of ES 100, NQ 500, YM 1,000, RTY 50; MINOR = ES 25, NQ 100, YM 250, RTY 10.
Event: first 5m close above a round level after a close at / below it (per session, per level class), b <= 67, entry next open.
Definitions: NR2_MAJOR, NR2_MINOR (2) + PSEUDO nulls NR2P_MAJOR / NR2P_MINOR = identical crossings of levels offset by half the spacing
(non-round, same geometry).  Magnitude null (all bars, PH3 definition) for all; primary comparison = round minus pseudo (date-clustered CI).
## NR3 PRE-HOLIDAY DRIFT (Ariel 1990, J. Finance: high returns before exchange holidays)
Pre-holiday session = a trading day whose next trading day is more than one business day later (Mon-Fri calendar gap, weekends excluded),
derived causally from the known exchange calendar (holiday dates are public in advance).  Definition NR3_PREHOLIDAY: long 09:30 open -> 16:15 on
pre-holiday sessions (1 micro per index).  Null: all other sessions, same year x vt cell mean.  Small sample (~9 events / year / index) is stated.
Total reserve definitions: 7 (+ nulls).
