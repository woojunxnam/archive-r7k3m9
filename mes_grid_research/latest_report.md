# latest_report — RUN-2 (Roll gate + Research factory), 2026-09-29

engine 0.2.0 · EXEC-1.1 conservative · ROLL-1.0 · 데이터 SHA `2b4f41b1…c454116` · 2019-05-05 ~ 2026-05-27 · $150k 기준 · MES $5/pt
(이전 보고서: git history의 RUN-1 `latest_report.md`)

## 1. Roll gate — PASS
- 메타데이터: `contract`(29계약), `cum_adjustment`(계약 내 상수), `roll_adjacent`(신계약 첫 세션). roll 28회 모두 17:00→18:01. 조정 = 첫 계약 기준 forward additive, spread = cum_old − cum_new.
- ROLL-1.0: 모든 tranche가 논리 ID를 유지하며 계약별 raw 원가를 들고 roll을 넘어감. `basis_adjust`(원가 이동) / `close_reopen`(구계약 실현 후 재개시) 두 방식은 equity 곡선이 동일하고 realized/unrealized 분할만 다름. 청산 시 불변식 오차 0.0.
- 비용: roll 1회당 계약당 $2.49 (commission 2 sides + spread 1 tick), 2× slippage $3.74.

| 항목 | 기존 연속시리즈 | ROLL basis_adjust | ROLL close_reopen | roll 2× slip | naive 비조정 (금지) |
|---|---|---|---|---|---|
| 총 MTM P&L | 480,297.31 | 480,297.31 | 480,297.31 | 479,622.31 | 504,073 (+23.8k 가짜) |
| realized (논리) | 479,737 | 479,737 | 479,737 | 479,062 | 503,513 |
| 종료 미실현 | +560 | +560 | +560 | +560 | +560 |
| Max MTM DD | −204,875 | −204,875 | −204,875 | −204,915 | −196,556 (과소) |
| 최장 32-lock | 616일 | 616일 | 616일 | 616일 | 691일 |
| roll 비용 합계 | 1,344.60 | 1,344.60 | 1,344.60 | 2,019.60 | 0 |

stress 창 (최악 미실현 시점):
| 창 | 최악 시점 | 수량 | adjusted 평단 | raw 손익분기(현재 계약) | 브로커 평단(close_reopen) | roll 시 실현된 손실(브로커) | 회복 |
|---|---|---|---|---|---|---|---|
| 2020 | 2020-03-22 | 32 | 3,222.5 | 3,222.0 | 2,399.5 | −$131.6k | 2020-06-08 |
| 2022–23 | 2022-10-13 | 32 | 4,610.0 | 4,559.3 | 4,137.0 | −$67.6k | 2023-12-14 (8회 roll 통과) |
| 2025 | 2025-04-06 | 32 | 5,636.6 | 6,114.1 (M5) | 5,731.8 | −$61.2k | 2025-06-26 |
→ 기존 결과는 모두 유효. 장기 보유는 roll마다 contango carry를 지불(2025: raw 손익분기가 roll 후 6,114로 상승). naive 비조정은 2022–23 "회복"을 2023-07-27로 잘못 보고함(실제 2023-12-14).

## 2. 테스트한 설정 수
| 단계 | 내용 | 설정/실행 |
|---|---|---|
| S1 broad screen | 19개 모듈 가족(A–R), 각 1개 변경 | 202 |
| S3 local robustness | 22개 후보 × 인접/±10/±20% | 103 |
| S4 interactions | 선택 2-way + 소수 3/4-way | 28 |
| S4b capacity-maintenance combos | floating recycle + core 위험 모듈 | 19 |
| S3b robustness (FQ 계열) | | 28 |
| Walk-forward | 4개 가족 × 4 fold | 23 |
| S5 temporal | 결선 12개 연도/rolling 12m/top-10 DD + fresh start 3개 | 12 + 36 |
| S6 execution/cost | 결선 12개 × 10종 | 120 |
| 합계 | **고유 설정 372개, 총 실행 약 570회** (+ 결정성 확인용 v2 재실행 333회, 결과 동일) | |

## 3. 가장 강한 메커니즘
**핵심 재해석**: "최장 무진입 기간"을 추가하자 DD를 줄인 모듈 대부분이 **2022-01 → 2024-02 약 750일 동안 신규 진입 0**임이 드러남. 즉 32계약 lock을 16–24계약 lock으로 바꾼 것일 뿐.

| 메커니즘 | 효과 | 강건성 | 판정 |
|---|---|---|---|
| **FQ: 항상 활성 floating recycle(low60 앵커) + 회복모드(core 가득 차면 core 정지, core layer +5 개별 청산, recycle TP 2 / 간격 10)** | 무진입 5.8일, 활동일 97%, DD −$116k~−$130k, 최소 equity ~$100k, >24계약 7–43일 | S3b 28개 전부 DD −$104k~−$139k, ret/DD 2.1–2.6 | **capacity + DD 동시 개선 — 유일** |
| 노출 상한 (cap 16/20/24) | DD −$107k/−$132k/−$157k, ret/DD 2.9/2.7/2.4 | 13–29 전 구간 매끈, WF 4 fold 모두 cap16 선택 & OOS DD 1위 | 위험 크기 조절로는 최강, 그러나 무진입 ~760일 |
| 회복모드 Q / state machine I_S6 | DD −$98k~−$130k | 안정 | 무진입 ~750일 (더 작은 lock) |
| Armed-reversal add (lower-low failure / bull higher-close) | 같은 DD에서 +$51k~$64k | ±20% 안정 | 수익 개선 모듈 |
| ATR-spike governor | 2020 급락 DD −$164k → −$65k, 최소 equity $108k | 2020에만 효과, WF 불안정 | 급락 전용 보조 |

## 4. 실패한 메커니즘
- **Rolling recycle (CR_002, B 가족 18개)**: 32-lock 4–8일로 capacity는 유지하나 DD −$207k~−$224k로 악화, 손익 −30%, underwater 880–1,016일. 하락 중 손실을 실현하고 반등을 놓쳐 평균회귀 edge 제거. 선택 방식(highest/oldest)은 하강 ladder에서 동일.
- **Profit-only recycle 고정 배분 (A)**: CR_001 재확인, lock 660–757일.
- **느린 core 간격 (C: fixed 7.5–15, convex, ATR, %, DD, vol, age)**: DD −$151k~−$203k로 감소하나 ret/DD 1.5–2.2 < base 2.34, 노출 상한에 지배됨. 2022 bear에서 여전히 450–730일 무진입.
- **Cycle-age core-off (J) 및 gov+age 조합**: 2025 개선은 경로 운 — 2024-12-23 ~ 2025-07-03 진입 0건. 기각 (D-016).
- Basket TP 변경(G), 진입 필터(K), 시간대(O), recycle TP 변경(E), 동적 core cap(H/A dyn), ETH 컨텍스트(P): 대부분 NEUTRAL 또는 거래 중단형. P(갭다운 진입)의 수중기간 289일은 경로 의존.
- Float vs ladder 간격: recycle TP(3) < step(5)이면 구조적으로 동일 → 별도 증거 아님.

## 5. Pareto 후보 (손익 × Max MTM DD × 무진입일, 비지배 65개 중 대표) — `PARETO_CANDIDATES.csv`
| 후보 | 총 MTM | Max DD | 최소 equity | 무진입 | >24계약 | 거래/일 | 평균 notional | 비고 |
|---|---|---|---|---|---|---|---|---|
| BASE | 480k | −205k | 17k | 616일 | 621일 | 1.9 | 399k | control |
| **FQ_12_20** | 256k | **−116k** | 103k | **5.8일** | 6.9일 | 3.8 | 264k | 최저 DD + capacity |
| **FQ_16_16_add** | 306k | −122k | 103k | **5.8일** | 24.9일 | 4.1 | 283k | 균형 |
| FQ_18_14_add | 322k | −122k | 82k | 25일 | 24.9일 | 4.1 | 286k | |
| FLOAT_16_16 (단일 모듈) | 404k | −169k | 76k | 59일 | 453일 | 4.1 | 368k | 고수익 capacity |
| CAP16 | 307k | −107k | 84k | 763일 | 0 | 1.3 | 262k | 거래 중단형 |
| CAP20 + armed add | 390k | −131k | 71k | 756일 | 0 | 1.6 | 314k | 거래 중단형 |
| QC24 + gov | 292k | −113k | 107k | 484일 | 3.8일 | 1.4 | — | 거래 중단형 |
| ADD_llfail (단일) | 531k | −204k | 22k | 733일 | 734일 | 2.1 | 412k | 수익형, 위험 불변 |
낮은 손익 후보(FQ_12_20)를 버리지 않음: 같은 자본에서 DD 43% 감소 + 거래 지속.

모든 후보 종료 시 open inventory 4–7계약, 미실현 +$560~+$986 (공개).

## 6. 2022–23 / 2025 stress 동작
| 후보 | 2020 DD | 2022–23 DD | 2022–23 >24계약 | 2025 DD | 2025 lock | top-DD 최장 수중 |
|---|---|---|---|---|---|---|
| BASE | −168k | −171k | 621일 | −205k | 121일 | 618일 |
| FQ_16_16_add | −75k | −122k | 25일 | −101k | 0 | 709일 |
| FQ_12_20 | −70k | −116k | 7일 | −94k | 0 | 709일 |
| CAP16 | −90k | −102k | 0 | −107k | 0 (16계약 방치) | 765일 |
Fresh start (새 $150k, 과거 이익 없음):
| 시작 | BASE 최소 equity | FQ_16_16_add | FQ_12_20 | CAP16 |
|---|---|---|---|---|
| 2022-01-01 | **−$10k (파산)** | $28k | $35k | $49k |
| 2023-01-01 | $149k | $139k | $148k | $149k |
| 2025-01-01 | **−$40k (파산)** | $65k | $66k | $55k |

## 7. 최대 lock / MTM DD 개선
- 최장 무진입: 616일 → **5.8일** (FQ 계열), 32-lock 616일 → 0.
- Max MTM DD: −$205k → **−$116k (FQ_12_20, −43%)**; 거래 중단을 허용하면 −$77k(경로 운) / −$98k(Q_16_16)까지 가능하나 capacity 실패.
- 최소 equity: $16.8k → ~$100k.
- Rolling 12m 최악 DD: −$190k → −$106k~−$118k.

## 8. 거래 빈도 변화
- BASE 1.94 trades/일(계약 round-trip), 활동일 44%.
- FQ 계열 3.8–4.1/일 (core ~1.0 + recycle ~3.0), **활동일 97%**, recycle lane 가득 찬 시간 0%, 평균 여유 recycle slot 11.8/16.
- 비용: FQ $18.6k–$19.8k (BASE $10.7k), 여전히 gross 대비 작음.

## 9. 해결 안 된 위험
1. **깊이**: FQ도 2022-01 fresh start에서 최소 equity $28k (−81%). $150k 계좌에 16–32 MES 롱 무손절은 여전히 과도.
2. **회복 기간**: 2022 bear 수중 ~708일은 어떤 모듈로도 줄지 않음 (보유 재고의 경제 손실은 사라지지 않음).
3. **체결 민감도**: FQ DD가 slippage 2틱에서 −$122k → −$148k. TV-like 체결은 FQ를 과대평가(−$111k). recycle 진입이 market 주문 전제.
4. **데이터**: ES 1m로만 검증. MES 체결·스프레드 미검증. 1분 OHLC 순서 불명.
5. **과최적화 위험**: 전 결과 in-sample 탐색. WF는 4개 가족만. FQ 계열은 이 run의 발견이므로 독립 기간 검증 전.
6. TV parity 미완(Pine 원문 필요).

## 10. 다음 연구 run (정확히)
**RUN-3 — FQ 계열의 자본위험 보정 + 체결 현실성** (`NEXT_ACTION.md`):
A) total ceiling 10/12/14/16/20/24 스케일링, 1차 판정 = fresh-start(2020-02, 2022-01, 2025-02) 최소 equity ≥ $75k;
B) recycle 진입 market vs limit, slippage 1/2/3틱 × recycle TP 2.5/3/4 → DD 탄력성;
C) 2019–2021 설계 / 2022–2026 검증 고정 분할(재선택 금지);
D) 분리 등록 tail 위험정책(계좌 DD −X% 시 core 금지 vs 부분 청산).
병행: MES 1m 데이터 확보(Massive 커넥터 인증 필요).
