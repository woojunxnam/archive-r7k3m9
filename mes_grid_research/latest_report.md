# latest_report — 2026-09-29

엔진 0.1.0 · EXEC-1.0 (conservative) · 데이터 SHA `2b4f41b1…c454116` · 기간 2019-05-05 ~ 2026-05-27 · 모두 in-sample

## 1. 무엇을 테스트했나
1. 데이터 복원·감사 (39 chunk → parquet, bytes/SHA/rows/범위/schema/중복/gap/DST/roll)
2. 실행 엔진 + 35개 unit test (필수 20항목 + roll/휴일/전략 동치성/no-lookahead)
3. **Baseline A** = 이전 TV Basket +25의 단순 재구성: flat이면 다음 open 1계약, `close ≤ 마지막 체결가 − 5`면 다음 open 1계약 추가, basket 평균 +25 limit 청산, max 32, hard SL 없음
4. **Parity 매트릭스**: adjusted vs unadjusted(TV 기본 연속차트) × conservative vs TV-like 체결 × 시작일 5개
5. **CR_001**: Core/Recycle R1 (profit-only) 24/8·20/12·16/16 × recycle TP 2.5/3/4/5 × 활성화(항상 / core full일 때만), control 32/0

## 2. Baseline A — 필수 지표

**Return**
| 항목 | 값 |
|---|---|
| realized net | **+$479,737** |
| 종료 미실현 (4계약 open, 2026-05-26 진입) | +$560 |
| 총 MTM P&L | +$480,297 (CAGR 22.5%, $150k 기준) |
| 연도별 MTM | 2019 +29k · 2020 +48k · 2021 +93k · **2022 −107k** · 2023 +122k · 2024 +107k · 2025 +100k · 2026(5월) +88k |
| 연도별 realized | 2022 +8.5k, 2023 +6.1k (2년간 거의 거래 정지) |
| PF / 평균 / 중앙값 trade | 5.47 / +$140 / +$128 (계약 단위 round-trip) |
| trades / 일 | 3,439 / 1.94 |
| 완료 사이클 | 514 (100% 이익), 사이클당 평균 6.7계약 |

**Cost**: commission $4,267 · slippage $5,089 · roll $1,345 · 합계 $10,700 (gross profit의 1.8%)

**Risk**
| 항목 | 값 |
|---|---|
| **Max MTM DD** | **−$204,875** (peak 2025-02-21 → trough 2025-04-06) |
| intrabar low 기준 | −$205,321 |
| realized equity DD | −$578 ← closed-trade만 보면 위험이 안 보임 |
| **최소 equity** | **$16,761 (2020-03-22)** — $150k 시작 계좌가 89% 손실 상태 |
| 최악 사이클 MTM | −$198,221 (2025-02-19 ~ 06-26) |
| 최악 일/주/월 | −$48.7k (2025-04-04) / −$80.9k (2025-04-04 주) / −$81.8k (2020-03) |
| 최장 underwater | 618일 (2022-04-05 → 2023-12-14) |

**Top MTM drawdowns (일간 equity)**: 2025-02-18→04-08 −$190k (회복 06-26) · 2020-02-16→03-22 −$164k (회복 07-17) · 2022-04-04→10-12 −$155k (회복 **2023-12-13**, 618일) · 2022-01 −$76k · 2024-07/08 −$58k …

**Inventory** (RTH 시간가중)
| avg | median | p95 | p99 | max | ≥8 | ≥16 | ≥20 | ≥24 | ≥28 | =32 |
|---|---|---|---|---|---|---|---|---|---|---|
| 18.1 | 18 | 32 | 32 | 32 | 64% | 52% | 48% | 46% | 44% | **42%** |

- 최장 32-lock: **2022-04-11 → 2023-12-18 (616일)** · 2020-02-26 → 07-20 (145일) · **2025-02-25 → 06-26 (121일)** · 2022-01-20 → 03-29 (68일)
- 최장 >24 구간: 621일 (2022-04-06 → 2023-12-18)

**Exposure / margin**: peak notional $1.108M (32 × raw 가격) · peak notional/equity 20.8× · margin $1,500/ct 가정에서도 excess liquidity 최소 **−$31k (2020-03-22)** → 실제로는 margin call/강제청산 발생 구간

**2025-02~07 regression 창**: 32 도달 2025-02-25 10:07 · lock 121일 · 창 내 RTH의 69%가 32계약 · 창 내 최악 미실현 −$204.7k (2025-04-06) · 최소 equity $262.7k (그전 누적 이익 덕분)

## 3. TradingView parity
| 변형 | 사이클 | 진입 | realized | 2025 lock | 최악 사이클 |
|---|---|---|---|---|---|
| TV (제공값) | 306 | 2,444 | $344.7k | ≈118일 (02-28→06-26) | ≈−$195k |
| adjusted, 2019 시작, conservative | 514 | 3,443 | $479.7k | 121일 (02-25→06-26) | −$198k |
| adjusted, 2019, TV-like 체결 | 521 | 3,460 | $485.0k | 121일 | −$198k |
| unadjusted, 2022 시작 | 333 | 2,248 | $333.7k | 119일 (02-25→06-24) | −$190k |
| adjusted, 2024 시작 | 312 | 2,123 | $294.4k | 121일 | −$198k |

해석:
- **실패 모드는 가정에 강건함**: 2025 lock과 −$190k~−$198k 사이클 MTM은 모든 변형에서 재현. TV에서 본 위험은 실재한다.
- 체결모델(1 tick 관통 vs touch, same-bar 허용)은 realized를 ≤1.1%만 바꿈 → 이 전략은 intrabar 가정에 민감하지 않음 (bar당 1회 market add 구조이므로).
- unadjusted 연속차트는 2023년 이후 roll마다 +45~74pt 가짜 점프 → realized +5%, lock 종료가 약간 빨라짐. TV 차트 설정 확인 필요.
- TV 수치와 정확히 일치하는 변형 없음. TV는 basket당 8.0계약, Python은 6.7계약 → **add 규칙(평단 기준? 첫 진입 기준? bar당 복수 add?)과 테스트 시작일이 다를 가능성**. Python 결과를 TV에 억지로 맞추지 않음 (D-008).
- **중요**: TV 요약에는 없던 **2022-04 → 2023-12 616일 32-lock**이 전체 데이터에서 가장 심각한 lock. TV 테스트가 2023년 이후로 시작했을 가능성.

## 4. CR_001 — Core/Recycle R1 (profit-only)
| config | realized | Max MTM DD | 최소 equity | 32 비중 | 최장 32-lock | recycle trades/일 | recycle full 비중 | 2025 lock |
|---|---|---|---|---|---|---|---|---|
| **32/0 control** | 479.7k | −204.9k | 16.8k | 42% | 616일 | 0 | – | 121일 |
| 24/8 tp3 always | 516.7k | −211.5k | 16.1k | 51% | 757일 | 4.5 | 68% | 123일 |
| 24/8 tp3 core_full | 442.3k | −205.4k | 18.8k | 45% | 741일 | 2.0 | 45% | 99일 |
| 16/16 tp3 always | 572.3k | −213.7k | 16.8k | 53% | 741일 | 8.5 | 54% | 125일 |
| **16/16 tp3 core_full** | 478.6k | **−201.3k** | 20.7k | 43% | 661일 | 5.4 | 43% | **95일** |
| 16/16 tp5 always | 586.0k | −213.9k | 17.8k | 54% | 746일 | 5.3 | 55% | 125일 |

(전체 25개 설정: `results/CR_001/summary.csv`, `master_results.csv`)

- recycle 거래는 모두 이익 청산(정의상 profit-only), recycle P&L +$66k~+$280k.
- 그러나 **recycle lane도 추세 하락에서 가득 차 잠김** (full 42–69%). "always"는 노출을 늘려 DD와 lock을 악화. "core_full"도 core capacity가 줄어 core 평단이 덜 낮아지고 core 회복이 늦어짐 → 최장 lock이 616일 → 660–741일로 늘어남.
- 가장 나은 16/16 core_full도 DD 개선 $3.6k(1.8%)에 불과.

## 5. 최대 위험 / 실패
- 모든 버전이 $150k 계좌 기준 **최소 equity $15k~$22k**, Max MTM DD ≈ −$200k. 실거래 불가 수준.
- 근본 원인(가설): 5pt 고정 grid는 32계약을 ~155pt(가격의 약 2.6%) 안에 소진. 20%+ 하락(2020, 2022, 2025)에서 평단이 하락 초입에 고정되고 나머지 수백 pt를 무방비로 맞음. lane 분할(R1)은 이 기하학을 바꾸지 못함.
- ES 데이터 기반. MES 실제 체결 미검증.

## 6. 가설 판정
- "Python이 TV 실패 모드를 재현한다" → **확인** (그리고 전체 기간에서는 더 나쁨).
- "R1 profit-only recycle reserve가 lock/MTM DD를 줄인다" → **기각** (CR_001).

## 7. 다음 한 단계
**CR_002 — R3 rolling recycle** (`NEXT_ACTION.md`): recycle lane이 가득 차고 가격이 더 내려가면 최고 원가 tranche를 손실실현 후 현재가 근처로 교체. 노출은 줄지 않으므로 DD 개선은 기대하지 않고, capacity 유지와 총 경제적 P&L(realized+unrealized)을 평가한다. 이후 후보: core grid geometry(convex/ATR widening), freefall governor.
