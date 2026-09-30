# NEXT_ACTION (단 하나)

## RUN-4 — 진짜 OOS + MES 체결 검증 (데이터 우선), 이후 소규모 사전등록 구조 재검증

### 왜
RUN-3 결과(`latest_report.md`): FQ 수익은 회계상 실재하지만, (a) 2019–2026 전체 in-sample, (b) 활동을 유지하는 구조는 fresh-start 깊이 $22–54k, (c) C32는 2–3틱 슬리피지에서 깊이 붕괴, (d) bottom 예측 edge 없음 — 수익원은 core 재고 + ES drift, recycle은 슬롯 회전 도구.

### 순서 (사전 등록)
1. **데이터**: 2026-05-28 이후 ES 1m 및/또는 MES 1m 확보 → DATA_AUDIT 절차(bytes/hash/rows/range/schema/dup/gap/DST/roll) 후 원본 불변 보관.
2. **Frozen 1회 실행**: `FROZEN_CANDIDATES.json`(C32/C14/C10) + `FROZEN_POSTHOC_FILTERS.json`(C14_bs70, C14_rpos60, C32_bs70) + BASE. 재조정 금지. 보고: 총 MTM, realized/unrealized, open inventory, MTM DD, 무진입, recycle 거래/일·P&L.
3. **MES 체결**: MES 데이터로 limit_close recycle 진입 체결률 / 부분체결 / ES-MES 가격 괴리 측정. 체결 확인 전 C32 계열 보류.
4. (데이터가 여전히 없을 때만) **소규모 구조 재검증**: core 한도 × recycle 슬롯 × 진입 필터 강도 ≤30 configs, 2019–2021에서만 선택, 2022–2026은 확인 전용. 새 broad search 금지.

### 보고 규칙 추가
- "활동" = 무진입일 + recycle 거래/일 + recycle P&L (필터 후보의 recycle 소멸을 숨기지 않기 위해).
- 합성 점수 금지, 자본 등급(≥$75k/$90k/$105k/$120k)으로 병기.
