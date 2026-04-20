# Daily AI Card News — 자동화 파이프라인 설계 (v0.2)

> 작성일: 2026-04-20 · 최종수정: 2026-04-20
> 연관 inbox: 2026-04-20 "클로드 코워크+클로드 크롬으로 AI 카톡 뉴스 자동화"
> 연관 스킬: 본 폴더의 `SKILL.md` (텍스트 → JSON → HTML 카드뉴스 변환기)

## 변경 이력

- **v0.1** (2026-04-20 초안) — Chrome+Cowork 구성 가정
- **v0.2** (2026-04-20 당일 수정) — **Chrome 제거** (사내 보안으로 확장 매일 삭제). **소스 AI타임스 단독**. **로컬 Python 수집 + Cowork 가공** 역할분리 도입.

---

## 1. 목적

매일 아침 AI타임스의 주요 뉴스를 카드뉴스(HTML → PNG)로 뽑아서
사내 메신저/메일로 공유하는 **반자동 파이프라인** 구축.

기존 `daily-card-news/SKILL.md` 는 "텍스트 → 카드뉴스" 만 담당.
이 문서는 그 앞단(수집)과 뒷단(공유·백업)을 붙여 한 바퀴를 완성한다.

---

## 2. 환경 제약 (설계 전제)

이 프로젝트가 처음부터 안고 있어야 할 제약 3가지:

| 제약 | 영향 | 대응 |
|---|---|---|
| Claude in Chrome 확장이 **매일 삭제됨** | 브라우저 자동화 불가 | Chrome MCP 배제. 로컬 Python으로 대체 |
| Cowork egress 프록시가 **AI타임스 차단** | Cowork 내 직접 크롤링 불가 | 로컬 Python이 수집, Cowork는 가공만 |
| `.html` / `.png` / `.zip` 등 **매일 삭제** | 결과물 영속성 불가 | 영속 `.json` / `.md` 소스 + 재생성 스크립트 |

---

## 3. 큰 그림 (역할 분리)

```
┌──────────────── 사용자 로컬 PC (Windows) ────────────────┐
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │ Step 1. AI타임스 수집                 │  Python         │
│  │  - RSS 우선 (/rss/allArticle.xml)     │  requests +    │
│  │  - 실패 시 HTML 스크래핑 폴백         │  beautifulsoup │
│  │  - 오늘 기사 12~20개 덤프             │                │
│  └──────────────┬───────────────────────┘                │
│                 ▼                                        │
│  ┌──────────────────────────────────────┐                │
│  │ 결과물/scraps/YYYY-MM-DD-raw.json    │  영속 (.json)   │
│  │   [{title, url, lead, published_at}] │                │
│  └──────────────┬───────────────────────┘                │
└─────────────────┼────────────────────────────────────────┘
                  │
                  ▼ (같은 폴더, Cowork가 읽음)
┌──────────────── Cowork ──────────────────────────────────┐
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │ Step 2. 선별·요약·태깅                │  LLM           │
│  │  - 5~8개 선정 (전력·공공·실무 가중치)  │                │
│  │  - 15자 제목 / 2~3줄 body / 태그 1~3  │                │
│  └──────────────┬───────────────────────┘                │
│                 ▼                                        │
│  ┌──────────────────────────────────────┐                │
│  │ 결과물/scraps/YYYY-MM-DD.json (카드용) │ 영속 (.json)  │
│  │ 결과물/scraps/YYYY-MM-DD.md (요약기)  │ 영속 (.md)    │
│  └──────────────┬───────────────────────┘                │
│                 ▼                                        │
│  ┌──────────────────────────────────────┐                │
│  │ Step 3. generate_cards.py 실행        │                │
│  │ → 결과물/cardnews/YYYY-MM-DD.html    │  휘발성         │
│  └──────────────┬───────────────────────┘                │
└─────────────────┼────────────────────────────────────────┘
                  ▼
┌──────────────── 사용자 수동 ─────────────────────────────┐
│  Step 4. 브라우저로 HTML 열기                            │
│  Step 5. "PNG로 저장" 버튼 → 카드별 PNG 다운로드         │
│  Step 6. 카톡/메일에 첨부해 공유                         │
└──────────────────────────────────────────────────────────┘
```

**Cowork가 할 수 있는 것 / 못 하는 것 명확화**:
- ✅ 할 수 있음: JSON 읽기, 선별·요약, Python 스크립트 실행(로컬 실행 아닌 샌드박스 내 실행이라 한계 있으나 `generate_cards.py` 는 독립 실행 가능), 문서 갱신, 메모리 저장
- ❌ 할 수 없음: AI타임스 직접 HTTP 요청, Chrome 열어 크롤링, PNG 다운로드(브라우저 렌더가 필요해서)

---

## 4. 단계별 상세

### Step 1. AI타임스 수집 (로컬 Python)

**스크립트**: `scripts/collect_aitimes.py` (본 커밋에서 생성)

**로직**
1. RSS 1차 시도: `https://www.aitimes.com/rss/allArticle.xml`
2. 실패 시 RSS 2차 시도: `https://www.aitimes.com/rss/S1N1.xml` (섹션 메인)
3. 모두 실패 시 HTML 목록 페이지 스크래핑 폴백: `https://www.aitimes.com/news/articleList.html`
4. 각 아이템에서 `title`, `url`, `lead`(요약/첫 문단), `published_at` 추출
5. **오늘자**만 필터링 (날짜 기준)
6. `결과물/scraps/YYYY-MM-DD-raw.json` 으로 저장

**의존성**: `requests`, `feedparser`, `beautifulsoup4` (모두 pip 일반 패키지)
**실행**: `python scripts/collect_aitimes.py` (인자 없이, 당일 기준)
**재현**: `python scripts/collect_aitimes.py --date 2026-04-19` (날짜 지정 과거분 수집)

### Step 2. 선별·요약 (Cowork)

Cowork 대화에서 사용자가 `YYYY-MM-DD-raw.json` 을 보여주면,
Claude가 다음 기준으로 선별:

**선정 기준 (우선순위)**
1. 모델/오픈소스 릴리즈
2. 산업·공공 도입 사례 (전력·에너지·공공부문이면 가점)
3. 규제·표준 (EU AI Act, 국내 AI 기본법 등)
4. 기술 동향 (RAG, 에이전트, 온디바이스, 안전·정렬 등)
5. 스타트업/빅테크 동향

**출력 — 카드별**
```json
{
  "type": "news",
  "number": 1,
  "title": "15자 이내",
  "body": "2~3줄, 마침표로 끝",
  "tags": ["태그1", "태그2"],
  "source_url": "https://www.aitimes.com/..."
}
```

**출력 — 파일 2개**
- `결과물/scraps/YYYY-MM-DD.json` — `generate_cards.py` 바로 투입용
- `결과물/scraps/YYYY-MM-DD.md` — 사람용 요약 (선정 이유 + 원문 링크, 검색·복기용)

### Step 3. HTML 카드뉴스 생성

```bash
python scripts/generate_cards.py \
  --input 결과물/scraps/2026-04-20.json \
  --output 결과물/cardnews/2026-04-20.html \
  --theme modern-light
```

### Step 4~6. 수동

- 브라우저로 HTML 열기 → 내장 "PNG로 저장" 버튼
- 카톡/메일 공유

---

## 5. 파일 구조 (영속성 정책)

CLAUDE.md의 **영속 소스 + 휘발성 뷰 + 재생성 스크립트** 3박자 적용:

```
daily-card-news/
├── SKILL.md                        ← 영속 (스킬 정의)
├── PIPELINE.md                     ← 영속 (이 문서)
├── scripts/
│   ├── generate_cards.py           ← 영속 (카드 생성기)
│   ├── collect_aitimes.py          ← 영속 (NEW · 수집 스크립트)
│   └── regen_today.bat             ← TODO (원클릭 재생성)
└── 결과물/
    ├── scraps/
    │   ├── YYYY-MM-DD-raw.json     ← 영속 (수집 원본)
    │   ├── YYYY-MM-DD.json         ← 영속 (카드 소스)
    │   └── YYYY-MM-DD.md           ← 영속 (사람용 요약)
    └── cardnews/
        ├── YYYY-MM-DD.html         ← 휘발성 (매일 삭제)
        └── YYYY-MM-DD/*.png        ← 휘발성 (매일 삭제)
```

**보존 규칙**: `scraps/` 30일 보관, 분기별 `archives/` 이동 검토.

---

## 6. 자동화 레벨 (현재 L1, 목표 L2)

| 레벨 | 설명 | 현재 상태 |
|---|---|---|
| L0 | 매번 수동 ("뉴스 검색 → 정리 → 카드 만들기"를 맨바닥부터) | — |
| **L1** | **로컬 수집 스크립트 + Cowork 대화로 가공** | ← 목표 (v0.2) |
| L2 | L1 + 매일 08:30 자동 수집 (Windows 작업 스케줄러로 `collect_aitimes.py` 예약) | 다음 단계 |
| L3 | L2 + Cowork scheduled-tasks 가 알림 + 반자동 선별 초안 | 연구 필요 |
| L4 | 완전 무인 (선별까지 LLM이 기준 파일 보고 혼자 처리) | 장기 |

---

## 7. Open Questions (v0.2 재조정)

| ID | 질문 | 현 상태 |
|---|---|---|
| Q1 | AI타임스 RSS 실제 URL? | 로컬에서 실행 시 확정. 후보 2개 스크립트에 반영 |
| Q2 | 카드 수 고정 (7장) vs 범위 (5~8) ? | **7장 고정** 권장 (운영 단순) |
| Q3 | 테마 `modern-light` 고정? | **고정** (v0.2) — 다양성은 2주 후 검토 |
| Q4 | 카드뉴스 총 카드 순서 규칙 (시간순? 중요도순?) | **중요도순** (선정 기준 1→5) 권장 |
| Q5 | 전력·에너지 가점 — 구체 키워드는? | 별도 TBD. 잠정: "한전", "전력", "에너지", "그리드", "스마트팩토리" |
| Q6 | 주말/공휴일 | **월~금만 생성** 권장 |
| Q7 | `결과물/scraps/YYYY-MM-DD.md` 요약기 서식? | 별도 TBD (Step 2의 산출물) |

---

## 8. 재생성 절차 (휘발성 파일 복구)

`.html`/`.png` 이 내일 사라져도 `.json` 이 살아있다면:

```bash
cd daily-card-news
python scripts/generate_cards.py \
  --input 결과물/scraps/2026-04-19.json \
  --output 결과물/cardnews/2026-04-19.html \
  --theme modern-light
```

`결과물/scraps/*-raw.json` 으로는 수집 단계부터 재현 가능 (같은 데이터로 다른 선별 시도).

---

## 9. 다음 액션 (D0 ~)

- [x] **D0-1** Cowork 환경 제약 확인 (Chrome 불가, AI타임스 egress 차단)
- [x] **D0-2** 설계 문서 v0.2 확정 (이 문서)
- [ ] **D0-3** `scripts/collect_aitimes.py` 작성 (본 커밋)
- [ ] **D1-1** 사용자가 로컬 PC에서 `collect_aitimes.py` 실행 → RSS 경로 실제 확정
- [ ] **D1-2** 생성된 `YYYY-MM-DD-raw.json` 을 Cowork 에 공유 → 선별·요약·카드 생성 1회 시범
- [ ] **D2** 1주일 수동 운영 → 선정 기준·서식 안정화
- [ ] **D3** Windows 작업 스케줄러에 `collect_aitimes.py` 예약 (08:00) → L2 진입
- [ ] **D4** `regen_today.bat` 작성

---

## 10. 변경 이력

- **2026-04-20** · v0.1 · 초안 작성 (Chrome+Cowork 구성 가정)
- **2026-04-20** · v0.2 · Chrome 제거, AI타임스 단독, 로컬·Cowork 역할분리 도입
