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
| 25 | FQ: 항상 활성 floating recycle + 회복모드 | Y | TESTED(S4b,S3b,S5,S6) | 유일한 capacity+DD 동시 개선 계열 → RUN-3 |
| 26 | 무진입 기간 지표 | – | ADOPTED | D-015 |
| 27 | FQ 자본위험 스케일링 (fresh-start 기준) | – | QUEUED | RUN-3 A |
| 28 | Limit 기반 recycle 진입 + slippage 탄력성 | – | QUEUED | RUN-3 B |
| 29 | 계좌 DD 기반 tail 위험정책 | – | QUEUED | RUN-3 D, 별도 등록 |
| 30 | FQ 회계 감사 (per-bar 불변식) | – | DONE | Phase 0 PASS (D-021) |
| 31 | Capital frontier (cap 10–32 × split) | – | DONE | 활동 vs 깊이 충돌 (D-026) |
| 32 | Recycle limit 진입 (limit_close) | – | DONE | C32 depth 소폭 개선(2–3틱에서), 활동 유지. 결선 |
| 33 | 이익 layer 수확 (all_prof +3/+5) | – | DONE | C32 fresh 28k→44–54k, 손익 −40~46%. 결선(harv5) |
| 34 | LIFO recycle 청산 (last/last2) | – | REJECTED | C32 fresh depth 악화(11–24k) |
| 35 | 계좌 DD core pause (core/core_harvest/progressive) | – | REJECTED | FQ에서 무효과 (D-025) |
| 36 | 계좌 DD all-pause / equity cap | – | REJECTED(활동) | depth 개선이나 무진입 298–758일 |
| 37 | Bottom event 조건 / BottomScore / ML | – | REJECTED(단독 edge) | D-024 |
| 38 | Recycle 진입 필터 (bs70, rpos60≤0.05, rpos5d, below_pdl 등) | – | PARTIAL | fresh depth 개선 + 무진입 짧음, 대신 recycle 활동 거의 소멸 → "core 중심 grid + 희소 recycle" 구조. YM post-hoc 일관. RUN-4 검증 대상 |
| 39 | Recycle cooldown / 동적 TP (vol, ATR, late, inv) | – | REJECTED | 차이 ≤ 노이즈, tp_inv는 C32 depth 악화 |
| 40 | Core 필터 (core_deep, no-gap-down), momentum governor, volcap | – | REJECTED | core_deep는 손익 −30%, 나머지 무효과 |
| 41 | 진짜 OOS: 2026-05-28 이후 ES / MES 1m | – | BLOCKED(데이터) | FROZEN_CANDIDATES.json + FROZEN_POSTHOC_FILTERS.json 준비됨 |
| 42 | 주문 수준 MES 체결 시뮬레이션 (queue, partial fill) | – | QUEUED | limit 진입 결론의 전제 |
