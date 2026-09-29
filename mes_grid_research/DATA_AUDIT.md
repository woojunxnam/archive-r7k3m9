# DATA_AUDIT — canonical ES 1m (Massive Futures)

감사일: 2026-09-29 · 스크립트: `scripts/restore_from_mcp_dump.py`, `scripts/data_audit.py` · 원본 결과: `results/data_audit.json`

## 1. 복원 (Reconstruction)

| 항목 | 기대값 | 실측 | 결과 |
|---|---|---|---|
| Drive 폴더 | `1Y8NnJzxTwaeisvpsD5tLMoJrVc-56O6Z` | part000~part038 + `CANONICAL_1M_ES_CHUNKS_MANIFEST.json` + `README.md` | OK |
| chunk 수 | 39 | 39 | OK |
| chunk별 bytes/SHA256 (manifest 대조) | 38×1,000,000 + 881,868 | 39/39 일치 | OK |
| 결합 순서 | lexical part000→038 | 동일 | OK |
| 최종 bytes | 38,881,868 | 38,881,868 | OK |
| 최종 SHA256 | `2b4f41b1…c454116` | `2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116` | OK |
| rows | 2,486,058 | 2,486,058 | OK |
| 첫 timestamp | 2019-05-05 18:01:00 | 2019-05-05 18:01:00 | OK |
| 마지막 timestamp | 2026-05-27 17:00:00 | 2026-05-27 17:00:00 | OK |

- 다운로드 경로: Drive 파일이 비공개라 직접 HTTP 다운로드 불가 → Google Drive MCP `download_file_content`(base64)로 받아 디코드.
- 원본(Drive)은 수정하지 않았음. 복원 파일은 `data/canonical/canonical_1m_ES.parquet` (git 미포함, `.gitignore`).

## 2. Schema

| 컬럼 | 타입 | 의미(추정 포함) |
|---|---|---|
| `dt` | datetime64[ns], naive | **bar END** 시각, America/New_York 벽시계 |
| `session_date` | datetime64 | Globex 세션 날짜 (18:00 전일 → 17:00). 휴일은 다음 세션에 병합되는 경우 있음 |
| `o,h,l,c` | float64 | **forward additive back-adjusted** 연속가격 (아래 §4) |
| `v` | int64 | 거래량 (해당 계약) |
| `contract` | str | 실제 계약 (ESM9 … ESM6, 29개) |
| `cum_adjustment` | float64 | 누적 조정값. **raw = adj − cum_adjustment**. 계약 내 상수 |
| `session_date_plus6h` | datetime64 | dt+6h의 날짜 (휴일 병합 차이로 51,546행에서 session_date와 다름 — 정보용) |
| `cal_date` | datetime64 | 달력 날짜 |
| `roll_adjacent` | bool | roll 인접 구간 플래그 (38,439행) |

## 3. 무결성 점검

| 점검 | 결과 |
|---|---|
| 중복 timestamp | 0 |
| 단조 증가 | True |
| NULL | 전 컬럼 0 |
| OHLC 위반 (h<max(o,c), l>min(o,c), h<l) | 0 / 0 / 0 |
| tick grid(0.25) 이탈 | 0 (o,h,l,c 모두) |
| volume 0 또는 음수 | 0 / 0 |
| 초 단위 ≠ 0 | 0 |
| 17:00–18:00 휴장 구간 bar | 0 |
| 세션 시작 bar | 18:01 = 1,776/1,780 세션 (bar-end 의미와 일치) |
| 세션 종료 bar | 17:00 = 1,755; 13:15(조기폐장) 15; 기타 휴일 |

### 세션 내부 gap
- 총 2,082건 / 29,282분 누락. 대부분 (a) 야간 무거래 1–2분 gap, (b) 2021년 이전 CME 16:15–16:30 일일 halt (16분 gap 537건), (c) 휴일 조기폐장.
- **거래창(bar-end 09:31–16:15, 405 bar/일) 기준**: 1,820 거래일 중 1,723일 완전.
  - 거래소 휴일(NYSE 휴장, Globex 13:00 조기종료) 47일: 209–210 bar. → baseline에서 **신규 거래 금지일**로 처리 (DECISIONS D-004).
  - 조기폐장(7/3, 추수감사절 다음날, 12/24) 15일: 225 bar (13:15 종료). 정상 거래일로 처리.
  - 기타 35일: provider 결측 (예: 2020-01-30 12:00→14:01, 2021-04-22 10:00→12:01 등 정시 경계 1–2시간 블록) 및 2020-03 limit-down halt (2020-03-09/12/16/18의 14–15분 halt는 **실제 시장 이벤트**). 총 결측 약 1,528분(거래창 전체의 약 0.2%).
  - 처리: 결측 bar는 합성하지 않음. 결측 구간 동안 체결 불가. 결측 후 첫 bar open에서 gap 처리 (EXECUTION_SPEC §6).

### DST
- 데이터는 naive 뉴욕 벽시계. DST 전환일 16개(2019-03-11 … 2026-11-02 기준 목록) 전후로 세션 시작 18:01 일관.
- RTH 개장 거래량 spike 검증: 09:31 bar 거래량 / 09:30 bar 거래량 중앙값 = DST 기간 5.22×, 표준시 5.06×; 전체 세션 88.6%에서 >3×. → 개장 spike가 연중 09:31 bar-end에 정확히 위치 → **DST 정렬 정상, UTC 오변환 흔적 없음.**
- 일요일 02:00 전환 시각은 Globex 휴장 시간대 → 중복/구멍 영향 없음.

### Suspicious jumps
- 세션 내부 open-vs-prev-close >10pt: 23건. 상위는 2020-03 (limit-down halt 재개, Fed 긴급인하 2020-03-03 10:01 +68pt bar 등), 2022-09-21 FOMC. 모두 실제 이벤트와 정합.
- 1분 range >30pt: 265건. 최대 2025-04-09 13:20 (171pt, 관세 유예 발표), 2022 CPI 발표일 08:31 등. 실제 이벤트.
- 판단: 데이터 오류로 볼 만한 jump 없음.

## 4. 연속선물 조정 방식 (매우 중요)

- `cum_adjustment`는 계약 내 상수, roll마다 변경. **첫 계약 ESM9 = 0 기준 forward additive(Panama) 조정.**
- 검증: raw = adj − cum_adjustment → 2020-03 최저 raw 2,174.0 (실제 ES 2020-03-23 저점 ≈ 2,174와 일치); 최종 raw 7,554.25; 최초 raw 2,908.25.
- roll 28회, 모두 17:00 → 18:01 (거래창 밖). adjusted 시리즈의 roll 전후 jump는 −12.75~+17.25pt(대부분 ±2pt 이내)로 연속; **raw 시리즈는 roll마다 −11~+74pt 점프** (2023년 이후 금리로 인한 contango: +44~+74pt).
- 함의:
  1. 포인트 차이(grid 간격, TP 거리, 평단 대비 P&L)는 adjusted 시리즈에서 경제적으로 올바름 (roll 시 spread 가격으로 롤오버한 것과 동등, roll 비용은 별도 부과 — EXECUTION_SPEC §8).
  2. **절대 가격 수준**(notional, margin)은 raw 가격으로 계산해야 함 (2026년 adjusted는 raw보다 ≈696pt 낮음).
  3. TradingView `ES1!`/`MES1!` 기본 연속차트는 back-adjust OFF(unadjusted)가 기본값. 이 경우 **롱 포지션이 roll을 넘길 때마다 가짜 +45~74pt 이익**이 생겨 Basket +25가 roll 한 번에 체결될 수 있음 → TV 결과가 낙관적이었을 가능성의 주요 후보 (latest_report의 parity 감사 참조).

## 5. ES vs MES

- 이 데이터는 ES. 전략 로직은 ES 가격으로 연구하고 P&L은 MES $5/pt로 계산.
- ES 체결/유동성/스프레드는 MES와 다름. **ES 1m 백테스트는 MES 실거래 체결 품질을 증명하지 않음.** 최종 후보는 MES 데이터로 재검증 필요 (현재 Drive에 MES 데이터 미확인).

## 6. 결론

데이터 무결성(bytes/hash/rows/범위/schema/중복/단조/OHLC/tick/DST) 모두 통과. 연구에 사용 가능.
주의 사항: (1) adjusted 가격 → notional은 raw 사용, (2) 휴일 47일 신규거래 금지, (3) provider 결측 ~1,528분은 합성하지 않음, (4) ES≠MES.
