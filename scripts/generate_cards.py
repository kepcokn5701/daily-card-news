#\!/usr/bin/env python3
"""
카드뉴스 HTML 생성기 v2
세련된 그라데이션 배경, 장식 요소, 글래스모피즘 효과가 적용된 카드뉴스를 생성합니다.
HTML 템플릿을 여러 문자열 연결로 분할하여 f-string 크기 제한을 방지합니다.
"""

import json
import argparse
from datetime import datetime

# 카드별 배경 그라데이션 팔레트
CARD_PALETTES = [
    {"grad": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "accent": "#e0d4f7", "text": "#fff", "sub": "rgba(255,255,255,0.8)", "tag_bg": "rgba(255,255,255,0.2)", "tag_text": "#fff", "number_color": "rgba(255,255,255,0.12)"},
    {"grad": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)", "accent": "#4fd1c5", "text": "#fff", "sub": "rgba(255,255,255,0.75)", "tag_bg": "rgba(79,209,197,0.2)", "tag_text": "#4fd1c5", "number_color": "rgba(79,209,197,0.12)"},
    {"grad": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)", "accent": "#e94560", "text": "#fff", "sub": "rgba(255,255,255,0.75)", "tag_bg": "rgba(233,69,96,0.2)", "tag_text": "#e94560", "number_color": "rgba(233,69,96,0.1)"},
    {"grad": "linear-gradient(135deg, #232526 0%, #414345 100%)", "accent": "#f7971e", "text": "#fff", "sub": "rgba(255,255,255,0.75)", "tag_bg": "rgba(247,151,30,0.2)", "tag_text": "#f7d08a", "number_color": "rgba(247,151,30,0.1)"},
    {"grad": "linear-gradient(135deg, #141e30 0%, #243b55 100%)", "accent": "#00d2ff", "text": "#fff", "sub": "rgba(255,255,255,0.75)", "tag_bg": "rgba(0,210,255,0.15)", "tag_text": "#7ee8fa", "number_color": "rgba(0,210,255,0.1)"},
    {"grad": "linear-gradient(135deg, #1f1c2c 0%, #928dab 100%)", "accent": "#f8cdda", "text": "#fff", "sub": "rgba(255,255,255,0.8)", "tag_bg": "rgba(248,205,218,0.2)", "tag_text": "#f8cdda", "number_color": "rgba(248,205,218,0.1)"},
    {"grad": "linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 50%, #2d1b69 100%)", "accent": "#a78bfa", "text": "#fff", "sub": "rgba(255,255,255,0.75)", "tag_bg": "rgba(167,139,250,0.2)", "tag_text": "#c4b5fd", "number_color": "rgba(167,139,250,0.1)"},
    {"grad": "linear-gradient(135deg, #134e5e 0%, #71b280 100%)", "accent": "#d4fc79", "text": "#fff", "sub": "rgba(255,255,255,0.85)", "tag_bg": "rgba(212,252,121,0.2)", "tag_text": "#d4fc79", "number_color": "rgba(212,252,121,0.1)"},
]

COVER_GRADIENT = "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"
CLOSING_GRADIENT = "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"


def deco_shapes(card_type, index):
    """장식 도형을 생성합니다."""
    if card_type == "cover":
        return (
            '<div class="deco deco-circle-1"></div>'
            '<div class="deco deco-circle-2"></div>'
            '<div class="deco deco-circle-3"></div>'
            '<div class="deco deco-line-1"></div>'
            '<div class="deco deco-line-2"></div>'
            '<div class="deco deco-dots"></div>'
        )
    elif card_type == "closing":
        return (
            '<div class="deco deco-circle-1"></div>'
            '<div class="deco deco-circle-2"></div>'
            '<div class="deco deco-ring"></div>'
        )
    else:
        variations = [
            '<div class="deco deco-blob-tr"></div><div class="deco deco-line-accent"></div><div class="deco deco-dot-grid"></div>',
            '<div class="deco deco-circle-br"></div><div class="deco deco-stripe"></div><div class="deco deco-cross"></div>',
            '<div class="deco deco-arc-tl"></div><div class="deco deco-dots-row"></div><div class="deco deco-square-float"></div>',
            '<div class="deco deco-ring-sm"></div><div class="deco deco-line-diag"></div><div class="deco deco-triangle"></div>',
            '<div class="deco deco-blob-bl"></div><div class="deco deco-dash-line"></div><div class="deco deco-circle-sm"></div>',
        ]
        return variations[index % len(variations)]


def generate_card_html(card, index, total):
    """개별 카드 HTML 생성"""
    card_type = card.get("type", "news")
    palette = CARD_PALETTES[index % len(CARD_PALETTES)]
    decos = deco_shapes(card_type, index)

    if card_type == "cover":
        h = ""
        h += '<div class="card cover-card" id="card-' + str(index)
        h += '" style="background:' + COVER_GRADIENT + ';">\n'
        h += decos + "\n"
        h += '<div class="card-inner">\n'
        h += '<div class="cover-badge">AI NEWSLETTER</div>\n'
        h += '<h1 class="cover-title">' + card.get("title", "") + '</h1>\n'
        h += '<div class="cover-divider"></div>\n'
        h += '<p class="cover-subtitle">' + card.get("subtitle", "") + '</p>\n'
        h += '<p class="cover-accent">' + card.get("accent_text", "") + '</p>\n'
        h += '</div>\n'
        h += '<div class="card-footer">\n'
        h += '<span class="page-indicator">1 / ' + str(total) + '</span>\n'
        h += '</div>\n'
        h += '</div>'
        return h

    elif card_type == "closing":
        h = ""
        h += '<div class="card closing-card" id="card-' + str(index)
        h += '" style="background:' + CLOSING_GRADIENT + ';">\n'
        h += decos + "\n"
        h += '<div class="card-inner">\n'
        h += '<div class="closing-icon-wrap">\n'
        h += '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
        h += 'stroke="rgba(255,255,255,0.9)" stroke-width="2" '
        h += 'stroke-linecap="round" stroke-linejoin="round">\n'
        h += '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>\n'
        h += '<polyline points="22 4 12 14.01 9 11.01"/>\n'
        h += '</svg>\n'
        h += '</div>\n'
        h += '<h2 class="closing-title">' + card.get("title", "마무리") + '</h2>\n'
        h += '<p class="closing-body">' + card.get("body", "") + '</p>\n'
        h += '<div class="closing-divider"></div>\n'
        h += '<p class="closing-source">' + card.get("source", "") + '</p>\n'
        h += '</div>\n'
        h += '<div class="card-footer">\n'
        h += '<span class="page-indicator">'
        h += str(index + 1) + ' / ' + str(total) + '</span>\n'
        h += '</div>\n'
        h += '</div>'
        return h

    else:
        number = card.get("number", index)
        num_str = str(number).zfill(2)
        tags_html = ""
        if card.get("tags"):
            tags_html = '<div class="tags">'
            for t in card["tags"]:
                tags_html += '<span class="tag" style="background:'
                tags_html += palette["tag_bg"] + ";color:"
                tags_html += palette["tag_text"] + '">#' + t + '</span>'
            tags_html += '</div>'

        h = ""
        h += '<div class="card news-card" id="card-' + str(index)
        h += '" style="background:' + palette["grad"] + ';">\n'
        h += decos + "\n"
        h += '<div class="card-inner">\n'
        h += '<div class="news-header">\n'
        h += '<span class="news-number" style="color:'
        h += palette["number_color"] + '">' + num_str + '</span>\n'
        h += '<div class="news-label" style="color:'
        h += palette["accent"] + '">NEWS ' + num_str + '</div>\n'
        h += '</div>\n'
        h += '<div class="news-content">\n'
        h += '<h2 class="news-title" style="color:'
        h += palette["text"] + '">' + card.get("title", "") + '</h2>\n'
        h += '<div class="news-body-wrap" style="border-left:3px solid '
        h += palette["accent"] + '">\n'
        h += '<p class="news-body" style="color:'
        h += palette["sub"] + '">' + card.get("body", "") + '</p>\n'
        h += '</div>\n'
        h += tags_html + "\n"
        h += '</div>\n'
        h += '</div>\n'
        h += '<div class="card-footer">\n'
        h += '<span class="page-indicator" style="color:'
        h += palette["sub"] + '">'
        h += str(index + 1) + ' / ' + str(total) + '</span>\n'
        h += '</div>\n'
        h += '</div>'
        return h


def _build_css():
    """CSS 스타일을 일반 문자열로 반환 (f-string 불필요)"""
    css = "<style>\n"
    css += "  * { margin: 0; padding: 0; box-sizing: border-box; }\n\n"
    css += "  body {\n"
    css += "    font-family: 'Noto Sans KR', 'Inter', -apple-system, sans-serif;\n"
    css += "    background: #0a0a0f;\n"
    css += "    display: flex; flex-direction: column; align-items: center;\n"
    css += "    padding: 48px 20px; gap: 40px; min-height: 100vh;\n"
    css += "  }\n\n"
    css += "  .controls {\n"
    css += "    position: fixed; top: 20px; right: 20px;\n"
    css += "    z-index: 1000; display: flex; gap: 8px;\n"
    css += "  }\n"
    css += "  .btn {\n"
    css += "    padding: 10px 20px; border: none; border-radius: 10px;\n"
    css += "    font-family: 'Noto Sans KR', sans-serif;\n"
    css += "    font-size: 14px; font-weight: 600; cursor: pointer;\n"
    css += "    transition: all 0.2s; backdrop-filter: blur(12px);\n"
    css += "  }\n"
    css += "  .btn-primary {\n"
    css += "    background: rgba(99,102,241,0.9); color: white;\n"
    css += "    box-shadow: 0 4px 20px rgba(99,102,241,0.4);\n"
    css += "  }\n"
    css += "  .btn-primary:hover {\n"
    css += "    transform: translateY(-2px);\n"
    css += "    box-shadow: 0 6px 28px rgba(99,102,241,0.5);\n"
    css += "  }\n"
    css += "  .btn-secondary {\n"
    css += "    background: rgba(255,255,255,0.1);\n"
    css += "    color: rgba(255,255,255,0.8);\n"
    css += "    border: 1px solid rgba(255,255,255,0.15);\n"
    css += "  }\n"
    css += "  .btn-secondary:hover { background: rgba(255,255,255,0.18); }\n\n"
    css += "  .card {\n"
    css += "    width: 1080px; height: 1080px; position: relative;\n"
    css += "    overflow: hidden; display: flex; flex-direction: column;\n"
    css += "  }\n"
    css += "  .card-inner {\n"
    css += "    position: relative; z-index: 2; flex: 1;\n"
    css += "    display: flex; flex-direction: column; padding: 80px;\n"
    css += "  }\n\n"
    css += "  .deco { position: absolute; pointer-events: none; z-index: 1; }\n\n"
    css += _build_css_decos()
    css += _build_css_cards()
    css += _build_css_responsive()
    css += _build_css_toast()
    css += "</style>\n"
    return css


def _build_css_decos():
    """장식 요소 CSS"""
    c = ""
    c += "  .deco-circle-1 {\n"
    c += "    width: 500px; height: 500px; border-radius: 50%;\n"
    c += "    background: radial-gradient(circle, rgba(139,92,246,0.25) 0%, transparent 70%);\n"
    c += "    top: -150px; right: -100px;\n"
    c += "  }\n"
    c += "  .deco-circle-2 {\n"
    c += "    width: 350px; height: 350px; border-radius: 50%;\n"
    c += "    background: radial-gradient(circle, rgba(79,70,229,0.2) 0%, transparent 70%);\n"
    c += "    bottom: -80px; left: -60px;\n"
    c += "  }\n"
    c += "  .deco-circle-3 {\n"
    c += "    width: 200px; height: 200px; border-radius: 50%;\n"
    c += "    border: 1px solid rgba(255,255,255,0.06);\n"
    c += "    top: 60%; left: 65%;\n"
    c += "  }\n"
    c += "  .deco-line-1 {\n"
    c += "    width: 1px; height: 300px;\n"
    c += "    background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.08), transparent);\n"
    c += "    top: 100px; right: 200px;\n"
    c += "  }\n"
    c += "  .deco-line-2 {\n"
    c += "    width: 400px; height: 1px;\n"
    c += "    background: linear-gradient(to right, transparent, rgba(255,255,255,0.06), transparent);\n"
    c += "    bottom: 200px; left: 100px;\n"
    c += "  }\n"
    c += "  .deco-dots {\n"
    c += "    width: 120px; height: 120px;\n"
    c += "    background-image: radial-gradient(rgba(255,255,255,0.08) 1.5px, transparent 1.5px);\n"
    c += "    background-size: 16px 16px;\n"
    c += "    bottom: 120px; right: 80px;\n"
    c += "  }\n\n"
    c += "  .deco-blob-tr {\n"
    c += "    width: 400px; height: 400px; border-radius: 50%;\n"
    c += "    background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);\n"
    c += "    top: -120px; right: -120px;\n"
    c += "  }\n"
    c += "  .deco-line-accent {\n"
    c += "    width: 160px; height: 3px;\n"
    c += "    background: linear-gradient(to right, rgba(255,255,255,0.15), transparent);\n"
    c += "    bottom: 160px; left: 80px;\n"
    c += "  }\n"
    c += "  .deco-dot-grid {\n"
    c += "    width: 80px; height: 80px;\n"
    c += "    background-image: radial-gradient(rgba(255,255,255,0.07) 1.5px, transparent 1.5px);\n"
    c += "    background-size: 12px 12px;\n"
    c += "    top: 80px; right: 80px;\n"
    c += "  }\n"
    c += "  .deco-circle-br {\n"
    c += "    width: 300px; height: 300px; border-radius: 50%;\n"
    c += "    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);\n"
    c += "    bottom: -100px; right: -80px;\n"
    c += "  }\n"
    c += "  .deco-stripe {\n"
    c += "    width: 200px; height: 1px;\n"
    c += "    background: rgba(255,255,255,0.06);\n"
    c += "    top: 200px; right: 80px;\n"
    c += "  }\n"
    c += "  .deco-cross {\n"
    c += "    width: 24px; height: 24px;\n"
    c += "    top: 100px; right: 120px;\n"
    c += "  }\n"
    c += "  .deco-cross::before, .deco-cross::after {\n"
    c += "    content: ''; position: absolute;\n"
    c += "    background: rgba(255,255,255,0.1);\n"
    c += "  }\n"
    c += "  .deco-cross::before { width: 24px; height: 1px; top: 12px; }\n"
    c += "  .deco-cross::after { width: 1px; height: 24px; left: 12px; }\n\n"
    c += "  .deco-arc-tl {\n"
    c += "    width: 250px; height: 250px;\n"
    c += "    border: 1px solid rgba(255,255,255,0.05);\n"
    c += "    border-radius: 50%; top: -80px; left: -80px;\n"
    c += "  }\n"
    c += "  .deco-dots-row {\n"
    c += "    width: 100px; height: 4px;\n"
    c += "    background-image: radial-gradient(rgba(255,255,255,0.1) 2px, transparent 2px);\n"
    c += "    background-size: 12px 4px;\n"
    c += "    bottom: 140px; right: 100px;\n"
    c += "  }\n"
    c += "  .deco-square-float {\n"
    c += "    width: 40px; height: 40px;\n"
    c += "    border: 1px solid rgba(255,255,255,0.06);\n"
    c += "    border-radius: 8px; transform: rotate(15deg);\n"
    c += "    top: 120px; right: 160px;\n"
    c += "  }\n"
    c += "  .deco-ring-sm {\n"
    c += "    width: 160px; height: 160px;\n"
    c += "    border: 1px solid rgba(255,255,255,0.05);\n"
    c += "    border-radius: 50%; bottom: 60px; left: -40px;\n"
    c += "  }\n"
    c += "  .deco-line-diag {\n"
    c += "    width: 200px; height: 1px;\n"
    c += "    background: rgba(255,255,255,0.06);\n"
    c += "    transform: rotate(-30deg); top: 160px; right: 40px;\n"
    c += "  }\n"
    c += "  .deco-triangle {\n"
    c += "    width: 0; height: 0;\n"
    c += "    border-left: 20px solid transparent;\n"
    c += "    border-right: 20px solid transparent;\n"
    c += "    border-bottom: 35px solid rgba(255,255,255,0.04);\n"
    c += "    top: 80px; right: 200px;\n"
    c += "  }\n"
    c += "  .deco-blob-bl {\n"
    c += "    width: 350px; height: 350px; border-radius: 50%;\n"
    c += "    background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);\n"
    c += "    bottom: -100px; left: -80px;\n"
    c += "  }\n"
    c += "  .deco-dash-line {\n"
    c += "    width: 120px; height: 1px;\n"
    c += "    background: repeating-linear-gradient(to right, "
    c += "rgba(255,255,255,0.08), rgba(255,255,255,0.08) 6px, "
    c += "transparent 6px, transparent 12px);\n"
    c += "    top: 180px; right: 80px;\n"
    c += "  }\n"
    c += "  .deco-circle-sm {\n"
    c += "    width: 60px; height: 60px; border-radius: 50%;\n"
    c += "    background: rgba(255,255,255,0.03);\n"
    c += "    top: 80px; right: 100px;\n"
    c += "  }\n\n"
    c += "  .deco-ring {\n"
    c += "    width: 300px; height: 300px;\n"
    c += "    border: 1px solid rgba(255,255,255,0.06);\n"
    c += "    border-radius: 50%; bottom: -60px; right: -60px;\n"
    c += "  }\n\n"
    return c


def _build_css_cards():
    """카드 타입별 CSS"""
    c = ""
    c += "  .cover-card .card-inner {\n"
    c += "    justify-content: center; align-items: center; text-align: center;\n"
    c += "  }\n"
    c += "  .cover-badge {\n"
    c += "    display: inline-block; padding: 10px 28px;\n"
    c += "    background: rgba(255,255,255,0.08);\n"
    c += "    backdrop-filter: blur(8px);\n"
    c += "    border: 1px solid rgba(255,255,255,0.12);\n"
    c += "    color: rgba(255,255,255,0.9);\n"
    c += "    font-size: 14px; font-weight: 700;\n"
    c += "    letter-spacing: 4px; border-radius: 40px;\n"
    c += "    margin-bottom: 56px;\n"
    c += "  }\n"
    c += "  .cover-title {\n"
    c += "    font-size: 60px; font-weight: 900; color: #fff;\n"
    c += "    line-height: 1.25; margin-bottom: 32px; letter-spacing: -1px;\n"
    c += "  }\n"
    c += "  .cover-divider {\n"
    c += "    width: 64px; height: 3px;\n"
    c += "    background: linear-gradient(to right, #8b5cf6, #6366f1);\n"
    c += "    border-radius: 2px; margin: 0 auto 32px;\n"
    c += "  }\n"
    c += "  .cover-subtitle {\n"
    c += "    font-size: 26px; font-weight: 300;\n"
    c += "    color: rgba(255,255,255,0.6); margin-bottom: 12px;\n"
    c += "  }\n"
    c += "  .cover-accent {\n"
    c += "    font-size: 18px; color: rgba(167,139,250,0.9);\n"
    c += "    font-weight: 500; margin-top: 24px;\n"
    c += "  }\n\n"
    c += "  .news-card .card-inner { justify-content: flex-start; }\n"
    c += "  .news-header { position: relative; margin-bottom: 32px; }\n"
    c += "  .news-number {\n"
    c += "    font-family: 'Inter', sans-serif;\n"
    c += "    font-size: 140px; font-weight: 900;\n"
    c += "    line-height: 1; letter-spacing: -6px;\n"
    c += "    position: absolute; top: -20px; left: -10px;\n"
    c += "  }\n"
    c += "  .news-label {\n"
    c += "    position: relative; font-family: 'Inter', sans-serif;\n"
    c += "    font-size: 13px; font-weight: 700;\n"
    c += "    letter-spacing: 4px; padding-top: 8px;\n"
    c += "  }\n"
    c += "  .news-content {\n"
    c += "    flex: 1; display: flex; flex-direction: column;\n"
    c += "    justify-content: center; margin-top: 20px;\n"
    c += "  }\n"
    c += "  .news-title {\n"
    c += "    font-size: 46px; font-weight: 800;\n"
    c += "    line-height: 1.35; margin-bottom: 36px;\n"
    c += "    letter-spacing: -0.5px; white-space: pre-line;\n"
    c += "  }\n"
    c += "  .news-body-wrap { padding-left: 24px; margin-bottom: 8px; }\n"
    c += "  .news-body {\n"
    c += "    font-size: 22px; font-weight: 400;\n"
    c += "    line-height: 1.85; max-width: 780px;\n"
    c += "  }\n"
    c += "  .tags { display: flex; gap: 10px; margin-top: 40px; flex-wrap: wrap; }\n"
    c += "  .tag {\n"
    c += "    padding: 8px 20px; font-size: 15px; font-weight: 600;\n"
    c += "    border-radius: 24px; backdrop-filter: blur(4px);\n"
    c += "    border: 1px solid rgba(255,255,255,0.08);\n"
    c += "  }\n\n"
    c += "  .closing-card .card-inner {\n"
    c += "    justify-content: center; align-items: center; text-align: center;\n"
    c += "  }\n"
    c += "  .closing-icon-wrap {\n"
    c += "    width: 80px; height: 80px; border-radius: 50%;\n"
    c += "    background: rgba(255,255,255,0.08);\n"
    c += "    backdrop-filter: blur(8px);\n"
    c += "    border: 1px solid rgba(255,255,255,0.12);\n"
    c += "    display: flex; align-items: center;\n"
    c += "    justify-content: center; margin-bottom: 40px;\n"
    c += "  }\n"
    c += "  .closing-title {\n"
    c += "    font-size: 42px; font-weight: 800;\n"
    c += "    color: #fff; margin-bottom: 24px;\n"
    c += "  }\n"
    c += "  .closing-body {\n"
    c += "    font-size: 22px; color: rgba(255,255,255,0.65);\n"
    c += "    line-height: 1.75; margin-bottom: 48px; max-width: 560px;\n"
    c += "  }\n"
    c += "  .closing-divider {\n"
    c += "    width: 48px; height: 2px;\n"
    c += "    background: rgba(255,255,255,0.15);\n"
    c += "    margin: 0 auto 32px;\n"
    c += "  }\n"
    c += "  .closing-source { font-size: 15px; color: rgba(255,255,255,0.35); }\n\n"
    c += "  .card-footer {\n"
    c += "    position: absolute; z-index: 3;\n"
    c += "    bottom: 0; left: 0; right: 0;\n"
    c += "    padding: 28px 48px;\n"
    c += "    display: flex; justify-content: flex-end;\n"
    c += "  }\n"
    c += "  .page-indicator {\n"
    c += "    font-family: 'Inter', sans-serif;\n"
    c += "    font-size: 13px; color: rgba(255,255,255,0.35);\n"
    c += "    font-weight: 500; letter-spacing: 3px;\n"
    c += "  }\n\n"
    return c


def _build_css_responsive():
    """반응형 CSS"""
    c = ""
    c += "  @media (max-width: 1120px) {\n"
    c += "    .card { width: 540px; height: 540px; }\n"
    c += "    .card-inner { padding: 40px; }\n"
    c += "    .cover-title { font-size: 32px; }\n"
    c += "    .cover-subtitle { font-size: 16px; }\n"
    c += "    .cover-badge { font-size: 11px; padding: 6px 16px; margin-bottom: 28px; }\n"
    c += "    .cover-accent { font-size: 13px; }\n"
    c += "    .news-number { font-size: 70px; }\n"
    c += "    .news-label { font-size: 10px; }\n"
    c += "    .news-title { font-size: 24px; margin-bottom: 16px; }\n"
    c += "    .news-body { font-size: 13px; }\n"
    c += "    .news-body-wrap { padding-left: 14px; }\n"
    c += "    .tag { font-size: 11px; padding: 4px 12px; }\n"
    c += "    .tags { margin-top: 16px; gap: 6px; }\n"
    c += "    .closing-title { font-size: 24px; }\n"
    c += "    .closing-body { font-size: 14px; margin-bottom: 24px; }\n"
    c += "    .closing-source { font-size: 11px; }\n"
    c += "    .closing-icon-wrap { width: 48px; height: 48px; margin-bottom: 20px; }\n"
    c += "    .closing-icon-wrap svg { width: 24px; height: 24px; }\n"
    c += "  }\n\n"
    return c


def _build_css_toast():
    """토스트 CSS"""
    c = ""
    c += "  .toast {\n"
    c += "    position: fixed; bottom: 24px; left: 50%;\n"
    c += "    transform: translateX(-50%);\n"
    c += "    background: rgba(30,30,40,0.95); color: white;\n"
    c += "    padding: 12px 28px; border-radius: 12px;\n"
    c += "    font-size: 14px; z-index: 9999; display: none;\n"
    c += "    font-family: 'Noto Sans KR', sans-serif;\n"
    c += "    backdrop-filter: blur(12px);\n"
    c += "    border: 1px solid rgba(255,255,255,0.1);\n"
    c += "  }\n"
    return c


def _build_js():
    """JavaScript 코드를 일반 문자열로 반환"""
    js = "<script>\n"
    js += "function showToast(msg) {\n"
    js += "    const t = document.getElementById('toast');\n"
    js += "    t.textContent = msg;\n"
    js += "    t.style.display = 'block';\n"
    js += "    clearTimeout(t._tid);\n"
    js += "    t._tid = setTimeout(() => t.style.display = 'none', 2500);\n"
    js += "}\n\n"
    js += "async function captureCard(cardEl, filename) {\n"
    js += "    const origW = cardEl.style.width;\n"
    js += "    const origH = cardEl.style.height;\n"
    js += "    cardEl.style.width = '1080px';\n"
    js += "    cardEl.style.height = '1080px';\n"
    js += "    const canvas = await html2canvas(cardEl, {\n"
    js += "        scale: 1, width: 1080, height: 1080,\n"
    js += "        useCORS: true, backgroundColor: null, logging: false\n"
    js += "    });\n"
    js += "    cardEl.style.width = origW;\n"
    js += "    cardEl.style.height = origH;\n"
    js += "    const link = document.createElement('a');\n"
    js += "    link.download = filename;\n"
    js += "    link.href = canvas.toDataURL('image/png');\n"
    js += "    link.click();\n"
    js += "}\n\n"
    js += "async function downloadAll() {\n"
    js += "    const cards = document.querySelectorAll('.card');\n"
    js += "    showToast('전체 ' + cards.length + '장 저장 시작...');\n"
    js += "    for (let i = 0; i < cards.length; i++) {\n"
    js += "        showToast((i + 1) + ' / ' + cards.length + ' 저장 중...');\n"
    js += "        await captureCard(cards[i], "
    js += "'card_' + String(i + 1).padStart(2, '0') + '.png');\n"
    js += "        await new Promise(r => setTimeout(r, 600));\n"
    js += "    }\n"
    js += "    showToast('전체 저장 완료\!');\n"
    js += "}\n\n"
    js += "function downloadSingle() {\n"
    js += "    const cards = document.querySelectorAll('.card');\n"
    js += "    let best = 0, bestDist = Infinity;\n"
    js += "    const viewMid = window.scrollY + window.innerHeight / 2;\n"
    js += "    cards.forEach((c, i) => {\n"
    js += "        const rect = c.getBoundingClientRect();\n"
    js += "        const cardMid = window.scrollY + rect.top + rect.height / 2;\n"
    js += "        const dist = Math.abs(viewMid - cardMid);\n"
    js += "        if (dist < bestDist) { bestDist = dist; best = i; }\n"
    js += "    });\n"
    js += "    captureCard(cards[best], "
    js += "'card_' + String(best + 1).padStart(2, '0') + '.png');\n"
    js += "    showToast('카드 ' + (best + 1) + ' 저장\!');\n"
    js += "}\n"
    js += "</script>\n"
    return js


def generate_html(data, theme="modern-light"):
    """전체 HTML 파일을 생성합니다."""
    title = data.get("title", "카드뉴스")
    cards = data.get("cards", [])
    total = len(cards)
    date = data.get("date", datetime.now().strftime("%Y.%m.%d"))

    cards_html = "\n".join(
        generate_card_html(card, i, total) for i, card in enumerate(cards)
    )

    html = "<\!DOCTYPE html>\n"
    html += '<html lang="ko">\n'
    html += "<head>\n"
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html += "<title>" + title + " - " + date + "</title>\n"
    html += '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    html += '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    html += '<link href="https://fonts.googleapis.com/css2?'
    html += 'family=Noto+Sans+KR:wght@300;400;500;700;900'
    html += '&family=Inter:wght@300;400;500;700;900&display=swap" rel="stylesheet">\n'
    html += '<script src="https://cdnjs.cloudflare.com/ajax/libs/'
    html += 'html2canvas/1.4.1/html2canvas.min.js"></script>\n'
    html += _build_css()
    html += "</head>\n"
    html += "<body>\n\n"
    html += '<div class="controls">\n'
    html += '    <button class="btn btn-primary" onclick="downloadAll()">'
    html += '전체 PNG 저장</button>\n'
    html += '    <button class="btn btn-secondary" onclick="downloadSingle()">'
    html += '현재 카드만 저장</button>\n'
    html += '</div>\n\n'
    html += '<div id="cards-container">\n'
    html += cards_html + "\n"
    html += '</div>\n\n'
    html += '<div class="toast" id="toast">저장 중...</div>\n\n'
    html += _build_js()
    html += "</body>\n"
    html += "</html>"
    return html


def main():
    parser = argparse.ArgumentParser(description="카드뉴스 HTML 생성기 v2")
    parser.add_argument("--input", required=True, help="입력 JSON 파일 경로")
    parser.add_argument("--output", required=True, help="출력 HTML 파일 경로")
    parser.add_argument("--theme", default="modern-light",
                       choices=["modern-light", "dark-tech"],
                       help="테마 선택")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = generate_html(data, args.theme)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print("카드뉴스 생성 완료: " + args.output)
    print("총 " + str(len(data.get("cards", []))) + "장의 카드가 생성되었습니다.")


if __name__ == "__main__":
    main()
