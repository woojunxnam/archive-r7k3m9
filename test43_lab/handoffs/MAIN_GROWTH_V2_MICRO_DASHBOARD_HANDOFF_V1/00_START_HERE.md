# MAIN_GROWTH_V2 Micro Dashboard Handoff — START HERE

이 폴더가 dashboard Claude Code 세션의 첫 진입점이다.

## 현재 운영 이름
**MAIN_GROWTH_V2 — LIVE CANDIDATE (MICRO)**

구성:
1. `MAIN_GROWTH_V1 = T61-R1C_ATOMIC_CAP6 + FIXED_CLUE_BASKET_V1`
2. `C2_P2_FAILED_FIRST` 1 micro
3. C2의 `FIRST_WINNER_ADD1` 1 micro

실행 계약:
- ES signal -> MES
- NQ signal -> MNQ
- YM signal -> MYM
- RTY signal -> M2K
- mini contract scaling은 이 handoff에 포함하지 않는다.

## 반드시 먼저 읽을 순서
1. `01_PORTFOLIO_SPEC.json`
2. `02_EXECUTION_LOGIC.md`
3. `03_SOURCE_MANIFEST.json`
4. `09_LIVE_IMPLEMENTATION_GAPS.md`
5. `04_DASHBOARD_DATA_CONTRACT.json`
6. `05_RUNBOOK.md`
7. `06_VALIDATION_CHECKLIST.md`
8. `07_HANDOFF_PROMPT.md`

## 중요한 상태
- Research cutoff: **2026-05-27**
- Forward OOS start: **2026-09-29**
- V2 historical comparison window: **2021-01-01..2026-05-27**
- Historical V2 avg/day: **$160.65**
- MaxDD: **$14,105**
- Worst day: **-$4,792**
- Ret/DD: **0.01139**
- V2 is user-promoted as a **dashboard/live candidate**.
- 이것은 broker 주문 전송 승인과 동일하지 않다. 이 패키지의 `broker_live_authorization = NO`.

## 가장 중요한 금지사항
- frozen T61을 수정하지 말 것.
- frozen clue basket 모델/규칙을 retune하지 말 것.
- C2 threshold를 새로 최적화하지 말 것.
- ADD2/물타기/recovery를 V2에 추가하지 말 것.
- historical output parquet을 live signal source로 사용하지 말 것.
- 2026-05-28 이후 데이터를 연구/retune 용도로 사용하지 말 것.

## Live 구현 blocker
현재 repo에는 T61 forward-shadow runner는 있으나,
- Fixed Clue Basket의 단일 forward integration runner는 아직 없고,
- C2+winner의 통합 forward runner도 아직 없으며,
- historical C2 portfolio allocator는 진입 시 future occupancy interval을 보는 비인과적 capacity precheck를 사용한다.

따라서 dashboard는 먼저 **read-only/shadow integration**으로 구현하고, causal capacity allocator를 재현/검증한 뒤에만 broker execution으로 넘어간다.
