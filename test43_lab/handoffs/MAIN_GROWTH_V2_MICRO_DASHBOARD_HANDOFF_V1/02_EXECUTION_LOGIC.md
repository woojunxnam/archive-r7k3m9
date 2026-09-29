# MAIN_GROWTH_V2 Exact Execution Logic

## 1. MAIN_GROWTH_V1

### 1A. T61-R1C_ATOMIC_CAP6
Canonical authority:
`test43_lab/frozen/t61_r1c/T61_R1C_MANIFEST.json`

핵심:
- C43 1x integer decision을 먼저 만들고 x2.
- C43 dollar governor thresholds도 x2.
- TEST53 = frozen M1/M2/M3/M4, 각 1 MNQ/lot, ensemble cap 2, day governor -$1,000.
- C43 MNQ target 우선.
- `allowed_TEST53 = max(0, 6 - C43_MNQ_target)`.
- TEST53를 allowed capacity로 clamp.
- C43 + TEST53를 하나의 aggregate MNQ target으로 net order.
- broker target/position MNQ <= 6.
- MES target = C43 1x MES integer target x2; historical peak 6 MES.
- overnight holdings 존재. Overnight 중 임의의 신규 진입/add/reduce/stop을 만들지 말고 frozen semantics를 그대로 따른다.

### 1B. FIXED_CLUE_BASKET_V1
Members:
- T66_ML_OPENING = 1 MNQ
- T68_RAW_BREAKS = 1 MNQ
- T67_TOM_INTRADAY = 2 MES
- PG12_ML = 1 MNQ

Capacity:
- T61 has priority.
- T61 + basket MNQ <= 6.
- T61 + basket MES <= 8.
- basket 자체 shared governor 없음.
- canonical reference는 frozen package의 `src/t94b_basket.py`.

## 2. C2_P2_FAILED_FIRST

Signal data universe:
ES / NQ / YM / RTY.

Execution:
ES->MES, NQ->MNQ, YM->MYM, RTY->M2K.
1 micro base unit.

Canonical detector:
`test43_lab/src/t103_pullback.py::detect`.

### Exact P2 structure
5m completed bars 기준:
1. `brk = close > prior-high(12 bars)`.
2. fresh breakout = current brk and previous flattened bar was not brk.
3. session에서 첫 eligible fresh breakout `b0`를 잡는다 (source code bounds 그대로).
4. breakout swing high `SH`를 추적.
5. current high < previous high가 처음 나타나면 pullback starts.
6. context invalidation:
   - low < SH - 1 daily ATR, 또는
   - high > SH (new high로 trend already resumed).
7. first resumption `r1`:
   `close[b] > high[b-1]`.
8. first resumption failure:
   r1 이후 최대 3 bars 안에
   `close[b] < low[r1]`.
9. P2_FAILED_FIRST:
   failure 이후 처음으로 다시
   `close[b] > high[b-1]`.
10. signal on completed bar -> entry at next legal open.
11. frozen exit = 16:15 ET.
12. no stop, no early resistance exit, no overnight.

## 3. FIRST_WINNER_ADD1

Canonical order builder:
`test43_lab/src/da_ph9.py::add_orders`.

For an open C2 base trade:
1. completed 5m checkpoints only.
2. at least 30 minutes of legal holding must remain before 16:15.
3. winner checkpoint if `close[k] > C2 base entry price`.
4. checkpoint is NOT eligible if the same bar is an independent C3/C5/C6/C7/C8 bank event.
5. take the first eligible winner checkpoint.
6. add exactly 1 micro of the same instrument at next legal open.
7. add exits with the parent C2 at 16:15.
8. no ADD2 in MAIN_GROWTH_V2.

Independent-event set used only to exclude the checkpoint:
- C3_P1_H2
- C5_HTF1_30m
- C6_AV_OR30
- C7_L1_SWH60
- C8_CHOCH_15m

Exact event reproduction lives in `rp_bank.py::events`.

## 4. Portfolio priority / caps

Research caps:
- MES 8
- MNQ 6
- MYM 4
- M2K 4

Priority:
1. MAIN_GROWTH_V1
2. C2 base
3. C2 winner ADD1

Within MAIN_GROWTH_V1, T61 priority over clue basket is already frozen.

## 5. Legal timing
- Signal decisions use completed information only.
- Fill is next legal open.
- Preserve END-stamped 1m convention.
- C2 and winner ADD1 flatten at 16:15.
- Do not invent intrabar stop/breakout fills.
