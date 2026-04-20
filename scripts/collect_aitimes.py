#!/usr/bin/env python3
"""
AI타임스(aitimes.com) 당일 기사 수집기 v2
==========================================

PIPELINE.md v0.2 의 Step 1 을 구현.
v2 변경점: Most Popular 섹션 + 에너지 섹션 수집 추가 (D0-5 피벗).

실행:
    python scripts/collect_aitimes.py                         # 기본 (RSS+Popular+Energy 전부)
    python scripts/collect_aitimes.py --sources rss           # RSS 최신순만
    python scripts/collect_aitimes.py --sources popular,energy# 인기+에너지만
    python scripts/collect_aitimes.py --date 2026-04-19       # 특정일 (RSS 소스에만 적용)
    python scripts/collect_aitimes.py --insecure              # SSL 긴급 우회

출력:
    결과물/scraps/YYYY-MM-DD-raw.json
    형식: [{title, url, lead, published_at, source, tags:[]}, ...]
    같은 URL이 여러 소스에서 잡히면 tags 에 여러 라벨 누적 (예: ["popular","energy"])

의존성:
    pip install requests feedparser beautifulsoup4
    (권장) pip install truststore

SSL 전략 (상세는 v1 헤더 참고):
    1) truststore inject
    2) REQUESTS_CA_BUNDLE env
    3) --insecure

소스 전략 3종:
    [rss]     /rss/allArticle.xml → /rss/S1N1.xml → /news/articleList.html
              당일 RSS 최신순 수집 (기존 v1 동작)
    [popular] 홈페이지 HTML 에서 "Most Popular" 위젯 파싱
              selector 후보 3종 + 헤딩텍스트 휴리스틱 2종 순차 시도
              결과는 **날짜 필터 적용 안 함** (인기글은 며칠 전 것도 OK)
    [energy]  에너지 섹션 수집:
              1) RSS 섹션 번호 후보 순차 시도 (S1N8~S1N20)
              2) 모두 실패 시 → 전체 RSS 에서 ENERGY_KEYWORDS 매칭 항목 필터
              [energy] 도 날짜 필터 적용 (당일분만)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Iterable

try:
    import requests
except ImportError:
    sys.exit("requests 미설치: pip install requests")

# SSL 전략 1순위: truststore 주입
_TRUSTSTORE_STATUS = "not-installed"
try:
    import truststore
    truststore.inject_into_ssl()
    _TRUSTSTORE_STATUS = "injected"
except ImportError:
    pass
except Exception as e:
    _TRUSTSTORE_STATUS = f"error: {e}"

try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("beautifulsoup4 미설치: pip install beautifulsoup4")

try:
    from urllib3.exceptions import InsecureRequestWarning  # type: ignore
except ImportError:
    InsecureRequestWarning = None  # type: ignore


# ── 상수 ─────────────────────────────────────────────────────────────
BASE = "https://www.aitimes.com"
RSS_CANDIDATES = [
    f"{BASE}/rss/allArticle.xml",
    f"{BASE}/rss/S1N1.xml",
]
LIST_URL = f"{BASE}/news/articleList.html"
HOME_URL = f"{BASE}/"

# Most Popular 섹션 파싱 후보 (상위 → 하위 휴리스틱)
POPULAR_SELECTORS = [
    ".most-popular",
    ".most-read",
    ".popular-news",
    ".ranking-news",
    "#mostPopular",
    "[class*='most-popular']",
    "[class*='most-read']",
    "[class*='popular']",
]
POPULAR_HEADING_TEXTS = ["Most Popular", "인기기사", "많이 본 기사", "인기뉴스"]

# 에너지 섹션 RSS 후보 (인포맥스 CMS 섹션 번호 추정 범위)
ENERGY_RSS_CANDIDATES = [
    f"{BASE}/rss/S1N{n}.xml" for n in range(8, 21)
]
# 에너지 관련 기사 식별 키워드 (RSS 제목/리드 매칭용 폴백)
ENERGY_KEYWORDS = [
    "에너지", "원전", "원자력", "재생에너지", "신재생",
    "태양광", "풍력", "수소", "전력", "전기", "그리드",
    "탄소중립", "발전소", "스마트그리드", "ESS",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0 Safari/537.36 (daily-card-news collector)"
)
TIMEOUT = 10


# ── 공용 I/O ─────────────────────────────────────────────────────────
def fetch(url: str, *, verify: bool = True) -> str | None:
    """URL 가져오기 (실패 시 None)."""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA},
            timeout=TIMEOUT,
            verify=verify,
        )
        r.raise_for_status()
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception as e:
        print(f"[warn] fetch 실패: {url} ({e})", file=sys.stderr)
        return None


# ── 파서: RSS ────────────────────────────────────────────────────────
def parse_rss(xml_text: str, source_label: str = "aitimes.com (RSS)") -> list[dict]:
    if not feedparser:
        return []
    fp = feedparser.parse(xml_text)
    out: list[dict] = []
    for e in fp.entries:
        title = (e.get("title") or "").strip()
        url = (e.get("link") or "").strip()
        lead = (e.get("summary") or e.get("description") or "").strip()
        lead = BeautifulSoup(lead, "html.parser").get_text(" ", strip=True)
        published = e.get("published_parsed") or e.get("updated_parsed")
        if published:
            published_at = dt.datetime(*published[:6]).isoformat()
        else:
            published_at = ""
        if title and url:
            out.append(
                {
                    "title": title,
                    "url": url,
                    "lead": lead[:500],
                    "published_at": published_at,
                    "source": source_label,
                    "tags": [],
                }
            )
    return out


# ── 파서: HTML 목록 폴백 (기본 RSS용) ─────────────────────────────────
def parse_html_list(html_text: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html_text, "html.parser")
    out: list[dict] = []
    anchors = []
    for sel in [
        "a.auto-titles[href*='articleView.html']",
        "a[href*='articleView.html?idxno=']",
    ]:
        anchors = soup.select(sel)
        if anchors:
            break
    seen = set()
    for a in anchors:
        href = a.get("href", "")
        if not href or "articleView.html" not in href:
            continue
        url = href if href.startswith("http") else f"{BASE}{href}"
        if url in seen:
            continue
        seen.add(url)
        title = a.get_text(strip=True)
        if not title:
            continue
        lead = ""
        parent = a.find_parent(["div", "li", "article"])
        if parent:
            lead_el = parent.select_one(".list-summary, .read p, .auto-article-summary")
            if lead_el:
                lead = lead_el.get_text(" ", strip=True)
        out.append(
            {
                "title": title,
                "url": url,
                "lead": lead[:500],
                "published_at": "",
                "source": "aitimes.com (HTML)",
                "tags": [],
            }
        )
        if len(out) >= limit * 2:
            break
    return out


# ── 파서: Most Popular 위젯 ──────────────────────────────────────────
def _anchors_to_items(anchors, source_label: str, tag: str) -> list[dict]:
    out: list[dict] = []
    seen = set()
    for a in anchors:
        href = a.get("href", "")
        if not href or "articleView.html" not in href:
            continue
        url = href if href.startswith("http") else f"{BASE}{href}"
        if url in seen:
            continue
        seen.add(url)
        title = a.get_text(" ", strip=True)
        if not title:
            continue
        out.append(
            {
                "title": title,
                "url": url,
                "lead": "",
                "published_at": "",
                "source": source_label,
                "tags": [tag],
            }
        )
    return out


def parse_popular(html_text: str, limit: int = 10) -> list[dict]:
    """홈페이지 HTML 에서 Most Popular 링크 추출."""
    soup = BeautifulSoup(html_text, "html.parser")

    # 1) CSS selector 후보 순차 시도
    for sel in POPULAR_SELECTORS:
        container = soup.select_one(sel)
        if container:
            anchors = container.select("a[href*='articleView.html']")
            if anchors:
                items = _anchors_to_items(
                    anchors[:limit], "aitimes.com (popular)", "popular"
                )
                if items:
                    print(f"[popular] selector '{sel}' 매칭, {len(items)}건")
                    return items

    # 2) "Most Popular" / "인기기사" 같은 헤딩 텍스트 기반 휴리스틱
    for text in POPULAR_HEADING_TEXTS:
        hdr = soup.find(
            lambda t: t.name in ("h1", "h2", "h3", "h4", "strong", "div", "span")
            and t.get_text(strip=True)
            and text in t.get_text(strip=True)
        )
        if hdr:
            # 가장 가까운 상위 컨테이너에서 링크 찾기
            container = hdr
            for _ in range(5):  # 최대 5레벨 상향
                container = container.parent
                if not container:
                    break
                anchors = container.select("a[href*='articleView.html']")
                if len(anchors) >= 3:  # 최소 3개 이상 모여야 "인기 리스트"로 간주
                    items = _anchors_to_items(
                        anchors[:limit], "aitimes.com (popular)", "popular"
                    )
                    if items:
                        print(f"[popular] heading '{text}' 매칭, {len(items)}건")
                        return items

    print("[popular] 매칭 실패 — 사이트 구조 변경 가능. 수동 확인 필요.")
    return []


# ── 파서: 에너지 섹션 ─────────────────────────────────────────────────
def fetch_energy(target_date: dt.date, *, verify: bool = True) -> list[dict]:
    """
    에너지 섹션 수집.
    1) RSS 섹션 번호 순차 시도 — 첫 번째로 '에너지 키워드 비중 높은' 피드 채택
    2) 실패 시 전체 RSS 에서 키워드 필터링 폴백
    """
    # 1) RSS 섹션 번호 순차 시도
    for url in ENERGY_RSS_CANDIDATES:
        xml = fetch(url, verify=verify)
        if not xml:
            continue
        items = parse_rss(xml, source_label=f"aitimes.com (energy:{url.rsplit('/',1)[-1]})")
        if not items:
            continue
        # 이 피드가 진짜 에너지 섹션인지 검증: 상위 10건 중 키워드 매칭 5개 이상
        matched = sum(
            1 for it in items[:10] if any(k in it["title"] + it["lead"] for k in ENERGY_KEYWORDS)
        )
        if matched >= 5:
            print(f"[energy] 섹션 피드 확정: {url} ({matched}/10 매칭)")
            for it in items:
                it["tags"] = ["energy"]
                it["source"] = "aitimes.com (energy-section)"
            return filter_by_date(items, target_date)
        else:
            print(f"[energy] {url} 매칭 부족 ({matched}/10), 다음 후보")

    # 2) 폴백: 전체 RSS 에서 키워드 필터
    print("[energy] 섹션 피드 실패 → 전체 RSS 키워드 폴백")
    for url in RSS_CANDIDATES:
        xml = fetch(url, verify=verify)
        if not xml:
            continue
        items = parse_rss(xml, source_label="aitimes.com (energy-keyword)")
        filtered = [
            it
            for it in items
            if any(k in it["title"] + it["lead"] for k in ENERGY_KEYWORDS)
        ]
        if filtered:
            print(f"[energy] 키워드 폴백 {len(filtered)}건")
            for it in filtered:
                it["tags"] = ["energy"]
            return filter_by_date(filtered, target_date)

    return []


# ── 필터 ─────────────────────────────────────────────────────────────
def filter_by_date(items: list[dict], target: dt.date) -> list[dict]:
    """published_at == target 또는 미상만 유지."""
    kept: list[dict] = []
    for it in items:
        pub = it.get("published_at") or ""
        if not pub:
            kept.append(it)
            continue
        try:
            if dt.datetime.fromisoformat(pub).date() == target:
                kept.append(it)
        except Exception:
            kept.append(it)
    return kept


# ── 중복 제거 (URL 기준, tags 병합) ──────────────────────────────────
def merge_items(*lists: list[dict]) -> list[dict]:
    by_url: dict[str, dict] = {}
    order: list[str] = []
    for lst in lists:
        for it in lst:
            url = it["url"]
            if url not in by_url:
                by_url[url] = {
                    **it,
                    "tags": list(it.get("tags") or []),
                    "sources": [it.get("source", "")],
                }
                order.append(url)
            else:
                merged = by_url[url]
                for t in it.get("tags") or []:
                    if t not in merged["tags"]:
                        merged["tags"].append(t)
                src = it.get("source", "")
                if src and src not in merged["sources"]:
                    merged["sources"].append(src)
                # lead 가 비어있으면 채워주기
                if not merged.get("lead") and it.get("lead"):
                    merged["lead"] = it["lead"]
                # published_at 이 비어있으면 채워주기
                if not merged.get("published_at") and it.get("published_at"):
                    merged["published_at"] = it["published_at"]
    return [by_url[u] for u in order]


# ── 파이프라인 ────────────────────────────────────────────────────────
def collect_rss(target: dt.date, limit: int, *, verify: bool = True) -> list[dict]:
    for url in RSS_CANDIDATES:
        print(f"[rss] 시도: {url}")
        xml = fetch(url, verify=verify)
        if not xml:
            continue
        items = parse_rss(xml)
        if items:
            print(f"[rss] {url} {len(items)} 건")
            return filter_by_date(items, target)[:limit]
    print(f"[rss] HTML 폴백: {LIST_URL}")
    html = fetch(LIST_URL, verify=verify)
    if not html:
        return []
    items = parse_html_list(html, limit)
    print(f"[rss] HTML {len(items)} 건")
    return filter_by_date(items, target)[:limit]


def collect_popular(limit: int = 10, *, verify: bool = True) -> list[dict]:
    print(f"[popular] 홈페이지 파싱: {HOME_URL}")
    html = fetch(HOME_URL, verify=verify)
    if not html:
        return []
    return parse_popular(html, limit)


def collect(
    target: dt.date,
    limit: int,
    sources: set[str],
    *,
    verify: bool = True,
) -> list[dict]:
    parts: list[list[dict]] = []
    if "rss" in sources:
        parts.append(collect_rss(target, limit, verify=verify))
    if "popular" in sources:
        parts.append(collect_popular(limit=10, verify=verify))
    if "energy" in sources:
        parts.append(fetch_energy(target, verify=verify))
    return merge_items(*parts)


# ── main ─────────────────────────────────────────────────────────────
def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AI타임스 당일 기사 수집 (v2)")
    ap.add_argument("--date", help="YYYY-MM-DD (생략 시 오늘)")
    ap.add_argument("--limit", type=int, default=20, help="소스별 최대 건수 (기본 20)")
    ap.add_argument(
        "--sources",
        default="rss,popular,energy",
        help="쉼표 구분. 기본 'rss,popular,energy'. 예: 'popular,energy'",
    )
    ap.add_argument(
        "--out-dir",
        default=None,
        help="출력 디렉토리 (기본: <repo>/daily-card-news/결과물/scraps/)",
    )
    ap.add_argument(
        "--insecure",
        action="store_true",
        help="SSL 검증 끄기 (사내 MITM 프록시 긴급 모드)",
    )
    args = ap.parse_args(argv)

    # SSL 상태 로그
    print(f"[ssl] truststore: {_TRUSTSTORE_STATUS}")
    env_ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("CURL_CA_BUNDLE")
    if env_ca:
        print(f"[ssl] REQUESTS_CA_BUNDLE={env_ca}")
    if args.insecure:
        print("[ssl] --insecure: SSL 검증 건너뜀")
        if InsecureRequestWarning is not None:
            import warnings
            warnings.simplefilter("ignore", InsecureRequestWarning)

    target = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    sources = {s.strip().lower() for s in args.sources.split(",") if s.strip()}
    valid = {"rss", "popular", "energy"}
    bad = sources - valid
    if bad:
        print(f"[err] 알 수 없는 소스: {bad}. 유효값: {valid}", file=sys.stderr)
        return 2
    print(f"[info] sources={sorted(sources)} target={target} limit={args.limit}")

    # 출력 경로
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        script_dir = Path(__file__).resolve().parent
        out_dir = script_dir.parent / "결과물" / "scraps"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{target.isoformat()}-raw.json"

    items = collect(target, args.limit, sources, verify=(not args.insecure))
    if not items:
        print("[err] 수집 결과 0건.", file=sys.stderr)
        if _TRUSTSTORE_STATUS == "not-installed" and not args.insecure:
            print(
                "[hint] SSL 에러라면 `pip install truststore` 또는 `--insecure`",
                file=sys.stderr,
            )
        return 1

    out_path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 간단한 통계
    tag_counts: dict[str, int] = {}
    for it in items:
        for t in it.get("tags") or []:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print(f"[done] {len(items)} 건 저장: {out_path}")
    if tag_counts:
        print(f"[stat] 태그 분포: {tag_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
