# DECISIONS

| ID | 날짜 | 결정 | 이유 |
|---|---|---|---|
| D-001 | 2026-09-29 | 연구 코드/상태는 repo `archive-r7k3m9`의 `mes_grid_research/` 하위에 둔다 | 이 세션에 허용된 유일한 repo. 기존 daily-report 사이트 파일과 분리 |
| D-002 | 2026-09-29 | 복원 parquet(`data/`)은 git에 넣지 않는다. `scripts/restore_from_mcp_dump.py`로 재현 | 원본 불변, 38.9MB 바이너리. hash로 lineage 보장 |
| D-003 | 2026-09-29 | 가격은 데이터의 forward additive adjusted 연속가를 그대로 사용, notional/margin은 raw(=adj−cum_adjustment) 사용, roll 시 $2.49/ct 부과 | long 선물의 경제적 P&L(roll carry 포함)을 올바르게 반영. unadjusted는 roll마다 가짜 점프 |
| D-004 | 2026-09-29 | 거래소 휴일(Globex 13:00 조기종료 47일)은 신규 거래 금지 | cash 휴장·저유동성. 조기폐장(13:15) 15일은 정상 거래 |
| D-005 | 2026-09-29 | 기본 체결모델 = EXEC-1.0 conservative (1 tick 관통, 1 tick slippage, intrabar BUY 후 같은 bar TP 금지, 모호 bar의 basket TP 미평가) | 1m OHLC 순서 불명. 유리한 가정 금지 |
| D-006 | 2026-09-29 | Baseline A의 add 규칙 = "완료 bar close ≤ 마지막 체결가 − 5 → 다음 open market 1계약, bar당 최대 1회", flat이면 다음 open에 즉시 1계약 | Pine V2.2 원문 부재. 가장 단순·인과적 해석. TV와 수량 차이의 원인 후보로 기록 |
| D-007 | 2026-09-29 | 시그널은 거래창 bar로만 생성 (09:30 bar-end ETH bar 미사용) → 당일 첫 체결은 09:31 open | RTH-only baseline 원칙 |
| D-008 | 2026-09-29 | TV 수치에 맞추려고 규칙을 바꾸지 않는다. parity 차이는 설명·기록만 | 프로젝트 원칙 |
| D-009 | 2026-09-29 | ROLL-1.0: adjusted 가격 + tranche별 raw 원장. 기본 `basis_adjust`, 브로커 관점 보고는 `close_reopen`. spread = cum_old − cum_new | 두 방식 경제적 동일성을 테스트로 증명. 기존 결과와 센트 단위 일치(ROLL_GATE_001) |
| D-010 | 2026-09-29 | lane capacity 합이 32를 넘는 중첩 허용(동적 배분용). 절대 한도 32는 엔진이 강제 | 32는 목표가 아닌 절대 천장 |
| D-011 | 2026-09-29 | 연구 팩토리는 `FactoryStrategy` 단일 클래스. 기본 설정 = Baseline A (fill 단위 동일성 테스트) | 모든 모듈을 같은 control 대비 단일 변경으로 귀속 가능 |
| D-012 | 2026-09-29 | ATR 기반 모듈의 ATR = RTH 15분봉 ATR(14) (완료된 15분봉만, 누락 분이 있으면 다음 bar에서 완료 인정). 일간 ATR = 이전 14일 RTH TR 평균, 백분위 = 이전 252일 대비 | 1분 ATR은 grid 간격 척도로 너무 작음. 인과성 테스트 통과 |
| D-013 | 2026-09-29 | "worst distance-to-market" 교체 선택 = long에서는 "highest-cost"와 동일 → 별도 실행하지 않음 | 수학적으로 동일 |
| D-014 | 2026-09-29 | Layer-exit(F) 모드는 add 기준가를 '마지막 체결가' 대신 '최저 보유 진입가'로 사용 (LIFO grid의 본질) | 최신 layer를 팔면 같은 레벨에서 재매수 가능해야 함 |
