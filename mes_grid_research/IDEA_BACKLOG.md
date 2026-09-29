# IDEA_BACKLOG

상태: `TESTED(S1)` = FACTORY_S1에서 단일 모듈로 검증 · `QUEUED` = 아직 · `REJECTED` = 기각 · `DEFERRED` = 데이터/엔진 선결 필요

| # | 아이디어 | 가족 | 상태 | 비고 |
|---|---|---|---|---|
| 1 | 32/28/24/20/16 core + recycle 고정 배분 | A | TESTED(S1) | core_full/always 활성화 |
| 2 | 3층 구조 (core/recycle/emergency) | A/H | TESTED(S1) | emergency = 나머지 lane full + 최저가 −step |
| 3 | 동적 core cap (vol/DD/age) | A/H | TESTED(S1) | |
| 4 | Rolling recycle (pts/ATR/new-low/reversal × highest/oldest) | B | TESTED(S1) | worst-distance = highest (D-013) |
| 5 | 느린 core 축적: fixed/convex/tiers/ATR/%/DD/vol-pct/age 간격 | C | TESTED(S1) | |
| 6 | Floating recycle anchor (runhigh/low30/low60/vwap/range/swing) × ladder/float | D | TESTED(S1) | |
| 7 | Recycle TP (pts/ATR/inventory/age/vol) | E | TESTED(S1) | |
| 8 | Layer exits (last/last2/last4/all_ind/newest/deepest/partial) | F | TESTED(S1) | LIFO 기준가 (D-014) |
| 9 | Basket TP 5–30, ATR basket, scale-out, VWAP/prev-close reclaim | G | TESTED(S1) | |
| 10 | State machine NORMAL/ELEVATED/HIGH/CRITICAL/RECOVERY | I | TESTED(S1) | |
| 11 | Cycle-age: core off / recovery | J | TESTED(S1) | |
| 12 | Initial entry filters (VWAP/range/BB/Keltner/session/prev-close) | K | TESTED(S1) | |
| 13 | Armed-reversal add, cooldown | L | TESTED(S1) | |
| 14 | Freefall governor (12 조건 × core/all) | M | TESTED(S1) | |
| 15 | Exposure caps (fixed/equity/DD/vol/notional) | N | TESTED(S1) | |
| 16 | Time of day | O | TESTED(S1) | |
| 17 | ETH context (gap-down / open location / ON return / below ON low) | P | TESTED(S1) | 라벨된 ETH 실험 |
| 18 | Recovery mode | Q | TESTED(S1) | |
| 19 | Roll 2× slippage, close/reopen 보고 | R | TESTED(S1) | |
| 20 | 강제청산 / hard stop 위험정책 | – | QUEUED | 별도 위험정책 실험으로만 (프로젝트 원칙) |
| 21 | Limit 기반 recycle 진입(현재는 market next-open) | D/E | QUEUED | intrabar 모호성 규칙이 결과에 영향 → execution 민감도와 함께 |
| 22 | MES 1m 데이터 검증 | – | DEFERRED | 데이터 미확보 |
| 23 | Walk-forward 파라미터 재선정 | – | QUEUED | Stage 5에서 부분 수행 |
| 24 | 1초/틱 데이터로 same-bar 순서 확인 | – | DEFERRED | 데이터 없음 |
