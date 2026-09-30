# NEXT_ACTION (단 하나)

## RUN-5 — 벤치마크 교체 + 진짜 OOS, 그 다음에만 새 알파 원천

### 왜 (RUN-4 결과, `latest_report.md`)
- FQ recycle 타이밍은 무작위 타이밍(NULL-C)·dumb recycle(NULL-B)을 이기지 못했다. FQ 손익은 평균 재고 × ES drift이며, 같은 평균 노출의 수동 static long보다 Max DD·fresh-start가 좋은 A 설정은 0개.
- 활동 유지(적은 계약)는 rebound salvage / prof_be로 달성했지만 그 효과는 탈위험이다.
- Sleeve B 1분 long 모멘텀은 비용 전부터 음(−) — SATURATED. B7F만 약한 생존.
- A+B 주 평균 $280–490(16계약) — 주 $4k까지 8–14배, 알파 없는 스케일링은 레버리지일 뿐.

### 사전 등록 순서
1. **벤치마크 규칙 채택**: 모든 A 후보는 (a) 같은 평균 재고의 수동 static long(NULL-D), (b) 무작위 타이밍 recycle(NULL-C, ≥20 seed)을 **동시에** 이겨야 생존. 이기지 못하면 탈락. 보고에 두 null 대비 초과 손익, 계약-일당 손익, DD·fresh 차이를 필수 표기.
2. **진짜 OOS**: 2026-05-28 이후 ES 1m 또는 MES 1m 확보 → DATA_AUDIT 절차 → frozen 후보(수동 long q=4/8, FQ-salvage 8/8, prof_be 4/8, B7F)를 재조정 없이 1회 실행.
3. **Sleeve A 재정의(선택)**: "노출 관리형 long"으로 목표를 바꿔 수동 long 대비 DD/fresh 개선만 평가(예: 반등 후 탈위험, 변동성 기반 노출 조절). 새 알파라고 부르지 않는다.
4. **새 알파 원천은 사용자 승인 사항**: Sleeve C(추세 추종·다일 보유), Sleeve D(다른 시장), short 허용 여부. 현 범위(ES 1m long-only)에서는 알파가 고갈된 것으로 판단.
5. Sleeve B: 1분 모멘텀 탐색 중단. B7F는 이벤트 파라미터 이웃 안정성 재검증을 통과할 때만 유지.
