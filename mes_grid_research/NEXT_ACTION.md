# NEXT_ACTION (단 하나)

## CR_002 — R3 Rolling Recycle: 손실실현 교체로 recycle capacity를 현재가 근처에 유지할 수 있는가

### 배경
CR_001에서 R1(profit-only)은 추세 하락 시 recycle lane도 함께 잠겨(lane full 42–69%) capacity 유지 목표를 달성하지 못했다.
손실을 실현하지 않는 recycle 변형(R2 dynamic zone, R4 inventory-aware TP)은 잠긴 slot을 풀 수 없으므로, capacity 유지 가설을 직접 검증하는 유일한 후보는 R3다.

### 가설
recycle lane이 가득 찼고 가격이 최저 recycle 진입가보다 `roll_trigger` 이상 더 내려갔을 때, **가장 높은 원가의 recycle tranche를 market 손절 후 현재가 근처에서 재매수**하면
recycle 거래가 하락장에서도 계속되어 (a) recycle lane full 시간이 줄고 (b) 총 경제적 P&L(realized + unrealized)이 R1보다 나빠지지 않는다.

### 설계 (사전 등록)
- control: CR_001의 `C24_8_tp3.0_core_full`, `C16_16_tp3.0_core_full` (R1)
- 변경: R3 교체 규칙만 추가 (동일 bar에 sell 1 + buy 1, 둘 다 다음 open market; 순 inventory 불변, 교체 1회/bar 이하)
- 파라미터: roll_trigger ∈ {10, 20, 40} pt, 교체 쿨다운 없음(1차), rec_tp 3
- 보고: realized/unrealized/총경제 P&L, 교체 횟수·교체 실현손실 합계, recycle lane full 비율, 최장 32-lock, Max MTM DD, 2025 regression 창, 2022-23 창, 비용
- 주의: 교체는 노출을 줄이지 않음 → MTM DD 개선은 기대하지 않는다. "비용 없는 평단 인하"로 서술 금지.

### 그 다음 후보 (참고, 지금 하지 않음)
- core grid geometry (5pt 고정 grid는 32계약을 ~155pt = 가격의 약 2.6%에 소진 → convex/ATR widening) — lock의 1차 원인 후보.
- freefall governor (신규 add만 pause).
