# T47_00 — NASSI (나씨) SOURCE AUDIT

Written BEFORE any TEST47 economics were computed. Public sources only; no testimonials or third-party profit claims
are used as evidence (the "6,900%" / "500만원 → 31억" figures in press articles are recorded as claims, NOT evidence).

## Source hierarchy

| Tier | Source | What it supports |
|---|---|---|
| A (book structure) | 나씨, 『가상화폐 단타의 정석: 나씨TV 비트코인 단타의 모든 것』, 경향미디어, 2021-09-08 (Yes24 / 교보 / NIA library catalogue TOC) | Chapters 4–8 = five techniques: (1) 5분봉 3틱 룰, (2) 찐바닥 잡기 (기본 규칙; 1분봉으로 바닥을 보는 방법; 매수 금액 결정; 찐바닥 판단 오류 시 대처), (3) 순환매수매도 (개념, 기본 규칙, 원금 감소 원인, 손익 계산, 금액 vs 수량, 반등이 없는 경우 대처), (4) 종목 선택, (5) RSI 활용; chapters 9–12 risk/asset management |
| A (direct statement) | Interview quotes in 위키트리 (wikitree.co.kr/articles/697231) and 매거진동아 video as reported by 인사이트 (insight.co.kr/news/358028) | "가격 상승 후 조정이 오면 과매도 구간을 지나 반등하는 패턴"; "5분봉 기준 3번 이상 연속 하락 → 반등"; "3번째 봉이 끝나고 나서 매수"; "100% 들어맞는 방법은 아니다"; 순환매수매도 = "가격이 하락할 때 물타기 … 추가 매수한 물량이 소폭 반등하면 그만큼만 매도해 평단가를 낮추면서" |
| A (direct statement) | Official Threads account @nassitv_official | "5분봉 3틱은 … 모든 자리에서 다 먹히는 무적의 룰이 아닙니다"; full-seed averaging and not taking profit = main risk |
| B (secondary summary of the book) | velog.io "가상화폐 단타의 정석" reading notes | 3틱 rules 1–5, 찐바닥 cues, 찐바닥 매수량, 오류 대처, 15분봉 usage (quoted below) |
| B (secondary summary) | Threads @junseere summary; wolsalnam.com/172 | 3틱 counting rules; 5m normal / 15m for slow stair-step decline |
| C (not evidence) | community boards (coinpan, fmkorea, dcinside) | only one recurring paraphrase used as a *hypothesis*: "같은 봉에서 물타지 말라" (do not add on the same candle) |

## SOURCE_SUPPORTED_RULE vs TEST47_FORMALIZATION

| # | SOURCE_SUPPORTED_RULE (tier) | TEST47_FORMALIZATION (translation to ES/NQ; predeclared in `out/t47/T47_02_predeclared_spec.json`) |
|---|---|---|
| S1 | 5분봉 is the primary chart; 15분봉 also used (A/B) | Completed 5m RTH bars (09:30–16:10, built from canonical 1m); completed synthetic 15m bars as context/confirmation only |
| S2 | "틱" = one qualifying bearish candle/step, NOT an exchange tick (B) | `MEANINGFUL_DOWN_LEG`; THREE_TICK_MEANS_EXCHANGE_TICKS = NO |
| S3 | 규칙1: 양봉→음봉 전환 봉은 카운트하지 않음 (B) | `nassi_r1`: in IDLE, a leg bar whose previous 5m bar was bullish does not start the count (T1–T3) |
| S4 | 규칙2: 음봉이 이전 봉들의 평균보다 월등히 크면 1틱 (B) | leg size normalised by the causal 5m unit `u5` (mean 5m range of the previous 10 sessions); T1/T2/T3 thresholds in u5 |
| S5 | 규칙3: 이전 음봉 대비 일정 크기 이상 더 내려가야 1틱; 이전 봉 마감보다 높거나 큰 차이 없으면 무시 (B) | small bearish movement is NOT a leg (neutral bar); leg requires close-to-close / body / structural displacement ≥ x·u5; T4 aggregates small steps into one leg |
| S6 | 차트를 무너뜨릴 양봉 → 초기화 (B) | up-bar family KEEP / DECAY / RESET by recovery fraction of the prior leg; full recovery of the pre-sequence close always resets |
| S7 | 횡보 handling: not explicitly specified in tier A/B | SIDEWAYS_KEEP / DECAY / RESET (coarse N ∈ {3, 6} neutral 5m bars) — TEST47 hypothesis |
| S8 | 3틱 완성 후 최초 진입; 초보는 3틱 캔들 마감 후 모양을 보고 또는 4틱 캔들 생성을 보고 진입; 규칙4: 다음 분봉 갱신 후 방향 보고 매수 (A/B) | Entry frontier E1 (at leg-3 close) / E2 (next-bar direction, 1m) / E3 (first bullish 5m) / E4 (1m bottom grammar) / E5 (micro-level reclaim); N-tick frontier 2/3/4 |
| S9 | 3틱룰은 상승 후 조정에서 바닥을 찾는 방법 (B); public cautions about buying right after a large spike (prompt) | Prior-rally context family: large prior 30m rally → (a) no filter, (b) need 4 legs, (c) no trade, (d) 15m confirmation — hypothesis, not assumed |
| S10 | 찐바닥: 캔들 길이가 점점 짧아짐 (매도세 약화); 종가 차이가 거의 없거나 높아짐; 아래꼬리로 마감 (B) | NB: deceleration (leg_k ≤ leg_{k-1}), new-low extension shrink, close improvement, lower-wick ratio — all on completed bars |
| S11 | 1분봉으로 바닥을 보는 방법 (A: TOC) | E4 / NB 1m grammar only AFTER a 5m candidate: lower low → failed extension → bullish 1m close above the pivot bar high |
| S12 | 15분봉: 매수 심리가 죽어 있고 변동성이 없는 장, 가격이 천천히 흐르는 장 (B) | 15m context: low-vol / slow sequences → require 15m leg structure; 15m bullish confirmation variant |
| S13 | 찐바닥 매수량: 평소보다 최소 2배 (B); 오류 시 매수 수량만큼 빠르게 손절 후 재진입 (B) | Inventory capped at 2 contracts; NB may take 2 only via NR-A structural second buy (no 2-lot initial entry beyond cap); error handling = stop variants in exit family |
| S14 | 규칙5: 1차 매수 후 규칙3 조건의 음봉(새 의미 있는 하락)이 나오면 2차 매수 (B); 같은 봉에서 물타지 말 것 (C) | NR-A confirmed second buy = new complete meaningful leg + new bottom confirmation, never on the same 5m bar |
| S15 | 순환매수매도: 추가 매수 물량이 소폭 반등하면 그만큼만 매도 (A) | NR-C trim: when q=2 and close ≥ lot-2 entry + trim·u5 → sell 1; NR-D rebuild to 2 on a new validated lower bottom (bounded: ≤ 2 rebuilds / campaign) |
| S16 | 반등이 없는 경우 대처 / 원금 감소 원인 (A: TOC; content not public) | Not reconstructable → not assumed; tested only through bounded caps, stops and the blind-DCA control |
| S17 | RSI/MACD combos (B, secondary) | EXCLUDED by the TEST47 prompt (§1, §60): RSI / static oversold are prior failed families |
| S18 | Crypto 24h market, altcoin volatility, absolute thresholds | NOT transferred; all thresholds volatility-normalised; ES/NQ RTH only, flat-or-locked overnight |

## Evidence limits
* The book's full chapter text is not publicly available; tier-B notes are a reader's summary. Every rule above not
  marked A is treated as a *formalisation hypothesis*.
* No source provides numeric thresholds transferable to ES/NQ; all thresholds are TEST47 predeclared round values.
* NASSI_SOURCE_AUDIT_COMPLETE = YES (with the limits stated).

Sources: https://m.yes24.com/Goods/Detail/103505075 · https://product.kyobobook.co.kr/detail/S000001016436 ·
https://www.wikitree.co.kr/articles/697231 · https://www.insight.co.kr/news/358028 ·
https://www.threads.com/@nassitv_official/post/DDZfayCTJgz · https://velog.io/@dev_/가상화폐-단타의-정석 ·
https://www.threads.com/@junseere/post/DIDqYcIPBp8 · https://www.wolsalnam.com/172 · https://www.fmkorea.com/3739055002
