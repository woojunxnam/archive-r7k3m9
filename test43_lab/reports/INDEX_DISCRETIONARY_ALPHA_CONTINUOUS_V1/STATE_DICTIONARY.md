# STATE_DICTIONARY (frozen in PH2 prereg 13ca487)
APPROACH: bars before a support interaction; features disp6, bars_since_high, bear_frac6, consec_bear, range_contract, lower_wick, cpos_chg3.
ATTEMPT: low <= S + 0.25 x ATR5 for a known support S.   FAILURE: close < S.   RECLAIM: first later close > the failed S.
RETEST: later bar with low <= S + 0.25 x ATR5 and close > S.   FIRST RESUMPTION: close > prior bar high.
FIRST RESUMPTION FAILURE: within 3 bars a close < the first-resumption bar's low.   SECOND RESUMPTION: next close > prior bar high.
EXPANSION: close > max high since the failure.   RESISTANCE / TREND LOSS: close < the reclaimed level.
Location types: SUPPORT {PDL, PWL, SW30L, SW60L, R2HL, R4HL, ORL, BRS}; RESISTANCE {PDH, PWH, SW30H, SW60H, R2HH, R4HH, ORH, BSR}; VWAP context only.
