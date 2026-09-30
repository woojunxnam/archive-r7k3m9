# PROJECT_STATE — MES Smart Recycling Grid Research

최종 갱신: 2026-09-30 (RUN-4: ES long-only 멀티알파 공장 — Sleeve A FQ + Sleeve B 모멘텀, 약 2,500개 설정) · 이 파일이 authoritative state다. 대화 기억보다 이 파일과 아래 경로를 우선한다.

## 현재 단계
| Phase | 상태 | 산출물 |
|---|---|---|
| 1 Data audit | 완료 (PASS) | `DATA_AUDIT.md` |
| 2 Engine + tests | 완료 — engine 0.2.0 + audit mode + RUN-4 모듈(기본 OFF, RUN-3 재현 동일), **160 tests pass** | `EXECUTION_SPEC.md` (EXEC-1.1 + ROLL-1.0) |
| 0' Roll gate | **완료 (PASS)** | `results/ROLL_GATE_001/` |
| 3 Baseline | 완료 | `results/BASE_A_001/` |
| 4 TV parity | 부분 완료 (Pine 원문 필요) | `results/PARITY_001/` |
| 5–7 Research factory (S1 screen → S3 robustness → S4/S4b interactions → S5 temporal/WF → S6 exec stress → Pareto) | **1차 완료** | `MODULE_LEADERBOARD.csv`, `PARETO_CANDIDATES.csv`, `IDEA_BACKLOG.md`, `results/FACTORY_*` |
| 8 Walk-forward | 부분 (4개 가족) | `results/FACTORY_S5/walkforward.csv` |
| R3-0 FQ 회계 감사 | **PASS** | `results/RUN3_P0_AUDIT/` |
| R3-1 Roll 정산 | **PASS** | `results/RUN3_P1_ROLL/` |
| R3-2 자본 frontier | 완료 (활동 vs 깊이 충돌) | `results/RUN3_P2_FRONTIER/` |
| R3-3 체결 민감도 | 완료 | `results/RUN3_P3_EXEC/` |
| R3-4/5 layer exit · tail 정책 · smart recycle | 완료 (103 configs) | `results/RUN3_P45/summary.csv`, `SMART_BOTTOM_PARETO.csv` |
| R3 Bottom event study | 완료 (edge 없음) | `BOTTOM_EVENT_STUDY.csv`, `results/RUN3_BOTTOM/` |
| R3-6 외부 검증 | **진짜 OOS 미수행** (데이터 없음). YM 동기간 cross-market만 | `results/RUN3_P6_YM*/` |
| R3-7 결선 Pareto | 완료 (14 후보 × slip 1/2/3) | `PARETO_RUN3.csv`, `results/RUN3_FINAL/` (bootstrap, safe_scaling, regime_removal) |
| R4 Sleeve A (FQ) 공장 | 완료: S1 376 + STATIC/prof_be 48 + soft 59 + S2/S3/S5 강건성 201 | `SLEEVE_A_RESULTS.csv`, `PARETO_A.csv`, `results/RUN4_OVERNIGHT/a_tables/` |
| R4 Sleeve B (모멘텀) 공장 | 완료: 이벤트 스터디 167 + 1,708 설정(S1–S6, null, 스트레스) | `SLEEVE_B_EVENTS.parquet`, `SLEEVE_B_RESULTS.csv`, `PARETO_B.csv` |
| R4 A+B 포트폴리오 | 완료: 고유 152개(전역 예산 G 10–24) | `AB_PORTFOLIO_RESULTS.csv`, `PARETO_AB.csv`, `WEEKLY_ANALYSIS.csv`, `BOOTSTRAP_SUMMARY.csv` |
| 9 MES 검증 | 미착수 (데이터 없음) | frozen: `FROZEN_CANDIDATES.json`, `FROZEN_POSTHOC_FILTERS.json` |

## 재현 방법
```bash
cd mes_grid_research
pip install pandas pyarrow numpy pytest
# 1) Drive MCP로 39 part + manifest를 받은 dump 폴더를 지정해 복원 (DATA_AUDIT §1)
python3 scripts/restore_from_mcp_dump.py <dump_dir>   # → data/canonical/canonical_1m_ES.parquet (SHA 검증)
python3 scripts/data_audit.py
python3 -m pytest -q tests
python3 scripts/run_baseline_a.py        # BASE_A_001
python3 scripts/parity_audit.py          # PARITY_001
python3 scripts/run_cr001.py             # CR_001
python3 scripts/roll_gate.py             # ROLL_GATE_001
python3 scripts/stage1.py FACTORY_S1v2   # 202 configs (~35 min, 4 cores)
python3 scripts/stage3.py FACTORY_S3v2; python3 scripts/stage4.py FACTORY_S4v2
python3 scripts/stage4b.py; python3 scripts/stage3b.py; python3 scripts/walkforward.py
python3 scripts/stage56.py s5; python3 scripts/stage56.py s6   # finalists from results/FINALISTS.json
python3 scripts/leaderboard.py FACTORY_S1v2 FACTORY_S4v2 FACTORY_S4b FACTORY_S3v2 FACTORY_S3b
# RUN-3 (메모리: worker 2개 권장 — 4개는 컨테이너 재시작 유발)
python3 scripts/fq_audit.py; python3 scripts/roll_recon.py
python3 scripts/run3_p2.py; python3 scripts/run3_p3.py; python3 scripts/run3_p45.py
python3 scripts/event_study.py; python3 scripts/bottom_score.py; python3 scripts/failure_diag.py
python3 scripts/cross_market_ym.py          # 외부 데이터 data/external/canonical_1m_YM.parquet 필요
EXTRA_FINALISTS='{...}' PROCS=2 python3 scripts/run3_final.py   # RUN3_FINALISTS.json에 최종 목록 기록
python3 scripts/scaling_bootstrap.py RUN3_FINAL; python3 scripts/run3_pareto.py
# RUN-4 (numba, psutil 필요: pip install numba psutil). 매니페스트/상태 기반 재개 가능 — 완료 config는 건너뜀
python3 scripts/run4_verify.py                        # 엔진 재현 + 감사
python3 scripts/run4_b_events.py                      # B 이벤트 + 스터디 (data/cache/r4_b_events.npz)
python3 scripts/run4_trap.py                          # trap-risk walk-forward 점수 (data/cache/r4_trap_scores.npz)
python3 scripts/run4_a.py wave1 3; python3 scripts/run4_a.py wave1b 1; python3 scripts/run4_a.py wave1c 1; python3 scripts/run4_a.py wave2 1
python3 scripts/run4_a.py wave3 3                     # 생존 후보 자동 선별 + S2/S3/S5
for s in s1 s2 s3 s4 s6 s6n; do python3 scripts/run4_b.py $s; done
python3 scripts/run4_port.py series results/RUN4_OVERNIGHT/mech_SALVpts10.json 1; python3 scripts/run4_port.py series results/RUN4_OVERNIGHT/mech_PASSIVE.json 1
python3 scripts/run4_fill_mech.py results/RUN4_OVERNIGHT/mech_SALVpts10.json; python3 scripts/run4_fill_mech.py results/RUN4_OVERNIGHT/mech_PASSIVE.json
python3 scripts/run4_port.py ab results/RUN4_OVERNIGHT/mech_SALVpts10.json; python3 scripts/run4_port.py ab results/RUN4_OVERNIGHT/mech_PASSIVE.json
python3 scripts/run4_analyze.py; python3 scripts/run4_a_report.py; python3 scripts/run4_final.py results/RUN4_OVERNIGHT/finals.json; python3 scripts/run4_md_tables.py
```

## Lineage (모든 결과 공통)
- dataset: `canonical_1m_ES.parquet`, SHA256 `2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116`, 2019-05-05 18:01 ~ 2026-05-27 17:00
- engine `0.2.0`, execution spec `EXEC-1.1` (conservative), roll model `ROLL-1.0` (이전 0.1.0 결과는 동일 재현 확인)
- 세션: bar-end 09:31–16:15 ET (open 09:30–16:14), 거래소 휴일 47일 신규거래 금지
- 비용: $0.62/ct/side, market 1 tick, limit 1 tick 관통, roll $2.49/ct
- 각 결과 폴더의 `metrics.json` → `lineage` 필드에 파라미터·git hash 기록

## 현재까지의 핵심 사실
1. 데이터 무결성 통과. 가격은 forward additive adjusted (raw = adj − cum_adjustment).
2. **Baseline A (Basket +25 / grid 5 / max 32)** — 2019-05 ~ 2026-05:
   - realized +$479.7k, 종료 미실현 +$560 (4계약 open), 514 사이클 전부 이익.
   - **Max MTM DD −$204.9k** (2025-02-21 → 2025-04-06), 최악 사이클 MTM −$198.2k, **최소 equity $16.8k (2020-03-22)** — $150k 계좌 기준 사실상 파산 수준.
   - 32계약 lock: **2022-04-11 → 2023-12-18 (616일)**, 2020-02-26 → 07-20 (145일), 2025-02-25 → 06-26 (121일). RTH 시간의 42%가 32계약.
   - realized DD −$578 / PF 5.5 / 사이클 승률 100% — closed-trade 통계가 위험을 완전히 숨김.
3. **Parity**: 2025 lock(119–121일)과 최악 사이클(−$190k~−$198k)은 가격기준·체결모델·시작일과 무관하게 재현 → TV에서 본 실패는 실재. TV 수치(306 basket / 2,444 entry / $344.7k)와 정확히 일치하는 변형은 없음 → Pine V2.2 add/entry 규칙과 TV 테스트 기간이 필요.
4. **CR_001 (R1 profit-only recycle)**: 기각. MTM DD 개선 없음(−$201k~−$214k), 최장 32-lock 오히려 증가(660–757일). recycle lane도 추세 하락에서 함께 잠김. 순이익 증가는 노출 증가 때문.

5. **ROLL_GATE_001 PASS**: 계약별 raw 원장(tranche ID 유지) 적용 시 Baseline A가 센트 단위 동일. naive 비조정 연속가는 +$23.8k 가짜 이익.
6. **Research factory (unique 372 configs, 총 실행 ~570회)**: DD를 줄이는 대부분의 모듈(노출 상한, state machine, 회복모드, governor, 느린 core)은 **2022-01~2024-02 약 750일 무진입** → lock을 없앤 것이 아니라 크기만 줄임.
   capacity와 DD를 동시에 개선한 유일한 강건 계열 = **FQ (항상 활성 floating recycle low60 + 회복모드 layer exit)**: 무진입 5.8일, DD −$116k~−$130k, 최소 equity ~$100k, 인접값 28개 모두 안정.
7. 해결 안 된 위험: fresh start 2022-01에서 FQ도 최소 equity ~$28k; 2022 underwater ~708일; FQ DD가 slippage에 민감.

8. **RUN-3 (2026-09-30)** — 모든 결과는 "ES-signal / MES-economics proxy backtest", in-sample:
   - FQ 회계 PASS (713,842 bar × 3, 오차 ~5e-8). roll 비용 $2.49/ct, 총손익의 ~0.3%.
   - 한도 frontier: 활동 유지(무진입 ≤10일)에는 recycle 슬롯 ≥16(총 32) 필요 → 최악 fresh 최소 equity $22–35k. cap 10–14는 fresh $76–97k지만 454–618일 무진입.
   - 체결: 손익은 2–4틱에서 −5~−12%로 유지, C32 fresh 깊이는 2–3틱에서 $10k/$1.5k로 붕괴. limit_close 진입이 완화.
   - Bottom 예측 edge 없음(AUC 0.50–0.51). layer exit는 all-profit harvest만 깊이 개선(손익 −40%). DD pause 계열은 무효과 또는 거래 중단.
   - Recycle 진입 필터(bs70, rpos60)는 깊이 개선 + 짧은 무진입이지만 recycle 활동이 거의 소멸(core 중심 구조).
   - 목표 "활동 유지 + 깊이 대폭 감소"는 미달성. FQ는 live-ready 아님.

9. **RUN-4 (2026-09-30)** — 모두 in-sample, "ES-signal / MES-economics proxy":
   - FQ recycle 타이밍은 무작위 타이밍(NULL-C 30 seed)·dumb recycle(NULL-B)을 이기지 못함 → alpha 아님(D-036).
   - FQ 손익 ≈ 평균 재고 × ES drift. 같은 평균 노출 수동 long 대비 DD·fresh가 더 좋은 A 설정 0개(D-037).
   - 적은 계약 활동 유지는 rebound salvage / prof_be로 달성(12–16계약, 무진입 5–8일, fresh 2022 $96–100k) — 효과는 탈위험(D-038).
   - Dead slot 기회비용 작음(shadow slot 연 $15–980, D-039).
   - Sleeve B 고회전 long 모멘텀 실패(비용 전 음(−)), B7F만 약한 생존(D-040).
   - A+B: 주 평균 $280–490(16계약), 주 $4k까지 8–14배. 스케일링 정당화 안 됨.

## 열린 이슈 / blocker
- (비차단) TV parity 완결: Pine V2.2 원문, TV 차트 타임프레임, 테스트 시작일, back-adjust 설정, bar magnifier, 수수료/slippage 설정 필요.
- (**차단: 진짜 OOS**) 2026-05-28 이후 ES 1m 또는 MES 1m 데이터 미확보. frozen 후보는 준비됨.
- 전 결과는 full-period in-sample. walk-forward는 Phase 8.
