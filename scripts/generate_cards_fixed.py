#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카드뉴스 고정 템플릿 생성기 (dark-photo + glassmorphism)

설계 원칙:
- 전 카드 동일 레이아웃: 풀블리드 이미지 배경 + 하단 어두운 그라데이션 오버레이
- 텍스트: 100% 흰색
- 태그/페이지번호: backdrop-filter blur 글래스모피즘 블록
- 컬러: #000, #fff 와 그 투명도만 사용 (브랜드 컬러 없음)
- 이미지: card.image_url 명시 > loremflickr (태그 기반) > 단색 #111 폴백

입력: generate_cards.py 와 동일한 카드 JSON (cover/news/closing)
사용 예:
    python generate_cards_fixed.py \
        --input 결과물/scraps/2026-04-20.json \
        --output 결과물/cardnews/2026-04-20-fixed.html
"""

import json
import argparse
import base64
import html as html_mod
import ssl
from urllib.parse import quote, urlparse

# ─── SSL: 사내 프록시 MITM 대응 ────────────────────────────────────────
# truststore 가 설치돼 있으면 Windows 인증서 저장소(브라우저에 이미 깔린 사내 루트 CA) 사용.
# 없으면 --insecure 플래그로 검증을 꺼서 진행 가능.
try:
    import truststore  # type: ignore
    truststore.inject_into_ssl()
    _TRUSTSTORE_OK = True
except Exception:
    _TRUSTSTORE_OK = False
# ────────────────────────────────────────────────────────────────────


# 카드별 AI 이미지 생성 프롬프트 (영문). 뉴스 내용에 맞춘 구체 묘사.
# "dark/cinematic/photorealistic" 키워드로 톤을 고정 템플릿 룩(어두운 사진)에 맞춤.
_CARD_PROMPTS = {
    "cover":   "modern AI newsletter cover art, dark abstract geometric background, blue ambient light, minimal cinematic, 4k editorial",
    "closing": "quiet morning city skyline, dark minimal abstract, soft light, cinematic wide shot",
    1:  "close-up of dark computer monitor displaying AI chat interface, neon blue reflections, photorealistic, shallow depth of field, editorial photo",
    2:  "programmer workspace, dark terminal with glowing code lines, over-the-shoulder developer viewpoint, cinematic lighting, photorealistic",
    3:  "modern design studio with dual monitors showing UI interface mockups, dark room with ambient warm light, photorealistic editorial",
    4:  "macro photograph of futuristic quantum computer processor chip, glowing blue circuits on black, extreme detail, photorealistic",
    5:  "vast data center aisle with server racks, cool blue LED lights in dark room, wide angle cinematic photography",
    6:  "abstract 3D neural network architecture visualization, geometric dark forms, volumetric fog, cinematic rendering",
    7:  "offshore wind turbines at golden hour dusk, dramatic sky, cinematic landscape photography, renewable energy",
    8:  "dark technology abstract background with subtle blue light streaks, minimal editorial, cinematic",
    9:  "abstract geometric technology background, dark tones with soft gradient, minimal cinematic",
}


def prompt_for(card):
    ctype = card.get("type", "news")
    if ctype == "cover":
        return _CARD_PROMPTS["cover"]
    if ctype == "closing":
        return _CARD_PROMPTS["closing"]
    n = card.get("number")
    if n in _CARD_PROMPTS:
        return _CARD_PROMPTS[n]
    # 미리 등록되지 않은 뉴스는 제목에서 영문만 뽑아 generic AI 이미지
    ascii_title = "".join(ch if ord(ch) < 128 else " " for ch in card.get("title", "")).strip()
    return f"dark cinematic editorial photograph about {ascii_title or 'AI technology'}, photorealistic, minimal"


def image_url_for(card, idx, use_proxy=True):
    """이미지 URL 반환.
    Pollinations 는 fetch() CORS 헤더를 안 줘서 canvas 캡처 시 문제 → weserv.nl 프록시로 래핑.
    card.image_url 이 명시되면 그걸 최우선 (프록시도 우회).
    """
    if card.get("image_url"):
        return card["image_url"]
    prompt = prompt_for(card)
    # Pollinations 원본 URL (seed 고정 → 재생성해도 같은 이미지)
    pollinations = (
        "https://image.pollinations.ai/prompt/"
        f"{quote(prompt, safe='')}"
        f"?width=1080&height=1080&seed={idx+1}&nologo=true&model=flux"
    )
    if not use_proxy:
        return pollinations
    # images.weserv.nl CORS 프록시 래핑 — Access-Control-Allow-Origin: * 확실히 송출
    return f"https://images.weserv.nl/?url={quote(pollinations, safe='')}"


def maybe_embed(url, timeout=60, insecure=False):
    """--embed-images 모드에서 호출. URL 에서 이미지 download → data URI 변환.
    실패 시 원본 URL 을 그대로 반환 (브라우저가 다시 시도).
    insecure=True 면 SSL 검증을 끔 (사내 MITM 프록시 비상용)."""
    if url.startswith("data:"):
        return url
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (card-news generator)"})
        ctx = None
        if insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            data = resp.read()
        b64 = base64.b64encode(data).decode("ascii")
        print(f"  [embed] {content_type} {len(data)//1024}KB <- {url[:80]}...")
        return f"data:{content_type};base64,{b64}"
    except Exception as e:
        print(f"  [embed] 실패 (원본 URL 유지): {e.__class__.__name__}: {e}")
        return url


def domain_of(url):
    if not url:
        return ""
    try:
        host = (urlparse(url).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def esc(s):
    return html_mod.escape(str(s if s is not None else ""), quote=True)


CSS = r"""
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #0a0a0a; }
body {
    font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont,
                 system-ui, 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    min-height: 100vh;
    padding: 40px 20px 120px;
    color: #fff;
}
.page-header {
    text-align: center;
    color: rgba(255,255,255,0.55);
    margin-bottom: 30px;
    font-size: 13px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
.grid {
    display: flex;
    flex-direction: column;
    gap: 32px;
    align-items: center;
}
.card {
    position: relative;
    width: 1080px;
    height: 1080px;
    max-width: calc(100vw - 40px);
    aspect-ratio: 1 / 1;
    overflow: hidden;
    border-radius: 20px;
    background: #141413;
    color: #fff;
    box-shadow: 0 24px 72px rgba(0,0,0,0.6);
}
/* 이미지 로드 실패 시 CSS 그라디언트 폴백 (빨간 placeholder 원천 차단) */
.card.no-image {
    background: radial-gradient(ellipse at top right, #2a2a30 0%, #141413 50%, #0a0a0a 100%);
}
.card.no-image[data-seed="1"]  { background: radial-gradient(ellipse at top, #1f2937 0%, #0a0a0a 70%); }
.card.no-image[data-seed="2"]  { background: radial-gradient(ellipse at top left, #1e293b 0%, #0f172a 60%, #020617 100%); }
.card.no-image[data-seed="3"]  { background: radial-gradient(ellipse at center, #1c1917 0%, #0c0a09 70%); }
.card.no-image[data-seed="4"]  { background: radial-gradient(ellipse at bottom, #18181b 0%, #09090b 70%); }
.card.no-image[data-seed="5"]  { background: radial-gradient(ellipse at top right, #1e1b4b 0%, #0c0a24 70%); }
.card.no-image[data-seed="6"]  { background: radial-gradient(ellipse at top, #111827 0%, #030712 70%); }
.card.no-image[data-seed="7"]  { background: radial-gradient(ellipse at bottom left, #1a1a1a 0%, #0a0a0a 70%); }
.card.no-image[data-seed="8"]  { background: radial-gradient(ellipse at top, #1c1917 0%, #0c0a09 70%); }
.card.no-image[data-seed="9"]  { background: radial-gradient(ellipse at center, #18181b 0%, #09090b 70%); }
/* 배경 이미지 레이어 — filter 로 살짝 죽여서 텍스트에 밀림 */
.card-bg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: 0;
    filter: brightness(0.68) saturate(1.12) contrast(1.02);
}
/* 균일 dim 틴트 — 이미지 전반 살짝 더 누름 */
.card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.18);
    z-index: 1;
}
/* 하단 집중 그라데이션 — 텍스트 영역 가독성 확보 */
.card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
        180deg,
        transparent 0%,
        rgba(0,0,0,0.15) 38%,
        rgba(0,0,0,0.55) 65%,
        rgba(0,0,0,0.88) 100%
    );
    z-index: 1;
}
.card.cover::after,
.card.closing::after {
    background: linear-gradient(
        180deg,
        rgba(0,0,0,0.35) 0%,
        rgba(0,0,0,0.45) 50%,
        rgba(0,0,0,0.75) 100%
    );
}
.card-inner {
    position: relative;
    z-index: 2;
    height: 100%;
    padding: 72px 68px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
/* 상단 바 */
.top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
.label {
    font-size: 13px;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.80);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}
/* 글래스모피즘 페이지 인디케이터 */
.page-indicator {
    padding: 10px 18px;
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 100px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: #fff;
    font-variant-numeric: tabular-nums;
}
/* 표지 */
.cover .card-inner { justify-content: space-between; }
.cover-main { margin-top: auto; }
.cover-title {
    font-size: 92px;
    font-weight: 900;
    line-height: 1.04;
    letter-spacing: -0.025em;
    color: #fff;
    margin-bottom: 26px;
    text-shadow: 0 2px 20px rgba(0,0,0,0.3);
}
.cover-divider {
    width: 64px;
    height: 3px;
    background: rgba(255,255,255,0.85);
    margin-bottom: 28px;
    border-radius: 2px;
}
.cover-subtitle {
    font-size: 32px;
    font-weight: 500;
    color: rgba(255,255,255,0.96);
    margin-bottom: 18px;
    letter-spacing: -0.01em;
}
.cover-accent {
    font-size: 20px;
    color: rgba(255,255,255,0.68);
    font-weight: 400;
    letter-spacing: 0.01em;
}
/* 뉴스 */
.news-body {
    display: flex;
    flex-direction: column;
    gap: 30px;
    margin-top: auto;
    padding-top: 40px;
}
.news-title {
    font-size: 66px;
    font-weight: 800;
    line-height: 1.16;
    letter-spacing: -0.02em;
    color: #fff;
    text-shadow: 0 2px 16px rgba(0,0,0,0.35);
}
.news-text {
    font-size: 25px;
    line-height: 1.55;
    color: rgba(255,255,255,0.93);
    font-weight: 400;
    letter-spacing: -0.005em;
}
.tags {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 4px;
}
.tag {
    padding: 9px 17px;
    background: rgba(255,255,255,0.12);
    backdrop-filter: blur(14px) saturate(150%);
    -webkit-backdrop-filter: blur(14px) saturate(150%);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 100px;
    font-size: 15px;
    font-weight: 500;
    color: #fff;
    letter-spacing: 0.01em;
}
/* 원문 링크 (뉴스 카드 하단 우측) */
.source-row {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-top: 6px;
    padding-top: 18px;
    border-top: 1px solid rgba(255,255,255,0.14);
}
.source-link {
    font-size: 14px;
    color: rgba(255,255,255,0.58);
    text-decoration: none;
    letter-spacing: 0.02em;
    font-variant-numeric: tabular-nums;
    transition: color 0.2s;
}
.source-link:hover { color: rgba(255,255,255,0.92); }
.source-link .arrow { margin-left: 6px; opacity: 0.7; }
/* 마무리 */
.closing .card-inner { justify-content: space-between; }
.closing-main { margin-top: auto; }
.closing-title {
    font-size: 74px;
    font-weight: 900;
    line-height: 1.12;
    color: #fff;
    margin-bottom: 28px;
    letter-spacing: -0.02em;
    text-shadow: 0 2px 16px rgba(0,0,0,0.35);
}
.closing-text {
    font-size: 24px;
    color: rgba(255,255,255,0.90);
    line-height: 1.55;
    margin-bottom: 32px;
}
.closing-source {
    font-size: 14px;
    color: rgba(255,255,255,0.55);
    letter-spacing: 0.03em;
    padding-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.18);
}
/* 액션 */
.actions {
    position: fixed;
    bottom: 22px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 8px;
    z-index: 100;
    background: rgba(20,20,19,0.72);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 100px;
    padding: 6px;
}
.btn {
    padding: 10px 18px;
    background: rgba(255,255,255,0.92);
    color: #141413;
    border: none;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
    letter-spacing: 0.02em;
}
.btn:hover { background: #fff; }
.btn.ghost { background: transparent; color: #fff; }
.btn.ghost:hover { background: rgba(255,255,255,0.1); }
@media (max-width: 1120px) {
    .card { width: 100%; height: auto; aspect-ratio: 1/1; }
    .card-inner { padding: 6%; }
    .cover-title { font-size: 8.4vw; }
    .news-title { font-size: 6vw; }
    .news-text { font-size: 2.4vw; }
    .cover-subtitle { font-size: 3vw; }
    .cover-accent { font-size: 1.9vw; }
    .closing-title { font-size: 6.8vw; }
    .closing-text { font-size: 2.3vw; }
}
"""


def render_card(card, idx, total, embed=False, use_proxy=True, insecure=False):
    ctype = card.get("type", "news")
    # embed 모드에선 프록시 없이 원본 Pollinations 로 direct download (속도/안정성)
    img_url = image_url_for(card, idx, use_proxy=(use_proxy and not embed))
    if embed:
        img_url = maybe_embed(img_url, insecure=insecure)
    # 로드 실패 시: 이미지 숨기고 카드에 .no-image 클래스 추가 → CSS 그라디언트 폴백
    onerr = (
        "this.style.display='none';"
        "this.parentElement.classList.add('no-image');"
    )
    # crossorigin="anonymous" → html2canvas 에서 CORS 통과, PNG 저장 가능
    bg_img = (
        f'<img class="card-bg" src="{esc(img_url)}" '
        f'crossorigin="anonymous" referrerpolicy="no-referrer" '
        f'onerror="{onerr}" alt="">'
    )

    if ctype == "cover":
        inner = f"""
        <div class="top">
            <div class="label">AI NEWSLETTER</div>
            <div class="page-indicator">{idx+1:02d} / {total:02d}</div>
        </div>
        <div class="cover-main">
            <h1 class="cover-title">{esc(card.get('title',''))}</h1>
            <div class="cover-divider"></div>
            <p class="cover-subtitle">{esc(card.get('subtitle',''))}</p>
            <p class="cover-accent">{esc(card.get('accent_text',''))}</p>
        </div>
        """
    elif ctype == "closing":
        inner = f"""
        <div class="top">
            <div class="label">CLOSING</div>
            <div class="page-indicator">{idx+1:02d} / {total:02d}</div>
        </div>
        <div class="closing-main">
            <h1 class="closing-title">{esc(card.get('title',''))}</h1>
            <p class="closing-text">{esc(card.get('body',''))}</p>
            <p class="closing-source">{esc(card.get('source',''))}</p>
        </div>
        """
    else:
        n = card.get("number", idx)
        tags_html = "".join(f'<span class="tag">#{esc(t)}</span>' for t in card.get("tags", []))
        src_url = card.get("source_url", "")
        src_row = ""
        if src_url:
            dom = domain_of(src_url) or "원문"
            src_row = (
                f'<div class="source-row">'
                f'<a class="source-link" href="{esc(src_url)}" target="_blank" rel="noopener">'
                f'출처 · {esc(dom)}<span class="arrow">↗</span></a></div>'
            )
        inner = f"""
        <div class="top">
            <div class="label">NEWS · {n:02d}</div>
            <div class="page-indicator">{idx+1:02d} / {total:02d}</div>
        </div>
        <div class="news-body">
            <h2 class="news-title">{esc(card.get('title',''))}</h2>
            <p class="news-text">{esc(card.get('body',''))}</p>
            <div class="tags">{tags_html}</div>
            {src_row}
        </div>
        """

    return f'''<div class="card {ctype}" id="card-{idx}" data-seed="{idx+1}">
    {bg_img}
    <div class="card-inner">{inner}</div>
</div>'''


HTML_SKELETON = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<style>{css}</style>
</head>
<body>
<div class="page-header">{title} · 고정 템플릿 v1 (dark-photo)</div>
<div class="grid">
{cards_html}
</div>
<div class="actions">
    <button class="btn" id="btn-all" onclick="saveAll()">ZIP 일괄 다운로드</button>
    <button class="btn ghost" onclick="saveCurrent()">현재 카드만</button>
</div>
<script>
const ZIP_BASENAME = "{zip_basename}";

async function waitForImages() {{
    const imgs = Array.from(document.querySelectorAll('.card-bg'));
    await Promise.all(imgs.map(img => {{
        if (img.complete && img.naturalWidth > 0) return Promise.resolve();
        return new Promise(resolve => {{
            const done = () => resolve();
            img.addEventListener('load', done, {{ once: true }});
            img.addEventListener('error', done, {{ once: true }});
            // 최대 60초 대기 (Pollinations 최초 생성 대비)
            setTimeout(done, 60000);
        }});
    }}));
}}

// html2canvas CORS 우회: 외부 이미지를 fetch → Blob → blob URL 로 치환
// blob URL 은 same-origin 이라 canvas 로 그려도 tainted 되지 않음
async function rewireImagesAsBlobs() {{
    const imgs = Array.from(document.querySelectorAll('.card-bg'));
    let ok = 0, failed = 0;
    for (const img of imgs) {{
        const src = img.src;
        if (!src || src.startsWith('data:') || src.startsWith('blob:')) {{
            ok++; continue;
        }}
        try {{
            const resp = await fetch(src, {{ mode: 'cors', credentials: 'omit', cache: 'force-cache' }});
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(blob);
            // crossorigin 속성은 blob: URL 과 충돌할 수 있어 제거
            img.removeAttribute('crossorigin');
            img.removeAttribute('referrerpolicy');
            await new Promise((resolve, reject) => {{
                const t = setTimeout(() => reject(new Error('load timeout')), 30000);
                img.addEventListener('load',  () => {{ clearTimeout(t); resolve(); }}, {{ once: true }});
                img.addEventListener('error', () => {{ clearTimeout(t); reject(new Error('img load error')); }}, {{ once: true }});
                img.src = blobUrl;
            }});
            ok++;
        }} catch (e) {{
            console.warn('[cors-rewire] 실패:', src.slice(0, 80), e.message);
            failed++;
        }}
    }}
    return {{ ok, failed }};
}}

async function captureBlob(el) {{
    const canvas = await html2canvas(el, {{
        useCORS: true,
        allowTaint: false,
        scale: 1,
        backgroundColor: null,
        logging: false,
        imageTimeout: 60000,
    }});
    return new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
}}

function triggerDownload(blob, filename) {{
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}}

async function saveAll() {{
    const btn = document.getElementById('btn-all');
    const original = btn.textContent;
    btn.disabled = true;
    btn.textContent = '이미지 로딩 중...';
    try {{
        await waitForImages();
        btn.textContent = '이미지 CORS 변환 중...';
        const {{ ok, failed }} = await rewireImagesAsBlobs();
        if (failed > 0) {{
            const cont = confirm(
                `${{failed}}장의 이미지를 CORS 안전하게 변환 실패했습니다.\\n` +
                `PNG 에 해당 카드 배경이 빠질 수 있습니다.\\n\\n` +
                `계속 진행할까요?\\n` +
                `(확실히 하려면 로컬에서 --embed-images 옵션으로 재생성하세요)`
            );
            if (!cont) {{
                btn.textContent = original; btn.disabled = false; return;
            }}
        }}
        const zip = new JSZip();
        const cards = document.querySelectorAll('.card');
        for (let i = 0; i < cards.length; i++) {{
            btn.textContent = `캡처 중 ${{i+1}}/${{cards.length}}...`;
            const blob = await captureBlob(cards[i]);
            zip.file(`card-${{String(i+1).padStart(2,'0')}}.png`, blob);
        }}
        btn.textContent = 'ZIP 압축 중...';
        const zipBlob = await zip.generateAsync({{
            type: 'blob',
            compression: 'DEFLATE',
            compressionOptions: {{ level: 6 }}
        }});
        triggerDownload(zipBlob, ZIP_BASENAME + '.zip');
        btn.textContent = '완료 — ZIP 저장됨';
    }} catch (e) {{
        console.error(e);
        alert('ZIP 저장 실패: ' + e.message + '\\n\\n--embed-images 모드로 재생성하면 확실합니다.');
    }} finally {{
        setTimeout(() => {{ btn.textContent = original; btn.disabled = false; }}, 2000);
    }}
}}

async function saveCurrent() {{
    try {{
        await waitForImages();
        await rewireImagesAsBlobs();
        const el = document.querySelector('.card:hover') || document.querySelector('.card');
        const blob = await captureBlob(el);
        const idx = Array.from(document.querySelectorAll('.card')).indexOf(el) + 1;
        triggerDownload(blob, `card-${{String(idx).padStart(2,'0')}}.png`);
    }} catch (e) {{
        alert('PNG 저장 실패: ' + e.message);
    }}
}}
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="고정 템플릿 카드뉴스 생성기 (dark-photo)")
    ap.add_argument("--input", required=True, help="카드 JSON 파일")
    ap.add_argument("--output", required=True, help="출력 HTML 파일")
    ap.add_argument("--title", default=None, help="페이지 상단 레이블 오버라이드")
    ap.add_argument("--embed-images", action="store_true",
                    help="이미지를 data URI 로 HTML 에 내장 (네트워크 없이 열림 + PNG 저장 CORS 문제 해결)")
    ap.add_argument("--no-proxy", action="store_true",
                    help="images.weserv.nl CORS 프록시 래핑 비활성화 (Pollinations 직접 호출)")
    ap.add_argument("--insecure", action="store_true",
                    help="--embed-images 다운로드 시 SSL 검증 끔 (사내 MITM 프록시 비상 모드)")
    args = ap.parse_args()
    # SSL 상태 로그
    if args.embed_images:
        if args.insecure:
            print("[ssl] 모드: insecure (SSL 검증 OFF)")
        elif _TRUSTSTORE_OK:
            print("[ssl] 모드: truststore (Windows 인증서 저장소 사용)")
        else:
            print("[ssl] 모드: 기본 certifi 번들  (truststore 미설치)")
            print("      → 사내망에서 SSL 오류 나면 'pip install truststore' 또는 '--insecure' 사용")

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    cards = data.get("cards", [])
    total = len(cards)
    page_title = args.title or f"{data.get('title','카드뉴스')} · {data.get('date','')}"

    if args.embed_images:
        print(f"[embed] 이미지 내장 모드 — 카드 {total}장 네트워크에서 다운로드 중...")
    use_proxy = not args.no_proxy
    cards_html = "\n".join(
        render_card(c, i, total,
                    embed=args.embed_images,
                    use_proxy=use_proxy,
                    insecure=args.insecure)
        for i, c in enumerate(cards)
    )
    # ZIP 파일명용 날짜 (JSON date > 출력 파일명 stem > today)
    date_str = data.get("date", "").replace(".", "-").replace("/", "-").strip() or "cardnews"
    zip_basename = f"cards-{date_str}"
    html = HTML_SKELETON.format(
        title=esc(page_title),
        css=CSS,
        cards_html=cards_html,
        zip_basename=esc(zip_basename),
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    mode = "embed" if args.embed_images else "remote"
    print(f"[done] {total}장 카드 생성 ({mode}) → {args.output}")


if __name__ == "__main__":
    main()
