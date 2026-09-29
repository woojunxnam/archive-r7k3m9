# TEST114_AUDIT_CORRECTION_1 — exact-clock GHLZ target (preregistration, alone)

Audit finding (clock semantics, no economics): the canonical 1m grid is END-stamped (j = 0 is the bar ending 09:31; C45.g("16:00") = 389).
TEST114 (ac38e48 / 9ba1ffa) used:
- first-half-hour reference P(10:00) = C[29] (close of the bar ending 10:00) — CORRECT;
- prior close = C[389] of the prior session (close of the bar ending 16:00) — CORRECT;
- r12 reference P(15:30) = C[359] (close of the bar ending 15:30) — CORRECT;
- entry = FP[360] = open of the bar ending 15:31 = the 15:30:00 price — CORRECT (next legal open after the 15:30 decision);
- target exit = FP[J16] with J16 = 389 = OPEN of the bar ending 16:00, i.e. the 15:59 price — WRONG: the academic final-half-hour return ends at
  the 16:00 cash reference close = C[389] (close of the bar ending 16:00).
- The adjacent timing sensitivity (exit 16:15) used FP[J15 = 404] = open of the bar ending 16:15 (16:14 price); corrected to C[404].
Correction (no new hypotheses, windows, thresholds): rerun G1_R1, G2_R1_R12, G1_R1_X1615 and TB_OPEN_CONTROL with target exits C[389] (16:00)
and C[404] (16:15); nulls, CIs, classification and duplication test exactly as in the TEST114 prereg.  The corrected result replaces the old one
(not averaged).  If the G1 sign remains negative -> GHLZ replication CLOSED; if materially changed -> record the corrected result only.
