# PROJECT_STATE — MES Smart Recycling Grid Research

최종 갱신: 2026-09-29 · 이 파일이 authoritative state다. 대화 기억보다 이 파일과 아래 경로를 우선한다.

## 현재 단계
| Phase | 상태 | 산출물 |
|---|---|---|
| 1 Data audit | **완료 (PASS)** | `DATA_AUDIT.md`, `results/data_audit.json` |
| 2 Execution engine + tests | **완료** (35 tests pass) | `EXECUTION_SPEC.md` (EXEC-1.0), `src/mesgrid/`, `tests/` |
| 3 Python baseline | **완료** | `results/BASE_A_001/` |
| 4 TradingView parity audit | **부분 완료** (Pine 원문 필요) | `results/PARITY_001/parity_matrix.csv` |
| 5 Core/Recycle 구조 | **진행 중** — CR_001(R1) 기각 | `results/CR_001/` |
| 6+ | 미착수 | |

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
```

## Lineage (모든 결과 공통)
- dataset: `canonical_1m_ES.parquet`, SHA256 `2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116`, 2019-05-05 18:01 ~ 2026-05-27 17:00
- engine `0.1.0`, execution spec `EXEC-1.0` (conservative)
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

## 열린 이슈 / blocker
- (비차단) TV parity 완결: Pine V2.2 원문, TV 차트 타임프레임, 테스트 시작일, back-adjust 설정, bar magnifier, 수수료/slippage 설정 필요.
- (비차단) MES 1m 데이터 미확보 → Phase 9 전 필요. `Massive` MCP 서버 인증 시 조회 가능성.
- 전 결과는 full-period in-sample. walk-forward는 Phase 8.
