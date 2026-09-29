# NEXT_ACTION (단 하나)

## RUN-3 — FQ 계열의 자본위험 보정 + 체결 현실성 (Capital-at-risk calibration & execution realism)

### 왜
FQ(floating recycle + 회복모드)는 capacity(무진입 6일)와 DD(−$116k~−$130k)를 동시에 개선한 유일한 강건 계열이지만:
1. 2022-01 fresh start에서 최소 equity ~$28k (시작 $150k 대비 −81%) → 여전히 실거래 불가 수준의 깊이.
2. Max DD가 slippage 2틱에서 −$122k → −$148k로 민감 (recycle 약 3회/일, TP 3pt).
3. 2022 장기 하락 underwater ~708일은 어떤 모듈로도 해결되지 않음 (보유 재고의 경제적 손실은 사라지지 않음).

### 사전 등록 설계
- 대상: FQ_16_16_add, FQ_12_20 (control: BASE, CAP16, FQ 원본)
- A. 자본위험 보정: total ceiling 10/12/14/16/20/24 × core/rec 비율 고정 → **1차 판정 지표 = fresh-start(2020-02, 2022-01, 2025-02) 최소 equity ≥ $75k(자본의 50%)**, 부차: 손익, 무진입일
- B. 체결 현실성: recycle 진입을 market(next open) vs limit(현재 low60 기준) 비교, slippage 1/2/3틱, recycle TP 2.5/3/4 → DD의 slippage 탄력성 측정
- C. 기간 분할: 2019-2021 설계 / 2022-2026 검증을 명시적으로 고정 (파라미터 재선택 금지)
- D. (분리 등록) 극단 tail 위험정책: 계좌 DD −X% 도달 시 core 신규 금지 vs 부분 청산 — 강제청산은 별도 위험정책 실험으로만
- 보고: realized/unrealized/총 MTM, open inventory, MTM DD, 무진입일, fresh-start 최소 equity, slippage 탄력성

### 선결/병행
- MES 1m 데이터 확보 (Massive MCP 인증 필요) → Phase 9 검증 준비
