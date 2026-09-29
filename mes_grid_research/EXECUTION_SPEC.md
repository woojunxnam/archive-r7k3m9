# EXECUTION_SPEC — version `EXEC-1.0` (conservative)

엔진: `src/mesgrid/engine.py` (`ENGINE_VERSION` 참조). 모든 결과 파일에 이 spec 버전을 기록한다.
spec을 바꾸면 버전을 올리고 이 문서에 변경 이력을 남긴다. 결과가 좋아지는 방향으로 가정을 고르지 않는다.

## 1. 상품·단위
- 가격 데이터: ES 1m (adjusted, DATA_AUDIT §4). P&L: **MES $5/pt/contract**.
- tick = 0.25pt = $1.25.
- 최대 보유: 32 contracts (lane별 capacity 합 ≤ 32).
- Long only. hard SL 없음 (baseline). overnight 보유 허용.

## 2. 시간 규약
- `dt` = bar END (naive America/New_York). bar `dt=T`는 [T−1m, T) 구간.
- bar open 시각 = T−1m.
- **거래창**: open 시각이 09:30 ≤ t < 16:15 인 bar → bar-end 09:31 … 16:15 (정상일 405 bar).
- 거래창 밖 bar: 주문 없음, 체결 없음. 포지션은 유지되고 MTM만 갱신.
- 16:15 bar 종료 시 모든 대기주문(market/limit) 취소. 다음 거래일 09:31 bar(=09:30 open)부터 재개.
- 거래소 휴일(Globex 13:00 조기종료, NYSE 휴장, 거래창 bar ≤210 & 마지막 bar ≤13:00): **신규 주문 금지**. (설정 `trade_exchange_holidays=False`)
- 조기폐장일(13:15 종료)은 정상 거래일로 취급. 마지막 거래창 bar에서 주문 취소.

## 3. 신호 인과성 (no look-ahead)
- 전략은 bar t가 **완료된 후** t까지의 정보만으로 판단한다 (`on_bar_close(t)`).
- 결과 주문은 **다음 bar t+1에만** 유효. t+1이 같은 거래일의 거래창 bar가 아니면 주문은 폐기(다음날로 이월 없음).
- baseline feature(VWAP/ATR/range 등)는 거래창(RTH) bar만 사용. ETH 정보는 별도 라벨된 실험에서만.
- 거래창 직전 ETH bar(09:30 bar-end)로 신호를 만들지 않는다 → 당일 첫 market 주문 체결은 09:32 bar(09:31 open). 단, "flat이면 즉시 진입" 같은 가격 무관 신호도 동일 규칙을 따른다(첫 거래창 bar 종료 후 판단).

## 4. 주문 유형과 체결 규칙

기호: O,H,L = 체결 bar의 open/high/low, tick = 0.25.

### 4.1 Market BUY (신호 t → t+1 open)
- 체결가 = O + slippage_ticks × tick (기본 1 tick 불리).
- `filled_at_open = True`.

### 4.2 Limit BUY at L
- **gap-through**: O ≤ L − tick → 체결가 = min(L, O + slippage_ticks×tick), `filled_at_open=True`.
- **intrabar**: 그 외 L_bar ≤ L − penetration_ticks×tick (기본 1 tick 관통) → 체결가 = L, `filled_at_open=False`.
- 그 외 미체결.

### 4.3 Limit SELL (TP) at T
- **gap-through**: O ≥ T + tick → 체결가 = max(T, O − slippage_ticks×tick).
- **intrabar**: H ≥ T + penetration_ticks×tick → 체결가 = T.
- 그 외 미체결.

### 4.4 Basket TP
- lane별 평균가 avg(lane) + basket_tp_pts를 tick grid로 **올림**한 가격 T에 sell limit (lane 전체 수량).
- T는 해당 bar의 open 체결(market 진입, gap-through limit) 반영 후 평균가로 계산 (open에서 체결 → 즉시 TP 주문 갱신 가정).

### 4.5 Individual TP
- tranche 체결가 + tp_pts (tick grid 올림)에 sell limit.

## 5. Same-bar 규칙 (1분 OHLC는 H/L 순서 불명)
1. open에서 체결된 진입(market, gap-through limit)은 같은 bar 안의 TP 조건 충족 시 청산 허용.
2. **intrabar limit BUY로 체결된 tranche는 같은 bar에서 청산 금지** (가장 이른 청산 = 다음 bar).
3. 어떤 lane에서 intrabar limit BUY가 체결된 bar에서는 그 lane의 basket TP를 **평가하지 않음** (TP가 BUY 전에 도달했는지 증명 불가 → 불리하게 가정). 해당 bar 수를 `ambiguous_bars`로 집계.
4. 같은 bar에서 TP로 풀린 slot은 그 bar의 다른 BUY에 쓰일 수 없음. 주문은 직전 bar 종료 시점의 여유 capacity 내에서만 생성됨 → 체결 시 capacity 초과 불가.
5. 다른(이미 보유 중인) tranche의 individual TP는 같은 bar의 intrabar BUY와 독립적으로 체결 가능 (각각 이미 걸려있는 주문).

## 6. Gap / 결측 bar
- 결측 bar 구간에는 체결 없음. 결측 후 첫 bar는 §4 gap-through 규칙 적용.
- 대기 주문은 "다음 bar" 한 개에만 유효. 결측 때문에 다음 bar가 다른 거래일이면 폐기.

## 7. 비용
- commission: $0.62 / contract / side (설정 가능).
- slippage: market 및 gap-through 체결 1 tick 불리 (= $1.25/contract). intrabar limit 체결은 slippage 0 (limit 가격 체결, 대신 관통 요건).
- 보고: gross P&L (slippage·commission 제외 이상 가격 기준), slippage 비용, commission, net.

## 8. Roll
- 가격은 additive adjusted 연속. roll(계약 변경) 시 보유 수량 × roll_cost_per_contract 부과.
- 기본 roll_cost_per_contract = 2 sides × $0.62 + 1 tick($1.25) = **$2.49** (calendar spread 1 tick 가정).
- P&L은 adjusted 가격 차이로 계산 → roll 시점 spread로 롤오버한 것과 동등.
- 실제 roll은 roll일 RTH 중에 해야 하나 데이터 roll은 17:00→18:01. 시점 차이에 따른 spread 변동은 무시(근사).

## 9. MTM / Equity
- equity(t) = 초기자본 + realized_net(t) + unrealized(t) − roll_costs(t).
- unrealized(t) = Σ_tranche (close_t − entry_px) × $5 (전 bar, ETH 포함).
- 보조 지표: worst-intrabar unrealized = (low_t 기준).
- notional = qty × raw_close × $5 (raw = adj − cum_adjustment).
- margin stress: margin_per_contract 시나리오($1,500 / $2,500 / $3,500)로 excess liquidity = equity − qty×margin 최소값 보고.

## 10. 사이클
- 전체 사이클: 전 lane 합산 flat → 첫 진입 → 다시 flat.
- lane 사이클: lane 기준 동일 정의 (core basket 사이클).
- 기록: 시작/종료, 진입 수, 최대 수량, realized, 사이클 중 최악 MTM (close 기준 및 low 기준), 기간.

## 11. End-of-test
- 테스트 종료 시 미청산 포지션은 청산하지 않고 **open inventory, 평균가, 미실현 손익을 공개**. 총 경제적 P&L = realized + unrealized.

## 12. 민감도 모델 (향후)
| 모델 | 관통 요건 | intrabar BUY 후 같은 bar TP | slippage |
|---|---|---|---|
| conservative (기본, EXEC-1.0) | 1 tick | 금지 | 1 tick |
| neutral | 0 tick (touch) | 금지 | 1 tick |
| tv_like | 0 tick | 허용 (OHLC 경로 가정) | 0 |
결과가 가장 좋은 모델을 선택하지 않는다. 기본 결론은 conservative로 낸다.

## 변경 이력
- EXEC-1.0 (2026-09-29): 최초 작성.
