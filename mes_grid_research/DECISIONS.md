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
| D-015 | 2026-09-29 | "inventory lock" 평가에 **최장 무진입 기간(no_entry_days)**과 활동일 비율을 필수 지표로 추가. 32계약 lock만으로 판단하지 않음 | S4 검증에서 DD 개선 조합 대부분이 2022-01~2024-02 약 750일 무진입(더 작은 lock)임을 발견 |
| D-016 | 2026-09-29 | X_gov+age 계열의 2025 개선은 경로 운으로 판정(2024-12-23~2025-07-03 진입 0건), 후보에서 제외 | 단독 모듈은 2025를 막지 못함, 거래 중단이 원인 |
| D-017 | 2026-09-29 | Rolling recycle(B)은 capacity 유지 도구로만 기록, 단독 후보로 승격하지 않음 | lock 4-8일이지만 DD 악화, 손익 -30%: 하락 중 손실 실현이 평균회귀 edge를 제거 |
| D-018 | 2026-09-29 | 1차 결선 구조 = FQ 계열(항상 활성 floating recycle low60 + 회복모드 layer exit). 최종 선정 아님(in-sample, ES 데이터, slippage 민감) | capacity와 DD를 동시에 개선한 유일한 강건 계열 |
| D-019 | 2026-09-29 | 합성 점수 금지 유지. Pareto는 (손익, Max MTM DD, 무진입일) 3축 비지배 집합으로 산출, 나머지 지표는 병기 | 사용자 지시 |
| D-020 | 2026-09-29 | RUN-3 이후 모든 결과 라벨 = "ES-signal / MES-economics proxy backtest". ES OHLC를 MES 가격 proxy로 사용($5/pt). MES 데이터는 최종 frozen 검증에만 사용 | ES→MES 아키텍처 addendum. MES 체결 품질·roll 정렬은 미검증 |
| D-021 | 2026-09-29 | 엔진 `audit=True` 모드: 매 bar lane/tranche 수량 일치, cost-sum drift, capacity, 열림=닫힘+보유, 사라진 tranche 금지를 강제. `audit.reconcile()`로 realized = Σ(exit−entry)×qty×5 − commission − roll 검증 | FQ 수익이 회계 오류가 아님을 증명(Phase 0, 713,842 bar×3 후보 PASS, 오차 ~5e-8) |
| D-022 | 2026-09-29 | 2022–2026은 OOS가 아니다(FQ는 2019–2026 전체에서 발견). 진짜 OOS = 2026-05-28 이후 ES 또는 MES 데이터에서 frozen 후보(FROZEN_CANDIDATES.json, commit 3536a01) 1회 실행 | 사용자 규칙 |
| D-023 | 2026-09-29 | 외부 데이터가 없어 YM(다우 선물) 동기간 cross-market 검증을 1회 수행(가격을 ES 수준으로 k 배율 변환, 규칙 재조정 없음). OOS가 아닌 "다른 시장 구조 검증"으로만 표기 | 시간 OOS 불가 시 차선책. 같은 기간·상관 높은 시장이므로 증거력 제한 |
| D-024 | 2026-09-29 | Bottom event study 결론: 단일/2단/3단 bottom 조건과 chronological ML(AUC 0.50–0.51) 모두 신뢰할 만한 edge 없음 → FQ 수익원은 bottom picking이 아니라 재고 구조 + ES 상승 drift로 해석. Smart-entry 필터는 recycle 활동을 줄이는 "위험 조절기"로만 평가 | BOTTOM_EVENT_STUDY.csv, results/RUN3_BOTTOM |
| D-025 | 2026-09-29 | 계좌 DD 기반 core-pause 계열(core/core_harvest/progressive)은 FQ에서 무효과로 판정 — FQ의 recovery mode가 이미 core 추가를 멈춤. "all" pause와 equity-cap은 depth를 줄이지만 무진입 300–760일을 만들어 활동 유지 목표에 실패 | results/RUN3_P45 |
| D-026 | 2026-09-29 | 32계약 이하 FQ에서 "활동 유지"와 "fresh-start depth ≤ $75k" 는 동시 달성 불가(이 모델 공간 내). recycle slot ≤12 → 2022–2024에 무진입 160–620일, recycle slot ≥16(총 32) → worst fresh min equity $22–35k | Phase 2 frontier |
| D-027 | 2026-09-30 | RUN-4 실행 관리: `results/RUN4_OVERNIGHT/RUN4_MANIFEST.json`(config_id = sleeve + sha1(params, exec, fresh, extra)[:12]) + append-only `RUN4_STATUS.csv`(마지막 행이 권위). 재시작 시 COMPLETE + 결과 파일이 있는 config는 건너뜀. 동시 실행은 메모리 가용량 기반 in-flight 제한(시작 2, 최대 3) | 컨테이너 재시작 대비, 완료 결과 보존 |
| D-028 | 2026-09-30 | Sleeve B는 numba 단일 포지션 시뮬레이터(`fastsim.sim_single`)로 실행. 엔진 기준 구현(`strategies_b.MomentumStrategy`)과 fill 단위 동일성을 테스트로 보장(시장가/지정가 진입, TP, 시간, 종가 기반 stop/trail, EOD, cooldown, 1·3틱). B 기본 진입 = 신호 bar 다음 1m open 시장가, 모든 포지션 장 마감 전 청산(16:14 open) | 1,000+ 설정을 엔진 규칙 그대로 빠르게 실행 |
| D-029 | 2026-09-30 | 파생 타임프레임(2/3/5/10/15/30/60m): 09:30 기준 세션 고정 bucket, 마지막 분 bar 종료 시 완성(누락 시 다음 가용 bar에서만 인지), 부분 bucket(예: 10m 16:11–16:15)은 신호 없음. 절단(truncation) 인과성 테스트 통과 | 상위 타임프레임 미완성 bar 누설 금지 |
| D-030 | 2026-09-30 | B 이벤트 스터디 규약: 진입가 = 다음 open + 1틱, 목표 체결은 1틱 관통 필요, 같은 bar에서 목표·손절 동시 도달 = 손실, 세션 내 미결 = NaN. EV proxy = P·U − (1−P)(D+1틱) − 왕복 수수료, 시간청산 EV = ret − 2틱 − 수수료 | 보수적 체결, 비용 포함 비교 |
| D-031 | 2026-09-30 | Trap-risk 모델: 정책 무관 recycle 신호(low60 touch + 0.25 ATR 반등) 전체에 1계약 가상 거래(TP +3) 결과 라벨. 연도별 walk-forward(테스트 연도 시작 전에 라벨이 확정된 표본만 학습 = purge). 점수 = 학습 분포 대비 percentile, 모델 없는 기간(2019–2020) = 중립 | 미래 누설 없는 soft filter 입력 |
| D-032 | 2026-09-30 | Dead slot 정의(1차): recycle tranche 나이 ≥ 5 달력일. 민감도: ≥10/20/40일, 거리 기준(진입가 − 종가 ≥ 1 일간 ATR). FRESH < 1일, STALLED 1–5일, active slot = 빈 slot + FRESH | 굵은 단위, 과적합 방지 |
| D-033 | 2026-09-30 | Shadow slot = 실제 book이 slot/예산 부족으로 받지 못한 recycle 신호만 받는 추가 1 slot(실행 안 함, 동일 체결 규칙). Dead slot 경제적 비용 = shadow slot 순손익 / 차단일 | 미실현 손익만으로 dead slot을 평가하지 않음 |
| D-034 | 2026-09-30 | NULL-D 분해: Σ q_{t−1}Δp_t = q̄·ΣΔp(노출 일치 수동 long) + Σ(q_{t−1}−q̄)Δp_t(재고 타이밍); 체결 잔차 = 실제 가격손익 − Σ qΔp; 비용 별도 | FQ 수익의 drift/구조/타이밍 분리 |
| D-035 | 2026-09-30 | A+B 포트폴리오 전역 예산 = 정적 분할(cap_A + size_B ≤ G) → 총 계약이 G를 넘을 수 없음(정확). 재고 상호작용은 결정 bar의 A 재고로 B 크기 조절(인과적) | 동적 공유는 A·B 동시 시뮬레이션 없이는 한도 위반 가능 |
