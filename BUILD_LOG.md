# Daily Card News — 구축 로그

> 파이프라인이 단계별로 어떻게 짜여가고 있는지 누적 기록하는 파일입니다.
> 며칠 뒤에 "내가 지금 어디쯤 왔지?" 싶을 때 이 파일부터 읽으면 맥락 복원 가능.
>
> 각 항목 구조: **무엇 / 왜 / 결과 / 다음**

---

## 🗺️ 구현 단위 로드맵 (C1 ~ C6)

| 단위 | 내용 | 주체 | 상태 |
|---|---|---|---|
| D0 | 설계 · 환경제약 확인 · 스크립트 v1 작성 | Cowork | ✅ |
| C1 | 로컬에서 `collect_aitimes.py` v1 실행 | 사용자 PC | ✅ |
| C2 v1 | RSS 최신순 기반 선별 (baseline, v1 파일로 보존) | Cowork | ✅ |
| **D0-5** | **소스 피벗: RSS 최신순 → Most Popular + 에너지 섹션. 스크립트 v2 확장** | **Cowork** | ✅ |
| C1' 시도 #1 | 스크립트 v2 재실행 | 사용자 PC | ⚠️ 부분 성공 (Popular 매칭 실패) |
| D0-6 | `--debug-save-html` 플래그 추가 | Cowork | ✅ |
| **C1' 시도 #2** | **`--debug-save-html` 로 홈페이지 HTML 수집** | **사용자 PC** | ⏳ 대기 |
| D0-7 | Cowork가 HTML 분석 후 selector 고정 → 스크립트 v2.1 | Cowork | 대기 |
| C1' 시도 #3 | 고정된 selector 로 정상 수집 | 사용자 PC | 대기 |
| C2 v2 | 새 raw.json 기반 선별·요약 (popular+energy 가중치) | Cowork | 대기 |
| C3 | `generate_cards.py` 로 HTML 생성 | Cowork | 대기 |
| C4 | HTML → PNG → 공유 | 사용자 수동 | 대기 |
| C5 | `scripts/regen_today.bat` 원클릭 재생성 | Cowork | ✅ |
| C6 | Windows 작업 스케줄러 등록 (L2 자동화) | 사용자 + Cowork | 대기 |

**진행 원칙**: 한 번에 한 단위만. 끝날 때마다 이 파일 갱신 + 사용자에게 보고 → 다음 단위 확인.

---

## 📚 진행 이력

### D0-1 · Cowork 환경 제약 확인  (2026-04-20)

**무엇**
- Claude in Chrome 확장 사용 가능성 점검
- Cowork WebFetch / 샌드박스 curl 로 AI타임스 접근 가능성 점검

**왜**
- v0.1 초안은 "Chrome 으로 수집" 을 가정했으나 사내 보안 정책으로 확장 매일 삭제 지적받음
- 대체 경로의 가용 범위를 데이터로 확인해야 설계 확정 가능

**결과**
- Claude in Chrome = 매일 삭제 → **배제**
- Cowork WebFetch → aitimes.com / aitimes.kr **모두 `EGRESS_BLOCKED`**
- Cowork 샌드박스 `curl` → 연결 실패 (HTTP 000)
- Cowork **WebSearch** → 기사 제목/요약/URL 은 가져와짐 (보조 수단으로는 가능)
- → **수집 인프라는 "사용자 로컬 PC의 Python"만 안정적**
- 메모리 기록: `env_chrome_extension.md`, `env_egress_limits.md`

**다음** → D0-2

---

### D0-2 · 설계 문서 v0.2 확정  (2026-04-20)

**무엇**
- `PIPELINE.md` 를 v0.1 → v0.2 로 갱신

**왜**
- D0-1 에서 밝혀진 제약 3개 (Chrome 삭제 / egress 차단 / 결과물 매일 삭제) 를 처음부터 설계 전제로 못박아야 흔들리지 않음
- 역할 분리 (로컬=수집, Cowork=가공) 를 문서의 큰 그림에 명시

**결과**
- `PIPELINE.md` 섹션 2 에 "환경 제약" 표 추가
- 섹션 3 큰 그림을 **로컬 PC / Cowork / 사용자 수동** 3구역으로 재그림
- 자동화 레벨 L0~L4 정의 (현재 목표 L1)
- Open Questions 재조정 (Q1~Q7)

**다음** → D0-3

---

### D0-3 · `collect_aitimes.py` 초안 작성  (2026-04-20)

**무엇**
- 로컬 PC 에서 실행할 수집 스크립트 작성

**왜**
- Cowork 가 AI타임스에 접근 못 하므로, 수집은 반드시 사용자 PC에서 진행
- "RSS → HTML 폴백" 이중화로 CMS 변경이나 RSS 미제공 시에도 동작 보장

**결과**
- `scripts/collect_aitimes.py` 생성
- 동작 순서: `/rss/allArticle.xml` → `/rss/S1N1.xml` → `/news/articleList.html` 순차 시도
- 출력: `결과물/scraps/YYYY-MM-DD-raw.json` (title/url/lead/published_at/source)
- 옵션: `--date YYYY-MM-DD`, `--limit N`, `--out-dir PATH`
- 검증: `python3 -c "import ast; ast.parse(...)"` 통과, `--help` 정상 출력

**다음** → **C1 (사용자 실행 대기)**

---

## ✅ C1 완료 (2026-04-20)

- 시도 #2 (truststore 1안) 성공: `[ssl] truststore: injected` + RSS 50건 → 당일 13건 저장
- 저장 위치: `결과물/scraps/2026-04-20-raw.json`

## ✅ C2 v1 완료 (2026-04-20) — baseline

- 입력: `2026-04-20-raw.json` (RSS 최신순 13건)
- 선별: 7건 (앤트로픽/구글 국내 도입/한컴/뉴엔AI 공공 R&D/씨이랩/인핸스/국방 칼럼)
- 제외: 6건 (지역 공고 3 + AI 무관 1 + 루머 1 + 학술 수상 1)
- 산출물: `결과물/scraps/2026-04-20-v1.json`, `2026-04-20-v1.md` (파일명 `-v1` 으로 보존)

## ✅ D0-5 완료 (2026-04-20) — **소스 피벗**

**무엇**
- 사용자 피드백: "Most Popular 기사랑 future 에너지 기사 위주로 하면 좋을거같은데?"
- 방향 전환: RSS 최신순 단일 소스 → Most Popular + 에너지 섹션 조합

**왜**
- RSS 최신순은 속보 성격이 강해, 지역공고/비-AI 잡음이 13건 중 6건(46%) 섞여 나옴
- 사내 메일 브리핑은 "이번 주 화제" 성격이 더 적합 → Most Popular
- 업무 관련성(전력·에너지) 가중치를 원칙적으로 반영 → 에너지 섹션 고정 소스화 (PIPELINE Q5 해소)

**결과**
- `collect_aitimes.py` v2 로 확장
- 추가 기능:
  - `--sources rss,popular,energy` 다중 소스 지정 (기본 3종 전부)
  - Most Popular: 홈페이지 HTML 파싱 (selector 후보 8종 + 헤딩텍스트 휴리스틱 4종)
  - 에너지 섹션: RSS `S1N8~S1N20` 순차 시도 (매칭률 5/10 이상이면 채택) → 실패 시 전체 RSS 키워드 폴백
  - 중복 제거: URL 기준으로 merge, `tags=["popular","energy"]` 여러 라벨 누적 가능
  - 통계: 마지막에 `[stat] 태그 분포: {'popular':10, 'energy':3}` 같은 로그
- C2 v1 산출물은 `-v1` 접미어로 보존 (비교용 baseline)

**다음** → **C1' (사용자 재실행)**

---

## 🔜 C1' · 사용자 PC에서 스크립트 v2 재실행

**실행 명령**
```cmd
python scripts\collect_aitimes.py
```

**에러 (전 경로 동일)**
```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self-signed certificate in certificate chain'))
```

**원인 분석**
- 사내 네트워크 프록시(Zscaler·Bluecoat·SonicWall 류)가 HTTPS 트래픽을 **MITM 검사**하며 자체 서명 인증서로 재포장해서 내려줌
- 브라우저는 Windows 인증서 저장소에 사내 루트 CA가 설치돼 있어 통과
- Python `requests` 는 기본적으로 `certifi` 패키지 번들(공개 CA 만 포함)만 참조 → 사내 루트 CA를 모르는 상태 → 검증 실패
- RSS 2개 경로, HTML 경로 **모두 같은 에러** → 네트워크/사이트 문제 아니라 **SSL 계층 문제** 확정

### C1 스크립트 보강 (2026-04-20 · D0-4)

**변경점**
- 상단에 `truststore.inject_into_ssl()` 자동 시도 추가 (Python 3.10+ · Windows 인증서 저장소 자동 사용)
- `--insecure` 플래그 추가 (SSL 검증 끄기, 긴급 모드)
- 시작 시 `[ssl] truststore: ...` / `REQUESTS_CA_BUNDLE` 환경변수 상태를 로그로 출력 → 어느 경로로 해결됐는지 가시화
- 실패 시 `[hint]` 로 다음 조치 방법 안내

**해결 경로 3가지**

| 순위 | 방법 | 명령 | 비고 |
|---|---|---|---|
| ⭐1 | `truststore` 설치 (정석) | `pip install truststore` → 이후 `python scripts\collect_aitimes.py` | Windows 인증서 저장소를 자동 사용. 사내 루트 CA가 이미 브라우저에 있으니 바로 통과 |
| 2 | `REQUESTS_CA_BUNDLE` 환경변수 | 사내 IT가 제공하는 `.pem` 받아서 환경변수로 지정 | IT 협조 필요하지만 가장 "정석" |
| 3 | `--insecure` 플래그 | `python scripts\collect_aitimes.py --insecure` | 즉시 동작, 보안 경고 무시 — **사내망 안이라 실질 위험은 낮음** |

**사용자 실행**

```cmd
cd C:\Users\Admin\Desktop\project\daily-card-news
python scripts\collect_aitimes.py
```

(truststore 는 이미 설치됐으니 새 의존성 없음. 실패 시 `--insecure` 도 그대로 유효.)

**기대 로그 (예시)**

```
[ssl] truststore: injected
[info] sources=['energy', 'popular', 'rss'] target=2026-04-20 limit=20
[rss] 시도: https://www.aitimes.com/rss/allArticle.xml
[rss] ... 50 건
[popular] 홈페이지 파싱: https://www.aitimes.com/
[popular] selector '.most-popular' 매칭, 10건     ← 또는 heading 매칭
[energy] 섹션 피드 확정: .../rss/S1NXX.xml (7/10 매칭)   ← 또는 키워드 폴백
[done] NN 건 저장: ...\결과물\scraps\2026-04-20-raw.json
[stat] 태그 분포: {'popular': 10, 'energy': 5}
```

**확인 포인트 (중요)**

성공/실패와 무관하게 아래 정보가 필요합니다:

1. `[popular] ...` 로그 한 줄 — selector 중 어느 게 매칭됐는지 (다음 실행을 위한 고정용)
2. `[energy] ...` 로그 — 섹션 피드가 확정됐는지 아니면 키워드 폴백으로 갔는지
3. `[stat] 태그 분포` — popular/energy 태그가 몇 건씩인지
4. 최종 건수

**실패 케이스 3종**

| 증상 | 원인 | 대응 |
|---|---|---|
| `[popular] 매칭 실패` | 홈페이지 Most Popular 위젯 CSS 구조 변경 | 사용자가 브라우저로 홈페이지 열어서 위젯 영역 "검사(F12)" → CSS class 알려주면 `POPULAR_SELECTORS` 에 추가 |
| `[energy] 섹션 피드 실패 → 키워드 폴백` | 인포맥스 CMS 섹션 번호 불일치 | 정상 폴백. AI타임스 메뉴의 "에너지" 링크 URL 알려주면 섹션 피드로 고정 가능 |
| Most Popular 제목은 잡히는데 body 가 빈 상태 | 위젯이 제목만 노출 (본문 미리보기 없음) | C2 에서 URL 타고 들어가 본문 리드 1문단만 추가 스크래핑하는 옵션 검토 (다음 반복) |

**C1' 완료 후 알려주실 것**
- 위 기대 로그에서 어떤 변형이 나왔는지 (또는 로그 통째로 붙여넣기)
- 새 `raw.json` 이 만들어졌다는 사실만 알려주셔도 Cowork 가 바로 Read

→ 저희는 **C2 v2** 진행 (새 raw 로 재선별)

---

### C1' 시도 #1 결과 (2026-04-20) — ⚠️ 부분 성공

| 소스 | 결과 | 문제점 |
|---|---|---|
| RSS | ✅ 50건 → 당일 13건 | 정상 |
| Popular | ❌ 매칭 0건 | selector 12종 모두 미스. 구조 실측 필요 |
| Energy | ⚠️ 키워드 폴백 · 당일 2건 | S1N8~20 중 S1N13만 응답(에너지 아님), 나머지 404. 섹션번호 체계 비연속 |

**진단 근거**
- `{'energy': 2}` 태그 분포 → popular 태그 0건으로 피벗 핵심 미달
- 키워드 폴백 5건 중 3건이 당일 아님(날짜 필터 제거)
- S1N13 응답 사실은 AI타임스가 **섹션 번호를 연속적으로 쓰지 않음**을 시사 — 실제 에너지 메뉴 URL 확인 필요

### D0-6 · 디버그 플래그 추가 (2026-04-20)

**무엇**
- `collect_aitimes.py` 에 `--debug-save-html` 플래그 추가
- 플래그 지정 시 홈페이지 HTML 을 `결과물/scraps/_debug_home.html` 로 저장

**왜**
- Cowork 는 aitimes.com 을 직접 못 감 (egress block)
- 하지만 사용자 PC가 저장해 준 HTML 파일은 mount 폴더에 들어오면 Cowork 가 읽을 수 있음
- HTML 실물을 보면 Most Popular 위젯의 정확한 class/id 를 뽑아내어 `POPULAR_SELECTORS` 에 박을 수 있음

**다음** → C1' 시도 #2 (디버그 모드 실행)

---

## 🔜 C1' 시도 #2 · 디버그 HTML 수집 (사용자 1회 실행)

```cmd
cd C:\Users\Admin\Desktop\project\daily-card-news
python scripts\collect_aitimes.py --debug-save-html
```

**기대 결과**
- `결과물\scraps\_debug_home.html` 파일 생성 (홈페이지 전체 HTML, 수백 KB)
- raw.json 은 동일하게 생성됨 (디버그 모드라도 평상 동작)

**사용자가 알릴 것**
- `_debug_home.html` 파일 생겼다는 사실만 알려주면 됨
  - → Cowork 가 파일 읽어서 Most Popular 위젯 분석
  - → 실제 class/id 확인하여 `POPULAR_SELECTORS` 에 추가
  - → 스크립트 v2.1 배포 → C1' 시도 #3 는 selector 매칭 성공 예상
- 추가로 AI타임스 홈페이지 메뉴에서 "에너지" 또는 유사 카테고리가 **있는지** 눈으로 확인 후 알려주면 에너지 섹션도 개선 가능 (없으면 키워드 폴백 유지)

---

## 📒 변경 이력

- **2026-04-20 v0.1** · BUILD_LOG.md 최초 작성. D0 완료, C1 대기.
- **2026-04-20 v0.2** · C1 시도 #1 실패 기록 (SSL MITM). D0-4 (`truststore` + `--insecure`).
- **2026-04-20 v0.3** · C1 성공 · C2 v1 완료 (baseline) · **D0-5 소스 피벗** (RSS → Most Popular + 에너지) · 스크립트 v2 배포 · C1' 대기.
- **2026-04-20 v0.4** · C1' 시도 #1 부분 성공 기록 (RSS OK, Popular 0건, Energy 2건) · **D0-6 `--debug-save-html` 플래그 추가** · C1' 시도 #2 지침.
- **2026-04-20 v0.5** · C1' 시도 #2 성공 (debug HTML 확보) · **긴급모드 단축**: 사용자 재실행 없이 Cowork 가 HTML 직접 파싱해 Popular 10건 추출 → C2 v2 + C3 한 턴 처리. 오늘치 `2026-04-20.html` (9장 카드) 생성 완료. 스크립트 selector 고정은 내일(D0-7).
- **2026-04-20 v0.6** · **C5 `regen_today.bat` 작성 완료** (퇴근 직전 추가). 더블클릭 → 오늘/지정일 카드뉴스 HTML 재생성 + 브라우저 자동 오픈. 내일 이후 휘발성 파일 복구는 이 파일 하나로 충분.

## ✅ C2 v2 + C3 완료 (2026-04-20 긴급모드)

**C2 v2** — Popular 10건 + Energy 후보 → 7건 선별
- 앤트로픽 관련 5건 중 2건만 선택 (편향 축소)
- 루머·칼럼성 제외
- 에너지 1건 포함

**C3** — `generate_cards.py` 실행 성공
- 출력: `결과물/cardnews/2026-04-20.html` (9장 · 23KB)
- 터미널: "총 9장의 카드가 생성되었습니다"

**파일 매트릭스 (최종)**

| 파일 | 종류 | 영속성 |
|---|---|---|
| `결과물/scraps/2026-04-20-raw.json` | 수집 원본 | ✅ 영속 |
| `결과물/scraps/2026-04-20-v1.json/.md` | v1 baseline | ✅ 영속 |
| `결과물/scraps/2026-04-20.json` | 카드용 소스 | ✅ 영속 |
| `결과물/scraps/2026-04-20.md` | 사람용 요약 | ✅ 영속 |
| `결과물/scraps/_debug_home.html` | 디버그 스냅샷 | ⚠️ 휘발성 (.html) |
| `결과물/cardnews/2026-04-20.html` | **카드뉴스 결과물** | ⚠️ 휘발성 (.html) |

**C4 (사용자 수동)**
1. HTML 브라우저로 열기
2. 내장 "PNG로 저장" 버튼으로 카드별 다운로드
3. 카톡/메일 첨부

**내일 이어갈 것 (D0-7 ~ C5, C6)**
- 스크립트 v2.1: HTML 실측 기반 selector 고정 (`article.box-skin.idx--bg` 등)
- 에너지 섹션 URL 확인
- `regen_today.bat` 작성 (C5)
- Windows 작업 스케줄러 등록 (C6)
